# The lineage chain, extracted and loaded — workplan (2026-09-03)

- **Reviewed at:** commit `f338097d` on `main`, port base `port-base-20260902`; venue desktop. *Absent here reads as not-yet-ported, not as broken (docs/style/review-provenance.md).*
- **Direction (user, 2026-09-03):** the plan focuses first on mapping the Control-M job to its ETL tool — a DPL pipeline id or an Ab Initio pset — then the pipeline to its datasets, then the dataset to its landing-zone table, with the first goal of creating the extracts and the loads.
- **Evidence behind the key rules:** the machine-local capture session `2026-09-03-pex-research` (four company research documents transcribed frame by frame; its SYNTHESIS Part 2 carries twenty mechanism-only findings, cited below as F1–F20). The images are never cited; the transcript files are.
- **Epic:** `lineage-chain` (series `LIN`). Phase 1 minted at this commit: LIN1, LIN2.

## 1. The finding that shapes the plan

The lineage package has nine extractors and a curated writer, and **no verb runs the chain and no verb loads it.** `drydocs lineage-review` renders the SME page from a jobs CSV and writes nothing; `resolve-cmdline-staging` resolves command lines. `drydocs_lineage.writer.write_curated` and `plan_curated` — signed at G55 (2026-08-07) for four active labels — are called from no command. So the extractors exist as classes and the extract and the load do not exist as operations. Phase 1 is those two operations, on the hop that is already fully built, end to end.

## 2. The chain, hop by hop

| Hop | Extract today | Load today | What is missing |
|---|---|---|---|
| **1. Job → ETL tool** (DPL `-pipeline` GUID; Ab Initio `.pset`) | `controlm_inventory` through core `parse_command`: `:ETLProcess` with kind `dpl` / `abinitio` (G12); both spellings of the DPL pipeline flag (G15); the wrapper unwrap that surfaces the pset (`orchestration/shell.py`, invocation type `ABINITIO`); launcher / payload split with `USES_ARTIFACT` (G97); file ops from CMD_LINE and PRECMD/POSTCMD (G14, G60). **Built.** | `scheduler_invokes`, `scheduler_uses_artifact`, `scheduler_reads_from`, `scheduler_writes_to` are **active**; `write_curated` writes them. | A verb. Then two parser rules from the research: the pipeline id is the one flag written as a **literal** in the definition, so it outranks every variable-resolved key (F9); the scheduler's terminator period survives into extracted names and must be de-normalized before keying (F10). |
| **2a. DPL pipeline → datasets** | `dpl_mac` stages `READS_FROM` / `WRITES_TO` from `dataset_flow.json` onto GUID-keyed `dpl_dataset` assets (G17); `dpl_registry` stages pipeline and dataset GUIDs with the version and active flag (G25; skip counters fixed at G135). **Built; both contracts ASSUMED.** | The same four active labels. | The contracts have never been validated against a real export — G64 and G65, both `todo`, gate-bound. |
| **2b. Ab Initio pset → datasets** | **Nothing.** The pset is an identity token on the `:ETLProcess` and no more. | — | A collector change (capture `.pset` beside scripts — the rua `-n` glob, G18) and a new extractor that reads pset parameters into dataset-path and table candidates. An SME ruling on pset conventions before the endpoints are typed. |
| **3. Dataset → landing-zone table** | `glue_tables` lands per-zone `glue_database_*` / `glue_table_*` / `glue_path_*` as **properties** on the same GUID-keyed asset (G41); `catalog_crosscheck` reconciles placements with distribution URNs (G43); `snowflake_catalog` (G42). **Built.** | No edge by design — the placement is a property, so the load is the asset write. | G136 (`todo`): the MAC zone is a storage technology, not the medallion layer. From the research: the identifier that welds placement to trust does **not** span trust to refine (F12), a view can be a lossy projection of the config (F14), and the warehouse hop is a scoped-out **boundary** to record as one, not a metadata defect. |
| **4. Runtime witness** | MM7 (the Output-tab log extractor) `in_progress`. | — | Corroborates hops 1–2 at run time: the ordering folder does not reach the run output (F7); definition-to-runtime reconciliation needs the normalizations core already owns (F11). |

## 3. The plan, in build order

### Phase 1 — the extract and the load, on hop 1, end to end (LIN1, LIN2)

- **LIN1 `drydocs lineage-extract`.** A new S8 command module `drydocs/cli_lineage.py`. Runs the existing extractors in hop order into one `LineageGraph`: hop 1 required (jobs CSV or XML export, variables CSV when present); hop 2a (`dpl_mac`, `dpl_registry`) and hop 3 (`glue_tables`) optional, absent-means-skipped-and-counted. Every input resolves through a declared acquisition path or read zone (G81, G121) — no side door. The staged graph is written once as JSON into a new declared write zone (`lineage/staged/`) with the coverage objects beside it and a `LoaderRunLog` (G107), carrying source paths, extractor versions and the run id.
- **LIN2 `drydocs lineage-load <artifact>`.** Reads the artifact, runs `plan_curated`, prints the `WritePlan` and **stops**; `--write` runs `write_curated` for the active labels only, with the confirmed set coming from the review surface's JSON export — nothing reaches `drydocs` uncurated. Planned labels stay refused and the refusal is printed. The written nodes carry the artifact's run id, so a graph fact traces to the extract that produced it.
- **Acceptance, venue-tagged.** On the bundled samples (desktop): job → `:ETLProcess` for both kinds, `INVOKES` / `USES_ARTIFACT`, the file-op edges; hops 2a and 3 on the synthetic fixtures the existing tests already use. Then `lineage-load --write` on the desktop's `neo4jtest` / `drydocs`, idempotent on a second run, counts matching the plan. That is the first extract-and-load.
- **Why the desktop.** The bundled samples, the cmdline-staging store and the live container are here; this is Lane A work.

### Phase 2 — hop 2a and hop 3 in the same run

`dpl_mac` + `dpl_registry` join the Phase 1 run so pipeline → dataset edges load on the GUID key, and `glue_tables` adds the placements as properties in the same load. In parallel, the gate work the contracts need: **G64 / G65** validate the ASSUMED field contracts against a real export (the company holds the export; producer runs on the synthetic shapes until then). No new item until G64/G65 rule; the verbs are LIN1/LIN2's.

### Phase 3 — hop 2b, Ab Initio (LIN3, to mint at Phase 2 close)

The collector captures `.pset` files beside scripts; a new `abinitio_pset` extractor stages dataset candidates from pset parameters (input / output paths, table names) as `ETLProcess → DataAsset` `READS_FROM` / `WRITES_TO` — the file-ops shape, so likely no new label, but the endpoint typing goes through the vocabulary as `planned` first and the gate rules it. Needs company-side pset samples and an SME ruling on parameter conventions.

### Phase 4 — the research findings that change the keys (mint after Phase 1 lands)

- **F9** in core orchestration: the substitution resolver already knows, per token, whether a value was a literal or came through a variable; use that to **rank** resolved keys, not only to exclude unresolved ones.
- **F10** in core orchestration: the terminator period as a distinct parser failure mode — a value that looks resolved and is wrong; scope the correction to columns with a runtime witness.
- **F12** in the lineage model, **gate-bound**: a join-key strength grade and a definition-or-runtime flag as *edge properties* (a new property, not a new type), with the control that supports it; record the warehouse boundary as a boundary.
- **G136**: zone semantics on the MAC payload.

### Phase 5 — runbooks read from the loaded chain

F18's checks — the expected count per (business date, run slot), the run **start** time, the artifact the **next** step actually consumes — become the first `controlm-runbook-automation` outputs derived from the graph rather than from a hand profile. F2's rule rides with them: an absence names its scope (live vs archive), because an archive-only census proves history and never arrival.

## 4. What this plan deliberately does not do yet

- It does not build the landing-zone **inventory collector** (F1–F6). That collector is the research's own subject and it is real work, but the user's first goal is the chain's extracts and loads; the collector's acquisition contract (the command as run, verbatim, in the header; live and archive as separately labeled scopes; dedupe on the whole line) is recorded here so it is minted next, not forgotten.
- It does not infer a dataset-to-physical-object bridge; both research logs left it open and showed the gap is part boundary, part lossy view (F12, F14).
- It does not encode what selects a launcher's job kind (correlated 10/10, mechanism not established — "do not encode the rule").

## 5. Related backlog (from the sweep)

The capture session's `related-backlog.md` sweeps 642 items and 255 ideas against seven themes. The items this plan touches directly: G12, G14, G15, G17, G25, G41, G43, G55, G60, G97, G107, G135 (done — the pieces); G64, G65, G136, MM7 (open — the contracts, the zone, the runtime witness); G132, Z4 (open, adjacent — the folder-pull collector and the load-balancer resolver). Six gaps the sweep found with no backlog counterpart are carried in Idea-252's neighborhood for the next groom: the acquisition-contract terms, decommissioned applications as historical nodes, a vocabulary-homonym sweep, the uncaptured job-naming standard, the retrieval benchmark, and event-subscription-backed config as a lineage join.
