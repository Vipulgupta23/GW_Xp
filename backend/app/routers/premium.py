"""
Premium Router — Dynamic premium calculation endpoint.
"""

from fastapi import APIRouter, HTTPException
from app.database import get_supabase
from app.ml.premium_engine import calculate_premium
from app.utils.microgrid_utils import get_grid_by_id
from app.services import weather_service

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

    grid = get_grid_by_id(worker.get("grid_id", "BLR_05_05"))
    if not grid:
        grid = {
            "flood_risk": 0.3,
            "heat_index": 0.4,
            "aqi_avg": 120,
            "traffic_risk": 0.4,
            "composite_risk": 0.35,
            "city": "Bengaluru",
        }

    rainfall_avg = await weather_service.get_rainfall_7d_avg(
        grid.get("center_lat", 12.93), grid.get("center_lng", 77.62)
    )

    result = calculate_premium(worker, plan, grid, rainfall_avg)
    return result
