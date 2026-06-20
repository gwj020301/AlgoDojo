"""Submission and per-user progress models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, JSONType


class Submission(Base):
    """A code submission and its judge result."""

    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    language: Mapped[str] = mapped_column(String(16))
    code: Mapped[str] = mapped_column(Text)
    # True for "运行(自测样例)" — judge only sample cases and skip progress update.
    sample_only: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(16), default="queued", index=True)
    verdict: Mapped[str | None] = mapped_column(String(8), nullable=True)
    runtime_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 首个失败用例详情：{"index":..., "input":..., "expected":..., "actual":...}
    failed_case: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    # 编译/运行时错误信息（CE/RE/SE 时填充，供前端展示）
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    user: Mapped["User"] = relationship(back_populates="submissions")  # noqa: F821
    problem: Mapped["Problem"] = relationship()  # noqa: F821


class UserProblemStatus(Base):
    """Tracks a user's progress on a problem (composite PK)."""

    __tablename__ = "user_problem_status"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    problem_id: Mapped[int] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), primary_key=True
    )
    status: Mapped[str] = mapped_column(String(16), default="not_started", index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="problem_statuses")  # noqa: F821
    problem: Mapped["Problem"] = relationship()  # noqa: F821
