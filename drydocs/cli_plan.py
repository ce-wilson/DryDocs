"""Snapshot commands: snapshot, prune-snapshots.

S8 (2026-08-21): split out of drydocs/cli.py. The root stays the composition
root and the only module that may wire other components; this module holds
one domain's verbs and registers them on its own Typer, which the root merges
FLAT so `drydocs --help` lists the same names as before. Shared state
(console, registries, gates, adapters) lives in the root and is imported
from it; ``_client`` is resolved THROUGH the root at call time so tests that
monkeypatch ``drydocs.cli._client`` keep working.
"""

from __future__ import annotations

from pathlib import Path

import typer

from drydocs import cli as _root  # the composition root; call-time lookups only
from drydocs.cli import (
    console,
)
from drydocs_core.neo4j_client import Neo4jClient

from .code_graph_freshness import check
from .loaders.code_snapshot import DEFAULT_SNAPSHOT_DIR
from .snapshots import SnapshotWriter

app = typer.Typer()


def _client(database: str | None = None) -> Neo4jClient:
    """Resolved through the root at call time (tests patch drydocs.cli._client)."""
    return _root._client(database)


@app.command()
def snapshot() -> None:
    """(Re)compute snapshots without re-loading source data."""
    with _client() as cli:
        console.print(SnapshotWriter(cli).write_all())


@app.command(name="prune-snapshots")
def prune_snapshots(years: int = typer.Option(5)) -> None:
    """Delete snapshots older than N years (keeps the latest per entity)."""
    with _client() as cli:
        console.print(SnapshotWriter(cli).prune_older_than(years))


@app.command(name="code-graph-freshness")
def code_graph_freshness(
    snapshot_dir: Path = typer.Option(
        DEFAULT_SNAPSHOT_DIR,
        "--snapshot-dir",
        help="Directory of drydocs-*.json snapshots to compare the graph against.",
    ),
) -> None:
    """Is the code graph current? (U22) Compares max(:CodeModule.last_seen_at)
    against the newest snapshot's meta.captured_at and names the drift, the run
    id and the snapshot. WARN-ONLY: exits 0 on every verdict, never refreshes
    anything, and reports DATABASE UNREACHABLE as its own verdict — never as
    fresh."""
    verdict = check(_client, snapshot_dir)
    color = {"fresh": "green", "stale": "yellow"}.get(verdict.verdict.value, "yellow")
    console.print(f"[{color}]{verdict.message()}[/]")
