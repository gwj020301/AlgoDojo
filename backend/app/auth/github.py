"""GitHub OAuth client: build authorize URL, exchange code, fetch user.

Network calls use httpx. The two async functions are intentionally small and
module-level so tests can monkeypatch them without hitting GitHub.
"""

from __future__ import annotations

from urllib.parse import urlencode

import httpx

from app.config import get_settings

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"

_HTTP_TIMEOUT = 10.0


class GitHubOAuthError(Exception):
    """Raised when the OAuth exchange or user fetch fails."""


def build_authorize_url(state: str) -> str:
    """Build the GitHub authorization URL to redirect the user to."""
    settings = get_settings()
    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": settings.github_redirect_uri,
        "scope": settings.github_scope,
        "state": state,
        "allow_signup": "true",
    }
    return f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code_for_token(code: str) -> str:
    """Exchange an OAuth ``code`` for a GitHub access token."""
    settings = get_settings()
    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
        resp = await client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_redirect_uri,
            },
        )
    if resp.status_code != 200:
        raise GitHubOAuthError(f"Token exchange failed (HTTP {resp.status_code})")
    data = resp.json()
    token = data.get("access_token")
    if not token:
        # GitHub returns {"error": "..."} on failure; never log the raw body.
        raise GitHubOAuthError(f"Token exchange error: {data.get('error', 'unknown')}")
    return token


async def fetch_github_user(access_token: str) -> dict:
    """Fetch the authenticated GitHub user's profile.

    Returns a dict with at least ``id``, ``login`` and ``avatar_url``.
    """
    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
        resp = await client.get(
            GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
    if resp.status_code != 200:
        raise GitHubOAuthError(f"Fetching GitHub user failed (HTTP {resp.status_code})")
    data = resp.json()
    if "id" not in data:
        raise GitHubOAuthError("GitHub user response missing id")
    return data
