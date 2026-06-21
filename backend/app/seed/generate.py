"""Generate a draft seed YAML file from hot100.md.

The generated file is a *draft*: it fills in topic/number/title/description and
sensible defaults (languages, empty templates/test_cases/hints). Difficulty,
test cases, reference solutions, templates and hints must be curated by hand
afterwards (a few example problems are fully populated in the committed
``seed/problems.yaml``).

Run with::

    uv run python -m app.seed.generate            # writes seed/problems.draft.yaml
    uv run python -m app.seed.generate --stdout    # print to stdout
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

from app.constants import Difficulty, Language
from app.seed.curated import CURATED_PROBLEMS, PATTERN_TEMPLATES, TOPIC_SUMMARIES
from app.seed.hot100 import parse_hot100_file, parse_topics_in_order

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DRAFT_PATH = _BACKEND_ROOT / "seed" / "problems.draft.yaml"
DEFAULT_SEED_PATH = _BACKEND_ROOT / "seed" / "problems.yaml"
_REPO_ROOT = Path(__file__).resolve().parents[3]


def build_seed_dict(curated: bool = True) -> dict[str, Any]:
    """Build the seed data structure from hot100.md.

    When ``curated`` is True (default), overlay editorial data from
    ``app.seed.curated`` (topic summaries + fully-populated example problems).
    """
    problems = parse_hot100_file()
    topic_order = parse_topics_in_order((_REPO_ROOT / "hot100.md").read_text(encoding="utf-8"))

    # Topics with roadmap recommended order (problem numbers within the topic).
    topics: list[dict[str, Any]] = []
    for idx, name in enumerate(topic_order):
        recommended = [p.number for p in problems if p.topic == name]
        topics.append(
            {
                "name": name,
                "order_index": idx,
                "pattern_summary": TOPIC_SUMMARIES.get(name, "") if curated else "",
                "recommended_problem_numbers": recommended,
            }
        )

    problem_entries: list[dict[str, Any]] = []
    for p in problems:
        overlay = CURATED_PROBLEMS.get(p.number, {}) if curated else {}
        problem_entries.append(
            {
                "number": p.number,
                "title": p.title,
                "topic": p.topic,
                "difficulty": overlay.get("difficulty", Difficulty.MEDIUM),
                "languages": list(Language.ALL),
                "description": p.description,
                "reference_solution": overlay.get("reference_solution"),
                "templates": overlay.get("templates", {}),
                "knowledge_tips": overlay.get("knowledge_tips", []),
                "test_cases": overlay.get("test_cases", []),
                "hints": overlay.get("hints", []),
            }
        )

    # Pattern templates for the cheat-sheet (flattened to one row per language).
    patterns: list[dict[str, Any]] = []
    if curated:
        for entry in PATTERN_TEMPLATES:
            for lang, code in entry["code"].items():
                patterns.append(
                    {
                        "pattern_name": entry["pattern_name"],
                        "language": lang,
                        "code": code,
                        "mnemonic": entry.get("mnemonic"),
                    }
                )

    return {"topics": topics, "problems": problem_entries, "patterns": patterns}


def dump_seed_yaml(data: dict[str, Any]) -> str:
    """Serialize the seed dict to YAML (UTF-8, block style, keys unsorted)."""
    return yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=100,
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate seed YAML from hot100.md")
    parser.add_argument(
        "--draft",
        action="store_true",
        help="emit the un-curated draft (no editorial overlay) to problems.draft.yaml",
    )
    parser.add_argument("--stdout", action="store_true", help="print to stdout instead of file")
    parser.add_argument("--out", type=Path, default=None, help="output path override")
    args = parser.parse_args(argv)

    curated = not args.draft
    text = dump_seed_yaml(build_seed_dict(curated=curated))
    if args.stdout:
        sys.stdout.write(text)
        return
    out = args.out or (DEFAULT_DRAFT_PATH if args.draft else DEFAULT_SEED_PATH)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"Wrote {'draft' if args.draft else 'curated'} seed to {out}")


if __name__ == "__main__":
    main()
