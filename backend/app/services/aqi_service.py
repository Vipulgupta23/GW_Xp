"""
AQICN API Service — Free tier (unlimited calls)
"""

import httpx
from app.config import settings

BASE_URL = "https://api.waqi.info"


async def get_current(lat: float, lng: float) -> float:
    """Get current AQI for coordinates. Returns AQI number."""
    if not settings.AQICN_API_KEY:
        return _mock_aqi()

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{BASE_URL}/feed/geo:{lat};{lng}/",
                params={"token": settings.AQICN_API_KEY},
            )
            data = resp.json()
            if data.get("status") == "ok":
                return float(data["data"]["aqi"])
            return _mock_aqi()
    except Exception as e:
        print(f"AQI API error: {e}")
        return _mock_aqi()


def _mock_aqi() -> float:
    """Mock AQI for development."""
    import random

    return float(random.randint(80, 180))
