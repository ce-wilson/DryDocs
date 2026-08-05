# Runbook — CMD_LINE staging, resolution & parse (the G39→G48→G40 chain)

<!-- anchor: front-matter -->
- **Rev note, 2026-08-04:** the resolver path was pre-relocate
  (`drydocs_core/controlm/`); it lives under `drydocs_core/orchestration/controlm/`.
  Found by the currency audit.
- **Status:** DESCRIPTIVE — documents the working procedure. **Rev 1, 2026-07-29**
  (reflects commit `ba6b83b`: the G48 build that completed the chain — store schema
  v3, `resolution_quality` provenance, the `resolve-cmdline-staging` verb)
- **Classification:** Internal-Public (mechanism only — every command line, folder,
  and variable in this document is SYNTHETIC; real command lines are Internal and
  live only in the out-of-tree store under `DRYDOCS_DATA_ROOT`)
- **Audience:** anyone turning verbatim Control-M `CMD_LINE`s into resolved,
  parseable, structured job detail — producer-side with synthetic data, or
  company-side against the real graph + XML exports
- **Companion:** `drydocs/cmdline_staging.py` (the store + all three steps),
  `drydocs_core/orchestration/controlm/resolver.py` (the ONE resolver, G46),
  `drydocs_lineage/extractors/controlm_xml.py` (the XML seam, G47),
  `config/gate-prompts/rua-load-shapes.yaml` (G22 — the terminus any load waits on)

---

<!-- anchor: purpose-scope -->
## Purpose & scope

**Purpose.** A job's `CMD_LINE` often hides its real payload behind Control-M
variables (`%%SCRIPT_DIR/%%SCRIPT …`) — unparseable as stored. This chain stages
every job's command verbatim (G39), substitutes variables from a Control-M XML
definition export through the one shared resolver (G48), and parses the resolved
text into structured detail columns — launcher, script path, DPL pipeline GUID,
props (G40). The output is a SQLite evidence store, not a graph.

```
Neo4j :ControlMJob ──①export──▶ job_detail (cmd_line VERBATIM)
XML export ──G47 extractor──▶ ordered variables ──②resolve (G46)──▶ cmd_line_resolved + resolution_quality
job_detail ──③parse (G26/G15/G16)──▶ job_detail_parsed + parse_quality
```

**In scope.** The three CLI verbs, their run order and re-run semantics, the store
tables, and the coverage/provenance surfaces to check after each step.

**Out of scope.** Writing ANY of this to Neo4j (G22 is the only door); the
psgmgr-vs-XML source-precedence ruling (OPEN — parked in `IDEAS.md` as a HITL
question; this chain fills a nullable derived column and decides nothing); the
variables pull into the graph itself (deferred by the G18→G22 plan).

<!-- anchor: prerequisites -->
## Prerequisites

1. **A loaded graph** — `:ControlMJob` nodes with `cmd_line`, `parent_table`
   (folder name; the v3 join key) and `instance_name` present, i.e. the
   `controlm_folders` → `controlm_jobs` loader chain has run (see the startup &
   refresh runbook).
2. **`DRYDOCS_DATA_ROOT`** resolvable (env var, else `~/data/DryDocs`) — the store
   and the XML landing zone both live under it, never in the repo.
3. **A Control-M XML definition export** (DEFTABLE format) landed in
   `<DRYDOCS_DATA_ROOT>/controlm-xml/` — arbitrarily-named `*.xml` files; the
   landing zone convention is the guard (no filename fingerprint exists). Without
   one, steps ① and ③ still work; step ② refuses with exit 2.
4. The poetry environment (`poetry install`); all commands below run as
   `poetry run drydocs …` (or `drydocs …` inside the venv).

<!-- anchor: startup -->
## Startup

Bring the store from NOTHING to POPULATED — the export is the chain's step ①:

1. **Export** — one row per loaded job, command text verbatim:

   ```powershell
   drydocs export-cmdline-staging
   # jobs=240137 with_cmd_line=182254 active=175003 | task_type: Job=…, Watcher=…
   ```

   Writes `<DRYDOCS_DATA_ROOT>/cmdline-staging/job_detail.db` (schema
   `drydocs.cmdline-staging.v3`). The store is REBUILT from scratch on every run —
   it is derived plumbing (same graph → same rows, no wall-clock values), and it is
   a TEMPORARY stand-in: the retirement note in its `meta` table says it dies the
   day a real `CM_DEF_VJOB_DETAIL`-style table exists.

   The only graph access in the whole chain happens here, and it is a read-only
   `MATCH`:

   ```cypher
   MATCH (j:ControlMJob)
   RETURN j.folder_id, j.job_id, j.job_name, j.parent_table AS folder_name,
          j.instance_name AS data_center, j.task_type, j.active, j.cmd_line
   ORDER BY j.folder_id, j.job_id
   ```

   Success looks like: the summary line prints with a per-task-type census and the
   `.db` file exists at the path above.

<!-- anchor: refresh-ingest -->
## Refresh / ingest

The recurring chain on a populated store. **Order matters twice**: ② must run
before ③ (the parse prefers resolved text), and re-running ① wipes ②+③'s output
by design (resolution re-runs after every export).

2. **Resolve** (G48) — XML variables through the one shared resolver:

   ```powershell
   drydocs resolve-cmdline-staging          # default XML source: <root>/controlm-xml/
   drydocs resolve-cmdline-staging --xml-source C:\path\to\export.xml   # override
   ```

   What happens, precisely:
   - the G47 extractor stages the export taxonomy-first — folders, jobs, and
     variables with **document-order ordinals** (the resolver's
     sequential-assignment contract);
   - each store row joins an XML job on `(data_center, folder_name, job_name)`
     (a counted `dc_fallback` to `(folder_name, job_name)` exists for rows whose
     `data_center` is NULL);
   - the **store's verbatim** `cmd_line` is resolved via
     `resolve_command_line(extract.scope_layers(xml_job), cmd_line)` — the XML
     supplies ONLY the bindings. The XML job's own `CMDLINE` is compared and a
     disagreement is COUNTED (`cmd_line_mismatch` — measured evidence for the open
     precedence question), never substituted;
   - `cmd_line_resolved` is populated only when resolution changed the text;
     `cmd_line` is never touched. Per-job provenance lands in
     `resolution_quality`: verdict, source, match route, substituted names with
     the winning scope, unresolved residue, `{ODATE}`-class canonical tokens.

   ```text
   resolution: resolved=2 residue=1 nothing=2 no_match=1 ambiguous=1 no_cmd_line=1
   (of 8 jobs, 7 xml jobs) | substitutions=3 dc_fallback=1 no_folder_name=0 cmd_line_mismatch=1
   ```

   Every job lands in exactly one verdict — the buckets always sum to the job count.

3. **Parse** (G40) — resolved-when-present into structured columns:

   ```powershell
   drydocs parse-cmdline-staging
   # coverage: parsed=… partial=… unparsed=… no_cmd_line=… (…; N from resolved cmd lines)
   ```

   `parse_command` (G26 launcher registry, G15 DPL arg contract, G16 values-decide)
   fills `job_detail_parsed` (launcher, launch_mode, script_path, config_path,
   artifact_kind, pipeline_guid, props/args JSON); `parse_quality.parsed_from`
   records `resolved` or `raw` per job. Resolution exists to raise this step's
   coverage: a `%%VAR`-launcher job that was `unparsed` raw becomes `parsed` from
   its resolved text.

A worked example, one row through all three steps (synthetic):

| stage | value |
|---|---|
| ① `cmd_line` (verbatim, forever) | `%%PY_LAUNCH --pipeline-id <guid> --aws` |
| ② `cmd_line_resolved` | `/apps/py/py-launcher.sh --pipeline-id <guid> --aws` |
| ② `resolution_quality` | `verdict=resolved · substituted=[["PY_LAUNCH","FOLDER"]]` |
| ③ `job_detail_parsed` | `launcher=/apps/py/py-launcher.sh · pipeline_guid=<guid>` |
| ③ `parse_quality` | `verdict=parsed · parsed_from=resolved` |

<!-- anchor: verify -->
## Verify

- **Summary lines** print on every verb (the never-silent rule). The resolve
  buckets must sum to the job count; if `no_xml_match` dominates, see
  Troubleshooting before trusting anything downstream.
- **Spot-check the store** (sqlite3, or any client):

  ```sql
  SELECT value FROM meta WHERE key='schema_version';   -- drydocs.cmdline-staging.v3
  SELECT verdict, count(*) FROM resolution_quality GROUP BY verdict;
  SELECT parsed_from, count(*) FROM parse_quality GROUP BY parsed_from;
  SELECT cmd_line, cmd_line_resolved FROM job_detail
   WHERE cmd_line_resolved IS NOT NULL LIMIT 5;        -- verbatim ALWAYS beside derived
  ```

- **Determinism:** re-running ② or ③ without a new export produces identical
  counts (both clear their own output first).
- **The unit contract:** `poetry run pytest tests/unit/test_cmdline_staging.py
  tests/unit/test_lineage_controlm_xml.py tests/unit/test_variable_resolver.py -q`
  — green means the chain's semantics (verbatim-beside-derived, verdict
  exhaustiveness, one-resolver handoff) still hold.

<!-- anchor: rollback -->
## Rollback

The store is derived and rebuildable — rollback is re-derivation, never surgery:

- A bad resolve or parse run: just re-run it (each step clears its own tables
  first). A bad export: re-run `drydocs export-cmdline-staging`.
- Last resort: delete `job_detail.db` and re-run ①→②→③. Blast radius: the file
  itself — the graph is never written by this chain, so there is no graph state to
  restore.
- An older-schema file (v1/v2) needs no migration: export rebuilds it in place;
  resolve/parse refuse it loudly with a re-export hint rather than guessing.

<!-- anchor: troubleshooting -->
## Troubleshooting

| Symptom | Diagnosis | Fix |
|---|---|---|
| `XML source not found …` (exit 2) | nothing landed in `controlm-xml/` | land an export there, or pass `--xml-source` |
| `not a drydocs.cmdline-staging.v3 store` | pre-v3 file from an earlier session | `drydocs export-cmdline-staging` (rebuilds in place) |
| `no_xml_match` unexpectedly high | join key broken: `folder_name` NULL (graph loaded before the loader stamped `parent_table`) or `data_center` spellings differ between psgmgr and the export | check `no_folder_name` in the summary; reload jobs, or rely on the counted `dc_fallback` only where the store dc is NULL |
| `ambiguous_match` > 0 | the same job name appears twice under one folder (sub-folder twins) — skipped, never guessed | expected; resolve those by hand if they matter, or refine the export |
| `cmd_line_mismatch` > 0 | psgmgr's and the XML's command text disagree | EXPECTED evidence, not an error — it feeds the open precedence ruling; do not "fix" either side |
| `residue` verdicts | `%%NAME` had no binding in scope, or the token is runtime-only | check `unresolved_json`; `{ODATE}`-class canonical tokens are expected residue, not failures |
| WARN flood on parse | partial/unparsed rows log per job | that is the WARN stream doing its job — counts are in the summary; the rows are all in `parse_quality` |

<!-- anchor: contacts-escalation -->
## Contacts & escalation

- **Owner:** the main (producer) session; company-side the raw-twin XML loader team
  runs the same mechanism against real exports.
- **Anything that would give this data MEANING in the graph** — loading resolved
  commands, INVOKES edges from parsed detail, usage conclusions — escalates to the
  HITL gate chain (G22, `config/gate-prompts/rua-load-shapes.yaml`). No loader
  exists for this store, deliberately.
- **The psgmgr-vs-XML precedence question** (which source wins per object, with a
  named owner-and-sunset for the dual definition path) is the SME's to rule —
  parked in `docs/restructure/IDEAS.md`; `cmd_line_mismatch` is its evidence feed.

<!-- anchor: appendices -->
## Appendices

**A — store tables (schema `drydocs.cmdline-staging.v3`).**

| table | one row per | key columns |
|---|---|---|
| `meta` | store fact | `schema_version`, `retirement`, `psgmgr_projection`, `variables` |
| `job_detail` | loaded job | `cmd_line` (verbatim) · `cmd_line_resolved` (derived, nullable) · `folder_name` (v3 join key) |
| `resolution_quality` | job, per resolve run | `verdict` · `resolution_source` · `matched_via` · `substituted_json` · `unresolved_json` · `canonical_tokens_json` |
| `job_detail_parsed` | parsed invocation | `invocation_type` · `launcher` · `launch_mode` · `script_path` · `pipeline_guid` · `props_json` |
| `parse_quality` | job, per parse run | `verdict` · `parsed_from` (`resolved`\|`raw`) |

**B — verdict vocabularies.**

- resolution: `resolved · residue · nothing_to_substitute · no_xml_match ·
  ambiguous_match · no_cmd_line`
- parse: `parsed · partial · unparsed · no_cmd_line`

**C — the company-side equivalent of step ①** is documented inside the store
itself (`meta.psgmgr_projection` — the `psgmgr.CM_DEF_VJOB` SELECT with the same
columns in the same order, `cmd_line_resolved` as `NULL` for downstream
population).
