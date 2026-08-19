# Runbook — DryDocs lineage ingest (jobs CSV + DPL MAC) → curated graph load

<!-- anchor: front-matter -->
- **Status:** DESCRIPTIVE — documents the working procedure end-to-end, INCLUDING the
  deliberate gate refusal at the load step. **Rev 3, 2026-07-23** (clone authority
  caveat: the clone's main may lag — feature branches pushed, not reliably merged —
  so the folder listing is a floor, not the authority; by-SEAL bulk
  `pipeline_id.json`/`dataset_id.json` downloads are the backup discovery source,
  dataflow stays per-pipeline swagger regardless; reflects commit `41c4879`.
  Rev 2, 2026-07-23: commit `4e77c1c` — clone-layout
  discovery: the MAC root may be a Bitbucket promotion-repo checkout —
  `<name>#<guid>` folder parsing, per-folder scope, the swagger per-pipeline
  dataflow work list; `controlm_jobs.sql` path corrected; curated-load graph-shape
  pin added. Rev 1, 2026-07-21: commit `297167e` —
  post-G14 file-ops pass, post-G15 launcher contract, post-G17 MAC ingest seam.
  The m3_* lineage vocabulary is `status: planned` — the live load REFUSES by
  design until the HITL gate flips it)
- **Classification:** Internal-Public (mechanism only — every example value is
  synthetic; real jobs CSVs and MAC JSON exports are internal-confidential and live
  OUT of the repo tree, never in this doc)
- **Audience:** whoever runs the lineage ingest — producer-side against synthetic
  fixtures, company-side against real psgmgr extracts and DPL Metadata-As-Code sets
- **Companion:** `docs/design/drydocs-startup-refresh-runbook.md` (container, schema
  bootstrap — prerequisite for the load step only),
  `docs/restructure/03-hitl-sme-flow.md` (the gate that unlocks the load),
  `drydocs_lineage/extractors/dpl_mac.py` (the assumed MAC field contract),
  `config/gate-log.md` 2026-07-15 "Lineage rel vocabulary gate" + 2026-07-16
  "cmdline-lineage-review" (the shapes this pipeline implements)

---

<!-- anchor: purpose-scope -->
## Purpose & scope

**Purpose.** Take Control-M job definitions from a `psgmgr` CSV projection, enrich
them with DPL Metadata-As-Code (MAC) JSON sets, and drive the result through the
candidate → SME review → curated → (gated) graph-load chain. "The script" at the
front of this chain is the SQL extract that produces the jobs CSV; "the load script"
at the end is `drydocs_lineage.writer.write_curated`, which populates :Script /
:ETLProcess / :DataAsset nodes and INVOKES / TRIGGERS / READS_FROM / WRITES_TO edges
— **only after** the lineage vocabulary gate flips those entries active.

**In scope.** Producing/staging the two inputs; running both extractors into one
candidate graph; the SME review page; assembling the confirmed set; `plan_curated`
(the exact write batches, reviewable before anything runs); the gated live load and
its unlock path.

**Out of scope.** Container startup and schema bootstrap (companion startup-refresh
runbook); the rua server-extract phase (G18–G25 — its own pipeline, its own G22
gate); Epic P host resolution (`node_target` stays polymorphic here); attribution
edges (Epic K owns those — this pipeline records SEAL *facts* only).

<!-- anchor: prerequisites -->
## Prerequisites

1. **Toolchain:** pipx-installed Poetry with the in-project `.venv` synced
   (`poetry install`). No network or Neo4j needed until the load step.
2. **The jobs CSV** — a projection of `psgmgr.CM_DEF_VJOB` whose header matches the
   `controlm_jobs.sql` SELECT aliases (`job_id, version_serial, folder_id, job_name,
   parent_table, application, owner, node_id, cmd_line, is_current_version, …` —
   the column contract is pinned by `tests/unit/test_source_mapping_drift.py`).
   Company-side: run `drydocs/loaders/sql/controlm_jobs.sql` through your JDBC
   path — the SAME file `ingest-controlm --use-oracle` executes, so this CSV and an
   `ingest-controlm --use-oracle --phase nodes` initial load come from one
   projection. Producer-side: the synthetic twin `tests/fixtures/lineage/jobs.csv`.
3. **The MAC root (optional — skip and the pipeline still runs, un-enriched):**
   either staging layout works; consumption is identical:
   - **Hand-staged sets** — a directory of per-pipeline JSON sets, each
     subdirectory holding `pipeline.json` + `dataset_flow.json` (+ the rest of the
     traced 6-set, which is counted and ignored).
   - **Promotion-repo clone (Bitbucket)** — dataset and pipeline folders sit as
     SIBLINGS under `src/main/resources/promotion/pipelines/`, one folder per
     object, named `<name>#<guid>`: pipeline folders lowercase
     (`accounts_conform_aws_ingest#<guid>`), dataset folders UPPERCASE
     (`ACCOUNTS_RAW#<guid>`). The extractor parses the folder names: pipeline
     GUIDs join exactly like `pipelineId`, folder names land as `mac_clone_name`
     facts, dataset folder names fill `dataset_name` where a flow entry lacks
     one. The swagger export tool serves `dataset_flow.json` only per-pipeline
     (bulk `pipeline_id.json` / `dataset_id.json` by SEAL exist, but no bulk
     dataflow) — a fresh clone therefore has pipeline folders with NO JSON set
     yet: `clone: missing_sets=` counts them and `clone_missing_set_guids` IS the
     per-pipeline fetch work list. Drop each fetched set into its `name#guid`
     folder and re-run.

     **Authority caveat (SME, 2026-07-23):** the clone's main may LAG — the dev
     team pushes feature branches and does not reliably merge — so the folder
     listing is a floor on the inventory, never the authority. Backup discovery:
     pull ALL pipelines/datasets for the SEAL as bulk `pipeline_id.json` /
     `dataset_id.json` (field contract unacquired — not yet consumed by the
     extractor; hand-reconcile until a sample lands). Dataflow is per-pipeline
     swagger regardless of which source discovered the pipeline.

   Field contract documented at the top of
   `drydocs_lineage/extractors/dpl_mac.py` — ASSUMED until a real sample validates
   it. **Real exports and clones are internal-confidential: keep them out of the
   repo tree** (out-of-tree home `~/data/DryDocs/` per the G19 convention; until
   G19 lands the location is manual discipline, not tooling).
4. **For the load step only:** the `neo4jtest` EE container READY per the companion
   runbook, `.env` at repo root with `NEO4J_*` (names only — never in this doc), and
   the target database `drydocs` (the writer hard-refuses any other DB). The writer
   MATCHes ControlMJob by the `(folder_id, job_id)` NODE KEY — the psgmgr-shaped
   graph an `ingest-controlm` load produces (`job_id` is folder-scoped there; the
   `ctlm_id` composite is its `folder_id.job_id` single-string form). A graph
   loaded from the XML definition path carries differently-shaped job identity and
   is NOT the target of this runbook's load step.
5. **Reference reading before a first run:** the two gate-log entries named in
   Companion — they are the WHY for every endpoint shape below.

<!-- anchor: startup -->
## Startup

From nothing to READY-to-ingest. Run from the repo root.

1. **Sync the venv:** `poetry install`. *Success:* `poetry run drydocs --help` prints
   the command list.
2. **Stage the jobs CSV** somewhere readable (synthetic:
   `tests/fixtures/lineage/jobs.csv` works as-is). *Success:* the header line
   contains `job_name`, `cmd_line`, `node_id`.
3. **Stage the MAC root** (optional): hand-staged — one subdirectory per pipeline,
   each with at least `pipeline.json`; clone — `git clone` the promotion repo (out
   of the repo tree). *Success:* hand-staged: `Get-ChildItem <mac-root> -Recurse
   -Filter pipeline.json` lists one file per pipeline set; clone: the
   `promotion/pipelines/` listing shows `name#guid` siblings — pipelines
   lowercase, datasets UPPERCASE.

<!-- anchor: refresh-ingest -->
## Refresh / ingest

The recurring procedure on a READY setup. Steps 1–4 are pure candidate-side (no
graph, rerun freely); step 5 is the gated write.

1. **Extract candidates** — both extractors feed ONE `LineageGraph`:

   ```powershell
   poetry run python -c @"
   from drydocs_lineage.extractors import ControlMInventoryExtractor, DplMacExtractor
   from drydocs_lineage.model import LineageGraph
   g = LineageGraph()
   inv = ControlMInventoryExtractor().extract(r'tests/fixtures/lineage/jobs.csv', g)
   print('inventory |', inv.summary())
   mac = DplMacExtractor().extract(r'<mac-root>', g)   # skip these 2 lines if no MAC
   print('mac       |', mac.summary())
   print('graph     |', g.stats())
   "@
   ```

   `<mac-root>` may be the hand-staged root, the clone root (or its
   `promotion/pipelines/` dir), or a SINGLE `name#guid` pipeline folder — the
   per-folder scope for one-pipeline reruns.

   *Success:* both `summary()` lines print, and every skip shows up as a COUNT
   (`unresolved=`, `unmatched=`, `riders=`…) — the house rule is counted-never-
   silent, so a zero-warning run and a warning-heavy run are both "working";
   what matters is that the numbers reconcile with what you fed in.
   The MAC join is by `--pipeline-id` GUID (both launcher spellings) onto the
   `proc#dpl:{GUID}` identity the inventory pass created; `matched` +
   `unmatched` should equal `sets_read - sets_no_guid - sets_invalid`. On a
   clone, `clone: pipes=` should equal sets consumed plus `missing_sets=` (the
   still-to-fetch list).

2. **Render the SME review page** (no Neo4j):

   ```powershell
   poetry run drydocs lineage-review <jobs.csv> -o lineage-review.html
   ```

   *Success:* the HTML opens; same-basename multi-mount Script duplicates and
   `kind UNKNOWN` invocations are flagged for the SME — they are NEVER
   auto-merged/auto-typed.

3. **Curate.** The SME confirms a subset of candidate rels (today: assemble the
   confirmed `(src, TYPE, dst)` set from the review pass — `curation.curate` is a
   stub by design). Anything ambiguous goes to the HITL gate, not a guess.

4. **Plan the write** — pure function, produces the EXACT batches for review:

   ```python
   from drydocs_lineage.writer import plan_curated
   plan = plan_curated(g, confirmed)
   print(plan.scripts, plan.etl_processes, plan.assets, plan.rels)
   ```

   *Success:* no `ValueError` (a raise means the confirmed set drifted from the
   graph, or a job lacks its `folder_id.job_id` NODE-KEY composite — fix the
   input, don't hand-edit the plan). ETLProcess rows take their `kind` from the
   MAC-derived `mac_kind` where present; rider-path nodes (e.g.
   `subType=provisioning`) keep the default `'etl'` **on purpose** until the
   enum gate ruling.

5. **Load — currently REFUSES, and that is the contract:**

   ```python
   from drydocs_lineage.writer import write_curated
   write_curated(g, confirmed, client)   # raises GateBoundVocabularyError today
   ```

   The four `m3_*` registry entries are `status: planned`; `write_curated` reads
   the registry and refuses a live load until they are `active` (D2:
   curated-only writes). **The unlock is a HITL gate session, not a code edit:**
   the lineage live-load gate flips the entries active WITH their
   `ontology_supplement.cypher` blocks (the K2 flips-are-follow-ups pattern;
   `test_schema.py` enforces block-per-active-edge). After the flip, rerun this
   step — MERGE semantics make it idempotent.

<!-- anchor: verify -->
## Verify

- **Candidate side (every run):** `poetry run pytest
  tests/unit/test_lineage_inventory.py tests/unit/test_lineage_mac.py
  tests/unit/test_lineage_writer.py -q` → all green (fully synthetic, no network).
  Coverage numbers from step 1 reconcile: MAC `matched + unmatched =
  sets_read - sets_no_guid - sets_invalid`; inventory `jobs_added + skipped_* =
  rows_read`.
- **Plan side:** `plan.rels == len(confirmed)`; every statement in
  `plan.statements` is a MERGE/MATCH batch you can eyeball — nothing is hidden.
- **Post-flip load (once the gate opens):** rerun step 5, then in the graph:
  node counts match `plan.scripts / .etl_processes / .assets`; every written rel
  carries `vocab_id` + `source='drydocs-lineage'`; ETLProcess `kind` is
  MAC-derived where a MAC set covered the pipeline and `'etl'` elsewhere.
- **Full suite before any commit that touched this component:**
  `poetry run pytest -q` green + `python -c "import drydocs.cli"` +
  `drydocs --help` (the CLAUDE.md §6 gates).

<!-- anchor: rollback -->
## Rollback

- **Steps 1–4 persist nothing** — the candidate graph is process memory (or a JSON
  export you chose to write). Re-run at will; that IS the rollback.
- **A failed/partial live load:** rerun step 5 — every node/rel statement is a
  keyed MERGE (`Script.path`, `ETLProcess.token`, `DataAsset.assetId`, NODE-KEY
  jobs), so re-running converges rather than duplicating.
- **Last resort (destructive — blast radius: everything this component ever
  wrote, and ONLY that):** delete by provenance stamp,
  `MATCH ()-[r {source:'drydocs-lineage'}]-() DELETE r` then the orphaned
  `{source:'drydocs-lineage'}` nodes. Job nodes are never created by this writer
  (MATCH-only), so the Control-M load is untouched.

<!-- anchor: troubleshooting -->
## Troubleshooting

- **`GateBoundVocabularyError` at step 5** → not a bug; the vocabulary is still
  `planned`. See the unlock path in step 5. If it raises AFTER the gate flipped,
  the registry edit didn't land — check the statuses in `drydocs_core/ontology/relationship_vocabulary/` (per-domain fragments since S5).
- **`TrustBoundaryError`** → the client points at a database other than
  `drydocs`. Fix the connection; the writer will not follow you.
- **MAC `unmatched` unexpectedly high** → the jobs CSV and MAC export cover
  different scopes (unmatched sets are still staged, flagged `mac_only=true`), or
  the GUID never appeared on a CMD_LINE (the code-fetch gap family — real
  finding, not noise).
- **`clone: missing_sets` > 0** → expected on a fresh clone: the swagger tool
  serves dataflow only per-pipeline. Fetch per GUID in
  `clone_missing_set_guids`, drop the JSONs into the matching `name#guid`
  folder, re-run. Not an error.
- **`clone: mismatch` > 0** → a folder-name GUID differs from its
  `pipeline.json` `pipelineId`; the json wins (it IS the set's key). Review
  material — a stale clone or a set dropped into the wrong folder.
- **`dpl_without_mac` > 0 on a clone run** → pipelines running in Control-M
  with no clone folder — the clone-main lag showing up (prereq 3 authority
  caveat). Cross-check against the by-SEAL bulk `pipeline_id.json` before
  concluding the pipeline is undocumented.
- **`kind_riders` > 0** → expected for `provisioning` and any unmapped subType;
  the enum question is inboxed (IDEAS 2026-07-21 gate-rider entry). Do NOT add
  mappings to `_KIND_BY_SUBTYPE` without a gate ruling.
- **`ValueError: … lacks the ControlMJob NODE-KEY composite`** → the CSV came
  from a hand-made source without `folder_id`/`job_id`. Re-extract from the real
  projection; curated writes refuse degraded identity by design.
- **Column-contract drift** (`row.get` misses) → `test_source_mapping_drift.py`
  is the guard; reconcile the SQL alias, never patch around it in the extractor.
- **`%%VAR` values in properties** → unresolved Control-M variables are kept
  VERBATIM as curation material — resolution belongs to the variable pipeline,
  not this extractor.

<!-- anchor: contacts-escalation -->
## Contacts & escalation

- **Procedure owner:** the DryDocs producer (repo owner). Company-side runs are
  owned by whoever operates the psgmgr extract + MAC export there.
- **Anything touching edge MEANING** (new relationship types, endpoint reshapes,
  the kind-enum question, planned→active flips) escalates to the SME through the
  HITL gate (`docs/restructure/03-hitl-sme-flow.md`) via the ontology-mapper
  flow — never decided in-pipeline. Decisions land in `config/gate-log.md`.
- **Field-contract corrections** (real MAC samples disagreeing with the assumed
  contract): update `dpl_mac.py`'s header + fixtures together, cite the sample's
  provenance in the commit.

<!-- anchor: appendices -->
## Appendices

**A. The candidate chain at a glance**

```
controlm_jobs.sql ─▶ jobs CSV ─▶ ControlMInventoryExtractor ─┐
                                                             ├─▶ LineageGraph ─▶ review ─▶ confirmed ─▶ plan_curated ─▶ write_curated ─▶ Neo4j
MAC root (hand-staged sets OR ─▶ DplMacExtractor ────────────┘                                              (refuses until gate flip)
 promotion-repo clone, name#guid)
```

**B. What each extractor contributes**

| Source | Nodes | Rels (all `status: planned` vocab) | Properties |
|---|---|---|---|
| jobs CSV | ControlMJob, Script, ETLProcess | INVOKES; job-level READS_FROM/WRITES_TO (G14 file ops) | G15 launcher args incl. `seal` |
| MAC sets | ETLProcess (join/enrich), `dpl_dataset` DataAssets | dataset-level READS_FROM/WRITES_TO | `mac_pipeline_type`, `mac_sub_type`, `mac_kind` / `mac_kind_rider`, `mac_owner_seal`, `mac_clone_name` (clone layout) |
