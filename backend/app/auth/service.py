"""Auth domain service: upsert a user from GitHub and init first-login data."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import ProblemStatus
from app.models import Problem, User, UserProblemStatus


async def upsert_user_from_github(session: AsyncSession, gh: dict) -> tuple[User, bool]:
    """Create or update a User from a GitHub profile dict.

    Returns ``(user, created)`` where ``created`` is True for first-time logins.
    """
    github_id = int(gh["id"])
    username = gh.get("login") or f"user{github_id}"
    avatar_url = gh.get("avatar_url")

    user = (
        await session.execute(select(User).where(User.github_id == github_id))
    ).scalar_one_or_none()

    created = user is None
    if user is None:
        user = User(github_id=github_id, username=username, avatar_url=avatar_url)
        session.add(user)
    else:
        # Keep profile fields fresh on every login.
        user.username = username
        user.avatar_url = avatar_url

    await session.flush()

    if created:
        await init_user_progress(session, user)

    await session.commit()
    await session.refresh(user)
    return user, created


async def init_user_progress(session: AsyncSession, user: User) -> int:
    """Initialize per-problem progress for a new user (requirement 1.3).

    Creates a ``not_started`` status row for every problem the user does not yet
    have one for. Returns the number of rows created. Safe to call repeatedly.
    """
    problem_ids = list((await session.execute(select(Problem.id))).scalars())
    if not problem_ids:
        return 0

    existing = set(
        (
            await session.execute(
                select(UserProblemStatus.problem_id).where(UserProblemStatus.user_id == user.id)
            )
        ).scalars()
    )
    created = 0
    for pid in problem_ids:
        if pid not in existing:
            session.add(
                UserProblemStatus(user_id=user.id, problem_id=pid, status=ProblemStatus.NOT_STARTED)
            )
            created += 1
    await session.flush()
    return created
