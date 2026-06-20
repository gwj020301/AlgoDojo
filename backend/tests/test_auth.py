"""Tests for GitHub OAuth + JWT auth (requirements 1.1-1.7).

GitHub network calls are monkeypatched; the DB is in-memory SQLite (see conftest).
"""

from urllib.parse import parse_qs, urlparse

import pytest
from app.auth import github
from app.auth.jwt import TokenError, create_access_token, decode_access_token, get_subject


# --------------------------- JWT unit tests ---------------------------
def test_jwt_roundtrip() -> None:
    token = create_access_token("user-123")
    assert get_subject(token) == "user-123"
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"
    assert "exp" in payload and "iat" in payload


def test_jwt_expired_is_rejected() -> None:
    token = create_access_token("user-123", expires_minutes=-1)
    with pytest.raises(TokenError):
        decode_access_token(token)


def test_jwt_tampered_is_rejected() -> None:
    token = create_access_token("user-123")
    with pytest.raises(TokenError):
        decode_access_token(token + "tamper")


# ----------------------- OAuth callback helpers -----------------------
def _patch_github(monkeypatch, gh_user: dict, *, fail: bool = False) -> None:
    async def fake_exchange(code: str) -> str:
        if fail:
            raise github.GitHubOAuthError("boom")
        return "fake-access-token"

    async def fake_fetch(token: str) -> dict:
        return gh_user

    monkeypatch.setattr(github, "exchange_code_for_token", fake_exchange)
    monkeypatch.setattr(github, "fetch_github_user", fake_fetch)


def _login_and_get_state(client) -> str:
    resp = client.get("/auth/github/login", follow_redirects=False)
    assert resp.status_code in (302, 307)
    loc = resp.headers["location"]
    assert loc.startswith("https://github.com/login/oauth/authorize")
    # The CSRF state cookie is now stored in the client's cookie jar.
    return parse_qs(urlparse(loc).query)["state"][0]


def _complete_login(client, monkeypatch, gh_user: dict) -> str:
    _patch_github(monkeypatch, gh_user)
    state = _login_and_get_state(client)
    resp = client.get(f"/auth/github/callback?code=abc&state={state}", follow_redirects=False)
    assert resp.status_code in (302, 307)
    loc = resp.headers["location"]
    assert "/auth/callback#token=" in loc
    return loc.split("#token=")[1]


# --------------------------- login flow ---------------------------
def test_login_redirects_to_github_with_no_repo_scope(client) -> None:
    resp = client.get("/auth/github/login", follow_redirects=False)
    loc = resp.headers["location"]
    scope = parse_qs(urlparse(loc).query)["scope"][0]
    assert "repo" not in scope  # requirement 1.7: never request repo write access


def test_callback_success_creates_user_and_returns_token(client, monkeypatch) -> None:
    gh_user = {"id": 4242, "login": "octocat", "avatar_url": "http://x/a.png"}
    token = _complete_login(client, monkeypatch, gh_user)

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["github_id"] == 4242
    assert body["username"] == "octocat"


def test_callback_denied_redirects_to_login_with_error(client) -> None:
    resp = client.get("/auth/github/callback?error=access_denied", follow_redirects=False)
    loc = resp.headers["location"]
    assert "/login?" in loc
    assert parse_qs(urlparse(loc).query)["error"][0] == "access_denied"


def test_callback_invalid_state_redirects_with_error(client, monkeypatch) -> None:
    _patch_github(monkeypatch, {"id": 1, "login": "a"})
    _login_and_get_state(client)
    resp = client.get("/auth/github/callback?code=abc&state=WRONG", follow_redirects=False)
    loc = resp.headers["location"]
    assert parse_qs(urlparse(loc).query)["error"][0] == "invalid_state"


def test_callback_oauth_failure_redirects_with_error(client, monkeypatch) -> None:
    _patch_github(monkeypatch, {"id": 1, "login": "a"}, fail=True)
    state = _login_and_get_state(client)
    resp = client.get(f"/auth/github/callback?code=abc&state={state}", follow_redirects=False)
    loc = resp.headers["location"]
    assert parse_qs(urlparse(loc).query)["error"][0] == "oauth_failed"


def test_second_login_updates_existing_user(client, monkeypatch) -> None:
    gh_user = {"id": 777, "login": "old", "avatar_url": "http://x/1.png"}
    token1 = _complete_login(client, monkeypatch, gh_user)
    id1 = client.get("/auth/me", headers={"Authorization": f"Bearer {token1}"}).json()["id"]

    # Same github id, updated profile.
    gh_user2 = {"id": 777, "login": "new", "avatar_url": "http://x/2.png"}
    token2 = _complete_login(client, monkeypatch, gh_user2)
    body2 = client.get("/auth/me", headers={"Authorization": f"Bearer {token2}"}).json()
    assert body2["id"] == id1  # same user row
    assert body2["username"] == "new"  # profile refreshed


# --------------------------- 401 / protection ---------------------------
def test_me_without_token_is_401(client) -> None:
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_with_garbage_token_is_401(client) -> None:
    resp = client.get("/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401


def test_me_with_expired_token_is_401(client) -> None:
    expired = create_access_token("00000000-0000-0000-0000-000000000000", expires_minutes=-1)
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401


def test_me_with_valid_token_for_unknown_user_is_401(client) -> None:
    # Well-formed token, valid UUID subject, but no such user in the DB.
    token = create_access_token("11111111-1111-1111-1111-111111111111")
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_user_isolation_two_users_get_distinct_identities(client, monkeypatch) -> None:
    token_a = _complete_login(client, monkeypatch, {"id": 1001, "login": "alice"})
    token_b = _complete_login(client, monkeypatch, {"id": 1002, "login": "bob"})

    a = client.get("/auth/me", headers={"Authorization": f"Bearer {token_a}"}).json()
    b = client.get("/auth/me", headers={"Authorization": f"Bearer {token_b}"}).json()
    assert a["id"] != b["id"]
    assert a["username"] == "alice"
    assert b["username"] == "bob"


# --------------------------- dev-login (acceptance) ---------------------------
def test_dev_login_issues_token_in_dev(client) -> None:
    resp = client.post("/auth/dev-login")
    assert resp.status_code == 200
    token = resp.json()["token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "demo"


def test_dev_login_disabled_when_not_dev(client, monkeypatch) -> None:
    from app.auth import router as auth_router
    from app.config import Settings

    # Simulate a production environment.
    monkeypatch.setattr(auth_router, "get_settings", lambda: Settings(env="prod"))
    resp = client.post("/auth/dev-login")
    assert resp.status_code == 404
