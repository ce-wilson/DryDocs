"""Guards for the /load-map console surface (backlog O57).

THE FAILURE THIS EXISTS TO CATCH: load-map.json is REGENERATED — a new
registered source, a new system, a new sequence step or a newly-computed
defect appears in the file whenever the registries change. A page that renders
a hand-listed subset would keep looking healthy while silently omitting the new
row, which is exactly the invisible-omission problem the item was raised about.

STATIC BY NECESSITY, AND SAYING SO. The console has no JS test runner
(config/taxonomy/ui-tests.yaml records `execution: manual`, and there is not a
single .test.tsx in the tree), so these assertions read the committed JSON and
the page's SOURCE rather than a rendered DOM. That buys less than a browser
assertion and more than nothing: it pins the partition arithmetic exactly, and
it fails when a collection loses its consumer or a render grows a truncation.
The in-browser half is TC-LOADMAP-01..03 in the ui-tests ledger, seeded from
observation at the build.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LOAD_MAP = REPO / "web" / "src" / "generated" / "load-map.json"
MODEL = REPO / "web" / "src" / "loadmap" / "loadMapModel.ts"
ROUTE = REPO / "web" / "src" / "routes" / "LoadMapRoute.tsx"
SOFTWARE_MODEL = REPO / "web" / "src" / "software" / "softwareModel.ts"
REGISTRY = REPO / "web" / "src" / "modules" / "registry.ts"
APP = REPO / "web" / "src" / "App.tsx"

DOC_REGISTRY = "doc-registry"


def _data() -> dict:
    return json.loads(LOAD_MAP.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# the counts, recomputed from the JSON — never transcribed
# --------------------------------------------------------------------------- #
def test_the_page_owns_every_source_software_does_not() -> None:
    """The two pages partition `sources` — no row on both, none on neither.

    /software filters `home == doc-registry`; this page takes the complement.
    Asserting the SUM rather than either count is what makes the guard immune
    to the file growing: add a source to either registry and this still holds,
    but change one predicate without the other and it breaks immediately.
    """
    sources = _data()["sources"]
    ours = [s for s in sources if s.get("home") != DOC_REGISTRY]
    theirs = [s for s in sources if s.get("home") == DOC_REGISTRY]

    assert len(ours) + len(theirs) == len(sources)
    assert ours, "every source is a doc corpus — /load-map would render an empty table"

    model = MODEL.read_text(encoding="utf-8")
    assert (
        "s.home !== DOC_REGISTRY" in model
    ), "the model no longer takes the complement of /software"
    assert "s.home === 'doc-registry'" in SOFTWARE_MODEL.read_text(
        encoding="utf-8"
    ), "/software changed its side of the partition — /load-map's complement must move with it"


def test_every_collection_in_the_json_has_a_consumer() -> None:
    """A new top-level key must be routed somewhere, not silently unread.

    This is the O57 gap restated as a test: `systems`, `retired`, `sequence`,
    `ad_hoc_commands` and both defect lists sat in the file with no reader for
    two weeks because nothing asserted that they had one.
    """
    consumed = {
        "sources": "SOURCES",
        "systems": "SYSTEMS",
        "retired": "RETIRED",
        "sequence": "SEQUENCE",
        "ad_hoc_commands": "AD_HOC_COMMANDS",
        "sourceless_loaders": "SOURCELESS_LOADERS",
        "map_entries_without_registry_source": "MAP_ENTRIES_WITHOUT_SOURCE",
        "unchained_loaders": "UNCHAINED_LOADERS",
        "steps_with_uncommitted_inputs": "STEPS_WITH_UNCOMMITTED_INPUTS",
        "note": "GENERATOR_NOTE",
    }
    keys = set(_data()) - {"note"}
    unrouted = keys - set(consumed)
    assert not unrouted, (
        f"load-map.json grew {sorted(unrouted)} and no console surface reads it — "
        f"route it in loadMapModel.ts or record why it has no reader"
    )

    model = MODEL.read_text(encoding="utf-8")
    for key, export in consumed.items():
        assert f"export const {export}" in model, f"{key} lost its export ({export}) from the model"


def test_the_route_renders_each_collection_whole() -> None:
    """Every table maps the full array — no slice, no take-N, no head."""
    route = ROUTE.read_text(encoding="utf-8")
    for export in (
        "SOURCES",
        "SYSTEMS",
        "RETIRED",
        "SEQUENCE",
        "AD_HOC_COMMANDS",
        "SOURCELESS_LOADERS",
        "MAP_ENTRIES_WITHOUT_SOURCE",
        "UNCHAINED_LOADERS",
        "STEPS_WITH_UNCOMMITTED_INPUTS",
    ):
        assert f"{export}." in route, f"{export} is imported but never rendered by LoadMapRoute"

    assert ".slice(" not in route, (
        "LoadMapRoute truncates a collection — a page that shows the first N rows of a "
        "regenerated file is the omission this surface exists to prevent"
    )


def test_both_defect_lists_reach_the_defects_tab() -> None:
    """The known-broken rows render AS defects, with their written reasons.

    The acceptance is explicit that dropping them is worse than having no
    surface, because a page that omits them reads as 'all clear'.
    """
    route = ROUTE.read_text(encoding="utf-8")
    assert "Defects:" in route, "the Defects tab is not wired into the module template"
    assert "l.reason" in route, "sourceless loaders render without their stated reason"
    assert "e.exemption" in route, "unregistered-source entries render without their exemption text"

    # The headline defect number must be the SUM of all four lists. Reporting
    # only some of them is the failure that looks most like success: a "1
    # declared defect" tile beside a tab holding four rows reads as though the
    # other three were reviewed and dismissed. (G80 added the second pair.)
    model = MODEL.read_text(encoding="utf-8")
    defect_count_block = model.split("export const DEFECT_COUNT", 1)[1].split("\n\n", 1)[0]
    for term in (
        "SOURCELESS_LOADERS.length",
        "MAP_ENTRIES_WITHOUT_SOURCE.length",
        "UNCHAINED_LOADERS.length",
        "STEPS_WITH_UNCOMMITTED_INPUTS.length",
    ):
        assert term in defect_count_block, (
            f"DEFECT_COUNT no longer totals {term} — the headline number must "
            "sum every declared defect list"
        )
    # and the G80 rows render with their reason-or-null made visible
    route_src = ROUTE.read_text(encoding="utf-8")
    assert "l.reason ??" in route_src, "unchained loaders render without the null-reason fallback"
    assert (
        "s.exemption ??" in route_src
    ), "uncommitted-input rows render without the null-exemption fallback"


# --------------------------------------------------------------------------- #
# registration — the surface is reachable and declared
# --------------------------------------------------------------------------- #
def test_the_module_is_registered_with_an_access_designation() -> None:
    """A nav module with no access decision defaults silently; O57 forbids that."""
    registry = REGISTRY.read_text(encoding="utf-8")
    assert "'loadmap'" in registry, "loadmap is missing from the ModuleId union"
    block = registry.split("id: 'loadmap',", 1)[1].split("},", 1)[0]
    assert "path: '/load-map'" in block
    assert "access: 'sme'" in block, "the load-map module lost its access designation"


def test_the_route_is_gated_the_same_way_the_registry_says() -> None:
    """Registry designation and router gate must not drift apart."""
    app = APP.read_text(encoding="utf-8")
    assert 'path="load-map"' in app, "/load-map is not routed"
    gate = app.split('path="load-map"', 1)[1].split("/>", 1)[0]
    assert "steward" in gate and "admin" in gate, "the SME designation is not enforced on the route"
