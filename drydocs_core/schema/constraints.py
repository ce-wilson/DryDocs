"""The constraints contract (D8) — what ``constraints.cypher`` declares.

``drydocs bootstrap`` applies constraints through ``execute_file``, which
raises on a Cypher error — but a file that is truncated, mis-pathed, or
swallowed by a silent DDL no-op runs "fine" and creates nothing. That is not
hypothetical: ``apoc.cypher.runMany`` silently no-ops DDL, so pre-D5
bootstraps printed success while creating zero constraints. The guard family
that closed this class for supplements (``supplements.declared_terms`` + the
per-file presence check in ``_apply_supplement_chain``) gets its constraints
twin here: parse the NAMES the file declares, and let bootstrap assert every
one is present in ``SHOW CONSTRAINTS`` after the apply.

Names, not counts, carry the check: the target database may legitimately hold
constraints this file never declared (provisioning, older experiments), so
"applied count == declared count" can pass while the apply landed nothing.
"""

from __future__ import annotations

import re
from pathlib import Path

# A live declaration only. constraints.cypher is line-oriented and every
# declaration is idempotent (test_constraints_are_idempotent pins the
# IF NOT EXISTS), so the line-start anchor is the comment filter: a retired
# `// CREATE CONSTRAINT ...` line never matches.
_DECLARATION_RE = re.compile(
    r"^\s*CREATE CONSTRAINT\s+(?P<name>[A-Za-z0-9_]+)\s+IF NOT EXISTS",
    re.MULTILINE,
)
_ANY_DECLARATION_RE = re.compile(r"^\s*CREATE CONSTRAINT\b", re.MULTILINE)


def declared_constraint_names(path: Path) -> tuple[str, ...]:
    """Constraint names *path* declares, in file order.

    Raises ``ValueError`` when a declaration is anonymous or a name repeats —
    the bootstrap presence check keys on names, so an unnameable declaration
    would silently fall outside the guard.
    """
    text = path.read_text(encoding="utf-8")
    names = [m.group("name") for m in _DECLARATION_RE.finditer(text)]
    total = len(_ANY_DECLARATION_RE.findall(text))
    if total != len(names):
        raise ValueError(
            f"{path.name}: {total - len(names)} CREATE CONSTRAINT declaration(s) "
            "have no parseable name — the bootstrap guard cannot key on them"
        )
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        raise ValueError(f"{path.name}: duplicate constraint names {duplicates}")
    return tuple(names)


#: Every file under the schema tree that may declare a constraint. Globbed
#: rather than listed: a supplement added without touching this module would
#: otherwise read as UNDECLARED and be reported as drift, which is the fastest
#: way to teach an operator to ignore the warning.
SCHEMA_GLOB = "*.cypher"


def declared_constraint_names_in_tree(schema_dir: Path) -> dict[str, str]:
    """``{constraint name: declaring file, repo-relative-ish}`` across the tree (G130).

    The INVERSE of the bootstrap guard needs the whole tree, not
    ``constraints.cypher`` alone. ``schema_graph.cypher`` declares one of its own,
    and every supplement may; keying the drift report on a single file would
    report those as undeclared and make the warning noise on its first run.

    Sorted by ``as_posix()`` because a bare ``sorted()`` over Path objects
    compares a case-folded key on Windows and a case-sensitive one on POSIX --
    the ordering bug that held CI red for roughly 180 runs
    (tests/unit/test_render_determinism.py).
    """
    out: dict[str, str] = {}
    for path in sorted(schema_dir.rglob(SCHEMA_GLOB), key=lambda q: q.as_posix()):
        for name in _DECLARATION_RE.finditer(path.read_text(encoding="utf-8")):
            out.setdefault(name.group("name"), path.name)
    return out


def undeclared_constraints(
    live: tuple[dict, ...] | list[dict], schema_dir: Path
) -> tuple[dict, ...]:
    """Live constraints the schema tree declares nowhere. Pure -- it opens no session.

    WHY THIS MATTERS, and it is the whole reason the check exists: CONSTRAINTS
    OUTLIVE DATA WIPES. A wipe is a data delete, not a database drop, so a census
    at a TRUE-ZERO node baseline still found 62 constraints. A clean graph is not
    a clean schema, and a retired label's constraint silently enforces an old
    identity rule against any future load that reuses the label.

    Never a drop, and not even a suggestion of one -- see the caller.
    """
    declared = declared_constraint_names_in_tree(schema_dir)
    return tuple(row for row in live if row.get("name") not in declared)
