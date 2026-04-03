from datetime import datetime
from zoneinfo import ZoneInfo


def _slot_value(hour: int, slots: list[dict]) -> float:
    for slot in slots:
        if slot["start"] <= hour < slot["end"]:
            return float(slot["value"])
    return 0.35


def get_current_congestion(
    city_meta: dict,
    weather_context: dict,
    aqi_norm: float,
    config: dict,
) -> tuple[float, str]:
    """
    Return a live traffic proxy score.
    The score is derived from live local time and live environmental stress.
    """
    timezone_name = city_meta.get("timezone", "Asia/Kolkata")
    local_hour = datetime.now(ZoneInfo(timezone_name)).hour
    traffic_cfg = config.get("traffic_profile", {})
    slot_risk = _slot_value(local_hour, traffic_cfg.get("slots", []))

    rain_norm = min(
        float(weather_context.get("rain_6h", 0))
        / max(config["feature_bounds"].get("rainfall_short_max", 60.0), 1.0),
        1.0,
    )
    heat_norm = min(
        max(float(weather_context.get("heat_index", 0)) - config["feature_bounds"].get("heat_index_min", 24.0), 0)
        / max(
            config["feature_bounds"].get("heat_index_max", 60.0)
            - config["feature_bounds"].get("heat_index_min", 24.0),
            1.0,
        ),
        1.0,
    )
    score = (
        slot_risk
        + rain_norm * float(traffic_cfg.get("rain_weight", 0.22))
        + heat_norm * float(traffic_cfg.get("heat_weight", 0.08))
        + aqi_norm * float(traffic_cfg.get("aqi_weight", 0.05))
    )
    return min(score, float(traffic_cfg.get("max", 1.0))), "derived_live_proxy"
