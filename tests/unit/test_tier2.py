"""R6 — the Tier-2 bounded enhance/solve loop, with fakes (no LLM, no driver).

What this suite proves, per R6's acceptance:

- the loop engages ONLY when Tier-1 context is insufficient (and a run that
  Tier 0/1 answered never pays for it);
- every cap holds: iterations <= 2, the next-step decision is a majority of 3
  independent votes, the fix loop stays Tier-1's <= 2, and the per-question
  token budget stops exploration;
- every run terminates — an answer, or the explicit "cannot answer";
- **the enhance branch writes only the in-process task graph.** R1 ruled the
  residency in-process only, so the proof is structural: the task-graph module
  has nothing to persist WITH, and the loop's only executor is Tier-1 read
  retrieval. Both are asserted here.
- per-iteration snapshots are captured in the shape the console's d3 pane
  lays out, and the R3 ledger sees a real iteration number per call.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
for entry in (str(REPO_ROOT / "agents"), str(REPO_ROOT)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from graph_qa import pipeline as pl  # noqa: E402
from graph_qa import tier2 as t2  # noqa: E402
from graph_qa.providers import LlmReply, LlmUsage  # noqa: E402
from graph_qa.task_graph import TaskGraph  # noqa: E402

TASK_GRAPH_SRC = REPO_ROOT / "agents" / "graph_qa" / "task_graph.py"


@dataclass
class FakeResult:
    row_count: int = 0
    records: list = field(default_factory=list)
    truncated: bool = False
    ms: int = 1


class FakeLlm:
    """Replies are consumed in order; `calls` records (step, system-prefix)."""

    def __init__(self, replies: list[str], tokens_per_call: int = 100) -> None:
        self.replies = list(replies)
        self.calls: list[str] = []
        self.tokens = 0
        self.tokens_per_call = tokens_per_call

    def __call__(self, system: str, user: str, step: str = "tier2") -> str:
        self.calls.append(step)
        self.tokens += self.tokens_per_call
        return self.replies.pop(0) if self.replies else '{"step": "solve"}'


def _vote(step: str) -> str:
    return json.dumps({"step": step})


def _sub(text: str) -> str:
    return json.dumps({"subquestion": text})


def _run(llm: FakeLlm, retrieve, **kw):
    return t2.run_tier2(
        "which jobs feed the payments warehouse?",
        llm=llm,
        retrieve=retrieve,
        tokens_used=lambda: llm.tokens,
        **kw,
    )


# --------------------------------------------------------------------------- #
# caps
# --------------------------------------------------------------------------- #
def test_the_vote_is_three_independent_samples_and_the_majority_decides() -> None:
    llm = FakeLlm([_vote("enhance"), _vote("enhance"), _vote("solve"), _sub("which jobs?")])
    outcome = _run(llm, lambda q: FakeResult(row_count=3))
    assert llm.calls[:3] == ["tier2-vote-1.1", "tier2-vote-1.2", "tier2-vote-1.3"]
    assert outcome.votes[:3] == ["enhance", "enhance", "solve"]
    assert t2.VOTE_SAMPLES == 3


def test_a_split_vote_resolves_to_solve_so_the_loop_always_shrinks() -> None:
    """A tie is ambiguity, and ambiguity must not buy another round of spending
    — the failure mode of voting is a loop that will not stop."""
    llm = FakeLlm([_vote("enhance"), _vote("solve"), _vote("garbage")])
    outcome = _run(llm, lambda q: FakeResult(row_count=1))
    assert outcome.votes == ["enhance", "solve", "solve"]
    assert outcome.iterations == 1
    assert not outcome.graph.nodes_of_kind("subquestion")  # never enhanced


def test_an_unparseable_vote_counts_as_solve_not_as_a_retry() -> None:
    llm = FakeLlm(["not json at all", "also not json", "{}"])
    outcome = _run(llm, lambda q: FakeResult())
    assert outcome.votes == ["solve", "solve", "solve"]


def test_iterations_are_capped_at_two() -> None:
    """Vote 'enhance' forever; the cap, not the model, has to stop it."""
    llm = FakeLlm([_vote("enhance")] * 3 + [_sub("q1")] + [_vote("enhance")] * 3 + [_sub("q2")])
    outcome = _run(llm, lambda q: FakeResult(row_count=2))
    assert t2.MAX_ITERATIONS == 2
    assert outcome.iterations == 2
    assert len(outcome.graph.nodes_of_kind("subquestion")) == 2
    assert (
        outcome.forced_solve
    ), "hitting the cap must be reported, not silently equivalent to solve"


def test_the_token_budget_stops_exploration_and_says_so() -> None:
    llm = FakeLlm(
        [_vote("enhance")] * 3 + [_sub("q1")] + [_vote("enhance")] * 3, tokens_per_call=500
    )
    outcome = _run(llm, lambda q: FakeResult(row_count=1), token_budget=1_000)
    assert outcome.budget_exhausted
    assert outcome.iterations <= t2.MAX_ITERATIONS


def test_the_budget_bounds_exploration_but_still_lets_the_run_answer() -> None:
    """Evidence gathered under budget must not be thrown away unanswered — the
    terminating solve call runs deliberately over budget, and is recorded."""
    llm = FakeLlm(
        [_vote("enhance")] * 3 + [_sub("q1")] + ["the answer"],
        tokens_per_call=400,
    )
    outcome = _run(llm, lambda q: FakeResult(row_count=5), token_budget=1_500)
    # round 1 spends past the budget; round 2 never starts, but the evidence
    # round 1 bought still gets answered
    assert outcome.budget_exhausted
    assert outcome.iterations == 2, "the budget check is what ended round 2"
    assert outcome.answered
    assert outcome.answer == "the answer"


def test_no_evidence_and_no_budget_spends_nothing_more() -> None:
    """The cheap exit: nothing gathered and the budget already gone (a caller
    that spent it in Tier 1) — the loop makes no call at all."""
    llm = FakeLlm([], tokens_per_call=5_000)
    llm.tokens = 5_000  # Tier 0/1 already spent it before Tier 2 engaged
    outcome = _run(llm, lambda q: None, token_budget=1_000)
    assert outcome.budget_exhausted
    assert outcome.answer == t2.CANNOT_ANSWER
    assert llm.calls == []


# --------------------------------------------------------------------------- #
# termination
# --------------------------------------------------------------------------- #
def test_every_run_terminates_with_an_answer_or_an_explicit_cannot_answer() -> None:
    llm = FakeLlm([_vote("enhance")] * 3 + [_sub("q1")] + [_vote("solve")] * 3)
    outcome = _run(llm, lambda q: None)  # retrieval never yields anything
    assert outcome.answered is False
    assert outcome.answer == t2.CANNOT_ANSWER
    assert "could not answer" in outcome.answer


def test_an_empty_decomposition_stops_rather_than_repeating_itself() -> None:
    llm = FakeLlm([_vote("enhance")] * 3 + [_sub("   ")])
    outcome = _run(llm, lambda q: FakeResult(row_count=1))
    assert outcome.forced_solve
    assert outcome.iterations == 1


def test_a_solve_call_that_raises_degrades_to_cannot_answer() -> None:
    class Exploding(FakeLlm):
        def __call__(self, system, user, step="tier2"):
            if step == "tier2-solve":
                raise RuntimeError("provider down")
            return super().__call__(system, user, step)

    llm = Exploding([_vote("enhance")] * 3 + [_sub("q1")] + [_vote("solve")] * 3)
    outcome = _run(llm, lambda q: FakeResult(row_count=4))
    assert outcome.answered is False
    assert outcome.answer == t2.CANNOT_ANSWER


# --------------------------------------------------------------------------- #
# the R1 residency ruling — in-process only
# --------------------------------------------------------------------------- #
def test_the_task_graph_module_has_nothing_to_persist_with() -> None:
    """R1 gate ruling A: in-process only, dies with the run.

    Structural, not behavioural, and deliberately so — a comment saying "do not
    persist this" is not a control. If someone later imports a driver or writes
    a MERGE here, this fails, and re-proposing persistence is a NEW gate.
    """
    src = TASK_GRAPH_SRC.read_text(encoding="utf-8")
    code = "\n".join(line for line in src.splitlines() if not line.lstrip().startswith("#"))
    body = code.split('"""', 2)[-1]  # drop the module docstring, which NAMES the databases
    for forbidden in ("neo4j", "driver", "session(", "MERGE", "CREATE ", "ddcontext", "ddlineage"):
        assert forbidden not in body, f"task_graph.py must not reference {forbidden!r}"


def test_the_loop_never_reaches_a_writer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Behavioural half: the only thing the loop can execute is the retrieval
    callable it was handed, and the pipeline hands it READ retrieval."""
    seen: list[str] = []

    def retrieve(subquestion: str):
        seen.append(subquestion)
        return FakeResult(row_count=1)

    llm = FakeLlm([_vote("enhance")] * 3 + [_sub("q1")] + [_vote("solve")] * 3 + ["answer"])
    outcome = _run(llm, retrieve)
    assert seen == ["q1"]
    assert outcome.answered
    # the graph the loop built is a plain object, reachable only from the outcome
    assert isinstance(outcome.graph, TaskGraph)


# --------------------------------------------------------------------------- #
# snapshots
# --------------------------------------------------------------------------- #
def test_snapshots_are_cumulative_and_shaped_for_the_existing_d3_pane() -> None:
    llm = FakeLlm([_vote("enhance")] * 3 + [_sub("q1")] + [_vote("solve")] * 3 + ["answer"])
    outcome = _run(llm, lambda q: FakeResult(row_count=7))
    snaps = outcome.graph.snapshots
    assert [s["phase"] for s in snaps] == ["start", "iteration", "final"]
    # every edge is exactly the record web/src/lib/forceLayout.ts consumes
    for snap in snaps:
        for edge in snap["edges"]:
            assert set(edge) == {"source", "target", "via"}
    # cumulative, not deltas — each snapshot renders alone
    assert len(snaps[0]["nodes"]) < len(snaps[1]["nodes"]) < len(snaps[2]["nodes"])


def test_the_answer_node_joins_every_piece_of_evidence() -> None:
    llm = FakeLlm(
        [_vote("enhance")] * 3 + [_sub("q1")] + [_vote("enhance")] * 3 + [_sub("q2")] + ["answer"]
    )
    outcome = _run(llm, lambda q: FakeResult(row_count=1))
    final = outcome.graph.snapshots[-1]
    answers = [e for e in final["edges"] if e["via"] == "answers"]
    assert len(answers) == 2, "each evidence node must connect to the answer it supports"


# --------------------------------------------------------------------------- #
# the task graph itself
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# the seam: engagement is conditional, and the caps ride the real envelope
# --------------------------------------------------------------------------- #
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
LIVE_SCHEMA = {
    "labels": ["ControlMJob"],
    "relationshipTypes": ["WAS_INFORMED_BY"],
    "propertyKeys": ["job_id"],
}


@dataclass
class ScriptedProvider:
    replies: list[str]
    provider: str = "anthropic"
    calls: int = 0

    def complete(self, system: str, user: str, max_tokens: int = 1200) -> LlmReply:
        text = self.replies[min(self.calls, len(self.replies) - 1)]
        self.calls += 1
        return LlmReply(text=text, usage=LlmUsage(100, 20), model="fake-model", ms=5)


def _pipeline(provider, run_read, **kw):
    return pl.GraphQaPipeline(
        provider=provider,
        run_read=run_read,
        graph_schema=lambda: LIVE_SCHEMA,
        vocabulary_loader=lambda: VOCAB,
        **kw,
    )


def _cypher(text: str) -> str:
    return json.dumps({"cypher": text})


BAD = "MATCH (n) RETURN n AS n"
GOOD = "MATCH (j:ControlMJob) RETURN j.job_id AS job_id"


def _selective_read(executed: list):
    def run_read(cypher, params=None, database=None, row_cap=100, timeout_s=15.0):
        executed.append(cypher)
        if "ControlMJob" not in cypher:
            raise RuntimeError("no such property")
        return FakeResult(row_count=4, records=[{"job_id": "J1"}])

    return run_read


def test_tier2_does_not_engage_when_tier1_answered() -> None:
    """The common question must never pay for the loop."""
    provider = ScriptedProvider(
        [
            '{"spec_id": null, "params": {}}',
            _cypher(GOOD),
            "4 jobs.",
        ]
    )
    env = _pipeline(provider, _selective_read([])).answer("which jobs?", run_id="qa-1")
    assert env.tier == "text2cypher"
    assert env.metrics.tier2["engaged"] is False
    assert env.task_graph == []
    assert env.metrics.iterations == 1


def test_tier2_engages_when_tier1_context_is_insufficient() -> None:
    executed: list[str] = []
    provider = ScriptedProvider(
        [
            '{"spec_id": null, "params": {}}',  # router: no spec fits
            _cypher(BAD),  # tier-1 attempt
            _cypher(BAD),  # fix 1
            _cypher(BAD),  # fix 2 -> tier 1 gives up
            _vote("enhance"),
            _vote("enhance"),
            _vote("enhance"),
            _sub("which jobs feed it?"),
            _cypher(GOOD),  # the sub-question's retrieval succeeds
            _vote("solve"),
            _vote("solve"),
            _vote("solve"),
            "4 jobs feed it.",  # tier2-solve
        ]
    )
    env = _pipeline(provider, _selective_read(executed)).answer("which jobs?", run_id="qa-2")

    assert env.tier == "tier2"
    assert env.answer == "4 jobs feed it."
    assert env.metrics.tier2["engaged"] is True
    assert env.metrics.iterations == 2
    assert [s["phase"] for s in env.task_graph] == ["start", "iteration", "final"]
    assert any(s.kind == "tier2" for s in env.steps)
    # tier-1's fix loop ran to its cap and tier 2 then retrieved once more —
    # every one of them through the same read path, never a second executor
    assert executed == [BAD, BAD, BAD, GOOD]


def test_the_budget_is_reported_even_when_it_never_bites() -> None:
    """A limit visible only once it has bitten is one nobody can tune first."""
    provider = ScriptedProvider(['{"spec_id": null, "params": {}}', _cypher(GOOD), "4 jobs."])
    env = _pipeline(provider, _selective_read([]), token_budget=9_999).answer("q", run_id="qa-3")
    assert env.metrics.budget["tokens_limit"] == 9_999
    assert env.metrics.budget["tokens_used"] == env.metrics.tokens.total
    assert env.metrics.budget["exhausted"] is False


def test_the_ledger_sees_a_real_iteration_number_per_call() -> None:
    """R6 acceptance: per-iteration cost is what makes the caps tunable from
    data. Before this the ledger recorded `1` for every call in the run."""
    rows: list[dict] = []

    class Ledger:
        def call(self, **kw):
            rows.append(kw)
            return 0.001

    provider = ScriptedProvider(
        [
            '{"spec_id": null, "params": {}}',
            _cypher(BAD),
            _cypher(BAD),
            _cypher(BAD),
            _vote("enhance"),
            _vote("enhance"),
            _vote("enhance"),
            _sub("which jobs feed it?"),
            _cypher(GOOD),
            _vote("solve"),
            _vote("solve"),
            _vote("solve"),
            "4 jobs feed it.",
        ]
    )
    _pipeline(provider, _selective_read([]), ledger=Ledger()).answer("q", run_id="qa-4")

    by_step = {r["step"]: r["iteration"] for r in rows}
    assert by_step["router"] == 1
    assert by_step["tier2-vote-1.1"] == 1
    assert by_step["tier2-vote-2.1"] == 2, "round 2's calls must be attributed to round 2"
    assert max(r["iteration"] for r in rows) == t2.MAX_ITERATIONS


def test_the_node_and_edge_vocabularies_are_closed() -> None:
    """An open `kind` would drift into an unreviewed parallel ontology."""
    graph = TaskGraph()
    with pytest.raises(ValueError):
        graph.add_node("whatever", "x", iteration=0)
    a = graph.add_node("question", "q", iteration=0)
    b = graph.add_node("evidence", "e", iteration=1, rows=2)
    with pytest.raises(ValueError):
        graph.add_edge(a, b, "relates_to")
    with pytest.raises(KeyError):
        graph.add_edge(a, "evidence-99", "evidence_for")
