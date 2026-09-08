"""dispositions.py — the ONE reading of PORT-MANIFEST.yaml's disposition rows (PORT6).

WHY THIS IS A MODULE AND NOT A HELPER INSIDE ONE SCRIPT. ``PORT-MANIFEST.yaml`` owns
disposition and nothing else may assert it (J68). Until 2026-09-08 the classifier that
turns a path into its disposition lived in ``scripts/render_port_dispositions.py`` and
the glob matcher it needs lived in a TEST module. The roll-close completeness check
(PORT6) needs the same answer for the same path, and a second reading of the manifest —
another loop over the rows, another glob matcher — is how two instruments come to
disagree about one file. The consumer's 2026-09-08 by-hand sweep and RELAY-35 already
did exactly that: the sweep called a ``drydocs/data/**`` sample "owed" and the manifest
says never-port. So there is one ``classify`` and both callers import it; a guard asserts
the renderer's name IS this function.

WHAT THE MATCH RULE IS. Rows are first-match-wins in file order
(``test_no_row_is_shadowed_by_an_earlier_glob`` guarantees a specific row precedes the
glob that would swallow it). ``default_ok`` is consulted only after every row misses,
which is what makes "deliberately default" (J16) distinguishable from "nobody thought
about it" (``DEFAULT``). ``**`` spans separators; ``*`` and ``?`` do not — so
``drydocs/review/publishing/**`` covers a subtree while ``docs/*.md`` stays at one level
and cannot quietly swallow ``docs/decisions/adr.md``. That distinction is the allowlist's
"prefer a narrow pattern" rule; ``fnmatch`` would erase it.

Pure functions over a loaded document; no repository, no I/O beyond ``load_manifest``.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

#: What ``classify`` returns for a path no row and no default_ok entry names — the
#: manifest's ``default:`` rule applies and nothing records that anyone decided so.
DEFAULT = "DEFAULT"

#: What ``classify`` returns for a path named under ``default_ok`` — the default ON
#: PURPOSE (J16); the row exists to say someone thought about it.
DEFAULT_OK = "default_ok"


def glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Compile a manifest path glob, anchored (``**`` spans ``/``; ``*`` and ``?`` do not)."""
    out: list[str] = []
    i = 0
    while i < len(pattern):
        if pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out) + r"\Z")


def matches(pattern: str, path: str) -> bool:
    """True when ``pattern`` (a literal path or a manifest glob) names ``path``."""
    return pattern == path or glob_to_regex(pattern).match(path) is not None


def classify(path: str, doc: dict) -> tuple[str, str, str]:
    """``(disposition, matching pattern, entry_rule)`` for one path — first match wins."""
    for row in doc["rows"]:
        pattern = row["path"]
        if matches(pattern, path):
            return row["disposition"], pattern, (row.get("entry_rule") or "").strip()
    for row in doc.get("default_ok") or []:
        pattern = row["path"]
        if matches(pattern, path):
            return DEFAULT_OK, pattern, ""
    return DEFAULT, "(no row)", ""


def load_manifest(path: Path) -> dict:
    """The manifest document the classifier reads — the CONSUMER's copy when run there."""
    return yaml.safe_load(path.read_text(encoding="utf-8"))
