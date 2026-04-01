"""
Admin Router — Stats, claims queue, fraud list, simulate disruption.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta

from app.database import get_supabase
from app.services.trigger_engine import (
    create_disruption_and_claims,
    TRIGGERS,
)

router = APIRouter(prefix="/admin", tags=["admin"])


class SimulateTriggerRequest(BaseModel):
    trigger_type: str
    grid_id: str
    severity: float
    description: Optional[str] = None


@router.get("/stats")
async def get_admin_stats():
    """Get overview statistics for admin dashboard."""
    db = get_supabase()

    # Total active workers
    workers_res = (
        db.table("workers")
        .select("id", count="exact")
        .eq("is_active", True)
        .execute()
    )
    total_workers = workers_res.count or 0

    # Active disruptions
    disruptions_res = (
        db.table("disruption_events")
        .select("id", count="exact")
        .eq("is_active", True)
        .execute()
    )
    active_disruptions = disruptions_res.count or 0

    # Claims today
    today = datetime.now(timezone.utc).date().isoformat()
    claims_res = (
        db.table("claims")
        .select("id, payout_amount")
        .gte("created_at", today)
        .execute()
    )
    claims_today = len(claims_res.data) if claims_res.data else 0
    total_payout_today = sum(
        c.get("payout_amount", 0) for c in (claims_res.data or [])
    )

    # Fraud alerts pending
    fraud_res = (
        db.table("claims")
        .select("id", count="exact")
        .in_("status", ["hard_flagged", "soft_flagged"])
        .execute()
    )
    fraud_alerts = fraud_res.count or 0

    # Active policies
    policies_res = (
        db.table("policies")
        .select("id", count="exact")
        .eq("status", "active")
        .execute()
    )
    active_policies = policies_res.count or 0

    return {
        "total_workers": total_workers,
        "active_disruptions": active_disruptions,
        "claims_today": claims_today,
        "total_payout_today": round(total_payout_today, 2),
        "fraud_alerts": fraud_alerts,
        "active_policies": active_policies,
    }


@router.get("/claims-queue")
async def get_claims_queue(limit: int = 50):
    """Get recent claims for admin review."""
    db = get_supabase()
    result = (
        db.table("claims")
        .select("*, workers(name, platform, grid_id), disruption_events(trigger_type, severity)")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data or []


@router.get("/fraud-list")
async def get_fraud_list():
    """Get all flagged claims requiring review."""
    db = get_supabase()
    result = (
        db.table("claims")
        .select("*, workers(name, platform, iss_score, grid_id)")
        .in_("status", ["hard_flagged", "soft_flagged"])
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


@router.get("/disruptions")
async def get_active_disruptions():
    """Get all active disruption events."""
    db = get_supabase()
    result = (
        db.table("disruption_events")
        .select("*")
        .eq("is_active", True)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


@router.get("/disruptions/history")
async def get_disruption_history(days: int = 7):
    """Get disruption history."""
    db = get_supabase()
    since = (
        datetime.now(timezone.utc) - timedelta(days=days)
    ).isoformat()
    result = (
        db.table("disruption_events")
        .select("*")
        .gte("created_at", since)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


@router.get("/daily-stats")
async def get_daily_stats(days: int = 7):
    """Get daily claims and payout stats for charts."""
    db = get_supabase()
    since = (
        datetime.now(timezone.utc) - timedelta(days=days)
    ).isoformat()

    claims_res = (
        db.table("claims")
        .select("created_at, payout_amount, status")
        .gte("created_at", since)
        .order("created_at")
        .execute()
    )

    # Group by date
    daily = {}
    for claim in claims_res.data or []:
        date = claim["created_at"][:10]
        if date not in daily:
            daily[date] = {"date": date, "claims": 0, "payout": 0}
        daily[date]["claims"] += 1
        daily[date]["payout"] += claim.get("payout_amount", 0)

    return list(daily.values())


@router.post("/simulate-trigger")
async def simulate_trigger(req: SimulateTriggerRequest):
    """🔴 Demo-only: Manually fire a disruption trigger."""
    db = get_supabase()

    # Get grid
    grid_res = (
        db.table("microgrids")
        .select("*")
        .eq("id", req.grid_id)
        .single()
        .execute()
    )
    if not grid_res.data:
        raise HTTPException(status_code=404, detail=f"Grid {req.grid_id} not found")
    grid = grid_res.data

    # Find matching trigger
    trigger = None
    for t in TRIGGERS:
        if t["type"] == req.trigger_type:
            trigger = t
            break
    if not trigger:
        # Allow custom trigger types for demo
        trigger = {
            "type": req.trigger_type,
            "param": "custom",
            "threshold": req.severity * 0.8,
            "unit": "",
            "payout_max": 500,
        }

    raw_weather = {
        "simulated": True,
        "description": req.description or f"Simulated {req.trigger_type}",
        "temp": 35,
        "rain_6h": req.severity if "rain" in req.trigger_type else 0,
    }

    await create_disruption_and_claims(grid, trigger, req.severity, raw_weather)

    return {
        "message": f"🔴 Trigger {req.trigger_type} fired for grid {req.grid_id}",
        "severity": req.severity,
        "grid": grid["id"],
    }
