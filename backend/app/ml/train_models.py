"""
Train XGBoost premium model and Isolation Forest fraud model.
Prefers real quote, claim, and disruption history from Supabase.
"""

import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.ensemble import IsolationForest
from xgboost import XGBRegressor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.database import get_supabase

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

PREMIUM_FEATURES = [
    "flood_risk",
    "heat_index",
    "aqi_norm",
    "traffic_risk",
    "iss_score",
    "consistency_score",
    "active_days",
    "peak_hour_ratio",
    "is_monsoon",
    "is_festival",
    "past_claims",
    "fraud_flags",
    "persona_hustler",
    "persona_opportunist",
    "rainfall_7d_norm",
]


def _parse_jsonish(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}
    return {}


def _parse_listish(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def generate_premium_training_data(n: int = 5000) -> pd.DataFrame:
    np.random.seed(42)
    df = pd.DataFrame(
        {
            "flood_risk": np.random.uniform(0, 1, n),
            "heat_index": np.random.uniform(0, 1, n),
            "aqi_norm": np.random.uniform(0, 1, n),
            "traffic_risk": np.random.uniform(0, 1, n),
            "iss_score": np.random.uniform(20, 95, n),
            "consistency_score": np.random.uniform(0.2, 1.0, n),
            "active_days": np.random.uniform(2, 7, n),
            "peak_hour_ratio": np.random.uniform(0.2, 0.8, n),
            "is_monsoon": np.random.randint(0, 2, n),
            "is_festival": np.random.randint(0, 2, n),
            "past_claims": np.random.randint(0, 6, n),
            "fraud_flags": np.random.randint(0, 3, n),
            "persona_hustler": np.random.randint(0, 2, n),
            "persona_opportunist": np.random.randint(0, 2, n),
            "rainfall_7d_norm": np.random.uniform(0, 1, n),
        }
    )
    df["multiplier"] = (
        0.70
        + df["flood_risk"] * 0.22
        + df["heat_index"] * 0.12
        + df["aqi_norm"] * 0.10
        + df["is_monsoon"] * 0.18
        + df["rainfall_7d_norm"] * 0.12
        + df["past_claims"] * 0.025
        + df["fraud_flags"] * 0.08
        - (df["iss_score"] / 100) * 0.20
        - df["consistency_score"] * 0.10
    ).clip(0.70, 1.60)
    return df


def build_real_premium_training_data() -> pd.DataFrame:
    db = get_supabase()

    quotes = (
        db.table("pricing_quotes")
        .select("id, worker_id, resolved_grid_id, resolved_city, quoted_at, feature_snapshot, premium_breakdown")
        .order("quoted_at", desc=True)
        .limit(5000)
        .execute()
        .data
        or []
    )
    workers = (
        db.table("workers")
        .select("id, persona, iss_score, active_days_per_week, peak_hour_ratio")
        .limit(5000)
        .execute()
        .data
        or []
    )
    claims = (
        db.table("claims")
        .select("worker_id, fraud_flags, created_at")
        .limit(10000)
        .execute()
        .data
        or []
    )
    disruptions = (
        db.table("disruption_events")
        .select("grid_id, city, severity, created_at")
        .limit(10000)
        .execute()
        .data
        or []
    )

    worker_map = {worker["id"]: worker for worker in workers}
    claim_counts: dict[str, int] = {}
    fraud_counts: dict[str, int] = {}
    for claim in claims:
        worker_id = claim.get("worker_id")
        if not worker_id:
            continue
        claim_counts[worker_id] = claim_counts.get(worker_id, 0) + 1
        fraud_counts[worker_id] = fraud_counts.get(worker_id, 0) + len(
            _parse_listish(claim.get("fraud_flags"))
        )

    disruption_pressure: dict[str, float] = {}
    disruption_counts: dict[str, int] = {}
    for disruption in disruptions:
        grid_id = disruption.get("grid_id")
        if not grid_id:
            continue
        disruption_counts[grid_id] = disruption_counts.get(grid_id, 0) + 1
        disruption_pressure[grid_id] = disruption_pressure.get(grid_id, 0.0) + _safe_float(
            disruption.get("severity"), 0.0
        )

    rows = []
    for quote in quotes:
        worker = worker_map.get(quote.get("worker_id"))
        if not worker:
            continue
        feature_snapshot = _parse_jsonish(quote.get("feature_snapshot"))
        premium_breakdown = _parse_jsonish(quote.get("premium_breakdown"))
        zone_multiplier = premium_breakdown.get("zone_multiplier")
        if zone_multiplier is None:
            continue

        grid_id = quote.get("resolved_grid_id")
        grid_disruption_count = disruption_counts.get(grid_id, 0)
        grid_disruption_pressure = disruption_pressure.get(grid_id, 0.0)

        rainfall_7d_norm = _safe_float(feature_snapshot.get("rainfall_7d_norm"))
        is_monsoon = 1 if rainfall_7d_norm >= 0.45 else 0
        is_festival = 1 if grid_disruption_count >= 8 and grid_disruption_pressure >= 6 else 0

        rows.append(
            {
                "flood_risk": _safe_float(feature_snapshot.get("flood_risk")),
                "heat_index": _safe_float(feature_snapshot.get("heat_index_norm")),
                "aqi_norm": _safe_float(feature_snapshot.get("aqi_norm")),
                "traffic_risk": _safe_float(feature_snapshot.get("traffic_risk")),
                "iss_score": _safe_float(worker.get("iss_score"), 50.0),
                "consistency_score": min(
                    max(_safe_float(worker.get("active_days_per_week"), 5.0) / 7.0, 0.0),
                    1.0,
                ),
                "active_days": _safe_float(worker.get("active_days_per_week"), 5.0),
                "peak_hour_ratio": _safe_float(worker.get("peak_hour_ratio"), 0.5),
                "is_monsoon": is_monsoon,
                "is_festival": is_festival,
                "past_claims": claim_counts.get(worker["id"], 0),
                "fraud_flags": fraud_counts.get(worker["id"], 0),
                "persona_hustler": 1 if worker.get("persona") == "hustler" else 0,
                "persona_opportunist": 1 if worker.get("persona") == "opportunist" else 0,
                "rainfall_7d_norm": rainfall_7d_norm,
                "multiplier": _safe_float(zone_multiplier),
            }
        )

    return pd.DataFrame(rows)


def train_premium_model():
    print("Training premium model...")
    try:
        real_df = build_real_premium_training_data()
    except Exception as exc:
        print(f"  Could not load real training history: {exc}")
        real_df = pd.DataFrame()
    real_rows = len(real_df)

    if real_rows >= 50:
        print(f"  Using {real_rows} real quote rows from Supabase")
        df = real_df.copy()
        if real_rows < 500:
            synthetic_needed = max(500 - real_rows, 0)
            if synthetic_needed:
                print(f"  Augmenting with {synthetic_needed} synthetic rows for stability")
                synthetic_df = generate_premium_training_data(synthetic_needed)
                df = pd.concat([df, synthetic_df], ignore_index=True)
    else:
        print("  Not enough real history yet, falling back to synthetic training data")
        df = generate_premium_training_data()

    features = PREMIUM_FEATURES
    model = XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.04,
        random_state=42,
    )
    model.fit(df[features], df["multiplier"])

    model_path = os.path.join(MODELS_DIR, "premium_model.joblib")
    features_path = os.path.join(MODELS_DIR, "premium_features.joblib")
    joblib.dump(model, model_path)
    joblib.dump(features, features_path)
    print(f"  Rows used: {len(df)}")
    print(f"  R² score: {model.score(df[features], df['multiplier']):.4f}")
    print(f"  Saved: {model_path}")
    print(f"  Saved: {features_path}")


def train_fraud_model():
    print("Training fraud detection model (Isolation Forest)...")
    np.random.seed(42)
    normal = np.random.normal(
        [500, 700, 4, 65, 1, 0], [200, 300, 1.5, 20, 0.8, 0.1], (2000, 6)
    )
    anomalous = np.random.normal(
        [2500, 300, 1, 25, 8, 3], [500, 100, 0.5, 10, 2, 1], (200, 6)
    )
    X = np.vstack([normal, anomalous])

    model = IsolationForest(
        n_estimators=200, contamination=0.09, random_state=42
    )
    model.fit(X)

    model_path = os.path.join(MODELS_DIR, "isolation_forest.joblib")
    joblib.dump(model, model_path)
    print(f"  Saved: {model_path}")


if __name__ == "__main__":
    train_premium_model()
    train_fraud_model()
    print("\n✅ All models saved to /models/")
