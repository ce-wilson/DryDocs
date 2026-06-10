# DryDocs Node Quick Reference

Generated from `drydocs/ontology/relationship_vocabulary.yaml` (node_classifications), 2026-06-09.

How to use: when writing a new relationship, find your **source node's Source type** and your **target node's Target type**, then read the matching row of the SECTION 1 `prov_matrix` to get the PROV-O term and Neo4j label.

- **Source type** — PROV classification when the node is on the `from` side of an edge.
- **Target type** — PROV classification when the node is on the `to` side. Collections are targeted as plain Entities (`prov:Collection ⊑ prov:Entity`); the special `Collection → any = HAD_MEMBER` row applies only when the collection is the source.
- **—** — node does not participate in the PROV matrix (structural ORG / infrastructure class). Edges touching it are local-only (`prov_maps_to: null`).
- All `dd:` classes expand via `namespaces.py` to `https://drydocs.local/ontology#`.

## Control-M (M3, active)

| Node label | Source type | Target type | PROV-O / W3C type |
|:---|:---|:---|:---|
| ControlMJob | Activity | Activity | dd:ControlMJob (prov:Activity) |
| ControlMFolder | Collection | Entity | dd:ControlMFolder (prov:Collection)⁷ |
| ControlMServer | — | — | dd:ControlMServer (local platform)¹ |
| Condition | Entity | Entity | dd:Condition (prov:Entity) |
| JobRun | Activity | Activity | dd:JobRun (prov:Activity)² |

## Control-M phase 2 (planned)

| Node label | Source type | Target type | PROV-O / W3C type |
|:---|:---|:---|:---|
| ControlMJobRun | Activity | Activity | dd:ControlMJobRun (prov:Activity)² |
| Deployment | Activity | Activity | dd:Deployment (prov:Activity) |
| Developer | Agent | Agent | prov:Person |
| AppUser | Agent | Agent | prov:SoftwareAgent |
| Script | Entity | Entity | dd:Script (prov:Entity / prov:Plan) |
| ETLProcess | Activity | Activity | dd:ETLProcess (prov:Activity) |
| ExecutionHost | Agent | Agent | prov:SoftwareAgent³ |
| DataSource | Entity | Entity | dcat:Dataset |
| DataTarget | Entity | Entity | dcat:Dataset |

## SEAL (active)

| Node label | Source type | Target type | PROV-O / W3C type |
|:---|:---|:---|:---|
| Application | Agent | Agent | prov:SoftwareAgent |
| Employee | Agent | Agent | prov:Agent |
| Membership | — | — | org:Membership⁴ |
| Role | — | — | org:Role |
| Port | Entity | Entity | dprod:Port |

## Catalog (active)

| Node label | Source type | Target type | PROV-O / W3C type |
|:---|:---|:---|:---|
| CatalogLOB | Agent | Agent | org:OrganizationalUnit |
| BusinessSegment | Agent | Agent | org:FormalOrganization⁵ |
| DevTeam | Agent | Agent | org:OrganizationalUnit |
| ProductLine | Entity | Entity | dd:ProductLine (local) |
| Product | Entity | Entity | dd:Product (local) |
| AreaProduct | Entity | Entity | dd:AreaProduct (local)⁸ |
| JiraBoard | Entity | Entity | dd:JiraBoard (local) |

## Architecture flow (planned, normalized from pre-ontology diagram)

| Node label | Source type | Target type | PROV-O / W3C type |
|:---|:---|:---|:---|
| Code | Collection | Entity | dd:Code (prov:Collection) |
| Bitbucket | Entity | Entity | dd:CodeRepository (local)⁶ |
| PipelineService | Entity | Entity | dd:PipelineService (prov:Entity) |
| Batch | Collection | Entity | dd:Batch (prov:Collection) |
| File | Entity | Entity | dd:File (prov:Entity) |

---

¹ Not an Agent — edges targeting ControlMServer (SCHEDULED_ON, DEPLOYED_TO) cannot map to `prov:wasAssociatedWith`; they are local infrastructure edges.

² JobRun (loader provenance, base ontology) and ControlMJobRun (phase-2 runtime execution) are distinct labels — do not merge.

³ Classified as SoftwareAgent (not pure infrastructure) so `AppUser -[:DELEGATES_TO]-> ExecutionHost` legally maps to `prov:actedOnBehalfOf` (Agent → Agent).

⁴ Corrected from "prov:Membership" (no such class in PROV-O). N-ary relation node from the W3C ORG ontology; HAS_MEMBERSHIP / OF_ROLE / HELD_BY edges are local-only.

⁵ Doc said org:FormalOrganization; catalog supplement comment says org:Organization. FormalOrganization adopted as the more precise valid term.

⁶ Candidate `prov:Location` if STORED_IN is ever mapped to `prov:atLocation`.

⁷ Renamed from JobFolder (2026-06-09). Supplements and loaders still write `:JobFolder` until migrated: `MATCH (n:JobFolder) SET n:ControlMFolder REMOVE n:JobFolder`.

⁸ Area Product Group / Team of Teams (Align/PAT terminology). Sits between Product and DevTeam in the hierarchy: `Product -[:HAS_AREA_PRODUCT]-> AreaProduct -[:HAS_DEV_TEAM]-> DevTeam`. DevTeams also carry `SUPPORTS {team_type, sponsored}` edges to both Product and AreaProduct — `team_type` (aligned|flex|dedicated) is an edge property, not a fixed node attribute.
