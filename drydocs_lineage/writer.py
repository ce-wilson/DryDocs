"""The lineage write boundary — curated lineage → the ``drydocs`` ground truth.

This is the ONLY module in the component that writes a database, and it writes
only :data:`DATABASE` (``drydocs``). Fork-3 mechanics — depgraph's *planned*
``profiles/drydocs.py``, built here per ADR 0002-C §4 (never existed depgraph-side):
constraint-on-key MERGE via UNWIND batches; no ``CYPHER 25`` (match the load
profile).

Split in two so review and load stay distinct:

- :func:`plan_curated` — PURE. Validates the contract and returns the exact
  Cypher batches a live load would run. Always allowed: the plan is gate
  material (what the SME reviews), not a write.
- :func:`write_curated` — the live load. Refuses unless every check passes.

Refusals (each is a contract, not a warning):

- **Curated-only** (D2): only rels in ``confirmed`` — the curation output — are
  written, and every confirmed rel must exist in the graph.
- **Identity** (0002-C §4): ControlMJob endpoints must carry the NODE-KEY
  composite (``folder_id.job_id``); the hand-made-CSV fallback identity
  (``folder/job_name``) is refused — canonical keys, not invented ids.
- **Trust boundary** (D2): the client must be bound to ``drydocs`` —
  :class:`TrustBoundaryError` otherwise. Never ``ddcontext``.
- **Gate-bound vocabulary**: the four rel labels are registered ``status:
  planned`` (``model.VOCAB_IDS``); a live load raises
  :class:`GateBoundVocabularyError` until the HITL gate flips them ``active``
  in ``relationship_vocabulary.yaml``. The gate cannot be reasoned around in
  code — it is a registry read.

Node mechanics: ControlMJob endpoints are **MATCHed, never MERGEd** — the M3
load owns those nodes (a lineage-created job stub would violate the m3-verify
"every job has a folder" invariant). Scripts, ETLProcess, and DataAssets are
MERGEd on their business keys (``Script.path``; ``ETLProcess.token`` — the SAME
kind-scoped stable token ``controlm_inventory._stable_invocation_key`` already
computes for Ab Initio/DPL invocations (G12; gate-log 2026-07-16
"cmdline-lineage-review" §b) — full path / dataflow / config-JSON path ride as
properties, never identity; ``DataAsset.assetId`` — the D1 proxy URN,
``provisioning/02_proxy_constraints.cypher``), with their constraints ensured
first (constraint-on-key rule).

File-ops endpoint resolution (G13; gate-log 2026-07-15 "reads/writes shapes
EDITED"): ``m3_reads_from`` / ``m3_writes_to`` from_node is ``ETLProcess |
ControlMJob`` — never ``Script``, because :Script is a prov:Entity and cannot
carry prov:used/generated. The ETL case (an ``_ETL_PROCESS_KINDS`` src) keeps
its ETLProcess Activity as-is. The file-ops case (a plain wrapper script doing
unix moves/gzips, no ETL engine involved) has no Activity of its own — before
grouping, :func:`plan_curated` re-points the candidate's src from the script to
the ControlMJob(s) that INVOKE it (:func:`_owning_jobs`, a lookup over the
graph's own INVOKES rels, independent of what else is in this write batch). A
script invoked by more than one job fans the candidate out to every owning job
(each job-run performs the file op); a script with no owning job in the graph
cannot be planned as a Script-sourced edge, so the candidate is dropped —
counted in ``WritePlan.unresolved_file_ops`` so review sees the loss, never a
silent shrink.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import drydocs_core.ontology as _core_ontology

from .model import VOCAB_IDS, LineageGraph

#: The write target — ground truth. The trust axis IS the DB boundary (ADR 0002 D1).
DATABASE = "drydocs"

#: the registered vocabulary (single source of truth for gate status)
_VOCAB_REGISTRY = Path(_core_ontology.__file__).resolve().parent / "relationship_vocabulary.yaml"

_JOB_KIND = "controlm_job"

#: invocation "engine" kinds that get their own :ETLProcess endpoint class
#: instead of :Script (G12; gate-log 2026-07-16 "cmdline-lineage-review" §b).
#: Identity is the SAME kind-scoped stable token the extractor already computes
#: in ``controlm_inventory._stable_invocation_key`` for exactly these two kinds
#: (everything else falls through to the full-target/path key Script already
#: uses) — keep this set in sync with that function's special-casing.
_ETL_PROCESS_KINDS = {"abinitio", "dpl"}

#: the ETLProcess ``kind`` property (etl | utility | notification — gate-log §a).
#: AMBIGUITY CALL (G12, guardrail 5): the invocation engine alone cannot
#: distinguish a real ETL pset/pipeline from a utility one (e.g. the
#: script-exec / send-email psets the gate log names) — a node with no better
#: signal stamps 'etl'. The discriminating signal now EXISTS where DPL MAC
#: metadata was ingested (G17): the dpl_mac extractor derives
#: ``properties["mac_kind"]`` from pipeline.json subType, and the row build
#: below consults it first — only non-MAC nodes still take the blind default.
_DEFAULT_ETL_KIND = "etl"

#: rel labels whose from_node is "ETLProcess | ControlMJob", never Script
#: (gate-log 2026-07-15 EDIT; G13). Endpoint resolution below only special-
#: cases these two — INVOKES/TRIGGERS srcs are untouched.
_FILE_OPS_TYPES = {"READS_FROM", "WRITES_TO"}


class GateBoundVocabularyError(RuntimeError):
    """A live load was attempted while the rel vocabulary is not yet ``active``."""


class TrustBoundaryError(RuntimeError):
    """A live load was attempted against a database other than ``drydocs``."""


# --- vocabulary gate ----------------------------------------------------------

_ID_RE = re.compile(r"^\s*-\s*id:\s*(\S+)")
_STATUS_RE = re.compile(r"^\s*status:\s*(\S+)")


def vocabulary_status(
    vocab_ids: Iterable[str], registry: Path | None = None
) -> dict[str, str]:
    """``id → status`` for the requested entries, read from the registry.

    Deliberately a line scan (id, then the first status under it) rather than a
    YAML dependency — the registry format is stable and guarded by tests; the
    gate must be readable everywhere the component imports.
    """
    wanted = set(vocab_ids)
    statuses: dict[str, str] = {}
    current: str | None = None
    for line in (registry or _VOCAB_REGISTRY).read_text(encoding="utf-8").splitlines():
        m = _ID_RE.match(line)
        if m:
            current = m.group(1)
            continue
        m = _STATUS_RE.match(line)
        if m and current in wanted and current not in statuses:
            statuses[current] = m.group(1)
    return statuses


# --- identity helpers -----------------------------------------------------------

def _node_key(node_id: str) -> str:
    """The business key inside a namespaced id (``proc#kind:KEY`` / ``data#kind:KEY``)."""
    return node_id.split(":", 1)[1]


def _job_composite(node_id: str) -> tuple[str, str]:
    """``(folder_id, job_id)`` from a controlm_job process id — refuse fallbacks."""
    key = _node_key(node_id)
    folder_id, dot, job_id = key.partition(".")
    if "/" in key or not dot or not folder_id or not job_id:
        raise ValueError(
            f"job {node_id!r} lacks the ControlMJob NODE-KEY composite "
            "(folder_id.job_id) — curated writes require canonical identity "
            "(0002-C §4); re-extract from a real controlm_jobs projection"
        )
    return folder_id, job_id


def asset_urn(kind: str, location: str) -> str:
    """DataAsset proxy URN — ``urn:drydocs:dataasset:{platform}:{namespace}:{name}``
    (the D1 key shape, ``provisioning/02_proxy_constraints.cypher``). Namespace is
    the location's parent path (``-`` when flat); the mapping is deterministic and
    reviewed at the same HITL gate that opens the vocabulary."""
    loc = location.replace("\\", "/").rstrip("/")
    namespace, _, name = loc.rpartition("/")
    return f"urn:drydocs:dataasset:{kind}:{namespace or '-'}:{name or loc}"


# --- the plan --------------------------------------------------------------------

_SCRIPT_CONSTRAINT = (
    "CREATE CONSTRAINT script_path IF NOT EXISTS "
    "FOR (s:Script) REQUIRE s.path IS UNIQUE"
)
_ASSET_CONSTRAINT = (
    "CREATE CONSTRAINT dataasset_id IF NOT EXISTS "
    "FOR (a:DataAsset) REQUIRE a.assetId IS UNIQUE"
)
#: key = the stable token alone (not token+kind) — AMBIGUITY CALL (G12,
#: guardrail 5): the gate log is silent on whether the constraint composites
#: with `kind`; the stable token is already collision-safe per engine (DPL
#: GUIDs, Ab Initio basenames), and this mirrors how Script keys on `path`
#: alone despite serving several invocation kinds.
_ETL_PROCESS_CONSTRAINT = (
    "CREATE CONSTRAINT etlprocess_token IF NOT EXISTS "
    "FOR (e:ETLProcess) REQUIRE e.token IS UNIQUE"
)

_SCRIPT_MERGE = """\
UNWIND $rows AS row
MERGE (s:Script {path: row.path})
  ON CREATE SET s.created_at = datetime($written_at),
                s.source     = 'drydocs-lineage'
SET s.kind         = row.kind,
    s.name         = row.name,
    s.last_seen_at = datetime($written_at)"""

_ETL_PROCESS_MERGE = """\
UNWIND $rows AS row
MERGE (e:ETLProcess {token: row.token})
  ON CREATE SET e.created_at = datetime($written_at),
                e.source     = 'drydocs-lineage'
SET e.kind         = row.kind,
    e.engine       = row.engine,
    e.name         = row.name,
    e.path         = row.path,
    e.dataflow     = row.dataflow,
    e.config_path  = row.config_path,
    e.last_seen_at = datetime($written_at)"""

_ASSET_MERGE = """\
UNWIND $rows AS row
MERGE (a:DataAsset {assetId: row.asset_id})
  ON CREATE SET a.created_at = datetime($written_at),
                a.source     = 'drydocs-lineage'
SET a.kind         = row.kind,
    a.location     = row.location,
    a.fmt          = row.fmt,
    a.last_seen_at = datetime($written_at)"""

# endpoint class → (MATCH fragment template, row-key builder)
_MATCH_FRAGMENT = {
    "job": "MATCH ({var}:ControlMJob {{folder_id: row.{side}_folder_id, job_id: row.{side}_job_id}})",
    "script": "MATCH ({var}:Script {{path: row.{side}_key}})",
    "etl_process": "MATCH ({var}:ETLProcess {{token: row.{side}_key}})",
    "asset": "MATCH ({var}:DataAsset {{assetId: row.{side}_key}})",
}


@dataclass(frozen=True)
class WritePlan:
    """The exact statements a live load runs — gate/review material."""

    statements: tuple[tuple[str, dict[str, Any]], ...]
    rel_types: tuple[str, ...]   # rel labels actually planned for write, sorted
    rels: int                    # confirmed rels planned
    scripts: int                 # Script nodes MERGEd
    etl_processes: int           # ETLProcess nodes MERGEd (G12: abinitio/dpl kinds)
    assets: int                  # DataAsset nodes MERGEd
    unresolved_file_ops: int     # script-src READS_FROM/WRITES_TO dropped: no
                                 # owning job found via INVOKES (G13) — counted,
                                 # never silently swallowed; see plan_curated


def _endpoint_class(graph: LineageGraph, node_id: str) -> str:
    node = graph.processes.get(node_id)
    if node is not None:
        if node.kind == _JOB_KIND:
            return "job"
        if node.kind in _ETL_PROCESS_KINDS:
            return "etl_process"
        return "script"
    if node_id in graph.data_assets:
        return "asset"
    raise ValueError(f"confirmed rel endpoint {node_id!r} is not in the graph")


def _endpoint_params(graph: LineageGraph, node_id: str, side: str) -> dict[str, Any]:
    cls = _endpoint_class(graph, node_id)
    if cls == "job":
        folder_id, job_id = _job_composite(node_id)
        return {f"{side}_folder_id": folder_id, f"{side}_job_id": job_id}
    if cls in ("script", "etl_process"):
        return {f"{side}_key": _node_key(node_id)}
    return {f"{side}_key": asset_urn(
        graph.data_assets[node_id].kind, graph.data_assets[node_id].location
    )}


def _owning_jobs(graph: LineageGraph, script_id: str) -> list[str]:
    """ControlMJob ids that INVOKE ``script_id`` (sorted for determinism).

    Reads the graph's FULL rel set, not the confirmed subset being planned —
    which job invokes a script is structural topology, not a per-batch curation
    decision, so this does not require the caller to also confirm that INVOKES
    edge in the same write batch (G13).
    """
    owners = []
    for src, rel_type, dst in graph.rels:
        if rel_type != "INVOKES" or dst != script_id:
            continue
        node = graph.processes.get(src)
        if node is not None and node.kind == _JOB_KIND:
            owners.append(src)
    return sorted(owners)


def unresolved_file_op_candidates(
    graph: LineageGraph,
) -> list[tuple[str, str, str]]:
    """Script-src READS_FROM/WRITES_TO candidates with NO owning job (sorted).

    Exactly the rels :func:`_resolve_file_ops` would DROP (and count in
    ``WritePlan.unresolved_file_ops``) at plan time — exposed as a function so
    the lineage-review page can show the would-be loss to the SME *before* any
    plan is cut (G14: the drop count must not sit unread). Src endpoints that
    are already a job or an ETLProcess resolve trivially and are not listed;
    a data-asset src is a curation error :func:`plan_curated` flags, not this
    function's concern.
    """
    out: list[tuple[str, str, str]] = []
    for src, rel_type, dst in sorted(graph.rels):
        if rel_type not in _FILE_OPS_TYPES:
            continue
        node = graph.processes.get(src)
        if node is None or node.kind == _JOB_KIND or node.kind in _ETL_PROCESS_KINDS:
            continue
        if not _owning_jobs(graph, src):
            out.append((src, rel_type, dst))
    return out


def _resolve_file_ops(
    graph: LineageGraph, confirmed: set[tuple[str, str, str]]
) -> tuple[set[tuple[str, str, str]], int]:
    """Re-point script-src READS_FROM/WRITES_TO candidates to their OWNING
    ControlMJob (gate-log 2026-07-15 EDIT: from_node is "ETLProcess |
    ControlMJob" — :Script is prov:Entity and cannot carry prov:used/generated,
    so the type-correct Activity for pure file ops is the job that INVOKES the
    script). ETL-case srcs (an ``_ETL_PROCESS_KINDS`` process) and srcs that are
    already a ControlMJob pass through unchanged — only a "script" endpoint
    class is resolved.

    AMBIGUITY CALLS (G13, guardrail 5): a script INVOKEd by more than one job
    fans the candidate out to every owning job (each job-run performs the file
    op, so each is a distinct Activity); a script with NO owning job in the
    graph cannot be planned as a Script-sourced edge at all (the gate forbids
    it) — dropped, and counted in the second return value so the plan surfaces
    the loss rather than silently shrinking. Returns a ``set`` so fan-out
    duplicates (two candidates resolving to the same (job, rel, asset) row, or
    the same script owned by the same job twice) collapse for free.
    """
    resolved: set[tuple[str, str, str]] = set()
    unresolved = 0
    for src, rel_type, dst in confirmed:
        if rel_type not in _FILE_OPS_TYPES:
            resolved.add((src, rel_type, dst))
            continue
        # to_node is DataAsset for BOTH cases (gate-log EDIT) — a candidate
        # that disagrees is a curation error; flag it, don't force a shape.
        if _endpoint_class(graph, dst) != "asset":
            raise ValueError(
                f"{rel_type} dst {dst!r} is not a DataAsset — the gate-log "
                "2026-07-15 EDIT unifies m3_reads_from/m3_writes_to to_node "
                "on DataAsset for both the ETL and file-ops cases"
            )
        if _endpoint_class(graph, src) != "script":
            resolved.add((src, rel_type, dst))  # ETL case or already a job
            continue
        owners = _owning_jobs(graph, src)
        if not owners:
            unresolved += 1
            continue
        for job_id in owners:
            resolved.add((job_id, rel_type, dst))
    return resolved, unresolved


def plan_curated(
    graph: LineageGraph, confirmed: set[tuple[str, str, str]]
) -> WritePlan:
    """Validate the curated subset and return the exact write batches (PURE)."""
    unknown = confirmed - graph.rels
    if unknown:
        raise ValueError(
            f"confirmed rels not present in the graph (curation out of sync): "
            f"{sorted(unknown)[:5]}"
        )

    # file-ops (READS_FROM/WRITES_TO) candidates sourced from a Script resolve
    # to their owning ControlMJob before anything below sees them (G13) —
    # everything downstream (endpoint rows, MATCH shapes) runs on `resolved`,
    # never the raw `confirmed` set, so a resolved job endpoint gets the SAME
    # identity refusal / MATCH treatment as any other job endpoint for free.
    resolved, unresolved_file_ops = _resolve_file_ops(graph, confirmed)

    # endpoint nodes of the resolved subset only
    endpoint_ids = {n for rel in resolved for n in (rel[0], rel[2])}
    script_rows, etl_process_rows, asset_rows = [], [], []
    for nid in sorted(endpoint_ids):
        cls = _endpoint_class(graph, nid)
        if cls == "job":
            _job_composite(nid)  # identity refusal happens at plan time
        elif cls == "script":
            node = graph.processes[nid]
            script_rows.append({
                "path": _node_key(nid), "kind": node.kind, "name": node.name,
            })
        elif cls == "etl_process":
            node = graph.processes[nid]
            etl_process_rows.append({
                "token": _node_key(nid),
                # MAC-derived kind wins over the blind default (G17 acceptance c);
                # a rider-path node (mac_kind_rider set, no mac_kind) deliberately
                # keeps the default until the gate rules the enum question
                "kind": node.properties.get("mac_kind") or _DEFAULT_ETL_KIND,
                "engine": node.kind,
                "name": node.name,
                "path": node.path,
                "dataflow": node.dataflow,
                "config_path": node.config_path,
            })
        else:
            node = graph.data_assets[nid]
            asset_rows.append({
                "asset_id": asset_urn(node.kind, node.location),
                "kind": node.kind, "location": node.location, "fmt": node.fmt,
            })

    statements: list[tuple[str, dict[str, Any]]] = []
    if script_rows:
        statements.append((_SCRIPT_CONSTRAINT, {}))
        statements.append((_SCRIPT_MERGE, {"rows": script_rows}))
    if etl_process_rows:
        statements.append((_ETL_PROCESS_CONSTRAINT, {}))
        statements.append((_ETL_PROCESS_MERGE, {"rows": etl_process_rows}))
    if asset_rows:
        statements.append((_ASSET_CONSTRAINT, {}))
        statements.append((_ASSET_MERGE, {"rows": asset_rows}))

    # rel batches, one statement per (src class, label, dst class) shape
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for src, rel_type, dst in sorted(resolved):
        shape = (_endpoint_class(graph, src), rel_type, _endpoint_class(graph, dst))
        groups.setdefault(shape, []).append(
            {**_endpoint_params(graph, src, "src"), **_endpoint_params(graph, dst, "dst")}
        )
    for (src_cls, rel_type, dst_cls), rows in sorted(groups.items()):
        cypher = (
            "UNWIND $rows AS row\n"
            + _MATCH_FRAGMENT[src_cls].format(var="src", side="src") + "\n"
            + _MATCH_FRAGMENT[dst_cls].format(var="dst", side="dst") + "\n"
            + f"MERGE (src)-[r:{rel_type}]->(dst)\n"
            + "  ON CREATE SET r.first_seen_at = datetime($written_at),\n"
            + "                r.source        = 'drydocs-lineage',\n"
            + f"                r.vocab_id      = '{VOCAB_IDS[rel_type]}'\n"
            + "SET r.last_seen_at = datetime($written_at)\n"
            + "RETURN count(r) AS written"
        )
        statements.append((cypher, {"rows": rows}))

    return WritePlan(
        statements=tuple(statements),
        rel_types=tuple(sorted({r[1] for r in resolved})),
        rels=len(confirmed),
        scripts=len(script_rows),
        etl_processes=len(etl_process_rows),
        assets=len(asset_rows),
        unresolved_file_ops=unresolved_file_ops,
    )


# --- the live load ---------------------------------------------------------------

def write_curated(
    graph: LineageGraph,
    confirmed: set[tuple[str, str, str]],
    client: Any = None,
    *,
    registry: Path | None = None,
) -> int:
    """Write the CONFIRMED subset of ``graph``'s rels (+ their endpoint nodes) to
    ground truth; returns the count of rels written.

    ``client`` is a :class:`drydocs_core.neo4j_client.Neo4jClient` (entered)
    bound to the ``drydocs`` database. A written count below ``len(confirmed)``
    can mean either: some ControlMJob endpoints were absent from the graph DB
    (the M3 load owns them — rerun it, then this), or a script-src file-ops
    candidate had no owning job to resolve to (G13; see
    ``plan_curated(...).unresolved_file_ops`` for the count before writing).
    """
    if not confirmed:
        return 0
    plan = plan_curated(graph, confirmed)

    if client is None:
        raise ValueError(
            "a Neo4jClient bound to the 'drydocs' database is required for a "
            "live load; use plan_curated() for review/dry-run"
        )
    database = client.connection_info().get("database")
    if database != DATABASE:
        raise TrustBoundaryError(
            f"drydocs-lineage writes ground truth ONLY to {DATABASE!r} (ADR 0002 "
            f"D2); refusing client bound to {database!r}"
        )

    needed = {VOCAB_IDS[t] for t in plan.rel_types}
    statuses = vocabulary_status(needed, registry)
    blocked = sorted(
        f"{vid}={statuses.get(vid, 'UNREGISTERED')}"
        for vid in needed
        if statuses.get(vid) != "active"
    )
    if blocked:
        raise GateBoundVocabularyError(
            "rel vocabulary is gate-bound — no live load before the HITL gate "
            f"flips these active in relationship_vocabulary.yaml: {blocked}"
        )

    written_at = datetime.now(timezone.utc).isoformat()
    written = 0
    for cypher, params in plan.statements:
        rows = client.run(cypher, {**params, "written_at": written_at})
        if rows and "written" in rows[0]:
            written += rows[0]["written"]
    return written
