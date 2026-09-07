"""Reading the R3 JSONL ledger back (R8).

THE LEDGER HAS ONLY EVER BEEN WRITTEN. R3 built two telemetry sinks and both
were append-only in practice: the graph node is queried by
``console.agent-runs.v1``, and this file was read by nobody. R8's three
data-driven clauses — evaluate stored triples, rank recurring Cypher, tune caps
from the distribution — are all reads of it, so the reader lands once, here,
rather than three times inside three consumers.

NOTHING IN THIS MODULE RUNS DURING AN ANSWER. It is imported by the on-demand
tools and by tests, never by ``pipeline.py``; the acceptance's "never inline in
the answer path" is a property of where this is called from, and
``tests/unit/test_answer_eval.py`` asserts the pipeline does not import it.

A CORRUPT LINE IS SKIPPED AND COUNTED, never fatal. The writer is best-effort by
design (telemetry must not be the reason an answer fails), so a half-written
line at the end of a day-file is a normal state of the world rather than a bug,
and a reader that raised on one would make the whole day unreadable. The count
is returned so a caller can say how much it skipped instead of quietly averaging
over less data than it thinks.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from drydocs_core.run_log import resolve_log_dir  # noqa: E402

#: The day-file prefix the writer uses (llm_ledger.LEDGER_BASENAME).
LEDGER_PREFIX = "qa.graph_qa"


@dataclass
class LedgerRead:
    """Everything one read of the ledger found, including what it could not."""

    runs: list[dict] = field(default_factory=list)
    calls: list[dict] = field(default_factory=list)
    files: list[Path] = field(default_factory=list)
    #: lines that were not parsable JSON, or carried no ``kind``
    skipped: int = 0

    @property
    def empty(self) -> bool:
        return not self.runs and not self.calls


def ledger_files(log_dir: Path | None = None) -> list[Path]:
    """Every day-file, oldest first. Missing directory is not an error — it is
    the state of a machine that has never answered a question."""
    directory = log_dir or resolve_log_dir()
    if not directory.is_dir():
        return []
    return sorted(directory.glob(f"{LEDGER_PREFIX}.*.jsonl"))


def read_ledger(log_dir: Path | None = None) -> LedgerRead:
    out = LedgerRead()
    for path in ledger_files(log_dir):
        out.files.append(path)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            out.skipped += 1
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                out.skipped += 1
                continue
            kind = record.get("kind")
            if kind == "run":
                out.runs.append(record)
            elif kind == "llm_call":
                out.calls.append(record)
            else:
                out.skipped += 1
    return out


@dataclass
class Triple:
    """One stored question/context/answer, as an evaluator receives it."""

    run_id: str
    question: str
    answer: str
    context: dict
    tier: str
    #: runs written before R8 carry no answer; they are not evaluable and say so
    complete: bool


def triples(read: LedgerRead) -> list[Triple]:
    """The evaluable runs, with the pre-R8 ones marked rather than dropped.

    A run written before the triple landed has a question and no answer. It is
    returned with ``complete=False`` instead of being filtered out, because
    "we have 40 runs and can evaluate 12" is a different and more useful report
    than "we have 12 runs".
    """
    out = []
    for r in read.runs:
        answer = r.get("answer")
        out.append(
            Triple(
                run_id=r.get("run_id", ""),
                question=r.get("question", ""),
                answer=answer or "",
                context=r.get("context") or {},
                tier=r.get("tier", ""),
                complete=bool(r.get("question")) and answer is not None,
            )
        )
    return out
