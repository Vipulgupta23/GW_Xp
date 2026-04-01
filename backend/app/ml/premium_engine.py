"""
Dynamic Premium Engine — Uses trained XGBoost model to calculate
personalized weekly premiums for each worker.
"""

import os
import joblib
import pandas as pd
from datetime import datetime

MODELS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models"
)

_model = None
_features = None

PERSONA_FACTORS = {
    "hustler": 1.08,
    "stabilizer": 0.97,
    "opportunist": 1.04,
}


def _load_models():
    global _model, _features
    if _model is None:
        model_path = os.path.join(MODELS_DIR, "premium_model.joblib")
        features_path = os.path.join(MODELS_DIR, "premium_features.joblib")
        if os.path.exists(model_path):
            _model = joblib.load(model_path)
            _features = joblib.load(features_path)
        else:
            print(f"⚠️  Premium model not found at {model_path}")
            print("   Run: python -m app.ml.train_models")


def calculate_premium(
    worker: dict, plan: dict, grid: dict, rainfall_7d_avg: float = 0.0
) -> dict:
    """Calculate dynamic premium for a worker-plan-grid combo."""
    _load_models()

    month = datetime.now().month
    is_monsoon = 1 if month in [6, 7, 8, 9] else 0
    is_pre_monsoon = 1 if month in [4, 5] else 0
    seasonal_factor = (
        1.35 if is_monsoon else (1.15 if is_pre_monsoon else 0.90)
    )

    fv = {
        "flood_risk": grid.get("flood_risk", 0.3),
        "heat_index": grid.get("heat_index", 0.4),
        "aqi_norm": min(grid.get("aqi_avg", 120) / 400, 1.0),
        "traffic_risk": grid.get("traffic_risk", 0.4),
        "iss_score": worker.get("iss_score", 50.0),
        "consistency_score": worker.get("consistency_score", 0.6),
        "active_days": worker.get("active_days_per_week", 5.0),
        "peak_hour_ratio": worker.get("peak_hour_ratio", 0.5),
        "is_monsoon": is_monsoon,
        "is_festival": 0,
        "past_claims": worker.get("past_claims_count", 0),
        "fraud_flags": worker.get("fraud_flags_count", 0),
        "persona_hustler": 1 if worker.get("persona") == "hustler" else 0,
        "persona_opportunist": 1
        if worker.get("persona") == "opportunist"
        else 0,
        "rainfall_7d_norm": min(rainfall_7d_avg / 120, 1.0),
    }

    if _model is not None and _features is not None:
        X = pd.DataFrame([fv])[_features]
        zone_multiplier = float(_model.predict(X)[0])
    else:
        # Fallback when model not trained yet
        composite = grid.get("composite_risk", 0.35)
        zone_multiplier = 0.85 + composite * 0.8

    iss_discount = 0.70 + (0.30 * (1 - worker.get("iss_score", 50) / 100))
    persona_factor = PERSONA_FACTORS.get(
        worker.get("persona", "stabilizer"), 1.0
    )

    final = (
        plan["weekly_premium_base"]
        * zone_multiplier
        * iss_discount
        * persona_factor
    )
    final = round(final, 2)

    composite_risk = grid.get("composite_risk", 0.35)
    if composite_risk > 0.6:
        risk_label = "High Risk"
    elif composite_risk > 0.35:
        risk_label = "Medium Risk"
    else:
        risk_label = "Low Risk"

    iss = worker.get("iss_score", 50)
    if iss > 70:
        iss_label = "High"
    elif iss > 45:
        iss_label = "Medium"
    else:
        iss_label = "Low"

    return {
        "base": plan["weekly_premium_base"],
        "zone_multiplier": round(zone_multiplier, 3),
        "seasonal_factor": round(seasonal_factor, 3),
        "iss_discount": round(iss_discount, 3),
        "persona_factor": round(persona_factor, 3),
        "final_premium": final,
        "zone_label": f"{grid.get('city', 'Bengaluru')} Zone — {risk_label}",
        "season_label": (
            "Monsoon Season"
            if is_monsoon
            else ("Pre-Monsoon" if is_pre_monsoon else "Dry Season")
        ),
        "iss_label": iss_label,
        "persona_label": worker.get("persona", "stabilizer").capitalize(),
    }
