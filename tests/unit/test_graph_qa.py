"""R2 — graph_qa pipeline control flow, with fakes (no litellm, no driver, no ADK).

The agents service is a separate venv, but its pipeline modules are
deliberately import-clean for this env: ``agents/`` goes on sys.path and the
pure modules (envelope, schema_context, pipeline, providers.extract_usage,
common.specs_catalog) load without agents-only dependencies. What this suite
proves, per R2's acceptance:

- Tier 0 routes onto a registered spec and shows the spec Cypher VERBATIM;
- Tier-1 prompts are assembled from vocabulary + live schema + few-shot spec
  examples — bounded, never whole-graph state;
- the fix loop caps at 2 (three executions total) and write-shaped Cypher is
  stopped by the pre-flight without reaching the executor;
- the envelope carries the documented contract fields;
- the usage extractor normalizes anthropic / azure-openai / gemini shapes;
- the agent consumes the QuerySpec registry (catalog covers every spec).

The server-side READ-mode boundary is intentionally NOT provable with fakes:
tests/integration/test_graph_qa_read_mode.py does it against a live graph.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
for entry in (str(REPO_ROOT / "agents"), str(REPO_ROOT)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common import specs_catalog  # noqa: E402
from graph_qa import pipeline as pl  # noqa: E402
from graph_qa.envelope import Envelope  # noqa: E402
from graph_qa.providers import LlmReply, LlmUsage, extract_usage  # noqa: E402
from graph_qa.schema_context import MAX_PROMPT_CHARS, build_schema_prompt  # noqa: E402

SPEC_ID = "explorer.applications.v1"
SPEC = specs_catalog.QUERY_SPECS[SPEC_ID]

VOCAB = [
    {
        "neo4j_label": "WAS_INFORMED_BY", "from_node": "ControlMJob",
        "to_node": "ControlMJob", "role": None, "note": "job dependency",
        "status": "active",
    }
]
LIVE_SCHEMA = {
    "labels": ["ControlMJob", "BusinessApplication"],
    "relationshipTypes": ["WAS_INFORMED_BY"],
    "propertyKeys": ["job_name", "seal_id"],
}


@dataclass
class FakeProvider:
    """Scripted replies; records every (system, user) prompt it was given."""

    replies: list[str]
    provider: str = "anthropic"
    calls: list[tuple[str, str]] = field(default_factory=list)

    def complete(self, system: str, user: str, max_tokens: int = 1200) -> LlmReply:
        self.calls.append((system, user))
        text = self.replies[min(len(self.calls) - 1, len(self.replies) - 1)]
        return LlmReply(text=text, usage=LlmUsage(100, 20), model="fake-model", ms=5)


@dataclass
class FakeResult:
    records: list
    keys: list
    row_count: int
    truncated: bool = False
    ms: int = 3


def _pipeline(provider, run_read):
    return pl.GraphQaPipeline(
        provider=provider,
        run_read=run_read,
        graph_schema=lambda: LIVE_SCHEMA,
        vocabulary_loader=lambda: VOCAB,
    )


def _ok_read(cypher, params=None, database=None, row_cap=100, timeout_s=15.0):
    return FakeResult(records=[{"n": 1}], keys=["n"], row_count=1)


def test_tier0_spec_cypher_verbatim() -> None:
    provider = FakeProvider(replies=[
        '{"spec_id": "%s", "params": {}}' % SPEC_ID,  # router
        "There is 1 application.",                     # answer
    ])
    executed: list[tuple] = []

    def run_read(cypher, params=None, database=None, row_cap=100, timeout_s=15.0):
        executed.append((cypher, database))
        return _ok_read(cypher)

    env = _pipeline(provider, run_read).answer("how many applications?", run_id="qa-test-1")
    assert env.tier == "spec"
    spec_steps = [s for s in env.steps if s.kind == "spec"]
    assert spec_steps and spec_steps[0].cypher == SPEC.cypher  # verbatim, not paraphrased
    assert executed[0] == (SPEC.cypher, SPEC.database)
    assert env.answer == "There is 1 application."


def test_executed_cypher_registers_an_explore_ref() -> None:
    """R4: every EXECUTED step carries the ephemeral-spec ref the registrar
    returned; a registration failure degrades to None, never kills the answer."""
    registered: list[dict] = []

    def register(cypher, database, params):
        registered.append({"cypher": cypher, "database": database, "params": params})
        return "eph.abc123def4567890"

    provider = FakeProvider(replies=[
        '{"spec_id": "%s", "params": {}}' % SPEC_ID,
        "There is 1 application.",
    ])
    pipeline = _pipeline(provider, _ok_read)
    pipeline.register_cypher = register
    env = pipeline.answer("how many applications?", run_id="qa-test-r4")
    spec_step = [s for s in env.steps if s.kind == "spec"][0]
    assert spec_step.explore_ref == "eph.abc123def4567890"
    assert registered[0]["cypher"] == SPEC.cypher and registered[0]["database"] == SPEC.database

    def broken_register(cypher, database, params):
        raise OSError("api down")

    provider2 = FakeProvider(replies=[
        '{"spec_id": "%s", "params": {}}' % SPEC_ID,
        "There is 1 application.",
    ])
    pipeline2 = _pipeline(provider2, _ok_read)
    pipeline2.register_cypher = broken_register
    env2 = pipeline2.answer("how many applications?", run_id="qa-test-r4b")
    assert env2.answer == "There is 1 application."  # registration failure is non-fatal
    assert [s for s in env2.steps if s.kind == "spec"][0].explore_ref is None


def test_steps_stream_to_the_observer_in_order() -> None:
    """R5: on_step fires per StepRecord as it lands (the Ask spoke's live
    stream); an observer that throws never affects the answer."""
    provider = FakeProvider(replies=[
        '{"spec_id": "%s", "params": {}}' % SPEC_ID,
        "There is 1 application.",
    ])
    seen: list[str] = []
    pipeline = pl.GraphQaPipeline(
        provider=provider, run_read=_ok_read,
        graph_schema=lambda: LIVE_SCHEMA, vocabulary_loader=lambda: VOCAB,
        on_step=lambda step: seen.append(step.kind),
    )
    env = pipeline.answer("how many applications?", run_id="qa-test-r5")
    assert seen == [s.kind for s in env.steps] == ["router", "spec", "answer"]

    provider2 = FakeProvider(replies=[
        '{"spec_id": "%s", "params": {}}' % SPEC_ID,
        "There is 1 application.",
    ])
    pipeline2 = pl.GraphQaPipeline(
        provider=provider2, run_read=_ok_read,
        graph_schema=lambda: LIVE_SCHEMA, vocabulary_loader=lambda: VOCAB,
        on_step=lambda step: (_ for _ in ()).throw(RuntimeError("observer down")),
    )
    env2 = pipeline2.answer("how many applications?", run_id="qa-test-r5b")
    assert env2.answer == "There is 1 application."  # observer failure is non-fatal


def test_control_part_parsing() -> None:
    """R5: part 0 is the question; a drydocs_control JSON part contributes the
    R4 owner-token handshake; malformed control degrades to none."""
    from graph_qa.control import split_question_and_control

    q, c = split_question_and_control([
        "how many jobs?",
        '{"drydocs_control": {"api_token": "tok-1", "api_url": "http://localhost:8001"}}',
    ])
    assert q == "how many jobs?"
    assert c == {"api_token": "tok-1", "api_url": "http://localhost:8001"}

    q2, c2 = split_question_and_control(["just a question"])
    assert q2 == "just a question" and c2 == {}
    q3, c3 = split_question_and_control(["q", "not json", '{"other": 1}'])
    assert q3 == "q" and c3 == {}
    assert split_question_and_control([]) == ("", {})


def test_tier1_prompt_is_grounded_and_bounded() -> None:
    provider = FakeProvider(replies=[
        '{"spec_id": null, "params": {}}',
        '{"cypher": "MATCH (j:ControlMJob) RETURN count(j) AS jobs"}',
        "42 jobs.",
    ])
    env = _pipeline(provider, _ok_read).answer("count the jobs", run_id="qa-test-2")
    assert env.tier == "text2cypher"
    schema_prompt = provider.calls[1][0]  # system prompt of the text2cypher call
    assert "WAS_INFORMED_BY" in schema_prompt          # vocabulary row
    assert "BusinessApplication" in schema_prompt      # live schema
    assert SPEC_ID in schema_prompt                    # few-shot spec example
    assert len(schema_prompt) <= MAX_PROMPT_CHARS      # bounded — never whole-graph state


def test_fix_loop_caps_at_two() -> None:
    from common.graph_read import CypherReadError

    provider = FakeProvider(replies=[
        '{"spec_id": null, "params": {}}',
        '{"cypher": "MATCH (x) RETURN broken"}',
        '{"cypher": "MATCH (x) RETURN broken2"}',
        '{"cypher": "MATCH (x) RETURN broken3"}',
    ])
    attempts: list[str] = []

    def failing_read(cypher, params=None, database=None, row_cap=100, timeout_s=15.0):
        attempts.append(cypher)
        raise CypherReadError("Invalid input 'broken'")

    env = _pipeline(provider, failing_read).answer("bad question", run_id="qa-test-3")
    assert env.tier == "unanswered"
    assert len(attempts) == 1 + pl.MAX_FIX_RETRIES  # initial + 2 fixes, then stop
    t2c = [s for s in env.steps if s.kind == "text2cypher"]
    assert [s.fix_retries for s in t2c] == [0, 1, 2]
    assert all(s.error for s in t2c)
    assert env.answer  # honest failure message, not empty


def test_write_shaped_cypher_never_reaches_executor() -> None:
    provider = FakeProvider(replies=[
        '{"spec_id": null, "params": {}}',
        '{"cypher": "CREATE (x:Evil) RETURN x"}',
        '{"cypher": "MATCH (x) RETURN x LIMIT 1"}',
        "ok",
    ])
    executed: list[str] = []

    def run_read(cypher, params=None, database=None, row_cap=100, timeout_s=15.0):
        executed.append(cypher)
        return _ok_read(cypher)

    env = _pipeline(provider, run_read).answer("sneaky", run_id="qa-test-4")
    assert all("CREATE" not in c for c in executed)  # pre-flight stopped it
    write_step = [s for s in env.steps if s.kind == "text2cypher"][0]
    assert "write clause" in (write_step.error or "")
    assert env.tier == "text2cypher"  # fix loop recovered with a read query


def test_envelope_contract_fields() -> None:
    provider = FakeProvider(replies=[
        '{"spec_id": "%s", "params": {}}' % SPEC_ID,
        "answer text",
    ])
    env = _pipeline(provider, _ok_read).answer(
        "q", run_id="qa-test-5", session_id="s1", memory_events=4, memory_chars=400
    )
    d = env.to_dict()
    for key in (
        "run_id", "session_id", "tier", "question_sha256", "question_chars",
        "answer", "model", "provider", "steps", "sources", "metrics",
    ):
        assert key in d, f"envelope missing {key}"
    for key in ("iterations", "llm_calls", "tokens", "context", "memory",
                "cost_est_usd", "response_ms"):
        assert key in d["metrics"], f"metrics missing {key}"
    assert d["metrics"]["memory"] == {"events": 4, "tokens_est": 100}
    assert d["metrics"]["tokens"]["total"] == d["metrics"]["tokens"]["prompt"] + d[
        "metrics"]["tokens"]["completion"]
    assert d["question_sha256"] != "q"  # hashed, never raw
    step_keys = set(d["steps"][0])
    assert {"i", "kind", "ms", "cypher", "database", "rows", "fix_retries",
            "error", "explore_ref"} <= step_keys


def test_usage_extractor_normalizes_provider_shapes() -> None:
    assert extract_usage({"prompt_tokens": 10, "completion_tokens": 2}).total_tokens == 12
    assert extract_usage({"input_tokens": 7, "output_tokens": 3}).prompt_tokens == 7
    gemini = extract_usage({"prompt_token_count": 5, "candidates_token_count": 4})
    assert (gemini.prompt_tokens, gemini.completion_tokens) == (5, 4)
    assert extract_usage(None).total_tokens == 0


def test_catalog_covers_every_spec_and_defines_no_cypher() -> None:
    lines = specs_catalog.catalog_lines()
    assert len(lines) == len(specs_catalog.QUERY_SPECS)
    for spec_id in specs_catalog.QUERY_SPECS:
        assert any(spec_id in line for line in lines)
    # the agent's only Cypher source is the registry: resolve round-trips
    assert specs_catalog.get_spec(SPEC_ID) is SPEC
    assert specs_catalog.resolve_params(SPEC, None) == {"limit": 500}
    with pytest.raises(ValueError):
        specs_catalog.resolve_params(SPEC, {"nope": 1})


def test_schema_prompt_truncates_at_cap() -> None:
    rows = [
        {"neo4j_label": f"REL_{i}", "from_node": "A", "to_node": "B",
         "note": "x" * 200, "status": "active"}
        for i in range(500)
    ]
    prompt = build_schema_prompt(rows, LIVE_SCHEMA, [("s.v1", "d", "MATCH (n) RETURN n")])
    assert len(prompt) <= MAX_PROMPT_CHARS


def test_tier0_zero_rows_falls_through_to_tier1() -> None:
    """A routed spec returning 0 rows is insufficient context — Tier 1 must engage."""
    provider = FakeProvider(replies=[
        '{"spec_id": "%s", "params": {}}' % SPEC_ID,                       # router
        '{"cypher": "MATCH (f:ControlMFolder) RETURN count(f) AS n"}',     # text2cypher
        "5 folders.",                                                       # answer
    ])
    calls: list[str] = []

    def run_read(cypher, params=None, database=None, row_cap=100, timeout_s=15.0):
        calls.append(cypher)
        if cypher == SPEC.cypher:  # the spec run comes back empty
            return FakeResult(records=[], keys=[], row_count=0)
        return FakeResult(records=[{"n": 5}], keys=["n"], row_count=1)

    env = _pipeline(provider, run_read).answer("count folders", run_id="qa-test-6")
    assert env.tier == "text2cypher"                       # what actually answered
    kinds = [s.kind for s in env.steps]
    assert "spec" in kinds and "text2cypher" in kinds      # both attempts recorded
    assert [s for s in env.steps if s.kind == "spec"][0].rows == 0
    assert env.metrics.context["rows"] == 1
    assert env.answer == "5 folders."


def test_schema_prompt_renders_per_label_properties() -> None:
    schema = dict(LIVE_SCHEMA)
    schema["propertiesByLabel"] = {"ControlMFolder": ["folder_id", "sched_table"]}
    prompt = build_schema_prompt(VOCAB, schema, [("s.v1", "d", "MATCH (n) RETURN n")])
    assert "ControlMFolder: folder_id, sched_table" in prompt
    assert "Properties by label" in prompt


def test_schema_prompt_sections_survive_oversized_vocabulary() -> None:
    """Regression (live, 2026-07-23): whole-prompt tail truncation dropped the live
    schema, per-label properties, and ALL examples once the vocabulary outgrew the
    cap. Per-section budgets must keep every section present."""
    huge_vocab = [
        {"neo4j_label": f"REL_{i}", "from_node": "A", "to_node": "B",
         "note": "x" * 300, "status": "active"}
        for i in range(500)
    ]
    schema = dict(LIVE_SCHEMA)
    schema["propertiesByLabel"] = {"ControlMFolder": ["folder_id", "sched_table"]}
    prompt = build_schema_prompt(
        huge_vocab, schema, [("spec.a.v1", "desc", "MATCH (n) RETURN n LIMIT 1")]
    )
    assert len(prompt) <= MAX_PROMPT_CHARS
    assert "Properties by label" in prompt
    assert "sched_table" in prompt
    assert "Example queries" in prompt and "spec.a.v1" in prompt
