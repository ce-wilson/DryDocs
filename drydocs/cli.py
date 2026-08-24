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

import logging
import uuid
from pathlib import Path
from typing import NamedTuple

import typer
from rich.console import Console
from rich.table import Table

import drydocs_core
from drydocs_core.adapters import CsvAdapter, OracleAdapter
from drydocs_core.config import load_settings
from drydocs_core.neo4j_client import Neo4jClient
from drydocs_core.repo_paths import repo_root
from drydocs_core.run_log import LoaderRunLog
from drydocs_core.source_registry import (
    RetiredSourceIdError,
    SourceRegistry,
    UnconfirmedSourceError,
    UnknownSourceError,
)

from . import seal_samples as seal_samples_mod
from .loaders import seal_applications as seal_apps_mod
from .loaders import seal_contacts as seal_contacts_mod
from .loaders.batch_port_orchestrator import (
    BatchPortOrchestratorLoader,
)
from .loaders.bmc_docs import (
    BmcDocsLoader,
)
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
    CodeSnapshotLoader,
    CodeTreeLoader,
)
from .loaders.controlm_conditions_in import ControlMConditionsInLoader
from .loaders.controlm_conditions_out import ControlMConditionsOutLoader
from .loaders.controlm_dependencies_derived import ControlMDependenciesDerivedLoader
from .loaders.controlm_folders import ControlMFoldersLoader
from .loaders.controlm_hosts import ControlMHostsLoader
from .loaders.controlm_jobs import ControlMJobsLoader
from .loaders.doc_traceability import (
    DesignDocFeedbackAdapter,
    DesignDocSectionsAdapter,
    DesignDocSectionsLoader,
    DocFeedbackLoader,
    DocTraceabilityLoader,
    TraceabilityMatrixAdapter,
)
from .loaders.email_extracts import EmailExtractsLoader
from .loaders.essential_graphrag import (
    EssentialGraphragLoader,
)
from .loaders.folder_attribution import (
    FolderAttributionLoader,
)
from .loaders.manual_loads import (
    ManualSealAttributionLoader,
)
from .loaders.server_inventory import ServerInventoryLoader
from .loaders.software_registry import (
    SoftwareRegistryLoader,
)
from .loaders.vendor_docs import VendorDocsLoader

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

#: The checkout the CALLER is standing in, for the repo-CONTENT defaults below
#: (Idea-109). The two package-internal constants in this module deliberately do
#: NOT route through it — see each one's note.
_REPO_ROOT = repo_root(Path(__file__).resolve().parents[1])

# Bundled CSV samples ship inside the package so dev-mode commands work
# from any cwd — including from an installed wheel where there is no repo
# root. Override with --samples-dir to point at an alternate fixture set.
# PACKAGE-INTERNAL on purpose, and the sentence above is the reason: an
# installed wheel HAS no checkout to follow, so `__file__` is the only anchor
# that answers. (`drydocs.seal_samples.DEFAULT_SAMPLES_DIR` names the same
# directory and DOES follow the caller — it is a build script's WRITE target,
# not a runtime read default.)
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
    # Z3 (server inventory; gate server-location-ontology):
    "server_inventory": ServerInventoryLoader,
    # bmc-docs lexical graph (Document -> Chunk):
    "bmc_docs": BmcDocsLoader,
    # Essential GraphRAG ebook lexical graph (Q2 experiment):
    "email_extracts": EmailExtractsLoader,
    "essential_graphrag": EssentialGraphragLoader,
    # Doc traceability + review feedback (L7 connector #1):
    "doc_sections": DesignDocSectionsLoader,
    "doc_traceability": DocTraceabilityLoader,
    "doc_feedback": DocFeedbackLoader,
}

# PACKAGE-INTERNAL: the .sql files are package data and travel with it.
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

# ---- G79: the reference chains, ONE SUBJECT EACH -----------------------------
# Until 2026-08-23 these seven loaders were a single `refresh-reference` tuple
# spanning THREE unrelated sources with three different refresh rhythms. That
# bundle had no organising principle, which is precisely why a loader could fall
# out of it and nothing noticed (G78's dropped dev_teams; G80's two orphans).
# Each command now covers ONE SUBJECT, and the subject — not the chain's
# accidental order — is what decides membership. Two subjects may legitimately
# draw on one source system (dev teams and the product catalog both come from
# PAT); what must not happen is the reverse, one command spanning three sources,
# because then nothing can say whether the command is complete.
#
# Shape is unchanged: (cli name, loader class, bundled sample filename).

# Subject: the product catalog hierarchy (LOB -> product line -> product).
# Order matters — hierarchy parents before children.
CATALOG_CHAIN: tuple[tuple[str, type, str], ...] = (
    ("catalog_lobs", CatalogLOBsLoader, "catalog_lobs__sample.csv"),
    ("product_lines", ProductLinesLoader, "product_lines__sample.csv"),
    ("products", ProductsLoader, "products__sample.csv"),
)

# Subject: business applications and the people attributed to them.
# SEAL apps before contacts — a contact MATCHes the application it hangs off.
BUSINESS_APPLICATION_CHAIN: tuple[tuple[str, type, str], ...] = (
    (
        "seal_applications",
        seal_apps_mod.SealApplicationsLoader,
        "seal_application_data__sample.csv",
    ),
    ("seal_contacts", seal_contacts_mod.SealContactsLoader, "seal_contact_data__sample.csv"),
)

# Subject: the delivery organisation — teams, the people in them, and the
# team<->application alignment. pat_product_mapping sits HERE and not with the
# catalog: its subject is which team is aligned to which application, which is an
# org fact that happens to cite product ids. Mapping stays last, as it always was.
# pat_team_roles JOINS THE CHAIN HERE (G79 (b)) — gate-confirmed at C9 on
# 2026-07-18, carrying a loader class and cypher, and yet reachable only as
# `drydocs load pat_team_roles`, so no operator path had ever run it.
TEAM_CHAIN: tuple[tuple[str, type, str], ...] = (
    ("dev_teams", DevTeamsLoader, "dev_teams__sample.csv"),
    ("pat_team_roles", PatTeamRolesLoader, "pat_team_roles__sample.csv"),
    ("pat_product_mapping", PatProductMappingLoader, "pat_product_mapping__sample.csv"),
)

#: command -> the ordered chain it runs. THE registry: every enumeration of "the
#: sequenced CSV chains" derives from this one mapping — COMMAND_LOADERS below,
#: the load-map render's declared-input walk, and the guards that check chain
#: bindings and bundled fixtures. Splitting a chain again is an edit HERE and
#: nowhere else, which is the property the single-tuple version did not have.
CHAINS: dict[str, tuple[tuple[str, type, str], ...]] = {
    "refresh-catalog": CATALOG_CHAIN,
    "refresh-applications": BUSINESS_APPLICATION_CHAIN,
    "refresh-teams": TEAM_CHAIN,
}


def chain_steps() -> tuple[tuple[str, type, str], ...]:
    """Every (name, loader, fixture) triple of every subject chain, in order."""
    return tuple(step for chain in CHAINS.values() for step in chain)


# ---- G79 (e): the one load-order invariant the split must not lose -----------
#: Loaders that can MINT a :BusinessApplication. seal_applications must run
#: BEFORE any of them, because SEAL is the authority for application identity and
#: anything else reaching an application node first would decide that identity by
#: accident of order. The producer satisfied this only as a POSITION IN A TUPLE,
#: which is exactly the kind of accident a split loses; now it is a DECLARATION
#: with a guard (tests/unit/test_load_map_declarations.py), so the next reorder
#: fails loudly instead of silently.
#:
#: Producer-side this is currently satisfied twice over: pat_product_mapping's
#: cypher MERGEs on the SAME neutral app_id key seal_applications uses, so there
#: is no stub and no second node. The COMPANY is not so lucky — its
#: pat_app_links.cypher still MERGEs on the pre-S3 seal_id with is_stub=true and
#: collides on the subsequent SET (SME hit it live 2026-08-11, RELAY-8) — which
#: is why the invariant is written down here rather than left to hold by luck.
BUSINESS_APPLICATION_MINTERS: frozenset[type] = frozenset({PatProductMappingLoader})

#: The loader that is the AUTHORITY for application identity.
APPLICATION_IDENTITY_LOADER: type = seal_apps_mod.SealApplicationsLoader

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
    **{cmd: tuple(cls for _, cls, _ in chain) for cmd, chain in CHAINS.items()},
    # The deprecated alias runs the union of all three, in sequence order (S8's
    # m1-verify -> verify-reference precedent: an alias is a real command that
    # delegates, never a second implementation).
    "refresh-reference": tuple(cls for _, cls, _ in chain_steps()),
    "ingest-controlm": tuple(
        cls for _, cls, *_ in CONTROLM_NODE_STAGES + CONTROLM_PART2_STAGES + CONTROLM_REL_STAGES
    ),
    "load-software-registry": (SoftwareRegistryLoader,),
    "load-batch-orchestrators": (BatchPortOrchestratorLoader,),
    "load-code-snapshot": (CodeSnapshotLoader, CodeTreeLoader),
    "load-bmc-docs": (BmcDocsLoader,),
    "load-vendor-docs": (VendorDocsLoader,),
    "load-doc-traceability": tuple(cls for cls, _, _ in DOC_TRACEABILITY_CHAIN),
    "load-email-extracts": (EmailExtractsLoader,),
    "load-essential-graphrag": (EssentialGraphragLoader,),
    "load-folder-attribution": (FolderAttributionLoader,),
    "load-server-inventory": (ServerInventoryLoader,),
    "load-manual-mappings": (ManualSealAttributionLoader,),
}

# Loader-running commands that are OPERATOR-DRIVEN, not sequence members:
# `load` runs any single LOADER_REGISTRY loader ad hoc; manual mappings load
# when an SME authors one (manifest-gated), not on a refresh cadence.
# `refresh-reference` joins them at G79: it is now a DEPRECATED ALIAS that
# delegates to the three subject commands, so it runs loaders but is not itself a
# sequence member — the three steps it delegates to are. Declaring it here is what
# keeps "every loader-running command is placed" true without putting a fourth,
# redundant step in the canonical sequence.
AD_HOC_COMMANDS: frozenset[str] = frozenset({"load", "load-manual-mappings", "refresh-reference"})

# ---- G80: no loader is silently outside every chain -------------------------
# A LOADER_REGISTRY loader that no COMMAND_LOADERS command runs is reachable
# ONLY as `drydocs load <name>` — registered, green, and never executed by any
# operator path. That is the G59 unchained-supplement class one registry over,
# and it is how area_products and pat_team_roles sat runnable-by-name for weeks
# with nothing turning red. A loader deliberately outside every chain needs its
# reason here (the SCHEDULED_INGEST_EXCLUSIONS idiom): cli name -> why.
# tests/unit/test_load_map_declarations.py fails naming any loader that is
# neither chained nor excused, and the load-map render publishes this dict so
# the omission is a decision on record rather than silence.
UNCHAINED_LOADER_EXCLUSIONS: dict[str, str] = {
    "area_products": (
        "there is nothing to load: the catalog capture records `area_products: 0` "
        "against the standing `area-product-missing` open question "
        "(config/taxonomy/lob-product-team.yaml), so this is a real source grain "
        "we do not yet receive rows for. Wiring an empty step into refresh-catalog "
        "would make every run report a step that loads nothing, which reads as a "
        "broken load rather than an absent feed. G79 (b) considered it and left it "
        "out on that basis; revisit when the open question closes and the extract "
        "carries area-product rows"
    ),
}


def unchained_registry_loaders() -> tuple[tuple[str, type], ...]:
    """Every LOADER_REGISTRY ``(name, class)`` no COMMAND_LOADERS command runs.

    Excused or not — the guard subtracts :data:`UNCHAINED_LOADER_EXCLUSIONS`,
    the load-map render joins the exclusions on as reason-or-null. ONE
    predicate for both so the suite and the surface cannot drift apart.
    """
    chained = {cls for classes in COMMAND_LOADERS.values() for cls in classes}
    return tuple((name, cls) for name, cls in sorted(LOADER_REGISTRY.items()) if cls not in chained)


def unchained_loaders() -> tuple[str, ...]:
    """Registry loaders in NO command's chain with NO written reason.

    Computed here, not in the test, so a consumer repo whose chains
    legitimately differ (the company chain carries sub_lobs where the producer
    carries pat_product_mapping) gets the same protection from its OWN
    registry, chains and exclusions — the test stays repo-agnostic (G59 shape).
    """
    return tuple(
        name
        for name, _cls in unchained_registry_loaders()
        if name not in UNCHAINED_LOADER_EXCLUSIONS
    )


#: Chain-declared sample files that are GENERATED PER MACHINE and never
#: committed (G78's SEAL fixtures): filename -> how to build one. The load-map
#: render lists these as written-down absences, PRESENCE-INDEPENDENT — probing
#: the filesystem would make the committed render flap between a machine that
#: has generated them and one that has not.
GENERATED_SAMPLE_FILES: dict[str, str] = {
    seal_samples_mod.APPLICATION_SAMPLE: (
        "generated per machine from the capture by scripts/build_seal_samples.py "
        "— run it after checkout; the fixture derives from internal SEAL data "
        "shapes and is deliberately not committed"
    ),
    seal_samples_mod.CONTACT_SAMPLE: (
        "generated per machine from the capture by scripts/build_seal_samples.py "
        "— run it after checkout; the fixture derives from internal SEAL data "
        "shapes and is deliberately not committed"
    ),
}

# (3) THE canonical ordered load sequence — declared once; ingest.sh and the
# startup/refresh runbook derive from it (N6 retires their independent copies).
# mode: "standing" = every full refresh; "optional" = site/experiment decision;
# "gated" = blocked on a source confirmation or precondition named in the note.
#
# N6 (2026-08-04) added `profiles`. Before it, the two operator surfaces ran
# DIFFERENT step sets and nothing said whether that was a decision or drift —
# which is the actual defect, because a deliberate subset and an accidental one
# look identical from outside. A profile names an operator surface; membership
# is declared per step; each surface then filters the ONE sequence instead of
# keeping a list of its own.


class LoadStep(NamedTuple):
    """One step of the canonical sequence.

    A NamedTuple, not a bare 3-tuple, because N6 widened it: unpacking sites
    that assumed ``for command, mode, note in ...`` now fail loudly at import
    rather than silently binding ``note`` to a set of profile names.

    ``profiles`` is either a declared set or :data:`DERIVED` (G79 (c)). DERIVED
    means the answer is computed from the CADENCE of the sources this step's
    loaders read — there is no literal to maintain and therefore none to drift.
    Resolve it with :func:`step_profiles`, never by reading the field.
    """

    command: str
    mode: str
    profiles: frozenset[str] | None
    note: str


#: Sentinel for :attr:`LoadStep.profiles`: this step's operator surfaces are
#: DERIVED from its sources' declared cadence, not written down here. G79 (c) —
#: "the source dictates how often it refreshes" is now true in code rather than
#: true in a comment.
DERIVED: None = None

#: cadence (config/source-registry.yaml) -> the operator surfaces that run it.
#: THE mapping, and the only place a rhythm becomes a surface. Adding a cadence
#: value means adding a row here, which is the point: an unmapped cadence fails
#: loudly rather than quietly running nowhere.
CADENCE_PROFILES: dict[str, frozenset[str]] = {
    # A slow reference feed. Not on the batch path: re-loading the catalog and
    # SEAL feeds every ingest would re-read unchanged sources many times a week.
    "weekly": frozenset({"cold-start"}),
    # Moves with the Control-M estate, so every scheduled ingest wants it.
    "batch": frozenset({"cold-start", "scheduled-ingest"}),
    # Changes when the REPO changes, never when a data source does — so it rides
    # a rebuild (cold start), not the batch schedule.
    "repo-change": frozenset({"cold-start"}),
}


class CadenceDerivationError(RuntimeError):
    """A DERIVED step whose cadence cannot be resolved — never a silent empty set."""


def step_sources(command: str) -> tuple[str, ...]:
    """The source-registry ids this command's loaders declare, sorted."""
    return tuple(
        sorted({cls.source_id for cls in COMMAND_LOADERS.get(command, ()) if cls.source_id})
    )


def step_profiles(step: LoadStep, registry: SourceRegistry | None = None) -> frozenset[str]:
    """The operator surfaces that run *step* — declared, or derived from cadence.

    A DERIVED step reads every source its loaders declare and maps the common
    cadence through :data:`CADENCE_PROFILES`. THE DIVERGENCE RULE, and it is
    deliberately strict: if a command's sources disagree about cadence there is
    no honest answer, so this RAISES rather than picking one. That is a ruling
    the SME owes, surfaced the moment it first matters — which is exactly what
    the old hand-assigned tuple could never do, because a tuple is equally happy
    describing a command whose sources agree and one whose sources do not.
    """
    if step.profiles is not None:
        return step.profiles
    reg = registry if registry is not None else _source_registry()
    sources = step_sources(step.command)
    if not sources:
        raise CadenceDerivationError(
            f"step {step.command!r} is DERIVED but runs no source-declaring loader — "
            "a step with no source has no cadence to read; declare its profiles."
        )
    cadences = {}
    for sid in sources:
        try:
            cadences[sid] = reg.get(sid).cadence
        except Exception as exc:  # unknown id is a registry defect, not a profile answer
            raise CadenceDerivationError(f"step {step.command!r}: source {sid!r}: {exc}") from exc
    missing = sorted(sid for sid, cad in cadences.items() if not cad)
    if missing:
        raise CadenceDerivationError(
            f"step {step.command!r} is DERIVED but source(s) {missing} declare no "
            "cadence — add `cadence:` to the registry row, or declare the step's "
            "profiles explicitly."
        )
    distinct = set(cadences.values())
    if len(distinct) > 1:
        detail = ", ".join(f"{sid}={cad}" for sid, cad in sorted(cadences.items()))
        raise CadenceDerivationError(
            f"step {step.command!r} spans sources with DIFFERENT cadences ({detail}). "
            "A command covering one subject may read several sources, but they must "
            "share a rhythm — otherwise which surface runs it has no honest answer. "
            "Split the command, or rule the cadences into agreement (G79 (c))."
        )
    cadence = distinct.pop()
    try:
        return CADENCE_PROFILES[cadence]
    except KeyError as exc:
        raise CadenceDerivationError(
            f"step {step.command!r}: cadence {cadence!r} is not in CADENCE_PROFILES — "
            f"declared values: {sorted(CADENCE_PROFILES)}"
        ) from exc


#: The operator surfaces that RUN a filtered view of the sequence. Adding one
#: means adding a surface, not a preference — every profile here has a real file
#: that derives from it and a guard that proves the derivation.
LOAD_PROFILES: dict[str, str] = {
    "scheduled-ingest": (
        "scripts/ingest.sh — unattended scheduled ingestion (Control-M / cron). "
        "The Control-M estate chain plus what it needs and the invariant checks; "
        "deliberately NOT a full refresh (see SCHEDULED_INGEST_EXCLUSIONS)"
    ),
    "cold-start": (
        "docs/design/drydocs-startup-refresh-runbook.md Appendix B — a human "
        "bringing an empty container all the way up, so every standing step runs "
        "plus the self-documentation corpus that makes the graph demonstrable"
    ),
}

#: N6's RULING, made machine-checkable: every `standing` step the scheduled
#: ingest does NOT run needs a reason here. Without this the omission of four
#: steps from ingest.sh was indistinguishable from someone forgetting them.
#: (`optional`/`gated` steps need no entry — not running them is what those
#: modes already mean.) Guarded by tests/unit/test_load_sequence_surfaces.py.
#:
#: SHRANK AT G79, and the reason matters: a step whose profiles are DERIVED owes
#: nothing here, because its source's declared `cadence` IS the written reason —
#: and a better one, since a reader can check it against the registry instead of
#: taking a sentence on trust. The old `refresh-reference` entry said in prose
#: exactly what `cadence: weekly` now says in data. What is left are the
#: omissions cadence cannot explain, which are the SEMANTIC ones.
SCHEDULED_INGEST_EXCLUSIONS: dict[str, str] = {
    "load-software-registry": (
        "repo-triggered, not estate-triggered: the registry is loaded from "
        "config/taxonomy/software-registry.yaml, so it changes when the REPO "
        "changes and not when Control-M data does. The runbook's own framing is "
        "'after ANY container rebuild', which is the cold-start profile"
    ),
    "load-bmc-docs": (
        "same class as load-software-registry — a vendor document corpus read "
        "from external/orchestration/bmc-controlm/. It moves with the repo, not "
        "with the batch estate, and re-chunking a static corpus on every ingest "
        "is cost for no change"
    ),
    "docs-verify": (
        "it would FAIL this profile by design. docs-verify reconciles the "
        "doc-source registry against what the graph holds, and the scheduled "
        "profile deliberately loads no doc corpora — under `set -e` a non-zero "
        "exit here would abort a Control-M ingest over a reconciliation that was "
        "never supposed to hold on this path"
    ),
}


_ALL = frozenset({"scheduled-ingest", "cold-start"})
_COLD = frozenset({"cold-start"})
_NONE: frozenset[str] = frozenset()

CANONICAL_LOAD_SEQUENCE: tuple[LoadStep, ...] = (
    LoadStep("check", "standing", _ALL, "Neo4j + APOC reachable"),
    LoadStep("bootstrap", "standing", _ALL, "constraints + ontology seed"),
    LoadStep(
        "bootstrap-schema-graph",
        "standing",
        _ALL,
        "schema meta-graph rendered + applied to ddschema (C21/G51). Targets a "
        "DIFFERENT database, so it is chain-independent of everything below and "
        "could sit anywhere — it sits here because a wiped DBMS is exactly when "
        "the meta-graph gets forgotten. ADDED 2026-08-04: it was already in both "
        "operator surfaces (scripts/ingest.sh step 3/6 and the startup runbook's "
        "Appendix B) and missing ONLY here, so the generated load-map published "
        "15 steps while both real paths ran 16",
    ),
    LoadStep("apply-supplements", "standing", _ALL, "the ONE verified supplement chain (G29)"),
    LoadStep(
        "refresh-catalog",
        "standing",
        DERIVED,
        "product catalog hierarchy: LOB -> product line -> product (G79 split)",
    ),
    LoadStep(
        "refresh-applications",
        "standing",
        DERIVED,
        "business applications + their contacts (SEAL). Sits BEFORE refresh-teams "
        "because SEAL is the authority for application identity and refresh-teams "
        "carries a :BusinessApplication minter — the G79 (e) invariant, declared in "
        "BUSINESS_APPLICATION_MINTERS and guarded, not left to tuple order",
    ),
    LoadStep(
        "refresh-teams",
        "standing",
        DERIVED,
        "the delivery organisation: dev teams, team roles (wired at G79 (b) after "
        "never having run) and the team<->application alignment",
    ),
    LoadStep(
        "ingest-controlm", "standing", _ALL, "folders -> jobs -> conditions -> derived deps (M3)"
    ),
    LoadStep("load-software-registry", "standing", _COLD, "vendor/product registry (plan 07)"),
    LoadStep(
        "load-batch-orchestrators",
        "optional",
        _NONE,
        "declared batch-port USES_SOFTWARE edges (C14); MATCH-only — needs the "
        "SEAL chain and the software registry already loaded",
    ),
    LoadStep("load-bmc-docs", "standing", _COLD, "BMC corpus lexical graph"),
    LoadStep(
        "load-vendor-docs",
        "optional",
        _NONE,
        "Q13 captured vendor documentation (verbatim, out-of-repo capture -> "
        "convert -> load); taxonomy only, gated until its corpus is confirmed",
    ),
    LoadStep("load-essential-graphrag", "optional", _NONE, "Q2 book corpus -> drydocs (G102 fold)"),
    LoadStep(
        "load-email-extracts",
        "optional",
        _NONE,
        "Q10 failure/activity email extracts -> lexical graph (assignment edge gated)",
    ),
    LoadStep(
        "load-doc-traceability",
        "optional",
        _COLD,
        "L7 self-documentation (design docs + feedback). The one `optional` step "
        "a profile runs: a cold start is exactly when the doc graph is empty, and "
        "it stayed missing from the runbook until Rev 5 for want of saying so",
    ),
    LoadStep(
        "load-code-snapshot",
        "optional",
        _NONE,
        "G33 self-documentation; ritual-driven (newest committed snapshot)",
    ),
    LoadStep(
        "load-folder-attribution",
        "gated",
        _NONE,
        "K8 folder-grain attribution: the app-code defined mapping "
        "(config/overrides/app-code-mappings.csv) + the stg_app_fact fallback "
        "feed need ingest-controlm + refresh-reference first (gate §E "
        "preconditions)",
    ),
    LoadStep(
        "load-server-inventory",
        "optional",
        _NONE,
        "Z3 server inventory: per-application infra exports (the "
        "internal/server-inventory/ landing zone) -> :Server/:DataCenter + "
        "the tiered ExecutionHost join; the app port leg is MATCH-only, so "
        "refresh-reference (SEAL) and ingest-controlm (hosts) first make it "
        "complete rather than valid",
    ),
    LoadStep("m1-verify", "standing", _ALL, "M1 invariants"),
    LoadStep("m3-verify", "standing", _ALL, "M3 invariants"),
    LoadStep(
        "docs-verify",
        "standing",
        _COLD,
        "doc corpora declared vs loaded (registry-driven; non-zero on wrong-db)",
    ),
)


def load_profile(name: str) -> tuple[LoadStep, ...]:
    """The steps ONE operator surface runs, in canonical order.

    This is the derivation N6 exists for: ``scripts/ingest.sh`` calls this at
    run time, so that script has no sequence of its own left to drift from.
    The runbook's Appendix B cannot call anything — it is prose — so its copy is
    held to the same answer by tests/unit/test_load_sequence_surfaces.py.
    """
    if name not in LOAD_PROFILES:
        raise KeyError(f"unknown load profile {name!r} — declared: {sorted(LOAD_PROFILES)}")
    return tuple(step for step in CANONICAL_LOAD_SEQUENCE if name in step_profiles(step))


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
    configured target DB (post-G102 every content load targets ``drydocs``;
    the override survives for ``ddschema`` and transitional sweeps)."""
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

    ``run_as`` IS UPPER-CASED HERE, and the reason is worth stating because the
    obvious alternative is wrong. psgmgr stores ``CM_DEF_VJOB.OWNER`` ALL UPPER
    (SME 2026-08-12), while the SQL binds ``J.OWNER = :run_as`` as an exact
    match — so a lower-case ``--run-as`` silently returned ZERO ROWS and looked
    like "that account runs nothing". Normalizing the BIND VALUE fixes it for
    free: the column is untouched, so the predicate stays sargable on a ~240k-row
    table. Wrapping the COLUMN (``UPPER(J.OWNER) = ...``) would fix the same
    symptom while defeating a plain b-tree index — and would be pure loss here,
    since a column already upper at rest makes ``UPPER()`` on it a no-op.
    Case-folding the DIRECTORY side is a separate matter and does not belong in
    this bind (gate fid-identity-and-scope §Q6).
    """
    return {
        "folder_filter": folder,
        "run_as": run_as.upper() if run_as else run_as,
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


# --- per-domain command modules (S8) -----------------------------------------
# The root registers each domain's Typer FLAT, so every verb keeps its top-level
# name. Imported at the bottom on purpose: the submodules import the shared
# state defined above, and this is the one point where the circular edge is
# safe. The three verbs above (resolve-cmdline-staging, lineage-review,
# fid-census) stay here because they wire another component (drydocs_lineage,
# drydocs.fid_census) — the composition root is the only module
# exempt from the component-import invariant (ENTRYPOINT_MODULES), and S8 adds
# no new exemption.
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
    app()
