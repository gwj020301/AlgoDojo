"""Roadmap service: ordered topics with pattern summary, progress, recommended order."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import ProblemStatus
from app.learning.schemas import RoadmapProblem, RoadmapTopic
from app.models import Problem, RoadmapNode, Topic, UserProblemStatus


async def get_roadmap(session: AsyncSession, user_id: uuid.UUID) -> list[RoadmapTopic]:
    """Build the learning roadmap: topics in difficulty order, each with its
    pattern summary, completion progress, and recommended problem sequence
    (requirements 6.1-6.4)."""
    nodes = list(
        (
            await session.execute(
                select(RoadmapNode, Topic)
                .join(Topic, Topic.id == RoadmapNode.topic_id)
                .order_by(RoadmapNode.order_index)
            )
        ).all()
    )

    status_by_problem = dict(
        (
            await session.execute(
                select(UserProblemStatus.problem_id, UserProblemStatus.status).where(
                    UserProblemStatus.user_id == user_id
                )
            )
        ).all()
    )

    # Total problems per topic.
    topic_totals = dict(
        (
            await session.execute(
                select(Problem.topic_id, func.count(Problem.id)).group_by(Problem.topic_id)
            )
        ).all()
    )

    out: list[RoadmapTopic] = []
    for node, topic in nodes:
        # Load recommended problems in the stored order.
        rec_ids: list[int] = node.recommended_problem_ids or []
        problems_by_id = {
            p.id: p
            for p in (
                await session.execute(select(Problem).where(Problem.id.in_(rec_ids)))
            ).scalars()
        }
        rec_problems: list[RoadmapProblem] = []
        passed = 0
        for pid in rec_ids:
            p = problems_by_id.get(pid)
            if p is None:
                continue
            st = status_by_problem.get(pid, ProblemStatus.NOT_STARTED)
            if st == ProblemStatus.PASSED:
                passed += 1
            rec_problems.append(RoadmapProblem(id=p.id, number=p.number, title=p.title, status=st))

        total = int(topic_totals.get(topic.id, len(rec_problems)))
        out.append(
            RoadmapTopic(
                topic_id=topic.id,
                name=topic.name,
                order_index=node.order_index,
                pattern_summary=topic.pattern_summary,
                total=total,
                passed=passed,
                completion_rate=round(passed / total, 4) if total else 0.0,
                problems=rec_problems,
            )
        )
    return out
