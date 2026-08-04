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
- a spec that binds a label the schema meta-graph stamps on a ``:SchemaMeta``
  exemplar (``drydocs_core/schema/schema_graph.cypher`` — applied manually,
  keyless by design) excludes the exemplars with the rename-proof label
  predicate ``WHERE NOT n:SchemaMeta`` (O33; the exemplar carries the REAL
  label with no key, so an unguarded spec returns it as a phantom null-keyed
  row — and the meta-graph also MERGEs exemplar EDGES, including property-
  qualified ones like ``{role: 'seal_app_ref'}``, so pattern specs are
  exposed too, not just single-node ones). Enforced by
  ``tests/unit/test_schema_meta_exclusion.py`` against the committed
  meta-graph, and proven live by ``tests/integration/test_meta_graph_exclusion.py``.
- no spec returns a graph-internal element id (``elementId()`` / ``id()``) —
  they are unstable across restore and re-load, so a deep link or manifest
  built on one silently resolves to a DIFFERENT node later (O27 rule 3)

**Authoring conventions: see ``drydocs_api/AUTHORING.md``** (O27) — the three
rules a new spec must satisfy, with their rationale: consume gate-confirmed
edges rather than re-deriving meaning from raw staged columns; the
``kind:namespace/name`` external-ref grammar; and the element-id rule enforced
below.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from drydocs_api.guard import ensure_no_element_ids, ensure_read_only
from drydocs_api.queries import ParamSpec

# Databases a spec may read. Deliberately NOT the whole provisioned topology:
# `ddlineage` is provisioned but written by nothing (G30 ruling 2026-07-26 — curated
# lineage lands in `drydocs` per ADR 0002 D1/D2), so a spec pointed there would read
# an empty database forever. Leaving it out makes that a deliberate edit rather than
# a typo; `tests/unit/test_database_names.py` proves the read set has a writer.
SPEC_DATABASES: frozenset[str] = frozenset({"drydocs", "ddcontext", "ddall"})
# Databases whose content is synthesized/uncertain — results carry the
# SYNTHESIZED watermark in the manifest AND as a grid-visible column.
WATERMARKED_DATABASES: frozenset[str] = frozenset({"ddcontext", "ddall"})
# The publish-boundary vocabulary. This is a SECOND copy of what
# config/classification.yaml defines — the API is pure and does not read the
# config at import — so tests/unit/test_classification.py asserts the two agree.
# That guard is why J23's collapse to three levels could be missed here for a
# day: nothing checked. `internal-confidential` was retired 2026-07-31 (J23);
# `internal` absorbs it.
CLASSIFICATIONS: frozenset[str] = frozenset({"external", "internal-public", "internal"})
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
            description=(
                "Business applications for the Explorer Applications frame, keyed on the "
                "canonical app_id (gate business-application-identity 2026-07-27 — the "
                "console never emits the issuing registry's name; ADR 0010 rule 4)."
            ),
            cypher=(
                "MATCH (a:BusinessApplication) WHERE NOT a:SchemaMeta "
                "RETURN a.app_id AS app_id, a.name AS name, a.status AS status "
                "ORDER BY app_id LIMIT $limit"
            ),
            columns=(
                ColumnDef("app_id", "string", "Application ID"),
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
                "WHERE NOT f:SchemaMeta "
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
                "MATCH (c:Condition) WHERE NOT c:SchemaMeta "
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
                "ControlMFolder -> BusinessApplication crosswalk: the ruled folder-grain "
                "attribution edge BELONGS_TO_APPLICATION {role:'seal_app_ref'} onto the "
                "application's BatchProcessing Port (K7/K8 — re-bound from the retired "
                "job-grain derivation per gate §A2), with the ORIGIN disclosure flag "
                "(§B3), the folder's data center and job count. Jobs inherit the "
                "attribution via CONTAINS_JOB (§A1)."
            ),
            cypher=(
                "MATCH (f:ControlMFolder)-[r:BELONGS_TO_APPLICATION {role: 'seal_app_ref'}]"
                "->(p:Port)<-[:HAS_PORT]-(a:BusinessApplication) "
                "WHERE NOT f:SchemaMeta AND p.kind = 'BatchProcessing' "
                "OPTIONAL MATCH (f)-[:SCHEDULED_ON]->(s:ControlMServer) "
                "OPTIONAL MATCH (f)-[:CONTAINS_JOB]->(j:ControlMJob) "
                "RETURN f.sched_table AS folder, s.name AS data_center, "
                "a.app_id AS app_id, a.name AS application, r.origin AS origin, "
                "count(DISTINCT j) AS jobs "
                "ORDER BY folder LIMIT $limit"
            ),
            columns=(
                ColumnDef("folder", "string", "Folder"),
                ColumnDef("data_center", "string", "Data center"),
                ColumnDef("app_id", "string", "Application ID"),
                ColumnDef("application", "string", "Application"),
                ColumnDef("origin", "string", "Origin"),
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
                "pattern to :BusinessApplication (SME review 2026-07-21; re-bound to "
                "the K7-ruled folder-grain edges at K8 per gate §A2): a code whose "
                "folders all attribute to ONE application is a 'direct (dedicated "
                "code)' candidate; a code spanning several applications is a 'shared "
                "platform code'; no attribution = the SME work queue. The "
                "authoritative code->application mapping is the K9 defined-mapping "
                "store (app-code-mapping console domain); this view is the observed "
                "cross-check."
            ),
            cypher=(
                "MATCH (ca:ControlMApplication) WHERE NOT ca:SchemaMeta "
                "OPTIONAL MATCH (ca)-[:CONTAINS_FOLDER]->(f:ControlMFolder) "
                "OPTIONAL MATCH (f)-[:CONTAINS_JOB]->(j:ControlMJob) "
                "OPTIONAL MATCH (f)-[:BELONGS_TO_APPLICATION {role: 'seal_app_ref'}]"
                "->(:Port)<-[:HAS_PORT]-(a:BusinessApplication) "
                "WITH ca, count(DISTINCT f) AS folders, count(DISTINCT j) AS jobs, "
                "collect(DISTINCT a.app_id) AS app_ids "
                "RETURN ca.name AS app_code, "
                "CASE WHEN size(app_ids) = 0 THEN 'unmapped — SME queue' "
                "WHEN size(app_ids) = 1 THEN 'direct (dedicated code)' "
                "ELSE 'shared platform code' END AS mapping_pattern, "
                "size(app_ids) AS applications, folders, jobs, "
                "CASE WHEN size(app_ids) = 1 THEN app_ids[0] "
                "WHEN size(app_ids) = 0 THEN null "
                "ELSE toString(size(app_ids)) + ' applications' END AS mapped_to "
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
                "WHERE NOT f:SchemaMeta "
                "OPTIONAL MATCH (j)-[r:WAS_ASSOCIATED_WITH {role: 'seal_app_ref'}]"
                "->(a:BusinessApplication) "
                "WITH f, j, [h IN collect({app_id: a.app_id, name: a.name, "
                "method: r.match_method}) WHERE h.app_id IS NOT NULL] AS res "
                "RETURN f.sched_table AS folder, j.job_name AS job, "
                "f.folder_id AS folder_id, j.job_id AS job_id, "
                "CASE WHEN size(res) = 0 THEN null ELSE res[0].app_id END AS app_id, "
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
                ColumnDef("app_id", "string", "Application ID"),
                ColumnDef("application", "string", "Application"),
                # match_method keeps the source's own vocabulary ('seal', 'fid',
                # 'app_name', 'alias', 'manual') — gate §B2(ii): evidence records what
                # another system literally wrote. Renaming it here would make the
                # console misdescribe the graph's provenance, not tidy it.
                ColumnDef("match_method", "string", "Tier/evidence"),
                ColumnDef("status", "string", "Status"),
            ),
            classification="internal",
            params=_LIMIT,
        ),
        QuerySpec(
            id="mappings.seal-contact-roles.v1",
            database="drydocs",
            description=(
                "O24 override-list source rows: the LIVE SEAL operate-manager "
                "attributions (L1/L2) as loaded by seal_contacts.v1 — the K4 "
                "qualified-attribution shape (Attribution + HAD_ROLE -> TOMRole, "
                "HAS_AGENT -> Employee). These are the origin='source' rows the "
                "/mappings seal-contact-override grid pairs with the committed "
                "user overrides; the graph is never written by an override."
            ),
            cypher=(
                "MATCH (a:BusinessApplication)-[:QUALIFIED_ATTRIBUTION]->(m:Attribution) "
                "WHERE NOT a:SchemaMeta "
                "AND m.role_source_name IN ['L1 Operate Manager', 'L2 Operate Manager'] "
                "AND m.valid_to IS NULL "
                "OPTIONAL MATCH (m)-[:HAS_AGENT]->(e:Employee) "
                "RETURN a.app_id AS app_id, a.name AS application, "
                "m.role_source_name AS role_name, m.level AS level, "
                "e.employee_id AS holder_sid, e.full_name AS holder_name "
                "ORDER BY app_id, role_name LIMIT $limit"
            ),
            columns=(
                ColumnDef("app_id", "string", "Application ID"),
                ColumnDef("application", "string", "Application"),
                ColumnDef("role_name", "string", "Role"),
                ColumnDef("level", "string", "Level"),
                ColumnDef("holder_sid", "string", "Holder SID"),
                ColumnDef("holder_name", "string", "Holder"),
            ),
            classification="internal",
            params=_LIMIT,
        ),
        QuerySpec(
            id="explorer.servers.v1",
            database="drydocs",
            description="Control-M servers for the Explorer Servers frame.",
            cypher=(
                "MATCH (s:ControlMServer) WHERE NOT s:SchemaMeta "
                "RETURN s.name AS name ORDER BY name"
            ),
            columns=(ColumnDef("name", "string", "Server"),),
            classification="internal",
        ),
        # O15 ownership frames — the K4 qualified-attribution shape.
        QuerySpec(
            id="ownership.teams.v1",
            database="drydocs",
            description=(
                "Dev teams with their DEVELOPS application count (arch_develops, C3 gate). "
                "Team rosters are confidential material — Internal handling (J23)."
            ),
            cypher=(
                "MATCH (dt:DevTeam) WHERE NOT dt:SchemaMeta "
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
            classification="internal",
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
                "WHERE NOT a:SchemaMeta "
                "OPTIONAL MATCH (m)-[:HAD_ROLE]->(tr:TOMRole) "
                "OPTIONAL MATCH (m)-[:HAS_AGENT]->(e) "
                "RETURN a.app_id AS app_id, m.attribution_id AS attribution_id, "
                "m.role_source_name AS source_role, tr.id AS tom_role, m.level AS level, "
                "m.unmapped_role AS unmapped_role, e.sid AS holder_sid "
                "ORDER BY m.unmapped_role DESC, app_id LIMIT $limit"
            ),
            columns=(
                ColumnDef("app_id", "string", "Application ID"),
                ColumnDef("attribution_id", "string", "Attribution id"),
                ColumnDef("source_role", "string", "Source role"),
                ColumnDef("tom_role", "string", "TOM role"),
                ColumnDef("level", "string", "Level"),
                ColumnDef("unmapped_role", "string", "Unmapped?"),
                ColumnDef("holder_sid", "string", "Holder SID"),
            ),
            classification="internal",
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
                "MATCH (g:ServiceNowGroup) WHERE NOT g:SchemaMeta "
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
        # O18 docs frames — the lexical corpus (Document -> Chunk, PART_OF).
        QuerySpec(
            id="docs.documents.v1",
            database="drydocs",
            description=(
                "Corpus documents with chunk counts — trust_default (VERBATIM / "
                "GROUNDED / SYNTHESIZED) visible as a column, never hidden."
            ),
            cypher=(
                "MATCH (d:Document) WHERE NOT d:SchemaMeta "
                "OPTIONAL MATCH (c:Chunk)-[:PART_OF]->(d) "
                "RETURN d.doc_id AS doc_id, d.title AS title, "
                "d.trust_default AS trust_default, d.classification AS classification, "
                "count(c) AS chunks "
                "ORDER BY doc_id LIMIT $limit"
            ),
            columns=(
                ColumnDef("doc_id", "string", "Document"),
                ColumnDef("title", "string", "Title"),
                ColumnDef("trust_default", "string", "Trust tier"),
                ColumnDef("classification", "string", "Classification"),
                ColumnDef("chunks", "int", "Chunks"),
            ),
            classification="internal-public",
            params=_LIMIT,
        ),
        QuerySpec(
            id="docs.chunks.v1",
            database="drydocs",
            description=(
                "Corpus chunks with their parent document and effective trust tier "
                "(chunk override, else the document default)."
            ),
            cypher=(
                "MATCH (c:Chunk)-[:PART_OF]->(d:Document) "
                "WHERE NOT c:SchemaMeta "
                "RETURN c.chunk_id AS chunk_id, d.doc_id AS doc_id, c.seq AS seq, "
                "c.heading AS heading, coalesce(c.trust, d.trust_default) AS trust "
                "ORDER BY doc_id, seq LIMIT $limit"
            ),
            columns=(
                ColumnDef("chunk_id", "string", "Chunk"),
                ColumnDef("doc_id", "string", "Document"),
                ColumnDef("seq", "int", "Seq"),
                ColumnDef("heading", "string", "Heading"),
                ColumnDef("trust", "string", "Trust tier"),
            ),
            classification="internal-public",
            params=_LIMIT,
        ),
        QuerySpec(
            id="docs.trust-provenance.v1",
            database="drydocs",
            description="Trust-tier census over the corpus — the provenance audit frame.",
            cypher=(
                "MATCH (c:Chunk)-[:PART_OF]->(d:Document) "
                "WHERE NOT c:SchemaMeta "
                "RETURN coalesce(c.trust, d.trust_default) AS trust, "
                "count(*) AS chunks, count(DISTINCT d) AS documents "
                "ORDER BY trust"
            ),
            columns=(
                ColumnDef("trust", "string", "Trust tier"),
                ColumnDef("chunks", "int", "Chunks"),
                ColumnDef("documents", "int", "Documents"),
            ),
            classification="internal-public",
        ),
        # O17 runbooks frames.
        QuerySpec(
            id="runbooks.series.v1",
            # G30 ruling (2026-07-26): curated lineage lands in `drydocs`, per ADR
            # 0002 D1/D2. Was `ddlineage` — a database nothing writes.
            database="drydocs",
            description=(
                "Data-series chains: FileWatcher-triggered ETL processes and the "
                "assets they land (curated post-gate; zero rows is the honest state "
                "until the lineage live-load gate flips)."
            ),
            cypher=(
                "MATCH (j:ControlMJob)-[:TRIGGERS]->(e:ETLProcess) "
                "WHERE NOT j:SchemaMeta "
                "OPTIONAL MATCH (e)-[:WRITES_TO]->(d:DataAsset) "
                "RETURN j.job_name AS trigger_job, e.token AS process, e.kind AS kind, "
                "collect(DISTINCT d.assetId) AS lands "
                "ORDER BY trigger_job LIMIT $limit"
            ),
            columns=(
                ColumnDef("trigger_job", "string", "Trigger job"),
                ColumnDef("process", "string", "ETL process"),
                ColumnDef("kind", "string", "Kind"),
                ColumnDef("lands", "string", "Lands (assets)"),
            ),
            classification="internal",
            params=_LIMIT,
        ),
        QuerySpec(
            id="runbooks.metadata-completeness.v1",
            database="drydocs",
            description=(
                "Runbook metadata completeness per job: whether the Description "
                "field carries anything for the runbook generator to work with "
                "(the description-field metadata plan's coverage view). Missing "
                "rows float to the top — the fix-in-batches work queue."
            ),
            cypher=(
                "MATCH (f:ControlMFolder)-[:CONTAINS_JOB]->(j:ControlMJob) "
                "WHERE NOT f:SchemaMeta "
                "WITH f, j, (j.description IS NULL OR j.description = '') AS missing "
                "RETURN f.sched_table AS folder, j.job_name AS job, "
                "CASE WHEN missing THEN 'missing' ELSE 'present' END AS description_metadata "
                "ORDER BY missing DESC, folder, job LIMIT $limit"
            ),
            columns=(
                ColumnDef("folder", "string", "Folder"),
                ColumnDef("job", "string", "Job"),
                ColumnDef("description_metadata", "string", "Description metadata"),
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
                "MATCH (r:JobRun) WHERE NOT r:SchemaMeta AND r.kind = 'load' "
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
                "MATCH (r:JobRun) WHERE NOT r:SchemaMeta AND r.kind = 'load' "
                "AND coalesce(r.rows_rejected, 0) > 0 "
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
                "MATCH (r:JobRun) WHERE NOT r:SchemaMeta AND r.kind = 'load' AND "
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
        QuerySpec(
            id="loads.status-items.v1",
            database="drydocs",
            description=(
                "O28 node-status envelope: the per-source status items a producing "
                "system DERIVED for each load run, newest first. One row per item "
                "({type, level, message, error?} — see "
                "knowledge/standards/node-status-envelope.md). The item rides as a "
                "JSON string because Neo4j cannot hold a map inside a list property; "
                "the consumer parses ONE stable shape. A run with no items is "
                "healthy — 'never ran' is the ABSENCE of a :JobRun, which is why no "
                "all-clear item is emitted and the two states stay distinguishable."
            ),
            cypher=(
                "MATCH (r:JobRun) WHERE NOT r:SchemaMeta AND r.kind = 'load' "
                "AND r.status_items IS NOT NULL AND size(r.status_items) > 0 "
                "UNWIND r.status_items AS status_item "
                "RETURN r.run_id AS run_id, r.loader AS loader, r.source AS source, "
                "toString(r.started_at) AS started_at, status_item "
                "ORDER BY started_at DESC, run_id LIMIT $limit"
            ),
            columns=(
                ColumnDef("run_id", "string", "Run id"),
                ColumnDef("loader", "string", "Loader"),
                ColumnDef("source", "string", "Source"),
                ColumnDef("started_at", "string", "Started"),
                ColumnDef("status_item", "string", "Status item (JSON)"),
            ),
            classification="internal",
            params=_LIMIT,
        ),
        # O10 lineage frames — target `drydocs`, where the curated writer lands
        # (G30 ruling 2026-07-26; ADR 0002 "Residency clarification"). They were
        # pointed at `ddlineage`, which is provisioned but written by nothing, so
        # they read an empty database for the wrong reason. They still return zero
        # rows until the lineage live-load gate flips the four m3_* vocabulary
        # entries — that gate, not the database, is what keeps them empty, and the
        # UI shows its SYNTHESIZED demo honestly meanwhile.
        QuerySpec(
            id="lineage.hops.v1",
            database="drydocs",
            description=(
                "Source-to-target hops: every READS_FROM / WRITES_TO edge the Fork-3 "
                "writer landed (curated post-gate), with the activity endpoint "
                "(ETLProcess token / Script path / ControlMJob name) and the DataAsset."
            ),
            cypher=(
                "MATCH (x)-[r:READS_FROM|WRITES_TO]->(d:DataAsset) "
                "WHERE NOT x:SchemaMeta "
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
            database="drydocs",  # G30: was ddlineage — see the block comment above
            description=(
                "DataAsset inventory with writer/reader degree — which activities "
                "produce and consume each asset."
            ),
            cypher=(
                "MATCH (d:DataAsset) WHERE NOT d:SchemaMeta "
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
            database="drydocs",  # G30: was ddlineage — see the block comment above
            description=(
                "Definition-level schema of each DataAsset node: identity, kind, and "
                "the property set present. Column-level schema arrives with the DPL "
                "Metadata-As-Code enrichment feed (G17) — this spec is honest about "
                "carrying node-schema only until that feed lands."
            ),
            cypher=(
                "MATCH (d:DataAsset) WHERE NOT d:SchemaMeta "
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
            id="console.agent-runs.v1",
            database="ddcontext",  # R1 gate ruling 2026-07-23: :AgentRun lands in ddcontext, never drydocs
            description=(
                "R3 agent-run telemetry for the admin view: one :AgentRun per "
                "answered question (kind 'qa', mirroring :JobRun), newest first. "
                "Question and caller identity appear as sha256 + length ONLY — "
                "full text lives solely in the local JSONL ledger. Reads "
                "ddcontext, so rows carry the standard SYNTHESIZED watermark; "
                "the telemetry values themselves are measured, not synthesized."
            ),
            cypher=(
                "MATCH (r:AgentRun) WHERE NOT r:SchemaMeta AND r.kind = 'qa' "
                "RETURN r.run_id AS run_id, toString(r.recorded_at) AS recorded_at, "
                "r.tier AS tier, r.model AS model, r.llm_calls AS llm_calls, "
                "r.tokens_total AS tokens_total, r.cost_est_usd AS cost_est_usd, "
                "r.cypher_count AS cypher_count, r.fix_retries AS fix_retries, "
                "r.response_ms_total AS response_ms_total, "
                "r.question_sha256 AS question_sha256, r.question_chars AS question_chars "
                "ORDER BY r.recorded_at DESC LIMIT $limit"
            ),
            columns=(
                ColumnDef("run_id", "string", "Run id"),
                ColumnDef("recorded_at", "string", "Recorded"),
                ColumnDef("tier", "string", "Tier"),
                ColumnDef("model", "string", "Model"),
                ColumnDef("llm_calls", "int", "LLM calls"),
                ColumnDef("tokens_total", "int", "Tokens"),
                ColumnDef("cost_est_usd", "string", "Cost (est)"),
                ColumnDef("cypher_count", "int", "Cyphers"),
                ColumnDef("fix_retries", "int", "Fix retries"),
                ColumnDef("response_ms_total", "int", "Total ms"),
                ColumnDef("question_sha256", "string", "Question sha256"),
                ColumnDef("question_chars", "int", "Chars"),
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
                "MATCH (n) WHERE NOT n:SchemaMeta "
                "RETURN labels(n) AS labels, count(*) AS count ORDER BY count DESC"
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
        assert _SPEC_ID_RE.match(
            spec.id
        ), f"spec id '{spec.id}' is not versioned (<area>.<frame>.vN)"
        assert (
            spec.database in SPEC_DATABASES
        ), f"spec '{spec.id}': database '{spec.database}' not in the reviewed set"
        assert (
            spec.classification in CLASSIFICATIONS
        ), f"spec '{spec.id}': classification '{spec.classification}' unknown"
        assert spec.columns, f"spec '{spec.id}' declares no columns"
        ensure_read_only(spec.cypher)  # raises WriteRejected on a write-shaped spec
        ensure_no_element_ids(spec.cypher, f"spec '{spec.id}'")  # O27 rule 3


_validate_registry()


def query_spec(spec_id: str) -> QuerySpec:
    try:
        return QUERY_SPECS[spec_id]
    except KeyError as exc:
        raise UnknownSpecError(spec_id) from exc


def is_watermarked(spec: QuerySpec) -> bool:
    return spec.database in WATERMARKED_DATABASES
