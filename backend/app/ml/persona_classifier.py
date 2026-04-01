"""
Persona Classifier — Hustler / Stabilizer / Opportunist
"""


def classify_persona(
    avg_hours_per_day: float,
    peak_hour_ratio: float,
    consistency: float,
) -> str:
    """
    Classify worker persona based on behavioral patterns.

    Hustler:      High hours (9+), inconsistent schedule
    Stabilizer:   Fixed hours, consistent
    Opportunist:  Low total hours but high peak concentration
    """
    if avg_hours_per_day >= 9 and consistency < 0.65:
        return "hustler"
    elif peak_hour_ratio > 0.68 and avg_hours_per_day < 7.5:
        return "opportunist"
    else:
        return "stabilizer"
