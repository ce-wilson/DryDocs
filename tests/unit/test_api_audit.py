"""G108 — the API audit record (kinds `api` + `api-debug`).

Two tiers of test, deliberately. The PURE tier exercises ApiAuditLog directly
so the acceptance's core claims — actor never equals the raw input, an error
mid-block still emits a record with the error class, the api line never
carries Cypher — hold with no framework installed. The WIRING tier
(importorskip fastapi, the test_fastapi_wiring_smoke idiom) sends one request
per audited route and asserts exactly one audit line lands.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from drydocs_api.audit import (
    AUDIT_KIND,
    CYPHER_TEXT_BOUND,
    DEBUG_KIND,
    ApiAuditLog,
    actor_hash,
    clean_run_id,
)

# ── helpers ──────────────────────────────────────────────────────────────────


def _lines(log_dir: Path, kind_id: str) -> list[dict]:
    out: list[dict] = []
    for path in sorted(log_dir.glob(f"{kind_id}.*.jsonl")):
        out += [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    return out


def _debug_kinds_file(tmp_path: Path) -> Path:
    """A declaration identical in shape to the repo's, with api-debug at DEBUG —
    the settings-level switch (ruling C): tests flip the DECLARATION, because
    there is nothing per-request to flip."""
    target = tmp_path / "log-kinds.yaml"
    target.write_text(
        "schema: drydocs.log-kinds.v1\n"
        "root: {base: home, path: logs/DryDocs/}\n"
        "defaults: {level: INFO, retention_days: 90, rotation: per-run, format: log}\n"
        "kinds:\n"
        "  - {id: api, writer: drydocs_api.audit.ApiAuditLog, rotation: per-day,\n"
        "     format: jsonl, note: test}\n"
        "  - {id: api-debug, writer: drydocs_api.audit.ApiAuditLog, level: DEBUG,\n"
        "     retention_days: 7, format: jsonl, note: test}\n",
        encoding="utf-8",
    )
    return target


# ── pure tier ────────────────────────────────────────────────────────────────


def test_actor_hash_is_the_agentrun_function():
    """Known-value pin: the SAME function :AgentRun's writer applies to caller
    identity (sha256 hexdigest of utf-8) — checked, not asserted."""
    assert actor_hash("token-123") == hashlib.sha256(b"token-123").hexdigest()
    assert len(actor_hash("x")) == 64


def test_actor_field_never_equals_the_raw_input(tmp_path):
    audit = ApiAuditLog(log_dir=tmp_path)
    with audit.observe("/raw-cypher", token="a-very-real-bearer-token") as rec:
        rec.rows = 0
    (line,) = _lines(tmp_path, AUDIT_KIND)
    assert line["actor_sha256"] != "a-very-real-bearer-token"
    assert "a-very-real-bearer-token" not in json.dumps(line)
    assert line["actor_sha256"] == actor_hash("a-very-real-bearer-token")


def test_an_error_mid_block_still_emits_a_record_with_the_error_class(tmp_path):
    audit = ApiAuditLog(log_dir=tmp_path)
    with pytest.raises(RuntimeError):
        with audit.observe("/query/{query_id}", token="t") as rec:
            rec.query_id = "overview-counts"
            raise RuntimeError("driver fell over mid-query")
    (line,) = _lines(tmp_path, AUDIT_KIND)
    assert line["outcome"] == "error"
    assert line["error_class"] == "RuntimeError"
    assert line["query_id"] == "overview-counts"
    assert line["rows"] is None
    assert isinstance(line["elapsed_ms"], int)


def test_the_api_line_never_carries_cypher_or_params(tmp_path):
    """The lean/verbose split is STRUCTURAL: the api line is built from an
    allowlist, so setting the debug-tier fields on the record cannot leak
    them into the 90-day record."""
    audit = ApiAuditLog(log_dir=tmp_path)
    with audit.observe("/raw-cypher", token="t") as rec:
        rec.cypher = "MATCH (secret:Node) RETURN secret"
        rec.params = {"p": "value"}
        rec.rows = 1
    (line,) = _lines(tmp_path, AUDIT_KIND)
    assert "cypher" not in line and "params" not in line
    assert "MATCH (secret" not in json.dumps(line)


def test_debug_tier_is_off_under_the_repo_declaration(tmp_path):
    """The repo declares api-debug at the INFO default — capture is OFF until
    an operator flips the declaration to level: DEBUG (ruling C)."""
    audit = ApiAuditLog(log_dir=tmp_path)
    assert audit.debug_enabled is False
    with audit.observe("/raw-cypher", token="t") as rec:
        rec.cypher = "MATCH (n) RETURN n"
    assert _lines(tmp_path, AUDIT_KIND)
    assert _lines(tmp_path, DEBUG_KIND) == []


def test_debug_tier_carries_bounded_cypher_when_the_declaration_says_debug(tmp_path):
    audit = ApiAuditLog(log_dir=tmp_path, kinds_path=_debug_kinds_file(tmp_path))
    assert audit.debug_enabled is True
    long_cypher = "MATCH (n) RETURN n // " + "x" * CYPHER_TEXT_BOUND
    with audit.observe("/raw-cypher", token="t") as rec:
        rec.cypher = long_cypher
        rec.params = {"limit": 5}
    (debug_line,) = _lines(tmp_path, DEBUG_KIND)
    assert debug_line["cypher"] == long_cypher[:CYPHER_TEXT_BOUND]
    assert debug_line["cypher_truncated"] is True
    assert debug_line["params"] == {"limit": 5}
    # and the lean line still landed, still clean
    (audit_line,) = _lines(tmp_path, AUDIT_KIND)
    assert "cypher" not in audit_line


def test_correlation_is_run_id_when_supplied_else_the_session_hash(tmp_path):
    """Ruling D: the field that joins this record to the qa ledger."""
    audit = ApiAuditLog(log_dir=tmp_path)
    with audit.observe("/specs/ephemeral", token="tok", run_id="qa-20260826-101500-abc123"):
        pass
    with audit.observe("/specs/{spec_id}/run", token="tok"):
        pass
    with_run, without = _lines(tmp_path, AUDIT_KIND)
    assert with_run["correlation_id"] == "qa-20260826-101500-abc123"
    assert with_run["correlation_source"] == "run_id"
    assert without["correlation_id"] == actor_hash("tok")
    assert without["correlation_source"] == "session"


def test_a_malformed_run_id_falls_back_rather_than_landing(tmp_path):
    """X-DryDocs-Run-Id is untrusted caller input bound for a 90-day record:
    over-long or non-printable values are dropped and the correlation falls
    back to the session hash."""
    assert clean_run_id("x" * 129) is None
    assert clean_run_id("bad\nid") is None
    assert clean_run_id("  ") is None
    assert clean_run_id("qa-ok-123") == "qa-ok-123"
    audit = ApiAuditLog(log_dir=tmp_path)
    with audit.observe("/raw-cypher", token="tok", run_id="x" * 500):
        pass
    (line,) = _lines(tmp_path, AUDIT_KIND)
    assert line["run_id"] is None
    assert line["correlation_source"] == "session"


def test_filenames_conform_to_the_derived_naming_rule(tmp_path):
    """api.access.<day>.jsonl / api-debug.access.<run-stamp>.jsonl — derived
    from the declaration via log_kinds, never formatted here."""
    audit = ApiAuditLog(log_dir=tmp_path, kinds_path=_debug_kinds_file(tmp_path))
    with audit.observe("/raw-cypher", token="t") as rec:
        rec.cypher = "RETURN 1"
    import re

    names = sorted(p.name for p in tmp_path.glob("*.jsonl"))
    assert len(names) == 2
    assert re.fullmatch(r"api-debug\.access\.\d{8}-\d{6}\.jsonl", names[0])
    assert re.fullmatch(r"api\.access\.\d{8}\.jsonl", names[1])


def test_a_broken_sink_never_breaks_the_request(tmp_path):
    target = tmp_path / "not-a-dir"
    target.write_text("a file where the log dir should be", encoding="utf-8")
    audit = ApiAuditLog(log_dir=target / "impossible")
    with audit.observe("/raw-cypher", token="t") as rec:  # must not raise
        rec.rows = 1


# ── wiring tier: one request per audited route ───────────────────────────────


class FakeRunner:
    def run(self, cypher, params, database):
        return ["n"], [{"n": 1}, {"n": 2}]

    def stream(self, cypher, params, database):
        return ["n"], iter([{"n": 1}])


class ExplodingRunner:
    def run(self, cypher, params, database):
        raise ConnectionError("neo4j went away mid-query")


AUDIT_TEST_SECRET = "a-test-console-secret"


@pytest.fixture()
def wired(tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from drydocs_api.app import create_app
    from drydocs_api.credentials import CredentialStore
    from drydocs_api.sessions import InMemorySessionStore

    # O73/O75/O76 at the merge: /login now proves a SECRET against a credential
    # store, so this fixture supplies one. Before that landed a bare persona_id
    # was enough, which is why the pre-merge form returned no token at all here.
    creds = CredentialStore()
    creds.set("morpheus", AUDIT_TEST_SECRET)  # admin
    creds.set("neo", AUDIT_TEST_SECRET)  # plain user, for the 403 case

    audit_dir = tmp_path / "audit"
    app = create_app(
        runner=FakeRunner(),
        store=InMemorySessionStore(),
        credentials=creds,
        audit=ApiAuditLog(log_dir=audit_dir),
    )
    client = TestClient(app)
    admin = client.post(
        "/login", json={"persona_id": "morpheus", "secret": AUDIT_TEST_SECRET}
    ).json()["token"]
    return client, admin, audit_dir


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_each_cypher_route_writes_exactly_one_audit_record(wired, monkeypatch):
    client, admin, audit_dir = wired
    monkeypatch.setenv("DRYDOCS_AGENT_REG_KEY", "reg-key")

    assert (
        client.post("/query/overview-counts", json={"params": {}}, headers=_auth(admin)).status_code
        == 200
    )
    assert (
        client.post(
            "/raw-cypher", json={"cypher": "MATCH (n) RETURN n"}, headers=_auth(admin)
        ).status_code
        == 200
    )
    registered = client.post(
        "/specs/ephemeral",
        json={
            "owner_token": admin,
            "cypher": "MATCH (n) RETURN n AS n",
            "database": "drydocs",
            "columns": ["n"],
        },
        headers={
            "X-DryDocs-Agent-Key": "reg-key",
            "X-DryDocs-Run-Id": "qa-20260826-000000-abcdef",
        },
    )
    assert registered.status_code == 200
    ref = registered.json()["explore_ref"]
    assert (
        client.post(f"/specs/{ref}/run", json={"params": {}}, headers=_auth(admin)).status_code
        == 200
    )
    assert (
        client.post(f"/specs/{ref}/export", json={"params": {}}, headers=_auth(admin)).status_code
        == 200
    )

    lines = _lines(audit_dir, AUDIT_KIND)
    by_route = {line["route"]: line for line in lines}
    assert (
        len(lines) == 5
    ), f"expected one line per request, got {[line['route'] for line in lines]}"
    assert set(by_route) == {
        "/query/{query_id}",
        "/raw-cypher",
        "/specs/ephemeral",
        "/specs/{spec_id}/run",
        "/specs/{spec_id}/export",
    }
    assert by_route["/query/{query_id}"]["query_id"] == "overview-counts"
    assert by_route["/query/{query_id}"]["rows"] == 2
    assert by_route["/raw-cypher"]["rows"] == 2
    # the run_id arrived on the registration and became its correlation id
    assert by_route["/specs/ephemeral"]["correlation_id"] == "qa-20260826-000000-abcdef"
    assert by_route["/specs/ephemeral"]["spec_id"] == ref
    assert by_route["/specs/{spec_id}/run"]["spec_id"] == ref
    # a stream's row count is the export MANIFEST's fact — the audit line is
    # the access record, rows deliberately null
    assert by_route["/specs/{spec_id}/export"]["rows"] is None
    assert by_route["/specs/{spec_id}/export"]["detail"]["export_id"]
    # every actor is hashed
    assert all(line["actor_sha256"] != admin for line in lines)
    assert all(line["outcome"] == "ok" for line in lines)


def test_a_route_raising_mid_query_still_emits_the_record(tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from drydocs_api.app import create_app
    from drydocs_api.credentials import CredentialStore
    from drydocs_api.sessions import InMemorySessionStore

    creds = CredentialStore()
    creds.set("morpheus", AUDIT_TEST_SECRET)

    audit_dir = tmp_path / "audit"
    app = create_app(
        runner=ExplodingRunner(),
        store=InMemorySessionStore(),
        credentials=creds,
        audit=ApiAuditLog(log_dir=audit_dir),
    )
    client = TestClient(app, raise_server_exceptions=False)
    admin = client.post(
        "/login", json={"persona_id": "morpheus", "secret": AUDIT_TEST_SECRET}
    ).json()["token"]
    response = client.post(
        "/raw-cypher", json={"cypher": "MATCH (n) RETURN n"}, headers=_auth(admin)
    )
    assert response.status_code == 500
    (line,) = _lines(audit_dir, AUDIT_KIND)
    assert line["route"] == "/raw-cypher"
    assert line["outcome"] == "error"
    assert line["error_class"] == "ConnectionError"


def test_a_forbidden_outcome_records_the_original_class_not_the_mapped_one(wired):
    client, _admin, audit_dir = wired
    viewer = client.post("/login", json={"persona_id": "neo", "secret": AUDIT_TEST_SECRET}).json()[
        "token"
    ]
    response = client.post(
        "/raw-cypher", json={"cypher": "MATCH (n) RETURN n"}, headers=_auth(viewer)
    )
    assert response.status_code == 403
    (line,) = _lines(audit_dir, AUDIT_KIND)
    assert line["error_class"] == "Forbidden"  # never the mapped HTTPException


def test_write_routes_are_audited_and_reads_are_not(wired):
    client, admin, audit_dir = wired
    created = client.post(
        "/intake",
        json={"context_type": "other", "area": {}, "note": "audit-test"},
        headers=_auth(admin),
    )
    assert created.status_code == 200
    # reads: none of these may add a line
    assert client.get("/health").status_code == 200
    assert client.get("/queries").status_code == 200
    assert client.get("/specs").status_code == 200
    assert client.get("/intake", headers=_auth(admin)).status_code == 200

    lines = _lines(audit_dir, AUDIT_KIND)
    assert [line["route"] for line in lines] == ["/intake"]
    assert lines[0]["outcome"] == "ok"
