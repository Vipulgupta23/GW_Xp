"""
3-Layer Fraud Detection Engine
Layer 1: Rule-based validations (hard flags)
Layer 2: Behavioral analysis (soft flags)
Layer 3: Isolation Forest ML anomaly detection (soft flags)
"""

import os
import joblib
import numpy as np
from datetime import datetime, timezone

MODELS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models"
)

_iso_forest = None


def _load_iso_forest():
    global _iso_forest
    if _iso_forest is None:
        path = os.path.join(MODELS_DIR, "isolation_forest.joblib")
        if os.path.exists(path):
            _iso_forest = joblib.load(path)
        else:
            print(f"⚠️  Isolation Forest not found at {path}")


def run_fraud_layer1(
    worker: dict,
    disruption: dict,
    has_duplicate_claim: bool = False,
    policy_after_event: bool = False,
) -> dict:
    """Rule-based checks — hard failures block payout."""
    flags = []

    # 1. Worker's grid must match disruption's grid
    if worker.get("grid_id") and disruption.get("grid_id"):
        if worker["grid_id"] != disruption["grid_id"]:
            flags.append(
                {"type": "zone_mismatch", "layer": 1, "severity": "hard"}
            )

    # 2. Worker should have recent activity
    # (In demo context, we check is_active flag)
    if not worker.get("is_active", True):
        flags.append(
            {"type": "not_recently_active", "layer": 1, "severity": "hard"}
        )

    # 3. No duplicate claim for same disruption
    if has_duplicate_claim:
        flags.append(
            {"type": "duplicate_claim", "layer": 1, "severity": "hard"}
        )

    # 4. Worker must have had policy BEFORE disruption started
    if policy_after_event:
        flags.append(
            {"type": "policy_after_event", "layer": 1, "severity": "hard"}
        )

    hard = [f for f in flags if f["severity"] == "hard"]
    return {"pass": len(hard) == 0, "flags": flags}


def run_fraud_layer2(worker: dict, simulation: dict, income_gap: float) -> dict:
    """Behavioral analysis — soft flags reduce payout to 70%."""
    flags = []

    # 1. Income gap can't be more than 2.2× average daily earnings
    avg_daily = worker.get("avg_daily_earnings", 900)
    if income_gap > avg_daily * 2.2:
        flags.append(
            {"type": "abnormal_claim_size", "layer": 2, "severity": "soft"}
        )

    # 2. New worker risk (less than 14 days old)
    created_at = worker.get("created_at")
    if created_at:
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(
                    created_at.replace("Z", "+00:00")
                )
            except Exception:
                created_at = None
        if created_at:
            age_days = (datetime.now(timezone.utc) - created_at).days
            if age_days < 14:
                flags.append(
                    {
                        "type": "new_worker_high_risk",
                        "layer": 2,
                        "severity": "soft",
                    }
                )

    # 3. ISS too low
    if worker.get("iss_score", 50) < 30:
        flags.append(
            {"type": "very_low_iss", "layer": 2, "severity": "soft"}
        )

    return {"pass": len(flags) == 0, "flags": flags}


def run_fraud_layer3(
    payout: float,
    income_gap: float,
    disruption_hours: int,
    worker: dict,
) -> dict:
    """ML anomaly detection — Isolation Forest."""
    _load_iso_forest()

    X = [
        [
            payout,
            income_gap,
            disruption_hours,
            worker.get("iss_score", 50),
            worker.get("past_claims_count", 0),
            worker.get("fraud_flags_count", 0),
        ]
    ]

    if _iso_forest is not None:
        prediction = _iso_forest.predict(X)[0]
        score = float(_iso_forest.decision_function(X)[0])
        is_anomaly = prediction == -1
    else:
        # Fallback: pass everything if model not loaded
        is_anomaly = False
        score = 0.5

    return {
        "pass": not is_anomaly,
        "anomaly_score": score,
        "flags": (
            [
                {
                    "type": "ml_anomaly_detected",
                    "layer": 3,
                    "severity": "soft",
                    "score": score,
                }
            ]
            if is_anomaly
            else []
        ),
    }
