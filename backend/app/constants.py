"""Shared domain constants used across models and services.

Stored as plain strings in the database (no native DB enums) for migration
flexibility. These constants are the canonical set of allowed values.
"""

from typing import Final


class Language:
    """Supported answer languages (requirement: Python / TypeScript)."""

    PYTHON: Final = "python"
    TYPESCRIPT: Final = "typescript"
    ALL: Final = (PYTHON, TYPESCRIPT)


class Difficulty:
    """Problem difficulty levels."""

    EASY: Final = "easy"
    MEDIUM: Final = "medium"
    HARD: Final = "hard"
    ALL: Final = (EASY, MEDIUM, HARD)


class SubmissionStatus:
    """Lifecycle status of a judge task."""

    QUEUED: Final = "queued"
    RUNNING: Final = "running"
    DONE: Final = "done"
    SYSTEM_ERROR: Final = "system_error"
    ALL: Final = (QUEUED, RUNNING, DONE, SYSTEM_ERROR)


class Verdict:
    """Judge verdicts (design.md section 3.4)."""

    AC: Final = "AC"  # Accepted
    WA: Final = "WA"  # Wrong Answer
    TLE: Final = "TLE"  # Time Limit Exceeded
    MLE: Final = "MLE"  # Memory Limit Exceeded
    CE: Final = "CE"  # Compile Error
    RE: Final = "RE"  # Runtime Error
    ALL: Final = (AC, WA, TLE, MLE, CE, RE)


class ProblemStatus:
    """Per-user progress status for a problem."""

    NOT_STARTED: Final = "not_started"
    IN_PROGRESS: Final = "in_progress"
    PASSED: Final = "passed"
    ALL: Final = (NOT_STARTED, IN_PROGRESS, PASSED)


class HintLevel:
    """Layered hint levels (requirement 7.1)."""

    DIRECTION: Final = 1  # 思路方向
    KEY_STEPS: Final = 2  # 关键步骤
    PSEUDOCODE: Final = 3  # 伪代码
    FULL_SOLUTION: Final = 4  # 完整题解
    ALL: Final = (DIRECTION, KEY_STEPS, PSEUDOCODE, FULL_SOLUTION)
