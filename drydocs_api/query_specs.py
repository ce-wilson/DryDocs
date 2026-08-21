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
  reads uncertain content declares ``uncertain=True`` as an explicit, reviewed
  row here — never a default; those results are watermarked. Pre-fold this
  meant reading the retired ``ddcontext``/``ddall`` databases; since G102 the
  uncertain realm is the :Uncertain label — ADR 0011 §117)
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
# `ddschema` describes the schema, not the estate; `ddlineage` (retired at X1 —
# ADR 0002 amendment, 2026-08-04) was excluded here since G30 as
# provisioned-but-written-by-nothing (curated lineage lands in `drydocs` per D1/D2).
# Keeping the allow-list explicit makes a new database a deliberate edit rather than
# a typo; `tests/unit/test_database_names.py` proves the read set has a writer.
SPEC_DATABASES: frozenset[str] = frozenset({"drydocs"})
# G102 (2026-08-18): `ddcontext` and `ddall` RETIRED with the fold — the
# uncertain realm is the :Uncertain LABEL inside the one database, and the
# watermark trigger is each spec's own `uncertain=True` declaration
# (ADR 0011 §117). WATERMARKED_DATABASES is gone: keying trust on storage
# location was the root cause the gate's §B named.
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
    #: G102 / ADR 0011 clause 1: True ONLY for specs that deliberately read the
    #: :Uncertain realm (the re-homed context specs and the audit spec). Such a
    #: spec is EXEMPT from the structural ground-truth exclusion below and its
    #: exports carry the trust watermark. Ground-truth specs leave the default.
    uncertain: bool = False
    #: R20: relationship types this spec names that the vocabulary registers as
    #: PLANNED ONLY (no loader yet). Naming one is allowed solely inside an
    #: OPTIONAL MATCH whose null result the description explains — a written-
    #: down degradation, never an accident. The static guard in
    #: tests/unit/test_query_spec_vocabulary.py fails on any planned-only type
    #: that is not listed here, and on any listed type that has since gone
    #: active (the list must shrink when the loader lands).
    planned_terms: tuple[str, ...] = ()


class UnknownSpecError(KeyError):
    """Raised for a spec id not in the registry."""


_LIMIT = (ParamSpec("limit", "int", required=False, default=500),)


def _with_ground_truth_exclusion(spec: QuerySpec) -> QuerySpec:
    """ADR 0011 clause 1 guard (a), applied at REGISTRY BUILD — never by hand.

    Post-fold, ground truth and :Uncertain context share one database, so every
    ground-truth spec must exclude :Uncertain. Hand-editing ~30 queries is the
    exact failure the clause names; instead this rides the :SchemaMeta exclusion
    idiom that test_schema_meta_exclusion already forces onto every bound label
    var: each `NOT x:SchemaMeta` becomes `NOT x:SchemaMeta AND NOT x:Uncertain`.
    Specs declaring `uncertain=True` are exempt — they exist to read that realm.
    tests/unit/test_uncertain_boundary.py proves the transform landed on every
    ground-truth spec and that none mentions :Uncertain any other way.
    """
    if spec.uncertain or spec.database != "drydocs":
        return spec
    cypher = re.sub(
        r"NOT\s+(\w+):SchemaMeta(?!\s+AND\s+NOT\s+\1:Uncertain)",
        r"NOT \1:SchemaMeta AND NOT \1:Uncertain",
        spec.cypher,
    )
    if cypher == spec.cypher:
        return spec
    return QuerySpec(
        id=spec.id,
        database=spec.database,
        description=spec.description,
        cypher=cypher,
        columns=spec.columns,
        classification=spec.classification,
        params=spec.params,
        uncertain=spec.uncertain,
        planned_terms=spec.planned_terms,
    )


QUERY_SPECS: dict[str, QuerySpec] = {
    s.id: _with_ground_truth_exclusion(s)
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
                "attribution via CONTAINS_JOB (§A1). R20 (2026-08-21): audited against the "
                "declared vocabulary and found CURRENT — BELONGS_TO_APPLICATION, HAS_PORT, "
                ":Port and Port.active_state are the K7/K8 + S3 shapes; an empty answer means "
                "load-folder-attribution / the SEAL extract have not run on THAT graph (Neo4j "
                "says so as unknown-label notifications), not that the vocabulary moved."
            ),
            cypher=(
                "MATCH (f:ControlMFolder)-[r:BELONGS_TO_APPLICATION {role: 'seal_app_ref'}]"
                "->(p:Port)<-[:HAS_PORT]-(a:BusinessApplication) "
                "WHERE NOT f:SchemaMeta AND p.kind = 'BatchProcessing' "
                "OPTIONAL MATCH (f)-[:SCHEDULED_ON]->(s:ControlMServer) "
                "OPTIONAL MATCH (f)-[:CONTAINS_JOB]->(j:ControlMJob) "
                "RETURN f.sched_table AS folder, s.name AS data_center, "
                "a.app_id AS app_id, a.name AS application, r.origin AS origin, "
                "p.active_state AS port_state, count(DISTINCT j) AS jobs "
                "ORDER BY folder LIMIT $limit"
            ),
            columns=(
                ColumnDef("folder", "string", "Folder"),
                ColumnDef("data_center", "string", "Data center"),
                ColumnDef("app_id", "string", "Application ID"),
                ColumnDef("application", "string", "Application"),
                ColumnDef("origin", "string", "Origin"),
                ColumnDef("port_state", "string", "Port state"),
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
        # ── K11 — the steward mapping-cascade specs (gate seal-app-ref-edge-
        # reshape §G, SIGNED OFF 2026-08-03). The cascade is Product Line ->
        # Product -> Business Application (a LIST, §G6) -> orchestrator (§G1,
        # prefilled from the declared edge, §G2) -> unmapped-folder filter
        # (§G7). The screen drafts store rows only; the K8 loader writes. ──
        QuerySpec(
            # The backlog acceptance spells this intake.area_tree.v1; the registry id
            # convention is kebab-case (enforced at import) and wins — recorded at the
            # O47 close rather than silently diverged.
            id="intake.area-tree.v1",
            database="drydocs",
            description=(
                "The intake page's area cascade (O47): ProductLine -> HAS_PRODUCT "
                "-> Product -> HAS_AREA_PRODUCT -> AreaProduct, one call, flat "
                "rows the picker groups client-side (cacheable — the tree changes "
                "only at catalog loads). WRITTEN FOR THE DAY THE EDGE LANDS: "
                "catalog_has_area_product is status planned with no extract, and "
                "the AreaProduct nodes that exist today are pat_product_mapping "
                "fallback anchors with no parent edge and no name — so "
                "area_product is null until the area_products extract arrives, "
                "the pane says so, and 'Unknown' stays the honest answer at that "
                "level (the plan's own rule)."
            ),
            cypher=(
                "MATCH (pl:ProductLine) WHERE NOT pl:SchemaMeta "
                "OPTIONAL MATCH (pl)-[:HAS_PRODUCT]->(p:Product) "
                "OPTIONAL MATCH (p)-[:HAS_AREA_PRODUCT]->(ap:AreaProduct) "
                "RETURN pl.product_line_id AS product_line_id, pl.name AS product_line, "
                "p.product_id AS product_id, p.name AS product, "
                "ap.area_product_id AS area_product_id, ap.name AS area_product "
                "ORDER BY product_line, product, area_product LIMIT $limit"
            ),
            columns=(
                ColumnDef("product_line_id", "string", "Product line ID"),
                ColumnDef("product_line", "string", "Product line"),
                ColumnDef("product_id", "string", "Product ID"),
                ColumnDef("product", "string", "Product"),
                ColumnDef("area_product_id", "string", "Area product ID"),
                ColumnDef("area_product", "string", "Area product"),
            ),
            classification="internal",
            params=_LIMIT,
        ),
        QuerySpec(
            id="mappings.catalog-cascade.v1",
            database="drydocs",
            description=(
                "The cascade's catalog spine: ProductLine -> HAS_PRODUCT -> Product "
                "-> HAS_APPLICATION -> BusinessApplication, flat rows the picker "
                "groups client-side. §G6 rules the COMPANY reading of "
                "HAS_APPLICATION (a structural support link, 1:many by design — the "
                "picker returns a LIST, never a single application; semantics "
                "reconciled at K13). PRODUCER-SIDE catalog_has_application is "
                "still planned with no loader — loading waits on the C9 "
                "product-scoped-extract condition — so app_id is null here until "
                "that lands; the pane says so and degrades to the full "
                "application search."
            ),
            cypher=(
                "MATCH (pl:ProductLine) WHERE NOT pl:SchemaMeta "
                "OPTIONAL MATCH (pl)-[:HAS_PRODUCT]->(p:Product) "
                "OPTIONAL MATCH (p)-[:HAS_APPLICATION]->(a:BusinessApplication) "
                "RETURN pl.product_line_id AS product_line_id, pl.name AS product_line, "
                "p.product_id AS product_id, p.name AS product, "
                "a.app_id AS app_id, a.name AS application "
                "ORDER BY product_line, product, application LIMIT $limit"
            ),
            columns=(
                ColumnDef("product_line_id", "string", "Product line ID"),
                ColumnDef("product_line", "string", "Product line"),
                ColumnDef("product_id", "string", "Product ID"),
                ColumnDef("product", "string", "Product"),
                ColumnDef("app_id", "string", "Application ID"),
                ColumnDef("application", "string", "Application"),
            ),
            classification="internal",
            params=_LIMIT,
            # the third leg is OPTIONAL and null by contract until the C9 extract lands
            planned_terms=("HAS_APPLICATION",),
        ),
        QuerySpec(
            id="mappings.orchestrators.v1",
            database="drydocs",
            description=(
                "Orchestrator candidates for the cascade's §G1 picker: registry "
                "SoftwareProducts carrying role='orchestrator' (the C12 ruling — "
                "the role value IS the classification; no capability node layer)."
            ),
            cypher=(
                "MATCH (sp:SoftwareProduct {role: 'orchestrator'}) "
                "WHERE NOT sp:SchemaMeta "
                "RETURN sp.product_id AS product_id, sp.name AS product "
                "ORDER BY product LIMIT $limit"
            ),
            columns=(
                ColumnDef("product_id", "string", "Product ID"),
                ColumnDef("product", "string", "Orchestrator"),
            ),
            classification="internal",
            params=_LIMIT,
        ),
        QuerySpec(
            id="mappings.app-orchestrators.v1",
            database="drydocs",
            description=(
                "Per-application orchestrator edges for the §G2 prefill and the "
                "§G3 1:N display: every USES_SOFTWARE edge onto an orchestrator "
                "product with its source ('batch-port' = the SEAL declaration, "
                "prefill only; 'app-code-mapping' = authored by a confirmed "
                "mapping) and origin (declared | confirmed). An app with several "
                "orchestrators is mid-migration — a NORMAL state, never drift."
            ),
            cypher=(
                "MATCH (a:BusinessApplication)-[u:USES_SOFTWARE]->"
                "(sp:SoftwareProduct {role: 'orchestrator'}) "
                "WHERE NOT a:SchemaMeta "
                "RETURN a.app_id AS app_id, sp.product_id AS product_id, "
                "sp.name AS product, u.source AS source, u.origin AS origin, "
                "u.orchestrator_raw AS declared_raw "
                "ORDER BY app_id, product LIMIT $limit"
            ),
            columns=(
                ColumnDef("app_id", "string", "Application ID"),
                ColumnDef("product_id", "string", "Product ID"),
                ColumnDef("product", "string", "Orchestrator"),
                ColumnDef("source", "string", "Source"),
                ColumnDef("origin", "string", "Origin"),
                ColumnDef("declared_raw", "string", "Declared string"),
            ),
            classification="internal",
            params=_LIMIT,
        ),
        QuerySpec(
            id="mappings.unmapped-folders.v1",
            database="drydocs",
            description=(
                "The cascade's 'available folders' queue — §G7 rules it UNMAPPED "
                "ONLY (folders with no BELONGS_TO_APPLICATION {role:'seal_app_ref'} "
                "edge; the naming-pattern filter is OPTIONAL and layered on top "
                "client-side, never primary). run_as_users aggregates the folder's "
                "distinct job owners (the Control-M RUN_AS/OWNER field) — surfaced "
                "as a sort option by SME direction at the gate."
            ),
            cypher=(
                "MATCH (f:ControlMFolder) WHERE NOT f:SchemaMeta "
                "AND NOT EXISTS { MATCH (f)-[:BELONGS_TO_APPLICATION "
                "{role: 'seal_app_ref'}]->(:Port) } "
                "OPTIONAL MATCH (ca:ControlMApplication)-[:CONTAINS_FOLDER]->(f) "
                "OPTIONAL MATCH (f)-[:SCHEDULED_ON]->(s:ControlMServer) "
                "OPTIONAL MATCH (f)-[:CONTAINS_JOB]->(j:ControlMJob) "
                "WITH f, ca, s, count(DISTINCT j) AS jobs, "
                "[o IN collect(DISTINCT j.owner) WHERE o IS NOT NULL] AS owners "
                "RETURN f.folder_id AS folder_id, f.sched_table AS folder, "
                "ca.name AS app_code, s.name AS data_center, jobs, "
                "reduce(acc = '', o IN owners | acc + "
                "CASE WHEN acc = '' THEN '' ELSE ', ' END + o) AS run_as_users "
                "ORDER BY folder LIMIT $limit"
            ),
            columns=(
                ColumnDef("folder_id", "string", "Folder id"),
                ColumnDef("folder", "string", "Folder"),
                ColumnDef("app_code", "string", "App code"),
                ColumnDef("data_center", "string", "Data center"),
                ColumnDef("jobs", "int", "Jobs"),
                ColumnDef("run_as_users", "string", "Run-as users"),
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
                "Dev teams with the count of applications attributed to them as developer "
                "(arch_develops = (:BusinessApplication)-[:WAS_ATTRIBUTED_TO {role: "
                "'developed_by'}]->(:DevTeam), C3 gate; M:N both ways per the K5 §E "
                "ruling). R20 (2026-08-21): this spec formerly asked a DEVELOPS edge "
                "that was never registered — the vocabulary names the PROV attribution "
                "shape, so every team read 0. Team rosters are confidential material — "
                "Internal handling (J23)."
            ),
            cypher=(
                "MATCH (dt:DevTeam) WHERE NOT dt:SchemaMeta "
                "OPTIONAL MATCH (a:BusinessApplication)-[:WAS_ATTRIBUTED_TO {role: 'developed_by'}]"
                "->(dt) "
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
                "m.unmapped_role AS unmapped_role, e.employee_id AS holder_sid "
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
            id="software.doc-coverage.v1",
            database="drydocs",
            description=(
                "Registered software products as the graph holds them, with the count "
                "of :Document nodes joined by the gate-confirmed DESCRIBES edge. A ZERO "
                "HERE MEANS NO EDGE IN THIS DATABASE AND NOTHING MORE: "
                "config/doc-source-registry.yaml is the declaration, and a corpus "
                "targeting a database this spec cannot read (dddocs, unprovisioned "
                "pending G32) is absent by TOPOLOGY, not by defect. `drydocs "
                "docs-coverage` is the multi-database reconciliation a single-database "
                "spec cannot perform."
            ),
            cypher=(
                "MATCH (sp:SoftwareProduct) WHERE NOT sp:SchemaMeta "
                "OPTIONAL MATCH (sp)-[:MADE_BY]->(v:Vendor) WHERE NOT v:SchemaMeta "
                "OPTIONAL MATCH (d:Document)-[r:DESCRIBES]->(sp) WHERE NOT d:SchemaMeta "
                "WITH sp, v, count(DISTINCT d) AS documents, "
                "collect(DISTINCT r.target_version) AS versions "
                "RETURN sp.product_id AS product_id, sp.name AS name, "
                "coalesce(v.vendor_id, '-') AS vendor_id, sp.category AS category, "
                "documents, "
                "CASE WHEN size(versions) = 0 THEN '-' ELSE reduce(s = '', x IN versions | "
                "CASE WHEN s = '' THEN toString(x) ELSE s + ', ' + toString(x) END) END "
                "AS target_versions "
                "ORDER BY documents DESC, product_id LIMIT $limit"
            ),
            columns=(
                ColumnDef("product_id", "string", "Product"),
                ColumnDef("name", "string", "Name"),
                ColumnDef("vendor_id", "string", "Vendor"),
                ColumnDef("category", "string", "Category"),
                ColumnDef("documents", "int", "Documents (DESCRIBES)"),
                ColumnDef("target_versions", "string", "Target versions"),
            ),
            classification="internal-public",
            params=_LIMIT,
        ),
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
                "Data-series chains: the ETL process each job's command line "
                "invokes and the assets it lands (curated lineage; zero rows is "
                "the honest state until the live load runs)."
            ),
            # G89 (2026-08-21, gate vocabulary-domains-and-id-policy §C3): this spec
            # MATCHed [:TRIGGERS], a PLANNED edge no loader may write — and one whose
            # registered shape is Script -> ETLProcess, not job -> ETLProcess, so the
            # surface implied data that could not exist in either direction. Resolved
            # onto INVOKES (scheduler_invokes, ACTIVE since G55): ControlMJob ->
            # Script | ETLProcess is exactly the job-launches-process fact the runbook
            # series needs. The TRIGGERS entry stays planned and untouched; when its
            # build lands, the wrapper-script hop is a second, finer spec, not a
            # rewrite of this one.
            cypher=(
                "MATCH (j:ControlMJob)-[:INVOKES]->(e:ETLProcess) "
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
        # pointed at `ddlineage`, which was written by nothing (retired at X1,
        # 2026-08-04) — an empty database read for the wrong reason. They still return zero
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
            database="drydocs",  # G30: was `ddlineage` (retired at X1) — see the block comment
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
            database="drydocs",  # G30: was `ddlineage` (retired at X1) — see the block comment
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
            id="infra.app-job-host-locations.v1",
            database="drydocs",
            description=(
                "Z3 (gate server-location-ontology): the distinct job hosts for one "
                "business application, each carrying its resolved physical location "
                "when the tiered ExecutionHost->Server join found one and an explicit "
                "UNMATCHED marker when it did not — the selection that feeds the Z4 "
                "nslookup resolver. Traversal per gate SS C3: app -> folder attribution "
                "-> jobs -> RUNS_ON host/group -> RESOLVES_TO_SERVER -> LOCATED_IN."
            ),
            cypher=(
                "MATCH (a:BusinessApplication {app_id: $app_id}) WHERE NOT a:SchemaMeta "
                "MATCH (a)-[:HAS_PORT]->(bp:Port)<-[:BELONGS_TO_APPLICATION]-(f:ControlMFolder) "
                "WHERE NOT bp:SchemaMeta AND NOT f:SchemaMeta "
                "MATCH (f)-[:CONTAINS_JOB]->(j:ControlMJob)-[:RUNS_ON]->(t) "
                "WHERE NOT j:SchemaMeta AND NOT t:SchemaMeta "
                "OPTIONAL MATCH (t)-[:CONTAINS_HOST]->(m:ExecutionHost) WHERE NOT m:SchemaMeta "
                "WITH DISTINCT CASE WHEN t:ExecutionHost THEN t ELSE m END AS h "
                "WHERE h IS NOT NULL "
                "OPTIONAL MATCH (h)-[res:RESOLVES_TO_SERVER]->(s:Server)-[loc:LOCATED_IN]->(dc:DataCenter) "
                "WHERE NOT s:SchemaMeta AND NOT dc:SchemaMeta "
                "RETURN h.nodeid AS job_host, "
                "CASE WHEN res IS NULL THEN 'UNMATCHED' ELSE res.match_tier END AS match_tier, "
                "s.name AS server, dc.name AS data_center, dc.city AS city, "
                "dc.state AS state, dc.country AS country, dc.location_grain AS location_grain "
                "ORDER BY job_host LIMIT $limit"
            ),
            columns=(
                ColumnDef("job_host", "string", "Job host (nodeid)"),
                ColumnDef("match_tier", "string", "Join tier / UNMATCHED"),
                ColumnDef("server", "string", "Inventory server"),
                ColumnDef("data_center", "string", "Data center (physical)"),
                ColumnDef("city", "string", "City"),
                ColumnDef("state", "string", "State"),
                ColumnDef("country", "string", "Country"),
                ColumnDef("location_grain", "string", "Declared grain"),
            ),
            classification="internal",
            params=(ParamSpec("app_id", "string"), *_LIMIT),
        ),
        QuerySpec(
            id="console.agent-runs.v1",
            database="drydocs",  # G102 fold (2026-08-18): the R1 ruling's substance ("never in ground truth") survives as :Uncertain on the write; uncertain=True below is the watermark trigger
            description=(
                "R3 agent-run telemetry for the admin view: one :AgentRun per "
                "answered question (kind 'qa', mirroring :JobRun), newest first. "
                "Question and caller identity appear as sha256 + length ONLY — "
                "full text lives solely in the local JSONL ledger. Reads "
                ":Uncertain rows (uncertain=True), so rows carry the UNCERTAIN "
                "watermark; the telemetry values themselves are measured."
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
            uncertain=True,
            params=_LIMIT,
        ),
        QuerySpec(
            id="context.label-census.v1",
            database="drydocs",  # G102 fold: the census re-scopes to the :Uncertain realm
            description=(
                "Label census of the :Uncertain realm — post-fold (G102) the "
                "uncertain content is a LABEL inside the one database, so the "
                "census matches it directly; exports carry the trust watermark."
            ),
            cypher=(
                "MATCH (n:Uncertain) WHERE NOT n:SchemaMeta "
                "RETURN labels(n) AS labels, count(*) AS count ORDER BY count DESC"
            ),
            columns=(
                ColumnDef("labels", "string", "Labels"),
                ColumnDef("count", "int", "Nodes"),
            ),
            classification="internal-public",
            uncertain=True,
        ),
        QuerySpec(
            id="audit.uncertain-reachable.v1",
            database="drydocs",
            description=(
                "ADR 0011 clause-1 guard (c), the live audit for the G102 fold: "
                ":Uncertain nodes sharing ANY relationship with a non-Uncertain "
                "node. EXPECTED 0 — any hit is a promotion that skipped the HITL "
                "gate, the exact bug class the fold trades the database wall for. "
                "uncertain=True: this spec exists to read that realm and is exempt "
                "from the structural ground-truth exclusion."
            ),
            cypher=(
                "OPTIONAL MATCH (u:Uncertain) WITH count(u) AS uncertain_total "
                "OPTIONAL MATCH (b:Uncertain)--(g) "
                "WHERE NOT g:Uncertain AND NOT g:SchemaMeta "
                "RETURN uncertain_total, count(DISTINCT b) AS breaching"
            ),
            columns=(
                ColumnDef("uncertain_total", "int", "Uncertain nodes"),
                ColumnDef("breaching", "int", "Reachable from ground truth (expect 0)"),
            ),
            classification="internal-public",
            uncertain=True,
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
    # G102: the trigger is the spec's own declaration (ADR 0011 §117 — "a spec
    # is watermarked iff its Cypher touches :Uncertain, declared per row").
    # The database-name trigger retired with the fold.
    return spec.uncertain
