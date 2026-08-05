"""Runbook CURRENCY — do the things a runbook names still exist?

The sibling guard (``test_runbook_coverage.py``, V1) proves a module HAS a
runbook. It says nothing about whether that runbook is TRUE, and on 2026-08-04
that gap cost three separate catches, all by a person noticing rather than a
test:

* the mapping-store runbook had been missing K9's ``app_code_mapping`` for a day
  and carried a "nothing here can lose data" rule S4 had just falsified;
* the drydocs-core runbook copied the topology database list inline and named
  ``ddlineage`` hours before the X1 amendment retired it;
* the drydocs-api runbook cited ``tests/unit/test_guard.py`` as its oracle — a
  file that does not exist.

Coverage and currency are different problems and only the first had a test. This
is the second.

WHAT IT CAN AND CANNOT DO. It checks that named things EXIST: repo-relative file
paths in backticks, and ``drydocs`` CLI verbs. It cannot check that a sentence is
still true — "nothing here can lose data" is not detectable by grep, and neither
was the stale database enumeration. So this narrows the gap rather than closing
it, which is why the runbooks also ship re-derive one-liners with the rule that
the CODE wins on disagreement. A pointer cannot go stale; only a copy can.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DESIGN_DIR = REPO_ROOT / "docs" / "design"

#: Paths a runbook names that are NOT claims about the current tree. Each needs a
#: reason — the exemption IS the reason, same idiom as MODULE_EXEMPT.
HISTORICAL_PATHS: dict[str, str] = {
    "docs/runbook-mapping-demo.md": (
        "front-matter history — the demo runbook records where it was RELOCATED FROM "
        "at the L14 refit. A former path is a fact about the past, not a claim that it exists"
    ),
}

#: Extensions worth checking. Deliberately narrow: prose mentions plenty of
#: things that look path-like, and a guard with false positives gets muted.
_PATH = re.compile(
    r"`([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:py|md|yaml|yml|cypher|sql|json|html|ps1|sh|csv|xlsx))`"
)
_VERB = re.compile(r"drydocs\s+([a-z][a-z0-9-]{2,})")

#: `drydocs load <name>` / `drydocs check` — the first is a subcommand argument,
#: not a verb; the second is real but reads as a word elsewhere.
_NOT_VERBS = {"load", "check"}


def _runbooks() -> dict[str, str]:
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(DESIGN_DIR.glob("*-runbook.md"))}


def _cli_verbs() -> set[str]:
    out = subprocess.run(
        ["poetry", "run", "drydocs", "--help"], capture_output=True, text=True, cwd=REPO_ROOT
    )
    if out.returncode != 0:
        pytest.skip("drydocs CLI unavailable")
    return set(re.findall(r"^\|?\s*([a-z][a-z0-9-]+)\s", out.stdout, re.M))


def test_every_path_a_runbook_names_exists() -> None:
    """A runbook that points at a file which moved sends its reader nowhere.

    Three of the four found on 2026-08-04 were the S5 monolith->directory split
    and a package relocate: the kind of change that updates every importer
    automatically and every DOCUMENT not at all.

    BACKTICKS ARE AN EXISTENCE CLAIM. A rev note explaining that an earlier
    revision cited the wrong path must NOT backtick the dead name -- quote it as
    plain text. This guard caught exactly that case on its first run, in the very
    note describing the error it was written for.
    """
    failures: list[str] = []
    for name, text in _runbooks().items():
        for path in sorted(set(_PATH.findall(text))):
            if "/" not in path or path in HISTORICAL_PATHS:
                continue
            if not (REPO_ROOT / path).exists():
                failures.append(f"{name}: `{path}` does not exist")
    assert not failures, (
        f"{len(failures)} runbook path(s) name something that is not there — fix the path, "
        "or add it to HISTORICAL_PATHS with the reason it is a statement about the past:\n"
        + "\n".join(failures)
    )


def test_every_cli_verb_a_runbook_names_is_registered() -> None:
    """A documented command that no longer exists is worse than an undocumented
    one: the reader trusts it and only finds out at the prompt."""
    verbs = _cli_verbs()
    failures: list[str] = []
    for name, text in _runbooks().items():
        for verb in sorted(set(_VERB.findall(text))):
            if verb in _NOT_VERBS or verb in verbs:
                continue
            failures.append(f"{name}: `drydocs {verb}` is not a registered command")
    assert not failures, f"{len(failures)} stale CLI verb(s):\n" + "\n".join(failures)


def test_historical_exemptions_carry_a_reason_and_are_still_cited() -> None:
    """Shrink-only, the N2 LEDGER_PENDING idiom: an exemption for a path nobody
    cites any more is dead weight that outlives the reason it was added."""
    empty = [p for p, why in HISTORICAL_PATHS.items() if not why.strip()]
    assert not empty, f"exemption without a reason: {empty}"

    all_text = "\n".join(_runbooks().values())
    unused = [p for p in HISTORICAL_PATHS if f"`{p}`" not in all_text]
    assert (
        not unused
    ), f"HISTORICAL_PATHS names a path no runbook cites any more — remove it: {unused}"
