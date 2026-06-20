"""Worker tests: process_submission writes back verdicts; SE retries; process_next.

Uses in-memory SQLite (StaticPool) and a fake judge function — no Docker/Redis.
"""

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from app.constants import SubmissionStatus
from app.models import Base, Problem, Submission, TestCase, Topic, User
from app.submissions import worker
from dojo_judge import DockerNotAvailableError, FailedCase, JudgeResult, Limits, Verdict
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool


@pytest_asyncio.fixture
async def factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    await engine.dispose()


async def _seed_submission(
    factory, *, language: str = "python", code: str = "print(1)", sample_only: bool = False
) -> uuid.UUID:
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
        s.add_all(
            [
                TestCase(problem_id=problem.id, input="2 3", expected_output="5", is_sample=True),
                TestCase(problem_id=problem.id, input="1 1", expected_output="2"),
            ]
        )
        user = User(github_id=1, username="u")
        s.add(user)
        await s.flush()
        sub = Submission(
            user_id=user.id,
            problem_id=problem.id,
            language=language,
            code=code,
            status=SubmissionStatus.QUEUED,
            sample_only=sample_only,
        )
        s.add(sub)
        await s.commit()
        return sub.id


def _fake_judge(result: JudgeResult):
    def fn(language, code, cases, limits):
        # Sanity: cases are passed through from the DB test cases.
        assert len(cases) == 2
        return result

    return fn


async def _status(factory, sid) -> Submission:
    async with factory() as s:
        return await s.get(Submission, sid)


async def test_accepted_verdict_written_back(factory) -> None:
    sid = await _seed_submission(factory)
    result = JudgeResult(verdict=Verdict.AC, runtime_ms=12, cases_total=2, cases_passed=2)
    async with factory() as s:
        outcome = await worker.process_submission(s, sid, _fake_judge(result), limits=Limits())
    assert outcome == worker.PROCESSED_DONE
    sub = await _status(factory, sid)
    assert sub.status == SubmissionStatus.DONE
    assert sub.verdict == "AC"
    assert sub.runtime_ms == 12
    assert sub.failed_case is None


async def test_wrong_answer_stores_failed_case(factory) -> None:
    sid = await _seed_submission(factory)
    fc = FailedCase(index=1, input="1 1", expected="2", actual="3")
    result = JudgeResult(
        verdict=Verdict.WA,
        runtime_ms=5,
        failed_index=1,
        failed_case=fc,
        cases_total=2,
        cases_passed=1,
    )
    async with factory() as s:
        await worker.process_submission(s, sid, _fake_judge(result))
    sub = await _status(factory, sid)
    assert sub.status == SubmissionStatus.DONE
    assert sub.verdict == "WA"
    assert sub.failed_case["actual"] == "3"
    assert sub.failed_case["index"] == 1


@pytest.mark.parametrize("verdict", [Verdict.TLE, Verdict.MLE, Verdict.CE, Verdict.RE])
async def test_other_verdicts_written_back(factory, verdict) -> None:
    sid = await _seed_submission(factory)
    result = JudgeResult(verdict=verdict, detail="some detail", cases_total=2)
    async with factory() as s:
        await worker.process_submission(s, sid, _fake_judge(result))
    sub = await _status(factory, sid)
    assert sub.status == SubmissionStatus.DONE
    assert sub.verdict == verdict
    assert sub.detail == "some detail"


async def test_system_error_verdict_retries_then_fails(factory) -> None:
    sid = await _seed_submission(factory)
    se = JudgeResult(verdict=Verdict.SE, detail="boom")

    # attempt 1 of 2 -> retry (back to queued)
    async with factory() as s:
        outcome = await worker.process_submission(
            s, sid, _fake_judge(se), attempt=1, max_attempts=2
        )
    assert outcome == worker.PROCESSED_RETRY
    assert (await _status(factory, sid)).status == SubmissionStatus.QUEUED

    # attempt 2 of 2 -> final system_error
    async with factory() as s:
        outcome = await worker.process_submission(
            s, sid, _fake_judge(se), attempt=2, max_attempts=2
        )
    assert outcome == worker.PROCESSED_FAILED
    assert (await _status(factory, sid)).status == SubmissionStatus.SYSTEM_ERROR


async def test_docker_unavailable_is_handled_as_system_error(factory) -> None:
    sid = await _seed_submission(factory)

    def raising_judge(language, code, cases, limits):
        raise DockerNotAvailableError("no docker")

    async with factory() as s:
        outcome = await worker.process_submission(s, sid, raising_judge, attempt=2, max_attempts=2)
    assert outcome == worker.PROCESSED_FAILED
    assert (await _status(factory, sid)).status == SubmissionStatus.SYSTEM_ERROR


async def test_engine_crash_is_handled_as_system_error(factory) -> None:
    sid = await _seed_submission(factory)

    def crashing_judge(language, code, cases, limits):
        raise RuntimeError("unexpected")

    async with factory() as s:
        outcome = await worker.process_submission(s, sid, crashing_judge, attempt=2, max_attempts=2)
    assert outcome == worker.PROCESSED_FAILED


async def test_missing_submission_returns_missing(factory) -> None:
    async with factory() as s:
        outcome = await worker.process_submission(
            s, uuid.uuid4(), _fake_judge(JudgeResult(verdict=Verdict.AC))
        )
    assert outcome == worker.PROCESSED_MISSING


def test_parse_task() -> None:
    assert worker._parse_task("abc") == ("abc", 1)
    assert worker._parse_task("abc|3") == ("abc", 3)
    assert worker._parse_task("abc|bad") == ("abc", 1)


async def test_sample_only_runs_only_sample_cases_and_skips_progress(factory) -> None:
    from app.constants import ProblemStatus
    from app.models import UserProblemStatus
    from sqlalchemy import select

    sid = await _seed_submission(factory, sample_only=True)

    seen_case_counts: list[int] = []

    def fn(language, code, cases, limits):
        seen_case_counts.append(len(cases))  # should be 1 (only the sample case)
        return JudgeResult(
            verdict=Verdict.AC, runtime_ms=3, cases_total=len(cases), cases_passed=len(cases)
        )

    async with factory() as s:
        outcome = await worker.process_submission(s, sid, fn)
    assert outcome == worker.PROCESSED_DONE
    assert seen_case_counts == [1]  # only the is_sample=True case was judged

    sub = await _status(factory, sid)
    assert sub.verdict == "AC"

    # A sample-only run must NOT create/update progress.
    async with factory() as s:
        rows = (await s.execute(select(UserProblemStatus))).scalars().all()
    passed = [r for r in rows if r.status == ProblemStatus.PASSED]
    assert passed == []
