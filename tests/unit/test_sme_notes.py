"""Unit tests for sme_notes (drydocs/review/sme_notes.py) — pure, no Neo4j. Synthetic SIDs only."""

from __future__ import annotations

from drydocs.review.sme_notes import ROUTE_TAGS, harvest_text, harvest_tree, route


def test_harvest_python_and_cypher_comments() -> None:
    text = (
        "x = 1  # SME[sme01] $FR jobs must map to a folder\n"
        "// SME[sme02] $OQ is CM_DEF_SETVAR the right source view?\n"
        "plain line with no note\n"
    )
    notes = harvest_text(text, path="f.py")
    assert len(notes) == 2
    assert notes[0].sid == "sme01" and notes[0].tag == "FR"
    assert "folder" in notes[0].text
    assert notes[1].tag == "OQ" and notes[1].line == 2


def test_all_four_tags_parse() -> None:
    text = "\n".join(f"# SME[s] ${t} something {t}" for t in ROUTE_TAGS)
    tags = {n.tag for n in harvest_text(text)}
    assert tags == set(ROUTE_TAGS)


def test_separator_variants() -> None:
    for sep in (" ", ": ", " - "):
        (note,) = harvest_text(f"# SME[s1] $UC{sep}the use case")
        assert note.text == "the use case"


def test_route_buckets_present_even_when_empty() -> None:
    notes = harvest_text("# SME[s1] $FR only a requirement")
    buckets = route(notes)
    assert set(buckets) == set(ROUTE_TAGS)
    assert len(buckets["FR"]) == 1
    assert buckets["UC"] == []


def test_harvest_tree_respects_extensions_and_excludes(tmp_path) -> None:
    (tmp_path / "keep.py").write_text("# SME[s1] $FR real one", encoding="utf-8")
    (tmp_path / "skip.txt").write_text("# SME[s2] $FR ignored ext", encoding="utf-8")
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "secret.py").write_text("# SME[s3] $FR excluded dir", encoding="utf-8")

    notes = harvest_tree(tmp_path)
    sids = {n.sid for n in notes}
    assert sids == {"s1"}  # .txt skipped, data/ excluded
