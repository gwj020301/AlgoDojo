"""FastAPI dependency that resolves the current user from a Bearer JWT."""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import TokenError, get_subject
from app.db import get_session
from app.models import User

# auto_error=False so we can return a consistent 401 (with WWW-Authenticate)
# rather than FastAPI's default 403 for a missing header.
_bearer = HTTPBearer(auto_error=False)

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Return the authenticated user, or raise 401."""
    if credentials is None or not credentials.credentials:
        raise _UNAUTHORIZED
    try:
        subject = get_subject(credentials.credentials)
        user_id = uuid.UUID(subject)
    except (TokenError, ValueError):
        raise _UNAUTHORIZED from None

    user = await session.get(User, user_id)
    if user is None:
        raise _UNAUTHORIZED
    return user
