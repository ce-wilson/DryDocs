"""R8 — loop-cap proposals from the ledger.

The clause is "loop caps re-tuned from ledger data with the change recorded in
notes", and the load-bearing half is FROM LEDGER DATA. A tuner that answers "2"
from an empty ledger is indistinguishable from one that answers "2" from a
thousand runs, and only the second is worth having — so the refusal is the first
thing tested.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for entry in (str(REPO_ROOT / "agents"), str(REPO_ROOT)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.cap_tuning import (  # noqa: E402
    MIN_RUNS_FOR_CONFIDENCE,
    current_fix_retry_cap,
    fix_retry_distribution,
    iteration_distribution,
    propose_fix_retry_cap,
    report,
)
from common.ledger_read import LedgerRead  # noqa: E402


def _runs(count: int, retries: int, iterations: int = 1) -> list[dict]:
    return [
        {
            "kind": "run",
            "run_id": f"r{i}",
            "iterations": iterations,
            "cypher_steps": [
                {
                    "i": 1,
                    "kind": "text2cypher",
                    "cypher": "MATCH (n) RETURN n",
                    "fix_retries": retries,
                }
            ],
        }
        for i in range(count)
    ]


# ── the refusal ──────────────────────────────────────────────────────────────


def test_an_empty_ledger_yields_no_proposal_and_says_so():
    proposal = propose_fix_retry_cap(LedgerRead())
    assert proposal.confident is False
    assert proposal.changed is False
    assert proposal.value == proposal.current, "the cap is returned UNCHANGED, never zero"
    assert "0 run(s)" in proposal.reason


def test_too_few_runs_is_a_refusal_with_the_threshold_named():
    proposal = propose_fix_retry_cap(LedgerRead(runs=_runs(MIN_RUNS_FOR_CONFIDENCE - 1, 0)))
    assert proposal.confident is False
    assert str(MIN_RUNS_FOR_CONFIDENCE) in proposal.reason
    assert proposal.distribution, "the observed distribution still rides along"


def test_the_current_cap_is_read_from_the_pipeline_not_restated():
    """A proposal is relative to the value actually in force, so the tuner must
    not carry its own copy of it."""
    from graph_qa.pipeline import MAX_FIX_RETRIES

    assert current_fix_retry_cap() == MAX_FIX_RETRIES


# ── the proposals ────────────────────────────────────────────────────────────


def test_headroom_never_reached_proposes_lowering_the_cap():
    """Every step succeeded in 0 retries across a real distribution: the cap's
    remaining attempts have never been used."""
    read = LedgerRead(runs=_runs(MIN_RUNS_FOR_CONFIDENCE, 0))
    proposal = propose_fix_retry_cap(read, current=2)
    assert proposal.confident is True
    assert proposal.value == 0
    assert proposal.changed is True
    assert "never been reached" in proposal.reason


def test_steps_hitting_the_cap_is_not_evidence_to_raise_it():
    """The ambiguity is stated rather than resolved: from the ledger alone a
    step that USED the cap and a step that was CUT OFF by it look identical."""
    read = LedgerRead(runs=_runs(MIN_RUNS_FOR_CONFIDENCE, 2))
    proposal = propose_fix_retry_cap(read, current=2)
    assert proposal.confident is True
    assert proposal.value == 2, "unchanged — hitting a cap is not a reason to move it"
    assert proposal.changed is False
    assert "CUT OFF" in proposal.reason


def test_the_distribution_counts_retrieval_steps_not_llm_calls():
    """A fix retry is a property of a QUERY attempt. Counting call lines would
    fold in the router and the answer call and inflate every bucket."""
    read = LedgerRead(
        runs=[
            {
                "kind": "run",
                "run_id": "r",
                "cypher_steps": [
                    {"kind": "text2cypher", "cypher": "a", "fix_retries": 0},
                    {"kind": "text2cypher", "cypher": "b", "fix_retries": 2},
                ],
            }
        ],
        calls=[{"kind": "llm_call", "step": "router"}] * 9,
    )
    assert dict(fix_retry_distribution(read)) == {0: 1, 2: 1}


def test_iterations_come_off_the_run_line():
    read = LedgerRead(runs=_runs(3, 0, iterations=2))
    assert dict(iteration_distribution(read)) == {2: 3}


# ── the report ───────────────────────────────────────────────────────────────


def test_the_report_says_none_observed_rather_than_zero():
    """ "none observed" and "observed to be zero" are different facts, and a
    report that printed `{}` for both would let a reader take the second."""
    text = report(LedgerRead())
    assert "none observed" in text
    assert "NOT confident" in text
    assert "NO CHANGE PROPOSED" in text


def test_the_report_names_what_it_read():
    read = LedgerRead(runs=_runs(2, 1), files=[Path("qa.graph_qa.20260906.jsonl")], skipped=1)
    text = report(read)
    assert "runs read         : 2" in text
    assert "lines skipped     : 1" in text
