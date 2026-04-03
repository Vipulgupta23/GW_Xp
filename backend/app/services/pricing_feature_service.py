from datetime import datetime, timedelta, timezone
from typing import Any

from app.database import get_supabase
from app.services import weather_service, aqi_service, traffic_service
from app.services.pricing_config_service import get_active_pricing_config


def _normalize(value: float, min_value: float, max_value: float) -> float:
    if max_value <= min_value:
        return 0.0
    return min(max((value - min_value) / (max_value - min_value), 0.0), 1.0)


def _compute_heat_index_c(temp_c: float, humidity: float) -> float:
    # Rothfusz regression adapted to Celsius.
    f = temp_c * 9 / 5 + 32
    hi_f = (
        -42.379
        + 2.04901523 * f
        + 10.14333127 * humidity
        - 0.22475541 * f * humidity
        - 6.83783e-3 * f * f
        - 5.481717e-2 * humidity * humidity
        + 1.22874e-3 * f * f * humidity
        + 8.5282e-4 * f * humidity * humidity
        - 1.99e-6 * f * f * humidity * humidity
    )
    return round((hi_f - 32) * 5 / 9, 2)


def _snapshot_is_fresh(snapshot_row: dict) -> bool:
    try:
        expires_at = datetime.fromisoformat(snapshot_row["expires_at"].replace("Z", "+00:00"))
        return expires_at > datetime.now(timezone.utc)
    except Exception:
        return False


def _rolling_peak_rain_24h(forecast: list[dict]) -> float:
    if not forecast:
        return 0.0
    window_size = min(8, len(forecast))
    totals = []
    for start in range(0, len(forecast) - window_size + 1):
        totals.append(
            sum(float(item.get("rain_3h", 0)) for item in forecast[start : start + window_size])
        )
    if not totals:
        totals = [sum(float(item.get("rain_3h", 0)) for item in forecast)]
    return round(max(totals), 2)


def _predictive_risk_hours(forecast: list[dict], config: dict) -> int:
    if not forecast:
        return 0
    coverage_cfg = config.get("coverage_hours", {})
    thresholds = coverage_cfg.get("risk_hour_thresholds", {})
    rain_threshold = float(thresholds.get("rain_3h", 4.0))
    heat_threshold = float(thresholds.get("temp", 35.0))
    qualifying_slots = 0
    for item in forecast:
        rain_3h = float(item.get("rain_3h", 0))
        temp = float(item.get("temp", 0))
        if rain_3h >= rain_threshold or temp >= heat_threshold:
            qualifying_slots += 1
    max_predictive_hours = int(coverage_cfg.get("max_predictive_hours", 24))
    return min(qualifying_slots * 3, max_predictive_hours)


async def refresh_grid_features(grid: dict, city_meta: dict, force: bool = False) -> dict:
    db = get_supabase()
    config = get_active_pricing_config()

    current_res = (
        db.table("microgrid_features_current")
        .select("*")
        .eq("grid_id", grid["id"])
        .limit(1)
        .execute()
    )
    current = current_res.data[0] if current_res.data else None
    if current and not force and _snapshot_is_fresh(current):
        return current

    weather = await weather_service.get_current(grid["center_lat"], grid["center_lng"])
    forecast = await weather_service.get_forecast_7day(grid["center_lat"], grid["center_lng"])
    aqi = await aqi_service.get_current(grid["center_lat"], grid["center_lng"])

    heat_index = _compute_heat_index_c(
        float(weather.get("temp", 30)),
        float(weather.get("humidity", 60)),
    )
    aqi_norm = min(
        float(aqi) / max(config["feature_bounds"].get("aqi_max", 400.0), 1.0),
        1.0,
    )
    rainfall_7d_avg = (
        sum(float(item.get("rain_3h", 0)) for item in forecast) / max(len(forecast), 1) * 8
        if forecast
        else 0.0
    )
    forecast_peak_rain_24h = _rolling_peak_rain_24h(forecast)
    predictive_risk_hours = _predictive_risk_hours(forecast, config)
    rain_6h = float(weather.get("rain_6h", 0))
    flood_cfg = config.get("flood_formula", {})
    flood_risk = min(
        _normalize(
            rain_6h,
            0.0,
            config["feature_bounds"].get("rainfall_short_max", 60.0),
        )
        * float(flood_cfg.get("rain_6h_weight", 0.62))
        + _normalize(
            rainfall_7d_avg,
            0.0,
            config["feature_bounds"].get("rainfall_daily_max", 120.0),
        )
        * float(flood_cfg.get("rainfall_7d_weight", 0.38)),
        float(flood_cfg.get("max", 1.0)),
    )

    weather_context = {
        **weather,
        "heat_index": heat_index,
        "rainfall_7d_avg": rainfall_7d_avg,
    }
    traffic_risk, traffic_source = traffic_service.get_current_congestion(
        city_meta,
        weather_context,
        aqi_norm,
        config,
    )

    heat_index_norm = _normalize(
        heat_index,
        config["feature_bounds"].get("heat_index_min", 24.0),
        config["feature_bounds"].get("heat_index_max", 60.0),
    )
    rainfall_7d_norm = _normalize(
        rainfall_7d_avg,
        0.0,
        config["feature_bounds"].get("rainfall_daily_max", 120.0),
    )
    seasonal_cfg = config.get("seasonal_factor", {})
    seasonal_signal = min(
        rainfall_7d_norm * float(seasonal_cfg.get("rainfall_weight", 0.24))
        + heat_index_norm * float(seasonal_cfg.get("heat_weight", 0.16))
        + aqi_norm * float(seasonal_cfg.get("aqi_weight", 0.08)),
        1.0,
    )
    seasonal_factor = min(
        float(seasonal_cfg.get("base", 0.92)) + seasonal_signal,
        float(seasonal_cfg.get("max", 1.35)),
    )

    observed_at = datetime.now(timezone.utc)
    ttl_minutes = max(
        int(config.get("freshness_minutes", {}).get("quote", 30)),
        5,
    )
    expires_at = observed_at + timedelta(minutes=ttl_minutes)

    snapshot = {
        "grid_id": grid["id"],
        "city_slug": city_meta["slug"],
        "city": city_meta["name"],
        "weather_temp": round(float(weather.get("temp", 30)), 2),
        "humidity": round(float(weather.get("humidity", 60)), 2),
        "heat_index": heat_index,
        "heat_index_norm": round(heat_index_norm, 4),
        "aqi": round(float(aqi), 2),
        "aqi_norm": round(aqi_norm, 4),
        "rain_6h": round(rain_6h, 2),
        "rainfall_7d_avg": round(rainfall_7d_avg, 2),
        "rainfall_7d_norm": round(rainfall_7d_norm, 4),
        "forecast_peak_rain_24h": forecast_peak_rain_24h,
        "predictive_risk_hours": predictive_risk_hours,
        "flood_risk": round(flood_risk, 4),
        "traffic_risk": round(float(traffic_risk), 4),
        "seasonal_signal": round(seasonal_signal, 4),
        "seasonal_factor": round(seasonal_factor, 4),
        "weather_description": weather.get("description", "clear"),
        "weather_source": "openweather",
        "aqi_source": "aqicn",
        "traffic_source": traffic_source,
    }
    row = {
        "grid_id": grid["id"],
        "city_slug": city_meta["slug"],
        "feature_snapshot": snapshot,
        "observed_at": observed_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "source": "live_data_pipeline",
        "source_status": "fresh",
        "pricing_version": config["version"],
    }
    db.table("microgrid_features_current").upsert(row).execute()
    db.table("microgrid_features_history").insert(row).execute()
    db.table("supported_cities").update(
        {
            "feature_status": "fresh",
            "updated_at": observed_at.isoformat(),
        }
    ).eq("slug", city_meta["slug"]).execute()
    return {
        **row,
        "feature_snapshot": snapshot,
    }


async def get_grid_features(grid: dict, city_meta: dict) -> dict:
    db = get_supabase()
    current_res = (
        db.table("microgrid_features_current")
        .select("*")
        .eq("grid_id", grid["id"])
        .limit(1)
        .execute()
    )
    current = current_res.data[0] if current_res.data else None
    if current and _snapshot_is_fresh(current):
        return current
    if current:
        try:
            refreshed = await refresh_grid_features(grid, city_meta, force=True)
            refreshed["source_status"] = "fresh"
            return refreshed
        except Exception:
            current["source_status"] = "stale"
            return current
    return await refresh_grid_features(grid, city_meta, force=True)


def get_grid_history_context(grid_id: str, city_slug: str, current_snapshot: dict) -> dict:
    db = get_supabase()
    config = get_active_pricing_config()
    limit = int(config.get("history_window_rows", 72))
    history_rows = (
        db.table("microgrid_features_history")
        .select("feature_snapshot, observed_at")
        .eq("grid_id", grid_id)
        .eq("city_slug", city_slug)
        .order("observed_at", desc=True)
        .limit(limit)
        .execute()
    ).data or []

    snapshots = [row.get("feature_snapshot") or {} for row in history_rows]
    if not snapshots:
        snapshots = [current_snapshot]

    def _avg(key: str) -> float:
        values = [float(snapshot.get(key, 0)) for snapshot in snapshots]
        return round(sum(values) / max(len(values), 1), 4)

    historical_flood_risk = _avg("flood_risk")
    flood_delta = round(
        float(current_snapshot.get("flood_risk", 0)) - historical_flood_risk,
        4,
    )
    water_cfg = config.get("waterlogging_credit", {})
    safe_threshold = float(water_cfg.get("safe_threshold", 0.18))
    elevated_threshold = float(water_cfg.get("elevated_threshold", 0.55))
    current_guard = float(water_cfg.get("current_flood_guard", 0.30))

    if (
        historical_flood_risk <= safe_threshold
        and float(current_snapshot.get("flood_risk", 0)) <= current_guard
    ):
        waterlogging_band = "historically_safe"
    elif historical_flood_risk >= elevated_threshold:
        waterlogging_band = "historically_exposed"
    else:
        waterlogging_band = "mixed_history"

    return {
        "samples": len(snapshots),
        "historical_flood_risk": historical_flood_risk,
        "historical_heat_index_norm": _avg("heat_index_norm"),
        "historical_aqi_norm": _avg("aqi_norm"),
        "historical_traffic_risk": _avg("traffic_risk"),
        "flood_trend_delta": flood_delta,
        "waterlogging_band": waterlogging_band,
    }


def feature_health_summary() -> dict[str, Any]:
    db = get_supabase()
    cities = db.table("supported_cities").select("*").eq("pricing_enabled", True).execute().data or []
    feature_rows = db.table("microgrid_features_current").select("city_slug, expires_at").execute().data or []
    now = datetime.now(timezone.utc)

    freshness = []
    for city in cities:
        city_rows = [row for row in feature_rows if row.get("city_slug") == city["slug"]]
        fresh = 0
        stale = 0
        for row in city_rows:
            try:
                expires_at = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
                if expires_at > now:
                    fresh += 1
                else:
                    stale += 1
            except Exception:
                stale += 1
        freshness.append(
            {
                "city": city["name"],
                "slug": city["slug"],
                "feature_status": city.get("feature_status", "pending"),
                "grid_count": city["grid_rows"] * city["grid_cols"],
                "fresh_grids": fresh,
                "stale_grids": stale,
            }
        )
    return {"cities": freshness, "checked_at": now.isoformat()}
