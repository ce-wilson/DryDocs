"""Backlog project-board renderer (``drydocs-plan`` component).

Renders ``docs/restructure/backlog/`` (schema ``drydocs.backlog.v3``, sharded per ADR 0013 — the
machine-readable SOURCE OF TRUTH for work items, CLAUDE.md §0) into a **self-contained
interactive HTML project board**: a roadmap strip (one card per ``plan.phase``, with a
computed done/total progress bar) above a kanban board (todo / in_progress / blocked /
done columns), with client-side filters (module/phase/epic/type/search) and a
quick-capture box that formats a paste-ready ``docs/restructure/IDEAS.md`` line to the
clipboard. This is the human view that **replaces ``02-backlog.md``** once it lands
(see backlog item I2).

Pure/offline — no Neo4j, no graph write, no network calls. **The repo (``backlog/``)
is the system of record; the browser is a working aid** — filters and quick-capture text
live in ``localStorage`` for convenience only, and quick-capture never writes to the repo
directly; it copies a line for a human to paste into ``IDEAS.md``. classification:
Internal-Public — the renderer is generic and the backlog itself carries no secrets
(SIDs/schemas/credentials live in ``internal/``, never in the backlog).

Rendering is **deterministic**: given the same backlog tree, ``render_board`` always
produces byte-identical HTML — no build timestamps, no randomness. The board is committed
to git, so its diffs must reflect real backlog changes, not render noise. The backlog's
item count is shown in the header instead of a build time (ADR 0013 dropped the hand-set
``updated:`` date — git holds it). Roll-ups (counts, ``next_ready``) are DERIVED here and
rendered; nothing stores them.
"""

from __future__ import annotations

import html
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from drydocs_core.backlog_store import DEFAULT_BACKLOG_DIR, derive_summary, load_backlog_document
from drydocs_core.repo_paths import repo_root

# Resolve the checkout the CALLER is in, not the one this file was installed from —
# the editable install pins ``__file__`` to the main tree, so a worktree run would
# otherwise read main's backlog and write main's board (Idea-109).
_REPO_ROOT = repo_root(Path(__file__).resolve().parent.parent)
DEFAULT_BACKLOG_PATH = DEFAULT_BACKLOG_DIR  # the sharded tree (ADR 0013); a single file still loads
DEFAULT_BOARD_PATH = _REPO_ROOT / "docs" / "plan" / "board.html"

STATUS_COLUMNS: tuple[str, ...] = ("todo", "in_progress", "blocked", "done")
STATUS_LABELS: dict[str, str] = {
    "todo": "To do",
    "in_progress": "In progress",
    "blocked": "Blocked",
    "done": "Done",
}
CAPTURE_TAGS: tuple[str, ...] = ("idea", "bug", "doc", "source", "question", "chore")


class BoardError(RuntimeError):
    """The backlog file is missing, malformed, or not the expected schema."""


@dataclass(frozen=True)
class Phase:
    id: Any
    title: str
    goal: str = ""
    status: str = "todo"
    release: str = ""


@dataclass(frozen=True)
class WorkItem:
    id: str
    title: str
    type: str = ""
    module: str = ""
    phase: Any = None
    epic: str = ""
    agent: str = ""
    model: str = ""
    priority: str = ""
    status: str = "todo"
    depends_on: tuple[str, ...] = ()
    acceptance: str = ""
    notes: str = ""


@dataclass(frozen=True)
class Backlog:
    schema: str
    updated: str
    phases: tuple[Phase, ...] = ()
    items: tuple[WorkItem, ...] = ()


def load_backlog(path: str | Path = DEFAULT_BACKLOG_PATH) -> Backlog:
    """Load the backlog tree (or one monolith-shaped file). Pure — no graph, no network."""
    path = Path(path)
    if not path.exists():
        raise BoardError(f"backlog source not found: {path}")
    try:
        doc = load_backlog_document(path) or {}
    except Exception as exc:  # BacklogStoreError / YAML errors — one failure type for callers
        raise BoardError(str(exc)) from exc
    return backlog_from_dict(doc)


def backlog_from_dict(doc: dict[str, Any]) -> Backlog:
    schema = str(doc.get("schema", ""))
    if not schema.startswith("drydocs.backlog."):
        raise BoardError(
            f"unexpected backlog schema {schema!r} — expected it to start with "
            "'drydocs.backlog.'"
        )
    # ADR 0013: the hand-set `updated:` date is gone from storage; an old single-file
    # document may still carry one and it is shown if present.
    updated = str(doc.get("updated", "") or "")

    raw_phases = doc.get("plan", {}).get("phases") or []
    if not isinstance(raw_phases, list) or not raw_phases:
        raise BoardError("backlog `plan.phases` is missing or empty")
    phases: list[Phase] = []
    for raw in raw_phases:
        if "id" not in raw or not raw.get("title"):
            raise BoardError(f"phase needs an `id` and a `title`: {raw!r}")
        phases.append(
            Phase(
                id=raw["id"],
                title=str(raw["title"]),
                goal=str(raw.get("goal", "")),
                status=str(raw.get("status", "todo")),
                release=str(raw.get("release", "")),
            )
        )

    raw_items = doc.get("items") or []
    if not isinstance(raw_items, list) or not raw_items:
        raise BoardError("backlog `items` is missing or empty")
    items: list[WorkItem] = []
    for raw in raw_items:
        iid = raw.get("id")
        title = raw.get("title")
        if not iid or not title:
            raise BoardError(f"item needs an `id` and a `title`: {raw!r}")
        deps = raw.get("depends_on") or []
        if not isinstance(deps, list):
            raise BoardError(f"[{iid}] depends_on must be a list")
        items.append(
            WorkItem(
                id=str(iid),
                title=str(title),
                type=str(raw.get("type", "")),
                module=str(raw.get("module", "")),
                phase=raw.get("phase"),
                epic=str(raw.get("epic", "")),
                agent=str(raw.get("agent", "")),
                model=str(raw.get("model", "")),
                priority=str(raw.get("priority", "")),
                status=str(raw.get("status", "todo")),
                depends_on=tuple(str(d) for d in deps),
                acceptance=str(raw.get("acceptance", "")),
                notes=str(raw.get("notes", "") or ""),
            )
        )

    return Backlog(schema=schema, updated=updated, phases=tuple(phases), items=tuple(items))


# ── rendering helpers ────────────────────────────────────────────────────


def _esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _phase_progress(phase: Phase, items: tuple[WorkItem, ...]) -> tuple[int, int]:
    in_phase = [it for it in items if it.phase == phase.id]
    done = sum(1 for it in in_phase if it.status == "done")
    return done, len(in_phase)


def _ready_ids(items: tuple[WorkItem, ...]) -> frozenset[str]:
    by_id = {it.id: it for it in items}
    ready = set()
    for it in items:
        if it.status == "todo" and all(
            dep in by_id and by_id[dep].status == "done" for dep in it.depends_on
        ):
            ready.add(it.id)
    return frozenset(ready)


def _chip(label: str, value: str) -> str:
    if not value:
        return ""
    return f'<span class="chip" data-kind="{_esc(label)}">{_esc(value)}</span>'


def _render_phase_card(phase: Phase, items: tuple[WorkItem, ...]) -> str:
    done, total = _phase_progress(phase, items)
    pct = round(100 * done / total) if total else 0
    progress_text = f"{done} / {total}" if total else "no items"
    release = f'<span class="release">{_esc(phase.release)}</span>' if phase.release else ""
    return (
        '<div class="phase-card">'
        f'<div class="phase-head"><span class="phase-id">P{_esc(phase.id)}</span>'
        f'<span class="status-badge status-{_esc(phase.status)}">'
        f"{_esc(phase.status)}</span>{release}</div>"
        f"<h3>{_esc(phase.title)}</h3>"
        f'<p class="goal">{_esc(phase.goal)}</p>'
        '<div class="progress"><div class="progress-bar" style="width:'
        f'{pct}%"></div></div>'
        f'<p class="progress-text">{_esc(progress_text)}</p>'
        "</div>"
    )


def _render_item_card(item: WorkItem, ready_ids: frozenset[str]) -> str:
    classes = "card"
    if item.id in ready_ids:
        classes += " ready"
    dep_links = " ".join(
        f'<a class="dep-link" href="#card-{_esc(dep)}" data-target="card-{_esc(dep)}">'
        f"{_esc(dep)}</a>"
        for dep in item.depends_on
    )
    deps_html = (
        f'<div class="deps"><span class="deps-label">depends on:</span> {dep_links}</div>'
        if item.depends_on
        else ""
    )
    epic_html = f'<div class="epic">{_esc(item.epic)}</div>' if item.epic else ""
    model_agent = " / ".join(v for v in (item.model, item.agent) if v)
    chips = "".join(
        [
            _chip("module", item.module),
            _chip("phase", f"P{item.phase}" if item.phase is not None else ""),
            _chip("type", item.type),
            _chip("priority", item.priority),
            _chip("model-agent", model_agent),
        ]
    )
    notes_html = (
        f'<p class="notes"><strong>Notes:</strong> {_esc(item.notes)}</p>' if item.notes else ""
    )
    return (
        f'<div class="{classes}" id="card-{_esc(item.id)}" data-id="{_esc(item.id)}" '
        f'data-module="{_esc(item.module)}" data-phase="{_esc(item.phase)}" '
        f'data-epic="{_esc(item.epic)}" data-type="{_esc(item.type)}" '
        f'data-status="{_esc(item.status)}" '
        f'data-search="{_esc((item.id + " " + item.title).lower())}" '
        'tabindex="0">'
        f'<div class="card-head"><span class="card-id">{_esc(item.id)}</span>'
        f'<span class="card-title">{_esc(item.title)}</span></div>'
        f'<div class="chips">{chips}</div>'
        f"{epic_html}"
        f"{deps_html}"
        '<div class="detail">'
        f'<p class="acceptance"><strong>Acceptance:</strong> {_esc(item.acceptance)}</p>'
        f"{notes_html}"
        "</div>"
        "</div>"
    )


def _render_column(status: str, items: tuple[WorkItem, ...], ready_ids: frozenset[str]) -> str:
    in_status = [it for it in items if it.status == status]
    cards = "\n".join(_render_item_card(it, ready_ids) for it in in_status)
    if not cards:
        cards = '<p class="empty">(no items)</p>'
    return (
        f'<div class="column" data-status="{_esc(status)}">'
        f'<div class="column-head"><h2>{_esc(STATUS_LABELS.get(status, status))}</h2>'
        f'<span class="count" data-count-for="{_esc(status)}">{len(in_status)}</span></div>'
        f'<div class="column-body">{cards}</div>'
        "</div>"
    )


def _options(values: list[str]) -> str:
    uniq = sorted({v for v in values if v})
    return "\n".join(f'<option value="{_esc(v)}">{_esc(v)}</option>' for v in uniq)


_CSS = """
:root{color-scheme:light}
body{font-family:system-ui,sans-serif;margin:0;padding:1.5rem 2rem 4rem;max-width:96rem;
  margin-left:auto;margin-right:auto;color:#1a1a1a;background:#fff}
h1{font-size:1.5rem;margin:.2rem 0}
h2{font-size:1rem;margin:0}
h3{font-size:1rem;margin:.3rem 0 .2rem}
.subtitle{color:#555;margin:.1rem 0 1rem}
.roadmap{display:flex;flex-wrap:wrap;gap:.75rem;margin:1rem 0 1.5rem}
.phase-card{border:1px solid #e2e2e2;border-radius:8px;padding:.6rem .8rem;background:#fafafa;
  flex:1 1 13rem;min-width:13rem}
.phase-head{display:flex;align-items:center;gap:.4rem;font-size:.8rem;color:#555}
.phase-id{font-weight:700;color:#111}
.release{margin-left:auto;background:#e0e7ff;color:#3730a3;border-radius:4px;padding:0 .35rem;
  font-size:.75rem}
.goal{font-size:.82rem;color:#444;margin:.2rem 0}
.progress{height:.4rem;background:#e5e7eb;border-radius:4px;overflow:hidden;margin:.3rem 0 .15rem}
.progress-bar{height:100%;background:#2563eb}
.progress-text{font-size:.75rem;color:#666;margin:0}
.status-badge{display:inline-block;padding:.05rem .4rem;border-radius:4px;font-size:.72rem;
  text-transform:uppercase;letter-spacing:.02em}
.status-todo{background:#e5e7eb;color:#374151}
.status-in_progress{background:#fde68a;color:#92400e}
.status-blocked{background:#fecaca;color:#991b1b}
.status-done{background:#bbf7d0;color:#166534}
.filters{display:flex;flex-wrap:wrap;gap:.6rem;align-items:end;margin:1rem 0;
  border:1px solid #e2e2e2;border-radius:8px;padding:.7rem .9rem;background:#f9fafb}
.filters label{display:flex;flex-direction:column;font-size:.75rem;color:#444;gap:.15rem}
.filters select,.filters input[type=search]{font:inherit;padding:.25rem .4rem;border:1px solid #ccc;
  border-radius:4px;min-width:9rem}
.filters button{font:inherit;padding:.3rem .7rem;border:1px solid #ccc;border-radius:4px;
  background:#fff;cursor:pointer}
.board{display:grid;grid-template-columns:repeat(4,1fr);gap:.9rem;align-items:start}
.column{border:1px solid #e2e2e2;border-radius:8px;background:#fafafa;min-height:4rem}
.column-head{display:flex;justify-content:space-between;align-items:center;padding:.5rem .7rem;
  border-bottom:1px solid #e2e2e2}
.count{background:#e5e7eb;border-radius:10px;padding:0 .5rem;font-size:.78rem}
.ready-strip{margin:.6rem 0;padding:.5rem .8rem;border:1px dashed #a7f3d0;border-radius:8px;background:#f0fdf4;font-size:.85rem;line-height:1.9}
.ready-id{text-decoration:none;margin-right:.15rem}
.column-body{padding:.5rem;display:flex;flex-direction:column;gap:.5rem}
.card{border:1px solid #e2e2e2;border-radius:6px;padding:.5rem .6rem;background:#fff;cursor:pointer;
  font-size:.85rem}
.card.ready{border-color:#2563eb;box-shadow:0 0 0 1px #2563eb inset}
.card.hidden{display:none}
.card.highlight{outline:2px solid #f59e0b}
.card-head{display:flex;gap:.4rem;align-items:baseline;flex-wrap:wrap}
.card-id{font-weight:700;font-family:ui-monospace,monospace;font-size:.8rem}
.card-title{font-weight:500}
.chips{display:flex;flex-wrap:wrap;gap:.25rem;margin:.3rem 0}
.chip{background:#eef2ff;color:#3730a3;border-radius:4px;padding:.02rem .4rem;font-size:.72rem}
.epic{color:#666;font-size:.72rem;margin-top:.15rem}
.deps{font-size:.75rem;color:#555;margin-top:.25rem}
.deps-label{color:#888}
.dep-link{color:#2563eb;text-decoration:none;margin-right:.3rem}
.dep-link:hover{text-decoration:underline}
.detail{display:none;margin-top:.4rem;border-top:1px dashed #ddd;padding-top:.35rem;font-size:.8rem}
.card.expanded .detail{display:block}
.acceptance,.notes{margin:.2rem 0}
.empty{color:#999;font-size:.85rem;padding:.4rem}
.capture{margin-top:2rem;border:1px solid #e2e2e2;border-radius:8px;padding:.8rem 1rem;
  background:#f9fafb}
.capture-row{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center}
.capture input[type=text]{flex:1 1 20rem;font:inherit;padding:.35rem .5rem;border:1px solid #ccc;
  border-radius:4px}
.capture select{font:inherit;padding:.35rem .4rem;border:1px solid #ccc;border-radius:4px}
.capture button{font:inherit;padding:.35rem .8rem;border:1px solid #2563eb;border-radius:4px;
  background:#2563eb;color:#fff;cursor:pointer}
.capture-hint{font-size:.78rem;color:#666;margin:.4rem 0 0}
.capture-link{display:inline-block;margin-left:.4rem;padding:.15rem .55rem;border:1px solid #2563eb;
  border-radius:4px;background:#fff;color:#2563eb;text-decoration:none;font-size:.78rem}
.capture-link:hover{background:#eff6ff}
.capture-status{font-size:.78rem;color:#166534;margin:.3rem 0 0;min-height:1.1em}
""".strip()


def _item_dict(it: WorkItem) -> dict[str, Any]:
    return {"id": it.id, "status": it.status, "depends_on": list(it.depends_on)}


def render_board(backlog: Backlog) -> str:
    """Render a self-contained interactive project board. Pure — deterministic output."""
    ready_ids = _ready_ids(backlog.items)

    roadmap = "\n".join(_render_phase_card(p, backlog.items) for p in backlog.phases)
    columns = "\n".join(_render_column(s, backlog.items, ready_ids) for s in STATUS_COLUMNS)

    module_opts = _options([it.module for it in backlog.items])
    phase_opts = "\n".join(
        f'<option value="{_esc(p.id)}">P{_esc(p.id)} — {_esc(p.title)}</option>'
        for p in backlog.phases
    )
    epic_opts = _options([it.epic for it in backlog.items])
    type_opts = _options([it.type for it in backlog.items])
    tag_opts = "\n".join(f'<option value="{_esc(t)}">{_esc(t)}</option>' for t in CAPTURE_TAGS)

    total_items = len(backlog.items)
    # ADR 0013 Clause 3: the roll-ups are renderer OUTPUT. Counts from the same items the
    # columns show; `next_ready` from the same rule the ready-badge uses, listed once so a
    # session picking work reads it here instead of from a stored block nothing keeps honest.
    summary = derive_summary({"items": [_item_dict(it) for it in backlog.items]})
    ready_strip = (
        " ".join(
            f'<a class="ready-id" href="#{_esc(i)}"><code>{_esc(i)}</code></a>'
            for i in summary["next_ready"]
        )
        or "<em>nothing is dependency-ready</em>"
    )

    js = r"""
const FILTER_KEY = "drydocs.board.filters";
const cards = () => Array.from(document.querySelectorAll(".card"));

function currentFilters() {
  return {
    module: document.getElementById("f-module").value,
    phase: document.getElementById("f-phase").value,
    epic: document.getElementById("f-epic").value,
    type: document.getElementById("f-type").value,
    q: document.getElementById("f-search").value.trim().toLowerCase(),
  };
}

function applyFilters() {
  const f = currentFilters();
  const counts = { todo: 0, in_progress: 0, blocked: 0, done: 0 };
  cards().forEach((card) => {
    const matches =
      (!f.module || card.dataset.module === f.module) &&
      (!f.phase || card.dataset.phase === f.phase) &&
      (!f.epic || card.dataset.epic === f.epic) &&
      (!f.type || card.dataset.type === f.type) &&
      (!f.q || card.dataset.search.includes(f.q));
    card.classList.toggle("hidden", !matches);
    if (matches) counts[card.dataset.status] = (counts[card.dataset.status] || 0) + 1;
  });
  Object.keys(counts).forEach((status) => {
    const el = document.querySelector('[data-count-for="' + status + '"]');
    if (el) el.textContent = counts[status];
  });
  localStorage.setItem(FILTER_KEY, JSON.stringify(f));
}

function restoreFilters() {
  let saved = {};
  try {
    saved = JSON.parse(localStorage.getItem(FILTER_KEY) || "{}");
  } catch (e) {
    saved = {};
  }
  if (saved.module) document.getElementById("f-module").value = saved.module;
  if (saved.phase) document.getElementById("f-phase").value = saved.phase;
  if (saved.epic) document.getElementById("f-epic").value = saved.epic;
  if (saved.type) document.getElementById("f-type").value = saved.type;
  if (saved.q) document.getElementById("f-search").value = saved.q;
}

function clearFilters() {
  ["f-module", "f-phase", "f-epic", "f-type"].forEach(
    (id) => (document.getElementById(id).value = "")
  );
  document.getElementById("f-search").value = "";
  applyFilters();
}

function jumpToCard(id) {
  const target = document.getElementById(id);
  if (!target) return;
  target.scrollIntoView({ behavior: "smooth", block: "center" });
  target.classList.add("highlight");
  setTimeout(() => target.classList.remove("highlight"), 1500);
}

function wireCards() {
  cards().forEach((card) => {
    card.addEventListener("click", (evt) => {
      if (evt.target.closest("a.dep-link")) return;
      card.classList.toggle("expanded");
    });
    card.addEventListener("keydown", (evt) => {
      if (evt.key === "Enter" || evt.key === " ") {
        evt.preventDefault();
        card.classList.toggle("expanded");
      }
    });
  });
  document.querySelectorAll("a.dep-link").forEach((a) => {
    a.addEventListener("click", (evt) => {
      evt.preventDefault();
      jumpToCard(a.dataset.target);
    });
  });
}

function wireFilters() {
  ["f-module", "f-phase", "f-epic", "f-type"].forEach((id) =>
    document.getElementById(id).addEventListener("change", applyFilters)
  );
  document.getElementById("f-search").addEventListener("input", applyFilters);
  document.getElementById("f-clear").addEventListener("click", clearFilters);
}

function copyText(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard.writeText(text);
  }
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.style.position = "fixed";
  ta.style.opacity = "0";
  document.body.appendChild(ta);
  ta.focus();
  ta.select();
  try {
    document.execCommand("copy");
  } finally {
    document.body.removeChild(ta);
  }
  return Promise.resolve();
}

function wireCapture() {
  const btn = document.getElementById("capture-copy");
  const status = document.getElementById("capture-status");
  btn.addEventListener("click", () => {
    const tag = document.getElementById("capture-tag").value;
    const text = document.getElementById("capture-text").value.trim();
    if (!text) {
      status.textContent = "Type something to capture first.";
      return;
    }
    const line = "- [" + tag + "] " + text;
    copyText(line).then(() => {
      status.textContent = "Copied: " + line;
    }).catch(() => {
      status.textContent = "Could not copy automatically — select and copy: " + line;
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  wireCards();
  wireFilters();
  wireCapture();
  restoreFilters();
  applyFilters();
});
""".strip()

    return (
        '<!doctype html>\n<html><head><meta charset="utf-8">\n'
        "<title>DryDocs — project board</title>\n"
        f"<style>{_CSS}</style>\n</head><body>\n"
        "<h1>DryDocs — project board</h1>\n"
        f'<p class="subtitle">Rendered from <code>docs/restructure/backlog/</code> '
        f"{('(updated ' + _esc(backlog.updated) + ') &middot; ') if backlog.updated else ''}"
        f"{total_items} items &middot; {summary['todo']} todo / {summary['in_progress']} in progress / "
        f"{summary['blocked']} blocked / {summary['done']} done. "
        "The repo is the system of record; this page is a working aid.</p>\n"
        # Self-locating URL: filled client-side so the committed HTML stays
        # byte-identical across machines (producer C:\ vs company I:\) and the
        # stale-board determinism check keeps working.
        '<p class="subtitle">Location: <code id="board-url"></code> '
        '<button type="button" id="board-url-copy">copy</button></p>\n'
        "<script>document.getElementById('board-url').textContent=window.location.href;"
        "document.getElementById('board-url-copy').onclick=function(){"
        "navigator.clipboard.writeText(window.location.href);};</script>\n"
        # The third planning surface (2026-08-07): per-module build-out vs. the
        # backlog, with size estimates for open ideas — board / inbox / roadmap.
        '<p class="subtitle"><a class="capture-link" href="roadmap.html">'
        "Module roadmap &rarr;</a> "
        '<a class="capture-link" href="ideas.html">Idea inbox &rarr;</a></p>\n'
        f'<div class="roadmap">\n{roadmap}\n</div>\n'
        f'<div class="ready-strip"><strong>Ready to pull</strong> ({len(summary["next_ready"])}; '
        "<code>todo</code> with every <code>depends_on</code> done &mdash; derived, never stored): "
        f"{ready_strip}</div>\n"
        '<div class="filters">\n'
        '  <label>Module<select id="f-module"><option value="">All</option>\n'
        f"{module_opts}\n</select></label>\n"
        '  <label>Phase<select id="f-phase"><option value="">All</option>\n'
        f"{phase_opts}\n</select></label>\n"
        '  <label>Epic<select id="f-epic"><option value="">All</option>\n'
        f"{epic_opts}\n</select></label>\n"
        '  <label>Type<select id="f-type"><option value="">All</option>\n'
        f"{type_opts}\n</select></label>\n"
        '  <label>Search<input type="search" id="f-search" placeholder="id or title"></label>\n'
        '  <button type="button" id="f-clear">Clear filters</button>\n'
        "</div>\n"
        f'<div class="board">\n{columns}\n</div>\n'
        '<div class="capture">\n'
        "  <h2>Quick capture</h2>\n"
        '  <div class="capture-row">\n'
        '    <input type="text" id="capture-text" '
        'placeholder="a thought, idea, bug, or question">\n'
        f'    <select id="capture-tag">\n{tag_opts}\n</select>\n'
        '    <button type="button" id="capture-copy">Copy line</button>\n'
        "  </div>\n"
        '  <p class="capture-hint">Copies <code>- [tag] text</code> to your clipboard — '
        "paste into docs/restructure/IDEAS.md — the repo is the system of record. "
        # The inbox's own rendered surface (2026-08-05): capture had a button, REVIEW
        # had none, so the one artifact in the inbox->backlog->board chain that could
        # only be read as raw markdown was the one holding unreviewed work.
        '<a class="capture-link" href="ideas.html">Review the idea inbox &rarr;</a></p>\n'
        '  <p class="capture-status" id="capture-status"></p>\n'
        "</div>\n"
        f"<script>\n{js}\n</script>\n</body></html>\n"
    )


def write_board(
    backlog_path: str | Path = DEFAULT_BACKLOG_PATH,
    out_path: str | Path = DEFAULT_BOARD_PATH,
) -> Path:
    """Load ``backlog_path``, render it, and write the HTML to ``out_path``. Returns the path."""
    backlog = load_backlog(backlog_path)
    html_doc = render_board(backlog)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_doc, encoding="utf-8", newline="\n")
    return out_path
