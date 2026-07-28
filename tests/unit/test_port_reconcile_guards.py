"""J7 — executable per-entry port reconciler guards (PORT-MANIFEST entry_rules).

The manifest's `per-entry` rows carry prose entry_rules; these are those rules as
code (docs/reviews/tech-debt-port-boundary.md Phase 2). Same YAML loading idiom
as the map guard (pytest + yaml.safe_load) — no second parser.

Three rules:

* **Status no-downgrade** — a merge may never downgrade
  relationship_vocabulary.yaml ``active`` → planned/deprecated/removed, nor
  taxonomy-ontology-map.yaml ``confirmed``/``applied`` → proposed; and a
  consumer entry may never simply VANISH (per-entry means union of entries).
* **Append-only** — union-append audit files (config/gate-log.md): the
  pre-merge text must be a byte prefix of the merged text.
* **Version-string rule** — asserted in test_port_manifest.py (the manifest row
  itself is the contract).

Consumer-side usage during reconcile-port (documented in that skill):

    1. BEFORE applying the port, snapshot the consumer copies:
         mkdir %TEMP%/reconcile-before
         cp drydocs_core/ontology/relationship_vocabulary.yaml \
            config/taxonomy-ontology-map.yaml config/gate-log.md  <before-dir>/
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
from pathlib import Path
from typing import Any, Iterable, Mapping

import pytest

yaml = pytest.importorskip("yaml")

REPO = Path(__file__).resolve().parents[2]
MANIFEST_FILE = REPO / "PORT-MANIFEST.yaml"
VOCAB_FILE = REPO / "drydocs_core" / "ontology" / "relationship_vocabulary.yaml"
MAP_FILE = REPO / "config" / "taxonomy-ontology-map.yaml"
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
            violations.append(
                f"{k}: status downgraded {status!r} -> {merged.get(status_field)!r}"
            )
    return violations


def append_only_violation(before_text: str, after_text: str) -> str | None:
    """None if ``before_text`` is a byte prefix of ``after_text``; else a message."""
    if after_text.startswith(before_text):
        return None
    limit = min(len(before_text), len(after_text))
    at = next(
        (i for i in range(limit) if before_text[i] != after_text[i]), limit
    )
    return (
        f"append-only violated: merged file diverges from the pre-merge text at "
        f"char {at} (existing entries must be a prefix — dropping or editing "
        "either side's audit entries is an audit violation)"
    )


def vocab_entries(doc: dict) -> list[dict]:
    return doc["local_relationships"]


def map_entries(doc: dict) -> list[dict]:
    return doc["mappings"]


# --- fixture-driven mechanics (run everywhere) ------------------------------------

_VOCAB_BEFORE = [
    {"id": "m3_active_edge", "status": "active"},
    {"id": "m3_planned_edge", "status": "planned"},
]


def test_vocab_active_downgrade_fails() -> None:
    after = [
        {"id": "m3_active_edge", "status": "planned"},   # producer clobbered it
        {"id": "m3_planned_edge", "status": "planned"},
    ]
    violations = status_downgrades(
        _VOCAB_BEFORE, after, key="id", downgrade_map=VOCAB_DOWNGRADES
    )
    assert violations == ["m3_active_edge: status downgraded 'active' -> 'planned'"]


def test_vocab_upgrade_and_new_entries_pass() -> None:
    after = [
        {"id": "m3_active_edge", "status": "active"},
        {"id": "m3_planned_edge", "status": "active"},    # upgrade: fine
        {"id": "m3_brand_new", "status": "planned"},      # union: fine
    ]
    assert status_downgrades(
        _VOCAB_BEFORE, after, key="id", downgrade_map=VOCAB_DOWNGRADES
    ) == []


def test_dropped_entry_fails() -> None:
    violations = status_downgrades(
        _VOCAB_BEFORE, [{"id": "m3_planned_edge", "status": "planned"}],
        key="id", downgrade_map=VOCAB_DOWNGRADES,
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
    vocab = yaml.safe_load(VOCAB_FILE.read_text(encoding="utf-8"))
    assert status_downgrades(
        vocab_entries(vocab), vocab_entries(vocab), key="id", downgrade_map=VOCAB_DOWNGRADES
    ) == []
    mapping = yaml.safe_load(MAP_FILE.read_text(encoding="utf-8"))
    assert status_downgrades(
        map_entries(mapping), map_entries(mapping), key="id", downgrade_map=MAP_DOWNGRADES
    ) == []
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
    after = yaml.safe_load(VOCAB_FILE.read_text(encoding="utf-8"))
    violations = status_downgrades(
        vocab_entries(before), vocab_entries(after), key="id", downgrade_map=VOCAB_DOWNGRADES
    )
    assert not violations, "\n".join(violations)


@_needs_before
def test_reconcile_map_no_downgrade_live() -> None:
    before_dir = Path(os.environ[BEFORE_DIR_ENV])
    before = yaml.safe_load(
        (before_dir / "taxonomy-ontology-map.yaml").read_text(encoding="utf-8")
    )
    after = yaml.safe_load(MAP_FILE.read_text(encoding="utf-8"))
    violations = status_downgrades(
        map_entries(before), map_entries(after), key="id", downgrade_map=MAP_DOWNGRADES
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


def _tracked_files() -> list[str]:
    try:
        out = subprocess.run(
            ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover
        pytest.skip("git unavailable — the tracked tree cannot be enumerated")
    return [line for line in out.splitlines() if line]


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
    ordered = _compiled([
        {"path": "knowledge/depgraph-snapshots/*.json"},
        {"path": "knowledge/depgraph-snapshots/**"},
    ])
    assert resolve_path("knowledge/depgraph-snapshots/drydocs-20260727.json", ordered) == \
        "knowledge/depgraph-snapshots/*.json"
    assert resolve_path("knowledge/depgraph-snapshots/snapshot.ps1", ordered) == \
        "knowledge/depgraph-snapshots/**"


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
    entry = next(
        (e for e in manifest["default_ok"] if e["path"] == "git-readme.md"), None
    )
    assert entry is not None, "the git-readme.md standing decision must stay written down"
    assert "deliberately uncovered" in entry["reason"]


def test_no_tracked_path_falls_through_silently(manifest: dict) -> None:
    """Every tracked path resolves to a row, or to an allowlist entry that says why
    the default is right. Nothing resolves to `default:` by silence."""
    rows = _compiled(manifest["rows"])
    allowed = _compiled(manifest["default_ok"])

    orphans = [
        p for p in _tracked_files()
        if resolve_path(p, rows) is None and resolve_path(p, allowed) is None
    ]
    assert not orphans, (
        f"{len(orphans)} tracked path(s) resolve to PORT-MANIFEST `default:` with "
        "nothing written down. Decide each one: add a row (it needs a real "
        "disposition) or a default_ok entry with a reason (the default is right "
        f"and here is why).\n  " + "\n  ".join(sorted(orphans)[:40])
    )
