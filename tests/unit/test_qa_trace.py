"""R18 — the Ask decision trace, offline (fakes; no litellm, no driver, no ADK).

What this suite proves, clause by clause:

- (a) enablement is the `qa-debug` kind's declared ``level: DEBUG`` and nothing
  else — the api-debug mechanism, reused rather than re-invented — and every
  record carries ``run_id`` and ``session_id``, so two sessions interleaved in
  one day-file still read back apart;
- (b) a full router -> query -> answer run produces the observable decision
  path: the question as typed and as normalized, the candidates on offer, the
  chosen spec AND the router's stated reason, the schema/vocabulary prompt, the
  generated Cypher with its fix attempts and errors, executed row counts, the
  answer call's inputs, and the closing tier and timing;
- (c) OFF is the default and the fallback, the pipeline behaves identically in
  both modes, and the two redactions hold: the answer hop records row SHAPE and
  never row VALUES (R8's boundary), and no raw caller identity is written;
- (d) the reader retrieves by correlation key, refuses to be a log download,
  and the route that serves it is admin-gated.
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

from common.llm_ledger import LlmLedger  # noqa: E402
from common.qa_trace import TRACE_TEXT_BOUND, QaTrace  # noqa: E402
from graph_qa import pipeline as pl  # noqa: E402

from drydocs_api.qa_trace_read import TraceQueryError, read_trace  # noqa: E402

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

#: A value that exists in NO schema, vocabulary or prompt — only in a returned
#: row. Anything that copies row values into the trace copies this with them,
#: which is what makes its absence a measurement rather than an opinion.
SECRET_ROW_VALUE = "PAYROLL-SEAL-70042-nightly"

_KINDS_DOC = """\
schema: drydocs.log-kinds.v1
root:
  base: home
  path: logs/DryDocs/
defaults:
  level: INFO
  retention_days: 90
  rotation: per-run
  format: log
  dir: ~
kinds:
  - id: qa-debug
    writer: agents.common.qa_trace.QaTrace
{level}    retention_days: 7
    rotation: per-day
    format: jsonl
"""


def _kinds(tmp_path: Path, *, debug: bool) -> Path:
    """A declaration with the qa-debug kind on or off — the ONE switch."""
    tmp_path.mkdir(parents=True, exist_ok=True)  # callers pass sub-paths for A/B runs
    path = tmp_path / f"log-kinds-{'debug' if debug else 'off'}.yaml"
    path.write_text(_KINDS_DOC.format(level="    level: DEBUG\n" if debug else ""), "utf-8")
    return path


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
    def __init__(self, records=None):
        self.records = records if records is not None else [{"app": SECRET_ROW_VALUE, "jobs": 3}]
        self.keys = list(self.records[0]) if self.records else []
        self.row_count = len(self.records)
        self.truncated = False
        self.ms = 3
        self.notifications = []


def _ok_read(cypher, params=None, database=None, row_cap=100, timeout_s=15.0):
    return FakeResult()


ROUTED = f'{{"spec_id": "{SPEC_ID}", "params": {{}}, "reason": "the question asks how many applications exist, which is exactly what this spec counts"}}'
ANSWERED = "There is 1 application."


def _run(
    tmp_path: Path,
    *,
    debug: bool = True,
    replies=None,
    run_id: str = "qa-test-r18",
    session_id: str = "ask-sess-1",
    user_id: str = "",
    run_read=_ok_read,
):
    """One question through the real pipeline with a tmp-dir trace + ledger."""
    provider = FakeProvider(replies if replies is not None else [ROUTED, ANSWERED])
    trace = QaTrace(log_dir=tmp_path, kinds_path=_kinds(tmp_path, debug=debug))
    pipeline = pl.GraphQaPipeline(
        provider=provider,
        run_read=run_read,
        graph_schema=lambda: LIVE_SCHEMA,
        vocabulary_loader=lambda: VOCAB,
        ledger=LlmLedger(log_dir=tmp_path),
        trace=trace,
    )
    envelope = pipeline.answer(
        "how many applications?",
        run_id=run_id,
        session_id=session_id,
        user_id=user_id,
    )
    return envelope, provider, trace


def _records(tmp_path: Path) -> list[dict]:
    files = list(tmp_path.glob("qa-debug.graph_qa.*.jsonl"))
    if not files:
        return []
    assert len(files) == 1, f"one day-file expected, got {[f.name for f in files]}"
    return [json.loads(line) for line in files[0].read_text("utf-8").splitlines() if line.strip()]


def _raw(tmp_path: Path) -> str:
    return "\n".join(p.read_text("utf-8") for p in tmp_path.glob("qa-debug.graph_qa.*.jsonl"))


# ── (a) enablement ───────────────────────────────────────────────────────────


def test_the_declaration_is_the_switch(tmp_path):
    """``level: DEBUG`` in config/log-kinds.yaml, and nothing else. There is no
    env var, no constructor flag and no request field that can turn this on —
    which is the api-debug ruling: an Ask question arrives as an HTTP request,
    and a per-request switch would belong to whoever sent the request."""
    assert QaTrace(log_dir=tmp_path, kinds_path=_kinds(tmp_path, debug=True)).enabled is True
    assert QaTrace(log_dir=tmp_path, kinds_path=_kinds(tmp_path, debug=False)).enabled is False


def test_the_repo_declaration_ships_the_trace_off():
    """The committed declaration is the DEFAULT deployment, and it is off. A
    debug tier that shipped on would make its own retention argument moot."""
    assert QaTrace().enabled is False


def test_an_unreadable_declaration_disables_rather_than_guesses(tmp_path):
    missing = tmp_path / "nope.yaml"
    assert QaTrace(log_dir=tmp_path, kinds_path=missing).enabled is False


def test_disabled_writes_nothing_at_all(tmp_path):
    """Default behaviour is the existing minimal telemetry contract (clause c):
    the 90-day ledger still writes, and the trace file does not exist."""
    envelope, _, trace = _run(tmp_path, debug=False)
    assert trace.enabled is False
    assert envelope.answer.endswith(ANSWERED)
    assert list(tmp_path.glob("qa-debug.*")) == []
    assert list(tmp_path.glob("qa.graph_qa.*.jsonl")), "the R3 ledger must be unaffected"


def test_the_envelope_says_whether_a_trace_exists(tmp_path):
    """An explicit False, not a missing field: the console has to tell "no trace
    was recorded" from "this agent predates R18"."""
    assert _run(tmp_path, debug=True)[0].debug_trace is True
    assert _run(tmp_path, debug=False)[0].debug_trace is False


# ── (a) correlation ──────────────────────────────────────────────────────────


def test_every_record_carries_the_correlation_key(tmp_path):
    _run(tmp_path)
    records = _records(tmp_path)
    assert records, "an enabled trace writes records"
    for record in records:
        assert record["kind"] == "qa_trace"
        assert record["run_id"] == "qa-test-r18"
        assert record["session_id"] == "ask-sess-1"
        assert isinstance(record["seq"], int)
        assert record["hop"]
        assert record["ts"]


def test_two_concurrent_sessions_interleave_and_still_separate(tmp_path):
    """Acceptance (d)'s "distinguish one question from concurrent sessions",
    measured the way it actually happens: both runs write to ONE day-file, and
    the correlation key is the only thing that pulls them apart."""
    _run(tmp_path, run_id="qa-run-A", session_id="ask-sess-A")
    _run(tmp_path, run_id="qa-run-B", session_id="ask-sess-B")

    both = _records(tmp_path)
    assert {r["run_id"] for r in both} == {"qa-run-A", "qa-run-B"}

    a = read_trace(run_id="qa-run-A", log_dir=tmp_path)
    b = read_trace(session_id="ask-sess-B", log_dir=tmp_path)
    assert a["record_count"] and a["record_count"] + b["record_count"] == len(both)
    assert {r["run_id"] for r in a["records"]} == {"qa-run-A"}
    assert {r["session_id"] for r in b["records"]} == {"ask-sess-B"}
    # seq is monotonic within a run, so a reader never has to trust file order
    seqs = [r["seq"] for r in a["records"]]
    assert seqs == sorted(seqs)


# ── (b) the full decision path ───────────────────────────────────────────────


def test_a_full_router_query_answer_trace(tmp_path):
    envelope, _, _ = _run(tmp_path)
    records = _records(tmp_path)
    hops = [r["hop"] for r in records]
    assert hops[0] == "run_open" and hops[-1] == "run_close"
    assert "router" in hops and "llm" in hops and "step" in hops

    opened = records[0]
    assert opened["question"] == "how many applications?"
    assert opened["normalized_question"] == "how many applications?"
    assert opened["question_chars"] == len("how many applications?")

    router = next(r for r in records if r["hop"] == "router")
    assert router["spec_id"] == SPEC_ID
    assert SPEC_ID in router["candidates"], "what was ON OFFER, not just what won"
    assert len(router["candidates"]) > 1
    assert "counts" in router["rationale"]  # the generated half of clause (b)
    assert router["parse_error"] is None

    router_call = next(
        r for r in records if r["hop"] == "llm" and r.get("hop") and "reason" in r["system"]
    )
    assert "spec_id" in router_call["system"] and "reason" in router_call["system"]
    assert router_call["reply"] == ROUTED  # the ENTIRE reply, which today is dropped
    assert router_call["prompt_tokens"] == 100 and router_call["completion_tokens"] == 20

    spec_step = next(r for r in records if r["hop"] == "step" and r["step_kind"] == "spec")
    assert spec_step["cypher"], "the executed Cypher is on the timeline"
    assert spec_step["rows"] == 1
    assert spec_step["database"]

    closed = records[-1]
    assert closed["tier"] == envelope.tier == "spec"
    assert closed["question_sha256"] == envelope.question_sha256
    assert closed["llm_calls"] == envelope.metrics.llm_calls
    assert closed["response_ms"] == envelope.metrics.response_ms
    assert closed["steps"] == len(envelope.steps)


def test_the_normalized_question_is_recorded_beside_the_typed_one(tmp_path):
    """R19 appends the person's own clarifications to the question before any
    prompt sees it. A trace showing only one of the two hides the single
    transformation the pipeline performs on a question."""
    provider = FakeProvider([ROUTED, ANSWERED])
    trace = QaTrace(log_dir=tmp_path, kinds_path=_kinds(tmp_path, debug=True))
    pipeline = pl.GraphQaPipeline(
        provider=provider,
        run_read=_ok_read,
        graph_schema=lambda: LIVE_SCHEMA,
        vocabulary_loader=lambda: VOCAB,
        trace=trace,
    )
    pipeline.answer(
        "how many applications?",
        run_id="qa-clar",
        session_id="s",
        clarifications=[{"term": "PAT", "resolution": "the product alignment tool"}],
    )
    opened = _records(tmp_path)[0]
    assert opened["question"] == "how many applications?"
    assert opened["normalized_question"] != opened["question"]
    assert "product alignment tool" in opened["normalized_question"]


def test_text2cypher_records_its_schema_prompt_generated_cypher_and_fix_attempts(tmp_path):
    """The Tier-1 half of clause (b): the grounding prompt, every generated
    query, and the validation errors that produced the next attempt. R18's
    evidence is three runs whose Cypher was reconstructable and whose REASONING
    was not — this is the other half arriving."""
    bad = '{"cypher": "MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk) RETURN d.name AS name"}'
    fixed = '{"cypher": "MATCH (c:Chunk)-[:PART_OF]->(d:Document) RETURN d.title AS title"}'
    calls = {"n": 0}

    def flaky_read(cypher, params=None, database=None, row_cap=100, timeout_s=15.0):
        calls["n"] += 1
        if "HAS_CHUNK" in cypher:
            raise ValueError("Unknown relationship type: HAS_CHUNK")
        return FakeResult()

    _run(
        tmp_path,
        replies=[
            '{"spec_id": null, "params": {}, "reason": "no spec covers document text"}',
            bad,
            fixed,
            ANSWERED,
        ],
        run_read=flaky_read,
    )
    records = _records(tmp_path)

    t2c_calls = [
        r
        for r in records
        if r["hop"] == "llm" and "Write ONE read-only Cypher" in r.get("user", "")
    ]
    assert t2c_calls, "the text2cypher call is on the timeline"
    assert "WAS_INFORMED_BY" in t2c_calls[0]["system"], "the vocabulary it was grounded on"
    assert "ControlMJob" in t2c_calls[0]["system"], "and the live schema"

    t2c_steps = [r for r in records if r["hop"] == "step" and r["step_kind"] == "text2cypher"]
    assert len(t2c_steps) >= 2, "the failed attempt AND the fix, not just the winner"
    assert "HAS_CHUNK" in t2c_steps[0]["cypher"]
    assert "HAS_CHUNK" in t2c_steps[0]["error"]
    assert t2c_steps[0]["fix_retries"] == 0
    assert t2c_steps[-1]["error"] is None and t2c_steps[-1]["rows"] == 1

    fix_call = [
        r for r in records if r["hop"] == "llm" and "previous Cypher failed" in r.get("user", "")
    ]
    assert fix_call, "the fix prompt carries the error the model was asked to correct"


def test_an_unparseable_router_reply_is_recorded_as_noise_not_as_a_choice(tmp_path):
    """Both fall-throughs put ``spec_id: None`` in the envelope, and they are
    different defects: one is a router that judged nothing fits, the other is a
    reply that never parsed."""
    _run(tmp_path, replies=["I think you want the applications one, honestly", "no rows"])
    router = next(r for r in _records(tmp_path) if r["hop"] == "router")
    assert router["spec_id"] is None
    assert router["parse_error"] and "no JSON object" in router["parse_error"]
    assert router["rationale"] is None


# ── (b) the generated rationale — a contract change, not a capture change ────


def test_the_router_is_asked_for_a_reason_in_both_modes(tmp_path):
    """The reason belongs to the DECISION, not to the observer watching it. A
    debug mode that changed the prompt would debug a pipeline nobody runs."""
    assert '"reason"' in pl.ROUTER_SYSTEM
    on = _run(tmp_path / "on", debug=True)[1].calls[0][0]
    off = _run(tmp_path / "off", debug=False)[1].calls[0][0]
    assert on == off == pl.ROUTER_SYSTEM


def test_the_rationale_reaches_the_step_and_is_bounded(tmp_path):
    envelope, _, _ = _run(tmp_path)
    router_step = next(s for s in envelope.steps if s.kind == "router")
    assert "counts" in router_step.rationale
    assert all(s.rationale is None for s in envelope.steps if s.kind != "router")

    long_reason = "x" * (pl.RATIONALE_CHARS + 500)
    envelope, _, _ = _run(
        tmp_path / "long",
        replies=[
            json.dumps({"spec_id": SPEC_ID, "params": {}, "reason": long_reason}),
            ANSWERED,
        ],
    )
    router_step = next(s for s in envelope.steps if s.kind == "router")
    assert len(router_step.rationale) == pl.RATIONALE_CHARS


def test_a_reply_without_a_reason_reads_as_absent(tmp_path):
    """A pre-R18 reply, and a model that ignored the instruction, both give
    None — never an empty string that looks like a stated non-reason."""
    envelope, _, _ = _run(
        tmp_path, replies=[f'{{"spec_id": "{SPEC_ID}", "params": {{}}}}', ANSWERED]
    )
    assert next(s for s in envelope.steps if s.kind == "router").rationale is None


# ── (c) debug adds a sink and changes nothing else ───────────────────────────


def test_the_pipeline_behaves_identically_with_the_trace_on_and_off(tmp_path):
    on_env, on_provider, _ = _run(tmp_path / "on", debug=True)
    off_env, off_provider, _ = _run(tmp_path / "off", debug=False)

    assert on_provider.calls == off_provider.calls, "same prompts, same order, same count"
    assert on_env.answer == off_env.answer
    assert on_env.tier == off_env.tier
    assert on_env.metrics.llm_calls == off_env.metrics.llm_calls
    assert [s.kind for s in on_env.steps] == [s.kind for s in off_env.steps]
    assert [s.cypher for s in on_env.steps] == [s.cypher for s in off_env.steps]


def test_a_broken_sink_never_breaks_an_answer(tmp_path):
    """Telemetry is an audit trail, never the reason an answer fails — the
    ledger's ruling, inherited."""
    blocked = tmp_path / "file-where-a-directory-should-be"
    blocked.write_text("not a directory", "utf-8")
    trace = QaTrace(log_dir=blocked, kinds_path=_kinds(tmp_path, debug=True))
    assert trace.enabled is True
    pipeline = pl.GraphQaPipeline(
        provider=FakeProvider([ROUTED, ANSWERED]),
        run_read=_ok_read,
        graph_schema=lambda: LIVE_SCHEMA,
        vocabulary_loader=lambda: VOCAB,
        trace=trace,
    )
    envelope = pipeline.answer("how many applications?", run_id="qa-broken", session_id="s")
    assert envelope.answer.endswith(ANSWERED) and envelope.tier == "spec"


# ── (c) redaction ────────────────────────────────────────────────────────────


def test_the_answer_hop_records_shape_and_never_row_values(tmp_path):
    """R8 refused retrieved VALUES in the 90-day ledger — a row holds folder
    names, host names and SEAL ids — and a debug tier that crossed that
    boundary would move graph content into a log whose rule was written for a
    question a person typed. The answer call's user prompt IS the rows JSON, so
    this is the one hop that records shape."""
    _run(tmp_path)
    assert SECRET_ROW_VALUE not in _raw(tmp_path)

    answer_call = next(r for r in _records(tmp_path) if r["hop"] == "llm" and "input" in r)
    assert answer_call["input"] == {
        "rows": 1,
        "columns": ["app", "jobs"],
        "row_count": 1,
        "truncated": False,
    }
    assert "user" not in answer_call, "the rows prompt is sized, never copied"
    assert answer_call["user_chars"] > 0 and answer_call["reply_chars"] > 0
    assert pl.ANSWER_SYSTEM in answer_call["system"], "the repo-authored half is kept in full"


def test_column_keys_are_schema_and_travel_but_their_values_do_not(tmp_path):
    """The distinction the redaction turns on, stated as a test: "which columns
    came back" is what a diagnostic needs; "what was in them" is the graph."""
    from common.qa_trace import _row_shape

    shape = _row_shape([{"host": "prod-db-07", "seal_id": 70042}, {"host": "prod-db-08"}])
    assert shape == {"rows": 2, "columns": ["host", "seal_id"]}
    assert "prod-db-07" not in json.dumps(shape)


def test_no_raw_caller_identity_is_ever_written(tmp_path):
    """Caller identity mirrors the question rule one level down: the envelope
    carries sha256 + length, and this module has no parameter that could take
    the identity itself."""
    envelope, _, _ = _run(tmp_path, user_id="alice.smith@example.com")
    assert "alice.smith@example.com" not in _raw(tmp_path)
    closed = _records(tmp_path)[-1]
    assert closed["user_id_sha256"] == envelope.user_id_sha256
    assert closed["question_sha256"] == envelope.question_sha256


def test_text_is_bounded_and_says_so(tmp_path):
    """A silently shortened prompt is a diagnostic that lies, so the flag ships
    with the truncation — always both fields, never one."""
    trace = QaTrace(log_dir=tmp_path, kinds_path=_kinds(tmp_path, debug=True))
    trace.llm(
        "r",
        "s",
        step="text2cypher",
        system="x" * (TRACE_TEXT_BOUND + 10),
        user="short",
        reply="also short",
        model="m",
        provider="anthropic",
        prompt_tokens=1,
        completion_tokens=1,
        ms=1,
    )
    record = _records(tmp_path)[0]
    assert len(record["system"]) == TRACE_TEXT_BOUND and record["system_truncated"] is True
    assert record["user"] == "short" and record["user_truncated"] is False


# ── (d) the read surface ─────────────────────────────────────────────────────


def test_a_lookup_without_a_correlation_key_is_refused(tmp_path):
    """A lookup by run id and a bulk log download are not the same route."""
    with pytest.raises(TraceQueryError):
        read_trace(log_dir=tmp_path)
    with pytest.raises(TraceQueryError):
        read_trace(run_id="   ", session_id="", log_dir=tmp_path)


def test_an_unknown_run_reads_as_empty_not_as_an_error(tmp_path):
    _run(tmp_path)
    out = read_trace(run_id="qa-never-happened", log_dir=tmp_path)
    assert out["records"] == [] and out["record_count"] == 0 and out["skipped"] == 0


def test_a_corrupt_line_is_skipped_and_counted(tmp_path):
    """The writer is best-effort by design, so a half-written last line is a
    normal state of the world; a reader that raised would make the day
    unreadable, and one that stayed quiet would average over less data than it
    reports."""
    _run(tmp_path)
    day_file = next(tmp_path.glob("qa-debug.graph_qa.*.jsonl"))
    with day_file.open("a", encoding="utf-8") as fh:
        fh.write('{"kind": "qa_trace", "run_id": "qa-test-r18", "hop": "tr\n')
    out = read_trace(run_id="qa-test-r18", log_dir=tmp_path)
    assert out["skipped"] == 1
    assert out["record_count"] > 0 and out["truncated"] is False


def test_the_reader_reports_whether_this_deployment_records_at_all(tmp_path):
    """An empty list with ``enabled: false`` is "nothing was recorded"; with
    ``true`` it is "no such run". Same empty list, two different problems."""
    assert read_trace(run_id="x", log_dir=tmp_path, kinds_path=_kinds(tmp_path, debug=True))[
        "enabled"
    ]
    assert not read_trace(run_id="x", log_dir=tmp_path, kinds_path=_kinds(tmp_path, debug=False))[
        "enabled"
    ]


def test_a_missing_log_directory_is_not_an_error(tmp_path):
    out = read_trace(run_id="x", log_dir=tmp_path / "never-created")
    assert out["files"] == [] and out["records"] == []


def test_the_reader_reaches_exactly_one_kind(tmp_path):
    """There is no parameter through which another kind's file can be named —
    the api-debug surfacing question log_estate.py holds for SME review stays
    held, because nothing here can reach that file."""
    (tmp_path / "api-debug.access.20260908.jsonl").write_text(
        json.dumps({"kind": "api_audit", "run_id": "qa-test-r18", "cypher": "MATCH (n) RETURN n"})
        + "\n",
        "utf-8",
    )
    _run(tmp_path)
    out = read_trace(run_id="qa-test-r18", log_dir=tmp_path)
    assert all(r["kind"] == "qa_trace" for r in out["records"])
    assert all(name.startswith("qa-debug.graph_qa.") for name in out["files"])


def test_the_trace_route_is_admin_gated():
    """The /raw-cypher gate, reused — a non-admin 403s before the query string
    is read. This is the one route on the API that serves log CONTENTS, so the
    gate is asserted here as well as in the route-wide guard."""
    pytest.importorskip("fastapi", reason="optional api group (poetry install --with api)")
    import ast
    import inspect

    from drydocs_api import app as app_module

    tree = ast.parse(inspect.getsource(app_module))
    fn = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "get_qa_trace"
    )
    annotations = {ast.unparse(a.annotation) for a in fn.args.args if a.annotation}
    assert "AdminUser" in annotations


def test_tier_2_prompts_carry_counts_and_never_row_values(tmp_path):
    """The OTHER path that touches rows, measured rather than assumed.

    Tier 2 is reached only when Tier 1 gathered nothing, and its solve call is
    what answers — so the values-free answer hop above never runs on this path
    and would not have covered it. Reading tier2.py settles what its prompts
    actually carry: ``_summarize`` emits ``- <subquestion> -> <N> row(s)``, the
    evidence node's label is the model's own subquestion and ``rows`` is a
    count, and nothing interpolates ``result.records`` anywhere in the loop.
    That is already R8's counts-and-identities shape, so no capture rule was
    needed here — but "no rule was needed" is a claim about today's code, and
    this is what makes a future prompt that pasted evidence rows in fail loudly
    instead of quietly widening the trace.
    """
    good = "MATCH (j:ControlMJob) RETURN j.job_id AS job_id"
    bad = "MATCH (n) RETURN n AS n"

    def selective_read(cypher, params=None, database=None, row_cap=100, timeout_s=15.0):
        if "ControlMJob" not in cypher:
            raise RuntimeError("no such property")
        return FakeResult([{"job_id": SECRET_ROW_VALUE}])

    envelope, _, _ = _run(
        tmp_path,
        run_id="qa-tier2",
        replies=[
            '{"spec_id": null, "params": {}, "reason": "no registered spec covers this"}',
            json.dumps({"cypher": bad}),  # tier-1 attempt
            json.dumps({"cypher": bad}),  # fix 1
            json.dumps({"cypher": bad}),  # fix 2 -> tier 1 gives up
            json.dumps({"step": "enhance"}),
            json.dumps({"step": "enhance"}),
            json.dumps({"step": "enhance"}),
            json.dumps({"subquestion": "which jobs feed it?"}),
            json.dumps({"cypher": good}),  # the sub-question's retrieval succeeds
            json.dumps({"step": "solve"}),
            json.dumps({"step": "solve"}),
            json.dumps({"step": "solve"}),
            "4 jobs feed it.",  # tier2-solve
        ],
        run_read=selective_read,
    )
    assert envelope.tier == "tier2", "the test must actually reach the path it is about"

    records = _records(tmp_path)
    steps = {r.get("step") for r in records if r["hop"] == "llm"}
    assert "tier2-solve" in steps, "the solve prompt IS captured — the absence below is a finding"
    assert any(s and s.startswith("tier2-vote") for s in steps)

    solve = next(r for r in records if r.get("step") == "tier2-solve")
    assert "which jobs feed it?" in solve["user"], "the subquestion, which is the model's own text"
    assert "1 row(s)" in solve["user"], "and the evidence COUNT"
    assert SECRET_ROW_VALUE not in _raw(tmp_path)
