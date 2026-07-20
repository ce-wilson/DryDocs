# DryDocs Node Quick Reference

Generated from `drydocs_core/ontology/relationship_vocabulary.yaml` (node_classifications).
Created 2026-06-09; updated 2026-07-09 (software registry, docs corpus, ControlMApplication,
SEAL TOM reshape proposals, SOSA context graph). Companion to
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
| DataSource | Entity | Entity | dcat:Dataset |
| DataTarget | Entity | Entity | dcat:Dataset |

## SEAL (active)

| Node label | Source type | Target type | PROV-O / W3C type |
|:---|:---|:---|:---|
| Application | Agent | Agent | prov:SoftwareAgent⁶ |
| Employee | Agent | Agent | prov:Agent |
| Membership | — | — | org:Membership⁷ ⁸ |
| Role | — | — | org:Role⁸ |
| Port | Entity | Entity | dprod:Port |

## SEAL TOM reshape (PROPOSED, gate-bound 2026-07-08)

Nothing here is active — these classes exist only so the proposed qualified-attribution
edges type-check under the PROV matrix once the SME confirms. See
`config/gate-prompts/seal-tom-attribution-reshape.yaml`.

| Node label | Source type | Target type | PROV-O / W3C type |
|:---|:---|:---|:---|
| Document | Entity | Entity | prov:Entity⁹ |
| Attribution | — | — | prov:Attribution (n-ary influence node) |
| TOMRole | — | — | skos:Concept¹⁰ |

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

⁶ GATE-BOUND PROPOSAL (2026-07-08 review, NOT applied): reclass to prov:Entity /
dprod:DataProduct — the node currently carries three incompatible PROV readings
(SoftwareAgent, dprod:Port children, org role-holders). Active loaders and the drift
guard depend on the current SoftwareAgent typing; do not flip until the SME confirms.
See `config/gate-prompts/seal-tom-attribution-reshape.yaml`.

⁷ Corrected from "prov:Membership" (no such class in PROV-O). N-ary relation node from the W3C ORG ontology; HAS_MEMBERSHIP / OF_ROLE / HELD_BY edges are local-only.

⁸ GATE-BOUND PROPOSAL (2026-07-08, NOT applied): deprecate the SEAL use of
Membership/Role (HAS_MEMBERSHIP / OF_ROLE / HELD_BY) in favor of the TOM
qualified-attribution pattern (`QUALIFIED_ATTRIBUTION` → Attribution → Employee /
TOMRole). `org:` stays for the PAT product hierarchy (e.g. DevTeam→Membership).
Status stays active until the SME confirms.

⁹ Two registry entries share the `Document` label and class (`prov:Entity`): the
**docs-corpus** Document (active — the bmc-docs lexical graph, `DESCRIBES` →
SoftwareProduct) and the **SEAL-reshape / docmeta** Document (proposed — target of
`prov:hadPrimarySource`). Distinct entries in `node_classifications`; do not merge
their notes.

¹⁰ SEAL Technical Operating Model role vocabulary (skos:ConceptScheme, 6 concepts:
cto, application_owner, information_owner, data_owner, operate_manager,
risk_compliance_officer). DISTINCT from `:Role` (org:Role, PAT hierarchy only).

¹¹ Doc said org:FormalOrganization; catalog supplement comment says org:Organization. FormalOrganization adopted as the more precise valid term.

¹² Area Product Group / Team of Teams (Align/PAT terminology). Sits between Product and DevTeam in the hierarchy: `Product -[:HAS_AREA_PRODUCT]-> AreaProduct -[:HAS_DEV_TEAM]-> DevTeam`. DevTeams also carry `SUPPORTS {team_type, sponsored}` edges to both Product and AreaProduct — `team_type` (aligned|flex|dedicated) is an edge property, not a fixed node attribute.

¹³ Candidate `prov:Location` if STORED_IN is ever mapped to `prov:atLocation`.

¹⁴ Third-party software company/brand ONLY (ADR 0004); ids shared with the
drydocs-icons manifest. What a vendor ships is a `SoftwareProduct` (`MADE_BY` → Vendor).
