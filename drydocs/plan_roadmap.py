"""plan_roadmap.py — render the per-module roadmap to docs/plan/roadmap.html.

THE PAGE THIS ADDS (user directive 2026-08-07): the third planning surface, beside
the board (``board.html``) and the idea inbox (``ideas.html``) — per module, how far
the functionality is built out relative to the backlog, and a size estimate for each
open inbox idea. A roadmap without target dates: stages and estimates are relative
judgments, never commitments.

TWO SOURCES, ONE RULE EACH. ``docs/restructure/roadmap.yaml`` carries what only a
human judgment can: the stage call, the built/remaining prose, the idea estimates.
``docs/restructure/backlog.yaml`` carries what must never be transcribed: item
counts, statuses, and open-item titles are read live at render time, so the numbers
on the page cannot rot in the authored file. The coverage guard in
``tests/unit/test_plan_roadmap.py`` closes the loop: every module in the backlog's
``modules:`` registry must have a roadmap entry, so registering a module forces a
build-out judgment for it.

Same contracts as the sibling pages: deterministic (no clock, no host path —
byte-identical output for identical input, so the session ritual's stale-render
check works on it), self-contained (opens from ``file://`` offline), committed.
Lives in the ``plan`` component group WITH ``plan_board`` — the backlog parsing is
plan_board's published shape, and a within-group import is what the component
boundary allows (unlike plan_ideas, which renders markdown and therefore lives in
docgen). classification: Internal — idea summaries ride along, same boundary as the
inbox page.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

import yaml

from drydocs.plan_board import WorkItem, backlog_from_dict
from drydocs_core.repo_paths import repo_root

# Caller's checkout, not the installed package's — see plan_board / Idea-109.
_REPO_ROOT = repo_root(Path(__file__).resolve().parent.parent)
DEFAULT_ROADMAP_PATH = _REPO_ROOT / "docs" / "restructure" / "roadmap.yaml"
DEFAULT_ROADMAP_BACKLOG_PATH = _REPO_ROOT / "docs" / "restructure" / "backlog.yaml"
DEFAULT_ROADMAP_OUT_PATH = _REPO_ROOT / "docs" / "plan" / "roadmap.html"

STAGES: dict[str, str] = {
    "mature": "built out; changes are refinements",
    "active": "under active build-out",
    "early": "core exists; maturation ahead",
    "steady": "steady-state; grows additively",
    "parked": "deliberately paused on a named trigger",
}
ESTIMATES: dict[str, str] = {
    "S": "one focused session",
    "M": "a few sessions, one backlog item",
    "L": "an epic slice — multiple sessions, usually a HITL gate",
    "XL": "a multi-epic program",
}
#: Statuses that count as "open" for the progress bar and the open-item list —
#: everything that is not done, in the order the list shows them.
_OPEN_ORDER: tuple[str, ...] = ("in_progress", "blocked", "todo")


class RoadmapError(RuntimeError):
    """The roadmap file is missing, malformed, or disagrees with the backlog."""


def load_roadmap(path: str | Path = DEFAULT_ROADMAP_PATH) -> dict[str, Any]:
    """Parse and validate ``roadmap.yaml`` shape (schema, enums). Pure — no graph."""
    path = Path(path)
    if not path.exists():
        raise RoadmapError(f"roadmap file not found: {path}")
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    schema = str(doc.get("schema", ""))
    if not schema.startswith("drydocs.roadmap."):
        raise RoadmapError(
            f"unexpected roadmap schema {schema!r} — expected it to start with "
            "'drydocs.roadmap.'"
        )
    if not doc.get("updated"):
        raise RoadmapError("roadmap is missing an `updated:` date")
    entries = doc.get("modules")
    if not isinstance(entries, list) or not entries:
        raise RoadmapError("roadmap `modules` is missing or empty")
    for entry in entries:
        name = entry.get("module")
        if not name:
            raise RoadmapError(f"roadmap entry needs a `module`: {entry!r}")
        stage = entry.get("stage")
        if stage not in STAGES:
            raise RoadmapError(f"[{name}] stage {stage!r} is not one of {sorted(STAGES)}")
        if not str(entry.get("built", "")).strip():
            raise RoadmapError(f"[{name}] needs a `built` assessment")
        if not str(entry.get("remaining", "")).strip():
            raise RoadmapError(f"[{name}] needs a `remaining` assessment")
        for idea in entry.get("ideas") or []:
            iid = idea.get("id", "")
            if not str(iid).startswith("Idea-"):
                raise RoadmapError(f"[{name}] idea id {iid!r} must be an Idea-N id")
            if idea.get("estimate") not in ESTIMATES:
                raise RoadmapError(
                    f"[{name}] {iid}: estimate {idea.get('estimate')!r} is not one "
                    f"of {sorted(ESTIMATES)}"
                )
            if not str(idea.get("note", "")).strip():
                raise RoadmapError(f"[{name}] {iid} needs a `note`")
    return doc


def check_coverage(roadmap: dict[str, Any], backlog_doc: dict[str, Any]) -> None:
    """The roadmap and the backlog `modules:` registry must name the SAME set.

    A missing entry means a registered module has no build-out judgment; an extra
    entry means the roadmap describes a module the backlog does not know — either
    way the page would silently lie by omission, so both are hard errors.
    """
    registry = set(backlog_doc.get("modules") or [])
    covered = {e["module"] for e in roadmap["modules"]}
    missing = sorted(registry - covered)
    unknown = sorted(covered - registry)
    if missing or unknown:
        raise RoadmapError(
            f"roadmap/backlog module mismatch — missing from roadmap: {missing}; "
            f"not in the backlog registry: {unknown}"
        )


# ── rendering ────────────────────────────────────────────────────────────


def _esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _prose(value: Any) -> str:
    """Collapse folded-YAML whitespace so prose renders as one clean paragraph."""
    return _esc(" ".join(str(value or "").split()))


def _open_items(items: tuple[WorkItem, ...], module: str) -> list[WorkItem]:
    in_module = [it for it in items if it.module == module and it.status != "done"]
    return sorted(in_module, key=lambda it: (_OPEN_ORDER.index(it.status), it.id))


def _render_idea_row(idea: dict[str, Any]) -> str:
    return (
        "<tr>"
        f'<td><a class="idea-link" href="ideas.html">{_esc(idea["id"])}</a></td>'
        f'<td><span class="est est-{_esc(idea["estimate"])}">{_esc(idea["estimate"])}'
        "</span></td>"
        f"<td>{_prose(idea['note'])}</td>"
        "</tr>"
    )


def _render_module(entry: dict[str, Any], items: tuple[WorkItem, ...]) -> str:
    module = entry["module"]
    done = sum(1 for it in items if it.module == module and it.status == "done")
    open_items = _open_items(items, module)
    total = done + len(open_items)
    pct = round(100 * done / total) if total else 0
    counts = f"{done} done &middot; {len(open_items)} open" if total else "no backlog items"

    open_html = ""
    if open_items:
        rows = "\n".join(
            f'<li><a class="item-link" href="board.html#card-{_esc(it.id)}">'
            f"{_esc(it.id)}</a> "
            f'<span class="status-badge status-{_esc(it.status)}">{_esc(it.status)}'
            f"</span> {_esc(it.title)}</li>"
            for it in open_items
        )
        open_html = f'<ul class="open-items">\n{rows}\n</ul>'

    ideas = entry.get("ideas") or []
    ideas_html = ""
    if ideas:
        rows = "\n".join(_render_idea_row(i) for i in ideas)
        ideas_html = (
            '<table class="ideas"><thead><tr><th>Idea</th><th>Size</th>'
            "<th>What / trigger</th></tr></thead>"
            f"<tbody>\n{rows}\n</tbody></table>"
        )

    return (
        f'<section class="module" id="module-{_esc(module)}">'
        f'<div class="module-head"><h2>{_esc(module)}</h2>'
        f'<span class="stage stage-{_esc(entry["stage"])}">{_esc(entry["stage"])}'
        f'</span><span class="counts">{counts}</span></div>'
        '<div class="progress"><div class="progress-bar" style="width:'
        f'{pct}%"></div></div>'
        f'<p class="prose"><strong>Built:</strong> {_prose(entry["built"])}</p>'
        f'<p class="prose"><strong>Remaining:</strong> {_prose(entry["remaining"])}</p>'
        f"{open_html}"
        f"{ideas_html}"
        "</section>"
    )


_CSS = """
:root{color-scheme:light}
body{font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:#1a1a1a;
  margin:2rem auto;padding:0 1.5rem 3rem;max-width:64rem;background:#fff}
h1{font-size:1.5rem;margin:0 0 .3rem}
h2{font-size:1.1rem;margin:0}
.subtitle{color:#666;font-size:.85rem;margin:.2rem 0}
.backlink{display:inline-block;margin:0 .3rem 1.2rem 0;padding:.35rem .8rem;
  border:1px solid #2563eb;border-radius:4px;background:#fff;color:#2563eb;
  text-decoration:none;font-size:.85rem}
.backlink:hover{background:#eff6ff}
.legend{border:1px solid #e2e2e2;border-radius:8px;background:#f9fafb;
  padding:.6rem .9rem;font-size:.8rem;color:#444;margin:1rem 0 1.5rem}
.legend dt{font-weight:600;display:inline}
.legend dd{display:inline;margin:0 .9rem 0 .25rem}
.module{border:1px solid #e2e2e2;border-radius:8px;padding:.8rem 1rem;margin:.9rem 0;
  background:#fafafa}
.module-head{display:flex;align-items:center;gap:.6rem;flex-wrap:wrap}
.counts{margin-left:auto;color:#666;font-size:.8rem}
.stage{display:inline-block;padding:.05rem .5rem;border-radius:4px;font-size:.72rem;
  text-transform:uppercase;letter-spacing:.02em}
.stage-mature{background:#bbf7d0;color:#166534}
.stage-active{background:#dbeafe;color:#1e40af}
.stage-early{background:#fde68a;color:#92400e}
.stage-steady{background:#e5e7eb;color:#374151}
.stage-parked{background:#e9d5ff;color:#6b21a8}
.progress{height:.4rem;background:#e5e7eb;border-radius:4px;overflow:hidden;
  margin:.45rem 0 .3rem}
.progress-bar{height:100%;background:#2563eb}
.prose{font-size:.88rem;margin:.35rem 0;color:#333}
.open-items{margin:.4rem 0 .2rem;padding-left:1.1rem;font-size:.85rem}
.open-items li{margin:.25rem 0}
.item-link{font-family:ui-monospace,monospace;font-weight:700;color:#2563eb;
  text-decoration:none}
.item-link:hover{text-decoration:underline}
.status-badge{display:inline-block;padding:0 .35rem;border-radius:4px;font-size:.7rem;
  text-transform:uppercase;letter-spacing:.02em}
.status-todo{background:#e5e7eb;color:#374151}
.status-in_progress{background:#fde68a;color:#92400e}
.status-blocked{background:#fecaca;color:#991b1b}
.ideas{border-collapse:collapse;margin:.5rem 0 .2rem;font-size:.83rem}
.ideas td,.ideas th{border:1px solid #e2e2e2;padding:.3rem .55rem;text-align:left;
  vertical-align:top}
.ideas th{background:#f3f4f6}
.idea-link{font-family:ui-monospace,monospace;font-weight:700;color:#2563eb;
  text-decoration:none}
.idea-link:hover{text-decoration:underline}
.est{display:inline-block;min-width:1.4rem;text-align:center;border-radius:4px;
  padding:0 .3rem;font-weight:700;font-size:.78rem;background:#eef2ff;color:#3730a3}
""".strip()


def render_roadmap(roadmap: dict[str, Any], backlog_doc: dict[str, Any]) -> str:
    """Render the roadmap page. Pure and deterministic — no clock, no host path."""
    check_coverage(roadmap, backlog_doc)
    backlog = backlog_from_dict(backlog_doc)
    sections = "\n".join(_render_module(e, backlog.items) for e in roadmap["modules"])
    stage_legend = "".join(f"<dt>{_esc(k)}</dt><dd>{_esc(v)}</dd>" for k, v in STAGES.items())
    est_legend = "".join(f"<dt>{_esc(k)}</dt><dd>{_esc(v)}</dd>" for k, v in ESTIMATES.items())
    return (
        '<!doctype html>\n<html><head><meta charset="utf-8">\n'
        "<title>DryDocs — module roadmap</title>\n"
        f"<style>{_CSS}</style>\n</head><body>\n"
        '<a class="backlink" href="board.html">&larr; Project board</a>'
        '<a class="backlink" href="ideas.html">Idea inbox &rarr;</a>\n'
        "<h1>DryDocs — module roadmap</h1>\n"
        '<p class="subtitle">Per-module build-out vs. the backlog, with size '
        "estimates for open ideas. Assessments from "
        f"<code>docs/restructure/roadmap.yaml</code> (updated "
        f"{_esc(roadmap['updated'])}); counts and open items read live from "
        f"<code>backlog.yaml</code> (updated {_esc(backlog.updated)}). "
        "A roadmap without target dates — stages and sizes are relative "
        "judgments, not commitments.</p>\n"
        '<p class="subtitle"><strong>INTERNAL</strong> — idea summaries ride along '
        "(PUBLISH-BOUNDARY.md).</p>\n"
        '<dl class="legend"><strong>Stages:</strong> '
        f"{stage_legend}<br><strong>Idea sizes:</strong> {est_legend}</dl>\n"
        f"{sections}\n"
        "</body></html>\n"
    )


def write_roadmap(
    roadmap_path: str | Path = DEFAULT_ROADMAP_PATH,
    backlog_path: str | Path = DEFAULT_ROADMAP_BACKLOG_PATH,
    out_path: str | Path = DEFAULT_ROADMAP_OUT_PATH,
) -> Path:
    """Load both sources, render, write the HTML to ``out_path``. Returns the path."""
    roadmap = load_roadmap(roadmap_path)
    backlog_doc = yaml.safe_load(Path(backlog_path).read_text(encoding="utf-8")) or {}
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_roadmap(roadmap, backlog_doc), encoding="utf-8", newline="\n")
    return out_path
