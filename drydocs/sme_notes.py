"""SME-notes harvester (``drydocs-review`` component).

Scans the repo for owner-attributed inline notes and routes them to requirement
buckets, so SME feedback left *in the source* becomes structured input for the agent.

Note grammar (works in any comment style — Python/YAML ``#``, Cypher ``//``, Markdown)::

    SME[<sid>] $FR <text>        # a functional requirement
    SME[<sid>] $UC <text>        # a use case
    SME[<sid>] $OQ <text>        # an open question
    SME[<sid>] $NOTES <text>     # a general note

Read-only — this module never writes the graph or the repo, so it needs no HITL gate.
``<sid>`` is an owner id; **use synthetic sids in committed fixtures** (real SIDs are
Internal-Confidential). classification: Internal-Public.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

ROUTE_TAGS: tuple[str, ...] = ("FR", "UC", "OQ", "NOTES")

_NOTE_RE = re.compile(
    r"SME\[(?P<sid>[^\]]+)\]\s*\$(?P<tag>" + "|".join(ROUTE_TAGS) + r")\b[:\-\s]*(?P<text>.*?)\s*$"
)

DEFAULT_EXTENSIONS: frozenset[str] = frozenset(
    {".py", ".yaml", ".yml", ".cypher", ".cql", ".sql", ".md", ".toml"}
)
DEFAULT_EXCLUDE_DIRS: frozenset[str] = frozenset(
    {".git", "__pycache__", ".venv", "venv", "node_modules", "data", ".mypy_cache", ".pytest_cache"}
)


@dataclass(frozen=True)
class Note:
    sid: str
    tag: str
    text: str
    path: str | None = None
    line: int | None = None


def harvest_text(text: str, path: str | None = None) -> list[Note]:
    """Extract notes from a blob of text. Pure — no filesystem access."""
    notes: list[Note] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        m = _NOTE_RE.search(raw)
        if m:
            notes.append(
                Note(
                    sid=m.group("sid").strip(),
                    tag=m.group("tag"),
                    text=m.group("text").strip(),
                    path=path,
                    line=lineno,
                )
            )
    return notes


def harvest_file(path: str | Path) -> list[Note]:
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    return harvest_text(text, path=str(path))


def harvest_tree(
    root: str | Path,
    *,
    extensions: Iterable[str] = DEFAULT_EXTENSIONS,
    exclude_dirs: Iterable[str] = DEFAULT_EXCLUDE_DIRS,
) -> list[Note]:
    """Harvest every eligible file under ``root``, sorted by path then line."""
    root = Path(root)
    exts = frozenset(extensions)
    excluded = frozenset(exclude_dirs)
    notes: list[Note] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in exts:
            continue
        if any(part in excluded for part in path.relative_to(root).parts):
            continue
        notes.extend(harvest_file(path))
    return notes


def route(notes: Iterable[Note]) -> dict[str, list[Note]]:
    """Group notes into the requirement buckets (every tag present, even if empty)."""
    buckets: dict[str, list[Note]] = {tag: [] for tag in ROUTE_TAGS}
    for note in notes:
        buckets.setdefault(note.tag, []).append(note)
    return buckets
