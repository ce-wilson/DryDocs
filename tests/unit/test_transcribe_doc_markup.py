"""Tests for the L6 paper-HITL loop's transcription -> feedback-yaml step (Epic L / L6).

transcribe-doc-markup (.claude/skills/transcribe-doc-markup/SKILL.md) is a PROCEDURE, not
new production code — its final step reuses ``drydocs.docgen.design_doc.feedback_yaml``, the same
canonical emitter the digital (L5) loop's clipboard export uses. That is the whole point:
paper and digital feedback must land in an IDENTICAL schema so L7 ingests both the same way
(docs/design/feedback/README.md).

This test proves the paper path really does produce that schema, using a synthetic fixture
that stands in for a faithfully-transcribed (but fake) scanned page — no real scan, no real
annotation content, nothing beyond what's already committed in the fixture file.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from drydocs.docgen.design_doc import feedback_yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = (
    REPO_ROOT / "tests" / "fixtures" / "transcribe_doc_markup" / "sample-scan-transcription.yaml"
)
CONTROLM_TDD = REPO_ROOT / "docs" / "design" / "controlm-ingestion-tdd.md"


def _load_fixture() -> dict:
    return yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))


def test_fixture_exists_and_is_synthetic() -> None:
    fx = _load_fixture()
    assert fx["schema"] == "drydocs.transcribe-doc-markup-fixture.v1"
    assert fx["doc"] == "controlm-ingestion-tdd"
    assert fx["faithful_transcription"], "fixture must carry at least one transcribed note"


def test_fixture_anchors_are_real_anchors_in_the_doc() -> None:
    """Step 2 (anchor-keying) only makes sense against anchors that actually exist — the
    same discipline the digital loop's README documents ('must be an anchor that exists
    in the doc')."""
    md = CONTROLM_TDD.read_text(encoding="utf-8")
    fx = _load_fixture()
    for row in fx["faithful_transcription"]:
        assert (
            f'<!-- anchor: {row["margin_tag_seen"]} -->' in md
        ), f"fixture anchor {row['margin_tag_seen']!r} does not exist in the real TDD"


def test_transcription_keys_to_feedback_yaml_schema() -> None:
    """The anchor-keying step: each transcribed row's margin_tag_seen (read straight off
    the print-margin gutter tag, drydocs/docgen/design_doc.py:_inject_margin_anchors) becomes the
    feedback_yaml anchor; the pen_note becomes the note text."""
    fx = _load_fixture()
    notes = {row["margin_tag_seen"]: row["pen_note"] for row in fx["faithful_transcription"]}
    out = feedback_yaml(fx["doc"], notes)

    assert out.startswith(
        "# design-doc feedback — paste into docs/design/feedback/controlm-ingestion-tdd-rev<N>.yaml\n"
    )
    assert "doc: controlm-ingestion-tdd\n" in out
    for row in fx["faithful_transcription"]:
        assert f'  - anchor: {row["margin_tag_seen"]}\n' in out
        assert f'      {row["pen_note"]}\n' in out


def test_transcription_output_matches_l5_yaml_shape() -> None:
    """Round-trips through the same parse a human/agent does when saving either loop's
    output as docs/design/feedback/<doc>-rev<N>.yaml — proves paper and digital feedback
    are structurally identical, not just visually similar, so L7 can ingest both alike."""
    fx = _load_fixture()
    notes = {row["margin_tag_seen"]: row["pen_note"] for row in fx["faithful_transcription"]}
    out = feedback_yaml(fx["doc"], notes)

    parsed = yaml.safe_load(
        "\n".join(out.splitlines()[1:])
    )  # drop feedback_yaml's own '# ...' header line
    assert parsed["doc"] == fx["doc"]
    assert {n["anchor"] for n in parsed["notes"]} == set(notes)
    assert all(
        parsed_note["note"].strip() == notes[parsed_note["anchor"]]
        for parsed_note in parsed["notes"]
    )
