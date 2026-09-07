"""On-demand answer evaluation over stored triples (R8).

NEVER INLINE, and that is the clause's substance rather than a caveat. Nothing
in the answer path imports this module: ``graph_qa.pipeline`` does not, and
``tests/unit/test_answer_eval.py`` asserts it by reading the pipeline's imports.
An evaluation that ran during an answer would add a model call, its latency and
its cost to every question a person asks, and would make the grade a thing the
person waits for rather than a thing an operator reviews.

TWO SCORERS, AND THEY ARE NOT THE SAME KIND OF THING. Saying so is the point.

  * GROUNDEDNESS is DETERMINISTIC and runs here. It asks one narrow question —
    did the answer come back with retrieved rows behind it, or none — and it can
    answer that from the stored context counts with no model. It is a floor, not
    a grade: an answer built on rows can still be wrong about them.

  * FAITHFULNESS and ANSWER-RELEVANCY are LLM-JUDGED. That is what those words
    mean in the RAGAS vocabulary the acceptance borrows, and there is no
    deterministic stand-in for them. ``LlmJudge`` is a DECLARED SEAM that raises
    rather than a stub that returns a number: a token-overlap score labelled
    "answer relevancy" would be a fabricated metric wearing a real name, and a
    reader would have no way to tell. It raises with the provider it needs
    named, so the failure says what to do.

The harness — read triples, apply scorers, report — is complete and testable
without a judge, and that is deliberate: the architecture is what R8 asks for,
and the judge is a machine capability rather than a design question.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from common.ledger_read import LedgerRead, Triple, triples


@dataclass
class Score:
    name: str
    #: 0.0-1.0, or None when the scorer could not answer for this triple
    value: float | None
    reason: str


@dataclass
class Evaluation:
    run_id: str
    scores: list[Score] = field(default_factory=list)
    #: False for a run stored before R8 carried the answer — not a bad score,
    #: an unevaluable record, and the two must never average together
    evaluable: bool = True


class Scorer(Protocol):
    name: str

    def score(self, triple: Triple) -> Score: ...


class Groundedness:
    """Did the answer have retrieved rows behind it?

    DETERMINISTIC, and narrow on purpose. It does not read the answer's claims
    against the rows — it cannot, because the rows are not stored (the ledger
    keeps counts and identities, never values, and that is the right call). What
    it catches is the failure that needs no judge: an answer produced with
    nothing retrieved. That answer came from the model's own weights and the
    schema prompt, and on a support question about this graph it is the one
    class of wrong that is wrong every time.
    """

    name = "groundedness"

    def score(self, triple: Triple) -> Score:
        ctx = triple.context or {}
        rows = ctx.get("rows") or 0
        chunks = ctx.get("chunks") or 0
        retrieved = rows + chunks
        if not triple.answer.strip():
            return Score(self.name, None, "no answer text stored — nothing to ground")
        if retrieved > 0:
            return Score(
                self.name,
                1.0,
                f"{rows} row(s) and {chunks} chunk(s) were retrieved before answering. "
                "A FLOOR, not a grade: an answer built on rows can still misread them.",
            )
        return Score(
            self.name,
            0.0,
            "nothing was retrieved — this answer came from the model and the schema "
            "prompt alone, with no graph content behind it.",
        )


class JudgeUnavailableError(RuntimeError):
    """Raised instead of returning a number nobody measured."""


class LlmJudge:
    """Faithfulness / answer-relevancy, as the vocabulary actually means them.

    A DECLARED SEAM. It raises rather than approximating, because the whole
    failure this module is written against is a fabricated metric wearing a real
    name: a caller who receives 0.72 from a token-overlap function labelled
    "answer relevancy" has no way to learn it was never judged.

    Implementing it needs a provider — ``graph_qa.providers`` resolves one from
    ``agents/.env``, merged by ``common.neo4j_tool`` at import (G131) — and a
    machine where the agent stack runs. The prompt pair belongs here when that
    lands, beside the seam, not in the caller.
    """

    def __init__(self, metric: str) -> None:
        self.name = metric

    def score(self, triple: Triple) -> Score:
        raise JudgeUnavailableError(
            f"{self.name} is LLM-judged and no judge is configured. It needs a provider "
            "(graph_qa.providers, keyed from agents/.env) on a machine where the agent "
            "stack runs. There is deliberately no deterministic fallback: a number "
            "computed by string overlap and labelled "
            f"'{self.name}' would be indistinguishable from a judged one."
        )


DETERMINISTIC_SCORERS: tuple[Scorer, ...] = (Groundedness(),)


def evaluate(
    read: LedgerRead,
    scorers: tuple[Scorer, ...] = DETERMINISTIC_SCORERS,
) -> list[Evaluation]:
    """Score every stored triple. Unevaluable runs come back MARKED, not dropped.

    A run written before R8 has a question and no answer. Returning it with
    ``evaluable=False`` is what lets a report say "40 runs, 12 evaluable"
    instead of silently reporting on 12 and calling it the ledger.
    """
    out: list[Evaluation] = []
    for triple in triples(read):
        if not triple.complete:
            out.append(
                Evaluation(
                    run_id=triple.run_id,
                    evaluable=False,
                    scores=[
                        Score(
                            "stored",
                            None,
                            "run recorded before the triple was persisted — question only",
                        )
                    ],
                )
            )
            continue
        out.append(Evaluation(run_id=triple.run_id, scores=[s.score(triple) for s in scorers]))
    return out


def summarize(evaluations: list[Evaluation]) -> str:
    total = len(evaluations)
    evaluable = [e for e in evaluations if e.evaluable]
    lines = [
        "Answer evaluation (R8, on demand)",
        f"  runs stored    : {total}",
        f"  evaluable      : {len(evaluable)}",
        f"  question-only  : {total - len(evaluable)} (recorded before the triple was persisted)",
    ]
    if not evaluable:
        lines.append("")
        lines.append("  NOTHING TO SCORE. Not a result — no complete triple has been stored.")
        return "\n".join(lines)
    for name in {s.name for e in evaluable for s in e.scores}:
        values = [
            s.value for e in evaluable for s in e.scores if s.name == name and s.value is not None
        ]
        if values:
            lines.append(
                f"  {name}: mean {sum(values) / len(values):.2f} over {len(values)} run(s)"
            )
        else:
            lines.append(f"  {name}: no run could be scored")
    lines.append("")
    lines.append("  Faithfulness and answer-relevancy are NOT in this report: they are")
    lines.append("  LLM-judged and no judge ran. See LlmJudge.")
    return "\n".join(lines)
