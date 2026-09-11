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
import re
import subprocess
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

#: THE BAND, RETIRED FORWARD-ONLY (gate ontology-domain-registry-and-edition-grain §C4,
#: 2026-09-02; built at PLAN2, 2026-09-05). It governs no new mint: a venue is named by
#: its EDITION SEGMENT now, and the allocator's band check became the edition-segment
#: check (`_parse` below reads both). The constant stays because old ids are still READ
#: by it - FROZEN_BAND is judged against it, and the base edition stays at or below it.
PRODUCER_BAND_CEILING = 9999

#: Company items that have legitimately arrived through a per-entry port merge.
#: EMPTY today and hand-maintained on purpose -- a company item appearing in the
#: producer backlog is worth one human look, and a typed exemption is what forces it.
PORTED_COMPANY_IDS: frozenset[str] = frozenset()


def _parse(iid: str) -> tuple[str | None, str, int] | None:
    """``(edition, series, number)`` through THE ALLOCATOR'S regex, or None.

    One parser, on purpose (PLAN2 a). Three places in this file used to pull the
    letters and the digits out of an id by hand (``isalpha()`` / ``isdigit()`` joins),
    and none of them FAILED on an edition segment - they turned ``XMPL-LOAD1`` into
    series ``XMPLLOAD`` and quietly stopped guarding, which is worse than failing.
    Reading the allocator's regex means there is one grammar the guards cannot drift
    from; the allocator is already imported here for the agreement guards.
    """
    m = _allocator()._ID_RE.match(str(iid))
    if not m:
        return None
    return (m.group("edition"), m.group("series"), int(m.group("number")))


def test_the_base_backlog_carries_no_band_shaped_id() -> None:
    """No item minted here may take a band-shaped number.

    The band is RETIRED as a partition rule (§C4), but the base edition stays at or
    below the ceiling, so a five-digit id in THIS backlog is still one of two things:
    a company id that arrived through a port (add it to PORTED_COMPANY_IDS, so it is
    looked at once), or a mint that bypassed the allocator. Forward-only: historical
    ids are never renumbered (join keys - the G87 ruling, and config/gate-log.md cites
    them inside signed records).
    """
    doc = _load()
    stray = []
    for item in doc.get("items", []):
        iid = str(item.get("id", ""))
        if iid in PORTED_COMPANY_IDS:
            continue
        parsed = _parse(iid)
        if parsed and parsed[2] > PRODUCER_BAND_CEILING:
            stray.append(iid)
    assert not stray, (
        f"band-shaped backlog ids (>{PRODUCER_BAND_CEILING}): {sorted(stray)}. The base "
        "edition stays below the retired band. If these arrived through a port, add them "
        "to PORTED_COMPANY_IDS rather than widening anything."
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
    taken = {"PLAN1", "PLAN2", "PLAN5"}  # PLAN3 and PLAN4 are gaps
    # venue pinned, as the siblings below pin it: without it the call reads the live
    # config/dev-environment.yaml, and on a tree that declares no `edition:` (a consumer
    # before its own edition gate) the allocator refuses before it ever counts - which
    # made THIS test red on the 2026-09-05 apply for a reason that is not the gap rule.
    assert alloc.next_id("PLAN", taken, venue="base") == ("PLAN6", 5)


def test_the_allocator_refuses_the_reserved_series() -> None:
    """DD is frozen: the company reserve retired as a partition rule (§C4), the
    refusal names the replacement (the edition segment) and the record."""
    alloc = _allocator()
    with pytest.raises(SystemExit, match="FROZEN.*edition segment"):
        alloc.next_id("DD", {"DD1"})


def test_the_allocator_refuses_a_band_shaped_base_id() -> None:
    """The base stays below the retired band; the refusal names the segment as the
    replacement, never a wider band."""
    alloc = _allocator()
    with pytest.raises(SystemExit, match="band-shaped.*edition segment"):
        alloc.next_id("PLAN", {"PLAN" + str(PRODUCER_BAND_CEILING)}, venue="base")


# ---- the edition segment (PLAN2, 2026-09-05) -----------------------------------------
# Gate ontology-domain-registry-and-edition-grain §C1/§C4 and its rider
# idea-series-grammar §B1/§C1/§D1. `[<EDITION>-]<MODULE><n>` and `[<EDITION>-]Idea-<n>`,
# edition first, the base unprefixed. Both halves DECLARED: the segment in
# config/taxonomy/editions.yaml (CFG2), the series in modules.yaml. The venue a session
# runs as is DECLARED in config/dev-environment.yaml `edition:`, never inferred.

#: The one fixed list both parsers must agree on (PLAN2 e - "two parsers, one grammar").
#: validate.py accepted uppercase only and no suffix; backlog_store.py accepted any case
#: and an optional [a-z] suffix; nothing asserted they agreed. The suffix is RULED here:
#: an item id never carries one (the split suffix is an Idea-inbox shape), so both
#: parsers refuse `G129a`; and both are uppercase-only.
PARSE_AGREEMENT: dict[str, tuple[str | None, str, int] | None] = {
    "G129": (None, "G", 129),
    "MM4": (None, "MM", 4),
    "DD7": (None, "DD", 7),
    "LOAD12": (None, "LOAD", 12),
    "PLAN2": (None, "PLAN", 2),
    "G10003": (None, "G", 10003),
    "DD10001": (None, "DD", 10001),
    "XMPL-LOAD1": ("XMPL", "LOAD", 1),
    "SMPL-PLAN12": ("SMPL", "PLAN", 12),
    "AB-CFG3": ("AB", "CFG", 3),
    # refused by both: lowercase, a suffix, a 1-letter or 6-letter segment, no number
    "load1": None,
    "G129a": None,
    "xmpl-LOAD1": None,
    "X-LOAD1": None,
    "XMPLQZ-LOAD1": None,
    "LOAD": None,
    "LOAD-1": None,
}


def _store_parse(iid: str) -> tuple[str | None, str, int] | None:
    from drydocs_core import backlog_store

    m = backlog_store._ID_RE.match(iid)
    return None if not m else (m.group("edition"), m.group("series"), int(m.group("number")))


def test_the_two_parsers_agree_on_one_grammar() -> None:
    for iid, expected in PARSE_AGREEMENT.items():
        assert _parse(iid) == expected, f"allocator parse of {iid!r}"
        assert _store_parse(iid) == expected, f"backlog_store parse of {iid!r}"


def test_every_current_id_round_trips_through_the_grammar() -> None:
    """The first guard written (PLAN2 a): every id in the tree parses, and printing the
    parse back gives the id. No existing id moves and none changes shape."""
    doc = _load()
    broken = []
    for item in doc.get("items", []):
        iid = str(item.get("id", ""))
        parsed = _parse(iid)
        if parsed is None:
            broken.append(f"{iid} (unparsed)")
            continue
        edition, series, number = parsed
        rebuilt = f"{edition}-{series}{number}" if edition else f"{series}{number}"
        if rebuilt != iid:
            broken.append(f"{iid} -> {rebuilt}")
    assert not broken, f"ids that do not round-trip through the grammar: {broken}"


def _declared_editions() -> set[str]:
    from drydocs_core.edition_registry import load_registry

    return set(load_registry(reload=True).codes())


def test_an_edition_segment_must_be_declared_and_the_base_carries_none() -> None:
    """Both halves declared (PLAN2 b): a segment is a code in editions.yaml or it is a
    typo, not a tenant; a module code is in modules.yaml `series:`. And THIS backlog is
    the base edition's, so no item here carries a segment at all - an instance's items
    live in the instance's own backlog (ADR 0015 D2, amended at DOC1)."""
    doc = _load()
    codes = _declared_editions()
    by_code = {v: k for k, v in _module_series().items()}
    undeclared, segmented, unknown_series = [], [], []
    for item in doc.get("items", []):
        iid = str(item.get("id", ""))
        parsed = _parse(iid)
        if parsed is None:
            continue
        edition, series, _ = parsed
        if edition is not None:
            segmented.append(iid)
            if edition not in codes:
                undeclared.append(iid)
        if series not in by_code and series not in FROZEN_SERIES and series not in FROZEN_BAND:
            unknown_series.append(iid)
    assert not undeclared, f"ids whose edition segment no editions.yaml row declares: {undeclared}"
    assert not segmented, (
        f"the base backlog carries edition-segment ids: {segmented}. The base is unprefixed; "
        "an edition's items live in that edition's own backlog."
    )
    assert (
        not unknown_series
    ), f"ids whose series is neither a module code nor a frozen letter: {unknown_series}"


def test_the_allocator_mints_into_the_declared_venue_and_refuses_the_rest() -> None:
    """PLAN2 b/d/e, from fixtures - the tree only ever exhibits the base case."""
    alloc = _allocator()
    codes = {"XMPL", "SMPL"}
    taken = {"LOAD11", "LOAD12", "XMPL-LOAD1", "XMPL-LOAD2", "SMPL-LOAD7"}
    ms = alloc.module_series()
    assert ms["drydocs-load"] == "LOAD"

    # the base mints unprefixed, counting only unprefixed ids
    assert alloc.next_id("LOAD", taken, venue="base") == ("LOAD13", 12)
    # the base may mint DOWNWARD for an edition it hosts, counting that edition's ids
    alloc.declared_editions = lambda: codes  # type: ignore[method-assign]
    assert alloc.next_id("LOAD", taken, edition="XMPL", venue="base") == ("XMPL-LOAD3", 2)
    # an instance mints its own segment without asking
    assert alloc.next_id("LOAD", taken, venue="SMPL") == ("SMPL-LOAD8", 7)
    assert alloc.next_id("LOAD", taken, edition="SMPL", venue="SMPL") == ("SMPL-LOAD8", 7)
    # an undeclared SEGMENT is a typo, not a tenant
    with pytest.raises(SystemExit, match="not declared.*typo, not a tenant"):
        alloc.next_id("LOAD", taken, edition="NOPE", venue="base")
    # an instance never mints for its base or for a sibling (downward only)
    with pytest.raises(SystemExit, match="never mints for its base"):
        alloc.next_id("LOAD", taken, edition="base", venue="SMPL")
    with pytest.raises(SystemExit, match="mints for itself only"):
        alloc.next_id("LOAD", taken, edition="XMPL", venue="SMPL")
    # a venue whose own declaration is not in the registry is refused, naming the file
    with pytest.raises(SystemExit, match="does not declare that code"):
        alloc.next_id("LOAD", taken, venue="GHOST")
    # a venue with NO `edition:` mints no item, and the refusal names the key and CFG2
    with pytest.raises(SystemExit, match="declares no `edition:`.*editions.yaml"):
        alloc.next_id("LOAD", taken, venue=None)


def test_the_idea_path_goes_through_next_idea_id_with_the_same_rules() -> None:
    """Rider D1/C1/C2 from fixtures: max+1 never the gap; the floor; the venue check in
    ONE branch - a declared venue mints prefixed (or unprefixed for the base), an
    undeclared venue mints band-shaped until it declares."""
    alloc = _allocator()
    alloc.declared_editions = lambda: {"XMPL", "SMPL"}  # type: ignore[method-assign]
    ideas = {(None, 1), (None, 2), (None, 257), (None, 10034), ("XMPL", 1), ("XMPL", 4)}
    # base: unprefixed at or below the ceiling; a band-shaped entry (a ported company
    # idea) is NOT counted, or one union-append would jump the base to 10035
    assert alloc.next_idea_id(ideas, venue="base") == ("Idea-258", 257)
    # never the lowest gap
    assert alloc.next_idea_id({(None, 5), (None, 9)}, venue="base") == ("Idea-10", 9)
    # a declared edition counts its own
    assert alloc.next_idea_id(ideas, venue="XMPL") == ("XMPL-Idea-5", 4)
    assert alloc.next_idea_id(ideas, edition="SMPL", venue="base") == ("SMPL-Idea-1", 0)
    # an UNDECLARED venue still captures (C1) - band-shaped, above the ceiling, max+1
    assert alloc.next_idea_id(ideas, venue=None) == ("Idea-10035", 10034)
    assert alloc.next_idea_id({(None, 3)}, venue=None) == ("Idea-10000", 0)
    # ... but it cannot override, because it does not know what it is
    with pytest.raises(SystemExit, match="declares no `edition:`"):
        alloc.next_idea_id(ideas, edition="XMPL", venue=None)
    # the Idea regexes carry the segment and the split suffix stays a split
    header = "- **`XMPL-Idea-3a`** · 2026-09-05 · `[plan]` · **open** · prio? **Med** — x"
    assert alloc._idea_numbers(header) == {("XMPL", 3)}
    assert alloc._idea_numbers(header.replace("XMPL-", "")) == {(None, 3)}


def test_the_frozen_band_ids_parse_and_pass_under_the_new_grammar() -> None:
    """The six legacy band ids stay legal forever, forward-only (PLAN3's table, read as
    PLAN2 finds it)."""
    for iid in ("G10001", "G10002", "G10003", "DD10001", "DD10002", "DD10003"):
        assert _parse(iid) is not None
    assert _frozen_strays(["G10001", "DD10003"]) == []


def _declared_venue_value() -> str | None:
    doc = yaml.safe_load((REPO / "config" / "dev-environment.yaml").read_text(encoding="utf-8"))
    value = doc.get("edition") if isinstance(doc, dict) else None
    return None if value is None or str(value).strip() == "" else str(value).strip()


def test_the_allocator_reads_the_venue_from_the_venue_file_and_nowhere_else() -> None:
    """PLAN2 b: venue_edition() answers from config/dev-environment.yaml `edition:` -
    `base` -> BASE_EDITION, a code -> that code upper-cased, no key -> None - and from
    nothing else. This pins the READ, so it holds on every tree, declared or not. The
    VALUE the producer declares is the next test's, kept apart on purpose: on the
    2026-09-05 apply (carve-out D, 2026-09-07) the consumer left `edition:` absent on
    the producer's own ruling, and the one test that asserted both went red on a fact
    about the producer's tree, not about the allocator."""
    alloc = _allocator()
    declared = _declared_venue_value()
    got = alloc.venue_edition()
    if declared is None:
        assert got is None
    elif declared.lower() == alloc.BASE_EDITION:
        assert got == alloc.BASE_EDITION
    else:
        assert got == declared.upper()


def test_the_producer_declares_itself_the_base() -> None:
    """PRODUCER-VENUE FACT (rider C1): the producer is `base`, never undeclared. A
    consumer tree fails this by construction - undeclared until its edition gate, then
    declared as its own code - so a per-entry take drops THIS test deliberately and
    keeps the read test above, which is the one that travels."""
    assert _declared_venue_value() == "base"


# ---- the series is the module (ruling 2026-09-02) ----------------------------------
# The letter was an epoch tag: plan.yaml mapped phases 1:1 to epics and to letters, so a
# series recorded WHEN a phase opened, not what an item is about. G held 136 items across
# six epics and "search the G series" meant nothing. Every item already carried the topic
# axis as a REQUIRED field - `module:` - so the fix is to derive the series from it and
# freeze the letters. No id moves (join keys; config/gate-log.md cites them inside signed
# records). Forward-only, like the band: the freeze governs the NEXT id, and the frozen
# max is a committed constant so it cannot rise with the file it guards.

#: When the letters were frozen.
FROZEN_ON = "2026-09-02"

#: Each legacy series at the highest number it had ever taken - local, every remote ref
#: and history unioned through the allocator - on the day of the ruling. Duplicated from
#: validate.py DELIBERATELY (it runs where pytest does not) and asserted equal below.
FROZEN_SERIES: dict[str, int] = {
    "A": 4,
    "B": 5,
    "C": 44,
    "D": 11,
    "E": 2,
    "F": 2,
    "G": 136,
    "GN": 2,
    "H": 8,
    "I": 8,
    "J": 78,
    "K": 30,
    "L": 29,
    "M": 4,
    "MM": 14,
    "N": 28,
    "O": 92,
    "P": 6,
    "Q": 28,
    "R": 23,
    "S": 16,
    "U": 27,
    "V": 11,
    "W": 3,
    "X": 4,
    "Y": 7,
    "Z": 9,
}


def _module_series() -> dict[str, str]:
    doc = yaml.safe_load((BACKLOG / "modules.yaml").read_text(encoding="utf-8")) or {}
    return {str(k): str(v) for k, v in (doc.get("series") or {}).items()}


#: The company's legacy band ids, frozen at the band's own max (PLAN3, 2026-09-02).
#: FROZEN_SERIES is producer-measured; G10001-G10003 and DD10001-DD10003 exist only on
#: the company side and were legal when minted. A band-shaped number is judged against
#: this table, a letter-shaped one against FROZEN_SERIES. Duplicated from validate.py
#: DELIBERATELY and asserted equal below.
FROZEN_BAND: dict[str, int] = {
    "G": 10003,
    "DD": 10003,
}


def _frozen_strays(ids: list[str]) -> list[str]:
    """The ids that were minted into a closed series after the freeze.

    Two tables, one rule each: a number above PRODUCER_BAND_CEILING is a legacy BAND id
    and must sit at or below FROZEN_BAND[series]; any other number in a frozen letter
    must sit at or below FROZEN_SERIES[series]. A band-shaped number in a series with no
    band entry is a stray - nobody ever minted there legally.
    """
    stray = []
    for iid in ids:
        parsed = _parse(iid)
        if parsed is None:
            continue
        # The freeze is on the SERIES whatever segment precedes it: an edition id in a
        # frozen letter (`XMPL-G1`) is as much a stray as `G137` - the letters closed
        # for every venue, not only the base.
        _edition, series, n = parsed
        if series not in FROZEN_SERIES and series not in FROZEN_BAND:
            continue
        if n > PRODUCER_BAND_CEILING:
            if n > FROZEN_BAND.get(series, 0):
                stray.append(iid)
        elif series in FROZEN_SERIES and n > FROZEN_SERIES[series]:
            stray.append(iid)
    return stray


def test_the_allocator_and_the_guard_agree_on_the_frozen_snapshot() -> None:
    """Written down twice, so asserted equal - the same discipline as the ceiling."""
    alloc = _allocator()
    assert alloc.FROZEN_SERIES == FROZEN_SERIES
    assert alloc.FROZEN_ON == FROZEN_ON
    assert alloc.FROZEN_BAND == FROZEN_BAND


def test_every_module_has_a_series_code_and_no_code_can_collide() -> None:
    """One code per module, and a code that can never be mistaken for a frozen letter.

    Three letters or more, because every frozen series is one or two; not DD, because the
    company side occupied DD1..DD10 in a series this repo cannot see (Idea-162); unique,
    because two modules sharing a series is the G problem reappearing under a new name.
    """
    doc = _load()
    codes = _module_series()
    missing = sorted(set(doc["modules"]) - set(codes))
    assert not missing, f"modules with no series code in modules.yaml `series:`: {missing}"
    orphan = sorted(set(codes) - set(doc["modules"]))
    assert not orphan, f"series codes for modules the census does not list: {orphan}"
    bad = sorted(
        c
        for c in codes.values()
        if not (c.isalpha() and c.isupper() and len(c) >= 3) or c in FROZEN_SERIES or c == "DD"
    )
    assert (
        not bad
    ), f"series codes must be >=3 uppercase letters, not a frozen letter, not DD: {bad}"
    values = list(codes.values())
    dupes = sorted({c for c in values if values.count(c) > 1})
    assert not dupes, f"two modules share a series code: {dupes}"


def test_frozen_series_take_no_new_ids() -> None:
    """Nothing minted after the freeze may land in a letter series.

    An id above the frozen max is a mint that bypassed the allocator - the allocator
    refuses every frozen series - and it goes back to be re-minted under its module.
    """
    doc = _load()
    stray = _frozen_strays([str(item.get("id", "")) for item in doc.get("items", [])])
    assert not stray, (
        f"ids minted in a FROZEN series after {FROZEN_ON}: {sorted(stray)}. The letters are "
        "closed. Re-mint under the module: validate.py --next-id --module <module>."
    )


def test_the_legacy_band_ids_pass_and_the_next_one_does_not() -> None:
    """The company's six band ids are legacy, not strays; G10004 and DD10004 are strays.

    This is the case the producer tree cannot exhibit (no band id exists here), so it is
    pinned as a fixture: without FROZEN_BAND the six fail the day PLAN1 ports (review F3).
    """
    legacy = ["G10001", "G10002", "G10003", "DD10001", "DD10002", "DD10003"]
    assert _frozen_strays(legacy) == []
    assert _frozen_strays(["G10004"]) == ["G10004"]
    assert _frozen_strays(["DD10004"]) == ["DD10004"]
    # a letter-shaped number still answers to the letter table, band or not
    assert _frozen_strays(["G136"]) == []
    assert _frozen_strays(["G137"]) == ["G137"]
    # a band-shaped number in a series that never had a band is a stray
    assert _frozen_strays(["J10001"]) == ["J10001"]
    # module-series ids are outside both tables
    assert _frozen_strays(["PLAN3", "LOAD12"]) == []


def test_a_module_series_id_belongs_to_that_module() -> None:
    """An item whose id carries a module code names that module in `module:`.

    This is what makes the id readable: LOAD12 IS a drydocs-load item, with no lookup.
    The reverse is not asserted - legacy items keep their letters and their modules.
    """
    doc = _load()
    codes = _module_series()
    by_code = {v: k for k, v in codes.items()}
    wrong = []
    for item in doc.get("items", []):
        iid = str(item.get("id", ""))
        parsed = _parse(iid)
        if parsed is None:
            continue
        series = parsed[1]
        if series in by_code and item.get("module") != by_code[series]:
            wrong.append(f"{iid} (module: {item.get('module')!r}, series says {by_code[series]!r})")
    assert not wrong, f"module-series ids filed under a different module: {wrong}"


def test_the_allocator_refuses_a_frozen_series() -> None:
    alloc = _allocator()
    with pytest.raises(SystemExit, match="FROZEN"):
        alloc.next_id("G", {"G1"})


def test_the_allocator_refuses_an_unregistered_series() -> None:
    """A letter nobody registered is how the epoch tags started."""
    alloc = _allocator()
    with pytest.raises(SystemExit, match="not a registered module series"):
        alloc.next_id("QQQ", set())


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
        "id(s) carrying a DIFFERENT title here than on the remote trunk:\n  "
        + "\n  ".join(disagreements)
        + "\n\nTWO CAUSES, and they need opposite fixes. (1) Two machines minted the "
        "same number -- renumber the LOCAL one with: python .claude/skills/"
        "groom-backlog/validate.py --next-id --module <module>. (2) You pushed a mint stub "
        "and then refined its title before pushing the body -- this guard compares "
        "TITLES, not bodies, so it cannot tell that apart from a collision. Push the "
        "body. The mint rule says the stub carries the FINAL title for exactly this "
        "reason (CLAUDE.md, I6)."
    )


GATE_PROMPTS = REPO / "config" / "gate-prompts"


# ---- venue-aware grooming, the edit side (PLAN4, 2026-09-05) ---------------------------
# Two venues groom one inbox and one item set. What a session may do to an entry the
# OTHER venue owns is a mechanism now: the existing text survives verbatim as a prefix,
# additions are stamped `[<venue> YYYY-MM-DD]`, the inbox state token is the owner's.
# These run from FIXTURES, not the live tree: CI's tree is clean against itself and the
# detector is only meaningful against a base (`--check-venue-edits --base <ref>`).

_INBOX_FIXTURE = """## Inbox

- **`Idea-10034`** · 2026-09-05 · `[plan]` · **open** · prio? **Med** —
  **A band-shaped entry - the other venue's.** body line.

- **`XMPL-Idea-2`** · 2026-09-05 · `[plan]` · **parked → CFG2** · prio? **Low** —
  **An edition's entry.** body.

- **`Idea-257`** · 2026-09-05 · `[plan]` · **open** · prio? **Med** —
  **Ours, the base's.** body.

## Recently groomed (audit trail)
"""


def test_owner_of_is_one_function_keyed_to_the_edition_segment() -> None:
    """PLAN4 (a): a segment names its edition; no segment at or below the ceiling is the
    base; no segment above it is the undeclared venue's band (the company's shape
    before it declared). Items and ideas alike; unparseable is None."""
    alloc = _allocator()
    assert alloc.owner_of("PLAN4") == "base"
    assert alloc.owner_of("Idea-257") == "base"
    assert alloc.owner_of("G10003") == alloc.BAND_VENUE
    assert alloc.owner_of("DD10001") == alloc.BAND_VENUE
    assert alloc.owner_of("Idea-10034") == alloc.BAND_VENUE
    assert alloc.owner_of("XMPL-LOAD1") == "XMPL"
    assert alloc.owner_of("XMPL-Idea-2a") == "XMPL"
    assert alloc.owner_of("not-an-id") is None
    # an UNDECLARED venue (None) owns the band; a declared one owns its own segment
    assert alloc.owns(None, "Idea-10034") and not alloc.owns(None, "Idea-257")
    assert alloc.owns("base", "Idea-257") and not alloc.owns("base", "Idea-10034")
    assert alloc.owns("XMPL", "XMPL-Idea-2") and not alloc.owns("XMPL", "Idea-257")


def test_the_detector_catches_a_rewrite_an_unstamped_append_and_a_state_flip() -> None:
    """PLAN4 (c): the three failure modes, each on an entry the base does not own."""
    alloc = _allocator()
    old = _INBOX_FIXTURE
    rewrite = old.replace("body line.", "a different body.")
    unstamped = old.replace("body line.", "body line.\n  an answer with no stamp")
    flip = old.replace(
        "`[plan]` · **open** · prio? **Med** —\n  **A band-shaped",
        "`[plan]` · **closed** · prio? **Med** —\n  **A band-shaped",
    )
    removed = old.replace(
        "- **`XMPL-Idea-2`** · 2026-09-05 · `[plan]` · **parked → CFG2** · prio? **Low** —\n"
        "  **An edition's entry.** body.\n\n",
        "",
    )
    header_rewrite = old.replace("`[plan]` · **parked → CFG2**", "`[bug]` · **parked → CFG2**")

    (f,) = alloc.venue_edit_findings_ideas(old, rewrite, "base")
    assert f.startswith("REWRITE Idea-10034")
    (f,) = alloc.venue_edit_findings_ideas(old, unstamped, "base")
    assert f.startswith("UNSTAMPED Idea-10034")
    (f,) = alloc.venue_edit_findings_ideas(old, flip, "base")
    assert f.startswith("STATE FLIP Idea-10034: open -> closed") and "proposed:" in f
    (f,) = alloc.venue_edit_findings_ideas(old, removed, "base")
    assert f == "REWRITE XMPL-Idea-2: the entry was removed"
    (f,) = alloc.venue_edit_findings_ideas(old, header_rewrite, "base")
    assert f == "REWRITE XMPL-Idea-2: the header changed"


def test_a_stamped_append_an_owners_own_flip_and_an_item_status_change_pass() -> None:
    """PLAN4 (b)/(c): everything that lands. A proposed close is a stamped append; the
    owner flips its own token freely; item-file status is venue-local and out of scope."""
    alloc = _allocator()
    old = _INBOX_FIXTURE
    proposed = old.replace(
        "body line.",
        "body line.\n  [base 2026-09-05] proposed: closed - answered at LOAD2 (c); see LOAD2.yaml",
    )
    assert alloc.venue_edit_findings_ideas(old, proposed, "base") == []
    own_flip = old.replace(
        "- **`Idea-257`** · 2026-09-05 · `[plan]` · **open**",
        "- **`Idea-257`** · 2026-09-05 · `[plan]` · **groomed → PLAN9**",
    )
    assert alloc.venue_edit_findings_ideas(old, own_flip, "base") == []
    # the other venue, running as itself, may flip its own token and rewrite its own body
    theirs = old.replace("body line.", "rewritten by the owner").replace(
        "`[plan]` · **open** · prio? **Med** —\n  **A band-shaped",
        "`[plan]` · **closed** · prio? **Med** —\n  **A band-shaped",
    )
    assert alloc.venue_edit_findings_ideas(old, theirs, None) == []
    # an edition running as itself owns its segment
    assert (
        alloc.venue_edit_findings_ideas(
            old, old.replace("**An edition's entry.** body.", "**An edition's entry.** new"), "XMPL"
        )
        == []
    )

    before = {"id": "G10003", "status": "todo", "notes": "Minted.", "acceptance": "(a) x"}
    after_ok = {
        "id": "G10003",
        "status": "done",
        "notes": "Minted.\n\n[base 2026-09-05] BUILT here; see G10003 close.",
        "acceptance": "(a) x",
    }
    assert alloc.venue_edit_findings_item("G10003", before, after_ok, "base") == []
    after_bad = {
        "id": "G10003",
        "status": "done",
        "notes": "Rewritten.",
        "acceptance": "(a) x",
        "title": "new",
    }
    found = alloc.venue_edit_findings_item("G10003", before, after_bad, "base")
    assert any(f.startswith("REWRITE G10003.notes") for f in found)
    assert any(f.startswith("REWRITE G10003.title") for f in found)
    # the base's own item: nothing to say, whatever changed
    assert alloc.venue_edit_findings_item("PLAN4", before, after_bad, "base") == []


def test_check_venue_edits_is_wired_as_a_detector_with_a_base() -> None:
    """The CLI form the reconcile-port skill runs; against its own HEAD it is vacuous
    (the tree is clean against itself), which is the point of requiring a base."""
    alloc = _allocator()
    assert alloc.check_venue_edits("HEAD", venue="base") == []
    skill = (REPO / ".claude" / "skills" / "reconcile-port" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert (
        "--check-venue-edits --base" in skill
    ), "the reconcile-port skill no longer runs the venue-edit detector at the previous port base"


def test_the_pending_file_mints_n_consecutive_ids_in_one_pass() -> None:
    """PLAN4 (d): candidates carry `Idea-?`, never a number; the landing pass allocates
    consecutively through next_idea_id() - the same function, one code path - inserts
    at the top of the inbox newest first, and a real id in a pending file is refused."""
    alloc = _allocator()
    pending = (
        "# pending-feat-x\n\n"
        "- **`Idea-?`** · 2026-09-05 · `[plan]` · **open** · prio? **Med** — **first.** body\n"
        "  more body\n"
        "- **`Idea-?`** · 2026-09-05 · `[bug]` · **open** · prio? **Low** — **second.**\n"
    )
    assert alloc.pending_file_problems(pending) == []
    candidates = alloc.pending_candidates(pending)
    assert len(candidates) == 2
    minted = alloc.mint_pending(candidates, {(None, 257), (None, 10034)}, venue="base")
    assert [i for i, _ in minted] == ["Idea-258", "Idea-259"]
    assert minted[0][1].startswith("- **`Idea-258`** · 2026-09-05 · `[plan]`")
    assert "Idea-?" not in minted[0][1] + minted[1][1]
    # an edition's pending file mints into its own inbox of numbers
    assert [i for i, _ in alloc.mint_pending(candidates, {("XMPL", 4)}, venue="XMPL")] == [
        "XMPL-Idea-5",
        "XMPL-Idea-6",
    ]
    # an undeclared venue still lands its captures, band-shaped (rider C1)
    assert [i for i, _ in alloc.mint_pending(candidates, {(None, 10034)}, venue=None)] == [
        "Idea-10035",
        "Idea-10036",
    ]
    inbox = "intro\n\n## Inbox\n\n- **`Idea-257`** · old\n\n## Recently groomed\n"
    out = alloc.insert_into_inbox(inbox, [e for _, e in minted])
    assert out.index("Idea-259") < out.index("Idea-258") < out.index("Idea-257")
    # refused: a real id, or a bullet that is not a candidate
    problems = alloc.pending_file_problems(pending + "- **`Idea-9`** · x\n- a plain bullet\n")
    assert any("never carries a real id" in p for p in problems)
    assert any("a candidate opens" in p for p in problems)


def test_retired_is_not_free_a_renumbered_idea_stays_taken() -> None:
    """PLAN4 (e): the allocator reads inbox HISTORY, so a number whose header was
    renumbered away is still taken. This is the case the company's hand count got
    wrong on 2026-09-05 (10006-10008 read as free from the live headers). The fixture
    is a `git log -p` shaped history in which Idea-10006 became Idea-10023."""
    alloc = _allocator()
    history = (
        "-- **`Idea-10006`** · 2026-09-03 · `[plan]` · **open** · prio? **Med** — **x.**\n"
        "+- **`Idea-10023`** · 2026-09-03 · `[plan]` · **open** · prio? **Med** — **x.**"
        " *(renumbered 2026-09-05 from Idea-10006)*\n"
    )
    live = "- **`Idea-10023`** · 2026-09-03 · `[plan]` · **open** · prio? **Med** — **x.**\n"
    taken = alloc._idea_numbers(live) | alloc._idea_numbers(history, alloc._IDEA_IN_DIFF_RE)
    assert (None, 10006) in taken, "the renumbered-away number must stay in the taken set"
    allocated, _ = alloc.next_idea_id(taken, venue=None)
    assert allocated == "Idea-10024" and allocated != "Idea-10006"


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


def _declared_venue_codes() -> set[str]:
    """The codes under `venues:` in config/dev-environment.yaml, empty if the block is
    absent. Read in one place so the travelling guard and the producer-fact guard below
    cannot drift apart."""
    venue_doc = yaml.safe_load(
        (REPO / "config" / "dev-environment.yaml").read_text(encoding="utf-8")
    )
    return set((venue_doc.get("venues") or {}).keys())


def test_declared_venues_are_lists_of_codes_the_venue_file_declares() -> None:
    """PLAN6: `venue:` is optional; when present it is a list of codes declared under
    `venues:` in config/dev-environment.yaml. lane-handoff reads ONLY this field to flag
    an item the receiving machine cannot build, so an undeclared code is a wall the
    check cannot see - hence the guard, on the `gates:` shape (J50).

    This pins the SHAPE and the membership, so it holds on every tree. The membership
    half is checked only where the block exists: `config/dev-environment.yaml` is
    canonical-company and a consumer adopts new KEYS by hand, so between the roll that
    ships this field and the hand-copy, a consumer tree has items carrying `venue:` and
    no block to resolve them against. Asserting the block's PRESENCE here would fail on
    that tree by construction - the shape RELAY-31 carved out of
    `test_the_venue_is_declared_in_the_venue_file...` on 2026-09-07, one day before this
    guard reintroduced it. The presence is the next test's, kept apart on purpose."""
    doc = _load()
    codes = _declared_venue_codes()
    failures: list[str] = []
    for item in doc.get("items", []):
        venue = item.get("venue")
        if venue is None:
            continue
        if not isinstance(venue, list) or not all(isinstance(v, str) for v in venue):
            failures.append(f"[{item['id']}] venue must be a list of code strings")
            continue
        for v in venue:
            if codes and v not in codes:
                failures.append(f"[{item['id']}] venue names undeclared code '{v}'")
        if len(set(venue)) != len(venue):
            failures.append(f"[{item['id']}] venue repeats a code")
    assert not failures, "\n".join(failures)


def test_the_producer_declares_its_venues() -> None:
    """PRODUCER-VENUE FACT (PLAN6), the pair to `test_the_producer_declares_itself_the_base`
    above: the producer's own `config/dev-environment.yaml` carries a non-empty `venues:`
    block, because it is where the KEYS are minted and lane-handoff's V mark reads them.
    A consumer tree fails this by construction until it hand-copies the keys into its
    canonical-company copy - the file's own header states that rule - so a per-entry take
    drops THIS test deliberately and keeps the membership test above, which travels."""
    assert _declared_venue_codes(), "config/dev-environment.yaml declares no venues: section"


#: PLAN12 (2026-09-09) - `inputs:` entries a non-done item may carry that are NOT claims
#: about the tracked tree. Shrink-only, on the runbook-currency guard's idiom: every entry
#: carries a reason of at least forty characters, and an exemption no non-done item cites
#: any more fails the suite. Empty at the guard's landing on purpose - the four genuine
#: failures the premise-drift review measured were FIXED in the same commit, not exempted.
INPUT_EXEMPTIONS: dict[str, str] = {}

#: PLAN14 (2026-09-10) - `outputs:` entries a DONE item may carry that are NOT claims about
#: the tracked tree. Same shrink-only discipline as INPUT_EXEMPTIONS above: a reason of at
#: least forty characters, and an exemption no done item cites any more fails the suite.
#: Empty at landing, for the reason that one was - an exemption is for a path that
#: legitimately cannot resolve, never a parking space for one nobody fixed.
OUTPUT_EXEMPTIONS: dict[str, str] = {}

#: The one path an `outputs:` list may never contain: the item's OWN file.
#: Measured 2026-09-10 across five lane merges (LOAD13, LOAD14, DOC12, API5, CORE15) - the
#: item's own yaml is in 5 of 5 change sets, necessarily, because claiming and closing both
#: edit it. An edge true of every item carries no information; worse, it is the wrong
#: relation. The file is the requirement's ORIGIN - a property :Requirement already declares
#: - not an artifact the requirement is implemented by. LOAD13 is the case that proves the
#: rule: its three changed files are its own yaml plus two tests, so the honest answer is
#: two verified-by edges and ZERO implemented-by, and a reader who counts the yaml
#: manufactures an implementation that does not exist.
_ITEMS_DIR_REL = "docs/restructure/backlog/items"

#: The path grammar an `inputs:` entry must fit to be a claim the guard can test. Anything
#: A leading dot is a path (`.claude/`, `.github/`); a `..` segment is not. Anything
#: else on a non-done item - a prose annotation (`config/x (G26)`), a cross-repo reference
#: (`owner/repo@sha`), a screenshot filename - is MALFORMED and fails loudly: a pre-filter that
#: silently discarded entries with a space is exactly how a stale annotated path would slip
#: through unchecked.
_INPUT_PATH = re.compile(
    r"^(?!\.\.)[A-Za-z0-9_.][A-Za-z0-9_.+\-]*(?:/(?!\.\.)[A-Za-z0-9_.+\-]+)*/?$"
)


def _tracked_paths() -> set[str]:
    """Every path git tracks, read with -z and decoded HERE. Bytes on both sides of the
    pipe on purpose (J76): a text pipe on Windows writes CRLF, git reads the CR as part of
    the pathname and C-quotes its echo - both measurers of the premise-drift review hit it."""
    out = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z"], capture_output=True, check=True
    ).stdout
    return {p.decode("utf-8") for p in out.split(b"\0") if p}


def _ignored_paths(paths: list[str]) -> set[str]:
    """The subset of *paths* that .gitignore rules cover - machine-local inputs, absent on
    every clone by construction (LIN3, MM5, MM7, MM9 at the guard's landing). -z and bytes
    both ways, same reason as above; a non-zero exit with empty output means none matched."""
    if not paths:
        return set()
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "check-ignore", "-z", "--stdin"],
        input="\0".join(paths).encode("utf-8") + b"\0",
        capture_output=True,
        check=False,
    )
    return {p.decode("utf-8") for p in proc.stdout.split(b"\0") if p}


def _input_resolves(rel: str, tracked: set[str]) -> bool:
    """A file resolves when git tracks it; a directory resolves when git tracks anything
    under it. Tracked, never `Path.exists()`: the parent guard documents the fresh-clone
    divergence as its known limit, and Windows `.exists()` is case-insensitive while CI is
    not."""
    rel = rel.rstrip("/")
    if rel in tracked:
        return True
    prefix = rel + "/"
    return any(p.startswith(prefix) for p in tracked)


def test_inputs_of_open_items_resolve_against_the_tracked_tree() -> None:
    """PLAN12: for every item whose status is `todo` or `in_progress`, every `inputs:` string
    resolves against `git ls-files` - the premise-drift review's organ (a), path drift, on
    the one drifting surface where the instrument already existed (test_runbook_currency.py),
    the data is structured rather than prose, and nothing had ever been pointed at it. Five
    of five Lane B items in the 2026-09-09 burst had a premise wrong against the tree.

    Scoped to non-done items: I8 clause (c) already rules a closed item's text a record of
    completed work, so the 109 stale citations on done items are history, not defects.
    Gitignored inputs are classified with `git check-ignore` and skipped - a machine-local
    path is absent on every clone by construction, and failing it would red the suite for
    whoever holds the claim. Deliberately NOT extended to `acceptance:` (five of eleven
    bare-path hits there are deliverables the item will create; a regex cannot tell a promise
    from a claim) and NOT applied to the gate prompts (their sanctioned `[AMENDED; was ...]`
    edit shape preserves the old path on purpose)."""
    doc = _load()
    tracked = _tracked_paths()
    failures: list[str] = []
    candidates: list[tuple[str, str]] = []
    for item in doc.get("items", []):
        if item.get("status") not in {"todo", "in_progress"}:
            continue
        inputs = item.get("inputs") or []
        if not isinstance(inputs, list):
            failures.append(f"[{item['id']}] inputs must be a list")
            continue
        for raw in inputs:
            if not isinstance(raw, str) or not _INPUT_PATH.match(raw):
                failures.append(
                    f"[{item['id']}] malformed inputs entry {raw!r} - a path, or an INPUT_EXEMPTIONS row"
                )
                continue
            if raw in INPUT_EXEMPTIONS:
                continue
            candidates.append((item["id"], raw))
    ignored = _ignored_paths(sorted({raw for _, raw in candidates}))
    for iid, raw in candidates:
        if raw.rstrip("/") in ignored or raw in ignored:
            continue  # machine-local by construction; the item's venue note says where it lives
        if not _input_resolves(raw, tracked):
            failures.append(f"[{iid}] inputs names `{raw}`, which git does not track here")
    assert not failures, (
        f"{len(failures)} inputs: entr{'y' if len(failures) == 1 else 'ies'} on open items "
        "do not resolve - fix the path (the file moved: cite where it is now), or add an "
        "INPUT_EXEMPTIONS row with the reason:\n" + "\n".join(failures)
    )


def test_input_exemptions_carry_a_reason_and_are_still_cited() -> None:
    """Shrink-only, the runbook-currency idiom: an exemption for a path no open item cites
    is dead weight that outlives the reason it was added."""
    doc = _load()
    cited = {
        raw
        for item in doc.get("items", [])
        if item.get("status") in {"todo", "in_progress"}
        for raw in (item.get("inputs") or [])
        if isinstance(raw, str)
    }
    short = [p for p, why in INPUT_EXEMPTIONS.items() if len(why.strip()) < 40]
    assert not short, f"INPUT_EXEMPTIONS reason under forty characters: {short}"
    unused = [p for p in INPUT_EXEMPTIONS if p not in cited]
    assert not unused, f"INPUT_EXEMPTIONS names a path no open item cites - remove it: {unused}"


def _done_outputs(doc: dict) -> list[tuple[str, str]]:
    """``(item id, raw entry)`` for every ``outputs:`` string on a DONE item."""
    pairs: list[tuple[str, str]] = []
    for item in doc.get("items", []):
        if item.get("status") != "done":
            continue
        for raw in item.get("outputs") or []:
            if isinstance(raw, str):
                pairs.append((item["id"], raw))
    return pairs


def test_outputs_of_done_items_resolve_against_the_tracked_tree() -> None:
    """PLAN14: for every DONE item, every `outputs:` string resolves against `git ls-files`.

    The MIRROR IMAGE of the `inputs:` guard above, and the scope inversion is the whole
    design. `inputs:` is checked on NON-done items because it is a premise the work is about
    to act on; `outputs:` is checked on DONE items because it is a claim about work that
    happened. Checking `outputs:` on an open item would be checking a promise, which is
    exactly why the `inputs:` guard's docstring refuses to extend itself to `acceptance:` -
    "a regex cannot tell a promise from a claim". Here the status field tells it.

    Same machinery deliberately: the `_INPUT_PATH` grammar, `git ls-files -z` with bytes on
    both sides of the pipe (J76), gitignored entries skipped because a machine-local path is
    absent on every clone by construction, and a malformed entry failing loudly rather than
    being silently pre-filtered.
    """
    doc = _load()
    tracked = _tracked_paths()
    failures: list[str] = []
    candidates: list[tuple[str, str]] = []
    for iid, raw in _done_outputs(doc):
        if not _INPUT_PATH.match(raw):
            failures.append(
                f"[{iid}] malformed outputs entry {raw!r} - a path, or an OUTPUT_EXEMPTIONS row"
            )
            continue
        if raw in OUTPUT_EXEMPTIONS:
            continue
        candidates.append((iid, raw))
    for item in doc.get("items", []):
        outputs = item.get("outputs")
        if outputs is not None and not isinstance(outputs, list):
            failures.append(f"[{item['id']}] outputs must be a list")
    ignored = _ignored_paths(sorted({raw for _, raw in candidates}))
    for iid, raw in candidates:
        if raw.rstrip("/") in ignored or raw in ignored:
            continue  # machine-local by construction; the item's venue note says where it lives
        if not _input_resolves(raw, tracked):
            failures.append(f"[{iid}] outputs names `{raw}`, which git does not track here")
    assert not failures, "\n".join(failures)


def test_an_item_never_lists_its_own_file_as_an_output() -> None:
    """The item's own yaml is its ORIGIN, not something it implements.

    Every item edits its own file - claiming and closing both do - so an entry that is
    always true carries no information, and it would make every item look like the
    implementation of itself. See the _ITEMS_DIR_REL note for the measurement.
    """
    doc = _load()
    offenders = [
        f"[{iid}] outputs lists its own file `{raw}` - that is the item's origin, not an output"
        for iid, raw in _done_outputs(doc)
        if raw.rstrip("/") == f"{_ITEMS_DIR_REL}/{iid}.yaml"
    ]
    assert not offenders, "\n".join(offenders)


def test_the_outputs_guard_can_actually_fail() -> None:
    """The anti-vacuity control (J26). `outputs:` is new, so the guard above runs over few
    items or none, and a guard that has nothing to look at is indistinguishable from one
    that cannot look. These three assertions exercise the three ways it refuses, against
    synthetic values, so its teeth are proven without waiting for a real offender."""
    tracked = _tracked_paths()
    assert _input_resolves("tests/unit/test_backlog.py", tracked), "control: a real path resolves"
    assert not _input_resolves(
        "tests/unit/no_such_guard_file.py", tracked
    ), "a path git does not track must NOT resolve - if this passes the resolver is broken"
    assert not _INPUT_PATH.match(
        "drydocs/x.py (see LOAD13)"
    ), "an annotated path must be MALFORMED, not silently accepted"


def test_output_exemptions_carry_a_reason_and_are_still_cited() -> None:
    """Shrink-only, the same idiom INPUT_EXEMPTIONS uses: an exemption for a path no done
    item cites any more is dead weight that outlives the reason it was added."""
    doc = _load()
    cited = {raw for _, raw in _done_outputs(doc)}
    short = [p for p, why in OUTPUT_EXEMPTIONS.items() if len(why.strip()) < 40]
    assert not short, f"OUTPUT_EXEMPTIONS reason under forty characters: {short}"
    unused = [p for p in OUTPUT_EXEMPTIONS if p not in cited]
    assert not unused, f"OUTPUT_EXEMPTIONS names a path no done item cites - remove it: {unused}"


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
    todo items whose every dependency is done AND that carry no ``hold:`` (Y7); ``held``
    is exactly the items that do."""
    doc = _load()
    summary = backlog_store.derive_summary(doc)
    items = {i["id"]: i for i in doc["items"]}
    assert sum(summary[s] for s in STATUSES) == len(items)
    expected = {
        iid
        for iid, item in items.items()
        if item["status"] == "todo"
        and not backlog_store.is_held(item)
        and all(items[dep]["status"] == "done" for dep in item.get("depends_on", []))
    }
    assert set(summary["next_ready"]) == expected
    assert set(summary["held"]) == {
        iid for iid, item in items.items() if backlog_store.is_held(item)
    }
    assert not set(summary["held"]) & set(summary["next_ready"])


# --- Y7: a hold is a declared field, read by the derivation, rendered by the board -------
#
# O26 was pulled and claimed on 2026-09-02 with its dependencies done and a hold sitting in
# annotations.status, which no derivation reads. These pin the fix at all three surfaces:
# the derivation (held leaves next_ready), the board (HELD is rendered, never dropped) and
# the boundary (an annotation is a note and never a hold - a general rule over annotations
# would hold items nobody meant to hold, invisibly).


def _hold_doc(hold, status: str = "todo") -> dict:
    """Two done deps and one todo item that is dependency-ready by construction."""
    item = {"id": "H3", "status": status, "depends_on": ["H1", "H2"]}
    if hold is not None:
        item["hold"] = hold
    return {
        "items": [
            {"id": "H1", "status": "done", "depends_on": []},
            {"id": "H2", "status": "done", "depends_on": []},
            item,
        ]
    }


_HOLD = {
    "since": "2026-07-22",
    "by": "SME",
    "until": "the template session rules",
    "reason": "do not pull",
}


def test_held_item_is_excluded_from_next_ready() -> None:
    """(c) and (g): dependency-ready, and still not ready, because a human said so."""
    ready = backlog_store.derive_summary(_hold_doc(None))
    assert ready["next_ready"] == ["H3"] and ready["held"] == []
    held = backlog_store.derive_summary(_hold_doc(_HOLD))
    assert held["next_ready"] == [], "a held item must leave next_ready"
    assert held["held"] == ["H3"], "and must be listed as held, never silently dropped"


def test_unblessed_annotation_does_not_hold() -> None:
    """(b): the exact O26 shape before Y7 - a hold written as prose in annotations - does
    NOT hold. Only the declared field does. This is the boundary, stated as a test so that
    a future 'helpful' rule over annotations fails here first."""
    doc = _hold_doc(None)
    doc["items"][2]["annotations"] = {
        "status": "SME HOLD 2026-07-22: do NOT pull this item until that session rules"
    }
    summary = backlog_store.derive_summary(doc)
    assert summary["next_ready"] == ["H3"], "an annotation is a note, not a hold"
    assert summary["held"] == []
    assert not backlog_store.is_held(doc["items"][2])
    assert backlog_store.hold_errors(doc["items"][2]) == []


def test_held_item_is_rendered_as_held_with_its_text() -> None:
    """(d): the board shows the item as HELD, with the hold text visible OUTSIDE the
    collapsed detail, and lists it in the Held strip; it does not appear in the ready
    strip and does not get the ready accent."""
    from drydocs.plan.plan_board import backlog_from_dict, render_board

    raw = _hold_doc(_HOLD)
    for it in raw["items"]:
        it.update(
            title=f"t {it['id']}", type="chore", module="docs", agent="a", phase=8, priority="p2"
        )
    doc = {
        "schema": "drydocs.backlog.v3",
        "plan": {"phases": [{"id": 8, "title": "eight", "goal": "g"}]},
        "items": raw["items"],
    }
    html = render_board(backlog_from_dict(doc))
    h3 = html.index('id="card-H3"')
    card_tag = html[html.rindex('<div class="card', 0, h3) : h3]
    assert "held" in card_tag
    assert "ready" not in card_tag, "a held item never wears the ready accent"
    card = html[h3 : html.index('<div class="detail"', h3)]
    assert "hold-badge" in card and "HELD" in card
    assert "do not pull" in card, "the hold text is outside the collapsed detail"
    assert "the template session rules" in card
    held_strip = html[html.index('class="held-strip"') :]
    held_strip = held_strip[: held_strip.index("</div>")]
    assert "H3" in held_strip
    ready_strip = html[html.index('class="ready-strip"') :]
    ready_strip = ready_strip[: ready_strip.index("</div>")]
    assert "H3" not in ready_strip


def test_hold_shape_is_guarded_and_fails_closed() -> None:
    """A malformed hold still HOLDS (fail closed - a typo must not release an item) and
    is reported, so the mistake is visible rather than silently obeyed. A hold on a status
    that cannot be pulled is a stale or bypassed hold, and fails too."""
    bad = {"id": "X1", "status": "todo", "depends_on": [], "hold": "SME HOLD"}
    assert backlog_store.is_held(bad)
    assert backlog_store.hold_errors(bad), "a non-mapping hold is reported"
    missing = {"id": "X2", "status": "todo", "depends_on": [], "hold": {"since": "2026-09-07"}}
    assert any("reason" in e for e in backlog_store.hold_errors(missing))
    unknown = {"id": "X3", "status": "todo", "depends_on": [], "hold": {**_HOLD, "date": "x"}}
    assert any("date" in e for e in backlog_store.hold_errors(unknown))
    done = {"id": "X4", "status": "done", "depends_on": [], "hold": dict(_HOLD)}
    assert any("done" in e for e in backlog_store.hold_errors(done))
    assert (
        backlog_store.hold_errors({"id": "X5", "status": "todo", "depends_on": [], "hold": None})
        == []
    )
    assert (
        backlog_store.hold_errors(
            {"id": "X6", "status": "blocked", "depends_on": [], "hold": dict(_HOLD)}
        )
        == []
    )


def test_every_committed_hold_is_well_formed() -> None:
    """The fixtures are real items (O26, G64). Any hold in the tree passes the shape guard,
    and the two the item named are present and held."""
    doc = _load()
    errors = [e for it in doc["items"] for e in backlog_store.hold_errors(it)]
    assert errors == [], errors
    held = set(backlog_store.derive_summary(doc)["held"])
    assert {"O26", "G64"} <= held, f"the two live instances must be held: {sorted(held)}"


def test_monolith_is_a_tombstone() -> None:
    """The retired backlog.yaml must stay a pointer. A re-grown `items:` key means
    someone (or a port) resurrected the monolith beside the tree — two sources of
    truth, which is the 2026-08-04 collision with a second copy."""
    assert TOMBSTONE.exists(), "the tombstone file must remain (ports and docs point at it)"
    doc = yaml.safe_load(TOMBSTONE.read_text(encoding="utf-8")) or {}
    assert doc.get("schema") == "drydocs.backlog.tombstone", "backlog.yaml is not the tombstone"
    assert "items" not in doc, "backlog.yaml grew an `items:` key — the monolith was resurrected"


# ---------------------------------------------------------------------------
# I8 -- dependency currency, the groom-time warning.
#
# THE MECHANISM ONLY. These assert that a known-stale pair is reported and a
# current one is not, against a hand-built time map. They deliberately never
# assert the CONTENT of the live list: that list changes with every commit that
# touches an item file, so a test pinning it would be a diary that fails for
# reasons unrelated to the code -- and would be "fixed" by pasting in whatever
# today's output happens to be, which asserts nothing.
# ---------------------------------------------------------------------------

#: A fixed clock. Values are unix times only in shape; nothing here reads git.
_OLDER, _NEWER = 1_700_000_000, 1_700_009_999


def test_a_dependency_committed_after_its_dependent_is_reported() -> None:
    v = _allocator()
    times = {"A1": _OLDER, "A2": _NEWER}
    items = [{"id": "A1", "status": "todo", "depends_on": ["A2"]}]
    assert v.dependency_currency_warnings(items, times) == [("A1", "A2")]


def test_a_dependency_older_than_its_dependent_is_not_reported() -> None:
    """The common case, and the reason this is a warning and not a gate: most
    edges are simply fine and must produce no line at all."""
    v = _allocator()
    times = {"A1": _NEWER, "A2": _OLDER}
    items = [{"id": "A1", "status": "todo", "depends_on": ["A2"]}]
    assert v.dependency_currency_warnings(items, times) == []


def test_a_done_item_is_excluded_however_stale_its_dependency_is() -> None:
    """Clause (c), asserted rather than only commented: a closed item's acceptance
    describing an older dependency is a HISTORICAL RECORD and correct as written.
    Reporting those would invite reopening verified work to make it retrospectively
    true -- the argument the 2026-08-28 groom used when it filed O77 fresh rather
    than reopening O66."""
    v = _allocator()
    times = {"A1": _OLDER, "A2": _NEWER}
    for status in ("done", "blocked"):
        items = [{"id": "A1", "status": status, "depends_on": ["A2"]}]
        assert v.dependency_currency_warnings(items, times) == [], status


def test_an_item_or_dependency_with_no_commit_is_skipped_not_crashed() -> None:
    """A just-minted item file has no commit yet, so it is absent from the map.
    There is nothing to compare and the right answer is silence -- not a
    KeyError in the middle of a groom."""
    v = _allocator()
    items = [
        {"id": "A1", "status": "todo", "depends_on": ["MISSING"]},
        {"id": "UNCOMMITTED", "status": "todo", "depends_on": ["A2"]},
        {"id": "A3", "status": "todo"},  # no depends_on key at all
    ]
    assert v.dependency_currency_warnings(items, {"A1": _OLDER, "A2": _NEWER}) == []


def test_equal_timestamps_are_not_stale() -> None:
    """One commit touching both files is the ordinary case for an item minted with
    its dependency, or for a bulk status sweep. Strictly-newer is the rule."""
    v = _allocator()
    items = [{"id": "A1", "status": "todo", "depends_on": ["A2"]}]
    assert v.dependency_currency_warnings(items, {"A1": _OLDER, "A2": _OLDER}) == []


def test_the_time_map_actually_reads_this_repository() -> None:
    """Instrument check (J76). Every assertion above would pass unchanged against a
    time map that is always empty, and an always-empty map is exactly what a broken
    git call produces -- silently, since the warning list would simply be empty and
    read as "nothing stale". So one test asks the real reader for the real tree."""
    v = _allocator()
    times = v.item_commit_times()
    if not times:
        pytest.skip("no git history here — the batched log returned nothing")
    ids = {p.stem for p in (BACKLOG / "items").glob("*.yaml")}
    assert len(times) > 100, f"only {len(times)} item files have a commit time"
    assert times.keys() & ids, "the map shares no id with the items directory"
    assert all(isinstance(v_, int) for v_ in times.values()), "non-integer commit time"
