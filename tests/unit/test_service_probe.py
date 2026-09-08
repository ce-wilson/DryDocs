"""O63 — the two server-side halves of the service probe.

The console asks four questions to tell one broken page apart from another: is
drydocs-api up, is the graph behind it there, is the agent server serving
graph_qa, and can the agent reach a model. Two of those needed a server route
that did not exist; this file guards both, plus the one property that makes the
agent answer trustworthy.

WHY THE AGENT HALF IS TESTED BY READING SOURCE. ``agents/serve.py`` lives behind
its own venv — ``google-adk`` is not importable from this interpreter, which is
why ``tests/unit/test_session_redaction.py`` skips — so the assertions here read
the file. The BEHAVIOUR is covered where it can actually run: the stub serves the
same route and the console's tests drive it.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.source_scan import source_text

REPO = Path(__file__).resolve().parents[2]
SERVE = REPO / "agents" / "serve.py"


def _serve_tree() -> ast.Module:
    """``agents/serve.py`` as an AST.

    DELIBERATELY NOT ``source_scan.code_only``, and the reason is worth stating
    because it is the same trap J66 warns about from the other side. That helper
    strips STRING LITERALS (so a guard grepping for a forbidden pattern cannot
    match the comment explaining it) and re-joins tokens with single spaces. Both
    assertions below need precisely what it removes: a path's literal VALUE, and
    real statement ORDER. The parser reads code and nothing but, so it is the
    right instrument here — and it cannot match prose either, which is the
    property J66 actually asks for.
    """
    return ast.parse(source_text(SERVE))


def _assigned_literal(tree: ast.Module, name: str) -> object:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == name for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError(f"agents/serve.py declares no module-level {name}")


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"agents/serve.py declares no {name}()")


# ── the agent-side probe ─────────────────────────────────────────────────────


def test_the_stub_and_the_server_agree_on_the_probe_path() -> None:
    """One path, declared twice because the two live in different venvs.

    The stub cannot import ``agents/serve.py`` and the server will never import
    the stub, so the constant is duplicated on purpose — and duplicated constants
    drift. This is the guard that says they have not."""
    from tests.stub_adk import PROVIDER_PROBE_PATH as STUB_PATH

    served = _assigned_literal(_serve_tree(), "PROVIDER_PROBE_PATH")
    assert served == STUB_PATH, (
        f"agents/serve.py serves {served!r} but the stub serves {STUB_PATH!r}; "
        "every console test would pass against a route production does not have"
    )


def test_the_probe_path_is_not_one_adk_already_owns() -> None:
    """ADK's api_server registers /, /health, /version, /list-apps, /run,
    /run_sse, /dev-ui* and /apps/* — read off the installed vendor file, not
    assumed. Ours must be none of them, and NOT ``/health`` in particular, which
    is the tempting name: that route is ADK's own and answers for the SERVER,
    which is a different question from whether the agent can reach a model."""
    from tests.stub_adk import PROVIDER_PROBE_PATH

    reserved = {"/", "/health", "/version", "/list-apps", "/run", "/run_sse"}
    assert PROVIDER_PROBE_PATH not in reserved
    assert not PROVIDER_PROBE_PATH.startswith(("/apps/", "/dev-ui"))


def test_the_provider_check_loads_the_agents_env_before_reading_it() -> None:
    """THE TRAP THIS GUARD EXISTS FOR, stated because the assertion is otherwise
    unreadable: ``graph_qa/providers.py`` merges only the REPO-ROOT ``.env`` at
    import, while ``agents/.env`` — the file every ProviderConfigError message
    names — is merged by ``common.neo4j_tool`` at ITS import (G131). So a probe
    that imported ``providers`` alone would read a half-loaded environment and
    report ANTHROPIC_API_KEY unset on a machine where a real turn succeeds.

    A false RED here is worse than no probe at all: it sends an operator to edit
    a file that is already correct, which is the same harm O63 was raised to
    remove. The import is load-bearing, so it is asserted."""
    fn = _function(_serve_tree(), "provider_check")

    merge_at: int | None = None
    call_at: int | None = None
    for node in ast.walk(fn):
        if isinstance(node, ast.Import) and any(
            alias.name == "common.neo4j_tool" for alias in node.names
        ):
            merge_at = node.lineno
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "provider_from_env"
        ):
            call_at = node.lineno

    assert merge_at is not None, (
        "agents/serve.provider_check must import common.neo4j_tool for its "
        "agents/.env merge, or it reports on a half-loaded environment"
    )
    assert call_at is not None, "provider_check never calls provider_from_env()"
    assert (
        merge_at < call_at
    ), "the agents/.env merge has to happen before the check reads the environment"


def test_the_probe_reports_no_secret(monkeypatch) -> None:
    """Rule 3: the diagnosis says a key is UNSET — never its value, length,
    prefix or a masked form. Proven against the real error text rather than
    argued: ``provider_from_env`` is pure environment reading, and its messages
    are the probe's ``detail`` verbatim.

    THIS ONE RUNS RATHER THAN SKIPS, deliberately. The rest of ``agents/`` needs
    its own venv, so the reflex is to ``importorskip`` anything under it — but
    ``providers.py`` imports only stdlib and ``python-dotenv``, which the main
    venv has, and litellm is imported LAZILY inside ``complete()``. A skip here
    would have been a security-relevant assertion that ran on no machine and in
    no CI job, which is worse than not writing it: it reads as coverage."""
    import sys

    agents_dir = str(REPO / "agents")
    if agents_dir not in sys.path:
        sys.path.insert(0, agents_dir)
    providers = pytest.importorskip(
        "graph_qa.providers", reason="python-dotenv absent — providers cannot import at all"
    )
    secret = "sk-ant-do-not-leak-me-0123456789"
    monkeypatch.setenv("GRAPHQA_PROVIDER", "anthropic")
    monkeypatch.setenv("GRAPHQA_MODEL", "some-model")
    monkeypatch.setenv("ANTHROPIC_API_KEY", secret)
    providers.provider_from_env()  # configured: no error, nothing to leak

    monkeypatch.delenv("ANTHROPIC_API_KEY")
    with pytest.raises(providers.ProviderConfigError) as exc:
        providers.provider_from_env()
    detail = str(exc.value)
    assert "ANTHROPIC_API_KEY" in detail and "agents/.env" in detail
    assert secret not in detail and secret[:8] not in detail


# ── the graph half, on drydocs-api ───────────────────────────────────────────

pytest.importorskip("fastapi", reason="optional api group (poetry install --with api)")


class _Reachable:
    def run(self, cypher, params, database):
        return ["ok"], [{"ok": 1}]


class _Refused:
    def run(self, cypher, params, database):
        raise ConnectionRefusedError("bolt://a-host-that-must-not-reach-the-page:7687 refused")


def _client(monkeypatch, tmp_path, runner, persona="morpheus"):
    from fastapi.testclient import TestClient

    from drydocs_api.app import create_app
    from drydocs_api.credentials import CredentialStore
    from drydocs_api.sessions import InMemorySessionStore

    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setenv("DRYDOCS_MAPPING_DB", str(tmp_path / "mapping.db"))
    creds = CredentialStore()
    creds.set(persona, "s")
    app = create_app(runner=runner, store=InMemorySessionStore(), credentials=creds)
    client = TestClient(app)
    token = client.post("/login", json={"persona_id": persona, "secret": "s"}).json()["token"]
    return client, {"Authorization": f"Bearer {token}"}


def test_graph_status_reports_the_reviewed_read_database(monkeypatch, tmp_path) -> None:
    from drydocs_api.query_specs import SPEC_DATABASES

    client, auth = _client(monkeypatch, tmp_path, _Reachable())
    body = client.get("/graph-status", headers=auth).json()
    assert body == {"reachable": True, "database": sorted(SPEC_DATABASES)[0], "detail": None}


def test_an_unreachable_graph_is_a_verdict_not_a_500(monkeypatch, tmp_path) -> None:
    """``LiveRunner`` builds its driver LAZILY, so a wrong NEO4J_URI first throws
    on this very call rather than at server start. That has to render as a red
    VERDICT — a 500 would put the strip in its "could not check" state and lose
    the one fact it was asked for."""
    client, auth = _client(monkeypatch, tmp_path, _Refused())
    res = client.get("/graph-status", headers=auth)
    assert res.status_code == 200
    assert res.json()["reachable"] is False


def test_the_failure_detail_is_the_class_and_never_the_coordinate(monkeypatch, tmp_path) -> None:
    """A driver's message quotes the URI it dialled. A page must carry no host or
    port (ADR 0020, enforced on the bundle by checkDistCoordinates.mjs) — and the
    exception CLASS is also the thing that actually separates an auth failure
    from a refused connection, so nothing diagnostic is lost by dropping the
    rest."""
    client, auth = _client(monkeypatch, tmp_path, _Refused())
    detail = client.get("/graph-status", headers=auth).json()["detail"]
    assert detail == "ConnectionRefusedError"
    assert "bolt://" not in detail and "7687" not in detail


def test_graph_status_is_steward_or_admin(monkeypatch, tmp_path) -> None:
    """Matching /docs-verify: it reports an infrastructure fact, and an end user
    reads "the graph is down" as breakage rather than as the operator signal it
    is."""
    client, auth = _client(monkeypatch, tmp_path, _Reachable(), persona="neo")  # plain user
    assert client.get("/graph-status", headers=auth).status_code == 403
