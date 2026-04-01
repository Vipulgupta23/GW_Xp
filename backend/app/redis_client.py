from upstash_redis import Redis
from app.config import settings

_redis_client: Redis | None = None


def get_redis() -> Redis:
    """Get or create Upstash Redis client."""
    global _redis_client
    if _redis_client is None:
        if settings.UPSTASH_REDIS_REST_URL and settings.UPSTASH_REDIS_REST_TOKEN:
            _redis_client = Redis(
                url=settings.UPSTASH_REDIS_REST_URL,
                token=settings.UPSTASH_REDIS_REST_TOKEN,
            )
        else:
            # Return a dummy redis for development without Redis
            _redis_client = DummyRedis()
    return _redis_client


class DummyRedis:
    """Fallback Redis that stores in memory — for local dev without Upstash."""

    def __init__(self):
        self._store: dict = {}

    def get(self, key: str):
        return self._store.get(key)

    def set(self, key: str, value: str, ex: int = None):
        self._store[key] = value
        return True

    def exists(self, key: str) -> bool:
        return key in self._store

    def delete(self, key: str):
        self._store.pop(key, None)
        return True
