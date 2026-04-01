"""
OpenWeatherMap API Service — Free tier (1000 calls/day)
"""

import httpx
from app.config import settings

BASE_URL = "https://api.openweathermap.org/data/2.5"


async def get_current(lat: float, lng: float) -> dict:
    """Get current weather for coordinates."""
    if not settings.OPENWEATHER_API_KEY:
        return _mock_weather()

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{BASE_URL}/weather",
                params={
                    "lat": lat,
                    "lon": lng,
                    "appid": settings.OPENWEATHER_API_KEY,
                    "units": "metric",
                },
            )
            data = resp.json()

            rain_1h = data.get("rain", {}).get("1h", 0)
            rain_3h = data.get("rain", {}).get("3h", 0)

            return {
                "temp": data.get("main", {}).get("temp", 30),
                "humidity": data.get("main", {}).get("humidity", 60),
                "rain_1h": rain_1h,
                "rain_3h": rain_3h,
                "rain_6h": rain_3h * 2,  # estimate
                "wind_speed": data.get("wind", {}).get("speed", 5),
                "description": data.get("weather", [{}])[0].get(
                    "description", "clear"
                ),
                "icon": data.get("weather", [{}])[0].get("icon", "01d"),
            }
    except Exception as e:
        print(f"Weather API error: {e}")
        return _mock_weather()


async def get_forecast_7day(lat: float, lng: float) -> list:
    """Get 7-day forecast for disruption prediction."""
    if not settings.OPENWEATHER_API_KEY:
        return _mock_forecast()

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{BASE_URL}/forecast",
                params={
                    "lat": lat,
                    "lon": lng,
                    "appid": settings.OPENWEATHER_API_KEY,
                    "units": "metric",
                    "cnt": 40,  # 5-day forecast (3hr intervals)
                },
            )
            data = resp.json()
            forecasts = []
            for item in data.get("list", []):
                forecasts.append(
                    {
                        "dt": item["dt"],
                        "temp": item["main"]["temp"],
                        "rain_3h": item.get("rain", {}).get("3h", 0),
                        "description": item["weather"][0]["description"],
                    }
                )
            return forecasts
    except Exception as e:
        print(f"Forecast API error: {e}")
        return _mock_forecast()


async def get_rainfall_7d_avg(lat: float, lng: float) -> float:
    """Compute average rainfall over upcoming forecast period."""
    forecasts = await get_forecast_7day(lat, lng)
    if not forecasts:
        return 0.0
    total_rain = sum(f.get("rain_3h", 0) for f in forecasts)
    return total_rain / max(len(forecasts), 1) * 8  # daily avg estimate


def _mock_weather() -> dict:
    return {
        "temp": 32,
        "humidity": 65,
        "rain_1h": 0,
        "rain_3h": 0,
        "rain_6h": 0,
        "wind_speed": 8,
        "description": "partly cloudy",
        "icon": "02d",
    }


def _mock_forecast() -> list:
    import time

    return [
        {
            "dt": int(time.time()) + i * 10800,
            "temp": 30 + (i % 5),
            "rain_3h": 2.0 if i % 3 == 0 else 0,
            "description": "scattered clouds",
        }
        for i in range(8)
    ]
