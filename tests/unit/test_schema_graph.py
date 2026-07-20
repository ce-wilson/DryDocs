"""Drift guard for the generated schema meta-graph (backlog C8).

``drydocs_core/schema/schema_graph.cypher`` is a DERIVED VIEW of
``drydocs_core/ontology/relationship_vocabulary.yaml`` (the confirmed source of
truth for edge meaning), rendered deterministically by
``drydocs_core.ontology.schema_graph`` via ``scripts/render_schema_graph.py``.
Same committed-render-matches-source idiom as the plan board: the tests here
re-render the vocabulary in-memory and fail when the committed file has drifted,
so the meta-graph can never silently stale again.
"""
from __future__ import annotations

import re
from pathlib import Path

from drydocs_core.ontology.schema_graph import (
    DEFAULT_OUTPUT_PATH,
    DEFAULT_VOCAB_PATH,
    RENDERED_STATUSES,
    render_schema_graph,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMITTED_FILE = REPO_ROOT / "drydocs_core" / "schema" / "schema_graph.cypher"


def test_default_paths_point_into_the_repo() -> None:
    assert DEFAULT_VOCAB_PATH.exists(), f"Missing: {DEFAULT_VOCAB_PATH}"
    assert DEFAULT_OUTPUT_PATH == COMMITTED_FILE


def test_committed_schema_graph_matches_vocabulary() -> None:
    """THE drift guard: the committed render must match an in-memory render of
    the vocabulary. If this fails, the vocabulary changed without regenerating —
    run:  poetry run python scripts/render_schema_graph.py
    """
    expected = render_schema_graph(DEFAULT_VOCAB_PATH)
    committed = COMMITTED_FILE.read_text(encoding="utf-8")
    assert committed == expected, (
        "schema_graph.cypher is STALE relative to relationship_vocabulary.yaml "
        "(or was hand-edited — it is a generated file). Regenerate it:\n"
        "    poetry run python scripts/render_schema_graph.py"
    )


def test_render_is_deterministic() -> None:
    assert render_schema_graph() == render_schema_graph()


def test_render_carries_no_timestamps() -> None:
    """Determinism: no dates/build times may appear in the generated output."""
    out = render_schema_graph()
    assert not re.search(r"\d{4}-\d{2}-\d{2}", out), (
        "generated schema_graph must not embed dates (deterministic render)"
    )


def test_acceptance_edges_present() -> None:
    """The C8 acceptance set: edges the stale 2026-06-09 render was missing
    (docs_*, m3_runs_on_*, seal_requires_scheduler) plus the ACTIVE
    m3_seal_app_ref must all render.
    """
    out = render_schema_graph()
    for vocab_id in (
        "m3_seal_app_ref",
        "seal_requires_scheduler",
        "m3_runs_on_agent_host",
        "m3_runs_on_etl_host",
        "m3_runs_on_host_group",
        "docs_describes",
        "docs_chunk_part_of",
        "docs_first_chunk",
        "docs_next_chunk",
        "docs_has_document",
        "docs_governed_by",
    ):
        assert f"r.vocab_id = '{vocab_id}'" in out, f"missing edge for {vocab_id}"


def test_deprecated_and_removed_entries_excluded() -> None:
    """Only active/planned entries render; withdrawn meaning stays out."""
    assert set(RENDERED_STATUSES) == {"active", "planned"}
    out = render_schema_graph()
    for vocab_id in ("m3_runs_on", "seal_has_membership", "seal_of_role", "seal_held_by"):
        assert f"r.vocab_id = '{vocab_id}'" not in out, (
            f"deprecated entry {vocab_id} must not render"
        )
    for retired_label in ("DataSource", "DataTarget"):
        assert f":SchemaMeta:{retired_label} " not in out, (
            f"retired label {retired_label} must not render (unreferenced by any edge)"
        )


def test_meta_graph_is_idempotent_and_declares_generated() -> None:
    """MERGE-only (same rule as ontology.cypher) and the header states the
    derived-view stance."""
    out = render_schema_graph()
    assert not re.findall(r"\bCREATE\s+\(", out), "meta-graph must use MERGE, not CREATE"
    assert "GENERATED" in out and "DO NOT EDIT" in out
