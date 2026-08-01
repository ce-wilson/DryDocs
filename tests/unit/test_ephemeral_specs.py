"""R4 — ephemeral session-scoped QuerySpecs, offline (fakes, no driver).

What this suite proves, per R4's acceptance:

- registration is hash-addressed (same execution → same ref) and validates
  read-only + reviewed-database at the door;
- ``/specs/{ref}/run|export`` resolve ONLY for the owning session; foreign,
  expired, and unknown refs are indistinguishable (UnknownSpecError → 404);
- refs are TTL-bounded (fake clock) and the store is capacity-bounded;
- params are frozen at registration — supplying params at run time fails
  closed exactly like an undeclared param on a permanent spec;
- the export manifest carries cypher_sha256 + provenance through the SAME
  code path as permanent specs, with the fail-closed internal-confidential
  classification (banner + filename prefix);
- registration is a trusted-caller surface: no agent key (or no configured
  key) is Forbidden — a browser bearer token alone can never register
  Cypher, so the admin-only /raw-cypher gate (ADR 0005) stays the only
  interactive Cypher surface, byte-for-byte unchanged.
"""

from __future__ import annotations

import hashlib

import pytest

from drydocs_api.ephemeral_specs import (
    EPHEMERAL_CLASSIFICATION,
    EphemeralSpecStore,
    EphemeralValidationError,
    is_ephemeral_ref,
    register_ephemeral,
)
from drydocs_api.exports import ExportLedger, export_spec, filename_for, run_spec
from drydocs_api.guard import WriteRejected
from drydocs_api.handlers import Forbidden, run_raw
from drydocs_api.queries import ParamValidationError
from drydocs_api.query_specs import UnknownSpecError
from drydocs_api.sessions import InMemorySessionStore, InvalidTokenError

CYPHER = "MATCH (j:ControlMJob) RETURN j.job_name AS job_name LIMIT 5"


class FakeRunner:
    def __init__(self, keys=None, rows=None):
        self.calls: list[tuple[str, dict, str]] = []
        self._keys = keys or ["job_name"]
        self._rows = rows or [{"job_name": "J1"}]

    def run(self, cypher, params, database):
        self.calls.append((cypher, dict(params), database))
        return self._keys, self._rows


class FakeClock:
    def __init__(self, now: float = 1000.0):
        self.now = now

    def __call__(self) -> float:
        return self.now


def _session(store: InMemorySessionStore) -> str:
    return store.issue("jdoe4821").token


# ── store: hashing, ownership, TTL, capacity ─────────────────────────────────


def test_ref_is_hash_addressed_and_idempotent():
    ephemerals = EphemeralSpecStore()
    a = ephemerals.register("tok", CYPHER, "drydocs", params={"limit": 5})
    b = ephemerals.register("tok", CYPHER, "drydocs", params={"limit": 5})
    c = ephemerals.register("tok", CYPHER, "drydocs", params={"limit": 6})
    assert a.ref == b.ref and is_ephemeral_ref(a.ref)
    assert c.ref != a.ref  # params are part of the address
    assert ephemerals.register("tok", CYPHER, "ddcontext").ref != a.ref  # so is the db


def test_resolve_is_owner_scoped():
    ephemerals = EphemeralSpecStore()
    spec = ephemerals.register("owner-token", CYPHER, "drydocs")
    assert ephemerals.resolve("owner-token", spec.ref).cypher == CYPHER
    with pytest.raises(UnknownSpecError):  # foreign session: same 404 as unknown
        ephemerals.resolve("other-token", spec.ref)
    with pytest.raises(UnknownSpecError):
        ephemerals.resolve("owner-token", "eph.0000000000000000")


def test_ttl_expiry():
    clock = FakeClock()
    ephemerals = EphemeralSpecStore(ttl_seconds=60, clock=clock)
    spec = ephemerals.register("tok", CYPHER, "drydocs")
    clock.now += 59
    assert ephemerals.resolve("tok", spec.ref).ref == spec.ref
    clock.now += 2
    with pytest.raises(UnknownSpecError):
        ephemerals.resolve("tok", spec.ref)
    # re-registering the same execution mints the SAME ref with a fresh TTL
    again = ephemerals.register("tok", CYPHER, "drydocs")
    assert again.ref == spec.ref and again.expires_at > spec.expires_at


def test_capacity_evicts_oldest():
    ephemerals = EphemeralSpecStore(capacity=2)
    first = ephemerals.register("tok", CYPHER, "drydocs")
    ephemerals.register("tok", CYPHER + " UNION MATCH (n) RETURN n.x AS job_name", "drydocs")
    ephemerals.register("tok", "MATCH (n) RETURN count(n) AS c", "drydocs")
    with pytest.raises(UnknownSpecError):
        ephemerals.resolve("tok", first.ref)


def test_registration_validates_at_the_door():
    ephemerals = EphemeralSpecStore()
    with pytest.raises(WriteRejected):
        ephemerals.register("tok", "CREATE (n:Evil)", "drydocs")
    with pytest.raises(EphemeralValidationError):
        ephemerals.register("tok", CYPHER, "neo4j")  # not in the reviewed set
    with pytest.raises(EphemeralValidationError):
        ephemerals.register("tok", "   ", "drydocs")


# ── the pure registration handler (trusted-caller gate) ──────────────────────


def test_register_handler_requires_the_agent_key():
    sessions, ephemerals = InMemorySessionStore(), EphemeralSpecStore()
    token = _session(sessions)
    args = (token, CYPHER, "drydocs", {}, "", (), sessions, ephemerals)
    with pytest.raises(Forbidden):  # no key configured server-side: disabled
        register_ephemeral("some-key", None, *args)
    with pytest.raises(Forbidden):  # no key presented
        register_ephemeral(None, "server-key", *args)
    with pytest.raises(Forbidden):  # wrong key
        register_ephemeral("wrong", "server-key", *args)
    with pytest.raises(InvalidTokenError):  # owner session must be live
        register_ephemeral(
            "server-key",
            "server-key",
            "dead-token",
            CYPHER,
            "drydocs",
            {},
            "",
            (),
            sessions,
            ephemerals,
        )


def test_register_handler_payload():
    sessions, ephemerals = InMemorySessionStore(), EphemeralSpecStore()
    token = _session(sessions)
    out = register_ephemeral(
        "k",
        "k",
        token,
        CYPHER,
        "ddcontext",
        {"limit": 5},
        "agent query",
        ["job_name"],
        sessions,
        ephemerals,
    )
    assert is_ephemeral_ref(out["explore_ref"])
    assert out["classification"] == EPHEMERAL_CLASSIFICATION  # fail-closed ceiling
    assert out["watermarked"] is True  # ddcontext stays watermarked
    assert out["expires_at"].endswith("+00:00")


# ── run/export through the existing /specs paths ─────────────────────────────


def test_run_spec_replays_the_frozen_execution():
    sessions, ephemerals, runner = InMemorySessionStore(), EphemeralSpecStore(), FakeRunner()
    token = _session(sessions)
    ref = ephemerals.register(token, CYPHER, "drydocs", params={"limit": 5}).ref
    out = run_spec(ref, {}, token, sessions, runner, ephemerals)
    assert out["spec_id"] == ref and out["ephemeral"] is True
    assert out["classification"] == EPHEMERAL_CLASSIFICATION
    cypher, params, database = runner.calls[0]
    assert (cypher, params, database) == (CYPHER, {"limit": 5}, "drydocs")


def test_run_spec_params_fail_closed_and_ownership_holds():
    sessions, ephemerals, runner = InMemorySessionStore(), EphemeralSpecStore(), FakeRunner()
    token = _session(sessions)
    ref = ephemerals.register(token, CYPHER, "drydocs").ref
    with pytest.raises(ParamValidationError):  # frozen params: none accepted
        run_spec(ref, {"limit": 10}, token, sessions, runner, ephemerals)
    other = _session(sessions)
    with pytest.raises(UnknownSpecError):  # another session: plain 404
        run_spec(ref, {}, other, sessions, runner, ephemerals)
    with pytest.raises(UnknownSpecError):  # no store wired: eph refs don't exist
        run_spec(ref, {}, token, sessions, runner, None)
    assert runner.calls == []


def test_permanent_specs_are_unchanged_with_the_store_present():
    sessions, ephemerals = InMemorySessionStore(), EphemeralSpecStore()
    runner = FakeRunner(keys=["name"], rows=[{"name": "S1"}])
    out = run_spec("explorer.servers.v1", {}, _session(sessions), sessions, runner, ephemerals)
    assert out["spec_id"] == "explorer.servers.v1" and out["ephemeral"] is False


def test_export_manifest_matches_permanent_spec_provenance():
    sessions, ephemerals, ledger = InMemorySessionStore(), EphemeralSpecStore(), ExportLedger()
    runner = FakeRunner()
    token = _session(sessions)
    eph = ephemerals.register(token, CYPHER, "drydocs", params={"limit": 5})
    job = export_spec(eph.ref, {}, "csv", token, sessions, runner, ledger, ephemerals=ephemerals)
    assert job.filename == f"INTERNAL-CONFIDENTIAL__{eph.ref}.csv"
    chunks = list(job.chunks)  # exhausting the stream registers the manifest
    assert chunks[0].startswith("# CLASSIFICATION: INTERNAL-CONFIDENTIAL")
    manifest = ledger.manifest(job.export_id)
    assert manifest["query_spec"] == eph.ref
    assert manifest["cypher_sha256"] == hashlib.sha256(CYPHER.encode("utf-8")).hexdigest()
    assert manifest["params"] == {"limit": 5}
    assert manifest["database"] == "drydocs"
    assert manifest["classification"] == EPHEMERAL_CLASSIFICATION
    assert filename_for(eph.as_query_spec(), "jsonl").startswith("INTERNAL-CONFIDENTIAL__")


def test_raw_cypher_gate_still_admin_only():
    """R4 must not loosen ADR 0005: the interactive raw path stays admin-gated."""
    sessions = InMemorySessionStore()
    with pytest.raises(Forbidden):
        run_raw("MATCH (n) RETURN n", _session(sessions), sessions, FakeRunner())


# ── FastAPI wiring (skips when the api group isn't installed) ────────────────


def test_ephemeral_wiring_end_to_end(monkeypatch):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from drydocs_api.app import create_app

    monkeypatch.setenv("DRYDOCS_AGENT_REG_KEY", "wiring-test-key")
    store = InMemorySessionStore()
    client = TestClient(create_app(runner=FakeRunner(), store=store))
    token = client.post("/login", json={"persona_id": "jdoe4821"}).json()["token"]

    # a browser bearer token alone can never register Cypher
    body = {"owner_token": token, "cypher": CYPHER, "database": "drydocs"}
    assert client.post("/specs/ephemeral", json=body).status_code == 403
    assert (
        client.post(
            "/specs/ephemeral", json=body, headers={"X-DryDocs-Agent-Key": "wrong"}
        ).status_code
        == 403
    )

    registered = client.post(
        "/specs/ephemeral", json=body, headers={"X-DryDocs-Agent-Key": "wiring-test-key"}
    )
    assert registered.status_code == 200
    ref = registered.json()["explore_ref"]

    auth = {"Authorization": f"Bearer {token}"}
    ok = client.post(f"/specs/{ref}/run", json={"params": {}}, headers=auth)
    assert ok.status_code == 200 and ok.json()["ephemeral"] is True

    exported = client.post(f"/specs/{ref}/export?format=csv", json={"params": {}}, headers=auth)
    assert exported.status_code == 200
    assert exported.headers["Content-Disposition"].startswith(
        'attachment; filename="INTERNAL-CONFIDENTIAL__eph.'
    )
    manifest_path = exported.headers["X-DryDocs-Manifest-Path"]
    manifest = client.get(manifest_path, headers=auth).json()
    assert manifest["query_spec"] == ref

    # the owning session only: a second login sees a plain 404
    other = client.post("/login", json={"persona_id": "kchen2190"}).json()["token"]
    foreign = client.post(
        f"/specs/{ref}/run", json={"params": {}}, headers={"Authorization": f"Bearer {other}"}
    )
    assert foreign.status_code == 404

    # write-shaped registration is rejected before anything is stored
    evil = client.post(
        "/specs/ephemeral",
        json={"owner_token": token, "cypher": "CREATE (n)", "database": "drydocs"},
        headers={"X-DryDocs-Agent-Key": "wiring-test-key"},
    )
    assert evil.status_code == 400
