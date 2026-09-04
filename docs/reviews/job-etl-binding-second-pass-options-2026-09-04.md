# The job-to-ETL binding: what the definition cannot tell us, and options for a runtime second pass (2026-09-04)

- **Reviewed at:** commit `93f4d832` on `main`, port base `port-base-20260902`; venue desktop. *Absent here reads as not-yet-ported, not as broken (docs/style/review-provenance.md).*
- **Direction (user, 2026-09-04):** review the folder and job unknowns and partial-knowns in the hop-1 mapping (Control-M job to DPL pipeline id or Ab Initio pset); plan options for a **second class of properties** added to the job or folder nodes **after runtime**, for the values that are difficult to determine from the definition SQL; use Neo4j modeling best practice.
- **Evidence:** the code as cited below; the live graph on this desktop (`neo4jtest`, database `drydocs`: 17 `:ControlMJob`, 8 `:ControlMFolder` from the bundled samples, no `:ETLProcess` yet — LIN2 is unbuilt); the machine-local capture session `2026-09-03-pex-research` (SYNTHESIS Part 2, mechanism-only findings F1–F20, cited by number — the images are never cited); the `neo4j-modeling` skill's decision tables (marked `[official]` / `[field]` as that skill marks them). Companion to the lineage-chain workplan (`docs/reviews/lineage-chain-extract-load-workplan-2026-09-03.md`); this paper is Phase 4 of that plan, thought through before it is minted.
- **Review chain (docs/reviews/README.md):** SUBJECT `0cc996cf` → REVIEW `0015fcfa` + `1b615dc7` (`job-etl-binding-second-pass-review-2026-09-04.md`, laptop, twelve citations re-read, all held) → this APPLY. Every change below is marked with the `R<n>` it closes; §9 is the ledger.
- **Decides nothing.** Every new label, relationship type or edge property here is an ontology change and goes through the relationship-vocabulary registry as `status: planned` and the HITL gate. The recommendation at the end is what the gate prompt should propose.

---

## 1. Two epistemic classes, and why the graph must keep them apart

The hop-1 binding — *which ETL workload does this job launch* — can be established two ways, and they are different claims:

| Class | Source | What it proves | What it cannot prove |
|---|---|---|---|
| **Definition** | `CM_DEF_VJOB.CMD_LINE` + `CM_DEF_SETVAR` (the variables pool), resolved by `drydocs_core.orchestration.controlm.resolver` | What the job is *configured* to launch, at the capture date, for the current version | That it ever ran; what a per-run variable resolved to; that the resolver's reading of the vendor syntax matched the agent's |
| **Runtime** | Output-tab sysout / shell trace echo per `<job, order id, run>` (MM7's subject); the launcher banner JSON | What was *actually submitted*, byte for byte, on a dated run (F11's positive control: a resolved command matched its echo character for character, doubled slash included) | That the definition still says so today (F20: a witness has a shelf life); anything about data movement — the sysout proves submission, not rows (F12) |

Today the graph holds only the first class, and it holds it on one surface: the curated `INVOKES` edge from `:ControlMJob` to `:ETLProcess {token}` (`drydocs_lineage/writer.py:233-235`), keyed by the env-stable token `_stable_invocation_key` computes (`drydocs_lineage/extractors/controlm_inventory.py:281-298`: DPL → the pipeline GUID; Ab Initio → the pset basename). That edge is the **confirmed** surface — nothing reaches it uncurated (the package invariant — `writer.py:20-22`'s curated-only refusal; `model.py:29-30` states the complement, that everything in a `LineageGraph` is a candidate) (R13). A runtime observation is a *candidate* by construction (it may disagree with the definition, it may be stale, it may be n=1), so it cannot be written to that edge without breaking the invariant. That is the whole design constraint for the second pass: **the second class needs its own home, from which curation can promote.**

## 2. The unknowns and partial-knowns, by class

What follows is the taxonomy of a job's hop-1 state after the definition pass, read off the code's own verdict counters and the research's residue classes (F9, F10, F11, F12). It is the queue the second pass exists to work.

### 2.1 Job-level

| # | State | How the code reaches it | Research grade | What only runtime can add |
|---|---|---|---|---|
| J1 | **Resolved, literal** — the DPL pipeline GUID is written literally in CMD_LINE | `shell.py:389-393` forces `UNKNOWN`→`DPL` on `pipeline_guid(args)` (rule `dpl.pipeline_guid_literal`, G15 c); token = GUID | **strong** (F9: in the census, the one literal among all-variable flags, 34/34) | Corroboration only. Plus the run-scoped facts the definition never has: image digest, compute target, launcher kind, run date (MM7's list) |
| J2 | **Resolved through a variable** — the pset (or jar) path arrives via `%%VAR` and resolves | `_resolve_shell` verdict `resolve_resolved` (`controlm_inventory.py:558-572`); **but** invocation identity is parsed from the VERBATIM command (G112 clause d, `:439-450`), so the `:ETLProcess` token may be the unresolved template, not the pset basename | **medium** (F9: only as reliable as the variable pool is read) | The pset **as executed** — the value the agent actually substituted. This is the largest partial-known class and re-keying it on resolved text is gate-bound (`cmdline-lineage-review`, 2026-07-16); a runtime class records the executed name **beside** the ruled identity without moving the ruling |
| J3 | **Residue** — per-run tokens (`{ODATE}` class) remain | verdict `resolve_residue`; canonical tokens in `ResolvedCommandLine.canonical_tokens` (`resolver.py:359-378`) | not a defect (F11: "per-run values cannot exist at definition time") | Nothing durable. The per-run value is **ephemeral** (F8) and must not become a job property at all — see §4 |
| J4 | **Unresolved** — a real miss: a misspelled or absent variable, or a cross-job reference the pool cannot follow | verdict `resolve_unresolved`; `ResolvedCommandLine.unresolved` / `external_refs` | **broken** on the definition side | The only witness there is. The echo shows either the substituted value (the pool was incomplete in the *extract*, not the estate) or the literal `%%NAME` unexpanded (a real defect, now proven rather than inferred) |
| J5 | **Looks resolved, is wrong** — a terminator or escape period survived into the value | the resolver consumes the single delimiter dot (`resolver.py:141-151`) but states at `:30-31` that the `..` literal-period escape is **not handled** — "this shop smuggles dots via values, not `..`" | F10 measured 2 `..` escapes and 46 terminator dots across 18 of 56 job definitions in one application, so that assumption is now contradicted by evidence | The executed filename, which is the only way to know which spelling exists on disk (F10: "the artifact names as printed do not exist on disk") |
| J6 | **Pset identity split by venue or case** — 34 distinct pset strings that are ~14 psets | basename keying (`_stable_invocation_key`) removes the venue prefix; **case variance and phantom dots are not normalized** | F12 hop grade untested past trust; C21 in the source log | A witness per venue: which prefix ran where, so the ~14 can be confirmed as 14. **Part of this is already answered definition-side (R9):** `ResolvedCommandLine.variants` enumerates the `_D/_Q/_P/_T` expansions of an environment-lettered name (`resolver.py:261-301`) and `_resolve_shell` discards them; for prefixes that arrive that way the definition pass can record every venue's spelling before any sysout is read, and the runtime class covers only what is left |
| J7 | **No invocation recognized** — nothing classified, or no target | `commands_unparsed`, `invocations_no_target`, `classify_executable`→`UNKNOWN` against `config/launcher-registry.yaml` | unknown kind | The launcher banner names the kind (`launcher_kind` in MM7). Note F12's caution against encoding the kind rule from correlation alone |
| J8 | **Artifact variable unresolved** — `%%JAR_PATH`-class values are refused as node names | `_is_resolved_literal` (`controlm_inventory.py:269-278`), counted in `artifact_values_unresolved` | — | The resolved artifact URI, as a witnessed string, not as a node |

**The counters above are a first-match ladder, not a state census (R5).** `controlm_inventory.py:564-571` tests `unresolved`, then `canonical_tokens`, then `substituted`, and reports one bucket per job. A job can be J2 and J3 and J4 at once; a pset that arrives through a `%%VAR` *and* carries an `{ODATE}` token counts as `resolve_residue` and never as `resolve_resolved`, and residue is the normal state of a batch job — so J2 is undercounted by the population that has runtime residue, and J4 absorbs every job that failed one reference and substituted others. A second ladder in `drydocs/cmdline_staging.py:496-516` answers the same question differently (an unresolved reference folds into `residue` there; here it has its own bucket). Sizing the second pass off either counter sizes it wrong; the sizes in this paper are floors for J3/J4 and an undercount for J2 until the verdict record below exists.

Two things the definition side lacks that the second pass needs *from the first pass*:

- **A per-job, per-token verdict record — computed once, in core (R5).** F9's grade (a literal outranks a resolved variable) needs to know, per token, whether it was substituted; `ResolvedCommandLine.substituted` records *which names* bound and in which scope, with no per-token map. And the gap is larger than the token map: `_resolve_shell` returns `rcl.resolved` — a string (`:572`) — so `substituted`, `unresolved`, `external_refs`, `canonical_tokens` and `variants` are consumed as counters and discarded, and there is no per-*job* record at the lineage call site either. One change covers both ladders and both gaps: a typed classification of a `ResolvedCommandLine` in `drydocs_core.orchestration.controlm.resolver` (a `ResolutionVerdict` with the per-token map, the residue class and the strength grade), returned by `_resolve_shell` in place of the string, and read by both the staging store and the lineage extractor. Then `strength` and `residue_class` are computable without touching the substitution logic, the enumeration means one thing in both components, and the two ladders collapse into one. Prior art for the persisted shape is `cmdline_staging`'s `resolution_quality` table — lift the shape, never depend on the module (its docstring says it is deleted the day a real detail table exists).
- **In-place enrichment.** `LineageGraph.add_process` is `setdefault` (`model.py:145`) — a second pass cannot enrich a node by re-adding it. The working precedent is `_stage_payload` (`controlm_inventory.py:702-744`), which mutates `into.processes[id].properties` and *moves* an edge rather than duplicating it.

### 2.2 Folder-level

The folder is the weaker subject for a runtime second pass, and the research says why:

| # | State | Finding | Consequence |
|---|---|---|---|
| F-a | **Run attribution to the ordering folder is not in the output** | F7: two runs of one job ordered by two folders differed only per-run; no folder token reaches the sysout; at a *later* step the folder IS recoverable from the job name | Attribution capability is **per step, inconsistent**. The second pass records `run_attribution: not_derivable` on the step where it is not, and never names an observed clock bucket a "cycle" |
| F-b | **Cadence is derivable from the job name in one application and not another** | F5/C7: 56/56 name-character-to-folder-suffix agreement in one app; not derivable in the other — "an application-level convention, not an estate rule" | A definition-side derived property, `cadence_char`, carrying `convention_scope: <application>`; never generalized to a folder rule |
| F-c | **The folder's data-center default time** | already modeled (DC name encodes the default run time) | Nothing runtime adds |

So the folder second pass is mostly **refusals and definition-side derivations**; the runtime class attaches to the job (and, when it exists, to the run). The paper's options below are job-centric for that reason.

## 3. Options for the second class

The `neo4j-modeling` skill's decision table `[official]`: a scalar always returned with its parent and never filtered alone is a **property**; a low-cardinality category used for filtering or traversal is a **label**; a connection with its own properties, multiple sources, or that is itself the subject of a query is an **intermediate node**. The use-case queries in §5 decide which applies here.

### Option A — namespaced runtime properties on `:ControlMJob`

`rt_pipeline_id`, `rt_pset`, `rt_launcher_kind`, `rt_observed_at`, `rt_witness_ref`, `rt_resolved_command` set on the existing node by a derived pass (the `runs_on_resolution` / `folder_attribution` shape: MATCH, never MERGE, unmatched counted). Sparse refresh coalesces so a partial witness never blanks a value (`catalog.py:115-118` precedent).

- **For:** the smallest change; no new label or type; the queue query is `WHERE j.rt_pset IS NULL`.
- **Against:** one value per job, so a definition/runtime **disagreement has nowhere to live** — the very fact the second pass is most valuable for; the D7 envelope on the node (`source`, `last_run_id`, `row_checksum`) describes the *definition pull*, and a runtime value under the same envelope inherits a provenance it does not have; per-fact `_observed_at`/`_source` twins bloat the node (30+ properties already); and it invites the F8 error — an ephemeral id that "looks like a lineage key" landing next to a durable one on the same node. Verdict `[field]`: acceptable for one or two scalars, wrong as the home for a class.

### Option B — resolution-state labels on `:ControlMJob`

`:EtlBound` / `:EtlPartial` / `:EtlUnbound` and `:RuntimeWitnessed`, recomputed by whichever pass ran last. Low-cardinality categorical used as a traversal filter → label `[official]`.

- **For:** the unknowns queue becomes `MATCH (j:ControlMJob:EtlUnbound)`; cheap; index-friendly.
- **Against:** a label is **state**, and the board's own rule applies — roll-ups are derived, never stored. Two passes writing one state label on one node is the collision shape this repo has already paid for. Labels alone carry no evidence (which witness, when, how strong). Verdict: **derive at query time from whatever holds the evidence**; store a label only if a measured query cost demands it, and then from one writer.

### Option C — an intermediate binding node

```
(j:ControlMJob)-[:HAS_BINDING]->(b:InvocationBinding)-[:BINDS_TO]->(e:ETLProcess)
```

One `:InvocationBinding` per **(job, binding class, token)** — so a job typically has one or two, never one per run. **This is the house `prov:qualifiedAttribution` pattern under a new name (R3):** `:Attribution` (`10-node-classifications.yaml:325-333`, `class: prov:Attribution`, **`prov_type: n/a`**, "reified n-ary node, not itself a PROV participant") has been active since K4 and is reused by three families; `40-local-scheduler.yaml:592` already points at the qualified form for this neighborhood. The binding follows that precedent — a reified n-ary node, `prov_type: n/a` — and inherits its already-argued registry shape; the earlier reading of the binding as a `prov:Entity` is withdrawn. Its PROV class is the R4 question below.

| property | meaning |
|---|---|
| `binding_id` | `<folder_id>.<job_id>|<binding_class>|<token>` — the MERGE key, with a uniqueness constraint (skill default 4) |
| `binding_class` | `definition` \| `runtime` — not `class`, which is the OWL/RDFS CURIE field on every node classification in the same registry (R11). Neither trust axis: a source class |
| `strength` | `literal` \| `variable` \| `runtime_echo` \| `unresolved` (F9's ranking, F12's grade) |
| `kind`, `token` | as `_stable_invocation_key` would compute from the value this class saw |
| `executed_value` | the pset path / GUID *as seen by this class* (venue prefix intact — J6's evidence) |
| `resolved_command` | the normalized command (F11's two normalizations applied) |
| `residue_class` | `none` \| `runtime_only` \| `cross_job_ref` \| `unresolved` (F11: classify, do not count) |
| `first_observed_at`, `last_observed_at`, `observations` | witness dedupe: one node per distinct executed value, dated (F20's shelf life) |
| `witness_ref` | the sysout file / order id that supports it — a reference, never a key (F8) |
| `capture_ref` | for the definition class: the extract's `capture_date` and version |
| `curation_status`, `curated_by`, `curated_at` | `proposed` \| `confirmed` \| `rejected` — `CurationStatus` (`curation.py:13-17`) placed on the binding, so the confirmed set is **derivable** and a rejection is recorded, not lost (R2). The HITL decision, not a trust reading |

**The two trust axes, mapped (R2).** G102 §F (`config/gate-log.md:3503-3509`) rules that `origin` = authority and `:Uncertain` = confidence, kept distinct, and that every surface states which axis it reads. This surface reads both:

| binding property | axis |
|---|---|
| `binding_class` | neither — the source class |
| `strength`, `residue_class` | **confidence** — the `:Uncertain` axis |
| `witness_ref`, `capture_ref` | **authority** — the `origin` axis, whose vocabulary Q9 of the same record declared general and adopted per surface as each is touched; this is a new surface |
| `curation_status` and its twins | neither — the HITL decision |

Which raises the clause the gate must take: an unpromoted binding is machine-derived and unverified — the definition of `:Uncertain` — and `writer.py:24-26` says the lineage writer never stamps that label because curated results are ground truth. A candidate surface inside `drydocs` is the first thing that is neither, so the prompt asks whether a `proposed` binding carries `:Uncertain` (and `confirmed` sheds it), or whether `curation_status` alone carries the confidence reading. `CurationStatus` and `:Uncertain` are different mechanisms and are not collapsed into one.

- **For `[official]`:** the connection has >2 properties, has **multiple sources for one (job, target) pair**, and is the subject of its own queries (Q2, Q5, Q6 below) — all three of the skill's promote-to-intermediate-node conditions, and the house precedent above. The two classes coexist on separate nodes, so a disagreement is a *query*, not a lost write. `INVOKES` stays exactly as ruled and curated: a `runtime` binding is a candidate that curation promotes by confirming the token; the gate ruling on env-stable identity is untouched. Cardinality is bounded: 1–3 per job, ~750K nodes at estate scale — not a supernode risk on the job side. **On the workload side it is not free (R10):** `BINDS_TO` is added beside a retained `INVOKES`, at two classes, so in-degree at a shared `:ETLProcess` rises to roughly three times today's; Q3 traverses from that side, and a pset shared across 56 definitions is already the hot node. Not fatal; a `(token, binding_class)` composite index is the mitigation to plan.
- **Against:** a new label and two new relationship types — an ontology change, gate-bound, `planned` first; one more hop in the traversal from job to workload (mitigated: `INVOKES` remains the confirmed shortcut); a loader that must MATCH both endpoints and count unmatched (the established derived-pass shape) — and it lives **inside `drydocs_lineage/writer.py`**, the component's only database-writing module (`writer.py:1`), never beside it (R7).

### Option D — provenance properties on `INVOKES` (F12's literal proposal)

`class`, `strength`, `witness_ref`, `observed_at` on the existing edge; a runtime disagreement becomes a second `INVOKES` to a different `:ETLProcess`.

- **For:** F12 asks for exactly this — a grade and a definition-or-runtime flag *as edge properties, not a new type*; the smallest vocabulary change.
- **Against:** it writes an **unconfirmed** runtime candidate onto the **confirmed** surface, which is the invariant §1 says the second pass must not break; run-scoped facts (image digest, compute target) are not facts about the job→workload connection; and `40-local-scheduler.yaml` has **no machine-readable `properties:` key on any entry** — edge properties exist only as prose in `note:` blocks — so an edge-property contract has no registry home yet. Verdict (revised, R1): **the grade stays derived; `INVOKES` gets nothing new.** The first draft had curation copy `strength` and `class` up onto the confirmed edge at promotion — which is a stored roll-up written by a second writer, the exact shape Option B was rejected for, and one-way: once copied, the grade stays as confident as the day it was copied while the job's `version_timestamp` moves past the witness that supported it, and Q6 (which asks the bindings) no longer covers it. So every strength question is a traversal to the binding, where the dates live, and Option D shrinks to what it can carry honestly — at most a `binding_id` pointer, and even that only once the registry has a `properties:` key for it to be declared in. The alternative — store the grade and rule invalidation (void when `version_timestamp` passes `last_observed_at`, with a named writer and cadence) — is a real mechanism that nobody has asked for; the gate records the derived-grade ruling so it is not re-litigated per surface. F12's request for a graded edge is met by the binding the edge would point at.

### Option E — the run as a node: `:ControlMJobRun`

Already in the vocabulary as `planned` (`scheduler_instance_of`, `scheduler_executed_by`, `40-local-scheduler.yaml:608,653`), in the schema graph (`schema_graph.cypher:68-69`), and in a SOSA gate prompt (`config/gate-prompts/sosa-jobrun-observation.yaml`, `CM_HIST_VW`). One node per execution carrying the witnessed facts; the job's runtime view is a roll-up over its runs.

- **For:** the most faithful — a witness *is* an event; every ephemeral id (F8) has a correct home and never touches the definition node; F7's per-step attribution and F20's dating fall out naturally; nothing new to rule, only two planned entries to activate.
- **Against:** cardinality — ~240K jobs × daily runs is millions of nodes a quarter, and the runtime witness today is a *sample* of sysouts, not a history feed; MM7's own acceptance is "sets properties only, creates no edge" precisely because no run node exists. A per-run node is the right **eventual** shape for run history (the `CM_HIST_VW` gate); it is not the right first home for hop-1 bindings.

## 4. What must never be a job property, whatever the option

- Per-run values from residue (J3): business date, order id, process id, executing host — the launcher host is a pool, not an attribute of the step. **The platform's run-minted correlation token belongs in this bullet (R8b):** it is order-id class — unique per run — and F8's "three values for one dataset in nine days" is three runs, the token working as designed, not instability. Its subject is a **dataset's zone transition** (S3 landing to Glue table), not the job-to-ETLProcess binding, so it is out of this paper's gate entirely. It is already ruled: SME 2026-08-21 (`8adfa688`), "a correlation token, not provenance in the PROV-O sense; never keys an edge, identifies a flow, or stands as evidence that a lineage path is real", with the rename to `placement_handoff` landed in `deepdoc-data-flow-overview.md` and the `data-flow-overview` gate prompt; only a field name in MM7's acceptance prose lags. What remains open is where the token *lives*, and that is G136's finding: signed identity is the GUID alone with `zone` as a property (G22 §G f), so the two placements of one dataset are one node, the transition is a self-loop, and a run-scoped id qualifying a self-loop has no edge to sit on and would be overwritten on a node every run. Owner: the drafted `dpl-dataset-identity-zone` gate (G136), pointed at here the way §6 points `:ControlMJobRun` at its gate, so the deferral is recorded rather than lost.
- Anything named for the event it *resembles* rather than the event it records (F6, F7): the observed clock bucket is not a `cycle`; the archive stamp is a job **start**, not a move.

## 5. The queries the model must answer (skill default 1: use cases before design)

| # | Question | A | B | C | D | E |
|---|---|---|---|---|---|---|
| Q1 | Which jobs have **no** ETL identity from the definition? (the queue) | prop null | label | no `definition` binding, or `strength = unresolved` — and the *reason* is counted per job at write time, `binding_absent` by reason on the writer's coverage, on `OutputCoverage`'s skip-reason shape, because G11's rule is skipped-and-counted, never silently absent (R12) | no edge | — |
| Q2 | Which jobs' definition token **disagrees** with the runtime-witnessed token? | cannot — one slot | cannot | two bindings, different `token` | two `INVOKES` (but on the confirmed surface) | roll-up over runs |
| Q3 | For pipeline GUID X, which jobs invoke it — by definition, by runtime, by both? | partial | — | `BINDS_TO` grouped by `binding_class` | edge `class` (D as first drafted) | run join |
| Q4 | Which psets run under more than one venue prefix? (J6) | — | — | `executed_value` distinct per `token` | — | per run |
| Q5 | Which **unresolved** jobs have a runtime witness newer than N days — i.e., now resolvable? | no date per fact | — | `runtime` binding with `last_observed_at` | — | yes |
| Q6 | Which witnesses are **older** than the job's `version_timestamp`? (F20 — stale evidence) | partial | — | compare binding date to job version | — | yes |
| Q7 | Runbook: for job J, the artifact the **next** step actually consumes (F18) | — | — | `executed_value` of the downstream binding | — | yes |

Option C answers all seven without a run-history feed; E answers them once one exists; A and B answer only Q1.

## 6. Recommendation, staged

**C now, the grade derived, E when run history is a feed.** (The first draft said "D at promotion"; R1 withdrew it.) Concretely:

1. **The verdict, once, in core (R5).** `ResolutionVerdict` in `drydocs_core.orchestration.controlm.resolver`: the per-token literal-vs-variable map, the residue class and the strength grade, computed from a `ResolvedCommandLine`; `_resolve_shell` returns the `ResolvedCommandLine` instead of a string (an internal signature change, no gate) and `cmdline_staging` reads the same classification. This absorbs the per-token parser item the first draft listed beside it. The **`..` escape** (J5) is the one genuine change to the substitution logic and rides with it.
2. **Definition class (LIN2's neighborhood).** The definition pass writes a `definition` binding per job alongside `INVOKES`, `strength` from the verdict, `curation_status: proposed`; the `variants` expansions are recorded as the venue spellings the definition already knows (R9); a job with no binding is counted by reason (R12). The writer lives in `writer.py` (R7).
3. **Runtime class — a NEW item over MM7's coverage, not a rewrite of MM7 (R8).** MM7 is `in_progress` and its acceptance says "sets properties only, creates no edge"; it stays shippable as claimed. The runtime-binding writer is a separate item that consumes MM7's `OutputCoverage` — the executed command, GUID, launcher kind and digest per `<job, order id, run>` — and stages a `runtime` binding deduped on `(job, executed_value)` with first/last observed and a count, joined to the job by the identity MM7 parses from the sysout filename and to `:ETLProcess` by the token the executed value yields. The run-minted correlation token is not on the binding (R8b).
4. **Curation is a mechanism, and today it is not one (R2).** `curate()` raises `NotImplementedError` (`curation.py:21`); `plan_curated` wants rel triples (`writer.py:402`); `lineage-review`'s export is per-folder free text (`review.py:384-386`). Three grains, no producer for `confirmed` — and **LIN2 (b) hits this first**, because its acceptance says the confirmed set comes from that export, which cannot produce it. With `curation_status` on the binding, the confirmed set is a query, the review page's decisions land per binding, promotion is idempotent and auditable, and `--confirmed` gets a real producer. A `runtime` binding whose token matches the `definition` binding is corroboration; a mismatch is a review row; a `runtime` binding with no definition counterpart (J4, J7) is the case the pass exists for and reaches `INVOKES` only by confirmation. `INVOKES` gains no grade (R1).
5. **The queue is derived, not stored (Option B rejected as storage).** `drydocs lineage-load` prints the counts per §2.1 state from the bindings; a label is added only if a measured query needs it, from one writer.
6. **Folders get definition-side derivations and per-step refusals only** (§2.2): `cadence_char` with `convention_scope`; `run_attribution: not_derivable` recorded on the step, never inferred.

**Gate scope (one prompt, `lineage-binding-class`):** (a) the `:InvocationBinding` label and `HAS_BINDING` / `BINDS_TO` types, registered `planned`, with the house qualified-pattern precedent cited and `prov_type: n/a` (R3); (b) the binding's PROV class, which the qualified form forces into the open (R4): `scheduler_invokes` maps to `prov:used` for both endpoint classes, and that is the Activity→Entity row for `:Script` (`prov_type: Entity`) but not for `:ETLProcess` (`prov_type: Activity`, `10-node-classifications.yaml:117-119`), whose row is `prov:wasInformedBy`; the qualified forms diverge with the rows (`prov:Usage` against `prov:Communication`), and `prov:Influence` is the superclass of both — so the prompt proposes `class: prov:Influence` for the binding with the subclass recorded per endpoint, or asks the vocabulary owner to split the entry. Pre-existing, single-valued and unguarded: no test compares `prov_maps_to` against `30-prov-matrix.yaml` (`test_vocabulary_endpoints.py` guards endpoints only), which is an item for the vocabulary owner either way, and an argument for Option C that the first draft did not make — Option D could be applied without anyone noticing the row; (c) the `strength` and `residue_class` enumerations, defined by the core verdict so they mean one thing in both components (R5); (d) the rule that `INVOKES` stays the confirmed surface, a binding is the candidate surface, and **the grade on `INVOKES` stays derived** (R1); (e) the trust-axis map and whether a `proposed` binding carries `:Uncertain` (R2); (f) `curation_status` on the binding as the promotion mechanism and the producer of `--confirmed` (R2); (g) the F8 exclusion list for job-node properties, with the correlation token handed to `dpl-dataset-identity-zone` / G136 rather than ruled here (R8b); (h) whether the derived queue may ever be stored as a label; (i) deferral of `:ControlMJobRun` to the `CM_HIST_VW` gate with a pointer, so nobody reads its absence as an oversight.

**Naming.** The skill's default is camelCase properties; this repo's every node uses snake_case (`folder_id`, `job_id`, `last_seen_at`) and the gate-signed envelope names are snake_case. Repo convention wins, deliberately, and this paper says so rather than leaving a reviewer to wonder.

## 7. Gaps this review found, independent of the option chosen

1. `resolver.py:30-31` assumes `..` is not used in this shop; the research measured it (2 escapes, 46 terminator dots, 18 of 56 definitions in one application). Parser gap, testable from a fixture.
2. No per-argv-token literal-vs-variable record in `ResolvedCommandLine` — F9's grade cannot be computed mechanically today.
3. `40-local-scheduler.yaml` entries carry no `properties:` key; F12's edge-property contract has no registry home. Registry schema question for the vocabulary owner.
4. MM7's acceptance prose still names the run-minted correlation token `provenance_guid`; the rename to `placement_handoff` landed 2026-08-21 in the design doc and the `data-flow-overview` prompt (R8b). A field-name lag in one item, not a conflict; where the token lives is G136's.
5. `:ControlMJobRun` is planned in three places and built in none; this paper points at the `CM_HIST_VW` gate as its owner so the deferral is recorded, not lost.
6. Pset identity: case variance and phantom dots are not normalized under the basename key (J6); a normalization rule is gate-bound because it changes identity.
7. **LIN2 (b) names a producer that does not exist (R2).** The acceptance says `--confirmed <file>` comes from `lineage-review`'s JSON export; that export is `{doc, exported, notes: [{folder, note}]}` — per-folder free text — and `plan_curated` wants `(from, type, to)` triples. LIN2 cannot meet (b) as written without either a per-rel decision export on the review page or the binding-level curation state in §6-4. Named here so the item's implementer finds it in the acceptance, not at the console.
8. **The planned/active discipline is enforced on edges and not on nodes (R6).** `writer.py:552` builds the gate check from `plan.rel_types` only; a `planned` node label can be MERGEd with nothing refusing it. `:InvocationBinding` registered `planned` would be refused through its edges (`HAS_BINDING` / `BINDS_TO`) and not in its own right. The binding writer's item extends the check to node labels, or the gate records why edges suffice.
9. **`prov_maps_to` is single-valued over a two-row endpoint and unguarded (R4)** — §6 (b). A vocabulary-owner item.
10. **Two resolution ladders (R5)** — `controlm_inventory.py:564-571` and `cmdline_staging.py:496-516` bucket the same `ResolvedCommandLine` differently; closed by §6-1.

## 8. What to mint (proposed, not minted)

After LIN2 lands, in the `LIN` series unless the module says otherwise — revised at APPLY (§4 of the review):

| # | Item | Module | Closes |
|---|---|---|---|
| 1 | **The verdict in core** — `ResolutionVerdict` on `ResolvedCommandLine` (per-token map, residue class, strength), `_resolve_shell` returns the object, `cmdline_staging` reads it; the `..` escape with a fixture at F10's measured values | `drydocs-core` (`CORE`) | R5, J5; absorbs the first draft's per-token parser item |
| 2 | **Curation state and its producer** — `curation_status` / `curated_by` / `curated_at` on the binding, a per-binding decision export from the review page, `--confirmed` derived from it, `curate()` un-stubbed; the load-bearing item | `drydocs-lineage` (`LIN`) | R2, and LIN2 (b)'s gap (§7-7) — LIN2's acceptance is amended to name it |
| 3 | **The definition-binding writer**, inside `writer.py`; node-label gate check; `binding_absent` by reason; `variants` recorded | `drydocs-lineage` (`LIN`) | R6, R7, R9, R12 |
| 4 | **The runtime-binding writer**, a new item over MM7's `OutputCoverage` | `drydocs-lineage` (`LIN`) | R8 — MM7 unchanged |
| 5 | **Gate prompt `lineage-binding-class`**, clauses (a)–(i) above | `gates` | R1, R2, R3, R4, R8b |
| 6 | **`prov_maps_to` against the matrix** — a guard that each entry's PROV term is the matrix row for its endpoint pair, or the entry declares the split | `drydocs-core` ontology (vocabulary owner) | R4 |

Not minted here: anything on the correlation token (G136 owns it, R8b); `:ControlMJobRun` (its gate). The workplan's Phase 4 row (F9, F10, F12) is this paper; Phase 3 (Ab Initio pset → datasets) is unchanged and downstream of J2/J6 being witnessed.

## 9. APPLY ledger — review `0015fcfa` + `1b615dc7`, applied 2026-09-04 (desktop)

| R | Disposition | Where |
|---|---|---|
| R1 | Taken: the grade stays derived; "D at promotion" withdrawn; the invalidation alternative recorded as the road not taken | §3-D, §6 head, §6-4, gate (d) |
| R2 | Taken: `curation_status` on the binding; the trust-axis map; the `:Uncertain` question; LIN2 (b) named as the first collision | §3-C table and axis map, §6-4, §7-7, gate (e)(f), mint 2 |
| R3 | Taken: the house qualified-attribution precedent cited, `prov_type: n/a`, the `prov:Entity` reading withdrawn | §3-C, gate (a) |
| R4 | Taken: the two-row `prov_maps_to` named; `prov:Influence` proposed with the subclass per endpoint; the guard as a vocabulary-owner item | gate (b), §7-9, mint 6 |
| R5 | Taken: the ladder and the second ladder named; the verdict computed once in core; the per-token item absorbed | §2.1 (after the table), §6-1, §7-10, mint 1 |
| R6 | Taken: node-label gate gap recorded; the writer item extends the check | §7-8, mint 3 |
| R7 | Taken: the writer lives in `writer.py` | §3-C against, §6-2 |
| R8 | Taken: the runtime writer is a new item over `OutputCoverage`; MM7's acceptance untouched | §6-3, mint 4 |
| R8b | Taken: the correlation token moved to §4's order-id bullet, out of the gate, deferred to `dpl-dataset-identity-zone` / G136; §7-4 corrected from "conflict" to "field-name lag" | §4, §7-4, gate (g) |
| R9 | Taken: `variants` recorded definition-side; J6 shrinks | §2.1 J6, §6-2 |
| R10 | Taken: fan-in corrected to ~3× at a shared `:ETLProcess`; composite index named | §3-C for |
| R11 | Taken: `class` → `binding_class` | §3-C table, throughout |
| R12 | Taken: `binding_absent` by reason on the writer's coverage | §5-Q1, mint 3 |
| R13 | Taken: the invariant cites `writer.py:20-22` | §1 |

Not applied to the tree by this APPLY: LIN2's acceptance amendment (mint 2's row) — that is an item-file edit under the `backlog` pen and lands with the mint, not with a paper. MM7's `provenance_guid` field name — MM7 is `in_progress` on another session with no `wip/` branch, so its file is not touched here; the lag is recorded for its close.
