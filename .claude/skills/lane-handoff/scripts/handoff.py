"""Generate, suggest and check a lane handoff — the per-burst queue one machine hands another.

Usage (from the repo root):
    python .claude/skills/lane-handoff/scripts/handoff.py --suggest
    python .claude/skills/lane-handoff/scripts/handoff.py --lane B --machine laptop \
        --queue LOAD12,CORE3 [--other-queue CFG1,CFG2] [--from "desktop Lane A session"] \
        [--out docs/lane-b-handoff.md]
    python .claude/skills/lane-handoff/scripts/handoff.py --check docs/lane-b-handoff.md

WHY A SCRIPT AND NOT A SENTENCE. The retired 2026-08-27 handoff was written by
hand and did three things a sentence cannot do reliably: it listed items that
were actually ready, it kept venue-bound items on the machine that has the
data, and it fenced the surfaces the other lane owns. The same repo learned
with the id allocator (I6) that a rule living only in prose "cannot look
anywhere". This script looks: readiness comes from
``drydocs_core.backlog_store.derive_summary`` — the board's own rule — so the
queue and the Ready-to-pull strip can never disagree; venue and surface checks
read each item's ``inputs``; the standing rules are CITED from CLAUDE.md, never
retyped, because the retired file's retyped list had already drifted from §0
by the time it was deleted.

ONE VOCABULARY FOR SURFACES. CLAUDE.md §0's "one pen per surface" rule names
the pens — ``backlog``, ``port``, ``adr``, ``code:<module>``. :data:`PENS` is
keyed by those names (plus two this skill adds, ``gates`` and ``snapshot``, and
says so), and BOTH the surfaces table and the pens line the receiving session
declares in its first commit are generated from that one structure. A second
list of the same surfaces is the drift this skill exists to prevent (review of
fe120bf9, point 2).

WHAT IT REFUSES, AND WHAT IT ONLY FLAGS. It refuses an id that does not exist,
an item that is not ``todo``, and an item whose dependencies are not all
``done`` — those are facts the board holds. It only FLAGS venue-bound inputs
and, for a Lane B queue, inputs under a Lane A pen, because which machine
holds a data root and which session owns a surface this week are the author's
facts, not the tree's; the flags print, and land in the file, so the decision
is visible. The other lane's queue gets the same check as NOTES.

Reads the backlog; writes ONE markdown file; touches nothing else. It does
not claim items (the pull rule does that, per item, at pull time), does not
render the board, and does not mint ids.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
# A Windows console defaults to cp1252 and turns every em dash in the report into
# a replacement glyph; the file on disk is written UTF-8 regardless.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from drydocs_core import backlog_store  # noqa: E402

BACKLOG = REPO / "docs" / "restructure" / "backlog"

#: THE pens, keyed by the names CLAUDE.md §0 uses. Each pen maps to the path
#: prefixes it covers, with the reason a reader can check. Lane A holds every pen
#: listed here by default; Lane B holds ``code:<module>`` per queued item.
PENS: dict[str, tuple[tuple[str, str], ...]] = {
    "backlog": (
        ("docs/restructure/backlog/", "items, epics, plan — the board's sources"),
        ("docs/restructure/IDEAS.md", "the idea inbox — one file until R6 shards it"),
        ("docs/restructure/ideas/", "the sharded inbox, once R6 lands (§0 names it already)"),
        ("docs/plan/", "the plan renders: board, roadmap, ideas, load-map"),
    ),
    "port": (
        ("docs/port/", "port prompt, relays, dossiers"),
        ("PORT-MANIFEST.yaml", "port dispositions"),
        ("docs/company-prompts/", "the company-facing prompts"),
        (".claude/skills/reconcile-port/", "the port skill"),
    ),
    "adr": (("docs/decisions/", "ADRs and their index"),),
    "gates": (
        ("config/gate-prompts/", "gate prompts — SME sessions run from Lane A"),
        ("config/gate-log.md", "the signed gate record"),
        ("config/crosswalks/", "orchestrator crosswalks — gate-bound config"),
    ),
    "snapshot": (("knowledge/depgraph-snapshots/", "the session snapshot — one writer per burst"),),
}
#: The pens §0 names today. ``gates`` and ``snapshot`` are this skill's additions —
#: the generated file says so, and the §0 cross-link is where they graduate.
SECTION_0_PENS: tuple[str, ...] = ("backlog", "port", "adr")
LANE_A_PENS: tuple[str, ...] = tuple(PENS)

#: Input paths that say "this item needs data that lives on one machine".
VENUE_MARKERS: tuple[str, ...] = ("internal-local/", "DRYDOCS_DATA_ROOT", "data/DryDocs")

LANES = ("A", "B")


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def norm_path(p: object) -> str:
    """``./config/x``, ``config\\x`` and ``config/x`` are one path (review point 3)."""
    return PurePosixPath(str(p).replace("\\", "/")).as_posix()


def load() -> tuple[dict, dict[str, dict], list[str]]:
    doc = backlog_store.load_backlog_document(BACKLOG)
    items = {str(i["id"]): i for i in doc.get("items") or []}
    ready = backlog_store.derive_summary(doc)["next_ready"]
    return doc, items, ready


def venue_flags(item: dict) -> list[str]:
    """Machine-local inputs. The notes check is a substring heuristic — a note that says
    "not machine-local" flags too, by design: a false flag costs a reader one glance,
    a missed one costs the other machine a session."""
    flags = []
    for p in item.get("inputs") or []:
        if any(m in norm_path(p) for m in VENUE_MARKERS):
            flags.append(f"input `{p}` is machine-local")
    notes = str(item.get("notes") or "")
    if re.search(r"machine[- ]local", notes, re.I):
        flags.append("notes say machine-local")
    return flags


def pen_of(path: object) -> tuple[str, str] | None:
    """The (pen, why) that covers a path, or None — one structure, one answer."""
    p = norm_path(path)
    for pen, surfaces in PENS.items():
        for prefix, what in surfaces:
            if p.startswith(norm_path(prefix)):
                return pen, what
    return None


def surface_flags(item: dict) -> list[str]:
    flags = []
    for p in item.get("inputs") or []:
        hit = pen_of(p)
        if hit:
            pen, what = hit
            flags.append(f"input `{p}` — pen `{pen}` ({what})")
    return flags


def gate_flags(item: dict) -> list[str]:
    gates = item.get("gates") or []
    return [f"gate-bound: {', '.join(gates)} (an SME session, not a build)"] if gates else []


def check_queue(
    ids: list[str], items: dict[str, dict], ready: list[str], lane: str = "B"
) -> tuple[list[dict], list[str]]:
    """Validate an ordered queue: refusals stop the run; flags ride into the file.

    Surface flags are a Lane B concern: Lane A OWNS those pens, so a Lane A queue
    of gate sessions is the normal case, not a warning (the first eval run flagged
    G116-G119 for touching config/gate-prompts on a Lane A handoff — wrong).
    """
    rows, refusals = [], []
    seen: set[str] = set()
    for raw in ids:
        iid = raw.strip()
        if not iid:
            continue
        if iid in seen:
            refusals.append(f"{iid}: listed twice")
            continue
        seen.add(iid)
        item = items.get(iid)
        if item is None:
            refusals.append(f"{iid}: no such item in {BACKLOG / 'items'}")
            continue
        status = str(item.get("status"))
        if status != "todo":
            refusals.append(f"{iid}: status is {status!r}, a queue lists todo items only")
            continue
        if iid not in ready:
            missing = [
                d
                for d in item.get("depends_on") or []
                if items.get(str(d), {}).get("status") != "done"
            ]
            refusals.append(f"{iid}: not ready — depends on {missing} (not all done)")
            continue
        rows.append(
            {
                "id": iid,
                "title": " ".join(str(item.get("title", "")).split()),
                "type": item.get("type"),
                "priority": item.get("priority"),
                "module": str(item.get("module")),
                "model": item.get("model"),
                "deps": [str(d) for d in item.get("depends_on") or []],
                "venue": venue_flags(item),
                "surfaces": surface_flags(item) if lane == "B" else [],
                "gates": gate_flags(item),
            }
        )
    return rows, refusals


def other_queue_notes(
    other: list[str], items: dict[str, dict], ready: list[str], other_lane: str
) -> list[str]:
    """The other lane's queue through the same check, as NOTES rather than refusals:
    this file cannot fix the other lane's plan, but the sender should not learn on
    the other machine that MM4 was never ready or that MM5's input lives elsewhere."""
    if not other:
        return []
    rows, refusals = check_queue(other, items, ready, other_lane)
    notes = list(refusals)
    for r in rows:
        for f in r["venue"] + r["surfaces"] + r["gates"]:
            notes.append(f"{r['id']}: {f}")
    return notes


def lane_pens(lane: str, rows: list[dict]) -> list[str]:
    """What this lane declares in its first commit: Lane A the surface pens, Lane B one
    ``code:<module>`` per module in its queue."""
    if lane == "A":
        return list(LANE_A_PENS)
    seen: dict[str, None] = {}
    for r in rows:
        seen.setdefault(f"code:{r['module']}", None)
    return list(seen)


def render(
    *,
    lane: str,
    machine: str,
    sender: str,
    rows: list[dict],
    other_queue: list[str],
    other_notes: list[str] | None = None,
) -> str:
    other = "B" if lane == "A" else "A"
    today = dt.date.today().isoformat()
    sha = _git("rev-parse", "--short", "HEAD") or "unknown"
    branch = _git("branch", "--show-current") or "unknown"
    queue_ids = [r["id"] for r in rows]
    pens = lane_pens(lane, rows)
    pens_other = list(LANE_A_PENS) if other == "A" else ["code:<module> per queued item"]

    out: list[str] = []
    out += [
        "---",
        "handoff: drydocs.lane-handoff.v1",
        f"lane: {lane}",
        f"machine: {machine}",
        f"generated: {today}",
        f"generated_at: {sha} ({branch})",
        f"queue: [{', '.join(queue_ids)}]",
        f"pens: [{', '.join(pens)}]",
        "---",
        "",
        f"# Lane {lane} handoff — {machine}, {today}",
        "",
        f"**From:** {sender}. **To:** the Lane {lane} session on the {machine}.",
        "**Lifecycle:** a working handoff, not a durable record — the item files are. When",
        "the queue below is empty, delete this file in the closing commit",
        "(`python .claude/skills/lane-handoff/scripts/handoff.py --check <this file>` says when).",
        "",
        "## Pens — declare them in your first commit (CLAUDE.md §0, one pen per surface)",
        "",
        "Collisions come from two sessions writing the same surface, not from two sessions",
        "existing. Your first commit message (or your `wip/` branch name) names what you hold:",
        "",
        "```text",
        f"pen: {' · '.join(pens)}",
        "```",
        "",
        f"Lane {other} holds: `{' · '.join(pens_other)}`. Anything not declared by either lane",
        "is off-limits to both until one asks. The item-file claim is the pen for ONE item; this",
        "is the pen for a SURFACE.",
        "",
        "## Start ritual — CLAUDE.md §0, cited, not restated",
        "",
        "1. `git pull` (fast-forward), read CLAUDE.md, open the board's Ready-to-pull strip.",
        "2. Claim ONE item at a time: push `status: in_progress` in that item file BEFORE work,",
        "   no render (Y5). `git branch --show-current` before every commit (the branch",
        "   guardrail). In-flight work pushes to `wip/<id>-" + machine + "` at the first",
        "   substantive edit (J31).",
        "3. Ids come from the allocator, never from your tree (I6) — but a lane does not mint:",
        "   ideas and groom requests go back to the sender (see the pens above).",
        "4. Per-machine facts are yours to verify: `DRYDOCS_DATA_ROOT`, `DRYDOCS_LOGDIR`, the",
        "   `.env`, and whether Neo4j is reachable here. Venue-stamp any live claim (J18).",
        "",
        f"## Your queue, in order ({len(rows)} item{'s' if len(rows) != 1 else ''}) — claim one at a time",
        "",
        "Every item below is `todo` with every dependency `done` at the generating commit — the",
        "same rule the board's Ready strip uses (`derive_summary`). Re-check on pull: the other",
        "lane may have moved something. The split is by MODULE (the id series is the module",
        "since PLAN1), so two lanes minting in disjoint series cannot collide on a number.",
        "",
        "| # | Id | Title | Type / prio | Module | Model | Notes from the check |",
        "|---|---|---|---|---|---|---|",
    ]
    for n, r in enumerate(rows, 1):
        notes = r["venue"] + r["surfaces"] + r["gates"]
        note = "; ".join(notes) if notes else "clean"
        deps = f" (after {', '.join(r['deps'])})" if r["deps"] else ""
        out.append(
            f"| {n} | **{r['id']}** | {r['title']}{deps} | {r['type']} / {r['priority']} | "
            f"`{r['module']}` | {r['model']} | {note} |"
        )
    flagged = [r for r in rows if r["venue"] or r["surfaces"]]
    if flagged:
        out += [
            "",
            "**Flags to rule before claiming** (the script flags; the author decides):",
            "",
        ]
        for r in flagged:
            for f in r["venue"]:
                out.append(
                    f"- {r['id']}: {f} — does the {machine} have it? If not, this item belongs"
                    " to the other lane or waits for the file to be copied over."
                )
            for f in r["surfaces"]:
                out.append(f"- {r['id']}: {f} — Lane A's pen; coordinate before editing.")
    out += [
        "",
        "## Surfaces — who holds which pen this burst",
        "",
        "The partition is by SURFACE, not only by item, because the collisions a burst",
        "produces land on shared files rather than on claimed items: the inbox top, the",
        "rendered pages, the snapshot. A lane touches the other lane's pens only by handing",
        "the change back through the sender.",
        "",
        "| Pen | Surface | Why |",
        "|---|---|---|",
    ]
    for pen, surfaces in PENS.items():
        tag = "" if pen in SECTION_0_PENS else " (this skill's addition to §0)"
        for prefix, what in surfaces:
            out.append(f"| `{pen}`{tag} | `{prefix}` | Lane A — {what} |")
    if other_queue:
        out.append(
            f"| Lane {other}'s queue | the items {', '.join(other_queue)} and their inputs | "
            "do not claim or edit |"
        )
    out += [
        "| `code:<module>` | everything an item in YOUR queue names in `inputs` | this lane, claimed per item |",
        "| — | `docs/plan/*.html`, `web/src/generated/**`, `docs/design/*.html` | derived renders — "
        "Lane A regenerates once at close; nobody merges them by hand (J43) |",
        "",
    ]
    if other_notes:
        out += [
            f"**About Lane {other}'s queue, from the same check** (for the sender to rule — this lane",
            "does nothing with these):",
            "",
        ]
        out += [f"- {n}" for n in other_notes]
        out.append("")
    if lane == "B":
        out += [
            "**Lane B claims status-only and never renders.** A claim is one item file, pushed;",
            "Y5 tolerates it un-rendered, and Lane A renders once at close. **Lane B does not",
            "append to `IDEAS.md` while the inbox is one file** (until R6 shards it): even an",
            "allocator-minted id conflicts at the inbox top when both machines insert there in",
            "one burst (observed 2026-09-02, twice). Anything worth capturing goes back to the",
            "sender in your close report.",
            "",
        ]
    out += [
        "## Rules that have bitten — the durable ones live in CLAUDE.md",
        "",
        "- Full suite before every push (`poetry run pytest -q`), plus `ruff check .` and a bare",
        "  `ruff format --check .` — CI blocks on both and ran red for a week once while subsets",
        "  passed locally (§0, Idea-111).",
        "- A guard reads code, not prose (J66); never parse a render (J37); a review names its",
        "  tree (J63). Read them in §6 — this file will not keep up with them.",
        "- Item notes: no backslash escapes through a shell heredoc; write the note with the Write",
        "  tool and run `tests/unit/test_backlog.py` before committing it.",
        "- LANES ARE PRODUCER-SIDE ONLY. The company apply is a THIRD session in a different repo,",
        "  never a lane: it ports methodically, one pen, accuracy over speed — this file never",
        "  exists there. The `port` pen is producer-side and stays with Lane A; never run the port",
        "  from the machine that holds it here.",
        "",
        "## Close — in this order",
        "",
    ]
    if lane == "B":
        out += [
            "1. Every claimed item `done` and pushed; unfinished work on `wip/<id>-"
            + machine
            + "`,",
            "   pushed. No render, no snapshot — those are Lane A's pens.",
            "2. `python .claude/skills/lane-handoff/scripts/handoff.py --check <this file>` — when it",
            "   reports the queue empty, delete this file in the same closing commit.",
            "3. Report back: what closed, what is on `wip/`, what you noticed (that is how ideas",
            "   reach the inbox from Lane B). Lane A merges your `wip/` branches `--no-ff`, deletes",
            "   them, renders once, snapshots once.",
            "",
        ]
    else:
        out += [
            "1. Merge Lane B's `wip/<id>-*` branches `--no-ff` and delete them; then every item",
            "   `done` and pushed.",
            "2. Regenerate the renders ONCE (`render_board.py`, the design docs); `gh run list` at",
            "   YOUR sha; then the depgraph snapshot — the `snapshot` pen is yours.",
            "3. `python .claude/skills/lane-handoff/scripts/handoff.py --check <this file>` — when it",
            "   reports the queue empty, delete this file in the same closing commit.",
            "",
        ]
    return "\n".join(out)


def cmd_suggest(items: dict[str, dict], ready: list[str]) -> int:
    by_module: dict[str, list[dict]] = {}
    for iid in ready:
        by_module.setdefault(str(items[iid].get("module")), []).append(items[iid])
    print(
        f"Ready to pull: {len(ready)} items, grouped by module. Marks: V = machine-local input, "
        "S = under a Lane A pen (a Lane B concern), G = gate-bound (an SME session)\n"
    )
    for module in sorted(by_module):
        print(f"[{module}]")
        for it in by_module[module]:
            v, s, g = venue_flags(it), surface_flags(it), gate_flags(it)
            marks = ("V" if v else "-") + ("S" if s else "-") + ("G" if g else "-")
            title = " ".join(str(it.get("title", "")).split())
            print(f"  {marks} {it['id']:7} {it.get('priority')}  {title[:88]}")
            for f in v + s + g:
                print(f"        - {f}")
        print()
    return 0


def cmd_check(path: Path, items: dict[str, dict]) -> int:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^queue: \[(.*?)\]$", text, re.M)
    if not m:
        print(f"{path}: no `queue:` line in the front matter — not a generated handoff")
        return 2
    ids = [x.strip() for x in m.group(1).split(",") if x.strip()]
    open_ids, missing_ids = [], []
    for iid in ids:
        item = items.get(iid)
        if item is None:
            print(f"  {iid:7} MISSING — no such item now (re-minted or removed since the handoff)")
            missing_ids.append(iid)
            continue
        status = str(item.get("status", ""))
        print(f"  {iid:7} {status}")
        if status != "done":
            open_ids.append(iid)
    if missing_ids:
        print(
            f"\nMISSING: {', '.join(missing_ids)} — not open, not done: the queue predates a change "
            "to the backlog. Keep the file and ask the sender what replaced them."
        )
    if open_ids:
        print(f"\nQueue not empty: {', '.join(open_ids)} still open. Keep the file.")
    if open_ids or missing_ids:
        return 1
    print(f"\nQueue empty ({len(ids)} done). Delete {path} in the closing commit.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--suggest", action="store_true", help="list the Ready strip by module with marks"
    )
    ap.add_argument("--check", type=Path, help="report an existing handoff's queue status")
    ap.add_argument("--lane", choices=LANES, help="the RECEIVING lane")
    ap.add_argument("--machine", help="the receiving machine, e.g. laptop / desktop")
    ap.add_argument("--queue", help="ordered, comma-separated item ids for the receiving lane")
    ap.add_argument(
        "--other-queue", default="", help="ids the OTHER lane holds (fenced in the file)"
    )
    ap.add_argument("--from", dest="sender", default="", help="who is handing off")
    ap.add_argument("--out", type=Path, help="output path (default docs/lane-<x>-handoff.md)")
    ap.add_argument(
        "--allow-flagged",
        action="store_true",
        help="write even when items carry venue/surface flags",
    )
    args = ap.parse_args(argv)

    _, items, ready = load()
    if args.suggest:
        return cmd_suggest(items, ready)
    if args.check:
        return cmd_check(args.check, items)
    if not (args.lane and args.machine and args.queue):
        ap.error("generate needs --lane, --machine and --queue (or use --suggest / --check)")

    rows, refusals = check_queue(args.queue.split(","), items, ready, args.lane)
    if refusals:
        print("REFUSED — fix the queue:")
        for r in refusals:
            print(f"  - {r}")
        return 2
    flagged = [r["id"] for r in rows if r["venue"] or r["surfaces"]]
    if flagged and not args.allow_flagged:
        print(f"FLAGGED — {', '.join(flagged)} carry venue or surface flags (shown below).")
        for r in rows:
            for f in r["venue"] + r["surfaces"]:
                print(f"  - {r['id']}: {f}")
        print(
            "Rule on them, then re-run with --allow-flagged to write the file with the flags recorded."
        )
        return 3

    other = [x.strip() for x in args.other_queue.split(",") if x.strip()]
    other_lane = "B" if args.lane == "A" else "A"
    notes = other_queue_notes(other, items, ready, other_lane)
    for n in notes:
        print(f"  note (Lane {other_lane} queue): {n}")
    sender = args.sender or f"the Lane {other_lane} session"
    out = args.out or (REPO / "docs" / f"lane-{args.lane.lower()}-handoff.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        render(
            lane=args.lane,
            machine=args.machine,
            sender=sender,
            rows=rows,
            other_queue=other,
            other_notes=notes,
        ),
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {out} — {len(rows)} items: {', '.join(r['id'] for r in rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
