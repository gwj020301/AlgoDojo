"""Output normalization and comparison for judging.

The default comparison is whitespace-tolerant, which avoids spurious WA from
trailing newlines or trailing spaces — a common source of false negatives in
online judges:

- strip trailing whitespace on each line,
- drop trailing blank lines,
- compare line by line.
"""

from __future__ import annotations


def normalize_output(text: str) -> str:
    """Normalize program output for comparison.

    - Normalize line endings (\\r\\n, \\r -> \\n).
    - Strip trailing whitespace from each line.
    - Remove trailing blank lines.
    """
    unified = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in unified.split("\n")]
    # Drop trailing empty lines.
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def outputs_match(actual: str, expected: str) -> bool:
    """Return True if normalized actual equals normalized expected."""
    return normalize_output(actual) == normalize_output(expected)
