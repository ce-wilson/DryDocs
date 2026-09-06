"""The log estate: what each declared log KIND actually has on disk (O68).

``log_kinds.py`` declares what the system WRITES — the kinds, their retention,
their rotation. ``data_zones.py`` reports what is IN a declared directory. This
joins them, per kind, so the question a retention policy is really about can be
answered: **days declared against days actually on disk, and how much of it.**

WHY IT LIVES IN CORE and not in the API that serves it (O68 clause b, and the
item's own note asks for exactly this): the walk that knows a file count is the
only walk that should also be stating a size, and a byte sum computed one layer
up would be free to disagree with the inventory beside it. The API returns this;
it does not compute it.

KINDS ARE COUNTED BY FILENAME, because that is what the declaration says they
are. Every kind in ``config/log-kinds.yaml`` currently has ``dir: null`` — they
share one root — so a kind's files are the ones whose name begins with
``<kind>.``, which is the naming rule that file DERIVES rather than asserts
(``<kind>.<name>.<stamp>.<ext>``). A kind that later declares its own ``dir``
gets counted in that directory instead, and both cases are one code path
because ``LogKind.path()`` already answers the question.

WHAT THIS DELIBERATELY DOES NOT DO. It never reads a log's CONTENTS — not one
byte, for any kind. Sizes come from ``stat``. That is not an incidental
property: ADR 0014 clause 6 splits a lean API log from a verbose short-retention
debug log carrying Cypher text and request detail, and capturing that text is
ruled while SURFACING it is not (O68 clause c). A module that could return the
bytes would make the difference between those two a matter of who called it.

Never creates a directory. A report that repairs the tree it is inspecting has
hidden the thing it was asked about.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from drydocs_core.log_kinds import LogKind, load_kinds, resolve_root


@dataclass(frozen=True)
class KindEstate:
    """One declared kind, and what is on disk for it right now."""

    kind: LogKind
    #: The resolved directory — the root, or the kind's own ``dir`` under it.
    path: Path
    exists: bool
    file_count: int
    total_bytes: int
    #: Age in days of the OLDEST file, or None when there are none. This is the
    #: half of the retention question the declaration cannot answer: `retention_days`
    #: says what is meant to happen, and this says what has.
    oldest_days: int | None

    @property
    def over_retention(self) -> bool:
        """Is something on disk older than this kind says it keeps?

        Reported, never acted on. A sweeper is a different decision with a
        different blast radius; this is a panel that tells an operator the two
        numbers disagree and lets them decide.
        """
        return self.oldest_days is not None and self.oldest_days > self.kind.retention_days


def _age_days(path: str, now: datetime) -> int | None:
    try:
        mtime = datetime.fromtimestamp(os.path.getmtime(path), tz=UTC)
    except OSError:
        return None
    return max(0, (now - mtime).days)


def estate(
    kinds: tuple[LogKind, ...] | None = None,
    root: Path | None = None,
    now: datetime | None = None,
) -> tuple[KindEstate, ...]:
    """Per declared kind: directory, resolved path, file count, size, oldest age.

    Reads nothing but directory entries and their stat. Arguments are injectable
    so a test can point it at a tmp tree — the alternative is a test that reports
    on the developer's real log directory, which is both unrepeatable and rude.
    """
    at = now or datetime.now(UTC)
    base = root if root is not None else resolve_root()
    out: list[KindEstate] = []

    for k in kinds if kinds is not None else load_kinds():
        directory = k.path(base)
        exists = directory.is_dir()
        count = 0
        size = 0
        oldest: int | None = None
        if exists:
            for entry in os.scandir(directory):
                # A kind's files are the ones its naming rule claims. A kind with
                # its own `dir` owns everything in it; a kind sharing the root
                # owns the `<kind>.`-prefixed names and nothing else — otherwise
                # every kind would report every other kind's bytes.
                if not entry.is_file():
                    continue
                if k.dir is None and not entry.name.startswith(f"{k.id}."):
                    continue
                count += 1
                try:
                    size += entry.stat().st_size
                except OSError:
                    # Same rule as the zone inventory: a file that vanished
                    # between the scan and the stat is not a reason to fail a
                    # read-only report. It is still counted.
                    continue
                age = _age_days(entry.path, at)
                if age is not None and (oldest is None or age > oldest):
                    oldest = age
        out.append(
            KindEstate(
                kind=k,
                path=directory,
                exists=exists,
                file_count=count,
                total_bytes=size,
                oldest_days=oldest,
            )
        )
    return tuple(out)
