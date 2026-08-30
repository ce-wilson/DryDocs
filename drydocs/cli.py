"""drydocs CLI — entry point for all bootstrap, supplement, and ingest commands.

Bootstrap order (first run):
  1. drydocs bootstrap           — constraints + ontology backbone
  2. drydocs apply-supplements   — the whole ordered supplement chain
                                   (base -> seal -> catalog -> registry ->
                                   infrastructure), each one verified against
                                   the terms its .cypher declares. The chain is
                                   DATA, and this sentence is swept against it:
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
  drydocs refresh-catalog         — LOB -> product line -> product (weekly)
  drydocs refresh-applications    — SEAL applications + contacts (weekly)
  drydocs refresh-teams           — dev teams, team roles, team<->app alignment
  drydocs refresh-reference       — DEPRECATED alias: runs the three above in
                                    order (G79 split them by subject)
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
  drydocs load-server-inventory   — Z3: infra server export -> :Server /
                                    :DataCenter + the tiered ExecutionHost join
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

import uuid
from pathlib import Path

import typer
from rich.table import Table

from drydocs_core.config import load_settings
from drydocs_core.data_root import DataRootNotSetError, ReadZoneWriteError
from drydocs_core.neo4j_client import Neo4jClient
from drydocs_core.run_log import LoaderRunLog
from drydocs_core.source_registry import SourceRegistry

# --- shared state, hoisted (S13) ---------------------------------------------
# Definitions live in drydocs/cli_shared.py; re-exported here so every existing
# `drydocs.cli.X` consumer — tests, scripts, the render pipeline, the company
# port — keeps its import path. __all__ below is that compat surface. The root
# REMAINS the composition root: the app, the mutable registry cache and the
# client factory stay in THIS module, and only this module wires components.
from .cli_shared import (
    _REPO_ROOT,
    AD_HOC_COMMANDS,
    APPLICATION_IDENTITY_LOADER,
    BUSINESS_APPLICATION_CHAIN,
    BUSINESS_APPLICATION_MINTERS,
    CADENCE_PROFILES,
    CANONICAL_LOAD_SEQUENCE,
    CATALOG_CHAIN,
    CHAINS,
    COMMAND_LOADERS,
    CONSTRAINTS_FILE,
    CONTROLM_NODE_STAGES,
    CONTROLM_PART2_STAGES,
    CONTROLM_REL_STAGES,
    DEFAULT_SAMPLES_DIR,
    DERIVED,
    DOC_TRACEABILITY_CHAIN,
    GENERATED_SAMPLE_FILES,
    LOAD_PROFILES,
    LOADER_REGISTRY,
    LOADER_SOURCE,
    LOGGER,
    ONTOLOGY_FILE,
    SCHEDULED_INGEST_EXCLUSIONS,
    SCHEMA_DIR,
    SCHEMA_GRAPH_DATABASE,
    SCHEMA_GRAPH_FILE,
    SOURCELESS_LOADERS,
    SQL_DIR,
    TEAM_CHAIN,
    UNCHAINED_LOADER_EXCLUSIONS,
    CadenceDerivationError,
    LoadStep,
    _csv_adapter,
    _data_center_opt,
    _developer_sid_opt,
    _folder_opt,
    _gate_loader,
    _gate_source,
    _oracle_adapter,
    _row_cap_opt,
    _run_as_opt,
    _scope_binds,
    _source_registry,
    chain_steps,
    console,
    load_profile,
    step_profiles,
    step_sources,
    unchained_loaders,
    unchained_registry_loaders,
)

__all__ = [
    "console",
    "LOGGER",
    "SCHEMA_DIR",
    "CONSTRAINTS_FILE",
    "ONTOLOGY_FILE",
    "SCHEMA_GRAPH_FILE",
    "SCHEMA_GRAPH_DATABASE",
    "_REPO_ROOT",
    "DEFAULT_SAMPLES_DIR",
    "LOADER_REGISTRY",
    "SQL_DIR",
    "LOADER_SOURCE",
    "SOURCELESS_LOADERS",
    "CATALOG_CHAIN",
    "BUSINESS_APPLICATION_CHAIN",
    "TEAM_CHAIN",
    "CHAINS",
    "BUSINESS_APPLICATION_MINTERS",
    "APPLICATION_IDENTITY_LOADER",
    "CONTROLM_NODE_STAGES",
    "CONTROLM_PART2_STAGES",
    "CONTROLM_REL_STAGES",
    "DOC_TRACEABILITY_CHAIN",
    "COMMAND_LOADERS",
    "AD_HOC_COMMANDS",
    "UNCHAINED_LOADER_EXCLUSIONS",
    "GENERATED_SAMPLE_FILES",
    "LoadStep",
    "DERIVED",
    "CADENCE_PROFILES",
    "CadenceDerivationError",
    "LOAD_PROFILES",
    "SCHEDULED_INGEST_EXCLUSIONS",
    "CANONICAL_LOAD_SEQUENCE",
    "chain_steps",
    "unchained_registry_loaders",
    "unchained_loaders",
    "step_sources",
    "step_profiles",
    "load_profile",
    "_source_registry",
    "_gate_source",
    "_gate_loader",
    "_csv_adapter",
    "_oracle_adapter",
    "_scope_binds",
    "_folder_opt",
    "_run_as_opt",
    "_developer_sid_opt",
    "_row_cap_opt",
    "_data_center_opt",
]

app = typer.Typer(no_args_is_help=True, rich_markup_mode="rich")


# --- root-owned state (the tested patch surfaces) ----------------------------

#: Source-registry cache. Read/written by ``cli_shared._source_registry()``
#: THROUGH this module at call time; tests monkeypatch it here.
_registry: SourceRegistry | None = None


def _client(database: str | None = None) -> Neo4jClient:
    """Build the Neo4j client from settings; ``database`` overrides the
    configured target DB (post-G102 every content load targets ``drydocs``;
    the override survives for ``ddschema`` and transitional sweeps).

    Stays ON THE ROOT (S8): command modules resolve it through this module at
    call time, so tests that monkeypatch ``drydocs.cli._client`` keep working.
    """
    cfg, _, _ = load_settings()
    pw = cfg.password.get_secret_value()
    if not pw:
        console.print("[red]NEO4J_PASSWORD is empty.[/]")
        raise typer.Exit(2)
    return Neo4jClient(cfg.uri, cfg.user, pw, database or cfg.database)


# --- entry point -------------------------------------------------------------


def run() -> None:
    """Console-script entry point (``pyproject.toml`` -> ``drydocs``).

    Exists to turn an OPERATOR CONFIGURATION error into a message and exit 2
    rather than a Python traceback. G81 made ``DRYDOCS_DATA_ROOT`` mandatory,
    and the command most likely to meet that error is ``landing-zones`` — whose
    entire reason for existing is that "my extracts are gone" should be a
    one-command answer. Handing that operator a stack trace would defeat the
    command at exactly the moment it matters. Exit 2 is the repo's
    operator-error code (the G78 ``load``/chain contract).
    """
    try:
        app()
    except DataRootNotSetError as exc:
        console.print(f"[red]{exc}[/]")
        raise SystemExit(2) from exc
    except ReadZoneWriteError as exc:
        console.print(f"[red]{exc}[/]")
        raise SystemExit(2) from exc


# --- callback ---------------------------------------------------------------


def configure_logging(*, verbose: bool = False) -> None:
    """The ONE logging configuration call — ADR 0014 clause 2 (G105).

    Replaces the single ``basicConfig`` this CLI carried, which was stderr-only
    and took its level from ``--verbose`` alone, so ``AppSettings.log_level``
    existed and was read by nobody.

    Stdlib ``dictConfig``, no new runtime dependency. Console plus a file sink
    under the resolved log root; the level comes from ``RuntimeSettings``, and
    ``--verbose`` still WINS over it — a flag the operator typed outranks a
    declared default.

    THE RULE THAT FOLLOWS FROM THIS BEING THE ONLY CALL: no module calls
    ``basicConfig``. A library that configures the root logger steals it from its
    caller, which is why the four components get module loggers instead.

    Never raises. Logging that refuses to start must not stop the command the
    operator actually asked for — the same reasoning that makes a run log
    best-effort after open.
    """
    import logging.config

    level = "DEBUG" if verbose else "INFO"
    handlers: dict[str, dict[str, object]] = {
        "console": {
            "class": "logging.StreamHandler",
            "level": level,
            "formatter": "plain",
            "stream": "ext://sys.stderr",
        }
    }
    try:
        from drydocs_core.config import RuntimeSettings
        from drydocs_core.log_kinds import log_filename
        from drydocs_core.run_log import resolve_log_dir

        if not verbose:
            level = RuntimeSettings().log_level.upper()
            handlers["console"]["level"] = level
        log_dir = resolve_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        handlers["file"] = {
            "class": "logging.FileHandler",
            "level": level,
            "formatter": "plain",
            "filename": str(log_dir / log_filename("cli", "console")),
            "encoding": "utf-8",
            "delay": True,  # no file until something is actually logged
        }
    except Exception:  # — an unconfigurable sink never costs the operator the console
        pass

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"plain": {"format": "%(asctime)s %(name)s %(levelname)s %(message)s"}},
            "handlers": handlers,
            "root": {"level": level, "handlers": sorted(handlers)},
        }
    )


@app.callback()
def main(verbose: bool = typer.Option(False, "--verbose", "-v")) -> None:
    """DryDocs — production support inventory + data product KG."""
    configure_logging(verbose=verbose)


# --- M0 commands -------------------------------------------------------------


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
    # J49: LF on every platform — a review page diffed between machines must not
    # differ by line endings. Not a committed surface (default path is untracked).
    out.write_text(to_html(graph, doc_id=doc_id or source.stem), encoding="utf-8", newline="\n")
    st = graph.stats()
    console.print(
        f"[green]wrote {out}[/] — processes={st['processes']} "
        f"data_assets={st['data_assets']} rels={st['rels']}"
    )
    console.print(f"coverage: {coverage.summary()}")


def _column_map(spec: str, *, required: tuple[str, ...], what: str) -> dict[str, str]:
    """Parse `role=HEADER,role=HEADER` into {role: header}.

    NO DEFAULT HEADERS, deliberately. The producer repo has never seen a
    functional-id directory export, and `config/source-mappings/seal-extract.yaml`
    records what happens when a loader's field names get mistaken for verified
    source vocabulary: `SEALID` lived in this repo for months as a column name
    that appears in no source. The caller names the real headers or the command
    refuses.
    """
    mapping: dict[str, str] = {}
    for pair in spec.split(","):
        pair = pair.strip()
        if not pair:
            continue
        if "=" not in pair:
            raise typer.BadParameter(f"{what}: '{pair}' is not role=HEADER")
        role, header = pair.split("=", 1)
        mapping[role.strip()] = header.strip()
    missing = [r for r in required if not mapping.get(r)]
    if missing:
        raise typer.BadParameter(f"{what}: missing role(s) {missing}; got {sorted(mapping)}")
    return mapping


def _read_column(path: Path, column: str, delimiter: str) -> list[str]:
    import csv as _csv

    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = _csv.DictReader(fh, delimiter=delimiter)
        if reader.fieldnames is None or column not in reader.fieldnames:
            raise typer.BadParameter(
                f"{path.name}: no column '{column}' (headers: {reader.fieldnames})"
            )
        return [row[column] for row in reader if (row.get(column) or "").strip()]


@app.command(name="fid-census")
def fid_census_cmd(
    application: str = typer.Option(..., "--application", help="The ONE application to census."),
    directory: Path = typer.Option(
        ..., "--directory", help="Functional-id directory export (CSV)."
    ),
    map_spec: str = typer.Option(
        ...,
        "--map",
        help=(
            "Directory column roles -> real headers, e.g. "
            "account=ID,application=APP,type=TYPE,status=STATUS,owner=OWNER. "
            "account and application are required; type/status/owner optional."
        ),
    ),
    delimiter: str = typer.Option(
        ",", "--delimiter", help="Field delimiter; use '|' for raw exports."
    ),
    run_as: Path = typer.Option(None, "--run-as", help="Control-M job extract (demand set i)."),
    run_as_column: str = typer.Option("owner", "--run-as-column", help="CM_DEF_VJOB.OWNER alias."),
    fid_facts: Path = typer.Option(
        None, "--fid-facts", help="Unresolved FID facts (demand set ii)."
    ),
    fid_facts_column: str = typer.Option("fact_value", "--fid-facts-column"),
    adhoc: Path = typer.Option(None, "--adhoc", help="Registered adhoc evidence (demand set iii)."),
    adhoc_column: str = typer.Option("account", "--adhoc-column"),
    attribution: Path = typer.Option(
        None, "--attribution", help="account -> Control-M-derived folder attribution (for Q0)."
    ),
    attribution_map: str = typer.Option(
        "account=account,application=application", "--attribution-map"
    ),
) -> None:
    """Doc 09 phase 0 — the FID directory census, on ONE application.

    COUNTS ONLY. `FidCensus` holds ints and dicts of ints, so a row dump is not
    expressible in the return type — which is what lets the result travel back to
    the producer repo while the measured values stay Internal.

    Column headers are NEVER guessed: `--map` names the real ones. The directory
    export's GRAIN is handled either way — one row per account, or one row per
    (account, owner) under the two-human-owners rule — so rows and distinct
    accounts are reported separately and a multi-owner repeat is not a duplicate.

    Every disagreement between the directory's application assignment and the
    Control-M-derived attribution lands in `unruled` and STAYS there: §G5 says the
    three readings are distinguished per case by a human, never globally.
    """
    import csv as _csv

    from .fid_census import DirectoryRow, fid_census

    cols = _column_map(map_spec, required=("account", "application"), what="--map")
    with directory.open(encoding="utf-8-sig", newline="") as fh:
        reader = _csv.DictReader(fh, delimiter=delimiter)
        headers = reader.fieldnames or []
        unknown = [h for r, h in cols.items() if h not in headers]
        if unknown:
            raise typer.BadParameter(
                f"--map names header(s) absent from {directory.name}: {unknown}"
            )
        rows = [
            DirectoryRow(
                account=r.get(cols["account"], ""),
                application=r.get(cols["application"], ""),
                account_type=r.get(cols.get("type", ""), "") or "",
                status=r.get(cols.get("status", ""), "") or "",
                owner=r.get(cols.get("owner", ""), "") or "",
            )
            for r in reader
        ]

    attribution_by_account: dict[str, str] = {}
    if attribution:
        amap = _column_map(
            attribution_map, required=("account", "application"), what="--attribution-map"
        )
        with attribution.open(encoding="utf-8-sig", newline="") as fh:
            for r in _csv.DictReader(fh, delimiter=delimiter):
                acct = (r.get(amap["account"]) or "").strip()
                if acct:
                    attribution_by_account[acct] = (r.get(amap["application"]) or "").strip()

    census = fid_census(
        application,
        rows,
        run_as_owners=_read_column(run_as, run_as_column, delimiter) if run_as else (),
        unresolved_fid_facts=(
            _read_column(fid_facts, fid_facts_column, delimiter) if fid_facts else ()
        ),
        adhoc_accounts=_read_column(adhoc, adhoc_column, delimiter) if adhoc else (),
        attribution_by_account=attribution_by_account,
    )

    table = Table(title=f"FID directory census - {census.application}")
    table.add_column("measure")
    table.add_column("count", justify="right")
    d = census.as_dict()
    for key in (
        "directory_rows_total",
        "directory_accounts_total",
        "demand_total",
        "demand_in_application",
        "demand_not_in_directory",
        "remainder_total",
        "comparable",
        "agreements",
        "disagreements",
        "undecidable",
        "accounts_below_owner_minimum",
        "accounts_with_no_owner_recorded",
        "multi_owner_rows",
        "duplicate_directory_rows",
        "case_only_mismatches",
    ):
        table.add_row(key, str(d[key]))
    console.print(table)
    console.print(f"demand by source: {d['demand_by_source']}")
    console.print(f"remainder by type: {d['remainder_by_type']}")
    console.print(f"remainder by status: {d['remainder_by_status']}")
    console.print(f"run-as owner types (gate Q5): {d['run_as_owner_types']}")
    console.print(f"§G5 breakdown: {d['disagreements_by_reading']}")

    if not census.owner_rule_measurable:
        console.print(
            "[yellow]owner rule NOT MEASURED — the export carried no owner column, so "
            "'0 below minimum' means unmeasured, not compliant.[/]"
        )
    if not census.reconciles():
        console.print("[red]census does not reconcile - an input assumption is wrong.[/]")
        raise typer.Exit(1)
    console.print(
        "[dim]counts only - no row left this command. Send as_dict() back to the producer.[/]"
    )


@app.command(name="profile-folder-set")
def profile_folder_set(
    source: Path = typer.Argument(
        ..., help="Directory holding the Control-M definition XML export."
    ),
    out: Path = typer.Option(
        Path("folder-set-profile.json"), "--out", "-o", help="Output JSON artifact path."
    ),
) -> None:
    """G68 - census a folder set: what the export SAYS, and what only you can supply.

    TRANSPORT NAMED, NOT DEFAULTED (the O58 precedent). A CLI verb writing a
    JSON artifact, because remediation writes no graph - so QuerySpecs are out
    BY CONSTRUCTION, not by preference - and no upload path exists yet. The
    cost against ADR 0005 is nil: that ADR governs the browser->Neo4j access
    path, and nothing here reads or writes a graph. `changedoc` and `jira`
    already write artifacts from this component, so this adds no new shape.

    The output has two halves, and the division is the point: FIVE CENSUSES
    report what the export carries (shape, identity, variables, contacts,
    invocation fan-out), each with WHERE-USED rather than bare distinct values;
    then a SUBSTITUTION SLOT list names the facts the export does NOT carry -
    DEVX_KEY, the MFTS set, the contact DLs - for a human to supply. A slot with
    no current value reports `not-supplied` with a null value and NEVER a
    default: inventing one is how a proposal becomes a wrong fact nobody
    re-checks.

    Asserts nothing about meaning. detect_all()'s findings ride alongside
    unratified, and no graph is written (the module's standing invariant).
    """
    import json as _json

    from drydocs_lineage.extractors import ControlMXmlDefsExtractor
    from drydocs_remediation.profile import NOT_SUPPLIED, profile
    from drydocs_remediation.xml_bridge import to_definition_set

    definitions = to_definition_set(ControlMXmlDefsExtractor().extract(source))
    result = profile(definitions)
    # newline pinned: the artifact is deterministic output, and a CRLF host
    # would otherwise make the same profile diff against itself
    out.write_text(_json.dumps(result.as_dict(), indent=2), encoding="utf-8", newline="\n")
    console.print(result.summary())
    open_slots = [s.name for s in result.substitution_slots if s.status == NOT_SUPPLIED]
    if open_slots:
        console.print(
            f"[yellow]not supplied by the export - needs an SME:[/] {', '.join(open_slots)}"
        )
    console.print(f"[green]wrote[/] {out}")
    console.print(
        "[dim]a census, not a ruling: findings ride alongside unratified and "
        "nothing was written to a graph.[/]"
    )


# --- per-domain command modules (S8) -----------------------------------------
# The root registers each domain's Typer FLAT, so every verb keeps its top-level
# name. Since S13 the import graph is a DAG, not a blessed cycle: the command
# modules import drydocs.cli_shared (never this module at module scope), and
# this root imports both — so any CLI module works as the first import of a
# fresh interpreter (guarded by tests/unit/test_cli_import_order.py). The three
# verbs above (resolve-cmdline-staging, lineage-review, fid-census) stay here
# because they wire another component (drydocs_lineage, drydocs.fid_census) —
# the composition root is the only module exempt from the component-import
# invariant (ENTRYPOINT_MODULES); S8 added no new exemption and S13 removes
# none.
from . import (  # noqa: E402
    cli_docs,
    cli_ingest,
    cli_plan,
    cli_schema,
    cli_variables,
    cli_verify,
)

COMMAND_MODULES = (cli_schema, cli_ingest, cli_verify, cli_variables, cli_docs, cli_plan)
for _sub in COMMAND_MODULES:
    app.registered_commands.extend(_sub.app.registered_commands)


if __name__ == "__main__":
    run()
