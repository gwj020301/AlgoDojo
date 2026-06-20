"""Problem-domain models: Topic, Problem, TestCase, Hint."""

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, JSONType


class Topic(Base):
    """An algorithm topic (哈希 / 双指针 / 动态规划 ...)."""

    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    # 套路总结，复用支撑路线图与套路速查（design.md 数据模型备注）
    pattern_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 难度梯度排序（哈希 -> ... -> 动态规划）
    order_index: Mapped[int] = mapped_column(Integer, default=0, index=True)

    problems: Mapped[list["Problem"]] = relationship(
        back_populates="topic", order_by="Problem.number"
    )
    roadmap_node: Mapped["RoadmapNode | None"] = relationship(  # noqa: F821
        back_populates="topic", uselist=False
    )


class Problem(Base):
    """A single coding problem from the Hot 100 set."""

    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 题号（hot100 内 1..100 的序号），唯一
    number: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    difficulty: Mapped[str] = mapped_column(String(16), index=True)
    # 可作答语言列表，如 ["python", "typescript"]
    languages: Mapped[list[str]] = mapped_column(JSONType, default=list)
    # 各语言初始代码模板，如 {"python": "...", "typescript": "..."}
    templates: Mapped[dict[str, str]] = mapped_column(JSONType, default=dict)
    reference_solution: Mapped[str | None] = mapped_column(Text, nullable=True)

    topic: Mapped["Topic"] = relationship(back_populates="problems")
    test_cases: Mapped[list["TestCase"]] = relationship(
        back_populates="problem", cascade="all, delete-orphan", order_by="TestCase.id"
    )
    hints: Mapped[list["Hint"]] = relationship(
        back_populates="problem", cascade="all, delete-orphan", order_by="Hint.level"
    )


class TestCase(Base):
    """A judge test case for a problem."""

    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), index=True
    )
    input: Mapped[str] = mapped_column(Text)
    expected_output: Mapped[str] = mapped_column(Text)
    # 样例用例（用于"运行/自测"），非样例仅用于"提交/判题"
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)

    problem: Mapped["Problem"] = relationship(back_populates="test_cases")


class Hint(Base):
    """A layered hint for a problem (level 1..4)."""

    __tablename__ = "hints"
    __table_args__ = (UniqueConstraint("problem_id", "level", name="uq_hint_problem_level"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), index=True
    )
    level: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)

    problem: Mapped["Problem"] = relationship(back_populates="hints")
