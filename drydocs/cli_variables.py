"""Control-M variable / command-line staging commands: export-cmdline-staging, parse-cmdline-staging, analyze-variables, normalize-variables. (resolve-cmdline-staging and fid-census stay in the root: they wire
drydocs_lineage / drydocs.fid_census, and only the root may.)

S8 (2026-08-21): split out of drydocs/cli.py. The root stays the composition
root and the only module that may wire other components; this module holds
one domain's verbs and registers them on its own Typer, which the root merges
FLAT so `drydocs --help` lists the same names as before. Shared state
(console, registries, gates, adapters) lives in the root and is imported
from it; ``_client`` is resolved THROUGH the root at call time so tests that
monkeypatch ``drydocs.cli._client`` keep working.
"""

from __future__ import annotations

import uuid
from datetime import UTC
from pathlib import Path

import typer
from rich.table import Table

from drydocs.cli_shared import (
    DEFAULT_SAMPLES_DIR,
    SQL_DIR,
    _data_center_opt,
    _developer_sid_opt,
    _folder_opt,
    _oracle_adapter,
    _row_cap_opt,
    _run_as_opt,
    _scope_binds,
    console,
)
from drydocs_core.adapters import CsvAdapter
from drydocs_core.models import ControlMVariableRow
from drydocs_core.neo4j_client import Neo4jClient
from drydocs_core.orchestration.controlm import (
    VariableCoverage,
    classify_job_variables,
    resolve_job,
)
from drydocs_core.run_log import LoaderRunLog

from .staging import build_staging_bundle, collect_jobs

app = typer.Typer()


def _client(database: str | None = None) -> Neo4jClient:
    """Resolved through the root at call time (tests patch drydocs.cli._client).

    The import is function-local ON PURPOSE: a module-scope root import is the
    S13 cycle (root body -> command modules -> root), and the guard
    (test_cli_import_order.py) fails this module by name if one returns."""
    from drydocs import cli as _root

    return _root._client(database)


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
    data_center: str | None = _data_center_opt(),
) -> None:
    """Variable taxonomy coverage report (no Neo4j required).

    Classifies every variable definition (LITERAL / VAR_REF / SYSTEM_FUNC /
    DYNAMIC_NAME / FLOW_REF / PLUGIN_NS / EMBEDDED_SHELL / SEMANTIC_FACT /
    MALFORMED), confirms _D/_Q/_P environment triplets per job, and prints
    the coverage numbers that validate the taxonomy. With --resolve, each
    job's definitions are resolved under its folder scope (Phase B) and
    resolution coverage is reported. With --use-oracle, --folder / --run-as /
    --developer-sid / --row-cap / --data-center scope the psgmgr extract.
    """
    if use_oracle:
        sql = (SQL_DIR / "controlm_variables.sql").read_text(encoding="utf-8")
        adapter = _oracle_adapter(
            sql,
            _scope_binds(folder, run_as, developer_sid, row_cap, data_center=data_center),
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
    data_center: str | None = _data_center_opt(),
) -> None:
    """Classify + resolve the variable extract and emit staging load files.

    Writes stg_variable.csv, stg_parse_quality.csv, and stg_run.csv with
    columns matching controlm_staging_ddl.sql exactly — load them into the
    DRYDOCS_STG schema via SQL Developer import or SQL*Loader. No database
    write access required from this command. With --use-oracle, --folder /
    --run-as / --developer-sid / --row-cap / --data-center scope the extract
    (handy for fresh samples from a single folder, run-as FID, developer, or
    one data center — the G115 per-data-center run recipe).
    """
    import csv as _csv
    import uuid
    from datetime import datetime

    if use_oracle:
        sql = (SQL_DIR / "controlm_variables.sql").read_text(encoding="utf-8")
        adapter = _oracle_adapter(
            sql,
            _scope_binds(folder, run_as, developer_sid, row_cap, data_center=data_center),
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
