"""
Train XGBoost premium model and Isolation Forest fraud model.
Run once: python -m scripts.train_models (from backend/)
"""

import os
import sys
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.ensemble import IsolationForest
import joblib

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
os.makedirs(MODELS_DIR, exist_ok=True)


# ─── PREMIUM MODEL ───
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
    # Target: premium multiplier (0.70 to 1.60)
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


def train_premium_model():
    print("Training premium model...")
    df = generate_premium_training_data()
    features = [c for c in df.columns if c != "multiplier"]
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
    print(f"  R² score: {model.score(df[features], df['multiplier']):.4f}")
    print(f"  Saved: {model_path}")
    print(f"  Saved: {features_path}")


# ─── ISOLATION FOREST (Fraud Layer 3) ───
def train_fraud_model():
    print("Training fraud detection model (Isolation Forest)...")
    np.random.seed(42)
    # Normal claims: [payout, income_gap, disruption_hours, iss_score, past_claims, fraud_flags]
    normal = np.random.normal(
        [500, 700, 4, 65, 1, 0], [200, 300, 1.5, 20, 0.8, 0.1], (2000, 6)
    )
    # Anomalous claims (fraudsters)
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
