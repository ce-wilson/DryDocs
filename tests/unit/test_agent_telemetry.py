"""R3 — agent run telemetry, offline (fakes; no litellm, no driver, no ADK).

What this suite proves, per R3's acceptance:

- every LLM call appends one JSONL line (run_id, step, model, prompt/
  completion tokens, cost_est, duration_ms, iteration) to DRYDOCS_LOGDIR —
  never the repo — and the run-summary line is the ONLY sink carrying the
  full question text;
- the ledger owns the model -> price map: known Anthropic ids price out,
  unknown models yield None (never a guessed number);
- the :AgentRun props mirror :JobRun (kind 'qa') and carry question sha256 +
  length ONLY, plus tier / iterations / llm_calls / token totals / context
  and memory sizes / cypher count / fix retries / specs used / dbs touched /
  timings / staleness flags / the reserved hashed caller-identity slot;
- the dedicated writer refuses 'drydocs' no matter how it is asked (env or
  explicit argument) — the R1 ruling is code, not prose;
- console.agent-runs.v1 exists in the registry on ddcontext (watermarked),
  read-only-validated at import like every spec.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
for entry in (str(REPO_ROOT / "agents"), str(REPO_ROOT)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common import agent_run_writer  # noqa: E402
from common.llm_ledger import LlmLedger, estimate_cost_usd  # noqa: E402
from graph_qa import pipeline as pl  # noqa: E402

from drydocs_api.query_specs import QUERY_SPECS, is_watermarked  # noqa: E402

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
    def __init__(self):
        self.records = [{"n": 1}]
        self.keys = ["n"]
        self.row_count = 1
        self.truncated = False
        self.ms = 3


def _ok_read(cypher, params=None, database=None, row_cap=100, timeout_s=15.0):
    return FakeResult()


def _answer(tmp_path, user_id=""):
    """Run one Tier-0 question through the pipeline with a tmp-dir ledger."""
    provider = FakeProvider(
        [
            f'{{"spec_id": "{SPEC_ID}", "params": {{}}}}',
            "There is 1 application.",
        ]
    )
    pipeline = pl.GraphQaPipeline(
        provider=provider,
        run_read=_ok_read,
        graph_schema=lambda: LIVE_SCHEMA,
        vocabulary_loader=lambda: VOCAB,
        ledger=LlmLedger(log_dir=tmp_path),
    )
    return pipeline.answer("how many applications?", run_id="qa-test-r3", user_id=user_id)


# ── price map ────────────────────────────────────────────────────────────────


def test_price_map_prices_known_models_and_declines_unknown():
    # 100k prompt + 10k completion on sonnet-4-5: 0.1*3.00 + 0.01*15.00 = 0.45
    assert estimate_cost_usd("claude-sonnet-4-5-20250929", 100_000, 10_000) == 0.45
    assert estimate_cost_usd("anthropic/claude-haiku-4-5", 1_000_000, 0) == 1.0
    assert estimate_cost_usd("gpt-4o-azure-deployment", 1000, 1000) is None  # honest unknown
    assert estimate_cost_usd(None, 1000, 1000) is None


# ── JSONL ledger ─────────────────────────────────────────────────────────────


def test_every_llm_call_appends_one_jsonl_line(tmp_path):
    envelope = _answer(tmp_path)
    ledger_files = list(tmp_path.glob("qa.graph_qa.*.jsonl"))
    assert len(ledger_files) == 1  # in the log dir, never the repo
    lines = [json.loads(l) for l in ledger_files[0].read_text(encoding="utf-8").splitlines()]
    calls = [l for l in lines if l["kind"] == "llm_call"]
    assert len(calls) == envelope.metrics.llm_calls == 2  # router + answer
    assert [c["step"] for c in calls] == ["router", "answer"]
    for call in calls:
        for field in (
            "run_id",
            "step",
            "model",
            "prompt_tokens",
            "completion_tokens",
            "cost_est_usd",
            "duration_ms",
            "iteration",
        ):
            assert field in call, f"ledger line missing {field}"
        assert call["run_id"] == "qa-test-r3"
        assert call["cost_est_usd"] is not None  # sonnet-4-5 is in the price map
    # the envelope's cost is the sum the ledger priced
    assert envelope.metrics.cost_est_usd == pytest.approx(sum(c["cost_est_usd"] for c in calls))


def test_run_line_is_the_only_home_of_the_question_text(tmp_path):
    envelope = _answer(tmp_path)
    ledger = LlmLedger(log_dir=tmp_path)
    ledger.run(envelope, "how many applications?")
    lines = [json.loads(l) for l in ledger.path().read_text(encoding="utf-8").splitlines()]
    runs = [l for l in lines if l["kind"] == "run"]
    assert len(runs) == 1
    run = runs[0]
    assert run["question"] == "how many applications?"  # full text: ledger only
    assert run["question_sha256"] == envelope.question_sha256
    assert run["tier"] == "spec" and run["llm_calls"] == 2
    # graph props NEVER carry the text (checked against the writer below too)
    props = agent_run_writer.agent_run_props(envelope)
    assert "how many applications?" not in json.dumps(props)


def test_no_ledger_means_no_cost_and_no_failure(tmp_path):
    provider = FakeProvider(
        [
            f'{{"spec_id": "{SPEC_ID}", "params": {{}}}}',
            "There is 1 application.",
        ]
    )
    pipeline = pl.GraphQaPipeline(
        provider=provider,
        run_read=_ok_read,
        graph_schema=lambda: LIVE_SCHEMA,
        vocabulary_loader=lambda: VOCAB,
    )
    envelope = pipeline.answer("how many applications?", run_id="qa-test-r3b")
    assert envelope.metrics.cost_est_usd is None
    assert list(tmp_path.glob("*.jsonl")) == []


# ── :AgentRun props + writer boundary ────────────────────────────────────────


def test_agent_run_props_mirror_the_acceptance_fields(tmp_path):
    envelope = _answer(tmp_path, user_id="jdoe4821")
    props = agent_run_writer.agent_run_props(envelope, user_id="jdoe4821")
    assert props["kind"] == "qa" and props["run_id"] == "qa-test-r3"
    assert props["question_sha256"] == envelope.question_sha256
    assert props["question_chars"] == len("how many applications?")
    assert props["tier"] == "spec"
    assert props["iterations"] == 1 and props["llm_calls"] == 2
    assert props["tokens_total"] == props["tokens_prompt"] + props["tokens_completion"]
    assert props["context_rows"] == 1 and props["memory_events"] == 0
    assert props["cypher_count"] == 1 and props["fix_retries"] == 0
    assert props["specs_used"] == [SPEC_ID]
    assert props["dbs_touched"] == ["drydocs"]
    assert props["response_ms_total"] >= 0 and "response_ms_llm" in props
    assert props["stale_sources"] == 0  # staleness flags: honest zero until R7
    assert props["cost_est_usd"] is not None
    # reserved caller-identity slot: hash + length ONLY
    expected = hashlib.sha256(b"jdoe4821").hexdigest()
    assert props["user_id_sha256"] == expected
    assert props["user_id_chars"] == 8
    assert "jdoe4821" not in json.dumps({k: v for k, v in props.items() if k != "user_id_chars"})


def test_writer_refuses_drydocs_from_env_and_argument(tmp_path, monkeypatch):
    monkeypatch.setenv(agent_run_writer.AGENT_RUN_DB_ENV, "drydocs")
    with pytest.raises(ValueError, match="never lands in 'drydocs'"):
        agent_run_writer.agent_run_db()
    monkeypatch.delenv(agent_run_writer.AGENT_RUN_DB_ENV)
    assert agent_run_writer.agent_run_db() == "ddcontext"  # the R1 ruling default
    envelope = _answer(tmp_path)
    with pytest.raises(ValueError, match="never lands in 'drydocs'"):
        agent_run_writer.write_agent_run(envelope, database="drydocs")


# ── console.agent-runs.v1 ────────────────────────────────────────────────────


def test_agent_runs_spec_registered_on_ddcontext():
    spec = QUERY_SPECS["console.agent-runs.v1"]
    assert spec.database == "ddcontext"  # the R1 ruling's DB, never drydocs
    assert is_watermarked(spec)  # ddcontext reads carry the standard watermark
    assert "question_sha256" in spec.cypher and "question_chars" in spec.cypher
    assert "r.kind = 'qa'" in spec.cypher and "NOT r:SchemaMeta" in spec.cypher
    # registry-wide read-only/classification validation already ran at import;
    # reaching this line with the spec present is the assertion that it passed.
