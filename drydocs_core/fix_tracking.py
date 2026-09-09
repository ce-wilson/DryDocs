"""Fix-tracking change-sets — the vocabulary and the reader both sides share.

Gate ``remediation-fix-tracking`` SIGNED OFF 2026-08-12 (``config/gate-log.md``)
ruled a SEPARATION OF DUTIES: ``drydocs_remediation`` EMITS a
``drydocs.remediation.fix-tracking.v1`` change-set artifact and never writes the
graph (§A2 — NFR-REM-1, the AST guard and the corroborate write-clause regex are
untouched); a dedicated drydocs-load loader APPLIES it (§C1).

Two components, one vocabulary — so the vocabulary lives HERE. The schema id, the
status enum (§B2) and the three ruled property names (§B1) are defined once in
core and imported by both sides, which is what makes §E1's "drift guard" a
structural fact rather than a test comparing two hand-kept copies: there is only
one copy. ``drydocs_remediation.changes`` re-exports the two names it published
first, so its own tested surface is unchanged. This mirrors
``drydocs_core.manual_mappings``: the PURE half (parse, validate, refuse) is core
and shared, the graph-writing half is the loader's and only the loader's.

WHAT THIS MODULE REFUSES, and why each refusal is here rather than in the loader:

* a ``schema`` that is not :data:`FIX_TRACKING_SCHEMA` — a v2 artifact read by a
  v1 loader would apply rulings nobody made;
* a target label outside :data:`TARGET_KEYS` — the ruled targets are the two
  Control-M objects whose NODE KEY ``drydocs_core/schema/constraints.cypher``
  declares, and a fix anchored to anything else has no key to MATCH on;
* a ``node_key`` that is not EXACTLY that label's key fields — a partial key
  matches more nodes than the fix names, and an extra field is a key the graph
  does not have;
* a ``remediation_status`` outside :data:`FIX_STATUS_ENUM` — refused at emission
  already, and refused again here because intake is where a hand-edited artifact
  arrives.

REJECTION IS A MODE, NOT A STATUS (§B2). The ruled enum has no ``rejected``
member: a rejected fix REMOVES the three properties, and the fix package records
the rejection. So the artifact cannot carry the intent — the same v1 change-set
that applied a fix is what un-applies it — and the caller states the mode.
:data:`APPLY` / :data:`REJECT` name it; :func:`parse_change_set` is
mode-agnostic and reads the same bytes either way.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .yaml_fragments import load_yaml_source

#: The artifact schema this reader accepts. Emitted by
#: ``drydocs_remediation.changes.fix_tracking_changeset``.
FIX_TRACKING_SCHEMA = "drydocs.remediation.fix-tracking.v1"

#: The status enum ruled at gate remediation-fix-tracking §B2. 'applied' = the
#: dev team imported the updated XML; 'verified' = the equivalence proof re-ran
#: against the re-exported live definition. There is deliberately no 'rejected'
#: member — see the module docstring.
FIX_STATUS_ENUM = ("proposed", "in_progress", "applied", "verified")

#: The three property names ruled at §B1, in the order the gate names them. The
#: ``remediation_`` prefix keeps this axis visually separate from ``source_*``
#: (the authorship envelope) and ``*_seen_at`` (pull tracking) on any node
#: inspector — §A1 fences the envelope names against reuse here.
FIX_TRACKING_PROPERTIES = (
    "remediation_fix_id",
    "remediation_status",
    "remediation_status_date",
)

#: Loader modes. Not artifact content — the caller's intent (§B2).
APPLY = "apply"
REJECT = "reject"
MODES = (APPLY, REJECT)

#: Target label -> its NODE KEY fields, verbatim from
#: ``drydocs_core/schema/constraints.cypher``. The emitter anchors fixes to
#: exactly these two (``changes.graph_anchors``), and the loader MATCHes on the
#: key — never MERGEs (§C1: a fix target that does not exist is an error, not a
#: node to invent).
TARGET_KEYS: dict[str, tuple[str, ...]] = {
    "ControlMJob": ("folder_id", "job_id"),
    "ControlMFolder": ("folder_id",),
}

#: Label -> the row discriminator the Cypher branches on. Kept beside
#: TARGET_KEYS so adding a third target kind is one edit, not two that can drift.
TARGET_KINDS: dict[str, str] = {
    "ControlMJob": "job",
    "ControlMFolder": "folder",
}


class FixTrackingError(RuntimeError):
    """A fix-tracking change-set is malformed, or names something unruled."""


def _primary_label(labels: list[str], where: str) -> str:
    """The one ruled target label in a target's label list.

    The emitter writes the full label tuple (``("ControlMJob", "Activity")``),
    so this picks the keyed one out rather than requiring a bare label. Two
    ruled labels on one target is refused, not resolved by order — that would
    decide the node key by accident of how the tuple was written.
    """
    ruled = [label for label in labels if label in TARGET_KEYS]
    if not ruled:
        raise FixTrackingError(
            f"{where}: labels {labels!r} name no fix-tracking target — the ruled "
            f"targets are {', '.join(sorted(TARGET_KEYS))} (gate "
            "remediation-fix-tracking §C1; these are the objects "
            "constraints.cypher gives a NODE KEY)"
        )
    if len(ruled) > 1:
        raise FixTrackingError(
            f"{where}: labels {labels!r} name {len(ruled)} fix-tracking targets "
            f"({', '.join(ruled)}) — one target, one node key; which key would "
            "the loader MATCH on?"
        )
    return ruled[0]


def _node_key(label: str, node_key: dict[str, Any], where: str) -> dict[str, Any]:
    """The target's key fields, checked against the label's declared NODE KEY."""
    required = TARGET_KEYS[label]
    given = set(node_key)
    missing = [field for field in required if field not in given]
    extra = sorted(given - set(required))
    if missing or extra:
        detail = []
        if missing:
            detail.append(f"missing {', '.join(missing)}")
        if extra:
            detail.append(f"unexpected {', '.join(extra)}")
        raise FixTrackingError(
            f"{where}: node_key {sorted(given)} is not the :{label} NODE KEY "
            f"({', '.join(required)}) — {'; '.join(detail)}. A partial key "
            "matches more nodes than the fix names."
        )
    for field in required:
        if node_key[field] in (None, ""):
            raise FixTrackingError(
                f"{where}: node_key.{field} is empty — a fix target with no key "
                "cannot be MATCHed, and this loader never invents one (§C1)."
            )
    return {field: node_key[field] for field in required}


def _properties(target: dict[str, Any], fix_id: str, where: str) -> dict[str, Any]:
    """The three ruled properties, checked for the enum and for fix-id agreement."""
    props = target.get("proposed_properties")
    if not isinstance(props, dict):
        raise FixTrackingError(
            f"{where}: no proposed_properties mapping — a target that proposes "
            "nothing is not a fix-tracking target."
        )
    missing = [name for name in FIX_TRACKING_PROPERTIES if name not in props]
    extra = sorted(set(props) - set(FIX_TRACKING_PROPERTIES))
    if missing or extra:
        detail = []
        if missing:
            detail.append(f"missing {', '.join(missing)}")
        if extra:
            detail.append(f"unruled {', '.join(extra)}")
        raise FixTrackingError(
            f"{where}: proposed_properties must be exactly "
            f"{', '.join(FIX_TRACKING_PROPERTIES)} (gate remediation-fix-tracking "
            f"§B1) — {'; '.join(detail)}."
        )
    status = props["remediation_status"]
    if status not in FIX_STATUS_ENUM:
        raise FixTrackingError(
            f"{where}: unknown remediation_status {status!r} — the ruled enum is "
            f"{' | '.join(FIX_STATUS_ENUM)} (§B2). There is no 'rejected' state: "
            "rejection REMOVES the properties, which is the loader's reject mode, "
            "not an artifact value."
        )
    if props["remediation_fix_id"] != fix_id:
        raise FixTrackingError(
            f"{where}: remediation_fix_id {props['remediation_fix_id']!r} "
            f"disagrees with the change-set's fix_id {fix_id!r} — one change-set "
            "carries one fix (§B3: one last-transition date per node)."
        )
    date = props["remediation_status_date"]
    if not str(date).strip():
        raise FixTrackingError(
            f"{where}: remediation_status_date is empty — §B3 rules ONE date "
            "carrying the last transition; an absent one makes the node's status "
            "unreadable."
        )
    return {name: props[name] for name in FIX_TRACKING_PROPERTIES}


def parse_change_set(path: str | Path) -> list[dict[str, Any]]:
    """Read a fix-tracking change-set into flat loader rows.

    One row per target, carrying the row discriminator (``kind``), the label's
    NODE KEY fields flattened (``folder_id``, and ``job_id`` for job targets —
    ``None`` for folders so every row has the same shape and the Cypher can
    UNWIND one batch), the display name for the operator-facing report, and the
    three ruled properties.

    Every refusal names the target by index and by display name: a change-set
    arrives as a file from another machine, so "target 3 (DAILY_EXTRACT)" is the
    difference between a fixable message and a re-read of the YAML.
    """
    path = Path(path)
    if not path.exists():
        raise FixTrackingError(f"fix-tracking change-set not found: {path}")
    payload = load_yaml_source(path)
    if not isinstance(payload, dict):
        raise FixTrackingError(f"{path}: not a fix-tracking change-set (expected a mapping)")

    schema = payload.get("schema")
    if schema != FIX_TRACKING_SCHEMA:
        raise FixTrackingError(
            f"{path}: schema {schema!r} is not {FIX_TRACKING_SCHEMA!r} — this "
            "loader applies rulings made for v1 and cannot read another version's "
            "artifact as if they were the same."
        )
    fix_id = payload.get("fix_id")
    if not fix_id:
        raise FixTrackingError(
            f"{path}: no fix_id — remediation_fix_id is the fix package / Jira "
            "reference the whole axis hangs off (§B1)."
        )
    targets = payload.get("targets")
    if not isinstance(targets, list) or not targets:
        raise FixTrackingError(
            f"{path}: no targets — a change-set that names no node applies nothing."
        )

    rows: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for index, target in enumerate(targets):
        display = target.get("display_name", "?") if isinstance(target, dict) else "?"
        where = f"{path}: target {index} ({display})"
        if not isinstance(target, dict):
            raise FixTrackingError(f"{where}: not a mapping")
        labels = target.get("labels")
        if not isinstance(labels, list) or not labels:
            raise FixTrackingError(f"{where}: no labels — nothing says what kind of node this is")
        label = _primary_label(labels, where)
        node_key = _node_key(label, target.get("node_key") or {}, where)
        props = _properties(target, fix_id, where)

        identity = (label, *(node_key[field] for field in TARGET_KEYS[label]))
        if identity in seen:
            raise FixTrackingError(
                f"{where}: :{label} {node_key} appears twice in one change-set — "
                "two rows for one node race each other to set the same three "
                "properties, and which one lands is batch order."
            )
        seen.add(identity)

        rows.append(
            {
                "kind": TARGET_KINDS[label],
                "label": label,
                "folder_id": node_key["folder_id"],
                "job_id": node_key.get("job_id"),
                "display_name": str(display),
                **props,
            }
        )
    return rows
