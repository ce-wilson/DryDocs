"""drydocs CLI — M0 + M1 + M3 (part 1) entry point.

This file SUPERSEDES the M1 cli.py.  Strict superset — every M0/M1 command
still works; M3 commands are additive.

  M3 (part 1)
  -----------
  drydocs ingest-controlm     load folders then jobs against samples or Oracle
  drydocs apply-m3-supplement add Control-M local-namespace anchor terms
  drydocs m3-verify           assert M3 (part 1) invariants
"""
from __future__ import annotations

import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .adapters import CsvAdapter, OracleAdapter
from .config import load_settings
from .loaders import seal_applications as seal_apps_mod
from .loaders import seal_contacts as seal_contacts_mod
from .loaders.business_segments import refresh_business_segments
from .loaders.catalog import (
    CatalogLOBsLoader,
    DevTeamsLoader,
    ProductLinesLoader,
    ProductsLoader,
)
from .loaders.controlm_folders import ControlMFoldersLoader
from .loaders.controlm_jobs import ControlMJobsLoader
from .neo4j_client import Neo4jClient
from .snapshots import SnapshotWriter

app = typer.Typer(no_args_is_help=True, rich_markup_mode="rich")
console = Console()
LOGGER = logging.getLogger("drydocs.cli")

SCHEMA_DIR = Path(__file__).resolve().parent / "schema"
CONSTRAINTS_FILE = SCHEMA_DIR / "constraints.cypher"
ONTOLOGY_FILE = SCHEMA_DIR / "ontology.cypher"
M1_ROLE_VOCAB_UPGRADE = SCHEMA_DIR / "m1_role_vocabulary_update.cypher"
M3_SUPPLEMENT_FILE = SCHEMA_DIR / "m3_ontology_supplement.cypher"
M3_CONSTRAINTS_UPGRADE = SCHEMA_DIR / "m3_constraints_upgrade.cypher"

LOADER_REGISTRY: dict[str, type] = {
    "seal_applications":  seal_apps_mod.SealApplicationsLoader,
    "seal_contacts":      seal_contacts_mod.SealContactsLoader,
    "catalog_lobs":       CatalogLOBsLoader,
    "product_lines":      ProductLinesLoader,
    "products":           ProductsLoader,
    "dev_teams":          DevTeamsLoader,
    # M3 (part 1):
    "controlm_folders":   ControlMFoldersLoader,
    "controlm_jobs":      ControlMJobsLoader,
}


# --- helpers -----------------------------------------------------------------

def _client() -> Neo4jClient:
    cfg, _, _ = load_settings()
    pw = cfg.password.get_secret_value()
    if not pw:
        console.print("[red]NEO4J_PASSWORD is empty.[/]")
        raise typer.Exit(2)
    return Neo4jClient(cfg.uri, cfg.user, pw, cfg.database)


def _csv_adapter(csv_path: Path) -> CsvAdapter:
    if not csv_path.exists():
        console.print(f"[red]CSV not found: {csv_path}[/]")
        raise typer.Exit(2)
    return CsvAdapter(csv_path)


def _oracle_adapter(query: str) -> OracleAdapter:
    _, oracle_cfg, _ = load_settings()
    if not oracle_cfg.configured:
        console.print("[red]Oracle not configured.[/]")
        raise typer.Exit(2)
    return OracleAdapter(
        user=oracle_cfg.user,
        password=oracle_cfg.password.get_secret_value(),
        dsn=oracle_cfg.dsn,
        query=query,
    )


# --- callback ---------------------------------------------------------------

@app.callback()
def main(verbose: bool = typer.Option(False, "--verbose", "-v")) -> None:
    """DryDocs — production support inventory + data product KG."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


# --- M0 commands -------------------------------------------------------------

@app.command()
def check() -> None:
    """Verify Neo4j connectivity, server version, and APOC availability."""
    with _client() as cli:
        console.print(f"[cyan]Server:[/] {cli.server_version()}")
        if not cli.apoc_available():
            console.print("[red]APOC not available.[/]"); raise typer.Exit(2)
        console.print("[green]APOC OK.[/]")


@app.command()
def bootstrap(
    skip_constraints: bool = typer.Option(False),
    skip_ontology: bool = typer.Option(False),
) -> None:
    """Apply M0 constraints + ontology seed."""
    with _client() as cli:
        if not cli.apoc_available():
            console.print("[red]APOC required.[/]"); raise typer.Exit(2)
        if not skip_constraints:
            cli.execute_file(CONSTRAINTS_FILE)
            console.print("[green]Constraints applied.[/]")
        if not skip_ontology:
            cli.execute_file(ONTOLOGY_FILE)
            console.print("[green]Ontology seed applied.[/]")


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
    t.add_column("Label"); t.add_column("Terms", justify="right")
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


# --- shared load command -----------------------------------------------------

@app.command()
def load(
    name: str = typer.Argument(..., help=f"Loader: {', '.join(LOADER_REGISTRY)}"),
    csv_path: Path | None = typer.Option(None, "--csv"),
    sql: str | None = typer.Option(None, "--sql"),
    batch_size: int = typer.Option(1000, "--batch-size"),
) -> None:
    """Run a single loader against a CSV or Oracle source."""
    cls = LOADER_REGISTRY.get(name)
    if cls is None:
        console.print(f"[red]Unknown loader: {name}[/]"); raise typer.Exit(2)
    if csv_path is not None:
        adapter = _csv_adapter(csv_path)
    elif sql is not None:
        adapter = _oracle_adapter(sql)
    else:
        console.print("[red]Provide either --csv or --sql.[/]"); raise typer.Exit(2)
    with _client() as cli:
        summary = cls(cli, adapter, batch_size=batch_size).load()
    console.print(summary.as_dict())


# --- M1 commands -------------------------------------------------------------

@app.command(name="refresh-reference")
def refresh_reference(
    samples_dir: Path = typer.Option(Path("data/samples"), "--samples-dir"),
    snapshot: bool = typer.Option(True),
) -> None:
    """M1 reference-refresh chain (catalog + SEAL + dev teams). Weekly cadence."""
    chain = [
        ("catalog_lobs",      CatalogLOBsLoader,             "catalog_lobs__sample.csv"),
        ("product_lines",     ProductLinesLoader,            "product_lines__sample.csv"),
        ("products",          ProductsLoader,                "products__sample.csv"),
        ("seal_applications", seal_apps_mod.SealApplicationsLoader,
                              "seal_application_data__sample.csv"),
        ("seal_contacts",     seal_contacts_mod.SealContactsLoader,
                              "seal_contact_data__sample.csv"),
        ("dev_teams",         DevTeamsLoader,                "dev_teams__sample.csv"),
    ]
    with _client() as cli:
        bs = refresh_business_segments(cli)
        console.print(f"[cyan]Business segments active: {bs['codes']}[/]")
        for nm, cls, sample_csv in chain:
            sample = samples_dir / sample_csv
            if not sample.exists():
                console.print(f"[yellow]No sample for {nm}; skipping.[/]"); continue
            console.print(f"[cyan]>> {nm}[/]")
            summary = cls(cli, _csv_adapter(sample)).load()
            console.print(
                f"   rows={summary.rows_processed} rejected={summary.rows_rejected}"
            )
        if snapshot:
            console.print("[cyan]>> snapshots[/]")
            console.print(SnapshotWriter(cli).write_all())


@app.command(name="m1-verify")
def m1_verify() -> None:
    """Assert M1 invariants on the populated graph."""
    with _client() as cli:
        rows = cli.run("""
            MATCH (a:Application)
            OPTIONAL MATCH (a)-[:HAS_PORT]->(ep:EventProcessing)
            OPTIONAL MATCH (a)-[:HAS_PORT]->(bp:BatchProcessing)
            RETURN count(a) AS apps, count(ep) AS ep, count(bp) AS bp
        """)
    r = rows[0] if rows else {"apps": 0, "ep": 0, "bp": 0}
    ok = r["apps"] == r["ep"] == r["bp"]
    console.print(f"apps have both ports: {'yes' if ok else 'NO'} (apps={r['apps']})")
    if not ok:
        raise typer.Exit(1)


# --- M3 commands -------------------------------------------------------------

@app.command(name="apply-m3-supplement")
def apply_m3_supplement() -> None:
    """Apply the Control-M ontology supplement (idempotent).

    Adds local-namespace anchor terms (:ControlMServer, :JobFolder,
    :ControlMJob) and wires them via :SUBCLASS_OF to the PROV anchors M0
    seeded. Safe to re-run.
    """
    if not M3_SUPPLEMENT_FILE.exists():
        console.print(f"[red]Missing: {M3_SUPPLEMENT_FILE}[/]"); raise typer.Exit(1)
    with _client() as cli:
        cli.execute_file(M3_SUPPLEMENT_FILE)
    console.print("[green]M3 ontology supplement applied.[/]")
    if M1_ROLE_VOCAB_UPGRADE.exists():
    cli.execute_file(M1_ROLE_VOCAB_UPGRADE)
    console.print("[green]Role vocabulary aligned to SEAL spec.[/]")


@app.command(name="ingest-controlm")
def ingest_controlm(
    samples_dir: Path = typer.Option(
        Path("data/samples"),
        "--samples-dir",
        help="Directory holding controlm_folders__sample.csv + controlm_jobs__sample.csv.",
    ),
    use_oracle: bool = typer.Option(
        False,
        "--use-oracle",
        help="Run against psgmgr.CM_DEF_VTAB + psgmgr.CM_DEF_VJOB instead of samples.",
    ),
    folders_sql_path: Path = typer.Option(
        Path(__file__).resolve().parent / "loaders" / "sql" / "controlm_folders.sql",
        "--folders-sql",
    ),
    jobs_sql_path: Path = typer.Option(
        Path(__file__).resolve().parent / "loaders" / "sql" / "controlm_jobs.sql",
        "--jobs-sql",
    ),
) -> None:
    """M3 part 1: load Control-M folders then jobs.

    Order is enforced — jobs MATCH their parent folder by folder_id.
    Run nightly in production; ad-hoc against samples in dev.
    """
    with _client() as cli:
        # Folders first.
        if use_oracle:
            sql = folders_sql_path.read_text(encoding="utf-8")
            adapter = _oracle_adapter(sql)
        else:
            sample = samples_dir / "controlm_folders__sample.csv"
            adapter = _csv_adapter(sample)
        console.print("[cyan]>> controlm_folders[/]")
        summary = ControlMFoldersLoader(cli, adapter).load()
        console.print(
            f"   rows={summary.rows_processed} rejected={summary.rows_rejected}"
        )

        # Then jobs.
        if use_oracle:
            sql = jobs_sql_path.read_text(encoding="utf-8")
            adapter = _oracle_adapter(sql)
        else:
            sample = samples_dir / "controlm_jobs__sample.csv"
            adapter = _csv_adapter(sample)
        console.print("[cyan]>> controlm_jobs[/]")
        summary = ControlMJobsLoader(cli, adapter).load()
        console.print(
            f"   rows={summary.rows_processed} rejected={summary.rows_rejected}"
        )


@app.command(name="m3-verify")
def m3_verify() -> None:
    """Assert M3 (part 1) invariants on the populated graph."""
    checks = []
    with _client() as cli:
        # Every folder has a server.
        rows = cli.run("""
            MATCH (f:JobFolder)
            OPTIONAL MATCH (f)-[:RUNS_ON]->(srv:ControlMServer)
            WITH count(f) AS folders, count(srv) AS srv_links
            RETURN folders, srv_links
        """)
        if rows:
            r = rows[0]
            checks.append((
                "every folder has a server",
                r["folders"] == r["srv_links"],
                f"folders={r['folders']} srv_links={r['srv_links']}",
            ))

        # Every job has a folder.
        rows = cli.run("""
            MATCH (j:ControlMJob)
            OPTIONAL MATCH (f:JobFolder)-[:CONTAINS_JOB]->(j)
            WITH count(j) AS jobs, count(f) AS with_folder
            RETURN jobs, with_folder
        """)
        if rows:
            r = rows[0]
            checks.append((
                "every job has a folder",
                r["jobs"] == r["with_folder"],
                f"jobs={r['jobs']} with_folder={r['with_folder']}",
            ))

        # Composite key sanity — no duplicate (job_id, version_serial).
        rows = cli.run("""
            MATCH (j:ControlMJob)
            WITH j.job_id AS jid, j.version_serial AS vs, count(*) AS n
            WHERE n > 1
            RETURN count(*) AS dupes
        """)
        if rows:
            checks.append((
                "no duplicate (job_id, version_serial)",
                rows[0]["dupes"] == 0,
                f"dupes={rows[0]['dupes']}",
            ))

        # SchedulerKind ControlM exists.
        rows = cli.run("MATCH (k:SchedulerKind {name:'ControlM'}) RETURN count(k) AS n")
        if rows:
            checks.append((
                "ControlM SchedulerKind seeded",
                rows[0]["n"] == 1,
                f"n={rows[0]['n']}",
            ))

        # Local-namespace anchor terms present (post supplement).
        rows = cli.run("""
            MATCH (n:OntologyTerm:LocalClass)
            WHERE n.iri STARTS WITH 'https://drydocs.local/ontology#'
              AND n.iri ENDS WITH 'JobFolder'
               OR n.iri ENDS WITH 'ControlMJob'
               OR n.iri ENDS WITH 'ControlMServer'
            RETURN count(DISTINCT n) AS n
        """)
        if rows:
            checks.append((
                "M3 local anchor terms seeded",
                rows[0]["n"] >= 3,
                f"n={rows[0]['n']} (expect >= 3 after apply-m3-supplement)",
            ))

        # Every active folder has at least one active job (sample-friendly bound).
        rows = cli.run("""
            MATCH (f:JobFolder {active: true})
            OPTIONAL MATCH (f)-[:CONTAINS_JOB]->(j:ControlMJob)
            WITH f, count(j) AS jc
            RETURN sum(CASE WHEN jc = 0 THEN 1 ELSE 0 END) AS empty_folders,
                   count(f) AS total
        """)
        if rows:
            r = rows[0]
            checks.append((
                "active folders contain at least one job",
                r["empty_folders"] == 0,
                f"empty={r['empty_folders']} total={r['total']}",
            ))

    t = Table(title="M3 (part 1) invariants")
    t.add_column("Check"); t.add_column("OK", justify="center"); t.add_column("Detail")
    failed = 0
    for name, ok, detail in checks:
        t.add_row(name, "yes" if ok else "NO", detail)
        if not ok:
            failed += 1
    console.print(t)
    if failed:
        console.print(f"[red]{failed} invariant(s) failed.[/]"); raise typer.Exit(1)
    console.print("[green]All M3 (part 1) invariants passed.[/]")


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


if __name__ == "__main__":
    app()
