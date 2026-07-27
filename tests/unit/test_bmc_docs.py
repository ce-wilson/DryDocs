"""bmc-docs lexical-graph loader tests: adapter over the REAL corpus (26
committed, deterministic controlm-*.md files) + static Cypher checks in the
test_controlm_cypher.py style."""
from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from drydocs.loaders.bmc_docs import (
    DEFAULT_CORPUS_DIR,
    BmcDocsAdapter,
    BmcDocsLoader,
    classify_chunk_tier,
)
from drydocs_core.models.docs import BmcDocChunkRow

ROOT = Path(__file__).resolve().parent.parent.parent
CYPHER_PATH = ROOT / "drydocs" / "loaders" / "cypher" / "bmc_docs.cypher"

# 26 at first load (2026-07-08); 27 after controlm-api-installation.md
# (Automation API Monthly doc set — remediation TDD OQ-1 spike, 2026-07-09).
# Bump when the corpus intentionally grows.
EXPECTED_DOC_COUNT = 27


def _all_rows() -> list[dict]:
    with BmcDocsAdapter(DEFAULT_CORPUS_DIR) as adapter:
        return list(adapter.rows())


def _rows_by_doc(rows: list[dict]) -> dict[str, list[dict]]:
    by_doc: dict[str, list[dict]] = {}
    for row in rows:
        by_doc.setdefault(row["doc_id"], []).append(row)
    return by_doc


# ---- corpus-level shape ----------------------------------------------------

def test_corpus_dir_exists() -> None:
    assert DEFAULT_CORPUS_DIR.exists()


def test_corpus_document_count() -> None:
    rows = _all_rows()
    doc_ids = {row["doc_id"] for row in rows}
    assert len(doc_ids) == EXPECTED_DOC_COUNT, sorted(doc_ids)


def test_source_manifest_is_not_a_document_row() -> None:
    rows = _all_rows()
    assert "SOURCE-MANIFEST" not in {row["doc_id"] for row in rows}


def test_every_row_validates_against_the_row_model() -> None:
    for row in _all_rows():
        BmcDocChunkRow.model_validate(row)


# ---- known-file header parse -------------------------------------------------

def test_known_file_header_parses() -> None:
    rows = _rows_by_doc(_all_rows())["controlm-variables"]
    preamble = rows[0]
    assert preamble["doc_id"] == "controlm-variables"
    assert preamble["title"] == "Control-M Variables - Vendor Specifications"
    assert preamble["scraped_on"] == "2026-06-11"
    assert preamble["source_page"] == "Variables.htm"
    assert "parameterization" in preamble["purpose"]
    assert preamble["path"].replace("\\", "/") == (
        "external/orchestration/bmc-controlm/controlm-variables.md"
    )
    assert preamble["target_version"] == "9.0.21.300"
    assert preamble["classification"] == "External"
    assert preamble["subject_product_id"] == "controlm"
    # every row for this doc carries the same denormalized header fields
    for row in rows:
        assert row["title"] == preamble["title"]
        assert row["scraped_on"] == preamble["scraped_on"]


def test_captured_header_fallback_when_no_date_scraped_line() -> None:
    """controlm-folder-definition-parameters.md uses '**Captured:**' instead
    of '**Date Scraped:**' and has no '**Document:**' line at all — both must
    be handled null-safe."""
    rows = _rows_by_doc(_all_rows())["controlm-folder-definition-parameters"]
    preamble = rows[0]
    assert preamble["scraped_on"] == "2026-06-11"
    assert preamble["source_page"] is None


def test_acquisition_stub_has_no_header_fields() -> None:
    """controlm-xml-definition-format.md carries Status/Classification lines
    instead of Source/Date Scraped/Purpose — every header field not present
    must resolve to None, never raise."""
    rows = _rows_by_doc(_all_rows())["controlm-xml-definition-format"]
    preamble = rows[0]
    assert preamble["title"].startswith("Control-M XML Definition Format")
    assert preamble["scraped_on"] is None
    assert preamble["source_page"] is None
    assert preamble["purpose"] is None
    assert preamble["source_url"] is None


# ---- chunk shape -------------------------------------------------------------

def test_chunk_id_format_is_zero_padded() -> None:
    rows = _rows_by_doc(_all_rows())["controlm-variables"]
    for row in rows:
        assert re.match(r"^controlm-variables#\d{3}$", row["chunk_id"])
    assert rows[0]["chunk_id"] == "controlm-variables#000"


def test_seq_zero_is_the_preamble() -> None:
    for doc_id, rows in _rows_by_doc(_all_rows()).items():
        seq0 = [r for r in rows if r["seq"] == 0]
        assert len(seq0) == 1, doc_id
        assert seq0[0]["heading"] == "(preamble)"
        assert seq0[0]["level"] == 0
        assert seq0[0]["prev_chunk_id"] is None


def test_prev_chunk_id_chains_in_file_order() -> None:
    for doc_id, rows in _rows_by_doc(_all_rows()).items():
        rows_sorted = sorted(rows, key=lambda r: r["seq"])
        prev = None
        for row in rows_sorted:
            assert row["prev_chunk_id"] == prev, doc_id
            prev = row["chunk_id"]


def test_char_count_matches_text_length() -> None:
    for row in _all_rows():
        assert row["char_count"] == len(row["text"])


def test_row_checksum_present_after_to_params() -> None:
    rows = _all_rows()
    model = BmcDocChunkRow.model_validate(rows[0])
    loader = BmcDocsLoader.__new__(BmcDocsLoader)  # bypass __init__ (no client needed)
    params = loader.to_params(model)
    assert "row_checksum" in params
    assert isinstance(params["row_checksum"], str) and len(params["row_checksum"]) == 64


# ---- tier classifier ----------------------------------------------------------

@pytest.mark.parametrize(
    "heading,text,expected",
    [
        # SYNTHESIZED heading family (SOURCE-MANIFEST default tier rule)
        ("Advanced Patterns", "some prose", "SYNTHESIZED"),
        ("Best Practices for Folder API", "some prose", "SYNTHESIZED"),
        ("Use Cases for Planning Utilities", "some prose", "SYNTHESIZED"),
        ("Notes for Planning Agents", "some prose", "SYNTHESIZED"),
        ("Notes for Planning Agent", "some prose", "SYNTHESIZED"),  # singular variant
        ("For Planning Agents: Key Design Questions Answered", "prose", "SYNTHESIZED"),
        ("Vendor Attributes", "some prose", "SYNTHESIZED"),
        ("File Watcher Detection Workflow", "some prose", "SYNTHESIZED"),
        # VERBATIM — authoritative corrections/additions win first
        (
            "✅ Authoritative Corrections — Classic Parameter Reference (2026-06-11)",
            "some prose",
            "VERBATIM",
        ),
        ("✅ Authoritative Additions — Classic Help (2026-06-11)", "prose", "VERBATIM"),
        # conservative default
        ("Calendar Definition and Purpose", "some prose", "GROUNDED"),
    ],
)
def test_classify_chunk_tier_heading_rules(heading: str, text: str, expected: str) -> None:
    assert classify_chunk_tier(heading, text) == expected


def test_classify_chunk_tier_does_not_misfire_on_pattern_matching_doc() -> None:
    """'Pattern Matching Overview' etc. must NOT hit the SYNTHESIZED 'patterns'
    (plural) rule — the real corpus doc controlm-pattern-matching.md is a core
    GROUNDED feature reference, not a design-patterns section."""
    assert classify_chunk_tier("Pattern Matching Overview", "plain prose, no code") == "GROUNDED"
    assert classify_chunk_tier("Pattern Matching Syntax Rules", "plain prose") == "GROUNDED"


def test_classify_chunk_tier_majority_fenced_code_is_synthesized() -> None:
    code_heavy = "\n".join(
        ["Some intro line."]
        + ["```json"]
        + ['{"Type": "Job:Command"}'] * 10
        + ["```"]
    )
    assert classify_chunk_tier("Usage Examples", code_heavy) == "SYNTHESIZED"


def test_classify_chunk_tier_minority_code_stays_grounded() -> None:
    mostly_prose = "\n".join(
        ["Line of prose one.", "Line of prose two.", "Line of prose three.",
         "Line of prose four.", "```", "one code line", "```"]
    )
    assert classify_chunk_tier("Command Syntax", mostly_prose) == "GROUNDED"


def test_tier_distribution_only_uses_the_three_contract_values() -> None:
    tiers = {row["provenance"] for row in _all_rows()}
    assert tiers <= {"VERBATIM", "GROUNDED", "SYNTHESIZED"}
    assert tiers, "expected at least one tier in the real corpus"


# ---- static Cypher checks (test_controlm_cypher.py style) --------------------

def test_cypher_exists() -> None:
    assert CYPHER_PATH.exists()


def test_cypher_uses_unwind_batch() -> None:
    text = CYPHER_PATH.read_text(encoding="utf-8")
    assert "UNWIND $batch AS row" in text


def test_cypher_idempotent_merge_not_create() -> None:
    text = CYPHER_PATH.read_text(encoding="utf-8")
    body = "\n".join(
        l for l in text.splitlines() if l.strip() and not l.strip().startswith("//")
    )
    assert "MERGE" in body
    assert not re.findall(r"^\s*CREATE\s+\(", body, re.MULTILINE)


def test_describes_uses_match_not_merge_on_software_product() -> None:
    text = CYPHER_PATH.read_text(encoding="utf-8")
    assert "OPTIONAL MATCH (sp:SoftwareProduct {product_id: row.subject_product_id})" in text
    assert "MERGE (sp:SoftwareProduct" not in text
    assert "MERGE (doc)-[d:DESCRIBES {target_version: row.target_version}]->(sp)" in text


def test_next_chunk_uses_match_not_merge_on_prev_chunk() -> None:
    text = CYPHER_PATH.read_text(encoding="utf-8")
    assert "OPTIONAL MATCH (prev:Chunk {chunk_id: row.prev_chunk_id})" in text
    assert "MERGE (prev:Chunk" not in text


def test_was_generated_by_is_checksum_guarded_exactly_once() -> None:
    text = CYPHER_PATH.read_text(encoding="utf-8")
    assert "row_checksum IS NULL OR" in text
    assert "<> row.row_checksum) AS row_changed" in text
    assert "FOREACH (_ IN CASE WHEN row_changed THEN [1] ELSE [] END |" in text

    foreach_start = text.index("FOREACH (_ IN CASE WHEN row_changed")
    close_match = re.search(r"^\)\s*$", text[foreach_start:], re.MULTILINE)
    assert close_match, "FOREACH block has no standalone closing paren"
    foreach_end = foreach_start + close_match.end()

    code_lines = [
        l for l in text.splitlines() if l.strip() and not l.strip().startswith("//")
    ]
    code = "\n".join(code_lines)
    assert code.count("WAS_GENERATED_BY") == 1
    assert "WAS_GENERATED_BY" in text[foreach_start:foreach_end]


def test_row_checksum_is_persisted_on_the_chunk() -> None:
    text = CYPHER_PATH.read_text(encoding="utf-8")
    assert re.search(r"SET c\.row_checksum = row\.row_checksum", text)


def test_first_chunk_block_survives_the_provenance_guard() -> None:
    """Mirrors controlm_folders.cypher's deliberate tail order: the
    WHERE-gated FIRST_CHUNK block must come AFTER the checksum-guarded
    provenance tail (its WHERE drops non-zero-seq rows from the remainder of
    the statement — nothing may follow it)."""
    text = CYPHER_PATH.read_text(encoding="utf-8")
    provenance_idx = text.index("AS row_changed")
    where_idx = text.index("WHERE row.seq = 0", provenance_idx)
    first_chunk_idx = text.index("MERGE (doc)-[fc:FIRST_CHUNK]->(c)", provenance_idx)
    assert provenance_idx < where_idx < first_chunk_idx


def test_cypher_header_documents_where_the_prereq_is_enforced() -> None:
    """The template cannot tell a bad row from an absent registry (it runs per
    batch) — its header must point at the loader-side check that can, so the
    next person re-pointing this loader at another database finds it."""
    text = CYPHER_PATH.read_text(encoding="utf-8")
    assert "_assert_product_registry_present" in text


# ---- Q8: absent product registry vs per-row miss ----------------------------
#
# Duck-typed client (the test_incremental_delete.py idiom, no live DB): the
# behaviour under test is which queries the loader issues before and after the
# load, and what it does with the answers.


class _FakeAdapter:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def __enter__(self) -> _FakeAdapter:
        return self

    def __exit__(self, *_: Any) -> None:
        return None

    def rows(self) -> Iterator[dict]:
        yield from self._rows


class _FakeClient:
    """Answers the registry-count and unresolved-product probes.

    ``registry`` is the set of product_ids a real (non-SchemaMeta)
    :SoftwareProduct exists for; ``schema_meta_only`` simulates a database
    where the ONLY :SoftwareProduct is schema_graph.cypher's keyless
    :SchemaMeta exemplar — the case a bare count(:SoftwareProduct) would pass.
    """

    def __init__(self, registry: set[str], *, schema_meta_only: bool = False) -> None:
        self.registry = registry
        self.schema_meta_only = schema_meta_only
        self.run_calls: list[tuple[str, dict]] = []
        self.run_script_calls: list[tuple[str, dict]] = []

    def run(self, cypher: str, params: dict[str, Any] | None = None,
            **kwargs: Any) -> list[dict]:
        bind = {**(params or {}), **kwargs}
        self.run_calls.append((cypher, bind))
        if "AS products" in cypher:
            # The exemplar is excluded by the query's own NOT sp:SchemaMeta
            # predicate, so it never contributes to this count.
            return [{"products": len(self.registry)}]
        if "WHERE NOT (doc)-[:DESCRIBES]->(:SoftwareProduct)" in cypher:
            # Stand in for the graph: the template's FOREACH guard writes the
            # edge only when the row's product id resolves, so the documents
            # left without one are exactly those whose id is off-registry.
            seen: dict[str, str | None] = {}
            for row in self.flushed_rows():
                seen.setdefault(row["doc_id"], row.get("subject_product_id"))
            return [
                {"doc_id": doc_id, "subject_product_id": product_id}
                for doc_id, product_id in sorted(seen.items())
                if product_id not in self.registry
            ]
        if "SHOW INDEXES" in cypher:
            return []
        if "AS rows_changed" in cypher:
            return [{"rows_changed": 0}]
        return []

    def run_script(self, script: str, params: dict[str, Any] | None = None) -> None:
        self.run_script_calls.append((script, dict(params or {})))

    def flushed_rows(self) -> list[dict]:
        rows: list[dict] = []
        for _, bind in self.run_calls:
            rows.extend(bind.get("batch", []))
        for _, params in self.run_script_calls:
            rows.extend(params.get("batch", []))
        return rows


def _chunk_row(**overrides: Any) -> dict:
    row = dict(_all_rows()[0])
    row.update(overrides)
    return row


def _loader(client: _FakeClient, rows: list[dict]) -> BmcDocsLoader:
    return BmcDocsLoader(client, _FakeAdapter(rows), run_log=False)


def test_empty_product_registry_fails_loudly() -> None:
    """The whole-corpus miss: ZERO reachable :SoftwareProduct must refuse the
    load instead of reporting success with no DESCRIBES edges."""
    client = _FakeClient(registry=set())
    with pytest.raises(RuntimeError, match="no :SoftwareProduct nodes are reachable"):
        _loader(client, [_chunk_row()]).load()


def test_empty_registry_refusal_writes_nothing_not_even_the_job_run() -> None:
    """Refusal follows the _preflight_indexes convention — it lands before
    _open_run, so a refused load leaves no :JobRun behind to look successful."""
    client = _FakeClient(registry=set())
    with pytest.raises(RuntimeError):
        _loader(client, [_chunk_row()]).load()
    assert not client.flushed_rows()
    assert not [c for c, _ in client.run_calls if "MERGE (run:JobRun" in c]


def test_schema_meta_exemplar_alone_does_not_satisfy_the_prereq() -> None:
    """schema_graph.cypher MERGEs :SchemaMeta:SoftwareProduct with NO
    product_id. A bare count(:SoftwareProduct) would see 1 and wave an empty
    registry through — the guard's predicate must exclude it."""
    client = _FakeClient(registry=set(), schema_meta_only=True)
    with pytest.raises(RuntimeError, match="no :SoftwareProduct nodes are reachable"):
        _loader(client, [_chunk_row()]).load()

    probe = [c for c, _ in client.run_calls if "AS products" in c]
    assert probe, "no registry-presence probe was issued"
    assert "NOT sp:SchemaMeta" in probe[0], (
        "the registry probe must use the rename-proof label predicate"
    )


def test_populated_registry_loads_and_reports_no_missing_edges() -> None:
    client = _FakeClient(registry={"controlm"})
    loader = _loader(client, [_chunk_row()])
    summary = loader.load()
    assert summary.status == "OK"
    assert summary.rows_processed == 1
    assert loader.documents_without_product == []
    assert len(client.flushed_rows()) == 1


def test_per_row_product_miss_still_loads_the_chunk_and_reports_the_miss(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The other half: one row with a bad product id keeps its Document and
    Chunk (the FOREACH guard drops only that edge) but the miss is reported,
    never silent."""
    client = _FakeClient(registry={"controlm"})
    rows = [
        _chunk_row(doc_id="good-doc", chunk_id="good-doc#000"),
        _chunk_row(  # misspelled product id
            doc_id="bad-doc", chunk_id="bad-doc#000", subject_product_id="contorlm"
        ),
    ]
    loader = _loader(client, rows)
    with caplog.at_level(logging.WARNING, logger="drydocs.loaders.bmc_docs"):
        summary = loader.load()

    assert summary.status == "OK"
    assert summary.rows_processed == 2
    # both rows reached the graph — a bad product id costs the edge, not the chunk
    flushed = {r["chunk_id"] for r in client.flushed_rows()}
    assert flushed == {"good-doc#000", "bad-doc#000"}
    # ...and the miss is reported, naming the document AND the unresolved id
    assert loader.documents_without_product == [
        {"doc_id": "bad-doc", "subject_product_id": "contorlm"}
    ]
    assert "contorlm" in caplog.text
    assert "bad-doc" in caplog.text


def test_missing_edge_probe_is_scoped_to_this_run() -> None:
    """The probe must not report documents an earlier run left behind."""
    client = _FakeClient(registry={"controlm"})
    loader = _loader(client, [_chunk_row()])
    loader.load()
    probes = [
        (c, b) for c, b in client.run_calls
        if "WHERE NOT (doc)-[:DESCRIBES]->(:SoftwareProduct)" in c
    ]
    assert len(probes) == 1
    cypher, bind = probes[0]
    assert "last_run_id: $run_id" in cypher
    assert bind["run_id"] == loader.run_id


def test_no_merge_on_nullable_keys() -> None:
    """doc_id and chunk_id (the only node MERGE keys) are required/non-nullable
    on the row model. The two genuinely-nullable joins (prev_chunk_id,
    subject_product_id) never appear as a MERGE key anywhere in the file —
    they are OPTIONAL MATCH targets, wired into an edge MERGE only inside a
    FOREACH guard (asserted separately above)."""
    text = CYPHER_PATH.read_text(encoding="utf-8")
    assert "MERGE (doc:Document:Entity {doc_id: row.doc_id})" in text
    assert "MERGE (c:Chunk:Entity {chunk_id: row.chunk_id})" in text
    assert "chunk_id: row.prev_chunk_id" not in text.replace(
        "OPTIONAL MATCH (prev:Chunk {chunk_id: row.prev_chunk_id})", ""
    )
    assert "product_id: row.subject_product_id" not in text.replace(
        "OPTIONAL MATCH (sp:SoftwareProduct {product_id: row.subject_product_id})", ""
    )
