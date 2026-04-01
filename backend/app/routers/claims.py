"""
Claims Router — Claims history, detail view, manual trigger for demo.
"""

from fastapi import APIRouter, HTTPException
from app.database import get_supabase

router = APIRouter(prefix="/claims", tags=["claims"])


@router.get("/worker/{worker_id}")
async def get_worker_claims(worker_id: str, limit: int = 10):
    """Get claims for a worker."""
    db = get_supabase()
    result = (
        db.table("claims")
        .select("*, disruption_events(*)")
        .eq("worker_id", worker_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data or []


@router.get("/{claim_id}")
async def get_claim_detail(claim_id: str):
    """Get full claim details including simulation."""
    db = get_supabase()
    result = (
        db.table("claims")
        .select("*, disruption_events(*), payouts(*)")
        .eq("id", claim_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Claim not found")
    return result.data


@router.get("/payouts/{worker_id}")
async def get_worker_payouts(worker_id: str):
    """Get payout history for a worker."""
    db = get_supabase()
    result = (
        db.table("payouts")
        .select("*, claims(*)")
        .eq("worker_id", worker_id)
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )
    return result.data or []


@router.put("/{claim_id}/approve")
async def approve_claim(claim_id: str):
    """Manually approve a flagged claim (admin action)."""
    db = get_supabase()

    claim_res = (
        db.table("claims")
        .select("*")
        .eq("id", claim_id)
        .single()
        .execute()
    )
    if not claim_res.data:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim = claim_res.data

    # Update claim status
    db.table("claims").update({"status": "approved"}).eq(
        "id", claim_id
    ).execute()

    # If was soft_flagged, pay remaining 30%
    if claim["status"] == "soft_flagged" and claim["payout_amount"] > 0:
        remaining = round(claim["payout_amount"] * 0.30 / 0.70, 2)
        db.table("payouts").insert(
            {
                "claim_id": claim_id,
                "worker_id": claim["worker_id"],
                "amount": remaining,
                "status": "paid",
                "upi_id": "worker@upi",
                "mock_payout_id": f"TOPUP_{claim_id[:8]}",
            }
        ).execute()

    # ISS trust bonus
    db.table("workers").update(
        {"iss_score": min(claim.get("iss_score", 50) + 3, 100)}
    ).eq("id", claim["worker_id"]).execute()

    return {"message": "Claim approved", "claim_id": claim_id}


@router.put("/{claim_id}/reject")
async def reject_claim(claim_id: str):
    """Reject a flagged claim (admin action)."""
    db = get_supabase()

    claim_res = (
        db.table("claims")
        .select("*")
        .eq("id", claim_id)
        .single()
        .execute()
    )
    if not claim_res.data:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim = claim_res.data

    db.table("claims").update(
        {"status": "rejected", "payout_amount": 0}
    ).eq("id", claim_id).execute()

    # ISS penalty
    worker_res = (
        db.table("workers")
        .select("iss_score")
        .eq("id", claim["worker_id"])
        .single()
        .execute()
    )
    if worker_res.data:
        new_iss = max(worker_res.data["iss_score"] - 10, 0)
        db.table("workers").update({"iss_score": new_iss}).eq(
            "id", claim["worker_id"]
        ).execute()

    return {"message": "Claim rejected", "claim_id": claim_id}
