"""The mind-map state file — the investigation's backlog, as data the loop reads.

MM3 (epic MM, docs/design/deepdoc-data-flow-overview.md §6). In the hand-run
investigation the mind map was a chat artifact: branches for the things that
had to be learned, a trailing ``?`` on every slot nobody had filled, and the
next search aimed at the next ``?``. It worked, and it was lost with the
session. This module makes it a file — ``drydocs.deepdoc.mindmap.v1`` — so the
map is what DRIVES ``investigate()`` (MM10: "pick the open slot with the highest
expected novelty") rather than something written up afterwards.

THE ONE RULE: a slot moves to ``filled`` only with an evidence ref and a date.
That is enforced twice, deliberately. On the transition (:meth:`MindMap.fill`
refuses without a ref), because that is where a loop would cut the corner; and
on load (a file whose slot says ``filled`` and carries no ref is refused), because
the other machine, or an earlier session, may have written the file, and a map
that reads as more complete than its evidence is worse than no map. A fact with
no breadcrumb is not written — the same discipline the data-flow-overview gate
(§E, confirmation 3) asks of the graph writer, applied one step earlier.

THE EVIDENCE REF is ``<kind>:<rest>`` with ``kind`` one of the six source kinds
the design doc's §2 ``evidence[]`` row enumerates: ``email``, ``log``, ``jira``,
``commit``, ``confluence``, ``transcript``. That shape is deliberately the part
common to every option the gate has not yet ruled between — E1 (a URN list on
the node), E2 (an edge to a corpus node per kind) and E3 (both): E1 and E3 use
this URN as the identity, and E2 needs the kind to know which corpus node to
resolve. What a ref RESOLVES to is MM10's business and the gate's ruling; this
module only refuses a ref that names no kind.

The file, by example::

    schema: drydocs.deepdoc.mindmap.v1
    seed: <folder>                   # the graph subject the map is about
    root_question: what is this flow, why does it exist, and why does it keep failing?
    branches:
    - name: ownership
      slots:
      - name: producer_app
        status: filled
        evidence_ref: confluence:<page-id>
        filled_on: 2026-08-20
        value: APP_ID-producer
      - name: consumer_app
        status: open

Mechanism only: every value above is a role placeholder; the real map for a real
seed is machine-local and never tracked (PUBLISH-BOUNDARY.md).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from datetime import date
from pathlib import Path
from typing import Any

SCHEMA = "drydocs.deepdoc.mindmap.v1"

OPEN = "open"
FILLED = "filled"
STATUSES: tuple[str, ...] = (OPEN, FILLED)

#: The six source kinds of the design doc's §2 ``evidence[]`` row. A ref is
#: ``<kind>:<rest>``; the kind is validated here, the rest is not.
EVIDENCE_KINDS: tuple[str, ...] = ("email", "log", "jira", "commit", "confluence", "transcript")

#: The central question of the hand-run investigation, verbatim from the design
#: doc's read-me-first — the default root a new map starts from.
ROOT_QUESTION = "what is this flow, why does it exist, and why does it keep failing?"

#: The §6 branches, in the order the session used them, each carrying the §2
#: record fields that belong to it. :func:`new_mindmap` builds a map from this,
#: which is what lets MM10 "load or create the state for the record fields
#: still unknown" without hand-listing them. ``open_questions`` and
#: ``evidence[]`` are not slots: the first IS the open-slot set, the second is
#: what fills one.
RECORD_SLOTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("business", ("business_purpose", "ingest_mode")),
    ("naming", ("flow_id", "launcher_kinds")),
    (
        "control-m",
        (
            "members",
            "zone_chain",
            "watchers",
            "tdq_self_asserted",
            "compute_target",
            "placement_handoff",
            "landing_prefix",
        ),
    ),
    ("lineage", ("pipeline_ids", "dataset_ids")),
    ("ownership", ("owner_app", "producer_app", "consumer_app", "support_dls", "producer_contact")),
    ("references", ("sdlc_anchors",)),
)

_SLOT_KEYS = frozenset({"name", "status", "evidence_ref", "filled_on", "value", "note"})
_BRANCH_KEYS = frozenset({"name", "slots"})
_MAP_KEYS = frozenset({"schema", "seed", "root_question", "branches"})


class MindMapError(ValueError):
    """The state file, or a change to it, breaks the one rule — never a silent repair."""


def validate_evidence_ref(ref: object) -> str:
    """``<kind>:<rest>`` with a known kind and a non-empty rest, or a refusal."""
    if not isinstance(ref, str) or not ref.strip():
        raise MindMapError("a slot fills only with an evidence ref — none was given")
    kind, sep, rest = ref.strip().partition(":")
    if not sep or kind not in EVIDENCE_KINDS or not rest.strip():
        raise MindMapError(
            f"evidence ref {ref!r} is not <kind>:<rest> with kind in {list(EVIDENCE_KINDS)} "
            "(design doc §2, the evidence[] breadcrumb grammar)"
        )
    return ref.strip()


@dataclass(frozen=True)
class Slot:
    """One thing to learn about the seed. ``open`` is the trailing ``?``."""

    name: str
    status: str = OPEN
    evidence_ref: str | None = None
    filled_on: date | None = None
    value: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if not self.name or not str(self.name).strip():
            raise MindMapError("a slot with no name cannot be targeted by a search")
        if self.status not in STATUSES:
            raise MindMapError(f"slot {self.name!r}: status {self.status!r} is not in {STATUSES}")
        if self.status == FILLED:
            validate_evidence_ref(self.evidence_ref)
            if not isinstance(self.filled_on, date):
                raise MindMapError(f"slot {self.name!r} is filled but carries no filled_on date")
        elif self.evidence_ref is not None or self.filled_on is not None:
            raise MindMapError(
                f"slot {self.name!r} is open but carries evidence — fill it, or drop the ref"
            )

    @property
    def is_open(self) -> bool:
        return self.status == OPEN


@dataclass(frozen=True)
class Branch:
    name: str
    slots: tuple[Slot, ...] = ()

    def __post_init__(self) -> None:
        if not self.name or not str(self.name).strip():
            raise MindMapError("a branch with no name")
        names = [s.name for s in self.slots]
        if len(set(names)) != len(names):
            raise MindMapError(f"branch {self.name!r} repeats a slot name: {names}")


@dataclass(frozen=True)
class MindMap:
    seed: str
    root_question: str
    branches: tuple[Branch, ...] = field(default_factory=tuple)
    schema: str = SCHEMA

    def __post_init__(self) -> None:
        if self.schema != SCHEMA:
            raise MindMapError(f"schema {self.schema!r} is not {SCHEMA!r}")
        if not self.seed or not str(self.seed).strip():
            raise MindMapError("a mind map needs a seed — the graph subject it is about")
        if not self.root_question or not str(self.root_question).strip():
            raise MindMapError("a mind map needs a root question — the evaluation criterion")
        names = [b.name for b in self.branches]
        if len(set(names)) != len(names):
            raise MindMapError(f"branch names repeat: {names}")

    # -- reading ------------------------------------------------------------

    def branch(self, name: str) -> Branch:
        for b in self.branches:
            if b.name == name:
                return b
        raise MindMapError(f"no branch {name!r} — have {[b.name for b in self.branches]}")

    def slot(self, branch: str, name: str) -> Slot:
        b = self.branch(branch)
        for s in b.slots:
            if s.name == name:
                return s
        raise MindMapError(
            f"no slot {name!r} on branch {branch!r} — have {[s.name for s in b.slots]}"
        )

    def open_slots(self) -> tuple[tuple[str, str], ...]:
        """Every ``(branch, slot)`` still open, in file order — the loop's worklist."""
        return tuple((b.name, s.name) for b in self.branches for s in b.slots if s.is_open)

    # -- the one transition ---------------------------------------------------

    def fill(
        self,
        branch: str,
        name: str,
        *,
        evidence_ref: str,
        filled_on: date | None = None,
        value: str | None = None,
        note: str | None = None,
    ) -> MindMap:
        """A new map with ``(branch, name)`` filled — refused without an evidence ref.

        Filling an already-filled slot is allowed and replaces the evidence: a
        better citation may arrive later, and the map records the current best.
        Returns a new value; the receiver is unchanged.
        """
        ref = validate_evidence_ref(evidence_ref)
        current = self.slot(branch, name)  # raises for an unknown target
        filled = replace(
            current,
            status=FILLED,
            evidence_ref=ref,
            filled_on=filled_on or date.today(),
            value=value if value is not None else current.value,
            note=note if note is not None else current.note,
        )
        branches = tuple(
            replace(b, slots=tuple(filled if s.name == name else s for s in b.slots))
            if b.name == branch
            else b
            for b in self.branches
        )
        return replace(self, branches=branches)


# -- construction -------------------------------------------------------------


def new_mindmap(
    seed: str,
    root_question: str = ROOT_QUESTION,
    layout: Iterable[tuple[str, Iterable[str]]] = RECORD_SLOTS,
) -> MindMap:
    """A fresh map for ``seed`` with every slot open — the §2 record fields under
    the §6 branches by default, or any ``(branch, slot names)`` layout."""
    branches = tuple(
        Branch(name=b, slots=tuple(Slot(name=s) for s in slots)) for b, slots in layout
    )
    return MindMap(seed=seed, root_question=root_question, branches=branches)


# -- the file -------------------------------------------------------------------


def _slot_from(raw: Mapping[str, Any], branch: str) -> Slot:
    unknown = set(raw) - _SLOT_KEYS
    if unknown:
        raise MindMapError(f"branch {branch!r}: slot has unknown keys {sorted(unknown)}")
    filled_on = raw.get("filled_on")
    if isinstance(filled_on, str):
        try:
            filled_on = date.fromisoformat(filled_on)
        except ValueError as exc:
            raise MindMapError(
                f"branch {branch!r} slot {raw.get('name')!r}: filled_on {filled_on!r} is not a date"
            ) from exc
    return Slot(
        name=str(raw.get("name") or ""),
        status=str(raw.get("status") or OPEN),
        evidence_ref=raw.get("evidence_ref"),
        filled_on=filled_on,
        value=raw.get("value"),
        note=raw.get("note"),
    )


def from_document(doc: Mapping[str, Any]) -> MindMap:
    """A map from the parsed YAML document — every rule of the dataclasses applies."""
    if not isinstance(doc, Mapping):
        raise MindMapError("the mind-map document is not a mapping")
    unknown = set(doc) - _MAP_KEYS
    if unknown:
        raise MindMapError(f"unknown top-level keys {sorted(unknown)} — the schema is {SCHEMA}")
    branches: list[Branch] = []
    for raw_b in doc.get("branches") or ():
        if not isinstance(raw_b, Mapping):
            raise MindMapError("a branch entry is not a mapping")
        unknown = set(raw_b) - _BRANCH_KEYS
        if unknown:
            raise MindMapError(f"branch has unknown keys {sorted(unknown)}")
        b_name = str(raw_b.get("name") or "")
        raw_slots = raw_b.get("slots") or ()
        if not all(isinstance(s, Mapping) for s in raw_slots):
            raise MindMapError(f"branch {b_name!r}: a slot entry is not a mapping")
        branches.append(Branch(name=b_name, slots=tuple(_slot_from(s, b_name) for s in raw_slots)))
    return MindMap(
        seed=str(doc.get("seed") or ""),
        root_question=str(doc.get("root_question") or ""),
        branches=tuple(branches),
        schema=str(doc.get("schema") or ""),
    )


def to_document(mm: MindMap) -> dict[str, Any]:
    """The YAML-ready document — keys in schema order, absent optionals omitted."""
    branches = []
    for b in mm.branches:
        slots = []
        for s in b.slots:
            row: dict[str, Any] = {"name": s.name, "status": s.status}
            if s.evidence_ref is not None:
                row["evidence_ref"] = s.evidence_ref
            if s.filled_on is not None:
                row["filled_on"] = s.filled_on.isoformat()
            if s.value is not None:
                row["value"] = s.value
            if s.note is not None:
                row["note"] = s.note
            slots.append(row)
        branches.append({"name": b.name, "slots": slots})
    return {
        "schema": mm.schema,
        "seed": mm.seed,
        "root_question": mm.root_question,
        "branches": branches,
    }


def loads(text: str) -> MindMap:
    import yaml

    return from_document(yaml.safe_load(text) or {})


def dumps(mm: MindMap) -> str:
    import yaml

    return yaml.safe_dump(to_document(mm), sort_keys=False, allow_unicode=True)


def load_mindmap(path: Path) -> MindMap:
    return loads(Path(path).read_text(encoding="utf-8"))


def save_mindmap(mm: MindMap, path: Path) -> Path:
    """Write the map; the parent directory is created. Returns the path."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dumps(mm), encoding="utf-8", newline="\n")
    return target
