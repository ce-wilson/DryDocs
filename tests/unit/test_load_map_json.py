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
    committed_html = (REPO / "docs" / "plan" / "load-map.html").read_text(encoding="utf-8")
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
        assert state in (
            "ledger",
            "pending",
            "placeholder",
        ), f"source {s['id']}: unknown ledger state {state!r}"
        assert (state == "ledger") == bool(
            s["ledger"]["path"]
        ), f"source {s['id']}: ledger state/path disagree"


def test_every_concrete_loader_appears_exactly_once():
    from tests.unit.test_load_map_declarations import _concrete_loader_classes

    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    rendered = [loader["name"] for s in committed["sources"] for loader in s["loaders"]] + [
        loader["name"] for loader in committed["sourceless_loaders"]
    ]
    assert sorted(rendered) == sorted(
        cls.name for cls in _concrete_loader_classes()
    ), "load-map.json loader coverage drifted from the concrete loader set"
    assert len(rendered) == len(set(rendered)), "a loader appears twice"


def test_sequence_mirrors_the_declaration():
    from drydocs import cli

    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    # Profiles are a sorted list in JSON and a frozenset in the declaration (N6),
    # so compare them as sets rather than asserting the render's ordering twice.
    rendered = [
        (s["command"], s["mode"], frozenset(s["profiles"]), s["note"])
        for s in committed["sequence"]
    ]
    # G79: a DERIVED step has no literal to mirror, so the render is compared
    # against the RESOLVED answer — the same function the operator paths call.
    # Comparing against `step.profiles` would compare the render to None.
    declared = [
        (s.command, s.mode, cli.step_profiles(s), s.note) for s in cli.CANONICAL_LOAD_SEQUENCE
    ]
    assert rendered == declared, "load-map.json sequence drifted from cli.CANONICAL_LOAD_SEQUENCE"

    # ...and the render says WHICH steps were derived, so a reader can tell a
    # declared surface membership from a computed one.
    derived = {s["command"] for s in committed["sequence"] if s["profiles_derived"]}
    assert derived == {
        s.command for s in cli.CANONICAL_LOAD_SEQUENCE if s.profiles is None
    }, "load-map.json disagrees with the declaration about which steps derive their profiles"


def test_doc_corpus_rows_carry_the_doc_governance_fields():
    """Q16 / the /software surface. `target_db` is the load-bearing one: without
    it a consumer cannot know when it is ENTITLED to report a document count, and
    a corpus targeting a database the reader cannot query must render "not
    queried" rather than 0 — a 0 there is a false claim of absence.
    """
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    doc_rows = [s for s in committed["sources"] if s.get("home") == "doc-registry"]
    assert doc_rows, "no doc-corpus rows in the load map"
    for row in doc_rows:
        for key in ("tier", "curation", "connector", "target_db", "trust_default"):
            assert key in row, f"doc corpus {row['id']}: projection dropped {key}"
        assert row["target_db"], f"doc corpus {row['id']}: target_db must not be empty"


def test_the_not_queryable_target_db_set_is_pinned():
    """THE ALARM FIRED 2026-08-18 AND WAS ANSWERED: G32 ruled (the fold, G102),
    the corpora re-targeted, and both surfaces this pin protects were revisited
    in the same change — softwareModel.ts inGraphLabel and the docs-coverage
    detail lines no longer render 'not provisioned (G32)'. The pin now holds the
    ruled state: EVERY doc-corpus target is spec-readable; the set is EMPTY."""
    from drydocs_api.query_specs import SPEC_DATABASES

    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    declared = {s["target_db"] for s in committed["sources"] if s.get("home") == "doc-registry"}
    assert declared - set(SPEC_DATABASES) == set(), (
        "a doc corpus declares a target database no QuerySpec can read — post-G102 "
        "that means a row missed the fold or a new realm arrived without a gate; "
        "revisit every surface that renders a 'not queried' label"
    )
