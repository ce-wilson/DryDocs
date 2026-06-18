"""drydocs CLI — entry point for all bootstrap, supplement, and ingest commands.

Bootstrap order (first run):
  1. drydocs bootstrap                  — constraints + ontology backbone
  2. drydocs apply-ontology-supplement  — Control-M local anchor terms
  3. drydocs apply-seal-supplement      — SEAL domain terms
  4. drydocs apply-catalog-supplement   — Catalog/PAT domain terms + all Role seeds

Ingest commands:
  drydocs refresh-reference   — catalog + SEAL weekly refresh chain
  drydocs ingest-controlm     — Control-M chain (folders → jobs → conditions → deps)
  drydocs load <name> --csv   — single loader against a CSV file
"""
from __future__ import annotations

import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .adapters import CsvAdapter, OracleAdapter
from .config import load_settings
from .controlm import (
    VariableCoverage,
    classify_job_variables,
    resolve_job,
)
from .controlm.staging import build_staging_bundle, collect_jobs
from .models import ControlMVariableRow
from .loaders import seal_applications as seal_apps_mod
from .loaders import seal_contacts as seal_contacts_mod
from .loaders.base import BaseLoader
from .loaders.business_segments import refresh_business_segments
from .loaders.catalog import (
    AreaProductsLoader,
    CatalogLOBsLoader,
    DevTeamsLoader,
    PatProductMappingLoader,
    PatTeamRolesLoader,
    ProductLinesLoader,
    ProductsLoader,
)
from .loaders.controlm_conditions_in import ControlMConditionsInLoader
from .loaders.controlm_conditions_out import ControlMConditionsOutLoader
from .loaders.controlm_dependencies_derived import ControlMDependenciesDerivedLoader
from .loaders.controlm_folders import ControlMFoldersLoader
from .loaders.controlm_jobs import ControlMJobsLoader
from .neo4j_client import Neo4jClient
from .snapshots import SnapshotWriter

app = typer.Typer(no_args_is_help=True, rich_markup_mode="rich")
console = Console()
LOGGER = logging.getLogger("drydocs.cli")

SCHEMA_DIR = Path(__file__).resolve().parent / "schema"
CONSTRAINTS_FILE        = SCHEMA_DIR / "constraints.cypher"
ONTOLOGY_FILE           = SCHEMA_DIR / "ontology.cypher"
ONTOLOGY_SUPPLEMENT_FILE = SCHEMA_DIR / "ontology_supplement.cypher"
SEAL_SUPPLEMENT_FILE    = SCHEMA_DIR / "seal_ontology_supplement.cypher"
CATALOG_SUPPLEMENT_FILE = SCHEMA_DIR / "catalog_ontology_supplement.cypher"

# Bundled CSV samples ship inside the package so dev-mode commands work
# from any cwd — including from an installed wheel where there is no repo
# root. Override with --samples-dir to point at an alternate fixture set.
DEFAULT_SAMPLES_DIR = Path(__file__).resolve().parent / "data" / "samples"

LOADER_REGISTRY: dict[str, type] = {
    "seal_applications":  seal_apps_mod.SealApplicationsLoader,
    "seal_contacts":      seal_contacts_mod.SealContactsLoader,
    "catalog_lobs":       CatalogLOBsLoader,
    "product_lines":      ProductLinesLoader,
    "products":           ProductsLoader,
    "dev_teams":          DevTeamsLoader,
    # PAT (catalog expansion):
    "area_products":          AreaProductsLoader,
    "pat_product_mapping":    PatProductMappingLoader,
    "pat_team_roles":         PatTeamRolesLoader,
    # M3 (part 1):
    "controlm_folders":   ControlMFoldersLoader,
    "controlm_jobs":      ControlMJobsLoader,
    # M3 (part 2):
    "controlm_conditions_in":       ControlMConditionsInLoader,
    "controlm_conditions_out":      ControlMConditionsOutLoader,
    "controlm_dependencies_derived": ControlMDependenciesDerivedLoader,
}

SQL_DIR = Path(__file__).resolve().parent / "loaders" / "sql"


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


def _oracle_adapter(query: str, bind_params: dict | None = None) -> OracleAdapter:
    _, oracle_cfg, _ = load_settings()
    if not oracle_cfg.configured:
        console.print("[red]Oracle not configured.[/]")
        raise typer.Exit(2)
    return OracleAdapter(
        user=oracle_cfg.user,
        password=oracle_cfg.password.get_secret_value(),
        dsn=oracle_cfg.dsn,
        query=query,
        bind_params=bind_params,
    )


def _scope_binds(
    folder: str | None = None,
    run_as: str | None = None,
    row_cap: int | None = None,
) -> dict:
    """Build the standard psgmgr-extract scope binds.

    Every Control-M extract SQL accepts these `:bind` names with NULL-tolerant
    predicates (a None value = no filter on that dimension). Folder-grained
    extracts (folders, conditions) reference only ``folder_filter`` /
    ``row_cap`` and ignore ``run_as`` — python-oracledb drops named binds the
    statement does not use, so the full dict is safe to pass to any extract.

    Employee-SID scoping is intentionally absent here: employee identity is not
    on the definition rows — it lives in the action-audit table
    psgmgr.CM_AUD_ACTS, so it belongs on a future audit extract (configure
    later). ``run_as`` is the tenant FID (service) user the job runs as.
    """
    return {
        "folder_filter": folder,
        "run_as": run_as,
        "row_cap": row_cap,
    }


# Reusable scope CLI options — attach to any command that runs a psgmgr extract.
_SCOPE_HELP = "psgmgr scope (Oracle only); omit for the full population."
def _folder_opt():
    return typer.Option(None, "--folder", help=f"Folder-name LIKE pattern, e.g. 'CCB_AUTO_%'. {_SCOPE_HELP}")
def _run_as_opt():
    return typer.Option(None, "--run-as", help=f"Tenant FID (service) user the job runs as — J.OWNER, exact. {_SCOPE_HELP}")
def _row_cap_opt():
    return typer.Option(None, "--row-cap", help=f"Unordered ROWNUM sample cap. {_SCOPE_HELP}")


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
    samples_dir: Path = typer.Option(
        DEFAULT_SAMPLES_DIR,
        "--samples-dir",
        help="Directory holding the *__sample.csv fixtures. Defaults to the bundled package samples.",
    ),
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

@app.command(name="apply-ontology-supplement")
def apply_ontology_supplement() -> None:
    """Apply the base ontology supplement (idempotent).

    Adds local-namespace anchor terms (:ControlMServer, :JobFolder,
    :ControlMJob) and wires them via :SUBCLASS_OF to the PROV anchors
    seeded by ontology.cypher. Also declares Control-M LocalRelationship
    mappings (SCHEDULED_ON, CONTAINS_JOB, REQUIRES_IN_CONDITION,
    EMITS_OUT_CONDITION, WAS_INFORMED_BY). Safe to re-run.
    """
    if not ONTOLOGY_SUPPLEMENT_FILE.exists():
        console.print(f"[red]Missing: {ONTOLOGY_SUPPLEMENT_FILE}[/]"); raise typer.Exit(1)
    with _client() as cli:
        cli.execute_file(ONTOLOGY_SUPPLEMENT_FILE)
        console.print("[green]Ontology supplement applied.[/]")


@app.command(name="apply-seal-supplement")
def apply_seal_supplement() -> None:
    """Apply the SEAL ontology supplement (idempotent).

    Declares :Application, :Port, :Membership, :Role, :Employee node types
    and their LocalRelationship mappings (HAS_PORT, HAS_MEMBERSHIP, OF_ROLE,
    HELD_BY). Safe to re-run.
    """
    if not SEAL_SUPPLEMENT_FILE.exists():
        console.print(f"[red]Missing: {SEAL_SUPPLEMENT_FILE}[/]"); raise typer.Exit(1)
    with _client() as cli:
        cli.execute_file(SEAL_SUPPLEMENT_FILE)
        console.print("[green]SEAL ontology supplement applied.[/]")


@app.command(name="apply-catalog-supplement")
def apply_catalog_supplement() -> None:
    """Apply the Catalog ontology supplement (idempotent).

    Declares :CatalogLOB, :BusinessSegment, :ProductLine, :Product,
    :DevTeam, :JiraBoard, :AreaProduct node types, PAT relationship
    mappings (HAS_APPLICATION, HAS_AREA_PRODUCT, SUPPORTS), and seeds all
    19 canonical Role nodes (PAT + SEAL).  Safe to re-run.
    """
    if not CATALOG_SUPPLEMENT_FILE.exists():
        console.print(f"[red]Missing: {CATALOG_SUPPLEMENT_FILE}[/]"); raise typer.Exit(1)
    with _client() as cli:
        cli.execute_file(CATALOG_SUPPLEMENT_FILE)
        console.print("[green]Catalog ontology supplement applied.[/]")


@app.command(name="ingest-controlm")
def ingest_controlm(
    samples_dir: Path = typer.Option(
        DEFAULT_SAMPLES_DIR,
        "--samples-dir",
        help=(
            "Directory holding the controlm_*__sample.csv files. Defaults to "
            "the bundled package samples — works from any cwd."
        ),
    ),
    use_oracle: bool = typer.Option(
        False,
        "--use-oracle",
        help="Run against psgmgr views instead of bundled samples.",
    ),
    skip_part2: bool = typer.Option(
        False,
        "--skip-part2",
        help="Stop after folders + jobs (M3 part 1 only).",
    ),
    folder: str | None = _folder_opt(),
    run_as: str | None = _run_as_opt(),
    row_cap: int | None = _row_cap_opt(),
) -> None:
    """M3 chain: folders -> jobs -> conditions in/out -> derived dependencies.

    Order is enforced — jobs MATCH their parent folder by folder_id;
    conditions MATCH their parent job by (folder_id, job_id); derived
    dependencies MATCH both endpoint jobs by the same composite key.

    Run nightly in production; ad-hoc against samples in dev. With
    --use-oracle, --folder / --run-as / --row-cap scope every extract in the
    chain (folder/row-cap apply to all; run-as applies to the job and
    dependency-anchor extracts).
    """
    scope = _scope_binds(folder, run_as, row_cap)
    stages: list[tuple[str, type[BaseLoader], str, str]] = [
        ("controlm_folders",     ControlMFoldersLoader,
         "controlm_folders__sample.csv",      "controlm_folders.sql"),
        ("controlm_jobs",        ControlMJobsLoader,
         "controlm_jobs__sample.csv",         "controlm_jobs.sql"),
    ]
    if not skip_part2:
        stages.extend([
            ("controlm_conditions_in",  ControlMConditionsInLoader,
             "controlm_conditions_in__sample.csv",  "controlm_conditions_in.sql"),
            ("controlm_conditions_out", ControlMConditionsOutLoader,
             "controlm_conditions_out__sample.csv", "controlm_conditions_out.sql"),
            ("controlm_dependencies_derived", ControlMDependenciesDerivedLoader,
             "controlm_dependencies__sample.csv",
             "controlm_dependencies_recursive.sql"),
        ])

    with _client() as cli:
        for stage_name, cls, sample_csv, sql_file in stages:
            if use_oracle:
                sql = (SQL_DIR / sql_file).read_text(encoding="utf-8")
                adapter = _oracle_adapter(sql, scope)
            else:
                sample = samples_dir / sample_csv
                adapter = _csv_adapter(sample)
            console.print(f"[cyan]>> {stage_name}[/]")
            summary = cls(cli, adapter).load()
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
            OPTIONAL MATCH (f)-[:SCHEDULED_ON]->(srv:ControlMServer)
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
        # Parentheses around the OR group — without them, AND binds tighter
        # and the IRI-prefix filter only constrains the JobFolder branch.
        rows = cli.run("""
            MATCH (n:OntologyTerm:LocalClass)
            WHERE n.iri STARTS WITH 'https://drydocs.local/ontology#'
              AND (n.iri ENDS WITH 'JobFolder'
                   OR n.iri ENDS WITH 'ControlMJob'
                   OR n.iri ENDS WITH 'ControlMServer')
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

        # Every :Condition has at least one job referencing it (IN or OUT).
        # Orphans would mean a condition definition without a producer or
        # consumer — meaningless and almost certainly a load bug.
        rows = cli.run("""
            MATCH (c:Condition)
            OPTIONAL MATCH (c)<-[:REQUIRES_IN_CONDITION|EMITS_OUT_CONDITION]-(:ControlMJob)
            WITH c, count(*) AS refs
            RETURN sum(CASE WHEN refs = 0 THEN 1 ELSE 0 END) AS orphan,
                   count(c) AS total
        """)
        if rows:
            r = rows[0]
            checks.append((
                "no orphan conditions",
                r["orphan"] == 0,
                f"orphan={r['orphan']} total={r['total']}",
            ))

        # Every derived :WAS_INFORMED_BY edge must carry recursion_level and
        # dependency_path — those are the cycle-safety and shortest-path
        # provenance fields written by the recursive SQL.
        rows = cli.run("""
            MATCH ()-[r:WAS_INFORMED_BY]->()
            WHERE r.derived = true
            RETURN count(r) AS total,
                   sum(CASE WHEN r.recursion_level IS NULL THEN 1 ELSE 0 END) AS missing_level,
                   sum(CASE WHEN r.dependency_path IS NULL THEN 1 ELSE 0 END) AS missing_path
        """)
        if rows:
            r = rows[0]
            checks.append((
                "WAS_INFORMED_BY edges have recursion_level + path",
                r["missing_level"] == 0 and r["missing_path"] == 0,
                (
                    f"total={r['total']} missing_level={r['missing_level']} "
                    f"missing_path={r['missing_path']}"
                ),
            ))

    t = Table(title="M3 (part 1 + part 2) invariants")
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


@app.command(name="analyze-variables")
def analyze_variables(
    csv_path: Path = typer.Option(
        DEFAULT_SAMPLES_DIR / "controlm_variables__sample.csv",
        "--csv",
        help=(
            "Variable extract. Accepts the formal projection "
            "(controlm_variables.sql) or the raw SQL Developer export "
            "(TABLE_NAME|JOB_NAME|JOB_ID|APPL_TYPE|NAME|VALUE)."
        ),
    ),
    delimiter: str = typer.Option(",", "--delimiter", help="Field delimiter; use '|' for raw exports."),
    use_oracle: bool = typer.Option(
        False, "--use-oracle", help="Run controlm_variables.sql against psgmgr instead of a file."
    ),
    resolve: bool = typer.Option(
        False, "--resolve",
        help="Also run the Phase-B resolver (folder scope -> job scope) and report resolution coverage.",
    ),
    folder: str | None = _folder_opt(),
    run_as: str | None = _run_as_opt(),
    row_cap: int | None = _row_cap_opt(),
) -> None:
    """Variable taxonomy coverage report (no Neo4j required).

    Classifies every variable definition (LITERAL / VAR_REF / SYSTEM_FUNC /
    DYNAMIC_NAME / FLOW_REF / PLUGIN_NS / EMBEDDED_SHELL / SEMANTIC_FACT /
    MALFORMED), confirms _D/_Q/_P environment triplets per job, and prints
    the coverage numbers that validate the taxonomy. With --resolve, each
    job's definitions are resolved under its folder scope (Phase B) and
    resolution coverage is reported. With --use-oracle, --folder / --run-as /
    --row-cap scope the psgmgr extract.
    """
    if use_oracle:
        sql = (SQL_DIR / "controlm_variables.sql").read_text(encoding="utf-8")
        adapter = _oracle_adapter(sql, _scope_binds(folder, run_as, row_cap))
    else:
        adapter = CsvAdapter(csv_path, delimiter=delimiter)
        if not csv_path.exists():
            console.print(f"[red]File not found: {csv_path}[/]")
            raise typer.Exit(2)

    # group definitions per job — env-triplet confirmation needs the
    # sibling variables of the same job
    per_job: dict[tuple, list[tuple[str, str | None]]] = {}
    job_meta: dict[tuple, str] = {}
    folder_headers: set[tuple] = set()
    rejected = 0
    with adapter:
        for raw in adapter.rows():
            try:
                row = ControlMVariableRow.model_validate(raw)
            except Exception:  # noqa: BLE001 — count + continue, like BaseLoader
                rejected += 1
                continue
            dc = row.data_center or "UNKNOWN"
            key = (dc, row.folder_id, row.job_id)
            per_job.setdefault(key, []).append((row.var_name, row.var_value))
            job_meta[key] = dc
            # folder-scope rows: var_scope from the formal projection, or the
            # smart-folder header heuristic (JOB_ID = 1) for raw extracts
            if row.var_scope == "FOLDER" or (row.var_scope is None and row.job_id == "1"):
                folder_headers.add(key)

    cov = VariableCoverage()
    for key, defs in per_job.items():
        for cv in classify_job_variables(defs):
            cov.add(cv, data_center=job_meta[key], job_key=key)

    console.print(
        f"definitions={cov.total} jobs={len(cov.jobs_seen)} rejected={rejected}"
    )

    t = Table(title="Variable kind distribution")
    t.add_column("Kind"); t.add_column("Count", justify="right"); t.add_column("%", justify="right")
    for kind, pct in cov.pct_by_kind.items():
        t.add_row(kind, str(cov.by_kind[kind]), f"{pct:.2f}")
    console.print(t)

    if len(cov.by_dc_kind) > 1:
        t = Table(title="Kind by data center")
        kinds = [k for k, _ in cov.by_kind.most_common()]
        t.add_column("Data center")
        for k in kinds:
            t.add_column(k, justify="right")
        for dc, counter in sorted(cov.by_dc_kind.items()):
            t.add_row(dc, *(str(counter.get(k, 0)) for k in kinds))
        console.print(t)

    for title, counter, n in (
        ("Plugin namespaces", cov.plugin_namespaces, 10),
        ("Semantic fact types", cov.fact_types, 15),
        ("System functions in use", cov.system_funcs, 10),
        ("System variables in use", cov.system_vars, 10),
        ("Most-referenced USER variables (resolution hot set)", cov.referenced_names, 15),
        ("Pool / cross-flow reference targets", cov.flow_targets, 10),
        ("Global variable references", cov.global_targets, 10),
    ):
        if not counter:
            continue
        t = Table(title=title)
        t.add_column("Name"); t.add_column("Count", justify="right")
        for name, cnt in counter.most_common(n):
            t.add_row(name, str(cnt))
        console.print(t)

    if cov.malformed_samples:
        console.print("[yellow]Malformed samples (first "
                      f"{len(cov.malformed_samples)}):[/]")
        for s in cov.malformed_samples:
            console.print(f"  {s}")

    if not resolve:
        return

    # --- Phase B: resolve each job under its folder scope ---
    from collections import Counter as _Counter

    folder_defs: dict[tuple, list[tuple[str, str | None]]] = {
        (k[0], k[1]): defs for k, defs in per_job.items() if k in folder_headers
    }
    total = fully = with_variants = with_externals = 0
    unresolved_names: "_Counter[str]" = _Counter()
    max_depth_seen = 0
    for key, defs in per_job.items():
        if key in folder_headers:
            # the header IS the folder scope — resolve it standalone
            rvs = resolve_job(defs, [])
        else:
            # resolve under the folder scope, but count only this job's own
            # definitions (the folder rows are counted on the header)
            fdefs = folder_defs.get((key[0], key[1]), [])
            rvs = [rv for rv in resolve_job(fdefs, defs) if rv.scope == "JOB"]
        for rv in rvs:
            total += 1
            fully += rv.is_fully_resolved
            with_variants += bool(rv.variants)
            with_externals += bool(rv.external_refs)
            max_depth_seen = max(max_depth_seen, rv.resolution_depth)
            for u in rv.unresolved:
                unresolved_names[u] += 1

    t = Table(title="Phase-B resolution coverage")
    t.add_column("Metric"); t.add_column("Value", justify="right")
    t.add_row("definitions resolved", str(total))
    t.add_row("fully resolved", f"{fully} ({100 * fully / total:.1f}%)" if total else "0")
    t.add_row("with env variants", str(with_variants))
    t.add_row("with external (global/pool) refs", str(with_externals))
    t.add_row("max substitution depth", str(max_depth_seen))
    console.print(t)

    if unresolved_names:
        t = Table(title="Top unresolved names (runtime-provided candidates)")
        t.add_column("Name"); t.add_column("Count", justify="right")
        for name, cnt in unresolved_names.most_common(15):
            t.add_row(name, str(cnt))
        console.print(t)


@app.command(name="normalize-variables")
def normalize_variables(
    csv_path: Path = typer.Option(
        DEFAULT_SAMPLES_DIR / "controlm_variables__sample.csv",
        "--csv",
        help="Variable extract (formal projection or raw SQL Developer export).",
    ),
    delimiter: str = typer.Option(",", "--delimiter", help="Field delimiter; use '|' for raw exports."),
    use_oracle: bool = typer.Option(
        False, "--use-oracle", help="Run controlm_variables.sql against psgmgr instead of a file."
    ),
    out_dir: Path = typer.Option(
        Path("stg_out"), "--out-dir",
        help="Output directory for the STG_* load files.",
    ),
    folder: str | None = _folder_opt(),
    run_as: str | None = _run_as_opt(),
    row_cap: int | None = _row_cap_opt(),
) -> None:
    """Classify + resolve the variable extract and emit staging load files.

    Writes stg_variable.csv, stg_parse_quality.csv, and stg_run.csv with
    columns matching controlm_staging_ddl.sql exactly — load them into the
    DRYDOCS_STG schema via SQL Developer import or SQL*Loader. No database
    write access required from this command. With --use-oracle, --folder /
    --run-as / --row-cap scope the extract (handy for fresh samples from a
    single folder or run-as FID).
    """
    import csv as _csv
    import uuid
    from datetime import datetime, timezone

    if use_oracle:
        sql = (SQL_DIR / "controlm_variables.sql").read_text(encoding="utf-8")
        adapter = _oracle_adapter(sql, _scope_binds(folder, run_as, row_cap))
    else:
        if not csv_path.exists():
            console.print(f"[red]File not found: {csv_path}[/]")
            raise typer.Exit(2)
        adapter = CsvAdapter(csv_path, delimiter=delimiter)

    started_at = datetime.now(timezone.utc)
    run_id = str(uuid.uuid4())
    rejected = 0

    def _validated():
        nonlocal rejected
        for raw in adapter.rows():
            try:
                yield ControlMVariableRow.model_validate(raw)
            except Exception:  # noqa: BLE001 — count + continue, like BaseLoader
                rejected += 1

    with adapter:
        jobs = collect_jobs(_validated())
    bundle = build_staging_bundle(jobs, run_id)
    ended_at = datetime.now(timezone.utc)

    run_row = {
        "run_id": run_id,
        "started_at": started_at.strftime("%Y-%m-%d %H:%M:%S"),
        "ended_at": ended_at.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "SUCCEEDED",
        "data_centers": ",".join(sorted({jd.data_center for jd in jobs.values()})),
        "src_job_count": len(jobs),
        "src_var_count": sum(len(jd.defs) for jd in jobs.values()),
        "normalizer_version": "phase-c.1",
        "notes": f"source={'oracle' if use_oracle else csv_path.name}; rejected={rejected}",
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    tables = (
        ("stg_run.csv", [run_row]),
        ("stg_variable.csv", bundle.variable),
        ("stg_parse_quality.csv", bundle.parse_quality),
        ("stg_invocation.csv", bundle.invocation),
        ("stg_file_op.csv", bundle.file_op),
        ("stg_file_ref.csv", bundle.file_ref),
        ("stg_notification.csv", bundle.notification),
        ("stg_app_fact.csv", bundle.app_fact),
    )
    for name, rows in tables:
        path = out_dir / name
        if not rows:
            console.print(f"[yellow]{path} (0 rows — skipped)[/]")
            continue
        with open(path, "w", encoding="utf-8", newline="") as fh:
            writer = _csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        console.print(f"[green]{path}[/] ({len(rows)} rows)")

    fully = sum(1 for r in bundle.variable if r["is_fully_resolved"] == "Y")
    console.print(
        f"run_id={run_id} jobs={len(jobs)} definitions={run_row['src_var_count']} "
        f"variable={len(bundle.variable)} invocation={len(bundle.invocation)} "
        f"file_op={len(bundle.file_op)} file_ref={len(bundle.file_ref)} "
        f"notification={len(bundle.notification)} app_fact={len(bundle.app_fact)} "
        f"fully_resolved={100 * fully / len(bundle.variable):.1f}% rejected={rejected}"
    )


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
