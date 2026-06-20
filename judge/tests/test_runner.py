"""Tests for the in-container runner logic, exercised locally with Python.

These run without Docker: they drive ``run_job`` against a temp work dir using
the host's python3, covering the AC / WA / RE / TLE / CE verdict branches.
Real container execution (and MLE / network / non-root) is covered by the
Docker integration tests.
"""

import json
from pathlib import Path

from dojo_judge.runner import run_job
from dojo_judge.types import Verdict

# A program that echoes the sum of two integers read from stdin.
SUM_PROGRAM = "import sys\na, b = map(int, sys.stdin.read().split())\nprint(a + b)\n"


def _write_job(tmp_path: Path, source: str, cases: list[dict], time_limit_s: float = 2.0) -> str:
    (tmp_path / "solution.py").write_text(source, encoding="utf-8")
    job = {"language": "python", "cases": cases, "time_limit_s": time_limit_s}
    job_path = tmp_path / "job.json"
    job_path.write_text(json.dumps(job), encoding="utf-8")
    return str(job_path)


def _run(tmp_path, source, cases, **kw):
    job_path = _write_job(tmp_path, source, cases, **kw)
    out_dir = tmp_path / "out"
    return run_job(job_path, work_dir=str(tmp_path), out_dir=str(out_dir))


def test_accepted(tmp_path) -> None:
    cases = [
        {"input": "2 3", "expected_output": "5"},
        {"input": "10 20", "expected_output": "30"},
    ]
    result = _run(tmp_path, SUM_PROGRAM, cases)
    assert result.verdict == Verdict.AC
    assert result.cases_passed == 2
    assert result.cases_total == 2
    assert result.runtime_ms >= 0


def test_wrong_answer_reports_first_failing_case(tmp_path) -> None:
    cases = [
        {"input": "2 3", "expected_output": "5"},
        {"input": "10 20", "expected_output": "999"},  # wrong expectation
    ]
    result = _run(tmp_path, SUM_PROGRAM, cases)
    assert result.verdict == Verdict.WA
    assert result.failed_index == 1
    assert result.failed_case is not None
    assert result.failed_case.input == "10 20"
    assert result.failed_case.expected == "999"
    assert result.failed_case.actual.strip() == "30"
    assert result.cases_passed == 1


def test_runtime_error(tmp_path) -> None:
    source = "raise ValueError('boom')\n"
    cases = [{"input": "", "expected_output": ""}]
    result = _run(tmp_path, source, cases)
    assert result.verdict == Verdict.RE
    assert "boom" in result.detail or "ValueError" in result.detail


def test_time_limit_exceeded(tmp_path) -> None:
    source = "while True:\n    pass\n"
    cases = [{"input": "", "expected_output": "x"}]
    result = _run(tmp_path, source, cases, time_limit_s=0.5)
    assert result.verdict == Verdict.TLE
    assert result.failed_index == 0


def test_compile_error_on_syntax(tmp_path) -> None:
    source = "def f(:\n    pass\n"  # syntax error
    cases = [{"input": "", "expected_output": ""}]
    result = _run(tmp_path, source, cases)
    assert result.verdict == Verdict.CE
    assert result.detail  # contains compiler message


def test_unsupported_language_is_system_error(tmp_path) -> None:
    (tmp_path / "solution.py").write_text(SUM_PROGRAM, encoding="utf-8")
    job_path = tmp_path / "job.json"
    job_path.write_text(json.dumps({"language": "ruby", "cases": []}), encoding="utf-8")
    result = run_job(str(job_path), work_dir=str(tmp_path), out_dir=str(tmp_path / "out"))
    assert result.verdict == Verdict.SE
