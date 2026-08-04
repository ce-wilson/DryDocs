# DryDocs Relationship Guide

How to create and maintain graph relationships with correct ontology mappings.

---

## The decision matrix

Classify the source and target node by PROV-O type, then read the Neo4j label
to use. Add a `role` property on the edge whenever the same label appears in
multiple contexts on the same node pair.

| Source type | Target type | PROV-O term | Neo4j label |
|---|---|---|---|
| Activity | Activity | `prov:wasInformedBy` | `WAS_INFORMED_BY` |
| Activity | Entity | `prov:used` | `USED` |
| Activity | Entity *(produces)* | `prov:generated` | `GENERATED` |
| Activity | Agent | `prov:wasAssociatedWith` | `WAS_ASSOCIATED_WITH` |
| Entity | Activity | `prov:wasGeneratedBy` | `WAS_GENERATED_BY` |
| Entity | Entity | `prov:wasDerivedFrom` | `WAS_DERIVED_FROM` |
| Entity | Agent | `prov:wasAttributedTo` | `WAS_ATTRIBUTED_TO` |
| Agent | Agent | `prov:actedOnBehalfOf` | `ACTED_ON_BEHALF_OF` |
| Collection | any | `prov:hadMember` | `HAD_MEMBER` |

**Tip — `USED` vs `GENERATED`:** both are Activity→Entity. Use `USED` when
the activity *reads* the entity; use `GENERATED` when the activity *produces*
the entity.

**Existing domain-specific labels** (e.g., `REQUIRES_IN_CONDITION`,
`EMITS_OUT_CONDITION`, `CONTAINS_JOB`) keep their names for query clarity
but are declared in the supplement as mapping to the correct PROV-O term.
New relationships should use the standard label from the matrix above.

---

## Node type quick reference

Abridged — the full per-domain catalog (source/target types, gate-bound proposals,
registry/docs-corpus/SOSA labels) is
[`knowledge/ontology/NODE_QUICK_REFERENCE.md`](../knowledge/ontology/NODE_QUICK_REFERENCE.md).

| Node label | PROV-O / W3C type | Supplement |
|---|---|---|
| `ControlMJob` | `prov:Activity` | `ontology_supplement.cypher` |
| `ControlMFolder` | `prov:Collection` | `ontology_supplement.cypher` |
| `ControlMServer` | local Platform | `ontology_supplement.cypher` |
| `Condition` | `prov:Entity` | `ontology_supplement.cypher` |
| `JobRun` | `prov:Activity` | *(base ontology)* |
| `BusinessApplication` | `prov:Entity` / `dprod:DataProduct` (K4 reshape 2026-07-15) | `seal_ontology_supplement.cypher` |
| `Employee` | `prov:Agent` | `seal_ontology_supplement.cypher` |
| `Membership` | `org:Membership` | `seal_ontology_supplement.cypher` |
| `Role` | `org:Role` | `seal_ontology_supplement.cypher` |
| `Port` | dprod:Port | `seal_ontology_supplement.cypher` |
| `CatalogLOB` | `org:OrganizationalUnit` | `catalog_ontology_supplement.cypher` |
| `BusinessSegment` | `org:FormalOrganization` | `catalog_ontology_supplement.cypher` |
| `DevTeam` | `org:OrganizationalUnit` | `catalog_ontology_supplement.cypher` |
| `ProductLine` | local | `catalog_ontology_supplement.cypher` |
| `Product` | local | `catalog_ontology_supplement.cypher` |
| `JiraBoard` | local | `catalog_ontology_supplement.cypher` |

---

## Same-row-derived nodes — the join-restatement rule

> **Status: CONFIRMED (C5), 2026-07-18** (gate `same-row-derived-edges`, `config/gate-log.md`). This section is a
> **methodology** rule, not a new relationship type: it adds no entry to
> `relationship_vocabulary.yaml` (Step 6 below doesn't apply to it) and requires no supplement
> block. It governs which edges among nodes derived from the *same source row* are legitimate
> to create at all, in any domain — read it before you reach Step 4 below. Guarded by the
> `m3-verify` check `no direct ControlMApplication<->ControlMServer edge`.

### The problem

One source row sometimes derives more than one node. The live case: one
`psgmgr.CM_DEF_VTAB` folder row derives `:ControlMFolder` (the row's own subject) plus
`:ControlMServer` (from `DATA_CENTER`) and, via the folder-header join, `:ControlMApplication`
(from the header row's `APPLICATION` — see `controlm_folders.cypher`). Once several nodes share
a birth row, it is tempting to wire every pair of them together — but most of those pairwise
edges would only restate the row's own join, not assert a new fact. The classic analogy: a
City/State/Country address row justifies City→State→Country, never *also* a direct
City→Country edge — that edge carries no fact the chain doesn't already carry, and it has no
provenance of its own to justify existing independently.

### Two shapes, two rules

**Hierarchy** — the derived nodes have a natural containment/scheduling order (A contains B
contains C; A schedules B). Chain it: each edge asserts exactly one containment or scheduling
fact, one level at a time. A skip-level edge (A→C directly) that merely restates the row's own
join is **BANNED** — reach C from A by traversal at query time
(`(a)-[:X]->(b)-[:Y]->(c)`), never by a stored edge.

**Star** — the derived nodes are independent attributes of one row **subject**, with no
hierarchy between them (e.g., a SEAL application row deriving its two `:Port` nodes and its
embedded-contact `:Employee`/`:Attribution` chains — see `seal_applications.cypher`). Each
satellite relates to the subject only. Satellite↔satellite edges (Port↔Employee, Employee↔
Employee, Port↔Port) are **BANNED** unless an independent source — not this row — asserts that
relationship in its own right.

### The test

Before writing any edge between two nodes that came off the same row, ask:

> Does this edge carry a fact the chain (or the star's subject-edges) doesn't already imply,
> with its **own** provenance? If not, it's a join-restatement — don't create it.

If the answer is "yes, and here is the independent source that asserts it," the edge is not a
join-restatement — it is a genuinely new fact and follows the normal 8-step checklist below
(classify both nodes, pick the matrix row, register, supplement, gate) like any other
relationship.

### The only way to an exception

A skip-level or satellite↔satellite edge is never added ad hoc inside a loader. It happens only
through the HITL gate (`docs/restructure/03-hitl-sme-flow.md`), presented like any other
mapping decision, with its own `relationship_vocabulary.yaml` entry (`status: planned`, citing
the *independent* source that asserts the fact — never "the same row") and its own supplement
block — Steps 6–7 of the checklist below. The gate's job here is specifically to confirm the
edge is not a restatement before it is allowed to exist.

**Not covered by this rule:** a *separately computed* derived/transitive edge that summarizes a
longer chain spanning **different** source rows (e.g., `WAS_INFORMED_BY`, which materializes
successor→predecessor reachability across the recursive `CM_DEF_LNKI_P_VW`/`CM_DEF_LNKO_P_VW`
condition join, `derived: true`, possibly several hops deep) is a different, already-recognized
pattern — a materialized shortcut over many rows for query performance, not a same-row
join-restatement. It still needs its own vocabulary entry and provenance (and already has one:
`m3_was_informed_by`), but it is not what this rule bans.

### Applied to the live case

`ControlMFolder` is the row's subject; `ControlMServer` (`DATA_CENTER`) and
`ControlMApplication` (header-row `APPLICATION`) are two *independent* attributes of that one
folder row — a **star on the folder**, not a hierarchy between server and application:

```
(app:ControlMApplication)-[:CONTAINS_FOLDER]->(f:ControlMFolder)-[:SCHEDULED_ON]->(srv:ControlMServer)
```

**Recommendation: no direct `ControlMApplication`↔`ControlMServer` edge, in either direction,
of any type.** "Which servers does this app's work run on" is a traversal, not a stored edge:

```cypher
MATCH (app:ControlMApplication)-[:CONTAINS_FOLDER]->(f:ControlMFolder)-[:SCHEDULED_ON]->(srv:ControlMServer)
RETURN DISTINCT app.name, srv.name
```

A direct edge here would (a) restate the folder row's own two joins, (b) drift out of sync with
the folder if either side moves without anyone updating the shortcut, and (c) need its own
justification for direction and cardinality — none of which is needed since the traversal is
exactly one hop longer than either half-edge alone.

---

## Creating a new relationship — 8-step checklist

Work top to bottom. Each step has exactly one file to touch.

### Step 1 — Check the vocabulary

Open the registry directory [`drydocs_core/ontology/relationship_vocabulary/`](../drydocs_core/ontology/relationship_vocabulary/)
(S5: per-domain fragments merged in sorted-filename order — read the whole set,
edit the fragment matching your edge's `domain`). Search for your source node, target node, or intent. If an entry already
exists with `status: active`, use it — do not create a duplicate.

### Step 2 — Classify the source node

Look up the source node label in the **Node type quick reference** above.
If it is not listed, check its `SUBCLASS_OF` chain in the relevant supplement
file to find its PROV-O class.

### Step 3 — Classify the target node

Same as Step 2 for the target.

### Step 4 — Pick the matrix row

Match source type + target type to the decision matrix. That gives you the
`neo4j_label` to use.

### Step 5 — Choose a `role` value

If the same label already appears on the same node pair (e.g., a job that
`USED` both a config file and a script), add `role: "snake_case_verb_noun"`
to distinguish them (e.g., `role: "reads_config"`, `role: "executes_script"`).
If this is the only use of this label on these nodes, `role` can be omitted.

### Step 6 — Register in the vocabulary

Add an entry to `local_relationships` in the fragment for your edge's domain
(`drydocs_core/ontology/relationship_vocabulary/4N-local-<domain>.yaml`):

```yaml
- id:           domain_relationship_name        # unique snake_case id
  neo4j_label:  LABEL_FROM_MATRIX
  role:         role_value_or_null
  from_node:    SourceNodeLabel
  to_node:      TargetNodeLabel
  prov_maps_to: "prov:termFromMatrix"           # null if local-only
  note:         "One sentence description."
  supplement:   domain_ontology_supplement.cypher
  loader:       loader_file.cypher
  domain:       controlm | seal | catalog | ...
  status:       planned                         # set to active after Steps 7–8
```

Set `status: planned` now. Change to `active` after the supplement and loader
are written (Steps 7–8).

### Step 7 — Declare in the domain supplement

If the **target node type is new**, add a `LocalClass` block first:

```cypher
-- New node type
MERGE (n:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#YourNode"})
  SET n.label = "Your Node",
      n.notes = "Description.";

-- Wire to PROV-O class
MATCH (lc:OntologyTerm:LocalClass {iri: "https://drydocs.local/ontology#YourNode"})
MATCH (pc:OntologyTerm:ProvClass   {iri: "http://www.w3.org/ns/prov#Entity"})   -- or Activity/Agent/Collection
MERGE (lc)-[r:SUBCLASS_OF]->(pc)
  ON CREATE SET r.source = "drydocs.your_supplement";
```

Then add the `LocalRelationship` block:

```cypher
-- Relationship declaration
MERGE (n:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#yourRelationship"})
  SET n.label  = "YOUR_LABEL",
      n.domain = "SourceNode",
      n.range  = "TargetNode",
      n.notes  = "One sentence. Mention the prov mapping.";

-- Wire to PROV-O (omit this block if prov_maps_to is null)
MATCH (local:OntologyTerm:LocalRelationship {iri: "https://drydocs.local/ontology#yourRelationship"})
MATCH (prov:OntologyTerm:ProvProperty       {iri: "http://www.w3.org/ns/prov#usedOrWhatever"})
MERGE (local)-[:MAPS_TO]->(prov);
```

If a new node type is introduced, also add a `NODE KEY` constraint to
`drydocs_core/schema/constraints.cypher` (the consolidated constraints file —
the former `m3_constraints_upgrade.cypher` was absorbed into it):

```cypher
CREATE CONSTRAINT yournode_key IF NOT EXISTS
  FOR (n:YourNode)
  REQUIRE (n.your_id_field) IS NODE KEY;
```

If this is a **new domain** (not M3 / SEAL / Catalog), create a new supplement
file following the structure of an existing one, then add a new
`apply-<domain>-supplement` CLI command in `drydocs/cli.py` (see the
`apply-seal-supplement` command as the template).

### Step 8 — Implement and verify

Write the relationship in the loader cypher file:

```cypher
MERGE (src:SourceNode {id: row.source_id})
MERGE (tgt:TargetNode {id: row.target_id})
MERGE (src)-[r:YOUR_LABEL]->(tgt)              -- add {role: "..."} if needed
  ON CREATE SET r.first_seen_at = datetime($loaded_at),
                r.source        = $source_label,
                r.loader        = $loader
SET r.last_seen_at = datetime($loaded_at),
    r.last_run_id  = $run_id
```

Then:
1. Set `status: active` in the vocabulary YAML for your new entry.
2. Run `pytest tests/unit/test_schema.py` — the drift guard will confirm the
   label appears in the supplement.
3. Add a verify check in the relevant `*-verify` CLI command if the
   relationship has an integrity invariant (e.g., "every X must have at
   least one Y").

---

## Applying supplements to the database

Run this once per environment, after `drydocs bootstrap`:

```bash
drydocs apply-supplements          # base -> seal -> catalog -> registry
```

One verb applies the whole chain in the order declared by
`drydocs_core/schema/supplements.py`, then verifies each file landed — every
`:OntologyTerm` IRI the `.cypher` declares must be present in the graph
afterwards. Idempotent — safe to re-run after any supplement update. The
per-file verbs (`apply-ontology-supplement`, `apply-seal-supplement`,
`apply-catalog-supplement`, `apply-registry-supplement`) still work as aliases;
`--only NAME` is the equivalent on the chain verb.

The SOSA/SSN context-graph terms are **experimental and opt-in** — deliberately
not in the default chain; every term they seed carries
`adoption: "experimental"`. Add them with `drydocs apply-supplements --with-sosa`
(or the `apply-sosa-supplement` alias).

---

## Maintaining existing relationships

### `inverse_label` — display phrasing only (C15)

Every vocabulary entry carries `inverse_label`: the **target-side display
phrasing**, read as `<target> <inverse_label> <source>` (`SUPPORTS` →
Product *"supported by"* DevTeam). Consumers use it to phrase INCOMING edges
correctly when inspecting a node from the target side (the Backstage
`ownedBy`/`ownerOf` inverse-pair pattern).

**PRESENTATIONAL ONLY — recorded as such, 2026-07-28.** The field changes no
direction, relationship type, status, or semantics; storage stays exactly one
directed edge; adding or rewording an `inverse_label` is explicitly **not a
gate matter** (contrast every other semantic field in the entry, which is).
Presence is enforced by `test_schema.py::test_vocabulary_every_entry_has_inverse_label` —
a new entry without one fails CI. Consumption in the node inspector rides the
next Epic O inspector touch, not the vocabulary.

### Role rename

Change the `role` value on the edge everywhere it appears:

1. Update `role` in `relationship_vocabulary.yaml`.
2. Update `notes` in the supplement cypher.
3. Update `role` value in the loader cypher.
4. Run a one-time migration in Neo4j:
   ```cypher
   MATCH ()-[r:LABEL {role: "old_name"}]->()
   SET r.role = "new_name"
   ```

### Node reclassification

When a node type turns out to belong to a different PROV-O class:

1. Update `prov_maps_to` in the vocabulary entries that reference it.
2. Update `SUBCLASS_OF` in the supplement cypher.
3. Re-run `drydocs apply-<domain>-supplement` (idempotent — updates the `SET`
   properties; the old `SUBCLASS_OF` edge must be manually removed if it was
   wrong).
4. Update any loader cypher that sets secondary labels on that node
   (e.g., `:Entity`, `:Activity`).

### Deprecation (stop loading; keep data in graph)

1. Set `status: deprecated` and add `deprecated_at: YYYY-MM-DD` in the vocabulary.
2. Add a `// DEPRECATED YYYY-MM-DD` comment at the top of the
   `LocalRelationship` block in the supplement.
3. Remove the relationship from the `*-verify` CLI check (stop asserting it
   exists).
4. Leave the data in the graph — do not delete.

### Removal (data and code both deleted)

1. Set `status: removed` in the vocabulary (keep the entry for audit history).
2. Run a migration in Neo4j to detach-delete the edges:
   ```cypher
   MATCH ()-[r:YOUR_LABEL]->()
   DELETE r
   ```
3. Remove the `LocalRelationship` block from the supplement cypher.
4. Delete or archive the loader cypher file.
5. Remove the loader from `cli.py` registration.

---

## Running the tests

```bash
pytest tests/unit/test_schema.py -v
```

Four vocabulary tests run automatically (require PyYAML):

| Test | What it checks |
|---|---|
| `test_vocabulary_file_exists` | `relationship_vocabulary.yaml` is present |
| `test_vocabulary_active_entries_declared_in_supplements` | Every `active` entry's `neo4j_label` appears in its declared supplement file |
| `test_vocabulary_prov_matrix_complete` | All 9 matrix rows are present |
| `test_vocabulary_no_duplicate_ids` | No duplicate `id` values in `local_relationships` |

The drift guard (`test_vocabulary_active_entries_declared_in_supplements`) is
the critical one: it fails if you add a vocabulary entry and set it to
`active` without writing the matching supplement block.

---

## File map

```
drydocs_core/
  ontology/
    relationship_vocabulary/           ← registry fragments, per domain (edit this first)
    namespaces.py                      ← IRI prefix definitions
  schema/
    ontology.cypher                    ← PROV-O base terms (do not edit)
    ontology_supplement.cypher         ← Control-M local terms
    seal_ontology_supplement.cypher    ← SEAL local terms
    catalog_ontology_supplement.cypher ← Catalog local terms
    registry_ontology_supplement.cypher← software-registry terms
    sosa_experimental_supplement.cypher← SOSA/SSN (opt-in, experimental)
    constraints.cypher                 ← node key constraints (incl. M3)
drydocs/
  cli.py                               ← apply-<domain>-supplement commands
  loaders/
    cypher/                            ← one .cypher per loader
tests/
  unit/
    test_schema.py                     ← includes vocabulary drift guard
docs/
  RELATIONSHIP_GUIDE.md                ← this file
```
