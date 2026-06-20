"""Submission routes: accept a submission (enqueue) and query its result."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.db import get_session
from app.models import User
from app.redis_client import redis_client
from app.submissions import queue
from app.submissions.schemas import (
    FailedCaseOut,
    SubmissionAccepted,
    SubmissionCreate,
    SubmissionOut,
)
from app.submissions.service import (
    SubmissionValidationError,
    create_submission,
    get_submission_for_user,
)

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=SubmissionAccepted)
async def submit(
    payload: SubmissionCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SubmissionAccepted:
    """Accept a submission: validate, persist as queued, enqueue for judging."""
    try:
        submission = await create_submission(
            session,
            user_id=user.id,
            problem_id=payload.problem_id,
            language=payload.language,
            code=payload.code,
            sample_only=payload.sample_only,
        )
    except SubmissionValidationError as exc:
        code = status.HTTP_404_NOT_FOUND if exc.not_found else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=exc.message) from None

    await queue.enqueue_submission(redis_client, str(submission.id))
    return SubmissionAccepted(id=submission.id, status=submission.status)


@router.get("/{submission_id}", response_model=SubmissionOut)
async def get_submission(
    submission_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SubmissionOut:
    """Return a submission's status/result. 404 if not owned by the caller."""
    submission = await get_submission_for_user(session, submission_id, user.id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    failed_case = None
    if submission.failed_case:
        failed_case = FailedCaseOut(**submission.failed_case)

    return SubmissionOut(
        id=submission.id,
        problem_id=submission.problem_id,
        language=submission.language,
        status=submission.status,
        verdict=submission.verdict,
        runtime_ms=submission.runtime_ms,
        failed_case=failed_case,
        detail=submission.detail,
        created_at=submission.created_at,
    )
