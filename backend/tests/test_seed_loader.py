"""Import-correctness tests for the seed loader, against in-memory SQLite."""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from app.models import Base, Hint, Problem, RoadmapNode, Topic
from app.models import TestCase as TestCaseModel
from app.seed.loader import load_seed_file, seed_database
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


@pytest.fixture(scope="module")
def seed_data() -> dict:
    return load_seed_file()


async def _count(session: AsyncSession, model) -> int:
    return (await session.execute(select(func.count()).select_from(model))).scalar_one()


async def test_seed_loads_all_topics_and_problems(session, seed_data) -> None:
    counts = await seed_database(session, seed_data)
    assert counts["topics"] == 17
    assert counts["problems"] == 100
    assert await _count(session, Topic) == 17
    assert await _count(session, Problem) == 100
    assert await _count(session, RoadmapNode) == 17


async def test_seed_links_problem_to_topic_and_example_data(session, seed_data) -> None:
    await seed_database(session, seed_data)
    problem = (await session.execute(select(Problem).where(Problem.number == 1))).scalar_one()
    assert problem.title == "两数之和"
    assert problem.difficulty == "easy"
    assert problem.languages == ["python", "typescript"]
    assert "python" in problem.templates

    topic = (await session.execute(select(Topic).where(Topic.id == problem.topic_id))).scalar_one()
    assert topic.name == "哈希"

    tc_count = (
        await session.execute(
            select(func.count())
            .select_from(TestCaseModel)
            .where(TestCaseModel.problem_id == problem.id)
        )
    ).scalar_one()
    assert tc_count == 3

    hint_count = (
        await session.execute(
            select(func.count()).select_from(Hint).where(Hint.problem_id == problem.id)
        )
    ).scalar_one()
    assert hint_count == 4


async def test_roadmap_node_recommends_problems_in_topic(session, seed_data) -> None:
    await seed_database(session, seed_data)
    hashing = (await session.execute(select(Topic).where(Topic.name == "哈希"))).scalar_one()
    node = (
        await session.execute(select(RoadmapNode).where(RoadmapNode.topic_id == hashing.id))
    ).scalar_one()
    # 哈希 topic has problems 1,2,3 → 3 recommended problem ids.
    assert len(node.recommended_problem_ids) == 3


async def test_seed_is_idempotent(session, seed_data) -> None:
    await seed_database(session, seed_data)
    await seed_database(session, seed_data)  # second run must not duplicate
    assert await _count(session, Problem) == 100
    assert await _count(session, Topic) == 17
    # Example problem still has exactly its curated children (no duplication).
    problem = (await session.execute(select(Problem).where(Problem.number == 1))).scalar_one()
    tc_count = (
        await session.execute(
            select(func.count())
            .select_from(TestCaseModel)
            .where(TestCaseModel.problem_id == problem.id)
        )
    ).scalar_one()
    assert tc_count == 3
