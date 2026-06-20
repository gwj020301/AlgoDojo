"""Tests for learning aids: roadmap, layered hints, pattern cheat-sheet."""

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from app.learning import hints as hints_service
from app.learning import patterns as patterns_service
from app.learning import roadmap as roadmap_service
from app.models import (
    Base,
    Hint,
    PatternTemplate,
    Problem,
    RoadmapNode,
    Topic,
    User,
    UserHintUnlock,
)
from app.progress.service import update_user_problem_status
from dojo_judge import Verdict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool


@pytest_asyncio.fixture
async def factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    await engine.dispose()


async def _seed(factory) -> tuple[uuid.UUID, int]:
    """One topic, 2 problems, hints (4 levels) on problem 1, a roadmap node, patterns."""
    async with factory() as s:
        t = Topic(name="哈希", order_index=0, pattern_summary="用哈希表以空间换时间")
        s.add(t)
        await s.flush()
        p1 = Problem(
            number=1,
            title="两数之和",
            description="d",
            topic_id=t.id,
            difficulty="easy",
            languages=["python"],
            templates={},
        )
        p2 = Problem(
            number=2,
            title="字母异位词分组",
            description="d",
            topic_id=t.id,
            difficulty="medium",
            languages=["python"],
            templates={},
        )
        s.add_all([p1, p2])
        await s.flush()
        for lvl, txt in [(1, "方向"), (2, "关键步骤"), (3, "伪代码"), (4, "完整题解")]:
            s.add(Hint(problem_id=p1.id, level=lvl, content=txt))
        s.add(RoadmapNode(topic_id=t.id, order_index=0, recommended_problem_ids=[p1.id, p2.id]))
        s.add_all(
            [
                PatternTemplate(
                    pattern_name="滑动窗口", language="python", code="py-code", mnemonic="右扩左缩"
                ),
                PatternTemplate(
                    pattern_name="滑动窗口",
                    language="typescript",
                    code="ts-code",
                    mnemonic="右扩左缩",
                ),
                PatternTemplate(
                    pattern_name="二分查找", language="python", code="bs-py", mnemonic="折半收缩"
                ),
            ]
        )
        u = User(github_id=1, username="u")
        s.add(u)
        await s.commit()
        return u.id, p1.id


# ----------------------------- roadmap -----------------------------
async def test_roadmap_lists_topics_with_progress_and_recommendations(factory) -> None:
    user_id, p1 = await _seed(factory)
    async with factory() as s:
        await update_user_problem_status(s, user_id, p1, Verdict.AC)
        await s.commit()
    async with factory() as s:
        roadmap = await roadmap_service.get_roadmap(s, user_id)
    assert len(roadmap) == 1
    topic = roadmap[0]
    assert topic.name == "哈希"
    assert topic.pattern_summary
    assert topic.total == 2
    assert topic.passed == 1
    assert abs(topic.completion_rate - 0.5) < 1e-9
    # Recommended problems in stored order.
    assert [p.number for p in topic.problems] == [1, 2]
    assert topic.problems[0].status == "passed"


# ----------------------------- hints -----------------------------
async def test_hints_initial_state_nothing_unlocked(factory) -> None:
    user_id, p1 = await _seed(factory)
    async with factory() as s:
        state = await hints_service.get_hints_state(s, user_id, p1)
    assert state.total_levels == 4
    assert state.unlocked == []
    assert state.next_level == 1
    assert state.next_is_full_solution is False


async def test_hints_sequential_unlock_and_record(factory) -> None:
    user_id, p1 = await _seed(factory)
    async with factory() as s:
        s1 = await hints_service.unlock_hint(s, user_id, p1, 1)
    assert [h.level for h in s1.unlocked] == [1]
    assert s1.next_level == 2

    async with factory() as s:
        s2 = await hints_service.unlock_hint(s, user_id, p1, 2)
    assert [h.level for h in s2.unlocked] == [1, 2]

    # Unlock recorded in DB.
    async with factory() as s:
        rows = (await s.execute(select(UserHintUnlock))).scalars().all()
    assert {r.level for r in rows} == {1, 2}


async def test_hints_cannot_skip_levels(factory) -> None:
    user_id, p1 = await _seed(factory)
    # Jumping straight to level 3 (or full solution) is rejected.
    async with factory() as s:
        with pytest.raises(hints_service.HintError):
            await hints_service.unlock_hint(s, user_id, p1, 3)


async def test_hints_full_solution_flagged_before_unlock(factory) -> None:
    user_id, p1 = await _seed(factory)
    async with factory() as s:
        await hints_service.unlock_hint(s, user_id, p1, 1)
    async with factory() as s:
        await hints_service.unlock_hint(s, user_id, p1, 2)
    async with factory() as s:
        s3 = await hints_service.unlock_hint(s, user_id, p1, 3)
    # After level 3, the next (4) is the full solution -> frontend must confirm.
    assert s3.next_level == 4
    assert s3.next_is_full_solution is True


async def test_hints_unlock_is_idempotent(factory) -> None:
    user_id, p1 = await _seed(factory)
    async with factory() as s:
        await hints_service.unlock_hint(s, user_id, p1, 1)
    async with factory() as s:
        again = await hints_service.unlock_hint(s, user_id, p1, 1)  # re-unlock same level
    assert [h.level for h in again.unlocked] == [1]


async def test_hints_missing_problem_raises_not_found(factory) -> None:
    user_id, _ = await _seed(factory)
    async with factory() as s:
        with pytest.raises(hints_service.HintError) as ei:
            await hints_service.get_hints_state(s, user_id, 99999)
    assert ei.value.not_found is True


# ----------------------------- patterns -----------------------------
async def test_patterns_grouped_by_name_with_languages(factory) -> None:
    await _seed(factory)
    async with factory() as s:
        patterns = await patterns_service.list_patterns(s)
    names = {p.pattern_name for p in patterns}
    assert names == {"滑动窗口", "二分查找"}
    sw = next(p for p in patterns if p.pattern_name == "滑动窗口")
    assert set(sw.templates.keys()) == {"python", "typescript"}
    assert sw.mnemonic == "右扩左缩"


async def test_patterns_keyword_search(factory) -> None:
    await _seed(factory)
    async with factory() as s:
        result = await patterns_service.list_patterns(s, "二分")
    assert [p.pattern_name for p in result] == ["二分查找"]

    async with factory() as s:
        by_mnemonic = await patterns_service.list_patterns(s, "折半")
    assert [p.pattern_name for p in by_mnemonic] == ["二分查找"]
