"""P5 — maintenance-window query: math, parsing, findings, and the committed cypher.

The window math is the acceptance's load-bearing clause: CRITICAL-PATH BASED,
NEVER A PATH SUM (the standing TDQ-ETA rule). ``test_union_never_a_sum`` pins
it directly: two chained 2-hour jobs overlapping one hour busy the clock for
three hours, not four.
"""

from __future__ import annotations

import re

from drydocs.loaders.patch_window import (
    CYPHER_PATH,
    DAY,
    build_report,
    load_sections,
    merge_busy,
    parse_time_of_day,
    quiet_gaps,
)

# ---------------------------------------------------------------- time parsing


def test_parse_time_shapes() -> None:
    assert parse_time_of_day("02:30") == 150
    assert parse_time_of_day("02:30:59") == 150
    assert parse_time_of_day("0230") == 150
    assert parse_time_of_day("023059") == 150
    assert parse_time_of_day(230) == 150  # bare HMM int
    assert parse_time_of_day("00:00") == 0
    assert parse_time_of_day("23:59") == 23 * 60 + 59


def test_parse_rejects_junk_never_guesses() -> None:
    for junk in (None, "", "25:00", "12:61", "morning", "1234567", "12,30", -1):
        assert parse_time_of_day(junk) is None, junk


# ---------------------------------------------------------------- interval math


def test_union_never_a_sum() -> None:
    """The TDQ-ETA rule: chained overlapping jobs busy the EXTENT, not the sum."""
    # 01:00-03:00 and 02:00-04:00 — a path sum would claim 4h of busy clock
    busy = merge_busy([(60, 180), (120, 240)])
    assert busy == [(60, 240)]  # 3h extent
    assert sum(e - s for s, e in busy) == 180  # == 3h, not 4h


def test_disjoint_intervals_stay_disjoint() -> None:
    assert merge_busy([(600, 660), (60, 120)]) == [(60, 120), (600, 660)]


def test_midnight_wrap_merges_across_the_boundary() -> None:
    # 23:00-01:00 (wrapped) + 00:30-02:00 -> one busy window 23:00-02:00
    busy = merge_busy([(23 * 60, 25 * 60), (30, 120)])
    assert busy == [(23 * 60, 26 * 60)]
    quiet = quiet_gaps(busy)
    assert quiet == [(120, 23 * 60)]  # 02:00-23:00


def test_full_day_busy_has_no_quiet_window() -> None:
    assert merge_busy([(0, DAY)]) == [(0, DAY)]
    assert quiet_gaps([(0, DAY)]) == []
    # one interval spanning >= a day covers everything regardless of phase
    assert merge_busy([(300, 300 + DAY)]) == [(0, DAY)]


def test_no_busy_means_whole_day_quiet() -> None:
    assert quiet_gaps([]) == [(0, DAY)]


def test_wraparound_quiet_gap() -> None:
    # busy 08:00-18:00 -> quiet 18:00-08:00 (one wrapped gap, not two halves)
    quiet = quiet_gaps(merge_busy([(480, 1080)]))
    assert quiet == [(1080, 480 + DAY)]


# ---------------------------------------------------------------- report assembly


def _row(**over) -> dict:
    base = {
        "job_name": "JOB_A",
        "job_id": "1",
        "path": "host_group",
        "group_name": "grp-x",
        "pinned_host": None,
        "folder": "F1",
        "node_id": "grp-x",
        "avg_start_time": None,
        "start_next_day": None,
        "avg_run_time": None,
        "window_start": None,
        "window_end": None,
    }
    base.update(over)
    return base


def test_report_places_job_stats_over_folder_window() -> None:
    rows = [
        _row(avg_start_time="01:00", avg_run_time=7200, window_start="00:00", window_end="12:00")
    ]
    report = build_report("group", "grp-x", {"group_jobs": rows})
    assert report.placeable_jobs == 1
    assert report.jobs[0]["window_source"] == "job_stats"
    assert report.busy == [{"start": "01:00", "end": "03:00", "minutes": 120}]
    # quiet ranked longest first
    assert report.quiet[0]["minutes"] == DAY - 120


def test_report_falls_back_to_folder_window() -> None:
    rows = [_row(window_start="22:00", window_end="02:00")]  # crosses midnight
    report = build_report("group", "grp-x", {"group_jobs": rows})
    assert report.jobs[0]["window_source"] == "folder_window"
    assert report.busy == [{"start": "22:00", "end": "02:00", "minutes": 240}]


def test_no_timing_is_a_finding_not_a_guess() -> None:
    report = build_report("group", "grp-x", {"group_jobs": [_row()]})
    assert report.placeable_jobs == 0
    assert report.unplaceable_jobs == 1
    assert [f.kind for f in report.findings] == ["no_timing_data"]
    assert report.quiet == [{"start": "00:00", "end": "00:00", "minutes": DAY}]


def test_unparseable_timing_is_its_own_finding() -> None:
    report = build_report(
        "group",
        "grp-x",
        {"group_jobs": [_row(avg_start_time="sometimes", window_start="junk", window_end="junk")]},
    )
    assert [f.kind for f in report.findings] == ["unparseable_timing"]


def test_runtime_outlier_never_covers_the_clock() -> None:
    # the gate's junk class: avg_run_time ~ 2.65 years
    report = build_report(
        "group",
        "grp-x",
        {"group_jobs": [_row(avg_start_time="01:00", avg_run_time=83_804_487)]},
    )
    assert report.placeable_jobs == 0
    assert [f.kind for f in report.findings] == ["runtime_outlier"]
    assert report.quiet[0]["minutes"] == DAY  # clock NOT silently busied


def test_hardcoded_pin_is_both_a_job_and_a_finding() -> None:
    pinned = _row(
        job_name="JOB_P",
        path="agent_host",
        pinned_host="host-1",
        node_id="host-1",
        avg_start_time="04:00",
        avg_run_time=600,
    )
    report = build_report("group", "grp-x", {"group_hardcoded": [pinned]})
    assert report.placeable_jobs == 1
    kinds = [f.kind for f in report.findings]
    assert "hardcoded_bypass" in kinds


def test_cross_validation_findings() -> None:
    report = build_report(
        "host",
        "host-1",
        {
            "host_direct": [],
            "xval_intent_without_edge": [{"job_name": "JOB_I", "node_id": "host-1"}],
            "xval_stale_edge_host": [{"job_name": "JOB_S", "node_id": "elsewhere"}],
        },
    )
    kinds = sorted(f.kind for f in report.findings)
    assert kinds == ["intent_without_edge", "stale_edge"]


def test_multi_dc_group_ambiguity_is_surfaced() -> None:
    report = build_report(
        "group",
        "grp-x",
        {
            "group_jobs": [],
            "group_dcs": [{"data_center": "DC1"}, {"data_center": "DC2"}],
        },
    )
    assert [f.kind for f in report.findings] == ["multi_dc_group"]


def test_duplicate_rows_across_sections_dedupe() -> None:
    row = _row(avg_start_time="01:00", avg_run_time=60)
    report = build_report("group", "grp-x", {"group_jobs": [row, dict(row)]})
    assert len(report.jobs) == 1


# ---------------------------------------------------------------- committed cypher


def test_committed_cypher_sections_exist() -> None:
    sections = load_sections()
    for name in (
        "host_exists",
        "group_exists",
        "group_dcs",
        "host_direct",
        "host_via_group",
        "group_jobs",
        "group_hardcoded",
        "xval_intent_without_edge",
        "xval_stale_edge_host",
        "xval_stale_edge_group",
    ):
        assert name in sections, name
        assert "$target" in sections[name], name


def test_committed_cypher_is_read_only_and_o33_guarded() -> None:
    text = CYPHER_PATH.read_text(encoding="utf-8")
    code = "\n".join(line for line in text.splitlines() if not line.strip().startswith("//"))
    for verb in ("MERGE", "CREATE", "DELETE", "DETACH", "REMOVE", "DROP", "SET "):
        assert not re.search(rf"\b{verb.strip()}\b", code, re.IGNORECASE), verb
    for name, stmt in load_sections().items():
        assert "SchemaMeta" in stmt, f"{name} is missing the O33 exemplar guard"
