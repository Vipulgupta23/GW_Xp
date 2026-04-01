"""
Auth Router — Supabase Email OTP verification + profile fetch.
"""

import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.config import settings
from app.database import get_supabase, get_supabase_anon

router = APIRouter(prefix="/auth", tags=["auth"])


# Development-only OTP cache for local testing when Supabase throttles OTP emails.
_DEV_OTP_TTL_SECONDS = 600
_DEV_OTP_CODE = "123456"
_dev_otp_cache: dict[str, tuple[str, float]] = {}


def _is_rate_limit_error(message: str) -> bool:
    normalized = message.lower()
    return "rate limit" in normalized or "too many requests" in normalized


def _store_dev_otp(email: str) -> None:
    _dev_otp_cache[email] = (_DEV_OTP_CODE, time.time() + _DEV_OTP_TTL_SECONDS)


def _validate_dev_otp(email: str, otp: str) -> bool:
    entry = _dev_otp_cache.get(email)
    if not entry:
        return False
    code, expires_at = entry
    if time.time() > expires_at:
        _dev_otp_cache.pop(email, None)
        return False
    return otp == code


def _get_worker_by_email(email: str):
    db = get_supabase()
    try:
        worker_res = (
            db.table("workers")
            .select("*")
            .eq("email", email)
            .limit(1)
            .execute()
        )
        return worker_res.data[0] if worker_res.data else None
    except Exception:
        # Schema may not be initialized yet in local development.
        return None


class SendOTPRequest(BaseModel):
    email: str


class VerifyOTPRequest(BaseModel):
    email: str
    otp: str


@router.post("/send-otp")
async def send_otp(req: SendOTPRequest):
    """Send OTP to email."""
    email = req.email.strip().lower()
    auth_client = get_supabase_anon()

    try:
        auth_client.auth.sign_in_with_otp({"email": email})
        return {
            "success": True,
            "message": "OTP sent successfully",
            "email_hint": email,  # For demo debugging
        }
    except Exception as e:
        error_message = str(e)
        if settings.ENVIRONMENT == "development" and _is_rate_limit_error(error_message):
            _store_dev_otp(email)
            return {
                "success": True,
                "message": "Supabase OTP rate-limited. Using development OTP fallback.",
                "email_hint": email,
                "dev_otp": _DEV_OTP_CODE,
            }
        status = 429 if _is_rate_limit_error(error_message) else 400
        raise HTTPException(status_code=status, detail=error_message)


@router.post("/verify-otp")
async def verify_otp(req: VerifyOTPRequest):
    """Verify OTP and return session."""
    email = req.email.strip().lower()
    auth_client = get_supabase_anon()

    if settings.ENVIRONMENT == "development" and _validate_dev_otp(email, req.otp):
        worker = _get_worker_by_email(email)
        return {
            "success": True,
            "access_token": f"dev-session-{email}",
            "user_id": None,
            "worker": worker,
            "is_new": worker is None,
        }

    try:
        result = auth_client.auth.verify_otp(
            {"email": email, "token": req.otp, "type": "email"}
        )

        session = result.session
        user = result.user

        if not session:
            raise HTTPException(status_code=401, detail="Invalid OTP")

        worker = _get_worker_by_email(email)

        return {
            "success": True,
            "access_token": session.access_token,
            "user_id": user.id if user else None,
            "worker": worker,
            "is_new": worker is None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/profile/{worker_id}")
async def get_profile(worker_id: str):
    """Get worker profile."""
    db = get_supabase()
    result = (
        db.table("workers")
        .select("*")
        .eq("id", worker_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Worker not found")
    return result.data
