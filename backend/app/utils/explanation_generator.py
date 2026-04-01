"""
Template-Based Hinglish Explanation Generator
No external AI API needed — uses smart templates with claim data.
"""

import random

TRIGGER_LABELS = {
    "heavy_rainfall": ("baarish", "🌧️"),
    "extreme_heat": ("garmi", "🌡️"),
    "severe_aqi": ("pollution", "😷"),
    "flood_alert": ("baadh", "🌊"),
    "platform_outage": ("app outage", "📵"),
    "cyclone": ("toofaan", "🌪️"),
}

TEMPLATES = [
    "{emoji} Aaj {trigger} ki wajah se {hours} ghante kaam nahi hua. "
    "Normally ₹{sim} milta, lekin sirf ₹{actual} mila — isliye "
    "Incometrix ne ₹{payout} seedha aapke UPI mein bhej diya!",
    "{emoji} {name} bhai, {trigger} ki wajah se earning drop hua. "
    "₹{gap} ka nuksaan hua, to Incometrix ne {pct}% cover karke "
    "₹{payout} bhej diya. 💪",
    "{emoji} Aaj {trigger} ne {hours} ghante roka. Income gap tha "
    "₹{gap} — coverage ke baad ₹{payout} aapka account mein hai. "
    "Bas karo delivery, baaki hum sambhal lete hain!",
    "{emoji} {name}, {trigger} ki wajah se {hours} ghante ka kaam "
    "ruk gaya. Aapka expected earning tha ₹{sim} lekin mila sirf "
    "₹{actual}. Incometrix ne ₹{payout} instantly transfer kar diya! 🚀",
]


def generate_explanation(
    worker: dict,
    simulation: dict,
    payout: float,
    trigger_type: str,
) -> str:
    """Generate a Hinglish explanation for the claim payout."""
    label, emoji = TRIGGER_LABELS.get(trigger_type, ("disruption", "⚠️"))
    name = worker.get("name", "Bhai").split()[0] if worker.get("name") else "Bhai"
    template = random.choice(TEMPLATES)

    return template.format(
        emoji=emoji,
        trigger=label,
        name=name,
        hours=simulation.get("disruption_hours", 4),
        sim=int(simulation.get("simulated_earnings", 0)),
        actual=int(simulation.get("actual_earnings", 0)),
        gap=int(simulation.get("income_gap", 0)),
        payout=int(payout),
        pct=int(worker.get("coverage_pct", 0.70) * 100),
    )
