"""
Income Stability Score (ISS) Calculator — 0 to 100
The "credit score" for gig worker income stability.
"""

import numpy as np
from app.database import get_supabase


def calculate_iss(worker_id: str) -> dict:
    """Calculate ISS from last 30 days of earning records."""
    db = get_supabase()

    # Get earning records
    result = (
        db.table("earning_records")
        .select("*")
        .eq("worker_id", worker_id)
        .order("record_date", desc=True)
        .limit(750)  # ~30 days × 24 hours
        .execute()
    )
    records = result.data if result.data else []

    # Get worker's grid
    worker_result = (
        db.table("workers")
        .select("grid_id")
        .eq("id", worker_id)
        .single()
        .execute()
    )
    grid_id = worker_result.data.get("grid_id") if worker_result.data else None

    grid = {}
    if grid_id:
        grid_result = (
            db.table("microgrids")
            .select("composite_risk")
            .eq("id", grid_id)
            .single()
            .execute()
        )
        grid = grid_result.data if grid_result.data else {}

    # Get fraud count
    fraud_result = (
        db.table("claims")
        .select("id", count="exact")
        .eq("worker_id", worker_id)
        .eq("fraud_layer1_pass", False)
        .execute()
    )
    fraud_count = fraud_result.count if fraud_result.count else 0

    # ── Consistency: low variance in daily earnings = high score ──
    earnings = [
        r["earnings"]
        for r in records
        if r.get("was_active") and r.get("earnings", 0) > 0
    ]
    if len(earnings) >= 5:
        mean_e = np.mean(earnings)
        cv = np.std(earnings) / (mean_e + 1)
        consistency = max(0, 1 - min(cv, 1))
    else:
        consistency = 0.50  # default for new workers

    # ── Regularity: active days / 25 expected ──
    active_dates = set(
        r["record_date"] for r in records if r.get("was_active")
    )
    active_days = len(active_dates)
    regularity = min(active_days / 25, 1.0)

    # ── Zone score: inverse of composite risk ──
    zone_score = 1 - grid.get("composite_risk", 0.4)

    # ── Fraud history ──
    fraud_component = max(0, 1 - (fraud_count * 0.25))

    iss = (
        consistency * 0.40
        + regularity * 0.30
        + zone_score * 0.20
        + fraud_component * 0.10
    ) * 100

    return {
        "iss_score": round(iss, 1),
        "consistency": round(consistency * 100, 1),
        "regularity": round(regularity * 100, 1),
        "zone": round(zone_score * 100, 1),
        "trust": round(fraud_component * 100, 1),
    }
