"""Q10 — the failure/activity email loader: lexical shape, unassigned by design.

Runs entirely on the SYNTHETIC samples in drydocs/data/samples/email-extracts/
(they ARE the assumed extract contract, the G47 precedent) — sample-reproducible
per J18, no database, no real data.
"""

from __future__ import annotations

import json
from itertools import pairwise
from pathlib import Path

import pytest

from drydocs.loaders.base import _code_semicolons
from drydocs.loaders.email_extracts import (
    EmailExtractsAdapter,
    EmailExtractsLoader,
    email_doc_id,
    split_body,
)
from drydocs_core.models.docs import EmailExtractRow

REPO = Path(__file__).resolve().parents[2]
SAMPLES = REPO / "drydocs" / "data" / "samples" / "email-extracts"

# Policy guard (test_skip_guard_policy): these samples are COMMITTED, so on a
# clean clone this never fires — it exists so a partial checkout skips instead
# of failing, per the policy's fresh-clone rule.
pytestmark = pytest.mark.skipif(not SAMPLES.exists(), reason="sample extracts absent")


def test_samples_define_the_assumed_contract():
    """The two synthetic files carry every required key between them — one with
    message_id, one without (the doc_id fallback path)."""
    payloads = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(SAMPLES.glob("*.json"))]
    assert len(payloads) == 2
    assert any("message_id" in p for p in payloads)
    assert any("message_id" not in p for p in payloads)
    for p in payloads:
        for key in ("subject", "sent_at", "body_text", "msg_file"):
            assert p.get(key), key


def test_adapter_rows_validate_chain_and_stay_unassigned():
    adapter = EmailExtractsAdapter(SAMPLES)
    rows = list(adapter.rows())
    assert rows and not adapter.rejected
    docs = {r["doc_id"] for r in rows}
    assert len(docs) == 2
    for row in rows:
        model = EmailExtractRow.model_validate(row)
        assert model.doc_id.startswith("email:")
        assert model.msg_path.endswith(".msg")  # the citation, never the content
    # per-document chunk chains are contiguous
    for doc_id in docs:
        chunk_rows = [r for r in rows if r["doc_id"] == doc_id]
        assert chunk_rows[0]["prev_chunk_id"] is None
        for prev, cur in pairwise(chunk_rows):
            assert cur["prev_chunk_id"] == prev["chunk_id"]
    # UNASSIGNED BY DESIGN: no assignment field exists anywhere in a row
    for row in rows:
        assert not any("folder" in k or "process" in k or "assign" in k for k in row)


def test_doc_id_is_row_derived_and_deterministic():
    a = email_doc_id("Subject", "2026-08-01T00:00:00Z")
    assert a == email_doc_id("Subject", "2026-08-01T00:00:00Z")  # truncate-and-reload safe
    assert a != email_doc_id("Subject", "2026-08-02T00:00:00Z")


def test_rejects_are_counted_never_guessed(tmp_path):
    (tmp_path / "bad.json").write_text("{not json", encoding="utf-8")
    (tmp_path / "empty-body.json").write_text(
        json.dumps({"subject": "s", "sent_at": "t", "body_text": "\n\n", "msg_file": "m.msg"}),
        encoding="utf-8",
    )
    (tmp_path / "missing-key.json").write_text(
        json.dumps({"subject": "s", "sent_at": "t"}), encoding="utf-8"
    )
    adapter = EmailExtractsAdapter(tmp_path)
    assert list(adapter.rows()) == []
    assert len(adapter.rejected) == 3


def test_split_body_paragraphs():
    assert split_body("a b\n\n\n\nc  d\n\n") == ["a b", "c d"]


def test_cypher_is_single_statement_and_never_assigns():
    """The floor's hard fence: this loader writes the lexical shape ONLY. The
    assignment edge (docs_email_concerns / CONCERNS) went ACTIVE at Q21, and
    its ONE authorized writer is loaders/cypher/email_concerns.cypher — the
    exemption is BY NAME, and this fence on the LEXICAL loader's cypher is
    permanent: widening the check to the directory would discharge it, and
    lifting it would let the lexical loader quietly gain the write the gate
    placed elsewhere."""
    cypher = EmailExtractsLoader.cypher_path.read_text(encoding="utf-8")
    assert _code_semicolons(cypher) == 1
    code = "\n".join(line for line in cypher.splitlines() if not line.strip().startswith("//"))
    for forbidden in ("CONCERNS", "ControlMFolder", "ETLProcess", "ASSIGNED"):
        assert forbidden not in code, f"assignment token {forbidden!r} in the lexical loader"
    assert "corpus_id" in code  # the graph_locator contract (match: corpus_id)


def test_loader_binding():
    assert EmailExtractsLoader.source_id == "ops-email-extracts"
    assert EmailExtractsLoader.row_model is EmailExtractRow
