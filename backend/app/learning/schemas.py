"""Pydantic schemas for the learning-aid API."""

from __future__ import annotations

from pydantic import BaseModel


# --------------------------- roadmap ---------------------------
class RoadmapProblem(BaseModel):
    id: int
    number: int
    title: str
    status: str


class RoadmapTopic(BaseModel):
    topic_id: int
    name: str
    order_index: int
    pattern_summary: str | None
    total: int
    passed: int
    completion_rate: float
    problems: list[RoadmapProblem]  # recommended practice order


# --------------------------- hints ---------------------------
class HintItem(BaseModel):
    level: int
    content: str


class HintsState(BaseModel):
    problem_id: int
    total_levels: int
    unlocked: list[HintItem]
    next_level: int | None  # next level the user may unlock, or None if done
    # The next level is the full solution — frontend should double-confirm.
    next_is_full_solution: bool


# --------------------------- patterns ---------------------------
class PatternOut(BaseModel):
    pattern_name: str
    mnemonic: str | None
    templates: dict[str, str]  # language -> code
