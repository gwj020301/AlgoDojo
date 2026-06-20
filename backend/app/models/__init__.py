"""SQLAlchemy ORM models.

Importing this package ensures every model is registered on ``Base.metadata``
(needed by Alembic autogenerate and ``create_all``).
"""

from app.db import Base
from app.models.learning import PatternTemplate, RoadmapNode, UserHintUnlock
from app.models.problem import Hint, Problem, TestCase, Topic
from app.models.submission import Submission, UserProblemStatus
from app.models.user import User

__all__ = [
    "Base",
    "User",
    "Topic",
    "Problem",
    "TestCase",
    "Hint",
    "Submission",
    "UserProblemStatus",
    "RoadmapNode",
    "PatternTemplate",
    "UserHintUnlock",
]
