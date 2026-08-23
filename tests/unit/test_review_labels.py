"""Unit tests for the review backbone (drydocs/review_labels.py) — pure, no Neo4j."""

from __future__ import annotations

import pytest

from drydocs.review_labels import (
    ReviewLabels,
    ReviewLabelsError,
    UnknownReviewSourceError,
)

_DOC = {
    "classification": "Internal-Public",
    "sources": [
        {"id": "src-a", "provenance": "vendor", "labels": ["ControlMFolder", "ControlMJob"]},
        {"id": "src-b", "provenance": "grounded", "labels": ["ControlMJob", "JobRun"]},
    ],
}


def test_from_dict_parses_sources() -> None:
    rl = ReviewLabels.from_dict(_DOC)
    assert rl.sources() == ["src-a", "src-b"]
    assert rl.classification == "Internal-Public"


def test_labels_for_returns_chain_order() -> None:
    rl = ReviewLabels.from_dict(_DOC)
    assert rl.labels_for("src-a") == ("ControlMFolder", "ControlMJob")


def test_all_labels_is_distinct_first_seen() -> None:
    rl = ReviewLabels.from_dict(_DOC)
    # ControlMJob appears in both sources but only once, in first-seen order
    assert rl.all_labels() == ["ControlMFolder", "ControlMJob", "JobRun"]


def test_unknown_source_raises() -> None:
    rl = ReviewLabels.from_dict(_DOC)
    assert "src-a" in rl
    assert "missing" not in rl
    with pytest.raises(UnknownReviewSourceError):
        rl.labels_for("missing")


@pytest.mark.parametrize(
    "bad",
    [
        {"sources": "not-a-list"},
        {"sources": [{"provenance": "x", "labels": ["A"]}]},  # missing id
        {"sources": [{"id": "x", "labels": []}]},  # empty labels
        {"sources": [{"id": "x", "labels": ["A"]}, {"id": "x", "labels": ["B"]}]},  # dup id
    ],
)
def test_malformed_docs_raise(bad: dict) -> None:
    with pytest.raises(ReviewLabelsError):
        ReviewLabels.from_dict(bad)


def test_committed_backbone_loads_and_is_publishable() -> None:
    """The real config/review-labels.yaml parses and is committed at a publishable tier."""
    rl = ReviewLabels.load()
    assert rl.sources(), "committed backbone should declare sources"
    assert rl.classification in {
        "External",
        "Internal-Public",
    }, "committed review backbone must stay within the public-producer ceiling"
    # grounded in real schema labels
    assert "ControlMJob" in rl.all_labels()
