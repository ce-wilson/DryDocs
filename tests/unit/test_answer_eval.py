"""R8 — the stored triple and the on-demand evaluator, offline.

WHAT THIS SUITE PROVES:

- the run line now carries the question/context/answer TRIPLE, written by a real
  pipeline run through the R3 fixture rather than by a hand-built dict;
- ``context`` carries COUNTS and step identities and NEVER retrieved values —
  asserted against a fixture whose row values are distinctive enough to find;
- the :AgentRun graph node is unchanged: the extension is local-ledger-only;
- the evaluator is NEVER INLINE, read off the pipeline's own imports;
- the LLM-judged metrics RAISE rather than returning an approximation, which is
  the whole design decision the module exists to hold.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
for entry in (str(REPO_ROOT / "agents"), str(REPO_ROOT)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.answer_eval import (  # noqa: E402
    DETERMINISTIC_SCORERS,
    Groundedness,
    JudgeUnavailableError,
    LlmJudge,
    evaluate,
    summarize,
)
from common.ledger_read import LedgerRead, Triple, read_ledger, triples  # noqa: E402
from common.llm_ledger import LlmLedger  # noqa: E402
from graph_qa import pipeline as pl  # noqa: E402

from tests.source_scan import imported_modules, source_text  # noqa: E402

SPEC_ID = "explorer.applications.v1"
VOCAB = [
    {
        "neo4j_label": "WAS_INFORMED_BY",
        "from_node": "ControlMJob",
        "to_node": "ControlMJob",
        "role": None,
        "note": "job dependency",
        "status": "active",
    }
]
LIVE_SCHEMA = {"labels": ["ControlMJob"], "relationshipTypes": [], "propertyKeys": []}

#: A value distinctive enough that finding it anywhere in the ledger is proof
#: a retrieved VALUE leaked. Shaped like the things that actually would leak —
#: a folder name and a SEAL id from the reserved synthetic block.
SECRET_ROW_VALUE = "T032_NIGHTLY_CLOSE_70042"


class FakeProvider:
    provider = "anthropic"

    def __init__(self, replies):
        self.replies = replies
        self.calls = []

    def complete(self, system, user, max_tokens=1200):
        from graph_qa.providers import LlmReply, LlmUsage

        self.calls.append((system, user))
        text = self.replies[min(len(self.calls) - 1, len(self.replies) - 1)]
        return LlmReply(
            text=text, usage=LlmUsage(100, 20), model="claude-sonnet-4-5-20250929", ms=7
        )


class FakeResult:
    def __init__(self):
        self.records = [{"folder": SECRET_ROW_VALUE}]
        self.keys = ["folder"]
        self.row_count = 1
        self.truncated = False
        self.ms = 3


def _ok_read(cypher, params=None, database=None, row_cap=100, timeout_s=15.0):
    return FakeResult()


def _answer_and_record(tmp_path, question="how many applications?"):
    """Answer, then write the run line.

    Two steps because that is the real shape: the PIPELINE writes call lines and
    the ADK layer's ``_record_run`` writes the run line after the answer
    (graph_qa/agent.py). Calling ``ledger.run`` here is that layer, exactly as
    the R3 suite does it — reproducing the agent's own sequence rather than a
    convenience wrapper that would test a path nothing takes."""
    provider = FakeProvider(
        [
            f'{{"spec_id": "{SPEC_ID}", "params": {{}}}}',
            "There is 1 application.",
        ]
    )
    pipeline = pl.GraphQaPipeline(
        provider=provider,
        run_read=_ok_read,
        graph_schema=lambda: LIVE_SCHEMA,
        vocabulary_loader=lambda: VOCAB,
        ledger=LlmLedger(log_dir=tmp_path),
    )
    envelope = pipeline.answer(question, run_id="qa-test-r8")
    LlmLedger(log_dir=tmp_path).run(envelope, question)
    return envelope


def _run_line(tmp_path) -> dict:
    for path in tmp_path.glob("qa.graph_qa.*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            if record.get("kind") == "run":
                return record
    raise AssertionError("no run line written")


# ── the triple lands ─────────────────────────────────────────────────────────


def test_the_run_line_carries_the_whole_triple(tmp_path):
    envelope = _answer_and_record(tmp_path)
    line = _run_line(tmp_path)
    assert line["question"] == "how many applications?"
    assert line["answer"] == envelope.answer
    assert line["answer"], "an empty answer field would make every triple unevaluable"
    assert set(line["context"]) >= {"rows", "chunks", "tokens_est", "sources", "steps"}


def test_context_carries_counts_and_identities_but_no_retrieved_values(tmp_path):
    """The rule the extension turns on, asserted against the whole file.

    A retrieved row holds folder names, host names and SEAL ids. The ledger's
    full-text rule was written for a question a person typed, and moving graph
    content into it under that rule is a different act. The check is over the
    ENTIRE ledger text rather than the context key alone: a leak that arrived
    through some other field would be just as much a leak.
    """
    _answer_and_record(tmp_path)
    text = "".join(p.read_text(encoding="utf-8") for p in tmp_path.glob("qa.graph_qa.*.jsonl"))
    assert SECRET_ROW_VALUE not in text, "a retrieved row VALUE reached the ledger"
    line = _run_line(tmp_path)
    assert isinstance(line["context"]["rows"], int)
    assert line["context"]["steps"], "the step identities ARE recorded — that is the point"
    assert all("cypher" not in s for s in line["context"]["steps"]), (
        "the Cypher belongs in cypher_steps, which the promotion feed reads; "
        "duplicating it into the context summary would be two homes for one fact"
    )


def test_the_graph_node_is_unchanged(tmp_path):
    """Local-ledger-only. agent_run_writer builds the :AgentRun props, and the
    triple must not appear among them — the graph side of R3's privacy rule is
    not what R8 extended."""
    from common import agent_run_writer

    envelope = _answer_and_record(tmp_path)
    # The REAL props the writer builds — an earlier draft of this test guarded a
    # function name that does not exist and fell through to a weaker source scan,
    # which is the instrument-measuring-nothing failure this repo keeps meeting.
    props = agent_run_writer.agent_run_props(envelope)
    assert "answer" not in props, "the answer text must not reach the graph node"
    assert "question" not in props, "only question_sha256 + question_chars ever do"
    assert props["question_sha256"] == envelope.question_sha256
    assert envelope.answer not in json.dumps(
        props
    ), "not by key and not by value: the answer must not arrive inside some other prop"


def test_cypher_steps_carry_the_query_and_omit_steps_that_ran_none(tmp_path):
    _answer_and_record(tmp_path)
    line = _run_line(tmp_path)
    steps = line["cypher_steps"]
    assert steps, "the spec step ran Cypher and must be recorded"
    assert all(s["cypher"] for s in steps), (
        "a step that ran no Cypher is omitted rather than recorded as a null — "
        "an empty query must not look like a contribution to a frequency ranking"
    )


# ── never inline ─────────────────────────────────────────────────────────────


def test_the_answer_path_imports_none_of_the_evaluation_modules():
    """The acceptance's "never inline in the answer path", as a fact about
    imports rather than a promise in a docstring. An evaluation reached from
    the pipeline would put a model call, its latency and its cost on every
    question a person asks."""
    source = source_text(REPO_ROOT / "agents" / "graph_qa" / "pipeline.py")
    imported = imported_modules(source)
    for module in ("common.answer_eval", "common.cap_tuning", "common.spec_promotion"):
        assert module not in imported, f"pipeline.py imports {module}"
        assert module.split(".")[-1] not in imported, f"pipeline.py imports {module}"


# ── the scorers ──────────────────────────────────────────────────────────────


def _triple(answer="an answer", rows=0, chunks=0) -> Triple:
    return Triple(
        run_id="r1",
        question="q",
        answer=answer,
        context={"rows": rows, "chunks": chunks},
        tier="spec",
        complete=True,
    )


def test_groundedness_is_a_floor_and_says_so():
    grounded = Groundedness().score(_triple(rows=3))
    assert grounded.value == 1.0
    assert "FLOOR" in grounded.reason, (
        "the caveat is the point: an answer built on rows can still misread them, "
        "and a bare 1.0 would read as a correctness grade"
    )
    ungrounded = Groundedness().score(_triple(rows=0, chunks=0))
    assert ungrounded.value == 0.0
    assert "nothing was retrieved" in ungrounded.reason


def test_groundedness_declines_rather_than_scoring_a_missing_answer():
    assert Groundedness().score(_triple(answer="   ")).value is None


@pytest.mark.parametrize("metric", ["faithfulness", "answer_relevancy"])
def test_the_llm_judged_metrics_raise_instead_of_approximating(metric):
    """The design decision, asserted. A token-overlap number labelled
    'answer relevancy' would be indistinguishable from a judged one to every
    caller, which is exactly why there is no fallback."""
    with pytest.raises(JudgeUnavailableError) as exc:
        LlmJudge(metric).score(_triple(rows=1))
    message = str(exc.value)
    assert "graph_qa.providers" in message, "the failure has to say what it needs"
    assert "no deterministic fallback" in message


def test_the_default_scorer_set_holds_only_the_deterministic_one():
    names = {s.name for s in DETERMINISTIC_SCORERS}
    assert names == {"groundedness"}


# ── the harness ──────────────────────────────────────────────────────────────


def test_a_pre_r8_run_is_marked_unevaluable_rather_than_dropped():
    """ "40 runs, 12 evaluable" is a different and more useful report than
    "12 runs"."""
    read = LedgerRead(runs=[{"kind": "run", "run_id": "old", "question": "q"}])
    [result] = evaluate(read)
    assert result.evaluable is False
    assert "before the triple was persisted" in result.scores[0].reason


def test_evaluating_a_real_ledger_round_trips(tmp_path):
    _answer_and_record(tmp_path)
    read = read_ledger(tmp_path)
    assert len(read.runs) == 1 and read.skipped == 0
    [result] = evaluate(read)
    assert result.evaluable
    assert result.scores[0].name == "groundedness"


def test_a_corrupt_line_is_skipped_and_counted_never_fatal(tmp_path):
    _answer_and_record(tmp_path)
    path = next(tmp_path.glob("qa.graph_qa.*.jsonl"))
    with path.open("a", encoding="utf-8") as fh:
        fh.write('{"kind": "run", "run_id": "half-writ\n')
    read = read_ledger(tmp_path)
    assert read.skipped == 1, "the truncated line is counted"
    assert len(read.runs) == 1, "and the good line still reads"


def test_an_empty_ledger_reports_nothing_to_score_rather_than_a_number(tmp_path):
    text = summarize(evaluate(read_ledger(tmp_path)))
    assert "NOTHING TO SCORE" in text
    assert "Not a result" in text


def test_the_summary_says_which_metrics_did_not_run(tmp_path):
    _answer_and_record(tmp_path)
    text = summarize(evaluate(read_ledger(tmp_path)))
    assert "Faithfulness and answer-relevancy are NOT in this report" in text


def test_triples_reports_the_incomplete_ones_as_incomplete():
    read = LedgerRead(
        runs=[
            {"kind": "run", "run_id": "a", "question": "q", "answer": "a", "context": {}},
            {"kind": "run", "run_id": "b", "question": "q"},
        ]
    )
    complete = [t for t in triples(read) if t.complete]
    assert [t.run_id for t in complete] == ["a"]
