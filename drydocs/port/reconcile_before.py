"""reconcile_before.py — the reconcile-port BEFORE-snapshot, stamped with the sha it describes.

The per-entry guards in ``tests/unit/test_port_reconcile_guards.py`` compare a
before-dir (the consumer's copies, taken before the apply) against the live tree.
Until 2026-09-05 the before-dir carried no record of WHEN it was taken. Two
failures came from that in one apply (the company's ``port-base-20260902..
20260905``, transcribed machine-local and reviewed the same day):

* a before-dir survived a skipped teardown (runbook step 4) into the NEXT apply,
  and its stale snapshot produced a 22nd baseline failure that was an INSTRUMENT
  fault — J76 says check the instrument before the subject, and the instrument
  had nothing on it to check;
* the runbook's step 1 was six one-liners, so a partly-run step 1 was a partly
  armed guard, and nothing said which half ran.

So the snapshot is now ONE call that writes every file AND a stamp,
``BASE.sha`` — the commit the consumer tree was at — and the guards refuse a
before-dir whose stamp is missing, does not resolve in this repository, is not
an ancestor of ``HEAD``, disagrees with the tree it names (the ``gate-log.md``
snapshot must byte-equal ``git show <sha>:config/gate-log.md``), or is not where
the apply branch left main. :func:`describe` prints the one line the PORT-REPORT
must carry — sha, date, commits behind ``HEAD`` — so a stale before-dir is
VISIBLE in the report even where a guard cannot tell (an apply made directly on
the trunk has no fork point, and a stale dir IS an ancestor; only the distance
gives it away).

The writer refuses a dirty source: a snapshot taken over an uncommitted edit to
one of the four files describes no commit, and a stamp on it would be a lie.

Pure functions take TEXT and FACTS; only the git-backed functions shell out (the
``port_preflight.py`` idiom, so the mechanics tests run without a repository).
"""

from __future__ import annotations

import importlib
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from drydocs_core import yaml_fragments
from drydocs_core.backlog_store import dump_document

#: The stamp file — one line, the full 40-hex sha of the consumer commit snapshotted.
STAMP_FILE = "BASE.sha"

#: The four mandatory snapshots (mirrors BEFORE_SNAPSHOTS in the guard module).
MANDATORY = (
    "relationship_vocabulary.yaml",
    "taxonomy-ontology-map.yaml",
    "backlog.yaml",
    "gate-log.md",
)

#: The two optional J51 list-shaped snapshots; written when their modules import.
OPTIONAL = ("detect-rule-ids.txt", "runbook-exemption-keys.txt")

#: The tracked sources the four mandatory snapshots derive from — the dirty check.
SOURCES = (
    "config/gate-log.md",
    "docs/restructure/backlog",
    "drydocs_core/ontology/relationship_vocabulary",
    "config/taxonomy-ontology-map",
)

_SHA = re.compile(r"^[0-9a-f]{40}$")


class ReconcileBeforeError(RuntimeError):
    """The snapshot could not be taken — nothing was written."""


@dataclass
class SnapshotReport:
    before_dir: Path
    sha: str
    written: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)  # optional files whose module did not import

    def lines(self) -> list[str]:
        out = [f"before-dir {self.before_dir}: {STAMP_FILE} {self.sha[:8]}"]
        out += [f"  wrote   {name}" for name in self.written]
        out += [
            f"  skipped {name} (optional J51 snapshot; its module did not import here)"
            for name in self.skipped
        ]
        return out


# --- pure -----------------------------------------------------------------------------


def parse_stamp(text: str | None) -> str | None:
    """The sha a stamp file carries, or None when there is no usable stamp.

    ``None`` in means the file was absent (a before-dir that predates the stamp or
    was hand-built); a present file that is not one 40-hex line is the same answer,
    because a stamp that cannot be resolved protects nothing.
    """
    if text is None or not text.strip():
        return None
    line = text.strip().splitlines()[0].strip()
    return line if _SHA.match(line) else None


def stamp_problems(
    stamp: str | None,
    *,
    resolves: bool,
    is_ancestor: bool,
    gate_log_matches: bool,
    fork_point: str | None = None,
) -> list[str]:
    """Every way a before-dir's stamp can fail to describe the tree under comparison.

    The keyword inputs are FACTS the caller established with git; this function
    only names the failures, so the wording is testable without a repository. An
    empty list means the stamp is trustworthy. ``fork_point`` is where the current
    branch left main, or None when there is no such point to compare against.
    """
    if stamp is None:
        return [
            f"{STAMP_FILE} is missing or unreadable: this before-dir predates the stamp "
            "or was hand-built. Re-snapshot it with scripts/reconcile_before.py."
        ]
    if not resolves:
        return [
            f"{STAMP_FILE} {stamp[:8]} does not resolve in this repository: the before-dir "
            "was taken in another checkout or on another machine. Re-snapshot it here."
        ]
    problems: list[str] = []
    if not is_ancestor:
        problems.append(
            f"{STAMP_FILE} {stamp[:8]} is not an ancestor of HEAD: the tree under comparison "
            "did not grow out of the snapshotted one. Re-snapshot it from the branch base."
        )
    if not gate_log_matches:
        problems.append(
            f"gate-log.md in the before-dir differs from git show {stamp[:8]}:config/gate-log.md: "
            "the snapshot was edited, or taken over an uncommitted change. Re-snapshot it."
        )
    if fork_point is not None and fork_point != stamp:
        problems.append(
            f"{STAMP_FILE} {stamp[:8]} is not where this branch left main ({fork_point[:8]}): "
            "a before-dir from an EARLIER apply outlived its teardown (runbook step 4). "
            "Re-snapshot it at the branch base."
        )
    return problems


# --- git-backed -------------------------------------------------------------------------


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8"
    )


def head_sha(repo: Path) -> str:
    proc = git(repo, "rev-parse", "HEAD")
    if proc.returncode != 0:
        raise ReconcileBeforeError(f"not a git repository, or no HEAD: {repo}\n{proc.stderr}")
    return proc.stdout.strip()


def dirty_sources(repo: Path) -> list[str]:
    proc = git(repo, "status", "--porcelain", "--", *SOURCES)
    if proc.returncode != 0:
        raise ReconcileBeforeError(f"git status failed in {repo}\n{proc.stderr}")
    return [ln for ln in proc.stdout.splitlines() if ln.strip()]


def write_snapshot(before_dir: Path, repo: Path) -> SnapshotReport:
    """Write the four mandatory snapshots, the optional two where importable, and the stamp.

    Refuses (raises, writes nothing) when a source is dirty: the stamp names a
    commit, and a snapshot that includes an uncommitted edit is not that commit.
    """
    dirty = dirty_sources(repo)
    if dirty:
        raise ReconcileBeforeError(
            "the snapshot sources have uncommitted changes, so no stamp would be true — "
            "commit or discard them first:\n  " + "\n  ".join(dirty)
        )
    sha = head_sha(repo)
    before_dir.mkdir(parents=True, exist_ok=True)
    report = SnapshotReport(before_dir=before_dir, sha=sha)

    def put(name: str, text: str) -> None:
        (before_dir / name).write_text(text, encoding="utf-8", newline="")
        report.written.append(name)

    # gate-log.md byte-for-byte: the append-only guard is a prefix comparison, and the
    # stamp check re-reads this exact file against `git show <sha>:config/gate-log.md`.
    (before_dir / "gate-log.md").write_bytes((repo / "config" / "gate-log.md").read_bytes())
    report.written.append("gate-log.md")
    put("backlog.yaml", dump_document(repo / "docs" / "restructure" / "backlog"))
    put(
        "relationship_vocabulary.yaml",
        yaml_fragments.merged_text(repo / "drydocs_core" / "ontology" / "relationship_vocabulary"),
    )
    put(
        "taxonomy-ontology-map.yaml",
        yaml_fragments.merged_text(repo / "config" / "taxonomy-ontology-map"),
    )

    # J51 optional list-shaped snapshots — the module may not exist on this side.
    try:
        detect = importlib.import_module("drydocs_remediation.detect")
        put("detect-rule-ids.txt", "\n".join(detect.CONFORMANCE_RULE_IDS))
    except ImportError:
        report.skipped.append("detect-rule-ids.txt")
    # ---- THE TEST-MODULE CROSSING, DECLARED (GRAPH2, 2026-09-10) -------------
    # Production code importing `tests.unit.*` is a layering inversion, and it is
    # DELIBERATE here. The alternative — moving the tables to a core module — was
    # measured and rejected:
    #
    #   * These are PER-SIDE DATA, and the split is already governed.
    #     PORT-MANIFEST.yaml carries a per-entry row for
    #     tests/unit/test_runbook_currency.py whose entry_rule unions by KEY and
    #     keeps each side's reasons verbatim. The current home strands nothing;
    #     the port rule is what makes that true, not the directory.
    #   * That row records its own RETIREMENT TRIGGER — when T19/T22 land
    #     company-side the exemptions go and the row reverts to the tests/**
    #     default. Moving the tables would break a trigger somebody wrote down.
    #   * The company ADAPTED this file by hand at caa0406 on the SME's ruling.
    #
    # What the move would buy is removing this import. `tests` is not in
    # pyproject's `packages`, so the crossing works only from a checkout — and
    # this is a port tool that runs from a checkout on the receiving side, never
    # from a wheel. A real inversion with no practical cost is a thing to declare,
    # not to pay three costs to remove.
    #
    # BOTH SILENCES BELOW ARE LOAD-BEARING. Neither is sloppiness:
    #   * `getattr(mod, table, {})` — the tuple names tables from BOTH trees.
    #     DEFERRED_VERBS is COMPANY-SIDE ONLY (it carries the T22 pair; it has
    #     never existed producer-side), so producer-side it correctly yields
    #     nothing. One tuple, two trees.
    #   * `except ImportError` — the consumer may not carry this guard at all.
    #
    # GENERATED_PATHS was ADDED to the tuple at GRAPH2. It landed producer-side at
    # e6daa986 (J70a) and no reader followed, so every port snapshot since has
    # silently omitted it — measured on this tree: the before file carried twelve
    # keys and not one GENERATED_PATHS line. The `getattr` default is exactly what
    # made a missing table indistinguishable from an empty one, which is the cost
    # of the silence being correct. PORT-MANIFEST.yaml:906 still names three
    # tables and needs the same correction; that file is the port pen, so it is
    # handed back in this item's notes rather than edited here.
    try:
        mod = importlib.import_module("tests.unit.test_runbook_currency")
        keys = [
            f"{table}:{k}"
            for table in (
                "HISTORICAL_PATHS",
                "FOREIGN_PATHS",
                "GENERATED_PATHS",
                "DEFERRED_VERBS",
            )
            for k in sorted(getattr(mod, table, {}) or {})
        ]
        put("runbook-exemption-keys.txt", "\n".join(keys))
    except ImportError:
        report.skipped.append("runbook-exemption-keys.txt")

    (before_dir / STAMP_FILE).write_text(sha + "\n", encoding="utf-8", newline="")
    report.written.append(STAMP_FILE)
    return report


def read_stamp(before_dir: Path) -> str | None:
    path = before_dir / STAMP_FILE
    return parse_stamp(path.read_text(encoding="utf-8") if path.is_file() else None)


def fork_point(repo: Path) -> str | None:
    """Where HEAD's branch left main, or None when that cannot be told here.

    None when no ``origin/main``/``main`` resolves, or when HEAD IS main (an apply
    made directly on the trunk has no fork point — the ancestor check is all there
    is, and the describe line's distance is what shows staleness). "IS main" means
    the checked-out branch is ``main``, or HEAD sits detached at the trunk tip. It
    does NOT mean "HEAD equals the pushed tip": a producer checkout carries unpushed
    trunk commits before every push, and reading ``origin/main`` as the fork point
    there called a stamp written at HEAD an earlier apply's leftover (2026-09-06, the
    Lane B merge close - eight merges on main, none pushed yet, round-trip guard red).
    CI never saw it because CI's HEAD is always the pushed tip.
    """
    branch = git(repo, "symbolic-ref", "--quiet", "--short", "HEAD")
    if branch.returncode == 0 and branch.stdout.strip() == "main":
        return None
    for ref in ("origin/main", "main"):
        tip = git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
        if tip.returncode == 0:
            main = tip.stdout.strip()
            if main == head_sha(repo):
                return None
            base = git(repo, "merge-base", "HEAD", main)
            return base.stdout.strip() if base.returncode == 0 else None
    return None


def check_stamp(before_dir: Path, repo: Path) -> list[str]:
    """The live check: every problem with the before-dir's stamp, empty when trustworthy."""
    stamp = read_stamp(before_dir)
    if stamp is None:
        return stamp_problems(None, resolves=False, is_ancestor=False, gate_log_matches=False)
    resolves = git(repo, "cat-file", "-e", f"{stamp}^{{commit}}").returncode == 0
    if not resolves:
        return stamp_problems(stamp, resolves=False, is_ancestor=False, gate_log_matches=False)
    is_ancestor = git(repo, "merge-base", "--is-ancestor", stamp, "HEAD").returncode == 0
    shown = subprocess.run(
        ["git", "show", f"{stamp}:config/gate-log.md"], cwd=repo, capture_output=True
    )
    snap = before_dir / "gate-log.md"
    matches = shown.returncode == 0 and snap.is_file() and snap.read_bytes() == shown.stdout
    return stamp_problems(
        stamp,
        resolves=True,
        is_ancestor=is_ancestor,
        gate_log_matches=matches,
        fork_point=fork_point(repo) if is_ancestor else None,
    )


def describe(before_dir: Path, repo: Path) -> str:
    """One line for the PORT-REPORT: the stamp, its date, and how far HEAD has moved since."""
    if not before_dir.is_dir():
        return f"before-dir {before_dir}: MISSING (not a directory)"
    stamp = read_stamp(before_dir)
    if stamp is None:
        return (
            f"before-dir {before_dir}: NO {STAMP_FILE} - predates the stamp or hand-built; "
            "re-snapshot with scripts/reconcile_before.py"
        )
    meta = git(repo, "log", "-1", "--format=%h %cs", stamp)
    if meta.returncode != 0:
        return (
            f"before-dir {before_dir}: {STAMP_FILE} {stamp[:8]} does not resolve in this repository"
        )
    behind = git(repo, "rev-list", "--count", f"{stamp}..HEAD").stdout.strip() or "?"
    present = sorted(p.name for p in before_dir.iterdir() if p.name != STAMP_FILE)
    missing = [n for n in MANDATORY if n not in present]
    tail = f"; MISSING {', '.join(missing)}" if missing else ""
    return (
        f"before-dir {before_dir}: {STAMP_FILE} {meta.stdout.strip()}, {behind} commits behind "
        f"HEAD {head_sha(repo)[:8]}; files {', '.join(present)}{tail}"
    )
