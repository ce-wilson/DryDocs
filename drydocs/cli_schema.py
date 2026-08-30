"""Schema / environment commands: check, landing-zones, bootstrap, bootstrap-schema-graph, verify, reset, sweep-removed.

S8 (2026-08-21): split out of drydocs/cli.py. The root stays the composition
root and the only module that may wire other components; this module holds
one domain's verbs and registers them on its own Typer, which the root merges
FLAT so `drydocs --help` lists the same names as before. Shared state
(console, registries, gates, adapters) lives in the root and is imported
from it; ``_client`` is resolved THROUGH the root at call time so tests that
monkeypatch ``drydocs.cli._client`` keep working.
"""

from __future__ import annotations

import typer
from rich.table import Table

from drydocs.cli_shared import (
    CONSTRAINTS_FILE,
    ONTOLOGY_FILE,
    SCHEMA_GRAPH_DATABASE,
    SCHEMA_GRAPH_FILE,
    console,
)
from drydocs_core.neo4j_client import Neo4jClient
from drydocs_core.schema.constraints import declared_constraint_names

app = typer.Typer()


def _client(database: str | None = None) -> Neo4jClient:
    """Resolved through the root at call time (tests patch drydocs.cli._client).

    The import is function-local ON PURPOSE: a module-scope root import is the
    S13 cycle (root body -> command modules -> root), and the guard
    (test_cli_import_order.py) fails this module by name if one returns."""
    from drydocs import cli as _root

    return _root._client(database)


@app.command()
def check() -> None:
    """Verify Neo4j connectivity, server version, and APOC availability."""
    with _client() as cli:
        console.print(f"[cyan]Server:[/] {cli.server_version()}")
        if not cli.apoc_available():
            console.print("[red]APOC not available.[/]")
            raise typer.Exit(2)
        console.print("[green]APOC OK.[/]")


@app.command(name="landing-zones")
def landing_zones_cmd(
    as_json: bool = typer.Option(False, "--json", help="machine-readable inventory"),
    check: bool = typer.Option(
        False, "--check", help="exit 1 when a declared zone is missing or empty"
    ),
) -> None:
    """Where every MANUAL source drops, and what is actually there right now.

    Read-only: it never creates a zone, because a doctor that repairs the tree it
    is inspecting reports health on damage it just hid. ``--check`` is the
    before/after call for a port -- an emptied zone is the signature of a
    ``git clean``, and the reflog cannot recover it (see docs/port/port-prompt.md).
    """
    from drydocs_core.landing_zones import BASES, inventory, manual_zones

    zones = manual_zones()
    undeclared = [z.source_id for z in zones if z.base not in BASES]
    if undeclared:
        console.print(
            f"[red]{len(undeclared)} manual row(s) without acquisition.drop_dir_base: "
            f"{', '.join(undeclared)} — cannot resolve a zone that does not say where "
            "it is rooted.[/]"
        )
        raise typer.Exit(2)

    statuses = inventory(zones)

    # G109: the OTHER declaration. Until now this command read only the manual
    # rows in source-registry.yaml, so every zone G81 declared in
    # config/data-zones.yaml -- eleven of them, including read zones holding real
    # source data -- was invisible to the one command whose whole purpose is that
    # "my extracts are gone" is a one-command answer. A check that silently covers
    # half the zones reads as coverage; that is the defect, not the count.
    from drydocs_core.data_zones import READ as ZONE_READ
    from drydocs_core.data_zones import inventory as zone_inventory
    from drydocs_core.data_zones import load_zones

    declared = zone_inventory(load_zones())

    # G125: the THIRD declaration, and the one that made this command's headline
    # claim only half true. Both surfaces above are FILESYSTEM zones -- the manual
    # half. The fifteen `acquisition.mode: automated` rows resolved through
    # nothing at all: their system rows carried `locator.service: ~` and a comment,
    # and nothing resolves a comment. So a clean run here covered the rows it knew
    # about and said nothing about the rows it did not, which is the same defect
    # G109 fixed one level narrower. ADR 0017 clause 7 rules the SCOPE: this
    # reports what is configured on THIS machine, starts at the registration
    # rather than at .env, and stops at the first stage that is not built.
    from drydocs_core.source_bindings import load_unbound
    from drydocs_core.source_bindings import reports as binding_reports

    bindings = binding_reports()
    unbound = load_unbound()

    if as_json:
        console.print_json(
            data={
                "manual_zones": [
                    {
                        "source_id": s.zone.source_id,
                        "format": s.zone.fmt,
                        "base": s.zone.base,
                        "drop_dir": s.zone.drop_dir,
                        "path": str(s.zone.path),
                        "inside_repo": s.zone.inside_repo,
                        "exists": s.exists,
                        "file_count": s.file_count,
                        "empty": s.empty,
                    }
                    for s in statuses
                ],
                "declared_zones": [
                    {
                        "zone_id": s.zone.id,
                        "mode": s.zone.mode,
                        "base": s.zone.base,
                        "path": str(s.zone.path),
                        "inside_repo": s.zone.inside_repo,
                        # G126: an in-tree zone is reachable by `git clean -fdx`,
                        # so a machine reader needs the recovery path in the same
                        # row as the hazard, not in prose beside it.
                        "rebuild": s.zone.rebuild,
                        "exists": s.exists,
                        "file_count": s.file_count,
                        "empty": s.empty,
                    }
                    for s in declared
                ],
                # G125: ONE document, still. G109 caught this command emitting two
                # JSON payloads in its own change before it shipped; a third
                # declaration is a third KEY, never a second print_json call.
                "bindings": [
                    {
                        "carrier": b.carrier,
                        "profile": b.profile_id,
                        "verdict": b.verdict,
                        "venue": b.venue,
                        "datasets": b.datasets,
                        "stopped_at": b.stopped_at,
                        "unset": list(b.unset),
                        "is_failure": b.is_failure,
                        "stages": [
                            {
                                "stage": st.stage,
                                "capable": st.capable,
                                "detail": st.detail,
                                "mitigation": st.mitigation,
                            }
                            for st in b.stages
                        ],
                    }
                    for b in bindings
                ],
                "unbound_carriers": [{"carrier": u.carrier, "reason": u.reason} for u in unbound],
            }
        )
    else:
        t = Table(title="Manual landing zones (acquisition.mode: manual)")
        for col in ("source", "fmt", "base", "path", "state"):
            t.add_column(col, overflow="fold")
        for s in statuses:
            if not s.exists:
                state = "[dim]absent[/]"
            elif s.empty:
                state = "[yellow]EMPTY[/]"
            else:
                state = f"[green]{s.file_count} file(s)[/]"
            t.add_row(s.zone.source_id, s.zone.fmt, s.zone.base, str(s.zone.path), state)
        console.print(t)
        console.print(
            "[dim]absent = the directory is not there. That is the healthy first state of "
            "a zone nobody has dropped into yet — AND it is also what a `git clean -fd` "
            "leaves behind, because -d removes the untracked directory itself. Without a "
            "baseline the two are indistinguishable here, so absent is never a defect.[/]"
        )
        console.print(
            "[dim]EMPTY = the directory is present and holds nothing. That is the narrower "
            "signature — a selective delete, a half-finished restore — and --check exits 1 "
            "on it.[/]"
        )
        console.print(
            "[dim]Detection is the weaker half. What prevents the loss is location: "
            "data_root zones sit outside the tree where no clean can reach them, and repo "
            "LANDING zones hold TRACKED files, which no clean removes at any strength. "
            "One declared data zone is neither — see the rebuild note under the second "
            "table (G126).[/]"
        )

    if not as_json:
        dt = Table(title="Declared data zones (config/data-zones.yaml)")
        for col in ("zone", "mode", "base", "path", "state"):
            dt.add_column(col, overflow="fold")
        for s in declared:
            if not s.exists:
                state = "[dim]absent[/]"
            elif s.empty:
                state = "[yellow]EMPTY[/]" if s.zone.mode == ZONE_READ else "[dim]empty[/]"
            else:
                state = f"[green]{s.file_count} file(s)[/]"
            dt.add_row(s.zone.id, s.zone.mode, s.zone.base, str(s.zone.path), state)
        console.print(dt)
        console.print(
            "[dim]Mode decides what EMPTY means, which is why it is a column. An empty "
            "READ zone is the same signature as above -- source data that was there and "
            "is not. An empty write/scratch zone is an output directory the system will "
            "rebuild, so --check never fails on one.[/]"
        )
        rebuildable = [s.zone for s in declared if s.zone.base == "repo"]
        for zone in rebuildable:
            console.print(
                f"[red]{zone.id} sits INSIDE the working tree and is gitignored, so "
                "`git clean -fd` cannot reach it but `-fdx` CAN — and a zone is only "
                "as recoverable as the payload it holds.[/]"
            )
            console.print(
                f"[dim]The system's own payload here is rebuilt by:[/] [cyan]{zone.rebuild}[/]"
            )
            console.print(
                "[dim]Anything ELSE an operator keeps in this directory is theirs, "
                "travels by hand, and that command does not bring it back. Read the "
                "count above as 'files -fdx would delete', not as 'files one command "
                "restores'.[/]"
            )

    if not as_json:
        bt = Table(title="Source bindings (config/source-bindings.yaml) — automated carriers")
        for col in ("carrier", "profile", "datasets", "state", "stopped at"):
            bt.add_column(col, overflow="fold")
        for b in bindings:
            if b.is_failure:
                state = f"[red]{b.verdict}[/]"
            elif b.verdict == "configured":
                state = "[green]configured[/]"
            else:
                state = f"[dim]{b.verdict}[/]"
            bt.add_row(
                b.carrier, b.profile_id, str(b.datasets), state, b.stopped_at or "[green]-[/]"
            )
        console.print(bt)
        console.print(
            f"[dim]Reported on [/][cyan]{bindings[0].venue if bindings else '?'}[/]"
            "[dim]. The two machines hold different subsets, so a verdict is only "
            "meaningful beside the venue that produced it (J18).[/]"
            if bindings
            else ""
        )
        console.print(
            "[dim]not-configured-on-this-machine = the profile is declared and its "
            "variables are unset HERE. That is a STATE, never a defect: --check does not "
            "fail on it, because the other machine configures a different subset and "
            "scoring its bindings red would make this report noise.[/]"
        )
        console.print(
            "[dim]not-built-yet = the binding resolves and the pipeline downstream of it "
            "does not exist yet. Also a state — most of the registry is mid-lifecycle by "
            "design, and N12 (f) already rules that `manual` is the expected first state "
            "and never debt to eliminate.[/]"
        )
        console.print(
            "[dim]Nothing here tests your .env. The walk starts at the REGISTRATION and "
            "runs downstream; it never asserts a variable holds a CORRECT host and never "
            "probes a credential (ADR 0017 clause 7).[/]"
        )
        if unbound:
            console.print(
                f"[dim]{len(unbound)} carrier(s) declare NO binding, each with its reason "
                "in source-bindings.yaml `unbound:` — declared absence, not silence. "
                "A system in neither list is a test failure.[/]"
            )

    # A zone INSIDE the tree is a standing defect regardless of --check: it is
    # reachable by `git clean -fdx` no matter what .gitignore says. Both
    # declarations are checked -- the hazard is the resolved path, not the file
    # that declared it.
    exposed = [
        s.zone.source_id for s in statuses if s.zone.base == "data_root" and s.zone.inside_repo
    ]
    exposed += [s.zone.id for s in declared if s.zone.base == "data_root" and s.zone.inside_repo]
    if exposed:
        console.print(
            f"[red]{len(exposed)} data_root zone(s) resolve INSIDE the repo tree "
            f"({', '.join(exposed)}) — DRYDOCS_DATA_ROOT is pointed at the working "
            "tree, so a port-time clean can delete them.[/]"
        )
        raise typer.Exit(2)

    # G125: a MALFORMED binding is a defect regardless of --check, the same way an
    # in-tree zone is. It means a committed declaration cannot be resolved at all
    # -- not that this machine has not configured it.
    broken = [b.carrier for b in bindings if b.is_failure]
    if broken:
        console.print(
            f"[red]{len(broken)} binding(s) are malformed and cannot resolve "
            f"({', '.join(broken)}) — this is the declaration, not your environment.[/]"
        )
        raise typer.Exit(2)

    if check:
        emptied = [s.zone.source_id for s in statuses if s.empty]
        emptied += [s.zone.id for s in declared if s.empty and s.zone.mode == ZONE_READ]
        if emptied:
            console.print(
                f"[yellow]{len(emptied)} zone(s) exist but are empty: " f"{', '.join(emptied)}[/]"
            )
            raise typer.Exit(1)


@app.command()
def bootstrap(
    skip_constraints: bool = typer.Option(False),
    skip_ontology: bool = typer.Option(False),
) -> None:
    """Apply M0 constraints + ontology seed."""
    with _client() as cli:
        if not cli.apoc_available():
            console.print("[red]APOC required.[/]")
            raise typer.Exit(2)
        if not skip_constraints:
            cli.execute_file(CONSTRAINTS_FILE)
            # D8 guard: execute_file raising is not enough — a silent DDL
            # no-op (the pre-D5 apoc.cypher.runMany class) "succeeds" while
            # creating nothing. Assert every declared name is now present.
            declared = declared_constraint_names(CONSTRAINTS_FILE)
            present = cli.constraint_names()
            missing = [n for n in declared if n not in present]
            if missing:
                console.print(
                    f"[red]Constraint guard: {len(missing)} of {len(declared)} declared "
                    f"constraints absent after apply: {', '.join(missing)} — the apply "
                    "did not take. Nothing further runs.[/]"
                )
                raise typer.Exit(2)
            console.print(
                f"[green]Constraints applied ({len(declared)}/{len(declared)} declared present).[/]"
            )
        if not skip_ontology:
            cli.execute_file(ONTOLOGY_FILE)
            console.print("[green]Ontology seed applied.[/]")


@app.command()
def bootstrap_schema_graph(
    database: str = typer.Option(SCHEMA_GRAPH_DATABASE, help="target database for the meta-graph"),
) -> None:
    """Apply the schema meta-graph (labels + relationship types) to its OWN database.

    TWO DIFFERENT GRAPHS (SME 2026-08-02). This one describes the declared
    vocabulary — one exemplar node per label, one exemplar edge per vocabulary
    entry — so `CALL db.schema.visualization()` draws the schema. The `drydocs`
    graph holds code and operational rows. Their constraints are not the same
    constraints, which is why this is a separate verb against a separate target
    rather than a step inside `bootstrap`: every exemplar carries the REAL label
    beside :SchemaMeta, so running it against `drydocs` violates controlmjob_key
    (a NODE KEY enforces existence; the exemplar carries only `name`).
    """
    with _client(database=database) as cli:
        cli.execute_file(SCHEMA_GRAPH_FILE)
        # Same D8 guard as bootstrap: a silent DDL/data no-op "succeeds" while
        # writing nothing, which is this repo's most-repeated defect class.
        n = cli.run("MATCH (n:SchemaMeta) RETURN count(n) AS n")[0]["n"]
        if not n:
            console.print(
                f"[red]Schema meta-graph guard: 0 :SchemaMeta nodes in '{database}' after "
                "apply — the apply did not take.[/]"
            )
            raise typer.Exit(2)
        console.print(f"[green]Schema meta-graph applied to '{database}' ({n} label nodes).[/]")


@app.command()
def verify() -> None:
    """Report ontology-term counts (M0 verification)."""
    with _client() as cli:
        rows = cli.run("""
            MATCH (n:OntologyTerm)
            UNWIND labels(n) AS lbl
            WITH lbl WHERE lbl <> 'OntologyTerm'
            RETURN lbl AS source_label, count(*) AS terms
            ORDER BY source_label
        """)
    t = Table(title="Ontology terms by source")
    t.add_column("Label")
    t.add_column("Terms", justify="right")
    for r in rows:
        t.add_row(r["source_label"], str(r["terms"]))
    console.print(t)


@app.command()
def reset(yes: bool = typer.Option(False, "--yes")) -> None:
    """DETACH DELETE every node + relationship. DESTRUCTIVE."""
    if not yes:
        if not typer.confirm("Delete EVERY node and relationship?", default=False):
            raise typer.Exit(0)
    with _client() as cli:
        cli.run("MATCH (n) DETACH DELETE n")
    console.print("[green]Database wiped.[/]")


@app.command(name="sweep-removed")
def sweep_removed_cmd(
    days: int = typer.Option(
        30, "--days", help="Retention window: only marks OLDER than this are swept."
    ),
    label: list[str] = typer.Option(
        ["ControlMJob", "ControlMFolder"],
        "--label",
        help="Node label(s) to sweep (repeatable). Defaults to the labels the " "loaders mark.",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Count what WOULD be swept; delete nothing."
    ),
    yes: bool = typer.Option(False, "--yes", help="Skip the confirmation prompt."),
) -> None:
    """Hard-delete nodes soft-marked removed-from-source past retention (D7).

    Loads never delete: an ingest whose extract no longer carries a node only
    MARKS it (removed_from_source_at + removed_by_run_id, within the extract's
    declared scope). This command is the second half — DETACH DELETE marks
    older than the retention window, reporting swept/retained per label.
    DESTRUCTIVE unless --dry-run.
    """
    from .loaders.base import sweep_removed

    if not dry_run and not yes:
        if not typer.confirm(
            f"Hard-delete nodes marked removed-from-source > {days} days ago?",
            default=False,
        ):
            raise typer.Exit(0)
    t = Table(title=f"sweep-removed (window: {days} days{', DRY RUN' if dry_run else ''})")
    t.add_column("Label")
    t.add_column("Swept" if not dry_run else "Would sweep", justify="right")
    t.add_column("Retained (still marked)", justify="right")
    with _client() as cli:
        for lbl in label:
            counts = sweep_removed(cli, lbl, older_than_days=days, dry_run=dry_run)
            t.add_row(lbl, str(counts["swept"]), str(counts["retained"]))
    console.print(t)


# --- shared load command -----------------------------------------------------
