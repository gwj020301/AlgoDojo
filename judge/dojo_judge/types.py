"""Core types for the judge: verdicts, test cases, and results.

Kept stdlib-only so this module is importable both on the host (engine) and
inside the sandbox image (runner).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Final


class Verdict:
    """Judge verdicts (design.md section 3.4)."""

    AC: Final = "AC"  # Accepted — all cases pass
    WA: Final = "WA"  # Wrong Answer
    TLE: Final = "TLE"  # Time Limit Exceeded
    MLE: Final = "MLE"  # Memory Limit Exceeded
    CE: Final = "CE"  # Compile Error
    RE: Final = "RE"  # Runtime Error
    SE: Final = "SE"  # System Error (sandbox/infra failure, not user's fault)
    ALL: Final = (AC, WA, TLE, MLE, CE, RE, SE)


class Language:
    """Supported answer languages."""

    PYTHON: Final = "python"
    TYPESCRIPT: Final = "typescript"
    ALL: Final = (PYTHON, TYPESCRIPT)


@dataclass(frozen=True)
class TestCaseSpec:
    """A single judge test case (whole-program stdin -> stdout model)."""

    input: str
    expected_output: str
    is_sample: bool = False


@dataclass(frozen=True)
class Limits:
    """Resource limits for an execution."""

    # Per-test-case wall-clock timeout (seconds).
    time_limit_s: float = 2.0
    # Memory limit (MiB) applied to the whole sandbox container.
    memory_limit_mb: int = 256
    # CPU cores.
    cpus: float = 1.0
    # Max process/thread count (fork-bomb guard).
    pids_limit: int = 64


@dataclass
class FailedCase:
    """Detail of the first failing case (for WA), surfaced to the user."""

    index: int
    input: str
    expected: str
    actual: str


@dataclass
class JudgeResult:
    """Final judge outcome for a submission."""

    verdict: str
    runtime_ms: int = 0
    # Index of the case that produced a non-AC verdict (-1 if N/A).
    failed_index: int = -1
    failed_case: FailedCase | None = None
    # Human-readable detail (compile error text, exception message, etc.).
    detail: str = ""
    cases_total: int = 0
    cases_passed: int = 0

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> JudgeResult:
        fc = d.get("failed_case")
        result = cls(
            verdict=d["verdict"],
            runtime_ms=d.get("runtime_ms", 0),
            failed_index=d.get("failed_index", -1),
            detail=d.get("detail", ""),
            cases_total=d.get("cases_total", 0),
            cases_passed=d.get("cases_passed", 0),
        )
        if fc:
            result.failed_case = FailedCase(**fc)
        return result


@dataclass
class JobSpec:
    """The job handed to the in-container runner (serialized to JSON)."""

    language: str
    cases: list[TestCaseSpec] = field(default_factory=list)
    time_limit_s: float = 2.0
