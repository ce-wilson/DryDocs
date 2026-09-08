"""Loop-cap proposals, computed from the ledger (R8).

THE CAPS THIS READS, AND WHY THEY ARE TUNABLE AT ALL. ``pipeline.MAX_FIX_RETRIES``
bounds the text2cypher fix loop; the Tier-2 iteration cap bounds the enhance/solve
loop. R6 recorded ``budget.exhausted`` and ``tier2.forced_solve`` for exactly this
moment — its own comment says a cap whose effect is invisible cannot be tuned —
and R3 put ``iteration`` on every LLM-call line. R8 is where something finally
reads them.

THIS MODULE PROPOSES AND NEVER APPLIES. It returns numbers and the evidence
behind them; changing a constant is a code edit a person makes, in a commit that
can be read. That is not ceremony: a cap is a cost and latency bound on every
future answer, and a process that moved it automatically would move it on the
next unusual week too.

AND IT REFUSES TO PROPOSE FROM NOTHING. This is the rule the module exists to
hold. With no runs, or too few, ``propose`` returns a proposal whose ``value`` is
the CURRENT cap and whose ``confident`` is False, naming what it lacked. A tuner
that answered "2" from an empty ledger would be indistinguishable from a tuner
that answered "2" from a thousand runs, and the second is the only one worth
having. The observed distribution goes in the report either way, including when
it is empty.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from common.ledger_read import LedgerRead

#: Below this many runs, no proposal is confident. Small on purpose — the point
#: is not a statistical threshold, it is that ONE run is not a distribution and
#: the refusal has to bite before anybody is tempted.
MIN_RUNS_FOR_CONFIDENCE = 20


#: What the caps are today, read from the pipeline rather than restated, so a
#: proposal is always relative to the value actually in force.
def current_fix_retry_cap() -> int:
    from graph_qa.pipeline import MAX_FIX_RETRIES

    return MAX_FIX_RETRIES


@dataclass
class Proposal:
    name: str
    current: int
    value: int
    confident: bool
    reason: str
    #: the observed distribution the number came from, {observed: count}
    distribution: dict[int, int] = field(default_factory=dict)
    runs_seen: int = 0

    @property
    def changed(self) -> bool:
        return self.confident and self.value != self.current


def fix_retry_distribution(read: LedgerRead) -> Counter:
    """How many fix retries each retrieval step actually needed.

    Read off ``cypher_steps`` rather than the call lines: a fix retry is a
    property of a QUERY attempt, and the call lines count LLM calls, which
    include the answer call and the router. Counting those as retries would
    inflate every bucket.
    """
    seen: Counter = Counter()
    for run in read.runs:
        for step in run.get("cypher_steps") or []:
            retries = step.get("fix_retries")
            if isinstance(retries, int):
                seen[retries] += 1
    return seen


def iteration_distribution(read: LedgerRead) -> Counter:
    seen: Counter = Counter()
    for run in read.runs:
        iterations = run.get("iterations")
        if isinstance(iterations, int):
            seen[iterations] += 1
    return seen


def propose_fix_retry_cap(read: LedgerRead, *, current: int | None = None) -> Proposal:
    """Propose the fix-retry cap from what the loop actually needed.

    THE RULE: the cap should be the highest retry count that ever SUCCEEDED,
    because a lower cap would have turned those answers into failures and a
    higher one only buys attempts nothing has ever needed. What the ledger can
    see is how many retries each step used; a step that used the cap is the
    interesting one, because it either just made it or was cut off, and the two
    are indistinguishable from this side. That ambiguity is stated in the reason
    rather than resolved by assumption — resolving it needs the step's error
    field, which is a richer read than a cap proposal should require.
    """
    cap = current if current is not None else current_fix_retry_cap()
    dist = fix_retry_distribution(read)
    runs = len(read.runs)
    if runs < MIN_RUNS_FOR_CONFIDENCE:
        return Proposal(
            name="MAX_FIX_RETRIES",
            current=cap,
            value=cap,
            confident=False,
            reason=(
                f"{runs} run(s) in the ledger, below the {MIN_RUNS_FOR_CONFIDENCE} this "
                "module requires before it will call a number a proposal. The cap is "
                "unchanged and the distribution below is what was actually seen."
            ),
            distribution=dict(dist),
            runs_seen=runs,
        )
    used = max(dist) if dist else 0
    at_cap = dist.get(cap, 0)
    total = sum(dist.values()) or 1
    if used < cap:
        return Proposal(
            name="MAX_FIX_RETRIES",
            current=cap,
            value=used,
            confident=True,
            reason=(
                f"no step has ever used more than {used} retr(ies) across {total} "
                f"retrieval step(s); the remaining headroom has never been reached."
            ),
            distribution=dict(dist),
            runs_seen=runs,
        )
    share = at_cap / total
    return Proposal(
        name="MAX_FIX_RETRIES",
        current=cap,
        value=cap,
        confident=True,
        reason=(
            f"{at_cap} of {total} step(s) ({share:.0%}) used the full {cap}. From the "
            "ledger alone a step that used the cap and a step that was CUT OFF by it "
            "look identical, so this is not evidence to raise it — it is evidence to "
            "look at those steps' errors before deciding."
        ),
        distribution=dict(dist),
        runs_seen=runs,
    )


def report(read: LedgerRead) -> str:
    """A human-readable summary. Says what it saw, including nothing."""
    proposal = propose_fix_retry_cap(read)
    iterations = iteration_distribution(read)
    lines = [
        "Loop-cap proposal (R8)",
        f"  ledger files read : {len(read.files)}",
        f"  runs read         : {len(read.runs)}",
        f"  lines skipped     : {read.skipped}",
        "",
        f"  {proposal.name}: current {proposal.current}, proposed {proposal.value}"
        f" ({'confident' if proposal.confident else 'NOT confident'})",
        f"    {proposal.reason}",
        f"    fix-retry distribution : {proposal.distribution or 'none observed'}",
        f"    tier-2 iterations      : {dict(iterations) or 'none observed'}",
    ]
    if not proposal.changed:
        lines.append("")
        lines.append("  NO CHANGE PROPOSED. Nothing here is a reason to edit a constant.")
    return "\n".join(lines)
