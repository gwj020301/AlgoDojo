"""Progress route: /me/progress."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.db import get_session
from app.models import User
from app.progress import service
from app.progress.schemas import ProgressOut

router = APIRouter(prefix="/me", tags=["progress"])


@router.get("/progress", response_model=ProgressOut)
async def my_progress(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProgressOut:
    """Return the caller's overall and per-topic completion statistics."""
    return await service.compute_progress(session, user.id)
