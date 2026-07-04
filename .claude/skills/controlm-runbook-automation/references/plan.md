# §RUNBOOK — automating runbook creation from the graph (the primary use case)

**Why this skill exists.** The team is "application support" in name but supports
many apps without being in the design sessions. The runbooks handed over are
folder-level spreadsheets — yet ~95% of their content already lives in systems
we can query (the CM_ replica, the escalation DB, the pipeline metadata service,
git dataset-flow files, the naming standard itself). The goal: **generate the
runbook from the graph instead of maintaining it by hand**, and use each
generation pass to *fix the underlying metadata* in small batches.

Mechanism-only file: grammar tokens and column names are established vocabulary;
every concrete value below is a placeholder. Real instances live in gitignored
`internal-local/` and `internal/`.

---

## §PIPELINE — six phases (each independently useful)

```
P1 base graph  →  P2 CMDLINE lineage  →  P3 pick fix batch (failures)
      →  P4 extract data series (FW → provisioning)  →  P5 HITL review + target metadata
      →  P6 fix package → Jira (dev team implements; we never deploy)
```

### P1 — Control-M base (largely EXISTS)
Ingest the CM_ replica across all data centers → staging → graph
(`controlm-db` skill → `references/ingest.md`): folders, jobs, variables, in/out conditions, derived
`:WAS_INFORMED_BY` edges (the derived job→job dependency; `DEPENDS_ON` is the
retired name). This *deliberately imports stale folders too* — staleness is
a finding, not noise. Stale signals to tag on `:JobFolder`:
- `USER_DAILY IS NULL` (not actively scheduled) — excluded from the standard
  extracts, so run a separate stale-inventory pass **without** that filter
- naming that fails `parse_folder_name` / predates the current standard
- no current-version jobs; no conditions consumed by anything current
- `-PRPL` (parallel/pre-release) or decommissioned SCIM status

### P2 — CMDLINE lineage extension (parser EXISTS; join is NEW)
`drydocs/controlm/commands.py` (`parse_command` → `Invocation`/`FileOp`,
`classify_executable`) already decomposes `CMD_LINE`. Extend the classification
with the two launcher shapes seen in production runbooks:
1. **Framework launcher**: `<framework-launcher>.sh -env <env> -pipeline <PIPELINE_GUID>`
   → the GUID is the join key into the pipeline/dataset metadata service.
2. **Config-driven step**: script + `--JSON` / cfg path
   (`.../cfg/<SEAL>-epv-conf.json`) → config path carries the SEAL and the
   parameter file location (both runbook fields).

Then join outward (each is a `:DataAsset` source, per the
`data-context-extractor` skill — platform is a property, never a node):
- **Dataset metadata service** (REST): pipeline GUID → source/target dataset
  GUIDs, versions, zones, entity names, owner SEAL, description, contact.
  A 404 "not in Published State" is itself a hygiene finding.
- **Git `dataset_flow.json`** (per pipeline repo): `entityName`,
  `dataSetGuid`/version, `inputDataSets`, zone — the design-time counterpart.
- Storage layer from job zone + target type: S3 bucket/zone, Glue DB/table,
  HDFS path, Teradata/SQLServer table.

Result: job→dataset `USED`/`GENERATED` edges — the **data lineage** the
condition graph alone can't see.

### P3 — pick the fix batch by repeated failures (NEW)
Small batches, chosen by pain: jobs with repeated failures. Signals, cheapest
first:
- escalation/incident exports for the app's HPSM/SNOW queues (which jobs page)
- bounded `CM_HIST_VW` pulls (indexed predicates + `call_timeout`; see
  query-cookbook §HIST) for rerun counts / `OSCOMPSTAT` per job over a window
- jobs falling into the **common queue** (no SCIM row → failures effectively
  invisible) — highest-value fixes
Output: an ordered batch of *data series* (not individual jobs) to take through
P4–P6.

### P4 — extract the data series: FileWatcher → end provisioning (NEW)
A **data series** = the condition-connected chain from the `_FW` (FileWatcher)
job through its load steps to final provisioning — e.g.
`*_FW → *_RAW → *_ING → *_LD` (zones `RAW → TRUST/Staging → RFND → PROV`).
Walk `:WAS_INFORMED_BY` downstream from each FileWatcher (recursive closure per
query-cookbook §Q4) and capture the whole subgraph: folders (active *and*
stale), jobs, variables, conditions, and each job's P2 lineage joins. Export the
folder XML (the 9.0.21.300 source of record) alongside — it is both the "before"
artifact and the thing the dev team will diff.

### P5 — HITL review + target metadata (uses the review toolkit)
Load the series into the SME review flow (`drydocs/graph_review.py` + gate
pages; every change is a *proposal*, never auto-applied). Standard findings to
generate per series:
- **FileWatcher description enrichment** — insert file-transfer facts into the
  4000-char Description as pipe-delimited `key:value` (the description-metadata
  plan): MFTS route id, drop box path, and the decomposed file-name components
  (`FilePrefix | FileBusinessDate | FileSequence | FileExtension |
  FileCompression | FilePattern`) per the file-name component standard. The
  watch path is reconstructable from the job's `%%` variables
  (`%%DROPBOX/%%PARENT_DIR/%%FILE_NM_PREFIX.%%BUS_DATE...`).
- **FileWatcher post-exec `cat` (NFR)** — every FW watching a token/control
  file must `cat` it post-execution (same `%%` expression as the watch path) so
  the declared incoming TDQ/file count lands in sysout at detection time, not
  after raw-zone ingestion. Machine-checkable; never satisfied by catting the
  data file itself. Standard:
  `knowledge/standards/technology/filewatcher-postexec-token-cat.md`.
- **Variable review** — remove → normalize → supplement (full spec:
  `fix-package.md` §VARS): duplicate `(job, var)` definitions, unreferenced and
  standard-retired vars, redundant job-level shadowing of folder scope; then
  normalize watch paths to the ontology-typed component expression and
  supplement missing standard variables from the file-name decomposition.
- **Naming conformance** — folder/job names validated against the standards
  grammar (`PR<APPCODE>… - <AREA_PRODUCT> - <SEAL> - <PROCESS> - <ZONE> -
  <FREQ>`; job type suffix `_FW/_SFTP/_PROC/…`); `parse_folder_name` is the
  checker. Non-conforming names break the SCIM `EAPPLICATION` derivation — this
  is a routing defect, not cosmetics.
- **SCIM / escalation completeness** — every job in the series resolves through
  the escalation DB (`EAPPLICATION` from the job name, `ECOMPONENT` = numeric
  SEAL, `EWORKGROUPFAILED` = the app's own L2/L3 queue, tier, severity). A job
  with no SCIM row falls to the shared common queue and its failures can be
  missed.
- **Stale-folder disposition** — each stale folder gets a recommendation:
  delete / archive / migrate, with the evidence attached.

### P6 — the fix package → Jira (SoD: we analyze, dev implements)
One package per series — *"Fix for <domain> Data series <X>"* — **added to an
existing Jira** (comment + attachments; we never create the ticket or deploy).
Full artifact contract: `fix-package.md`. Contents:

| Artifact | Content |
|---|---|
| Original folder `.xml` | as exported in P4 (source of record, "before") |
| Original runbook `.xls` + escalation-db `.xls` | what support was handed |
| **Change doc** | each proposed change: what/why/evidence, SME-approved in P5 |
| **Updated `.xml`** | the "after" definition — minimal diff vs the original, never regenerated wholesale (see `fix-package.md` §XML) |
| **Mermaid flow** | the series graph: FW → steps → provisioned targets, with datasets |
| **New runbook** | *generated*, reads as a technical design doc for the series (§RB below) |
| **SCIM / impact doc** | escalation routing, tiers, severity, accountability per job |

The dev team implements the XML change; the runbook regenerates from the graph
after the change lands — that's the automation loop closing.

---

## §RB — runbook field → system of record (the ~95% map)

What today's runbook spreadsheets hold, and where each field actually lives.
This table IS the generator spec: a runbook is a projection of these sources
filtered to one series/SEAL.

| Runbook field (as handed to support) | System of record |
|---|---|
| SEAL id / app name / product / area-product | naming tokens (folder `<SEAL>`, `<AREA_PRODUCT>`) + PAT product catalog + escalation DB `ECOMPONENT` |
| Control-M folder / dependency folders | `CM_DEF_VTAB` + derived `:WAS_INFORMED_BY` (folder grain) |
| Job list, run-as, schedule, frequency, start time | `CM_DEF_VJOB` (`OWNER`, cyclic, calendar cols) |
| Command line / script / jar / config path | `CM_DEF_VJOB.CMD_LINE` → P2 parse |
| Parameter/YML/config file details | P2 parse (config-path extraction) |
| Pipeline id / dataset GUIDs / source+target entities | metadata service + `dataset_flow.json` via P2 join |
| S3 buckets, Glue DB/tables, HDFS zones, target tables | P2 storage joins (zone + target type) |
| File name / pattern for FileWatchers | FW job `%%` variables + file-name component standard (FilePrefix/BusinessDate/…) |
| MFTS routes, drop box, backup/outbound paths | FW description metadata (P5 enrichment) — today: tribal |
| SLO/SLA on ODATE | folder/job metadata + (planned) description key:value |
| SNOW queues L2/L3, distribution lists, tier, severity | escalation DB (SCIM columns) |
| Impact statements (LOB, business, user count, financial) | escalation DB severity/tier + SCIM module/item roll-ups |
| Bitbucket repo / scripts | P2 parse (script paths) + pipeline repo convention |
| Retention, restartable, manual-intervention flags | job/folder metadata + description key:value (P5 target) |
| Hygiene ("document SCIM, ensure L2 routing") | *generated findings* — P5 output, not a manual row |

Fields with no system of record today (MFTS/drop-box details, some retention
policies) are exactly what P5 pushes *into* the Description field — after which
the generator picks them up like everything else.

---

## §GAP — current repo vs the proposed standards (verified 2026-07-02)

| Capability | Status in repo |
|---|---|
| CM_ ingest (folders/jobs/vars/conditions) | **EXISTS** — loaders + staging DDL (see `controlm-db` → `references/ingest.md`) |
| Condition → `:WAS_INFORMED_BY` lineage | **EXISTS** — derived edge + recursive SQL |
| Folder-name grammar parse (PRAOCG / standards) | **EXISTS** — `drydocs/controlm/folder_name.py` |
| CMDLINE parse (invocations, file ops, configs) | **EXISTS** — `drydocs/controlm/commands.py` (Phase C) |
| Launcher-GUID → metadata-service join | **NEW** — P2; needs the REST client + GUID extraction rule |
| File-name component standard (FilePrefix/…/FilePattern) | **PROPOSED** on the website; repo has no decomposer yet — implement as a pure function + `CM_JOB_FILE_NAME_STANDARD`-shaped staging table |
| Description-field key:value metadata | **PLANNED** (3-phase plan exists in docs/memory); P5 is its first consumer |
| Failure-history batch selector | **NEW** — P3; bounded CM_HIST_VW + escalation exports |
| Series extractor (FW → provisioning subgraph + XML) | **NEW** — P4; composes existing pieces |
| SME review gate (proposals, labels, publishing) | **EXISTS** — review toolkit (company side is canonical) |
| Runbook generator (§RB projection → doc + mermaid) | **NEW** — P6; the deliverable |
| SCIM/escalation completeness check | **PARTIAL** — escalation DB is registered; the per-job validation rule is new |

Ontology note: the file-name components map to **DCAT/dcterms** terms
(`dcat:Distribution`, `dcterms:temporal` for the business date,
`dcat:mediaType` for the extension → DistributionRole) — run new
edges/properties through `ontology-mapper` + the HITL gate; extension →
DistributionRole is a **taxonomy** import first, per the layer rules.

Sequencing note: P1 is `feature/oracle-ingestion`'s existing scope. P2 is the
first new build (it unlocks §RB's biggest rows). P3–P6 compose onto it; every
phase ships value standalone, so batch-fix (P3→P6 on one painful series) can
start before P2 is complete using hand-supplied lineage.
