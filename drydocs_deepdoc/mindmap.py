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

#: The trust axis, verbatim from the one place it is already declared —
#: ``drydocs_core.models.docs``'s ``provenance`` Literal, which every doc-corpus
#: row carries. Restated here rather than imported because those are pydantic
#: row models and this module is plain dataclasses over YAML; the two are held
#: together by a test that reads the Literal's arguments, so they cannot drift.
TRUST_LEVELS: tuple[str, ...] = ("VERBATIM", "GROUNDED", "SYNTHESIZED")

#: MM12 clause (d). A harvested acronym is read out of a corpus by a machine, so
#: it is SYNTHESIZED and never anything else. The point is not the label: it is
#: that a harvested candidate must never be indistinguishable from one an SME
#: supplied, and the only way to guarantee that is for the harvester to be
#: incapable of writing any other value (ADR 0006's corpus-consumer ruling, ADR
#: 0011, tests/unit/test_uncertain_boundary.py for the graph-side half).
HARVESTED_TRUST = "SYNTHESIZED"

_SLOT_KEYS = frozenset({"name", "status", "evidence_ref", "filled_on", "value", "note"})
_BRANCH_KEYS = frozenset({"name", "slots"})
_ACRONYM_KEYS = frozenset({"value", "evidence", "evidence_ref", "trust", "gloss"})
#: ``acronyms`` is ADDITIVE on v1 rather than a v2: a file without the key loads
#: exactly as before and a map with no candidates writes no key, so nothing that
#: exists today changes shape. What it does cost is one direction of
#: compatibility — an OLDER checkout reading a NEWER file refuses on the unknown
#: key, because ``from_document`` rejects unknown top-level keys on purpose. That
#: is acceptable here and is worth saying rather than discovering: the state file
#: is machine-local and untracked (PUBLISH-BOUNDARY.md), so it never travels
#: ahead of the code that reads it.
_MAP_KEYS = frozenset({"schema", "seed", "root_question", "branches", "acronyms"})


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
class AcronymCandidate:
    """One acronym as it was found — the token, and the sentence that gives it meaning.

    MM12. Every other extracted class is useful as a bare token: an issue key
    resolves, a GUID resolves, an application id resolves. An acronym does not.
    ``SNOW`` is worth something only because somebody wrote down that it means
    ServiceNow and explicitly NOT Snowflake, and that sentence is the whole of
    the evidence. So the sentence is a REQUIRED field here, not an optional
    annotation: a candidate that arrived without one would be a string with no
    way to judge it, which is the thing this class exists to avoid.

    ``gloss`` is what a parenthetical said, when the text supplied one. Recorded,
    never resolved — one acronym glossed two ways in two documents is a finding
    to surface, not a conflict to settle here.

    A CANDIDATE, NOT A FACT. Nothing in this dataclass decides what the acronym
    IS. Whether a harvested acronym eventually becomes graph nodes or proposes
    into the config glossary is an open fork nobody has ruled (see the MM12 item
    notes), and the state file is deliberately a place a candidate can sit while
    that stays unanswered.
    """

    value: str
    evidence: str
    evidence_ref: str
    trust: str = HARVESTED_TRUST
    gloss: str | None = None

    def __post_init__(self) -> None:
        if not self.value or not str(self.value).strip():
            raise MindMapError("an acronym candidate with no value")
        if not self.evidence or not str(self.evidence).strip():
            raise MindMapError(
                f"acronym {self.value!r} carries no evidence sentence — the sentence IS "
                "the evidence for this class, so a candidate without one cannot be judged"
            )
        validate_evidence_ref(self.evidence_ref)
        if self.trust not in TRUST_LEVELS:
            raise MindMapError(
                f"acronym {self.value!r}: trust {self.trust!r} is not in {list(TRUST_LEVELS)}"
            )

    @property
    def is_harvested(self) -> bool:
        """Machine-read out of a corpus, rather than supplied by a person."""
        return self.trust == HARVESTED_TRUST


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
    acronyms: tuple[AcronymCandidate, ...] = ()

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

    # -- the acronym shelf ----------------------------------------------------

    def with_acronyms(self, candidates: Iterable[AcronymCandidate]) -> MindMap:
        """A new map carrying ``candidates`` alongside the ones already here.

        DE-DUPLICATED ON (value, evidence_ref, evidence), which is the whole
        design of this method rather than a detail of it. Collapsing on the VALUE
        would keep one reading of ``SNOW`` and throw the other away — and the two
        readings are the finding. Re-harvesting the same sentence from the same
        document adds nothing and is dropped; the same acronym in a second
        sentence, or in a second document, is a second candidate and is kept.

        Order is first-seen, so the file reads in harvest order.
        """
        seen = {(a.value, a.evidence_ref, a.evidence) for a in self.acronyms}
        added: list[AcronymCandidate] = []
        for candidate in candidates:
            key = (candidate.value, candidate.evidence_ref, candidate.evidence)
            if key in seen:
                continue
            seen.add(key)
            added.append(candidate)
        if not added:
            return self
        return replace(self, acronyms=self.acronyms + tuple(added))


# -- harvesting ---------------------------------------------------------------


def harvest_acronyms(text: str, *, evidence_ref: str) -> tuple[AcronymCandidate, ...]:
    """Acronym candidates in ``text``, each carrying the sentence it was found in.

    The extraction is :func:`drydocs_core.entity_extract.extract_entities` — one
    reading shared with the connectors and the novelty score (MM3), never a
    second one here. This function is the adaptation: an ``EntityMatch`` into the
    state file's row, with the trust the item requires and the breadcrumb the
    module's one rule requires.

    ``evidence_ref`` is REQUIRED and validated, so a harvest cannot happen
    without saying which document it came from. That is the same discipline the
    slot transition already enforces, reached one step earlier: a fact with no
    breadcrumb is not written, and a candidate with no breadcrumb is not either.
    """
    from drydocs_core.entity_extract import ACRONYM, extract_entities

    ref = validate_evidence_ref(evidence_ref)
    out: list[AcronymCandidate] = []
    for match in extract_entities(text):
        if match.kind != ACRONYM:
            continue
        out.append(
            AcronymCandidate(
                value=match.value,
                evidence=match.attribute("evidence") or "",
                evidence_ref=ref,
                trust=HARVESTED_TRUST,
                gloss=match.attribute("gloss"),
            )
        )
    return tuple(out)


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
        acronyms=tuple(_acronym_from(a) for a in doc.get("acronyms") or ()),
    )


def _acronym_from(raw: Mapping[str, Any]) -> AcronymCandidate:
    if not isinstance(raw, Mapping):
        raise MindMapError("an acronym entry is not a mapping")
    unknown = set(raw) - _ACRONYM_KEYS
    if unknown:
        raise MindMapError(f"acronym entry has unknown keys {sorted(unknown)}")
    # The trust default lives in the dataclass, not here: a row that omits it
    # reads as harvested, which is the only thing this file ever writes. A row
    # that NAMES a level keeps it, so an SME-supplied entry stays distinguishable
    # once something starts writing one.
    return AcronymCandidate(
        value=str(raw.get("value") or ""),
        evidence=str(raw.get("evidence") or ""),
        evidence_ref=str(raw.get("evidence_ref") or ""),
        trust=str(raw.get("trust") or HARVESTED_TRUST),
        gloss=raw.get("gloss"),
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
    doc: dict[str, Any] = {
        "schema": mm.schema,
        "seed": mm.seed,
        "root_question": mm.root_question,
        "branches": branches,
    }
    # Absent optionals omitted, as everywhere else in this document: a map with
    # no candidates writes no `acronyms` key, so every file that exists today
    # round-trips byte-identically through this change.
    if mm.acronyms:
        doc["acronyms"] = [
            {
                "value": a.value,
                "evidence": a.evidence,
                "evidence_ref": a.evidence_ref,
                "trust": a.trust,
                **({"gloss": a.gloss} if a.gloss is not None else {}),
            }
            for a in mm.acronyms
        ]
    return doc


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
