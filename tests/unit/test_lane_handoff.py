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


# ---- a declared venue the receiving machine lacks (PLAN6) -------------------------------

WITHOUT_SERVER = {"controlm-server": {"available": False}, "neo4j": {"available": True}}
WITH_SERVER = {"controlm-server": {"available": True}, "neo4j": {"available": True}}


def _declared(iid: str, *codes: str):
    item = _item(iid)
    item["venue"] = list(codes)
    return item


def test_a_declared_venue_this_side_lacks_is_a_venue_flag_naming_the_code(h):
    """PLAN6 (a)/(b): the FIELD is read, never the acceptance prose, and the flag says
    which requirement failed. The same item on a machine that declares the venue is
    silent; an undeclared code is its own flag, not a silent pass."""
    item = _declared("SERVER1", "controlm-server")
    assert h.venue_flags(item, WITHOUT_SERVER) == [
        "venue `controlm-server` required, not available on this machine "
        "(venues.controlm-server.available: false in dev-environment.yaml)"
    ]
    assert h.venue_flags(item, WITH_SERVER) == []
    assert h.venue_flags(_declared("TYPO1", "mainframe"), WITH_SERVER) == [
        "venue `mainframe` required, but dev-environment.yaml declares no such code"
    ]
    # no declaration: silence, not a new failure (PLAN6 c)
    assert h.venue_flags(_item("PLAIN1"), WITHOUT_SERVER) == []


def test_check_queue_carries_the_declared_venue_as_a_flag_on_both_lanes(h, items, ready):
    items["SERVER1"] = _declared("SERVER1", "controlm-server")
    ready = [*ready, "SERVER1"]
    for lane in ("A", "B"):
        (row,), refusals = h.check_queue(["SERVER1"], items, ready, lane, venues=WITHOUT_SERVER)
        assert refusals == [] and row["venue"] == [
            "venue `controlm-server` required, not available on this machine "
            "(venues.controlm-server.available: false in dev-environment.yaml)"
        ]
    (row,), _ = h.check_queue(["SERVER1"], items, ready, "B", venues=WITH_SERVER)
    assert row["venue"] == []


def test_g132_is_the_worked_example(h):
    """PLAN6 (c): G132 carries the declaration, and a --suggest run on a machine without
    the server venue flags it. Read from the real item file; the venue map is synthetic
    on both sides of the comparison so this holds on a checkout that DOES declare it."""
    g132 = h.backlog_store.load_backlog_document(h.BACKLOG / "items" / "G132.yaml")
    assert g132["venue"] == ["controlm-server"]
    assert h.declared_venue_flags(g132, WITHOUT_SERVER) == [
        "venue `controlm-server` required, not available on this machine "
        "(venues.controlm-server.available: false in dev-environment.yaml)"
    ]
    assert h.declared_venue_flags(g132, WITH_SERVER) == []


def test_load_venues_reads_the_venue_file_and_an_absent_section_declares_nothing(h, tmp_path):
    live = h.load_venues()
    assert live and all({"available", "what"} <= set(v) for v in live.values())
    assert all(isinstance(v["available"], bool) for v in live.values())
    f = tmp_path / "dev-environment.yaml"
    f.write_text("schema: drydocs.dev-environment.v1\nedition: base\n", encoding="utf-8")
    assert h.load_venues(f) == {}
    assert h.load_venues(tmp_path / "missing.yaml") == {}


def test_suggest_marks_v_and_names_the_failed_requirement(h, items, ready, capsys):
    items["SERVER1"] = _declared("SERVER1", "controlm-server")
    assert h.cmd_suggest(items, [*ready, "SERVER1"], venues=WITHOUT_SERVER) == 0
    out = capsys.readouterr().out
    assert "(declared here: neo4j)" in out
    line = next(ln for ln in out.splitlines() if "SERVER1" in ln)
    assert line.strip().startswith("V---")
    assert "- venue `controlm-server` required, not available on this machine" in out


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


def test_a_third_lane_letter_is_a_build_lane_and_only_a_is_the_pen_holder(h, items, ready):
    """The module branches on the ROLE, never on the letter (2026-09-11).

    A burst can open a second build lane - a UI session, a desk session - on a
    worktree or a third checkout. Lane A stays the one pen holder; C behaves
    exactly as B, which is what makes rule 1 (partition by module) the thing that
    keeps them apart rather than the letter count.
    """
    (c_row,), _ = h.check_queue(["GATE1"], items, ready, "C")
    (b_row,), _ = h.check_queue(["GATE1"], items, ready, "B")
    assert c_row["surfaces"] == b_row["surfaces"] != []

    rows, _ = h.check_queue(["OPEN1", "READY2", "NOTED1"], items, ready, "C")
    assert h.lane_pens("C", rows) == h.lane_pens("B", rows) != list(h.PENS)

    text = h.render(lane="C", machine="desktop-ui", sender="A", rows=rows, other_queue=[])
    assert "lane: C" in text
    assert "**Lane C claims status-only and never renders.**" in text
    assert "reach the inbox from Lane C)" in text
    # its counterpart is still A, and A still holds every surface pen
    assert "Lane A holds: `backlog · port · adr · gates · snapshot`" in text


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


def test_a_module_surface_renders_with_its_code_pen_only_when_the_module_is_queued(h, items, ready):
    # The row is generated from MODULE_SURFACES, so the test reads the structure rather
    # than retyping the path (one vocabulary for surfaces — the skill's own rule).
    module, surfaces = next(iter(h.MODULE_SURFACES.items()))
    prefix = surfaces[0][0]
    items["WEB1"] = _item_module(module)
    ready.append("WEB1")
    rows, _ = h.check_queue(["WEB1"], items, ready, "B")
    text = h.render(lane="B", machine="laptop", sender="A", rows=rows, other_queue=[])
    assert f"| `code:{module}` | `{prefix}` | this lane, with the module" in text
    rows, _ = h.check_queue(["OPEN1"], items, ready, "B")
    text = h.render(lane="B", machine="laptop", sender="A", rows=rows, other_queue=[])
    assert prefix not in text
    # and it is a module surface, not a Lane A pen: no surface flag for touching it
    assert h.pen_of(prefix) is None


def _item_module(module: str):
    return _item("WEB1", module=module)


# ---- input overlap against the OTHER queue (PLAN5) --------------------------------------


@pytest.fixture
def overlap_items(h):
    return {
        "COARSE1": _item("COARSE1", inputs=("drydocs_api/", "docs/reviews/modules/api.md")),
        "FINE1": _item("FINE1", inputs=("drydocs_api/schemas.py", "docs/reviews/modules/api.md")),
        "SAME1": _item("SAME1", inputs=("web/src/ask/askApi.ts",)),
        "SAME2": _item("SAME2", inputs=(".\\web\\src\\ask\\askApi.ts",)),
        "REVIEWONLY1": _item("REVIEWONLY1", inputs=("docs/reviews/modules/api.md",)),
        "APART1": _item("APART1", inputs=("drydocs_core/x.py",)),
        "DONE2": _item("DONE2", status="done", inputs=("drydocs_api/schemas.py",)),
    }


def test_a_coarse_prefix_covers_a_finer_path_and_the_row_names_the_coarse_side(h, overlap_items):
    rows = h.input_overlaps(["FINE1"], ["COARSE1"], overlap_items)
    assert [(r["shared"], r["coarse"]) for r in rows] == [("drydocs_api", "COARSE1")]
    assert h.format_overlap(rows[0]) == (
        "FINE1 <-> COARSE1: `drydocs_api` (COARSE1's input, coarse) covers `drydocs_api/schemas.py`"
    )
    # symmetric: the same collision seen from the coarse side names the same coarse item
    (back,) = h.input_overlaps(["COARSE1"], ["FINE1"], overlap_items)
    assert back["coarse"] == "COARSE1"
    assert h.covers("a/b", "a/b/c") == "a/b" == h.covers("a/b/c", "a/b")
    assert h.covers("a/b", "a/bc") is None


def test_the_same_path_is_one_row_after_normalization(h, overlap_items):
    (row,) = h.input_overlaps(["SAME1"], ["SAME2"], overlap_items)
    assert row["coarse"] == "same"
    assert h.format_overlap(row) == "SAME1 <-> SAME2: both name `web/src/ask/askApi.ts`"


def test_a_shared_review_path_is_provenance_and_never_an_overlap(h, overlap_items):
    """The PLAN5 (b) ruling, 2026-09-08: exclude provenance by convention, no outputs field.
    COARSE1 and FINE1 both name the review that spawned them; only the code path collides."""
    assert h.PROVENANCE_PREFIXES == ("docs/reviews/",)
    assert h.input_overlaps(["REVIEWONLY1"], ["COARSE1", "FINE1"], overlap_items) == []
    assert len(h.input_overlaps(["FINE1"], ["COARSE1"], overlap_items)) == 1
    assert h.write_inputs(overlap_items["COARSE1"]) == ["drydocs_api"]


def test_disjoint_and_unknown_and_self_ids_yield_no_rows(h, overlap_items):
    assert h.input_overlaps(["APART1"], ["COARSE1", "GHOST9"], overlap_items) == []
    assert h.input_overlaps(["COARSE1"], ["COARSE1"], overlap_items) == []


def test_check_queue_carries_overlap_as_a_flag_and_render_records_the_other_queue(
    h, items, overlap_items
):
    items.update(overlap_items)
    ready = [i for i, it in items.items() if it["status"] == "todo" and not it["depends_on"]]
    (row,), refusals = h.check_queue(["FINE1"], items, ready, "B", other=["COARSE1"])
    assert refusals == [] and row["overlap"] == [
        "FINE1 <-> COARSE1: `drydocs_api` (COARSE1's input, coarse) covers `drydocs_api/schemas.py`"
    ]
    (clean,), _ = h.check_queue(["FINE1"], items, ready, "B")
    assert clean["overlap"] == []
    text = h.render(
        lane="B", machine="laptop", sender="A", rows=[row], other_queue=["COARSE1", "APART1"]
    )
    assert "\nother_queue: [COARSE1, APART1]\n" in text
    assert "overlap: FINE1 <-> COARSE1" in text


def test_check_reruns_the_overlap_from_the_front_matter_and_skips_files_that_predate_it(
    h, items, overlap_items, tmp_path, capsys
):
    items.update(overlap_items)
    f = tmp_path / "lane-b-handoff.md"
    f.write_text("---\nqueue: [FINE1]\nother_queue: [COARSE1, DONE2]\n---\n", encoding="utf-8")
    assert h.cmd_check(f, items) == 1
    out = capsys.readouterr().out
    assert "Input overlap, open items on both sides (1):" in out
    assert "FINE1 <-> COARSE1" in out and "DONE2" not in out  # a done item is not a collision
    # predates PLAN5: no other_queue line — graceful, and the queue verdict is unchanged
    f.write_text("---\nqueue: [FINE1]\n---\n", encoding="utf-8")
    assert h.cmd_check(f, items) == 1
    out = capsys.readouterr().out
    assert "no `other_queue:` line" in out and "skipped" in out and "Keep the file" in out


def test_the_prototype_retired_when_the_fold_in_landed(h):
    assert not (Path(h.__file__).parent / "overlap_prototype.py").exists()


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
