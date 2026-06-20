"""Judge worker: consume submissions from the queue and write back verdicts.

Layered for testability:

- ``process_submission``: judge one submission against an injected ``judge_fn``
  (no Redis). The unit tests drive this with a fake judge.
- ``process_next``: pop one id from an injected Redis + session factory, then
  call ``process_submission``. Handles retry/requeue.
- ``run_worker``: production loop — N concurrent consumers using the app's Redis
  client and session factory.

Concurrency is bounded by the number of consumer coroutines (``judge_concurrency``);
excess submissions wait in the Redis queue rather than being rejected
(requirement 4.10). A sandbox/infra failure marks the submission ``system_error``
and is retried up to ``judge_max_attempts`` times (design.md error handling).

Logging is sanitized: we never log user code, tokens, or full error bodies —
only ids, verdicts, and attempt counts.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Callable
from dataclasses import asdict

from dojo_judge import (
    DockerNotAvailableError,
    JudgeResult,
    Limits,
    TestCaseSpec,
    Verdict,
    judge,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.constants import SubmissionStatus
from app.db import async_session_factory
from app.models import Problem, Submission
from app.progress.service import update_user_problem_status
from app.redis_client import redis_client
from app.submissions import queue

logger = logging.getLogger("algodojo.judge.worker")

# A judge function: (language, code, cases, limits) -> JudgeResult. Synchronous
# (the real one shells out to Docker); the worker runs it in a thread.
JudgeFn = Callable[[str, str, list[TestCaseSpec], Limits], JudgeResult]

# Outcome of processing one submission.
PROCESSED_DONE = "done"
PROCESSED_RETRY = "retry"
PROCESSED_FAILED = "system_error"
PROCESSED_MISSING = "missing"


def default_judge_fn(
    language: str, code: str, cases: list[TestCaseSpec], limits: Limits
) -> JudgeResult:
    """Real judge: run the sandbox container image from settings."""
    return judge(language, code, cases, limits, image=get_settings().judge_image)


def _limits() -> Limits:
    s = get_settings()
    return Limits(time_limit_s=s.judge_time_limit_s, memory_limit_mb=s.judge_memory_limit_mb)


async def process_submission(
    session: AsyncSession,
    submission_id: uuid.UUID,
    judge_fn: JudgeFn,
    *,
    limits: Limits | None = None,
    attempt: int = 1,
    max_attempts: int | None = None,
) -> str:
    """Judge one submission and write the result back.

    Returns one of PROCESSED_DONE / PROCESSED_RETRY / PROCESSED_FAILED /
    PROCESSED_MISSING.
    """
    settings = get_settings()
    limits = limits or _limits()
    max_attempts = max_attempts or settings.judge_max_attempts

    submission = (
        await session.execute(
            select(Submission)
            .where(Submission.id == submission_id)
            .options(selectinload(Submission.problem).selectinload(Problem.test_cases))
        )
    ).scalar_one_or_none()
    if submission is None:
        logger.warning("submission %s not found; skipping", submission_id)
        return PROCESSED_MISSING

    submission.status = SubmissionStatus.RUNNING
    await session.commit()

    problem = submission.problem
    all_cases = problem.test_cases
    # "运行(自测样例)" only judges sample cases; "提交" judges all.
    selected = [tc for tc in all_cases if tc.is_sample] if submission.sample_only else all_cases
    cases = [
        TestCaseSpec(input=tc.input, expected_output=tc.expected_output, is_sample=tc.is_sample)
        for tc in selected
    ]

    try:
        result: JudgeResult = await asyncio.to_thread(
            judge_fn, submission.language, submission.code, cases, limits
        )
    except DockerNotAvailableError as exc:
        return await _handle_failure(
            session, submission, attempt, max_attempts, reason=f"sandbox unavailable: {exc}"
        )
    except Exception:  # noqa: BLE001 - any unexpected engine failure is a system error
        logger.exception("judge engine crashed for submission %s", submission_id)
        return await _handle_failure(
            session, submission, attempt, max_attempts, reason="judge engine error"
        )

    if result.verdict == Verdict.SE:
        return await _handle_failure(
            session, submission, attempt, max_attempts, reason="judge reported system error"
        )

    # Normal verdict (AC/WA/TLE/MLE/CE/RE) -> done.
    submission.status = SubmissionStatus.DONE
    submission.verdict = result.verdict
    submission.runtime_ms = result.runtime_ms
    submission.failed_case = asdict(result.failed_case) if result.failed_case else None
    submission.detail = result.detail or None

    # Update the user's per-problem progress (first AC -> passed, else in_progress).
    # Self-test runs ("运行") never affect progress.
    if not submission.sample_only:
        await update_user_problem_status(
            session, submission.user_id, submission.problem_id, result.verdict
        )

    await session.commit()
    logger.info(
        "submission %s judged: verdict=%s runtime_ms=%s",
        submission_id,
        result.verdict,
        result.runtime_ms,
    )
    return PROCESSED_DONE


async def _handle_failure(
    session: AsyncSession,
    submission: Submission,
    attempt: int,
    max_attempts: int,
    *,
    reason: str,
) -> str:
    """Mark a submission for retry or as final system_error."""
    if attempt < max_attempts:
        submission.status = SubmissionStatus.QUEUED
        await session.commit()
        logger.warning(
            "submission %s failed (%s); retry %d/%d",
            submission.id,
            reason,
            attempt + 1,
            max_attempts,
        )
        return PROCESSED_RETRY

    submission.status = SubmissionStatus.SYSTEM_ERROR
    submission.detail = "判题系统错误，请稍后重试。"
    await session.commit()
    logger.error("submission %s gave up after %d attempts (%s)", submission.id, attempt, reason)
    return PROCESSED_FAILED


def _parse_task(value: str) -> tuple[str, int]:
    """Parse a queue value 'id' or 'id|attempt' into (id, attempt)."""
    if "|" in value:
        sid, _, attempt = value.partition("|")
        try:
            return sid, int(attempt)
        except ValueError:
            return sid, 1
    return value, 1


async def process_next(
    redis,
    session_factory: async_sessionmaker[AsyncSession],
    judge_fn: JudgeFn,
    *,
    limits: Limits | None = None,
    timeout: int = 5,
) -> str | None:
    """Pop one task and process it. Returns the submission id, or None on timeout."""
    value = await queue.dequeue_submission(redis, timeout=timeout)
    if value is None:
        return None

    sid, attempt = _parse_task(value)
    try:
        submission_id = uuid.UUID(sid)
    except ValueError:
        logger.error("invalid submission id in queue: %r", sid)
        return None

    settings = get_settings()
    async with session_factory() as session:
        outcome = await process_submission(
            session,
            submission_id,
            judge_fn,
            limits=limits,
            attempt=attempt,
            max_attempts=settings.judge_max_attempts,
        )
    if outcome == PROCESSED_RETRY:
        await redis.lpush(settings.judge_queue_key, f"{sid}|{attempt + 1}")
    return sid


async def _consumer(name: int, judge_fn: JudgeFn) -> None:
    logger.info("judge consumer %d started", name)
    while True:
        try:
            await process_next(redis_client, async_session_factory, judge_fn)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - keep the consumer alive on any error
            logger.exception("consumer %d loop error", name)
            await asyncio.sleep(1)


async def run_worker(concurrency: int | None = None, judge_fn: JudgeFn = default_judge_fn) -> None:
    """Run N concurrent judge consumers forever (production entrypoint)."""
    n = concurrency or get_settings().judge_concurrency
    logger.info("starting judge worker with concurrency=%d", n)
    await asyncio.gather(*[_consumer(i, judge_fn) for i in range(n)])


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
