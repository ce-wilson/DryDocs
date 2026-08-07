"""Guards for the first-party UI component sub-ledger (backlog O42).

config/taxonomy/ui-components.yaml inventories what we BUILT;
config/taxonomy/software-registry.yaml registers what we are BUILT ON. These
tests keep the two joined, and keep the ledger honest against the filesystem.

The bidirectional drift check is the whole point. An inventory nobody is forced
to update rots into fiction — and this one was hand-generated from a `find`
whose output truncated at 60 of 62 files, which is precisely the failure mode
the guard exists to catch.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml", reason="PyYAML not installed")

REPO = Path(__file__).resolve().parents[2]
UI_LEDGER = REPO / "config" / "taxonomy" / "ui-components.yaml"
SOFTWARE_REGISTRY = REPO / "config" / "taxonomy" / "software-registry.yaml"


def _ui() -> dict:
    return yaml.safe_load(UI_LEDGER.read_text(encoding="utf-8"))


def _registry() -> dict:
    return yaml.safe_load(SOFTWARE_REGISTRY.read_text(encoding="utf-8"))


def _on_disk(ledger: dict) -> set[str]:
    root = REPO / ledger["root"]
    ext = ledger["extension"]
    return {f.relative_to(root).as_posix() for f in root.rglob(f"*{ext}")}


# --------------------------------------------------------------------------- #
# shape
# --------------------------------------------------------------------------- #
def test_ledger_schema_and_classification() -> None:
    doc = _ui()
    assert doc["schema"] == "drydocs.ui-component-registry.v1"
    assert doc["classification"] == "Internal-Public"
    assert doc["root"] and doc["extension"]


def test_entries_are_well_formed_with_unique_ids_and_known_areas() -> None:
    doc = _ui()
    areas = {a["id"] for a in doc["areas"]}
    seen: set[str] = set()
    for c in doc["components"]:
        assert c.get("id"), f"component row missing id: {c}"
        assert c["id"] not in seen, f"duplicate component id '{c['id']}'"
        seen.add(c["id"])
        assert c.get("path"), f"'{c['id']}' missing path"
        assert c.get("area") in areas, f"'{c['id']}' has unknown area '{c.get('area')}'"


def test_every_declared_area_is_actually_used() -> None:
    """A documented area with no members is drift, not structure."""
    doc = _ui()
    used = {c["area"] for c in doc["components"]}
    declared = {a["id"] for a in doc["areas"]}
    assert not (declared - used), f"areas declared but empty: {sorted(declared - used)}"


# --------------------------------------------------------------------------- #
# the drift guard — both directions
# --------------------------------------------------------------------------- #
def test_no_component_on_disk_is_missing_from_the_ledger() -> None:
    """Add a component without registering it and this fails.

    This is the direction that matters most: an unregistered component is
    invisible to every tool that reads the ledger, which is the exact gap O42
    was raised for.
    """
    doc = _ui()
    missing = sorted(_on_disk(doc) - {c["path"] for c in doc["components"]})
    assert not missing, (
        f"{len(missing)} component(s) exist under {doc['root']} but are not in "
        f"{UI_LEDGER.name}: {missing}"
    )


def test_no_ledger_entry_points_at_a_missing_file() -> None:
    """Delete or move a component without updating the ledger and this fails."""
    doc = _ui()
    stale = sorted({c["path"] for c in doc["components"]} - _on_disk(doc))
    assert not stale, f"{len(stale)} ledger entr(ies) name a file that no longer exists: {stale}"


def test_component_id_matches_its_filename() -> None:
    doc = _ui()
    ext = doc["extension"]
    bad = [c["id"] for c in doc["components"] if c["path"].rsplit("/", 1)[-1] != f"{c['id']}{ext}"]
    assert not bad, f"component id does not match filename for: {bad}"


# --------------------------------------------------------------------------- #
# the join to the third-party registry
# --------------------------------------------------------------------------- #
def test_ledger_joins_to_a_real_registered_product() -> None:
    """`framework` and `stack` must name things the software registry knows."""
    doc, reg = _ui(), _registry()
    products = {p["id"]: p for p in reg["products"]}
    assert (
        doc["framework"] in products
    ), f"ui ledger framework '{doc['framework']}' is not a registered product"
    product = products[doc["framework"]]
    assert doc["stack"] in (product.get("stack") or []), (
        f"ui ledger stack '{doc['stack']}' is not one of product "
        f"'{product['id']}' stacks {product.get('stack')}"
    )


def test_the_pointer_is_reciprocal() -> None:
    """The registry must point BACK at this ledger.

    A one-way link is how a sub-ledger gets orphaned: readers arriving at the
    react product would never learn the component inventory exists.
    """
    doc, reg = _ui(), _registry()
    product = next(p for p in reg["products"] if p["id"] == doc["framework"])
    pointer = product.get("components")
    assert pointer, f"product '{product['id']}' has no components pointer"
    assert (
        REPO / pointer["ledger"]
    ) == UI_LEDGER, f"components.ledger points at {pointer['ledger']}, not {UI_LEDGER.name}"
    assert pointer["schema"] == doc["schema"], "pointer schema disagrees with the ledger"


# --------------------------------------------------------------------------- #
# module binding — the one idea borrowed from the Miller process model:
# the join UP from a UI element to the feature it serves
# --------------------------------------------------------------------------- #
import re  # noqa: E402

MODULE_REGISTRY_TS = REPO / "web" / "src" / "modules" / "registry.ts"
VALID_EVIDENCE = {"directory", "route-name", "route-dir"}


def _module_ids() -> set[str]:
    return set(re.findall(r"id:\s*'([a-z-]+)'", MODULE_REGISTRY_TS.read_text(encoding="utf-8")))


def test_every_module_binding_names_a_real_console_module() -> None:
    """The binding joins to web/src/modules/registry.ts, the canonical list."""
    valid = _module_ids()
    assert valid, "could not read module ids from registry.ts"
    bad = [
        (c["id"], c["module"])
        for c in _ui()["components"]
        if c.get("module") and c["module"] not in valid
    ]
    assert not bad, f"component(s) bound to unknown modules: {bad} (valid: {sorted(valid)})"


def test_a_binding_always_records_how_it_was_derived() -> None:
    """Evidence is mandatory, so a guess can never masquerade as a fact."""
    failures = []
    for c in _ui()["components"]:
        has_module, has_evidence = bool(c.get("module")), bool(c.get("module_evidence"))
        if has_module != has_evidence:
            failures.append(
                f"{c['id']}: module={c.get('module')!r} evidence={c.get('module_evidence')!r}"
            )
        if has_evidence and c["module_evidence"] not in VALID_EVIDENCE:
            failures.append(f"{c['id']}: unknown evidence '{c['module_evidence']}'")
    assert not failures, "\n".join(failures)


def test_directory_evidence_actually_holds() -> None:
    """'directory' must mean the file really lives under that module folder."""
    for c in _ui()["components"]:
        if c.get("module_evidence") == "directory":
            assert (
                c["path"].split("/")[0] == c["module"]
            ), f"{c['id']} claims directory evidence for '{c['module']}' but sits at {c['path']}"


def test_unbound_components_are_counted_not_hidden() -> None:
    """37 shell/primitive/shared components carry no module ON PURPOSE.

    Pinned so the split stays visible: if it moves, someone either bound more
    (good — update the pin) or added components without thinking about it.
    62 -> 63 at O28: StatusItems (with HealthGlyph) is deliberately UNBOUND —
    it renders the node-status envelope for the Explorer inspector AND the
    landing hub's spokes, so binding it to either module would misstate it.
    63 -> 64 at R6: TaskGraphPane IS bound (ask/, directory evidence), so the
    bound count moves too — the Tier-2 task graph serves exactly one module.
    64 -> 65 at K11: AppCodeCascadePane rides UNBOUND like its parent
    MappingsRoute — 'mappings' is not a registry module, so a binding would
    invent one (the same reason the route itself carries no module).
    65 -> 66 at O29: TrustLegend is deliberately UNBOUND — the trust-tier
    legend renders on the lineage AND docs canvases (and any pane that opts
    in), so binding it to either module would misstate it.
    Assigning the rest properly means reading imports, which is O42's TS
    resolver, not a naming heuristic.
    """
    comps = _ui()["components"]
    bound = [c for c in comps if c.get("module")]
    assert (len(bound), len(comps)) == (
        27,
        66,
    ), f"module-binding coverage changed: {len(bound)}/{len(comps)} bound"
