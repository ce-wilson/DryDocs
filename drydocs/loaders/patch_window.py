"""Maintenance-window query (P5): best patch window for a host or host group.

Given an ``ExecutionHost.nodeid`` or a ``ControlMHostGroup.name``, collect
every job that can land on it per the signed resolution rules (2-hop
``RUNS_ON {role: host_group}`` through ``CONTAINS_HOST`` + 1-hop
``RUNS_ON {role: agent_host}``), place each job's busy interval on a
24-hour clock, and report the QUIET windows — the gaps where nothing is
scheduled to run — ranked longest first.

THE WINDOW MATH IS CRITICAL-PATH BASED, NEVER A PATH SUM (the standing
TDQ-ETA rule): busy time is the UNION of intervals, so two chained
two-hour jobs that overlap for an hour occupy three hours of clock, not
four. Folder windows arrive pre-shaped the same way — the P4 contract
defines ``window_start``/``window_end`` as min member start .. max member
end, an extent, never a sum of durations.

Busy-interval source, per job, in order (counted, never guessed):

1. job-level ``avg_start_time`` (+ ``avg_run_time`` seconds) — the P4
   supplement properties (gate controlm-avg-run-supplement §A);
2. else the folder's ``window_start``/``window_end`` rollup;
3. else the job is UNPLACEABLE — reported as a ``no_timing_data``
   metadata finding (the remediation feeder), and excluded from the math.

ASSUMED TIME SHAPES (the dpl_mac discipline — the P4 supplement loader is
company-side only today, note 15043cd, so producer-side these normalize
whatever lands): ``HH:MM[:SS]`` strings or bare ``HHMM``/``HHMMSS``
digits; ``avg_run_time`` in seconds. Anything else is an
``unparseable_timing`` finding, never a guess.

The NODE_GROUP <-> RUNS_ON cross-validation rides every run: declared
intent (``ControlMJob.node_id``) is compared with the derived edges in
both directions (intent-without-edge / edge-without-intent), and group
mode also surfaces hard-coded pins onto member hosts (bypassing the
group's load balancing) plus multi-DC group-name ambiguity. All of it
lands in one metadata-findings list — the feeder remediation batches
pull from.

Read-only: the committed Cypher lives in ``cypher/patch_window.cypher``
(named ``// >>> section`` statements); the pass that WRITES the edges is
``runs_on_resolution.py``.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path

CYPHER_PATH = Path(__file__).resolve().parent / "cypher" / "patch_window.cypher"

_SECTION_RE = re.compile(r"^//\s*>>>\s*(?P<name>[a-z_]+)\s*$", re.MULTILINE)

#: minutes in the wall-clock day the intervals live on
DAY = 24 * 60

#: sections whose rows are candidate jobs, per mode
_JOB_SECTIONS = {
    "host": ("host_direct", "host_via_group"),
    "group": ("group_jobs", "group_hardcoded"),
}
_EXISTS_SECTION = {"host": "host_exists", "group": "group_exists"}
_STALE_SECTION = {"host": "xval_stale_edge_host", "group": "xval_stale_edge_group"}


def load_sections(path: Path = CYPHER_PATH) -> dict[str, str]:
    """Parse the committed cypher file into ``{section_name: statement}``."""
    text = path.read_text(encoding="utf-8")
    matches = list(_SECTION_RE.finditer(text))
    sections: dict[str, str] = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        stmt = text[m.end() : end].strip().rstrip(";").strip()
        sections[m.group("name")] = stmt
    return sections


# -- time parsing (tolerant, counted) -----------------------------------------


def parse_time_of_day(value: object) -> int | None:
    """Time-of-day → minutes since midnight, or None when unparseable.

    Accepts ``HH:MM``/``HH:MM:SS`` strings and bare ``HHMM``/``HHMMSS``
    digit strings or ints (Control-M's compact clock). Out-of-range parts
    fail — they are a finding upstream, never clamped here.
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    if ":" in s:
        parts = s.split(":")
        if len(parts) not in (2, 3) or not all(p.isdigit() for p in parts):
            return None
        h, m = int(parts[0]), int(parts[1])
    elif s.isdigit():
        if len(s) in (5, 6):  # H(H)MMSS
            h, m = int(s[:-4]), int(s[-4:-2])
        elif len(s) in (3, 4):  # H(H)MM
            h, m = int(s[:-2]), int(s[-2:])
        else:
            return None
    else:
        return None
    if h > 23 or m > 59:
        return None
    return h * 60 + m


def _run_minutes(value: object) -> int | None:
    """``avg_run_time`` seconds → whole busy minutes (at least 1)."""
    try:
        seconds = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if seconds < 0:
        return None
    return max(1, math.ceil(seconds / 60))


# -- report shapes -------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    """One metadata finding — the remediation-feeder unit."""

    kind: str  # no_timing_data | unparseable_timing | hardcoded_bypass |
    # intent_without_edge | stale_edge | multi_dc_group
    subject: str  # job name (or group name for multi_dc_group)
    detail: str


@dataclass
class PatchWindowReport:
    """Everything `drydocs patch-window` prints; ``as_dict`` is the --json shape."""

    mode: str  # 'host' | 'group'
    target: str
    jobs: list[dict] = field(default_factory=list)
    busy: list[dict] = field(default_factory=list)  # {start,end,minutes} HH:MM
    quiet: list[dict] = field(default_factory=list)  # ranked longest-first
    placeable_jobs: int = 0
    unplaceable_jobs: int = 0
    findings: list[Finding] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "mode": self.mode,
            "target": self.target,
            "jobs": self.jobs,
            "busy_windows": self.busy,
            "quiet_windows": self.quiet,
            "placeable_jobs": self.placeable_jobs,
            "unplaceable_jobs": self.unplaceable_jobs,
            "findings": [vars(f) for f in self.findings],
        }


# -- interval math (union on the 24h circle — never a sum) ---------------------


def merge_busy(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Union of ``(start, end)`` minute intervals on a wrapping day.

    ``end`` may exceed ``start`` by up to a full day (a window crossing
    midnight). Returns disjoint, sorted ``[start, end)`` segments within
    ``[0, DAY)`` — except that a segment wrapping midnight is returned as
    ``(start, end + DAY)`` folded back by the caller via :func:`quiet_gaps`.
    The union IS the critical-path extent: overlap is absorbed, durations
    are never added together (the TDQ-ETA rule).
    """
    segments: list[tuple[int, int]] = []
    for start, end in intervals:
        start %= DAY
        if end <= start:
            raise ValueError(f"empty/inverted interval ({start}, {end})")
        if end - start >= DAY:
            return [(0, DAY)]  # a single interval already covers the clock
        if end > DAY:  # wraps midnight — split into two circle segments
            segments.append((start, DAY))
            segments.append((0, end - DAY))
        else:
            segments.append((start, end))
    if not segments:
        return []
    segments.sort()
    merged = [segments[0]]
    for s, e in segments[1:]:
        ls, le = merged[-1]
        if s <= le:
            merged[-1] = (ls, max(le, e))
        else:
            merged.append((s, e))
    # re-join across midnight so 23:00-24:00 + 00:00-02:00 reads as one window
    if len(merged) > 1 and merged[0][0] == 0 and merged[-1][1] == DAY:
        first, last = merged[0], merged[-1]
        merged = merged[1:-1]
        merged.append((last[0], first[1] + DAY))
    return merged


def quiet_gaps(busy: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Complement of the busy union on the circle, i.e. the patch windows.

    A gap crossing midnight is returned as ``(start, end + DAY)`` — same
    wrapped representation :func:`merge_busy` uses for busy windows.
    """
    if not busy:
        return [(0, DAY)]
    # normalize any wrapped segment back onto the circle for gap walking
    flat: list[tuple[int, int]] = []
    for s, e in busy:
        if e > DAY:
            flat.append((s, DAY))
            flat.append((0, e - DAY))
        else:
            flat.append((s, e))
    flat.sort()
    gaps = [(e1, s2) for (_, e1), (s2, _) in zip(flat, flat[1:], strict=False) if s2 > e1]
    head, tail = flat[0][0], flat[-1][1]
    # the wrap-around gap: last busy end -> first busy start next morning.
    # Absent exactly when busy coverage touches BOTH midnight boundaries
    # (which includes the full-day case).
    if not (head == 0 and tail == DAY):
        gaps.append((tail, head + DAY))
    return gaps


def _fmt(minute: int) -> str:
    m = minute % DAY
    return f"{m // 60:02d}:{m % 60:02d}"


def _window_dicts(windows: list[tuple[int, int]]) -> list[dict]:
    return [{"start": _fmt(s), "end": _fmt(e), "minutes": e - s} for s, e in windows]


# -- assembly -------------------------------------------------------------------


def build_report(mode: str, target: str, sections: dict[str, list[dict]]) -> PatchWindowReport:
    """Pure assembly: fetched rows → report. No I/O, fully unit-testable."""
    report = PatchWindowReport(mode=mode, target=target)
    seen: set[tuple] = set()
    intervals: list[tuple[int, int]] = []

    for section in _JOB_SECTIONS[mode]:
        for row in sections.get(section, []):
            key = (
                row.get("job_id"),
                row.get("path"),
                row.get("group_name"),
                row.get("pinned_host"),
            )
            if key in seen:
                continue
            seen.add(key)
            placement, interval = _place(row)
            job = dict(row)
            job["window_source"] = placement
            report.jobs.append(job)
            name = str(row.get("job_name") or row.get("job_id") or "?")
            if interval is not None:
                intervals.append(interval)
                report.placeable_jobs += 1
            else:
                report.unplaceable_jobs += 1
                if placement == "unparseable":
                    kind, detail = (
                        "unparseable_timing",
                        "timing present but not in an accepted shape",
                    )
                elif placement == "outlier":
                    kind, detail = (
                        "runtime_outlier",
                        "avg_run_time spans a full day or more (the gate's "
                        "known junk-outlier class) — excluded so it cannot "
                        "silently cover the whole clock; fix the stat",
                    )
                else:
                    kind, detail = (
                        "no_timing_data",
                        "no avg_start_time/avg_run_time on the job and no "
                        "window_start/window_end on its folder — fix the "
                        "metadata to place this job",
                    )
                report.findings.append(Finding(kind=kind, subject=name, detail=detail))
            if section == "group_hardcoded":
                report.findings.append(
                    Finding(
                        kind="hardcoded_bypass",
                        subject=name,
                        detail=(
                            f"pinned to member host {row.get('pinned_host')} — "
                            f"bypasses group '{target}' load balancing"
                        ),
                    )
                )

    for row in sections.get("xval_intent_without_edge", []):
        report.findings.append(
            Finding(
                kind="intent_without_edge",
                subject=str(row.get("job_name") or "?"),
                detail=(
                    f"node_id names '{target}' but no RUNS_ON edge exists — "
                    "rerun the resolution pass or the target is missing from the "
                    "CM_HOSTS capture"
                ),
            )
        )
    for row in sections.get(_STALE_SECTION[mode], []):
        report.findings.append(
            Finding(
                kind="stale_edge",
                subject=str(row.get("job_name") or "?"),
                detail=(
                    f"RUNS_ON edge into '{target}' but the job's node_id is now "
                    f"{row.get('node_id')!r} — the edge outlived the intent"
                ),
            )
        )
    if mode == "group":
        dcs = sorted(
            {r.get("data_center") for r in sections.get("group_dcs", []) if r.get("data_center")}
        )
        if len(dcs) > 1:
            report.findings.append(
                Finding(
                    kind="multi_dc_group",
                    subject=target,
                    detail=(
                        f"group name exists in {len(dcs)} data centers "
                        f"({', '.join(dcs)}) — jobs shown span all of them "
                        "(DC scoping blocked on the DEFINED_ON residuals)"
                    ),
                )
            )

    busy = merge_busy(intervals)
    gaps = sorted(quiet_gaps(busy), key=lambda g: (-(g[1] - g[0]), g[0]))
    report.busy = _window_dicts(busy)
    report.quiet = _window_dicts(gaps)
    return report


def _place(row: dict) -> tuple[str, tuple[int, int] | None]:
    """One job's busy interval + which source placed it.

    Returns ``(source, interval)`` where source is ``job_stats`` /
    ``folder_window`` / ``none`` / ``unparseable`` / ``outlier``.
    """
    has_job_timing = row.get("avg_start_time") is not None
    has_folder_window = row.get("window_start") is not None or row.get("window_end") is not None
    if has_job_timing:
        start = parse_time_of_day(row.get("avg_start_time"))
        run = _run_minutes(row.get("avg_run_time"))
        if start is not None and run is not None and run >= DAY:
            # the gate's junk-outlier class (P3c: max ~2.65 years) — never
            # let one bad stat silently declare the whole clock busy
            return "outlier", None
        if start is not None:
            return "job_stats", (start, start + (run or 1))
        # fall through to the folder only if the job-level value was junk
        if has_folder_window:
            placed = _folder_interval(row)
            if placed is not None:
                return "folder_window", placed
        return "unparseable", None
    if has_folder_window:
        placed = _folder_interval(row)
        if placed is not None:
            return "folder_window", placed
        return "unparseable", None
    return "none", None


def _folder_interval(row: dict) -> tuple[int, int] | None:
    start = parse_time_of_day(row.get("window_start"))
    end = parse_time_of_day(row.get("window_end"))
    if start is None or end is None:
        return None
    if end <= start:  # crosses midnight (or a single-instant window)
        end += DAY if end < start else 1
    return (start, end)


# -- fetch ----------------------------------------------------------------------


class PatchWindowQuery:
    """Run the committed read-only sections for one target and build the report."""

    def __init__(self, client, cypher_path: Path = CYPHER_PATH) -> None:
        self.client = client
        self.sections = load_sections(cypher_path)

    def target_exists(self, mode: str, target: str) -> bool:
        rows = self.client.run(self.sections[_EXISTS_SECTION[mode]], target=target)
        return bool(rows and rows[0].get("n"))

    def run(self, mode: str, target: str) -> PatchWindowReport:
        if mode not in _JOB_SECTIONS:
            raise ValueError(f"mode must be 'host' or 'group', got {mode!r}")
        wanted = [*list(_JOB_SECTIONS[mode]), "xval_intent_without_edge", _STALE_SECTION[mode]]
        if mode == "group":
            wanted.append("group_dcs")
        fetched = {name: self.client.run(self.sections[name], target=target) for name in wanted}
        return build_report(mode, target, fetched)
