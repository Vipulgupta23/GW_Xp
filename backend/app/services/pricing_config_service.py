from app.database import get_supabase


def get_active_pricing_config() -> dict:
    db = get_supabase()
    result = (
        db.table("pricing_config_versions")
        .select("*")
        .eq("is_active", True)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise RuntimeError(
            "No active pricing config found. Run bootstrap_live_pricing.py first."
        )
    row = result.data[0]
    config = row.get("config") or {}
    if isinstance(config, str):
        import json

        config = json.loads(config)
    config["version"] = row["version"]
    return config
