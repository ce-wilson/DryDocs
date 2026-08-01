"""Unit tests for plan_board (drydocs/plan_board.py) — pure, no Neo4j."""

from __future__ import annotations

import pytest

try:
    import yaml

    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

from drydocs.plan_board import (
    Backlog,
    BoardError,
    Phase,
    WorkItem,
    backlog_from_dict,
    load_backlog,
    render_board,
    write_board,
)

pytestmark = pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML not installed")

_DOC = {
    "schema": "drydocs.backlog.v2",
    "updated": "2026-07-01",
    "plan": {
        "phases": [
            {"id": 0, "title": "Scaffolding", "goal": "set things up", "status": "done"},
            {
                "id": 1,
                "title": "Planning infra",
                "goal": "board + capture",
                "status": "in_progress",
                "release": "v0.3.0",
            },
            {"id": 2, "title": "Empty phase", "goal": "nothing yet", "status": "todo"},
        ]
    },
    "modules": ["drydocs-plan", "docs"],
    "items": [
        {
            "id": "X1",
            "title": "Ship the <script> board",
            "type": "task",
            "module": "drydocs-plan",
            "phase": 0,
            "epic": "project-board",
            "agent": "main",
            "model": "sonnet",
            "priority": "p1",
            "status": "done",
            "depends_on": [],
            "acceptance": "board renders",
        },
        {
            "id": "X2",
            "title": "Filter by module",
            "type": "task",
            "module": "drydocs-plan",
            "phase": 1,
            "epic": "project-board",
            "agent": "main",
            "model": "sonnet",
            "priority": "p2",
            "status": "todo",
            "depends_on": ["X1"],
            "acceptance": "filters work client-side",
            "notes": "small follow-up",
        },
        {
            "id": "X3",
            "title": "Blocked item",
            "type": "bug",
            "module": "docs",
            "phase": 1,
            "epic": "hygiene",
            "agent": "main",
            "model": "haiku",
            "priority": "p3",
            "status": "blocked",
            "depends_on": ["X2"],
            "acceptance": "unblocked eventually",
        },
        {
            "id": "X4",
            "title": "Not ready yet",
            "type": "chore",
            "module": "docs",
            "phase": 1,
            "epic": "hygiene",
            "agent": "main",
            "model": "haiku",
            "priority": "p3",
            "status": "in_progress",
            "depends_on": [],
            "acceptance": "in flight",
        },
    ],
    "summary": {"todo": 1, "in_progress": 1, "blocked": 1, "done": 1, "next_ready": []},
}


def _backlog() -> Backlog:
    return backlog_from_dict(_DOC)


def test_load_backlog_rejects_wrong_schema(tmp_path) -> None:
    bad = dict(_DOC)
    bad["schema"] = "some.other.schema"
    path = tmp_path / "backlog.yaml"
    path.write_text(yaml.safe_dump(bad), encoding="utf-8")
    with pytest.raises(BoardError):
        load_backlog(path)


def test_load_backlog_missing_file_raises(tmp_path) -> None:
    with pytest.raises(BoardError):
        load_backlog(tmp_path / "does-not-exist.yaml")


def test_backlog_from_dict_requires_phases_and_items() -> None:
    doc = dict(_DOC)
    doc["plan"] = {"phases": []}
    with pytest.raises(BoardError):
        backlog_from_dict(doc)

    doc2 = dict(_DOC)
    doc2["items"] = []
    with pytest.raises(BoardError):
        backlog_from_dict(doc2)


def test_render_contains_phase_and_item_titles() -> None:
    out = render_board(_backlog())
    assert "Scaffolding" in out
    assert "Planning infra" in out
    assert "Filter by module" in out
    assert "v0.3.0" in out


def test_items_land_in_correct_status_column() -> None:
    out = render_board(_backlog())
    todo_col = out.split('<div class="column" data-status="todo">')[1].split(
        '<div class="column" data-status="in_progress">'
    )[0]
    assert "Filter by module" in todo_col
    assert "Ship the" not in todo_col  # X1 is done, not todo

    done_col_start = out.index('<div class="column" data-status="done">')
    done_col = out[done_col_start:]
    assert "Ship the" in done_col


def test_empty_phase_shows_no_items() -> None:
    out = render_board(_backlog())
    assert "no items" in out


def test_deps_render_as_anchors() -> None:
    out = render_board(_backlog())
    assert 'href="#card-X1"' in out
    assert 'data-target="card-X1"' in out
    assert 'id="card-X1"' in out


def test_ready_items_get_accent_class() -> None:
    out = render_board(_backlog())
    # X2 is todo with X1 (done) as its only dep -> ready
    x2_start = out.index('id="card-X2"')
    # walk back to the start of the card div to check its class list
    card_start = out.rindex('<div class="card', 0, x2_start)
    card_tag = out[card_start : x2_start + 10]
    assert "ready" in card_tag


def test_html_escaping_of_malicious_title() -> None:
    out = render_board(_backlog())
    # The item title "Ship the <script> board" must be escaped — it must never appear as
    # a literal injected tag, only as the escaped entity. (The page's own single closing
    # </script> for its inline JS is expected and is not this pattern.)
    assert "<script> board" not in out
    assert "&lt;script&gt; board" in out


def test_render_is_self_contained() -> None:
    out = render_board(_backlog())
    assert out.startswith("<!doctype html>")
    assert "<style>" in out and "<script>" in out
    assert "http://" not in out and "https://" not in out


def test_render_is_deterministic() -> None:
    backlog = _backlog()
    first = render_board(backlog)
    second = render_board(backlog)
    assert first == second


def test_quick_capture_markup_present() -> None:
    out = render_board(_backlog())
    assert 'id="capture-text"' in out
    assert 'id="capture-tag"' in out
    assert 'id="capture-copy"' in out
    assert "IDEAS.md" in out
    assert "navigator.clipboard" in out
    assert "execCommand" in out


def test_filter_markup_and_localstorage_key_present() -> None:
    out = render_board(_backlog())
    for select_id in ("f-module", "f-phase", "f-epic", "f-type"):
        assert f'id="{select_id}"' in out
    assert 'id="f-search"' in out
    assert "drydocs.board.filters" in out


def test_write_board_writes_file(tmp_path) -> None:
    backlog_path = tmp_path / "backlog.yaml"
    backlog_path.write_text(yaml.safe_dump(_DOC), encoding="utf-8")
    out_path = tmp_path / "out" / "board.html"

    written = write_board(backlog_path, out_path)

    assert written == out_path
    assert out_path.exists()
    assert out_path.read_text(encoding="utf-8").startswith("<!doctype html>")


def test_phase_and_workitem_dataclasses_are_frozen() -> None:
    phase = Phase(id=0, title="t")
    item = WorkItem(id="A1", title="t")
    with pytest.raises(Exception):
        phase.title = "changed"  # type: ignore[misc]
    with pytest.raises(Exception):
        item.title = "changed"  # type: ignore[misc]
