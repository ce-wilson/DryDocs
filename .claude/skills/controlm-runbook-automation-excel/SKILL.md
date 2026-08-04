---
name: controlm-runbook-automation-excel
description: "COMPANY-SPECIFIC: produce or fill the MINIMUM VIABLE Control-M application runbook — the 2-tab Excel workbook (Technical_Details + Control M Job details) support teams exchange at the folder grain. Use when: (1) generating the 2-tab Excel runbook for a Control-M folder/application from the graph, (2) filling or auditing an existing workbook of this shape (which columns the graph answers vs which need SME capture), (3) changing the template itself (template-spec.yaml -> generate_template.py -> controlm-runbook-template.xlsx), or (4) mapping a workbook column to its system of record. Sibling of controlm-runbook-automation (the pipeline/fix-package skill; a future -SDLC sibling owns the long-form Word/markdown run book). Mechanism-only in committed files; FILLED workbooks are Internal and live in internal-local/ or internal/."
---

# Control-M runbook automation — Excel (minimum viable runbook)

**What this is.** Support teams exchange application runbooks as folder-grain
Excel workbooks. The reviewed company example carries seven tabs (Overview,
Technical_Details, Control M Job details, Recovery Details, Outages, Business
Flow, Feedback), but the user ruling (2026-08-04) is that **two tabs are the
minimum viable runbook**:

1. **Technical_Details** — ~48 `Information | Details | Description/comments |
   SOR Flag` rows: identity (SEAL, product, area-product), Control-M folder,
   file-transfer routes, script/jar locations, S3 zone buckets
   (raw/trusted/refined/error), retentions, repo, access, the L2/L3 queue+DL
   contact block, SLA, and escalation DB.
2. **Control M Job details** — one row per job, ~35 columns: job identity and
   description, severity, QR (quantitative resource), source/target DL+queue,
   file-watcher paths (DAT+TOK), command line, dataset/pipeline GUIDs,
   source/target dataset groups + entities, error tables, Snowflake/Glue
   landing, SLO/SLA on ODATE, start/avg times, cyclic + holiday calendar,
   restartability.

**Coverage estimate (verified against the capture, 2026-08-04):** ~90% of the
Job-details tab is graph-derivable — 31 of 35 columns are `graph` or
`graph-partial` in the spec; only Avg Volume, SLO (policy), Job Restartable and
Manual Intervention are purely SME. Technical_Details is roughly half graph,
half SME capture (MFTS routes, retentions, access steps, engagement model).

## Files here

| File | Role |
|---|---|
| `template-spec.yaml` | **Source of truth**: both tabs, every row/column, per-field `source:` (graph / graph-partial / manual) + synthesized OrderHub example values |
| `generate_template.py` | Deterministic-content renderer: spec → xlsx (`poetry run python .claude/skills/controlm-runbook-automation-excel/generate_template.py`) |
| `controlm-runbook-template.xlsx` | The committed 2-tab template with example rows — hand to a team as-is |

Color convention (kept from the source workbook): **yellow-tinted = a human
must capture or confirm it**; untinted = the graph fills it.

## Column → system-of-record map (the generation contract)

When generating for a real folder, fill from these, in this order:

| Workbook field family | System of record in DryDocs |
|---|---|
| Folder, job names, descriptions, start times, CYCLIC, calendar | `ingest-controlm` graph (`:ControlMFolder`/`:ControlMJob`, CM_DEF_VJOB/VTAB) |
| SEAL id/name, Product, Area-Product | K8 folder-grain attribution (`BELONGS_TO_APPLICATION`) + SEAL reference + PAT catalog |
| File-watcher DAT/TOK paths, drop-box location | FileWatcher templates + condition grammar (`TOK-IN-COND…`/`DAT-IN-COND…`) |
| Command line, script/jar, param files | cmd-line staging store (G39 export → G48 resolve → G40 parse) + the G15 dt-launcher arg contract |
| Dataset/pipeline GUIDs, source/target entities, error tables | `pipeline_guid()`/`-dataset` parse + the G17 `dpl_mac` seam (`dataset_flow.json` READS/WRITES) |
| S3 zone buckets | the DPL zone model (RAW→TRUSTED→REFINED + error), dataset registry |
| Snowflake schema/table | G42 Snowflake catalog seam |
| Glue table | G41 Glue base-table inventory seam |
| Severity, L2/L3 queues + DLs, escalation DB | `cm_escalation_db` (EJOBNAME/ECOMPONENT/SCIM routing) + the email-DL contact-point mapping (gated) |
| Avg run time, availability | `cm_avg_run` (P2 gate; `ctlm_id` join) |
| SLA/SLO on ODATE | description-field metadata plan + cm_avg_run — **graph-partial until that plan lands** |
| Bitbucket repo | G24 code-repo seam (graph-partial) |
| FID / Client ID | folder variables (FID_* co-located with SEAL — the K2 candidate source) |
| MFTS routes, retentions, access steps, S3 login commands, engagement model, hygiene, restartability | **SME capture** — no ingested system of record; leave tinted |

Generation is READ-ONLY on the graph. Where a graph value disagrees with what
a team's existing workbook says, that is a **metadata finding** — route it to
the parent skill's failure-driven fix loop (proposal → HITL gate → Jira),
never silently overwrite either side.

## Boundaries

- **Committed files are mechanism-only.** The template + spec carry ONLY
  synthesized values (the OrderHub universe: SEAL 70004, `example.com`,
  zeroed-pattern GUIDs). Real filled workbooks are **Internal**: write them to
  `internal-local/` (machine-local) or `internal/` (repo-internal), never to
  the skill directory.
- The source screenshots this structure was captured from are gitignored in
  the repo root — do not commit them; move them to `internal-local/` if they
  should be kept.
- Header typos in the source workbook were corrected in the spec
  ("Dependecy"→Dependency, "Compute Jason File"→Compute JSON File,
  "Distrubution"→Distribution). If round-tripping INTO a team's existing
  workbook, match THEIR headers verbatim — the spec's `name` is ours, not a
  claim about theirs.
- The five non-minimum tabs (Overview, Recovery Details, Outages, Business
  Flow, Feedback) are out of scope here; the long-form equivalent content
  lives in the SDLC Run Book doc type (`docs/design/templates/
  sdlc-app-runbook.outline.yaml`) and its planned `-SDLC` generator sibling
  (inboxed 2026-08-04).

## Related

- `controlm-runbook-automation` — the parent workflow skill (pipeline phases,
  fix packages, SoR map §RB). This skill is its Excel output format.
- `controlm-db` — CM_ replica schema map and query cookbook for every
  graph-backed column above.
- `sdlc-app-runbook.outline.yaml` — the long-form document twin (Epic L doc
  type SDLC-Runbook).
