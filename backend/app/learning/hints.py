"""Layered hints service: sequential unlock, usage recording (requirement 7)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import HintLevel
from app.learning.schemas import HintItem, HintsState
from app.models import Hint, Problem, UserHintUnlock


class HintError(Exception):
    """Raised on invalid hint access (missing problem/hints or illegal level)."""

    def __init__(self, message: str, *, not_found: bool = False) -> None:
        super().__init__(message)
        self.message = message
        self.not_found = not_found


async def _ordered_levels(session: AsyncSession, problem_id: int) -> list[Hint]:
    return list(
        (
            await session.execute(
                select(Hint).where(Hint.problem_id == problem_id).order_by(Hint.level)
            )
        ).scalars()
    )


async def _max_unlocked(session: AsyncSession, user_id: uuid.UUID, problem_id: int) -> int:
    levels = list(
        (
            await session.execute(
                select(UserHintUnlock.level).where(
                    UserHintUnlock.user_id == user_id,
                    UserHintUnlock.problem_id == problem_id,
                )
            )
        ).scalars()
    )
    return max(levels) if levels else 0


def _build_state(problem_id: int, hints: list[Hint], unlocked_through: int) -> HintsState:
    levels = [h.level for h in hints]
    max_level = max(levels) if levels else 0
    unlocked = [
        HintItem(level=h.level, content=h.content) for h in hints if h.level <= unlocked_through
    ]
    next_level = unlocked_through + 1 if unlocked_through < max_level else None
    return HintsState(
        problem_id=problem_id,
        total_levels=len(hints),
        unlocked=unlocked,
        next_level=next_level,
        next_is_full_solution=next_level == HintLevel.FULL_SOLUTION,
    )


async def get_hints_state(session: AsyncSession, user_id: uuid.UUID, problem_id: int) -> HintsState:
    """Return current hint state without unlocking anything."""
    if await session.get(Problem, problem_id) is None:
        raise HintError("Problem not found", not_found=True)
    hints = await _ordered_levels(session, problem_id)
    unlocked_through = await _max_unlocked(session, user_id, problem_id)
    return _build_state(problem_id, hints, unlocked_through)


async def unlock_hint(
    session: AsyncSession, user_id: uuid.UUID, problem_id: int, level: int
) -> HintsState:
    """Unlock the next hint level (must be exactly current_unlocked + 1).

    Records the unlock (requirement 7.3). Only one level is unlocked at a time
    (requirement 7.2). Raises HintError on illegal level.
    """
    if await session.get(Problem, problem_id) is None:
        raise HintError("Problem not found", not_found=True)
    hints = await _ordered_levels(session, problem_id)
    if not hints:
        raise HintError("This problem has no hints", not_found=True)

    available_levels = {h.level for h in hints}
    if level not in available_levels:
        raise HintError(f"Hint level {level} does not exist")

    unlocked_through = await _max_unlocked(session, user_id, problem_id)
    if level <= unlocked_through:
        # Already unlocked — idempotent, just return state.
        return _build_state(problem_id, hints, unlocked_through)
    if level != unlocked_through + 1:
        # Enforce one-at-a-time sequential unlocking (no skipping ahead).
        raise HintError(
            f"Must unlock levels in order; next allowed level is {unlocked_through + 1}"
        )

    session.add(UserHintUnlock(user_id=user_id, problem_id=problem_id, level=level))
    await session.commit()
    return _build_state(problem_id, hints, level)
