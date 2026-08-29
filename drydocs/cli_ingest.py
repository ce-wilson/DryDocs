"""Load / ingest commands: load, refresh-catalog, refresh-applications, refresh-teams (+ the deprecated refresh-reference alias that runs all three), apply-supplements (+ legacy per-supplement aliases), load-software-registry, load-batch-orchestrators, load-code-snapshot, patch-window, load-server-inventory, load-folder-attribution, load-manual-mappings, ingest-controlm.

S8 (2026-08-21): split out of drydocs/cli.py. The root stays the composition
root and the only module that may wire other components; this module holds
one domain's verbs and registers them on its own Typer, which the root merges
FLAT so `drydocs --help` lists the same names as before. Shared state
(console, registries, gates, adapters) lives in the root and is imported
from it; ``_client`` is resolved THROUGH the root at call time so tests that
monkeypatch ``drydocs.cli._client`` keep working.
"""

from __future__ import annotations

import getpass
import uuid
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path

import typer
from rich.table import Table

from drydocs.chain_inputs import (
    ChainModeError,
    ChainStep,
    MissingChainInputError,
    StepResult,
    resolve_chain_inputs,
    summary_lines,
)
from drydocs.cli_shared import (
    CHAINS,
    CONTROLM_NODE_STAGES,
    CONTROLM_PART2_STAGES,
    CONTROLM_REL_STAGES,
    DEFAULT_SAMPLES_DIR,
    LOADER_REGISTRY,
    LOADER_SOURCE,
    LOGGER,
    SQL_DIR,
    _csv_adapter,
    _data_center_opt,
    _developer_sid_opt,
    _folder_opt,
    _gate_loader,
    _oracle_adapter,
    _row_cap_opt,
    _run_as_opt,
    _scope_binds,
    _source_registry,
    console,
)
from drydocs_core.data_root import DataRootNotSetError
from drydocs_core.data_zones import read_zone_containing
from drydocs_core.neo4j_client import Neo4jClient
from drydocs_core.run_log import LoaderRunLog
from drydocs_core.schema.supplements import (
    BY_NAME as SUPPLEMENTS_BY_NAME,
)
from drydocs_core.schema.supplements import (
    SUPPLEMENTS,
    Supplement,
    declared_terms,
    default_chain,
)

from .loaders.base import BaseLoader
from .loaders.batch_port_orchestrator import (
    DEFAULT_APPS_PATH,
    DEFAULT_PLATFORMS_PATH,
    BatchOrchestratorYamlAdapter,
    BatchPortOrchestratorLoader,
)
from .loaders.business_segments import refresh_business_segments
from .loaders.code_snapshot import (
    DEFAULT_SNAPSHOT_DIR,
    CodeSnapshotAdapter,
    CodeSnapshotError,
    CodeSnapshotLoader,
    CodeTreeAdapter,
    CodeTreeLoader,
    select_newest_snapshot,
)
from .loaders.folder_attribution import (
    FolderAttributionAdapter,
    FolderAttributionLoader,
    check_folder_preconditions,
    fetch_folder_codes,
    fetch_folder_first_seen,
    fetch_pinned_folders,
    load_platform_codes,
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
from .loaders.server_inventory import COVERAGE_QUERY as SERVER_COVERAGE_QUERY
from .loaders.server_inventory import ServerInventoryLoader
from .loaders.server_resolution import ServerResolutionPass
from .loaders.software_registry import (
    DEFAULT_REGISTRY_PATH,
    RegistryYamlAdapter,
    SoftwareRegistryLoader,
)
from .snapshots import SnapshotWriter

app = typer.Typer()


def _client(database: str | None = None) -> Neo4jClient:
    """Resolved through the root at call time (tests patch drydocs.cli._client).

    The import is function-local ON PURPOSE: a module-scope root import is the
    S13 cycle (root body -> command modules -> root), and the guard
    (test_cli_import_order.py) fails this module by name if one returns."""
    from drydocs import cli as _root

    return _root._client(database)


def _csv_acquisition_meta(csv_path: Path, *, allow_unzoned: bool) -> dict[str, str]:
    """G121: an acquisition route is DECLARED or it does not run.

    `load --csv` gated the LOADER but never the PATH — the one acquisition
    route landing-zones could not see. Resolution reuses the G81 runtime check
    (:func:`drydocs_core.data_zones.read_zone_containing`); no second
    resolution mechanism is minted. The returned dict is the loader's
    ``run_meta`` — BaseLoader writes it onto the :JobRun AND into the disk
    log's header, so a zoned load names its zone and an override is never
    silent (flag, path, operator). The source-connection-and-run-identity
    gate's E1 clause ratifies the rule as standing policy; if its E2 ruling
    refuses overrides entirely, --allow-unzoned is removed in that build.
    """
    try:
        zone = read_zone_containing(csv_path)
    except DataRootNotSetError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(2) from None
    if zone is not None:
        return {"acquisition_zone": zone.id, "acquisition_path": str(csv_path)}
    if not allow_unzoned:
        console.print(
            f"[red]REFUSED: {csv_path} is outside every declared read zone.[/] "
            "An acquisition route is declared or it does not run (G121). Declare the "
            "drop in config/source-registry.yaml (acquisition.drop_dir) or "
            "config/data-zones.yaml, then re-run — `drydocs landing-zones` lists what "
            "is declared. To load it anyway pass --allow-unzoned; the override is "
            "recorded in the run record and the disk log, never silently."
        )
        raise typer.Exit(2)
    try:
        operator = getpass.getuser()
    except Exception:  # — some CI environments have no resolvable user
        operator = ""
    console.print(
        f"[yellow]UNZONED OVERRIDE[/]: {csv_path} is outside every declared read zone "
        f"— recorded in the run record and the disk log (operator: {operator or '<unknown>'})."
    )
    return {
        "acquisition_override": "--allow-unzoned",
        "acquisition_path": str(csv_path),
        "acquisition_operator": operator,
    }


@app.command()
def load(
    name: str = typer.Argument(..., help=f"Loader: {', '.join(LOADER_REGISTRY)}"),
    csv_path: Path | None = typer.Option(None, "--csv"),
    sql: str | None = typer.Option(None, "--sql"),
    batch_size: int = typer.Option(1000, "--batch-size"),
    allow_unzoned: bool = typer.Option(
        False,
        "--allow-unzoned",
        help="Accept a --csv path outside every declared read zone. The override is "
        "recorded in the run record and the disk log (flag, path, operator) — "
        "never silent.",
    ),
) -> None:
    """Run a single loader against a CSV or Oracle source."""
    cls = LOADER_REGISTRY.get(name)
    if cls is None:
        console.print(f"[red]Unknown loader: {name}[/]")
        raise typer.Exit(2)
    if name in LOADER_SOURCE:
        _gate_loader(cls)  # confirmed-gate (overlay-aware, D2) before any DB write
    run_meta: dict[str, str] = {}
    if csv_path is not None:
        adapter = _csv_adapter(csv_path)  # existence first: a typo reads as "not found"
        run_meta = _csv_acquisition_meta(csv_path, allow_unzoned=allow_unzoned)
    elif sql is not None:
        adapter = _oracle_adapter(sql)
    else:
        console.print("[red]Provide either --csv or --sql.[/]")
        raise typer.Exit(2)
    with _client() as cli:
        summary = cls(cli, adapter, batch_size=batch_size, run_meta=run_meta).load()
    console.print(summary.as_dict())


# --- M1 commands -------------------------------------------------------------


# ---- G79: one command per SUBJECT -------------------------------------------
# These three replace the single `refresh-reference`, which bundled seven loaders
# across three sources with three rhythms. They share ONE runner because the
# contract is identical (G78: explicit input or exit 2, resolve every step before
# the first write, closing table) — what differs is the subject, which is exactly
# what the chain constant now names.

_SAMPLES_HELP = (
    "FIXTURE run: directory holding the bundled *__sample.csv fixtures. No default "
    "(G78) — a default loaded fixtures into a real graph and reported success."
)
_SOURCE_HELP = (
    "REAL run: a source-registry dataset id (repeatable). Each selected step reads "
    "<step>.csv from the source's declared landing zone (acquisition.drop_dir under "
    "DRYDOCS_DATA_ROOT); steps bound to an unselected source are reported NOT SELECTED."
)


def _run_reference_chain(
    command: str,
    *,
    samples_dir: Path | None,
    sources: list[str],
    snapshot: bool,
    snapshot_families: tuple[str, ...],
    preamble: Callable[[Neo4jClient], None] | None = None,
) -> None:
    """Run ONE subject chain end to end. `snapshot_families` names the snapshot
    writers this SUBJECT owns — never write_all(), which spans two subjects and
    would have each command claiming the others' entities."""
    chain = CHAINS[command]
    # Confirmed-gate (D3): every feed the chain touches must be SME-confirmed
    # before any write — derived from the chain's own source_id declarations.
    for cls in {cls for _, cls, _ in chain}:
        _gate_loader(cls)
    steps = [ChainStep(nm, cls, fixture) for nm, cls, fixture in chain]
    try:
        plan = resolve_chain_inputs(
            steps, samples_dir=samples_dir, sources=sources, registry=_source_registry()
        )
    except (ChainModeError, MissingChainInputError) as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(2) from exc
    mode = "FIXTURE" if samples_dir is not None else "SOURCE"
    console.print(f"[cyan]{command} — {mode} run; {len(plan.inputs)} step(s) resolved[/]")
    results: list[StepResult] = []
    with _client() as cli:
        if preamble is not None:
            preamble(cli)
        for item in plan.inputs:
            console.print(f"[cyan]>> {item.step.name}[/]  {item.path}")
            summary = item.step.loader(cli, _csv_adapter(item.path)).load()
            console.print(f"   rows={summary.rows_processed} rejected={summary.rows_rejected}")
            results.append(
                StepResult(
                    step=item.step.name,
                    mode=item.mode,
                    path=str(item.path),
                    rows=summary.rows_processed,
                    rejected=summary.rows_rejected,
                    source_id=item.source_id,
                )
            )
        if snapshot and snapshot_families:
            console.print("[cyan]>> snapshots[/]")
            writer = SnapshotWriter(cli)
            console.print(
                {fam: getattr(writer, f"write_{fam}_snapshots")() for fam in snapshot_families}
            )
    for line in summary_lines(results, plan.skipped):
        console.print(line)


def _segments_preamble(cli: Neo4jClient) -> None:
    """business_segments RE-HOMED here (G79). It is a read-only COUNT, not a
    loader — it verifies the bootstrap-seeded corporate backbone is still there.
    It belongs to the CATALOG subject because catalog_lobs reconciles LOBs to
    those corporate BusinessSegments, so the count is that reconciliation's
    precondition rather than a step of its own."""
    bs = refresh_business_segments(cli)
    console.print(f"[cyan]Business segments active: {bs['codes']}[/]")


@app.command(name="refresh-catalog")
def refresh_catalog(
    samples_dir: Path | None = typer.Option(None, "--samples-dir", help=_SAMPLES_HELP),
    source: list[str] = typer.Option([], "--source", help=_SOURCE_HELP),
    snapshot: bool = typer.Option(True),
) -> None:
    """Product catalog hierarchy: LOBs -> product lines -> products.

    Explicit input or exit 2 — the single-loader `load --csv` contract (G78).
    """
    _run_reference_chain(
        "refresh-catalog",
        samples_dir=samples_dir,
        sources=source,
        snapshot=snapshot,
        snapshot_families=("product", "lob"),
        preamble=_segments_preamble,
    )


@app.command(name="refresh-applications")
def refresh_applications(
    samples_dir: Path | None = typer.Option(None, "--samples-dir", help=_SAMPLES_HELP),
    source: list[str] = typer.Option([], "--source", help=_SOURCE_HELP),
    snapshot: bool = typer.Option(True),
) -> None:
    """Business applications and their contacts (SEAL).

    Runs BEFORE refresh-teams: SEAL is the authority for application identity,
    and refresh-teams carries a :BusinessApplication minter (G79 (e)).
    """
    _run_reference_chain(
        "refresh-applications",
        samples_dir=samples_dir,
        sources=source,
        snapshot=snapshot,
        snapshot_families=("application",),
    )


@app.command(name="refresh-teams")
def refresh_teams(
    samples_dir: Path | None = typer.Option(None, "--samples-dir", help=_SAMPLES_HELP),
    source: list[str] = typer.Option([], "--source", help=_SOURCE_HELP),
    snapshot: bool = typer.Option(True),
) -> None:
    """The delivery organisation: dev teams, their roles, and team<->app alignment.

    No snapshot family: the temporal snapshot writers cover applications,
    products and LOBs — there is no team snapshot to write, and inventing one
    here would be a load this subject was never asked for.
    """
    _run_reference_chain(
        "refresh-teams",
        samples_dir=samples_dir,
        sources=source,
        snapshot=snapshot,
        snapshot_families=(),
    )


@app.command(name="refresh-reference")
def refresh_reference(
    samples_dir: Path | None = typer.Option(None, "--samples-dir", help=_SAMPLES_HELP),
    source: list[str] = typer.Option([], "--source", help=_SOURCE_HELP),
    snapshot: bool = typer.Option(True),
) -> None:
    """[dim](deprecated)[/] Runs refresh-catalog, refresh-applications and
    refresh-teams in sequence — the three subjects this command used to bundle.

    DEPRECATED, NOT DELETED (the S8 `m1-verify` -> `verify-reference`
    precedent): operator muscle memory, runbooks and the company's own scripts
    name this verb, and a removed command fails in a way that reads like a
    broken install. It DELEGATES — there is no second implementation to drift.
    """
    console.print(
        "[yellow]refresh-reference is deprecated (G79): it bundled three subjects "
        "with three refresh rhythms. Running refresh-catalog, refresh-applications "
        "and refresh-teams in order.[/]"
    )
    refresh_catalog(samples_dir=samples_dir, source=source, snapshot=snapshot)
    refresh_applications(samples_dir=samples_dir, source=source, snapshot=snapshot)
    refresh_teams(samples_dir=samples_dir, source=source, snapshot=snapshot)


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
    + HAS_MODULE / IMPORTS / IS_ENCODED_IN / HAS_MEDIA_TYPE edges, then the
    containment layer (:CodeDirectory + CONTAINS_ENTRY from the v2 rels
    section — SME ruling 2026-08-05 admitted the tree the G33 gate deferred).
    Idempotent; re-runnable from committed files (ADR 0002 D3). abs_path never
    loads (§H4).

    WHOLE-TREE snapshots are the normal shape (meta.tree == true) since the
    scanner stopped taking a hand-maintained root list; §G1(a)'s "refuse
    tree-mode" ruling was REVERSED by SME direction and refusing it would now
    refuse every snapshot there is. What still gets refused, loudly: a file with
    NO `meta` header at all (the headerless one-off shape §G1 was really
    protecting against — the assertion stays POSITIVE because those files carry
    no `meta`, so a truthiness test on meta.tree would ACCEPT them), and a
    `meta.tree` that is not a boolean. The tree loader additionally refuses a
    roots-only snapshot (meta.tree == false: no containment to load) — the
    module loader still loads it, so `-CodeOnly` comparison files stay loadable.
    """
    _gate_loader(CodeSnapshotLoader)  # confirmed-gate (overlay-aware) before any DB write
    try:
        path = Path(file) if file else select_newest_snapshot(snapshot_dir)
        adapter = CodeSnapshotAdapter(path)
        console.print(f"snapshot: {path.name}")
        with _client() as cli:
            # Every snapshot is a FULL scan of the source tree by construction,
            # so both runs declare full_extract: the D7 mark pass flags
            # :CodeModule / :CodeDirectory nodes that left the tree between
            # snapshots.
            loader = CodeSnapshotLoader(cli, adapter, full_extract=True)
            summary = loader.load()
            console.print(summary.as_dict())
            is_tree_snapshot = adapter.skipped_directories > 0
            tree_adapter = None
            if is_tree_snapshot:
                tree_adapter = CodeTreeAdapter(path)
                tree_loader = CodeTreeLoader(cli, tree_adapter, full_extract=True)
                tree_summary = tree_loader.load()
                console.print(tree_summary.as_dict())
            else:
                console.print(
                    "[yellow]TREE SKIPPED[/]: roots-only snapshot (no directory nodes) — "
                    "no containment layer to load"
                )
    except CodeSnapshotError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(2) from exc
    # SME ruling 2026-08-06: binary assets (images + fonts) are not code-graph
    # content — both passes skip them; counts reported so the exclusion stays
    # visible.
    if adapter.skipped_assets:
        console.print(
            f"[yellow]ASSETS SKIPPED[/]: {adapter.skipped_assets} image/font file(s) "
            f"(+{tree_adapter.skipped_assets if tree_adapter else 0} containment rel(s)) — "
            "not code-graph content (SME ruling 2026-08-06; see ASSET_EXTENSIONS_SKIPPED)"
        )
    # Counts always reported, never silent: extensions with NEITHER a seeded
    # SWO language term NOR a seeded MediaType format term load their node fine
    # but carry no type edge at all (IS_ENCODED_IN and HAS_MEDIA_TYPE skipped).
    for ext, n in sorted(adapter.unmapped_extensions.items()):
        console.print(
            f"[yellow]UNTYPED EXTENSION[/]: {n} node(s) with extension '{ext or '<none>'}' — "
            "no seeded SwoClass or MediaType term (see EXTENSION_LANGUAGE_IRI / "
            "EXTENSION_MEDIA_TYPE_IRI); reported, never guessed"
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


@app.command(name="load-server-inventory")
def load_server_inventory(
    export_path: Path = typer.Option(
        ...,
        "--export",
        help="A per-application server-export CSV, or a directory of them "
        "(the internal/server-inventory/ landing zone; the bundled synthetic "
        "sample is tests/fixtures/server_inventory/).",
    ),
    batch_size: int = typer.Option(1000, "--batch-size"),
    skip_resolution: bool = typer.Option(
        False,
        "--skip-resolution",
        help="Load inventory only; skip the derived ExecutionHost join pass.",
    ),
) -> None:
    """Z3: load the infra server export + the tiered ExecutionHost join.

    Gate server-location-ontology (SIGNED OFF 12/12, 2026-08-19): :Server is
    the inventory backbone (§A1), :DataCenter carries geography + the Idea-90
    location_grain declaration (§B1/§B2), and the §C2 technology-port leg —
    (:BusinessApplication)-[:HAS_PORT]->(:Port {kind:'Technology'})-
    [:RUNS_ON {role:'technology_port'}]->(:Server) — is MATCH-only on the
    app (apps absent from the graph are COUNTED, never minted). One CSV =
    one application's download (both PROD and DR rows). The derived
    resolution pass then joins :ExecutionHost -> :Server under the §C1
    tiers (T1 exact, T2 normalized short-name with the ambiguity guard; T3
    dns-resolved arrives with the Z4 collector) — evidence on every edge,
    unmatched reported, never guessed.
    """
    _gate_loader(ServerInventoryLoader)  # confirmed-gate (overlay-aware) before any DB write
    files = sorted(export_path.glob("*.csv")) if export_path.is_dir() else [export_path]
    if not files or not all(f.exists() for f in files):
        console.print(f"[red]No CSV export found at {export_path}[/]")
        raise typer.Exit(1)
    with _client() as cli:
        for f in files:
            summary = ServerInventoryLoader(cli, _csv_adapter(f), batch_size=batch_size).load()
            console.print({f.name: summary.as_dict()})
        rows = cli.run(SERVER_COVERAGE_QUERY)
        if rows:
            console.print({"inventory_coverage": rows[0]})
        if not skip_resolution:
            console.print("[cyan]>> server_resolution (T1 exact / T2 normalized; T3 = Z4)[/]")
            coverage = ServerResolutionPass(cli).run()
            console.print({"server_resolution_coverage": coverage.as_dict()})


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
            # K18: the closed platform-code list (values twin; empty when the
            # internal file is absent — the derivation guard goes inert).
            platform_codes=load_platform_codes(),
            # K19: folder first-seen dates feed the mapping-age check — a
            # mapping older than folders it lands on queues for review.
            folder_first_seen=fetch_folder_first_seen(cli),
        )
        summary = FolderAttributionLoader(cli, adapter, batch_size=batch_size).load()
        console.print(summary.as_dict())
        if adapter.coverage is not None:
            console.print({"coverage": adapter.coverage.as_dict()})
            # K19 review queue: which as-of assertions predate their folders.
            # Reported to the steward, never re-attributed automatically — a
            # reissued code and a growing application look identical here.
            if adapter.coverage.mapping_age_suspects:
                console.print(
                    {
                        "mapping_age_review_queue": [
                            asdict(s) for s in adapter.coverage.mapping_age_suspects
                        ]
                    }
                )
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
    data_center: str | None = _data_center_opt(),
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
    --use-oracle, --folder / --run-as / --developer-sid / --row-cap /
    --data-center scope every extract in the chain (folder/developer-sid/
    row-cap apply to all; run-as applies to the job, variable, and
    dependency-anchor extracts; data-center applies to the folders, jobs, and
    hosts extracts — absent means all data centers, and the per-data-center
    run recipe lives in docs/design/drydocs-load-runbook.md, G115).
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
    scope = _scope_binds(folder, run_as, developer_sid, row_cap, data_center=data_center)
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

    if not use_oracle:
        # G78 (a): every stage's fixture is resolved BEFORE the first write and a
        # missing one fails the chain BY NAME — never "skipping". The bundled
        # default stays for this verb because sample mode IS its documented mode
        # (the e2e chain and the runbooks run it) and the real run is
        # --use-oracle, not a different directory; the banner makes the mode
        # unmistakable in the log.
        console.print(f"[yellow]FIXTURE RUN[/]: reading controlm_*__sample.csv from {samples_dir}")
        try:
            resolve_chain_inputs(
                [ChainStep(nm, cls, csv) for nm, cls, csv, _ in stages],
                samples_dir=samples_dir,
                sources=[],
                registry=_source_registry(),
            )
        except MissingChainInputError as exc:
            console.print(f"[red]{exc}[/]")
            raise typer.Exit(2) from exc
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
            # D7: with no folder filter AND no data-center filter the extract
            # declares the full folder population (bundled samples or
            # unfiltered Oracle), so unscoped loaders (folders) may run their
            # removed-from-source mark pass. A data-center-scoped run is a
            # partial extract (G115) — marking the other data centers removed
            # would be exactly the source-outage-looks-like-deletion trap.
            summary = cls(cli, adapter, full_extract=folder is None and data_center is None).load()
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
