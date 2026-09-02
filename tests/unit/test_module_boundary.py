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
    REPO_ROOT / "drydocs_docmeta",
    REPO_ROOT / "drydocs_api",
    REPO_ROOT / "agents",
    REPO_ROOT / "libs",
]

# Directory names never scanned (vendored / virtualenv trees inside a scanned root —
# `agents/.venv` holds its own interpreter and would otherwise be swept in).
SKIP_DIRS: frozenset[str] = frozenset({".venv", "venv", "node_modules", "__pycache__", ".adk"})

# The declaration lives in core since ADR 0018 D1 (2026-09-02): the same object the
# MODULE_MAP renderer and the Team Edition copier read. This test ENFORCES it; it does not
# define it. Every ruling comment moved with the data - read drydocs_core/component_map.py.
from drydocs_core.component_map import (  # noqa: E402
    ALL_COMPONENT_PREFIXES,
    COMPONENT_GROUPS,
    COMPONENT_MODULE,
    CORE_MODULE,
    CORE_PREFIXES,
    DECLARED_COMPONENT_IMPORTS,
    ENTRYPOINT_MODULES,
    NON_PYTHON_MODULES,
    SURFACE_OWNERS,
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
    "drydocs_docmeta",
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
# ---- ADR 0018 D2/D3: the two registries join by NAME, and every surface has an owner ------
# `modules.yaml` is the backlog axis (series = module); `COMPONENT_GROUPS` is the import-
# boundary axis. They must agree by name and nothing else - two registries never share a
# column, they join (design review 2026-09-02 §A2). Before 2026-09-02 the `port` group had
# no module and no series, and nothing noticed.

MODULES_YAML = REPO_ROOT / "docs" / "restructure" / "backlog" / "modules.yaml"


def _registered_modules() -> set[str]:
    import yaml

    doc = yaml.safe_load(MODULES_YAML.read_text(encoding="utf-8")) or {}
    return set(doc.get("modules") or [])


def test_every_component_group_names_a_registered_module():
    """Each boundary group maps to exactly one `modules.yaml` module, and that module exists."""
    assert set(COMPONENT_MODULE) == set(COMPONENT_GROUPS), (
        "COMPONENT_MODULE and COMPONENT_GROUPS name different groups: "
        f"{set(COMPONENT_MODULE) ^ set(COMPONENT_GROUPS)}"
    )
    registered = _registered_modules()
    unknown = {g: m for g, m in COMPONENT_MODULE.items() if m not in registered}
    assert not unknown, (
        f"component groups mapped to a module modules.yaml does not register: {unknown}. "
        "Add the module (name + series) to docs/restructure/backlog/modules.yaml."
    )
    assert CORE_MODULE in registered


def test_the_module_registry_is_exactly_the_three_kinds():
    """modules.yaml == core + the component groups' modules + the declared non-Python set.

    A module cannot be registered without saying which kind it is: a Python package
    (owned through COMPONENT_GROUPS / CORE_PREFIXES) or a work area / non-Python surface
    (NON_PYTHON_MODULES). The `port` gap of 2026-09-02 was a group with no module; this
    also catches the reverse, a module with no group and no declaration.
    """
    declared = {CORE_MODULE} | set(COMPONENT_MODULE.values()) | set(NON_PYTHON_MODULES)
    registered = _registered_modules()
    assert declared == registered, (
        f"registered but undeclared: {sorted(registered - declared)}; "
        f"declared but unregistered: {sorted(declared - registered)}"
    )


def test_surface_owners_name_registered_modules_and_real_directories():
    registered = _registered_modules()
    bad_owner = {d: m for d, m in SURFACE_OWNERS.items() if m not in registered}
    assert not bad_owner, f"SURFACE_OWNERS names unregistered modules: {bad_owner}"
    missing = [d for d in SURFACE_OWNERS if not (REPO_ROOT / d).is_dir()]
    assert not missing, f"SURFACE_OWNERS names directories that do not exist: {missing}"


def test_every_tracked_top_level_directory_has_an_owner():
    """ADR 0018 D3: 'nobody knows what this is' is not a file class the copier can use.

    Every tracked top-level directory is a Python package root (owned through the
    component map) or a key in SURFACE_OWNERS. `tests` is the scan root, not a surface.
    """
    import subprocess

    try:
        out = subprocess.run(
            ["git", "ls-files"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):  # — no git here; the tree check is enough
        return
    tops = {line.split("/", 1)[0] for line in out.splitlines() if "/" in line}
    package_roots = {p.name for p in PKG_ROOTS}
    unowned = sorted(
        d
        for d in tops
        if d not in package_roots
        and d not in SURFACE_OWNERS
        and d not in {"tests", ".github", ".claude", ".vscode"}
    )
    assert not unowned, (
        f"top-level directories with no owning module: {unowned}. Add each to "
        "drydocs_core.component_map.SURFACE_OWNERS (ADR 0018 D3) or retire it."
    )


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
