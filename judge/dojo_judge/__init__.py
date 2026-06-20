"""AlgoDojo judge sandbox package.

- ``types``: verdicts, test cases, results.
- ``compare``: output normalization and comparison.
- ``adapters``: per-language compile/run commands.
- ``runner``: in-container entrypoint (stdlib only).
- ``engine``: host-side Docker execution engine.
"""

from dojo_judge.engine import DockerNotAvailableError, docker_available, judge
from dojo_judge.types import (
    FailedCase,
    JobSpec,
    JudgeResult,
    Language,
    Limits,
    TestCaseSpec,
    Verdict,
)

__all__ = [
    "Verdict",
    "Language",
    "TestCaseSpec",
    "Limits",
    "FailedCase",
    "JudgeResult",
    "JobSpec",
    "judge",
    "docker_available",
    "DockerNotAvailableError",
]
