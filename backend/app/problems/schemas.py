"""Pydantic schemas for the problem bank API."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class ProblemListItem(BaseModel):
    id: int
    number: int
    title: str
    difficulty: str
    languages: list[str]
    status: str  # not_started | in_progress | passed


class TopicGroup(BaseModel):
    topic_id: int
    topic_name: str
    order_index: int
    problems: list[ProblemListItem]


class SampleCase(BaseModel):
    input: str
    expected_output: str


class KnowledgeTip(BaseModel):
    title: str
    content: str
    code: dict[str, str] = {}


class ProblemDetail(BaseModel):
    id: int
    number: int
    title: str
    description: str
    difficulty: str
    topic_id: int
    topic_name: str
    languages: list[str]
    templates: dict[str, str]
    status: str
    samples: list[SampleCase]
    knowledge_tips: list[KnowledgeTip]


class SubmissionSummary(BaseModel):
    id: uuid.UUID
    language: str
    status: str
    verdict: str | None
    runtime_ms: int | None
    created_at: datetime
