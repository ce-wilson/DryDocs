"""drydocs CLI — entry point for all bootstrap, supplement, and ingest commands.

Bootstrap order (first run):
  1. drydocs bootstrap           — constraints + ontology backbone
  2. drydocs apply-supplements   — the whole ordered supplement chain
                                   (base -> seal -> catalog -> registry), each
                                   one verified against the terms its .cypher
                                   declares. The chain is DATA:
                                   drydocs_core.schema.supplements.SUPPLEMENTS.

Optional / experimental:
  drydocs apply-supplements --with-sosa — EARLY ADOPTION: also apply the
                                  SOSA/SSN observation+temporal terms for the
                                  layer-4 context graph. NOT a declared company
                                  standard; never in the default chain.

The per-supplement verbs (apply-ontology-supplement, apply-seal-supplement,
apply-catalog-supplement, apply-registry-supplement, apply-sosa-supplement)
still work — since G29 they are thin aliases that delegate into the same
chain runner, so they too verify and write a run log.

Ingest commands:
  drydocs refresh-reference       — catalog + SEAL weekly refresh chain
  drydocs ingest-controlm         — Control-M chain (folders → jobs → conditions → deps)
  drydocs load <name> --csv       — single loader against a CSV file
  drydocs load-software-registry  — third-party software registry from
                                    config/taxonomy/software-registry.yaml
  drydocs load-batch-orchestrators — C14: declared batch-port orchestrator
                                    strings -> USES_SOFTWARE {source:'batch-port'}
  drydocs load-bmc-docs           — bmc-docs lexical graph (Document -> Chunk)
                                    from external/orchestration/bmc-controlm/
  drydocs load-essential-graphrag — Essential GraphRAG ebook lexical graph
                                    (Q2 experiment; local gitignored PDF)
  drydocs load-folder-attribution — K8: app-code defined mapping + the K2
                                    fallback -> folder BELONGS_TO_APPLICATION
                                    {role: seal_app_ref} edges onto Batch Ports
  drydocs load-manual-mappings    — tier-5 SME-authored mapping CSV
                                    (config/manual-loads/, PIN semantics)
  drydocs load-code-snapshot      — G33 self-documentation: newest depgraph
                                    snapshot -> :Project / :CodeModule subgraph
  drydocs export-cmdline-staging  — G39: graph :ControlMJob rows -> the
                                    TEMPORARY job-detail staging store (SQLite
                                    under DRYDOCS_DATA_ROOT; stand-in for the
                                    unbuilt psgmgr CM_DEF_VJOB_DETAIL table)
  drydocs resolve-cmdline-staging — G48: XML-staged variables -> the store's
                                    cmd_line_resolved column via the ONE
                                    shared resolver (verbatim kept beside it)
  drydocs parse-cmdline-staging   — G40: staged cmd_lines -> structured detail
                                    columns (G26 registry + G15 DPL contract);
                                    NO graph writes — G22 gates any load
  drydocs patch-window            — P5: best patch window for a host/host
                                    group (READ-ONLY; quiet windows = the
                                    complement of the busy UNION — critical
                                    path, never a path sum) + the
                                    NODE_GROUP<->RUNS_ON metadata findings
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

import drydocs_core
from drydocs_core.adapters import CsvAdapter, OracleAdapter
from drydocs_core.config import load_settings
from drydocs_core.models import ControlMVariableRow
from drydocs_core.neo4j_client import Neo4jClient
from drydocs_core.orchestration.controlm import (
    VariableCoverage,
    classify_job_variables,
    resolve_job,
)
from drydocs_core.run_log import LoaderRunLog
from drydocs_core.schema.constraints import declared_constraint_names
from drydocs_core.schema.supplements import (
    BY_NAME as SUPPLEMENTS_BY_NAME,
)
from drydocs_core.schema.supplements import (
    SUPPLEMENTS,
    Supplement,
    declared_terms,
    default_chain,
)
from drydocs_core.source_registry import (
    RetiredSourceIdError,
    SourceRegistry,
    UnconfirmedSourceError,
    UnknownSourceError,
)

from .docs_verify import Summary as DocsVerifySummary
from .docs_verify import exit_code as docs_verify_exit_code
from .docs_verify import verify as verify_corpora
from .loaders import seal_applications as seal_apps_mod
from .loaders import seal_contacts as seal_contacts_mod
from .loaders.base import BaseLoader
from .loaders.batch_port_orchestrator import (
    DEFAULT_APPS_PATH,
    DEFAULT_PLATFORMS_PATH,
    BatchOrchestratorYamlAdapter,
    BatchPortOrchestratorLoader,
)
from .loaders.bmc_docs import (
    DEFAULT_CORPUS_DIR,
    BmcDocsAdapter,
    BmcDocsLoader,
)
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
from .loaders.code_snapshot import (
    DEFAULT_SNAPSHOT_DIR,
    CodeSnapshotAdapter,
    CodeSnapshotError,
    CodeSnapshotLoader,
    select_newest_snapshot,
)
from .loaders.controlm_conditions_in import ControlMConditionsInLoader
from .loaders.controlm_conditions_out import ControlMConditionsOutLoader
from .loaders.controlm_dependencies_derived import ControlMDependenciesDerivedLoader
from .loaders.controlm_folders import ControlMFoldersLoader
from .loaders.controlm_hosts import ControlMHostsLoader
from .loaders.controlm_jobs import ControlMJobsLoader
from .loaders.doc_traceability import (
    DEFAULT_DESIGN_DIR,
    DEFAULT_FEEDBACK_DIR,
    DesignDocFeedbackAdapter,
    DesignDocSectionsAdapter,
    DesignDocSectionsLoader,
    DocFeedbackLoader,
    DocTraceabilityLoader,
    TraceabilityMatrixAdapter,
)
from .loaders.essential_graphrag import (
    DEFAULT_PDF,
    EssentialGraphragAdapter,
    EssentialGraphragLoader,
)
from .loaders.folder_attribution import (
    FolderAttributionAdapter,
    FolderAttributionLoader,
    check_folder_preconditions,
    fetch_folder_codes,
    fetch_pinned_folders,
)
from .loaders.manual_loads import (
    ManualLoadError,
    ManualMappingAdapter,
    ManualSealAttributionLoader,
    mapping_rows,
)
from .loaders.patch_window import PatchWindowQuery
from .loaders.runs_on_resolution import RunsOnResolutionPass
from .loaders.seal_attribution import (
    TierReconcilers,
    fetch_app_name_reconciler,
)
from .loaders.software_registry import (
    DEFAULT_REGISTRY_PATH,
    RegistryYamlAdapter,
    SoftwareRegistryLoader,
)
from .loaders.vendor_docs import VendorDocsLoader
from .snapshots import SnapshotWriter
from .staging import build_staging_bundle, collect_jobs

app = typer.Typer(no_args_is_help=True, rich_markup_mode="rich")
console = Console()
LOGGER = logging.getLogger("drydocs.cli")

SCHEMA_DIR = Path(drydocs_core.__file__).resolve().parent / "schema"
CONSTRAINTS_FILE = SCHEMA_DIR / "constraints.cypher"
ONTOLOGY_FILE = SCHEMA_DIR / "ontology.cypher"
# The schema meta-graph is a SEPARATE GRAPH with separate constraints (SME
# 2026-08-02), so it carries its own target rather than following NEO4J_DATABASE.
SCHEMA_GRAPH_FILE = SCHEMA_DIR / "schema_graph.cypher"
SCHEMA_GRAPH_DATABASE = "ddschema"
# The supplement .cypher paths are NOT constants here — they live in the
# registry (drydocs_core.schema.supplements), so the chain and its order have
# exactly one home. G29.

# Bundled CSV samples ship inside the package so dev-mode commands work
# from any cwd — including from an installed wheel where there is no repo
# root. Override with --samples-dir to point at an alternate fixture set.
DEFAULT_SAMPLES_DIR = Path(__file__).resolve().parent / "data" / "samples"

LOADER_REGISTRY: dict[str, type] = {
    "seal_applications": seal_apps_mod.SealApplicationsLoader,
    "seal_contacts": seal_contacts_mod.SealContactsLoader,
    "catalog_lobs": CatalogLOBsLoader,
    "product_lines": ProductLinesLoader,
    "products": ProductsLoader,
    "dev_teams": DevTeamsLoader,
    # PAT (catalog expansion):
    "area_products": AreaProductsLoader,
    "pat_product_mapping": PatProductMappingLoader,
    "pat_team_roles": PatTeamRolesLoader,
    # M3 (part 1):
    "controlm_folders": ControlMFoldersLoader,
    "controlm_jobs": ControlMJobsLoader,
    # M3 (part 2):
    "controlm_conditions_in": ControlMConditionsInLoader,
    "controlm_conditions_out": ControlMConditionsOutLoader,
    "controlm_dependencies_derived": ControlMDependenciesDerivedLoader,
    # P3 (host topology; gate controlm-hosts-topology):
    "controlm_hosts": ControlMHostsLoader,
    # bmc-docs lexical graph (Document -> Chunk):
    "bmc_docs": BmcDocsLoader,
    # Essential GraphRAG ebook lexical graph (Q2 experiment):
    "essential_graphrag": EssentialGraphragLoader,
    # Doc traceability + review feedback (L7 connector #1):
    "doc_sections": DesignDocSectionsLoader,
    "doc_traceability": DocTraceabilityLoader,
    "doc_feedback": DocFeedbackLoader,
}

SQL_DIR = Path(__file__).resolve().parent / "loaders" / "sql"

# Which source-registry entry each loader draws from. The confirmed-gate (D3)
# uses this to refuse a loader whose source's crosswalk is not SME-confirmed.
# DERIVED since N3: each loader class declares its own `source_id` — this dict
# is a projection of those declarations, never hand-maintained (a re-hardcoded
# entry here would be a drift bug; test_load_map_declarations guards the tie).
# Note the bmc-docs nuance survives the derivation: until a source is
# SME-confirmed, `_gate_source` fails fast (exit 2) — correct, not a bug.
LOADER_SOURCE: dict[str, str] = {
    cli_name: cls.source_id
    for cli_name, cls in LOADER_REGISTRY.items()
    if cls.source_id is not None
}

# ---- N3: the load map's three declared joins --------------------------------
# (1) loader -> source_id lives ON each loader class (BaseLoader.source_id);
# (2) command -> loaders, in run order, is COMMAND_LOADERS below (the chain
#     constants are consumed by the command bodies, so the declaration cannot
#     drift from behavior);
# (3) the ONE canonical ordered load sequence is CANONICAL_LOAD_SEQUENCE.
# All three are guarded by tests/unit/test_load_map_declarations.py and joined
# into web/src/generated/load-map.json by the N4 render.

# Loaders with deliberately NO source-registry id — every entry needs a written
# reason (silent omissions are the defect this exists to end).
SOURCELESS_LOADERS: dict[type, str] = {
    ManualSealAttributionLoader: (
        "SME-authored tier-5 mapping CSVs gated by config/manual-loads/"
        "manifest.yaml (gate seal-attribution-match-policy §F) — a human "
        "source with its own manifest governance, not a registry feed"
    ),
}

# The M1 reference-refresh chain (weekly cadence): (cli name, loader class,
# bundled sample filename). Order matters — hierarchy parents before children,
# SEAL apps before contacts, mapping last.
REFRESH_REFERENCE_CHAIN: tuple[tuple[str, type, str], ...] = (
    ("catalog_lobs", CatalogLOBsLoader, "catalog_lobs__sample.csv"),
    ("product_lines", ProductLinesLoader, "product_lines__sample.csv"),
    ("products", ProductsLoader, "products__sample.csv"),
    (
        "seal_applications",
        seal_apps_mod.SealApplicationsLoader,
        "seal_application_data__sample.csv",
    ),
    ("seal_contacts", seal_contacts_mod.SealContactsLoader, "seal_contact_data__sample.csv"),
    ("dev_teams", DevTeamsLoader, "dev_teams__sample.csv"),
    ("pat_product_mapping", PatProductMappingLoader, "pat_product_mapping__sample.csv"),
)

# The M3 ingest-controlm stages: (cli name, loader class, sample csv, sql file).
# Order is enforced — jobs MATCH their parent folder; conditions MATCH their
# parent job; the deferred dependency pass MATCHes both endpoints (two-phase
# contract). PART2 extends NODE when --skip-part2 is not set.
CONTROLM_NODE_STAGES: tuple[tuple[str, type, str, str], ...] = (
    (
        "controlm_folders",
        ControlMFoldersLoader,
        "controlm_folders__sample.csv",
        "controlm_folders.sql",
    ),
    ("controlm_jobs", ControlMJobsLoader, "controlm_jobs__sample.csv", "controlm_jobs.sql"),
)
CONTROLM_PART2_STAGES: tuple[tuple[str, type, str, str], ...] = (
    (
        "controlm_conditions_in",
        ControlMConditionsInLoader,
        "controlm_conditions_in__sample.csv",
        "controlm_conditions_in.sql",
    ),
    (
        "controlm_conditions_out",
        ControlMConditionsOutLoader,
        "controlm_conditions_out__sample.csv",
        "controlm_conditions_out.sql",
    ),
    # P3 host topology (gate controlm-hosts-topology): independent of
    # folders/jobs — CM_HOSTS has no folder/owner/author grain, so the scope
    # binds don't apply and the extract is always a full snapshot.
    ("controlm_hosts", ControlMHostsLoader, "controlm_hosts__sample.csv", "controlm_hosts.sql"),
)
CONTROLM_REL_STAGES: tuple[tuple[str, type, str, str], ...] = (
    (
        "controlm_dependencies_derived",
        ControlMDependenciesDerivedLoader,
        "controlm_dependencies__sample.csv",
        "controlm_dependencies_recursive.sql",
    ),
)

# The L7 doc-traceability chain: (loader class, adapter class, which directory
# option feeds it). Three passes in a fixed order — sections, then matrix rows
# (sections MATCHed, never MERGEd), then feedback.
DOC_TRACEABILITY_CHAIN: tuple[tuple[type, type, str], ...] = (
    (DesignDocSectionsLoader, DesignDocSectionsAdapter, "design"),
    (DocTraceabilityLoader, TraceabilityMatrixAdapter, "design"),
    (DocFeedbackLoader, DesignDocFeedbackAdapter, "feedback"),
)

# (2) Command -> the loaders it runs, in order. Derived from the chain
# constants above wherever a chain exists, so declaration == behavior.
COMMAND_LOADERS: dict[str, tuple[type, ...]] = {
    "refresh-reference": tuple(cls for _, cls, _ in REFRESH_REFERENCE_CHAIN),
    "ingest-controlm": tuple(
        cls for _, cls, *_ in CONTROLM_NODE_STAGES + CONTROLM_PART2_STAGES + CONTROLM_REL_STAGES
    ),
    "load-software-registry": (SoftwareRegistryLoader,),
    "load-batch-orchestrators": (BatchPortOrchestratorLoader,),
    "load-code-snapshot": (CodeSnapshotLoader,),
    "load-bmc-docs": (BmcDocsLoader,),
    "load-vendor-docs": (VendorDocsLoader,),
    "load-doc-traceability": tuple(cls for cls, _, _ in DOC_TRACEABILITY_CHAIN),
    "load-essential-graphrag": (EssentialGraphragLoader,),
    "load-folder-attribution": (FolderAttributionLoader,),
    "load-manual-mappings": (ManualSealAttributionLoader,),
}

# Loader-running commands that are OPERATOR-DRIVEN, not sequence members:
# `load` runs any single LOADER_REGISTRY loader ad hoc; manual mappings load
# when an SME authors one (manifest-gated), not on a refresh cadence.
AD_HOC_COMMANDS: frozenset[str] = frozenset({"load", "load-manual-mappings"})

# (3) THE canonical ordered load sequence — declared once; ingest.sh and the
# startup/refresh runbook derive from it (N6 retires their independent copies).
# mode: "standing" = every full refresh; "optional" = site/experiment decision;
# "gated" = blocked on a source confirmation or precondition named in the note.
CANONICAL_LOAD_SEQUENCE: tuple[tuple[str, str, str], ...] = (
    ("check", "standing", "Neo4j + APOC reachable"),
    ("bootstrap", "standing", "constraints + ontology seed"),
    (
        "bootstrap-schema-graph",
        "standing",
        "schema meta-graph rendered + applied to ddschema (C21/G51). Targets a "
        "DIFFERENT database, so it is chain-independent of everything below and "
        "could sit anywhere — it sits here because a wiped DBMS is exactly when "
        "the meta-graph gets forgotten. ADDED 2026-08-04: it was already in both "
        "operator surfaces (scripts/ingest.sh step 3/6 and the startup runbook's "
        "Appendix B) and missing ONLY here, so the generated load-map published "
        "15 steps while both real paths ran 16",
    ),
    ("apply-supplements", "standing", "the ONE verified supplement chain (G29)"),
    ("refresh-reference", "standing", "catalog + SEAL + dev teams (M1)"),
    ("ingest-controlm", "standing", "folders -> jobs -> conditions -> derived deps (M3)"),
    ("load-software-registry", "standing", "vendor/product registry (plan 07)"),
    (
        "load-batch-orchestrators",
        "optional",
        "declared batch-port USES_SOFTWARE edges (C14); MATCH-only — needs the "
        "SEAL chain and the software registry already loaded",
    ),
    ("load-bmc-docs", "standing", "BMC corpus lexical graph"),
    (
        "load-vendor-docs",
        "optional",
        "Q13 captured vendor documentation (verbatim, out-of-repo capture -> "
        "convert -> load); taxonomy only, gated until its corpus is confirmed",
    ),
    ("load-essential-graphrag", "optional", "Q2 experiment -> ddcontext database"),
    ("load-doc-traceability", "optional", "L7 self-documentation (design docs + feedback)"),
    (
        "load-code-snapshot",
        "optional",
        "G33 self-documentation; ritual-driven (newest committed snapshot)",
    ),
    (
        "load-folder-attribution",
        "gated",
        "K8 folder-grain attribution: the app-code defined mapping "
        "(config/overrides/app-code-mappings.csv) + the stg_app_fact fallback "
        "feed need ingest-controlm + refresh-reference first (gate §E "
        "preconditions)",
    ),
    ("m1-verify", "standing", "M1 invariants"),
    ("m3-verify", "standing", "M3 invariants"),
    (
        "docs-verify",
        "standing",
        "doc corpora declared vs loaded (registry-driven; non-zero on wrong-db)",
    ),
)


# --- helpers -----------------------------------------------------------------

_registry: SourceRegistry | None = None


def _source_registry() -> SourceRegistry:
    global _registry
    if _registry is None:
        _registry = SourceRegistry.from_yaml()
    return _registry


def _gate_source(source_id: str) -> None:
    """Confirmed-gate (D3): fail fast (exit 2) unless the source is SME-confirmed."""
    try:
        _source_registry().require_confirmed(source_id)
    except (UnconfirmedSourceError, UnknownSourceError, RetiredSourceIdError) as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(2) from exc


def _gate_loader(cls: type) -> None:
    """Confirmed-gate for a LOADER: gate the dataset id the loader actually
    binds to — the per-side overlay entry when one exists (D2,
    config/loader-source-overlay.yaml wins over the class default), else the
    class's own N3 ``source_id`` declaration."""
    effective = _source_registry().effective_source_id(cls.name, cls.source_id)
    if effective is not None:
        _gate_source(effective)


def _client(database: str | None = None) -> Neo4jClient:
    """Build the Neo4j client from settings; ``database`` overrides the
    configured target DB (e.g. ``ddcontext`` for context-graph loads)."""
    cfg, _, _ = load_settings()
    pw = cfg.password.get_secret_value()
    if not pw:
        console.print("[red]NEO4J_PASSWORD is empty.[/]")
        raise typer.Exit(2)
    return Neo4jClient(cfg.uri, cfg.user, pw, database or cfg.database)


def _csv_adapter(csv_path: Path) -> CsvAdapter:
    if not csv_path.exists():
        console.print(f"[red]CSV not found: {csv_path}[/]")
        raise typer.Exit(2)
    return CsvAdapter(csv_path)


def _oracle_adapter(
    query: str, bind_params: dict | None = None, name: str | None = None
) -> OracleAdapter:
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
        name=name,
    )


def _scope_binds(
    folder: str | None = None,
    run_as: str | None = None,
    developer_sid: str | None = None,
    row_cap: int | None = None,
) -> dict:
    """Build the standard psgmgr-extract scope binds.

    NULL-tolerant: a None value = no filter on that dimension. Folder-grained
    extracts (folders, conditions) ignore ``run_as``; python-oracledb drops
    named binds a statement does not use, so the full dict is safe everywhere.

      folder_filter  folder-name LIKE pattern
      run_as         tenant FID (service) user the job runs as — J.OWNER
      developer_sid  human developer who authored/changed the definition;
                     matched on J.AUTHOR / J.CREATION_USER / J.CHANGE_USERID
                     (jobs) and T.LAST_UPDATED_USER (folders/conditions),
                     joined back to the employee hierarchy. Control-M SIDs
                     start with a lowercase letter; a SID ending in lowercase
                     'p' is the automation release process, not a person.
      row_cap        unordered ROWNUM sample cap

    Operational employee identity (who *ran* actions, vs who authored the
    definition) is separate and not here — it lives in psgmgr.CM_AUD_ACTS;
    wire it on a future audit extract.
    """
    return {
        "folder_filter": folder,
        "run_as": run_as,
        "developer_sid": developer_sid,
        "row_cap": row_cap,
    }


# Reusable scope CLI options — attach to any command that runs a psgmgr extract.
_SCOPE_HELP = "psgmgr scope (Oracle only); omit for the full population."


def _folder_opt():
    return typer.Option(
        None, "--folder", help=f"Folder-name LIKE pattern, e.g. 'CCB_AUTO_%'. {_SCOPE_HELP}"
    )


def _run_as_opt():
    return typer.Option(
        None,
        "--run-as",
        help=f"Tenant FID (service) user the job runs as — J.OWNER, exact. {_SCOPE_HELP}",
    )


def _developer_sid_opt():
    return typer.Option(
        None,
        "--developer-sid",
        help=f"Developer SID who authored/changed the def — J.AUTHOR/CREATION_USER/CHANGE_USERID or folder LAST_UPDATED_USER. {_SCOPE_HELP}",
    )


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
            console.print("[red]APOC not available.[/]")
            raise typer.Exit(2)
        console.print("[green]APOC OK.[/]")


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
        console.print(f"[red]Unknown loader: {name}[/]")
        raise typer.Exit(2)
    if name in LOADER_SOURCE:
        _gate_loader(cls)  # confirmed-gate (overlay-aware, D2) before any DB write
    if csv_path is not None:
        adapter = _csv_adapter(csv_path)
    elif sql is not None:
        adapter = _oracle_adapter(sql)
    else:
        console.print("[red]Provide either --csv or --sql.[/]")
        raise typer.Exit(2)
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
    # Confirmed-gate (D3): every feed the chain touches must be SME-confirmed
    # before any write — derived from the chain's own source_id declarations
    # (overlay-aware per D2).
    for cls in {cls for _, cls, _ in REFRESH_REFERENCE_CHAIN}:
        _gate_loader(cls)
    with _client() as cli:
        bs = refresh_business_segments(cli)
        console.print(f"[cyan]Business segments active: {bs['codes']}[/]")
        for nm, cls, sample_csv in REFRESH_REFERENCE_CHAIN:
            sample = samples_dir / sample_csv
            if not sample.exists():
                console.print(f"[yellow]No sample for {nm}; skipping.[/]")
                continue
            console.print(f"[cyan]>> {nm}[/]")
            summary = cls(cli, _csv_adapter(sample)).load()
            console.print(f"   rows={summary.rows_processed} rejected={summary.rows_rejected}")
        if snapshot:
            console.print("[cyan]>> snapshots[/]")
            console.print(SnapshotWriter(cli).write_all())


@app.command(name="m1-verify")
def m1_verify() -> None:
    """Assert M1 invariants on the populated graph."""
    with _client() as cli:
        # G33 §F1 (gate self-documentation-code-graph): :CodeModule and
        # :SoftwareProduct are two kinds of 'software' in one database and must
        # never co-label a node. Neo4j cannot declare label mutual-exclusion,
        # so the invariant lives here as a graph-test (0 also passes on a graph
        # with no code snapshot loaded — vacuously true, deliberately).
        colabeled = cli.run("""
            MATCH (n:CodeModule:SoftwareProduct)
            RETURN count(n) AS n
        """)
        # Scoped to SEAL-loaded apps (a.source = 'SEAL'): port data comes from the
        # SEAL extract only. Anchor apps MERGEd by attribution edges (e.g. the C9
        # pat mapping's seal_ids, a.source = 'pat') are legitimately port-less
        # until the SEAL extract covers them.
        rows = cli.run("""
            MATCH (a:BusinessApplication) WHERE a.source = 'SEAL'
            OPTIONAL MATCH (a)-[:HAS_PORT]->(ep:EventProcessing)
            OPTIONAL MATCH (a)-[:HAS_PORT]->(bp:BatchProcessing)
            RETURN count(a) AS apps, count(ep) AS ep, count(bp) AS bp
        """)
        # C9 (gate 2026-07-18): the home-product SUPPORTS edge is fallback-only.
        # An unsponsored DevTeam->Product edge beside an unsponsored
        # DevTeam->AreaProduct alignment restates the row join (C5 rule) — the
        # loader never writes it and the migration removed the pre-C9 ones.
        restate = cli.run("""
            MATCH (dt:DevTeam)-[r:SUPPORTS]->(:Product)
            WHERE coalesce(r.sponsored, false) = false
              AND EXISTS {
                MATCH (dt)-[r2:SUPPORTS]->(:AreaProduct)
                WHERE coalesce(r2.sponsored, false) = false
              }
            RETURN count(r) AS n
        """)
    r = rows[0] if rows else {"apps": 0, "ep": 0, "bp": 0}
    ok = r["apps"] == r["ep"] == r["bp"]
    console.print(f"apps have both ports: {'yes' if ok else 'NO'} (apps={r['apps']})")
    n_restate = restate[0]["n"] if restate else 0
    ok2 = n_restate == 0
    console.print(
        f"no join-restating DevTeam->Product SUPPORTS: {'yes' if ok2 else 'NO'} (found={n_restate})"
    )
    n_colabeled = colabeled[0]["n"] if colabeled else 0
    ok3 = n_colabeled == 0
    console.print(
        f"no :CodeModule+:SoftwareProduct co-labeling (G33 §F1): "
        f"{'yes' if ok3 else 'NO'} (found={n_colabeled})"
    )
    if not (ok and ok2 and ok3):
        raise typer.Exit(1)


# --- ontology supplements (G29: one data-driven chain) ------------------------

_TERM_TOTAL = "MATCH (n:OntologyTerm) RETURN count(n) AS n"
_TERMS_PRESENT = "MATCH (n:OntologyTerm) WHERE n.iri IN $iris RETURN count(DISTINCT n.iri) AS n"


def _apply_supplement_chain(chain: tuple[Supplement, ...]) -> None:
    """Apply *chain* in order, verifying each file landed; write a run log.

    Verification is the point. ``execute_file`` raises on a Cypher error, but
    a supplement that is truncated, renamed, or comment-only runs "fine" and
    seeds nothing — which then surfaces hundreds of rows later as a loader
    MATCH that silently matches zero canonical :Role nodes. So after each file
    we assert that every :OntologyTerm IRI the .cypher DECLARES is present in
    the graph, and fail the command if any is missing.

    The total :OntologyTerm count is reported before and after each step. It is
    NOT asserted to increase — supplements are idempotent, so a re-run
    legitimately moves it by zero; the per-file presence check is what carries
    the guarantee.
    """
    missing_paths = [s for s in chain if not s.path.exists()]
    if missing_paths:
        for s in missing_paths:
            console.print(f"[red]Missing: {s.path}[/]")
        raise typer.Exit(1)

    run_id = str(uuid.uuid4())
    results: list[tuple[Supplement, int, int, int, list[str]]] = []
    error: BaseException | None = None
    run_log = LoaderRunLog(
        "supplement",
        run_id,
        source="drydocs_core/schema (" + ", ".join(s.filename for s in chain) + ")",
        target="",
        meta={"chain": " -> ".join(s.name for s in chain)},
    )
    try:
        with _client() as cli:
            run_log.target = (
                f"{cli.connection_info()['uri']} db={cli.connection_info()['database']}"
            )
            try:
                run_log.open()
                run_log.attach()
                LOGGER.info("[run-log] %s", run_log.path)
            except OSError as exc:  # audit trail is never why an apply fails
                LOGGER.warning("supplement run log unavailable (%s) — continuing", exc)

            for supplement in chain:
                before = cli.run(_TERM_TOTAL)[0]["n"]
                cli.execute_file(supplement.path)
                iris = sorted(declared_terms(supplement.path))
                present = cli.run(_TERMS_PRESENT, {"iris": iris})[0]["n"]
                after = cli.run(_TERM_TOTAL)[0]["n"]
                absent = []
                if present != len(iris):
                    found = {
                        r["iri"]
                        for r in cli.run(
                            "MATCH (n:OntologyTerm) WHERE n.iri IN $iris RETURN n.iri AS iri",
                            {"iris": iris},
                        )
                    }
                    absent = [i for i in iris if i not in found]
                    LOGGER.error(
                        "supplement %s: %d of %d declared terms absent after apply",
                        supplement.name,
                        len(absent),
                        len(iris),
                    )
                results.append((supplement, before, after, len(iris), absent))
    except BaseException as exc:
        error = exc
        raise
    finally:
        run_log.close(
            {
                "chain": " -> ".join(s.name for s in chain),
                "supplements applied": len(results),
                "terms verified": sum(r[3] for r in results),
                "terms missing": sum(len(r[4]) for r in results),
                "status": "FAILED" if (error or any(r[4] for r in results)) else "OK",
                **{
                    f"{s.name}: terms/total": f"{declared}/{after} (was {before})"
                    for s, before, after, declared, _ in results
                },
            },
            error=error,
        )

    t = Table(title="apply-supplements")
    t.add_column("Supplement")
    t.add_column("Declared terms", justify="right")
    t.add_column("Verified", justify="right")
    t.add_column("OntologyTerm total", justify="right")
    t.add_column("OK", justify="center")
    failed = 0
    for supplement, before, after, declared, absent in results:
        t.add_row(
            supplement.name,
            str(declared),
            str(declared - len(absent)),
            f"{before} -> {after}",
            "yes" if not absent else "NO",
        )
        failed += bool(absent)
    console.print(t)
    if failed:
        for supplement, _, _, _, absent in results:
            for iri in absent[:10]:
                console.print(f"[red]{supplement.name}: term not in graph after apply — {iri}[/]")
            if len(absent) > 10:
                console.print(f"[red]{supplement.name}: … and {len(absent) - 10} more[/]")
        console.print(f"[red]{failed} supplement(s) did not land.[/]")
        raise typer.Exit(1)
    console.print(f"[green]{len(results)} supplement(s) applied and verified.[/]")


@app.command(name="apply-supplements")
def apply_supplements(
    only: list[str] = typer.Option(
        [],
        "--only",
        help=(
            "Apply just these supplements (repeatable), in the registry's order: "
            + ", ".join(s.name for s in SUPPLEMENTS)
        ),
    ),
    with_sosa: bool = typer.Option(
        False,
        "--with-sosa",
        help="Also apply the EXPERIMENTAL SOSA/SSN supplement (opt-in, not a company standard).",
    ),
) -> None:
    """Apply the ontology supplement chain in order, verified (idempotent).

    Default chain: base -> seal -> catalog -> registry. The order is
    load-bearing — catalog reuses the :Attribution class and #hasAgent term
    that seal declares — and it lives in ONE place,
    ``drydocs_core.schema.supplements.SUPPLEMENTS``.

    Each file is applied, then every :OntologyTerm IRI it declares is checked
    for presence in the graph; a supplement that runs but seeds nothing fails
    the command instead of surfacing later as an empty loader MATCH. The run
    writes a ``load.supplement.<stamp>.log`` envelope to DRYDOCS_LOGDIR.

    Safe to re-run: every supplement is idempotent.
    """
    if only:
        unknown = [n for n in only if n not in SUPPLEMENTS_BY_NAME]
        if unknown:
            console.print(
                f"[red]Unknown supplement(s): {', '.join(unknown)}. "
                f"Known: {', '.join(s.name for s in SUPPLEMENTS)}[/]"
            )
            raise typer.Exit(2)
        # Registry order wins over the order the flags were typed in — the
        # chain's dependencies are why the order exists.
        chain = tuple(s for s in SUPPLEMENTS if s.name in set(only))
    else:
        chain = default_chain()
        if with_sosa:
            chain = (*chain, SUPPLEMENTS_BY_NAME["sosa"])
    _apply_supplement_chain(chain)


def _alias(name: str) -> None:
    """Register the pre-G29 per-supplement verb as a delegating alias."""
    supplement = SUPPLEMENTS_BY_NAME[name]

    def _run() -> None:
        _apply_supplement_chain((supplement,))

    _run.__doc__ = (
        f"{supplement.summary} (idempotent).\n\n"
        f"    Alias for `drydocs apply-supplements --only {name}` — the chain "
        f"    and its order live in drydocs_core.schema.supplements (G29)."
    )
    app.command(name=supplement.legacy_verb)(_run)


for _name in SUPPLEMENTS_BY_NAME:
    _alias(_name)


@app.command(name="load-software-registry")
def load_software_registry(
    registry_path: Path = typer.Option(
        DEFAULT_REGISTRY_PATH,
        "--registry",
        help="Path to software-registry.yaml (defaults to the committed ledger).",
    ),
) -> None:
    """Load the third-party software registry (plan 07 / ADR 0004).

    MERGEs :Vendor and :SoftwareProduct from
    config/taxonomy/software-registry.yaml, attributes products via MADE_BY,
    and wires DryDocs' own stack to the reserved :BusinessApplication node via
    USES_SOFTWARE. Idempotent — the YAML is the source of truth.
    """
    _gate_loader(SoftwareRegistryLoader)  # confirmed-gate (overlay-aware) before any DB write
    if not registry_path.exists():
        console.print(f"[red]Missing: {registry_path}[/]")
        raise typer.Exit(1)
    adapter = RegistryYamlAdapter(registry_path)
    with _client() as cli:
        summary = SoftwareRegistryLoader(cli, adapter).load()
    console.print(summary.as_dict())


@app.command(name="load-batch-orchestrators")
def load_batch_orchestrators(
    apps_path: Path = typer.Option(
        DEFAULT_APPS_PATH,
        "--apps",
        help="Path to business-application.yaml (the SEAL taxonomy capture).",
    ),
    platforms_path: Path = typer.Option(
        DEFAULT_PLATFORMS_PATH,
        "--platforms",
        help="Path to platforms.yaml (the seed-row crosswalk to the registry).",
    ),
) -> None:
    """Load declared batch-port orchestrator edges (backlog C14, gate C12).

    Migrates each app's SEAL-declared batch-port orchestrator string to
    (:BusinessApplication)-[:USES_SOFTWARE {source: 'batch-port'}]->
    (:SoftwareProduct) via the platforms.yaml software_registry_ref crosswalk.
    MATCH-only on both endpoints — run the SEAL chain and
    `drydocs load-software-registry` first. Unmapped strings are REPORTED
    (flagged on the app node + listed below), never guessed.
    """
    _gate_loader(BatchPortOrchestratorLoader)  # confirmed-gate (overlay-aware) before any DB write
    for path in (apps_path, platforms_path):
        if not path.exists():
            console.print(f"[red]Missing: {path}[/]")
            raise typer.Exit(1)
    adapter = BatchOrchestratorYamlAdapter(apps_path, platforms_path)
    with _client() as cli:
        loader = BatchPortOrchestratorLoader(cli, adapter)
        summary = loader.load()
    console.print(summary.as_dict())
    # Coverage report (the invocation-patterns coverage-policy rule: counts
    # always reported, never silent).
    mapped = summary.rows_processed - len(adapter.unmapped)
    console.print(
        f"coverage: {mapped}/{summary.rows_processed} declared strings mapped; "
        f"{adapter.apps_without_declaration} app(s) with no declaration (skipped)"
    )
    for miss in adapter.unmapped:
        console.print(
            f"[yellow]UNMAPPED[/]: app {miss['seal_id']} declares "
            f"'{miss['orchestrator_raw']}' — no software_registry_ref in "
            "platforms.yaml (flagged batch_orchestrator_unmapped; no edge written)"
        )
    # The GRAPH-side view. The block above counts crosswalk hits on the SOURCE
    # side, so on its own it reads "n/n mapped" even when every row missed its
    # app or its product in the database (Q8 family, 2026-07-27).
    for seal_id in loader.apps_not_in_graph:
        console.print(
            f"[red]NOT IN GRAPH[/]: app {seal_id} is declared in the capture but has "
            "no :BusinessApplication node — NOTHING was written for it, not even the "
            "raw string. Re-run the SEAL application load."
        )
    for row in loader.apps_without_edge:
        if row.get("unmapped"):
            continue  # already reported above as a platforms.yaml config gap
        console.print(
            f"[red]PRODUCT MISSING[/]: app {row['seal_id']} declares "
            f"'{row['orchestrator_raw']}' and the crosswalk resolved it, but no "
            "matching :SoftwareProduct is in this database — the registry is "
            "present but incomplete. Re-run `drydocs load-software-registry`."
        )


@app.command(name="load-code-snapshot")
def load_code_snapshot(
    snapshot_dir: Path = typer.Option(
        DEFAULT_SNAPSHOT_DIR,
        "--snapshot-dir",
        help="Directory of dated depgraph snapshots (defaults to knowledge/depgraph-snapshots).",
    ),
    file: Path | None = typer.Option(
        None,
        "--file",
        help="Load this exact snapshot file instead of the newest drydocs-*.json "
        "(still refused unless it carries a `meta` header).",
    ),
) -> None:
    """Load DryDocs' own code snapshot (G33 / Epic U self-documentation).

    MERGEs the newest knowledge/depgraph-snapshots/drydocs-*.json into one
    (:Project {project_id:'drydocs'}) root + :CodeModule nodes (keyed file_id)
    + HAS_MODULE / IMPORTS / IS_ENCODED_IN edges. Idempotent; re-runnable from
    committed files (ADR 0002 D3). abs_path never loads (§H4).

    WHOLE-TREE snapshots are the normal shape (meta.tree == true) since the
    scanner stopped taking a hand-maintained root list; §G1(a)'s "refuse
    tree-mode" ruling was REVERSED by SME direction and refusing it would now
    refuse every snapshot there is. What still gets refused, loudly: a file with
    NO `meta` header at all (the headerless one-off shape §G1 was really
    protecting against — the assertion stays POSITIVE because those files carry
    no `meta`, so a truthiness test on meta.tree would ACCEPT them), and a
    `meta.tree` that is not a boolean. Directories in a tree snapshot are
    counted and reported, never loaded — :Directory and CONTAINS would be a new
    node class and a new edge type, both gate decisions (CLAUDE.md §6).
    """
    _gate_loader(CodeSnapshotLoader)  # confirmed-gate (overlay-aware) before any DB write
    try:
        path = Path(file) if file else select_newest_snapshot(snapshot_dir)
        adapter = CodeSnapshotAdapter(path)
        console.print(f"snapshot: {path.name}")
        with _client() as cli:
            # Every snapshot is a FULL scan of the source tree by construction,
            # so the run declares full_extract: the D7 mark pass flags
            # :CodeModule nodes whose file left the tree between snapshots.
            loader = CodeSnapshotLoader(cli, adapter, full_extract=True)
            summary = loader.load()
    except CodeSnapshotError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(2) from exc
    console.print(summary.as_dict())
    # The adapter's contract says directories are "counted, not dropped in
    # silence — the count is reported by the CLI". It was counted and never
    # printed, so "the tree is not in the graph yet" could only be inferred from
    # a node total nobody checks. Print it and the claim becomes true.
    if adapter.skipped_directories:
        console.print(
            f"[yellow]DIRECTORIES SKIPPED[/]: {adapter.skipped_directories} tree node(s) "
            "of kind 'dir' — :Directory nodes and CONTAINS edges are a gate decision "
            "(CLAUDE.md §6), so the containment tree stays in the snapshot, not the graph"
        )
    # Counts always reported, never silent: extensions with no seeded SWO term
    # load their node fine but skip the IS_ENCODED_IN edge (§E2 partial use).
    for ext, n in sorted(adapter.unmapped_extensions.items()):
        console.print(
            f"[yellow]NO SWO TERM[/]: {n} node(s) with extension '{ext}' — "
            "IS_ENCODED_IN skipped (no seeded SwoClass term; see EXTENSION_LANGUAGE_IRI)"
        )


@app.command(name="patch-window")
def patch_window_cmd(
    host: str = typer.Option(None, "--host", help="ExecutionHost nodeid you want to patch."),
    group: str = typer.Option(None, "--group", help="ControlMHostGroup name you want to patch."),
    database: str = typer.Option(None, "--database", help="Override the configured target DB."),
    as_json: bool = typer.Option(False, "--json", help="Print the report as JSON."),
) -> None:
    """Best patch window for a host or host group (P5 — READ-ONLY).

    Collects every job that can land on the target (2-hop RUNS_ON
    {role: host_group} through CONTAINS_HOST + 1-hop {role: agent_host}),
    places each on the 24h clock from the P4 timing supplement (job
    avg_start_time/avg_run_time, else the folder window rollup), and prints
    the QUIET windows — the busy math is the interval UNION (critical-path
    extent, never a path sum; the standing TDQ-ETA rule). The
    NODE_GROUP<->RUNS_ON cross-validation rides along as a metadata-findings
    list (the remediation feeder). Cypher: drydocs/loaders/cypher/patch_window.cypher.
    """
    if bool(host) == bool(group):
        console.print("[red]Pass exactly one of --host or --group.[/]")
        raise typer.Exit(2)
    mode, target = ("host", host) if host else ("group", group)
    with _client(database) as cli:
        query = PatchWindowQuery(cli)
        if not query.target_exists(mode, target):
            label = "ExecutionHost nodeid" if mode == "host" else "ControlMHostGroup name"
            console.print(f"[red]No {label} {target!r} in the graph.[/]")
            raise typer.Exit(2)
        report = query.run(mode, target)

    if as_json:
        console.print_json(data=report.as_dict())
        return

    jobs_table = Table(title=f"Jobs that can land on {mode} '{target}'")
    for col in ("job", "path", "via", "folder", "window source", "node_id"):
        jobs_table.add_column(col)
    for job in report.jobs:
        via = job.get("pinned_host") or job.get("group_name") or "-"
        jobs_table.add_row(
            str(job.get("job_name") or job.get("job_id") or "?"),
            str(job.get("path")),
            str(via),
            str(job.get("folder") or "-"),
            str(job.get("window_source")),
            str(job.get("node_id") or "-"),
        )
    console.print(jobs_table)

    if report.busy:
        console.print(
            "busy (union — critical-path extent, never a sum): "
            + ", ".join(f"{w['start']}-{w['end']}" for w in report.busy)
        )
    quiet_table = Table(title="Quiet windows (patch candidates, longest first)")
    for col in ("start", "end", "minutes"):
        quiet_table.add_column(col)
    for w in report.quiet:
        quiet_table.add_row(w["start"], w["end"], str(w["minutes"]))
    console.print(quiet_table)
    if report.placeable_jobs == 0:
        console.print(
            "[yellow]CAVEAT[/]: 0 of "
            f"{report.placeable_jobs + report.unplaceable_jobs} job(s) carried "
            "usable timing — the whole day reads quiet. The findings below are "
            "the fix list (the P4 supplement loader is company-side today)."
        )
    console.print(
        f"placed {report.placeable_jobs} job(s), "
        f"unplaceable {report.unplaceable_jobs} — every gap is a finding, never a guess"
    )
    if report.findings:
        findings_table = Table(title="Metadata findings (remediation feeder)")
        for col in ("kind", "subject", "detail"):
            findings_table.add_column(col)
        for f in report.findings:
            findings_table.add_row(f.kind, f.subject, f.detail)
        console.print(findings_table)
    else:
        console.print("no metadata findings — intent and derived topology agree")


@app.command(name="export-cmdline-staging")
def export_cmdline_staging(
    db_path: Path | None = typer.Option(
        None,
        "--db-path",
        help="Store location override (default: <DRYDOCS_DATA_ROOT>/cmdline-staging/job_detail.db).",
    ),
) -> None:
    """G39: materialize the TEMPORARY cmd-line job-detail staging store.

    One row per loaded :ControlMJob — identity keys, task-type discriminator,
    VERBATIM cmd_line — read FROM THE GRAPH (no Oracle needed; the psgmgr
    CM_DEF_VJOB projection for the same shape is documented in the module and
    the store's meta). Stand-in for the unbuilt CM_DEF_VJOB_DETAIL table —
    deleted the day a real one exists. Reads the graph, writes only SQLite.
    """
    from .cmdline_staging import default_db_path, export_job_detail

    path = Path(db_path) if db_path else default_db_path(create=True)
    run_id = str(uuid.uuid4())
    run_log = LoaderRunLog(
        "cmdline_staging_export.v1", run_id, source="graph::ControlMJob", target=str(path)
    )
    run_log.open()
    run_log.attach()
    try:
        with _client() as cli:
            report = export_job_detail(cli, path)
    except Exception as exc:
        run_log.close(error=exc)
        raise
    run_log.close(summary={"store": path, **report.__dict__})
    console.print(f"store: {path}")
    console.print(report.summary())
    if report.jobs == 0:
        console.print(
            "[yellow]0 jobs exported — the target database has no :ControlMJob "
            "rows (wrong DB, or controlm jobs not loaded?)[/]"
        )


@app.command(name="resolve-cmdline-staging")
def resolve_cmdline_staging(
    db_path: Path | None = typer.Option(
        None,
        "--db-path",
        help="Store location override (default: <DRYDOCS_DATA_ROOT>/cmdline-staging/job_detail.db).",
    ),
    xml_source: Path | None = typer.Option(
        None,
        "--xml-source",
        help="Control-M XML export file or directory (default: <DRYDOCS_DATA_ROOT>/controlm-xml/).",
    ),
) -> None:
    """G48: populate cmd_line_resolved from XML-staged variables.

    Extracts a Control-M XML definition export (G47), joins its jobs to the
    staged rows on (data_center, folder_name, job_name), and resolves each
    STORE-VERBATIM cmd_line through the one shared resolver (G46) —
    cmd_line stays untouched beside the derived value; resolution_quality
    records the provenance per job. Run BEFORE parse-cmdline-staging so the
    parse reads resolved text. NO graph writes — G22 remains the terminus.
    """
    from drydocs_core.data_root import controlm_xml_dir
    from drydocs_lineage.extractors import ControlMXmlDefsExtractor

    from .cmdline_staging import (
        CmdlineStagingError,
        default_db_path,
        resolve_job_detail,
    )

    path = Path(db_path) if db_path else default_db_path()
    source = Path(xml_source) if xml_source else controlm_xml_dir()
    if not source.exists():
        console.print(
            f"[red]XML source not found: {source} — land an export "
            "in the controlm-xml/ landing zone or pass --xml-source[/]"
        )
        raise typer.Exit(2)
    run_id = str(uuid.uuid4())
    run_log = LoaderRunLog(
        "cmdline_staging_resolve.v1", run_id, source=str(source), target=str(path)
    )
    run_log.open()
    run_log.attach()
    try:
        extract = ControlMXmlDefsExtractor().extract(source)
        coverage = resolve_job_detail(path, extract)
    except CmdlineStagingError as exc:
        run_log.close(error=exc)
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(2) from exc
    except Exception as exc:
        run_log.close(error=exc)
        raise
    run_log.close(summary={"xml": extract.coverage.as_dict(), "resolution": coverage.__dict__})
    console.print(extract.coverage.summary())
    console.print(coverage.summary())


@app.command(name="parse-cmdline-staging")
def parse_cmdline_staging(
    db_path: Path | None = typer.Option(
        None,
        "--db-path",
        help="Store location override (default: <DRYDOCS_DATA_ROOT>/cmdline-staging/job_detail.db).",
    ),
) -> None:
    """G40: parse staged cmd_lines into structured job-detail columns.

    Shared core parser end to end (G26 launcher registry + G15 DPL arg
    contract incl. the %%VAR-launcher GUID fallback; G16 values-decide).
    Partial/unparsed rows hit the WARN stream and are counted, never dropped.
    NO graph writes — G22 remains the terminus gate for anything entering
    Neo4j.
    """
    from .cmdline_staging import (
        CmdlineStagingError,
        default_db_path,
        parse_job_detail,
    )

    path = Path(db_path) if db_path else default_db_path()
    run_id = str(uuid.uuid4())
    run_log = LoaderRunLog("cmdline_staging_parse.v1", run_id, source=str(path), target=str(path))
    run_log.open()
    run_log.attach()
    try:
        coverage = parse_job_detail(path)
    except CmdlineStagingError as exc:
        run_log.close(error=exc)
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(2) from exc
    except Exception as exc:
        run_log.close(error=exc)
        raise
    run_log.close(summary=coverage.__dict__)
    console.print(coverage.summary())


@app.command(name="load-bmc-docs")
def load_bmc_docs(
    corpus_dir: Path = typer.Option(
        DEFAULT_CORPUS_DIR,
        "--corpus-dir",
        help="Directory of controlm-*.md docs (defaults to external/orchestration/bmc-controlm).",
    ),
) -> None:
    """Load the BMC documentation corpus as a Document -> Chunk lexical graph.

    Manual chunking + MERGE (Neo4j llm-graph-builder pattern) — chunk-only, no
    LLM extraction, no embeddings, fully deterministic. Splits each doc on H2
    headings, classifies every chunk's provenance tier per the
    SOURCE-MANIFEST default tier rule, and wires each :Document to its
    :SoftwareProduct via DESCRIBES (MATCH only — run
    `drydocs load-software-registry` first).
    """
    _gate_loader(
        BmcDocsLoader
    )  # confirmed-gate (overlay-aware; doc-ledger union) before any DB write
    if not corpus_dir.exists():
        console.print(f"[red]Missing: {corpus_dir}[/]")
        raise typer.Exit(1)
    adapter = BmcDocsAdapter(corpus_dir)
    with _client() as cli:
        summary = BmcDocsLoader(cli, adapter).load()
    console.print(summary.as_dict())


@app.command(name="convert-vendor-docs")
def convert_vendor_docs(
    capture_id: str = typer.Argument(..., help="Capture id, e.g. bmc-controlm-9.0.20-utilities."),
    corpus_id: str | None = typer.Option(
        None,
        "--corpus-id",
        help=(
            "doc-source-registry corpus this capture belongs to. Defaults to what the "
            "capture manifest declared, else the registry entry naming this capture."
        ),
    ),
) -> None:
    """Stage 2 of the vendor-docs pipeline: captured HTML -> markdown.

    Reads the capture manifest written by scripts/external_vendor_scrape.py,
    strips the Author-it navigation chrome, normalizes heading levels (they
    encode TOC depth, not importance), derives page_role from an explicit title
    rule, and writes markdown/ + convert-manifest.json beside the capture.
    No graph, no network — safe to re-run.
    """
    from drydocs.loaders.vendor_docs import CorpusNotRegisteredError, convert_capture
    from drydocs_core.data_root import vendor_docs_dir

    base = vendor_docs_dir(capture_id)
    if not (base / "capture-manifest.json").exists():
        console.print(
            f"[red]No capture at {base}[/] — run scripts/external_vendor_scrape.py first."
        )
        raise typer.Exit(1)
    try:
        summary = convert_capture(capture_id, corpus_id=corpus_id)
    except CorpusNotRegisteredError as exc:
        console.print(f"[red]Unregistered corpus:[/] {exc}")
        raise typer.Exit(1) from exc
    console.print(summary.render())


@app.command(name="load-vendor-docs")
def load_vendor_docs(
    capture_id: str = typer.Argument(..., help="Capture id, e.g. bmc-controlm-9.0.20-utilities."),
) -> None:
    """Stage 3: load a converted vendor capture as a navigable Document graph.

    Writes :Document + :Chunk (PART_OF / FIRST_CHUNK / NEXT_CHUNK) and the
    publisher's own TOC hierarchy (:DocSection, IN_SECTION, SUBSECTION_OF).
    TAXONOMY ONLY — no :ControlMUtility, no DOCUMENTS/DESCRIBES, no SEE_ALSO;
    those are gate-bound (Q14) and the estate join additionally waits on the
    database-residency ruling (G32), because a relationship cannot span
    Neo4j databases.
    """
    from drydocs.loaders.vendor_docs import VendorDocsAdapter
    from drydocs_core.data_root import vendor_docs_dir

    _gate_loader(VendorDocsLoader)  # confirmed-gate before any DB write
    base = vendor_docs_dir(capture_id)
    if not (base / "convert-manifest.json").exists():
        console.print(
            f"[red]Not converted:[/] {base} — run `drydocs convert-vendor-docs {capture_id}` first."
        )
        raise typer.Exit(1)
    adapter = VendorDocsAdapter(capture_id)
    with _client() as cli:
        summary = VendorDocsLoader(cli, adapter).load()
    console.print(summary.as_dict())


@app.command(name="load-doc-traceability")
def load_doc_traceability(
    design_dir: Path = typer.Option(
        DEFAULT_DESIGN_DIR,
        "--design-dir",
        help="Directory of design-doc .md files (defaults to docs/design).",
    ),
    feedback_dir: Path = typer.Option(
        DEFAULT_FEEDBACK_DIR,
        "--feedback-dir",
        help="Directory of <doc-id>-rev<N>.yaml feedback files (defaults to docs/design/feedback).",
    ),
) -> None:
    """Load the doc-traceability graph — DryDocs documenting itself (L7).

    Connector #1 of the product-plane documentation ontology (gate
    doc-traceability-feedback, signed off 2026-07-20): three passes in a
    fixed order — (1) docs/design/*.md -> :DesignDoc + :DocSection + PART_OF;
    (2) traceability-matrix rows -> :Requirement + :Component + :TestCase +
    SPECIFIED_IN / IMPLEMENTED_BY / VERIFIED_BY (sections MATCHed, never
    MERGEd); (3) feedback yamls -> :FeedbackNote + ANNOTATES (+ attribution
    when the author resolves to a real :Employee). Idempotent; fully
    deterministic parsing (no LLM).
    """
    _gate_loader(DesignDocSectionsLoader)  # confirmed-gate (overlay-aware) before any DB write
    if not design_dir.exists():
        console.print(f"[red]Missing: {design_dir}[/]")
        raise typer.Exit(1)
    dirs = {"design": design_dir, "feedback": feedback_dir}
    with _client() as cli:
        for loader_cls, adapter_cls, dir_key in DOC_TRACEABILITY_CHAIN:
            loader = loader_cls(cli, adapter_cls(dirs[dir_key]))
            try:
                summary = loader.load()
            except RuntimeError as exc:  # L17 prereq refusal — loud, exit 2
                console.print(f"[red]{exc}[/]")
                raise typer.Exit(2) from exc
            console.print(summary.as_dict())
            # L17 per-row coverage: anchor links / attributions that MATCHed
            # nothing were dropped by design — reported, never silent.
            for attr, what in (
                ("unmatched_anchors", "cited anchor(s) matched no :DocSection"),
                ("unknown_authors", "author(s) matched no :Employee"),
            ):
                missed = getattr(loader, attr, None)
                if missed:
                    console.print(
                        f"[yellow]{loader.name}: {len(missed)} {what} — "
                        f"dropped, not written: {missed}[/]"
                    )


@app.command(name="load-essential-graphrag")
def load_essential_graphrag(
    pdf_path: Path = typer.Option(
        DEFAULT_PDF,
        "--pdf",
        help="The local (gitignored) Essential GraphRAG PDF (defaults to the repo root copy).",
    ),
    database: str = typer.Option(
        "ddcontext",
        "--database",
        help="Target database (Q2 decision: ddcontext — experiment content stays "
        "out of the ground-truth drydocs DB).",
    ),
) -> None:
    """Load the Essential GraphRAG ebook as a Document -> Chunk lexical graph (Q2).

    Deterministic chapter/section chunking of the published Manning ebook
    (pdf-lexical-v1 — no LLM, no embeddings), reusing the ACTIVE docs_*
    vocabulary confirmed at the bmc-docs-lexical-load gate. The PDF is
    local-only (gitignored); the graph cites source_url.
    """
    _gate_loader(
        EssentialGraphragLoader
    )  # confirmed-gate (overlay-aware; doc-ledger union) before any DB write
    if not pdf_path.exists():
        console.print(
            f"[red]Missing: {pdf_path} (the PDF is local-only/gitignored — "
            "obtain it from the source_url in config/source-registry.yaml)[/]"
        )
        raise typer.Exit(1)
    adapter = EssentialGraphragAdapter(pdf_path)
    with _client(database) as cli:
        summary = EssentialGraphragLoader(cli, adapter).load()
    console.print(summary.as_dict())


@app.command(name="load-folder-attribution")
def load_folder_attribution(
    csv_path: Path | None = typer.Option(
        None,
        "--csv",
        help="STG_APP_FACT export CSV feeding the K2 FALLBACK; omit to run "
        "the Oracle extract (controlm_app_facts.sql against DRYDOCS_STG); "
        "--no-fallback skips the fact feed entirely.",
    ),
    no_fallback: bool = typer.Option(
        False,
        "--no-fallback",
        help="Authored store rows only — skip the K2 matched-fallback feed.",
    ),
    batch_size: int = typer.Option(1000, "--batch-size"),
) -> None:
    """K8: attribute folders to SEAL applications (BELONGS_TO_APPLICATION).

    Gate seal-app-ref-edge-reshape (SIGNED OFF 2026-08-03): the app-code
    DEFINED mapping (config/overrides/app-code-mappings.csv, the K9 store)
    is primary — one row per Control-M app code, fanned out to folders via
    CONTAINS_FOLDER (§B1). The K2 match policy DEMOTES to a fallback for
    codes with no authored row; every fallback value is DISCLOSED via
    origin=matched-fallback (§B3). Writes ONLY (:ControlMFolder)-
    [:BELONGS_TO_APPLICATION {role:'seal_app_ref'}]->(:Port) edges onto the
    application's BatchProcessing Port (§C1) — never nodes. Folder ->
    application is 1:1 (OWNER-NOT-USER); coverage counts (attributed +
    unmatched + conflicts + pinned = eligible folders) are stamped on the
    :JobRun and reconciled by graph-tests/folder-attribution-coverage.yaml.
    """
    _gate_loader(FolderAttributionLoader)  # confirmed-gate (overlay-aware) before any DB write
    from drydocs_core.mapping_store import app_code_rows_from_store

    if no_fallback:
        inner = None
    elif csv_path is not None:
        inner = _csv_adapter(csv_path)
    else:
        sql = (SQL_DIR / "controlm_app_facts.sql").read_text(encoding="utf-8")
        inner = _oracle_adapter(sql, name="controlm_app_facts.sql")
    with _client() as cli:
        # Sequencing preconditions (gate §E): folders + SEAL reference first.
        folders, apps = check_folder_preconditions(cli)
        if not folders or not apps:
            console.print(
                f"[red]Sequencing precondition failed (gate §E): the graph has "
                f"{folders} ControlMFolder and {apps} Application nodes — run "
                f"`drydocs ingest-controlm` and `drydocs refresh-reference` "
                f"(SEAL) before the attribution load.[/]"
            )
            raise typer.Exit(2)
        adapter = FolderAttributionAdapter(
            app_code_rows_from_store(),
            fetch_folder_codes(cli),
            fact_source=inner,
            reconcilers=TierReconcilers(
                app_name=fetch_app_name_reconciler(cli),
            ),
            pinned=fetch_pinned_folders(cli),
        )
        summary = FolderAttributionLoader(cli, adapter, batch_size=batch_size).load()
        console.print(summary.as_dict())
        if adapter.coverage is not None:
            console.print({"coverage": adapter.coverage.as_dict()})
            if not adapter.coverage.reconciles():
                console.print(
                    "[red]Coverage invariant violated: attributed + unmatched + "
                    "conflicts + pinned != eligible_folders.[/]"
                )
                raise typer.Exit(1)


@app.command(name="load-manual-mappings")
def load_manual_mappings(
    csv_path: Path = typer.Argument(
        ...,
        help="SME-authored mapping CSV, registered in "
        "config/manual-loads/manifest.yaml BEFORE load.",
    ),
) -> None:
    """Tier-5 manual mapping load (gate seal-attribution-match-policy §F).

    Manifest-gated: the CSV must be registered with a named replaces_with
    automation path. Edges written here PIN — the automated attribution
    loader never silently supersedes them; retirement is a human act
    (manifest entry -> superseded).
    """
    try:
        rows = mapping_rows(csv_path)  # M3: reads via the mapping-store materialization
    except ManualLoadError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(2) from exc
    with _client() as cli:
        summary = ManualSealAttributionLoader(cli, ManualMappingAdapter(rows)).load()
    console.print(summary.as_dict())


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
    phase: str = typer.Option(
        "all",
        "--phase",
        help=(
            "nodes = Pass 1 only (labels/nodes + intra-folder edges — "
            "self-contained rows, safe to run scoped, folder by folder); "
            "relationships = the deferred cross-folder WAS_INFORMED_BY "
            "dependency pass ONLY (run once, UNSCOPED, after all nodes "
            "exist); all = both (prior behavior)."
        ),
    ),
    folder: str | None = _folder_opt(),
    run_as: str | None = _run_as_opt(),
    developer_sid: str | None = _developer_sid_opt(),
    row_cap: int | None = _row_cap_opt(),
) -> None:
    """M3 chain: folders -> jobs -> conditions in/out -> derived dependencies.

    Order is enforced — jobs MATCH their parent folder by folder_id;
    conditions MATCH their parent job by (folder_id, job_id); derived
    dependencies MATCH both endpoint jobs by the same composite key.

    TWO-PHASE CONTRACT (ported from the company repo 2026-07-23): the
    cross-folder WAS_INFORMED_BY edge links jobs across DIFFERENT folders,
    so a per-folder scoped run silently dropped it — the second endpoint's
    MATCH missed because that job wasn't loaded yet. --phase nodes runs
    Pass 1 (repeat per folder as needed); --phase relationships runs the
    deferred dependency pass once, unscoped, after all nodes exist.

    Run nightly in production; ad-hoc against samples in dev. With
    --use-oracle, --folder / --run-as / --developer-sid / --row-cap scope every
    extract in the chain (folder/developer-sid/row-cap apply to all; run-as
    applies to the job, variable, and dependency-anchor extracts).
    """
    if phase not in ("nodes", "relationships", "all"):
        console.print(f"[red]--phase must be nodes | relationships | all (got {phase!r}).[/]")
        raise typer.Exit(2)
    # Confirmed-gate (D3): every Control-M dataset the chain touches must be
    # SME-confirmed before any write — since the v2 registry split (N9) the
    # stages bind DIFFERENT psgmgr datasets, so each stage's own declaration
    # gates (overlay-aware per D2), not a single umbrella id.
    for cls in {
        cls for _, cls, *_ in (CONTROLM_NODE_STAGES + CONTROLM_PART2_STAGES + CONTROLM_REL_STAGES)
    }:
        _gate_loader(cls)
    scope = _scope_binds(folder, run_as, developer_sid, row_cap)
    # Stage declarations live at module level (N3: CONTROLM_*_STAGES) so the
    # command's chain and the load map render from the same source.
    node_stages: list[tuple[str, type[BaseLoader], str, str]] = list(CONTROLM_NODE_STAGES)
    if not skip_part2:
        node_stages.extend(CONTROLM_PART2_STAGES)
    # The deferred dependency pass: its rows are pure ctlm_id references
    # between independently-loaded jobs, so it runs AFTER all nodes exist.
    rel_stages: list[tuple[str, type[BaseLoader], str, str]] = []
    if not skip_part2:
        rel_stages.extend(CONTROLM_REL_STAGES)
    stages = (
        node_stages
        if phase == "nodes"
        else rel_stages
        if phase == "relationships"
        else node_stages + rel_stages
    )
    if not stages:
        console.print(
            "[yellow]Nothing to run: --phase relationships with --skip-part2 "
            "selects no stages.[/]"
        )
        return

    with _client() as cli:
        for stage_name, cls, sample_csv, sql_file in stages:
            if use_oracle:
                sql = (SQL_DIR / sql_file).read_text(encoding="utf-8")
                # controlm_hosts.sql binds :grpname_filter instead of the
                # folder-grained quartet (no folder/owner/author on CM_HOSTS);
                # bind it NULL so the statement is fully bound, unfiltered.
                stage_scope = (
                    {**scope, "grpname_filter": None} if stage_name == "controlm_hosts" else scope
                )
                adapter = _oracle_adapter(sql, stage_scope, name=sql_file)
            else:
                sample = samples_dir / sample_csv
                adapter = _csv_adapter(sample)
            console.print(f"[cyan]>> {stage_name}[/]")
            # D7: with no folder filter the extract declares the full folder
            # population (bundled samples or unfiltered Oracle), so unscoped
            # loaders (folders) may run their removed-from-source mark pass.
            summary = cls(cli, adapter, full_extract=folder is None).load()
            line = f"   rows={summary.rows_processed} rejected={summary.rows_rejected}"
            if summary.nodes_marked_removed or summary.nodes_reactivated:
                line += (
                    f" marked_removed={summary.nodes_marked_removed}"
                    f" reactivated={summary.nodes_reactivated}"
                )
            console.print(line)

        # P3: the derived RUNS_ON resolution pass (gate controlm-hosts-topology
        # §B). Reads nothing from staging — both inputs are already in the
        # graph — so it rides the relationships phase, after all nodes exist.
        # Group match wins; UNMATCHED/NULL are coverage, never guessed.
        if phase in ("relationships", "all") and not skip_part2:
            console.print("[cyan]>> runs_on_resolution[/]")
            coverage = RunsOnResolutionPass(cli).run()
            console.print({"runs_on_coverage": coverage.as_dict()})


@app.command(name="lineage-review")
def lineage_review(
    source: Path = typer.Argument(
        ..., help="controlm_jobs CSV export (or a directory to search for one)."
    ),
    out: Path = typer.Option(Path("lineage-review.html"), "--out", "-o", help="Output HTML path."),
    doc_id: str | None = typer.Option(
        None, "--doc-id", help="Review-page identity (defaults to the source stem)."
    ),
) -> None:
    """Render the lineage SME review page from a Control-M jobs CSV (no Neo4j).

    The drydocs-lineage curation surface (ADR 0002-C): one self-contained HTML
    file — folder sections, job cards with their INVOKES dependencies, an
    assertion panel, per-folder SME notes with JSON export. Candidates only;
    nothing here writes the graph (the curated write is gate-bound in
    drydocs_lineage.writer).
    """
    from drydocs_lineage.extractors import ControlMInventoryExtractor
    from drydocs_lineage.model import LineageGraph
    from drydocs_lineage.review import to_html

    if not source.exists():
        console.print(f"[red]Source not found: {source}[/]")
        raise typer.Exit(2)
    graph = LineageGraph()
    coverage = ControlMInventoryExtractor().extract(source, graph)
    out.write_text(to_html(graph, doc_id=doc_id or source.stem), encoding="utf-8")
    st = graph.stats()
    console.print(
        f"[green]wrote {out}[/] — processes={st['processes']} "
        f"data_assets={st['data_assets']} rels={st['rels']}"
    )
    console.print(f"coverage: {coverage.summary()}")


DOC_REGISTRY_PATH = Path(__file__).resolve().parents[1] / "config" / "doc-source-registry.yaml"

#: Databases docs-verify sweeps. The registry admits dddocs | ddcontext as
#: targets, but a corpus can only be found in a database that EXISTS — and
#: `drydocs` is where the bmc-docs corpus actually lives today. The sweep is
#: intersected with SHOW DATABASES at runtime, so an unprovisioned name here is
#: reported as db-absent rather than raising from the driver.
#: (`ddlineage` retired 2026-08-04, ADR 0002 X1 amendment — swept here until then.)
DOC_SWEEP_DATABASES = ("drydocs", "dddocs", "ddcontext")


@app.command(name="docs-verify")
def docs_verify() -> None:
    """Reconcile the doc-source registry against what the graph actually holds.

    One row per config/doc-source-registry.yaml entry: declared target_db, the
    loaded Document/Chunk counts, and a status. Exits non-zero on wrong-db —
    a corpus sitting in a database it did not declare is the G30 failure class
    at corpus granularity, and it is the one result that cannot be seen by
    querying a single database.
    """
    import yaml

    registry = yaml.safe_load(DOC_REGISTRY_PATH.read_text(encoding="utf-8"))
    sources = registry.get("sources", [])

    # The sweep deliberately probes databases that hold no documents — that is
    # how a stray copy is found — so the driver's "unknown label :Document"
    # notifications are the EXPECTED case here, not a warning worth printing.
    # Scoped to this command: elsewhere an unknown label really is a signal.
    notifications = logging.getLogger("neo4j.notifications")
    prior = notifications.level
    notifications.setLevel(logging.ERROR)

    try:
        _docs_verify_run(sources)
    finally:
        notifications.setLevel(prior)


def _docs_verify_run(sources: list[dict]) -> None:
    with _client() as probe:
        existing = {r["name"] for r in probe.run("SHOW DATABASES YIELD name RETURN name")}

        def run(database: str, cypher: str, params: dict) -> list[dict]:
            # One client per database: a transaction cannot span databases, and
            # the whole point of the sweep is to look in the OTHER ones.
            with _client(database) as cli:
                return cli.run(cypher, params)

        rows = verify_corpora(
            sources,
            DOC_SWEEP_DATABASES,
            run,
            available=[db for db in DOC_SWEEP_DATABASES if db in existing],
        )

    table = Table(title="doc corpora — declared vs loaded")
    for col in ("corpus", "target_db", "status", "docs", "chunks", "detail"):
        table.add_column(col)
    for r in rows:
        colour = {
            "loaded": "green",
            "wrong-db": "red",
            "stale": "yellow",
            "missing": "yellow",
        }.get(r.status, "dim")
        table.add_row(
            r.corpus_id,
            r.target_db,
            f"[{colour}]{r.status}[/]",
            str(r.documents) if r.documents else "-",
            str(r.chunks) if r.chunks else "-",
            r.detail,
        )
    console.print(table)
    console.print(DocsVerifySummary.of(rows).line())

    code = docs_verify_exit_code(rows)
    if code:
        console.print(
            "[red]wrong-db rows present — a corpus is not in the database it declared.[/]"
        )
        raise typer.Exit(code)


@app.command(name="m3-verify")
def m3_verify() -> None:
    """Assert M3 (part 1) invariants on the populated graph."""
    checks = []
    with _client() as cli:
        # Every folder has a server.
        rows = cli.run("""
            MATCH (f:ControlMFolder)
            OPTIONAL MATCH (f)-[:SCHEDULED_ON]->(srv:ControlMServer)
            WITH count(f) AS folders, count(srv) AS srv_links
            RETURN folders, srv_links
        """)
        if rows:
            r = rows[0]
            checks.append(
                (
                    "every folder has a server",
                    r["folders"] == r["srv_links"],
                    f"folders={r['folders']} srv_links={r['srv_links']}",
                )
            )

        # Every application grouping contains at least one folder (no orphan
        # :ControlMApplication nodes — they only exist via the header-row join).
        rows = cli.run("""
            MATCH (a:ControlMApplication)
            OPTIONAL MATCH (a)-[:CONTAINS_FOLDER]->(f:ControlMFolder)
            WITH count(DISTINCT a) AS apps, count(DISTINCT CASE WHEN f IS NOT NULL THEN a END) AS with_folder
            RETURN apps, with_folder
        """)
        if rows:
            r = rows[0]
            checks.append(
                (
                    "every ControlMApplication contains a folder",
                    r["apps"] == r["with_folder"],
                    f"apps={r['apps']} with_folder={r['with_folder']}",
                )
            )

        # C5 (gate 2026-07-18): no direct edge between the two row-derived
        # satellites of the folder header row. App and server both hang off the
        # folder (star-on-folder); "which servers run this app's work" is the
        # per-folder traversal CONTAINS_FOLDER + SCHEDULED_ON — a stored
        # shortcut would flatten a many-to-many that changes as folders
        # migrate, restating the row join with no provenance of its own.
        rows = cli.run("""
            MATCH (app:ControlMApplication)-[r]-(srv:ControlMServer)
            RETURN count(r) AS direct_edges
        """)
        if rows:
            checks.append(
                (
                    "no direct ControlMApplication<->ControlMServer edge",
                    rows[0]["direct_edges"] == 0,
                    f"direct_edges={rows[0]['direct_edges']}",
                )
            )

        # Every job has a folder.
        rows = cli.run("""
            MATCH (j:ControlMJob)
            OPTIONAL MATCH (f:ControlMFolder)-[:CONTAINS_JOB]->(j)
            WITH count(j) AS jobs, count(f) AS with_folder
            RETURN jobs, with_folder
        """)
        if rows:
            r = rows[0]
            checks.append(
                (
                    "every job has a folder",
                    r["jobs"] == r["with_folder"],
                    f"jobs={r['jobs']} with_folder={r['with_folder']}",
                )
            )

        # Composite key sanity — no duplicate (folder_id, job_id): the NODE KEY.
        # JOB_ID alone is folder-scoped in BMC (the same JOB_ID legitimately
        # appears in multiple folders, e.g. a DLY/CYC promoted pair) — grouping
        # without folder_id was a stale pre-composite-key check (caught by the
        # J9 e2e run against the bundled sample, which carries such a pair).
        rows = cli.run("""
            MATCH (j:ControlMJob)
            WITH j.folder_id AS fid, j.job_id AS jid, count(*) AS n
            WHERE n > 1
            RETURN count(*) AS dupes
        """)
        if rows:
            checks.append(
                (
                    "no duplicate (folder_id, job_id)",
                    rows[0]["dupes"] == 0,
                    f"dupes={rows[0]['dupes']}",
                )
            )

        # The "ControlM SchedulerKind seeded" check retired with the seeds
        # (C12 platforms-taxonomy gate 2026-07-21): fresh bootstraps no longer
        # create :SchedulerKind nodes, and old graphs that still hold them are
        # harmless. The orchestrator fact is verified via the software registry
        # (USES_SOFTWARE {source:'batch-port'} — loader migration C14).

        # ---- doc-06 Phase 3 invariants (M2, 2026-07-21) ------------------
        # Post-migration shape: no blanket provenance from pre-diet runs, the
        # raw-named folder audit props retired, and node pull-provenance uses
        # first_seen_at (created_at survives ONLY on the snapshot version
        # labels — the snapshot writer's own vocabulary).
        rows = cli.run("""
            MATCH (run:JobRun {kind:'load', status:'OK'})
            WHERE run.rows_changed IS NULL
            OPTIONAL MATCH ()-[r:WAS_GENERATED_BY]->(run)
            RETURN count(r) AS blanket
        """)
        if rows:
            checks.append(
                (
                    "no blanket WAS_GENERATED_BY from pre-diet runs",
                    rows[0]["blanket"] == 0,
                    f"blanket={rows[0]['blanket']} (pre-diet load detected — rebuild from bootstrap; the one-time 20260721 migration was removed 2026-07-23)",
                )
            )

        rows = cli.run("""
            MATCH (f:ControlMFolder)
            WHERE f.last_updated IS NOT NULL OR f.last_updated_user IS NOT NULL
            RETURN count(f) AS raw_props
        """)
        if rows:
            checks.append(
                (
                    "raw-named folder audit props retired",
                    rows[0]["raw_props"] == 0,
                    f"raw_props={rows[0]['raw_props']} (envelope pair is the record)",
                )
            )

        rows = cli.run("""
            MATCH (n)
            WHERE n.created_at IS NOT NULL
              AND NOT n:ApplicationSnapshot AND NOT n:ProductSnapshot
              AND NOT n:CatalogLOBSnapshot
            RETURN count(n) AS legacy_created_at
        """)
        if rows:
            checks.append(
                (
                    "loader nodes use first_seen_at (created_at renamed)",
                    rows[0]["legacy_created_at"] == 0,
                    f"legacy_created_at={rows[0]['legacy_created_at']}",
                )
            )

        # Local-namespace anchor terms present (post supplement).
        # Parentheses around the OR group — without them, AND binds tighter
        # and the IRI-prefix filter only constrains the ControlMFolder branch.
        rows = cli.run("""
            MATCH (n:OntologyTerm:LocalClass)
            WHERE n.iri STARTS WITH 'https://drydocs.local/ontology#'
              AND (n.iri ENDS WITH 'ControlMFolder'
                   OR n.iri ENDS WITH 'ControlMJob'
                   OR n.iri ENDS WITH 'ControlMServer')
            RETURN count(DISTINCT n) AS n
        """)
        if rows:
            checks.append(
                (
                    "M3 local anchor terms seeded",
                    rows[0]["n"] >= 3,
                    f"n={rows[0]['n']} (expect >= 3 after apply-ontology-supplement)",
                )
            )

        # Every active folder has at least one active job (sample-friendly bound).
        rows = cli.run("""
            MATCH (f:ControlMFolder {active: true})
            OPTIONAL MATCH (f)-[:CONTAINS_JOB]->(j:ControlMJob)
            WITH f, count(j) AS jc
            RETURN sum(CASE WHEN jc = 0 THEN 1 ELSE 0 END) AS empty_folders,
                   count(f) AS total
        """)
        if rows:
            r = rows[0]
            checks.append(
                (
                    "active folders contain at least one job",
                    r["empty_folders"] == 0,
                    f"empty={r['empty_folders']} total={r['total']}",
                )
            )

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
            checks.append(
                (
                    "no orphan conditions",
                    r["orphan"] == 0,
                    f"orphan={r['orphan']} total={r['total']}",
                )
            )

        # Every derived :WAS_INFORMED_BY edge must carry via_condition — the
        # linking condition is the edge's identity discriminator. The old
        # level/path checks went with the stored closure (phased-loader
        # change 2026-07-23: direct edges only; transitive reach is a
        # graph traversal).
        rows = cli.run("""
            MATCH ()-[r:WAS_INFORMED_BY]->()
            WHERE r.derived = true
            RETURN count(r) AS total,
                   sum(CASE WHEN r.via_condition IS NULL THEN 1 ELSE 0 END) AS missing_condition
        """)
        if rows:
            r = rows[0]
            checks.append(
                (
                    "WAS_INFORMED_BY edges carry via_condition",
                    r["missing_condition"] == 0,
                    f"total={r['total']} missing_condition={r['missing_condition']}",
                )
            )

    t = Table(title="M3 (part 1 + part 2) invariants")
    t.add_column("Check")
    t.add_column("OK", justify="center")
    t.add_column("Detail")
    failed = 0
    for name, ok, detail in checks:
        t.add_row(name, "yes" if ok else "NO", detail)
        if not ok:
            failed += 1
    console.print(t)
    if failed:
        console.print(f"[red]{failed} invariant(s) failed.[/]")
        raise typer.Exit(1)
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
    delimiter: str = typer.Option(
        ",", "--delimiter", help="Field delimiter; use '|' for raw exports."
    ),
    use_oracle: bool = typer.Option(
        False, "--use-oracle", help="Run controlm_variables.sql against psgmgr instead of a file."
    ),
    resolve: bool = typer.Option(
        False,
        "--resolve",
        help="Also run the Phase-B resolver (folder scope -> job scope) and report resolution coverage.",
    ),
    folder: str | None = _folder_opt(),
    run_as: str | None = _run_as_opt(),
    developer_sid: str | None = _developer_sid_opt(),
    row_cap: int | None = _row_cap_opt(),
) -> None:
    """Variable taxonomy coverage report (no Neo4j required).

    Classifies every variable definition (LITERAL / VAR_REF / SYSTEM_FUNC /
    DYNAMIC_NAME / FLOW_REF / PLUGIN_NS / EMBEDDED_SHELL / SEMANTIC_FACT /
    MALFORMED), confirms _D/_Q/_P environment triplets per job, and prints
    the coverage numbers that validate the taxonomy. With --resolve, each
    job's definitions are resolved under its folder scope (Phase B) and
    resolution coverage is reported. With --use-oracle, --folder / --run-as /
    --developer-sid / --row-cap scope the psgmgr extract.
    """
    if use_oracle:
        sql = (SQL_DIR / "controlm_variables.sql").read_text(encoding="utf-8")
        adapter = _oracle_adapter(
            sql,
            _scope_binds(folder, run_as, developer_sid, row_cap),
            name="controlm_variables.sql",
        )
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
            except Exception:  # — count + continue, like BaseLoader
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

    console.print(f"definitions={cov.total} jobs={len(cov.jobs_seen)} rejected={rejected}")

    t = Table(title="Variable kind distribution")
    t.add_column("Kind")
    t.add_column("Count", justify="right")
    t.add_column("%", justify="right")
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
        t.add_column("Name")
        t.add_column("Count", justify="right")
        for name, cnt in counter.most_common(n):
            t.add_row(name, str(cnt))
        console.print(t)

    if cov.malformed_samples:
        console.print("[yellow]Malformed samples (first " f"{len(cov.malformed_samples)}):[/]")
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
    unresolved_names: _Counter[str] = _Counter()
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
    t.add_column("Metric")
    t.add_column("Value", justify="right")
    t.add_row("definitions resolved", str(total))
    t.add_row("fully resolved", f"{fully} ({100 * fully / total:.1f}%)" if total else "0")
    t.add_row("with env variants", str(with_variants))
    t.add_row("with external (global/pool) refs", str(with_externals))
    t.add_row("max substitution depth", str(max_depth_seen))
    console.print(t)

    if unresolved_names:
        t = Table(title="Top unresolved names (runtime-provided candidates)")
        t.add_column("Name")
        t.add_column("Count", justify="right")
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
    delimiter: str = typer.Option(
        ",", "--delimiter", help="Field delimiter; use '|' for raw exports."
    ),
    use_oracle: bool = typer.Option(
        False, "--use-oracle", help="Run controlm_variables.sql against psgmgr instead of a file."
    ),
    out_dir: Path = typer.Option(
        Path("stg_out"),
        "--out-dir",
        help="Output directory for the STG_* load files.",
    ),
    folder: str | None = _folder_opt(),
    run_as: str | None = _run_as_opt(),
    developer_sid: str | None = _developer_sid_opt(),
    row_cap: int | None = _row_cap_opt(),
) -> None:
    """Classify + resolve the variable extract and emit staging load files.

    Writes stg_variable.csv, stg_parse_quality.csv, and stg_run.csv with
    columns matching controlm_staging_ddl.sql exactly — load them into the
    DRYDOCS_STG schema via SQL Developer import or SQL*Loader. No database
    write access required from this command. With --use-oracle, --folder /
    --run-as / --developer-sid / --row-cap scope the extract (handy for fresh
    samples from a single folder, run-as FID, or developer).
    """
    import csv as _csv
    import uuid
    from datetime import datetime

    if use_oracle:
        sql = (SQL_DIR / "controlm_variables.sql").read_text(encoding="utf-8")
        adapter = _oracle_adapter(
            sql,
            _scope_binds(folder, run_as, developer_sid, row_cap),
            name="controlm_variables.sql",
        )
    else:
        if not csv_path.exists():
            console.print(f"[red]File not found: {csv_path}[/]")
            raise typer.Exit(2)
        adapter = CsvAdapter(csv_path, delimiter=delimiter)

    started_at = datetime.now(UTC)
    run_id = str(uuid.uuid4())
    rejected = 0

    def _validated():
        nonlocal rejected
        for raw in adapter.rows():
            try:
                yield ControlMVariableRow.model_validate(raw)
            except Exception:  # — count + continue, like BaseLoader
                rejected += 1

    with adapter:
        jobs = collect_jobs(_validated())
    bundle = build_staging_bundle(jobs, run_id)
    ended_at = datetime.now(UTC)

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
