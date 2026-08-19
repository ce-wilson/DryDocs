# ADR 0011 — Single-database contingency: the fold-down plan if multi-DB becomes unavailable

```yaml
status: EXECUTED-BY-CHOICE   # 2026-08-18, gate document-content-topology (G32) — see the amendment note below; was PLANNED
date: 2026-08-10
authored_by: G53 session (desktop, autonomous; SME-directed pull)
deciders: []              # execution requires an SME gate; nothing here is pre-approved
layer: cross-cutting
relates_to:
  - 0002-component-database-topology.md   # stays ACCEPTED; this does NOT re-open D1
  - drydocs_core/schema/provisioning/01_databases.cypher
  - config/dev-environment.yaml
trigger: >
  Neo4j Enterprise becoming genuinely unavailable (a company-side edition
  constraint or a cost ruling). NOT the 2026-08-01 laptop eval expiry — that is
  a local license matter, explicitly out of scope per the G53 groom note.
```

> **AMENDED 2026-08-18 — EXECUTED BY CHOICE, for a trigger this record does not
> contain (gate `document-content-topology` / G32, Q10).** The fold this ADR shelved
> was chosen deliberately, and the reason MUST be recorded here because it is not
> the one below: Enterprise did NOT become unavailable. The SME ruled the fold on
> RETRIEVAL grounds — an agent that cannot see captured context beside the
> structured graph in one vector search fails silently — and on the §F precedent
> that per-assertion `origin` governance already protects the graph's most governed
> edges inside one database. Scope differences from the shelf plan: `ddschema` does
> NOT fold (clause 2 never fires — the single largest cost avoided, taken
> deliberately); the three clause-1 guards are a HARD PRECONDITION of the apply
> (G102, guards first), not a follow-up; and clause 1's `:Uncertain` label lands at
> the single uncertain write boundary exactly as written here. A future reader
> asking "did Enterprise go away?" — no. This executed because the plan was good.

## What this is, and is not

ADR 0002 D1 chose Enterprise multi-database because the trust axis maps onto the
database boundary: *"multi-DB moves the guarantee from discipline to physics."*
It priced the Community single-DB option and REJECTED it ("commingles trust; one
bad query promotes noise"). **That decision stands.** This record writes down the
fold-down we would otherwise improvise under duress: how `drydocs` + `ddcontext`
+ `ddschema` (+ the `ddall` composite) collapse into ONE database if Community's
one-user-database limit ever binds, what mechanism replaces each lost guarantee,
and — stated plainly, per the item's own instruction — **which guarantee cannot
be replaced.**

## Clause 1 — How the trust boundary survives (and what is lost)

**Mechanism, three layers, all mandatory together:**

1. **Label namespace.** Every node written by `drydocs_deepdoc` (today →
   `ddcontext`) additionally carries `:Uncertain` — one label, applied at the
   writer (`drydocs_deepdoc/writer.py`, the sole uncertain write boundary), never
   optional. Ground-truth loaders never apply it. This is the `:Candidate`
   namespace of the rejected D1 alternative, renamed to say what it means.
2. **Trust property.** The writer already stamps `reliability`/`trust` on every
   node and edge; in the fold-down these become **mandatory at write time**
   backed by an existence constraint (`REQUIRE n.reliability IS NOT NULL` on
   `:Uncertain`). Note the trap: existence constraints are THEMSELVES
   Enterprise-only. On true Community, the constraint is replaced by a refusal
   guard in the writer (the S10 `PreCutoverApplicationGuard` pattern — refuse
   before any write) plus a scheduled audit query. Discipline, not physics;
   see "what is lost."
3. **Guard tests replacing the transaction domain.** Three new guards:
   (a) every ground-truth QuerySpec's Cypher must exclude `:Uncertain` —
   enforced structurally by generating a `WHERE NOT n:Uncertain` clause into
   the registry rather than trusting 30+ hand-written queries;
   (b) a writer-boundary test: no module outside `drydocs_deepdoc` may apply
   `:Uncertain`, and `drydocs_deepdoc` may not MERGE without it (the
   `test_module_boundary.py` pattern, aimed at labels);
   (c) a live audit spec (`ownership.*`-style QuerySpec) counting
   `:Uncertain` nodes reachable from ground-truth-only traversals — expected 0,
   any hit is a promotion that skipped the HITL gate.

**What is lost, plainly:** the guarantee that a bad write CANNOT cross. Today a
transaction literally cannot span databases; folded down, every protection above
is a check that must run and pass. ADR 0002's own words reverse: one DB moves the
guarantee **from physics back to discipline**. A bug that both applies the wrong
label set AND slips the writer guard corrupts ground truth silently until audit
(c) fires. That residual risk is irreducible in one database, and accepting it is
an SME decision at execution time — this plan does not accept it on anyone's
behalf.

## Clause 2 — ddschema's exemplar nodes vs drydocs' NODE KEYs

This is the hard one, and it is a **constraint conflict, not a naming
collision**: exemplar nodes carry REAL labels (`:ControlMJob` etc.) beside
`:SchemaMeta`, deliberately WITHOUT the key properties, and `drydocs`' NODE KEYs
(`constraints.cypher`) enforce existence+uniqueness on those labels. In one
database, the moment `constraints.cypher` applies, every exemplar violates it —
or blocks it from applying at all.

**Mechanism: exemplars lose their real labels in the fold-down.** The schema
meta-graph is re-rendered (`drydocs_core/ontology/schema_graph.py` owns the
render; `bootstrap-schema-graph` applies it) so an exemplar becomes
`:SchemaMeta:Exemplar {describes_label: "ControlMJob"}` — the described label
moves from the node's label set into a PROPERTY. NODE KEYs never see it; the
schema graph keeps its content. Costs, named: (a) label-polymorphic queries over
exemplars stop working — anything doing `MATCH (n:ControlMJob)` to pick up
exemplars must switch to `describes_label`; today's known consumer set is the
schema-graph renderer itself and the G51 verbs, both ours to update; (b) the
"labels as data" presentation risk ADR 0002's provisioning comment warns about
becomes the DESIGN rather than the hazard — acceptable only because clause 3
keeps schema rows out of estate queries by filter instead of by database.
The alternative (dropping the NODE KEYs) is REJECTED here in advance: the keys
are the load-correctness backbone (the T23 crash class exists precisely because
a key was missing its property), and weakening ground truth to host exemplars
inverts the priorities.

## Clause 3 — What replaces ddall (the consumer enumeration)

`ddall` stores nothing; it is read federation. In one database, federation is
free — everything is already together — and the WORK is preserving the
watermarking contract that `ddall` reads currently trigger. The full consumer
inventory (grepped 2026-08-10, desktop, producer tree @ `4bd6b29`):

| Consumer | Today | Fold-down change |
|---|---|---|
| `drydocs_api/query_specs.py` — `SPEC_DATABASES = {drydocs, ddcontext, ddall}`, `WATERMARKED_DATABASES = {ddcontext, ddall}` (lines 52/55) | DB name = trust signal | Both sets collapse to `{drydocs}`; the watermark trigger RE-KEYS from database to the `:Uncertain` label — a spec is watermarked iff its Cypher touches `:Uncertain` (declared per-row, reviewed, exactly as `ddall` rows are reviewed into `routing.py` today) |
| Two `database="ddcontext"` specs (`:AgentRun`, lines 833/871 — R1 gate ruling) | Physically isolated | `database="drydocs"` + mandatory `:Uncertain` on the write side; the R1 ruling's SUBSTANCE (":AgentRun lands never-in-ground-truth") survives as the label |
| `drydocs_api/exports.py` — `watermarked: s.database in ("ddcontext","ddall")` (line 297) | DB-keyed | Keys off the spec's watermark flag from the row above; the export banner text is unchanged |
| `drydocs_api/routing.py` — explicit-`ddall`-row review rule | Review gate on federation | Review gate survives verbatim, re-keyed: an explicit `:Uncertain`-touching row through review, never a default |
| `drydocs/cli.py` — `SCHEMA_GRAPH_DATABASE = "ddschema"` (198), graphrag `--database ddcontext` (1671), `DOC_SWEEP_DATABASES` (1984), `CANONICAL_LOAD_SEQUENCE` target DBs | Per-verb targets | All resolve through the `config/dev-environment.yaml` map (clause 4); no verb hardcodes a physical name today except via that map's keys — verified: the map is the single choke point |
| `drydocs_deepdoc/__init__.py` — `DATABASE = "ddcontext"` (35) | The uncertain write target | Points at the folded DB; `writer.py` gains the mandatory `:Uncertain` stamp (clause 1) |
| `drydocs_core/ontology/schema_graph.py` — targets `ddschema` (10/177) | Own DB | Re-render per clause 2; target = folded DB |
| `drydocs/docs_coverage.py` — `target_db ∈ {dddocs, ddcontext}` (74) | Doc corpora split | `dddocs` is PLANNED-not-provisioned today; the doc-registry guard's set collapses with the same label re-key |
| Web console | Reads via specs only | No direct change — inherits every re-key above (the O20 census: `/raw-cypher` is the only graph-touching surface, read-pinned) |

**The invariant across every row: the trust signal moves from WHERE a query runs
to WHAT a query matches.** Every mechanism is a re-key of an existing reviewed
surface, not a new surface.

## Clause 4 — The config change point

`config/dev-environment.yaml` `neo4j.databases` is already the single name map
(`ground_truth: drydocs`, `uncertain_context: ddcontext`, `composite: ddall`,
`schema_meta: ddschema`) — and the fold-down is expressible IN it: point all four
keys at one name. **One map serves both topologies; the fallback is a config
switch, not a code fork** — with two code-side preconditions, both cheap and both
worth doing regardless: (a) the two `database="ddcontext"` QuerySpec literals
(the only hardcoded physical names outside the map found in the sweep) resolve
through the map instead; (b) a topology guard test asserts either all-distinct
(0002 mode) or all-equal (0011 mode) — a HALF-folded map is the misconfiguration
neither ADR tolerates, and today's `test_database_names.py` enforces only the
distinct set. `01_databases.cypher` gains nothing: on Community its Enterprise
DDL simply refuses, which is the correct behavior — provisioning failure is the
fold-down's tripwire, not its obstacle.

## Execution sequence (if the trigger ever fires — SME-gated, not from this item)

1. SME gate on the residual-risk acceptance (clause 1's "what is lost").
2. Code preconditions 4(a)+4(b); clause 1 guards (a)–(c) land and PASS against
   the still-multi-DB estate (they are valid there too — cheap early).
3. Re-render the schema graph per clause 2; verify exemplar consumers.
4. Export `ddcontext` + `ddschema`, import into `drydocs` (with `:Uncertain` /
   label-to-property rewrites applied in the import, not after).
5. Flip the `dev-environment.yaml` map; run the topology guard, full suite,
   and clause 1(c)'s audit at count 0.
6. Retire `ddall` references last (they are read-only and fail loud, not silent).

The honest summary the groom note asked for: **consolidation costs the physics
of the trust boundary and buys it back only as discipline** — three guards, one
audit, and a residual window between a double-fault write and the audit that
catches it. Everything else — federation, watermarks, the schema graph, the
config seam — survives re-keyed. If the trigger fires, the expensive part is
already done: it was the thinking, and it is this page.
