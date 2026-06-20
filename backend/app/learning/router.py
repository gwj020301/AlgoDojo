"""Learning-aid routes: /roadmap, /problems/{id}/hints, /patterns."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.db import get_session
from app.learning import hints as hints_service
from app.learning import patterns as patterns_service
from app.learning import roadmap as roadmap_service
from app.learning.schemas import HintsState, PatternOut, RoadmapTopic
from app.models import User

router = APIRouter(tags=["learning"])


@router.get("/roadmap", response_model=list[RoadmapTopic])
async def get_roadmap(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[RoadmapTopic]:
    """Difficulty-ordered topics with pattern summary, progress, recommended order."""
    return await roadmap_service.get_roadmap(session, user.id)


@router.get("/problems/{problem_id}/hints", response_model=HintsState)
async def get_hints(
    problem_id: int,
    level: int | None = Query(default=None, description="解锁第 n 层提示（必须按顺序）"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> HintsState:
    """Return unlocked hints; with ?level=n, unlock the next level (one at a time)."""
    try:
        if level is None:
            return await hints_service.get_hints_state(session, user.id, problem_id)
        return await hints_service.unlock_hint(session, user.id, problem_id, level)
    except hints_service.HintError as exc:
        code = status.HTTP_404_NOT_FOUND if exc.not_found else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=exc.message) from None


@router.get("/patterns", response_model=list[PatternOut])
async def get_patterns(
    q: str | None = Query(default=None, description="按关键词检索套路"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[PatternOut]:
    """List or search algorithm pattern templates (Python/TS + mnemonic)."""
    return await patterns_service.list_patterns(session, q)
