"""Fix-tracking loads — the write half of the ruled separation of duties.

Gate ``remediation-fix-tracking`` SIGNED OFF 2026-08-12 (``config/gate-log.md``)
ruled fix tracking as OUR intervention record: a fourth property axis beside
envelope authorship, pull tracking and load provenance (§A1). ``drydocs_remediation``
emits a ``drydocs.remediation.fix-tracking.v1`` change-set and stays no-graph-write
(§A2 — NFR-REM-1, the AST guard and the corroborate write-clause regex are
untouched by this build); §C1 ruled the writer to be a DEDICATED drydocs-load
loader, declining C2's pass-inside-an-existing-Control-M-loader because that would
couple fix cadence to ingest cadence and a fix should be markable the hour its
package ships.

The pure half — the schema id, the status enum, the three ruled property names,
the target NODE KEYs, and the change-set reader — lives in
``drydocs_core.fix_tracking``, shared with the emitter (components never import
each other). THE GRAPH WRITE IS HERE and only here.

MATCH, NEVER MERGE — AND THE PREFLIGHT THAT MAKES THAT MEAN SOMETHING. §C1 says a
fix target that does not exist is an error, not a node to invent. Writing ``MATCH``
instead of ``MERGE`` only gets half of that: a MATCH that finds nothing writes
nothing and reports success, so a change-set naming five jobs of which two were
never loaded would come back OK having marked three. :meth:`_preflight_indexes`
therefore resolves EVERY target first and refuses the whole change-set if any is
missing — all-or-nothing, the same posture ``changes.graph_anchors`` takes at the
emitting end with ``UnanchoredFixError``. It runs before ``_open_run``, so a
refused load writes nothing at all, not even the :JobRun.

TWO MODES (§B2). The ruled enum has no ``rejected`` member — a rejected fix
REMOVES the three properties, and the fix package records the rejection — so the
v1 artifact cannot carry that intent and the caller states it:
``FixTrackingLoader(client, rows, mode=REJECT)``. The reject branch is fenced on
``remediation_fix_id`` in the Cypher so a stale rejection cannot strip a newer
fix's marks.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any, ClassVar

from drydocs_core.fix_tracking import (  # noqa: F401 — re-exported surface
    APPLY,
    FIX_STATUS_ENUM,
    FIX_TRACKING_PROPERTIES,
    FIX_TRACKING_SCHEMA,
    MODES,
    REJECT,
    FixTrackingError,
    parse_change_set,
)
from drydocs_core.models import FixTrackingRow

from .base import BaseLoader

LOGGER = logging.getLogger(__name__)


class UnresolvedFixTargetError(FixTrackingError):
    """A change-set names a node that is not in the graph.

    Deliberately a hard failure and not a per-row reject: a fix package cites
    the graph's own keys, so an unresolved target means the change-set and the
    graph disagree about what exists — applying the resolvable half would leave
    a partially-marked fix nobody asked for.
    """


#: Resolve every target against its label's NODE KEY, in ONE read. The two
#: OPTIONAL MATCHes cannot multiply rows: (folder_id, job_id) and folder_id are
#: NODE KEYs, so each matches at most one node, and a null job_id matches
#: nothing (a property comparison against null never matches) — which is why a
#: folder row's job branch is naturally empty without a guard.
#:
#: THE WRITE TEMPLATE RESOLVES THE SAME WAY, on purpose. If this checked targets
#: by one rule while ``fix_tracking.cypher`` wrote by another, the preflight
#: could pass and the write still miss — which is precisely the failure the
#: preflight exists to prevent, reintroduced one layer down.
_RESOLVE_TARGETS = """
UNWIND $batch AS row
OPTIONAL MATCH (j:ControlMJob {folder_id: row.folder_id, job_id: row.job_id})
OPTIONAL MATCH (f:ControlMFolder {folder_id: row.folder_id})
WITH row, CASE row.kind WHEN 'job' THEN j WHEN 'folder' THEN f END AS n
RETURN row.kind         AS kind,
       row.label        AS label,
       row.folder_id    AS folder_id,
       row.job_id       AS job_id,
       row.display_name AS display_name,
       n IS NOT NULL    AS found
"""


class FixTrackingAdapter:
    """Yields parsed fix-tracking rows to BaseLoader."""

    name = "fix-tracking-changeset"

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def __enter__(self) -> FixTrackingAdapter:
        return self

    def __exit__(self, *exc: Any) -> None:
        return None

    def rows(self) -> Iterator[dict]:
        yield from self._rows


def _describe(row: dict[str, Any]) -> str:
    """One target, named the way the operator can act on it."""
    key = f"folder_id={row.get('folder_id')!r}"
    if row.get("kind") == "job":
        key += f", job_id={row.get('job_id')!r}"
    name = row.get("display_name") or "?"
    return f":{row.get('label')} {name} ({key})"


class FixTrackingLoader(BaseLoader):
    """Applies (or rejects) one fix-tracking change-set against the graph.

    Every target must already exist. See the module docstring for why that is a
    refusal rather than a skip, and why the check runs before the :JobRun opens.
    """

    name: ClassVar[str] = "fix_tracking.v1"
    # Deliberately None: the input is an artifact THIS SYSTEM emits from a
    # remediation session (drydocs_remediation.changes.fix_tracking_changeset),
    # not a feed from an external source system — there is no source-registry
    # entry to bind and no crosswalk to confirm. The named exemption lives in
    # cli.SOURCELESS_LOADERS (N3).
    source_id: ClassVar[str | None] = None
    cypher_path: ClassVar[Path | None] = (
        Path(__file__).resolve().parent / "cypher" / "fix_tracking.cypher"
    )
    row_model: ClassVar[type] = FixTrackingRow
    source_label: ClassVar[str] = "human"

    def __init__(self, client, rows: list[dict[str, Any]], *, mode: str = APPLY, **kwargs) -> None:
        if mode not in MODES:
            raise ValueError(f"unknown fix-tracking mode {mode!r} — expected {' | '.join(MODES)}")
        self.mode = mode
        self._rows = list(rows)
        super().__init__(client, FixTrackingAdapter(self._rows), **kwargs)

    def extra_cypher_params(self) -> dict[str, Any]:
        """``$mode`` is a per-RUN constant, not per-row: one change-set is
        applied or rejected as a whole, never half of each."""
        return {"mode": self.mode}

    def _preflight_indexes(self) -> None:
        """The index preflight, then the target preflight — both before the run opens.

        Order matters. The index check comes first because resolving targets
        against a FAILED NODE KEY index would answer the wrong question: a
        broken index is why a target "does not exist", and reporting missing
        jobs in that state would send the operator after the change-set instead
        of after the index.
        """
        super()._preflight_indexes()
        self._preflight_targets()

    def _probe_batch(self) -> list[dict[str, Any]]:
        """The rows the preflight sends, coerced the way the WRITE will send them.

        YAML types are not the graph's: an unquoted ``folder_id: 123`` parses as
        an int, and ``FixTrackingRow`` turns it into ``"123"`` before the write
        ever sees it. Probing with the raw value would compare an int against a
        string property and report a target that exists as missing — a refusal
        rather than a mis-write, so the direction is safe, but it is still the
        wrong answer. Validating here means the preflight asks about exactly the
        values the write will use.
        """
        return [self.to_params(self.row_model.model_validate(row)) for row in self._rows]

    def _preflight_targets(self) -> None:
        """Refuse the whole change-set unless every target resolves (§C1)."""
        if not self._rows:
            raise UnresolvedFixTargetError(
                f"{self.name}: the change-set names no targets — nothing to apply."
            )
        probe = self._probe_batch()
        resolved = self.client.run(_RESOLVE_TARGETS, batch=probe)
        found = {
            (r.get("kind"), r.get("folder_id"), r.get("job_id")) for r in resolved if r.get("found")
        }
        missing = [
            row
            for row in probe
            if (row.get("kind"), row.get("folder_id"), row.get("job_id")) not in found
        ]
        if missing:
            listed = "\n  ".join(_describe(row) for row in missing)
            raise UnresolvedFixTargetError(
                f"{self.name}: refusing the change-set — {len(missing)} of "
                f"{len(self._rows)} target(s) are not in the graph:\n  {listed}\n"
                "A fix target that does not exist is an error, not a node to "
                "invent (gate remediation-fix-tracking §C1). Load the Control-M "
                "objects first, or re-anchor the fix package against the graph "
                "it is citing. Nothing was written — not even the :JobRun."
            )

    def load(self):
        summary = super().load()
        verb = "marked" if self.mode == APPLY else "cleared"
        LOGGER.info(
            "fix_tracking: %s %d target(s) for fix %s (mode=%s)",
            verb,
            summary.rows_processed,
            self._rows[0].get("remediation_fix_id") if self._rows else "?",
            self.mode,
        )
        return summary


def change_set_rows(path: str | Path) -> list[dict[str, Any]]:
    """Read a change-set into loader rows. Re-exported so this module stays the
    loader's single import surface (the ``manual_loads`` idiom)."""
    return parse_change_set(path)
