"""The deepdoc search log — every search leaves a row, and the row says which slot it was for.

MM3 (epic MM, docs/design/deepdoc-data-flow-overview.md §5-§6). The three
session search scripts shared one log under ``DRYDOCS_LOGDIR`` with
``tool / search / theme / results / date``. This is that log, formalised: two
columns become a rule, and the writer joins the declared run-log family.

    theme     the mind-map slot the search targeted, as ``<branch>/<slot>``.
              REQUIRED: a row with no theme is refused BEFORE any I/O. A search
              that was not aimed at a slot is the lexical-match habit §6 records
              the session turning away from — "the score got to the
              neighborhood; novelty + entity extraction + gap tracking got to
              the answer" — and the log is where that discipline is kept.
    novelty   new ids vs the graph + the record: how many identifiers the hit
              carried that neither the graph nor the map already knew. The row
              carries the ids themselves (``new_ids``) beside the count, because
              a bare number is exactly the problem the column exists to fix.
              :func:`score_novelty` is the pure comparison; what counts as
              "known" is the caller's — the graph and the map — and this item
              touches neither.

WRITTEN THROUGH THE RUN-LOG FAMILY. The kind ``search`` is declared in
``config/log-kinds.yaml`` (G105: a kind that exists only in code is the state
that item removed), per-day JSONL — the ``qa`` ledger idiom, and for the same
reason: the record the novelty score reads IS this file, and a per-run file
would shard the one history into as many pieces as there were searches. The
filename derives from the declaration (``search.deepdoc.<YYYYmmdd>.jsonl``), the
directory from :func:`drydocs_core.run_log.resolve_log_dir`. An ``OSError``
after validation is swallowed with a warning — the family idiom: an audit trail
is never the reason a search fails. Opened per append, so two sessions on one
machine interleave lines rather than clobber a handle.

No connector calls any network in this item; the row is what a connector
(MM4/MM5) hands over after it has searched.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from drydocs_core.run_log import resolve_log_dir

from .mindmap import MindMap, MindMapError

LOGGER = logging.getLogger(__name__)

#: The declared kind and the free-form name segment (config/log-kinds.yaml).
KIND = "search"
NAME = "deepdoc"
_FALLBACK_BASENAME = f"{KIND}.{NAME}"

#: The columns, in the order they are written — the five the session scripts
#: agreed on, plus the two this item adds (``novelty``, ``new_ids``) and the
#: seed the search was about.
COLUMNS: tuple[str, ...] = (
    "tool",
    "search",
    "theme",
    "novelty",
    "new_ids",
    "results",
    "date",
    "seed",
)


class SearchLogError(ValueError):
    """A row that cannot be written as it stands — refused before any I/O."""


def theme_for(branch: str, slot: str) -> str:
    """The ``theme`` value for a mind-map slot: ``<branch>/<slot>``."""
    if not branch or not slot:
        raise SearchLogError("a theme names a branch and a slot")
    return f"{branch}/{slot}"


def split_theme(theme: str) -> tuple[str, str]:
    branch, sep, slot = theme.partition("/")
    if not sep or not branch or not slot:
        raise SearchLogError(f"theme {theme!r} is not <branch>/<slot>")
    return branch, slot


def score_novelty(found: Iterable[str], known: Iterable[str]) -> tuple[str, ...]:
    """The ids in ``found`` that ``known`` does not have — distinct, first-seen order.

    ``known`` is the graph plus the record (the map's filled values and the ids
    earlier rows already logged), supplied by the caller. Comparison is exact:
    normalising a token to a graph key is the caller's job, not a scorer's guess.
    """
    seen = set(known)
    out: dict[str, None] = {}
    for value in found:
        if value not in seen:
            out.setdefault(value, None)
    return tuple(out)


@dataclass(frozen=True)
class SearchRow:
    """One search, as the connector hands it over. ``date`` is stamped at append."""

    tool: str
    search: str
    theme: str
    results: int
    new_ids: tuple[str, ...] = ()
    seed: str | None = None

    def __post_init__(self) -> None:
        if not self.theme or not str(self.theme).strip():
            raise SearchLogError(
                "a search row without a theme is refused: every search targets a "
                "mind-map slot (<branch>/<slot>), or it is not a search the loop made"
            )
        split_theme(self.theme)
        if not self.tool or not str(self.tool).strip():
            raise SearchLogError("a search row names the tool that ran it")
        if not self.search or not str(self.search).strip():
            raise SearchLogError("a search row carries the search that was run")
        if not isinstance(self.results, int) or isinstance(self.results, bool) or self.results < 0:
            raise SearchLogError(f"results must be a whole count, got {self.results!r}")
        if not isinstance(self.new_ids, tuple) or not all(isinstance(v, str) for v in self.new_ids):
            raise SearchLogError(
                "new_ids is a tuple of the id strings the hit was the first to carry"
            )

    @property
    def novelty(self) -> int:
        return len(self.new_ids)


class SearchLog:
    """Append-only per-day JSONL ledger under the run-log directory."""

    def __init__(self, log_dir: Path | None = None) -> None:
        self._log_dir = log_dir

    def path(self, now: datetime | None = None) -> Path:
        log_dir = self._log_dir or resolve_log_dir()
        try:
            from drydocs_core.log_kinds import log_filename

            return log_dir / log_filename(KIND, NAME, now=now)
        except Exception:  # — an unreadable declaration falls back to the declared shape
            stamp = (now or datetime.now()).strftime("%Y%m%d")
            return log_dir / f"{_FALLBACK_BASENAME}.{stamp}.jsonl"

    def append(self, row: SearchRow, *, mindmap: MindMap | None = None) -> dict[str, Any]:
        """Validate, then append one line. Returns the record as written.

        With ``mindmap`` given, the theme must name one of its slots — the check
        that keeps a log and its map from drifting apart on slot names.
        """
        if mindmap is not None:
            branch, slot = split_theme(row.theme)
            try:
                mindmap.slot(branch, slot)
            except MindMapError as exc:
                raise SearchLogError(
                    f"theme {row.theme!r} names no slot on the map: {exc}"
                ) from exc
        record: dict[str, Any] = {
            **{k: v for k, v in asdict(row).items() if k != "new_ids"},
            "novelty": row.novelty,
            "new_ids": list(row.new_ids),
            "date": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        record = {col: record.get(col) for col in COLUMNS}
        try:
            path = self.path()
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, default=str) + "\n")
        except OSError as exc:  # — audit trail, never the reason a search fails
            LOGGER.warning("search log unavailable (%s) — row not recorded", exc)
        return record

    def rows(self, now: datetime | None = None) -> tuple[dict[str, Any], ...]:
        """Every row in the day-file (the record the novelty score reads), oldest first."""
        path = self.path(now)
        if not path.is_file():
            return ()
        out: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
        return tuple(out)

    def logged_ids(self, now: datetime | None = None) -> tuple[str, ...]:
        """The ids earlier rows already reported new — the record half of ``known``."""
        seen: dict[str, None] = {}
        for record in self.rows(now):
            for value in record.get("new_ids") or ():
                seen.setdefault(str(value), None)
        return tuple(seen)
