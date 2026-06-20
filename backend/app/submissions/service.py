"""Submission domain service: validation, creation, and owner-scoped lookup."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import SubmissionStatus
from app.models import Problem, Submission


class SubmissionValidationError(Exception):
    """Raised when a submission fails validation (bad problem or language)."""

    def __init__(self, message: str, *, not_found: bool = False) -> None:
        super().__init__(message)
        self.message = message
        self.not_found = not_found


async def create_submission(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    problem_id: int,
    language: str,
    code: str,
    sample_only: bool = False,
) -> Submission:
    """Validate and persist a new submission with status=queued.

    Raises SubmissionValidationError if the problem does not exist (not_found)
    or the language is not allowed for the problem.
    """
    problem = await session.get(Problem, problem_id)
    if problem is None:
        raise SubmissionValidationError("Problem not found", not_found=True)

    allowed = problem.languages or []
    if language not in allowed:
        raise SubmissionValidationError(
            f"Language {language!r} not allowed for this problem; allowed: {allowed}"
        )

    submission = Submission(
        user_id=user_id,
        problem_id=problem_id,
        language=language,
        code=code,
        sample_only=sample_only,
        status=SubmissionStatus.QUEUED,
    )
    session.add(submission)
    await session.commit()
    await session.refresh(submission)
    return submission


async def get_submission_for_user(
    session: AsyncSession, submission_id: uuid.UUID, user_id: uuid.UUID
) -> Submission | None:
    """Return the submission only if it belongs to the user (data isolation).

    Returns None both when the submission does not exist and when it belongs to
    another user, so callers can respond 404 without leaking existence
    (requirement: security 2 — users only access their own data).
    """
    result = await session.execute(
        select(Submission).where(Submission.id == submission_id, Submission.user_id == user_id)
    )
    return result.scalar_one_or_none()
