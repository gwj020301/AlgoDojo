"""Learning-aid models: RoadmapNode, PatternTemplate, UserHintUnlock."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, JSONType


class RoadmapNode(Base):
    """A node on the learning roadmap, mapping to a topic with an order and
    a recommended problem sequence (requirement 6)."""

    __tablename__ = "roadmap_nodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), unique=True, index=True
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0, index=True)
    # 推荐练习题号顺序，如 [1, 2, 3]
    recommended_problem_ids: Mapped[list[int]] = mapped_column(JSONType, default=list)

    topic: Mapped["Topic"] = relationship(back_populates="roadmap_node")  # noqa: F821


class PatternTemplate(Base):
    """A reusable algorithm pattern template for the cheat-sheet (requirement 8)."""

    __tablename__ = "pattern_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    pattern_name: Mapped[str] = mapped_column(String(128), index=True)
    language: Mapped[str] = mapped_column(String(16))
    code: Mapped[str] = mapped_column(Text)
    mnemonic: Mapped[str | None] = mapped_column(Text, nullable=True)


class UserHintUnlock(Base):
    """Records which hint level a user has unlocked for a problem (requirement 7.3)."""

    __tablename__ = "user_hint_unlocks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    problem_id: Mapped[int] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), primary_key=True
    )
    level: Mapped[int] = mapped_column(Integer, primary_key=True)
    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
