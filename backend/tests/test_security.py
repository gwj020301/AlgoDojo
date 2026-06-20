"""Security & data-isolation regression tests (requirements: security 1-3).

Covers:
- every protected endpoint returns 401 without a valid token,
- cross-user data isolation (a user cannot read another user's submissions or
  per-problem history),
- log sanitization (the worker never logs user code).
"""

import logging
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from app.auth.jwt import create_access_token
from app.constants import SubmissionStatus
from app.models import Base, Problem, Submission, Topic, User
from app.submissions import worker
from dojo_judge import JudgeResult, Verdict
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool


# --------------------- all protected endpoints require auth ---------------------
@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/auth/me"),
        ("GET", "/problems"),
        ("GET", "/problems/1"),
        ("GET", "/problems/1/submissions"),
        ("GET", "/problems/1/hints"),
        ("GET", f"/submissions/{uuid.uuid4()}"),
        ("GET", "/me/progress"),
        ("GET", "/roadmap"),
        ("GET", "/patterns"),
        ("POST", "/submissions"),
    ],
)
def test_protected_endpoints_require_auth(client, method, path) -> None:
    resp = client.request(method, path, json={} if method == "POST" else None)
    assert resp.status_code == 401, f"{method} {path} should require auth"


def test_invalid_and_expired_tokens_rejected(client) -> None:
    assert client.get("/problems", headers={"Authorization": "Bearer garbage"}).status_code == 401
    expired = create_access_token("00000000-0000-0000-0000-000000000000", expires_minutes=-1)
    assert (
        client.get("/problems", headers={"Authorization": f"Bearer {expired}"}).status_code == 401
    )


# --------------------------- cross-user isolation ---------------------------
async def _session(client):
    from app.db import get_session

    gen = client.app.dependency_overrides[get_session]()
    return gen, await gen.__anext__()


async def _seed_problem(client) -> int:
    gen, s = await _session(client)
    try:
        t = Topic(name="哈希", order_index=0)
        s.add(t)
        await s.flush()
        p = Problem(
            number=1,
            title="两数之和",
            description="d",
            topic_id=t.id,
            difficulty="easy",
            languages=["python"],
            templates={},
        )
        s.add(p)
        await s.commit()
        return p.id
    finally:
        await gen.aclose()


async def _make_user(client, github_id: int) -> str:
    gen, s = await _session(client)
    try:
        u = User(github_id=github_id, username=f"u{github_id}")
        s.add(u)
        await s.commit()
        return create_access_token(str(u.id))
    finally:
        await gen.aclose()


def _auth(t: str) -> dict:
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture
def no_redis(monkeypatch):
    """Stub the Redis enqueue so submission POSTs don't need a live Redis."""
    from app.submissions import queue as queue_mod

    async def fake_enqueue(_redis, _sid):
        return None

    monkeypatch.setattr(queue_mod, "enqueue_submission", fake_enqueue)


async def test_user_cannot_read_another_users_submission(client, no_redis) -> None:
    problem_id = await _seed_problem(client)
    token_a = await _make_user(client, 1)
    token_b = await _make_user(client, 2)

    created = client.post(
        "/submissions",
        json={"problem_id": problem_id, "language": "python", "code": "print(1)"},
        headers=_auth(token_a),
    ).json()
    sub_id = created["id"]

    # Owner can read.
    assert client.get(f"/submissions/{sub_id}", headers=_auth(token_a)).status_code == 200
    # Other user gets 404 (no existence leak), not 403/200.
    assert client.get(f"/submissions/{sub_id}", headers=_auth(token_b)).status_code == 404


async def test_problem_history_is_per_user(client, no_redis) -> None:
    problem_id = await _seed_problem(client)
    token_a = await _make_user(client, 1)
    token_b = await _make_user(client, 2)

    client.post(
        "/submissions",
        json={"problem_id": problem_id, "language": "python", "code": "print(1)"},
        headers=_auth(token_a),
    )

    a_hist = client.get(f"/problems/{problem_id}/submissions", headers=_auth(token_a)).json()
    b_hist = client.get(f"/problems/{problem_id}/submissions", headers=_auth(token_b)).json()
    assert len(a_hist) == 1
    assert b_hist == []  # B sees none of A's history


# --------------------------- log sanitization ---------------------------
@pytest_asyncio.fixture
async def factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    await engine.dispose()


async def test_worker_does_not_log_user_code(factory, caplog) -> None:
    marker = "SECRET_USER_CODE_MARKER_9f3a2b"
    async with factory() as s:
        t = Topic(name="哈希", order_index=0)
        s.add(t)
        await s.flush()
        p = Problem(
            number=1,
            title="t",
            description="d",
            topic_id=t.id,
            difficulty="easy",
            languages=["python"],
            templates={},
        )
        s.add(p)
        await s.flush()
        u = User(github_id=1, username="u")
        s.add(u)
        await s.flush()
        sub = Submission(
            user_id=u.id,
            problem_id=p.id,
            language="python",
            code=f"print('{marker}')",
            status=SubmissionStatus.QUEUED,
        )
        s.add(sub)
        await s.commit()
        sid = sub.id

    def fake_judge(language, code, cases, limits):
        return JudgeResult(verdict=Verdict.AC, runtime_ms=1, cases_total=0, cases_passed=0)

    with caplog.at_level(logging.DEBUG):
        async with factory() as s:
            await worker.process_submission(s, sid, fake_judge)

    # The user's code must never appear in logs (requirement: security 3).
    assert marker not in caplog.text
    # But the submission id should be logged (useful, non-sensitive).
    assert str(sid) in caplog.text
