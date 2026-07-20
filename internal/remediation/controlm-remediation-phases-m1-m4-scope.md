# M1–M4 Phase Scopes (Control-M Remediation)

**Corpus:** INTERNAL. **Status:** 🔵 SCOPED — 2026-06-11. **Branch:** `controlm-spinoff`.
**Parent:** [controlm-remediation-spinoff-plan.md](controlm-remediation-spinoff-plan.md). **Precedes:** built on [M0 PoC](controlm-remediation-m0-poc-scope.md).
Effort figures are indicative, one engineer; refine after M0.

---

## M1 — Engine spin-off (~1–2 wk)

**Objective:** lift the Control-M engine into the standalone `ctm-remediate` repo with **no behavior change to DryDocs**; the STG_ staging tables become the versioned contract between them.

| Task | Detail | Exists vs New |
|---|---|---|
| Repo init | Seed `ctm-remediate` from the `controlm-spinoff` branch (history-light export) | new |
| Move engine | `drydocs/controlm/` (8 modules) → `ctm-remediate` | move |
| Resolve model dep | Move `models/controlm.py` (carries `ControlMVariableRow`) **or** extract a tiny shared-models package | decision (§below) |
| Move SQL | `controlm_variables.sql`, `ddl/controlm_staging_ddl.sql`, + read queries (jobs/folders/conditions) | move |
| Move tests | `test_variable_classifier/resolver/staging`, `test_command_parser`, `test_controlm_models` | move |
| Adapters | Copy `adapters/` (csv, oracle) into `ctm-remediate` | copy |
| CLI carve | `analyze-variables`, `ingest-controlm` → `ctm-remediate` CLI; leave graph commands in DryDocs | split |
| Doc corpora | `vendor-bmc/` + `internal-standards/` move to `ctm-remediate` (they ARE the Control-M reference) | move |
| Packaging | `pyproject.toml`, CI (lint+test), version pin | new |
| DryDocs side | Repoint graph loaders to read staging via the contract; confirm DryDocs suite stays green | modify |

**Decisions:** (a) **shared models** — recommend *copy now* (simplest, no infra), extract a published lib only if drift bites; (b) **doc ownership** — `ctm-remediate` owns the corpora; DryDocs links if needed.

**Info needed:** confirmed `psgmgr.*` table names; CI runner availability; (if lib route) an internal package registry.

**Acceptance:** `ctm-remediate` suite green; DryDocs suite green; **staging output byte-identical to pre-split** for the M0 unit (the regression oracle).

---

## M2 — Documenter + Equivalence Prover + Standards Registry (~3–5 wk)

**Objective:** generalize gates 1–2 and 4 beyond the single FileWatcher, and build the **machine-checkable standards registry** (the M0 gap).

| Workstream | Detail |
|---|---|
| **Legacy documenter** | Per-job-type current-state extraction: FileWatcher (paths), OS/Command (cmd + pre/post), File Transfer, Job dependencies (in/out conditions), scheduling. Resolved-behavior report per unit. |
| **Equivalence prover** | Compare legacy↔candidate across: watched/transfer paths, in/out conditions (dependency graph), command strings, scheduling/ODATE. Structured diff + verdict. |
| **Resolver completeness** | Land the `var.text` dot rule (from M0), `..` literal-escape, confirm env-variant + system-func coverage; regression corpus from real folders. |
| **Standards rules registry** | Encode prose standards as checks: PRAOCG naming regex, DC-default-time awareness, required Description keys, `SEAL` var presence, no dot-smuggling (`value_is_delimiter`), canonical var-name map, name-drift detector. Output: per-unit conformance report. |

**Info needed:** job-type distribution across the estate (we have app-code counts, not type mix); ground-truth resolved samples per job type; **ratified** standards rules (esp. Description key list + required-vs-optional); the internal **job-naming** standard.

**Acceptance:** documenter + prover + standards-check run across a representative multi-type sample with validated output; resolver regression corpus green.

---

## M3 — Greenfield Templates + Jira Packager (~3–5 wk)

**Objective:** turn validation into *generation* — author greenfield definitions from templates and emit dev-ready Jiras at scale; batch one whole application.

| Workstream | Detail |
|---|---|
| **Greenfield template engine** | Apply: variable canonicalization (DRPBX_DIR→DROPBOX_DIR etc.), path directization (kill indirection + dot-smuggling), Description key:value metadata authoring, `SEAL` var injection, naming per the (ratified) standard. |
| **Jira packager** | Render the ticket template + equivalence evidence per unit; optional Jira REST integration; batch/rollup view. |
| **Batch run** | Drive a full application — **SEAL 111027 (PRARA, HL Advice & Reporting)** is the natural first (M0's app, ~236 jobs in P032 + others) — produce a Jira set with per-unit equivalence proofs. |

**Info needed:** ratified greenfield templates (var naming map, Description keys + escaping, job-naming standard); **dev-team Jira definition-of-ready** (confirmed, not proxy); change-management batching cadence.

**Acceptance:** a batch of dev-accepted Jiras for one application, each carrying equivalence evidence; measurable hazard-fix count.

---

## M4 — Scale & Graph Enrichment (ongoing)

**Objective:** operationalize per application / data center, and feed greenfield facts back into the DryDocs knowledge graph.

| Workstream | Detail |
|---|---|
| **Operate** | Per-app / per-DC runs; backlog tracking; metrics (units scanned, hazards found/fixed, Jiras raised/landed). |
| **Prioritize** | By volume + risk. Volume signal (2026-06-11 counts): `PRDCL` ~8,850 (P032), `PRICD` ~6,800 (P012+P014), `PRIOS` ~4,300 — but platform-coded (PRDCL/PRAOC) jobs lack a direct SEAL, so sequence app-coded estates first where conformance value is clearest. |
| **Graph feedback** | Emit greenfield facts (SEAL, Description metadata, delivery/route/queue) to DryDocs loaders → enrich the ontology graph; closes the structured↔unstructured loop. |

**Info needed:** remediation prioritization policy (volume vs risk vs SEAL-coverage); reporting/dashboard requirements; sustained change-management throughput with dev.

**Acceptance:** steady-state throughput; graph enrichment live; backlog burn-down visible.

---

## Cross-phase decisions to lock early

1. **Shared models/adapters:** copy vs published lib (recommend copy → lib later).
2. **Doc-corpus ownership:** `ctm-remediate` owns `vendor-bmc/` + `internal-standards/`.
3. **Staging contract versioning:** explicit schema version on STG_ tables; DryDocs pins it.
4. **Standards as code:** the registry (M2) is the single source for both validation *and* greenfield generation — author it once.

Related: [[project-controlm-remediation-spinoff]], [[project_controlm_c3_normalization]], [[project-description-metadata-plan]], [[project-folder-naming-praocg]]
