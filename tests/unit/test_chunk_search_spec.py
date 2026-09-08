"""API4 — chunk BODY TEXT is reachable by term, and the chunk count is real.

THE DEFECT THIS EXISTS FOR, stated the way the item found it: no registered
spec searched ``Chunk.text``. ``docs.search.v1`` searches a Document's title and
abstract and says of itself that it is chunk-free, so a term that appears only
inside a document's body was unreachable from /ask — and the pipeline reported
``chunks: 0`` as a LITERAL, so even a run that had read chunk text would have
said it read none.

WHAT IS AND IS NOT ASSERTED HERE. There is no graph in this suite and the
laptop's database holds no corpus, so this does not claim the spec returns the
right rows. It claims the two properties that make the defect impossible to
reproduce: the spec FILTERS ON BODY TEXT (not on a title, which is O62's
illusion — a full listing narrowed afterwards by title similarity), and the
chunk count is DERIVED from rows rather than declared. Both are properties of
the code, and both are what a graph test would be checking anyway.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi", reason="fastapi is an optional dep (the api group)")

REPO_ROOT = Path(__file__).resolve().parents[2]
for entry in (str(REPO_ROOT / "agents"), str(REPO_ROOT)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from graph_qa import pipeline as pl  # noqa: E402

from drydocs_api.query_specs import QUERY_SPECS, SNIPPET_CHARS  # noqa: E402

SPEC_ID = "docs.chunk-search.v1"
TITLE_SPEC_ID = "docs.search.v1"


def _spec(spec_id: str = SPEC_ID):
    assert spec_id in QUERY_SPECS, f"{spec_id} is not registered"
    return QUERY_SPECS[spec_id]


# ── (a) a registered spec searches chunk text ────────────────────────────────


def test_the_spec_is_registered_and_takes_a_required_term():
    params = {p.name: p for p in _spec().params}
    assert "q" in params, "a search spec with no term is a listing"
    assert params["q"].required, "an optional filter is no filter"


def test_the_filter_is_on_chunk_body_text_and_not_on_a_title():
    """The acceptance's own distinction, and O62's illusion stated as a test: a
    term found in a body must come back from a BODY predicate, not from a
    listing that a title match happened to include."""
    cypher = _spec().cypher
    assert "c.text" in cypher, f"{SPEC_ID} does not read chunk text at all"
    assert (
        "toLower(coalesce(c.text, '')) CONTAINS toLower($q)" in cypher
    ), "the term must narrow on body text, server-side"
    # the predicate is on the CHUNK, never on the document's title or abstract:
    # a title-matching predicate here would answer 'found' for a term that is
    # not in the corpus body, which is the thing the item exists to prevent
    predicate = cypher.split("RETURN")[0]
    assert "d.title" not in predicate
    assert "d.abstract" not in predicate


def test_it_walks_from_chunk_to_its_document():
    cypher = _spec().cypher
    assert "(c:Chunk)-[:PART_OF]->(d:Document)" in cypher, (
        "the corpus edge is (:Chunk)-[:PART_OF]->(:Document); HAS_CHUNK does not exist "
        "and generating it is one of the two defects R18's evidence recorded"
    )
    assert "NOT c:SchemaMeta" in cypher and "NOT d:SchemaMeta" in cypher


def test_it_returns_a_bounded_snippet_and_never_the_whole_chunk():
    """The Q15 rule for this family — chunk text is not what a navigation spec
    returns — kept while still making a hit judgeable. The full chunk is one
    call away by chunk_id."""
    cypher = _spec().cypher
    assert f"substring(coalesce(c.text, ''), 0, {SNIPPET_CHARS})" in cypher
    columns = {c.name for c in _spec().columns}
    assert "snippet" in columns and "text" not in columns
    assert "chunk_id" in columns, "the way to the full chunk must ride every row"
    assert SNIPPET_CHARS > 0


def test_the_title_door_is_left_alone():
    """A NEW spec rather than a widening: docs.search.v1's description promises
    chunk-free and two other descriptions cite that promise."""
    title_cypher = _spec(TITLE_SPEC_ID).cypher
    assert "Chunk" not in title_cypher
    assert "chunk-free" in _spec(TITLE_SPEC_ID).description.lower()


def test_the_description_says_which_door_this_is():
    """The catalog line is what AGENT1's router reads, so 'a match, not a
    listing' has to be IN it — a router choosing between two docs specs has
    nothing else to go on."""
    description = _spec().description
    assert "docs.search.v1" in description, "it must name its sibling to be chosen against"
    assert "listing" in description.lower()


# ── (b) chunks: 0 stops being a literal ──────────────────────────────────────


def test_the_chunk_count_is_derived_from_the_rows():
    assert pl.count_chunk_rows([]) == 0
    assert pl.count_chunk_rows(None) == 0
    assert (
        pl.count_chunk_rows([{"app_id": "A1"}, {"job_id": "J1"}]) == 0
    ), "graph rows carry no chunk id — 0 here is a true count, not a placeholder"
    assert pl.count_chunk_rows([{"chunk_id": "c1"}, {"chunk_id": "c2"}]) == 2


def test_a_chunk_reached_twice_is_counted_once():
    """The metric is how much corpus was in the context, not how many rows
    mentioned a chunk."""
    rows = [{"chunk_id": "c1", "role": "a"}, {"chunk_id": "c1", "role": "b"}]
    assert pl.count_chunk_rows(rows) == 1
    assert pl.chunk_row_ids(rows) == {"c1"}


def test_a_row_with_an_empty_chunk_id_is_not_a_chunk():
    assert pl.count_chunk_rows([{"chunk_id": None}, {"chunk_id": ""}]) == 0


# ── end to end: a non-zero count provably reaches the envelope ───────────────


class FakeProvider:
    provider = "anthropic"

    def __init__(self, replies):
        self.replies = replies
        self.calls = []

    def complete(self, system, user, max_tokens=1200):
        from graph_qa.providers import LlmReply, LlmUsage

        self.calls.append((system, user))
        text = self.replies[min(len(self.calls) - 1, len(self.replies) - 1)]
        return LlmReply(text=text, usage=LlmUsage(100, 20), model="fake-model", ms=5)


class FakeResult:
    def __init__(self, records):
        self.records = records
        self.keys = list(records[0]) if records else []
        self.row_count = len(records)
        self.truncated = False
        self.ms = 3
        self.notifications: list = []


CHUNK_ROWS = [
    {"chunk_id": "controlm-os-job-parameters#4", "doc_id": "d1", "snippet": "CYCLIC_TYPE ..."},
    {"chunk_id": "controlm-os-job-parameters#7", "doc_id": "d1", "snippet": "... interval"},
]
GRAPH_ROWS = [{"app_id": "A1", "name": "Payroll"}]


def _answer(rows, spec_id=SPEC_ID, params=None):
    routed = json.dumps(
        {
            "spec_id": spec_id,
            "params": {"q": "CYCLIC_TYPE"} if params is None else params,
            "reason": "body-text search",
        }
    )
    provider = FakeProvider([routed, "Two chunks."])
    pipeline = pl.GraphQaPipeline(
        provider=provider,
        run_read=lambda *a, **k: FakeResult(rows),
        graph_schema=lambda: {"labels": [], "relationshipTypes": [], "propertyKeys": []},
        vocabulary_loader=list,
    )
    return pipeline.answer("what is CYCLIC_TYPE?", run_id="qa-api4", session_id="s")


def test_a_chunk_answer_reports_a_non_zero_chunk_count():
    """(b)'s "a non-zero value provably reaches chunk text end to end" — the
    whole reason (a) is unobservable from the console without it."""
    envelope = _answer(CHUNK_ROWS)
    assert envelope.tier == "spec"
    assert envelope.metrics.context["chunks"] == 2
    assert envelope.metrics.context["rows"] == 2


def test_a_graph_answer_still_reports_zero_and_means_it():
    envelope = _answer(GRAPH_ROWS, spec_id="explorer.applications.v1", params={})
    assert envelope.metrics.context["chunks"] == 0
    assert envelope.metrics.context["rows"] == 1


# ── (c) SCOPED, not decided: where the chunk-level trust override lives ──────


def test_the_chunk_trust_override_is_read_from_a_property_no_loader_writes():
    """CLAUSE (c), SCOPED AND HANDED BACK. Read from the loaders and the models
    on 2026-09-08 (laptop, offline — no graph was consulted, and none is needed:
    every fact here is in committed code).

    Two specs compute effective trust as ``coalesce(c.trust, d.trust_default)``.
    NO loader writes ``Chunk.trust``: bmc_docs and essential_graphrag write
    ``c.provenance`` (VERBATIM / GROUNDED / SYNTHESIZED from
    ``classify_chunk_tier``) and email_extracts writes no chunk tier at all. So
    the coalesce always falls through and every chunk reports its document's
    default — which is exactly the cyclic-type-trap case's "trust defect": an
    illustrative enum reads GROUNDED because its document does, while the hazard
    banner that would have downgraded it sits in a different chunk.

    THE OVERRIDE ALREADY EXISTS. ``BmcDocChunkRow.trust_default`` documents
    itself as "the doc-level fallback tier absent any chunk-level override ...
    the per-chunk 'provenance' field is what actually varies", and both fields
    carry the same three-value vocabulary. So the gap is a PROPERTY NAME, not a
    missing model — and the ruling's first question is which name wins.

    NOT FIXED HERE, on the item's own instruction: the axis change is the
    docmeta owner's. This test pins the gap open so it cannot close by accident
    and so the ruling has something that fails when it lands.
    """
    for spec_id in ("docs.chunks.v1", "docs.trust-provenance.v1"):
        assert "coalesce(c.trust, d.trust_default)" in _spec(spec_id).cypher

    loaders = REPO_ROOT / "drydocs" / "loaders" / "cypher"
    bmc = (loaders / "bmc_docs.cypher").read_text(encoding="utf-8")
    graphrag = (loaders / "essential_graphrag.cypher").read_text(encoding="utf-8")
    emails = (loaders / "email_extracts.cypher").read_text(encoding="utf-8")

    assert "c.provenance" in bmc and "c.provenance" in graphrag
    assert "c.provenance" not in emails
    for template in (bmc, graphrag, emails):
        assert "c.trust " not in template and "c.trust=" not in template, (
            "a loader now writes Chunk.trust — the docmeta trust-axis ruling has landed "
            "or half-landed; reconcile this test with it rather than deleting the check"
        )
