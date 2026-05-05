"""drydocs CLI — entry point.

M0 commands:

- ``drydocs check``      verify Neo4j connection + APOC presence
- ``drydocs bootstrap``  apply constraints + ontology seed
- ``drydocs verify``     report ontology counts so the bootstrap is provable
- ``drydocs reset``      DETACH DELETE everything (DESTRUCTIVE — confirmation required)
"""
from __future__ import annotations

import logging
from pathlib import Path

import typer
from neo4j.exceptions import AuthError
from rich.console import Console
from rich.table import Table

from .config import load_settings
from .neo4j_client import Neo4jClient

app = typer.Typer(no_args_is_help=True, rich_markup_mode="rich")
console = Console()
LOGGER = logging.getLogger("drydocs.cli")

SCHEMA_DIR = Path(__file__).resolve().parent / "schema"
CONSTRAINTS_FILE = SCHEMA_DIR / "constraints.cypher"
ONTOLOGY_FILE = SCHEMA_DIR / "ontology.cypher"


def _client() -> Neo4jClient:
    neo4j_cfg, _, _ = load_settings()
    pw = neo4j_cfg.password.get_secret_value()
    if not pw:
        console.print("[red]NEO4J_PASSWORD is empty. Set it in .env or environment.[/]")
        raise typer.Exit(2)
    return Neo4jClient(neo4j_cfg.uri, neo4j_cfg.user, pw, neo4j_cfg.database)


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", is_flag=True, help="Debug logging."),
) -> None:
    """DryDocs — production support inventory + data product KG."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


@app.command()
def check() -> None:
    """Verify Neo4j connectivity, server version, and APOC availability."""
    client = _client()
    info = client.connection_info()
    console.print(f"[cyan]Connecting to:[/] {info['uri']}")
    console.print(f"[cyan]User:[/]         {info['user']}")
    console.print(f"[cyan]Database:[/]     {info['database']}")
    try:
        with client as cli:
            console.print(f"[cyan]Server:[/]       {cli.server_version()}")
            if not cli.apoc_available():
                console.print(
                    "[red]APOC not available.[/] Install the APOC plugin "
                    "(Neo4j Desktop -> plugins; Aura -> APOC procedures already "
                    "enabled; on-prem -> add to neo4j.conf)."
                )
                raise typer.Exit(2)
            console.print("[green]APOC OK.[/]")
    except AuthError as exc:
        console.print(f"[red]Authentication failed for user '{info['user']}' on {info['uri']}.[/]")
        console.print("[yellow]Check NEO4J_USER and NEO4J_PASSWORD in your .env file.[/]")
        LOGGER.debug("AuthError detail: %s", exc)
        raise typer.Exit(2) from exc


@app.command()
def bootstrap(
    skip_constraints: bool = typer.Option(False, help="Skip applying constraints."),
    skip_ontology: bool = typer.Option(False, help="Skip applying ontology seed."),
) -> None:
    """Apply M0 constraints + ontology seed. Idempotent."""
    if not CONSTRAINTS_FILE.exists():
        console.print(f"[red]Missing: {CONSTRAINTS_FILE}[/]")
        raise typer.Exit(1)
    if not ONTOLOGY_FILE.exists():
        console.print(f"[red]Missing: {ONTOLOGY_FILE}[/]")
        raise typer.Exit(1)

    with _client() as cli:
        if not cli.apoc_available():
            console.print("[red]APOC required for bootstrap.[/] Run `drydocs check`.")
            raise typer.Exit(2)

        if not skip_constraints:
            console.print(f"[cyan]Applying {CONSTRAINTS_FILE.name}...[/]")
            cli.execute_file(CONSTRAINTS_FILE)
            console.print("[green]Constraints applied.[/]")

        if not skip_ontology:
            console.print(f"[cyan]Applying {ONTOLOGY_FILE.name}...[/]")
            cli.execute_file(ONTOLOGY_FILE)
            console.print("[green]Ontology seed applied.[/]")

    console.print("[bold green]M0 bootstrap complete.[/]")


@app.command()
def verify() -> None:
    """Report ontology-term counts and key seed nodes."""
    with _client() as cli:
        # Ontology terms by source label.
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

        # Seed instance counts.
        seeds = cli.run("""
            CALL () {
              MATCH (r:Role) RETURN 'Role' AS k, count(*) AS n
              UNION ALL
              MATCH (k:SchedulerKind) RETURN 'SchedulerKind' AS k, count(*) AS n
              UNION ALL
              MATCH (s:BusinessSegment) RETURN 'BusinessSegment' AS k, count(*) AS n
              UNION ALL
              MATCH (d:Dimension) RETURN 'Dimension' AS k, count(*) AS n
              UNION ALL
              MATCH (m:Metric) RETURN 'Metric' AS k, count(*) AS n
              UNION ALL
              MATCH (a:Agent) RETURN 'Agent' AS k, count(*) AS n
            }
            RETURN k, n ORDER BY k
        """)
        t2 = Table(title="Seed instance counts")
        t2.add_column("Kind")
        t2.add_column("Count", justify="right")
        for r in seeds:
            t2.add_row(r["k"], str(r["n"]))
        console.print(t2)

        # Constraint count (sanity check).
        c_rows = cli.run("SHOW CONSTRAINTS YIELD name RETURN count(*) AS n")
        console.print(f"[cyan]Constraints in db:[/] {c_rows[0]['n']}")


@app.command()
def reset(
    yes: bool = typer.Option(False, "--yes", help="Skip confirmation."),
) -> None:
    """DETACH DELETE every node + relationship. DESTRUCTIVE."""
    if not yes:
        confirm = typer.confirm(
            "This will delete EVERY node and relationship in the database. Continue?",
            default=False,
        )
        if not confirm:
            console.print("[yellow]Reset cancelled.[/]")
            raise typer.Exit(0)
    with _client() as cli:
        cli.run("MATCH (n) DETACH DELETE n")
        console.print("[green]Database wiped. Run `drydocs bootstrap` to re-seed.[/]")


if __name__ == "__main__":
    app()