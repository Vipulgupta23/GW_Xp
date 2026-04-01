"""
Earning Simulator — Hour-by-hour breakdown of what worker
WOULD have earned vs what they actually earned during disruption.
"""


def calculate(worker: dict, disruption: dict) -> dict:
    """Build hour-by-hour earning simulation."""

    started_at = disruption.get("started_at")
    if isinstance(started_at, str):
        from datetime import datetime

        try:
            started_at = datetime.fromisoformat(
                started_at.replace("Z", "+00:00")
            )
        except Exception:
            started_at = datetime.now()

    start_hour = started_at.hour if started_at else 12
    disruption_hours = 4  # assume 4-hour disruption
    end_hour = min(start_hour + disruption_hours, 22)

    PEAK_HOURS = [11, 12, 13, 19, 20, 21, 22]
    avg_hourly = worker.get("avg_hourly_earnings", 90)
    avg_delivery_value = max(avg_hourly / max(avg_hourly / 45, 1), 30)

    # Disruption severity factor
    severity = disruption.get("severity", 50)
    threshold = disruption.get("threshold", 50)
    severity_ratio = severity / max(threshold, 1)
    disruption_factor = max(0.05, 1 - (severity_ratio - 1) * 0.6)

    hourly_breakdown = []
    simulated_total = 0
    actual_total = 0

    for hour in range(start_hour, end_hour + 1):
        is_peak = hour in PEAK_HOURS
        surge = 1.30 if is_peak else 1.0

        # Expected (without disruption)
        deliveries_expected = round(
            (avg_hourly * surge) / max(avg_delivery_value, 1)
        )
        earnings_expected = round(
            deliveries_expected * avg_delivery_value * surge, 2
        )

        # Actual (with disruption)
        deliveries_actual = round(deliveries_expected * disruption_factor)
        earnings_actual = round(earnings_expected * disruption_factor, 2)

        heavily_disrupted = disruption_factor < 0.20

        hourly_breakdown.append(
            {
                "hour_label": f"{hour}:00 – {hour + 1}:00",
                "is_peak": is_peak,
                "deliveries_expected": deliveries_expected,
                "earnings_expected": earnings_expected,
                "deliveries_actual": deliveries_actual,
                "earnings_actual": earnings_actual,
                "disrupted": heavily_disrupted,
                "surge_label": "🔥 Surge" if is_peak else "",
            }
        )

        simulated_total += earnings_expected
        actual_total += earnings_actual

    return {
        "simulated_earnings": round(simulated_total, 2),
        "actual_earnings": round(actual_total, 2),
        "income_gap": round(simulated_total - actual_total, 2),
        "disruption_hours": disruption_hours,
        "hourly_breakdown": hourly_breakdown,
        "disruption_factor": round(disruption_factor, 3),
    }
