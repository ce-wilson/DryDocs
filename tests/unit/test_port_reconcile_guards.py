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

    1. BEFORE applying the port, snapshot the consumer copies — ALL FOUR; each
       live check below reads one, and a missing file fails the run:
         mkdir %TEMP%/reconcile-before
         python -c "from pathlib import Path; from drydocs_core import backlog_store, yaml_fragments as yf; \
            Path('<before-dir>/relationship_vocabulary.yaml').write_text(yf.merged_text('drydocs_core/ontology/relationship_vocabulary'), encoding='utf-8'); \
            Path('<before-dir>/taxonomy-ontology-map.yaml').write_text(yf.merged_text('config/taxonomy-ontology-map'), encoding='utf-8')"
         poetry run python -c "from drydocs_core.backlog_store import dump_document as d; print(d(), end='')" > <before-dir>/backlog.yaml
         cp config/gate-log.md  <before-dir>/
       (S5: both registries are fragment DIRECTORIES now — the snapshot is the
       MERGED document, so the before/after comparison stays file-shaped.)
    2. Apply the port range / resolve collisions.
    3. RECONCILE_BEFORE_DIR=<before-dir> pytest tests/unit/test_port_reconcile_guards.py -q
       → FAILS on any downgrade / dropped entry / audit truncation the merge introduced.
    4. AFTER the reconcile, CLEAR the variable and drop the snapshot dir. Nothing
       else does — and the variable outliving its before-dir is what makes the
       next unrelated run in that shell report four broken-looking failures.

With RECONCILE_BEFORE_DIR UNSET the live-comparison tests SKIP; the fixture-driven
mechanics tests run everywhere (producer CI included). Set-but-unusable is NOT a
skip — see ``before_text`` for why it fails loudly instead.
"""

from __future__ import annotations

import os
import re
import subprocess
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import pytest

from drydocs_core import backlog_store, yaml_fragments

yaml = pytest.importorskip("yaml")

REPO = Path(__file__).resolve().parents[2]
MANIFEST_FILE = REPO / "PORT-MANIFEST.yaml"
VOCAB_FILE = REPO / "drydocs_core" / "ontology" / "relationship_vocabulary"
MAP_FILE = REPO / "config" / "taxonomy-ontology-map"
BACKLOG_TREE = (
    REPO / "docs" / "restructure" / "backlog"
)  # sharded (ADR 0013); read through the store
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
    backlog = backlog_store.load_backlog_document(BACKLOG_TREE)
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

# The four snapshots step 1 copies; named here so a missing one is reported as the
# operator's next action rather than as a FileNotFoundError traceback.
BEFORE_SNAPSHOTS = (
    "relationship_vocabulary.yaml",
    "taxonomy-ontology-map.yaml",
    "backlog.yaml",  # since ADR 0013: the ASSEMBLED tree, written by backlog_store.dump_document()
    "gate-log.md",
)


def before_text(name: str) -> str:
    """Read one snapshot out of <before-dir>, or fail saying what to do about it.

    UNSET skips (``_needs_before``); set-but-unusable FAILS. The asymmetry is the
    point. A set ``RECONCILE_BEFORE_DIR`` is a claim that a reconcile is in
    progress and its guard is armed — so the two ways that claim can be false
    need opposite treatment. Skipping a set-but-broken snapshot would silently
    drop the port's own safety check while the run still reports green, which is
    the J16/J22 default-deny failure exactly ("a deliberate default reads exactly
    like an oversight").

    What this replaces: the variable outlives the reconcile session — nothing in
    the runbook cleared it until step 4 was added — the before-dir gets cleaned
    up, and the next unrelated ``pytest`` in that shell raises FileNotFoundError
    from four tests at once. That reads as four broken guards, and it cost a real
    session the time to prove otherwise. Same failure, named at its cause.
    """
    before_dir = Path(os.environ[BEFORE_DIR_ENV])
    if not before_dir.is_dir():
        pytest.fail(
            f"{BEFORE_DIR_ENV} is set to {before_dir}, which is not a directory. "
            "Either re-snapshot it (reconcile-port step 1) or clear the variable "
            "— a stale value left over from an earlier reconcile makes every "
            "later run in this shell look broken."
        )
    snapshot = before_dir / name
    if not snapshot.is_file():
        pytest.fail(
            f"{BEFORE_DIR_ENV} points at {before_dir}, which has no {name}. "
            f"Step 1 must copy all four: {', '.join(BEFORE_SNAPSHOTS)}."
        )
    return snapshot.read_text(encoding="utf-8")


@_needs_before
def test_reconcile_vocab_no_downgrade_live() -> None:
    before = yaml.safe_load(before_text("relationship_vocabulary.yaml"))
    # S5: VOCAB_FILE is a fragment DIRECTORY — the snapshot stays file-shaped,
    # the live side must merge the fragments.
    after = yaml_fragments.load_yaml_source(VOCAB_FILE)
    violations = status_downgrades(
        vocab_entries(before), vocab_entries(after), key="id", downgrade_map=VOCAB_DOWNGRADES
    )
    assert not violations, "\n".join(violations)


@_needs_before
def test_reconcile_map_no_downgrade_live() -> None:
    before = yaml.safe_load(before_text("taxonomy-ontology-map.yaml"))
    # S5: MAP_FILE is a fragment DIRECTORY (see the vocab twin above).
    after = yaml_fragments.load_yaml_source(MAP_FILE)
    violations = status_downgrades(
        map_entries(before), map_entries(after), key="id", downgrade_map=MAP_DOWNGRADES
    )
    assert not violations, "\n".join(violations)


@_needs_before
def test_reconcile_backlog_no_regression_live() -> None:
    before = yaml.safe_load(before_text("backlog.yaml"))
    after = backlog_store.load_backlog_document(BACKLOG_TREE)
    violations = status_downgrades(
        backlog_entries(before),
        backlog_entries(after),
        key="id",
        downgrade_map=BACKLOG_DOWNGRADES,
    )
    assert not violations, "\n".join(violations)


@_needs_before
def test_reconcile_gate_log_append_only_live() -> None:
    before = before_text("gate-log.md")
    after = GATE_LOG.read_text(encoding="utf-8")
    violation = append_only_violation(before, after)
    assert violation is None, violation


# --- J51 (2026-08-20): list-shaped per-entry rows — "never drop a name" as code ---------
# Two of the six J51 rows govern Python files whose entries are LISTS the company
# extends: drydocs_remediation/detect.py (CONFORMANCE_RULE_IDS + the DPL-* ids the
# company appends) and tests/unit/test_runbook_currency.py (the three exemption
# tables, keyed by path / verb). The rule is no-drop by key. The before-snapshots
# are OPTIONAL (the four above stay the mandatory contract): step 1 may write
# `detect-rule-ids.txt` and `runbook-exemption-keys.txt` into <before-dir>; when
# present, the live checks compare; when absent, they skip and say how to arm them.


def dropped_names(before: Iterable[str], after: Iterable[str]) -> list[str]:
    """Names present before the merge and absent after it — the per-entry violation."""
    after_set = set(after)
    return sorted(n for n in before if n not in after_set)


def detect_rule_ids() -> list[str]:
    from drydocs_remediation import detect

    return list(detect.CONFORMANCE_RULE_IDS)


def runbook_exemption_keys() -> list[str]:
    import importlib

    mod = importlib.import_module("tests.unit.test_runbook_currency")
    keys: list[str] = []
    for table in ("HISTORICAL_PATHS", "FOREIGN_PATHS", "DEFERRED_VERBS"):
        keys += [f"{table}:{k}" for k in sorted(getattr(mod, table, {}) or {})]
    return keys


def test_dropped_names_mechanics() -> None:
    assert dropped_names(["R2", "R30", "DPL-1"], ["R2", "R30", "R31"]) == ["DPL-1"]
    assert dropped_names(["R2"], ["R2", "R99"]) == []


def test_list_shaped_rows_read_their_live_lists() -> None:
    """The two lists the J51 rows govern are importable and non-empty — the live
    checks below would otherwise pass vacuously on an import error."""
    assert "R30" in detect_rule_ids()
    keys = runbook_exemption_keys()
    assert any(k.startswith("HISTORICAL_PATHS:") for k in keys)


def _optional_before(name: str) -> list[str] | None:
    before_dir = os.environ.get(BEFORE_DIR_ENV)
    if not before_dir:
        return None
    path = Path(before_dir) / name
    if not path.is_file():
        pytest.skip(
            f"{name} not in {BEFORE_DIR_ENV} — optional J51 snapshot; arm it in step 1 by "
            "writing the pre-merge list there, one name per line"
        )
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


@_needs_before
def test_reconcile_detect_rule_ids_no_drop_live() -> None:
    before = _optional_before("detect-rule-ids.txt")
    dropped = dropped_names(before or [], detect_rule_ids())
    assert not dropped, f"detect.py rule ids DROPPED by the merge: {dropped}"


@_needs_before
def test_reconcile_runbook_exemptions_no_drop_live() -> None:
    before = _optional_before("runbook-exemption-keys.txt")
    dropped = dropped_names(before or [], runbook_exemption_keys())
    assert not dropped, f"test_runbook_currency exemption keys DROPPED by the merge: {dropped}"


# --- before_text mechanics (run everywhere; these are what UNSET-vs-BROKEN means) --


def test_before_text_reads_a_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "gate-log.md").write_text("# HITL gate log\n", encoding="utf-8")
    monkeypatch.setenv(BEFORE_DIR_ENV, str(tmp_path))
    assert before_text("gate-log.md") == "# HITL gate log\n"


def test_before_text_missing_dir_says_resnapshot_or_clear(monkeypatch: pytest.MonkeyPatch) -> None:
    """The stale-variable case: fail, and name both ways out.

    Previously a FileNotFoundError from four tests at once — indistinguishable
    from four genuinely broken guards.
    """
    monkeypatch.setenv(BEFORE_DIR_ENV, str(REPO / "__no_such_before_dir__"))
    # pytest.fail raises Failed, which subclasses BaseException — `Exception` misses it.
    with pytest.raises(pytest.fail.Exception, match="not a directory") as exc:
        before_text("gate-log.md")
    assert "clear the variable" in str(exc.value)


def test_before_text_missing_file_names_all_four(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An INCOMPLETE snapshot is the other half — the docstring's step 1 omitted
    backlog.yaml, so following it literally produced this exact failure."""
    monkeypatch.setenv(BEFORE_DIR_ENV, str(tmp_path))
    with pytest.raises(pytest.fail.Exception, match="has no backlog.yaml") as exc:
        before_text("backlog.yaml")
    for name in BEFORE_SNAPSHOTS:
        assert name in str(exc.value)


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


def union_overlays(manifest: dict, repo: Path = REPO) -> dict:
    """The J34 overlay seam: union each declared, EXISTING side-local overlay
    into the manifest view the guards run against.

    Overlay rows append AFTER the manifest's rows (first match wins, so the
    producer manifest's dispositions keep precedence — an overlay adds
    coverage, never overrides authority) and default_ok entries union;
    ``row_may_match_nothing`` entries union the same way, so each side can
    excuse its own deliberately-dead rows without touching the other's file.
    The returned dict is a new view; the input is not mutated. Because an overlay
    lives OUTSIDE PORT-MANIFEST.yaml, a producer-manifest-verbatim apply
    structurally cannot drop its rows — the property the seam exists for
    (PORT-REPORT-a14a8028: 89 company-only default_ok paths dropped by a
    wholesale take).
    """
    view = {
        **manifest,
        "rows": list(manifest.get("rows", [])),
        "default_ok": list(manifest.get("default_ok", [])),
        "row_may_match_nothing": list(manifest.get("row_may_match_nothing", [])),
    }
    for declared in (manifest.get("overlay") or {}).get("files", []):
        overlay_file = repo / declared["path"]
        if not overlay_file.exists():
            continue  # the other side's slot — absent here by design
        overlay = yaml.safe_load(overlay_file.read_text(encoding="utf-8")) or {}
        view["rows"].extend(overlay.get("rows", []))
        view["default_ok"].extend(overlay.get("default_ok", []))
        view["row_may_match_nothing"].extend(overlay.get("row_may_match_nothing", []))
    return view


@pytest.fixture(scope="module")
def manifest() -> dict:
    return union_overlays(yaml.safe_load(MANIFEST_FILE.read_text(encoding="utf-8")))


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


# --- Phase C prerequisite: the INVERSE of J16 — rows that match no path -----------
#
# J16 above asks "which paths match no row". Nobody had asked the mirror question,
# "which rows match no path" — and an unmatched row is the more dangerous half,
# because it fails SILENTLY in the wrong direction: the paths it was written to
# govern do not go ungoverned, they fall through to whatever broader row catches
# them next. Usually that is the generic `evaluate` row, so a canonical-producer
# or never-port intent quietly degrades to hand-merge-on-collision with no error.
#
# Live instance: `drydocs_core/controlm/**` (canonical-producer) pointed at a path
# that had not existed since the S2 / ADR 0008 relocate under `orchestration/`. The
# whole orchestration package fell through to `drydocs_core/**` evaluate for months
# and was caught by hand at G75/G76 (2026-08-11), not by any guard.
#
# The Phase B core relocate (ADR 0002-a-1) avoided this only because the rows were
# re-pathed in the SAME commit as the 42 renames — the "path-column diff" the
# manifest header promised. That discipline was remembered, never enforced. Phase C
# (the deferred 4-component split of the `drydocs` remainder) is the biggest rename
# wave still ahead, which is what makes this guard its prerequisite rather than a
# nice-to-have: after Phase C moves files, a row left on a pre-split path FAILS.
#
# Deliberately-dead rows are real and legitimate — a company-only module, a
# side-local overlay slot, a gitignored zone, a one-time cross-side migration
# instruction — so this is default-deny with a reasoned allowlist, the same shape
# as default_ok and as test_no_shadow_definitions (C18).


def dead_rows(
    rows: Iterable[Mapping[str, Any]],
    paths: Iterable[str],
    allowed: list[tuple[str, re.Pattern[str]]],
) -> list[str]:
    """Row paths matching nothing in ``paths`` and not excused by ``allowed``."""
    population = list(paths)
    out: list[str] = []
    for row in rows:
        pattern = row["path"]
        rx = glob_to_regex(pattern)
        if any(rx.match(p) for p in population):
            continue
        if resolve_path(pattern, allowed) is not None:
            continue
        out.append(pattern)
    return out


def test_dead_row_mechanics() -> None:
    """Mechanics on fixtures, pinned away from the live tree so a matcher
    regression cannot masquerade as a clean manifest (the J16 idiom)."""
    paths = ["drydocs_core/orchestration/controlm/shell.py", "drydocs/loaders/catalog.py"]
    rows = [
        {"path": "drydocs_core/orchestration/**"},  # matches
        {"path": "drydocs_core/controlm/**"},  # THE G75/G76 defect: pre-relocate path
    ]
    assert dead_rows(rows, paths, []) == ["drydocs_core/controlm/**"]

    # an allowlisted row resolves — the reasoned-entry route, not silence
    excused = _compiled([{"path": "drydocs_core/controlm/**"}])
    assert dead_rows(rows, paths, excused) == []

    # the allowlist is matched as a glob too, so one entry can excuse a family
    family = _compiled([{"path": "PORT-MANIFEST.*.yaml"}])
    assert dead_rows([{"path": "PORT-MANIFEST.company.yaml"}], paths, family) == []


def test_row_may_match_nothing_entries_are_well_formed(manifest: dict) -> None:
    """The allowlist is only worth anything if every entry says WHY."""
    entries = manifest.get("row_may_match_nothing")
    assert entries, (
        "row_may_match_nothing must exist — it is what makes the guard below "
        "meaningful (an unreasoned exemption is the silence it replaces)"
    )
    for entry in entries:
        assert entry.get("path"), f"entry without a path: {entry}"
        reason = (entry.get("reason") or "").strip()
        assert len(reason) > 20, f"{entry.get('path')}: reason is mandatory and must be specific"


def test_no_manifest_row_matches_nothing(manifest: dict) -> None:
    """Every row governs at least one real path, or is allowlisted with a reason.

    A row matching nothing is unenforced: its paths silently resolve to the next
    broader row instead. This is what rotted `drydocs_core/controlm/**` across the
    S2 relocate, and it is the failure Phase C's rename wave would reproduce at
    scale.
    """
    allowed = _compiled(manifest["row_may_match_nothing"])
    population = [*_tracked_files(), *_untracked_files()]
    dead = dead_rows(manifest["rows"], population, allowed)
    assert not dead, (
        f"{len(dead)} PORT-MANIFEST row(s) match no path on this side, so they are "
        "unenforced — the paths they were written to govern fall through to the next "
        "broader row (usually the generic `evaluate`). If the files MOVED, re-path the "
        "row in the same commit as the move (the path-column diff rule). If matching "
        "nothing is intended, add a row_may_match_nothing entry with a reason.\n  "
        + "\n  ".join(sorted(dead))
    )


# --- J34: the overlay seam — side-local rows a verbatim apply cannot drop ---------
#
# PORT-REPORT-a14a8028 (2026-08-06): a producer-manifest-verbatim take dropped the
# company's default_ok block — 89 company-only paths fell through their own J16
# guard. The fix is structural, not procedural: side-local rows live in an overlay
# FILE the guards union in (union_overlays above), so replacing PORT-MANIFEST.yaml
# wholesale cannot touch them. These tests prove the mechanism with fixtures; the
# company's real overlay is company-tracked and absent producer-side by design.

_PRODUCER_MANIFEST_V1 = {
    "overlay": {"files": [{"path": "PORT-MANIFEST.company.yaml", "side": "company"}]},
    "rows": [{"path": "drydocs/loaders/**", "disposition": "canonical-producer"}],
    "default_ok": [{"path": "README.md", "reason": "each repo's own front door"}],
}

# a later producer edition — different rows, same overlay declaration; what a
# verbatim apply installs over the consumer's copy
_PRODUCER_MANIFEST_V2 = {
    "overlay": {"files": [{"path": "PORT-MANIFEST.company.yaml", "side": "company"}]},
    "rows": [
        {"path": "drydocs/loaders/**", "disposition": "canonical-producer"},
        {"path": "docs/style/**", "disposition": "canonical-producer"},
    ],
    "default_ok": [{"path": "README.md", "reason": "each repo's own front door"}],
}

_COMPANY_OVERLAY = (
    "rows:\n"
    '  - path: "docs/site/**"\n'
    "    disposition: canonical-company\n"
    '    note: "company-only docs site"\n'
    "default_ok:\n"
    '  - path: "PORT-REPORT-*.md"\n'
    '    reason: "company port artifacts — theirs by construction"\n'
)


def test_overlay_rows_survive_producer_manifest_verbatim_apply(tmp_path: Path) -> None:
    """THE ACCEPTANCE PROOF: replacing the producer manifest wholesale (v1 -> v2,
    the verbatim apply) cannot drop a company overlay row, because the row was
    never in the file that was replaced."""
    (tmp_path / "PORT-MANIFEST.company.yaml").write_text(_COMPANY_OVERLAY, encoding="utf-8")

    for edition in (_PRODUCER_MANIFEST_V1, _PRODUCER_MANIFEST_V2):
        view = union_overlays(edition, repo=tmp_path)
        rows = _compiled(view["rows"])
        allowed = _compiled(view["default_ok"])
        # the company-only row resolves in BOTH editions — before and after the apply
        assert resolve_path("docs/site/index.html", rows) == "docs/site/**"
        assert resolve_path("PORT-REPORT-20260806.md", allowed) == "PORT-REPORT-*.md"

    # and the union is a view: the producer manifest dict itself is untouched
    assert len(_PRODUCER_MANIFEST_V2["rows"]) == 2


def test_overlay_precedence_producer_rows_win(tmp_path: Path) -> None:
    """Overlay rows append AFTER the manifest's rows: first match wins, so an
    overlay can add coverage but never override a producer disposition."""
    (tmp_path / "PORT-MANIFEST.company.yaml").write_text(
        "rows:\n"
        '  - path: "drydocs/loaders/**"\n'
        "    disposition: canonical-company\n"
        '    note: "an overlay may not seize this — the producer row must win"\n',
        encoding="utf-8",
    )
    view = union_overlays(_PRODUCER_MANIFEST_V1, repo=tmp_path)
    rows = _compiled(view["rows"])
    winner = next(
        r for r in view["rows"] if r["path"] == resolve_path("drydocs/loaders/base.py", rows)
    )
    assert winner["disposition"] == "canonical-producer"


def test_missing_overlay_is_a_clean_noop() -> None:
    """The other side's slot is absent by design — the union must not invent
    rows, fail, or mutate anything (producer-side runs hit this path always)."""
    view = union_overlays(_PRODUCER_MANIFEST_V1, repo=Path("does/not/exist"))
    assert view["rows"] == _PRODUCER_MANIFEST_V1["rows"]
    assert view["default_ok"] == _PRODUCER_MANIFEST_V1["default_ok"]


def test_live_overlay_declaration_is_well_formed(manifest: dict) -> None:
    """The real manifest declares BOTH side slots (Idea-41: the grammar must be
    able to express a producer-local file), each overlay path is itself covered
    by a never-port row, and no live overlay row duplicates a manifest row
    (a duplicate silently loses to first-match-wins — a guard error, not a
    quiet loser)."""
    raw = yaml.safe_load(MANIFEST_FILE.read_text(encoding="utf-8"))
    declared = (raw.get("overlay") or {}).get("files", [])
    assert {d["side"] for d in declared} == {"company", "producer"}

    rows = _compiled(raw["rows"])
    for d in declared:
        assert resolve_path(d["path"], rows) == "PORT-MANIFEST.*.yaml", (
            f"{d['path']}: every overlay file must resolve to the never-port row — "
            "side-local files never cross the boundary"
        )

    # duplicate-path check across the union (the manifest fixture IS the union)
    paths = [r["path"] for r in manifest["rows"]]
    dupes = sorted({p for p in paths if paths.count(p) > 1})
    assert (
        not dupes
    ), f"overlay row(s) duplicate a manifest row — first-match-wins hides them: {dupes}"
