"""Tier 2 — the bounded enhance/solve loop (ADR 0007 decision 1, backlog R6).

Engages ONLY when Tier-1 context is insufficient (no rows, or no valid query
at all). Everything about it is bounded, because an unbounded agent loop on a
production-support question is a cost incident waiting for a bad night:

  * iterations           <= MAX_ITERATIONS (2)
  * next-step decision   majority of VOTE_SAMPLES (3) independent samples
  * fix loop             <= 2, inherited by reusing Tier-1's retrieval
  * per-question tokens  a budget that STOPS exploration when spent

and every run terminates: either an answer, or an explicit "cannot answer".

Two bounding decisions worth stating, because both trade a nicety for
termination and neither is obvious from the caps alone:

**A tie, or an unparseable vote, counts as SOLVE.** The failure mode of voting
is not a wrong answer, it is a loop that will not stop; so ambiguity resolves
toward terminating, never toward another round of spending.

**The budget bounds EXPLORATION, not the whole run.** Once it is spent the loop
stops enhancing, but if evidence was gathered, one final solve call still runs —
deliberately over budget — and the envelope records `exhausted: true`. The
alternative (refusing the last call) would burn the budget gathering evidence
and then throw it away unanswered, which is the worst of both. With NO evidence
and no budget the run ends with the explicit cannot-answer and spends nothing
more.

Pure by construction: the controller takes `llm` / `retrieve` callables rather
than the pipeline, so the whole loop is testable with fakes and the private
coupling stays inside pipeline.py.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field

from graph_qa.task_graph import TaskGraph

MAX_ITERATIONS = 2
VOTE_SAMPLES = 3
DEFAULT_TOKEN_BUDGET = 12_000

NEXT_STEP_SYSTEM = (
    "You decide the next step for a bounded question-answering loop over a "
    "knowledge graph. Answer 'solve' when the evidence gathered so far can "
    "answer the question, or when no further sub-question would plausibly "
    "help. Answer 'enhance' ONLY when one more targeted sub-question would "
    "close a specific, named gap.\n"
    'Reply with JSON only: {"step": "enhance" | "solve", "why": "<short>"}'
)

DECOMPOSE_SYSTEM = (
    "You turn a question about a knowledge graph into ONE narrower "
    "sub-question that a single Cypher query could answer. Target the gap the "
    "evidence so far leaves open. Do not restate the original question.\n"
    'Reply with JSON only: {"subquestion": "..."}'
)

SOLVE_SYSTEM = (
    "You answer a question from evidence gathered across several graph "
    "queries. Use ONLY that evidence; cite counts and names from it. If the "
    "evidence is partial, answer what it supports and say plainly what is "
    "still missing — never invent data, and never imply more coverage than "
    "the evidence gives."
)

CANNOT_ANSWER = (
    "I could not answer this from the graph. The bounded follow-up loop ran "
    "and gathered no usable evidence — the steps show every query attempted "
    "and why each failed. Try naming the specific node type or property you "
    "are after, or run one of the registered explorer views."
)


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"no JSON object in model reply: {text[:200]!r}")
    return json.loads(match.group(0))


@dataclass
class Tier2Outcome:
    """What the loop did — every cap's effect is reportable, never silent."""

    answer: str | None = None
    answered: bool = False
    iterations: int = 0
    votes: list[str] = field(default_factory=list)
    forced_solve: bool = False
    budget_exhausted: bool = False
    graph: TaskGraph = field(default_factory=TaskGraph)
    evidence_rows: int = 0
    # chars of the evidence block actually handed to the solve call — the
    # envelope's context.tokens_est is derived from this, so it reports the
    # context Tier 2 really used rather than a placeholder zero
    evidence_chars: int = 0


def _vote_next_step(
    llm: Callable[..., str],
    question: str,
    evidence_summary: str,
    iteration: int,
) -> tuple[str, list[str]]:
    """VOTE_SAMPLES independent samples; majority wins, ties go to solve."""
    votes: list[str] = []
    for sample in range(VOTE_SAMPLES):
        user = (
            f"Question: {question}\n\n"
            f"Evidence gathered so far:\n{evidence_summary or '(none)'}\n\n"
            f"This would be follow-up round {iteration} of {MAX_ITERATIONS}."
        )
        try:
            raw = llm(NEXT_STEP_SYSTEM, user, step=f"tier2-vote-{iteration}.{sample + 1}")
            step = str(_extract_json(raw).get("step", "")).strip().lower()
        except Exception:
            step = "solve"  # a vote we cannot read is not a licence to keep spending
        votes.append(step if step in ("enhance", "solve") else "solve")
    enhance = votes.count("enhance")
    return ("enhance" if enhance > len(votes) - enhance else "solve"), votes


def _summarize(graph: TaskGraph) -> str:
    lines = []
    for node in graph.nodes_of_kind("evidence"):
        lines.append(f"- {node.label} -> {node.rows} row(s)")
    return "\n".join(lines)


def run_tier2(
    question: str,
    *,
    llm: Callable[..., str],
    retrieve: Callable[[str], object | None],
    tokens_used: Callable[[], int],
    set_iteration: Callable[[int], None] = lambda _n: None,
    token_budget: int = DEFAULT_TOKEN_BUDGET,
    max_iterations: int = MAX_ITERATIONS,
) -> Tier2Outcome:
    """Run the bounded loop. `retrieve` is Tier-1 retrieval (its own <=2 fix
    loop is inherited); it returns a row-carrying result or None."""
    outcome = Tier2Outcome()
    graph = outcome.graph
    root = graph.add_node("question", question, iteration=0)
    graph.capture(0, phase="start")

    for iteration in range(1, max_iterations + 1):
        set_iteration(iteration)
        outcome.iterations = iteration

        if tokens_used() >= token_budget:
            outcome.budget_exhausted = True
            outcome.forced_solve = True
            break

        decision, votes = _vote_next_step(llm, question, _summarize(graph), iteration)
        outcome.votes.extend(votes)
        if decision == "solve":
            break

        try:
            raw = llm(
                DECOMPOSE_SYSTEM,
                f"Question: {question}\n\nEvidence so far:\n{_summarize(graph) or '(none)'}",
                step=f"tier2-decompose-{iteration}",
            )
            subquestion = str(_extract_json(raw).get("subquestion", "")).strip()
        except Exception:
            subquestion = ""
        if not subquestion:
            # Nothing to enhance WITH — stop rather than burn the next round on
            # the same empty decomposition.
            outcome.forced_solve = True
            break

        sub_id = graph.add_node("subquestion", subquestion, iteration=iteration)
        graph.add_edge(root, sub_id, "decomposes_to")

        result = retrieve(subquestion)
        rows = getattr(result, "row_count", 0) if result is not None else 0
        if result is not None:
            ev_id = graph.add_node("evidence", subquestion, iteration=iteration, rows=rows)
            graph.add_edge(sub_id, ev_id, "evidence_for")
            outcome.evidence_rows += rows
        graph.capture(iteration, phase="iteration")

    else:
        # The for-else fires when the iteration cap is what stopped us, which is
        # a DIFFERENT reason from "the vote said solve" — worth distinguishing
        # in the envelope, since only one of them means the cap is too tight.
        outcome.forced_solve = True

    evidence = graph.nodes_of_kind("evidence")
    if not evidence:
        outcome.answer = CANNOT_ANSWER
        outcome.answered = False
        graph.capture(outcome.iterations, phase="final")
        return outcome

    if tokens_used() >= token_budget:
        outcome.budget_exhausted = True  # the final solve call runs anyway (see module docstring)

    evidence_block = _summarize(graph)
    outcome.evidence_chars = len(evidence_block)
    try:
        outcome.answer = llm(
            SOLVE_SYSTEM,
            f"Question: {question}\n\nEvidence:\n{evidence_block}",
            step="tier2-solve",
        )
        outcome.answered = bool(outcome.answer and outcome.answer.strip())
    except Exception:
        outcome.answer = CANNOT_ANSWER
        outcome.answered = False

    answer_id = graph.add_node("answer", "answer", iteration=outcome.iterations)
    for node in evidence:
        graph.add_edge(node.id, answer_id, "answers")
    graph.capture(outcome.iterations, phase="final")
    return outcome
