"""MM3 — the search log: theme and novelty columns, written as a declared kind.

The acceptance's one named refusal — a row without a theme — is tested before
any I/O happens, because that is where the rule has to hold.
"""

from __future__ import annotations

import importlib
import json
import logging
from datetime import datetime

import pytest

from drydocs_core import log_kinds
from drydocs_deepdoc import search_log as sl
from drydocs_deepdoc.mindmap import new_mindmap
from drydocs_deepdoc.search_log import SearchLog, SearchLogError, SearchRow, score_novelty

_AT = datetime(2026, 8, 25, 14, 30, 15)


@pytest.fixture
def logdir(tmp_path, monkeypatch):
    d = tmp_path / "logs"
    d.mkdir()
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(d))
    return d


def _row(**over):
    base = dict(
        tool="confluence",
        search="<DATAFLOW> producer register",
        theme="ownership/producer_app",
        results=3,
        new_ids=("70007",),
        seed="<folder>",
    )
    base.update(over)
    return SearchRow(**base)


# ---- the refusal -------------------------------------------------------------------


@pytest.mark.parametrize("theme", ["", "   ", None])
def test_a_row_without_a_theme_is_refused(theme) -> None:
    with pytest.raises(SearchLogError, match="without a theme"):
        _row(theme=theme)


@pytest.mark.parametrize("theme", ["ownership", "/producer_app", "ownership/"])
def test_a_theme_that_is_not_branch_slash_slot_is_refused(theme: str) -> None:
    with pytest.raises(SearchLogError, match="<branch>/<slot>"):
        _row(theme=theme)


def test_the_refusal_happens_before_any_io(logdir) -> None:
    with pytest.raises(SearchLogError):
        SearchLog().append(_row(theme=""))  # type: ignore[arg-type]
    assert list(logdir.iterdir()) == []


def test_a_theme_must_name_a_slot_when_the_map_is_given(logdir) -> None:
    log = SearchLog()
    with pytest.raises(SearchLogError, match="names no slot"):
        log.append(_row(theme="ownership/nope"), mindmap=new_mindmap("<folder>"))
    assert list(logdir.iterdir()) == []
    log.append(_row(), mindmap=new_mindmap("<folder>"))  # a real slot: accepted
    assert len(list(logdir.iterdir())) == 1


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("tool", "", "names the tool"),
        ("search", " ", "carries the search"),
        ("results", -1, "whole count"),
        ("results", True, "whole count"),
        ("new_ids", ["70007"], "tuple"),
    ],
)
def test_the_other_columns_are_shape_checked(field: str, value, match: str) -> None:
    with pytest.raises(SearchLogError, match=match):
        _row(**{field: value})


# ---- the columns ---------------------------------------------------------------------


def test_append_writes_one_jsonl_line_with_every_column(logdir) -> None:
    record = SearchLog().append(_row())
    files = list(logdir.iterdir())
    assert len(files) == 1
    assert files[0].name.startswith("search.deepdoc.") and files[0].name.endswith(".jsonl")
    lines = files[0].read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    written = json.loads(lines[0])
    assert written == record
    assert tuple(written) == sl.COLUMNS
    assert written["theme"] == "ownership/producer_app"
    assert written["novelty"] == 1 and written["new_ids"] == ["70007"]
    assert written["results"] == 3 and written["tool"] == "confluence"
    assert written["seed"] == "<folder>"
    datetime.fromisoformat(written["date"])  # stamped at append, parseable


def test_novelty_is_the_count_of_new_ids_never_a_separate_number() -> None:
    assert _row(new_ids=()).novelty == 0
    assert _row(new_ids=("70007", "AUTO-1234")).novelty == 2


def test_appends_accumulate_in_one_day_file_and_read_back_in_order(logdir) -> None:
    log = SearchLog()
    log.append(_row(search="first", new_ids=("70007",)))
    log.append(_row(search="second", new_ids=("AUTO-1234", "70007")))
    rows = log.rows()
    assert [r["search"] for r in rows] == ["first", "second"]
    assert log.logged_ids() == ("70007", "AUTO-1234")
    assert len(list(logdir.iterdir())) == 1  # one ledger, not one file per append


def test_rows_of_a_day_with_no_file_is_empty(logdir) -> None:
    assert SearchLog().rows() == ()
    assert SearchLog().logged_ids() == ()


# ---- novelty -----------------------------------------------------------------------


def test_score_novelty_is_found_minus_known_in_first_seen_order() -> None:
    found = ("70007", "AUTO-1234", "70007", "STAGE.ORDERS_DAILY", "AUTO-1234")
    known = ("AUTO-1234",)
    assert score_novelty(found, known) == ("70007", "STAGE.ORDERS_DAILY")
    assert score_novelty(found, found) == ()
    assert score_novelty((), known) == ()


def test_the_record_half_of_known_comes_from_the_log_itself(logdir) -> None:
    """Round 1 finds an id; round 2 finds it again — it is no longer new."""
    log = SearchLog()
    log.append(_row(new_ids=score_novelty(("70007",), known=())))
    second = score_novelty(("70007", "AUTO-1234"), known=log.logged_ids())
    assert second == ("AUTO-1234",)


# ---- the declared kind --------------------------------------------------------------


def test_the_kind_is_declared_per_day_jsonl_and_names_this_writer() -> None:
    declared = log_kinds.kind(sl.KIND)
    assert (declared.rotation, declared.format, declared.planned) == ("per-day", "jsonl", False)
    module_name, _, class_name = declared.writer.rpartition(".")
    assert getattr(importlib.import_module(module_name), class_name) is SearchLog


def test_the_filename_derives_from_the_declaration() -> None:
    assert SearchLog().path(now=_AT).name == "search.deepdoc.20260825.jsonl"


def test_theme_helpers_round_trip() -> None:
    assert sl.theme_for("ownership", "producer_app") == "ownership/producer_app"
    assert sl.split_theme("ownership/producer_app") == ("ownership", "producer_app")
    with pytest.raises(SearchLogError):
        sl.theme_for("", "x")


def test_an_unwritable_log_dir_warns_and_never_raises(tmp_path, monkeypatch, caplog) -> None:
    blocker = tmp_path / "not-a-dir"
    blocker.write_text("x", encoding="utf-8")
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(blocker))
    with caplog.at_level(logging.WARNING, logger="drydocs_deepdoc.search_log"):
        record = SearchLog().append(_row())
    assert record["theme"] == "ownership/producer_app"  # the row is still returned
    assert any("search log unavailable" in r.message for r in caplog.records)
