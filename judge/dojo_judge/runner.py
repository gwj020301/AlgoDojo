"""In-container judge runner (stdlib only).

Entry point executed inside the sandbox container. It:

1. reads the job spec (``/work/job.json``) and the user's source (``/work/...``),
2. runs the language's compile step (failure -> CE),
3. runs the program once per test case, feeding the case input on stdin,
   enforcing a per-case wall-clock timeout (timeout -> TLE),
4. compares normalized stdout to the expected output (mismatch -> WA, with the
   first failing case detail; non-zero exit -> RE),
5. prints a ``JudgeResult`` JSON document to stdout.

Memory-limit (MLE) detection is the host engine's job (it inspects the
container's OOMKilled state), since an OOM kill may terminate this runner too.

Usage (inside container)::

    python3 -m dojo_judge.runner            # reads /work/job.json
    python3 -m dojo_judge.runner /path/job.json
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

from dojo_judge.adapters import get_adapter
from dojo_judge.compare import outputs_match
from dojo_judge.types import FailedCase, JudgeResult, Verdict

WORK_DIR = "/work"
OUT_DIR = "/tmp/judge"
_DETAIL_MAX = 4000


def _truncate(text: str, limit: int = _DETAIL_MAX) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[:limit] + "...[truncated]"


def run_job(
    job_path: str = f"{WORK_DIR}/job.json",
    work_dir: str = WORK_DIR,
    out_dir: str = OUT_DIR,
) -> JudgeResult:
    spec = json.loads(Path(job_path).read_text(encoding="utf-8"))
    language: str = spec["language"]
    cases: list[dict] = spec.get("cases", [])
    time_limit_s: float = float(spec.get("time_limit_s", 2.0))

    try:
        adapter = get_adapter(language)
    except ValueError as exc:
        return JudgeResult(verdict=Verdict.SE, detail=str(exc), cases_total=len(cases))

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # --- Compile step (CE on failure) ---
    for cmd in adapter.compile_commands(work_dir, str(out_path)):
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(out_path),
            )
        except subprocess.TimeoutExpired:
            return JudgeResult(
                verdict=Verdict.CE,
                detail="Compilation timed out.",
                cases_total=len(cases),
            )
        except FileNotFoundError as exc:
            return JudgeResult(
                verdict=Verdict.SE, detail=f"Toolchain missing: {exc}", cases_total=len(cases)
            )
        if proc.returncode != 0:
            return JudgeResult(
                verdict=Verdict.CE,
                detail=_truncate(proc.stderr or proc.stdout),
                cases_total=len(cases),
            )

    run_cmd = adapter.run_command(work_dir, str(out_path))

    # --- Execute each test case ---
    total_ms = 0
    passed = 0
    for index, case in enumerate(cases):
        stdin_data = case.get("input", "")
        expected = case.get("expected_output", "")
        start = time.monotonic()
        try:
            proc = subprocess.run(
                run_cmd,
                input=stdin_data,
                capture_output=True,
                text=True,
                timeout=time_limit_s,
                cwd=str(out_dir),
            )
        except subprocess.TimeoutExpired:
            return JudgeResult(
                verdict=Verdict.TLE,
                runtime_ms=int(time_limit_s * 1000),
                failed_index=index,
                detail=f"Case {index} exceeded {time_limit_s}s.",
                cases_total=len(cases),
                cases_passed=passed,
            )
        elapsed_ms = int((time.monotonic() - start) * 1000)
        total_ms += elapsed_ms

        if proc.returncode != 0:
            return JudgeResult(
                verdict=Verdict.RE,
                runtime_ms=total_ms,
                failed_index=index,
                detail=_truncate(proc.stderr or f"Exited with code {proc.returncode}"),
                cases_total=len(cases),
                cases_passed=passed,
            )

        if not outputs_match(proc.stdout, expected):
            return JudgeResult(
                verdict=Verdict.WA,
                runtime_ms=total_ms,
                failed_index=index,
                failed_case=FailedCase(
                    index=index,
                    input=stdin_data,
                    expected=expected,
                    actual=proc.stdout,
                ),
                cases_total=len(cases),
                cases_passed=passed,
            )
        passed += 1

    return JudgeResult(
        verdict=Verdict.AC,
        runtime_ms=total_ms,
        cases_total=len(cases),
        cases_passed=passed,
    )


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    job_path = argv[0] if argv else f"{WORK_DIR}/job.json"
    result = run_job(job_path)
    # Result JSON is the runner's contract with the host engine.
    sys.stdout.write(json.dumps(asdict(result), ensure_ascii=False))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
