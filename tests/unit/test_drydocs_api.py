"""drydocs-api offline tests — pure handlers over a duck-typed runner
(the graph_verify idiom): no server, no driver, no FastAPI import needed."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from drydocs_api.guard import WriteRejected, ensure_read_only, is_write_cypher
from drydocs_api.handlers import Forbidden, login, logout, run_named, run_raw
from drydocs_api.personas import PERSONAS, UnknownPersonaError
from drydocs_api.queries import (
    NAMED_QUERIES,
    ParamValidationError,
    UnknownQueryError,
    named_query,
    validate_params,
)
from drydocs_api.routing import VIEW_DATABASES, UnknownViewError, database_for
from drydocs_api.sessions import InMemorySessionStore, InvalidTokenError

REPO_ROOT = Path(__file__).resolve().parents[2]


class FakeRunner:
    """Records the exact cypher/params/database the handlers hand to the driver."""

    def __init__(self, keys=None, rows=None):
        self.calls: list[tuple[str, dict, str]] = []
        self._keys = keys or ["n"]
        self._rows = rows or [{"n": 1}]

    def run(self, cypher, params, database):
        self.calls.append((cypher, dict(params), database))
        return self._keys, self._rows


def _admin_token(store: InMemorySessionStore) -> str:
    return store.issue("asmith7734").token


def _user_token(store: InMemorySessionStore) -> str:
    return store.issue("jdoe4821").token


# ── guard ────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "cypher",
    [
        "CREATE (n:Evil)",
        "MATCH (n) SET n.x = 1",
        "MATCH (n) DETACH DELETE n",
        "MERGE (n:Sneaky {id: 1})",
        "MATCH (n) REMOVE n.prop",
        "DROP CONSTRAINT c",
        "LOAD CSV FROM 'file:///x' AS row RETURN row",
        "FOREACH (x IN [1] | CREATE (:N))",
    ],
)
def test_guard_rejects_write_clauses(cypher):
    with pytest.raises(WriteRejected):
        ensure_read_only(cypher)


@pytest.mark.parametrize(
    "cypher",
    [
        "MATCH (n) RETURN n LIMIT 5",
        "MATCH p = shortestPath((a)-[:WAS_INFORMED_BY*..15]-(b)) RETURN p",
        # write words inside STRINGS and COMMENTS are data, not code (the ADR 0003
        # code-regions lesson) — must pass:
        "MATCH (n {name: 'please delete me'}) RETURN n",
        'MATCH (n) WHERE n.note = "set in stone" RETURN n',
        "// create nothing here\nMATCH (n) RETURN count(n)",
        "/* merge notes */ MATCH (n) RETURN n.dataset AS d",
        # substrings of write words are not write words:
        "MATCH (n) RETURN n.offset, n.reset, n.created_by",
    ],
)
def test_guard_allows_reads_and_data_mentions(cypher):
    ensure_read_only(cypher)
    assert is_write_cypher(cypher) is None


# ── sessions + personas ──────────────────────────────────────────────────────


def test_session_issue_resolve_revoke():
    store = InMemorySessionStore()
    s = store.issue("jdoe4821")
    assert s.role == "user" and s.persona_id == "jdoe4821" and len(s.token) > 20
    assert store.resolve(s.token).role == "user"
    store.revoke(s.token)
    with pytest.raises(InvalidTokenError):
        store.resolve(s.token)


def test_unknown_persona_rejected():
    store = InMemorySessionStore()
    with pytest.raises(UnknownPersonaError):
        store.issue("realuser1")


def test_personas_match_web_auth_ts():
    """Drift guard: the server stub's personas mirror web/src/lib/auth.ts."""
    ts = (REPO_ROOT / "web" / "src" / "lib" / "auth.ts").read_text(encoding="utf-8")
    ts_ids = dict(
        zip(re.findall(r"id: '([^']+)'", ts), re.findall(r"role: '([^']+)'", ts), strict=True)
    )
    assert ts_ids == {p.id: p.role for p in PERSONAS.values()}


# ── routing + queries ────────────────────────────────────────────────────────


def test_every_named_query_has_a_routing_row():
    for qid in NAMED_QUERIES:
        assert database_for(qid)  # fail-closed registry alignment
    assert "raw-cypher" in VIEW_DATABASES


def test_unknown_view_fails_closed():
    with pytest.raises(UnknownViewError):
        database_for("context-findings")  # future ddall view: explicit row required


def test_named_queries_are_read_only():
    for q in NAMED_QUERIES.values():
        ensure_read_only(q.cypher)


def test_param_validation():
    chain = named_query("dependency-chain")
    ok = validate_params(chain, {"job_a": "A", "job_b": "B"})
    assert ok == {"job_a": "A", "job_b": "B"}
    with pytest.raises(ParamValidationError):
        validate_params(chain, {"job_a": "A"})  # missing required
    with pytest.raises(ParamValidationError):
        validate_params(chain, {"job_a": "A", "job_b": "B", "depth": 3})  # unknown
    with pytest.raises(ParamValidationError):
        validate_params(chain, {"job_a": 1, "job_b": "B"})  # wrong type
    c4 = named_query("c4-graph")
    assert validate_params(c4, {}) == {"limit": 200}  # default applied
    with pytest.raises(ParamValidationError):
        validate_params(c4, {"limit": True})  # bool is not int here


# ── handlers ─────────────────────────────────────────────────────────────────


def test_login_and_named_query_routes_database():
    store = InMemorySessionStore()
    runner = FakeRunner(keys=["labels", "count"], rows=[{"labels": ["X"], "count": 1}])
    session = login("jdoe4821", store)
    out = run_named("overview-counts", {}, session["token"], store, runner)
    assert out["database"] == "drydocs" and out["rows"] == [{"labels": ["X"], "count": 1}]
    cypher, params, database = runner.calls[0]
    assert database == "drydocs" and params == {} and cypher.startswith("MATCH (n)")


def test_named_query_requires_auth_and_known_id():
    store = InMemorySessionStore()
    runner = FakeRunner()
    with pytest.raises(InvalidTokenError):
        run_named("overview-counts", {}, "not-a-token", store, runner)
    with pytest.raises(UnknownQueryError):
        run_named("nope", {}, _user_token(store), store, runner)
    assert runner.calls == []  # nothing reached the driver


def test_raw_cypher_admin_only_and_guarded():
    store = InMemorySessionStore()
    runner = FakeRunner()
    with pytest.raises(Forbidden):
        run_raw("MATCH (n) RETURN n", _user_token(store), store, runner)
    with pytest.raises(WriteRejected):
        run_raw("CREATE (n)", _admin_token(store), store, runner)
    assert runner.calls == []
    out = run_raw("MATCH (n) RETURN count(n) AS c", _admin_token(store), store, runner)
    assert out["database"] == "drydocs"
    assert runner.calls[0][2] == "drydocs"  # db routed server-side, not caller-chosen


def test_logout_revokes():
    store = InMemorySessionStore()
    session = login("asmith7734", store)
    logout(session["token"], store)
    with pytest.raises(InvalidTokenError):
        run_raw("MATCH (n) RETURN n", session["token"], store, FakeRunner())


# ── optional wiring smoke (skips when the api group isn't installed) ─────────


def test_fastapi_wiring_smoke():
    fastapi = pytest.importorskip("fastapi")  # noqa: F841 — poetry install --with api
    from fastapi.testclient import TestClient

    from drydocs_api.app import create_app

    app = create_app(runner=FakeRunner(), store=InMemorySessionStore())
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
    token = client.post("/login", json={"persona_id": "jdoe4821"}).json()["token"]
    ok = client.post(
        "/query/overview-counts", json={"params": {}}, headers={"Authorization": f"Bearer {token}"}
    )
    assert ok.status_code == 200 and ok.json()["database"] == "drydocs"
    forbidden = client.post(
        "/raw-cypher",
        json={"cypher": "MATCH (n) RETURN n"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert forbidden.status_code == 403


# --- test-transport dependency (back-flow #4, 2026-07-28) --------------------


def test_declared_test_transport_matches_what_starlette_resolves() -> None:
    """The declared httpx/httpx2 dependency must match what starlette imports.

    starlette >=1.3 does ``try: import httpx2 ... except ModuleNotFoundError:
    import httpx`` and warns (StarletteDeprecationWarning) when it lands on the
    fallback — so BOTH work and neither side is broken. That is precisely why
    this drifted silently: the producer swapped to httpx2 for starlette 1.3,
    the consumer kept httpx on an older starlette, and each was correct in its
    own environment (PORT-REPORT-94132c80, back-flow #4).

    So the answer is environment-derived, not a fact to carry in a ledger or a
    comment: ask the installed starlette what it actually resolved. The
    consumer's own suite then tells it to switch when it bumps starlette,
    instead of someone having to remember.
    """
    pytest.importorskip("starlette", reason="fastapi/starlette is an optional dep")
    import starlette.testclient as tc

    resolved = tc.httpx.__name__  # "httpx2" on starlette >=1.3, else "httpx"
    pyproject = (Path(__file__).resolve().parents[2] / "pyproject.toml").read_text(encoding="utf-8")
    declared = {
        name for name in ("httpx2", "httpx") if re.search(rf"^{name}\s*=", pyproject, re.MULTILINE)
    }
    assert declared == {resolved}, (
        f"pyproject declares {sorted(declared)} but the installed starlette resolves "
        f"{resolved!r} for TestClient — declare exactly the one it uses (the other "
        "still works, but via the deprecated fallback path)"
    )
