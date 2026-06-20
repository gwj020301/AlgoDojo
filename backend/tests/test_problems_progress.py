"""Tests for the problem bank API and the progress state machine."""

import uuid
from collections.abc import AsyncGenerator

import pytest_asyncio
from app.auth.jwt import create_access_token
from app.constants import ProblemStatus, Verdict
from app.models import Base, Problem, Topic, User
from app.progress.service import compute_progress, update_user_problem_status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool


# ----------------------- progress state machine (unit) -----------------------
@pytest_asyncio.fixture
async def factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    await engine.dispose()


async def _seed(factory) -> tuple[uuid.UUID, list[int]]:
    """Two topics; topic A has 2 problems, topic B has 1. Returns (user_id, [pids])."""
    async with factory() as s:
        ta = Topic(name="哈希", order_index=0)
        tb = Topic(name="双指针", order_index=1)
        s.add_all([ta, tb])
        await s.flush()
        p1 = Problem(
            number=1,
            title="a",
            description="d",
            topic_id=ta.id,
            difficulty="easy",
            languages=["python"],
            templates={"python": "tpl"},
        )
        p2 = Problem(
            number=2,
            title="b",
            description="d",
            topic_id=ta.id,
            difficulty="medium",
            languages=["python"],
            templates={},
        )
        p3 = Problem(
            number=3,
            title="c",
            description="d",
            topic_id=tb.id,
            difficulty="hard",
            languages=["python", "typescript"],
            templates={},
        )
        u = User(github_id=1, username="u")
        s.add_all([p1, p2, p3, u])
        await s.commit()
        return u.id, [p1.id, p2.id, p3.id]


async def test_first_ac_sets_passed(factory) -> None:
    user_id, pids = await _seed(factory)
    async with factory() as s:
        st = await update_user_problem_status(s, user_id, pids[0], Verdict.AC)
        await s.commit()
    assert st == ProblemStatus.PASSED


async def test_non_ac_sets_in_progress(factory) -> None:
    user_id, pids = await _seed(factory)
    async with factory() as s:
        st = await update_user_problem_status(s, user_id, pids[0], Verdict.WA)
        await s.commit()
    assert st == ProblemStatus.IN_PROGRESS


async def test_passed_is_terminal_not_downgraded(factory) -> None:
    user_id, pids = await _seed(factory)
    async with factory() as s:
        await update_user_problem_status(s, user_id, pids[0], Verdict.AC)
        # A later wrong submission must NOT downgrade a passed problem.
        st = await update_user_problem_status(s, user_id, pids[0], Verdict.WA)
        await s.commit()
    assert st == ProblemStatus.PASSED


async def test_in_progress_then_ac_becomes_passed(factory) -> None:
    user_id, pids = await _seed(factory)
    async with factory() as s:
        await update_user_problem_status(s, user_id, pids[0], Verdict.TLE)
        st = await update_user_problem_status(s, user_id, pids[0], Verdict.AC)
        await s.commit()
    assert st == ProblemStatus.PASSED


async def test_compute_progress_overall_and_per_topic(factory) -> None:
    user_id, pids = await _seed(factory)
    async with factory() as s:
        await update_user_problem_status(s, user_id, pids[0], Verdict.AC)  # topic A
        await update_user_problem_status(s, user_id, pids[2], Verdict.WA)  # topic B in_progress
        await s.commit()
    async with factory() as s:
        prog = await compute_progress(s, user_id)
    assert prog.total_problems == 3
    assert prog.passed == 1
    assert prog.in_progress == 1
    topic_a = next(t for t in prog.topics if t.topic_name == "哈希")
    assert topic_a.total == 2 and topic_a.passed == 1
    assert abs(topic_a.completion_rate - 0.5) < 1e-9


# ----------------------------- problems API -----------------------------
def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _session(client):
    from app.db import get_session

    gen = client.app.dependency_overrides[get_session]()
    return gen, await gen.__anext__()


async def _seed_api(client) -> str:
    gen, s = await _session(client)
    try:
        ta = Topic(name="哈希", order_index=0)
        tb = Topic(name="双指针", order_index=1)
        s.add_all([ta, tb])
        await s.flush()
        s.add_all(
            [
                Problem(
                    number=1,
                    title="两数之和",
                    description="desc1",
                    topic_id=ta.id,
                    difficulty="easy",
                    languages=["python", "typescript"],
                    templates={"python": "tpl-py"},
                ),
                Problem(
                    number=4,
                    title="移动零",
                    description="desc4",
                    topic_id=tb.id,
                    difficulty="medium",
                    languages=["python"],
                    templates={},
                ),
            ]
        )
        u = User(github_id=5, username="tester")
        s.add(u)
        await s.commit()
        return create_access_token(str(u.id))
    finally:
        await gen.aclose()


async def test_list_problems_grouped_with_status(client) -> None:
    token = await _seed_api(client)
    resp = client.get("/problems", headers=_auth(token))
    assert resp.status_code == 200
    groups = resp.json()
    assert [g["topic_name"] for g in groups] == ["哈希", "双指针"]  # ordered by order_index
    first = groups[0]["problems"][0]
    assert first["title"] == "两数之和"
    assert first["status"] == "not_started"
    assert "python" in first["languages"]


async def test_list_problems_filter_by_difficulty(client) -> None:
    token = await _seed_api(client)
    resp = client.get("/problems?difficulty=easy", headers=_auth(token))
    groups = resp.json()
    # Only the easy problem's topic remains.
    assert len(groups) == 1
    assert groups[0]["topic_name"] == "哈希"


async def test_list_problems_filter_by_status(client) -> None:
    token = await _seed_api(client)
    # Nothing attempted yet -> filtering by passed yields no groups.
    resp = client.get("/problems?status=passed", headers=_auth(token))
    assert resp.json() == []


async def test_problem_detail_includes_templates(client) -> None:
    token = await _seed_api(client)
    groups = client.get("/problems", headers=_auth(token)).json()
    pid = groups[0]["problems"][0]["id"]
    resp = client.get(f"/problems/{pid}", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["description"] == "desc1"
    assert body["templates"]["python"] == "tpl-py"
    assert body["topic_name"] == "哈希"


async def test_problem_detail_404(client) -> None:
    token = await _seed_api(client)
    resp = client.get("/problems/99999", headers=_auth(token))
    assert resp.status_code == 404


async def test_problems_require_auth(client) -> None:
    assert client.get("/problems").status_code == 401
    assert client.get("/me/progress").status_code == 401


async def test_me_progress_endpoint(client) -> None:
    token = await _seed_api(client)
    resp = client.get("/me/progress", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_problems"] == 2
    assert body["passed"] == 0
    assert body["completion_rate"] == 0.0
