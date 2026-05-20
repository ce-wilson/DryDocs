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

| Node label | PROV-O / W3C type | Supplement |
|---|---|---|
| `ControlMJob` | `prov:Activity` | `m3_ontology_supplement.cypher` |
| `JobFolder` | `prov:Collection` | `m3_ontology_supplement.cypher` |
| `ControlMServer` | local Platform | `m3_ontology_supplement.cypher` |
| `Condition` | `prov:Entity` | `m3_ontology_supplement.cypher` |
| `JobRun` | `prov:Activity` | *(base ontology)* |
| `Application` | `prov:SoftwareAgent` | `seal_ontology_supplement.cypher` |
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

## Creating a new relationship — 8-step checklist

Work top to bottom. Each step has exactly one file to touch.

### Step 1 — Check the vocabulary

Open [`drydocs/ontology/relationship_vocabulary.yaml`](../drydocs/ontology/relationship_vocabulary.yaml).
Search for your source node, target node, or intent. If an entry already
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

Add an entry to `local_relationships` in
`drydocs/ontology/relationship_vocabulary.yaml`:

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

If a new node type is introduced, also add a `NODE KEY` constraint to the
domain constraints file (e.g., `m3_constraints_upgrade.cypher`):

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

Run these once per environment, in order, after `drydocs bootstrap`:

```bash
drydocs apply-m3-supplement       # Control-M node types + relationships
drydocs apply-seal-supplement     # SEAL node types + relationships
drydocs apply-catalog-supplement  # Catalog node types + relationships
```

All commands are idempotent — safe to re-run after any supplement update.

---

## Maintaining existing relationships

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
drydocs/
  ontology/
    relationship_vocabulary.yaml      ← registry (edit this first)
    namespaces.py                     ← IRI prefix definitions
  schema/
    ontology.cypher                   ← PROV-O base terms (do not edit)
    m3_ontology_supplement.cypher     ← Control-M local terms
    seal_ontology_supplement.cypher   ← SEAL local terms
    catalog_ontology_supplement.cypher← Catalog local terms
    constraints.cypher                ← node key constraints
    m3_constraints_upgrade.cypher     ← M3-specific constraints
  loaders/
    cypher/                           ← one .cypher per loader
tests/
  unit/
    test_schema.py                    ← includes vocabulary drift guard
docs/
  RELATIONSHIP_GUIDE.md               ← this file
```
