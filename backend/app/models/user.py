"""User model (authenticated via GitHub OAuth)."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    """A platform user, identified by their GitHub account."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    github_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    submissions: Mapped[list["Submission"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    problem_statuses: Mapped[list["UserProblemStatus"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
