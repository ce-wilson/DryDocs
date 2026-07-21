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
            id="explorer.controlm-app-codes.v1",
            database="drydocs",
            description=(
                "Control-M APPLICATION codes classified by their OBSERVED mapping "
                "pattern to :BusinessApplication (SME review 2026-07-21): a code whose "
                "folders' jobs all attribute to ONE application is a 'direct "
                "(dedicated code)' candidate; a code spanning several applications is "
                "a 'shared platform code' (e.g. a cloud-ETL platform code carrying "
                "many apps); no attribution = the SME work queue. DERIVED from the "
                "gated job-level edges only — the authoritative code->application "
                "mapping table is a gate-bound O13 mapping domain, not this view."
            ),
            cypher=(
                "MATCH (ca:ControlMApplication) "
                "OPTIONAL MATCH (ca)-[:CONTAINS_FOLDER]->(f:ControlMFolder) "
                "OPTIONAL MATCH (f)-[:CONTAINS_JOB]->(j:ControlMJob) "
                "OPTIONAL MATCH (j)-[:WAS_ASSOCIATED_WITH {role: 'seal_app_ref'}]"
                "->(a:BusinessApplication) "
                "WITH ca, count(DISTINCT f) AS folders, count(DISTINCT j) AS jobs, "
                "collect(DISTINCT a.seal_id) AS seal_ids "
                "RETURN ca.name AS app_code, "
                "CASE WHEN size(seal_ids) = 0 THEN 'unmapped — SME queue' "
                "WHEN size(seal_ids) = 1 THEN 'direct (dedicated code)' "
                "ELSE 'shared platform code' END AS mapping_pattern, "
                "size(seal_ids) AS applications, folders, jobs, "
                "CASE WHEN size(seal_ids) = 1 THEN seal_ids[0] "
                "WHEN size(seal_ids) = 0 THEN null "
                "ELSE toString(size(seal_ids)) + ' applications' END AS mapped_to "
                "ORDER BY app_code LIMIT $limit"
            ),
            columns=(
                ColumnDef("app_code", "string", "App code"),
                ColumnDef("mapping_pattern", "string", "Mapping pattern"),
                ColumnDef("applications", "int", "Apps"),
                ColumnDef("folders", "int", "Folders"),
                ColumnDef("jobs", "int", "Jobs"),
                ColumnDef("mapped_to", "string", "Mapped to"),
            ),
            classification="internal",
            params=_LIMIT,
        ),
        QuerySpec(
            id="mappings.attribution-coverage.v1",
            database="drydocs",
            description=(
                "O13 stewardship coverage grid: every Control-M job with its CURRENT "
                "application resolution over the gated WAS_ASSOCIATED_WITH "
                "{role:'seal_app_ref'} edge (K2) — match_method is the tier evidence. "
                "No edge = 'unresolved' (the steward's first work queue); more than "
                "one attributed application = 'conflict' (second queue). Keyed by "
                "folder_id/job_id so the assign dialog drafts against the exact "
                "manual-loads composite key."
            ),
            cypher=(
                "MATCH (f:ControlMFolder)-[:CONTAINS_JOB]->(j:ControlMJob) "
                "OPTIONAL MATCH (j)-[r:WAS_ASSOCIATED_WITH {role: 'seal_app_ref'}]"
                "->(a:BusinessApplication) "
                "WITH f, j, [h IN collect({seal_id: a.seal_id, name: a.name, "
                "method: r.match_method}) WHERE h.seal_id IS NOT NULL] AS res "
                "RETURN f.sched_table AS folder, j.job_name AS job, "
                "f.folder_id AS folder_id, j.job_id AS job_id, "
                "CASE WHEN size(res) = 0 THEN null ELSE res[0].seal_id END AS seal_id, "
                "CASE WHEN size(res) = 0 THEN null ELSE res[0].name END AS application, "
                "CASE WHEN size(res) = 0 THEN null ELSE res[0].method END AS match_method, "
                "CASE WHEN size(res) = 0 THEN 'unresolved' "
                "WHEN size(res) > 1 THEN 'conflict' ELSE 'resolved' END AS status "
                "ORDER BY CASE WHEN size(res) = 0 THEN 0 WHEN size(res) > 1 THEN 1 "
                "ELSE 2 END, folder, job LIMIT $limit"
            ),
            columns=(
                ColumnDef("folder", "string", "Folder"),
                ColumnDef("job", "string", "Job"),
                ColumnDef("folder_id", "string", "Folder id"),
                ColumnDef("job_id", "string", "Job id"),
                ColumnDef("seal_id", "string", "SEAL id"),
                ColumnDef("application", "string", "Application"),
                ColumnDef("match_method", "string", "Tier/evidence"),
                ColumnDef("status", "string", "Status"),
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
        # O15 ownership frames — the K4 qualified-attribution shape.
        QuerySpec(
            id="ownership.teams.v1",
            database="drydocs",
            description="Dev teams with their DEVELOPS application count (arch_develops, C3 gate).",
            cypher=(
                "MATCH (dt:DevTeam) "
                "OPTIONAL MATCH (dt)-[:DEVELOPS]->(a:BusinessApplication) "
                "RETURN dt.team_id AS team_id, dt.name AS team, "
                "count(DISTINCT a) AS applications "
                "ORDER BY team LIMIT $limit"
            ),
            columns=(
                ColumnDef("team_id", "string", "Team id"),
                ColumnDef("team", "string", "Team"),
                ColumnDef("applications", "int", "Applications"),
            ),
            classification="internal-confidential",
            params=_LIMIT,
        ),
        QuerySpec(
            id="ownership.attributions.v1",
            database="drydocs",
            description=(
                "K4 qualified attributions: Attribution nodes keyed attribution_id with "
                "their TOMRole crosswalk — unmapped_role=true rows float to the top, "
                "visibly flagged, never hidden (the K4 rule). Holder by SID only "
                "(names are confidential)."
            ),
            cypher=(
                "MATCH (a:BusinessApplication)-[:QUALIFIED_ATTRIBUTION]->(m:Attribution) "
                "OPTIONAL MATCH (m)-[:HAD_ROLE]->(tr:TOMRole) "
                "OPTIONAL MATCH (m)-[:HAS_AGENT]->(e) "
                "RETURN a.seal_id AS seal_id, m.attribution_id AS attribution_id, "
                "m.role_source_name AS source_role, tr.id AS tom_role, m.level AS level, "
                "m.unmapped_role AS unmapped_role, e.sid AS holder_sid "
                "ORDER BY m.unmapped_role DESC, seal_id LIMIT $limit"
            ),
            columns=(
                ColumnDef("seal_id", "string", "SEAL id"),
                ColumnDef("attribution_id", "string", "Attribution id"),
                ColumnDef("source_role", "string", "Source role"),
                ColumnDef("tom_role", "string", "TOM role"),
                ColumnDef("level", "string", "Level"),
                ColumnDef("unmapped_role", "string", "Unmapped?"),
                ColumnDef("holder_sid", "string", "Holder SID"),
            ),
            classification="internal-confidential",
            params=_LIMIT,
        ),
        QuerySpec(
            id="ownership.escalation-routing.v1",
            database="drydocs",
            description=(
                "Escalation routing groups (ServiceNowGroup). The escalation source "
                "(CM_ESCALATION_DB / SCIM) is company-side — zero rows here is the "
                "honest producer state until that source loads."
            ),
            cypher=(
                "MATCH (g:ServiceNowGroup) "
                "RETURN g.group_id AS group_id, coalesce(g.name, g.group_id) AS group_name "
                "ORDER BY group_id LIMIT $limit"
            ),
            columns=(
                ColumnDef("group_id", "string", "Group id"),
                ColumnDef("group_name", "string", "Group"),
            ),
            classification="internal",
            params=_LIMIT,
        ),
        # O16 loads frames — the BaseLoader :JobRun envelope.
        QuerySpec(
            id="loads.runs.v1",
            database="drydocs",
            description="Loader :JobRun envelope, newest first — the /loads timeline feed.",
            cypher=(
                "MATCH (r:JobRun) WHERE r.kind = 'load' "
                "RETURN r.run_id AS run_id, r.loader AS loader, r.source AS source, "
                "toString(r.started_at) AS started_at, toString(r.completed_at) AS completed_at, "
                "r.status AS status, r.rows_processed AS rows_processed, "
                "r.rows_changed AS rows_changed "
                "ORDER BY r.started_at DESC LIMIT $limit"
            ),
            columns=(
                ColumnDef("run_id", "string", "Run id"),
                ColumnDef("loader", "string", "Loader"),
                ColumnDef("source", "string", "Source"),
                ColumnDef("started_at", "string", "Started"),
                ColumnDef("completed_at", "string", "Completed"),
                ColumnDef("status", "string", "Status"),
                ColumnDef("rows_processed", "int", "Rows"),
                ColumnDef("rows_changed", "int", "Changed"),
            ),
            classification="internal",
            params=_LIMIT,
        ),
        QuerySpec(
            id="loads.rejects.v1",
            database="drydocs",
            description="Runs that rejected rows (rows_rejected > 0) — never silent drops.",
            cypher=(
                "MATCH (r:JobRun) WHERE r.kind = 'load' AND coalesce(r.rows_rejected, 0) > 0 "
                "RETURN r.run_id AS run_id, r.loader AS loader, "
                "toString(r.started_at) AS started_at, r.rows_rejected AS rows_rejected, "
                "r.rows_processed AS rows_processed "
                "ORDER BY r.started_at DESC LIMIT $limit"
            ),
            columns=(
                ColumnDef("run_id", "string", "Run id"),
                ColumnDef("loader", "string", "Loader"),
                ColumnDef("started_at", "string", "Started"),
                ColumnDef("rows_rejected", "int", "Rejected"),
                ColumnDef("rows_processed", "int", "Rows"),
            ),
            classification="internal",
            params=_LIMIT,
        ),
        QuerySpec(
            id="loads.drift-coverage.v1",
            database="drydocs",
            description=(
                "Removed-from-source drift per run (the D7 mark pass): runs whose "
                "full-diff marked or reactivated nodes."
            ),
            cypher=(
                "MATCH (r:JobRun) WHERE r.kind = 'load' AND "
                "(coalesce(r.nodes_marked_removed, 0) > 0 OR coalesce(r.nodes_reactivated, 0) > 0) "
                "RETURN r.run_id AS run_id, r.loader AS loader, "
                "toString(r.started_at) AS started_at, "
                "r.nodes_marked_removed AS marked_removed, r.nodes_reactivated AS reactivated "
                "ORDER BY r.started_at DESC LIMIT $limit"
            ),
            columns=(
                ColumnDef("run_id", "string", "Run id"),
                ColumnDef("loader", "string", "Loader"),
                ColumnDef("started_at", "string", "Started"),
                ColumnDef("marked_removed", "int", "Marked removed"),
                ColumnDef("reactivated", "int", "Reactivated"),
            ),
            classification="internal",
            params=_LIMIT,
        ),
        # O10 lineage frames — ddlineage is REAL but empty until the lineage
        # live-load gate flips the four m3_* entries; these specs return zero
        # rows until then and the UI shows its SYNTHESIZED demo honestly.
        QuerySpec(
            id="lineage.hops.v1",
            database="ddlineage",
            description=(
                "Source-to-target hops: every READS_FROM / WRITES_TO edge the Fork-3 "
                "writer landed (curated post-gate), with the activity endpoint "
                "(ETLProcess token / Script path / ControlMJob name) and the DataAsset."
            ),
            cypher=(
                "MATCH (x)-[r:READS_FROM|WRITES_TO]->(d:DataAsset) "
                "RETURN coalesce(x.token, x.path, x.job_name) AS activity, "
                "labels(x)[0] AS activity_type, type(r) AS hop, "
                "d.assetId AS asset_id, d.kind AS asset_kind "
                "ORDER BY activity, hop LIMIT $limit"
            ),
            columns=(
                ColumnDef("activity", "string", "Activity"),
                ColumnDef("activity_type", "string", "Type"),
                ColumnDef("hop", "string", "Hop"),
                ColumnDef("asset_id", "string", "Data asset"),
                ColumnDef("asset_kind", "string", "Asset kind"),
            ),
            classification="internal",
            params=_LIMIT,
        ),
        QuerySpec(
            id="lineage.data-assets.v1",
            database="ddlineage",
            description=(
                "DataAsset inventory with writer/reader degree — which activities "
                "produce and consume each asset."
            ),
            cypher=(
                "MATCH (d:DataAsset) "
                "OPTIONAL MATCH (w)-[:WRITES_TO]->(d) "
                "OPTIONAL MATCH (rd)-[:READS_FROM]->(d) "
                "RETURN d.assetId AS asset_id, d.kind AS kind, "
                "count(DISTINCT w) AS writers, count(DISTINCT rd) AS readers "
                "ORDER BY asset_id LIMIT $limit"
            ),
            columns=(
                ColumnDef("asset_id", "string", "Data asset"),
                ColumnDef("kind", "string", "Kind"),
                ColumnDef("writers", "int", "Writers"),
                ColumnDef("readers", "int", "Readers"),
            ),
            classification="internal",
            params=_LIMIT,
        ),
        QuerySpec(
            id="lineage.schema-definition.v1",
            database="ddlineage",
            description=(
                "Definition-level schema of each DataAsset node: identity, kind, and "
                "the property set present. Column-level schema arrives with the DPL "
                "Metadata-As-Code enrichment feed (G17) — this spec is honest about "
                "carrying node-schema only until that feed lands."
            ),
            cypher=(
                "MATCH (d:DataAsset) "
                "RETURN d.assetId AS asset_id, d.kind AS kind, "
                "[k IN keys(d) WHERE NOT k IN ['assetId', 'kind']] AS properties, "
                "toString(d.created_at) AS created_at "
                "ORDER BY asset_id LIMIT $limit"
            ),
            columns=(
                ColumnDef("asset_id", "string", "Data asset"),
                ColumnDef("kind", "string", "Kind"),
                ColumnDef("properties", "string", "Properties present"),
                ColumnDef("created_at", "string", "First seen"),
            ),
            classification="internal",
            params=_LIMIT,
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
