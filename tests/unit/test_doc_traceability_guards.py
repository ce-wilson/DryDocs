"""L17 — the Q8-family loud-refusal guards on the doc-traceability loaders.

DocTraceabilityLoader (SPECIFIED_IN) and DocFeedbackLoader (ANNOTATES,
WAS_ATTRIBUTED_TO) MATCH — never MERGE — nodes a DIFFERENT loader writes, so
each had two ways to "succeed" while silently writing no links (instances
six and seven of the "succeeds loudly, does nothing" family: G29, G30, Q8,
both batch_port halves, these two). These tests pin: absent prereq -> loud
refusal, nothing written (not even the :JobRun); present prereq -> per-row
misses COUNTED and listed, never silent. No Neo4j — the client is faked the
same way test_batch_port_orchestrator does it.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from drydocs.loaders.doc_traceability import (
    DesignDocFeedbackAdapter,
    DocFeedbackLoader,
    DocTraceabilityLoader,
)
from drydocs_core.models.doc_traceability import DESIGN_DOCS_ORIGIN

REPO = Path(__file__).resolve().parents[2]
TRACE_CYPHER = REPO / "drydocs" / "loaders" / "cypher" / "doc_traceability.cypher"
FEEDBACK_CYPHER = REPO / "drydocs" / "loaders" / "cypher" / "doc_feedback.cypher"


class _FakeAdapter:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def __enter__(self) -> _FakeAdapter:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def rows(self) -> Iterator[dict]:
        # a generator each call — re-enterable, like the real file-backed
        # adapters (the feedback loader pre-scans for authors, then loads)
        yield from self._rows


class _FakeClient:
    """Stands in for the graph: which (doc_id, anchor) sections and which
    employee ids actually exist. Both start empty in a fresh database —
    exactly the silent-success cases these tests pin down."""

    def __init__(self, sections: set[tuple[str, str]], employees: set[str] = frozenset()) -> None:
        self.sections = sections
        self.employees = set(employees)
        self.run_calls: list[tuple[str, dict]] = []
        self.run_script_calls: list[tuple[str, dict]] = []

    def run(self, cypher: str, params: dict | None = None, **kwargs) -> list[dict]:
        bind = {**(params or {}), **kwargs}
        self.run_calls.append((cypher, bind))
        if "AS found" in cypher:
            if "(n:DocSection)" in cypher:
                return [{"found": len(self.sections)}]
            if "(n:Employee)" in cypher:
                return [{"found": len(self.employees)}]
            return [{"found": 0}]
        if "UNWIND $anchors AS p" in cypher:
            return [
                {"origin": p["origin"], "doc_id": p["doc_id"], "anchor": p["anchor"]}
                for p in bind["anchors"]
                if (p["doc_id"], p["anchor"]) in self.sections
            ]
        if "UNWIND $authors AS a" in cypher:
            return [{"employee_id": a} for a in bind["authors"] if a in self.employees]
        if "SHOW INDEXES" in cypher:
            return []
        if "AS rows_changed" in cypher:
            return [{"rows_changed": 0}]
        return []

    def run_script(self, script: str, params: dict | None = None) -> None:
        self.run_script_calls.append((script, dict(params or {})))

    def flushed_rows(self) -> list[dict]:
        rows: list[dict] = []
        for _, bind in self.run_calls:
            rows.extend(bind.get("batch", []))
        for _, params in self.run_script_calls:
            rows.extend(params.get("batch", []))
        return rows


def _trace_row(requirement_id: str, anchors: list[str]) -> dict:
    return {
        "origin": DESIGN_DOCS_ORIGIN,
        "doc_id": "synth-tdd",
        "requirement_id": requirement_id,
        "kind": "FR",
        "description": "synthetic",
        "section_anchors": anchors,
        "components": ["synth.py"],
        "tests": [{"kind": "unit", "ref": "test_synth"}],
        "matrix_status": "open",
    }


def _note_row(anchor: str, author: str | None = None) -> dict:
    return {
        "origin": DESIGN_DOCS_ORIGIN,
        "doc_id": "synth-tdd",
        "doc_rev": 1,
        "anchor": anchor,
        "base_anchor": anchor,
        "note": "a synthetic note",
        "status": "open",
        "author": author,
    }


def _trace_loader(client: _FakeClient, rows: list[dict]) -> DocTraceabilityLoader:
    return DocTraceabilityLoader(client, _FakeAdapter(rows), run_log=False)


def _feedback_loader(client: _FakeClient, rows: list[dict]) -> DocFeedbackLoader:
    return DocFeedbackLoader(client, _FakeAdapter(rows), run_log=False)


# ---- absent prereq -> loud refusal, nothing written ---------------------------


def test_traceability_refuses_on_empty_section_registry() -> None:
    client = _FakeClient(sections=set())
    with pytest.raises(RuntimeError, match="no :DocSection nodes are reachable"):
        _trace_loader(client, [_trace_row("FR-S-001", ["design"])]).load()


def test_feedback_refuses_on_empty_section_registry() -> None:
    client = _FakeClient(sections=set(), employees={"E1"})
    with pytest.raises(RuntimeError, match="no :DocSection nodes are reachable"):
        _feedback_loader(client, [_note_row("design")]).load()


def test_refusal_writes_nothing_not_even_the_job_run() -> None:
    """The _preflight_indexes convention: refusal lands before _open_run, so
    a refused load leaves no :JobRun behind to look successful."""
    for loader in (
        _trace_loader(_FakeClient(sections=set()), [_trace_row("FR-S-001", ["a"])]),
        _feedback_loader(_FakeClient(sections=set()), [_note_row("a")]),
    ):
        with pytest.raises(RuntimeError):
            loader.load()
        client = loader.client
        assert not client.flushed_rows()
        assert not [c for c, _ in client.run_calls if "MERGE (run:JobRun" in c]


def test_prereq_probes_exclude_schema_meta_exemplars() -> None:
    """A bare count() would count the :SchemaMeta:<Label> exemplar and wave
    an empty registry straight through (the O33 contamination, write side)."""
    client = _FakeClient(sections=set())
    with pytest.raises(RuntimeError):
        _trace_loader(client, [_trace_row("FR-S-001", ["a"])]).load()
    probes = [c for c, _ in client.run_calls if "AS found" in c]
    assert probes, "no prereq probe was issued"
    for probe in probes:
        assert "NOT n:SchemaMeta" in probe
        assert "IS NOT NULL" in probe


def test_feedback_refuses_authored_batch_against_empty_employee_registry() -> None:
    client = _FakeClient(sections={("synth-tdd", "design")}, employees=set())
    with pytest.raises(RuntimeError, match="no :Employee nodes are reachable"):
        _feedback_loader(client, [_note_row("design", author="E1")]).load()


def test_feedback_authorless_batch_loads_without_employee_registry() -> None:
    """The Employee prereq is conditional: attribution is optional-by-design
    (gate C1), so an author-less batch must not be hostage to it."""
    client = _FakeClient(sections={("synth-tdd", "design")}, employees=set())
    summary = _feedback_loader(client, [_note_row("design")]).load()
    assert summary.status == "OK"
    assert summary.rows_processed == 1


# ---- present prereq -> per-row misses counted, never silent -------------------


def test_traceability_unmatched_anchors_are_listed() -> None:
    client = _FakeClient(sections={("synth-tdd", "design")})
    loader = _trace_loader(
        client,
        [_trace_row("FR-S-001", ["design"]), _trace_row("FR-S-002", ["ghost-anchor"])],
    )
    summary = loader.load()
    assert summary.status == "OK"
    assert loader.unmatched_anchors == [{"doc_id": "synth-tdd", "anchor": "ghost-anchor"}]


def test_traceability_healthy_load_reports_no_misses() -> None:
    client = _FakeClient(sections={("synth-tdd", "design"), ("synth-tdd", "verify")})
    loader = _trace_loader(client, [_trace_row("FR-S-001", ["design", "verify"])])
    loader.load()
    assert loader.unmatched_anchors == []


def test_feedback_unmatched_anchor_and_unknown_author_are_listed() -> None:
    """Both per-row miss channels at once: the mis-cited anchor and the
    unknown author each land in their own report, and the load still
    completes (one bad row must not cost the others their edges)."""
    client = _FakeClient(sections={("synth-tdd", "design")}, employees={"E1"})
    loader = _feedback_loader(
        client,
        [_note_row("design", author="E1"), _note_row("ghost-anchor", author="E9")],
    )
    summary = loader.load()
    assert summary.status == "OK"
    assert loader.unmatched_anchors == [{"doc_id": "synth-tdd", "anchor": "ghost-anchor"}]
    assert loader.unknown_authors == ["E9"]


def test_feedback_stray_files_reported_after_load(tmp_path: Path, caplog) -> None:
    """L20 — a misnamed export beside a good one: the load completes, the
    stray is listed and warned, never silently ignored (the 2026-07-28
    Copy-feedback dead end, made detectable)."""
    (tmp_path / "synth-tdd-rev1.yaml").write_text(
        "doc: synth-tdd\nnotes:\n  - anchor: design\n    note: fine\n",
        encoding="utf-8",
    )
    (tmp_path / "synth-tdd-rev1 - Copy.yaml").write_text("doc: synth-tdd\n", encoding="utf-8")
    client = _FakeClient(sections={("synth-tdd", "design")})
    loader = DocFeedbackLoader(client, DesignDocFeedbackAdapter(tmp_path), run_log=False)
    with caplog.at_level("WARNING"):
        summary = loader.load()
    assert summary.status == "OK"
    assert loader.stray_feedback_files == ["synth-tdd-rev1 - Copy.yaml"]
    assert "synth-tdd-rev1 - Copy.yaml" in caplog.text
    assert "NOT loaded" in caplog.text


def test_feedback_fake_adapter_without_stray_census_is_tolerated() -> None:
    """The report is duck-typed: an adapter with no stray_files census (the
    fakes here, any future row source) never breaks the load."""
    client = _FakeClient(sections={("synth-tdd", "design")})
    loader = _feedback_loader(client, [_note_row("design")])
    assert loader.load().status == "OK"
    assert loader.stray_feedback_files == []


# ---- the template documents where its prereq is enforced ----------------------


def test_cypher_headers_document_where_the_prereqs_are_enforced() -> None:
    """The templates cannot make the whole-registry check themselves (they
    run per batch), so their headers must point at the loader methods that
    do — otherwise the next person re-pointing a loader at another database
    re-opens the silent-success hole."""
    trace = TRACE_CYPHER.read_text(encoding="utf-8")
    assert "_assert_doc_sections_present" in trace
    assert "cannot span databases" in trace
    feedback = FEEDBACK_CYPHER.read_text(encoding="utf-8")
    assert "_assert_doc_sections_present" in feedback
    assert "_assert_employees_present_if_authored" in feedback
    assert "cannot span databases" in feedback
