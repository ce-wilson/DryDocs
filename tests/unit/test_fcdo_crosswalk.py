"""W1 — the FCDO vocabulary crosswalk (config/crosswalks/fcdo-vocabulary.yaml).

A VOCABULARY crosswalk, not an orchestrator one: it maps DryDocs ontology
terms onto the standard vocabularies the firmwide frameworks require. These
guards pin what the backlog acceptance demands:

- every row stays ``proposed`` (or ``blocked-on-recapture``) until the
  fcdo-crosswalk gate signs it — nothing in this file is confirmed by a commit;
- rows whose evidence sits in a named capture hole are ``blocked-on-recapture``,
  and the hole ledger agrees with the row statuses;
- the committed file and its gate prompt are mechanism-only (standard CURIEs,
  no internal names);
- the orchestrator runtime deliberately SKIPS the sibling schema, so the
  confirmed-orchestrator invariants of test_orchestration_crosswalk.py hold.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from drydocs.gate_pages import load_gate_spec
from drydocs_core.orchestration.crosswalk import (
    SIBLING_SCHEMA_IDS,
    load_crosswalks,
)

REPO = Path(__file__).resolve().parent.parent.parent
CROSSWALK = REPO / "config" / "crosswalks" / "fcdo-vocabulary.yaml"
GATE_PROMPT = REPO / "config" / "gate-prompts" / "fcdo-crosswalk.yaml"

VOCAB_SCHEMA_ID = "drydocs.vocab-crosswalk.v1"
ROW_STATUSES = {"proposed", "blocked-on-recapture"}


def _doc() -> dict:
    return yaml.safe_load(CROSSWALK.read_text(encoding="utf-8"))


def test_file_exists_and_declares_the_sibling_schema() -> None:
    doc = _doc()
    assert doc["schema"] == VOCAB_SCHEMA_ID
    assert VOCAB_SCHEMA_ID in SIBLING_SCHEMA_IDS, (
        "the orchestrator runtime does not recognize the vocabulary schema — "
        "load_crosswalks() would raise on this file"
    )
    assert doc["gate_spec"] == "config/gate-prompts/fcdo-crosswalk.yaml"
    assert (REPO / doc["gate_spec"]).is_file()


def test_nothing_is_confirmed_without_the_gate() -> None:
    doc = _doc()
    assert doc["status"] == "proposed", "file status flips only via a gate-log entry"
    assert doc["rows"], "no rows"
    for row in doc["rows"]:
        assert row["status"] in ROW_STATUSES, (
            f"row {row['n']}: status {row['status']!r} — confirmed is the gate's "
            "verb, never a commit's"
        )


def test_capture_hole_ledger_agrees_with_row_statuses() -> None:
    doc = _doc()
    blocked_by_status = {r["n"] for r in doc["rows"] if r["status"] == "blocked-on-recapture"}
    blocked_by_ledger = {n for h in doc["capture_holes"] for n in h["blocks_rows"]}
    assert blocked_by_status == blocked_by_ledger, (
        "a row and the capture-hole ledger disagree about what is blocked"
    )
    assert blocked_by_status, "the Descriptive Metadata hole blocks row 5; the fixture is stale"


def test_gate_prompt_covers_every_row() -> None:
    doc = _doc()
    spec = load_gate_spec(GATE_PROMPT)
    mapped = {m.n for m in spec.mapping}
    rows = {r["n"] for r in doc["rows"]}
    assert rows <= mapped, f"gate prompt is missing rows {rows - mapped}"


def test_committed_surfaces_are_mechanism_only() -> None:
    """Standard CURIEs only — internal namespace prefixes and org names stay
    in internal/ (backlog W1 acceptance; PUBLISH-BOUNDARY.md)."""
    for path in (CROSSWALK, GATE_PROMPT):
        text = path.read_text(encoding="utf-8").lower()
        for forbidden in ("jpmv", "jpmorgan"):
            assert forbidden not in text, f"{path.name}: internal name {forbidden!r} committed"


def test_orchestrator_runtime_skips_the_vocabulary_crosswalk() -> None:
    walks = load_crosswalks()
    assert CROSSWALK not in {cw.path for cw in walks}, (
        "the vocabulary crosswalk leaked into the orchestrator registry"
    )
