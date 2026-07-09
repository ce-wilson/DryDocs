"""bmc-docs lexical-graph loader tests: adapter over the REAL corpus (26
committed, deterministic controlm-*.md files) + static Cypher checks in the
test_controlm_cypher.py style."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from drydocs.loaders.bmc_docs import (
    DEFAULT_CORPUS_DIR,
    BmcDocsAdapter,
    BmcDocsLoader,
    classify_chunk_tier,
)
from drydocs.models.docs import BmcDocChunkRow

ROOT = Path(__file__).resolve().parent.parent.parent
CYPHER_PATH = ROOT / "drydocs" / "loaders" / "cypher" / "bmc_docs.cypher"

EXPECTED_DOC_COUNT = 26


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


def test_corpus_has_26_documents() -> None:
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
