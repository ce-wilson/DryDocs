"""Is the code graph current? Compare the graph against the snapshot series (U22).

THE INCIDENT (2026-08-13, desktop, neo4jtest, drydocs DB): every :CodeModule
carried ``last_seen_at = 2026-08-02T23:06:42Z`` from ONE run id — loaded once,
never refreshed, eleven days — and a session read the A3 fan-in off it as
current. Same class as G78: not a failed read, a read that SUCCEEDED with the
wrong data, underneath every architecture and debt decision. ``drydocs
load-code-snapshot`` repairs it in one command; nothing COMPARED the graph
against the snapshot series. (Seen again at U21, 2026-08-21: 891 live IMPORTS
against 1032 in the newest snapshot before the load ran.)

WHAT THIS IS. ``max(:CodeModule.last_seen_at)`` and the run id that wrote it,
against the newest ``knowledge/depgraph-snapshots/drydocs-*.json``
``meta.captured_at`` — reported with the drift, the run id and WHICH snapshot
was compared, so "the graph is current" is falsifiable. WARN, NEVER FAIL: the
check rides the tech-debt skill's read path and the session ritual as a line,
and it must never block a suite or a snapshot on a machine with no database.
DATABASE-UNREACHABLE IS ITS OWN VERDICT, never "fresh" — the failure this
exists to stop is a check that reports green because it could not look. It
REPORTS a stale graph and never refreshes it: a check that repairs what it
measures can never be trusted to have measured anything.

The comparison is pure (:func:`compare`) so it is unit-testable over fixtures;
:func:`check` is the thin I/O wrapper around it.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from .loaders.code_snapshot import DEFAULT_SNAPSHOT_DIR, CodeSnapshotError, select_newest_snapshot

#: A graph loaded this long after the newest snapshot's capture still counts as
#: fresh — the load is a separate step run minutes to hours after the scan.
#: Older than the snapshot by any amount is stale: a newer scan exists.
FRESH_TOLERANCE = timedelta(0)


class Verdict(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    NO_SNAPSHOT = "no-snapshot"
    EMPTY_GRAPH = "empty-graph"
    UNREACHABLE = "database-unreachable"


@dataclass(frozen=True)
class Freshness:
    verdict: Verdict
    graph_last_seen: datetime | None = None
    graph_run_id: str | None = None
    snapshot_name: str | None = None
    snapshot_captured_at: datetime | None = None
    detail: str = ""

    @property
    def lag(self) -> timedelta | None:
        if self.graph_last_seen is None or self.snapshot_captured_at is None:
            return None
        return self.snapshot_captured_at - self.graph_last_seen

    @property
    def is_warning(self) -> bool:
        return self.verdict is not Verdict.FRESH

    def message(self) -> str:
        snap = self.snapshot_name or "<no snapshot>"
        if self.verdict is Verdict.FRESH:
            return (
                f"code graph: FRESH — loaded {_iso(self.graph_last_seen)} by run "
                f"{self.graph_run_id} against {snap} (captured {_iso(self.snapshot_captured_at)})"
            )
        if self.verdict is Verdict.STALE:
            lag = self.lag or timedelta(0)
            return (
                f"code graph: STALE by {_days(lag)} — last loaded {_iso(self.graph_last_seen)} "
                f"(run {self.graph_run_id}); newest snapshot {snap} captured "
                f"{_iso(self.snapshot_captured_at)}. Run `drydocs load-code-snapshot` — "
                "this check reports, it never refreshes."
            )
        if self.verdict is Verdict.NO_SNAPSHOT:
            return f"code graph: NO SNAPSHOT on disk to compare against ({self.detail}) — run snapshot.ps1"
        if self.verdict is Verdict.EMPTY_GRAPH:
            return (
                f"code graph: EMPTY — no :CodeModule loaded; newest snapshot is {snap} "
                f"(captured {_iso(self.snapshot_captured_at)}). Run `drydocs load-code-snapshot`."
            )
        return (
            f"code graph: DATABASE UNREACHABLE ({self.detail}) — freshness UNKNOWN, not fresh; "
            f"newest snapshot on disk is {snap}"
        )


def _iso(value: datetime | None) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ") if value else "?"


def _days(lag: timedelta) -> str:
    days = lag.total_seconds() / 86400
    return f"{days:.1f} day(s)" if days >= 1 else f"{lag.total_seconds() / 3600:.1f} hour(s)"


def _as_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    elif hasattr(value, "to_native"):  # neo4j.time.DateTime
        dt = value.to_native()
    else:
        text = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        # snapshot.ps1 stamps meta.captured_at as (Get-Date).ToString("s") —
        # LOCAL wall-clock time with no offset — while the loader writes
        # last_seen_at from an ISO string WITH +00:00. A naive value is therefore
        # local time of the machine that wrote it, never UTC; reading it as UTC
        # would shift the snapshot hours earlier and call a stale graph fresh.
        dt = dt.astimezone()
    return dt.astimezone(UTC)


def compare(
    graph_last_seen: Any,
    graph_run_id: str | None,
    snapshot_name: str | None,
    snapshot_captured_at: Any,
) -> Freshness:
    """The pure verdict. Fixtures in, verdict out — no I/O."""
    seen = _as_utc(graph_last_seen)
    captured = _as_utc(snapshot_captured_at)
    if snapshot_name is None or captured is None:
        return Freshness(
            Verdict.NO_SNAPSHOT,
            graph_last_seen=seen,
            graph_run_id=graph_run_id,
            detail="no drydocs-*.json with meta.captured_at",
        )
    if seen is None:
        return Freshness(
            Verdict.EMPTY_GRAPH,
            snapshot_name=snapshot_name,
            snapshot_captured_at=captured,
        )
    verdict = Verdict.FRESH if seen + FRESH_TOLERANCE >= captured else Verdict.STALE
    return Freshness(
        verdict,
        graph_last_seen=seen,
        graph_run_id=graph_run_id,
        snapshot_name=snapshot_name,
        snapshot_captured_at=captured,
    )


def newest_snapshot(snapshot_dir: Path | str = DEFAULT_SNAPSHOT_DIR) -> tuple[str | None, Any]:
    """(file name, meta.captured_at) of the newest snapshot, or (None, None)."""
    try:
        path = select_newest_snapshot(snapshot_dir)
    except (CodeSnapshotError, FileNotFoundError, OSError):
        return None, None
    meta = json.loads(Path(path).read_text(encoding="utf-8")).get("meta") or {}
    return Path(path).name, meta.get("captured_at")


GRAPH_PROBE = (
    "MATCH (m:CodeModule) WHERE NOT m:SchemaMeta "
    "WITH m ORDER BY m.last_seen_at DESC LIMIT 1 "
    "RETURN m.last_seen_at AS last_seen_at, m.last_run_id AS run_id"
)


def check(
    client_factory: Callable[[], Any],
    snapshot_dir: Path | str = DEFAULT_SNAPSHOT_DIR,
) -> Freshness:
    """The I/O wrapper: probe the graph (any failure -> UNREACHABLE, named),
    read the newest snapshot, compare. Never raises, never writes."""
    name, captured = newest_snapshot(snapshot_dir)
    try:
        with client_factory() as cli:
            rows = cli.run(GRAPH_PROBE)
    except Exception as exc:  # — unreachable is a verdict, not a crash
        return Freshness(
            Verdict.UNREACHABLE,
            snapshot_name=name,
            snapshot_captured_at=_as_utc(captured) if name else None,
            detail=f"{type(exc).__name__}: {str(exc)[:120]}",
        )
    if not rows or rows[0].get("last_seen_at") is None:
        return compare(None, None, name, captured)
    return compare(rows[0]["last_seen_at"], rows[0].get("run_id"), name, captured)
