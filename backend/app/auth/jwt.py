"""JWT signing and verification for API authentication."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt

from app.config import get_settings


class TokenError(Exception):
    """Raised when a token is invalid, expired, or malformed."""


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    """Sign a JWT whose ``sub`` claim is the given subject (the user id)."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expires_minutes or settings.jwt_expire_minutes)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT. Raises TokenError on any problem."""
    settings = get_settings()
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc


def get_subject(token: str) -> str:
    """Return the ``sub`` claim from a valid token."""
    payload = decode_access_token(token)
    subject = payload.get("sub")
    if not subject:
        raise TokenError("Token missing subject")
    return subject
