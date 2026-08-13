"""Guards for the module-roadmap page (docs/plan/roadmap.html).

Same contract as the board and inbox renders — deterministic, self-contained,
committed in sync with its sources — plus the two guards only this page needs:
the COVERAGE guard (every module in the backlog's ``modules:`` registry has a
roadmap entry, so registering a module forces a build-out judgment) and the
IDEA-CITATION guard (every Idea-N the roadmap estimates still exists in the
inbox, so a groom that consumes an idea is forced to retire its estimate row
instead of leaving a dangling judgment on the page).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from drydocs.plan_roadmap import (
    DEFAULT_ROADMAP_BACKLOG_PATH,
    DEFAULT_ROADMAP_OUT_PATH,
    DEFAULT_ROADMAP_PATH,
    ESTIMATES,
    STAGES,
    RoadmapError,
    load_roadmap,
    render_roadmap,
    write_roadmap,
)

_IDEAS_PATH = Path(__file__).resolve().parents[2] / "docs" / "restructure" / "IDEAS.md"

_SAMPLE_ROADMAP = {
    "schema": "drydocs.roadmap.v1",
    "updated": "2026-01-01",
    "modules": [
        {
            "module": "alpha",
            "stage": "active",
            "built": "the core works",
            "remaining": "the edges",
            "ideas": [{"id": "Idea-1", "estimate": "M", "note": "a thing"}],
        },
        {
            "module": "beta",
            "stage": "parked",
            "built": "scaffold only",
            "remaining": "everything",
            "ideas": [],
        },
    ],
}
_SAMPLE_BACKLOG = {
    "schema": "drydocs.backlog.v2",
    "updated": "2026-01-02",
    "modules": ["alpha", "beta"],
    "plan": {"phases": [{"id": 1, "title": "P"}]},
    "items": [
        {"id": "A1", "title": "done thing", "module": "alpha", "status": "done"},
        {"id": "A2", "title": "open thing", "module": "alpha", "status": "todo"},
    ],
}


def test_render_is_deterministic() -> None:
    assert render_roadmap(_SAMPLE_ROADMAP, _SAMPLE_BACKLOG) == render_roadmap(
        _SAMPLE_ROADMAP, _SAMPLE_BACKLOG
    )


def test_render_is_self_contained() -> None:
    html = render_roadmap(_SAMPLE_ROADMAP, _SAMPLE_BACKLOG)
    assert html.startswith("<!doctype html>")
    assert "<style>" in html
    for remote in ("http://", "https://", "<script src=", "@import"):
        assert remote not in html, remote


def test_counts_come_from_the_backlog_not_the_roadmap() -> None:
    """The authored file carries NO counts — the page's numbers and open-item
    titles must be the backlog's, read at render time."""
    html = render_roadmap(_SAMPLE_ROADMAP, _SAMPLE_BACKLOG)
    assert "1 done &middot; 1 open" in html
    assert "open thing" in html, "open item titles come live from backlog.yaml"
    assert 'href="board.html#card-A2"' in html, "open items link to their board card"
    assert "no backlog items" in html, "a zero-item module says so honestly"


def test_links_and_legends_render() -> None:
    html = render_roadmap(_SAMPLE_ROADMAP, _SAMPLE_BACKLOG)
    assert 'href="board.html"' in html and 'href="ideas.html"' in html
    for stage in STAGES:
        assert f"<dt>{stage}</dt>" in html
    for est in ESTIMATES:
        assert f"<dt>{est}</dt>" in html
    assert "Idea-1" in html and "est-M" in html


def test_coverage_mismatch_is_a_hard_error() -> None:
    """A registered module with no roadmap entry (or vice versa) must fail the
    render, not silently vanish from the page."""
    backlog = dict(_SAMPLE_BACKLOG, modules=["alpha", "beta", "gamma"])
    with pytest.raises(RoadmapError, match="gamma"):
        render_roadmap(_SAMPLE_ROADMAP, backlog)


def test_bad_stage_and_estimate_are_rejected(tmp_path: Path) -> None:
    bad = dict(
        _SAMPLE_ROADMAP,
        modules=[dict(_SAMPLE_ROADMAP["modules"][0], stage="soonish")],
    )
    path = tmp_path / "roadmap.yaml"
    path.write_text(yaml.safe_dump(bad), encoding="utf-8")
    with pytest.raises(RoadmapError, match="soonish"):
        load_roadmap(path)


def test_write_roadmap_writes_file(tmp_path: Path) -> None:
    rp = tmp_path / "roadmap.yaml"
    bp = tmp_path / "backlog.yaml"
    rp.write_text(yaml.safe_dump(_SAMPLE_ROADMAP), encoding="utf-8")
    bp.write_text(yaml.safe_dump(_SAMPLE_BACKLOG), encoding="utf-8")
    out = tmp_path / "out" / "roadmap.html"

    written = write_roadmap(rp, bp, out)

    assert written == out
    assert out.read_text(encoding="utf-8").startswith("<!doctype html>")


# ── guards over the REAL files ───────────────────────────────────────────


def test_real_roadmap_covers_the_real_module_registry() -> None:
    roadmap = load_roadmap(DEFAULT_ROADMAP_PATH)
    backlog_doc = yaml.safe_load(DEFAULT_ROADMAP_BACKLOG_PATH.read_text(encoding="utf-8"))
    # check_coverage runs inside render_roadmap; rendering IS the assertion.
    render_roadmap(roadmap, backlog_doc)


def test_real_roadmap_cites_only_live_inbox_ideas() -> None:
    """Every Idea-N with an estimate must still sit in the IDEAS.md inbox.
    When a groom consumes an idea (moves it to the audit trail), its roadmap
    row must be retired in the same pass — the estimate belongs to the backlog
    item from then on."""
    roadmap = load_roadmap(DEFAULT_ROADMAP_PATH)
    inbox = (
        _IDEAS_PATH.read_text(encoding="utf-8")
        .split("## Inbox", 1)[1]
        .split("## Recently groomed", 1)[0]
    )
    dangling = [
        idea["id"]
        for entry in roadmap["modules"]
        for idea in entry.get("ideas") or []
        if f"`{idea['id']}`" not in inbox
    ]
    assert not dangling, (
        f"roadmap.yaml estimates ideas no longer in the inbox: {dangling} — "
        "retire their rows (the backlog item they became speaks for itself now)"
    )


def test_committed_roadmap_page_matches_its_sources() -> None:
    """The stale-render check from the CLAUDE.md session ritual, as a test."""
    roadmap = load_roadmap(DEFAULT_ROADMAP_PATH)
    backlog_doc = yaml.safe_load(DEFAULT_ROADMAP_BACKLOG_PATH.read_text(encoding="utf-8"))
    expected = render_roadmap(roadmap, backlog_doc)
    committed = DEFAULT_ROADMAP_OUT_PATH.read_text(encoding="utf-8")
    assert committed == expected, (
        "docs/plan/roadmap.html is stale — re-run `python scripts/render_board.py` "
        "(it renders the roadmap too) and commit the refresh"
    )
