"""Parser for ``hot100.md`` (LeetCode 热题 Hot 100).

The source file groups problems under ``## 专题`` headers. Each problem is a
single line of the form::

    N. <标题> <题干描述>

The tricky part is splitting the title from the description: titles may contain
spaces (e.g. "LRU 缓存", "搜索二维矩阵 II", "数据流的中位数"), so we cannot simply
split on the first space. Instead we locate the earliest *description opener*
phrase — a curated set of sentence-opening clauses that begin every Hot 100
description but never appear inside a title. The text before that opener is the
title; from the opener onward is the description.

This heuristic is tuned for and validated against ``hot100.md`` (see
``tests/test_parse_hot100.py``, which asserts all 100 problems parse cleanly).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Repo root is four levels up: backend/app/seed/hot100.py -> AlgoDojo/
_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_HOT100_PATH = _REPO_ROOT / "hot100.md"

# Ordered, curated set of description-opening phrases. We pick the earliest
# occurrence (index > 0) across this set as the title/description boundary.
# Specific multi-character phrases are used so they never collide with titles.
DESCRIPTION_OPENERS: tuple[str, ...] = (
    "给定",
    "给你",
    "请你",
    "编写",
    "设计一个",
    "设计并",
    "以数组",
    "将两个",
    "在给定",
    "按照",
    "你这个",
    "你是一个",
    "假设",
    "已知",
    "数字 n",
    "一个机器人",
    "整数数组 nums",
    "整数数组的",
    "中位数是",
    "二叉树中的路径",
)

# A problem line: leading number, dot, then the body (title + description).
_PROBLEM_LINE = re.compile(r"^(\d+)\.\s+(.*)$")
# A topic header: "## 专题名".
_TOPIC_HEADER = re.compile(r"^##\s+(.+?)\s*$")


@dataclass(frozen=True)
class ParsedProblem:
    """One parsed problem from hot100.md."""

    number: int
    title: str
    description: str
    topic: str
    # 0-based position within its topic (for recommended ordering)
    order_in_topic: int


def split_title_description(body: str) -> tuple[str, str]:
    """Split a problem body into (title, description).

    Raises ValueError if no description opener is found (signals the heuristic
    needs updating for new content).
    """
    best: int | None = None
    for opener in DESCRIPTION_OPENERS:
        idx = body.find(opener)
        if idx > 0 and (best is None or idx < best):
            best = idx
    if best is None:
        raise ValueError(f"No description opener found in problem body: {body!r}")
    title = body[:best].strip()
    description = body[best:].strip()
    if not title or not description:
        raise ValueError(f"Empty title or description after split: {body!r}")
    return title, description


def parse_hot100(text: str) -> list[ParsedProblem]:
    """Parse the full hot100.md text into a list of ParsedProblem."""
    problems: list[ParsedProblem] = []
    current_topic: str | None = None
    topic_counts: dict[str, int] = {}

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        topic_match = _TOPIC_HEADER.match(line)
        if topic_match:
            current_topic = topic_match.group(1).strip()
            topic_counts.setdefault(current_topic, 0)
            continue

        problem_match = _PROBLEM_LINE.match(line)
        if problem_match:
            if current_topic is None:
                raise ValueError(f"Problem found before any topic header: {line!r}")
            number = int(problem_match.group(1))
            title, description = split_title_description(problem_match.group(2))
            order = topic_counts[current_topic]
            topic_counts[current_topic] = order + 1
            problems.append(
                ParsedProblem(
                    number=number,
                    title=title,
                    description=description,
                    topic=current_topic,
                    order_in_topic=order,
                )
            )

    return problems


def parse_hot100_file(path: Path | str | None = None) -> list[ParsedProblem]:
    """Parse hot100.md from disk (defaults to the repo-root hot100.md)."""
    p = Path(path) if path is not None else DEFAULT_HOT100_PATH
    return parse_hot100(p.read_text(encoding="utf-8"))


def parse_topics_in_order(text: str) -> list[str]:
    """Return topic names in their order of appearance in the file."""
    topics: list[str] = []
    for raw_line in text.splitlines():
        m = _TOPIC_HEADER.match(raw_line.strip())
        if m:
            name = m.group(1).strip()
            if name not in topics:
                topics.append(name)
    return topics
