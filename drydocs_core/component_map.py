"""The component map - what a first-party module BELONGS to (ADR 0018 D1).

One declaration, three readers. ``tests/unit/test_module_boundary.py`` enforces the
import boundary from it (J37: a guard reads the importable object); ``MODULE_MAP.md``'s
component tables are rendered from it (J43: derived, never carried); the Team Edition
copier (ADR 0015 D2/D4) derives its file classes from it. Until 2026-09-02 this lived as a
constant inside the test file, which nothing but pytest could import - the trip hazard
ADR 0018 names.

Pure data. Imports nothing, first-party or otherwise beyond the stdlib - it is CORE and
core imports nothing. The comments are rulings, not decoration: each entry carries why
it is classified where it is, and a reader changing a line changes a ruling.

Two axes join here by NAME (design review 2026-09-02 §A2: two registries never share a
column). ``COMPONENT_GROUPS`` is the import-boundary axis (group -> dotted prefixes);
``COMPONENT_MODULE`` maps each group to its backlog module in
``docs/restructure/backlog/modules.yaml`` (the series-is-the-module axis, PLAN1).
``tests/unit/test_module_boundary.py`` asserts the join is total in both directions.
"""

from __future__ import annotations

# Dotted prefixes that make up drydocs-core (see MODULE_MAP.md). Since the Phase B
# relocate the physical package is the whole of core (ADR 0002-a-1).
CORE_PREFIXES: tuple[str, ...] = ("drydocs_core",)

# Component group -> the dotted prefixes that belong to it.
COMPONENT_GROUPS: dict[str, tuple[str, ...]] = {
    # drydocs.staging = the load-cadence staging bundle builder (0002-a §6 borderline;
    # relocated out of core's controlm/ in Phase B).
    # drydocs.cmdline_staging = the G39/G40 TEMPORARY cmd-line job-detail
    # staging store + parse (graph read -> SQLite under the data root; no
    # graph writes) — load-cadence tooling, same bucket as staging.
    # drydocs.docs_verify was here until O58 (2026-08-31), when it moved to
    # drydocs_core. The old note said "RE-HOME it to docmeta if that component
    # takes over corpus state" — what actually forced the move was a SECOND
    # CONSUMER: the console's docs-verify surface needs the reconciliation in
    # drydocs_api, and a component may not import another component. The
    # placement test answers it without an exception, because the module imports
    # stdlib only and its single I/O seam is an injected callable: pure resolve
    # logic belongs in core. The `docs-verify` VERB stays here — it owns the
    # driver, the SHOW DATABASES probe and the table, which is the I/O half.
    # drydocs.seal_samples = generates the two SEAL fixtures the business-application chain
    # declares (drydocs/data/ is gitignored, so they are built per machine, never
    # committed). Load, same bucket as staging: it produces loader INPUT and its
    # output filenames are the chain's own constants.
    "load": (
        "drydocs.loaders",
        "drydocs.cli",
        # S8 (2026-08-21): cli.py is a thin composition root; the verbs live in
        # per-domain modules that the root merges FLAT. They are classified load
        # like the root but are NOT entrypoints — only drydocs.cli may wire other
        # components, which is why resolve-cmdline-staging and lineage-review
        # (drydocs_lineage) stayed in the root instead of moving out.
        "drydocs.cli_schema",
        "drydocs.cli_ingest",
        "drydocs.cli_verify",
        "drydocs.cli_variables",
        "drydocs.cli_docs",
        "drydocs.cli_plan",
        # S13 (2026-08-27): the hoisted shared state the command modules and the
        # root both import (DAG: commands <- cli_shared -> nothing; root imports
        # both). Load like its consumers; NOT an entrypoint — it imports only
        # this component and core, and the root keeps the only wiring exemption.
        "drydocs.cli_shared",
        # S16 (2026-09-02): the optional CONSUMER command module the root discovers
        # (importlib.util.find_spec, registered last). The producer ships none; a consumer
        # writes one on the S8 module shape and PORT-MANIFEST carries it canonical-company.
        # Classified load so default-deny does not fail the consumer's tree by name.
        "drydocs.cli_consumer",
        "drydocs.snapshots",
        "drydocs.staging",
        "drydocs.cmdline_staging",
        # drydocs.docs_verify left this list at ADR 0018 D1 (2026-09-02): the module moved to
        # core at O58 and the stale entry sat here unnoticed until the MODULE_MAP completeness
        # guard (test_module_map_render.py) asked where it was told.
        "drydocs.seal_samples",
        # drydocs.pat_projection = projects the raw PAT team report into the two
        # files the team chain reads (G82). Load, same bucket and same
        # reason as seal_samples: loader INPUT, output filenames are the chain's.
        "drydocs.pat_projection",
        # drydocs.chain_inputs = the G78 chain-input resolver (fixture dir or declared
        # landing zone, fail-by-name before any write). Load: it decides what the
        # chain verbs read.
        "drydocs.chain_inputs",
        # drydocs.code_graph_freshness = U22: is the loaded code graph current vs the
        # snapshot series? Reads the graph + a snapshot header, writes nothing; it is
        # the load side's own "did my load land" question, so load.
        "drydocs.code_graph_freshness",
        # drydocs.docs_coverage = the Q16 software->documentation coverage report.
        # Same bucket as docs_verify for the same recorded reason, and it IMPORTS
        # docs_verify (count_query/locator_of) so the two verbs can never disagree
        # about whether a corpus is loaded — an import that is free inside one group
        # and would need a DECLARED_COMPONENT_IMPORTS exception anywhere else.
        # Carries docs_verify's RE-HOME caveat: move both to docmeta if that
        # component ever takes over corpus state.
        "drydocs.docs_coverage",
        # drydocs.source_registration = source-registration PoC (2026-09-09): the synthetic
        # stand-ins for every registered source (seeded generator, the gzip bundle,
        # extraction into the loaders' landing zones), the optional DuckDB load and
        # the DataHub MCP emission. Load, same bucket as seal_samples and for the
        # same reason: it produces loader INPUT at the zone paths the chains read.
        # The five-axis DESCRIPTOR it consumes is core (drydocs_core.source_descriptors):
        # pure config + registry resolve, no I/O.
        "drydocs.source_registration",
    ),
    # drydocs-review — SME review + graph acceptance + docs publish (Epic H).
    # The default-deny test below FORCES a new review module to be classified here
    # rather than being silently unguarded.
    # drydocs.fid_census = the K16 / doc-09 phase-0 measurement that the
    # fid-identity-and-scope gate cannot sign without. Classified REVIEW, not load or
    # config: it loads nothing and configures nothing — it produces the counts an SME
    # rules from, which is what this bucket is. Same reasoning that puts
    # source_mappings here. Imports NO first-party module (stdlib only) by design: the
    # method is ported to the company side, which is where the measured values live.
    "review": (
        "drydocs.review",  # the subpackage (ADR 0018 D4, 2026-09-02) - the component IS the directory
        # the flat names below are the one-cycle re-export SHIMS at the old paths; drop at the roll after next
        "drydocs.graph_verify",
        "drydocs.review_labels",
        "drydocs.source_mappings",
        "drydocs.graph_review",
        "drydocs.sme_notes",
        "drydocs.gate_pages",
        "drydocs.publishing",
        "drydocs.fid_census",
        # drydocs.run_as_detect = K25, fid_census's sibling: the cross-application
        # run_as detection the K17 gate's §G numbers come from. Same reasoning,
        # same stdlib-only porting discipline.
        "drydocs.run_as_detect",
    ),
    # drydocs-plan — backlog.yaml -> HTML project board renderer (Epic I).
    # plan_roadmap belongs HERE (unlike plan_ideas, below): it renders no
    # markdown — it consumes plan_board's published backlog shape, and a
    # within-group import is exactly what this classification permits.
    "plan": (
        "drydocs.plan",  # the subpackage (ADR 0018 D4, 2026-09-02) - the component IS the directory
        # the flat names below are the one-cycle re-export SHIMS at the old paths; drop at the roll after next
        "drydocs.plan_board",
        "drydocs.plan_roadmap",
    ),
    # drydocs-port — J41 port machinery. Its own group rather than a lodger in
    # "plan", and the reason is the same one that moved plan_ideas to docgen:
    # classify by WHAT IT DOES, not by which documents it happens to read. It
    # renders nothing, publishes no surface, and reads port-prompt.md only as
    # text. Import profile is stdlib + subprocess plus ONE core import,
    # drydocs_core.repo_paths (Idea-109 sweep, 2026-08-12) — no component and no
    # config. That import is itself pathlib-only, so what the old "stdlib and
    # nothing else" note was protecting still holds: the guards run without a
    # repository, and now the checks run against the CALLER's checkout rather than
    # certifying the main tree from inside a worktree.
    "port": (
        "drydocs.port",  # the subpackage (ADR 0018 D4, 2026-09-02) - the component IS the directory
        # the flat names below are the one-cycle re-export SHIMS at the old paths; drop at the roll after next
        "drydocs.port_preflight",
        "drydocs.port_backlog_union",
        "drydocs.port_rename_detect",
    ),
    # drydocs-docgen — canonical doc-outline validation + deterministic render + HITL
    # markup (Epic L). Imports only stdlib + config; never a component.
    #
    # plan_ideas lives HERE, not under "plan", and this guard is why (2026-08-05):
    # it was written as a plan module and the boundary test caught it importing
    # design_doc.render_body. The choice was duplicate a markdown renderer or file
    # it where markdown rendering lives — and a second md->HTML implementation
    # would drift from the Epic L one it was copied from. Its OUTPUT lands in
    # docs/plan/ (hence the name), but the COMPONENT is docgen: what it does is
    # render markdown deterministically. The same guard then caught the reverse
    # import (a borrowed stylesheet from plan_board) and was right twice — the
    # page now carries its own CSS, so docgen imports nothing but stdlib.
    "docgen": (
        "drydocs.docgen",  # the subpackage (ADR 0018 D4, 2026-09-02) - the component IS the directory
        # the flat names below are the one-cycle re-export SHIMS at the old paths; drop at the roll after next
        "drydocs.doc_outline",
        "drydocs.design_doc",
        "drydocs.doc_pdf",
        "drydocs.plan_ideas",
    ),
    # drydocs-remediation — detect → transform → prove → Jira (ADR 0002-B, G3).
    # Writes NO graph; Jira is the SoR; imports only drydocs_core.
    "remediation": ("drydocs_remediation",),
    # drydocs-lineage — proactive/curated cmd-line lineage → drydocs (ADR 0002 D2 C2, G4).
    "lineage": ("drydocs_lineage",),
    # drydocs-deepdoc — the corpus-driven investigator seeded from the grounded
    # graph (ADR 0002 D2 C3, G4; charter ruled at gate document-content-topology
    # G32, restated MM1): writes :Uncertain-labelled findings into `drydocs` with
    # reliability/trust stamps, never a relationship whose subject is not already
    # there. Never imports lineage — the components-don't-import-each-other test
    # IS the D2 separation; the core parser is an INPUT it shares, not a call.
    "deepdoc": ("drydocs_deepdoc",),
    # drydocs-docmeta — proactive document-corpus ingestion (ADR 0006, Q6).
    # Separate from deepdoc by the Q4 gate ruling: different duty cycles and
    # different write targets, with deepdoc a CONSUMER of this corpus. So the
    # components-don't-import-each-other rule IS that separation, exactly as it
    # is for lineage/deepdoc — a deepdoc dive that wants a Document cites it
    # through the graph, never by importing this package.
    "docmeta": ("drydocs_docmeta",),
    # drydocs-api — the thin read API over the graph (ADR 0005, O5). Read-only
    # (endpoint guard + READ routing); imports only drydocs_core; FastAPI is an
    # optional dependency group so the default install stays framework-free.
    "api": ("drydocs_api",),
    # drydocs-agents — the tiered read-only Q&A apps (ADR 0007, R2). Not a poetry
    # package: each ADK app puts REPO_ROOT on sys.path and imports the first-party
    # tree directly. Classified here so default-deny covers it.
    "agents": ("agents",),
    # libs — standalone helpers that depend on NOTHING first-party (today: the Oracle
    # Kerberos connection helper). Leaf infrastructure: its own bucket so a future
    # lib that starts importing a component fails the guard instead of sliding in.
    "libs": ("libs",),
}
ALL_COMPONENT_PREFIXES: tuple[str, ...] = tuple(
    p for prefixes in COMPONENT_GROUPS.values() for p in prefixes
)

# The CLI composition root legitimately wires MULTIPLE components together (it is the
# top-level orchestrator, not a peer component), so it is exempt from the
# "components don't import each other" rule below. It is STILL subject to default-deny
# classification (it lives in the `load` group) and to the core-imports-nothing rule.
# This resolves the ADR 0002-a entrypoint TODO (see MODULE_MAP.md): a port whose cli.py
# owns review/plan commands and imports those components passes the guard unchanged.
#
# drydocs.cli_consumer joined the set on 2026-09-03 (S16 follow-up): the consumer's
# command module is the consumer's COMPOSITION SURFACE - its verbs wire the consumer's own
# components (docmeta, publishing, sme_notes on the company side) exactly as the root's
# verbs wire lineage and fid_census - so it carries the same exemption. S16 (e) said "a
# consumer module is the outermost layer and may import anything" and then did not put
# it here; the first consumer module built against the seam failed
# test_components_do_not_import_each_other on eleven imports, which is how the gap was
# found. It is still default-deny classified (load) and still bound by
# core-imports-nothing; absent producer-side, which the entrypoint test tolerates.
ENTRYPOINT_MODULES: frozenset[str] = frozenset(
    {"drydocs.cli", "drydocs_core.cli", "drydocs.cli_consumer"}
)

# Declared cross-component allowances — module -> component prefixes it may import.
# DISTINCT from ENTRYPOINT_MODULES: these are NOT composition roots, they are the places
# where one component legitimately consumes another's PUBLISHED CONTRACT. Every entry is
# a reviewed exception, not a default; the guard still fails on anything not listed.
DECLARED_COMPONENT_IMPORTS: dict[str, tuple[str, ...]] = {
    # The agent tier's Tier-0 router dispatches to QuerySpecs, so the spec catalog and
    # the read-only guard ARE the agent contract (ADR 0007). `agents/` consumes the same
    # read surface the web console consumes over HTTP — just in-process.
    # FOLLOW-UP (not decided here): the structurally cleaner resolution is promoting
    # query_specs + guard into drydocs_core, per MODULE_MAP's "Future, land in core"
    # list. This entry records today's reality until that ruling is made.
    "agents.common.specs_catalog": ("drydocs_api",),
}

# ---- the join to the backlog's module registry (ADR 0018 D2) ------------------------------

#: Component group -> the `modules.yaml` module it belongs to. Every group names one; the
#: guard asserts the name exists. `libs` is its own module by the 2026-09-02 ruling (Q1): a
#: server deployment is configured differently and never calls it, so it is a library beside
#: the product, not a part of core.
COMPONENT_MODULE: dict[str, str] = {
    "load": "drydocs-load",
    "review": "drydocs-review",
    "plan": "drydocs-plan",
    "port": "drydocs-port",
    "docgen": "drydocs-docgen",
    "remediation": "drydocs-remediation",
    "lineage": "drydocs-lineage",
    "deepdoc": "drydocs-deepdoc",
    "docmeta": "drydocs-docmeta",
    "api": "drydocs-api",
    "agents": "drydocs-agents",
    "libs": "drydocs-libs",
}

#: The module that owns `CORE_PREFIXES`.
CORE_MODULE = "drydocs-core"

#: Modules in `modules.yaml` that own NO Python package - work areas and the two
#: non-Python surfaces (S7's second clause: `web/` keeps its ecosystem name). The guard
#: asserts modules.yaml == {CORE_MODULE} | COMPONENT_MODULE.values() | this set, so a
#: module cannot be registered without saying which kind it is.
NON_PYTHON_MODULES: frozenset[str] = frozenset(
    {
        "drydocs-web",  # web/ - the React/TS console (Vite app; not a Python package)
        "reference",  # reference/ - external platforms, standards, research
        "taxonomy",  # config/taxonomy/ - pure classification imports
        "ontology",  # drydocs_core/ontology data + knowledge/ontology/ - the registries
        "config",  # config/ - precedence, source registry, crosswalks, gate prompts
        "graph-infra",  # Neo4j topology, provisioning, the local containers
        "docs",  # docs/, knowledge/ prose, the plans and ADRs
    }
)

#: Top-level directory -> owning module, for every first-party surface that is not a
#: Python package root (ADR 0018 D3). Rendered into MODULE_MAP.md's "Non-Python surfaces"
#: table. A directory here is OWNED - which module's ruling covers it - which is the
#: question the copier asks and PORT-MANIFEST (what to DO with it at a port) does not
#: answer. Python package roots are owned through COMPONENT_GROUPS / CORE_PREFIXES and are
#: not repeated here.
SURFACE_OWNERS: dict[str, str] = {
    "web": "drydocs-web",
    # O72: the Compose stack's Dockerfiles and proxy renderer. Owned by
    # drydocs-web because the stack exists to serve the console — the API and
    # agent images are there as its upstreams, the way ADR 0020 has them.
    "deploy": "drydocs-web",
    "agents": "drydocs-agents",
    "libs": "drydocs-libs",
    "graph-tests": "drydocs-review",  # graph_verify reads the TC suites; review's acceptance data
    "drydocs-icons": "drydocs-web",  # render_software_registry copies them to web/public/vendor-icons/
    "knowledge/depgraph-snapshots": "drydocs-load",  # the snapshot ritual and its ledger
    "knowledge/upgrade-plans": "docs",  # Internal-Public design prose
    "knowledge": "docs",
    "reference": "reference",
    "external": "reference",
    "config": "config",
    "docs": "docs",
    "scripts": "drydocs-load",  # renderers and rituals; each script's SUBJECT owns its logic
    "internal": "docs",  # the publish-boundary twin; never crosses
}


def component_of(module: str) -> str | None:
    """The component GROUP a dotted module name belongs to; ``"core"`` for core; ``None``
    when unclassified (which the boundary test fails as UNCLASSIFIED)."""
    if _matches(module, CORE_PREFIXES):
        return "core"
    owning = [g for g, prefixes in COMPONENT_GROUPS.items() if _matches(module, prefixes)]
    return owning[0] if len(owning) == 1 else None


def module_of(component: str) -> str:
    """The backlog module a component group belongs to (``"core"`` -> drydocs-core)."""
    return CORE_MODULE if component == "core" else COMPONENT_MODULE[component]


def _matches(module: str, prefixes: tuple[str, ...]) -> bool:
    return any(module == p or module.startswith(p + ".") for p in prefixes)


# ── CORE12 (2026-09-10): WHAT OF CORE IS PUBLIC ──────────────────────────────
#
# The third axis, and the one the core report (2026-09-07, S6/T5) said core did
# not have: not who may import core (CORE_PREFIXES), not what a component owns
# (COMPONENT_GROUPS), but WHICH OF CORE'S OWN MODULES a component may name.
#
# THE MEASUREMENT THAT DECIDED THE SHAPE. The report counted 22 of 34 modules
# imported by components from outside `__all__`. Re-measured at HEAD, it is 32
# of 39 - and the interesting half is the other seven: EVERY top-level module
# and subpackage in core is imported from outside it. There are no internals.
# So the question was never "sort the existing modules into public and private";
# it is that core has no line at all, and every module added to it becomes
# public by accident. The gap widened by ten in three days, which is the
# report's "compounds fastest" playing out.
#
# WHY A REGISTRY AND NOT `__all__` (the ruling; the ADR draft is in CORE12's
# item notes for Lane A to mint):
#
#   1. `__init__.py` EAGERLY imports the seven names in `__all__`. Growing that
#      list to 39 would make `import drydocs_core` pull in yaml, neo4j,
#      pydantic-settings and the rest - and this repo already guards import
#      order and cost with a subprocess-per-import test (S13,
#      tests/unit/test_cli_import_order.py) because that gap once shipped a
#      cycle. A contract must not be paid for at import time.
#   2. `__all__` governs `from drydocs_core import *`, which nothing in this
#      repo does. It is the wrong instrument: it declares names for star-import,
#      not an import contract between packages.
#   3. A declared registry plus a default-deny guard is what this repo already
#      does everywhere else it needs one - CORE_PREFIXES and COMPONENT_GROUPS
#      above, `drydocs_core.check_outcome.PROBES` for probes, `MODULE_MAP.md`
#      rows for placement. Registration is the act. A name that is not here is
#      not importable by a component, and the guard says so by name.
#
# `__all__` in `__init__.py` therefore stays as it is - a correct star-import
# surface - and its docstring points here for the contract.
#
# WHAT THIS LIST IS NOT: an endorsement that all 39 should be public. It is the
# contract AS IT STANDS, recorded so it can be argued with. Narrowing it is a
# later item and a real decision, per module, with the call sites in hand.
# What it buys today is that module 40 cannot slip in undeclared: adding a core
# module a component imports now means adding its name HERE, which is the moment
# someone has to decide whether it belongs in the contract at all.
#
# Grouped by what each is FOR, so a new module lands in a group rather than at
# the end of an alphabetical list - the group is the first question to answer
# about it.
PUBLIC_MODULES: frozenset[str] = frozenset(
    {
        # -- the historical contract: the seven `__init__.py` eagerly imports --
        "adapters",
        "config",
        "models",
        "ontology",
        "orchestration",
        "precedence",
        "source_registry",
        # -- paths and roots. `repo_paths` is the most-imported module in core
        #    (31 component call sites) and was the report's headline: nothing
        #    declared it was ever promised, so changing its signature was either
        #    a routine edit or a breaking change to a third of the repo, and the
        #    package did not say which. It says now.
        "repo_paths",
        "data_root",
        "data_zones",
        "landing_zones",
        "env_refs",
        "env_doctor",
        # -- the graph seam --
        "neo4j_client",
        "notifications",
        "cypher_split",
        "schema",
        # -- logging and run records --
        "run_log",
        "log_kinds",
        "log_estate",
        # -- declared configuration and registries --
        "source_descriptors",
        "source_bindings",
        "registry_view",
        "mapping_store",
        "manual_mappings",
        "data_centers",
        "console_personas",
        "edition_registry",
        "component_map",
        "yaml_fragments",
        # -- planning and documentation surfaces --
        "backlog_store",
        "docs",
        "docs_verify",
        "doc_anchors",
        "glossary",
        "ui_concepts",
        # -- typed results and analysis --
        "check_outcome",
        "entity_extract",
        "fix_tracking",
    }
)
