"""R8 — the spec promotion feed: ranks, and registers nothing.

The clause is "emits spec CANDIDATES for review — gate-bound, never
auto-registered as permanent specs", and the second half is the one that needs a
guard rather than a docstring. A module that could reach the registry will reach
it on the first convenient afternoon, so the reach is asserted absent.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for entry in (str(REPO_ROOT / "agents"), str(REPO_ROOT)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.ledger_read import LedgerRead  # noqa: E402
from common.spec_promotion import (  # noqa: E402
    CANDIDATE_STEP_KINDS,
    normalize_cypher,
    rank_candidates,
    to_yaml,
    write_candidates,
)

from tests.source_scan import called_names, code_only, imported_modules, source_text  # noqa: E402

MODULE = REPO_ROOT / "agents" / "common" / "spec_promotion.py"


def _run(run_id: str, *steps: dict) -> dict:
    return {"kind": "run", "run_id": run_id, "cypher_steps": list(steps)}


def _step(cypher: str, kind: str = "text2cypher", rows: int = 3, database: str = "drydocs") -> dict:
    return {"i": 1, "kind": kind, "cypher": cypher, "rows": rows, "database": database}


# ── normalization is the ranking ─────────────────────────────────────────────


def test_two_runs_of_one_question_normalize_to_one_fingerprint():
    """Ranked raw these are two candidates of one each and nothing ever recurs.
    The limit, the whitespace and the matched literal are exactly what differs
    between two runs of the same question."""
    a = "MATCH (j:ControlMJob) WHERE j.name = 'NIGHTLY' RETURN j LIMIT 25"
    b = "MATCH (j:ControlMJob)\n  WHERE j.name = 'WEEKLY'\n  RETURN j LIMIT 100"
    assert normalize_cypher(a) == normalize_cypher(b)


def test_a_comment_containing_a_quote_does_not_eat_the_line():
    """Comments strip FIRST. Stripping literals first would consume from the
    quote inside the comment to the next quote in real code — the same
    mis-tokenisation web/src/test/sourceScan.ts records, met again in Cypher."""
    with_comment = "MATCH (n) // it's a node\nRETURN n"
    assert "return n" in normalize_cypher(with_comment)


def test_genuinely_different_queries_stay_apart():
    a = "MATCH (j:ControlMJob) RETURN j"
    b = "MATCH (f:ControlMFolder) RETURN f"
    assert normalize_cypher(a) != normalize_cypher(b)


# ── the ranking ──────────────────────────────────────────────────────────────


def test_only_recurring_cypher_becomes_a_candidate():
    """`min_count` is 2 because "recurring" is the clause's word — a feed that
    proposed every query ever run would be a list of the ledger."""
    read = LedgerRead(
        runs=[
            _run("a", _step("MATCH (n) RETURN n LIMIT 1")),
            _run("b", _step("MATCH (n) RETURN n LIMIT 2")),
            _run("c", _step("MATCH (x:Other) RETURN x")),
        ]
    )
    ranked = rank_candidates(read)
    assert len(ranked) == 1
    assert ranked[0].count == 2
    assert ranked[0].run_ids == ["a", "b"]


def test_a_reviewed_spec_step_is_never_proposed():
    """A `spec` step already ran a REVIEWED query. Promoting one would propose
    a spec that exists."""
    read = LedgerRead(
        runs=[
            _run("a", _step("MATCH (n) RETURN n", kind="spec")),
            _run("b", _step("MATCH (n) RETURN n", kind="spec")),
        ]
    )
    assert rank_candidates(read) == []
    assert "spec" not in CANDIDATE_STEP_KINDS


def test_a_query_that_always_returned_nothing_is_flagged_not_ranked_silently():
    """That is a query FAILING repeatedly, which is the opposite of a promotion
    case, and a reviewer must not have to infer it from a zero."""
    read = LedgerRead(
        runs=[
            _run("a", _step("MATCH (n:Missing) RETURN n", rows=0)),
            _run("b", _step("MATCH (n:Missing) RETURN n", rows=0)),
        ]
    )
    [candidate] = rank_candidates(read)
    assert candidate.always_empty is True


def test_the_verbatim_cypher_rides_along_with_the_fingerprint():
    """A reviewer needs what actually ran, not the normalized shape."""
    read = LedgerRead(
        runs=[
            _run("a", _step("MATCH (n) RETURN n LIMIT 1")),
            _run("b", _step("MATCH (n) RETURN n LIMIT 2")),
        ]
    )
    [candidate] = rank_candidates(read)
    assert "LIMIT 1" in candidate.examples[0]
    assert "LIMIT 2" in candidate.examples[1]


def test_ties_are_broken_deterministically():
    read = LedgerRead(
        runs=[
            _run("a", _step("MATCH (a) RETURN a"), _step("MATCH (b) RETURN b")),
            _run("b", _step("MATCH (a) RETURN a"), _step("MATCH (b) RETURN b")),
        ]
    )
    once = [c.fingerprint for c in rank_candidates(read)]
    twice = [c.fingerprint for c in rank_candidates(read)]
    assert once == twice and len(once) == 2


# ── the artifact ─────────────────────────────────────────────────────────────


def test_the_artifact_says_on_its_face_that_nothing_is_registered():
    text = to_yaml([], LedgerRead())
    assert "NOTHING HERE IS REGISTERED" in text
    assert "schema: drydocs.spec-promotion-candidates.v1" in text


def test_an_empty_feed_says_why_rather_than_omitting_the_key():
    """ "no candidates" and "the feed never ran" have to look different."""
    text = to_yaml([], LedgerRead())
    assert "entries: []" in text
    assert "runs_read: 0" in text
    assert "answered no questions" in text


def test_writing_the_artifact_round_trips(tmp_path):
    out = tmp_path / "candidates.yaml"
    path, count = write_candidates(out, log_dir=tmp_path)
    assert path == out and count == 0
    assert "entries: []" in out.read_text(encoding="utf-8")


# ── the guard the clause needs ───────────────────────────────────────────────


def test_the_feed_cannot_reach_the_spec_registry():
    """Gate-bound, asserted. Source-scanned over `code_only` (J66) because the
    module's own docstring names every symbol it must not touch — a raw
    substring scan would fail on the explanation."""
    source = source_text(MODULE)
    code = code_only(source)
    for forbidden in ("QUERY_SPECS", "QuerySpec", "EphemeralSpecStore", "register_spec"):
        assert forbidden not in code, f"the promotion feed reaches {forbidden}"
    imported = imported_modules(source)
    assert not any("query_specs" in m for m in imported), imported
    assert not any(m.startswith("drydocs_api") for m in imported), (
        "the feed writes an artifact; reaching the API package at all is a step "
        "toward registering from it"
    )


def test_the_feed_writes_exactly_one_kind_of_thing():
    """It may write its artifact and nothing else — in particular never
    query_specs.py, which is where a 'helpful' auto-registration would land."""
    code = code_only(source_text(MODULE))
    assert "query_specs.py" not in code
    called = called_names(source_text(MODULE))
    assert "write_text" in called, "the artifact writer is the one write"
