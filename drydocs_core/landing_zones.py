"""Manual landing zones — the folders a hand-carried source drops into (N12).

WHY THIS MODULE EXISTS. ``config/source-registry.yaml`` declares, per dataset,
HOW the data arrives: ``acquisition.mode: manual`` names a ``drop_dir`` that a
human exports a file into, ``automated`` names a pull the pipeline runs. That
declaration was documentation only — nothing resolved it, nothing checked it,
and nothing noticed when a landing zone was emptied.

THE FAILURE IT GUARDS, stated plainly because a prose rule already existed and
did not hold. ``git clean -fd`` deletes untracked, non-ignored files;
``git clean -fdx`` deletes untracked files INCLUDING ignored ones. Source
payloads can never be tracked (PUBLISH-BOUNDARY.md), so inside a working tree
they are always in one of those two categories — which means **no combination
of .gitignore rules protects a manual drop from a port-time clean**. Whether a
given CSV survived a sweep came down to whether it happened to be ignored and
whether the sweep carried ``-x``: luck, not design. ``docs/port-prompt.md`` has
said "NEVER ``git clean`` during a port" since the J22 lesson and the files were
deleted anyway, which is the argument for a control rather than another warning.

THE RULE, and it is the whole design: a manual landing zone lives OUTSIDE the
repo working tree (``base: data_root``, resolved through
:mod:`drydocs_core.data_root`, default ``~/data/DryDocs``), where no git
operation of any strength can reach it. The single exception is a zone whose
contents are COMMITTED repo artifacts rather than source payloads
(``base: repo`` — ``config/taxonomy/``, ``knowledge/depgraph-snapshots/``,
``docs/design/``); tracked files survive every clean, so those are safe by the
same mechanism that makes them publishable. ``tests/unit/test_landing_zones.py``
enforces both halves, and the second half is the one that closes the hole: a
``repo``-based zone MUST be tracked, so an untracked data corpus can never be
declared as a landing zone and inherit an in-tree home.

Nothing here creates, moves or deletes a directory. It resolves what the
registry declares and reports what is actually there — ``drydocs
landing-zones`` is the read surface, and it exists so that "my extracts are
gone" is a one-command answer instead of an investigation.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from drydocs_core.data_root import resolve_data_root
from drydocs_core.repo_paths import repo_root

BASE_DATA_ROOT = "data_root"
BASE_REPO = "repo"
BASES = (BASE_DATA_ROOT, BASE_REPO)

#: Formats a hand drop can carry (mirrors the acquisition schema enum).
FORMATS = ("csv", "ascii", "json", "archive")

#: Worktree-aware (J48): a session running from .claude/worktrees/<agent>/ must
#: resolve ITS OWN checkout, or a repo-based zone would be measured against the
#: main tree and a worktree's landing zones would read as another tree's.
_REPO_ROOT = repo_root(Path(__file__).resolve().parent.parent)


@dataclass(frozen=True)
class LandingZone:
    """One manual source's declared drop folder, resolved to a real path."""

    source_id: str
    fmt: str
    drop_dir: str
    base: str
    path: Path

    @property
    def inside_repo(self) -> bool:
        """True when the resolved zone sits under the repo working tree.

        The property a clean can reach, so the one the guard asserts on —
        never inferred from ``base`` alone, because ``DRYDOCS_DATA_ROOT`` is
        env-settable and someone WILL point it at the tree one day.
        """
        try:
            self.path.resolve().relative_to(_REPO_ROOT)
        except ValueError:
            return False
        return True


@dataclass(frozen=True)
class ZoneStatus:
    """What is actually in a zone right now. Read-only, never creates."""

    zone: LandingZone
    exists: bool
    file_count: int

    @property
    def empty(self) -> bool:
        return self.exists and self.file_count == 0


def _rows(registry_path: Path | None = None) -> list[dict[str, Any]]:
    import yaml

    path = registry_path or (_REPO_ROOT / "config" / "source-registry.yaml")
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    return list(doc.get("datasets") or [])


def resolve(base: str, drop_dir: str) -> Path:
    """``drop_dir`` against its declared base. No side effects, no mkdir."""
    if base == BASE_REPO:
        return _REPO_ROOT / drop_dir
    return resolve_data_root() / drop_dir


def manual_zones(registry_path: Path | None = None) -> tuple[LandingZone, ...]:
    """Every ``acquisition.mode: manual`` row, resolved.

    Rows are returned in registry order so a report reads the same way the
    file does. A row missing ``drop_dir_base`` is returned with ``base=""``
    rather than guessed — the guard names it, and a silent default would be
    exactly the ambiguity this field was added to remove.
    """
    zones: list[LandingZone] = []
    for row in _rows(registry_path):
        acq = row.get("acquisition") or {}
        if acq.get("mode") != "manual":
            continue
        base = acq.get("drop_dir_base") or ""
        drop_dir = acq.get("drop_dir") or ""
        zones.append(
            LandingZone(
                source_id=row.get("id", "<no-id>"),
                fmt=acq.get("format") or "",
                drop_dir=drop_dir,
                base=base,
                path=resolve(base, drop_dir) if base and drop_dir else Path(drop_dir),
            )
        )
    return tuple(zones)


def inventory(zones: Iterable[LandingZone] | None = None) -> tuple[ZoneStatus, ...]:
    """Present-or-absent plus a file count per zone. Never creates a directory."""
    out: list[ZoneStatus] = []
    for zone in zones if zones is not None else manual_zones():
        exists = zone.path.is_dir()
        count = 0
        if exists:
            for _, _, files in os.walk(zone.path):
                count += len(files)
        out.append(ZoneStatus(zone=zone, exists=exists, file_count=count))
    return tuple(out)


def tracked_paths_under(rel_dir: str) -> int:
    """How many files git TRACKS under a repo-relative directory.

    The check that makes ``base: repo`` legitimate: tracked content survives
    every ``git clean``, so a repo-based zone is safe exactly when its contents
    are committed. Returns 0 when git is unavailable, which the guard reads as
    "cannot prove it is tracked" and fails on — the safe direction.
    """
    import subprocess

    try:
        done = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "ls-files", "--", rel_dir],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return 0
    if done.returncode != 0:
        return 0
    return len([line for line in done.stdout.splitlines() if line.strip()])
