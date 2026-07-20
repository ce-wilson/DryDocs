# §TOOLCHAIN — modules, tools, and skills for the lineage model + remediation

Plans the concrete build for `plan.md` P2 (lineage) and P4–P6 (fix batches),
anchored to `MODULE_MAP.md` / ADR 0002. Answering the standing design question
first:

## §DECISION — yes, remediation is its own sub-module

**Fixing Control-M and handing the result to dev teams gets a dedicated
component: `drydocs-remediation` (C1).** This is not new architecture — the slot
is already reserved in `MODULE_MAP.md` ("*(separate module)* `drydocs-remediation`
— C1 — failures → Jira — **no graph write**"). The plan here fills it in. Why it
must be separate:

1. **Different trust direction.** Lineage (C2) *writes the graph* from sources.
   Remediation *reads* the graph and emits **artifacts for humans** (XML, Excel,
   docs). A component that can regenerate folder XML must never hold graph-write
   authority, and vice versa.
2. **SoD is structural, not procedural.** We analyze; the dev team checks in and
   deploys. Putting XML emission in its own no-graph-write component makes the
   boundary test (`test_module_boundary.py`, default-deny) enforce the SoD
   instead of a code-review convention.
3. **XML round-trip is version-locked dirt.** Import/export of 9.0.21.300 folder
   XML is Control-M-version-specific serialization that would contaminate the
   graph model if co-located. Isolated in C1 it can later be extracted into the
   standalone `ctm-remediate` tool (the existing spin-off analysis) without
   touching the graph core.
4. **Components import core only, never each other.** C1 therefore consumes C2's
   *output* through the graph (read-only via `drydocs_core.neo4j`) and the review
   gate's approved-change export — never `import drydocs.lineage`.

## §C2 — `drydocs-lineage` (writes `drydocs`)

Wraps the shared core parser (`drydocs_core.controlm` — `commands.py`,
`paths.py`) exactly as MODULE_MAP anticipates. New modules:

| Module | Does | Notes |
|---|---|---|
| `launcher_rules.py` | extend `classify_executable` classification with the two production launcher shapes: framework launcher (`-pipeline <PIPELINE_GUID>`) and config-driven step (`--JSON` / cfg path) → `PipelineRef`, `ConfigRef`, SEAL hint from cfg filename | pure; rules table data-driven so new frameworks are config, not code |
| `metadata_client.py` | REST client for the dataset metadata service: dataset/versions by GUID | auth **pluggable** (company side reuses the IDAnywhere/token helper pattern; producer ships a fixture-backed stub). 404 "not in Published State" returns a *finding*, not an exception |
| `dataset_flow.py` | reader for per-pipeline `dataset_flow.json` (design-time lineage: entityName, dataSetGuid/version, inputDataSets, zone) | file/dir input; git access stays outside (hand it a checkout) |
| `filename_standard.py` | pure decomposer of the file-name component standard (FilePrefix / FileBusinessDate / FileSequence / FileExtension / FileCompression / FileSuffix / FilePattern) + extension→DistributionRole vocab | feeds a `CM_JOB_FILE_NAME_STANDARD`-shaped staging table; DCAT mapping goes through `ontology-mapper` (taxonomy first) |
| `assembler.py` | three-source reconciliation: runtime (CMDLINE parse) vs design (`dataset_flow`) vs catalog (metadata service), with precedence per `config/precedence.yaml`; emits `:DataAsset` rows + `USED`/`GENERATED` edge proposals; **disagreement = finding** | the lineage "truth engine"; nothing auto-loads — proposals go through the HITL gate |
| loader + CLI | `load-lineage` (append-only cli.py block per the entrypoint exemption) | writes `drydocs` after gate confirmation |

Testing: unit-only with fixtures (sample CMD_LINEs, a canned metadata-service
response, a `dataset_flow.json`) — no network, mirrors the existing
Track-1 style.

## §C1 — `drydocs-remediation` (no graph write)

| Module | Does | Notes |
|---|---|---|
| `xml_io.py` | import existing folder `.xml` → lossless internal model; emit updated `.xml` | **round-trip rules in `fix-package.md` §XML** — never regenerate from the graph alone |
| `series.py` | resolve a data series: read the graph (read-only) for the FW→provisioning subgraph, select the matching folder/jobs subset of the imported XML | graph access via `drydocs_core.neo4j` only |
| `changes.py` | apply an **approved change-set** (exported from the review gate) to the XML model; every change carries what/why/evidence | refuses unapproved changes by construction |
| `runbook_xlsx.py` | generate the runbook in the **previous Excel formats** (format A: vertical Information/Details sheet; format B: job-grain with impact statements) from the §RB projection | openpyxl; producer ships generic templates; the company overlays its real templates (internal) |
| `escalation_xlsx.py` | escalation-db sheet (the SCIM E-columns) — generated **only when routing changes** | same template split |
| `flow_mermaid.py` | series subgraph → mermaid flow (+ optional svg render) | |
| `changedoc.py` | the change doc: original issue, per-change what/why/evidence, before/after XML diff excerpt, approvals | markdown; docx export via the docx skill when a doc deliverable is required |
| `package.py` | assemble the **fix package** folder + the paste-ready Jira comment | layout + contract in `fix-package.md` |
| CLI | `remediate series … / package …` append-only cli.py block | |

**Jira boundary (per the working decision): we do NOT create the Jira.** The dev
team's ticket already exists; `package.py` produces `jira-comment.md` (+ the
attachment set) that a human pastes/attaches into it. No Jira API dependency
now; an optional "post comment to existing issue key" automation is a later,
separate decision.

## §SKILLS — skill layer (no new skill needed yet)

| Skill | Role in this build |
|---|---|
| `controlm-runbook-automation` (this) | owns the plan, this toolchain, and the fix-package contract |
| `controlm-db` | schema map + SQL patterns for every extract C1/C2 need |
| `data-context-extractor` | `:DataAsset` conventions and edge vocabulary for C2's proposals |
| `xlsx` / `docx` | artifact generation mechanics in C1 |
| `reconcile-port` | both components are producer-side builds → company cherry-pick; C1's templates are the expected company-overlay collision |

**Known vendor gap to fill first (reference-librarian task):** the 9.0.21.300
**XML definition schema docs** (export format, `ctmdeffolder`/`ctmdefine` XML) —
already flagged in the BMC `SOURCE-MANIFEST.md` as "the corpus actually worth
ingesting next". `xml_io.py`'s lossless-round-trip contract depends on it;
until acquired, C1 development runs against sanitized sample exports.

## §ORDER — build sequence (each step ships value)

1. **C2 `launcher_rules` + `filename_standard`** — pure functions, unit-tested,
   no dependencies; immediately improve CMDLINE facts and FW descriptions.
2. **C2 `dataset_flow` + `metadata_client` (stubbed) + `assembler`** — lineage
   proposals flowing through the gate; company side wires real auth at port.
3. **C1 `xml_io` (+ schema docs acquisition) + `series`** — import/inspect real
   series; "before" artifacts become producible.
4. **C1 `changes` + `package` + generators** — first end-to-end fix package on
   one painful series (the P3 batch selector can be a manual list until then).
5. **P3 selector last** — it only ranks work; steps 1–4 already let a
   hand-picked series flow end to end.
