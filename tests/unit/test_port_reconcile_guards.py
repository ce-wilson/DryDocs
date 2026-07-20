"""J7 — executable per-entry port reconciler guards (PORT-MANIFEST entry_rules).

The manifest's `per-entry` rows carry prose entry_rules; these are those rules as
code (docs/reviews/tech-debt-port-boundary.md Phase 2). Same YAML loading idiom
as the map guard (pytest + yaml.safe_load) — no second parser.

Three rules:

* **Status no-downgrade** — a merge may never downgrade
  relationship_vocabulary.yaml ``active`` → planned/deprecated/removed, nor
  taxonomy-ontology-map.yaml ``confirmed``/``applied`` → proposed; and a
  consumer entry may never simply VANISH (per-entry means union of entries).
* **Append-only** — union-append audit files (config/gate-log.md): the
  pre-merge text must be a byte prefix of the merged text.
* **Version-string rule** — asserted in test_port_manifest.py (the manifest row
  itself is the contract).

Consumer-side usage during reconcile-port (documented in that skill):

    1. BEFORE applying the port, snapshot the consumer copies:
         mkdir %TEMP%/reconcile-before
         cp drydocs_core/ontology/relationship_vocabulary.yaml \
            config/taxonomy-ontology-map.yaml config/gate-log.md  <before-dir>/
    2. Apply the port range / resolve collisions.
    3. RECONCILE_BEFORE_DIR=<before-dir> pytest tests/unit/test_port_reconcile_guards.py -q
       → FAILS on any downgrade / dropped entry / audit truncation the merge introduced.

Without RECONCILE_BEFORE_DIR the live-comparison tests SKIP; the fixture-driven
mechanics tests run everywhere (producer CI included).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable, Mapping

import pytest

yaml = pytest.importorskip("yaml")

REPO = Path(__file__).resolve().parents[2]
VOCAB_FILE = REPO / "drydocs_core" / "ontology" / "relationship_vocabulary.yaml"
MAP_FILE = REPO / "config" / "taxonomy-ontology-map.yaml"
GATE_LOG = REPO / "config" / "gate-log.md"

BEFORE_DIR_ENV = "RECONCILE_BEFORE_DIR"

# entry_rule: "NEVER downgrade a consumer entry whose status is active ... to
# the producer's planned/deprecated" (+ removed, a fortiori)
VOCAB_DOWNGRADES: dict[str, set[str]] = {"active": {"planned", "deprecated", "removed"}}
# entry_rule: "NEVER downgrade confirmed/applied -> proposed"
MAP_DOWNGRADES: dict[str, set[str]] = {
    "confirmed": {"proposed"},
    "applied": {"proposed"},
}


# --- the executable rules (pure) -------------------------------------------------

def status_downgrades(
    before: Iterable[Mapping[str, Any]],
    after: Iterable[Mapping[str, Any]],
    *,
    key: str,
    downgrade_map: dict[str, set[str]],
    status_field: str = "status",
) -> list[str]:
    """Violations a merge introduced: banned status transitions + dropped entries."""
    after_by = {e[key]: e for e in after}
    violations: list[str] = []
    for entry in before:
        k, status = entry[key], entry.get(status_field)
        merged = after_by.get(k)
        if merged is None:
            violations.append(f"{k}: entry DROPPED by the merge (was {status!r})")
        elif merged.get(status_field) in downgrade_map.get(status, set()):
            violations.append(
                f"{k}: status downgraded {status!r} -> {merged.get(status_field)!r}"
            )
    return violations


def append_only_violation(before_text: str, after_text: str) -> str | None:
    """None if ``before_text`` is a byte prefix of ``after_text``; else a message."""
    if after_text.startswith(before_text):
        return None
    limit = min(len(before_text), len(after_text))
    at = next(
        (i for i in range(limit) if before_text[i] != after_text[i]), limit
    )
    return (
        f"append-only violated: merged file diverges from the pre-merge text at "
        f"char {at} (existing entries must be a prefix — dropping or editing "
        "either side's audit entries is an audit violation)"
    )


def vocab_entries(doc: dict) -> list[dict]:
    return doc["local_relationships"]


def map_entries(doc: dict) -> list[dict]:
    return doc["mappings"]


# --- fixture-driven mechanics (run everywhere) ------------------------------------

_VOCAB_BEFORE = [
    {"id": "m3_active_edge", "status": "active"},
    {"id": "m3_planned_edge", "status": "planned"},
]


def test_vocab_active_downgrade_fails() -> None:
    after = [
        {"id": "m3_active_edge", "status": "planned"},   # producer clobbered it
        {"id": "m3_planned_edge", "status": "planned"},
    ]
    violations = status_downgrades(
        _VOCAB_BEFORE, after, key="id", downgrade_map=VOCAB_DOWNGRADES
    )
    assert violations == ["m3_active_edge: status downgraded 'active' -> 'planned'"]


def test_vocab_upgrade_and_new_entries_pass() -> None:
    after = [
        {"id": "m3_active_edge", "status": "active"},
        {"id": "m3_planned_edge", "status": "active"},    # upgrade: fine
        {"id": "m3_brand_new", "status": "planned"},      # union: fine
    ]
    assert status_downgrades(
        _VOCAB_BEFORE, after, key="id", downgrade_map=VOCAB_DOWNGRADES
    ) == []


def test_dropped_entry_fails() -> None:
    violations = status_downgrades(
        _VOCAB_BEFORE, [{"id": "m3_planned_edge", "status": "planned"}],
        key="id", downgrade_map=VOCAB_DOWNGRADES,
    )
    assert violations == ["m3_active_edge: entry DROPPED by the merge (was 'active')"]


def test_map_confirmed_and_applied_downgrades_fail() -> None:
    before = [
        {"id": "folder-scheduled-on", "status": "confirmed"},
        {"id": "job-was-informed-by", "status": "applied"},
    ]
    after = [
        {"id": "folder-scheduled-on", "status": "proposed"},
        {"id": "job-was-informed-by", "status": "proposed"},
    ]
    violations = status_downgrades(before, after, key="id", downgrade_map=MAP_DOWNGRADES)
    assert len(violations) == 2 and all("downgraded" in v for v in violations)


def test_gate_log_append_only_mechanics() -> None:
    before = "# HITL gate log\n\n## 2026-06-21 - C1\n- Confirmed: 4\n"
    appended = before + "\n## 2026-07-11 - new gate\n- Confirmed: 1\n"
    assert append_only_violation(before, appended) is None
    truncated = before[:-10]
    assert "append-only violated" in append_only_violation(before, truncated)
    edited = before.replace("Confirmed: 4", "Confirmed: 3") + "\n## later\n"
    assert "append-only violated" in append_only_violation(before, edited)


def test_current_files_pass_their_own_rules() -> None:
    """Sanity: each real file vs itself is violation-free (loaders + rules wire up)."""
    vocab = yaml.safe_load(VOCAB_FILE.read_text(encoding="utf-8"))
    assert status_downgrades(
        vocab_entries(vocab), vocab_entries(vocab), key="id", downgrade_map=VOCAB_DOWNGRADES
    ) == []
    mapping = yaml.safe_load(MAP_FILE.read_text(encoding="utf-8"))
    assert status_downgrades(
        map_entries(mapping), map_entries(mapping), key="id", downgrade_map=MAP_DOWNGRADES
    ) == []
    text = GATE_LOG.read_text(encoding="utf-8")
    assert append_only_violation(text, text) is None


# --- consumer-side live comparison (env-gated; the reconcile-port step) -----------

_needs_before = pytest.mark.skipif(
    not os.environ.get(BEFORE_DIR_ENV),
    reason=f"{BEFORE_DIR_ENV} not set — consumer-side reconcile check only",
)


@_needs_before
def test_reconcile_vocab_no_downgrade_live() -> None:
    before_dir = Path(os.environ[BEFORE_DIR_ENV])
    before = yaml.safe_load(
        (before_dir / "relationship_vocabulary.yaml").read_text(encoding="utf-8")
    )
    after = yaml.safe_load(VOCAB_FILE.read_text(encoding="utf-8"))
    violations = status_downgrades(
        vocab_entries(before), vocab_entries(after), key="id", downgrade_map=VOCAB_DOWNGRADES
    )
    assert not violations, "\n".join(violations)


@_needs_before
def test_reconcile_map_no_downgrade_live() -> None:
    before_dir = Path(os.environ[BEFORE_DIR_ENV])
    before = yaml.safe_load(
        (before_dir / "taxonomy-ontology-map.yaml").read_text(encoding="utf-8")
    )
    after = yaml.safe_load(MAP_FILE.read_text(encoding="utf-8"))
    violations = status_downgrades(
        map_entries(before), map_entries(after), key="id", downgrade_map=MAP_DOWNGRADES
    )
    assert not violations, "\n".join(violations)


@_needs_before
def test_reconcile_gate_log_append_only_live() -> None:
    before_dir = Path(os.environ[BEFORE_DIR_ENV])
    before = (before_dir / "gate-log.md").read_text(encoding="utf-8")
    after = GATE_LOG.read_text(encoding="utf-8")
    violation = append_only_violation(before, after)
    assert violation is None, violation
