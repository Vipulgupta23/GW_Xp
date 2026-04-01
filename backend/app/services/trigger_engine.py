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
from app.ml import earning_simulator, fraud_engine
from app.utils.explanation_generator import generate_explanation

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
        }

        for trigger in TRIGGERS:
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
    db = get_supabase()

    # Layer-1 support checks from database context.
    existing_claim_res = (
        db.table("claims")
        .select("id")
        .eq("worker_id", worker["id"])
        .eq("disruption_id", disruption["id"])
        .limit(1)
        .execute()
    )
    has_duplicate_claim = bool(existing_claim_res.data)

    policy_after_event = False
    try:
        policy_start = datetime.fromisoformat(f"{policy['start_date']}T00:00:00+00:00")
        disruption_started = datetime.fromisoformat(
            disruption["started_at"].replace("Z", "+00:00")
        )
        policy_after_event = policy_start > disruption_started
    except Exception:
        policy_after_event = False

    # Fraud Layer 1
    l1 = fraud_engine.run_fraud_layer1(
        worker,
        disruption,
        has_duplicate_claim=has_duplicate_claim,
        policy_after_event=policy_after_event,
    )

    # Earning simulation
    sim = earning_simulator.calculate(worker, disruption)

    # Payout calculation
    coverage_pct = plan.get("coverage_pct", 0.70)
    max_weekly = plan.get("max_weekly_payout", 2500)
    income_gap = sim["income_gap"]
    payout = min(income_gap * coverage_pct, max_weekly)
    payout = max(round(payout, 2), 0)

    # Fraud Layer 2
    l2 = fraud_engine.run_fraud_layer2(worker, sim, income_gap)

    # Fraud Layer 3 (Isolation Forest)
    l3 = fraud_engine.run_fraud_layer3(
        payout, income_gap, sim["disruption_hours"], worker
    )

    # Determine status
    if not l1["pass"]:
        status = "hard_flagged"
        final_payout = 0
    elif not l2["pass"] or not l3["pass"]:
        status = "soft_flagged"
        final_payout = round(payout * 0.70, 2)
    else:
        status = "approved"
        final_payout = payout

    # Worker info with coverage for explanation
    worker_for_explain = {**worker, "coverage_pct": coverage_pct}

    # Generate Hinglish explanation
    explanation = generate_explanation(
        worker_for_explain, sim, final_payout, trigger["type"]
    )

    # Compute fraud score 0-1
    all_flags = l1["flags"] + l2["flags"] + l3["flags"]
    fraud_score = min(len(all_flags) * 0.25, 1.0)

    # Save claim
    claim_data = {
        "worker_id": worker["id"],
        "policy_id": policy["id"],
        "disruption_id": disruption["id"],
        "trigger_type": trigger["type"],
        "status": status,
        "actual_earnings": sim["actual_earnings"],
        "simulated_earnings": sim["simulated_earnings"],
        "income_gap": income_gap,
        "payout_amount": final_payout,
        "coverage_pct": coverage_pct,
        "fraud_score": fraud_score,
        "fraud_layer1_pass": l1["pass"],
        "fraud_layer2_pass": l2["pass"],
        "fraud_layer3_pass": l3["pass"],
        "fraud_flags": all_flags,
        "earning_simulation": sim,
        "hinglish_explanation": explanation,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }
    claim_res = db.table("claims").insert(claim_data).execute()
    claim = claim_res.data[0] if claim_res.data else None
    if not claim:
        return

    # Create payout if approved or soft_flagged
    if final_payout > 0:
        payout_data = {
            "claim_id": claim["id"],
            "worker_id": worker["id"],
            "amount": final_payout,
            "upi_id": "worker@upi",
            "status": "paid",
            "mock_payout_id": f"MOCK_PAY_{claim['id'][:8]}",
            "paid_at": datetime.now(timezone.utc).isoformat(),
            "whatsapp_shown": False,
        }
        db.table("payouts").insert(payout_data).execute()

        # Update claim to paid
        db.table("claims").update({"status": "paid"}).eq(
            "id", claim["id"]
        ).execute()

    print(
        f"  ✅ Claim {status} for {worker.get('name', 'worker')}: ₹{final_payout}"
    )
