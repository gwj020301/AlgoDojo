"""Host-side sandbox execution engine.

Drives the ``docker`` CLI to run one hardened, throwaway container per
submission. Responsibilities (design.md 3.1-3.2, tasks 9-10):

- write the user's code + job spec to a temp work dir,
- launch a container with strong isolation + resource limits,
- enforce a wall-clock backstop timeout (kill -> TLE),
- detect out-of-memory kills (-> MLE),
- collect the runner's verdict JSON,
- always destroy the container and clean up the temp dir.

Hardening flags applied (requirement 4.1-4.4):
``--network none``, ``--user 65534:65534``, ``--read-only`` + ``--tmpfs /tmp``,
``--cpus``, ``--memory`` + ``--memory-swap`` (swap disabled), ``--pids-limit``,
``--cap-drop ALL``, ``--security-opt no-new-privileges``.

The engine shells out to ``docker`` rather than using an SDK to keep the
dependency surface minimal.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

from dojo_judge.adapters import get_adapter
from dojo_judge.types import JudgeResult, Limits, TestCaseSpec, Verdict

DEFAULT_IMAGE = "algodojo-judge:latest"
# Extra wall-clock budget on top of (time_limit * num_cases) to cover container
# startup and the compile step.
_COMPILE_BUDGET_S = 35.0
_STARTUP_BUDGET_S = 8.0


class DockerNotAvailableError(RuntimeError):
    """Raised when the docker CLI / daemon is not usable."""


def docker_available() -> bool:
    """Return True if the docker CLI and daemon are reachable."""
    try:
        proc = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=15)
        return proc.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _build_run_argv(container_name: str, work_dir: Path, image: str, limits: Limits) -> list[str]:
    mb = limits.memory_limit_mb
    return [
        "docker",
        "run",
        "--name",
        container_name,
        # --- isolation & hardening ---
        "--network",
        "none",
        "--user",
        "65534:65534",
        "--read-only",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,size=256m",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        # --- resource limits ---
        "--cpus",
        str(limits.cpus),
        "--memory",
        f"{mb}m",
        "--memory-swap",
        f"{mb}m",  # equal to --memory => swap disabled
        "--pids-limit",
        str(limits.pids_limit),
        # --- mounts ---
        "--volume",
        f"{work_dir}:/work:ro",
        "--workdir",
        "/tmp",
        image,
        # runner reads /work/job.json by default
    ]


def _inspect_oom(container_name: str) -> bool:
    try:
        proc = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.OOMKilled}}", container_name],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return proc.returncode == 0 and proc.stdout.strip() == "true"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _cleanup_container(container_name: str) -> None:
    subprocess.run(
        ["docker", "rm", "-f", container_name],
        capture_output=True,
        text=True,
        timeout=20,
    )


def judge(
    language: str,
    code: str,
    cases: list[TestCaseSpec],
    limits: Limits | None = None,
    image: str = DEFAULT_IMAGE,
) -> JudgeResult:
    """Judge a submission in a hardened sandbox container.

    Raises DockerNotAvailableError if Docker is not usable.
    """
    if not docker_available():
        raise DockerNotAvailableError("Docker CLI/daemon is not available.")

    limits = limits or Limits()
    adapter = get_adapter(language)  # validates language early

    work_dir = Path(tempfile.mkdtemp(prefix="algodojo-judge-"))
    container_name = f"algodojo-judge-{uuid.uuid4().hex[:12]}"
    try:
        # Write user source and the job spec into the (read-only-mounted) work dir.
        (work_dir / adapter.source_filename).write_text(code, encoding="utf-8")
        job = {
            "language": language,
            "time_limit_s": limits.time_limit_s,
            "cases": [{"input": c.input, "expected_output": c.expected_output} for c in cases],
        }
        (work_dir / "job.json").write_text(json.dumps(job), encoding="utf-8")

        argv = _build_run_argv(container_name, work_dir, image, limits)
        hard_timeout = (
            limits.time_limit_s * max(1, len(cases)) + _COMPILE_BUDGET_S + _STARTUP_BUDGET_S
        )

        try:
            proc = subprocess.run(argv, capture_output=True, text=True, timeout=hard_timeout)
        except subprocess.TimeoutExpired:
            # Backstop: the in-container per-case timeout should normally catch
            # TLE first; if the whole container blew the budget, kill -> TLE.
            subprocess.run(["docker", "kill", container_name], capture_output=True, timeout=20)
            return JudgeResult(
                verdict=Verdict.TLE,
                detail="Sandbox wall-clock timeout (engine backstop).",
                cases_total=len(cases),
            )

        # Out-of-memory kill -> MLE (overrides whatever the runner managed to emit).
        if _inspect_oom(container_name) or proc.returncode == 137:
            return JudgeResult(
                verdict=Verdict.MLE,
                detail="Container exceeded the memory limit.",
                cases_total=len(cases),
            )

        # Normal path: the runner prints a JudgeResult JSON document.
        out = proc.stdout.strip()
        if out:
            try:
                return JudgeResult.from_dict(json.loads(out))
            except (json.JSONDecodeError, KeyError):
                pass

        return JudgeResult(
            verdict=Verdict.SE,
            detail=_first_nonempty(proc.stderr, proc.stdout)
            or f"Runner produced no result (exit {proc.returncode}).",
            cases_total=len(cases),
        )
    finally:
        _cleanup_container(container_name)
        shutil.rmtree(work_dir, ignore_errors=True)


def _first_nonempty(*values: str) -> str:
    for v in values:
        if v and v.strip():
            return v.strip()[:4000]
    return ""
