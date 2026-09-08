r"""Serve the DryDocs ADK apps with APP DISCOVERY LIMITED TO REAL APPS (R14).

``adk api_server`` builds its FastAPI app with the flat ``AgentLoader``, whose
``/list-apps`` returns EVERY non-hidden subdirectory of the agents dir — so the
shared-tools package ``common/`` showed up beside graph_qa / core_ingest /
controlm_fix / graph_query as if it were an app. ``adk web`` does not have the
problem: it uses ADK's own ``NestedAgentLoader``, which lists a directory only
when it holds ``agent.py`` or ``root_agent.yaml``. This launcher builds the same
FastAPI app ``adk api_server`` builds, but hands it that loader — the hiding
mechanism the ADK itself supports — so nothing moves: ``common`` stays where the
apps import it from (``from common import ...``), and ``tests/conftest.py``
still closes ``common.neo4j_tool``'s driver singleton by that module name.

CONVENTION (agents/README.md): an app is a directory with an ``agent.py``; a
shared package has none and is therefore never an app. Run::

    cd agents
    .venv\Scripts\python serve.py

NO ``--allow_origins`` (ADR 0020, WEB10): the console reaches this server as
``/agent/*`` on its OWN origin, through the same reverse proxy that serves the
page (Vite's in dev, O72's in the Compose stack), so no browser request is
cross-origin and the allowlist ADK would install is left off. A cross-origin
caller is a deployment defect, not a case to configure for.

This launcher also installs the R23 CONTROL REDACTION, because it is the only
place both halves are in scope: ADK's ``get_fast_api_app`` takes a session
service *URI*, never a service, so the wrapper is applied by replacing the one
factory that module calls. See ``_install_control_redaction`` — it refuses
loudly rather than starting an unredacted server.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parent
if str(AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_DIR))

#: The ADK seam the redaction is installed at: the ONE function
#: ``google.adk.cli.fast_api`` calls to build its session service, whichever
#: backend the options resolve to. Named as a constant so the failure below can
#: quote it, and so an ADK upgrade that renames it is a grep away.
_ADK_SESSION_FACTORY = "create_session_service_from_options"


def _install_control_redaction() -> None:
    """Wrap whatever session service ADK builds so the R5 control token is
    redacted on the way to disk (R23).

    RAISES rather than warns when the seam is gone. A redaction that silently
    stops applying is worse than none: the store keeps looking the same, the
    handshake keeps working, and the only symptom is a credential on disk that
    nobody is looking for. This is the Idea-111 class — an instrument whose
    failure mode is silence — so it is made loud at the one moment somebody is
    watching, which is server start.
    """
    from common.session_redaction import RedactingSessionService
    from google.adk.cli import fast_api
    from graph_qa.control import redact_control_text

    factory = getattr(fast_api, _ADK_SESSION_FACTORY, None)
    if factory is None:
        raise RuntimeError(
            f"google.adk.cli.fast_api.{_ADK_SESSION_FACTORY} is gone, so the R23 "
            "control-token redaction cannot be installed. Re-point it at whatever "
            "builds the session service in this ADK version before serving: an "
            "unredacted server writes the caller's drydocs-api token to "
            "<app>/.adk/session.db in cleartext, once per turn, with no expiry."
        )
    if getattr(factory, "_drydocs_redacting", False):
        return

    def redacting_factory(**kwargs: object):
        return RedactingSessionService(factory(**kwargs), redact_control_text)

    redacting_factory._drydocs_redacting = True
    setattr(fast_api, _ADK_SESSION_FACTORY, redacting_factory)


#: The O63 probe's path. ADK's api_server registers /, /health, /version,
#: /list-apps, /run, /run_sse, /dev-ui* and /apps/* — checked against the
#: installed vendor file, not assumed — so this name is ours and collides with
#: nothing. It is deliberately NOT /health: that one is ADK's own and answers
#: for the SERVER, which is a different question from the one below.
PROVIDER_PROBE_PATH = "/drydocs-health"


def provider_check() -> dict[str, object]:
    """Is the agent's LLM provider configured? (O63 clause f.)

    CHEAP AND SAFE TO CALL: ``provider_from_env`` reads environment variables and
    raises ``ProviderConfigError`` with a fixable message. It contacts no model
    and spends nothing, so a page-load probe can ask it.

    THE IMPORT ORDER BELOW IS THE POINT, and it is a real trap rather than
    ceremony. ``providers.py`` merges only the REPO-ROOT ``.env`` at import;
    ``agents/.env`` — the file every ProviderConfigError message names — is
    merged by ``common.neo4j_tool`` at ITS import (G131's precedence: agents
    first, root as fallback). So a probe that imported ``providers`` alone would
    read a half-loaded environment and report ANTHROPIC_API_KEY unset on a
    machine where a real turn succeeds. Importing the same module the agent's
    own path imports is what makes this probe answer the question the operator
    is actually asking. A false red here is worse than no probe: it sends
    somebody to edit a file that is already correct.

    NO SECRET CROSSES (clause 3): every ProviderConfigError names a KEY and a
    FILE and never a value, and ``detail`` is that message unaltered.
    """
    import common.neo4j_tool  # noqa: F401 — imported for its agents/.env merge
    from graph_qa.providers import ProviderConfigError, provider_from_env

    try:
        provider_from_env()
    except ProviderConfigError as exc:
        return {"configured": False, "detail": str(exc)}
    return {"configured": True, "detail": None}


def build_app(host: str, port: int):
    from google.adk.cli.fast_api import get_fast_api_app
    from google.adk.cli.utils._nested_agent_loader import NestedAgentLoader

    _install_control_redaction()

    app = get_fast_api_app(
        agents_dir=str(AGENTS_DIR),
        agent_loader=NestedAgentLoader(str(AGENTS_DIR)),
        web=False,  # the API server, exactly as `adk api_server` — only the loader differs
        host=host,
        port=port,
    )

    # O63: the one question about this server that ADK cannot answer. /list-apps
    # proves the server is up and serving graph_qa; it says nothing about whether
    # the agent can reach a model, which is the SECOND failure the item exists to
    # tell apart from the first. Added here rather than inside the agent because
    # this launcher is already the place both halves are in scope (see the
    # redaction note above), and because an agent that can answer has, by
    # definition, already got past the thing being checked.
    app.add_api_route(PROVIDER_PROBE_PATH, _provider_probe, methods=["GET"])
    return app


async def _provider_probe() -> dict[str, object]:
    return provider_check()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    import uvicorn

    uvicorn.run(build_app(args.host, args.port), host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
