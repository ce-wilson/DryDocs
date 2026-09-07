"""R19 — the Ask clarification loop for unresolved acronyms and label intent.

Companion to R18 (the Tower → :TOMRole mismatch): a question that names a term
the pipeline cannot resolve to a registered spec, an active vocabulary row, a
live label/property or an approved glossary sense is NOT routed onto a near
match. It comes back as a structured clarification request, the console asks,
and the person's answer rides the next turn. What this suite proves, per the
acceptance:

- (a) an unknown acronym short-circuits with zero LLM calls and zero Cypher;
  an ambiguous label carries >= 2 candidates; candidates never include an
  unapproved glossary sense as a RESOLUTION, only as a choice;
- (b) a confirmed clarification is a `clarified` step in the trace and its
  clause reaches the router AND text2cypher prompts; the original question is
  what the envelope hashes;
- (c) a declined clarification prefixes the answer with the ambiguity note;
- (d) a clear lower-case question is byte-for-byte the single pass it was
  (same provider call count, same tier, no clarify step) — the regression path;
- the glossary reader: approved vs candidate, case-insensitive lookup.

Fakes throughout (no litellm, no driver, no ADK) — the same shape as
tests/unit/test_graph_qa.py, from which the fixtures are imported.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
for entry in (str(REPO_ROOT / "agents"), str(REPO_ROOT)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from graph_qa import pipeline as pl  # noqa: E402
from graph_qa import term_resolution as tr  # noqa: E402
from graph_qa.control import SECRET_CONTROL_FIELDS, split_question_and_control  # noqa: E402

from drydocs_core.glossary import GlossarySense, load_glossary, senses_for  # noqa: E402
from tests.unit.test_graph_qa import (  # noqa: E402
    LIVE_SCHEMA,
    SPEC_ID,
    VOCAB,
    FakeProvider,
    FakeResult,
    _ok_read,
)

GLOSSARY = (
    GlossarySense("DRY", "dry-1", "product", "DryDocs", (), "the product", "confirmed", "test"),
    GlossarySense(
        "CDO", "cdo-1", "industry", "Chief Data Officer", (), "oversees data", "candidate", "test"
    ),
    GlossarySense(
        "CDO",
        "cdo-2",
        "industry",
        "Chief Digital Officer",
        (),
        "leads digital",
        "candidate",
        "test",
    ),
)


def _pipeline(provider, run_read=_ok_read, glossary=GLOSSARY):
    return pl.GraphQaPipeline(
        provider=provider,
        run_read=run_read,
        graph_schema=lambda: LIVE_SCHEMA,
        vocabulary_loader=lambda: VOCAB,
        glossary_loader=lambda: glossary,
    )


ROUTER_TO_SPEC = f'{{"spec_id": "{SPEC_ID}", "params": {{}}}}'


# -- detection -------------------------------------------------------------------
@pytest.mark.parametrize(
    "question",
    [
        "how many applications?",
        "which jobs?",
        "count folders",
        "how many towers are there",
        "SHOW ALL JOBS",  # emphasis, not acronyms
        "what does the API return as JSON?",  # house terms
        "Which jobs run in the morning?",  # sentence-initial capital is not a label
    ],
)
def test_clear_questions_detect_nothing(question: str) -> None:
    assert tr.detect_terms(question) == []


def test_detects_acronyms_and_label_shapes_in_question_order() -> None:
    found = tr.detect_terms("which CTM jobs feed the TOMRole nodes or :BusinessApplication?")
    assert [(t.term, t.kind) for t in found] == [
        ("CTM", "acronym"),
        ("TOMRole", "label"),
        ("BusinessApplication", "label"),
    ]


# -- (a) unresolved terms short-circuit before any LLM or Cypher ------------------
def test_unknown_acronym_returns_a_clarification_with_no_llm_and_no_cypher() -> None:
    provider = FakeProvider(replies=[ROUTER_TO_SPEC, "never reached"])
    executed: list = []

    def run_read(cypher, params=None, database=None, row_cap=100, timeout_s=15.0):
        executed.append(cypher)
        return _ok_read(cypher)

    env = _pipeline(provider, run_read).answer("Which jobs belong to the PDN team?", run_id="r19-a")
    assert env.tier == "clarification"
    assert provider.calls == [] and executed == []
    assert env.metrics.llm_calls == 0
    assert env.clarification is not None
    (term,) = env.clarification["terms"]
    assert term["term"] == "PDN" and term["kind"] == "acronym"
    choice_ids = [c["id"] for c in term["choices"]]
    assert choice_ids[-2:] == [tr.FREE_TEXT_CHOICE, tr.PROCEED_CHOICE]
    assert "'PDN'" in env.clarification["prompt"] and env.answer == env.clarification["prompt"]
    clarify = [s for s in env.steps if s.kind == "clarify"]
    assert len(clarify) == 1 and clarify[0].spec_id == "clarify:PDN"
    assert clarify[0].note == env.clarification["prompt"]
    # the contract serialises — the console reads exactly this
    assert env.to_dict()["clarification"]["terms"][0]["term"] == "PDN"


def test_ambiguous_acronym_offers_every_unapproved_sense_as_a_choice_not_a_resolution() -> None:
    provider = FakeProvider(replies=[ROUTER_TO_SPEC])
    env = _pipeline(provider).answer("how many CDO applications are there?", run_id="r19-amb")
    assert env.tier == "clarification"
    (term,) = env.clarification["terms"]
    glossary = [c for c in term["candidates"] if c["source"] == "glossary"]
    assert {c["label"] for c in glossary} == {"Chief Data Officer", "Chief Digital Officer"}
    assert len(term["candidates"]) >= 2
    assert all("candidate" in c["detail"] for c in glossary)


def test_approved_glossary_sense_resolves_without_asking() -> None:
    provider = FakeProvider(replies=[ROUTER_TO_SPEC, "DryDocs is the product."])
    env = _pipeline(provider).answer("what is DRY?", run_id="r19-approved")
    assert env.tier == "spec"
    assert not [s for s in env.steps if s.kind == "clarify"]


def test_label_shaped_term_near_a_live_label_offers_the_label() -> None:
    provider = FakeProvider(replies=[ROUTER_TO_SPEC])
    env = _pipeline(provider).answer("list the ControlJob rows", run_id="r19-label")
    assert env.tier == "clarification"
    (term,) = env.clarification["terms"]
    assert term["kind"] == "label"
    assert {(c["source"], c["label"]) for c in term["candidates"]} >= {("label", "ControlMJob")}


def test_live_labels_vocab_and_spec_words_resolve() -> None:
    """Each of the four sources resolves on its own; none of these asks."""
    for question in (
        "how many BusinessApplication nodes?",  # live label
        "count WAS_INFORMED_BY edges",  # active vocabulary row
        "what does SEAL own?",  # live property part (seal_id)
    ):
        provider = FakeProvider(replies=[ROUTER_TO_SPEC, "ok"])
        env = _pipeline(provider).answer(question, run_id="r19-resolves")
        assert env.tier == "spec", question


def test_schema_failure_skips_clarification_and_runs_the_old_pass() -> None:
    provider = FakeProvider(replies=[ROUTER_TO_SPEC, "answer"])

    def boom():
        raise OSError("graph down")

    pipeline = pl.GraphQaPipeline(
        provider=provider,
        run_read=_ok_read,
        graph_schema=boom,
        vocabulary_loader=lambda: VOCAB,
        glossary_loader=lambda: GLOSSARY,
    )
    env = pipeline.answer("Which PDN jobs?", run_id="r19-schema-down")
    assert env.tier == "spec" and env.clarification is None


# -- (b) the selection rides the next turn and reaches the prompts ---------------
def test_selection_is_traced_and_reaches_router_and_text2cypher_prompts() -> None:
    provider = FakeProvider(
        replies=[
            '{"spec_id": null, "params": {}}',  # router: no spec
            '{"cypher": "MATCH (n) RETURN n.name AS name LIMIT 5"}',  # text2cypher
            "Three PDN jobs.",  # answer
        ]
    )
    question = "Which jobs belong to the PDN team?"
    env = _pipeline(provider).answer(
        question,
        run_id="r19-b",
        clarifications=[
            {"term": "PDN", "resolution": "Production Delay Notification", "declined": False}
        ],
    )
    assert env.tier == "text2cypher"
    assert env.clarification is None
    clarified = [s for s in env.steps if s.kind == "clarified"]
    assert len(clarified) == 1
    assert clarified[0].spec_id == "clarified:PDN"
    assert clarified[0].note == "Production Delay Notification"
    router_user, t2c_user = provider.calls[0][1], provider.calls[1][1]
    assert "PDN means: Production Delay Notification" in router_user
    assert "PDN means: Production Delay Notification" in t2c_user
    # the envelope hashes the ORIGINAL question, not the augmented prompt
    assert env.question_sha256 == pl.sha256_text(question)
    assert env.question_chars == len(question)
    assert not env.answer.startswith("Note:")


def test_clarified_term_is_never_asked_again_even_when_still_unresolved() -> None:
    provider = FakeProvider(replies=[ROUTER_TO_SPEC, "ok"])
    env = _pipeline(provider).answer(
        "Which PDN jobs?",
        run_id="r19-once",
        clarifications=[{"term": "pdn", "resolution": "the delay notice", "declined": False}],
    )
    assert env.tier == "spec"


def test_malformed_clarifications_degrade_to_not_clarified() -> None:
    assert tr.parse_clarifications("nonsense") == []
    assert tr.parse_clarifications([{"resolution": "x"}, 7, {"term": " "}]) == []
    (one,) = tr.parse_clarifications([{"term": "PDN", "resolution": ""}])
    assert one.declined and one.resolution is None


# -- (c) declined: the answer states the ambiguity ---------------------------------
def test_declined_clarification_prefixes_the_answer_with_the_ambiguity() -> None:
    provider = FakeProvider(
        replies=[
            '{"spec_id": null, "params": {}}',
            '{"cypher": "MATCH (n) RETURN n.name AS name LIMIT 5"}',
            "No rows matched.",
        ]
    )

    def zero_rows(cypher, params=None, database=None, row_cap=100, timeout_s=15.0):
        return FakeResult(records=[], keys=["name"], row_count=0)

    env = _pipeline(provider, zero_rows).answer(
        "Which PDN jobs?",
        run_id="r19-c",
        clarifications=[{"term": "PDN", "resolution": None, "declined": True}],
    )
    assert env.tier != "clarification"
    assert env.answer.startswith("Note: 'PDN' was not resolved")
    assert "not evidence that nothing exists" in env.answer
    clarified = next(s for s in env.steps if s.kind == "clarified")
    assert clarified.note == "declined: no clarification given"
    assert "treat it as unresolved" in provider.calls[0][1]


# -- (d) the regression path: clear questions are unchanged -------------------------
def test_clear_question_is_the_same_single_pass() -> None:
    provider = FakeProvider(replies=[ROUTER_TO_SPEC, "There is 1 application."])
    schema_calls = []

    def schema():
        schema_calls.append(1)
        return LIVE_SCHEMA

    pipeline = pl.GraphQaPipeline(
        provider=provider,
        run_read=_ok_read,
        graph_schema=schema,
        vocabulary_loader=lambda: VOCAB,
        glossary_loader=lambda: GLOSSARY,
    )
    env = pipeline.answer("how many applications?", run_id="r19-d")
    assert env.tier == "spec"
    assert len(provider.calls) == 2  # router + answer, as before R19
    assert [s.kind for s in env.steps] == ["router", "spec", "answer"]
    assert env.clarification is None
    assert schema_calls == []  # no extra schema read for a question that detects nothing
    assert env.answer == "There is 1 application."


# -- the control field ---------------------------------------------------------------
def test_clarifications_travel_in_the_control_part_and_are_not_a_secret() -> None:
    question, control = split_question_and_control(
        [
            "Which PDN jobs?",
            '{"drydocs_control": {"session_id": "s1", "clarifications": '
            '[{"term": "PDN", "resolution": "delay notice", "declined": false}]}}',
        ]
    )
    assert question == "Which PDN jobs?"
    assert control["clarifications"][0]["term"] == "PDN"
    assert "clarifications" not in SECRET_CONTROL_FIELDS


# -- the glossary reader -------------------------------------------------------------
def test_glossary_reader_reads_the_public_file_and_marks_approval() -> None:
    senses = load_glossary()
    assert senses, "the public glossary has terms"
    approved = [s for s in senses if s.approved]
    assert {s.acronym for s in approved} >= {"DRY"}
    assert all(s.confidence in ("confirmed", "corrected") for s in approved)
    assert any(not s.approved for s in senses)  # candidates exist and are not approved
    assert senses_for("dry", senses) == senses_for("DRY", senses)
    assert all(s.source.startswith(("config/", "internal/")) for s in senses)


def test_glossary_reader_refuses_the_wrong_schema(tmp_path: Path) -> None:
    bad = tmp_path / "terms.yaml"
    bad.write_text("schema: drydocs.other.v1\nterms: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="expected schema"):
        load_glossary((str(bad),))
