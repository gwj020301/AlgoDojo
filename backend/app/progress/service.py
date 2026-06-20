"""Progress service: status state machine + overall/per-topic statistics."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import ProblemStatus, Verdict
from app.models import Problem, Topic, UserProblemStatus
from app.progress.schemas import ProgressOut, TopicProgress


async def update_user_problem_status(
    session: AsyncSession, user_id: uuid.UUID, problem_id: int, verdict: str
) -> str:
    """Apply the progress state machine for one judged submission.

    Transitions (requirements 5.2/5.3):
    - first AC  -> passed (terminal; never downgraded)
    - any non-AC -> in_progress (unless already passed)

    Returns the resulting status. Does not commit (caller controls the txn).
    """
    row = (
        await session.execute(
            select(UserProblemStatus).where(
                UserProblemStatus.user_id == user_id,
                UserProblemStatus.problem_id == problem_id,
            )
        )
    ).scalar_one_or_none()

    if row is None:
        row = UserProblemStatus(
            user_id=user_id, problem_id=problem_id, status=ProblemStatus.NOT_STARTED
        )
        session.add(row)

    if row.status == ProblemStatus.PASSED:
        return row.status  # passed is terminal

    new_status = ProblemStatus.PASSED if verdict == Verdict.AC else ProblemStatus.IN_PROGRESS
    if new_status != row.status:
        row.status = new_status
        row.updated_at = datetime.now(timezone.utc)
    await session.flush()
    return row.status


async def compute_progress(session: AsyncSession, user_id: uuid.UUID) -> ProgressOut:
    """Overall + per-topic completion stats (requirement 5.4)."""
    # Total problems per topic.
    topic_totals = dict(
        (
            await session.execute(
                select(Problem.topic_id, func.count(Problem.id)).group_by(Problem.topic_id)
            )
        ).all()
    )

    # Passed problems per topic (join status -> problem).
    passed_rows = (
        await session.execute(
            select(Problem.topic_id, func.count(Problem.id))
            .join(UserProblemStatus, UserProblemStatus.problem_id == Problem.id)
            .where(
                UserProblemStatus.user_id == user_id,
                UserProblemStatus.status == ProblemStatus.PASSED,
            )
            .group_by(Problem.topic_id)
        )
    ).all()
    topic_passed = dict(passed_rows)

    # Overall in-progress count.
    in_progress = (
        await session.execute(
            select(func.count())
            .select_from(UserProblemStatus)
            .where(
                UserProblemStatus.user_id == user_id,
                UserProblemStatus.status == ProblemStatus.IN_PROGRESS,
            )
        )
    ).scalar_one()

    topics = list((await session.execute(select(Topic).order_by(Topic.order_index))).scalars())
    topic_progress: list[TopicProgress] = []
    total_all = 0
    passed_all = 0
    for topic in topics:
        total = int(topic_totals.get(topic.id, 0))
        passed = int(topic_passed.get(topic.id, 0))
        total_all += total
        passed_all += passed
        if total == 0:
            continue
        topic_progress.append(
            TopicProgress(
                topic_id=topic.id,
                topic_name=topic.name,
                total=total,
                passed=passed,
                completion_rate=round(passed / total, 4),
            )
        )

    return ProgressOut(
        total_problems=total_all,
        passed=passed_all,
        in_progress=int(in_progress),
        completion_rate=round(passed_all / total_all, 4) if total_all else 0.0,
        topics=topic_progress,
    )
