# Review of the job-to-ETL binding second-pass options paper (2026-09-04)

- **Reviewed at:** commit `0cc996cf` on `main`, port base `port-base-20260902`; venue NewThinkpad. *Absent here reads as not-yet-ported, not as broken (docs/style/review-provenance.md).*
- **Subject:** `docs/reviews/job-etl-binding-second-pass-options-2026-09-04.md` (156 lines, stamped at `93f4d832`, venue desktop).
- **Scope:** what the paper is missing and what would improve it. Like its subject, this **decides nothing** — every clause here is gate material or an item's acceptance, never a build decision.
- **Method:** twelve of the paper's code citations were re-read against this tree. **All twelve held** — `resolver.py:30-31` (`..` unhandled), the absent per-token record, the absent `properties:` key in the vocabulary, `:ControlMJobRun` planned-in-three-built-in-none, `_stable_invocation_key`, G112 clause (d), `add_process` setdefault, `_stage_payload`'s mutate-and-move, `catalog.py`'s sparse-refresh coalesce, `shell.py`'s `dpl.pipeline_guid_literal`, `schema_graph.cypher:68-69`, ~240K jobs. The conclusion below is not that the paper is careless. It is careful; the gaps are in what it did not look at.

---

## 1. The four findings that change the recommendation

### R1 — "D at promotion" re-introduces the exact defect Option B was rejected for, and has no invalidation rule

The paper rejects Option B as storage in one sentence and applies it in another. §3-B: *"a label is **state**, and the board's own rule applies — roll-ups are derived, never stored."* §6-3: at promotion, *"Option D's properties, copied up"* — `strength` and `class` are written onto the confirmed `INVOKES` edge. That is a stored roll-up over the bindings, from a second writer, which is the same shape.

Worse, it is one-way. Nothing in the paper un-copies a grade. §5-Q6 asks *"which witnesses are older than the job's `version_timestamp`"* — a **query about the bindings**. Once the grade has been copied onto `INVOKES`, that query no longer covers it: the definition moves, the witness goes stale, the promoted `strength` on the edge stays exactly as confident as the day it was copied. F20's shelf life applies to the evidence and not to the conclusion drawn from it.

Two consistent resolutions; the paper should take one and say which:

- **The grade stays derived.** `INVOKES` gets nothing new. Every strength question is a traversal to the bindings, which is where the dates live. Option D shrinks to what it can carry honestly — a pointer (`binding_id`) rather than a grade — and the F12 request is met by the binding node it points at. Cheapest, and consistent with the paper's own §6-4.
- **The grade is stored and INVALIDATION is ruled.** Then the gate must add a clause: a promoted grade is void when the job's `version_timestamp` moves past the supporting binding's `last_observed_at`, and *something re-runs* — which means naming the writer, the cadence and the void state. That is a real mechanism and it is not in §8's mint list.

This is the sharpest problem in the paper because it is internal: the staged recommendation contradicts the reason given for the stage before it.

### R2 — promotion has no mechanism, three grains disagree, and the trust axes are already ruled

Option C's whole argument is *"the second class needs its own home, from which curation promotes."* Promotion does not exist:

- `drydocs_lineage/curation.py` is 21 lines. `curate()` raises `NotImplementedError`; `drydocs_lineage/__init__.py:38` says so — *"STILL A STUB: `curation.curate`."*
- `plan_curated(graph, confirmed: set[tuple[str, str, str]])` (`writer.py:402`) needs **rel triples**.
- `lineage-review`'s export (`review.py:384-386`) is `{doc, exported, notes: [{folder, note}]}` — **per-folder free text**, keyed by folder id. There is no producer for `confirmed` anywhere in the tree.

So the grain runs folder → rel → and Option C adds a third, per-binding. **LIN2 (b) hits this before this paper's Phase 4 does:** it says the confirmed set *"comes from the review surface's confirmations (lineage-review's JSON export), passed as `--confirmed <file>`"*, and today's export cannot produce it. That is a LIN2 acceptance problem this paper is well placed to name and does not.

And the trust modelling is already ruled, generally, by a signed gate. **G102 §F** (`config/gate-log.md:3503-3509`): *"TWO TRUST AXES, kept distinct and now load-bearing. `origin` = AUTHORITY (who asserted…), `:Uncertain` = CONFIDENCE (machine-derived, unverified…). Never conflated, never collapsed into one flag; **every guard/filter/surface states WHICH axis it reads**."* Q9 in the same record rules `origin` the general authority vocabulary, *"adopted per-surface as each is touched"* — and a new surface is exactly that.

The paper's property table reads both axes and declares neither. Mapping them out is most of the design:

| binding property | axis (G102 §F) |
|---|---|
| `class` (`definition` / `runtime`) | neither — source class, not trust |
| `strength`, `residue_class` | **confidence** — the `:Uncertain` axis |
| `witness_ref`, `capture_ref` | **authority** — the `origin` axis, whose vocabulary Q9 already declared |
| curation state (below) | neither — the HITL decision, not a trust reading |

Two things follow, both gate clauses the paper is missing. **(a) Does an unpromoted binding carry `:Uncertain`?** It is machine-derived and unverified, which is the label's definition; `writer.py:24-26` says *this* writer never stamps it because curated results are ground truth. A candidate surface inside `drydocs` is the first thing that is neither. **(b) `CurationStatus` is not the same mechanism and must not be collapsed into it** — the enum already exists (`curation.py:13-17`: `proposed` / `confirmed` / `rejected`, *"kept for audit, never written"*). Put it on the binding node with `curated_by` / `curated_at` and the confirmed set becomes **derivable**: `--confirmed` gets a real producer, promotion becomes idempotent and auditable, and a rejection is recorded rather than lost. That is the item §8 is missing, and it is worth more than either parser item.

### R3 — the house already has this pattern, registered, active, and reused three times

Option C is presented as a fresh application of the modeling skill's promote-to-node rule. The repo has been doing it since K4 (2026-07-15), under PROV's own name:

```
BusinessApplication -[:QUALIFIED_ATTRIBUTION]-> (:Attribution) -[:HAS_AGENT]-> Employee
                                                              -[:HAD_ROLE]-> TOMRole
```

`Attribution` in `10-node-classifications.yaml:325-333`: `class: "prov:Attribution"`, **`prov_type: n/a`**, note — *"reified n-ary node… not itself a PROV participant — prov:Attribution rdfs:subClassOf prov:Influence."* Reused by three families: `human_qualified_attribution`, `itsm_group_qualified_attribution`, `catalog_cabinet_qualified_attribution`. And `40-local-scheduler.yaml:592` already gestures at it for this very neighbourhood — *"the tighter PROV pattern would treat ControlMJob as a prov:Plan via qualified association."*

The direct analogue of Option C is **`prov:qualifiedUsage` → a `prov:Usage` node → `prov:entity`**, since `scheduler_invokes` maps to `prov:used`. The paper's *"the binding is a `prov:Entity` derived from a witnessing `prov:Activity`"* is a defensible model — a claim can be an Entity — but it **deviates from an established house pattern without saying it is deviating**, and it answers the registry's `prov_type` field wrongly by implication: the `Attribution` precedent shows a reified n-ary node takes `n/a`, not `Entity`. Either follow the pattern and inherit its precedent, its naming shape and its already-argued `prov_type`, or say in one line why a binding is unlike an attribution. The gate prompt is much stronger with the precedent cited than with a skill table.

### R4 — the qualified form forces a matrix-row question the tree has left single-valued and unguarded

Following R3 surfaces something real. `scheduler_invokes` (`40-local-scheduler.yaml:915-921`) is `ControlMJob → "Script | ETLProcess"`, `prov_maps_to: "prov:used"`, note *"Matrix row: Activity → Entity = USED."* That reading is right for `Script` (`prov_type: Entity`, `:89`) and **not** for `ETLProcess`, which is `prov_type: Activity` (`:117-119`). Activity → Activity's row is `prov:wasInformedBy` (`30-prov-matrix.yaml`), and the qualified forms diverge with it: `prov:qualifiedUsage`/`prov:Usage` for `used`, `prov:qualifiedCommunication`/`prov:Communication` for `wasInformedBy`.

The G55 §B2 widening recorded *"one edge meaning, two endpoint classes, the ENDPOINT RECORDED PER EDGE"* — which handles the endpoint but leaves `prov_maps_to` a single value covering two rows. Nothing catches it: `test_vocabulary_endpoints.py` guards that endpoints are registered labels, both directions, and **no test compares `prov_maps_to` against `prov_matrix`** at all.

This is pre-existing and not the paper's to fix. It is the paper's to *name*, because Option C cannot be registered without answering it and Option D can be applied without ever noticing — which is an argument **for** C, and a better one than the paper makes.

### R5 — the J-taxonomy is read off a first-match ladder, so J2 is undercounted and a second ladder already disagrees

§2's classes are *"read off the code's own verdict counters."* Those counters are a precedence partition, not a state census (`controlm_inventory.py:564-571`):

```python
if rcl.unresolved:          coverage.resolve_unresolved += 1
elif rcl.canonical_tokens:  coverage.resolve_residue += 1
elif rcl.substituted:       coverage.resolve_resolved += 1
else:                       coverage.resolve_nothing_to_substitute += 1
```

A job can be J2 **and** J3 **and** J4 at once; the ladder reports one. So a pset that arrives through a `%%VAR` *and* carries an `{ODATE}` token counts as `resolve_residue` and never as `resolve_resolved` — and `{ODATE}`-class residue is the normal state of a batch job. **J2, which the paper calls "the largest partial-known class", is systematically undercounted by exactly the population that has runtime residue**, and J4 absorbs any job that both failed a reference and substituted others. Anyone sizing the second pass off these counters sizes it wrong.

A second ladder already exists and answers differently. `drydocs/cmdline_staging.py:496-516` computes `resolved` / `residue` / `nothing_to_substitute`, folding an **unresolved reference into `residue`** — the opposite of the lineage ladder, which gives `unresolved` its own bucket and reserves `residue` for canonical tokens. Two components, one question, two vocabularies. If `strength` and `residue_class` become a gate-signed enumeration, the enum will mean two things on day one.

And the prerequisite is larger and cheaper than §2.1 states. `_resolve_shell` **returns `rcl.resolved` — a string** (`:572`). `substituted`, `unresolved`, `external_refs`, `canonical_tokens` and `variants` are consumed as counters and discarded. So the gap is not only "no per-token map": at the lineage call site there is no **per-job** record either.

One conclusion covers all three: **compute the verdict once, in `drydocs_core.orchestration.controlm.resolver`, as a typed classification of a `ResolvedCommandLine`**, and have both the staging store and the lineage extractor read it. Then `_resolve_shell` returns the `ResolvedCommandLine` (an internal signature change, no gate), `strength`/`residue_class` are computable without touching the resolver's substitution logic, and the enum has one meaning. The prior art for the persisted shape is `cmdline_staging`'s `resolution_quality` table — per-job source, substituted names with winning scope, unresolved residue, canonical tokens, plus `parse_quality.parsed_from`. Lift the shape; do **not** depend on the module, whose own docstring says it *"is DELETED the day a real detail table exists."* The `..` escape (J5) remains the one genuine core-parser change.

---

## 2. Mechanics an acceptance must name

- **R6 — every new label is guarded, and one is not.** `:InvocationBinding` needs a `10-node-classifications.yaml` entry or `test_vocabulary_endpoints.test_every_declared_edge_endpoint_is_a_registered_label` fails; `test_every_edge_the_schema_seeds_has_a_vocabulary_entry` means the supplement block lands in the same commit; `drydocs_core/schema/schema_graph.cypher` is generated and must be regenerated there too (deterministic-render rule); a `binding_id` uniqueness constraint belongs in `constraints.cypher` beside `controlmjob_key`. **But the gate check is per REL label only** — `writer.py:552` builds `needed = {VOCAB_IDS[t] for t in plan.rel_types}`. `HAS_BINDING`/`BINDS_TO` registered `planned` are correctly refused; nothing at all stops a MERGE of a `planned` **node** label. The planned/active discipline is enforced on the edges and silently not on the node the paper is proposing.
- **R7 — the single-writer rule.** `writer.py:1` — *"This is the ONLY module in the component that writes a database."* A binding writer either lives inside it or breaks that invariant. The paper says *"a loader that must MATCH both endpoints… the established derived-pass shape, so not new machinery"* without saying where it goes. Name the module in the item.
- **R8 — MM7 is `in_progress`, not a draft, and has no `wip/` branch.** `git branch -r --list "wip/*"` is empty, so its work is unpushed and invisible (the J31 case). §6-2 rewrites its acceptance twice: MM7 says *"sets PROPERTIES only… and creates no edge"*, and §6-2 has it staging a binding. Cleaner: the runtime-binding writer is a **new** item that consumes MM7's `OutputCoverage`, leaving MM7 shippable as claimed. On the `provenance_guid` conflict — it is **narrower than stated**. MM7 already records it as *"a run-scoped PAIR whose scope is those two jobs and which never keys an edge"*, which is most of F8's guardrail. What survives is the **name** (a property called `provenance_guid` on a node whose D7 envelope already means provenance — a homonym of exactly the class §4's third bullet warns about) and the **host**. Rename it `placement_handoff_id` and the conflict is a rename, not a re-scope.

## 3. Smaller corrections

- **R9 — `variants` already answers part of J6, definition-side.** `ResolvedCommandLine.variants` carries `(environment, resolved)` expansions for `_D/_Q/_P/_T` names (`resolver.py:261-301, 401`). J6 asks *"which prefix ran where, so the ~14 can be confirmed as 14"* and the paper says only a witness can answer. For venue prefixes that arrive through an environment-lettered variable, the definition side already enumerates them and throws them away at `_resolve_shell`. A free win before any sysout is read, and it shrinks the class the runtime pass has to cover.
- **R10 — the fan-in claim is wrong on its second half.** *"~750K nodes"* is consistent with ~240.6K jobs at 1–3 bindings. But *"the `:ETLProcess` fan-in is the same as `INVOKES` has today"* is not: `BINDS_TO` is **added beside** a retained `INVOKES`, at two classes, so in-degree at a shared node goes to roughly 3×. Q3 traverses from that side, and a pset shared across 56 job definitions is already the hot node. Not fatal — but say it, and consider a `(token, class)` composite index.
- **R11 — `class` is a homonym.** The registry uses `class:` for the OWL/RDFS CURIE on every node classification. A binding property named `class` holding `definition|runtime` collides with it in the one file a reader will have open. `evidence_class` or `binding_class`.
- **R12 — absence needs a counted reason.** §5-Q1 answers "no `definition` binding" as an anti-join against `:ControlMJob`, which is right, but the *reason* is lost — and G11's house rule is skipped-and-counted, never silently absent. The binding writer's coverage object should carry a per-reason `binding_absent` count, on `OutputCoverage`'s skip-reason shape.
- **R13 — citation nit.** §1 cites `model.py:29-30` for *"nothing reaches it uncurated (the package invariant)."* Those two lines say the complement — *"Everything in a `LineageGraph` is a CANDIDATE until curation confirms it… working memory, not ground truth."* The invariant being invoked is `writer.py:20-22`'s curated-only refusal. The claim is right; the pointer sends a reader to the opposite half of it.

## 4. What this changes in §8

The four-items-and-a-gate list holds, with two additions and one re-scope: **the curation/promotion item (R2)** — the binding's curation state, a per-binding decision export, and `--confirmed`'s real producer — which is the load-bearing one; **the shared verdict classification in core (R5)**, which absorbs the per-token parser item rather than sitting beside it; and the runtime writer re-scoped to a new item over MM7's coverage (R8). The gate prompt gains: the axis map and the `:Uncertain` question (R2), the promotion-invalidation clause or the derived-grade ruling (R1), the qualified-pattern precedent and its `prov_type` (R3), and the `prov_maps_to` row question (R4) — which is a vocabulary-owner decision either way and now has a surface that forces it.
