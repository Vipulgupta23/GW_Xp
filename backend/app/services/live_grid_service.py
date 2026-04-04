from datetime import datetime, timezone
from typing import Any

from app.database import get_supabase


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _is_fresh(expires_at: str | None) -> bool:
    expires = _parse_dt(expires_at)
    return bool(expires and expires > datetime.now(timezone.utc))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _build_premium_impact(snapshot: dict[str, Any]) -> str:
    flood = _safe_float(snapshot.get("flood_risk"))
    aqi = _safe_float(snapshot.get("aqi_norm"))
    traffic = _safe_float(snapshot.get("traffic_risk"))
    seasonal = _safe_float(snapshot.get("seasonal_factor"), 1.0)
    if flood < 0.18 and seasonal < 1.0:
        return "Premium tailwind: safer-than-usual waterlogging conditions"
    if flood >= 0.55 or seasonal >= 1.18:
        return "Premium pressure: live weather risk is elevated in this zone"
    if aqi >= 0.65 or traffic >= 0.7:
        return "Premium watch: AQI and route stress are pushing risk upward"
    return "Premium steady: live risk is moderate in this zone"


def _build_grid_state(snapshot: dict[str, Any], has_disruption: bool, freshness_status: str) -> tuple[str, str, str, int]:
    if has_disruption:
        return ("active_disruption", "Active disruption", "#ef4444", 92)
    if freshness_status != "fresh":
        return ("stale", "Stale live data", "#64748b", 35)

    flood = _safe_float(snapshot.get("flood_risk"))
    aqi = _safe_float(snapshot.get("aqi_norm"))
    heat = _safe_float(snapshot.get("heat_index_norm"))
    traffic = _safe_float(snapshot.get("traffic_risk"))
    score = max(flood, aqi, heat, traffic)

    if score >= 0.72:
        return ("elevated_live_risk", "Elevated live risk", "#f97316", 76)
    if score >= 0.38:
        return ("moderate_live_risk", "Moderate live risk", "#fbbf24", 52)
    return ("calm", "Calm", "#10b981", 22)


def _fetch_workers_and_policies(grid_ids: list[str]) -> tuple[dict[str, int], dict[str, int]]:
    db = get_supabase()
    workers = (
        db.table("workers")
        .select("id, grid_id")
        .eq("is_active", True)
        .execute()
    ).data or []
    active_policies = (
        db.table("policies")
        .select("worker_id")
        .eq("status", "active")
        .execute()
    ).data or []
    active_worker_ids = {row["worker_id"] for row in active_policies if row.get("worker_id")}

    worker_counts: dict[str, int] = {}
    insured_counts: dict[str, int] = {}
    allowed_grid_ids = set(grid_ids)
    for worker in workers:
        grid_id = worker.get("grid_id")
        if not grid_id or grid_id not in allowed_grid_ids:
            continue
        worker_counts[grid_id] = worker_counts.get(grid_id, 0) + 1
        if worker.get("id") in active_worker_ids:
            insured_counts[grid_id] = insured_counts.get(grid_id, 0) + 1
    return worker_counts, insured_counts


def _build_grid_entry(
    grid: dict[str, Any],
    feature_row: dict[str, Any] | None,
    disruptions: list[dict[str, Any]],
    worker_count: int,
    insured_count: int,
) -> dict[str, Any]:
    snapshot = (feature_row or {}).get("feature_snapshot") or {}
    freshness_status = "fresh" if feature_row and _is_fresh(feature_row.get("expires_at")) else "stale"
    if feature_row and feature_row.get("source_status") == "stale":
        freshness_status = "stale"

    state, state_label, map_color, risk_percent = _build_grid_state(
        snapshot,
        bool(disruptions),
        freshness_status,
    )
    latest_disruption = disruptions[0] if disruptions else None
    trigger_origin = ((latest_disruption or {}).get("raw_data") or {}).get("trigger_origin")

    return {
        "id": grid["id"],
        "city": grid.get("city"),
        "center_lat": grid.get("center_lat"),
        "center_lng": grid.get("center_lng"),
        "feature_snapshot": snapshot,
        "feature_freshness": {
            "status": freshness_status,
            "observed_at": (feature_row or {}).get("observed_at"),
            "expires_at": (feature_row or {}).get("expires_at"),
        },
        "live_state": state,
        "state_label": state_label,
        "map_color": map_color,
        "risk_percent": risk_percent,
        "insured_worker_count": insured_count,
        "worker_count": worker_count,
        "active_disruption_count": len(disruptions),
        "active_disruptions": disruptions,
        "latest_disruption": latest_disruption,
        "trigger_origin": trigger_origin,
        "premium_impact_label": _build_premium_impact(snapshot),
    }


def get_live_grids(city: str | None = None, active_only: bool = False) -> list[dict[str, Any]]:
    db = get_supabase()
    grid_query = db.table("microgrids").select("*")
    if city:
        grid_query = grid_query.eq("city", city)
    grids = grid_query.limit(5000).execute().data or []
    if not grids:
        return []

    grid_ids = [grid["id"] for grid in grids]
    allowed_grid_ids = set(grid_ids)
    feature_rows = db.table("microgrid_features_current").select("*").execute().data or []
    disruptions = (
        db.table("disruption_events")
        .select("*")
        .eq("is_active", True)
        .order("started_at", desc=True)
        .execute()
    ).data or []
    worker_counts, insured_counts = _fetch_workers_and_policies(grid_ids)

    feature_map = {
        row["grid_id"]: row
        for row in feature_rows
        if row.get("grid_id") in allowed_grid_ids
    }
    disruptions_map: dict[str, list[dict[str, Any]]] = {}
    for disruption in disruptions:
        grid_id = disruption.get("grid_id")
        if grid_id in allowed_grid_ids:
            disruptions_map.setdefault(grid_id, []).append(disruption)

    live_rows = [
        _build_grid_entry(
            grid,
            feature_map.get(grid["id"]),
            disruptions_map.get(grid["id"], []),
            worker_counts.get(grid["id"], 0),
            insured_counts.get(grid["id"], 0),
        )
        for grid in grids
    ]
    if active_only:
        live_rows = [
            row
            for row in live_rows
            if row["active_disruption_count"] > 0 or row["insured_worker_count"] > 0
        ]
    return live_rows


def get_live_grid_detail(grid_id: str) -> dict[str, Any] | None:
    rows = get_live_grids()
    return next((row for row in rows if row["id"] == grid_id), None)
