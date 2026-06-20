"""Problem bank service: grouped listing with status, detail, and history."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import ProblemStatus
from app.models import Problem, Submission, TestCase, Topic, UserProblemStatus
from app.problems.schemas import (
    ProblemDetail,
    ProblemListItem,
    SampleCase,
    SubmissionSummary,
    TopicGroup,
)


async def _status_map(session: AsyncSession, user_id: uuid.UUID) -> dict[int, str]:
    """Map problem_id -> status for a user (missing => not_started)."""
    rows = await session.execute(
        select(UserProblemStatus.problem_id, UserProblemStatus.status).where(
            UserProblemStatus.user_id == user_id
        )
    )
    return dict(rows.all())


async def list_problems_grouped(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    topic_id: int | None = None,
    difficulty: str | None = None,
    status: str | None = None,
) -> list[TopicGroup]:
    """List problems grouped by topic, annotated with the user's status.

    Supports filtering by topic, difficulty, and status (requirement 2.5).
    Empty groups (after filtering) are dropped.
    """
    topics = list((await session.execute(select(Topic).order_by(Topic.order_index))).scalars())

    query = select(Problem).order_by(Problem.number)
    if topic_id is not None:
        query = query.where(Problem.topic_id == topic_id)
    if difficulty is not None:
        query = query.where(Problem.difficulty == difficulty)
    problems = list((await session.execute(query)).scalars())

    status_by_problem = await _status_map(session, user_id)

    items_by_topic: dict[int, list[ProblemListItem]] = {}
    for p in problems:
        p_status = status_by_problem.get(p.id, ProblemStatus.NOT_STARTED)
        if status is not None and p_status != status:
            continue
        items_by_topic.setdefault(p.topic_id, []).append(
            ProblemListItem(
                id=p.id,
                number=p.number,
                title=p.title,
                difficulty=p.difficulty,
                languages=p.languages or [],
                status=p_status,
            )
        )

    groups: list[TopicGroup] = []
    for topic in topics:
        items = items_by_topic.get(topic.id, [])
        if not items:
            continue
        groups.append(
            TopicGroup(
                topic_id=topic.id,
                topic_name=topic.name,
                order_index=topic.order_index,
                problems=items,
            )
        )
    return groups


async def get_problem_detail(
    session: AsyncSession, user_id: uuid.UUID, problem_id: int
) -> ProblemDetail | None:
    """Return a problem's detail (with templates) annotated with user status."""
    problem = await session.get(Problem, problem_id)
    if problem is None:
        return None
    topic = await session.get(Topic, problem.topic_id)
    status_by_problem = await _status_map(session, user_id)
    sample_rows = (
        await session.execute(
            select(TestCase)
            .where(TestCase.problem_id == problem_id, TestCase.is_sample.is_(True))
            .order_by(TestCase.id)
        )
    ).scalars()
    samples = [
        SampleCase(input=tc.input, expected_output=tc.expected_output) for tc in sample_rows
    ]
    return ProblemDetail(
        id=problem.id,
        number=problem.number,
        title=problem.title,
        description=problem.description,
        difficulty=problem.difficulty,
        topic_id=problem.topic_id,
        topic_name=topic.name if topic else "",
        languages=problem.languages or [],
        templates=problem.templates or {},
        status=status_by_problem.get(problem.id, ProblemStatus.NOT_STARTED),
        samples=samples,
    )


async def list_problem_submissions(
    session: AsyncSession, user_id: uuid.UUID, problem_id: int
) -> list[SubmissionSummary]:
    """Return the user's own submission history for a problem (newest first)."""
    rows = await session.execute(
        select(Submission)
        .where(Submission.user_id == user_id, Submission.problem_id == problem_id)
        .order_by(Submission.created_at.desc())
    )
    return [
        SubmissionSummary(
            id=s.id,
            language=s.language,
            status=s.status,
            verdict=s.verdict,
            runtime_ms=s.runtime_ms,
            created_at=s.created_at,
        )
        for s in rows.scalars()
    ]
