"""
Dynamic Premium Engine — ML-backed live pricing with explainable adjustments.
"""

import os
from functools import lru_cache

try:
    import joblib
    import pandas as pd
except Exception:  # pragma: no cover
    joblib = None
    pd = None


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@lru_cache(maxsize=1)
def _load_ml_assets() -> tuple[object | None, list[str] | None]:
    if joblib is None or pd is None:
        return None, None

    candidate_dirs = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "models"),
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "models",
        ),
    ]
    for models_dir in candidate_dirs:
        model_path = os.path.join(models_dir, "premium_model.joblib")
        features_path = os.path.join(models_dir, "premium_features.joblib")
        if os.path.exists(model_path) and os.path.exists(features_path):
            return joblib.load(model_path), joblib.load(features_path)
    return None, None


def _label_from_bands(value: float, bands: list[dict], fallback: str) -> str:
    for band in bands:
        try:
            if value <= float(band.get("max", 1.0)):
                return str(band.get("label", fallback))
        except (TypeError, ValueError):
            continue
    return fallback


def _zone_label(
    city_label: str,
    composite_signal: float,
    feature_snapshot: dict,
    pricing_config: dict,
) -> str:
    zone_cfg = pricing_config.get("zone_labels", {})
    risk_label = _label_from_bands(
        composite_signal,
        zone_cfg.get(
            "bands",
            [
                {"max": 0.30, "label": "Low Risk"},
                {"max": 0.55, "label": "Medium Risk"},
                {"max": 0.80, "label": "High Risk"},
                {"max": 1.0, "label": "Severe Risk"},
            ],
        ),
        "Live Risk",
    )

    dominant_signal = max(
        [
            ("water-logging", _safe_float(feature_snapshot.get("flood_risk"))),
            ("heat stress", _safe_float(feature_snapshot.get("heat_index_norm"))),
            ("AQI stress", _safe_float(feature_snapshot.get("aqi_norm"))),
            ("traffic drag", _safe_float(feature_snapshot.get("traffic_risk"))),
        ],
        key=lambda item: item[1],
    )

    suffix = ""
    if dominant_signal[1] >= 0.45:
        suffix = f" · {dominant_signal[0]}"
    return f"{city_label} Zone — {risk_label}{suffix}"


def _season_label(feature_snapshot: dict, pricing_config: dict) -> str:
    season_cfg = pricing_config.get("season_labels", {})
    rain_signal = max(
        _safe_float(feature_snapshot.get("rainfall_7d_norm")),
        min(_safe_float(feature_snapshot.get("rain_6h")) / 30.0, 1.0),
    )
    heat_signal = _safe_float(feature_snapshot.get("heat_index_norm"))
    aqi_signal = _safe_float(feature_snapshot.get("aqi_norm"))

    dominant_signal = max(
        [
            ("Rain-Heavy Window", rain_signal),
            ("Heat Stress Window", heat_signal),
            ("Pollution Stress Window", aqi_signal),
        ],
        key=lambda item: item[1],
    )

    calm_max = _safe_float(season_cfg.get("calm_max"), 0.22)
    if dominant_signal[1] <= calm_max:
        return str(season_cfg.get("calm_label", "Stable Conditions"))

    weather_description = str(
        feature_snapshot.get("weather_description", "clear")
    ).title()
    return f"{dominant_signal[0]} · {weather_description}"


def _iss_label(iss_score: float, pricing_config: dict) -> str:
    iss_cfg = pricing_config.get("iss_labels", {})
    return _label_from_bands(
        iss_score,
        iss_cfg.get(
            "bands",
            [
                {"max": 35, "label": "Low"},
                {"max": 70, "label": "Medium"},
                {"max": 100, "label": "High"},
            ],
        ),
        "Medium",
    )


def _persona_label(worker: dict, pricing_config: dict) -> str:
    persona = str(worker.get("persona", "stabilizer"))
    persona_labels = pricing_config.get("persona_labels", {})
    return str(persona_labels.get(persona, persona.replace("_", " ").title()))


def _ml_zone_multiplier(
    worker: dict,
    feature_snapshot: dict,
    history_context: dict,
    formula_multiplier: float,
    pricing_config: dict,
) -> tuple[float, str]:
    model, feature_names = _load_ml_assets()
    ml_cfg = pricing_config.get("ml", {})
    if not ml_cfg.get("enabled", True) or model is None or not feature_names or pd is None:
        return formula_multiplier, "config_formula"

    consistency_score = min(
        max(_safe_float(worker.get("active_days_per_week"), 5.0) / 7.0, 0.0),
        1.0,
    )
    feature_map = {
        "flood_risk": _safe_float(feature_snapshot.get("flood_risk")),
        "heat_index": _safe_float(feature_snapshot.get("heat_index_norm")),
        "aqi_norm": _safe_float(feature_snapshot.get("aqi_norm")),
        "traffic_risk": _safe_float(feature_snapshot.get("traffic_risk")),
        "iss_score": _safe_float(worker.get("iss_score"), 50.0),
        "consistency_score": consistency_score,
        "active_days": _safe_float(worker.get("active_days_per_week"), 5.0),
        "peak_hour_ratio": _safe_float(worker.get("peak_hour_ratio"), 0.5),
        "is_monsoon": 1 if _safe_float(feature_snapshot.get("rainfall_7d_norm")) >= 0.45 else 0,
        "is_festival": 0,
        "past_claims": _safe_float(worker.get("past_claims_count"), 0.0),
        "fraud_flags": _safe_float(worker.get("fraud_flags_count"), 0.0),
        "persona_hustler": 1 if worker.get("persona") == "hustler" else 0,
        "persona_opportunist": 1 if worker.get("persona") == "opportunist" else 0,
        "rainfall_7d_norm": _safe_float(feature_snapshot.get("rainfall_7d_norm")),
    }
    frame = pd.DataFrame(
        [{feature: feature_map.get(feature, 0.0) for feature in feature_names}]
    )
    raw_prediction = _safe_float(model.predict(frame)[0], formula_multiplier)
    historical_flood = _safe_float(history_context.get("historical_flood_risk"))
    historical_bias = 1 - (
        historical_flood * _safe_float(ml_cfg.get("historical_flood_blend"), 0.08)
    )
    adjusted_prediction = raw_prediction * historical_bias

    blend_weight = _safe_float(ml_cfg.get("blend_weight"), 0.65)
    blended = formula_multiplier * (1 - blend_weight) + adjusted_prediction * blend_weight
    min_multiplier = _safe_float(ml_cfg.get("min_multiplier"), 0.72)
    max_multiplier = _safe_float(ml_cfg.get("max_multiplier"), 1.65)
    return min(max(round(blended, 4), min_multiplier), max_multiplier), "ml_blended"


def calculate_premium(
    worker: dict,
    plan: dict,
    feature_snapshot: dict,
    history_context: dict,
    pricing_config: dict,
    city_label: str,
) -> dict:
    weights = pricing_config.get("feature_weights", {})
    composite_signal = (
        _safe_float(feature_snapshot.get("flood_risk"))
        * _safe_float(weights.get("flood_risk"))
        + _safe_float(feature_snapshot.get("heat_index_norm"))
        * _safe_float(weights.get("heat_index_norm"))
        + _safe_float(feature_snapshot.get("aqi_norm"))
        * _safe_float(weights.get("aqi_norm"))
        + _safe_float(feature_snapshot.get("traffic_risk"))
        * _safe_float(weights.get("traffic_risk"))
        + _safe_float(feature_snapshot.get("rainfall_7d_norm"))
        * _safe_float(weights.get("rainfall_7d_norm"))
        + _safe_float(feature_snapshot.get("seasonal_signal"))
        * _safe_float(weights.get("seasonal_signal"))
    )

    formula_zone_multiplier = round(
        _safe_float(pricing_config.get("base_multiplier"), 0.86)
        + composite_signal
        * _safe_float(pricing_config.get("zone_multiplier_scale"), 0.74),
        4,
    )
    zone_multiplier, zone_model_source = _ml_zone_multiplier(
        worker,
        feature_snapshot,
        history_context,
        formula_zone_multiplier,
        pricing_config,
    )

    iss_cfg = pricing_config.get("iss_discount", {})
    iss_discount = round(
        _safe_float(iss_cfg.get("base"), 0.70)
        + _safe_float(iss_cfg.get("span"), 0.30)
        * (1 - _safe_float(worker.get("iss_score"), 50.0) / 100),
        4,
    )

    persona_factor = round(
        _safe_float(
            pricing_config.get("persona_factors", {}).get(
                worker.get("persona", "stabilizer"),
                1.0,
            )
        ),
        4,
    )

    seasonal_factor = round(
        _safe_float(feature_snapshot.get("seasonal_factor"), 1.0),
        4,
    )

    base_rate = _safe_float(plan.get("weekly_premium_base"), 49.0)
    amount_after_zone = round(base_rate * zone_multiplier, 2)
    amount_after_season = round(amount_after_zone * seasonal_factor, 2)
    amount_after_iss = round(amount_after_season * iss_discount, 2)
    amount_after_persona = round(amount_after_iss * persona_factor, 2)

    water_cfg = pricing_config.get("waterlogging_credit", {})
    waterlogging_band = history_context.get("waterlogging_band", "mixed_history")
    waterlogging_adjustment = 0.0
    if waterlogging_band == "historically_safe":
        waterlogging_adjustment = -abs(
            _safe_float(water_cfg.get("safe_credit"), 2.0)
        )
    elif waterlogging_band == "historically_exposed":
        waterlogging_adjustment = abs(
            _safe_float(water_cfg.get("high_risk_surcharge"), 3.0)
        )

    final_premium = round(
        max(
            amount_after_persona + waterlogging_adjustment,
            _safe_float(pricing_config.get("minimum_premium"), 19.0),
        ),
        2,
    )

    coverage_cfg = pricing_config.get("coverage_hours", {})
    base_coverage_hours = int(
        coverage_cfg.get("base_by_plan", {}).get(plan.get("id"), 36)
    )
    bonus_cap = int(
        coverage_cfg.get("bonus_cap_by_plan", {}).get(plan.get("id"), 8)
    )
    predictive_risk_hours = int(
        _safe_float(feature_snapshot.get("predictive_risk_hours"), 0)
    )
    coverage_hours_bonus = min(int(round(predictive_risk_hours / 3)), bonus_cap)
    coverage_hours = base_coverage_hours + coverage_hours_bonus

    iss = _safe_float(worker.get("iss_score"), 50)
    iss_label = _iss_label(iss, pricing_config)

    waterlogging_note = {
        "historically_safe": "historically safe from water-logging",
        "historically_exposed": "historically exposed to water-logging",
        "mixed_history": "mixed water-logging history",
    }.get(waterlogging_band, "mixed water-logging history")
    if waterlogging_adjustment:
        pricing_story = (
            f"₹{abs(int(round(waterlogging_adjustment)))} "
            f"{'less' if waterlogging_adjustment < 0 else 'more'} this week because this grid is {waterlogging_note}."
        )
    else:
        pricing_story = "No extra flood-history adjustment this week."

    return {
        "base": base_rate,
        "zone_multiplier": zone_multiplier,
        "formula_zone_multiplier": formula_zone_multiplier,
        "seasonal_factor": seasonal_factor,
        "iss_discount": iss_discount,
        "persona_factor": persona_factor,
        "live_flood_factor": round(_safe_float(feature_snapshot.get("flood_risk")), 4),
        "live_aqi_factor": round(_safe_float(feature_snapshot.get("aqi_norm")), 4),
        "live_traffic_factor": round(_safe_float(feature_snapshot.get("traffic_risk")), 4),
        "historical_flood_risk": round(
            _safe_float(history_context.get("historical_flood_risk")),
            4,
        ),
        "waterlogging_adjustment": round(waterlogging_adjustment, 2),
        "waterlogging_band": waterlogging_band,
        "coverage_hours": coverage_hours,
        "coverage_hours_base": base_coverage_hours,
        "coverage_hours_bonus": coverage_hours_bonus,
        "coverage_hours_label": (
            f"{base_coverage_hours}h base + {coverage_hours_bonus}h predictive weather buffer"
            if coverage_hours_bonus
            else f"{base_coverage_hours}h standard protection window"
        ),
        "predictive_risk_hours": predictive_risk_hours,
        "price_steps": {
            "after_zone": amount_after_zone,
            "after_season": amount_after_season,
            "after_iss": amount_after_iss,
            "after_persona": amount_after_persona,
        },
        "final_premium": final_premium,
        "zone_label": _zone_label(
            city_label,
            composite_signal,
            feature_snapshot,
            pricing_config,
        ),
        "season_label": _season_label(feature_snapshot, pricing_config),
        "iss_label": iss_label,
        "persona_label": _persona_label(worker, pricing_config),
        "pricing_story": pricing_story,
        "zone_model_source": zone_model_source,
        "pricing_version": pricing_config.get("version", "unknown"),
    }
