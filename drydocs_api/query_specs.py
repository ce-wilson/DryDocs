"""QuerySpec registry (O11 / site-plan §4) — the contract that makes export possible.

Every console data frame binds to a VERSIONED spec declared here: id, target
database, parameterized read-only Cypher, column definitions, and the
sensitivity classification that drives the export rules (banner + filename
prefix; PUBLISH-BOUNDARY.md). The UI never invents Cypher — a frame renders
whatever its spec returned, and export re-runs the SAME spec, so what you
export is provably what you saw.

Registry rules (asserted at import, so a bad spec can never ship):
- ids are versioned like loaders: ``<area>.<frame>.v<N>``
- cypher passes the read-only guard (defense in depth — these are ours)
- database comes from the reviewed set (the routing.py philosophy: a spec that
  reads uncertain ``ddcontext``/``ddall`` content is an explicit, reviewed row
  here — never a default; those results are watermarked SYNTHESIZED)
- classification comes from the config/classification.yaml vocabulary
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from drydocs_api.guard import ensure_read_only
from drydocs_api.queries import ParamSpec

SPEC_DATABASES: frozenset[str] = frozenset({"drydocs", "ddlineage", "ddcontext", "ddall"})
# Databases whose content is synthesized/uncertain — results carry the
# SYNTHESIZED watermark in the manifest AND as a grid-visible column.
WATERMARKED_DATABASES: frozenset[str] = frozenset({"ddcontext", "ddall"})
CLASSIFICATIONS: frozenset[str] = frozenset(
    {"external", "internal-public", "internal", "internal-confidential"}
)
_SPEC_ID_RE = re.compile(r"^[a-z0-9-]+(\.[a-z0-9-]+)+\.v\d+$")


@dataclass(frozen=True)
class ColumnDef:
    name: str
    type: str  # 'string' | 'int'
    label: str | None = None


@dataclass(frozen=True)
class QuerySpec:
    id: str
    database: str
    description: str
    cypher: str
    columns: tuple[ColumnDef, ...]
    classification: str
    params: tuple[ParamSpec, ...] = field(default=())


class UnknownSpecError(KeyError):
    """Raised for a spec id not in the registry."""


_LIMIT = (ParamSpec("limit", "int", required=False, default=500),)

QUERY_SPECS: dict[str, QuerySpec] = {
    s.id: s
    for s in (
        QuerySpec(
            id="explorer.applications.v1",
            database="drydocs",
            description="Business applications (SEAL-keyed) for the Explorer Applications frame.",
            cypher=(
                "MATCH (a:BusinessApplication) "
                "RETURN a.seal_id AS seal_id, a.name AS name, a.status AS status "
                "ORDER BY seal_id LIMIT $limit"
            ),
            columns=(
                ColumnDef("seal_id", "string", "SEAL id"),
                ColumnDef("name", "string", "Application"),
                ColumnDef("status", "string", "Status"),
            ),
            classification="internal",
            params=_LIMIT,
        ),
        QuerySpec(
            id="explorer.jobs.v2",
            database="drydocs",
            description=(
                "Control-M jobs joined through their :ControlMFolder (real folder name, "
                "not the raw join key) and the folder's :ControlMServer — the DATA_CENTER "
                "field the folders loader reifies as a server node (SCHEDULED_ON). "
                "v2 SME correction 2026-07-21: v1 read the job's denormalized folder_id "
                "and had no data_center."
            ),
            cypher=(
                "MATCH (f:ControlMFolder)-[:CONTAINS_JOB]->(j:ControlMJob) "
                "OPTIONAL MATCH (f)-[:SCHEDULED_ON]->(s:ControlMServer) "
                "RETURN j.job_name AS job_name, f.sched_table AS folder, "
                "s.name AS data_center, j.job_id AS job_id "
                "ORDER BY job_name LIMIT $limit"
            ),
            columns=(
                ColumnDef("job_name", "string", "Job"),
                ColumnDef("folder", "string", "Folder"),
                ColumnDef("data_center", "string", "Data center"),
                ColumnDef("job_id", "string", "Job id"),
            ),
            classification="internal",
            params=_LIMIT,
        ),
        QuerySpec(
            id="explorer.conditions.v2",
            database="drydocs",
            description=(
                "Control-M conditions with their folder resolved to the :ControlMFolder "
                "node's real name (v2 SME correction 2026-07-21 — v1 showed the raw "
                "folder_id join key)."
            ),
            cypher=(
                "MATCH (c:Condition) "
                "OPTIONAL MATCH (f:ControlMFolder {folder_id: c.folder_id}) "
                "RETURN c.name AS name, coalesce(f.sched_table, c.folder_id) AS folder "
                "ORDER BY name LIMIT $limit"
            ),
            columns=(
                ColumnDef("name", "string", "Condition"),
                ColumnDef("folder", "string", "Folder"),
            ),
            classification="internal",
            params=_LIMIT,
        ),
        QuerySpec(
            id="explorer.folder-applications.v1",
            database="drydocs",
            description=(
                "ControlMFolder -> BusinessApplication crosswalk: which SEAL application "
                "each folder's jobs are attributed to, via the gated edges "
                "CONTAINS_JOB + WAS_ASSOCIATED_WITH {role:'seal_app_ref'} (K1/K2), with "
                "the folder's data center (SCHEDULED_ON server) and job count."
            ),
            cypher=(
                "MATCH (f:ControlMFolder)-[:CONTAINS_JOB]->(j:ControlMJob)"
                "-[:WAS_ASSOCIATED_WITH {role: 'seal_app_ref'}]->(a:BusinessApplication) "
                "OPTIONAL MATCH (f)-[:SCHEDULED_ON]->(s:ControlMServer) "
                "RETURN f.sched_table AS folder, s.name AS data_center, "
                "a.seal_id AS seal_id, a.name AS application, count(DISTINCT j) AS jobs "
                "ORDER BY folder LIMIT $limit"
            ),
            columns=(
                ColumnDef("folder", "string", "Folder"),
                ColumnDef("data_center", "string", "Data center"),
                ColumnDef("seal_id", "string", "SEAL id"),
                ColumnDef("application", "string", "Application"),
                ColumnDef("jobs", "int", "Jobs"),
            ),
            classification="internal",
            params=_LIMIT,
        ),
        QuerySpec(
            id="explorer.servers.v1",
            database="drydocs",
            description="Control-M servers for the Explorer Servers frame.",
            cypher="MATCH (s:ControlMServer) RETURN s.name AS name ORDER BY name",
            columns=(ColumnDef("name", "string", "Server"),),
            classification="internal",
        ),
        QuerySpec(
            id="context.label-census.v1",
            database="ddcontext",
            description=(
                "Label census of the synthesized context database — the reviewed "
                "ddcontext example (results watermark SYNTHESIZED by rule)."
            ),
            cypher=(
                "MATCH (n) RETURN labels(n) AS labels, count(*) AS count ORDER BY count DESC"
            ),
            columns=(
                ColumnDef("labels", "string", "Labels"),
                ColumnDef("count", "int", "Nodes"),
            ),
            classification="internal-public",
        ),
    )
}


def _validate_registry() -> None:
    for spec in QUERY_SPECS.values():
        assert _SPEC_ID_RE.match(spec.id), f"spec id '{spec.id}' is not versioned (<area>.<frame>.vN)"
        assert spec.database in SPEC_DATABASES, f"spec '{spec.id}': database '{spec.database}' not in the reviewed set"
        assert spec.classification in CLASSIFICATIONS, f"spec '{spec.id}': classification '{spec.classification}' unknown"
        assert spec.columns, f"spec '{spec.id}' declares no columns"
        ensure_read_only(spec.cypher)  # raises WriteRejected on a write-shaped spec


_validate_registry()


def query_spec(spec_id: str) -> QuerySpec:
    try:
        return QUERY_SPECS[spec_id]
    except KeyError as exc:
        raise UnknownSpecError(spec_id) from exc


def is_watermarked(spec: QuerySpec) -> bool:
    return spec.database in WATERMARKED_DATABASES
