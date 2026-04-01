"""
Workers Router — Registration, onboarding, platform linking.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.database import get_supabase
from app.utils.microgrid_utils import find_grid_by_coordinates, infer_city_from_coords
from app.ml.persona_classifier import classify_persona

router = APIRouter(prefix="/workers", tags=["workers"])


class RegisterRequest(BaseModel):
    email: str
    name: str
    phone: Optional[str] = None
    platform: str  # zomato, swiggy, zepto, amazon
    zone_lat: float = 12.9352
    zone_lng: float = 77.6245
    city: Optional[str] = "Bengaluru"


class LinkPlatformRequest(BaseModel):
    worker_id: str
    platform_worker_id: str


@router.post("/register")
async def register_worker(req: RegisterRequest):
    """Register a new worker during onboarding."""
    db = get_supabase()

    # Check if worker already exists
    existing = (
        db.table("workers")
        .select("id")
        .eq("email", req.email)
        .limit(1)
        .execute()
    )
    if existing.data:
        return {"worker": existing.data[0], "message": "Worker already exists"}

    # Find microgrid via PostGIS
    grid = find_grid_by_coordinates(req.zone_lat, req.zone_lng)
    grid_id = grid["id"] if grid else None
    detected_city = grid.get("city") if grid else infer_city_from_coords(req.zone_lat, req.zone_lng)

    # Classify initial persona (defaults for new worker)
    persona = classify_persona(
        avg_hours_per_day=8.0,
        peak_hour_ratio=0.5,
        consistency=0.5,
    )

    worker_data = {
        "email": req.email,
        "name": req.name,
        "phone": req.phone,
        "platform": req.platform,
        "zone_lat": req.zone_lat,
        "zone_lng": req.zone_lng,
        "grid_id": grid_id,
        "city": req.city or detected_city,
        "persona": persona,
        "iss_score": 50.0,
        "is_verified": False,
        "is_active": True,
        "avg_daily_earnings": 900.0,
        "avg_hourly_earnings": 90.0,
        "active_days_per_week": 5.0,
        "peak_hour_ratio": 0.5,
    }

    result = db.table("workers").insert(worker_data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create worker")

    worker = result.data[0]

    # Create initial ISS history entry
    db.table("iss_history").insert(
        {
            "worker_id": worker["id"],
            "iss_score": 50.0,
            "consistency_score": 50.0,
            "regularity_score": 50.0,
            "zone_score": 60.0,
            "fraud_score_component": 100.0,
            "delta": 0,
        }
    ).execute()

    return {
        "worker": worker,
        "grid": grid,
        "message": "Worker registered successfully",
    }


@router.post("/link-platform")
async def link_platform(req: LinkPlatformRequest):
    """Mock platform linking — simulates Zomato/Swiggy verification."""
    db = get_supabase()

    # Simulate verification (mock — always succeeds)
    import random

    deliveries = random.randint(200, 1500)
    rating = round(random.uniform(3.8, 4.9), 1)

    db.table("workers").update(
        {
            "platform_worker_id": req.platform_worker_id,
            "is_verified": True,
        }
    ).eq("id", req.worker_id).execute()

    return {
        "verified": True,
        "deliveries_on_record": deliveries,
        "platform_rating": rating,
        "message": f"Verified ✅ — {deliveries} deliveries on record",
    }


@router.get("/{worker_id}")
async def get_worker(worker_id: str):
    """Get worker details."""
    db = get_supabase()
    result = (
        db.table("workers")
        .select("*")
        .eq("id", worker_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Worker not found")
    return result.data


@router.get("/{worker_id}/iss-history")
async def get_iss_history(worker_id: str):
    """Get ISS score history."""
    db = get_supabase()
    result = (
        db.table("iss_history")
        .select("*")
        .eq("worker_id", worker_id)
        .order("calculated_at", desc=True)
        .limit(30)
        .execute()
    )
    return result.data or []
