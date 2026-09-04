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
  :class:`TrustBoundaryError` otherwise. Curated results are ground truth:
  this writer never stamps :Uncertain, the label the G102 fold made the
  uncertain realm (it retired the old ``ddcontext`` residency this clause
  used to forbid).
- **Gate-bound vocabulary**: every rel label a load writes is checked against
  its registered status (``model.VOCAB_IDS`` / ``RUA_VOCAB_IDS``); a live
  load raises :class:`GateBoundVocabularyError` for any label not ``active``
  in ``relationship_vocabulary.yaml``. The gate cannot be reasoned around in
  code — it is a registry read, PER LABEL: gate rua-load-shapes (SIGNED OFF
  2026-08-07, applied at G55) activated scheduler_invokes / scheduler_uses_artifact /
  scheduler_reads_from / scheduler_writes_to, while scheduler_triggers stays planned and still
  refuses.

Node mechanics: ControlMJob endpoints are **MATCHed, never MERGEd** — the M3
load owns those nodes (a lineage-created job stub would violate the m3-verify
"every job has a folder" invariant). Scripts, ETLProcess, and DataAssets are
MERGEd on their business keys (``Script.path``; ``ETLProcess.token`` — the SAME
kind-scoped stable token ``controlm_inventory._stable_invocation_key`` already
computes for Ab Initio/DPL invocations (G12; gate-log 2026-07-16
"cmdline-lineage-review" §b) — full path / dataflow / config-JSON path ride as
properties, never identity; ``DataAsset.assetId`` — the D1 proxy URN,
``constraints.cypher (dataasset_id — the D1 key, re-homed at G31)``), with their constraints ensured
first (constraint-on-key rule).

File-ops endpoint resolution (G13; gate-log 2026-07-15 "reads/writes shapes
EDITED"): ``scheduler_reads_from`` / ``scheduler_writes_to`` from_node is ``ETLProcess |
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

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import drydocs_core.ontology as _core_ontology
from drydocs_core import yaml_fragments
from drydocs_core.ontology.swo_adapter import EXTENSION_LANGUAGE_IRI
from drydocs_core.run_log import batch_run_log

from .model import ETL_PROCESS_KINDS, VOCAB_IDS, LineageGraph

#: The write target — ground truth. The trust axis IS the DB boundary (ADR 0002 D1).
DATABASE = "drydocs"

#: the registered vocabulary (single source of truth for gate status)
_VOCAB_REGISTRY = Path(_core_ontology.__file__).resolve().parent / "relationship_vocabulary"

_JOB_KIND = "controlm_job"

#: invocation "engine" kinds that get their own :ETLProcess endpoint class
#: instead of :Script (G12; gate-log 2026-07-16 "cmdline-lineage-review" §b).
#: MOVED TO model.py at G97 — the artifact pass needs the same set to know what
#: it may not migrate onto USES_ARTIFACT, and two copies of a classification set
#: is how they drift. Re-exported under the old private name so nothing that
#: imported it here breaks.
_ETL_PROCESS_KINDS = ETL_PROCESS_KINDS

#: the ETLProcess ``kind`` property (etl | utility | notification — gate-log §a).
#: AMBIGUITY CALL (G12, guardrail 5): the invocation engine alone cannot
#: distinguish a real ETL pset/pipeline from a utility one (e.g. the
#: script-exec / send-email psets the gate log names) — a node with no better
#: signal stamps 'etl'. The discriminating signal now EXISTS where DPL MAC
#: metadata was ingested (G17): the dpl_mac extractor derives
#: ``properties["mac_kind"]`` from pipeline.json subType, and the row build
#: below consults it first — only non-MAC nodes still take the blind default.
_DEFAULT_ETL_KIND = "etl"

#: the :Script refinement properties (gate cmdline-nfr-vetting SME-3,
#: 2026-07-21, adopted with m7 — G97 builds them). Read off ProcessNode
#: .properties and passed through as NULL where a row does not carry one, which
#: is what makes the coalesce guard in _SCRIPT_MERGE do its job.
_SCRIPT_REFINEMENTS = (
    "script_role",
    "platform",
    "artifact_uri",
    "artifact_kind",
    "platform_flags",
    "script_path",
    "evidence",
)

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


def vocabulary_status(vocab_ids: Iterable[str], registry: Path | None = None) -> dict[str, str]:
    """``id → status`` for the requested entries, read from the registry.

    Deliberately a line scan (id, then the first status under it) rather than a
    YAML dependency — the registry format is stable and guarded by tests; the
    gate must be readable everywhere the component imports.
    """
    wanted = set(vocab_ids)
    statuses: dict[str, str] = {}
    current: str | None = None
    for line in yaml_fragments.merged_text(registry or _VOCAB_REGISTRY).splitlines():
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
    (the D1 key shape, ``constraints.cypher (dataasset_id — the D1 key, re-homed at G31)``). Namespace is
    the location's parent path (``-`` when flat); the mapping is deterministic and
    reviewed at the same HITL gate that opens the vocabulary."""
    loc = location.replace("\\", "/").rstrip("/")
    namespace, _, name = loc.rpartition("/")
    return f"urn:drydocs:dataasset:{kind}:{namespace or '-'}:{name or loc}"


# --- the plan --------------------------------------------------------------------

_SCRIPT_CONSTRAINT = (
    "CREATE CONSTRAINT script_path IF NOT EXISTS " "FOR (s:Script) REQUIRE s.path IS UNIQUE"
)
_ASSET_CONSTRAINT = (
    "CREATE CONSTRAINT dataasset_id IF NOT EXISTS " "FOR (a:DataAsset) REQUIRE a.assetId IS UNIQUE"
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

#: G97 — the :Script refinements gate cmdline-nfr-vetting SME-3 (2026-07-21)
#: adopted with m7. `script_role` uses the SAME coalesce guard _RUA_SCRIPT_MERGE
#: uses, and for the same reason: one path can be staged by two loaders (a rua
#: profile AND a cmdline script), so a blind SET would let whichever ran last
#: silently erase the other's stamp. The artifact properties coalesce too — a
#: CMD_LINE row carries none of them, and it must not blank out what the
#: variable feed already established about the same artifact.
_SCRIPT_MERGE = """\
UNWIND $rows AS row
MERGE (s:Script {path: row.path})
  ON CREATE SET s.created_at = datetime($written_at),
                s.source     = 'drydocs-lineage'
SET s.kind           = row.kind,
    s.name           = row.name,
    s.script_role    = coalesce(row.script_role, s.script_role),
    s.platform       = coalesce(row.platform, s.platform),
    s.artifact_uri   = coalesce(row.artifact_uri, s.artifact_uri),
    s.artifact_kind  = coalesce(row.artifact_kind, s.artifact_kind),
    s.platform_flags = coalesce(row.platform_flags, s.platform_flags),
    s.script_path    = coalesce(row.script_path, s.script_path),
    s.evidence       = coalesce(row.evidence, s.evidence),
    s.last_seen_at   = datetime($written_at)"""

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


#: LIN2 (c): the load names its extract. When a plan is cut from a STAGED artifact
#: (``lineage-load``), every node and rel it MERGEs carries the artifact's run id and
#: the code commit the extractor ran at, and the load opens a :JobRun that carries the
#: artifact's ``sources`` block verbatim - the file the extractor actually read,
#: discovered or given, present or absent (the LIN1 lane review's condition). Plain
#: PROPERTIES and the existing :JobRun label (O28's ruling, base.py: a relationship
#: type is an ontology decision; a run record carries none) - no new label, no new
#: edge. Without a provenance the statements are exactly what they were before LIN2.
_PROV_NODE_SET = (
    ",\n    {var}.extract_run_id      = $extract_run_id,\n"
    "    {var}.extract_code_commit = $extract_code_commit"
)

_JOB_RUN_OPEN = """\
MERGE (run:JobRun {run_id: $run_id})
  ON CREATE SET run.kind       = 'load',
                run.loader     = 'lineage-load',
                run.started_at = datetime($written_at)
SET run.source              = 'drydocs-lineage',
    run.target              = 'drydocs',
    run.extract_run_id      = $extract_run_id,
    run.extract_code_commit = $extract_code_commit,
    run.extract_captured_at = $extract_captured_at,
    run.extract_artifact    = $extract_artifact,
    run.sources             = $sources,
    run.confirmed_rels      = $confirmed_rels,
    run.status              = 'STARTED'"""

_JOB_RUN_CLOSE = """\
MATCH (run:JobRun {run_id: $run_id})
SET run.status       = 'COMPLETED',
    run.completed_at = datetime()"""


@dataclass(frozen=True)
class ExtractProvenance:
    """What a staged artifact says about itself, as the load stamps it (LIN2 c)."""

    run_id: str
    code_commit: str
    captured_at: str = ""
    artifact: str = ""
    #: the artifact's ``sources`` block, one JSON string per hop in hop order (Neo4j
    #: holds no list of maps; O28's list-of-JSON-strings shape, parsed back by any reader)
    sources: tuple[str, ...] = ()

    @classmethod
    def from_header(cls, header: dict[str, Any], *, artifact: str = "") -> ExtractProvenance:
        """From the header ``staging.read_artifact`` returns (everything but the graph)."""
        return cls(
            run_id=str(header.get("run_id") or ""),
            code_commit=str(header.get("code_commit") or "unknown"),
            captured_at=str(header.get("captured_at") or ""),
            artifact=artifact,
            sources=tuple(json.dumps(src, sort_keys=True) for src in (header.get("sources") or [])),
        )

    @property
    def dirty(self) -> bool:
        """The extractor ran on an uncommitted tree (``staging.code_commit``'s marker)."""
        return self.code_commit.endswith("-dirty")

    def params(self) -> dict[str, Any]:
        return {"extract_run_id": self.run_id, "extract_code_commit": self.code_commit}


def gate_bound_labels(
    rel_types: Iterable[str], registry: Path | None = None
) -> list[tuple[str, str, str]]:
    """``(label, vocab id, status)`` for every label whose vocabulary entry is not
    ``active`` - what a live load WOULD refuse, computed without a database so the plan
    print can say it (LIN2 a). PURE: the same registry read ``_write_curated`` makes."""
    wanted = {t: VOCAB_IDS[t] for t in rel_types if t in VOCAB_IDS}
    statuses = vocabulary_status(wanted.values(), registry)
    return sorted(
        (label, vid, statuses.get(vid, "UNREGISTERED"))
        for label, vid in wanted.items()
        if statuses.get(vid) != "active"
    )


@dataclass(frozen=True)
class WritePlan:
    """The exact statements a live load runs — gate/review material."""

    statements: tuple[tuple[str, dict[str, Any]], ...]
    rel_types: tuple[str, ...]  # rel labels actually planned for write, sorted
    rels: int  # confirmed rels planned
    scripts: int  # Script nodes MERGEd
    etl_processes: int  # ETLProcess nodes MERGEd (G12: abinitio/dpl kinds)
    assets: int  # DataAsset nodes MERGEd
    unresolved_file_ops: int  # script-src READS_FROM/WRITES_TO dropped: no
    # owning job found via INVOKES (G13) — counted,
    # never silently swallowed; see plan_curated
    # -- G97 clause (e): what the launcher/payload split actually did in THIS
    #    batch, read off the planned rows rather than recomputed
    launchers: int = 0  # :Script rows carrying script_role='launcher'
    payloads: int = 0  # :Script rows carrying script_role='payload'
    scripts_unroled: int = 0  # :Script rows with no role — unchanged, reported
    uses_artifact_rels: int = 0  # USES_ARTIFACT edges planned


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
    return {
        f"{side}_key": asset_urn(
            graph.data_assets[node_id].kind, graph.data_assets[node_id].location
        )
    }


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
                "2026-07-15 EDIT unifies scheduler_reads_from/scheduler_writes_to to_node "
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
    graph: LineageGraph,
    confirmed: set[tuple[str, str, str]],
    *,
    provenance: ExtractProvenance | None = None,
    load_run_id: str | None = None,
) -> WritePlan:
    """Validate the curated subset and return the exact write batches (PURE).

    With ``provenance`` (LIN2 c) every MERGEd node and rel also carries
    ``extract_run_id`` / ``extract_code_commit``, and the plan opens with a :JobRun
    keyed by ``load_run_id`` that carries the artifact's sources block, and closes it
    last. Without it the plan is byte-for-byte what it was before LIN2.
    """
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
            script_rows.append(
                {
                    "path": _node_key(nid),
                    "kind": node.kind,
                    "name": node.name,
                    # G97 / SME-3: script_role {launcher, payload} plus the
                    # adopted artifact properties. `evidence` is §B3's verbatim
                    # derivation string — under §B2's union endpoints it is the
                    # only way the endpoint-class choice stays re-checkable.
                    **{k: node.properties.get(k) for k in _SCRIPT_REFINEMENTS},
                }
            )
        elif cls == "etl_process":
            node = graph.processes[nid]
            etl_process_rows.append(
                {
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
                }
            )
        else:
            node = graph.data_assets[nid]
            asset_rows.append(
                {
                    "asset_id": asset_urn(node.kind, node.location),
                    "kind": node.kind,
                    "location": node.location,
                    "fmt": node.fmt,
                }
            )

    prov_params = provenance.params() if provenance is not None else {}

    def _stamped(merge: str, var: str) -> str:
        return merge + (_PROV_NODE_SET.format(var=var) if provenance is not None else "")

    statements: list[tuple[str, dict[str, Any]]] = []
    # The :JobRun brackets a write that happens: an empty confirmed set is a no-op the
    # live path returns from before it opens anything, and the plan says the same.
    stamp_run = provenance is not None and bool(confirmed)
    if stamp_run:
        if not load_run_id:
            raise ValueError("a provenance-stamped plan needs the load's own run id")
        statements.append(
            (
                _JOB_RUN_OPEN,
                {
                    "run_id": load_run_id,
                    **prov_params,
                    "extract_captured_at": provenance.captured_at,
                    "extract_artifact": provenance.artifact,
                    "sources": list(provenance.sources),
                    "confirmed_rels": len(confirmed),
                },
            )
        )
    if script_rows:
        statements.append((_SCRIPT_CONSTRAINT, {}))
        statements.append((_stamped(_SCRIPT_MERGE, "s"), {"rows": script_rows, **prov_params}))
    if etl_process_rows:
        statements.append((_ETL_PROCESS_CONSTRAINT, {}))
        statements.append(
            (_stamped(_ETL_PROCESS_MERGE, "e"), {"rows": etl_process_rows, **prov_params})
        )
    if asset_rows:
        statements.append((_ASSET_CONSTRAINT, {}))
        statements.append((_stamped(_ASSET_MERGE, "a"), {"rows": asset_rows, **prov_params}))

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
            + _MATCH_FRAGMENT[src_cls].format(var="src", side="src")
            + "\n"
            + _MATCH_FRAGMENT[dst_cls].format(var="dst", side="dst")
            + "\n"
            + f"MERGE (src)-[r:{rel_type}]->(dst)\n"
            + "  ON CREATE SET r.first_seen_at = datetime($written_at),\n"
            + "                r.source        = 'drydocs-lineage',\n"
            + f"                r.vocab_id      = '{VOCAB_IDS[rel_type]}'\n"
            + "SET r.last_seen_at = datetime($written_at)"
            + (_PROV_NODE_SET.format(var="r") if provenance is not None else "")
            + "\nRETURN count(r) AS written"
        )
        statements.append((cypher, {"rows": rows, **prov_params}))
    if stamp_run:
        statements.append((_JOB_RUN_CLOSE, {"run_id": load_run_id}))

    roles = [r.get("script_role") for r in script_rows]
    return WritePlan(
        statements=tuple(statements),
        rel_types=tuple(sorted({r[1] for r in resolved})),
        rels=len(confirmed),
        scripts=len(script_rows),
        etl_processes=len(etl_process_rows),
        assets=len(asset_rows),
        unresolved_file_ops=unresolved_file_ops,
        launchers=roles.count("launcher"),
        payloads=roles.count("payload"),
        scripts_unroled=sum(1 for r in roles if not r),
        uses_artifact_rels=sum(1 for r in resolved if r[1] == "USES_ARTIFACT"),
    )


# --- the live load ---------------------------------------------------------------


def _write_curated(
    graph: LineageGraph,
    confirmed: set[tuple[str, str, str]],
    client: Any = None,
    *,
    registry: Path | None = None,
    provenance: ExtractProvenance | None = None,
    load_run_id: str | None = None,
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
    plan = plan_curated(graph, confirmed, provenance=provenance, load_run_id=load_run_id)

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

    written_at = datetime.now(UTC).isoformat()
    written = 0
    for cypher, params in plan.statements:
        rows = client.run(cypher, {**params, "written_at": written_at})
        if rows and "written" in rows[0]:
            written += rows[0]["written"]
    return written


# --- the rua curated load (G23; gate rua-load-shapes, SIGNED OFF 2026-08-07) ------
#
# Loads what the rua chain staged (G20 inventory + G24 repo seam), EXACTLY per
# the signed rulings and nothing beyond them:
#
# - :Script MERGEd on the §D1 key — the NORMALIZED ABSOLUTE PATH (mechanical
#   only: duplicate slashes collapsed, trailing slash stripped, relative or
#   ..-bearing paths counted malformed and never loaded; NO symlink
#   resolution, NO case folding). The URN urn:drydocs:script:{path} is a
#   RENDER stamped as a property, never the key (§G1: identity is a business
#   key). A profile IS a :Script with script_role='profile' (§C2(i)).
# - :DataAsset for the directory records (rua_path), MERGEd on the D1 proxy
#   URN. Directory `owner` stays a PLAIN PROPERTY: §C1's attribution edge is
#   planned and BUILD-BLOCKED on K17 — no :AppUser is minted or matched here.
# - :SourceOccurrence per staged observation (§D2's reified grain), MERGEd on
#   a deterministic occurrenceId (urn + origin + locator), each anchored
#   (:SourceOccurrence)-[:OCCURRENCE_OF]->(:Script) — arch_occurrence_of, the
#   transcribed §D2 prov:specializationOf binding. Server locator = host+path
#   (host = the §D3-ruled rua_fqdn spelling, falling back to hostname/bundle
#   for the ID only — resolution never uses the fallback); repo locator =
#   repo+ref+commit+path, joined to the server side on CONTENT HASH (the G24
#   git blob sha1), never by path. sha256 absence is a real, counted state
#   (§G2). storage_scope AND mount_source arrive from the G56 mount table on
#   v3 bundles and fall back to 'unknown' (no mount_source at all) on v1/v2,
#   which carry no mount table. A script whose server occurrences span >1
#   host is flagged identity_unconfirmed_across_hosts UNLESS every host's
#   occurrence reads storage_scope 'shared' AND carries the SAME
#   mount_source (G113's three-way rule: one export mounted on N hosts is
#   one file, proven by mount_source equality — never inferred from scope
#   alone, since 'shared' by itself does not say two hosts see the same
#   file). Hosts that agree on 'shared' but disagree on mount_source stay
#   unconfirmed and are ALSO counted separately (multi_host_shared_diverged)
#   — that split is a real finding (two hosts mounting the same path from
#   different exports), never folded silently into the general count.
#   'local' or 'unknown' scope stays unconfirmed exactly as before G113.
# - (:Script)-[:IS_ENCODED_IN]->(SwoClass) derived from the path extension
#   (§C3 — the shared core adapter; the term is OPTIONAL-MATCHed, never
#   minted: a mapped term missing from the graph means bootstrap has not run).
#
# What does NOT load, because the gate held or declined it: NO :AppUser and no
# scheduler_delegates_to (§A1 HELD behind K17); no arch_owns_directory edges (§C1
# planned, K17-blocked); no SOURCES edges (§C2 planned); no ExecutionHost is
# minted (§D3 — rua mints no second host identity; the loader only RESOLVES
# rua_fqdn against the deployed executionhost_nodeid key and counts the
# misses). The meta.txt envelope lands as the plain rua_* capture properties
# (§D4: the source is a STUB — no audit-envelope fields are written).

_SERVER_ORIGIN = "server-extract"
_REPO_ORIGIN = "code-repo"

_DUP_SLASH_RE = re.compile(r"/{2,}")

_OCCURRENCE_CONSTRAINT = (
    "CREATE CONSTRAINT sourceoccurrence_id IF NOT EXISTS "
    "FOR (o:SourceOccurrence) REQUIRE o.occurrenceId IS UNIQUE"
)

_RUA_SCRIPT_MERGE = """\
UNWIND $rows AS row
MERGE (s:Script {path: row.path})
  ON CREATE SET s.created_at = datetime($written_at),
                s.source     = 'drydocs-lineage',
                s.kind       = row.kind
SET s.name         = row.name,
    s.urn          = row.urn,
    s.script_role  = coalesce(row.script_role, s.script_role),
    s.identity_unconfirmed_across_hosts = row.identity_unconfirmed,
    s.last_seen_at = datetime($written_at)"""

_RUA_ASSET_MERGE = """\
UNWIND $rows AS row
MERGE (a:DataAsset {assetId: row.asset_id})
  ON CREATE SET a.created_at = datetime($written_at),
                a.source     = 'drydocs-lineage'
SET a.kind         = row.kind,
    a.location     = row.location,
    a += row.props,
    a.last_seen_at = datetime($written_at)"""

_OCCURRENCE_MERGE = """\
UNWIND $rows AS row
MATCH (s:Script {path: row.script_path})
MERGE (o:SourceOccurrence {occurrenceId: row.occurrence_id})
  ON CREATE SET o.created_at = datetime($written_at),
                o.source     = 'drydocs-lineage'
SET o += row.props,
    o.last_seen_at = datetime($written_at)
MERGE (o)-[r:OCCURRENCE_OF]->(s)
  ON CREATE SET r.first_seen_at = datetime($written_at),
                r.source        = 'drydocs-lineage',
                r.vocab_id      = 'arch_occurrence_of'
SET r.last_seen_at = datetime($written_at)
RETURN count(r) AS written"""

_ENCODED_IN_MERGE = """\
UNWIND $rows AS row
MATCH (s:Script {path: row.script_path})
OPTIONAL MATCH (lang:OntologyTerm:SwoClass {iri: row.language_iri})
FOREACH (l IN CASE WHEN lang IS NULL THEN [] ELSE [lang] END |
  MERGE (s)-[enc:IS_ENCODED_IN]->(l)
    ON CREATE SET enc.first_seen_at = datetime($written_at),
                  enc.source        = 'drydocs-lineage',
                  enc.vocab_id      = 'arch_is_encoded_in'
  SET enc.last_seen_at = datetime($written_at)
)
RETURN sum(CASE WHEN lang IS NULL THEN 0 ELSE 1 END) AS written"""

#: §D3(i): the envelope's captured host meets :ExecutionHost on `nodeid`
#: DIRECTLY (the deployed P3 UNIQUE key holds FQDNs); a bare hostname is
#: NEVER matched — binding a script to the wrong server is worse than not
#: binding it. Read-only: rua mints no second host identity.
_HOST_RESOLVE = """\
UNWIND $fqdns AS fqdn
OPTIONAL MATCH (h:ExecutionHost {nodeid: fqdn})
RETURN fqdn, h IS NOT NULL AS resolved"""


def normalize_script_path(path: str) -> str | None:
    """§D1 normalization — MECHANICAL ONLY: collapse duplicate slashes, strip
    the trailing slash; a relative or ``..``-bearing path is malformed
    (``None`` — the caller counts it). NO symlink resolution and NO case
    folding: POSIX paths are case-sensitive and nothing on the capture side
    ever resolved a link, so both would be guesses dressed up as
    normalization."""
    p = _DUP_SLASH_RE.sub("/", (path or "").strip())
    if len(p) > 1:
        p = p.rstrip("/")
    if not p.startswith("/") or any(seg == ".." for seg in p.split("/")):
        return None
    return p


def script_urn(normalized_path: str) -> str:
    """§D1/§G1: ``urn:drydocs:script:{normalized-abs-path}`` — a deterministic
    RENDER of the path key, one grammar with the unmanaged-asset URN."""
    return f"urn:drydocs:script:{normalized_path}"


def _occurrence_host(occ: dict) -> tuple[str, str]:
    """(id_host, resolvable_fqdn) for a server occurrence record.

    ``id_host`` (fqdn → hostname → bundle) only disambiguates the
    occurrenceId; ``resolvable_fqdn`` is non-empty ONLY for a qualified
    rua_fqdn — the §D3 rule that a bare hostname is never matched."""
    fqdn = occ.get("rua_fqdn", "")
    id_host = fqdn or occ.get("rua_host") or occ.get("rua_bundle", "")
    return id_host, (fqdn if "." in fqdn else "")


@dataclass(frozen=True)
class RuaWritePlan:
    """The exact statements the rua load runs — gate/review material (PURE)."""

    statements: tuple[tuple[str, dict[str, Any]], ...]
    rel_types: tuple[str, ...]  # edge labels planned (subset of OCCURRENCE_OF, IS_ENCODED_IN)
    scripts: int  # :Script nodes MERGEd (profiles included)
    profiles: int  # ...of which carry script_role='profile' (§C2)
    assets: int  # directory :DataAsset nodes MERGEd
    server_occurrences: int  # §D2 records from the server extract
    repo_occurrences: int  # §D2 records joined from the repo manifest (hash join)
    encoded_in: int  # scripts with a seeded language term (§C3)
    unbound_extensions: int  # scripts with no seeded term — reported, never guessed
    malformed_paths: int  # §D1 rejections — counted, never loaded
    hash_missing: int  # server occurrences staged hash-absent (§G2 — a real state)
    repo_join_uncomputable: int  # repo rows staged but no server copy to hash (G24)
    multi_host_unconfirmed: int  # scripts flagged identity_unconfirmed_across_hosts
    multi_host_shared_diverged: int  # of which: every host reads storage_scope
    # 'shared' but the hosts DISAGREE on mount_source (G113) — a real finding
    # (two hosts mounting the same path from different exports), broken out
    # so it stays visible on its own instead of vanishing into the total
    hosts: tuple[str, ...]  # distinct qualified fqdns for §D3 write-time resolution
    hosts_unqualified: int  # server occurrences with no qualified fqdn — unresolvable by rule


@dataclass(frozen=True)
class RuaLoadReport:
    """What a live rua load did — the counters the acceptance requires read
    together: the plan's coverage of the staging, the write results, the §D3
    host resolution, and the G20/G21/G24 extractor counters passed through."""

    plan: RuaWritePlan
    occurrence_edges_written: int
    encoded_in_written: int
    hosts_resolved: int
    hosts_unresolved: tuple[str, ...]
    coverage: dict[str, Any]  # G20/G21/G24 counters, passed through verbatim

    def summary(self) -> str:
        p = self.plan
        return (
            f"scripts={p.scripts} (profiles={p.profiles}) assets={p.assets} "
            f"occurrences={p.server_occurrences}+{p.repo_occurrences} "
            f"edges={self.occurrence_edges_written} "
            f"encoded_in={self.encoded_in_written} | "
            f"hosts: resolved={self.hosts_resolved} "
            f"unresolved={len(self.hosts_unresolved)} "
            f"unqualified={p.hosts_unqualified} | "
            f"counted: malformed_paths={p.malformed_paths} "
            f"hash_missing={p.hash_missing} "
            f"unbound_ext={p.unbound_extensions} "
            f"multi_host_unconfirmed={p.multi_host_unconfirmed} "
            f"(shared_diverged={p.multi_host_shared_diverged}) "
            f"repo_unjoinable={p.repo_join_uncomputable}"
        )


def _repo_occurrence_index(graph: LineageGraph) -> dict[str, list[tuple[Any, tuple]]]:
    """blob_sha → [(repo node, parsed occurrence)] — the load reads the PARSED
    records, never the packed staging string (§D2 / ADR 0001)."""
    from .extractors.code_repo import REPO_SCRIPT_KIND, _occurrences

    index: dict[str, list[tuple[Any, tuple]]] = {}
    for node in graph.processes.values():
        if node.kind != REPO_SCRIPT_KIND:
            continue
        for occ in _occurrences(node):
            index.setdefault(occ[3], []).append((node, occ))
    return index


def plan_rua(
    graph: LineageGraph,
    *,
    bundle_dir: str | Path | None = None,
) -> RuaWritePlan:
    """Validate the staged rua candidates and return the exact write batches
    (PURE — the review surface; :func:`write_rua` is the live load).

    ``bundle_dir`` locates the carried-back server copies for the G24 content-
    hash join of repo occurrences; without it (or without copies) repo rows
    stay unjoined and are COUNTED, never guessed onto a path."""
    from .extractors.code_repo import git_blob_sha1
    from .extractors.rua_inventory import RUA_PATH_KIND, RUA_PROFILE_KIND, RUA_SCRIPT_KIND

    repo_index = _repo_occurrence_index(graph)
    bundle = Path(bundle_dir) if bundle_dir is not None else None

    script_rows: list[dict[str, Any]] = []
    occurrence_rows: list[dict[str, Any]] = []
    encoded_rows: list[dict[str, Any]] = []
    profiles = 0
    server_occurrences = 0
    repo_occurrences = 0
    unbound_extensions = 0
    malformed_paths = 0
    hash_missing = 0
    repo_join_uncomputable = 0
    multi_host_unconfirmed = 0
    multi_host_shared_diverged = 0
    hosts: set[str] = set()
    hosts_unqualified = 0

    for nid in sorted(graph.processes):
        node = graph.processes[nid]
        if node.kind not in (RUA_SCRIPT_KIND, RUA_PROFILE_KIND):
            continue
        norm = normalize_script_path(node.path)
        if norm is None:
            malformed_paths += 1
            continue
        urn = script_urn(norm)
        is_profile = node.kind == RUA_PROFILE_KIND

        node_hosts: set[str] = set()
        host_scopes: dict[str, str] = {}  # id_host -> storage_scope, for the
        # G113 three-way rule below (per-host, since occurrences are per-host)
        host_mount_sources: dict[str, str] = {}  # id_host -> mount_source,
        # present only where G56's mount table stamped one
        records = node.occurrences or [dict(node.properties, path=node.path)]
        for occ in records:
            id_host, fqdn = _occurrence_host(occ)
            node_hosts.add(id_host)
            if fqdn:
                hosts.add(fqdn)
            else:
                hosts_unqualified += 1
            if not occ.get("sha256"):
                hash_missing += 1
            props = {k: v for k, v in occ.items() if isinstance(v, str) and v}
            props["origin"] = _SERVER_ORIGIN
            props["host"] = id_host
            # G56 landed: v3 bundles arrive already stamped by the extractor and
            # this setdefault only covers v1/v2 bundles, which carry no mount
            # table (and so no mount_source either — those hosts can never
            # qualify for the 'shared, same source' CONFIRMED leg below).
            props.setdefault("storage_scope", "unknown")
            host_scopes[id_host] = props["storage_scope"]
            if "mount_source" in props:
                host_mount_sources[id_host] = props["mount_source"]
            occurrence_rows.append(
                {
                    "script_path": norm,
                    "occurrence_id": f"{urn}#{_SERVER_ORIGIN}#{id_host}#{norm}",
                    "props": props,
                }
            )
            server_occurrences += 1

        # G24 hash join: repo occurrences attach on CONTENT HASH, never path
        if repo_index:
            copy_rel = node.properties.get("rua_copy", "")
            content: bytes | None = None
            if bundle is not None and copy_rel:
                try:
                    content = (bundle / copy_rel.lstrip("/")).read_bytes()
                except OSError:
                    content = None
            if content is None:
                repo_join_uncomputable += 1
            else:
                for repo_node, occ in repo_index.get(git_blob_sha1(content), []):
                    ref, commit, commit_date, blob_sha = occ
                    occurrence_rows.append(
                        {
                            "script_path": norm,
                            "occurrence_id": (
                                f"{urn}#{_REPO_ORIGIN}#"
                                f"{repo_node.properties.get('repo', '')}#"
                                f"{ref}@{commit}#{repo_node.path}"
                            ),
                            "props": {
                                "origin": _REPO_ORIGIN,
                                "repo": repo_node.properties.get("repo", ""),
                                "ref": ref,
                                "commit": commit,
                                "commit_date": commit_date,
                                "path": repo_node.path,
                                "blob_sha": blob_sha,
                            },
                        }
                    )
                    repo_occurrences += 1

        # G113 — the three-way rule. Multi-host is the precondition for all
        # three legs; a single-host script is never unconfirmed.
        #   1. every host reads storage_scope 'shared' AND all hosts agree on
        #      mount_source -> CONFIRMED (one export seen on N hosts is one
        #      file). mount_source equality is the identity test — scope
        #      alone never proves it, per the item's ruling.
        #   2. every host reads 'shared' but the hosts DISAGREE on
        #      mount_source -> stays unconfirmed AND is counted on its own
        #      (multi_host_shared_diverged) — two hosts mounting the same
        #      path from different exports is a real finding, not a
        #      non-finding folded silently into the general count.
        #   3. anything else ('local', 'unknown', or a mixed scope set) ->
        #      stays unconfirmed exactly as before G113.
        shared_diverged = False
        if len(node_hosts) <= 1:
            unconfirmed = False
        elif set(host_scopes.values()) == {"shared"}:
            same_source_everywhere = (
                len(host_mount_sources) == len(node_hosts)
                and len(set(host_mount_sources.values())) == 1
            )
            unconfirmed = not same_source_everywhere
            shared_diverged = unconfirmed
        else:
            unconfirmed = True
        if unconfirmed:
            multi_host_unconfirmed += 1
        if shared_diverged:
            multi_host_shared_diverged += 1
        if is_profile:
            profiles += 1
        script_rows.append(
            {
                "path": norm,
                "urn": urn,
                "name": node.name,
                "kind": node.kind,
                "script_role": "profile" if is_profile else None,
                "identity_unconfirmed": unconfirmed,
            }
        )

        extension = norm[norm.rfind(".") :] if "." in norm.rsplit("/", 1)[-1] else ""
        iri = EXTENSION_LANGUAGE_IRI.get(extension)
        if iri:
            encoded_rows.append({"script_path": norm, "language_iri": iri})
        else:
            unbound_extensions += 1

    asset_rows: list[dict[str, Any]] = []
    for aid in sorted(graph.data_assets):
        asset = graph.data_assets[aid]
        if asset.kind != RUA_PATH_KIND:
            continue
        asset_rows.append(
            {
                "asset_id": asset_urn(asset.kind, asset.location),
                "kind": asset.kind,
                "location": asset.location,
                "props": {k: v for k, v in asset.properties.items() if isinstance(v, str) and v},
            }
        )

    statements: list[tuple[str, dict[str, Any]]] = []
    rel_types: list[str] = []
    if script_rows:
        statements.append((_SCRIPT_CONSTRAINT, {}))
        statements.append((_RUA_SCRIPT_MERGE, {"rows": script_rows}))
    if asset_rows:
        statements.append((_ASSET_CONSTRAINT, {}))
        statements.append((_RUA_ASSET_MERGE, {"rows": asset_rows}))
    if occurrence_rows:
        statements.append((_OCCURRENCE_CONSTRAINT, {}))
        statements.append((_OCCURRENCE_MERGE, {"rows": occurrence_rows}))
        rel_types.append("OCCURRENCE_OF")
    if encoded_rows:
        statements.append((_ENCODED_IN_MERGE, {"rows": encoded_rows}))
        rel_types.append("IS_ENCODED_IN")

    return RuaWritePlan(
        statements=tuple(statements),
        rel_types=tuple(sorted(rel_types)),
        scripts=len(script_rows),
        profiles=profiles,
        assets=len(asset_rows),
        server_occurrences=server_occurrences,
        repo_occurrences=repo_occurrences,
        encoded_in=len(encoded_rows),
        unbound_extensions=unbound_extensions,
        malformed_paths=malformed_paths,
        hash_missing=hash_missing,
        repo_join_uncomputable=repo_join_uncomputable,
        multi_host_unconfirmed=multi_host_unconfirmed,
        multi_host_shared_diverged=multi_host_shared_diverged,
        hosts=tuple(sorted(hosts)),
        hosts_unqualified=hosts_unqualified,
    )


#: rel label → vocabulary id for the rua load's own gate check (the curated
#: CMD_LINE labels have theirs in model.VOCAB_IDS)
#: G87 (2026-08-21): g22_/u1_ -> arch_ under the domain-derived id scheme.
RUA_VOCAB_IDS = {"OCCURRENCE_OF": "arch_occurrence_of", "IS_ENCODED_IN": "arch_is_encoded_in"}


def _write_rua(
    graph: LineageGraph,
    client: Any = None,
    *,
    bundle_dir: str | Path | None = None,
    registry: Path | None = None,
    coverage: dict[str, Any] | None = None,
) -> RuaLoadReport:
    """The live rua load — same refusals as :func:`write_curated` (trust
    boundary, gate-bound vocabulary), then the §D3 host-resolution read.

    ``coverage`` is passed through verbatim onto the report (the G20/G21/G24
    extractor counters the acceptance requires beside the load numbers)."""
    plan = plan_rua(graph, bundle_dir=bundle_dir)

    if client is None:
        raise ValueError(
            "a Neo4jClient bound to the 'drydocs' database is required for a "
            "live load; use plan_rua() for review/dry-run"
        )
    database = client.connection_info().get("database")
    if database != DATABASE:
        raise TrustBoundaryError(
            f"drydocs-lineage writes ground truth ONLY to {DATABASE!r} (ADR 0002 "
            f"D2); refusing client bound to {database!r}"
        )

    needed = {RUA_VOCAB_IDS[t] for t in plan.rel_types}
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

    written_at = datetime.now(UTC).isoformat()
    occurrence_edges = 0
    encoded_in = 0
    for cypher, params in plan.statements:
        rows = client.run(cypher, {**params, "written_at": written_at})
        if rows and "written" in rows[0]:
            if cypher is _OCCURRENCE_MERGE:
                occurrence_edges += rows[0]["written"]
            elif cypher is _ENCODED_IN_MERGE:
                encoded_in += rows[0]["written"] or 0

    hosts_resolved = 0
    hosts_unresolved: list[str] = []
    if plan.hosts:
        for row in client.run(_HOST_RESOLVE, {"fqdns": list(plan.hosts)}):
            if row.get("resolved"):
                hosts_resolved += 1
            else:
                hosts_unresolved.append(row.get("fqdn", ""))

    return RuaLoadReport(
        plan=plan,
        occurrence_edges_written=occurrence_edges,
        encoded_in_written=encoded_in,
        hosts_resolved=hosts_resolved,
        hosts_unresolved=tuple(sorted(hosts_unresolved)),
        coverage=dict(coverage or {}),
    )


def write_curated(
    graph: LineageGraph,
    confirmed: set[tuple[str, str, str]],
    client: Any = None,
    *,
    registry: Path | None = None,
    provenance: ExtractProvenance | None = None,
    run_id: str | None = None,
) -> int:
    """Curated ground-truth write, wrapped in a run log (G107).

    Delegates to :func:`_write_curated` unchanged — this adds a record of the
    run, not behaviour. The empty-``confirmed`` guard runs BEFORE the log opens
    deliberately: nothing was asked for, so there is no batch to record, and a
    log per no-op call would bury the real runs.

    With ``provenance`` (LIN2 c) the run log's meta names the extract - its run id,
    code commit and the artifact path - and the same ``run_id`` keys the file log AND
    the :JobRun the plan opens, so the two records of one load share one id.
    """
    if not confirmed:
        return 0
    meta: dict[str, Any] = {"confirmed rels": len(confirmed)}
    if provenance is not None:
        meta["extract run_id"] = provenance.run_id
        meta["extract code_commit"] = provenance.code_commit
        meta["extract artifact"] = provenance.artifact
    with batch_run_log(
        "lineage.curated",
        run_id=run_id,
        source=provenance.artifact if provenance is not None else "",
        target=DATABASE,
        meta=meta,
    ) as summary:
        written = _write_curated(
            graph,
            confirmed,
            client,
            registry=registry,
            provenance=provenance,
            load_run_id=run_id,
        )
        summary["rels written"] = written
        summary["confirmed rels"] = len(confirmed)
        if provenance is not None:
            summary["extract sources"] = [json.loads(src) for src in provenance.sources]
        return written


def write_rua(
    graph: LineageGraph,
    client: Any = None,
    *,
    bundle_dir: str | Path | None = None,
    registry: Path | None = None,
    coverage: dict[str, Any] | None = None,
) -> RuaLoadReport:
    """The live rua load, wrapped in a run log (G107).

    Delegates to :func:`_write_rua` unchanged.
    """
    with batch_run_log(
        "lineage.rua",
        target=DATABASE,
        source=str(bundle_dir or ""),
    ) as summary:
        report = _write_rua(
            graph, client, bundle_dir=bundle_dir, registry=registry, coverage=coverage
        )
        summary["report"] = report
        return report
