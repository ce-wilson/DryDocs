"""debt-metrics.jsonl — one append-only row per snapshot run (U25, 2026-08-21).

WHY. The tech-debt skill's A3/A4/A5 numbers lived in prose baselines ("29 ->
31, all of it tree drift") re-derived by hand each run; "is it getting better"
was unanswerable by a machine. This ledger is the machine-readable history:
after ``snapshot.ps1`` writes a snapshot, it appends ONE row here carrying the
date, the git commit, the snapshot compared, the A3 top module and its fan-in,
the A4 package and first-party orphan counts, the A5 untested count, the live
IMPORTS edge count beside the snapshot's, and the U22 freshness verdict.

RULINGS CARRIED BY THIS FILE:
* COMMITTED, not gitignored — the payoff is history across both machines, and a
  ledger nobody else can read is a private diary. Two machines appending in the
  same window would conflict on the last line, so ``.gitattributes`` marks it
  ``merge=union``: both rows survive, order is irrelevant, every row carries its
  own date and commit.
* U12 STAYS INTACT: newest-only snapshot retention deletes ``<project>-<date>.json``
  files and never this ledger — a metrics ledger is not a retained snapshot.
  The README says so beside the retention rule.
* BORN LF, CR-free (Idea-121): rows are written through ``open(..., newline="\\n")``.
* NO HALF ROWS: with no reachable database the run prints WHY and appends
  NOTHING. A row of zeros presented as a measurement is the defect this series
  exists to prevent.

Usage (from snapshot.ps1, warn-only):
    poetry run python knowledge/depgraph-snapshots/metrics_ledger.py <snapshot.json>
    poetry run python knowledge/depgraph-snapshots/metrics_ledger.py --delta   # last two rows
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LEDGER = HERE / "debt-metrics.jsonl"

#: the eight package roots (pyproject packages + tests) — A3/A4/A5's $packages
PACKAGES = [
    "drydocs",
    "drydocs_core",
    "drydocs_remediation",
    "drydocs_lineage",
    "drydocs_deepdoc",
    "drydocs_docmeta",
    "drydocs_api",
    "tests",
]
FIRST_PARTY_NON_PACKAGE = ["agents", "scripts", "knowledge"]

_TOMB = "m.removed_from_source_at IS NULL"
Q_IMPORTS = (
    "MATCH (a:CodeModule)-[r:IMPORTS]->(b:CodeModule) "
    "WHERE NOT a:SchemaMeta AND NOT b:SchemaMeta RETURN count(r) AS n"
)
Q_A3 = (
    "MATCH (m:CodeModule)<-[:IMPORTS]-(x:CodeModule) WHERE NOT m:SchemaMeta AND NOT x:SchemaMeta "
    f"AND {_TOMB} AND x.removed_from_source_at IS NULL AND m.project IN $packages "
    "RETURN m.file_id AS module, count(x) AS fan_in ORDER BY fan_in DESC, module LIMIT 1"
)
Q_A4 = (
    f"MATCH (m:CodeModule) WHERE NOT m:SchemaMeta AND {_TOMB} AND m.extension = '.py' "
    "AND m.project IN $packages AND NOT ()-[:IMPORTS]->(m) AND NOT (m)-[:IMPORTS]->() "
    "AND m.project <> 'tests' AND NOT m.file_id CONTAINS '__init__' RETURN count(m) AS n"
)
Q_A5 = (
    f"MATCH (m:CodeModule) WHERE NOT m:SchemaMeta AND {_TOMB} AND m.extension = '.py' "
    "AND m.project IN $packages AND m.project <> 'tests' "
    "AND NOT EXISTS { MATCH (t:CodeModule {project:'tests'})-[:IMPORTS]->(m) WHERE NOT t:SchemaMeta } "
    "RETURN count(m) AS n"
)


@dataclass(frozen=True)
class MetricsRow:
    date: str
    commit: str
    snapshot: str
    snapshot_imports: int
    live_imports: int
    a3_top_module: str | None
    a3_fan_in: int
    a4_package_orphans: int
    a4_first_party_orphans: int
    a5_untested: int
    freshness: str
    venue: str

    def as_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def compute_row(
    client: Any, snapshot_path: Path, *, commit: str, venue: str, now: datetime | None = None
) -> MetricsRow:
    """The measurement, given an OPEN client. Pure apart from the queries."""
    doc = json.loads(snapshot_path.read_text(encoding="utf-8"))
    snapshot_imports = len(doc.get("edges") or [])
    live = client.run(Q_IMPORTS)[0]["n"]
    a3 = client.run(Q_A3, packages=PACKAGES)
    a4_pkg = client.run(Q_A4, packages=PACKAGES)[0]["n"]
    a4_fp = client.run(Q_A4, packages=FIRST_PARTY_NON_PACKAGE)[0]["n"]
    a5 = client.run(Q_A5, packages=PACKAGES)[0]["n"]
    try:
        from drydocs.code_graph_freshness import check as freshness_check

        freshness = freshness_check(lambda: client, snapshot_path.parent).verdict.value
    except Exception:  # — the verdict is a rider, never the reason a row fails
        freshness = "unknown"
    stamp = (now or datetime.now(UTC)).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return MetricsRow(
        date=stamp,
        commit=commit,
        snapshot=snapshot_path.name,
        snapshot_imports=snapshot_imports,
        live_imports=int(live),
        a3_top_module=a3[0]["module"] if a3 else None,
        a3_fan_in=int(a3[0]["fan_in"]) if a3 else 0,
        a4_package_orphans=int(a4_pkg),
        a4_first_party_orphans=int(a4_fp),
        a5_untested=int(a5),
        freshness=freshness,
        venue=venue,
    )


def append_row(row: MetricsRow, ledger: Path = LEDGER) -> None:
    """Append-only, LF, CR-free."""
    with ledger.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(row.as_json() + "\n")


def read_rows(ledger: Path = LEDGER) -> list[dict[str, Any]]:
    if not ledger.exists():
        return []
    return [
        json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def delta(rows: list[dict[str, Any]]) -> str:
    """A3/A4/A5 and IMPORTS deltas between the last two rows — the consumer the
    tech-debt skill reads instead of re-deriving prose."""
    if len(rows) < 2:
        return (
            "debt-metrics: fewer than two rows — no delta yet" if rows else "debt-metrics: no rows"
        )
    a, b = rows[-2], rows[-1]

    def d(key: str) -> str:
        x, y = a.get(key), b.get(key)
        if isinstance(x, int) and isinstance(y, int):
            sign = "+" if y - x > 0 else ""
            return f"{x} -> {y} ({sign}{y - x})"
        return f"{x} -> {y}"

    return (
        f"debt-metrics delta {a['date']} @{a['commit'][:7]} -> {b['date']} @{b['commit'][:7]}: "
        f"A3 {a.get('a3_top_module')}={a.get('a3_fan_in')} -> {b.get('a3_top_module')}={b.get('a3_fan_in')}; "
        f"A4 package {d('a4_package_orphans')}, first-party {d('a4_first_party_orphans')}; "
        f"A5 {d('a5_untested')}; live IMPORTS {d('live_imports')} (snapshot {d('snapshot_imports')}); "
        f"freshness {a.get('freshness')} -> {b.get('freshness')}"
    )


def _git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
            timeout=20,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "--delta":
        print(delta(read_rows()))
        return 0
    if not args:
        print("usage: metrics_ledger.py <snapshot.json> | --delta", file=sys.stderr)
        return 2
    snapshot = Path(args[0])
    if not snapshot.is_file():
        print(f"debt-metrics: snapshot {snapshot} not found — no row written", file=sys.stderr)
        return 2
    sys.path.insert(0, str(REPO))
    try:
        from drydocs_core.config import load_settings
        from drydocs_core.neo4j_client import Neo4jClient

        cfg, _, _ = load_settings()
        pw = cfg.password.get_secret_value()
        if not pw:
            raise RuntimeError("NEO4J_PASSWORD empty")
        venue = f"{cfg.uri}/{cfg.database}"
        with Neo4jClient(cfg.uri, cfg.user, pw, cfg.database) as cli:
            row = compute_row(cli, snapshot, commit=_git_commit(), venue=venue)
    except Exception as exc:  # — no database = no row, said plainly
        print(
            f"debt-metrics: no row written — database unreachable ({type(exc).__name__}: "
            f"{str(exc)[:100]}). A row of zeros is not a measurement.",
            file=sys.stderr,
        )
        return 0
    append_row(row)
    print(
        f"debt-metrics: appended row for {row.snapshot} @{row.commit[:7]} ({row.venue}): {row.as_json()}"
    )
    print(delta(read_rows()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
