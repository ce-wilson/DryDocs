"""Standalone backlog validator — the groom-backlog skill's fallback gate.

Runs the same checks as tests/unit/test_backlog.py for environments where
poetry/pytest are not installed. If the two ever disagree, test_backlog.py wins.

Usage (from the repo root):
    python .claude/skills/groom-backlog/validate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKLOG = REPO_ROOT / "docs" / "restructure" / "backlog"  # the sharded tree (ADR 0013)
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"

STATUSES = {"todo", "in_progress", "blocked", "done"}
TYPES = {"requirement", "task", "chore", "bug"}
PRIORITIES = {"p0", "p1", "p2", "p3"}
MODELS = {"haiku", "sonnet", "opus", "fable"}  # keep in sync with test_backlog.py (it wins)
REQUIRED = (
    "id",
    "title",
    "type",
    "module",
    "phase",
    "epic",
    "agent",
    "model",
    "priority",
    "status",
    "depends_on",
    "acceptance",
)


def main() -> int:
    fails: list[str] = []
    sys.path.insert(0, str(REPO_ROOT))
    from drydocs_core.backlog_store import derive_summary, load_backlog_document

    doc = load_backlog_document(BACKLOG)

    if doc.get("schema") != "drydocs.backlog.v3":
        fails.append(f"schema drifted: {doc.get('schema')!r}")

    phases = doc.get("plan", {}).get("phases", [])
    pids: set[int] = set()
    for ph in phases:
        pid = ph.get("id")
        if not isinstance(pid, int) or pid in pids:
            fails.append(f"phase id problem: {pid!r}")
        pids.add(pid)
        for f in ("title", "goal"):
            if not ph.get(f):
                fails.append(f"phase {pid} missing {f}")
        if ph.get("status") not in STATUSES:
            fails.append(f"phase {pid} bad status {ph.get('status')!r}")

    modules = doc.get("modules", [])
    if not modules or len(modules) != len(set(modules)):
        fails.append("modules registry empty or has duplicates")

    agents = {p.stem for p in AGENTS_DIR.glob("*.md")} | {"main"}

    items = doc.get("items", [])
    by_id: dict[str, dict] = {}
    for it in items:
        iid = it.get("id", "<no-id>")
        if iid in by_id:
            fails.append(f"[{iid}] duplicate id")
        by_id[iid] = it
        for f in REQUIRED:
            if f not in it or it[f] in (None, ""):
                fails.append(f"[{iid}] missing required field '{f}'")
        for ok, msg in (
            (it.get("status") in STATUSES, f"status {it.get('status')!r}"),
            (it.get("type") in TYPES, f"type {it.get('type')!r}"),
            (it.get("priority") in PRIORITIES, f"priority {it.get('priority')!r}"),
            (it.get("model") in MODELS, f"model {it.get('model')!r}"),
            (it.get("agent") in agents, f"agent {it.get('agent')!r}"),
            (it.get("module") in set(modules), f"module {it.get('module')!r}"),
            (it.get("phase") in pids, f"phase {it.get('phase')!r}"),
            (isinstance(it.get("depends_on"), list), "depends_on (must be a list)"),
        ):
            if not ok:
                fails.append(f"[{iid}] bad {msg}")

    for iid, it in by_id.items():
        for dep in it.get("depends_on", []):
            if dep == iid or dep not in by_id:
                fails.append(f"[{iid}] bad dep {dep!r}")

    # cycle detection (DFS, three-color)
    white, gray, black = 0, 1, 2
    color = dict.fromkeys(by_id, white)

    def visit(node: str, path: list[str]) -> None:
        color[node] = gray
        for dep in by_id[node].get("depends_on", []):
            if color.get(dep) == gray:
                fails.append(f"dependency cycle: {' -> '.join([*path, node, dep])}")
            elif color.get(dep) == white:
                visit(dep, [*path, node])
        color[node] = black

    for iid in by_id:
        if color[iid] == white:
            visit(iid, [])

    # ADR 0013 Clause 3: nothing stores a roll-up; the derived one is printed so the
    # groomer can read next_ready without opening the board.
    derived = derive_summary(doc)
    for path in sorted(BACKLOG.rglob("*.yaml")):
        d = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for key in ("summary", "next_ready", "updated"):
            if isinstance(d, dict) and key in d:
                fails.append(f"{path.name}: stored `{key}:` — roll-ups are derived, never stored")
    for path in (BACKLOG / "items").glob("*.yaml"):
        d = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if d.get("id") != path.stem:
            fails.append(f"{path.name}: id {d.get('id')!r} != filename")
    print(
        "derived: "
        + " ".join(f"{k}={derived[k]}" for k in ("todo", "in_progress", "blocked", "done"))
        + f" next_ready={len(derived['next_ready'])}"
    )

    print(f"items={len(items)} phases={len(phases)} modules={len(modules)}")
    if fails:
        print(f"FAIL ({len(fails)}):")
        for f in fails:
            print(" -", f)
        return 1
    print("ALL CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
