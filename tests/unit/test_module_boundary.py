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
# Packages scanned for the boundary: the component remainder, physical core, and the
# remediation component (G3 scaffold, 2026-07-10).
PKG_ROOTS = [
    REPO_ROOT / "drydocs",
    REPO_ROOT / "drydocs_core",
    REPO_ROOT / "drydocs_remediation",
    REPO_ROOT / "drydocs_lineage",
    REPO_ROOT / "drydocs_deepdoc",
]

# Dotted prefixes that make up drydocs-core (see MODULE_MAP.md). Since the Phase B
# relocate the physical package is the whole of core (ADR 0002-a-1).
CORE_PREFIXES: tuple[str, ...] = (
    "drydocs_core",
)

# Component group -> the dotted prefixes that belong to it.
COMPONENT_GROUPS: dict[str, tuple[str, ...]] = {
    # drydocs.staging = the load-cadence staging bundle builder (0002-a §6 borderline;
    # relocated out of core's controlm/ in Phase B).
    "load": ("drydocs.loaders", "drydocs.cli", "drydocs.snapshots", "drydocs.staging"),
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
    "plan": (
        "drydocs.plan_board",
    ),
    # drydocs-docgen — canonical doc-outline validation + deterministic render + HITL
    # markup (Epic L). Imports only stdlib + config; never a component.
    "docgen": (
        "drydocs.doc_outline",
        "drydocs.design_doc",
        "drydocs.doc_pdf",
    ),
    # drydocs-remediation — detect → transform → prove → Jira (ADR 0002-B, G3).
    # Writes NO graph; Jira is the SoR; imports only drydocs_core.
    "remediation": (
        "drydocs_remediation",
    ),
    # drydocs-lineage — proactive/curated cmd-line lineage → drydocs (ADR 0002 D2 C2, G4).
    "lineage": (
        "drydocs_lineage",
    ),
    # drydocs-deepdoc — reactive on-failure deep dive → drydocs_context with
    # reliability/trust stamps (ADR 0002 D2 C3, G4). Never imports lineage — the
    # components-don't-import-each-other test IS the D2 separation.
    "deepdoc": (
        "drydocs_deepdoc",
    ),
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
    return {m for m in mods if m == "drydocs" or m.startswith(("drydocs.", "drydocs_core"))}


def _iter_py_files():
    files: list[Path] = []
    for root in PKG_ROOTS:
        if root.exists():
            files.extend(root.rglob("*.py"))
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
        for imported in sorted(_imported_drydocs_modules(path)):
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
        problems.append("AMBIGUOUS — classified into more than one bucket:\n  " + "\n  ".join(ambiguous))
    assert not problems, "\n".join(problems)
