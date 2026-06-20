"""Pydantic schemas for submission requests and responses."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SubmissionCreate(BaseModel):
    """Request body for creating a submission."""

    problem_id: int
    language: str
    code: str = Field(min_length=1, max_length=100_000)
    # "运行(自测样例)" when True; "提交(全部用例)" when False.
    sample_only: bool = False


class FailedCaseOut(BaseModel):
    index: int
    input: str
    expected: str
    actual: str


class SubmissionOut(BaseModel):
    """Submission status/result returned to the client."""

    id: uuid.UUID
    problem_id: int
    language: str
    status: str
    verdict: str | None = None
    runtime_ms: int | None = None
    failed_case: FailedCaseOut | None = None
    detail: str | None = None
    created_at: datetime


class SubmissionAccepted(BaseModel):
    """Response to a freshly accepted submission."""

    id: uuid.UUID
    status: str
