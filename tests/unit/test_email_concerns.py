"""Q21 — the docs_email_concerns writer, every gate clause as a test.

Gate email-folder-assignment SIGNED 8/8 (2026-08-19); this file is the
acceptance's proof surface: the refusal fires (SS-A3), the source-signal pass
performs ZERO edges over the bundled samples (SS-B1 — the extract contract has
no structured field), the edge carries the ruled properties (SS-A2), and the
write is MATCH-only with the count reported. Offline: a recording client, no
graph (J18)."""

from __future__ import annotations

from pathlib import Path

import pytest

from drydocs.loaders.email_concerns import (
    ASSIGNED_BY,
    CYPHER_PATH,
    STRUCTURED_SIGNAL_FIELDS,
    AssignmentRefusedError,
    ConcernsAssignment,
    EmailConcernsWriter,
    extract_source_signal,
    validate,
)
from drydocs.loaders.email_extracts import EmailExtractsAdapter

SAMPLES = Path("drydocs/data/samples/email-extracts")

# Policy guard (test_skip_guard_policy): the samples are COMMITTED, so on a
# clean clone this never fires — a partial checkout skips instead of failing.
pytestmark = pytest.mark.skipif(not SAMPLES.exists(), reason="sample extracts absent")

_OK = ConcernsAssignment(
    doc_id="email:0001",
    endpoint_class="ControlMFolder",
    endpoint_key="F1",
    assigned_by="sme",
    evidence="SME ruling note 2026-08-27: incident thread names the folder",
)


class _RecordingClient:
    def __init__(self, written: int = 1) -> None:
        self.calls: list[tuple[str, dict]] = []
        self._written = written

    def run(self, cypher: str, params: dict | None = None, **kwargs):
        self.calls.append((cypher, {**(params or {}), **kwargs}))
        return [{"written": self._written}]


# -- SS-A3: no anonymous assignment — the refusal is a test, not a doc line ----


def test_missing_evidence_is_refused() -> None:
    with pytest.raises(AssignmentRefusedError, match="evidence"):
        validate(
            ConcernsAssignment(
                doc_id="email:0001",
                endpoint_class="ControlMFolder",
                endpoint_key="F1",
                assigned_by="sme",
                evidence="   ",
            )
        )


def test_unknown_assigned_by_is_refused() -> None:
    with pytest.raises(AssignmentRefusedError, match="assigned_by"):
        validate(
            ConcernsAssignment(
                doc_id="email:0001",
                endpoint_class="ControlMFolder",
                endpoint_key="F1",
                assigned_by="best-guess",
                evidence="x",
            )
        )
    assert ASSIGNED_BY == ("sme", "source-signal")


def test_unknown_endpoint_class_is_refused() -> None:
    with pytest.raises(AssignmentRefusedError, match="endpoint_class"):
        validate(
            ConcernsAssignment(
                doc_id="email:0001",
                endpoint_class="BusinessApplication",
                endpoint_key="x",
                assigned_by="sme",
                evidence="x",
            )
        )


def test_one_refused_assignment_refuses_the_whole_batch() -> None:
    """All-before-any (the G78 resolve-before-write pattern): a partial write
    cannot happen."""
    client = _RecordingClient()
    bad = ConcernsAssignment(
        doc_id="email:0002",
        endpoint_class="ControlMFolder",
        endpoint_key="F2",
        assigned_by="sme",
        evidence="",
    )
    with pytest.raises(AssignmentRefusedError):
        EmailConcernsWriter(client).assign([_OK, bad])
    assert client.calls == []  # nothing reached the graph


# -- SS-B1: structured field only — and the contract has none ------------------


def test_source_signal_pass_performs_zero_edges_over_the_bundled_samples() -> None:
    """The acceptance's own witness: the assumed extract contract has no
    structured folder/process field, so the source-signal path ships with no
    live producer. The declared field list being EMPTY is load-bearing."""
    assert STRUCTURED_SIGNAL_FIELDS == ()
    with EmailExtractsAdapter(SAMPLES) as adapter:
        rows = list(adapter.rows())
    assert rows, "bundled G47 samples parsed empty — the zero-edge claim would be vacuous"
    performed = extract_source_signal(rows)
    assert performed == ()
    client = _RecordingClient()
    summary = EmailConcernsWriter(client).assign(performed)
    assert summary == {"requested": 0, "written": 0, "unmatched": 0}
    assert client.calls == []


# -- SS-A2 + the write shape ---------------------------------------------------


def test_write_carries_the_ruled_properties_and_is_match_only() -> None:
    client = _RecordingClient(written=1)
    summary = EmailConcernsWriter(client).assign([_OK])
    assert summary == {"requested": 1, "written": 1, "unmatched": 0}
    cypher, params = client.calls[0]
    for token in ("endpoint_class", "assigned_by", "evidence", "vocab_id"):
        assert token in cypher
    assert "MERGE (d)-[r:CONCERNS]->(t)" in cypher
    assert "MERGE (t" not in cypher and "MERGE (d:" not in cypher  # MATCH-only endpoints
    assert params["rows"][0]["assigned_by"] == "sme"


def test_unmatched_endpoints_are_counted_never_silent() -> None:
    client = _RecordingClient(written=0)
    summary = EmailConcernsWriter(client).assign([_OK])
    assert summary == {"requested": 1, "written": 0, "unmatched": 1}


def test_the_cypher_is_the_named_exemption_and_keeps_the_k7_fence() -> None:
    """SS-C1 travels in the file itself: the one authorized writer states the
    aboutness-never-attribution fence where the next reader meets it."""
    text = CYPHER_PATH.read_text(encoding="utf-8")
    assert "K7" in text and "CONCERNS" in text
    assert CYPHER_PATH.name == "email_concerns.cypher"
