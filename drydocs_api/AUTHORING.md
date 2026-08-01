# QuerySpec authoring conventions (O27)

**Scope.** How to write a row in the `QUERY_SPECS` registry
(`drydocs_api/query_specs.py`) and, by extension, any Cypher whose results reach
an external surface — a console frame, a deep link, an export file, or a
provenance manifest. Three rules, each with the reason it exists, because a rule
whose rationale is lost gets "simplified" away by the next author.

These codify what O11 already does. The audit in §4 found the registry
**already compliant** with all three; what was missing was the written rule and
a guard, so compliance was a coincidence of good authoring rather than a
property of the system.

---

## Rule 1 — Consume gate-confirmed edges. Never re-derive meaning from raw staged columns.

A spec reads relationships the loaders **materialized** and the HITL gate
**confirmed**. It does not reconstruct a relationship inline that the graph is
supposed to carry.

**Why.** Precedence resolution (`config/precedence.yaml`) and the ontology
rulings that give an edge its meaning live in the **loaders**, behind the gate
(CLAUDE.md §1, §4). A spec that re-derives a relationship from raw columns
forks that logic into the read path, where nothing gates it — so the console can
disagree with the graph, and the disagreement is invisible because both look
authoritative. This is Backstage's *consume the relation, not the spec field*
rule.

**The worked example is in this repo.** `explorer.jobs.v1` returned the job's
denormalized `folder_id`. The 2026-07-21 SME correction bumped it to **v2**,
which traverses `(:ControlMFolder)-[:CONTAINS_JOB]->(:ControlMJob)` and reads
the folder node's real name, plus the data center via `SCHEDULED_ON`. Same
question, but the answer now comes from the edges the loaders built.

### What this rule does NOT forbid

Three things look like violations and are not. Getting this boundary wrong
would push authors into worse Cypher, so it is stated explicitly:

1. **Joining on a declared node-key component.** `explorer.conditions.v2` does
   `OPTIONAL MATCH (f:ControlMFolder {folder_id: c.folder_id})`. That is legal:
   `constraints.cypher` declares `(c.folder_id, c.name)` as `Condition`'s NODE
   KEY, so `folder_id` **is** part of the condition's identity, not a
   denormalized copy of a relationship. The join resolves an identity to a
   display name; it does not invent a relationship.
   *Test for the difference:* if the graph declares an edge for this
   relationship and the spec sidesteps it with a property match, that is a
   violation. If no edge exists and the property is a declared key component,
   it is a key join.
2. **Deriving a presentation category from gated edges.**
   `explorer.controlm-app-codes.v1` classifies a code as `direct (dedicated
   code)` / `shared platform code` / `unmapped — SME queue` by counting
   distinct applications reached **over the gated
   `WAS_ASSOCIATED_WITH {role:'seal_app_ref'}` edges**. Deriving *from* gated
   edges is the rule working, not breaking. That spec also states in its own
   description that the authoritative code→application mapping is a gate-bound
   O13 domain and this view is not it — copy that habit.
3. **Reporting a property's presence or value.**
   `runbooks.metadata-completeness.v1` reads `j.description` to report whether
   runbook metadata exists. A property is a property; the rule is about
   relationships.

### Author checklist

- Is every relationship in my `MATCH` one a loader writes and a gate confirmed?
- If I am matching on a property to reach another node, is that property a
  declared key component in `drydocs_core/schema/constraints.cypher`?
- If I am computing a category, does it derive from gated edges, or am I
  inventing an ontology decision in a `CASE`? The second one goes to the gate
  (`docs/restructure/03-hitl-sme-flow.md`), not into a spec.

---

## Rule 2 — External refs use `kind:namespace/name`, with the namespace taken from the declared key.

Deep links, export manifests, and any other outward-facing identifier for a
graph node use:

```
kind:namespace/name        e.g.  hostgroup:P032-E0700-DMA/BATCH-GRP-A
kind:name                  e.g.  application:0000012345
```

- **`kind`** — the node kind, lower-case kebab (`job`, `folder`, `condition`,
  `application`, `server`, `hostgroup`).
- **`namespace`** — **the scope in which the name is declared unique**, omitted
  when the name is already globally unique.
- **`name`** — the business name, verbatim.

### The namespace is the declared uniqueness scope — and it is usually not the data center

O27 was groomed as *"namespace = data center where names collide across the 4
DCs."* Checked against `drydocs_core/schema/constraints.cypher`, that is true
for **exactly one** node kind. The generalisation that actually holds is
"namespace = the declared uniqueness scope", which yields the data center where
the key says so and something else where it does not:

| Kind | Declared constraint | Namespace |
|---|---|---|
| `ControlMHostGroup` | `(data_center, name)` NODE KEY | **data center** |
| `ControlMJob` | `(folder_id, job_id)` NODE KEY | **folder** |
| `Condition` | `(folder_id, name)` NODE KEY | **folder** |
| `ControlMFolder` | `folder_id` UNIQUE | none |
| `ControlMServer` | `name` UNIQUE | none |
| `BusinessApplication` | `seal_id` UNIQUE | none |

**Why phrase it this way.** Tying the namespace to the constraint file makes the
grammar self-maintaining: when a loader adds a node kind, its NODE KEY already
states the namespace, and no one has to remember a separate rule. Tying it to
"the data center" would have been wrong for jobs and conditions — the two kinds
most likely to appear in a deep link — and wrong in the direction that produces
*ambiguous* refs rather than ugly ones.
`tests/unit/test_query_specs.py::test_authoring_doc_namespace_table_matches_declared_keys`
holds this table to the constraint file.

**Why not element ids** — see Rule 3. **Why not bare names** — a bare job name
is ambiguous across folders, and an ambiguous ref in an export manifest cannot
be re-resolved later, which defeats the manifest's purpose.

---

## Rule 3 — Graph-internal element ids never cross an external surface.

`elementId(n)` and the deprecated `id(n)` MUST NOT appear in a spec's returned
columns, a URL, an export file, or a provenance manifest.

**Why.** They are Neo4j-internal pointers, **not stable identifiers**. They
change on restore-from-backup, on a re-load into a fresh database, and on the
store-format migrations an upgrade performs. A deep link built on one dies
silently at the next reload — it resolves to *a different node* rather than to
nothing, which is the worse failure. A manifest carrying one cannot be
re-resolved at all, which breaks the "you can re-run exactly what you exported"
guarantee `exports.py` exists to provide.

**`job_id` and `folder_id` are not element ids.** They are Control-M's own
identifiers, carried from the source and declared in `constraints.cypher`.
Returning them is correct and several specs do. The rule is about
*graph-internal* handles, not about ids in general.

**Enforced, not just documented.** `guard.ensure_no_element_ids` runs inside
`query_specs._validate_registry()` at import, so a registry spec that returns
one cannot ship — the same fail-at-import idiom as the versioning and read-only
checks. It lives in `guard.py` beside `ensure_read_only` because it is the same
kind of thing (Cypher refused at the door) and because that module's
`_code_regions` already strips comments and string literals, so `RETURN 'id('`
as *data* never false-positives — the ADR 0003 bind-renderer lesson, scan code
regions only. That stripping also lower-cases, which is what makes the check
case-insensitive: `ElementId(` and `ID(` are the same Cypher call.
The identical check runs at **ephemeral** spec registration
(`ephemeral_specs.py`), which is where the real exposure is: those Cypher
strings are written by an LLM at runtime and flow into the same export and
manifest paths. Guarding only the hand-authored registry would have put the
check on the path that carries no risk. `agents/graph_qa/pipeline.py` carries
the rule in the text2cypher prompt as well — the prompt prevents, the guard
catches.

---

## 4. Audit of the current registry (2026-08-01, O27)

All specs in `QUERY_SPECS` were read against the three rules.

| Rule | Result |
|---|---|
| 1 — gated edges | **No violations.** One item flagged below. |
| 2 — ref grammar | No external refs are emitted yet; the grammar is defined here for the deep-link and export-manifest work that will. |
| 3 — element ids | **No violations** — zero first-party uses of `elementId(`/`id(` anywhere in the repo. The new guards are therefore pure regression guards. |

**Flagged, not fixed — `explorer.conditions.v2`.** Its folder join is legal
under Rule 1 (`folder_id` is a declared key component, and no folder→condition
edge exists in the schema). But the reason it is a property join is that the
ontology has never gated a `CONTAINS_CONDITION`-style edge; conditions attach to
*jobs* via `REQUIRES_IN_CONDITION` / `EMITS_OUT_CONDITION`. **If such an edge is
ever gated, this spec should bump to v3 and traverse it** — the same correction
`explorer.jobs.v1 → v2` already made. Recorded here rather than acted on
because materialising a new edge is an ontology decision and goes through the
HITL gate, never into a read spec.
