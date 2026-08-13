"""Approved change-sets: the join between analysis and emission, plus fix tracking.

TWO LANES, ONE JOIN (the xml_io design). Lane A is analysis — detectors and
Tier-1 rules over format-agnostic ``DefinitionSet``s. Lane B is emission —
``xml_io.EditScript`` splices over the original bytes. This module is the join:
it turns approved changes (each carrying its gate approval id) into EditScript
calls addressed by DOMAIN COORDINATES (``Locator``), and it is the ONLY module
that knows what "approved" means. xml_io refuses unattributed edits by
signature; this module refuses UNAPPROVED changes by construction —
``compile_changes`` takes :class:`ApprovedChange` only, and the dataclass
cannot be built without an ``approval_id``.

FIX TRACKING WITHOUT A GRAPH WRITE (user ruling 2026-08-12). The component's
no-graph-write invariant is structural (AST guard + the corroborate regex), so
trackability is delivered as an ARTIFACT: :func:`fix_tracking_changeset` emits
a YAML change-set naming the target nodes by their NODE KEY — ``(folder_id,
job_id)`` for ``:ControlMJob``, ``folder_id`` for ``:ControlMFolder``, per
``drydocs_core/schema/constraints.cypher`` — which a write-authorized loader
applies with the standard idiom (UNWIND $batch, MERGE on the business key).
The PROPERTY NAMES ride as ``proposed_properties`` and are RATIFIED — gate
``remediation-fix-tracking`` SIGNED OFF 2026-08-12 ruled the three names, the
status enum (:data:`FIX_STATUS_ENUM`), and the writer (a dedicated
drydocs-load loader). The four envelope properties stay source-system
authorship, fenced against reinterpretation (§A1).

GRAPH ANCHORS are read-only: :func:`graph_anchors` resolves the fix's start
and end points to real node identities (labels, node-key properties, display
names, active relationship types) through :class:`~.corroborate.ReadOnlyGraph`
— the identities land in the change doc so the fix package cites the graph
the way the graph actually keys things. The hand-made ``folder/job_name``
fallback identity is refused, mirroring the lineage writer's rule.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .corroborate import ReadOnlyGraph
from .xml_io import EditScript, Effect, Locator, XmlDocument, locate

FIX_TRACKING_SCHEMA = "drydocs.remediation.fix-tracking.v1"

#: the status enum ruled at gate remediation-fix-tracking §B2 (SIGNED OFF
#: 2026-08-12, config/gate-log.md). No "rejected" state: a rejected fix
#: removes the properties; the package records the rejection.
FIX_STATUS_ENUM = ("proposed", "in_progress", "applied", "verified")


def _citable_relationships() -> tuple[str, ...]:
    """The relationship types a change doc may cite: every ``status: active``
    label of the scheduler domain, read from the registry itself. Derived, not
    hand-mirrored — the hand-kept tuple drifted (it predated the G22 flips and
    missed USES_ARTIFACT/READS_FROM/WRITES_TO/CONTAINS_HOST). Planned entries
    (m3_triggers, ...) are absent because the filter says so, not by memory."""
    from drydocs_core.ontology.schema_graph import DEFAULT_VOCAB_PATH
    from drydocs_core.yaml_fragments import load_yaml_source

    registry = load_yaml_source(DEFAULT_VOCAB_PATH)
    labels: list[str] = []
    for entry in registry["local_relationships"]:
        if entry["domain"] == "scheduler" and entry["status"] == "active":
            if entry["neo4j_label"] not in labels:
                labels.append(entry["neo4j_label"])
    return tuple(labels)


CITABLE_RELATIONSHIPS = _citable_relationships()


class UnanchoredFixError(RuntimeError):
    """A fix target could not be resolved to a canonical graph identity."""


# --------------------------------------------------------------------------- #
# Approved changes → EditScript
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ApprovedChange:
    """One gate-approved change, addressed by domain coordinates.

    ``approval_id`` is the gate-log reference (§XML rule 3: each mutation maps
    1:1 to an approved change). ``kind`` vocabulary mirrors the EditScript
    surface; ``rename-variable`` compiles to the whole-scope reference sweep,
    never a field list — that is defect A′'s fix made unavoidable.
    """

    approval_id: str
    kind: str  # set-attribute | add-attribute | remove-attribute |
    #          # insert-element | delete-element | rename-variable
    locator: Locator
    #: set/add/remove: the attribute name; insert: the tag; rename: the OLD bare name
    detail: str
    value: str | None = None  # new value / NEW bare name for renames
    #: insert-element only: the new element's attributes in document order
    attributes: tuple[tuple[str, str], ...] = ()
    evidence: str = ""  # what/why, carried into the change doc


def compile_changes(
    doc: XmlDocument, changes: list[ApprovedChange]
) -> tuple[EditScript, list[Effect]]:
    """Turn approved changes into an attributed EditScript.

    Returns the script and every effect it enumerated (the change-doc feed).
    Locator misses and ambiguities raise — an approved change that no longer
    addresses exactly one element is a stale approval, not a best-effort edit.
    """
    script = EditScript(doc)
    effects: list[Effect] = []
    for change in changes:
        node = locate(doc, change.locator)
        if change.kind == "set-attribute":
            effects.append(
                script.set_attribute(
                    node, change.detail, change.value or "", change_id=change.approval_id
                )
            )
        elif change.kind == "add-attribute":
            effects.append(
                script.add_attribute(
                    node, change.detail, change.value or "", change_id=change.approval_id
                )
            )
        elif change.kind == "remove-attribute":
            effects.append(
                script.remove_attribute(node, change.detail, change_id=change.approval_id)
            )
        elif change.kind == "insert-element":
            effects.append(
                script.insert_element(
                    node, change.detail, list(change.attributes), change_id=change.approval_id
                )
            )
        elif change.kind == "delete-element":
            effects.append(script.delete_element(node, change_id=change.approval_id))
        elif change.kind == "rename-variable":
            effects.extend(
                script.replace_reference_tokens(
                    node, change.detail, change.value or "", change_id=change.approval_id
                )
            )
        else:
            raise ValueError(f"unknown change kind {change.kind!r} ({change.approval_id})")
    return script, effects


# --------------------------------------------------------------------------- #
# Graph anchors (read-only)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class FixAnchor:
    """One fix target as the graph actually keys it."""

    labels: tuple[str, ...]  # e.g. ("ControlMJob", "Activity")
    node_key: dict  # {"folder_id": ..., "job_id": ...} — the NODE KEY, verbatim
    display_name: str  # job_name / sched_table
    relationships: tuple[str, ...] = ()  # citable, active types touching the node


# DC disambiguation joins through the graph's own model — the folder node
# carries no data_center property; the server node does (controlm_folders
# cypher: one :ControlMServer per DATA_CENTER, folders SCHEDULED_ON it).
# $data_center = '' matches any server, and ambiguity is REFUSED below.
_JOB_ANCHOR_QUERY = """
MATCH (f:ControlMFolder {sched_table: $folder_name})-[:CONTAINS_JOB]->(j:ControlMJob {job_name: $job_name})
MATCH (f)-[:SCHEDULED_ON]->(srv:ControlMServer)
WHERE $data_center = '' OR srv.name = $data_center
RETURN f.folder_id AS folder_id, j.job_id AS job_id, j.job_name AS job_name
"""

_FOLDER_ANCHOR_QUERY = """
MATCH (f:ControlMFolder {sched_table: $folder_name})-[:SCHEDULED_ON]->(srv:ControlMServer)
WHERE $data_center = '' OR srv.name = $data_center
RETURN f.folder_id AS folder_id, f.sched_table AS sched_table, srv.name AS data_center
"""


def graph_anchors(
    graph: ReadOnlyGraph, folder_name: str, job_names: list[str], *, data_center: str = ""
) -> list[FixAnchor]:
    """Resolve the fix's start/end points to canonical node identities.

    Refuses (``UnanchoredFixError``) when a target has no canonical key —
    the ``folder/job_name`` fallback identity is exactly what the lineage
    writer refuses, and a fix package citing an invented id would be worse
    than one citing none. Also refuses AMBIGUITY: folder names are only
    unique per data center, so a name matching folders on more than one
    server without ``data_center`` given would anchor the fix to whichever
    row came back first — the silent wrong-anchor case.
    """
    anchors: list[FixAnchor] = []
    params = {"folder_name": folder_name, "data_center": data_center}
    folder_rows = graph.fetch(_FOLDER_ANCHOR_QUERY, params)
    if not folder_rows:
        raise UnanchoredFixError(
            f"folder {folder_name!r} has no :ControlMFolder node"
            + (f" on server {data_center!r}" if data_center else "")
            + " — load it before anchoring a fix to it (canonical keys, not invented ids)"
        )
    if len(folder_rows) > 1:
        servers = sorted({r["data_center"] for r in folder_rows})
        raise UnanchoredFixError(
            f"folder {folder_name!r} exists on {len(folder_rows)} servers "
            f"({', '.join(servers)}) — folder names are only unique per data "
            "center; pass data_center"
        )
    row = folder_rows[0]
    anchors.append(
        FixAnchor(
            labels=("ControlMFolder", "Collection"),
            node_key={"folder_id": row["folder_id"]},
            display_name=row["sched_table"],
            relationships=("CONTAINS_JOB",),
        )
    )
    for job_name in job_names:
        rows = graph.fetch(_JOB_ANCHOR_QUERY, {**params, "job_name": job_name})
        if not rows:
            raise UnanchoredFixError(
                f"job {job_name!r} under {folder_name!r} has no :ControlMJob node"
            )
        row = rows[0]
        anchors.append(
            FixAnchor(
                labels=("ControlMJob", "Activity"),
                node_key={"folder_id": row["folder_id"], "job_id": row["job_id"]},
                display_name=row["job_name"],
                relationships=tuple(
                    r for r in CITABLE_RELATIONSHIPS if r not in ("CONTAINS_FOLDER",)
                ),
            )
        )
    return anchors


# --------------------------------------------------------------------------- #
# Fix-tracking change-set (the write another component applies)
# --------------------------------------------------------------------------- #


@dataclass
class FixTrackingChangeset:
    """The proposal a write-authorized loader turns into node properties."""

    fix_id: str  # the fix package / Jira reference
    status: str  # proposed | in_progress | applied | verified
    date: str  # ISO date, caller-supplied (artifacts are deterministic)
    anchors: list[FixAnchor] = field(default_factory=list)
    approvals: list[str] = field(default_factory=list)  # gate approval ids


def fix_tracking_changeset(changeset: FixTrackingChangeset, target: Path) -> Path:
    """Write the fix-tracking change-set artifact.

    The property NAMES and status enum are RATIFIED (gate
    remediation-fix-tracking, SIGNED OFF 2026-08-12 — §B1 names, §B2 enum,
    §B3 one last-transition date, §C1 the dedicated drydocs-load writer that
    MATCHes on the NODE KEY and never MERGE-creates a target). The artifact
    still carries everything a loader needs EXCEPT the authority to apply it —
    the SoD boundary is unchanged (§A2).
    """
    if changeset.status not in FIX_STATUS_ENUM:
        raise ValueError(
            f"unknown remediation_status {changeset.status!r} — the ruled enum "
            f"is {' | '.join(FIX_STATUS_ENUM)} (gate remediation-fix-tracking §B2; "
            "there is no 'rejected' state: rejection removes the properties)"
        )
    payload = {
        "schema": FIX_TRACKING_SCHEMA,
        "fix_id": changeset.fix_id,
        "gate": {
            "status": "RATIFIED",
            "ruling": "remediation-fix-tracking — SIGNED OFF 2026-08-12 (config/gate-log.md)",
            "note": (
                "property names and status enum ruled at the gate; the writer is "
                "the dedicated drydocs-load fix-tracking loader (§C1). Envelope "
                "properties (source_created_by/at, source_updated_by/at) are "
                "source-system authorship and MUST NOT be reused here."
            ),
        },
        "approvals": list(changeset.approvals),
        "targets": [
            {
                "labels": list(anchor.labels),
                "node_key": dict(anchor.node_key),
                "display_name": anchor.display_name,
                "proposed_properties": {
                    "remediation_fix_id": changeset.fix_id,
                    "remediation_status": changeset.status,
                    "remediation_status_date": changeset.date,
                },
            }
            for anchor in changeset.anchors
        ],
    }
    target.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return target
