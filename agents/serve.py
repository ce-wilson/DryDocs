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
"""

from __future__ import annotations

import argparse
from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parent


def build_app(allow_origins: list[str] | None, host: str, port: int):
    from google.adk.cli.fast_api import get_fast_api_app
    from google.adk.cli.utils._nested_agent_loader import NestedAgentLoader

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
