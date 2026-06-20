"""Pydantic schemas for progress statistics."""

from __future__ import annotations

from pydantic import BaseModel


class TopicProgress(BaseModel):
    topic_id: int
    topic_name: str
    total: int
    passed: int
    completion_rate: float  # 0.0 - 1.0


class ProgressOut(BaseModel):
    total_problems: int
    passed: int
    in_progress: int
    completion_rate: float
    topics: list[TopicProgress]
