"""The lane-handoff script's queue check — refuse vs flag, lane-aware pens, other-queue notes.

Imported by path the way ``test_backlog._allocator()`` imports the groom script: the
logic under test lives under ``.claude/skills/`` where no package guard reaches it, and
both defects the first eval run found (review of fe120bf9, point 1) were in
``check_queue`` — surface flags firing on a Lane A queue, and the fenced other-lane
queue going unchecked. A subagent grading prose is not a test of that function.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def _handoff():
    path = REPO / ".claude" / "skills" / "lane-handoff" / "scripts" / "handoff.py"
    spec = importlib.util.spec_from_file_location("lane_handoff", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def h():
    return _handoff()


def _item(
    iid: str, *, status="todo", deps=(), inputs=(), gates=(), notes="", module="drydocs-load"
):
    return {
        "id": iid,
        "title": f"title of {iid}",
        "type": "task",
        "priority": "p2",
        "module": module,
        "model": "sonnet",
        "status": status,
        "depends_on": list(deps),
        "inputs": list(inputs),
        "gates": list(gates),
        "notes": notes,
    }


@pytest.fixture
def items(h):
    # The machine-local prefix is taken from the script's own VENUE_MARKERS rather than
    # written here: a literal would read as an asset this test READS (J8 skip-guard
    # policy), and it is fixture data, not a path anything opens.
    local = h.VENUE_MARKERS[0]
    return {
        "DONE1": _item("DONE1", status="done"),
        "OPEN1": _item("OPEN1"),
        "BLOCKED1": _item("BLOCKED1", deps=("OPEN1",)),
        "READY2": _item("READY2", deps=("DONE1",), module="drydocs-core"),
        "GATE1": _item(
            "GATE1",
            inputs=("config/gate-prompts/x.yaml", "config/gate-log.md"),
            gates=("x",),
            module="config",
        ),
        "VENUE1": _item(
            "VENUE1",
            inputs=(local + "deepdoc/session/capture.md",),
            module="drydocs-deepdoc",
        ),
        "NOTED1": _item("NOTED1", notes="the transcript is not machine-local, it is tracked"),
        "DOTTED1": _item("DOTTED1", inputs=("./config/gate-log.md",)),
        "BACKSLASH1": _item("BACKSLASH1", inputs=("docs\\port\\port-prompt.md",)),
    }


@pytest.fixture
def ready(items):
    # the board's rule, restated for the fixture: todo with every dependency done
    return [
        i
        for i, it in items.items()
        if it["status"] == "todo"
        and all(items.get(d, {}).get("status") == "done" for d in it["depends_on"])
    ]


# ---- refusals: facts the tree holds --------------------------------------------------


def test_a_done_id_is_refused(h, items, ready):
    rows, refusals = h.check_queue(["DONE1"], items, ready, "B")
    assert rows == [] and refusals == ["DONE1: status is 'done', a queue lists todo items only"]


def test_an_unknown_id_is_refused(h, items, ready):
    _, refusals = h.check_queue(["NOPE9"], items, ready, "B")
    assert len(refusals) == 1 and refusals[0].startswith("NOPE9: no such item")


def test_a_blocked_id_is_refused_naming_the_open_dependency(h, items, ready):
    _, refusals = h.check_queue(["BLOCKED1"], items, ready, "B")
    assert refusals == ["BLOCKED1: not ready — depends on ['OPEN1'] (not all done)"]


def test_a_repeated_id_is_refused(h, items, ready):
    _, refusals = h.check_queue(["OPEN1", "OPEN1"], items, ready, "B")
    assert refusals == ["OPEN1: listed twice"]


def test_a_ready_id_passes_with_its_dependency_recorded(h, items, ready):
    rows, refusals = h.check_queue(["READY2"], items, ready, "B")
    assert refusals == [] and rows[0]["deps"] == ["DONE1"] and rows[0]["module"] == "drydocs-core"


# ---- flags: the author's facts -------------------------------------------------------


def test_lane_b_keeps_surface_flags_and_lane_a_drops_them(h, items, ready):
    (b_row,), _ = h.check_queue(["GATE1"], items, ready, "B")
    (a_row,), _ = h.check_queue(["GATE1"], items, ready, "A")
    assert len(b_row["surfaces"]) == 2 and "pen `gates`" in b_row["surfaces"][0]
    assert a_row["surfaces"] == []
    # the gate note is lane-independent: an SME session is one on either machine
    assert b_row["gates"] == a_row["gates"] == ["gate-bound: x (an SME session, not a build)"]


def test_a_machine_local_input_flags_venue_on_both_lanes(h, items, ready):
    for lane in ("A", "B"):
        (row,), _ = h.check_queue(["VENUE1"], items, ready, lane)
        assert row["venue"] == [
            f"input `{h.VENUE_MARKERS[0]}deepdoc/session/capture.md` is machine-local"
        ]


def test_the_notes_heuristic_is_a_substring_match_and_says_so(h, items):
    """Named, not fixed: 'not machine-local' flags too. A false flag costs a reader one
    glance; a missed one costs the other machine a session (the docstring's rule)."""
    assert h.venue_flags(items["NOTED1"]) == ["notes say machine-local"]


def test_paths_are_normalized_before_pen_matching(h, items, ready):
    (dotted,), _ = h.check_queue(["DOTTED1"], items, ready, "B")
    (backslash,), _ = h.check_queue(["BACKSLASH1"], items, ready, "B")
    assert "pen `gates`" in dotted["surfaces"][0]
    assert "pen `port`" in backslash["surfaces"][0]
    assert h.norm_path("./config/gate-log.md") == "config/gate-log.md"
    assert h.norm_path("docs\\port\\x.md") == "docs/port/x.md"


# ---- the other lane's queue: notes, never refusals ------------------------------------


def test_the_other_queue_yields_notes_not_refusals(h, items, ready):
    notes = h.other_queue_notes(["BLOCKED1", "VENUE1", "GATE1"], items, ready, "B")
    assert notes == [
        "BLOCKED1: not ready — depends on ['OPEN1'] (not all done)",
        f"VENUE1: input `{h.VENUE_MARKERS[0]}deepdoc/session/capture.md` is machine-local",
        "GATE1: input `config/gate-prompts/x.yaml` — pen `gates` (gate prompts — SME sessions run from Lane A)",
        "GATE1: input `config/gate-log.md` — pen `gates` (the signed gate record)",
        "GATE1: gate-bound: x (an SME session, not a build)",
    ]
    assert h.other_queue_notes([], items, ready, "B") == []


# ---- one vocabulary: the pens ---------------------------------------------------------


def test_the_pens_are_keyed_by_section_0_names_and_additions_are_declared(h):
    assert set(h.SECTION_0_PENS) == {"backlog", "port", "adr"}
    assert set(h.SECTION_0_PENS) <= set(h.PENS)
    assert set(h.PENS) - set(h.SECTION_0_PENS) == {"gates", "snapshot"}
    assert h.pen_of("docs/restructure/IDEAS.md") == (
        "backlog",
        "the idea inbox — one file until R6 shards it",
    )
    assert h.pen_of("docs/decisions/0001-x.md")[0] == "adr"
    assert h.pen_of("drydocs_core/x.py") is None


def test_lane_pens_are_the_surface_pens_for_a_and_code_modules_for_b(h, items, ready):
    rows, _ = h.check_queue(["OPEN1", "READY2", "NOTED1"], items, ready, "B")
    assert h.lane_pens("B", rows) == ["code:drydocs-load", "code:drydocs-core"]
    assert h.lane_pens("A", rows) == list(h.PENS)


def test_render_declares_the_pens_in_front_matter_and_the_first_commit_line(h, items, ready):
    rows, _ = h.check_queue(["OPEN1"], items, ready, "B")
    text = h.render(lane="B", machine="laptop", sender="A", rows=rows, other_queue=["GATE1"])
    assert "pens: [code:drydocs-load]" in text
    assert "pen: code:drydocs-load" in text
    assert "queue: [OPEN1]" in text
    assert "wip/<id>-laptop" in text
    assert "| `gates` (this skill's addition to §0) |" in text
    text_a = h.render(lane="A", machine="desktop", sender="B", rows=rows, other_queue=[])
    assert "pen: backlog · port · adr · gates · snapshot" in text_a


# ---- check: MISSING is its own state ---------------------------------------------------


def test_check_reports_missing_ids_as_missing_and_keeps_the_file(h, items, tmp_path, capsys):
    f = tmp_path / "lane-b-handoff.md"
    f.write_text("---\nqueue: [DONE1, GONE9]\n---\n", encoding="utf-8")
    assert h.cmd_check(f, items) == 1
    out = capsys.readouterr().out
    assert "GONE9   MISSING" in out and "Keep the file" in out
    f.write_text("---\nqueue: [DONE1]\n---\n", encoding="utf-8")
    assert h.cmd_check(f, items) == 0
    assert "Queue empty" in capsys.readouterr().out
