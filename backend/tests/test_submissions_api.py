"""Tests for submission acceptance (POST) and result query (GET) with isolation.

Uses the SQLite-backed client fixture. The Redis enqueue is monkeypatched so no
Redis is needed for these API-level tests.
"""

import uuid

import pytest
from app.auth.jwt import create_access_token
from app.models import Problem, Topic, User
from app.submissions import queue as queue_mod


@pytest.fixture
def enqueued(monkeypatch) -> list[str]:
    """Capture enqueued submission ids instead of hitting Redis."""
    captured: list[str] = []

    async def fake_enqueue(_redis, submission_id: str) -> None:
        captured.append(submission_id)

    # The router calls app.submissions.queue.enqueue_submission.
    monkeypatch.setattr(queue_mod, "enqueue_submission", fake_enqueue)
    return captured


async def _session(client):
    """Open a session from the test's overridden factory."""
    from app.db import get_session

    factory = client.app.dependency_overrides[get_session]
    gen = factory()
    return gen, await gen.__anext__()


async def _seed_problem(client) -> int:
    gen, session = await _session(client)
    try:
        topic = Topic(name="哈希", order_index=0)
        session.add(topic)
        await session.flush()
        problem = Problem(
            number=1,
            title="两数之和",
            description="...",
            topic_id=topic.id,
            difficulty="easy",
            languages=["python", "typescript"],
            templates={},
        )
        session.add(problem)
        await session.commit()
        return problem.id
    finally:
        await gen.aclose()


async def _create_user(client, github_id: int) -> str:
    gen, session = await _session(client)
    try:
        user = User(github_id=github_id, username=f"user{github_id}")
        session.add(user)
        await session.commit()
        return create_access_token(str(user.id))
    finally:
        await gen.aclose()


async def _seed_user_and_problem(client) -> tuple[str, int]:
    problem_id = await _seed_problem(client)
    token = await _create_user(client, 999)
    return token, problem_id


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_submit_accepts_and_enqueues(client, enqueued) -> None:
    token, problem_id = await _seed_user_and_problem(client)
    resp = client.post(
        "/submissions",
        json={"problem_id": problem_id, "language": "python", "code": "print(1)"},
        headers=_auth(token),
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "queued"
    assert len(enqueued) == 1
    assert enqueued[0] == body["id"]


async def test_submit_unknown_problem_is_404(client, enqueued) -> None:
    token, _ = await _seed_user_and_problem(client)
    resp = client.post(
        "/submissions",
        json={"problem_id": 99999, "language": "python", "code": "x"},
        headers=_auth(token),
    )
    assert resp.status_code == 404
    assert enqueued == []


async def test_submit_disallowed_language_is_400(client, enqueued) -> None:
    token, problem_id = await _seed_user_and_problem(client)
    resp = client.post(
        "/submissions",
        json={"problem_id": problem_id, "language": "ruby", "code": "x"},
        headers=_auth(token),
    )
    assert resp.status_code == 400
    assert enqueued == []


async def test_submit_requires_auth(client) -> None:
    resp = client.post("/submissions", json={"problem_id": 1, "language": "python", "code": "x"})
    assert resp.status_code == 401


async def test_get_submission_returns_status(client, enqueued) -> None:
    token, problem_id = await _seed_user_and_problem(client)
    created = client.post(
        "/submissions",
        json={"problem_id": problem_id, "language": "python", "code": "print(1)"},
        headers=_auth(token),
    ).json()
    resp = client.get(f"/submissions/{created['id']}", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == created["id"]
    assert body["status"] == "queued"
    assert body["problem_id"] == problem_id


async def test_get_submission_isolation_returns_404_for_other_user(client, enqueued) -> None:
    token_a, problem_id = await _seed_user_and_problem(client)
    created = client.post(
        "/submissions",
        json={"problem_id": problem_id, "language": "python", "code": "print(1)"},
        headers=_auth(token_a),
    ).json()

    # A different, real user must get 404 (not their submission), not 403/200.
    token_b = await _create_user(client, 1000)
    resp = client.get(f"/submissions/{created['id']}", headers=_auth(token_b))
    assert resp.status_code == 404


async def test_get_missing_submission_is_404(client) -> None:
    token, _ = await _seed_user_and_problem(client)
    resp = client.get(f"/submissions/{uuid.uuid4()}", headers=_auth(token))
    assert resp.status_code == 404
