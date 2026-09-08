"""WEB18 guards: the UI-concept provenance artifact the console header reads.

The gates.json / context-types.json pattern — the committed json must equal a
fresh regeneration, so an edit to config/taxonomy/ui-concepts.yaml without a
re-render fails here rather than leaving a header that describes a term the yaml
no longer declares that way.

AND ONE GUARD THE SIBLINGS DO NOT HAVE, because this artifact feeds a sentence
about the ONTOLOGY BOUNDARY. R22's whole subject is a console term being read as
a graph concept, so the artifact may carry a term's SOURCE and may carry its
declared ``graph_binding``, and must never carry a rendered claim about what the
term maps to. The console composes its own wording from the fields; a sentence
baked in here would be a second definition wearing a build step, which is the
defect WEB18 exists to close rather than a way of closing it.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml", reason="PyYAML not installed")

REPO = Path(__file__).resolve().parent.parent.parent
SOURCE = REPO / "config" / "taxonomy" / "ui-concepts.yaml"
COMMITTED = REPO / "web" / "src" / "generated" / "ui-concepts.json"
CONSUMER = REPO / "web" / "src" / "lib" / "uiConcepts.ts"


def _generator():
    spec = importlib.util.spec_from_file_location(
        "render_ui_concepts", REPO / "scripts" / "render_ui_concepts.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_committed_artifact_matches_regeneration():
    fresh = _generator().build_ui_concepts()
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    assert committed == fresh, (
        "ui-concepts.json drifted from config/taxonomy/ui-concepts.yaml — run: "
        "python scripts/render_ui_concepts.py (or scripts/render_board.py) and commit it"
    )


def test_every_declared_concept_reaches_the_artifact():
    """A term declared and not rendered is a term the header cannot annotate,
    which is the same silence WEB18 is fixing."""
    declared = {c["term"] for c in yaml.safe_load(SOURCE.read_text(encoding="utf-8"))["concepts"]}
    rendered = {c["term"] for c in json.loads(COMMITTED.read_text(encoding="utf-8"))["concepts"]}
    assert declared and declared == rendered


def test_each_row_carries_what_the_header_needs_and_nothing_composed():
    for concept in json.loads(COMMITTED.read_text(encoding="utf-8"))["concepts"]:
        assert set(concept) == {
            "term",
            "aliases",
            "source",
            "source_kind",
            "cardinality",
            "members",
            "graph_binding",
        }, "the artifact's field set is the contract the console composes from"
        assert concept["cardinality"] == len(concept["members"]), (
            "a declared count that disagrees with its own members would put a wrong "
            "number in a provenance note, which is worse than no note"
        )


def test_the_artifact_states_a_binding_and_never_asserts_one():
    """Clause (b), as a property of the DATA rather than of the renderer.

    `graph_binding` is carried as declared, and today every row says `none`.
    What must not appear is a field naming a graph label or edge — a mapping is
    a HITL gate decision and an artifact that shipped one would pre-empt it on
    a page header, which is precisely the crossing R22 was written for.
    """
    text = COMMITTED.read_text(encoding="utf-8")
    for concept in json.loads(text)["concepts"]:
        assert concept["graph_binding"] in {"none", "planned", "confirmed"}
    assert (
        ":TOMRole" not in text and ":Tower" not in text
    ), "the artifact names a graph label — a binding claim belongs to the gate, not here"


def test_the_console_composes_the_sentence_and_hardcodes_no_fact():
    """The split that makes this worth building: the WORDING is in TypeScript,
    every FACT is in the artifact. A hand-written count or member name in the
    consumer would be the second definition WEB18 closes."""
    consumer = CONSUMER.read_text(encoding="utf-8")
    artifact = json.loads(COMMITTED.read_text(encoding="utf-8"))
    for concept in artifact["concepts"]:
        for member in concept["members"]:
            assert member not in consumer, f"{member!r} is hardcoded in the console consumer"
        assert f"'{concept['term']}'" not in consumer, (
            f"{concept['term']!r} is named as a literal in the console consumer; the "
            "lookup must be by declaration, not by term"
        )
        assert str(concept["cardinality"]) not in consumer.split("cardinality")[0]


def test_the_render_step_rides_the_board_run():
    """The J20 lesson: a generated artifact whose regeneration is not wired into
    the one command is one somebody forgets, and the guard above then fails for
    a reason nobody caused."""
    board = (REPO / "scripts" / "render_board.py").read_text(encoding="utf-8")
    assert "render_ui_concepts" in board
    assert "render_ui_concepts.main()" in board
