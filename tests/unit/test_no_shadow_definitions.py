"""Guard: one definition per class name across the production packages.

Backlog C18, and step 1 of the "did the gate land?" problem.

A gate ruling lands in code, and later someone asks "did it land?" — they grep,
find the symbol, and answer. That answer is only trustworthy if the symbol has
ONE definition. It did not: all eight catalog row models existed twice, in
``drydocs_core/models/catalog.py`` and again in ``drydocs/loaders/catalog.py``,
and the ``drydocs_core`` copy was stale — missing ``sponsored_area_product_id``,
the field the C9 gate ruled in on 2026-07-18, plus the ``';' -> ','``
``seal_ids`` normalizer the real PAT report needs. Reading that copy answers
"the gate did NOT land" about a gate that landed correctly; reading the other
answers "it did". Both greps succeed, and nothing tells you which file is the
live one.

The shadow was worse than misleading. Its ``model_config`` is ``extra="ignore"``,
so had anything switched to it, the C9 column would have been dropped SILENTLY
at validation — leaving ``pat_product_mapping.cypher`` §3b permanently dead with
no error and no failing test. And the ADR 0002-A-1 migration direction points AT
``drydocs_core``, so a Phase-C move would have made the stale copy win by default.

So this guard is not a style rule. It removes a whole class of wrong answer:
you cannot read the wrong copy if there is not one. Detecting duplicates is
cheaper than reasoning about which duplicate is authoritative, every time.

Scope is deliberate:
- production packages only. Test modules legitimately define their own local
  fakes (``_FakeClient`` appears in several by design) — those are per-module
  fixtures, not competing definitions of a shared contract.
- top-level classes only. A class nested in a function or another class is
  scoped by construction and cannot be imported by the ambiguous path.
- private names (leading underscore) are exempt for the same reason: they are
  module-local by convention and are not what a "did it land?" grep resolves to.

ALLOWLIST is empty and should stay that way. A genuine same-name-different-thing
pair goes here WITH its reason — never silently.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PACKAGES = ("drydocs", "drydocs_core")

# name -> why two definitions are correct. Empty by design; adding an entry is a
# decision that needs a reason, not a way to silence the test.
ALLOWLIST: dict[str, str] = {}


def _top_level_classes() -> dict[str, list[str]]:
    """Map class name -> the repo-relative modules defining it at top level."""
    defined: dict[str, list[str]] = defaultdict(list)
    for package in PACKAGES:
        for py in sorted((REPO / package).rglob("*.py")):
            if "__pycache__" in py.parts:
                continue
            tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
            for node in tree.body:
                if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                    defined[node.name].append(py.relative_to(REPO).as_posix())
    return defined


def test_no_class_name_is_defined_in_two_modules() -> None:
    """No shadow definitions — the C18 guard."""
    duplicates = {
        name: sorted(set(paths))
        for name, paths in _top_level_classes().items()
        if len(set(paths)) > 1 and name not in ALLOWLIST
    }
    assert not duplicates, (
        "class name(s) defined in more than one production module — a 'did the "
        "gate land?' grep cannot be trusted while a shadow exists (C18):\n"
        + "\n".join(f"  {n}: {', '.join(p)}" for n, p in sorted(duplicates.items()))
        + "\nFix the duplication, or add the name to ALLOWLIST with its reason."
    )


def test_allowlist_entries_are_justified() -> None:
    """An allowlist entry without a reason is a silenced failure."""
    unjustified = [n for n, reason in ALLOWLIST.items() if not reason.strip()]
    assert not unjustified, f"ALLOWLIST entries need a reason: {unjustified}"


def test_the_catalog_shadow_stays_deleted() -> None:
    """The specific file this guard was born from.

    Pinned by path as well as by the general rule: the general rule only fires
    once the duplicate is back, and this makes the intent legible to whoever
    is tempted to restore it during the Phase-C move.
    """
    shadow = REPO / "drydocs_core" / "models" / "catalog.py"
    assert not shadow.exists(), (
        "drydocs_core/models/catalog.py is back. The catalog row models are "
        "defined in drydocs/loaders/catalog.py. If Phase C moves them here, "
        "MOVE them — do not copy, and delete the originals in the same commit."
    )
