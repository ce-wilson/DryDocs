"""Phased HITL curation — the gate between candidates and ground truth.

The component is *proactive/curated* (ADR 0002 D2): candidates arrive in phases
(estate slices), a human confirms or rejects, and only confirmed candidates may be
written. The cadence/trigger wiring is later work; the state model is the contract.

THE DECISIONS FILE (LIN2 b) — the one shape the review surface exports and the load
reads. ``lineage-review`` renders candidate rels; the SME marks each one on the page;
"Export" writes this JSON; ``drydocs lineage-load --confirmed <file>`` reads it and
hands the ``confirmed`` subset to the writer. Nothing reaches ``drydocs`` uncurated:
with no file the confirmed set is empty, and the load says so.

    {
      "schema":    "drydocs.lineage-decisions.v1",
      "doc":       "<the review page's doc id>",
      "exported":  "<ISO-8601 timestamp, the browser's clock>",
      "decisions": [
        {"from": "proc#controlm_job:160500.1", "type": "INVOKES",
         "to":   "proc#shell_script:/opt/scripts/auto/fw.ksh", "decision": "confirmed"}
      ],
      "notes":     [{"folder": "<folder>", "note": "<free text>"}]
    }

``from`` / ``type`` / ``to`` are the graph's own rel triple — the node ids the
artifact carries, the registered label — so a decision joins to a candidate by
equality and nothing is re-derived. ``decision`` is a :class:`CurationStatus` value;
a rel the SME never touched is simply absent (it stays ``proposed`` by construction
and is never written). ``notes`` are the per-folder free text the page has always
exported, carried along unchanged; the load does not read them.

This is the SMALLEST honest grain (review 0015fcfa R2): a per-rel yes/no. The
binding-level curation state (``curation_status`` / ``curated_by`` / ``curated_at``
on an :InvocationBinding) is the later item that replaces it; nothing here
pre-empts that shape.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .model import REL_ALIASES, REL_TYPES

DECISIONS_SCHEMA = "drydocs.lineage-decisions.v1"


class CurationStatus(str, Enum):
    PROPOSED = "proposed"  # derived, unreviewed — never written to ground truth
    CONFIRMED = "confirmed"  # human-accepted — eligible for the drydocs write
    REJECTED = "rejected"  # human-declined — kept for audit, never written


class DecisionsError(ValueError):
    """A decisions file that cannot be trusted — refused, never partially applied."""


@dataclass(frozen=True)
class DecisionSet:
    """What a decisions file said, as sets the writer and the load report can use."""

    confirmed: frozenset[tuple[str, str, str]]
    rejected: frozenset[tuple[str, str, str]]
    proposed: frozenset[tuple[str, str, str]]  # exported as touched-but-undecided
    doc: str = ""
    exported: str = ""
    path: str = ""
    notes: tuple[dict[str, str], ...] = field(default_factory=tuple)

    @property
    def total(self) -> int:
        return len(self.confirmed) + len(self.rejected) + len(self.proposed)

    def missing_from(self, rels: set[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
        """Decisions naming a rel the graph does not carry — curation out of sync with
        the artifact (the page was rendered from another extract). Sorted."""
        return sorted((self.confirmed | self.rejected | self.proposed) - rels)


def _triple(raw: dict[str, Any], index: int) -> tuple[str, str, str]:
    missing = [k for k in ("from", "type", "to", "decision") if not raw.get(k)]
    if missing:
        raise DecisionsError(f"decisions[{index}] lacks {missing} — every decision names its rel")
    rel_type = REL_ALIASES.get(str(raw["type"]), str(raw["type"]))
    if rel_type not in REL_TYPES:
        raise DecisionsError(
            f"decisions[{index}]: rel type {raw['type']!r} is not a registered label "
            f"{sorted(REL_TYPES)}"
        )
    return (str(raw["from"]), rel_type, str(raw["to"]))


def parse_decisions(data: dict[str, Any], *, path: str = "") -> DecisionSet:
    """Validate the exported dict. Refusals are total: an unknown schema, a decision
    value outside :class:`CurationStatus`, an unregistered rel type or a rel decided
    twice with different answers refuses the whole file, because a half-applied
    curation is the one thing this gate exists to prevent."""
    if not isinstance(data, dict) or data.get("schema") != DECISIONS_SCHEMA:
        got = data.get("schema") if isinstance(data, dict) else type(data).__name__
        raise DecisionsError(
            f"not a lineage decisions file (schema {got!r}, want {DECISIONS_SCHEMA!r})"
            + (f": {path}" if path else "")
        )
    rows = data.get("decisions")
    if not isinstance(rows, list):
        raise DecisionsError("`decisions` must be a list (empty is allowed - it means none)")
    by_status: dict[CurationStatus, set[tuple[str, str, str]]] = {s: set() for s in CurationStatus}
    seen: dict[tuple[str, str, str], CurationStatus] = {}
    for i, raw in enumerate(rows):
        if not isinstance(raw, dict):
            raise DecisionsError(f"decisions[{i}] must be a mapping")
        triple = _triple(raw, i)
        try:
            status = CurationStatus(str(raw["decision"]))
        except ValueError:
            raise DecisionsError(
                f"decisions[{i}]: decision {raw['decision']!r} is not one of "
                f"{[s.value for s in CurationStatus]}"
            ) from None
        if triple in seen and seen[triple] != status:
            raise DecisionsError(
                f"decisions[{i}]: {triple} is decided twice with different answers "
                f"({seen[triple].value} then {status.value})"
            )
        seen[triple] = status
        by_status[status].add(triple)
    notes = tuple(
        {"folder": str(n.get("folder", "")), "note": str(n.get("note", ""))}
        for n in (data.get("notes") or [])
        if isinstance(n, dict)
    )
    return DecisionSet(
        confirmed=frozenset(by_status[CurationStatus.CONFIRMED]),
        rejected=frozenset(by_status[CurationStatus.REJECTED]),
        proposed=frozenset(by_status[CurationStatus.PROPOSED]),
        doc=str(data.get("doc") or ""),
        exported=str(data.get("exported") or ""),
        path=path,
        notes=notes,
    )


def load_decisions(path: Path) -> DecisionSet:
    """Read and validate a decisions file the review page exported."""
    path = Path(path)
    if not path.is_file():
        raise DecisionsError(f"decisions file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DecisionsError(f"cannot read decisions file {path}: {exc}") from exc
    return parse_decisions(data, path=str(path))


def curate(candidates: list, decisions: dict[str, CurationStatus]) -> list:
    """Apply human curation decisions to candidates (phased batches)."""
    raise NotImplementedError("curation cadence lands with the phased trigger wiring")
