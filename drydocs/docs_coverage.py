"""Q16 (a) — software → documentation COVERAGE: what docs we hold per product,
where they live, whether they are loaded, and what is blocking them.

The question this answers, verbatim from the user: *"when we have a tool like
Apache Airflow or Snowflake, the internal runs AWS MWAA and it has reference
documentation internally, and we have an internal scraper and a document
registry — what connects them all?"*

ONE EDGE CONNECTS THEM: ``(:Document)-[:DESCRIBES {target_version}]->(:SoftwareProduct)``
(vocabulary ``docs_describes``, status active, written by ``bmc_docs.cypher``).
There is no Document→Vendor edge — the vendor hop rides ``MADE_BY``. It resolves
for exactly ONE product today, and this module exists to make the other twelve
rows visible instead of absent.

WHY A REPORT RATHER THAN A QUERY. A Cypher query can only describe what IS in the
graph. Every interesting fact here is about what is NOT, and *why not* — and the
"why not" lives in two YAML registries, not in Neo4j. Four breaks stop the edge
generalizing, none of which is a bug:

1. The product→corpus pointer (``documentation:`` on a product) is YAML-only —
   ``software_registry.py``'s ``rows()`` never reads it, so it never reaches the
   graph. That is this item's own clause (b), still gated.
2. The doc-source registry has NO graph representation: ``:DocSource`` is not a
   live label and ``docs_has_document`` is ``planned`` with ``loader: ~``.
3. The vendor-docs corpus is staged and gate-blocked, and ``vendor_docs.cypher``
   DELIBERATELY writes no DESCRIBES edge: *a relationship cannot span Neo4j
   databases* (the Q8 finding). The registry writes ``drydocs``; ADR 0006
   re-targets doc corpora to ``dddocs``/``ddcontext``.
4. So no corpus can currently DECLARE its way to a traversable edge —
   ``target_db`` is constrained to ``{dddocs, ddcontext}`` by the doc-registry
   guard, and the registry writes ``drydocs``. **G32 owns that residency ruling.**

TWO LAYERS, AND THE BLOCKER LIVES IN THE PURE ONE
-------------------------------------------------
*Layer 1 — declaration join.* Pure: no Neo4j, no file I/O, every input injected.
It answers "is an edge even POSSIBLE" — which is arithmetic on two YAML fields,
so it is provable **with the database switched off**. That is the difference
between honest reporting and calling a ruled topology "missing data".

*Layer 2 — graph probe.* Optional, through the same injected
``run(database, cypher, params)`` seam :mod:`drydocs.docs_verify` already uses,
and reusing its :func:`~drydocs.docs_verify.count_query` verbatim so the two
verbs can never disagree about whether a corpus is loaded. When it does not run,
every graph-derived field is ``None`` — the explicit ``not-probed`` sentinel,
**never 0**, because a 0 there is a false claim of absence.

THE LADDER. ``coverage`` is the GOVERNING state (first match wins); ``blockers``
lists EVERY wall, so a row shows all of them rather than only the first.
``cross-db-blocked`` deliberately sits ABOVE every load state: a corpus that
cannot reach an edge must never be reported as merely ``not-loaded``.

WHAT FAILS THE RUN. Only :data:`FAILING` — a pointer to a corpus id that does not
exist, and version drift. NOT ``no-corpus`` and NOT ``cross-db-blocked``: those
are true statements about the world that G32 owns, and failing CI on an open
design ruling trains people to ignore the verb (the ``test_software_registry.py``
known-state-pin precedent, same reasoning).

CLASSIFICATION. The output is a CLOSED field set — ids, enum states, integer
counts, declared classification labels, and repo-relative paths already committed
in publishable config. Registry free text (``source``/``notes``/``source_url``)
never reaches it: three corpora are classification Internal and their prose
describes internal systems. Those entries are still counted and named by id —
dropping them would itself be a silent default — but their prose stays put.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass, field

from drydocs.docs_verify import locator_of

#: The database the software registry writes (`software_registry.cypher`). The
#: doc-registry guard constrains `target_db` to {dddocs, ddcontext}, so no corpus
#: can name this one — see `test_no_corpus_can_declare_the_registry_database`.
REGISTRY_DB = "drydocs"

# --- the coverage ladder (first match governs) --------------------------------
NO_CORPUS = "no-corpus"
UNREGISTERED_CORPUS = "unregistered-corpus"
UNGATED = "ungated"
CROSS_DB_BLOCKED = "cross-db-blocked"
NO_LOCATOR = "no-locator"
NOT_LOADED = "not-loaded"
PRODUCT_NODE_ABSENT = "product-node-absent"
LOADED_NO_EDGE = "loaded-no-edge"
# TRAVERSABLE_UNTIL_MOVE retired at G102 (2026-08-18): the move never happens —
# the fold makes residency permanent, so the rung had nothing left to reach.
TRAVERSABLE = "traversable"
NOT_PROBED = "not-probed"

LADDER: tuple[str, ...] = (
    NO_CORPUS,
    UNREGISTERED_CORPUS,
    UNGATED,
    CROSS_DB_BLOCKED,
    NO_LOCATOR,
    NOT_LOADED,
    PRODUCT_NODE_ABSENT,
    LOADED_NO_EDGE,
    TRAVERSABLE,
    NOT_PROBED,
)

#: Only these fail the command. `no-corpus` and `cross-db-blocked` are true facts
#: about the world owned by G32 — a red suite on an open ruling would be dishonest.
FAILING = frozenset({UNREGISTERED_CORPUS})

# --- currency (the original Q16 (a) columns, now fields on the coverage row) ---
CURRENT = "current"
DRIFTED = "drifted"
UNVERIFIED = "unverified"
NO_DOCS = "no-docs"

# --- blockers (all that apply, ladder order) ----------------------------------
BLOCKER_ORDER: tuple[str, ...] = (
    NO_CORPUS,
    UNREGISTERED_CORPUS,
    UNGATED,
    "cross-db-declared",
    "db-absent",
    NO_LOCATOR,
    NOT_LOADED,
    PRODUCT_NODE_ABSENT,
    "no-describes-edge",
    "cross-db-observed",
)

#: Graph-side facts the declarations do not predict.
DIVERGENCE_EDGES_UNDECLARED = "edges-from-an-undeclared-corpus"
DIVERGENCE_EDGE_CORPUS_UNKNOWN = "edge-corpus-unidentifiable"
DIVERGENCE_RESIDENT_OFF_DECLARATION = "resident-off-declaration"

#: The bucket a DESCRIBES edge lands in when the graph cannot say which corpus
#: produced it. A REAL, EXPECTED state: `bmc_docs.cypher` writes no `corpus_id`
#: (its locator is `path_prefix`), so those documents genuinely carry no corpus.
EDGE_CORPUS_UNKNOWN = "(no corpus_id)"


class DocsCoverageError(ValueError):
    """An input the report refuses to guess its way past."""


@dataclass
class ProductCoverageRow:
    """One software-registry product. Every product gets a row — a product with
    NO documentation at all is the row this report exists to print."""

    product_id: str = ""
    vendor_id: str = ""
    role: str = ""
    runtime_versions: tuple[str, ...] = ()
    corpus_id: str | None = None
    docs_version: str | None = None
    versions_not_current: tuple[str, ...] = ()
    currency: str = NO_DOCS
    corpus_classification: str | None = None
    corpus_tier: str | None = None
    corpus_target_db: str | None = None
    registry_db: str = REGISTRY_DB
    confirmed: bool | None = None
    locator_kind: str | None = None
    #: documentation locators found on the source-registry twin with NO corpus
    #: registered — the Airflow answer: "no corpus" is not "no docs".
    unregistered_doc_locators: tuple[str, ...] = ()
    coverage: str = NOT_PROBED
    blockers: tuple[str, ...] = ()
    divergence: tuple[str, ...] = ()
    documents: int | None = None
    describes_edges: int | None = None
    edge_corpora: tuple[str, ...] = ()
    detail: str = ""


@dataclass
class UnclaimedCorpusRow:
    """A doc-source-registry corpus, with whether any product declares it."""

    corpus_id: str = ""
    classification: str | None = None
    tier: str | None = None
    target_db: str | None = None
    confirmed: bool | None = None
    locator_kind: str | None = None
    #: EVIDENCE for a human, never a derivation — no file maps a taxonomy path
    #: to a product id, so this module must not join on it.
    taxonomy_path: str | None = None
    attribution: str = "unattributed"
    documents: int | None = None


@dataclass
class SystemRow:
    """A source-registry SYSTEM with no software-registry product row.

    Where Snowflake appears: it is a registered system and absent from the
    software registry entirely. A candidate list for a human ruling — this
    module makes no claim that any of them SHOULD be a product.
    """

    system_id: str = ""
    layer: str | None = None
    classification: str | None = None
    doc_locator_keys: tuple[str, ...] = ()
    product_match: str | None = None
    status: str = "unregistered-software"


@dataclass
class CoverageReport:
    products: list[ProductCoverageRow] = field(default_factory=list)
    #: ONLY the corpora no product declares — `corpora_total` carries the rest.
    #: Named `corpora` for the row-type it holds; the count keys keep the two
    #: apart so a reader cannot mistake the orphan list for the registry.
    corpora: list[UnclaimedCorpusRow] = field(default_factory=list)
    systems: list[SystemRow] = field(default_factory=list)
    corpora_total: int = 0
    probed: bool = False

    def summary(self) -> dict[str, int]:
        by_state = {state: 0 for state in LADDER}
        for row in self.products:
            by_state[row.coverage] += 1
        return {
            "products": len(self.products),
            **{f"products_{k}": v for k, v in by_state.items()},
            "corpora_total": self.corpora_total,
            "corpora_declared_by_a_product": self.corpora_total - len(self.corpora),
            "corpora_unclaimed": len(self.corpora),
            "corpora_edge_without_declaration": sum(
                1 for c in self.corpora if c.attribution == "edge-without-declaration"
            ),
            "systems_without_a_product_row": len(self.systems),
        }

    def reconciles(self) -> bool:
        """Every product lands in exactly one ladder state, and every corpus is
        either declared by a product or carried as an unclaimed row."""
        s = self.summary()
        states = sum(v for k, v in s.items() if k.startswith("products_"))
        corpora = s["corpora_declared_by_a_product"] + s["corpora_unclaimed"]
        return states == s["products"] and corpora == s["corpora_total"]

    def failing(self) -> list[ProductCoverageRow]:
        return [r for r in self.products if r.coverage in FAILING or r.currency == DRIFTED]

    def exit_code(self) -> int:
        return 1 if self.failing() else 0

    def as_dict(self) -> dict:
        return {
            "products": [asdict(r) for r in self.products],
            "corpora": [asdict(r) for r in self.corpora],
            "systems": [asdict(r) for r in self.systems],
            "probed": self.probed,
            "summary": self.summary(),
            "reconciles": self.reconciles(),
        }


def _currency(
    versions: tuple[str, ...], docs_version: object, current_for: object
) -> tuple[str, tuple[str, ...]]:
    """The original Q16 (a) computation, unchanged.

    `current_for` is only ever set by a human confirming a capture against a
    runtime version (acceptance (c)) — NEVER derived here by parsing version
    strings, because "does 9.0.20 documentation still describe 9.0.21.300?" is a
    judgement, not a string comparison.
    """
    if not docs_version:
        return UNVERIFIED, ()
    confirmed = tuple(str(v) for v in (current_for or ()))
    if not confirmed:
        return UNVERIFIED, versions
    missing = tuple(v for v in versions if v not in confirmed)
    return (DRIFTED if missing else CURRENT), missing


def _doc_locator_keys(system: Mapping) -> tuple[str, ...]:
    """Documentation locators on a source-registry system row.

    Keyed on a `*_docs` suffix rather than an allow-list so a locator added later
    is FOUND rather than silently uncounted.
    """
    locator = system.get("locator") or {}
    if not isinstance(locator, Mapping):
        return ()
    return tuple(sorted(k for k in locator if str(k).endswith("_docs")))


def coverage(
    products: Iterable[Mapping],
    corpora: Iterable[Mapping],
    *,
    systems: Iterable[Mapping] = (),
    platforms: Iterable[Mapping] = (),
    run: Callable[[str, str, dict], list[dict]] | None = None,
    registry_db: str = REGISTRY_DB,
) -> CoverageReport:
    """Build the coverage report. Layer 1 always; Layer 2 only when ``run`` is given."""
    report = CoverageReport(probed=run is not None)

    corpora_by_id = {}
    for entry in corpora:
        cid = str(entry.get("id") or "").strip()
        if cid:
            corpora_by_id[cid] = entry
    report.corpora_total = len(corpora_by_id)

    # system id -> product id, via the C12 gate-confirmed crosswalk, then exact id
    ref_by_system: dict[str, str] = {}
    for row in platforms:
        pid = row.get("software_registry_ref")
        sid = row.get("id")
        if pid and sid:
            ref_by_system[str(sid)] = str(pid)

    systems_list = [s for s in systems]
    locators_by_product: dict[str, list[str]] = {}
    for system in systems_list:
        sid = str(system.get("id") or "")
        keys = _doc_locator_keys(system)
        if not keys:
            continue
        target = ref_by_system.get(sid, sid)
        locator = system.get("locator") or {}
        for key in keys:
            locators_by_product.setdefault(target, []).append(str(locator.get(key)))

    # --- graph probe (Layer 2), once ------------------------------------------
    edges_by_product: dict[str, dict[str, int]] = {}
    product_nodes: set[str] = set()
    if run is not None:
        for row in run(registry_db, _PRODUCT_NODES_CYPHER, {}) or []:
            pid = row.get("product_id")
            if pid:
                product_nodes.add(str(pid))
        for row in run(registry_db, _EDGE_ATTRIBUTION_CYPHER, {}) or []:
            pid = str(row.get("product_id") or "")
            cid = str(row.get("corpus_id") or EDGE_CORPUS_UNKNOWN)
            edges = int(row.get("edges") or 0)
            edges_by_product.setdefault(pid, {})[cid] = edges

    declared_corpora: set[str] = set()

    # --- products --------------------------------------------------------------
    for product in products:
        row = _product_row(
            product,
            corpora_by_id,
            locators_by_product,
            registry_db=registry_db,
            run=run,
            product_nodes=product_nodes,
            edges_by_product=edges_by_product,
        )
        if row.corpus_id:
            declared_corpora.add(row.corpus_id)
        report.products.append(row)

    # --- corpora no product names ---------------------------------------------
    edge_corpora_seen = {cid for buckets in edges_by_product.values() for cid in buckets}
    for cid, entry in corpora_by_id.items():
        if cid in declared_corpora:
            continue
        kind, _value, _declared = locator_of(entry)
        attribution = "unattributed"
        if cid in edge_corpora_seen:
            attribution = "edge-without-declaration"
        elif run is None:
            attribution = "not-probed"
        report.corpora.append(
            UnclaimedCorpusRow(
                corpus_id=cid,
                classification=entry.get("classification"),
                tier=entry.get("tier"),
                target_db=entry.get("target_db"),
                confirmed=entry.get("confirmed"),
                locator_kind=kind,
                taxonomy_path=entry.get("taxonomy_path"),
                attribution=attribution,
            )
        )

    # --- systems with no product row ------------------------------------------
    known_products = {r.product_id for r in report.products}
    for system in systems_list:
        sid = str(system.get("id") or "")
        mapped = ref_by_system.get(sid, sid)
        if mapped in known_products:
            continue
        report.systems.append(
            SystemRow(
                system_id=sid,
                layer=system.get("layer"),
                classification=system.get("classification"),
                doc_locator_keys=_doc_locator_keys(system),
                product_match=ref_by_system.get(sid),
            )
        )

    return report


_PRODUCT_NODES_CYPHER = """
    MATCH (sp:SoftwareProduct) WHERE NOT sp:SchemaMeta
    RETURN sp.product_id AS product_id
"""

_EDGE_ATTRIBUTION_CYPHER = """
    MATCH (d:Document)-[:DESCRIBES]->(sp:SoftwareProduct)
    WHERE NOT d:SchemaMeta AND NOT sp:SchemaMeta
    RETURN sp.product_id AS product_id,
           coalesce(d.corpus_id, '(no corpus_id)') AS corpus_id,
           count(*) AS edges
"""


def _product_row(
    product: Mapping,
    corpora_by_id: Mapping[str, Mapping],
    locators_by_product: Mapping[str, list[str]],
    *,
    registry_db: str,
    run: Callable[[str, str, dict], list[dict]] | None,
    product_nodes: set[str],
    edges_by_product: Mapping[str, Mapping[str, int]],
) -> ProductCoverageRow:
    pid = str(product.get("id") or "").strip()
    if not pid:
        raise DocsCoverageError("software-registry product with no id")

    versions = tuple(str(v) for v in (product.get("versions") or ()))
    doc_block = product.get("documentation") or {}
    corpus_id = doc_block.get("corpus")
    docs_version = doc_block.get("docs_version")

    row = ProductCoverageRow(
        product_id=pid,
        vendor_id=str(product.get("vendor") or ""),
        role=str(product.get("role") or ""),
        runtime_versions=versions,
        corpus_id=corpus_id,
        docs_version=docs_version,
        registry_db=registry_db,
        unregistered_doc_locators=tuple(locators_by_product.get(pid, ())),
    )

    blockers: list[str] = []

    if not corpus_id:
        row.currency = NO_DOCS
        blockers.append(NO_CORPUS)
        row.coverage = NO_CORPUS
        row.detail = "no documentation pointer on the product" + (
            f"; {len(row.unregistered_doc_locators)} documentation locator(s) exist "
            "on the source-registry system with no corpus registered"
            if row.unregistered_doc_locators
            else ""
        )
        row.blockers = tuple(blockers)
        return row

    row.currency, row.versions_not_current = _currency(
        versions, docs_version, doc_block.get("current_for")
    )

    entry = corpora_by_id.get(str(corpus_id))
    if entry is None:
        blockers.append(UNREGISTERED_CORPUS)
        row.coverage = UNREGISTERED_CORPUS
        row.blockers = tuple(blockers)
        row.detail = f"documentation.corpus '{corpus_id}' is not a doc-source-registry id"
        return row

    kind, _value, _declared = locator_of(entry)
    row.locator_kind = kind
    row.corpus_classification = entry.get("classification")
    row.corpus_tier = entry.get("tier")
    row.corpus_target_db = entry.get("target_db")
    row.confirmed = entry.get("confirmed")

    if row.confirmed is not True:
        blockers.append(UNGATED)
    if row.corpus_target_db and row.corpus_target_db != registry_db:
        blockers.append("cross-db-declared")
    if kind == "none":
        blockers.append(NO_LOCATOR)

    # Layer 2 facts
    buckets = edges_by_product.get(pid, {})
    if run is not None:
        row.describes_edges = sum(buckets.values())
        row.edge_corpora = tuple(sorted(buckets))
        if pid not in product_nodes:
            blockers.append(PRODUCT_NODE_ABSENT)
        elif not buckets:
            blockers.append("no-describes-edge")
        divergence: list[str] = []
        if buckets and row.corpus_id not in buckets:
            divergence.append(DIVERGENCE_EDGES_UNDECLARED)
        if EDGE_CORPUS_UNKNOWN in buckets:
            divergence.append(DIVERGENCE_EDGE_CORPUS_UNKNOWN)
        row.divergence = tuple(divergence)

    # --- the ladder, first match governs --------------------------------------
    if UNGATED in blockers:
        row.coverage = UNGATED
    elif "cross-db-declared" in blockers:
        row.coverage = CROSS_DB_BLOCKED
    elif NO_LOCATOR in blockers:
        row.coverage = NO_LOCATOR
    elif run is None:
        row.coverage = NOT_PROBED
    elif PRODUCT_NODE_ABSENT in blockers:
        row.coverage = PRODUCT_NODE_ABSENT
    elif not buckets:
        row.coverage = LOADED_NO_EDGE
    else:
        # G102: the target_db != registry_db branch (traversable-until-move)
        # retired with the fold — every corpus's declared home IS the database.
        row.coverage = TRAVERSABLE

    row.blockers = tuple(b for b in BLOCKER_ORDER if b in blockers)
    row.detail = _detail(row)
    return row


def _detail(row: ProductCoverageRow) -> str:
    """A generated mechanism sentence. NEVER registry free text (acceptance (e))."""
    if row.coverage == CROSS_DB_BLOCKED:
        return (
            f"corpus targets {row.corpus_target_db}, registry writes {row.registry_db} — "
            "a relationship cannot span Neo4j databases. G32 RULED 2026-08-18 (the fold, "
            "applied at G102): post-fold this state means a row missed the re-target"
        )
    if row.coverage == UNGATED:
        return "corpus registered but confirmed: false — no loader may write from it"
    if row.coverage == NO_LOCATOR:
        return "graph_locator match: none — not on the lexical spine, by ruling"
    if row.coverage == NOT_PROBED:
        return "declaration clean; graph not probed"
    if DIVERGENCE_EDGES_UNDECLARED in row.divergence:
        return (
            f"edges exist from {sorted(row.edge_corpora)} — a corpus this product does not "
            "declare; the attribution lives in loader code, not the registry"
        )
    return ""
