"""Docker integration tests: run real sandbox containers for every verdict.

These are marked ``integration`` and skipped automatically when Docker is not
available. They require the ``algodojo-judge:latest`` image to be built::

    docker build -t algodojo-judge:latest judge/
    uv run pytest -m integration
"""

import pytest
from dojo_judge.engine import docker_available, judge
from dojo_judge.types import Language, Limits, TestCaseSpec, Verdict

pytestmark = pytest.mark.integration

_SKIP = not docker_available()
skip_reason = "Docker not available"

# Fast limits to keep the suite quick.
LIMITS = Limits(time_limit_s=2.0, memory_limit_mb=256, cpus=1.0, pids_limit=64)

PY_SUM = "import sys\na, b = map(int, sys.stdin.read().split())\nprint(a + b)\n"


@pytest.mark.skipif(_SKIP, reason=skip_reason)
def test_python_accepted() -> None:
    cases = [
        TestCaseSpec("2 3", "5"),
        TestCaseSpec("10 20", "30"),
        TestCaseSpec("-1 1", "0"),
    ]
    result = judge(Language.PYTHON, PY_SUM, cases, LIMITS)
    assert result.verdict == Verdict.AC, result.detail
    assert result.cases_passed == 3


@pytest.mark.skipif(_SKIP, reason=skip_reason)
def test_python_wrong_answer() -> None:
    bad = "import sys\na, b = map(int, sys.stdin.read().split())\nprint(a * b)\n"
    cases = [TestCaseSpec("2 3", "5"), TestCaseSpec("10 20", "30")]
    result = judge(Language.PYTHON, bad, cases, LIMITS)
    assert result.verdict == Verdict.WA
    assert result.failed_index == 0
    assert result.failed_case is not None
    assert result.failed_case.actual.strip() == "6"


@pytest.mark.skipif(_SKIP, reason=skip_reason)
def test_python_runtime_error() -> None:
    src = "raise RuntimeError('boom')\n"
    result = judge(Language.PYTHON, src, [TestCaseSpec("", "")], LIMITS)
    assert result.verdict == Verdict.RE
    assert "boom" in result.detail or "RuntimeError" in result.detail


@pytest.mark.skipif(_SKIP, reason=skip_reason)
def test_python_time_limit_exceeded() -> None:
    src = "while True:\n    pass\n"
    result = judge(Language.PYTHON, src, [TestCaseSpec("", "x")], Limits(time_limit_s=1.0))
    assert result.verdict == Verdict.TLE


@pytest.mark.skipif(_SKIP, reason=skip_reason)
def test_python_memory_limit_exceeded() -> None:
    # Allocate far more than the 256 MiB container limit -> OOM kill -> MLE.
    src = "x = bytearray(600 * 1024 * 1024)\nprint(len(x))\n"
    result = judge(Language.PYTHON, src, [TestCaseSpec("", "x")], LIMITS)
    assert result.verdict == Verdict.MLE


@pytest.mark.skipif(_SKIP, reason=skip_reason)
def test_python_compile_error() -> None:
    src = "def f(:\n    pass\n"  # syntax error
    result = judge(Language.PYTHON, src, [TestCaseSpec("", "")], LIMITS)
    assert result.verdict == Verdict.CE
    assert result.detail


@pytest.mark.skipif(_SKIP, reason=skip_reason)
def test_typescript_accepted() -> None:
    ts = (
        "const data = require('fs').readFileSync(0, 'utf8');\n"
        "const [a, b] = data.trim().split(/\\s+/).map(Number);\n"
        "console.log(a + b);\n"
    )
    cases = [TestCaseSpec("2 3", "5"), TestCaseSpec("10 20", "30")]
    result = judge(Language.TYPESCRIPT, ts, cases, LIMITS)
    assert result.verdict == Verdict.AC, result.detail
    assert result.cases_passed == 2


@pytest.mark.skipif(_SKIP, reason=skip_reason)
def test_typescript_compile_error() -> None:
    # Type error: assigning a string to a number variable.
    ts = "const x: number = 'not a number';\nconsole.log(x);\n"
    result = judge(Language.TYPESCRIPT, ts, [TestCaseSpec("", "")], LIMITS)
    assert result.verdict == Verdict.CE
    assert result.detail


@pytest.mark.skipif(_SKIP, reason=skip_reason)
def test_network_is_disabled_inside_sandbox() -> None:
    src = (
        "import socket\n"
        "try:\n"
        "    socket.create_connection(('1.1.1.1', 53), timeout=2)\n"
        "    print('NET_OK')\n"
        "except OSError:\n"
        "    print('NET_BLOCKED')\n"
    )
    result = judge(Language.PYTHON, src, [TestCaseSpec("", "NET_BLOCKED")], LIMITS)
    assert result.verdict == Verdict.AC, result.detail


@pytest.mark.skipif(_SKIP, reason=skip_reason)
def test_runs_as_non_root() -> None:
    src = "import os\nprint(os.getuid())\n"
    # Container runs as uid 65534 (nobody); the program should observe that.
    result = judge(Language.PYTHON, src, [TestCaseSpec("", "65534")], LIMITS)
    assert result.verdict == Verdict.AC, result.detail
