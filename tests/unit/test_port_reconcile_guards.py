"""J7 — executable per-entry port reconciler guards (PORT-MANIFEST entry_rules).

The manifest's `per-entry` rows carry prose entry_rules; these are those rules as
code (docs/reviews/tech-debt-port-boundary.md Phase 2). Same YAML loading idiom
as the map guard (pytest + yaml.safe_load) — no second parser.

Three rules:

* **Status no-downgrade** — a merge may never downgrade
  relationship_vocabulary.yaml ``active`` → planned/deprecated/removed,
  taxonomy-ontology-map.yaml ``confirmed``/``applied`` → proposed, nor
  backlog.yaml ``done`` → todo/in_progress (J16, 2026-07-28: that file became a
  per-entry row once the fall-through guard showed it had none); and a consumer
  entry may never simply VANISH (per-entry means union of entries).
* **Append-only** — union-append audit files (config/gate-log.md): the
  pre-merge text must be a byte prefix of the merged text.
* **Version-string rule** — asserted in test_port_manifest.py (the manifest row
  itself is the contract).

Consumer-side usage during reconcile-port (documented in that skill):

    1. BEFORE applying the port, snapshot the consumer copies:
         mkdir %TEMP%/reconcile-before
         python -c "from pathlib import Path; from drydocs_core import yaml_fragments as yf; \
            Path('<before-dir>/relationship_vocabulary.yaml').write_text(yf.merged_text('drydocs_core/ontology/relationship_vocabulary'), encoding='utf-8'); \
            Path('<before-dir>/taxonomy-ontology-map.yaml').write_text(yf.merged_text('config/taxonomy-ontology-map'), encoding='utf-8')"
         cp config/gate-log.md  <before-dir>/
       (S5: both registries are fragment DIRECTORIES now — the snapshot is the
       MERGED document, so the before/after comparison stays file-shaped.)
    2. Apply the port range / resolve collisions.
    3. RECONCILE_BEFORE_DIR=<before-dir> pytest tests/unit/test_port_reconcile_guards.py -q
       → FAILS on any downgrade / dropped entry / audit truncation the merge introduced.

Without RECONCILE_BEFORE_DIR the live-comparison tests SKIP; the fixture-driven
mechanics tests run everywhere (producer CI included).
"""

from __future__ import annotations

import os
import re
import subprocess
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import pytest

from drydocs_core import yaml_fragments

yaml = pytest.importorskip("yaml")

REPO = Path(__file__).resolve().parents[2]
MANIFEST_FILE = REPO / "PORT-MANIFEST.yaml"
VOCAB_FILE = REPO / "drydocs_core" / "ontology" / "relationship_vocabulary"
MAP_FILE = REPO / "config" / "taxonomy-ontology-map"
BACKLOG_FILE = REPO / "docs" / "restructure" / "backlog.yaml"
GATE_LOG = REPO / "config" / "gate-log.md"

BEFORE_DIR_ENV = "RECONCILE_BEFORE_DIR"

# entry_rule: "NEVER downgrade a consumer entry whose status is active ... to
# the producer's planned/deprecated" (+ removed, a fortiori)
VOCAB_DOWNGRADES: dict[str, set[str]] = {"active": {"planned", "deprecated", "removed"}}
# entry_rule: "NEVER downgrade confirmed/applied -> proposed"
MAP_DOWNGRADES: dict[str, set[str]] = {
    "confirmed": {"proposed"},
    "applied": {"proposed"},
}
# entry_rule (J16): "NEVER regress a status (done -> in_progress/todo) or drop an
# entry". Both sides plan against OVERLAPPING ids, so a port that walks work
# backwards is indistinguishable from a port that never happened.
BACKLOG_DOWNGRADES: dict[str, set[str]] = {
    "done": {"in_progress", "todo", "blocked"},
    "in_progress": {"todo"},
}


# --- the executable rules (pure) -------------------------------------------------


def status_downgrades(
    before: Iterable[Mapping[str, Any]],
    after: Iterable[Mapping[str, Any]],
    *,
    key: str,
    downgrade_map: dict[str, set[str]],
    status_field: str = "status",
) -> list[str]:
    """Violations a merge introduced: banned status transitions + dropped entries."""
    after_by = {e[key]: e for e in after}
    violations: list[str] = []
    for entry in before:
        k, status = entry[key], entry.get(status_field)
        merged = after_by.get(k)
        if merged is None:
            violations.append(f"{k}: entry DROPPED by the merge (was {status!r})")
        elif merged.get(status_field) in downgrade_map.get(status, set()):
            violations.append(f"{k}: status downgraded {status!r} -> {merged.get(status_field)!r}")
    return violations


def append_only_violation(before_text: str, after_text: str) -> str | None:
    """None if ``before_text`` is a byte prefix of ``after_text``; else a message."""
    if after_text.startswith(before_text):
        return None
    limit = min(len(before_text), len(after_text))
    at = next((i for i in range(limit) if before_text[i] != after_text[i]), limit)
    return (
        f"append-only violated: merged file diverges from the pre-merge text at "
        f"char {at} (existing entries must be a prefix — dropping or editing "
        "either side's audit entries is an audit violation)"
    )


def vocab_entries(doc: dict) -> list[dict]:
    return doc["local_relationships"]


def map_entries(doc: dict) -> list[dict]:
    return doc["mappings"]


def backlog_entries(doc: dict) -> list[dict]:
    return doc["items"]


# --- fixture-driven mechanics (run everywhere) ------------------------------------

_VOCAB_BEFORE = [
    {"id": "m3_active_edge", "status": "active"},
    {"id": "m3_planned_edge", "status": "planned"},
]


def test_vocab_active_downgrade_fails() -> None:
    after = [
        {"id": "m3_active_edge", "status": "planned"},  # producer clobbered it
        {"id": "m3_planned_edge", "status": "planned"},
    ]
    violations = status_downgrades(_VOCAB_BEFORE, after, key="id", downgrade_map=VOCAB_DOWNGRADES)
    assert violations == ["m3_active_edge: status downgraded 'active' -> 'planned'"]


def test_vocab_upgrade_and_new_entries_pass() -> None:
    after = [
        {"id": "m3_active_edge", "status": "active"},
        {"id": "m3_planned_edge", "status": "active"},  # upgrade: fine
        {"id": "m3_brand_new", "status": "planned"},  # union: fine
    ]
    assert status_downgrades(_VOCAB_BEFORE, after, key="id", downgrade_map=VOCAB_DOWNGRADES) == []


def test_dropped_entry_fails() -> None:
    violations = status_downgrades(
        _VOCAB_BEFORE,
        [{"id": "m3_planned_edge", "status": "planned"}],
        key="id",
        downgrade_map=VOCAB_DOWNGRADES,
    )
    assert violations == ["m3_active_edge: entry DROPPED by the merge (was 'active')"]


def test_map_confirmed_and_applied_downgrades_fail() -> None:
    before = [
        {"id": "folder-scheduled-on", "status": "confirmed"},
        {"id": "job-was-informed-by", "status": "applied"},
    ]
    after = [
        {"id": "folder-scheduled-on", "status": "proposed"},
        {"id": "job-was-informed-by", "status": "proposed"},
    ]
    violations = status_downgrades(before, after, key="id", downgrade_map=MAP_DOWNGRADES)
    assert len(violations) == 2 and all("downgraded" in v for v in violations)


def test_backlog_status_regression_fails() -> None:
    """A port that walks a `done` item back to `todo` erases the fact that the
    work happened — the reason backlog.yaml is per-entry and not `evaluate`."""
    before = [
        {"id": "J16", "status": "done"},
        {"id": "L17", "status": "in_progress"},
        {"id": "U1", "status": "todo"},
    ]
    after = [
        {"id": "J16", "status": "todo"},  # the producer's older plan won
        {"id": "L17", "status": "in_progress"},
        {"id": "U1", "status": "done"},  # progress forward: fine
    ]
    violations = status_downgrades(before, after, key="id", downgrade_map=BACKLOG_DOWNGRADES)
    assert violations == ["J16: status downgraded 'done' -> 'todo'"]


def test_backlog_dropped_item_fails() -> None:
    """The other half of per-entry: a whole-file checkout deletes the ids the
    other side added, and nothing else in the port would notice."""
    before = [{"id": "J16", "status": "done"}, {"id": "COMPANY-ONLY", "status": "todo"}]
    after = [{"id": "J16", "status": "done"}]
    violations = status_downgrades(before, after, key="id", downgrade_map=BACKLOG_DOWNGRADES)
    assert violations == ["COMPANY-ONLY: entry DROPPED by the merge (was 'todo')"]


def test_gate_log_append_only_mechanics() -> None:
    before = "# HITL gate log\n\n## 2026-06-21 - C1\n- Confirmed: 4\n"
    appended = before + "\n## 2026-07-11 - new gate\n- Confirmed: 1\n"
    assert append_only_violation(before, appended) is None
    truncated = before[:-10]
    assert "append-only violated" in append_only_violation(before, truncated)
    edited = before.replace("Confirmed: 4", "Confirmed: 3") + "\n## later\n"
    assert "append-only violated" in append_only_violation(before, edited)


def test_current_files_pass_their_own_rules() -> None:
    """Sanity: each real file vs itself is violation-free (loaders + rules wire up)."""
    vocab = yaml_fragments.load_yaml_source(VOCAB_FILE)
    assert (
        status_downgrades(
            vocab_entries(vocab), vocab_entries(vocab), key="id", downgrade_map=VOCAB_DOWNGRADES
        )
        == []
    )
    mapping = yaml_fragments.load_yaml_source(MAP_FILE)
    assert (
        status_downgrades(
            map_entries(mapping), map_entries(mapping), key="id", downgrade_map=MAP_DOWNGRADES
        )
        == []
    )
    backlog = yaml.safe_load(BACKLOG_FILE.read_text(encoding="utf-8"))
    assert (
        status_downgrades(
            backlog_entries(backlog),
            backlog_entries(backlog),
            key="id",
            downgrade_map=BACKLOG_DOWNGRADES,
        )
        == []
    )
    text = GATE_LOG.read_text(encoding="utf-8")
    assert append_only_violation(text, text) is None


# --- consumer-side live comparison (env-gated; the reconcile-port step) -----------

_needs_before = pytest.mark.skipif(
    not os.environ.get(BEFORE_DIR_ENV),
    reason=f"{BEFORE_DIR_ENV} not set — consumer-side reconcile check only",
)


@_needs_before
def test_reconcile_vocab_no_downgrade_live() -> None:
    before_dir = Path(os.environ[BEFORE_DIR_ENV])
    before = yaml.safe_load(
        (before_dir / "relationship_vocabulary.yaml").read_text(encoding="utf-8")
    )
    after = yaml_fragments.load_yaml_source(VOCAB_FILE)
    violations = status_downgrades(
        vocab_entries(before), vocab_entries(after), key="id", downgrade_map=VOCAB_DOWNGRADES
    )
    assert not violations, "\n".join(violations)


@_needs_before
def test_reconcile_map_no_downgrade_live() -> None:
    before_dir = Path(os.environ[BEFORE_DIR_ENV])
    before = yaml.safe_load((before_dir / "taxonomy-ontology-map.yaml").read_text(encoding="utf-8"))
    after = yaml_fragments.load_yaml_source(MAP_FILE)
    violations = status_downgrades(
        map_entries(before), map_entries(after), key="id", downgrade_map=MAP_DOWNGRADES
    )
    assert not violations, "\n".join(violations)


@_needs_before
def test_reconcile_backlog_no_regression_live() -> None:
    before_dir = Path(os.environ[BEFORE_DIR_ENV])
    before = yaml.safe_load((before_dir / "backlog.yaml").read_text(encoding="utf-8"))
    after = yaml.safe_load(BACKLOG_FILE.read_text(encoding="utf-8"))
    violations = status_downgrades(
        backlog_entries(before),
        backlog_entries(after),
        key="id",
        downgrade_map=BACKLOG_DOWNGRADES,
    )
    assert not violations, "\n".join(violations)


@_needs_before
def test_reconcile_gate_log_append_only_live() -> None:
    before_dir = Path(os.environ[BEFORE_DIR_ENV])
    before = (before_dir / "gate-log.md").read_text(encoding="utf-8")
    after = GATE_LOG.read_text(encoding="utf-8")
    violation = append_only_violation(before, after)
    assert violation is None, violation


# --- J16: no tracked path may silently resolve to `default:` ----------------------
#
# The manifest answers "how does THIS path resolve"; nobody had asked the inverse,
# "which paths match no row at all". Those take `default:` — clean-add if absent
# consumer-side — silently, so a deliberate default reads exactly like an oversight.
# It cost real incidents: knowledge/depgraph-snapshots/*.json and docs/port-*.md
# were each instructing the consumer to commit the producer's port INSTRUCTIONS as
# payload, found by accident one at a time, with a prose workaround standing in for
# a missing row for a week. This is test_no_shadow_definitions (C18) applied to port
# dispositions: default-deny, with an allowlist that must carry a reason.
#
# J22 (2026-07-30): the walk also covers untracked-but-not-ignored paths. The J16
# guard walked `git ls-files` only, so a NEW file passed the suite before `git add`
# and failed it after — live incident: the N5 session ran the suite green, committed
# docs/plan/load-map.html, and the very next full run failed this guard. The defect
# window was "on main until someone runs the suite again", which inverts the guard's
# purpose. Same fall-through semantics, wider walk; an untracked orphan has a third
# legitimate resolution the message names (.gitignore it — local-only by intent).


def glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Compile a manifest path glob, anchored.

    ``**`` spans separators, ``*`` and ``?`` do not — so ``drydocs/publishing/**``
    covers the whole subtree while ``docs/*.md`` stays at one level and cannot
    quietly swallow ``docs/decisions/adr.md``. That distinction is the whole point
    of the allowlist's "prefer a narrow pattern" rule; fnmatch would erase it.
    """
    out: list[str] = []
    i = 0
    while i < len(pattern):
        if pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out) + r"\Z")


def resolve_path(path: str, patterns: Iterable[tuple[str, re.Pattern[str]]]) -> str | None:
    """The manifest's own rule: first row whose glob matches wins (top-down).

    Returns the winning pattern, or None when the path falls through to ``default:``.
    """
    for pattern, rx in patterns:
        if rx.match(path):
            return pattern
    return None


def _compiled(entries: Iterable[Mapping[str, Any]]) -> list[tuple[str, re.Pattern[str]]]:
    return [(e["path"], glob_to_regex(e["path"])) for e in entries]


@pytest.fixture(scope="module")
def manifest() -> dict:
    return yaml.safe_load(MANIFEST_FILE.read_text(encoding="utf-8"))


def _git_files(*extra_args: str) -> list[str]:
    try:
        out = subprocess.run(
            ["git", "ls-files", *extra_args],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover
        pytest.skip("git unavailable — the tree cannot be enumerated")
    return [line for line in out.splitlines() if line]


def _tracked_files() -> list[str]:
    return _git_files()


def _untracked_files() -> list[str]:
    """Untracked-but-not-ignored paths — the pre-`git add` view (J22)."""
    return _git_files("--others", "--exclude-standard")


def fall_through_orphans(
    paths: Iterable[str],
    rows: list[tuple[str, re.Pattern[str]]],
    allowed: list[tuple[str, re.Pattern[str]]],
) -> list[str]:
    """Paths resolving to neither a manifest row nor a reasoned default_ok entry."""
    return [p for p in paths if resolve_path(p, rows) is None and resolve_path(p, allowed) is None]


def test_glob_matcher_separator_and_first_match_rules() -> None:
    """Mechanics, pinned separately from the live tree so a matcher regression
    cannot masquerade as a clean manifest."""
    subtree = glob_to_regex("drydocs/publishing/**")
    assert subtree.match("drydocs/publishing/confluence/client.py")
    assert not subtree.match("drydocs/publishing.py")

    one_level = glob_to_regex("docs/*.md")
    assert one_level.match("docs/RELATIONSHIP_GUIDE.md")
    assert not one_level.match("docs/decisions/0002-packaging.md")

    exact = glob_to_regex("PORT-MANIFEST.yaml")
    assert exact.match("PORT-MANIFEST.yaml")
    assert not exact.match("docs/PORT-MANIFEST.yaml")

    # first match wins, top-down — the *.json row above the directory row is the
    # live instance of this (depgraph snapshots: outputs held back, tooling ports)
    ordered = _compiled(
        [
            {"path": "knowledge/depgraph-snapshots/*.json"},
            {"path": "knowledge/depgraph-snapshots/**"},
        ]
    )
    assert (
        resolve_path("knowledge/depgraph-snapshots/drydocs-20260727.json", ordered)
        == "knowledge/depgraph-snapshots/*.json"
    )
    assert (
        resolve_path("knowledge/depgraph-snapshots/snapshot.ps1", ordered)
        == "knowledge/depgraph-snapshots/**"
    )


def test_default_ok_entries_are_well_formed(manifest: dict) -> None:
    """The allowlist is only worth anything if every entry says WHY."""
    entries = manifest.get("default_ok")
    assert entries, "default_ok must exist — it is what makes the guard below meaningful"

    unreasoned = [e["path"] for e in entries if not str(e.get("reason", "")).strip()]
    assert not unreasoned, f"default_ok entries without a reason: {unreasoned}"

    paths = [e["path"] for e in entries]
    assert len(paths) == len(set(paths)), "duplicate default_ok paths"

    # An allowlist entry that shadows a real row is a contradiction: the row already
    # decided, so the entry either does nothing or misleads the next reader.
    row_paths = {r["path"] for r in manifest["rows"]}
    both = sorted(set(paths) & row_paths)
    assert not both, f"paths in BOTH rows and default_ok — the row already decides: {both}"


def test_git_readme_decision_is_recorded(manifest: dict) -> None:
    """Regression pin: the one entry that exists to record a DECISION rather than
    to excuse an oversight. Before J16 it lived only in the idea inbox."""
    entry = next((e for e in manifest["default_ok"] if e["path"] == "git-readme.md"), None)
    assert entry is not None, "the git-readme.md standing decision must stay written down"
    assert "deliberately uncovered" in entry["reason"]


def test_untracked_new_file_is_caught_before_add() -> None:
    """J22 mechanics pin: a brand-new path with no disposition is an orphan in the
    pre-commit view already — same fall-through semantics as the tracked walk —
    while dispositioned or allowlisted paths stay clean (no false positives)."""
    rows = _compiled([{"path": "docs/plan/*.html"}])
    allowed = _compiled([{"path": "scratch-*.txt"}])

    # dispositioned path: clean, tracked or not
    assert fall_through_orphans(["docs/plan/board.html"], rows, allowed) == []
    # the N5 shape: a NEW sibling with no row is caught NOW, not one commit later
    assert fall_through_orphans(["docs/plan/new-surface.json"], rows, allowed) == [
        "docs/plan/new-surface.json"
    ]
    # an allowlisted transient resolves — the reasoned-entry route, not silence
    assert fall_through_orphans(["scratch-notes.txt"], rows, allowed) == []


def test_no_tracked_path_falls_through_silently(manifest: dict) -> None:
    """Every tracked AND untracked-but-not-ignored path resolves to a row, or to an
    allowlist entry that says why the default is right. Nothing resolves to
    `default:` by silence — and nothing waits for `git add` to be asked (J22)."""
    rows = _compiled(manifest["rows"])
    allowed = _compiled(manifest["default_ok"])

    untracked = set(_untracked_files())
    orphans = fall_through_orphans([*_tracked_files(), *untracked], rows, allowed)
    assert not orphans, (
        f"{len(orphans)} path(s) resolve to PORT-MANIFEST `default:` with nothing "
        "written down. Decide each one: add a row (it needs a real disposition), a "
        "default_ok entry with a reason (the default is right and here is why) — "
        "or, for an [untracked] path that is local-only by intent, .gitignore it.\n  "
        + "\n  ".join(f"{p} [untracked]" if p in untracked else p for p in sorted(orphans)[:40])
    )
