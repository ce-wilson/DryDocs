"""docs_email_concerns writer (Q21) — the build the signed gate authorized.

Gate ``email-folder-assignment`` SIGNED 8/8 on 2026-08-19 and ruled the edge;
this module is the writer it authorized and deliberately did not build:

    (:Document)-[:CONCERNS]->(:ControlMFolder | :ETLProcess)

THE CONTRACT, exactly as ruled — every clause here cites the sign-off:

* CONCERNS, not ASSIGNED_TO (§A1): the type names the MEANING (what the email
  is about); the assertion mechanics live in edge properties.
* Two endpoint classes, one meaning, the endpoint class RECORDED ON THE EDGE
  (§A2 — the rua-load-shapes §B2 union-endpoint convention).
* NO ANONYMOUS ASSIGNMENT (§A3): every write carries ``assigned_by``
  (``sme`` | ``source-signal``) AND an evidence pointer — the extract line, or
  the ruling note. A write missing either is REFUSED, before anything is
  written; :func:`validate` is the refusal and the tests assert it fires.
* STRUCTURED FIELD ONLY performs (§B1): an extraction pass may PROPOSE, never
  perform. :data:`STRUCTURED_SIGNAL_FIELDS` is EMPTY ON PURPOSE — the assumed
  extract contract (the G47 synthetic samples) has no structured folder or
  process field, so the source-signal path ships with no live producer and
  every assignment starts SME-performed. Prose mentions (subject line
  included) are candidates for the SME surface (Idea-138), never edges.
* UNASSIGNED NEVER DECAYS (§B3): nothing here sweeps, backfills or defaults.
  The unassigned count is exposed read-side (``docs.email-unassigned.v1``).
* THE K7 §A1 FENCE STANDS (§C1): this edge says what an email is ABOUT. It
  never authors folder→application attribution, ownership or support routing,
  and no derived edge may ever cite a CONCERNS edge as its basis. Traversing
  email → folder → application is legitimate READING.
* RETENTION RIDES THE ASSIGNMENT (§C2): nothing here deletes or expires.

The LEXICAL loader (email_extracts) keeps its hard fence: it may never gain
this write — tests/unit/test_email_extracts.py forbids these tokens in ITS
cypher, and this module's own cypher file is the one authorized writer.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

CYPHER_PATH = Path(__file__).resolve().parent / "cypher" / "email_concerns.cypher"

#: §A3's closed vocabulary — who performed the assignment.
ASSIGNED_BY = ("sme", "source-signal")

#: §A2's two endpoint classes, with the node key each is matched on
#: (MATCH-only — the writer never mints an endpoint; an assignment against a
#: folder or process the graph does not hold writes nothing and is counted).
ENDPOINT_KEYS: dict[str, str] = {
    "ControlMFolder": "folder_id",
    "ETLProcess": "token",
}

#: §B1 — the structured extract fields a source signal may READ. EMPTY ON
#: PURPOSE, and the emptiness is load-bearing: the assumed extract contract
#: has no structured folder/process field, so nothing can perform an edge
#: from the source today. Adding a field here is a CONTRACT change on the
#: extract, not a tuning knob — it must come with the field actually existing.
STRUCTURED_SIGNAL_FIELDS: tuple[str, ...] = ()


class AssignmentRefusedError(ValueError):
    """§A3: an anonymous or class-invalid assignment is refused, never fixed up."""


@dataclass(frozen=True)
class ConcernsAssignment:
    """One ruled assignment: this email Document is ABOUT this folder/process."""

    doc_id: str
    endpoint_class: str  # ControlMFolder | ETLProcess (§A2)
    endpoint_key: str  # folder_id / token value
    assigned_by: str  # sme | source-signal (§A3)
    evidence: str  # the extract line, or the ruling note (§A3)


def validate(assignment: ConcernsAssignment) -> None:
    """§A3's refusal, applied BEFORE any write. Raises, never repairs."""
    if assignment.endpoint_class not in ENDPOINT_KEYS:
        raise AssignmentRefusedError(
            f"endpoint_class {assignment.endpoint_class!r} is not one of "
            f"{sorted(ENDPOINT_KEYS)} — two endpoint classes, one meaning (gate SS-A2)"
        )
    if assignment.assigned_by not in ASSIGNED_BY:
        raise AssignmentRefusedError(
            f"assigned_by {assignment.assigned_by!r} is not one of {ASSIGNED_BY} — "
            "no anonymous assignment (gate SS-A3)"
        )
    if not (assignment.evidence or "").strip():
        raise AssignmentRefusedError(
            "assignment carries no evidence pointer — the extract line or the "
            "ruling note is REQUIRED on every write (gate SS-A3, O24)"
        )
    if not (assignment.doc_id or "").strip() or not (assignment.endpoint_key or "").strip():
        raise AssignmentRefusedError("assignment missing doc_id or endpoint_key")


def extract_source_signal(
    rows: Iterable[Mapping[str, object]],
) -> tuple[ConcernsAssignment, ...]:
    """The §B1 source-signal pass: STRUCTURED FIELDS ONLY may perform.

    Reads only :data:`STRUCTURED_SIGNAL_FIELDS` — which is empty, because the
    extract contract declares no such field — so over the bundled G47 samples
    (and any extract shaped like them) this returns ZERO assignments, proven
    by test. Prose mentions in subject or body are NOT read here at all:
    candidate-surfacing is the SME surface's job (SS-B2, Idea-138), and a
    candidate is never an edge.
    """
    performed: list[ConcernsAssignment] = []
    for row in rows:
        for field_name in STRUCTURED_SIGNAL_FIELDS:  # pragma: no branch — empty today
            value = str(row.get(field_name) or "").strip()
            if value:
                performed.append(
                    ConcernsAssignment(
                        doc_id=str(row.get("doc_id") or ""),
                        endpoint_class="ControlMFolder",
                        endpoint_key=value,
                        assigned_by="source-signal",
                        evidence=f"{field_name}={value}",
                    )
                )
    return tuple(performed)


class EmailConcernsWriter:
    """Lands ruled assignments as CONCERNS edges. MATCH-only on both endpoints.

    Validation is all-before-any (the G78 resolve-before-write pattern): one
    refused assignment refuses the whole batch, so a partial write cannot
    happen. The summary counts what matched and what found no endpoint —
    an assignment against an absent folder/process writes nothing, silently
    never (the count says so).
    """

    def __init__(self, client) -> None:
        self.client = client

    def assign(self, assignments: Sequence[ConcernsAssignment]) -> dict[str, int]:
        for a in assignments:
            validate(a)
        if not assignments:
            return {"requested": 0, "written": 0, "unmatched": 0}
        rows = [
            {
                "doc_id": a.doc_id,
                "endpoint_class": a.endpoint_class,
                "endpoint_key": a.endpoint_key,
                "assigned_by": a.assigned_by,
                "evidence": a.evidence,
            }
            for a in assignments
        ]
        cypher = CYPHER_PATH.read_text(encoding="utf-8")
        result = self.client.run(
            cypher,
            rows=rows,
            assigned_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        )
        written = int(result[0]["written"]) if result else 0
        return {
            "requested": len(rows),
            "written": written,
            "unmatched": len(rows) - written,
        }
