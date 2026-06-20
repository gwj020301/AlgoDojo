"""Redis-backed judge task queue.

The queue is a Redis list: submissions are pushed on the left (LPUSH) and the
worker pops them from the right (BRPOP) — a simple, durable FIFO. Backpressure
is automatic: if judging is slower than submission, tasks wait in the list
rather than being rejected (requirement 4.10).

Only the submission id travels through the queue; all submission data lives in
PostgreSQL (the source of truth for status/verdict).
"""

from __future__ import annotations

from redis.asyncio import Redis

from app.config import get_settings


def _queue_key() -> str:
    return get_settings().judge_queue_key


async def enqueue_submission(redis: Redis, submission_id: str) -> None:
    """Push a submission id onto the judge queue."""
    await redis.lpush(_queue_key(), submission_id)


async def dequeue_submission(redis: Redis, timeout: int = 5) -> str | None:
    """Block up to ``timeout`` seconds for the next submission id, or None."""
    result = await redis.brpop([_queue_key()], timeout=timeout)
    if result is None:
        return None
    # brpop returns (key, value); with decode_responses=True these are str.
    _key, value = result
    return value


async def queue_depth(redis: Redis) -> int:
    """Return the number of tasks currently waiting in the queue."""
    return await redis.llen(_queue_key())
