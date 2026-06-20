"""Redis client (async) used for the judge task queue and result cache."""

from redis.asyncio import Redis

from app.config import get_settings

_settings = get_settings()

redis_client: Redis = Redis.from_url(
    _settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
)


async def check_redis() -> bool:
    """Return True if Redis responds to PING."""
    return await redis_client.ping()
