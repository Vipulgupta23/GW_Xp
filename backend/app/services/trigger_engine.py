"""
Trigger Engine — APScheduler-based polling for weather/AQI disruptions.
Checks all active worker zones every 15 minutes.
"""

from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import get_supabase
from app.redis_client import get_redis
from app.services import weather_service, aqi_service
from app.services.claim_service import create_claim_for_disruption
from app.services.pricing_feature_service import refresh_grid_features
from app.utils.microgrid_utils import get_city_by_name

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")

TRIGGERS = [
    {
        "type": "heavy_rainfall",
        "param": "rain_6h",
        "threshold": 50,
        "unit": "mm",
        "payout_max": 500,
    },
    {
        "type": "extreme_heat",
        "param": "temp",
        "threshold": 44,
        "unit": "°C",
        "payout_max": 400,
    },
    {
        "type": "severe_aqi",
        "param": "aqi",
        "threshold": 400,
        "unit": "AQI",
        "payout_max": 350,
    },
    {
        "type": "flood_alert",
        "param": "flood_score",
        "threshold": 0.78,
        "unit": "score",
        "payout_max": 550,
    },
    {
        "type": "platform_outage",
        "param": "platform_outage_score",
        "threshold": 0.95,
        "unit": "score",
        "payout_max": 300,
        "manual_only": True,
    },
]


def get_6h_window() -> str:
    """Get current 6-hour window key for deduplication."""
    now = datetime.now(timezone.utc)
    window = now.hour // 6
    return f"{now.strftime('%Y%m%d')}_{window}"


def start_scheduler():
    """Start the trigger polling scheduler."""
    interval = settings.TRIGGER_POLL_INTERVAL_MINUTES

    @scheduler.scheduled_job("interval", minutes=interval, id="poll_zones")
    async def poll_all_zones():
        await _poll_all_zones()

    @scheduler.scheduled_job("interval", minutes=interval, id="refresh_live_features")
    async def refresh_live_features_job():
        await _refresh_active_grid_features()

    if not scheduler.running:
        scheduler.start()
        print(f"⏰ Trigger scheduler started (every {interval} min)")


async def _poll_all_zones():
    """Check weather + AQI for all grids with active workers."""
    db = get_supabase()
    redis = get_redis()

    # Get unique grids that have active insured workers
    workers_res = (
        db.table("workers")
        .select("grid_id")
        .eq("is_active", True)
        .execute()
    )
    grid_ids = list(
        set(w["grid_id"] for w in (workers_res.data or []) if w.get("grid_id"))
    )

    for grid_id in grid_ids:
        grid_res = (
            db.table("microgrids")
            .select("*")
            .eq("id", grid_id)
            .single()
            .execute()
        )
        grid = grid_res.data
        if not grid:
            continue

        weather = await weather_service.get_current(
            grid["center_lat"], grid["center_lng"]
        )
        aqi_val = await aqi_service.get_current(
            grid["center_lat"], grid["center_lng"]
        )

        measurements = {
            "rain_6h": weather.get("rain_6h", 0),
            "temp": weather.get("temp", 30),
            "aqi": aqi_val,
            "flood_score": max(
                grid.get("flood_risk", 0),
                min(1.0, weather.get("rain_6h", 0) / 60),
            ),
            "platform_outage_score": 0.0,
        }

        for trigger in TRIGGERS:
            if trigger.get("manual_only"):
                continue
            value = measurements.get(trigger["param"], 0)
            if value >= trigger["threshold"]:
                dedup_key = (
                    f"trigger:{grid_id}:{trigger['type']}:{get_6h_window()}"
                )
                if not redis.exists(dedup_key):
                    redis.set(dedup_key, "1", ex=21600)  # 6hr TTL
                    await create_disruption_and_claims(
                        grid, trigger, value, weather
                    )


async def _refresh_active_grid_features():
    """Refresh live pricing features for active worker grids."""
    db = get_supabase()
    workers_res = (
        db.table("workers")
        .select("grid_id")
        .eq("is_active", True)
        .execute()
    )
    grid_ids = list(
        set(w["grid_id"] for w in (workers_res.data or []) if w.get("grid_id"))
    )
    for grid_id in grid_ids:
        grid_res = (
            db.table("microgrids")
            .select("*")
            .eq("id", grid_id)
            .single()
            .execute()
        )
        grid = grid_res.data
        if not grid:
            continue
        city_meta = get_city_by_name(grid.get("city", ""))
        if not city_meta:
            continue
        try:
            await refresh_grid_features(grid, city_meta, force=True)
        except Exception as e:
            print(f"⚠️  Feature refresh failed for {grid_id}: {e}")


async def create_disruption_and_claims(
    grid: dict, trigger: dict, measured_value: float, raw_weather: dict
):
    """Create a disruption event and process claims for all affected workers."""
    db = get_supabase()

    # 1. Create disruption event
    disruption_data = {
        "trigger_type": trigger["type"],
        "grid_id": grid["id"],
        "city": grid.get("city", "Bengaluru"),
        "severity": measured_value,
        "threshold": trigger["threshold"],
        "weather_description": raw_weather.get("description", ""),
        "is_active": True,
        "raw_data": raw_weather,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    disruption_res = (
        db.table("disruption_events").insert(disruption_data).execute()
    )
    disruption = disruption_res.data[0] if disruption_res.data else None
    if not disruption:
        print(f"❌ Failed to create disruption: {trigger['type']}")
        return

    # 2. Get all insured workers in this grid
    workers_res = (
        db.table("workers")
        .select("*")
        .eq("grid_id", grid["id"])
        .eq("is_active", True)
        .execute()
    )

    for worker in workers_res.data or []:
        # Check worker has active policy
        policy_res = (
            db.table("policies")
            .select("*, plans(*)")
            .eq("worker_id", worker["id"])
            .eq("status", "active")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if not policy_res.data:
            continue

        policy = policy_res.data[0]
        plan = policy.get("plans", {})
        await _process_claim(worker, disruption, trigger, policy, plan)


async def _process_claim(
    worker: dict,
    disruption: dict,
    trigger: dict,
    policy: dict,
    plan: dict,
):
    """Full Zero-Touch pipeline — no worker action needed."""
    claim = create_claim_for_disruption(
        worker,
        disruption,
        policy,
        plan,
        claim_origin="auto",
    )
    if not claim:
        return
    print(
        f"  ✅ Claim {claim.get('status', 'processing')} for {worker.get('name', 'worker')}: ₹{claim.get('payout_amount', 0)}"
    )
