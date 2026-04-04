"""
Microgrids Router — Zone lookup by coordinates.
"""

from fastapi import APIRouter, HTTPException
from app.database import get_supabase
from app.services.live_grid_service import get_live_grid_detail, get_live_grids
from app.services.pricing_feature_service import refresh_grid_features
from app.utils.microgrid_utils import (
    find_grid_by_coordinates,
    get_city_by_name,
    get_grid_by_id,
    infer_city_from_coords,
    is_supported_city,
)

router = APIRouter(prefix="/microgrids", tags=["microgrids"])


@router.get("/lookup")
async def lookup_zone(lat: float, lng: float):
    """Find microgrid for given coordinates."""
    grid = find_grid_by_coordinates(lat, lng)
    if not grid:
        inferred_city = infer_city_from_coords(lat, lng)
        supported = is_supported_city(inferred_city)
        return {
            "grid": None,
            "risk_level": "Coverage Pending",
            "label": (
                f"Location detected near {inferred_city}. Local microgrid coverage is being expanded."
                if supported
                else "This location is outside the currently supported Phase 2 cities."
            ),
            "message": "No nearby supported microgrid found",
            "city": inferred_city,
            "is_supported_city": supported,
        }

    risk_level = "High Risk 🔴"
    if grid.get("composite_risk", 0) < 0.35:
        risk_level = "Low Risk 🟢"
    elif grid.get("composite_risk", 0) < 0.60:
        risk_level = "Medium Risk 🟡"

    return {
        "grid": grid,
        "risk_level": risk_level,
        "label": f"You're in {grid.get('city', 'Bengaluru')} Zone {grid['id']} — {risk_level}",
        "city": grid.get("city", "Bengaluru"),
        "is_supported_city": True,
    }


@router.get("/all")
async def get_all_grids():
    """Get all microgrids (for admin map)."""
    db = get_supabase()
    result = (
        db.table("microgrids")
        .select(
            "id, city, center_lat, center_lng, flood_risk, heat_index, "
            "aqi_avg, traffic_risk, social_risk, composite_risk"
        )
        .execute()
    )
    return result.data or []


@router.get("/live")
async def get_live_grid_status(city: str | None = None, active_only: bool = False):
    """Live grid state for admin and worker maps."""
    return get_live_grids(city=city, active_only=active_only)


@router.get("/{grid_id}/live-detail")
async def get_grid_live_detail(grid_id: str):
    """Detailed live grid state for map side panels."""
    detail = get_live_grid_detail(grid_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Grid not found")
    return detail


@router.post("/{grid_id}/refresh-live")
async def refresh_live_grid_detail(grid_id: str):
    """Force refresh a specific grid's live weather/AQI features."""
    grid = get_grid_by_id(grid_id)
    if not grid:
        raise HTTPException(status_code=404, detail="Grid not found")
    city_meta = get_city_by_name(grid.get("city", ""))
    if not city_meta:
        raise HTTPException(status_code=404, detail="Supported city metadata missing")
    await refresh_grid_features(grid, city_meta, force=True)
    detail = get_live_grid_detail(grid_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Grid not found after refresh")
    return detail


@router.get("/{grid_id}")
async def get_grid(grid_id: str):
    """Get specific microgrid."""
    db = get_supabase()
    result = (
        db.table("microgrids")
        .select("*")
        .eq("id", grid_id)
        .single()
        .execute()
    )
    return result.data
