"""R14 — ADK app discovery lists only the real agent apps, never the shared package.

The predicate is ADK's own (``is_single_agent_directory``: an ``agent.py`` or a
``root_agent.yaml``), which ``NestedAgentLoader`` — the loader ``agents/serve.py``
hands the API server — applies. Re-implemented here so the guard runs in the
poetry env, where google-adk is not installed.
"""

from __future__ import annotations

from pathlib import Path

AGENTS = Path(__file__).resolve().parents[2] / "agents"
REAL_APPS = {"graph_qa", "core_ingest", "controlm_fix", "graph_query"}


def _is_app(path: Path) -> bool:
    return (path / "agent.py").is_file() or (path / "root_agent.yaml").is_file()


def _candidates() -> list[Path]:
    return [
        p
        for p in AGENTS.iterdir()
        if p.is_dir() and not p.name.startswith(".") and p.name not in ("__pycache__", "tmp")
    ]


def test_only_the_real_apps_are_discoverable() -> None:
    apps = {p.name for p in _candidates() if _is_app(p)}
    assert apps == REAL_APPS, apps


def test_the_shared_package_is_not_an_app_and_stays_importable_by_name() -> None:
    common = AGENTS / "common"
    assert common.is_dir() and not _is_app(common), "common/ must never grow an agent.py"
    assert (
        common / "neo4j_tool.py"
    ).is_file()  # tests/conftest.py closes common.neo4j_tool by name
    assert (common / "__init__.py").is_file()


def test_serve_launcher_uses_the_nested_loader_and_readme_states_the_convention() -> None:
    serve = (AGENTS / "serve.py").read_text(encoding="utf-8")
    assert "NestedAgentLoader" in serve and "web=False" in serve
    readme = (AGENTS / "README.md").read_text(encoding="utf-8")
    assert "serve.py" in readme and "an APP is a directory with an `agent.py`" in readme
