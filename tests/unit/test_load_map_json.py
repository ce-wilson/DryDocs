"""N4 load-map.json drift guard (the gates.json pattern): the committed
render must equal regeneration, every registered source must have a row
(silent absence is a defect), and every concrete loader must appear on the
one surface exactly once."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent.parent
COMMITTED = REPO / "web" / "src" / "generated" / "load-map.json"


def _generator():
    spec = importlib.util.spec_from_file_location(
        "render_load_map", REPO / "scripts" / "render_load_map.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_committed_load_map_matches_regeneration():
    fresh = _generator().build_load_map()
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    assert committed == fresh, (
        "load-map.json drifted from the declarations/registries it joins — "
        "run: python scripts/render_load_map.py (or the default board render) "
        "and commit the result"
    )


def test_committed_load_map_html_matches_regeneration():
    """N5 — the human surface is deterministic and committed==regenerated
    (the board.html contract; docs/plan/ is the generated-surface home)."""
    mod = _generator()
    fresh = mod.build_load_map_html(mod.build_load_map())
    committed_html = (REPO / "docs" / "plan" / "load-map.html").read_text(
        encoding="utf-8"
    )
    assert committed_html == fresh, (
        "docs/plan/load-map.html drifted — run: python scripts/render_load_map.py "
        "(or the default board render) and commit the result"
    )


def test_every_registered_source_has_a_row():
    """v2: every DATASET row (registry order), then every doc-ledger corpus
    (the union — pipeline twins dropped at N9); systems get their own list."""
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    registry = yaml.safe_load(
        (REPO / "config" / "source-registry.yaml").read_text(encoding="utf-8")
    )
    doc_registry = yaml.safe_load(
        (REPO / "config" / "doc-source-registry.yaml").read_text(encoding="utf-8")
    )["sources"]
    rendered = [s["id"] for s in committed["sources"]]
    expected = [e["id"] for e in registry["datasets"]] + [e["id"] for e in doc_registry]
    assert rendered == expected, (
        "a registered dataset/doc corpus is absent from (or reordered in) "
        "load-map.json — silent absence is the defect N4 exists to end"
    )
    assert [s["id"] for s in committed["systems"]] == [
        e["id"] for e in registry["systems"]
    ], "a v2 system row is absent from load-map.json"
    assert [r["id"] for r in committed["retired"]] == [
        e["id"] for e in registry["retired"]
    ], "the D4 retired list drifted from the render"


def test_ledger_states_are_the_three_governed_ones():
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    for s in committed["sources"]:
        state = s["ledger"]["state"]
        assert state in ("ledger", "pending", "placeholder"), (
            f"source {s['id']}: unknown ledger state {state!r}"
        )
        assert (state == "ledger") == bool(s["ledger"]["path"]), (
            f"source {s['id']}: ledger state/path disagree"
        )


def test_every_concrete_loader_appears_exactly_once():
    from tests.unit.test_load_map_declarations import _concrete_loader_classes

    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    rendered = [
        loader["name"] for s in committed["sources"] for loader in s["loaders"]
    ] + [loader["name"] for loader in committed["sourceless_loaders"]]
    assert sorted(rendered) == sorted(
        cls.name for cls in _concrete_loader_classes()
    ), "load-map.json loader coverage drifted from the concrete loader set"
    assert len(rendered) == len(set(rendered)), "a loader appears twice"


def test_sequence_mirrors_the_declaration():
    from drydocs import cli

    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    assert [
        (s["command"], s["mode"], s["note"]) for s in committed["sequence"]
    ] == list(cli.CANONICAL_LOAD_SEQUENCE), (
        "load-map.json sequence drifted from cli.CANONICAL_LOAD_SEQUENCE"
    )
