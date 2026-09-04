# The job-to-ETL binding: what the definition cannot tell us, and options for a runtime second pass (2026-09-04)

- **Reviewed at:** commit `93f4d832` on `main`, port base `port-base-20260902`; venue desktop. *Absent here reads as not-yet-ported, not as broken (docs/style/review-provenance.md).*
- **Direction (user, 2026-09-04):** review the folder and job unknowns and partial-knowns in the hop-1 mapping (Control-M job to DPL pipeline id or Ab Initio pset); plan options for a **second class of properties** added to the job or folder nodes **after runtime**, for the values that are difficult to determine from the definition SQL; use Neo4j modeling best practice.
- **Evidence:** the code as cited below; the live graph on this desktop (`neo4jtest`, database `drydocs`: 17 `:ControlMJob`, 8 `:ControlMFolder` from the bundled samples, no `:ETLProcess` yet — LIN2 is unbuilt); the machine-local capture session `2026-09-03-pex-research` (SYNTHESIS Part 2, mechanism-only findings F1–F20, cited by number — the images are never cited); the `neo4j-modeling` skill's decision tables (marked `[official]` / `[field]` as that skill marks them). Companion to the lineage-chain workplan (`docs/reviews/lineage-chain-extract-load-workplan-2026-09-03.md`); this paper is Phase 4 of that plan, thought through before it is minted.
- **Decides nothing.** Every new label, relationship type or edge property here is an ontology change and goes through the relationship-vocabulary registry as `status: planned` and the HITL gate. The recommendation at the end is what the gate prompt should propose.

---

## 1. Two epistemic classes, and why the graph must keep them apart

The hop-1 binding — *which ETL workload does this job launch* — can be established two ways, and they are different claims:

| Class | Source | What it proves | What it cannot prove |
|---|---|---|---|
| **Definition** | `CM_DEF_VJOB.CMD_LINE` + `CM_DEF_SETVAR` (the variables pool), resolved by `drydocs_core.orchestration.controlm.resolver` | What the job is *configured* to launch, at the capture date, for the current version | That it ever ran; what a per-run variable resolved to; that the resolver's reading of the vendor syntax matched the agent's |
| **Runtime** | Output-tab sysout / shell trace echo per `<job, order id, run>` (MM7's subject); the launcher banner JSON | What was *actually submitted*, byte for byte, on a dated run (F11's positive control: a resolved command matched its echo character for character, doubled slash included) | That the definition still says so today (F20: a witness has a shelf life); anything about data movement — the sysout proves submission, not rows (F12) |

Today the graph holds only the first class, and it holds it on one surface: the curated `INVOKES` edge from `:ControlMJob` to `:ETLProcess {token}` (`drydocs_lineage/writer.py:233-235`), keyed by the env-stable token `_stable_invocation_key` computes (`drydocs_lineage/extractors/controlm_inventory.py:281-298`: DPL → the pipeline GUID; Ab Initio → the pset basename). That edge is the **confirmed** surface — nothing reaches it uncurated (the package invariant, `model.py:29-30`). A runtime observation is a *candidate* by construction (it may disagree with the definition, it may be stale, it may be n=1), so it cannot be written to that edge without breaking the invariant. That is the whole design constraint for the second pass: **the second class needs its own home, from which curation can promote.**

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
| J6 | **Pset identity split by venue or case** — 34 distinct pset strings that are ~14 psets | basename keying (`_stable_invocation_key`) removes the venue prefix; **case variance and phantom dots are not normalized** | F12 hop grade untested past trust; C21 in the source log | A witness per venue: which prefix ran where, so the ~14 can be confirmed as 14 |
| J7 | **No invocation recognized** — nothing classified, or no target | `commands_unparsed`, `invocations_no_target`, `classify_executable`→`UNKNOWN` against `config/launcher-registry.yaml` | unknown kind | The launcher banner names the kind (`launcher_kind` in MM7). Note F12's caution against encoding the kind rule from correlation alone |
| J8 | **Artifact variable unresolved** — `%%JAR_PATH`-class values are refused as node names | `_is_resolved_literal` (`controlm_inventory.py:269-278`), counted in `artifact_values_unresolved` | — | The resolved artifact URI, as a witnessed string, not as a node |

Two things the definition side lacks that the second pass needs *from the first pass*:

- **A per-argv-token literal-vs-variable record.** F9's grade (a literal outranks a resolved variable) needs to know, per token, whether it was substituted. `ResolvedCommandLine.substituted` records *which names* bound and in which scope; there is no per-token map. This is a `drydocs_core` change (the resolver already has the information at substitution time) and is a prerequisite for grading J1 vs J2 mechanically rather than by rule name.
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

One `:InvocationBinding` per **(job, class, token)** — so a job typically has one or two, never one per run:

| property | meaning |
|---|---|
| `binding_id` | `<folder_id>.<job_id>|<class>|<token>` — the MERGE key, with a uniqueness constraint (skill default 4) |
| `class` | `definition` \| `runtime` |
| `strength` | `literal` \| `variable` \| `runtime_echo` \| `unresolved` (F9's ranking, F12's grade) |
| `kind`, `token` | as `_stable_invocation_key` would compute from the value this class saw |
| `executed_value` | the pset path / GUID *as seen by this class* (venue prefix intact — J6's evidence) |
| `resolved_command` | the normalized command (F11's two normalizations applied) |
| `residue_class` | `none` \| `runtime_only` \| `cross_job_ref` \| `unresolved` (F11: classify, do not count) |
| `first_observed_at`, `last_observed_at`, `observations` | witness dedupe: one node per distinct executed value, dated (F20's shelf life) |
| `witness_ref` | the sysout file / order id that supports it — a reference, never a key (F8) |
| `capture_ref` | for the definition class: the extract's `capture_date` and version |

- **For `[official]`:** the connection has >2 properties, has **multiple sources for one (job, target) pair**, and is the subject of its own queries (Q2, Q5, Q6 below) — all three of the skill's promote-to-intermediate-node conditions. The two classes coexist on separate nodes, so a disagreement is a *query*, not a lost write. `INVOKES` stays exactly as ruled and curated: a `runtime` binding is a candidate that curation promotes by confirming the token; the gate ruling on env-stable identity is untouched. PROV-friendly — the binding is a `prov:Entity` derived from a witnessing `prov:Activity`. Cardinality is bounded (1–3 per job, ~750K nodes at estate scale — not a supernode risk; the `:ETLProcess` fan-in is the same as `INVOKES` has today).
- **Against:** a new label and two new relationship types — an ontology change, gate-bound, `planned` first; one more hop in the traversal from job to workload (mitigated: `INVOKES` remains the confirmed shortcut); a loader that must MATCH both endpoints and count unmatched (the established derived-pass shape, so not new machinery).

### Option D — provenance properties on `INVOKES` (F12's literal proposal)

`class`, `strength`, `witness_ref`, `observed_at` on the existing edge; a runtime disagreement becomes a second `INVOKES` to a different `:ETLProcess`.

- **For:** F12 asks for exactly this — a grade and a definition-or-runtime flag *as edge properties, not a new type*; the smallest vocabulary change.
- **Against:** it writes an **unconfirmed** runtime candidate onto the **confirmed** surface, which is the invariant §1 says the second pass must not break; run-scoped facts (image digest, compute target) are not facts about the job→workload connection; and `40-local-scheduler.yaml` has **no machine-readable `properties:` key on any entry** — edge properties exist only as prose in `note:` blocks — so an edge-property contract has no registry home yet. Verdict: right for the *grade on the confirmed edge once curation has promoted a binding* (curation copies `strength` and `class` up); wrong as the home for the candidate class.

### Option E — the run as a node: `:ControlMJobRun`

Already in the vocabulary as `planned` (`scheduler_instance_of`, `scheduler_executed_by`, `40-local-scheduler.yaml:608,653`), in the schema graph (`schema_graph.cypher:68-69`), and in a SOSA gate prompt (`config/gate-prompts/sosa-jobrun-observation.yaml`, `CM_HIST_VW`). One node per execution carrying the witnessed facts; the job's runtime view is a roll-up over its runs.

- **For:** the most faithful — a witness *is* an event; every ephemeral id (F8) has a correct home and never touches the definition node; F7's per-step attribution and F20's dating fall out naturally; nothing new to rule, only two planned entries to activate.
- **Against:** cardinality — ~240K jobs × daily runs is millions of nodes a quarter, and the runtime witness today is a *sample* of sysouts, not a history feed; MM7's own acceptance is "sets properties only, creates no edge" precisely because no run node exists. A per-run node is the right **eventual** shape for run history (the `CM_HIST_VW` gate); it is not the right first home for hop-1 bindings.

## 4. What must never be a job property, whatever the option

- The platform's run-correlation id that shares a name with DryDocs' own provenance term (F8 — three values for one dataset in nine days; never a provenance property, never a join key, always written qualified). MM7's property list carries it as `provenance_guid`; under Option C it is `witness_ref`-adjacent evidence on the binding at most, and it is **not** on `:ControlMJob`. This is a conflict between MM7's draft list and F8 to settle at MM7's gate.
- Per-run values from residue (J3): business date, order id, process id, executing host — the launcher host is a pool, not an attribute of the step.
- Anything named for the event it *resembles* rather than the event it records (F6, F7): the observed clock bucket is not a `cycle`; the archive stamp is a job **start**, not a move.

## 5. The queries the model must answer (skill default 1: use cases before design)

| # | Question | A | B | C | D | E |
|---|---|---|---|---|---|---|
| Q1 | Which jobs have **no** ETL identity from the definition? (the queue) | prop null | label | no `definition` binding, or `strength = unresolved` | no edge | — |
| Q2 | Which jobs' definition token **disagrees** with the runtime-witnessed token? | cannot — one slot | cannot | two bindings, different `token` | two `INVOKES` (but on the confirmed surface) | roll-up over runs |
| Q3 | For pipeline GUID X, which jobs invoke it — by definition, by runtime, by both? | partial | — | `BINDS_TO` grouped by `class` | edge `class` | run join |
| Q4 | Which psets run under more than one venue prefix? (J6) | — | — | `executed_value` distinct per `token` | — | per run |
| Q5 | Which **unresolved** jobs have a runtime witness newer than N days — i.e., now resolvable? | no date per fact | — | `runtime` binding with `last_observed_at` | — | yes |
| Q6 | Which witnesses are **older** than the job's `version_timestamp`? (F20 — stale evidence) | partial | — | compare binding date to job version | — | yes |
| Q7 | Runbook: for job J, the artifact the **next** step actually consumes (F18) | — | — | `executed_value` of the downstream binding | — | yes |

Option C answers all seven without a run-history feed; E answers them once one exists; A and B answer only Q1.

## 6. Recommendation, staged

**C now, D at promotion, E when run history is a feed.** Concretely:

1. **Definition class first (LIN2's neighborhood, no new evidence needed).** The definition pass writes a `definition` binding per job alongside `INVOKES`, with `strength` from F9's rule — which needs the **per-token literal-vs-variable record** in `drydocs_core.orchestration.controlm.resolver` (§2.1's first gap) and the **`..` escape** handled (J5). Both are core parser changes with sample-reproducible tests; neither moves a gate.
2. **Runtime class from MM7.** MM7's `OutputCoverage` already yields the executed command, GUID, launcher kind and digest per `<job, order id, run>`; its writer stages a `runtime` binding **deduped on `(job, executed_value)`** with first/last observed and a count, joined to the job by identity parsed from the sysout filename (MM7's rule) and to `:ETLProcess` by the token the executed value yields. `provenance_guid` leaves the job-node property list (§4).
3. **Curation promotes.** A `runtime` binding whose token matches the `definition` binding is corroboration and raises the confirmed edge's grade (Option D's properties, copied up at promotion); a mismatch is a review-page row (`lineage-review` already renders unresolved candidates); a `runtime` binding with **no** definition counterpart (J4, J7) is the case the pass exists for and is promoted to `INVOKES` only by confirmation.
4. **The queue is derived, not stored (Option B rejected as storage).** `drydocs lineage-load` prints the counts per §2.1 state from the bindings; a label is added only if a measured query needs it, from one writer.
5. **Folders get definition-side derivations and per-step refusals only** (§2.2): `cadence_char` with `convention_scope`; `run_attribution: not_derivable` recorded on the step, never inferred.

**Gate scope (one prompt, `lineage-binding-class`):** (a) the `:InvocationBinding` label and `HAS_BINDING` / `BINDS_TO` types, registered `planned`; (b) the `strength` and `residue_class` enumerations; (c) the rule that `INVOKES` stays the confirmed surface and a binding is the candidate surface; (d) the F8 exclusion list for job-node properties, settling MM7's draft list; (e) whether the derived queue may ever be stored as a label; (f) deferral of `:ControlMJobRun` to the `CM_HIST_VW` gate with a pointer, so nobody reads its absence as an oversight.

**Naming.** The skill's default is camelCase properties; this repo's every node uses snake_case (`folder_id`, `job_id`, `last_seen_at`) and the gate-signed envelope names are snake_case. Repo convention wins, deliberately, and this paper says so rather than leaving a reviewer to wonder.

## 7. Gaps this review found, independent of the option chosen

1. `resolver.py:30-31` assumes `..` is not used in this shop; the research measured it (2 escapes, 46 terminator dots, 18 of 56 definitions in one application). Parser gap, testable from a fixture.
2. No per-argv-token literal-vs-variable record in `ResolvedCommandLine` — F9's grade cannot be computed mechanically today.
3. `40-local-scheduler.yaml` entries carry no `properties:` key; F12's edge-property contract has no registry home. Registry schema question for the vocabulary owner.
4. MM7's `provenance_guid` property conflicts with F8; settle at MM7's gate.
5. `:ControlMJobRun` is planned in three places and built in none; this paper points at the `CM_HIST_VW` gate as its owner so the deferral is recorded, not lost.
6. Pset identity: case variance and phantom dots are not normalized under the basename key (J6); a normalization rule is gate-bound because it changes identity.

## 8. What to mint (proposed, not minted)

After LIN2 lands, in the `LIN` series: the core parser pair (per-token record + `..` escape), the definition-binding writer, the runtime-binding writer on MM7's coverage, and the gate item — four items and one gate prompt. The workplan's Phase 4 row (F9, F10, F12) is this paper; Phase 3 (Ab Initio pset → datasets) is unchanged and downstream of J2/J6 being witnessed.
