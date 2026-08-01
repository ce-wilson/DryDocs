"""Enforce the backlog schema (drydocs.backlog.v2) — no Neo4j required.

docs/restructure/backlog.yaml is the machine-readable SOURCE OF TRUTH for work
items (CLAUDE.md §0); the HTML board and 02-backlog.md are renders of it. This
guard keeps the database honest so those renders can trust it:

- every item carries the v2 fields (title/type/module/phase + the v1 core);
- ids are unique, dependencies resolve and are acyclic;
- module values come from the `modules:` registry, phases from `plan.phases`;
- the `summary:` roll-up and `next_ready:` list are COMPUTED views — they must
  match the items exactly, so they can never silently drift again.
"""

from __future__ import annotations

from pathlib import Path

import pytest

try:
    import yaml

    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKLOG = REPO_ROOT / "docs" / "restructure" / "backlog.yaml"
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"

STATUSES = {"todo", "in_progress", "blocked", "done"}
TYPES = {"requirement", "task", "chore", "bug"}
PRIORITIES = {"p0", "p1", "p2", "p3"}
MODELS = {
    "haiku",
    "sonnet",
    "opus",
    "fable",
}  # fable = Mythos-class top tier (2026-07-10); opus stays valid for existing items
REQUIRED_FIELDS = (
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

pytestmark = pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML not installed")


def _load() -> dict:
    assert BACKLOG.exists(), f"Missing backlog: {BACKLOG}"
    return yaml.safe_load(BACKLOG.read_text(encoding="utf-8"))


def _agents() -> set[str]:
    """Valid `agent:` values = the sub-agent roster + the main session."""
    roster = {p.stem for p in AGENTS_DIR.glob("*.md")} if AGENTS_DIR.exists() else set()
    return roster | {"main"}


def test_schema_is_v2() -> None:
    doc = _load()
    assert (
        doc.get("schema") == "drydocs.backlog.v2"
    ), f"backlog schema drifted: {doc.get('schema')!r}"
    assert doc.get("updated"), "backlog.yaml missing `updated:` date"


def test_plan_phases_shape() -> None:
    doc = _load()
    phases = doc.get("plan", {}).get("phases", [])
    assert phases, "plan.phases is empty — the roadmap strip has nothing to render"

    failures: list[str] = []
    seen: set[int] = set()
    for ph in phases:
        pid = ph.get("id")
        if not isinstance(pid, int):
            failures.append(f"phase id {pid!r} is not an int")
            continue
        if pid in seen:
            failures.append(f"duplicate phase id {pid}")
        seen.add(pid)
        if not ph.get("title"):
            failures.append(f"phase {pid} missing title")
        if not ph.get("goal"):
            failures.append(f"phase {pid} missing goal")
        if ph.get("status") not in STATUSES:
            failures.append(f"phase {pid} status {ph.get('status')!r} not in {sorted(STATUSES)}")

    assert not failures, f"{len(failures)} phase error(s):\n" + "\n".join(failures)


def test_modules_registry() -> None:
    doc = _load()
    modules = doc.get("modules", [])
    assert modules, "modules: registry is empty"
    assert all(isinstance(m, str) and m for m in modules), "modules must be non-empty strings"
    assert len(modules) == len(set(modules)), "duplicate module names in registry"


def test_items_have_valid_v2_fields() -> None:
    doc = _load()
    items = doc.get("items", [])
    assert items, "items: is empty"

    modules = set(doc.get("modules", []))
    phase_ids = {ph["id"] for ph in doc.get("plan", {}).get("phases", [])}
    agents = _agents()

    failures: list[str] = []
    seen_ids: set[str] = set()
    for item in items:
        iid = item.get("id", "<no-id>")
        if iid in seen_ids:
            failures.append(f"[{iid}] duplicate id")
        seen_ids.add(iid)

        for field in REQUIRED_FIELDS:
            if field not in item or item[field] in (None, ""):
                failures.append(f"[{iid}] missing required field '{field}'")

        if item.get("status") not in STATUSES:
            failures.append(f"[{iid}] status {item.get('status')!r} not in {sorted(STATUSES)}")
        if item.get("type") not in TYPES:
            failures.append(f"[{iid}] type {item.get('type')!r} not in {sorted(TYPES)}")
        if item.get("priority") not in PRIORITIES:
            failures.append(
                f"[{iid}] priority {item.get('priority')!r} not in {sorted(PRIORITIES)}"
            )
        if item.get("model") not in MODELS:
            failures.append(f"[{iid}] model {item.get('model')!r} not in {sorted(MODELS)}")
        if item.get("agent") not in agents:
            failures.append(f"[{iid}] agent {item.get('agent')!r} not in {sorted(agents)}")
        if item.get("module") not in modules:
            failures.append(f"[{iid}] module {item.get('module')!r} not in modules: registry")
        if item.get("phase") not in phase_ids:
            failures.append(f"[{iid}] phase {item.get('phase')!r} not in plan.phases ids")
        if not isinstance(item.get("depends_on"), list):
            failures.append(f"[{iid}] depends_on must be a list ([] = startable now)")

    assert not failures, f"{len(failures)} item error(s):\n" + "\n".join(failures)


def test_dependencies_resolve_and_are_acyclic() -> None:
    doc = _load()
    items = {item["id"]: item for item in doc.get("items", [])}

    failures: list[str] = []
    for iid, item in items.items():
        for dep in item.get("depends_on", []):
            if dep == iid:
                failures.append(f"[{iid}] depends on itself")
            elif dep not in items:
                failures.append(f"[{iid}] depends_on unknown id '{dep}'")
    assert not failures, f"{len(failures)} dependency error(s):\n" + "\n".join(failures)

    # cycle detection (DFS, three-color: unvisited / on the current path / done)
    white, gray, black = 0, 1, 2
    color = dict.fromkeys(items, white)

    def visit(node: str, path: list[str]) -> None:
        color[node] = gray
        for dep in items[node].get("depends_on", []):
            if color[dep] == gray:
                pytest.fail(f"dependency cycle: {' -> '.join([*path, node, dep])}")
            if color[dep] == white:
                visit(dep, [*path, node])
        color[node] = black

    for iid in items:
        if color[iid] == white:
            visit(iid, [])


def test_summary_rollup_matches_items() -> None:
    """The summary: block is a computed view — it may never drift from the items."""
    doc = _load()
    items = doc.get("items", [])
    summary = doc.get("summary", {})

    computed = {status: 0 for status in STATUSES}
    for item in items:
        computed[item["status"]] += 1

    failures = [
        f"summary.{status}={summary.get(status)} but items say {computed[status]}"
        for status in sorted(STATUSES)
        if summary.get(status) != computed[status]
    ]
    assert not failures, "summary roll-up drifted:\n" + "\n".join(failures)


def test_next_ready_is_computed() -> None:
    """next_ready = exactly the todo items whose every depends_on is done."""
    doc = _load()
    items = {item["id"]: item for item in doc.get("items", [])}

    expected = {
        iid
        for iid, item in items.items()
        if item["status"] == "todo"
        and all(items[dep]["status"] == "done" for dep in item.get("depends_on", []))
    }
    actual = set(doc.get("summary", {}).get("next_ready", []))
    assert actual == expected, (
        f"next_ready drifted — listed-but-not-ready: {sorted(actual - expected)}; "
        f"ready-but-missing: {sorted(expected - actual)}"
    )
