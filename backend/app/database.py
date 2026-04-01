from supabase import create_client, Client
from app.config import settings

_supabase_client: Client | None = None


def get_supabase() -> Client:
    """Get or create Supabase client using service role key for full DB access."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
            or settings.SUPABASE_ANON_KEY,
        )
    return _supabase_client


def get_supabase_anon() -> Client:
    """Get Supabase client with anon key (for auth operations)."""
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY,
    )
