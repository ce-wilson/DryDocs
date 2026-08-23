# DryDocs Node Quick Reference

Generated from `drydocs_core/ontology/relationship_vocabulary.yaml` (node_classifications).
Created 2026-06-09; updated 2026-07-22 (K4 BusinessApplication reshape APPLIED, TOM
attribution + ProductRole active, DataAsset replaces DataSource/DataTarget,
ControlMHostGroup, doc-graph L7 family). Companion to
[`docs/RELATIONSHIP_GUIDE.md`](../../docs/RELATIONSHIP_GUIDE.md); lives beside
[`DryDocs_Ontology_Documentation.md`](DryDocs_Ontology_Documentation.md) as layer-2
(ontology) reference.

How to use: when writing a new relationship, find your **source node's Source type** and your **target node's Target type**, then read the matching row of the SECTION 1 `prov_matrix` to get the PROV-O term and Neo4j label.

- **Source type** — PROV classification when the node is on the `from` side of an edge.
- **Target type** — PROV classification when the node is on the `to` side. Collections are targeted as plain Entities (`prov:Collection ⊑ prov:Entity`); the special `Collection → any = HAD_MEMBER` row applies only when the collection is the source.
- **—** — node does not participate in the PROV matrix (structural ORG / infrastructure / n-ary class). Edges touching it are local-only (`prov_maps_to: null`).
- All `dd:` classes expand via `namespaces.py` to `https://drydocs.local/ontology#`.

## Control-M (M3, active)

| Node label | Source type | Target type | PROV-O / W3C type |
|:---|:---|:---|:---|
| ControlMJob | Activity | Activity | dd:ControlMJob (prov:Activity) |
| ControlMFolder | Collection | Entity | dd:ControlMFolder (prov:Collection)¹ |
| ControlMApplication | Collection | Entity | dd:ControlMApplication (prov:Collection)² |
| ControlMServer | — | — | dd:ControlMServer (local platform)³ |
| Condition | Entity | Entity | dd:Condition (prov:Entity) |
| JobRun | Activity | Activity | dd:JobRun (prov:Activity)⁴ |
| ControlMHostGroup | Collection | Entity | dd:ControlMHostGroup (prov:Collection)¹⁵ |

## Control-M phase 2 (planned)

| Node label | Source type | Target type | PROV-O / W3C type |
|:---|:---|:---|:---|
| ControlMJobRun | Activity | Activity | dd:ControlMJobRun (prov:Activity)⁴ |
| Deployment | Activity | Activity | dd:Deployment (prov:Activity) |
| Developer | Agent | Agent | prov:Person |
| AppUser | Agent | Agent | prov:SoftwareAgent |
| Script | Entity | Entity | dd:Script (prov:Entity / prov:Plan) |
| ETLProcess | Activity | Activity | dd:ETLProcess (prov:Activity) |
| ExecutionHost | Agent | Agent | prov:SoftwareAgent⁵ |
| DataAsset | Entity | Entity | dcat:Dataset¹⁶ |

## SEAL (active)

| Node label | Source type | Target type | PROV-O / W3C type |
|:---|:---|:---|:---|
| BusinessApplication | Entity | Entity | prov:Entity / dprod:DataProduct⁶ |
| Employee | Agent | Agent | prov:Agent |
| Membership | — | — | org:Membership⁷ ⁸ |
| Role | — | — | org:Role⁸ |
| Port | Entity | Entity | dprod:Port |

## SEAL TOM attribution + Product Cabinet (ACTIVE — K4 2026-07-15, K6 2026-07-20)

The qualified-attribution pattern applied at K4 (gate signed 2026-07-10):
`BusinessApplication -[:QUALIFIED_ATTRIBUTION]-> Attribution -[:HAS_AGENT]-> Employee`,
`Attribution -[:HAD_ROLE]-> TOMRole`. ProductRole is the independent Product Cabinet
role scheme (K5 gate + K6 supplement; scope :Product / :AreaProduct only).

| Node label | Source type | Target type | PROV-O / W3C type |
|:---|:---|:---|:---|
| Document | Entity | Entity | prov:Entity⁹ |
| Attribution | — | — | prov:Attribution (n-ary influence node) |
| TOMRole | — | — | skos:Concept¹⁰ |
| ProductRole | — | — | skos:Concept¹⁰ |

## Catalog (active)

| Node label | Source type | Target type | PROV-O / W3C type |
|:---|:---|:---|:---|
| CatalogLOB | Agent | Agent | org:OrganizationalUnit |
| BusinessSegment | Agent | Agent | org:FormalOrganization¹¹ |
| DevTeam | Agent | Agent | org:OrganizationalUnit |
| ProductLine | Entity | Entity | dd:ProductLine (local) |
| Product | Entity | Entity | dd:Product (local) |
| AreaProduct | Entity | Entity | dd:AreaProduct (local)¹² |
| JiraBoard | Entity | Entity | dd:JiraBoard (local) |

## Architecture flow (planned, normalized from pre-ontology diagram)

| Node label | Source type | Target type | PROV-O / W3C type |
|:---|:---|:---|:---|
| Code | Collection | Entity | dd:Code (prov:Collection) |
| Bitbucket | Entity | Entity | dd:CodeRepository (local)¹³ |
| PipelineService | Entity | Entity | dd:PipelineService (prov:Entity) |
| Batch | Collection | Entity | dd:Batch (prov:Collection) |
| File | Entity | Entity | dd:File (prov:Entity) |

## Software registry (active, gate-confirmed 2026-07-07)

| Node label | Source type | Target type | PROV-O / W3C type |
|:---|:---|:---|:---|
| Vendor | Agent | Agent | org:Organization¹⁴ |
| SoftwareProduct | Entity | Entity | dd:SoftwareProduct |

## Docs corpus — lexical graph (active, gate `bmc-docs-lexical-load` accepted 2026-07-08)

| Node label | Source type | Target type | PROV-O / W3C type |
|:---|:---|:---|:---|
| Document | Entity | Entity | prov:Entity⁹ |
| Chunk | Entity | Entity | prov:Entity |

## Vendor-docs entity core (CONFIRMED — gate `vendor-docs-entity-core` SIGNED OFF 2026-08-22, 21/21; vocab stays planned until the Q24/Q25 builds)

| Node label | Source type | Target type | PROV-O / W3C type |
|:---|:---|:---|:---|
| ControlMUtility | Entity | Entity | dd:ControlMUtility (name-keyed; minted from bmc-docs-controlm-utilities page titles, deterministic — gate §A) |

(:DocSection is REUSED for the vendor TOC tree — second use recorded on its
classification, gate §E2; not a new label.)

## Doc graph — traceability backbone (ACTIVE, gate `doc-traceability-feedback` signed off 2026-07-20; L7 / ADR 0006)

| Node label | Source type | Target type | PROV-O / W3C type |
|:---|:---|:---|:---|
| DocSource | Entity | Entity | prov:Entity (DCAT-catalog-shaped registry node) |
| DesignDoc | Entity | Entity | dd:DesignDoc (managed, rev-tracked, outline-validated) |
| DocSection | Entity | Entity | dd:DocSection (keyed origin/doc_id/anchor) |
| Requirement | Entity | Entity | dd:Requirement (proposition from any registered source) |
| Component | Entity | Entity | dd:Component (implementation artifact cited by a requirement) |
| TestCase | Entity | Entity | dd:TestCase (verification citation; open `kind` enum) |
| FeedbackNote | Entity | Entity | dd:FeedbackNote (anchor-keyed review annotation) |

## Context graph — SOSA/SSN (EXPERIMENTAL, planned)

W3C standard but **not** a declared company standard; seeded only by the opt-in
`sosa_experimental_supplement.cypher`, every term tagged `adoption: "experimental"`.
SOSA edges sit **outside** the PROV matrix (they map to `sosa:*` terms, not PROV);
the Source/Target types below are the behavioural fallback only.

| Node label | Source type | Target type | Primary type |
|:---|:---|:---|:---|
| Observation | Activity | Activity | sosa:Observation |
| Sensor | Agent | Agent | sosa:Sensor |
| Result | Entity | Entity | sosa:Result |
| ObservableProperty | Entity | Entity | sosa:ObservableProperty |

ControlMJob and ControlMFolder additionally act as `sosa:FeatureOfInterest` via
`:CAN_ACT_AS` — an orthogonal context-graph role; their primary classification above
is unchanged.

---

¹ Renamed from `JobFolder` (ADR 0003 follow-up, 2026-07-05). Migration:
`drydocs/migrations/20260705_rename_jobfolder_to_controlmfolder.cypher`; supplements
and loaders all write `:ControlMFolder` now.

² The Control-M APPLICATION grouping from the folder HEADER ROW in `CM_DEF_VJOB`
(JOB_ID=1) — deliberately **not** the business `:Application` / SEAL concept. Written
in the folder pass so grouping labels exist before the jobs pass. SME gate
`controlm-q1q3-phase1` (2026-07-07).

³ Not an Agent — edges targeting ControlMServer (SCHEDULED_ON, DEPLOYED_TO) cannot map to `prov:wasAssociatedWith`; they are local infrastructure edges.

⁴ JobRun (loader provenance, base ontology) and ControlMJobRun (phase-2 runtime execution) are distinct labels — do not merge.

⁵ Classified as SoftwareAgent (not pure infrastructure) so `AppUser -[:DELEGATES_TO]-> ExecutionHost` legally maps to `prov:actedOnBehalfOf` (Agent → Agent).

⁶ APPLIED at K4 (2026-07-15; gate signed 2026-07-10): was label `Application`, class
prov:SoftwareAgent — the old typing carried three incompatible PROV readings
(SoftwareAgent, dprod:Port children, org role-holders). Reclassed prov:Entity /
dprod:DataProduct and renamed `:Application` → `:BusinessApplication` across vocabulary,
schema supplements, loaders, constraints, and tests in the same K4 change. Distinct from
`:ControlMApplication` (footnote ²) — never conflate.

⁷ Corrected from "prov:Membership" (no such class in PROV-O). N-ary relation node from the W3C ORG ontology; HAS_MEMBERSHIP / OF_ROLE / HELD_BY edges are local-only.

⁸ APPLIED at K4 (2026-07-15): the SEAL use of Membership/Role (HAS_MEMBERSHIP /
OF_ROLE / HELD_BY) is deprecated in favor of the TOM qualified-attribution pattern
(`QUALIFIED_ATTRIBUTION` → Attribution → Employee / TOMRole). `org:Membership` /
`org:Role` remain active for the PAT product hierarchy (e.g. DevTeam→Membership).

⁹ Two registry entries share the `Document` label and class (`prov:Entity`): the
**docs-corpus** Document (active — the bmc-docs lexical graph, `DESCRIBES` →
SoftwareProduct) and the **SEAL-reshape / docmeta** Document (proposed — target of
`prov:hadPrimarySource`). Distinct entries in `node_classifications`; do not merge
their notes.

¹⁰ Two INDEPENDENT skos:ConceptScheme role vocabularies — do not conflate with each
other or with `:Role` (org:Role, PAT hierarchy only). **TOMRole** (scheme `tom_roles`,
ACTIVE at K4, the gate-REVISED fixed 7): application_owner, primary_information_owner,
backup_information_owner, cto, technology_risk_controls, design_authority,
operate_manager (L1/L2 lives on the Attribution node). **ProductRole** (scheme
`product_roles`, ACTIVE at K6 2026-07-20, fixed 7): area_product_owner, product_owner,
product_architect, tech_partner, data_owner, data_certifier, analytics_lead — no shared
`cto` concept (K5 ruling supersedes the 2026-07-10 §B record); area_product_owner and
tech_partner attach only to :AreaProduct.

¹¹ Doc said org:FormalOrganization; catalog supplement comment says org:Organization. FormalOrganization adopted as the more precise valid term.

¹² Area Product Group / Team of Teams (Align/PAT terminology). Sits between Product and DevTeam in the hierarchy: `Product -[:HAS_AREA_PRODUCT]-> AreaProduct -[:HAS_DEV_TEAM]-> DevTeam`. DevTeams also carry `SUPPORTS {team_type, sponsored}` edges to both Product and AreaProduct — `team_type` (aligned|flex|dedicated) is an edge property, not a fixed node attribute.

¹³ Candidate `prov:Location` if STORED_IN is ever mapped to `prov:atLocation`.

¹⁴ Third-party software company/brand ONLY (ADR 0004); ids shared with the
drydocs-icons manifest. What a vendor ships is a `SoftwareProduct` (`MADE_BY` → Vendor).
Since the C12 platforms gate (2026-07-21) the registry model also carries the scheduler
role: `SoftwareProduct {role: orchestrator}` + `USES_SOFTWARE` (SchedulerKind retired).

¹⁵ Gate `controlm-hosts-topology` CONFIRMED 2026-07-09: host/node group from psgmgr
CM_HOSTS (vendor CMS_NODGRP). NOT `ControlMGroup` — the CM_DEF_VJOB GROUP_NAME
application-group concept is different. Loader pending (P3; definition-side probes owed).

¹⁶ Added at the lineage rel-vocabulary gate 2026-07-15: the D1 proxy shape — a piece of
data a process reads/writes (hdfs / s3 / hive_table / local_file / Glue table …), keyed
on assetId, constrained in all three data DBs so the `ddall` composite joins on it.
Replaces the RETIRED DataSource / DataTarget pair (edge direction encodes the role).
