"""The promotion feed: recurring Tier-1 Cypher, ranked, as CANDIDATES (R8).

WHAT THIS EMITS IS A PROPOSAL AND NOTHING ELSE. The acceptance says spec
candidates are "gate-bound, never auto-registered as permanent specs", so this
module writes ONE artifact and touches the registry in no code path — it does
not import ``QUERY_SPECS``, does not construct a ``QuerySpec``, does not reach
``EphemeralSpecStore``, and does not write ``drydocs_api/query_specs.py``.
``tests/unit/test_spec_promotion.py`` asserts that by scanning this file's
source, because a rule that lives only in a docstring is a rule until the first
convenient afternoon.

WHY A REGISTERED SPEC IS A GOVERNED THING. A permanent QuerySpec is reviewed
Cypher: it names its database, its classification, its columns and its params,
and ADR 0005's property — that the browser cannot influence which Cypher runs —
holds only because that review happened. Text2cypher output is the opposite: a
model wrote it, once, for one question. Frequency is evidence that a QUESTION
recurs, never evidence that the query answering it is correct. So the ranking is
a queue for a reviewer and the artifact says so on its face.

NORMALIZATION IS THE WHOLE RANKING. Two runs of the same question produce Cypher
that differs in whitespace, in an inlined limit, and in whatever string literal
the model chose to match on. Ranked raw, they are two candidates of one each and
nothing ever recurs. Normalized — comments dropped, string and numeric literals
replaced by a placeholder, whitespace collapsed, case folded on keywords — they
are one candidate of two, which is the number the clause asks for. The
UNNORMALIZED examples ride along in the artifact so a reviewer sees what actually
ran rather than the fingerprint.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from common.ledger_read import LedgerRead, read_ledger

#: Steps whose Cypher is a candidate. A `spec` step already ran a REVIEWED
#: query — promoting one would propose a spec that exists — so only the
#: model-authored retrieval steps are ranked.
CANDIDATE_STEP_KINDS = ("text2cypher", "tier2")

_COMMENT = re.compile(r"//[^\n]*")
_STRING = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")
_NUMBER = re.compile(r"\b\d+(?:\.\d+)?\b")
_PARAM = re.compile(r"\$\w+")
_WS = re.compile(r"\s+")


def normalize_cypher(cypher: str) -> str:
    """The fingerprint two runs of one question share.

    Order matters: comments go FIRST, because a comment can contain a quote and
    stripping literals first would eat the rest of the line — the same
    mis-tokenisation web/src/test/sourceScan.ts records, met again here.
    """
    text = _COMMENT.sub(" ", cypher)
    text = _STRING.sub("'?'", text)
    text = _PARAM.sub("$?", text)
    text = _NUMBER.sub("?", text)
    return _WS.sub(" ", text).strip().lower()


@dataclass
class Candidate:
    fingerprint: str
    normalized: str
    count: int
    databases: list[str]
    #: verbatim Cypher as it actually ran, newest last, capped for readability
    examples: list[str] = field(default_factory=list)
    run_ids: list[str] = field(default_factory=list)
    #: rows the query returned across its runs — a query that always returned
    #: zero recurs because it keeps failing, which is the opposite of a promotion
    #: case and must be visible in the ranking rather than inferred from it
    rows_seen: list[int] = field(default_factory=list)

    @property
    def always_empty(self) -> bool:
        return bool(self.rows_seen) and all(r == 0 for r in self.rows_seen)


def rank_candidates(
    read: LedgerRead,
    *,
    min_count: int = 2,
    max_examples: int = 3,
) -> list[Candidate]:
    """Rank by frequency, most frequent first, ties broken by fingerprint.

    ``min_count`` defaults to 2 because "recurring" is the clause's word: a
    query seen once is not evidence of anything, and a feed that proposed every
    query ever run would be a list of the ledger rather than a queue.
    """
    by_fp: dict[str, Candidate] = {}
    for run in read.runs:
        for step in run.get("cypher_steps") or []:
            if step.get("kind") not in CANDIDATE_STEP_KINDS:
                continue
            cypher = step.get("cypher")
            if not cypher:
                continue
            normalized = normalize_cypher(cypher)
            fp = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
            cand = by_fp.get(fp)
            if cand is None:
                cand = Candidate(fingerprint=fp, normalized=normalized, count=0, databases=[])
                by_fp[fp] = cand
            cand.count += 1
            db = step.get("database")
            if db and db not in cand.databases:
                cand.databases.append(db)
            if len(cand.examples) < max_examples:
                cand.examples.append(cypher)
            run_id = run.get("run_id")
            if run_id and run_id not in cand.run_ids:
                cand.run_ids.append(run_id)
            if isinstance(step.get("rows"), int):
                cand.rows_seen.append(step["rows"])
    ranked = [c for c in by_fp.values() if c.count >= min_count]
    ranked.sort(key=lambda c: (-c.count, c.fingerprint))
    return ranked


HEADER = """# =============================================================================
# Spec promotion CANDIDATES — generated, and a PROPOSAL rather than a decision.
#
# NOTHING HERE IS REGISTERED. Each entry is Cypher a model wrote during a Tier-1
# retrieval, seen more than once across runs. Frequency is evidence that a
# QUESTION recurs; it is not evidence that the query answering it is correct,
# and a permanent QuerySpec is reviewed Cypher whose database, classification,
# columns and params a person signed off. Promoting one means writing that spec
# by hand and taking it through the gate — never copying a block from this file.
#
# `always_empty: true` marks a query that recurred and returned nothing every
# time. That is a query failing repeatedly, which is the opposite of a promotion
# case, and it is surfaced rather than left to be inferred from a zero.
#
# Regenerate: python -m common.spec_promotion (from agents/, with the venv).
# =============================================================================
"""


def to_yaml(candidates: list[Candidate], read: LedgerRead) -> str:
    """Hand-rolled, because the artifact is small and the agents venv is a
    deliberately thin dependency set — pulling PyYAML in for one dump would be
    the registry-discipline cost this repo keeps declining to pay."""
    lines = [HEADER, "schema: drydocs.spec-promotion-candidates.v1"]
    lines.append(f"runs_read: {len(read.runs)}")
    lines.append(f"files_read: {len(read.files)}")
    lines.append(f"lines_skipped: {read.skipped}")
    lines.append(f"candidates: {len(candidates)}")
    if not candidates:
        # An empty list with a reason, never an absent key: "no candidates" and
        # "the feed never ran" have to look different in the artifact.
        lines.append("entries: []")
        lines.append("# No Cypher recurred across the runs read. If runs_read is 0,")
        lines.append("# this machine has answered no questions — not a finding.")
        return "\n".join(lines) + "\n"
    lines.append("entries:")
    for c in candidates:
        lines.append(f"  - fingerprint: {c.fingerprint}")
        lines.append(f"    count: {c.count}")
        lines.append(f"    databases: [{', '.join(c.databases)}]")
        lines.append(f"    always_empty: {'true' if c.always_empty else 'false'}")
        lines.append(f"    run_ids: [{', '.join(c.run_ids[:10])}]")
        lines.append("    normalized: |")
        lines.append(f"      {c.normalized}")
        lines.append("    examples:")
        for ex in c.examples:
            lines.append("      - |")
            for row in ex.splitlines() or [""]:
                lines.append(f"        {row}")
    return "\n".join(lines) + "\n"


def write_candidates(out_path: Path, log_dir: Path | None = None) -> tuple[Path, int]:
    """Generate the artifact. Returns the path and how many candidates it holds."""
    read = read_ledger(log_dir)
    ranked = rank_candidates(read)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(to_yaml(ranked, read), encoding="utf-8")
    return out_path, len(ranked)


def _default_out() -> Path:
    return (
        Path(__file__).resolve().parents[2] / "docs" / "design" / "spec-promotion-candidates.yaml"
    )


def main() -> int:
    path, count = write_candidates(_default_out())
    print(f"wrote {path} — {count} candidate(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
