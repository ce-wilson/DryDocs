"""O28 node-status envelope — the derivation and its wire spec.

The contract lives in ``knowledge/standards/node-status-envelope.md``: one shape
({type, level, message, error?}) carried by every producer, ALWAYS derived and
never hand-authored, with new sources adding namespaced TYPES rather than new
shapes.

``status_items_for`` is deliberately a pure function of the run summary, which
is what makes "always derived" a testable property instead of a promise —
these tests need no database.
"""

from __future__ import annotations

import json
import pathlib

from drydocs.loaders.base import (
    STATUS_LEVELS,
    STATUS_SOURCE,
    LoadSummary,
    status_items_for,
)
from drydocs_api.query_specs import QUERY_SPECS

_CONTRACT_DOC = (
    pathlib.Path(__file__).resolve().parents[2]
    / "knowledge"
    / "standards"
    / "node-status-envelope.md"
)


def _summary(**kw) -> LoadSummary:
    base = {
        "loader": "unit_probe.v1",
        "run_id": "run-1",
        "started_at": "2026-08-01T00:00:00Z",
        "status": "OK",
    }
    return LoadSummary(**{**base, **kw})


def test_a_clean_run_emits_no_items():
    """'No items' means healthy. An all-clear item would make healthy and
    never-observed render identically — the failure mode where a dashboard is
    green because nothing is watching. 'Never ran' is the ABSENCE of a :JobRun.
    """
    assert status_items_for(_summary(rows_processed=120)) == []


def test_rejected_rows_become_one_warning_carrying_the_first_error():
    items = status_items_for(
        _summary(
            rows_processed=117,
            rows_rejected=3,
            rejects=[{"row_index": 7, "errors": [{"loc": ("name",)}]}],
        )
    )
    assert len(items) == 1
    item = items[0]
    assert item["type"] == f"{STATUS_SOURCE}/rows-rejected"
    assert item["level"] == "warning"
    assert "3 of 120" in item["message"]  # processed + rejected = rows seen
    assert "row 7" in item["error"]


def test_reject_detail_is_a_signal_not_a_log():
    """100 rejects produce ONE item, not 100. The envelope is a health signal;
    the full stream stays in the per-run log file."""
    items = status_items_for(
        _summary(
            rows_rejected=100,
            rejects=[{"row_index": i, "errors": []} for i in range(100)],
        )
    )
    assert len(items) == 1


def test_failure_and_drift_each_get_their_own_namespaced_type():
    items = status_items_for(_summary(status="FAILED", nodes_marked_removed=4, nodes_reactivated=2))
    by_type = {i["type"]: i for i in items}
    assert by_type[f"{STATUS_SOURCE}/run-failed"]["level"] == "error"
    assert by_type[f"{STATUS_SOURCE}/removed-from-source"]["level"] == "warning"
    assert by_type[f"{STATUS_SOURCE}/reactivated"]["level"] == "info"


def test_an_unresolved_parent_count_is_a_warning_item():
    """C22 §c ruled EMIT over property-only: the per-node `orphan` flag is the
    durable record, but a property alone is invisible in the loads grid — a
    green run over a hierarchy with holes is the silent miss one level up."""
    items = status_items_for(_summary(unresolved_parents=3))
    assert len(items) == 1
    assert items[0]["type"] == f"{STATUS_SOURCE}/unresolved-parent"
    assert items[0]["level"] == "warning"
    assert "3" in items[0]["message"]


def test_every_item_matches_the_one_shape():
    """The rule that makes the envelope extensible: producers add namespaced
    TYPES, never fields. A new key here is the regression to catch."""
    items = status_items_for(
        _summary(
            status="FAILED",
            rows_rejected=1,
            rejects=[{"row_index": 0, "errors": []}],
            nodes_marked_removed=1,
            nodes_reactivated=1,
            unresolved_parents=1,
        )
    )
    assert items, "expected items for a summary with every condition set"
    for item in items:
        assert set(item) <= {"type", "level", "message", "error"}
        assert {"type", "level", "message"} <= set(item)
        assert item["level"] in STATUS_LEVELS
        assert item["type"].startswith(f"{STATUS_SOURCE}/")
        assert item["type"].count("/") == 1, "type is <source>/<slug>"
        assert json.loads(json.dumps(item))  # round-trips as stored


def test_items_serialize_to_the_json_strings_the_property_holds():
    """Storage is a list of JSON strings because Neo4j cannot hold a map inside
    a list property. Parallel lists were rejected: one mismatched append there
    silently mislabels an item's severity, whereas one string per item cannot
    desynchronise."""
    items = status_items_for(_summary(nodes_reactivated=2))
    encoded = [json.dumps(i, sort_keys=True) for i in items]
    assert json.loads(encoded[0])["type"] == f"{STATUS_SOURCE}/reactivated"


def test_status_items_spec_serves_the_envelope():
    spec = QUERY_SPECS["loads.status-items.v1"]
    assert spec.database == "drydocs"
    assert "UNWIND r.status_items AS status_item" in spec.cypher
    # Runs with an empty list are filtered out, so a row means a real signal.
    assert "size(r.status_items) > 0" in spec.cypher
    assert "status_item" in [c.name for c in spec.columns]


def test_the_contract_doc_exists_and_records_its_precedent_and_rules():
    text = _CONTRACT_DOC.read_text(encoding="utf-8")
    assert "status.items" in text and "Backstage" in text
    assert "NAMESPACED TYPES, never new shapes" in text
    assert "Never hand-authored" in text
    # The producer table must name the shipped producer, or the doc drifts from
    # the code the first time someone adds the second one.
    assert STATUS_SOURCE in text
    assert "status_items_for" in text
