"""Drift guard for the software-registry <-> drydocs-icons SOFT LINK
(web/src/generated/software-registry.json; the gates.json/load-map pattern).

The link is soft by design: vendors and icons join by id (vendor.icon
override, else vendor.id); a vendor with no icon is REPORTED in
vendors_without_icons, never silently dropped and never an error."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent.parent
COMMITTED = REPO / "web" / "src" / "generated" / "software-registry.json"
MANIFEST = REPO / "drydocs-icons" / "manifest.json"
REGISTRY = REPO / "config" / "taxonomy" / "software-registry.yaml"


def _generator():
    spec = importlib.util.spec_from_file_location(
        "render_software_registry",
        REPO / "scripts" / "render_software_registry.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_committed_view_matches_regeneration():
    fresh = _generator().build_software_registry_view()
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    assert committed == fresh, (
        "software-registry.json drifted from the registry/icon manifest it "
        "joins — run: python scripts/render_software_registry.py (or the "
        "default board render) and commit the result"
    )


def test_every_vendor_has_icon_or_is_reported():
    """The soft-link contract: icon present XOR listed in vendors_without_icons
    — a vendor may lack an icon, but never silently."""
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    rendered = [v["id"] for v in committed["vendors"]]
    assert rendered == [
        v["id"] for v in registry["vendors"]
    ], "a registry vendor is absent from (or reordered in) the rendered view"
    for v in committed["vendors"]:
        has_icon = v["icon"] is not None
        reported = v["id"] in committed["vendors_without_icons"]
        assert has_icon != reported, (
            f"vendor {v['id']}: must have an icon XOR be reported in "
            f"vendors_without_icons (icon={has_icon}, reported={reported})"
        )


def test_icon_ids_resolve_in_manifest_and_assets_exist():
    """Every linked icon id exists in the manifest, and its copied display
    asset under web/public/vendor-icons/ is byte-identical to the
    drydocs-icons source (the render copies, the guard verifies)."""
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    icons = json.loads(MANIFEST.read_text(encoding="utf-8"))["icons"]
    for v in committed["vendors"]:
        if not v["icon"]:
            continue
        icon = v["icon"]
        assert icon["id"] in icons, f"vendor {v['id']}: icon {icon['id']} not in manifest"
        src = REPO / "drydocs-icons" / icon["source"]
        dst = REPO / "web" / "public" / icon["asset"]
        assert src.exists(), f"vendor {v['id']}: manifest asset missing: {src}"
        assert dst.exists(), (
            f"vendor {v['id']}: served asset missing: {dst} — run the default "
            "board render (or scripts/render_software_registry.py)"
        )
        assert dst.read_bytes() == src.read_bytes(), (
            f"vendor {v['id']}: web/public/{icon['asset']} drifted from "
            f"drydocs-icons/{icon['source']} — re-run the render"
        )


def test_every_manifest_icon_has_a_kind():
    """2026-07-31 user directive: every icon states what it IS — software
    (vendor/product of software & data services), product (non-software brand,
    e.g. subaru), infrastructure (generic glyph), or persona (user/role)."""
    icons = json.loads(MANIFEST.read_text(encoding="utf-8"))["icons"]
    kinds = {"software", "product", "infrastructure", "persona"}
    for icon_id, icon in icons.items():
        assert (
            icon.get("kind") in kinds
        ), f"icon {icon_id}: kind {icon.get('kind')!r} missing or not in {sorted(kinds)}"
    # registry-linked vendor icons must be software — the registry IS the
    # software ledger; a product/persona glyph linked to a Vendor row is a
    # mis-assignment
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    for v in committed["vendors"]:
        if v["icon"]:
            assert v["icon"]["kind"] == "software", (
                f"vendor {v['id']}: linked icon {v['icon']['id']} has kind "
                f"{v['icon']['kind']!r} — registry vendors link software icons"
            )


def test_every_product_vendor_exists():
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    vendor_ids = {v["id"] for v in committed["vendors"]}
    for p in committed["products"]:
        assert (
            p["vendor"] in vendor_ids
        ), f"product {p['id']}: vendor {p['vendor']} not in the rendered view"


def test_documentation_corpus_resolves_to_a_registered_corpus():
    """Q16: the product->corpus pointer is the headline row of the /software
    coverage view. A typo there renders that row as an orphan, and nothing
    caught it before — `documentation` was YAML-only until this field shipped.
    """
    import yaml

    doc_registry = REPO / "config" / "doc-source-registry.yaml"
    known = {s["id"] for s in yaml.safe_load(doc_registry.read_text(encoding="utf-8"))["sources"]}
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    for p in committed["products"]:
        block = p.get("documentation")
        if not block:
            continue
        assert block["corpus"] in known, (
            f"product {p['id']}: documentation.corpus {block['corpus']!r} is not a "
            f"doc-source-registry id"
        )


def test_stack_is_a_list_so_built_on_and_ingested_from_stay_distinct():
    """`used_by_drydocs` is true for both neo4j (built on) and controlm
    (stack: [source] — ingested FROM). A surface rendering only that boolean
    conflates them, which is why `stack` is emitted."""
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    for p in committed["products"]:
        assert isinstance(p["stack"], list), f"product {p['id']}: stack must be a list"


def test_acronyms_render_as_a_sorted_list_with_provenance():
    """O68: the view carries the glossary the /software Acronyms tab renders.

    A LIST, not a mapping — the renderer's sort is the contract, so the pane
    does not get to invent an order. `added` is stringified because PyYAML
    parses a bare date into datetime.date, which json.dumps cannot serialize;
    a regression there fails the build rather than the page.
    """
    view = json.loads(COMMITTED.read_text(encoding="utf-8"))
    rows = view["acronyms"]
    assert isinstance(rows, list) and rows
    assert [r["term"] for r in rows] == sorted(r["term"] for r in rows)
    for r in rows:
        assert set(r) == {"term", "expansion", "source", "added", "note"}
        assert r["expansion"].strip() and r["source"].strip()
        assert isinstance(r["added"], str) and r["added"].count("-") == 2

    declared = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))["acronyms"]
    assert {r["term"] for r in rows} == set(
        declared
    ), "every declared acronym reaches the console, and the console invents none"
