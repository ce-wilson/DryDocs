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
  :class:`TrustBoundaryError` otherwise. Never ``drydocs_context``.
- **Gate-bound vocabulary**: the four rel labels are registered ``status:
  planned`` (``model.VOCAB_IDS``); a live load raises
  :class:`GateBoundVocabularyError` until the HITL gate flips them ``active``
  in ``relationship_vocabulary.yaml``. The gate cannot be reasoned around in
  code — it is a registry read.

Node mechanics: ControlMJob endpoints are **MATCHed, never MERGEd** — the M3
load owns those nodes (a lineage-created job stub would violate the m3-verify
"every job has a folder" invariant). Scripts and DataAssets are MERGEd on their
business keys (``Script.path``; ``DataAsset.assetId`` — the D1 proxy URN,
``provisioning/02_proxy_constraints.cypher``), with their constraints ensured
first (constraint-on-key rule).
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

_SCRIPT_MERGE = """\
UNWIND $rows AS row
MERGE (s:Script {path: row.path})
  ON CREATE SET s.created_at = datetime($written_at),
                s.source     = 'drydocs-lineage'
SET s.kind         = row.kind,
    s.name         = row.name,
    s.last_seen_at = datetime($written_at)"""

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
    "asset": "MATCH ({var}:DataAsset {{assetId: row.{side}_key}})",
}


@dataclass(frozen=True)
class WritePlan:
    """The exact statements a live load runs — gate/review material."""

    statements: tuple[tuple[str, dict[str, Any]], ...]
    rel_types: tuple[str, ...]   # rel labels present, sorted
    rels: int                    # confirmed rels planned
    scripts: int                 # Script nodes MERGEd
    assets: int                  # DataAsset nodes MERGEd


def _endpoint_class(graph: LineageGraph, node_id: str) -> str:
    node = graph.processes.get(node_id)
    if node is not None:
        return "job" if node.kind == _JOB_KIND else "script"
    if node_id in graph.data_assets:
        return "asset"
    raise ValueError(f"confirmed rel endpoint {node_id!r} is not in the graph")


def _endpoint_params(graph: LineageGraph, node_id: str, side: str) -> dict[str, Any]:
    cls = _endpoint_class(graph, node_id)
    if cls == "job":
        folder_id, job_id = _job_composite(node_id)
        return {f"{side}_folder_id": folder_id, f"{side}_job_id": job_id}
    if cls == "script":
        return {f"{side}_key": _node_key(node_id)}
    return {f"{side}_key": asset_urn(
        graph.data_assets[node_id].kind, graph.data_assets[node_id].location
    )}


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

    # endpoint nodes of the confirmed subset only
    endpoint_ids = {n for rel in confirmed for n in (rel[0], rel[2])}
    script_rows, asset_rows = [], []
    for nid in sorted(endpoint_ids):
        cls = _endpoint_class(graph, nid)
        if cls == "job":
            _job_composite(nid)  # identity refusal happens at plan time
        elif cls == "script":
            node = graph.processes[nid]
            script_rows.append({
                "path": _node_key(nid), "kind": node.kind, "name": node.name,
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
    if asset_rows:
        statements.append((_ASSET_CONSTRAINT, {}))
        statements.append((_ASSET_MERGE, {"rows": asset_rows}))

    # rel batches, one statement per (src class, label, dst class) shape
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for src, rel_type, dst in sorted(confirmed):
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
        rel_types=tuple(sorted({r[1] for r in confirmed})),
        rels=len(confirmed),
        scripts=len(script_rows),
        assets=len(asset_rows),
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
    means some ControlMJob endpoints were absent from the graph DB (the M3 load
    owns them — rerun it, then this).
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
