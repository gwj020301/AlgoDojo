"""Load a seed YAML file into the database (idempotent upsert by natural key).

Writes Topics, Problems, TestCases, Hints and RoadmapNodes. Re-running updates
existing rows (matched by Topic.name / Problem.number) rather than duplicating.

Run with::

    uv run python -m app.seed.loader                 # load seed/problems.yaml
    uv run python -m app.seed.loader --file path.yaml
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import async_session_factory
from app.models import Hint, PatternTemplate, Problem, RoadmapNode, TestCase, Topic

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SEED_PATH = _BACKEND_ROOT / "seed" / "problems.yaml"


def load_seed_file(path: Path | str | None = None) -> dict[str, Any]:
    """Read and parse the seed YAML file."""
    p = Path(path) if path is not None else DEFAULT_SEED_PATH
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "topics" not in data or "problems" not in data:
        raise ValueError("Seed file must contain top-level 'topics' and 'problems'.")
    return data


async def _upsert_topics(session: AsyncSession, topics: list[dict[str, Any]]) -> dict[str, Topic]:
    by_name: dict[str, Topic] = {}
    existing = {t.name: t for t in (await session.execute(select(Topic))).scalars()}
    for entry in topics:
        topic = existing.get(entry["name"])
        if topic is None:
            topic = Topic(name=entry["name"])
            session.add(topic)
        topic.order_index = entry.get("order_index", 0)
        topic.pattern_summary = entry.get("pattern_summary") or None
        by_name[topic.name] = topic
    await session.flush()
    return by_name


async def _upsert_problems(
    session: AsyncSession, problems: list[dict[str, Any]], topics: dict[str, Topic]
) -> dict[int, Problem]:
    by_number: dict[int, Problem] = {}
    existing = {p.number: p for p in (await session.execute(select(Problem))).scalars()}
    for entry in problems:
        number = entry["number"]
        problem = existing.get(number)
        if problem is None:
            problem = Problem(number=number)
            session.add(problem)
        problem.title = entry["title"]
        problem.description = entry["description"]
        problem.topic = topics[entry["topic"]]
        problem.difficulty = entry["difficulty"]
        problem.languages = list(entry.get("languages", []))
        problem.templates = dict(entry.get("templates", {}))
        problem.knowledge_tips = list(entry.get("knowledge_tips", []))
        problem.reference_solution = entry.get("reference_solution")
        by_number[number] = problem
    await session.flush()

    # Replace child rows (test cases / hints) to keep the load idempotent.
    problem_ids = [p.id for p in by_number.values()]
    if problem_ids:
        await session.execute(delete(TestCase).where(TestCase.problem_id.in_(problem_ids)))
        await session.execute(delete(Hint).where(Hint.problem_id.in_(problem_ids)))
    await session.flush()

    for entry in problems:
        problem = by_number[entry["number"]]
        for tc in entry.get("test_cases", []):
            session.add(
                TestCase(
                    problem_id=problem.id,
                    input=tc["input"],
                    expected_output=tc["expected_output"],
                    is_sample=bool(tc.get("is_sample", False)),
                )
            )
        for h in entry.get("hints", []):
            session.add(Hint(problem_id=problem.id, level=h["level"], content=h["content"]))
    await session.flush()
    return by_number


async def _upsert_roadmap(
    session: AsyncSession,
    topics_data: list[dict[str, Any]],
    topics: dict[str, Topic],
    problems: dict[int, Problem],
) -> None:
    existing = {n.topic_id: n for n in (await session.execute(select(RoadmapNode))).scalars()}
    for entry in topics_data:
        topic = topics[entry["name"]]
        node = existing.get(topic.id)
        if node is None:
            node = RoadmapNode(topic_id=topic.id)
            session.add(node)
        node.order_index = entry.get("order_index", 0)
        # Map recommended problem numbers -> problem ids (skip unknown numbers).
        node.recommended_problem_ids = [
            problems[n].id for n in entry.get("recommended_problem_numbers", []) if n in problems
        ]
    await session.flush()


async def seed_database(session: AsyncSession, data: dict[str, Any]) -> dict[str, int]:
    """Seed all entities from parsed seed data. Returns counts for reporting."""
    topics = await _upsert_topics(session, data["topics"])
    problems = await _upsert_problems(session, data["problems"], topics)
    await _upsert_roadmap(session, data["topics"], topics, problems)
    pattern_count = await _replace_patterns(session, data.get("patterns", []))
    await session.commit()
    return {
        "topics": len(topics),
        "problems": len(problems),
        "roadmap_nodes": len(data["topics"]),
        "patterns": pattern_count,
    }


async def _replace_patterns(session: AsyncSession, patterns: list[dict[str, Any]]) -> int:
    """Replace all pattern templates (idempotent full refresh)."""
    await session.execute(delete(PatternTemplate))
    await session.flush()
    for entry in patterns:
        session.add(
            PatternTemplate(
                pattern_name=entry["pattern_name"],
                language=entry["language"],
                code=entry["code"],
                mnemonic=entry.get("mnemonic"),
            )
        )
    await session.flush()
    return len(patterns)


async def run(path: Path | str | None = None) -> dict[str, int]:
    data = load_seed_file(path)
    async with async_session_factory() as session:
        return await seed_database(session, data)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Load seed YAML into the database")
    parser.add_argument("--file", type=Path, default=None, help="seed YAML path")
    args = parser.parse_args(argv)
    counts = asyncio.run(run(args.file))
    print(f"Seeded: {counts}")


if __name__ == "__main__":
    main()
