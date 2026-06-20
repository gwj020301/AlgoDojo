"""Pattern cheat-sheet service: list/search reusable templates (requirement 8)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.learning.schemas import PatternOut
from app.models import PatternTemplate


async def list_patterns(session: AsyncSession, query: str | None = None) -> list[PatternOut]:
    """List patterns (grouped by name with per-language templates).

    Optional case-insensitive keyword filter on pattern name or mnemonic
    (requirement 8.4).
    """
    rows = list(
        (
            await session.execute(select(PatternTemplate).order_by(PatternTemplate.pattern_name))
        ).scalars()
    )

    grouped: dict[str, PatternOut] = {}
    for row in rows:
        out = grouped.get(row.pattern_name)
        if out is None:
            out = PatternOut(pattern_name=row.pattern_name, mnemonic=row.mnemonic, templates={})
            grouped[row.pattern_name] = out
        out.templates[row.language] = row.code
        if out.mnemonic is None and row.mnemonic:
            out.mnemonic = row.mnemonic

    patterns = list(grouped.values())

    if query:
        q = query.strip().lower()
        patterns = [
            p
            for p in patterns
            if q in p.pattern_name.lower() or (p.mnemonic and q in p.mnemonic.lower())
        ]
    return patterns
