"""Auth routes: GitHub OAuth login, callback, and current-user lookup."""

from __future__ import annotations

import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import github
from app.auth.deps import get_current_user
from app.auth.jwt import create_access_token
from app.auth.service import upsert_user_from_github
from app.config import get_settings
from app.db import get_session
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

_STATE_COOKIE = "oauth_state"


@router.get("/github/login")
async def github_login() -> RedirectResponse:
    """Redirect the user to GitHub's authorization page.

    A random CSRF ``state`` is stored in an httponly cookie and echoed back by
    GitHub on the callback, where it is verified.
    """
    state = secrets.token_urlsafe(24)
    response = RedirectResponse(github.build_authorize_url(state))
    response.set_cookie(
        _STATE_COOKIE,
        state,
        max_age=600,
        httponly=True,
        samesite="lax",
        secure=get_settings().backend_url.startswith("https"),
    )
    return response


def _frontend_redirect(path: str, **params: str) -> RedirectResponse:
    base = get_settings().frontend_url.rstrip("/")
    query = f"?{urlencode(params)}" if params else ""
    return RedirectResponse(f"{base}{path}{query}")


@router.get("/github/callback")
async def github_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    oauth_state: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    """Handle GitHub's OAuth callback: verify state, exchange code, sign JWT.

    On success redirects to ``{frontend}/auth/callback#token=<jwt>``; on any
    failure redirects to ``{frontend}/login?error=<reason>`` (requirement 1.6).
    """
    # User denied authorization, or GitHub returned an error.
    if error:
        return _frontend_redirect("/login", error=error)

    # CSRF state must match the cookie we set at /login.
    if not code or not state or not oauth_state or state != oauth_state:
        return _frontend_redirect("/login", error="invalid_state")

    try:
        access_token = await github.exchange_code_for_token(code)
        gh_user = await github.fetch_github_user(access_token)
    except github.GitHubOAuthError:
        return _frontend_redirect("/login", error="oauth_failed")

    user, _created = await upsert_user_from_github(session, gh_user)
    jwt_token = create_access_token(str(user.id))

    # Token goes in the URL fragment so it is not sent to the server / logged.
    response = _frontend_redirect("/auth/callback")
    response.headers["location"] = (
        f"{get_settings().frontend_url.rstrip('/')}/auth/callback#token={jwt_token}"
    )
    response.delete_cookie(_STATE_COOKIE)
    return response


@router.get("/me")
async def me(user: User = Depends(get_current_user)) -> JSONResponse:
    """Return the authenticated user's profile (protected; 401 without a token)."""
    return JSONResponse(
        {
            "id": str(user.id),
            "github_id": user.github_id,
            "username": user.username,
            "avatar_url": user.avatar_url,
        }
    )


@router.post("/dev-login")
async def dev_login(session: AsyncSession = Depends(get_session)) -> JSONResponse:
    """DEV-ONLY shortcut login for acceptance testing (no GitHub App needed).

    Creates/returns a fixed demo user and issues a JWT. Returns 404 unless the
    app runs with ENV=dev, so it is unavailable in production.
    """
    if get_settings().env != "dev":
        raise HTTPException(status_code=404, detail="Not found")

    demo_github_id = 100000001
    user, _created = await upsert_user_from_github(
        session,
        {"id": demo_github_id, "login": "demo", "avatar_url": None},
    )
    token = create_access_token(str(user.id))
    return JSONResponse({"token": token, "username": user.username})
