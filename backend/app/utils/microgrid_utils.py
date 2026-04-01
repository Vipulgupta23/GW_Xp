"""
Microgrid Utilities — PostGIS zone lookup helpers
"""

import math

from app.database import get_supabase


def infer_city_from_coords(lat: float, lng: float) -> str:
    """Infer major Indian city name from coordinates (coarse bounding boxes)."""
    if 12.7 <= lat <= 13.3 and 80.0 <= lng <= 80.4:
        return "Chennai"
    if 12.8 <= lat <= 13.2 and 77.4 <= lng <= 77.8:
        return "Bengaluru"
    if 17.2 <= lat <= 17.7 and 78.2 <= lng <= 78.7:
        return "Hyderabad"
    if 18.8 <= lat <= 19.4 and 72.7 <= lng <= 73.1:
        return "Mumbai"
    if 28.4 <= lat <= 28.9 and 76.9 <= lng <= 77.5:
        return "Delhi NCR"
    return "Your City"


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def find_grid_by_coordinates(lat: float, lng: float) -> dict | None:
    """Find which microgrid contains the given coordinates using PostGIS."""
    db = get_supabase()

    # Use PostGIS ST_Contains to find the grid
    result = db.rpc(
        "find_grid_by_point",
        {"p_lat": lat, "p_lng": lng},
    ).execute()

    if result.data and len(result.data) > 0:
        return result.data[0]

    # Fallback: find nearest grid by center distance
    result = (
        db.table("microgrids")
        .select("*")
        .order("center_lat")
        .limit(225)
        .execute()
    )
    if not result.data:
        return None

    # Find closest grid by great-circle distance.
    best = None
    best_dist = float("inf")
    for grid in result.data:
        dist = _haversine_km(lat, lng, grid["center_lat"], grid["center_lng"])
        if dist < best_dist:
            best_dist = dist
            best = grid

    # Prevent mapping distant cities (for example Chennai) into Bengaluru grids.
    if best is None or best_dist > 35:
        return None
    return best


def get_grid_by_id(grid_id: str) -> dict | None:
    """Get a specific microgrid by ID."""
    db = get_supabase()
    try:
        result = (
            db.table("microgrids")
            .select("*")
            .eq("id", grid_id)
            .limit(1)
            .execute()
        )
        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception:
        return None
