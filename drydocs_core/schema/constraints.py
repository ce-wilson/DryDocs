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
