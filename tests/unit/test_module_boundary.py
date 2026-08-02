"""Module-boundary guard for the drydocs-core extraction (ADR 0002 / 0002-a, Phase B).

Phase B is PHYSICAL (2026-07-10, thin variant per ADR 0002-a-1): the core modules live in
``drydocs_core/`` for real; the ``drydocs`` package is the component remainder (load /
review / plan / docgen — the rename to per-component packages is Phase C). This test
enforces the boundary across BOTH packages, per ``MODULE_MAP.md``:

  * **Core imports nothing from any component.** The parse / model / config / driver layer
    (``drydocs_core``: models, adapters, neo4j_client, config, precedence, source_registry,
    ontology, controlm) must never import the component layer.
  * **Components import only core, never each other.** (The load-cadence staging builder
    lives component-side as ``drydocs.staging`` — 0002-a §6 borderline decision.)

It parses files with ``ast`` and never imports ``drydocs`` itself, so it has no DB or driver
side effects and runs anywhere.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
# Packages scanned for the boundary: the component remainder, physical core, the
# remediation component (G3 scaffold, 2026-07-10), and — added 2026-07-25 — the two
# first-party trees that were previously OUTSIDE the guard entirely (`agents/`, the
# ADK apps of ADR 0007; `libs/`, the standalone connection helper). Neither is a
# poetry package, so both were invisible to default-deny while `drydocs-agents` was a
# live backlog module. See MODULE_MAP.md.
PKG_ROOTS = [
    REPO_ROOT / "drydocs",
    REPO_ROOT / "drydocs_core",
    REPO_ROOT / "drydocs_remediation",
    REPO_ROOT / "drydocs_lineage",
    REPO_ROOT / "drydocs_deepdoc",
    REPO_ROOT / "drydocs_api",
    REPO_ROOT / "agents",
    REPO_ROOT / "libs",
]

# Directory names never scanned (vendored / virtualenv trees inside a scanned root —
# `agents/.venv` holds its own interpreter and would otherwise be swept in).
SKIP_DIRS: frozenset[str] = frozenset({".venv", "venv", "node_modules", "__pycache__", ".adk"})

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
    # drydocs.docs_verify = the Q7 doc-corpus reconciliation behind `docs-verify`.
    # Classified load, not review: the item chose drydocs-load because the verb sits
    # beside m1-verify/m3-verify and must work BEFORE the docmeta component exists
    # (Q6). RE-HOME it to docmeta if that component takes over corpus state.
    "load": (
        "drydocs.loaders",
        "drydocs.cli",
        "drydocs.snapshots",
        "drydocs.staging",
        "drydocs.cmdline_staging",
        "drydocs.docs_verify",
    ),
    # drydocs-review — SME review + graph acceptance + docs publish (Epic H).
    # The default-deny test below FORCES a new review module to be classified here
    # rather than being silently unguarded.
    "review": (
        "drydocs.graph_verify",
        "drydocs.review_labels",
        "drydocs.source_mappings",
        "drydocs.graph_review",
        "drydocs.sme_notes",
        "drydocs.gate_pages",
        "drydocs.publishing",
    ),
    # drydocs-plan — backlog.yaml -> HTML project board renderer (Epic I).
    "plan": ("drydocs.plan_board",),
    # drydocs-docgen — canonical doc-outline validation + deterministic render + HITL
    # markup (Epic L). Imports only stdlib + config; never a component.
    "docgen": (
        "drydocs.doc_outline",
        "drydocs.design_doc",
        "drydocs.doc_pdf",
    ),
    # drydocs-remediation — detect → transform → prove → Jira (ADR 0002-B, G3).
    # Writes NO graph; Jira is the SoR; imports only drydocs_core.
    "remediation": ("drydocs_remediation",),
    # drydocs-lineage — proactive/curated cmd-line lineage → drydocs (ADR 0002 D2 C2, G4).
    "lineage": ("drydocs_lineage",),
    # drydocs-deepdoc — reactive on-failure deep dive → ddcontext with
    # reliability/trust stamps (ADR 0002 D2 C3, G4). Never imports lineage — the
    # components-don't-import-each-other test IS the D2 separation.
    "deepdoc": ("drydocs_deepdoc",),
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
ENTRYPOINT_MODULES: frozenset[str] = frozenset({"drydocs.cli", "drydocs_core.cli"})

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


def _matches(module: str, prefixes: tuple[str, ...]) -> bool:
    return any(module == p or module.startswith(p + ".") for p in prefixes)


def _module_name(path: Path) -> str:
    rel = path.relative_to(REPO_ROOT).with_suffix("")
    parts = list(rel.parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _package_of(path: Path) -> str:
    name = _module_name(path)
    if path.name == "__init__.py":
        return name
    return name.rsplit(".", 1)[0] if "." in name else "drydocs"


def _imported_drydocs_modules(path: Path) -> set[str]:
    """First-party modules imported by ``path`` (relative imports resolved; ``from pkg import
    name`` expanded to ``pkg.name`` so a component leaf-import like ``from drydocs import
    loaders`` is caught, not just ``from drydocs.loaders import x``)."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    pkg = _package_of(path)
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mods.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative: level 1 = current package, 2 = parent, ...
                base = pkg
                for _ in range(node.level - 1):
                    base = base.rsplit(".", 1)[0] if "." in base else base
                root = f"{base}.{node.module}" if node.module else base
            else:
                root = node.module or ""
            if root:
                mods.add(root)
                for alias in node.names:
                    mods.add(f"{root}.{alias.name}")
    return {m for m in mods if _is_first_party(m)}


# Every first-party top-level name. The pre-2026-07-25 filter was
# ``m == "drydocs" or m.startswith(("drydocs.", "drydocs_core"))`` — note the DOT: it
# matched `drydocs.x` and `drydocs_core*` but NOT `drydocs_api`, `drydocs_lineage`,
# `drydocs_deepdoc`, or `drydocs_remediation`. Imports between the standalone component
# packages were therefore invisible to the guard, so `test_components_do_not_import_each_other`
# could never have caught one. Verified at the fix: 32 first-party imports were unseen,
# incl. drydocs.cli -> drydocs_lineage.* and agents -> drydocs_api.*.
FIRST_PARTY_ROOTS: tuple[str, ...] = (
    "drydocs",
    "drydocs_core",
    "drydocs_api",
    "drydocs_lineage",
    "drydocs_deepdoc",
    "drydocs_remediation",
    "agents",
    "libs",
)


def _is_first_party(module: str) -> bool:
    return any(module == r or module.startswith(r + ".") for r in FIRST_PARTY_ROOTS)


def _iter_py_files():
    files: list[Path] = []
    for root in PKG_ROOTS:
        if not root.exists():
            continue
        files.extend(
            p for p in root.rglob("*.py") if not SKIP_DIRS.intersection(p.relative_to(root).parts)
        )
    return sorted(files)


def test_core_does_not_import_components():
    violations: list[str] = []
    for path in _iter_py_files():
        module = _module_name(path)
        if not _matches(module, CORE_PREFIXES):
            continue
        for imported in sorted(_imported_drydocs_modules(path)):
            if _matches(imported, ALL_COMPONENT_PREFIXES):
                violations.append(f"{module}  ->  {imported}")
    assert not violations, (
        "Core modules must not import the component layer (loaders/cli/snapshots). "
        "See MODULE_MAP.md / ADR 0002-a.\n  " + "\n  ".join(violations)
    )


def test_components_do_not_import_each_other():
    violations: list[str] = []
    for path in _iter_py_files():
        module = _module_name(path)
        if module in ENTRYPOINT_MODULES:
            continue  # composition root may wire any component (see ENTRYPOINT_MODULES)
        owning = [g for g, prefixes in COMPONENT_GROUPS.items() if _matches(module, prefixes)]
        if not owning:
            continue
        group = owning[0]
        other_prefixes = tuple(
            p for g, prefixes in COMPONENT_GROUPS.items() if g != group for p in prefixes
        )
        allowed = DECLARED_COMPONENT_IMPORTS.get(module, ())
        for imported in sorted(_imported_drydocs_modules(path)):
            if _matches(imported, allowed):
                continue  # reviewed exception (see DECLARED_COMPONENT_IMPORTS)
            if _matches(imported, other_prefixes):
                violations.append(f"[{group}] {module}  ->  {imported}")
    assert not violations, (
        "A component must not import another component; route shared code through core. "
        "See MODULE_MAP.md / ADR 0002-a.\n  " + "\n  ".join(violations)
    )


def test_entrypoint_is_exempt_but_still_classified():
    """The CLI composition root may import any component (it is the top-level orchestrator),
    yet is still classified into exactly one component group for default-deny. This is the
    resolution of the entrypoint TODO — a port whose cli.py owns review/plan commands passes.
    """
    for entry in ENTRYPOINT_MODULES:
        owning = [g for g, prefixes in COMPONENT_GROUPS.items() if _matches(entry, prefixes)]
        # An entrypoint that exists must land in exactly one group; a not-yet-present
        # entrypoint (e.g. drydocs_core.cli) is allowed to be absent (zero groups).
        assert len(owning) <= 1, f"{entry} classified into multiple groups: {owning}"
    # the concrete, present entrypoint is in `load`
    assert _matches("drydocs.cli", COMPONENT_GROUPS["load"])


def test_declared_component_imports_are_load_bearing():
    """Every ``DECLARED_COMPONENT_IMPORTS`` entry must still be doing real work.

    A *stale* exception is worse than no exception: it silently widens the boundary for a
    module that no longer needs it, and nothing fails to say so. An entry is stale when the
    module is gone, or when it no longer imports anything under the prefixes it was granted
    — either way, delete it rather than carrying it.
    """
    by_module = {_module_name(p): p for p in _iter_py_files()}
    stale: list[str] = []
    for module, allowed in DECLARED_COMPONENT_IMPORTS.items():
        path = by_module.get(module)
        if path is None:
            stale.append(f"{module}  (module no longer exists)")
            continue
        if not any(_matches(i, allowed) for i in _imported_drydocs_modules(path)):
            stale.append(f"{module}  (imports nothing under {allowed})")
    assert not stale, (
        "Stale DECLARED_COMPONENT_IMPORTS entries — remove them so the boundary stays tight:\n  "
        + "\n  ".join(stale)
    )


def test_every_module_is_classified():
    """Default-deny: every scanned module resolves to EXACTLY ONE bucket.

    The two tests above are an *allow-list* — a module in neither ``CORE_PREFIXES`` nor
    any component group is skipped by both, so it is silently unguarded (the boundary
    blind spot). This flips the guard to default-deny: a module classified into no
    bucket fails as UNCLASSIFIED; a module in more than one bucket fails as AMBIGUOUS.
    Package ``__init__.py`` markers are exempt (they carry no importable logic of their
    own beyond re-exports). When a new module lands (e.g. drydocs-review's graph_review),
    this test fails until it is placed in MODULE_MAP.md + the tables above.
    """
    unclassified: list[str] = []
    ambiguous: list[str] = []
    for path in _iter_py_files():
        if path.name == "__init__.py":
            continue
        module = _module_name(path)
        in_core = _matches(module, CORE_PREFIXES)
        owning = [g for g, prefixes in COMPONENT_GROUPS.items() if _matches(module, prefixes)]
        if in_core and owning:
            ambiguous.append(f"{module}  (core + {owning})")
        elif len(owning) > 1:
            ambiguous.append(f"{module}  ({owning})")
        elif not in_core and not owning:
            unclassified.append(module)

    problems: list[str] = []
    if unclassified:
        problems.append(
            "UNCLASSIFIED — add each to CORE_PREFIXES or a COMPONENT_GROUP (and MODULE_MAP.md):\n  "
            + "\n  ".join(unclassified)
        )
    if ambiguous:
        problems.append(
            "AMBIGUOUS — classified into more than one bucket:\n  " + "\n  ".join(ambiguous)
        )
    assert not problems, "\n".join(problems)


# --- S2 / ADR 0008: the orchestration neutrality direction ---------------------
#
# The parent is neutral, the vendor sits beneath it, and the dependency runs ONE
# way: `orchestration/controlm/` may import `orchestration.shell` / `.paths` /
# `.crosswalk`; the neutral level must never import the vendor. Without this the
# split is a directory layout that nothing holds in place — exactly the state
# before S2, where ~600 neutral lines lived inside a vendor-named package.
#
# NOTE the rule is narrower than ADR 0008 action item 4's phrasing ("nothing
# outside orchestration/controlm/ imports Control-M-specific modules"). Taken
# literally that would fail the repo on its first run: drydocs/staging.py,
# drydocs/cli.py and the lineage extractors all import the Control-M parser and
# are RIGHT to — they ingest Control-M. The enforceable invariant is the
# WITHIN-CORE direction, which is what makes a second vendor possible.
ORCHESTRATION_DIR = REPO_ROOT / "drydocs_core" / "orchestration"
_VENDOR_PREFIX = "drydocs_core.orchestration.controlm"


def test_neutral_orchestration_never_imports_a_vendor() -> None:
    """orchestration/*.py must not depend on orchestration/controlm/ (ADR 0008 rule 1)."""
    offenders: list[str] = []
    for path in sorted(ORCHESTRATION_DIR.glob("*.py")):
        for imported in _imported_drydocs_modules(path):
            if imported == _VENDOR_PREFIX or imported.startswith(_VENDOR_PREFIX + "."):
                offenders.append(f"{path.name} -> {imported}")
    assert not offenders, (
        "the NEUTRAL orchestration level imported a vendor package — the dependency "
        "runs the other way (vendor may import neutral, never the reverse):\n  "
        + "\n  ".join(offenders)
    )


def test_the_vendor_package_actually_sits_beneath_the_parent() -> None:
    """Guards the shape itself, so a future move cannot quietly undo S2."""
    assert (ORCHESTRATION_DIR / "controlm" / "__init__.py").exists()
    for neutral in ("shell.py", "paths.py", "crosswalk.py", "__init__.py"):
        assert (ORCHESTRATION_DIR / neutral).exists(), f"missing neutral module {neutral}"
    assert not (REPO_ROOT / "drydocs_core" / "controlm").exists(), (
        "drydocs_core/controlm/ is back at the top level — S2 moved it under "
        "orchestration/ so a second orchestrator has a sibling slot"
    )
