"""Module-boundary guard for the drydocs-core extraction (ADR 0002 / 0002-a, Phase A).

Phase A is *logical*; the physical split is staged. A transitional ``drydocs_core`` shim
package now exists (re-exports the surface, ADR 0002-a Phase B step 1), but the core modules
still physically live under ``drydocs/``. This test enforces the boundary across BOTH, per
``MODULE_MAP.md``:

  * **Core imports nothing from any component.** The parse / model / config / driver layer
    (models, adapters, neo4j_client, config, precedence, source_registry, ontology, controlm)
    must never import the component layer (loaders / cli / snapshots — graph-write + run cadence).
  * **Components import only core, never each other.**

It parses files with ``ast`` and never imports ``drydocs`` itself, so it has no DB or driver
side effects and runs anywhere. When Phase B physically splits packages, update the prefix
tables below to the new package names; the invariant is unchanged.
"""
from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
# Packages scanned for the boundary: the monolith plus the transitional core shim.
PKG_ROOTS = [REPO_ROOT / "drydocs", REPO_ROOT / "drydocs_core"]

# Dotted prefixes that make up drydocs-core (see MODULE_MAP.md). Includes the
# `drydocs_core` shim package (ADR 0002-a Phase B step 1; re-exports the surface).
CORE_PREFIXES: tuple[str, ...] = (
    "drydocs.models",
    "drydocs.adapters",
    "drydocs.neo4j_client",
    "drydocs.config",
    "drydocs.precedence",
    "drydocs.source_registry",
    "drydocs.ontology",
    "drydocs.controlm",
    "drydocs_core",
)

# Component group -> the dotted prefixes that belong to it.
COMPONENT_GROUPS: dict[str, tuple[str, ...]] = {
    "load": ("drydocs.loaders", "drydocs.cli", "drydocs.snapshots"),
}
ALL_COMPONENT_PREFIXES: tuple[str, ...] = tuple(
    p for prefixes in COMPONENT_GROUPS.values() for p in prefixes
)


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
