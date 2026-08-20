"""Enforce the backlog schema (drydocs.backlog.v3, the sharded tree — ADR 0013) — no Neo4j.

docs/restructure/backlog/ is the machine-readable SOURCE OF TRUTH for work items
(CLAUDE.md §0): one item per file under items/<id>.yaml, epics under epics/,
plan.yaml + modules.yaml. The board is a render of it. This guard keeps it honest:

- every item carries the v2/v3 fields (title/type/module/phase + the v1 core);
- the path IS the identity: items/<id>.yaml declares that same `id`; epics likewise;
- ids are unique, dependencies resolve and are acyclic; every `epic:` has a file;
- module values come from modules.yaml, phases from plan.yaml;
- NO ROLL-UP IS STORED (Clause 3): `summary:` / `next_ready:` / `updated:` exist
  nowhere in the tree — the board derives them. The old "recompute from items"
  guards inverted into this one: a stored roll-up is the defect now;
- no mapping in any file carries a duplicate key (PyYAML is last-key-wins; the
  store's loader refuses, and this test proves it on the live tree);
- the retired monolith stays a TOMBSTONE — it must never grow an `items:` key again.
"""

from __future__ import annotations

from pathlib import Path

import pytest

try:
    import yaml

    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

from drydocs_core import backlog_store

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKLOG = REPO_ROOT / "docs" / "restructure" / "backlog"
TOMBSTONE = REPO_ROOT / "docs" / "restructure" / "backlog.yaml"
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
    assert BACKLOG.is_dir(), f"Missing backlog tree: {BACKLOG}"
    return backlog_store.load_backlog_document(BACKLOG)


def _find_duplicate_keys(text: str) -> list[str]:
    """Every duplicate mapping key in the document, with both line numbers."""
    dupes: list[str] = []

    class _Loader(yaml.SafeLoader):
        def construct_mapping(self, node, deep=False):
            seen: dict = {}
            for key_node, _value_node in node.value:
                key = self.construct_object(key_node, deep=True)
                line = key_node.start_mark.line + 1
                if key in seen:
                    dupes.append(f"duplicate key {key!r}: line {seen[key]} and line {line}")
                else:
                    seen[key] = line
            return super().construct_mapping(node, deep=deep)

    yaml.load(text, Loader=_Loader)
    return dupes


def _agents() -> set[str]:
    """Valid `agent:` values = the sub-agent roster + the main session."""
    roster = {p.stem for p in AGENTS_DIR.glob("*.md")} if AGENTS_DIR.exists() else set()
    return roster | {"main"}


def test_schema_is_v3() -> None:
    doc = _load()
    assert (
        doc.get("schema") == "drydocs.backlog.v3"
    ), f"backlog schema drifted: {doc.get('schema')!r}"


def test_path_is_the_identity() -> None:
    """items/<id>.yaml must declare that id; epics/<epic>.yaml likewise. The store raises
    on mismatch; this asserts the live tree passes and that every item's epic has a file."""
    doc = _load()
    epics = {e["id"] for e in doc["epics"]}
    used = {i["epic"] for i in doc["items"]}
    assert used <= epics, f"items name epics with no epics/<epic>.yaml: {sorted(used - epics)}"
    assert epics <= used, f"epic files with no items: {sorted(epics - used)}"
    for path in (BACKLOG / "items").glob("*.yaml"):
        assert yaml.safe_load(path.read_text(encoding="utf-8"))["id"] == path.stem, path


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


# ---- allocator bands (2026-08-18) -------------------------------------------
# Same partition as the idea inbox, same reason: three allocators
# (producer-desktop, producer-laptop, company) mint from one counter with no lock.
# PORT-MANIFEST.yaml records the consequence as normal operation for THIS file --
# "both sides run their own plan against OVERLAPPING ids" -- and it has already
# cost a forced renumber: a concurrent push produced two different G70 and two
# different G71, and the desktop pair moved to G75/G76 because config/gate-log.md
# cited G73/G74 inside a SIGNED-OFF record (docs/port-prompt.md). Bands make
# allocation need no coordination: producer 1-9999, company 10000+, readable by
# LENGTH so there is no boundary to remember.

#: Producer allocates at or below this, in EVERY letter series. Company is above it.
PRODUCER_BAND_CEILING = 9999

#: Company items that have legitimately arrived through a per-entry port merge.
#: EMPTY today and hand-maintained on purpose -- a company item appearing in the
#: producer backlog is worth one human look, and a typed exemption is what forces it.
PORTED_COMPANY_IDS: frozenset[str] = frozenset()


def test_producer_allocates_below_the_company_band() -> None:
    """No item minted here may take a company number.

    Forward-only: historical ids are never renumbered (they are join keys -- the G87
    ruling, and config/gate-log.md cites them inside signed records), so a low number
    means "allocated before the partition", not "producer". The rule governs the NEXT
    id in each series.
    """
    doc = _load()
    stray = []
    for item in doc.get("items", []):
        iid = str(item.get("id", ""))
        if iid in PORTED_COMPANY_IDS:
            continue
        digits = "".join(ch for ch in iid if ch.isdigit())
        if digits and int(digits) > PRODUCER_BAND_CEILING:
            stray.append(iid)
    assert not stray, (
        f"backlog ids in the COMPANY band (>{PRODUCER_BAND_CEILING}): {sorted(stray)}. "
        "Producer allocates 1-9999 in every series. If these arrived through a port, "
        "add them to PORTED_COMPANY_IDS rather than widening the band."
    )


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


def test_no_duplicate_mapping_keys() -> None:
    """A duplicated block passes every other guard here, so it needs its own.

    PyYAML keeps the LAST value for a duplicated key, so a repeated field inside
    one item silently shadows the first. A port merge script shipped exactly that
    — two `summary:` blocks in the monolith — through a green suite (company
    PORT-REPORT-40c35724 follow-up, 2026-08-03). Per file now, every file.
    """
    dupes: list[str] = []
    for path in sorted(BACKLOG.rglob("*.yaml")):
        dupes += [
            f"{path.name}: {d}" for d in _find_duplicate_keys(path.read_text(encoding="utf-8"))
        ]
    assert not dupes, f"{len(dupes)} duplicate YAML key(s):\n" + "\n".join(dupes)


def test_no_stored_rollup() -> None:
    """ADR 0013 Clause 3, the inversion of the old recompute guards: counts and
    next_ready are renderer OUTPUT. A `summary:`/`next_ready:`/`updated:` key
    anywhere in the tree is the defect — it is the line two sessions collide on."""
    offenders = []
    for path in sorted(BACKLOG.rglob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for key in ("summary", "next_ready", "updated"):
            if isinstance(doc, dict) and key in doc:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: `{key}:`")
    assert not offenders, "stored roll-ups found (derive them — ADR 0013):\n" + "\n".join(offenders)


def test_derived_summary_is_consistent() -> None:
    """The derivation itself: counts sum to the item total; next_ready is exactly the
    todo items whose every dependency is done."""
    doc = _load()
    summary = backlog_store.derive_summary(doc)
    items = {i["id"]: i for i in doc["items"]}
    assert sum(summary[s] for s in STATUSES) == len(items)
    expected = {
        iid
        for iid, item in items.items()
        if item["status"] == "todo"
        and all(items[dep]["status"] == "done" for dep in item.get("depends_on", []))
    }
    assert set(summary["next_ready"]) == expected


def test_monolith_is_a_tombstone() -> None:
    """The retired backlog.yaml must stay a pointer. A re-grown `items:` key means
    someone (or a port) resurrected the monolith beside the tree — two sources of
    truth, which is the 2026-08-04 collision with a second copy."""
    assert TOMBSTONE.exists(), "the tombstone file must remain (ports and docs point at it)"
    doc = yaml.safe_load(TOMBSTONE.read_text(encoding="utf-8")) or {}
    assert doc.get("schema") == "drydocs.backlog.tombstone", "backlog.yaml is not the tombstone"
    assert "items" not in doc, "backlog.yaml grew an `items:` key — the monolith was resurrected"
