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
    .venv\Scripts\python serve.py --allow_origins http://localhost:5173

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


def build_app(allow_origins: list[str] | None, host: str, port: int):
    from google.adk.cli.fast_api import get_fast_api_app
    from google.adk.cli.utils._nested_agent_loader import NestedAgentLoader

    _install_control_redaction()

    return get_fast_api_app(
        agents_dir=str(AGENTS_DIR),
        agent_loader=NestedAgentLoader(str(AGENTS_DIR)),
        allow_origins=allow_origins,
        web=False,  # the API server, exactly as `adk api_server` — only the loader differs
        host=host,
        port=port,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow_origins", nargs="*", default=["http://localhost:5173"])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    import uvicorn

    uvicorn.run(build_app(args.allow_origins, args.host, args.port), host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
