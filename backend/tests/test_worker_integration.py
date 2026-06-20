"""Full-chain integration test: enqueue -> Redis -> worker consume -> DB writeback.

Uses a REAL Redis (queue) but a fake judge (the Docker judge is covered by the
judge package's own integration tests) and in-memory SQLite for the DB. Skipped
unless ``REDIS_TEST_URL`` points at a reachable Redis.

    REDIS_TEST_URL=redis://localhost:56379/0 uv run pytest -m integration
"""

import os
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from app.constants import SubmissionStatus
from app.models import Base, Problem, Submission, TestCase, Topic, User
from app.submissions import queue, worker
from app.submissions.service import create_submission
from dojo_judge import JudgeResult, Verdict
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

pytestmark = pytest.mark.integration

REDIS_URL = os.environ.get("REDIS_TEST_URL", "redis://localhost:56379/0")


async def _redis_ok(url: str) -> bool:
    try:
        r = Redis.from_url(url, decode_responses=True)
        await r.ping()
        await r.aclose()
        return True
    except Exception:
        return False


@pytest_asyncio.fixture
async def redis() -> AsyncGenerator[Redis, None]:
    if not await _redis_ok(REDIS_URL):
        pytest.skip(f"Redis not reachable at {REDIS_URL}")
    r = Redis.from_url(REDIS_URL, decode_responses=True)
    # Clean the queue before/after.
    from app.config import get_settings

    await r.delete(get_settings().judge_queue_key)
    yield r
    await r.delete(get_settings().judge_queue_key)
    await r.aclose()


@pytest_asyncio.fixture
async def factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    await engine.dispose()


async def _seed(factory) -> uuid.UUID:
    async with factory() as s:
        topic = Topic(name="哈希", order_index=0)
        s.add(topic)
        await s.flush()
        problem = Problem(
            number=1,
            title="t",
            description="d",
            topic_id=topic.id,
            difficulty="easy",
            languages=["python"],
            templates={},
        )
        s.add(problem)
        await s.flush()
        s.add(TestCase(problem_id=problem.id, input="2 3", expected_output="5", is_sample=True))
        user = User(github_id=1, username="u")
        s.add(user)
        await s.flush()
        sub = await create_submission(
            s, user_id=user.id, problem_id=problem.id, language="python", code="print(5)"
        )
        return sub.id


def _judge_returning(result: JudgeResult):
    def fn(language, code, cases, limits):
        return result

    return fn


async def test_full_chain_enqueue_consume_writeback(redis, factory) -> None:
    sid = await _seed(factory)

    # API side: enqueue the queued submission.
    await queue.enqueue_submission(redis, str(sid))
    assert await queue.queue_depth(redis) == 1

    # Worker side: consume one task and judge it (fake AC).
    ac = JudgeResult(verdict=Verdict.AC, runtime_ms=7, cases_total=1, cases_passed=1)
    processed = await worker.process_next(redis, factory, _judge_returning(ac), timeout=5)
    assert processed == str(sid)
    assert await queue.queue_depth(redis) == 0  # consumed

    async with factory() as s:
        sub = await s.get(Submission, sid)
        assert sub.status == SubmissionStatus.DONE
        assert sub.verdict == "AC"
        assert sub.runtime_ms == 7


async def test_full_chain_system_error_requeues_then_fails(redis, factory) -> None:
    sid = await _seed(factory)
    await queue.enqueue_submission(redis, str(sid))

    se = JudgeResult(verdict=Verdict.SE, detail="boom")

    # First consume -> SE -> requeue as "<id>|2".
    await worker.process_next(redis, factory, _judge_returning(se), timeout=5)
    async with factory() as s:
        assert (await s.get(Submission, sid)).status == SubmissionStatus.QUEUED
    assert await queue.queue_depth(redis) == 1  # requeued

    # Second consume -> attempt 2 -> final system_error, queue drained.
    await worker.process_next(redis, factory, _judge_returning(se), timeout=5)
    async with factory() as s:
        assert (await s.get(Submission, sid)).status == SubmissionStatus.SYSTEM_ERROR
    assert await queue.queue_depth(redis) == 0
