"""
Premium Router — Dynamic premium calculation endpoint.
"""

from fastapi import APIRouter, HTTPException
from app.database import get_supabase
from app.services.pricing_quote_service import build_pricing_quote

router = APIRouter(prefix="/premium", tags=["premium"])


@router.get("/calculate/{worker_id}/{plan_id}")
async def calculate_premium_endpoint(worker_id: str, plan_id: str):
    """Calculate dynamic premium for a specific worker and plan."""
    db = get_supabase()

    worker_res = (
        db.table("workers")
        .select("*")
        .eq("id", worker_id)
        .single()
        .execute()
    )
    if not worker_res.data:
        raise HTTPException(status_code=404, detail="Worker not found")
    worker = worker_res.data

    plan_res = (
        db.table("plans")
        .select("*")
        .eq("id", plan_id)
        .single()
        .execute()
    )
    if not plan_res.data:
        raise HTTPException(status_code=404, detail="Plan not found")
    plan = plan_res.data

    try:
        quote = await build_pricing_quote(worker, plan)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return quote["breakdown"]
