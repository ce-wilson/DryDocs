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

import hashlib
from pathlib import Path

import pytest

from tests.source_scan import NAME, called_names

try:
    import yaml

    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

from drydocs_core import backlog_store

REPO_ROOT = Path(__file__).resolve().parents[2]
REPO = Path(__file__).resolve().parents[2]
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
# J50: `gates:` is OPTIONAL — the declared gate edge (slugs this item waits on or
# builds from), validated in test_declared_gates_are_lists_of_known_prompt_slugs.

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
# cited G73/G74 inside a SIGNED-OFF record (docs/port/port-prompt.md). Bands make
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


# ---- the id allocator (I6, 2026-08-30) --------------------------------------
# The band guard above partitions the two REPOS and always did its job. It says
# nothing about the two PRODUCER MACHINES minting the same number inside one
# band, which has now happened six times -- most recently O69 on 2026-08-29,
# where one machine's id was already pushed on a feature branch and the other
# never looked past its own working tree. These guards close that, and they are
# separate from the band rule rather than a restatement of it.


def _allocator():
    """The allocator module, imported by path (it lives under .claude/skills/).

    Imported rather than reimplemented: a test that spelled "next free" itself
    would be a SECOND allocator, which is the shape of the original defect.
    """
    import importlib.util

    path = REPO / ".claude" / "skills" / "groom-backlog" / "validate.py"
    spec = importlib.util.spec_from_file_location("groom_validate", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_the_allocator_and_the_band_guard_agree_on_the_ceiling() -> None:
    """The ceiling is written down twice, so it is asserted equal.

    validate.py duplicates it deliberately -- it runs where pytest does not,
    which is its entire reason to exist. A duplicated constant with a guard is
    one fact; a duplicated constant without one is two facts drifting.
    """
    assert _allocator().PRODUCER_BAND_CEILING == PRODUCER_BAND_CEILING


def test_next_free_is_max_plus_one_and_never_fills_a_gap() -> None:
    """A gap is not evidence a number is free; it is usually evidence it is BURNED.

    G70 and G71 were forced to G75/G76 because config/gate-log.md cites ids
    inside SIGNED records. Handing G70 out again would silently re-point a
    citation inside a signed-off gate, which is worse than leaving a hole.
    """
    alloc = _allocator()
    taken = {"Z1", "Z2", "Z5"}  # Z3 and Z4 are gaps
    assert alloc.next_id("Z", taken) == ("Z6", 5)


def test_the_allocator_refuses_the_reserved_series() -> None:
    alloc = _allocator()
    with pytest.raises(SystemExit, match="reserved for company-side"):
        alloc.next_id("DD", {"DD1"})


def test_the_allocator_refuses_to_cross_into_the_company_band() -> None:
    alloc = _allocator()
    with pytest.raises(SystemExit, match="COMPANY band"):
        alloc.next_id("Z", {"Z" + str(PRODUCER_BAND_CEILING)})


def test_the_taken_set_is_a_union_of_all_three_sources() -> None:
    """The union is at least as large as each term, and all three are consulted.

    WHAT THIS DELIBERATELY DOES NOT ASSERT, after it broke CI: that each term
    contributes an id the others miss. That is TRUE and it is MEASURED -- on the
    authoring clone, O79 and O80 sit in the working tree and appear in neither
    history listing (they arrived through a re-mint rename), and burned ids appear
    in history and in no tree at all -- but it is a property of THIS CHECKOUT's
    git graph, not of the code. CI checks out a different ref set and the
    difference came back empty, so the assertion failed on a machine where nothing
    was wrong. That is the same class as the Path-sorting bug in
    test_render_determinism.py: a test that passes on the authoring machine and
    fails on the runner is testing the machine.

    So the measurement lives in the docstring where it belongs as evidence, and
    what is ASSERTED is the shape: every term is in the union, and the allocator
    reads all three.
    """
    import inspect

    alloc = _allocator()
    local = alloc.local_ids()
    history = alloc.historical_ids()
    union, counts, _ = alloc.known_ids()

    assert local <= union, "the local items are not all in the union"
    assert history <= union, "the historical adds are not all in the union"
    assert counts["local"] == len(local)

    # All three terms are actually consulted -- the risk a set-comparison cannot
    # see is a term quietly dropped from known_ids() while the union still looks
    # complete on a checkout where two terms happen to cover the third.
    called = called_names(inspect.getsource(alloc.known_ids), kind=NAME)
    assert {"local_ids", "remote_ids", "historical_ids"} <= called, (
        f"known_ids() no longer reads all three sources (calls: {sorted(called)}). "
        "Free in one place is not free -- that is the whole item."
    )


def test_every_local_id_parses_as_a_series_and_a_number() -> None:
    """The allocator can only count ids it can parse.

    An id shaped unlike G129 is invisible to max+1, so it would be handed out
    again. Assert the corpus is parseable rather than trusting the regex.
    """
    alloc = _allocator()
    doc = _load()
    unparsed = [
        str(item.get("id"))
        for item in doc.get("items", [])
        if not alloc._ID_RE.match(str(item.get("id", "")))
    ]
    assert not unparsed, (
        f"item id(s) the allocator cannot parse: {unparsed}. An unparseable id is "
        "invisible to next-free and will be minted twice."
    )


def test_no_id_carries_two_different_titles_across_the_remote_trunk() -> None:
    """The collision, caught while it is still cheap.

    The duplicate-id check above fires only once both files sit in ONE checkout,
    which is to say once the collision has already happened and the work is
    renumbering. This compares the local item files against the remote trunk,
    where the other machine's push lands first.

    Skips with a named message where no remote is reachable -- the U26 precedent.
    A guard that FAILED offline would be a guard people learn to skip.
    """
    alloc = _allocator()
    trunk = "refs/remotes/origin/main"
    listing = alloc._git("ls-tree", "-r", trunk, "--", alloc.ITEMS_REL)
    if not listing:
        pytest.skip(trunk + " not listable here - remote check skipped, not failed")

    # Blob shas first, and read only the files that actually DIFFER. Comparing
    # every item with its own `git show` took 38 seconds; almost every file is
    # byte-identical to the trunk, so the sha is the cheap discriminator and the
    # read happens only where there is something to disagree about.
    trunk_blobs: dict[str, str] = {}
    for row in listing.splitlines():
        meta, _, name = row.partition("\t")
        parts = meta.split()
        if len(parts) == 3 and alloc._FILE_RE.search(name.strip()):
            trunk_blobs[name.strip()] = parts[2]

    header = b"blob %d" + bytes([0])  # git's own object rule: "blob <len>" NUL body
    candidates: list[tuple[str, str]] = []
    for name, sha in trunk_blobs.items():
        local_path = REPO / name
        if not local_path.exists():
            continue  # on the trunk and not here: a pull away, not a collision
        raw = local_path.read_bytes()
        local_sha = hashlib.sha1(header % len(raw) + raw).hexdigest()
        if local_sha != sha:
            candidates.append((name, sha))

    disagreements: list[str] = []
    for name, sha in candidates:
        blob = alloc._git("cat-file", "-p", sha)
        if not blob:
            continue
        remote_title = (yaml.safe_load(blob) or {}).get("title")
        local_title = (yaml.safe_load((REPO / name).read_text(encoding="utf-8")) or {}).get("title")
        if remote_title and local_title and remote_title != local_title:
            iid = alloc._FILE_RE.search(name).group("id")
            disagreements.append(
                f"{iid}: local {local_title[:60]!r} vs trunk {remote_title[:60]!r}"
            )

    assert not disagreements, (
        "id(s) carrying a DIFFERENT title here than on the remote trunk -- two "
        "machines minted the same number:\n  "
        + "\n  ".join(disagreements)
        + "\nRenumber the LOCAL one with: python .claude/skills/groom-backlog/"
        "validate.py --next-id <SERIES>"
    )


GATE_PROMPTS = REPO / "config" / "gate-prompts"


def test_declared_gates_are_lists_of_known_prompt_slugs() -> None:
    """J50: `gates:` is optional; when present it is a list of slugs that exist
    as config/gate-prompts/<slug>.yaml. render_gates.py reads ONLY this field
    for the unblocks edge, so a typo here is a silently missing edge — hence
    the guard."""
    doc = _load()
    slugs = {p.stem for p in GATE_PROMPTS.glob("*.yaml")}
    failures: list[str] = []
    for item in doc.get("items", []):
        gates = item.get("gates")
        if gates is None:
            continue
        if not isinstance(gates, list) or not all(isinstance(g, str) for g in gates):
            failures.append(f"[{item['id']}] gates must be a list of slug strings")
            continue
        for g in gates:
            if g not in slugs:
                failures.append(f"[{item['id']}] gates names unknown prompt slug '{g}'")
        if len(set(gates)) != len(gates):
            failures.append(f"[{item['id']}] gates repeats a slug")
    assert not failures, "\n".join(failures)


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
