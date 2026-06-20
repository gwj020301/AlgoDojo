"""Problem bank routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.db import get_session
from app.models import User
from app.problems import service
from app.problems.schemas import ProblemDetail, SubmissionSummary, TopicGroup

router = APIRouter(prefix="/problems", tags=["problems"])


@router.get("", response_model=list[TopicGroup])
async def list_problems(
    topic_id: int | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[TopicGroup]:
    """List problems grouped by topic with the user's completion status."""
    return await service.list_problems_grouped(
        session,
        user.id,
        topic_id=topic_id,
        difficulty=difficulty,
        status=status_filter,
    )


@router.get("/{problem_id}", response_model=ProblemDetail)
async def get_problem(
    problem_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProblemDetail:
    """Return a problem's detail, available languages, and code templates."""
    detail = await service.get_problem_detail(session, user.id, problem_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
    return detail


@router.get("/{problem_id}/submissions", response_model=list[SubmissionSummary])
async def get_problem_submissions(
    problem_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[SubmissionSummary]:
    """Return the caller's submission history for a problem (own data only)."""
    return await service.list_problem_submissions(session, user.id, problem_id)
