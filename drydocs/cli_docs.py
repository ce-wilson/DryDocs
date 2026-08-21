"""Document-corpus commands: load-bmc-docs, convert-vendor-docs, load-vendor-docs, load-doc-traceability, load-essential-graphrag, load-email-extracts, docs-verify, docs-coverage.

S8 (2026-08-21): split out of drydocs/cli.py. The root stays the composition
root and the only module that may wire other components; this module holds
one domain's verbs and registers them on its own Typer, which the root merges
FLAT so `drydocs --help` lists the same names as before. Shared state
(console, registries, gates, adapters) lives in the root and is imported
from it; ``_client`` is resolved THROUGH the root at call time so tests that
monkeypatch ``drydocs.cli._client`` keep working.
"""

from __future__ import annotations

import logging
from pathlib import Path

import typer
from rich.table import Table

from drydocs import cli as _root  # the composition root; call-time lookups only
from drydocs.cli import (
    _REPO_ROOT,
    DOC_TRACEABILITY_CHAIN,
    _gate_loader,
    console,
)
from drydocs_core.neo4j_client import Neo4jClient

from .docs_coverage import REGISTRY_DB as COVERAGE_REGISTRY_DB
from .docs_coverage import coverage as build_docs_coverage
from .docs_verify import Summary as DocsVerifySummary
from .docs_verify import exit_code as docs_verify_exit_code
from .docs_verify import verify as verify_corpora
from .loaders.bmc_docs import (
    DEFAULT_CORPUS_DIR,
    BmcDocsAdapter,
    BmcDocsLoader,
)
from .loaders.doc_traceability import (
    DEFAULT_DESIGN_DIR,
    DEFAULT_FEEDBACK_DIR,
    DesignDocSectionsLoader,
)
from .loaders.email_extracts import EmailExtractsAdapter, EmailExtractsLoader
from .loaders.essential_graphrag import (
    DEFAULT_PDF,
    EssentialGraphragAdapter,
    EssentialGraphragLoader,
)
from .loaders.vendor_docs import VendorDocsLoader

app = typer.Typer()


def _client(database: str | None = None) -> Neo4jClient:
    """Resolved through the root at call time (tests patch drydocs.cli._client)."""
    return _root._client(database)


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
        "drydocs",
        "--database",
        help="Target database (G102 fold, 2026-08-18: ONE content database — the "
        "retired ddcontext default was the residency the gate ended; reference "
        "content is distinguished per source by trust_default, never by DB).",
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


@app.command(name="load-email-extracts")
def load_email_extracts(
    extracts_dir: Path | None = typer.Option(
        None,
        "--dir",
        help="Extract landing zone (defaults to DRYDOCS_DATA_ROOT/email-extracts/; "
        "the repo carries only synthetic samples under drydocs/data/samples/).",
    ),
    database: str = typer.Option("drydocs", "--database"),
) -> None:
    """Q10: load failure/activity email extracts as the lexical graph.

    Copilot JSON extracts beside their preserved .msg originals — the pair is
    the ONLY copy after the Outlook purge, so both paths land as citations and
    nothing is copied. Emails load UNASSIGNED; the folder/process assignment
    edge is gated (email-folder-assignment) and this loader never writes it.
    """
    _gate_loader(EmailExtractsLoader)
    adapter = EmailExtractsAdapter(extracts_dir)
    with _client(database) as cli:
        summary = EmailExtractsLoader(cli, adapter).load()
    if adapter.rejected:
        console.print(
            f"[yellow]{len(adapter.rejected)} extract(s) rejected (counted, never guessed):[/]"
        )
        for name, reason in adapter.rejected:
            console.print(f"  {name}: {reason}")
    console.print(summary.as_dict())


DOC_REGISTRY_PATH = _REPO_ROOT / "config" / "doc-source-registry.yaml"

#: Databases docs-verify sweeps. G102 (2026-08-18): the fold — one content
#: database. The old comment admitted a three-way mismatch (registry said one
#: db, the sweep expected another, the data sat in a third); the mismatch is
#: gone, so the admission goes with it. The retired `ddcontext` still appears
#: ONE more time per machine: the sweep visits it while it exists so a corpus
#: stranded there post-fold reports wrong-db loudly instead of vanishing; it
#: drops out automatically once the inert database is dropped (SHOW DATABASES
#: intersection).
DOC_SWEEP_DATABASES = ("drydocs", "ddcontext")  # deliberately sweeps the retired db while it exists


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


SOFTWARE_REGISTRY_PATH = _REPO_ROOT / "config" / "taxonomy" / "software-registry.yaml"
PLATFORMS_PATH = _REPO_ROOT / "config" / "taxonomy" / "platforms.yaml"
SOURCE_REGISTRY_PATH = _REPO_ROOT / "config" / "source-registry.yaml"


@app.command(name="docs-coverage")
def docs_coverage(
    no_graph: bool = typer.Option(
        False, "--no-graph", help="Declaration layer only — never contacts Neo4j."
    ),
    product: str = typer.Option("", "--product", help="Filter to one product id."),
    section: str = typer.Option("all", "--section", help="products | corpora | systems | all"),
) -> None:
    """What documentation do we hold per software product, and what is blocking it.

    Q16 (a). One row per product — INCLUDING the twelve of thirteen that carry no
    documentation pointer at all, which are the rows the report exists to print.
    Plus the corpora no product declares, and the source-registry systems with no
    product row (where Snowflake appears, being absent from the registry entirely).

    Runs fine with the database down: the cross-DB determination is arithmetic on
    two YAML fields, so `--no-graph` still answers "is a DESCRIBES edge even
    POSSIBLE". Graph-derived columns then read `-` (not probed), never 0.

    Exits non-zero on a broken corpus pointer and on version drift — NOT on
    no-corpus or cross-db-blocked, which are true statements about the world that
    G32 owns.
    """
    import yaml

    software = yaml.safe_load(SOFTWARE_REGISTRY_PATH.read_text(encoding="utf-8"))
    docs = yaml.safe_load(DOC_REGISTRY_PATH.read_text(encoding="utf-8"))
    sources = yaml.safe_load(SOURCE_REGISTRY_PATH.read_text(encoding="utf-8"))
    platforms = yaml.safe_load(PLATFORMS_PATH.read_text(encoding="utf-8"))

    run = None
    if not no_graph:
        try:
            with _client(COVERAGE_REGISTRY_DB) as probe:
                probe.run("RETURN 1 AS ok")

            # `run` is a None sentinel above, conditionally replaced by this function
            # and passed to build_docs_coverage as the graph seam. It reads like a
            # redefinition and is not one — F811 does not fire, so no directive here.
            def run(database: str, cypher: str, params: dict) -> list[dict]:
                with _client(database) as cli:
                    return cli.run(cypher, params)

        except Exception as exc:  # pragma: no cover - environment dependent
            console.print(
                f"[yellow]graph not probed ({type(exc).__name__}); declaration layer only[/]"
            )

    report = build_docs_coverage(
        software.get("products", []),
        docs.get("sources", []),
        systems=sources.get("systems", []),
        platforms=platforms.get("platforms", []),
        run=run,
    )

    rows = report.products
    if product:
        rows = [r for r in rows if r.product_id == product]

    if section in ("all", "products"):
        # ASCII arrow: the Windows console encodes cp1252 and dies on U+2192.
        table = Table(title="software -> documentation coverage")
        for col in ("product", "vendor", "corpus", "coverage", "blockers", "currency", "edges"):
            table.add_column(col)
        for r in rows:
            colour = {
                "traversable": "green",
                "unregistered-corpus": "red",
                "cross-db-blocked": "cyan",
            }.get(r.coverage, "yellow" if r.coverage != "no-corpus" else "dim")
            table.add_row(
                r.product_id,
                r.vendor_id,
                r.corpus_id or "-",
                f"[{colour}]{r.coverage}[/]",
                ", ".join(r.blockers) or "-",
                r.currency,
                "-" if r.describes_edges is None else str(r.describes_edges),
            )
        console.print(table)
        for r in rows:
            if r.unregistered_doc_locators:
                console.print(
                    f"  [cyan]{r.product_id}[/]: documentation locator(s) with no corpus "
                    f"registered - {', '.join(r.unregistered_doc_locators)}"
                )
            if r.divergence:
                console.print(
                    f"  [magenta]{r.product_id}[/]: {', '.join(r.divergence)} - {r.detail}"
                )

    if section in ("all", "corpora") and report.corpora:
        table = Table(title="corpora no product declares")
        for col in ("corpus", "tier", "target_db", "confirmed", "attribution"):
            table.add_column(col)
        for c in report.corpora:
            table.add_row(
                c.corpus_id,
                str(c.tier or "-"),
                str(c.target_db or "-"),
                str(c.confirmed),
                c.attribution,
            )
        console.print(table)

    if section in ("all", "systems") and report.systems:
        table = Table(title="registered systems with no software-registry product")
        for col in ("system", "layer", "doc locators"):
            table.add_column(col)
        for s in report.systems:
            table.add_row(s.system_id, str(s.layer or "-"), ", ".join(s.doc_locator_keys) or "-")
        console.print(table)
        console.print(
            "[dim]  candidates for a human ruling - no claim that any SHOULD be a product[/]"
        )

    console.print(f"coverage: {report.summary()}")
    if not report.reconciles():
        console.print("[red]summary does not reconcile - an input assumption is wrong.[/]")

    code = report.exit_code()
    if code:
        names = ", ".join(r.product_id for r in report.failing())
        console.print(f"[red]drift or a broken corpus pointer: {names}[/]")
        raise typer.Exit(code)
