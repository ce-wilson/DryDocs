"""Unit tests for graph_review (drydocs/review/graph_review.py) — pure, no Neo4j."""

from __future__ import annotations

from drydocs.review.graph_review import DEFAULT_HIDDEN_PROPS, group_rows, render_review
from drydocs.review.review_labels import ReviewLabels

_ROWS = {
    "ControlMFolder": [
        {"name": "CCB_DAILY", "folder_id": "F1", "_internal_id": 42, "version_serial": 7}
    ],
    "ControlMJob": [{"name": "load_x", "job_id": "J1"}, {"name": "load_y", "job_id": "J2"}],
}


def test_group_rows_splits_by_label() -> None:
    flat = [{"_label": "A", "x": 1}, {"_label": "A", "x": 2}, {"_label": "B", "y": 9}]
    grouped = group_rows(flat)
    assert set(grouped) == {"A", "B"}
    assert grouped["A"] == [{"x": 1}, {"x": 2}]
    assert "_label" not in grouped["B"][0]


def test_render_has_one_section_per_label_and_counts() -> None:
    out = render_review(_ROWS)
    assert "<h2>ControlMFolder" in out
    assert "<h2>ControlMJob" in out
    assert "load_x" in out and "load_y" in out


def test_hidden_props_are_stripped() -> None:
    out = render_review(_ROWS)
    assert "_internal_id" not in out  # private key hidden
    assert "version_serial" not in out  # default hidden bookkeeping
    assert "folder_id" in out  # normal prop shown


def test_default_hidden_props_contract() -> None:
    assert "version_serial" in DEFAULT_HIDDEN_PROPS


def test_provenance_from_backbone_on_header() -> None:
    backbone = ReviewLabels.from_dict(
        {
            "sources": [
                {
                    "id": "bmc-x",
                    "provenance": "vendor baseline",
                    "labels": ["ControlMFolder", "ControlMJob"],
                }
            ]
        }
    )
    out = render_review(_ROWS, review_labels=backbone)
    assert "bmc-x" in out and "vendor baseline" in out


def test_output_is_self_contained_html() -> None:
    out = render_review(_ROWS)
    assert out.startswith("<!doctype html>")
    assert "<style>" in out  # inline CSS, no external deps
    assert out.rstrip().endswith("</html>")
