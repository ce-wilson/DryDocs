# Control-M Remediation — Spin-off Feasibility, Effort & Templated Plan

**Corpus:** INTERNAL (production-support initiative). **Status:** 🔵 PLANNING — drafted 2026-06-11.
**Author/owner:** Production Support (us). **Implementer of changes:** Dev team (separate, via Jira).

---

## 1. Context & the governing constraint (Segregation of Duties)

We are **production support**. The legacy hazards (e.g. the [concat-dot variable pattern](description-field-metadata-plan.md)) were created by a **dev team**. We want to fix/modernize them, but **SoD prevents us from checking in or releasing changes to the Control-M definitions themselves.**

**Therefore the whole initiative must be read-only toward production Control-M.** What we *can* do, fully within our remit:
- **Read** Control-M definitions (XML exports / `psgmgr` tables).
- **Analyze & document** legacy behavior.
- **Author & validate** a greenfield (modernized) design — *as artifacts*, proven correct offline.
- **Package** an implementation spec as a **Jira** for the dev team, who hold check-in/release rights.

We never deploy. The standalone tool is an **analyzer + proposal generator**, never a writer. This is the design axis everything else hangs on.

> **The elegant part:** the normalization engine we already built (offline AutoEdit resolver + command parser) lets us **prove a greenfield definition resolves to the *same* runtime behavior as legacy** — watched filenames, dependencies, commands — *without deploying anything*. That equivalence proof is the SoD-compliant way to "fix it ourselves": we do the hard correctness work; the dev team does a low-risk, pre-validated check-in.

---

## 2. Feasibility assessment

**Verdict: feasible, with a clean seam.** Grounded in the actual coupling (measured 2026-06-11):

| Finding | Evidence | Implication |
|---|---|---|
| `controlm/` is a near-leaf | Only imports `ControlMVariableRow` from `..models` | Core lifts out with one model dependency to sever/move |
| Graph loaders are *consumers*, not internals | `loaders/controlm*.py` (~189 LOC) import the package; nothing in the package imports them | Loaders **stay in DryDocs**; they read our staging output |
| Staging tables are the contract | `controlm_staging_ddl.sql` (8 STG_ tables) is the normalization output | **The split point is the STG_ layer**, a data contract — not a code-untangling exercise |
| Docs are additive | `vendor-bmc/` (26 files), `internal-standards/` (5) are pure prose | `git mv` / copy; zero code risk |

**Risk to feasibility:** low for the core engine; the real effort is **new** greenfield-authoring + Jira-packaging tooling that doesn't exist yet (today the pipeline stops at staging/analysis).

---

## 3. Target architecture (standalone project — working name `ctm-remediate`)

**Primary I/O is XML.** Import the **legacy** definition XML → normalize/analyze → export a **greenfield** definition XML — the greenfield XML *is* the artifact the dev team imports via the Jira. The Oracle (`psgmgr.*`) extract and the Neo4j graph are the **corroborating source of truth** (a cross-check, not the delivery medium): a legacy XML must reconcile with the loaded snapshot, and a greenfield XML is exported only after the offline equivalence proof **and** the graph re-derivation agree — letting *both* the legacy and greenfield XML stand as source of truth.

```
        IMPORT (read-only)                 AUTHOR / VALIDATE                 EXPORT → HANDOFF
┌────────────────────────┐   ┌──────────────────────────────────────┐   ┌──────────────┐
│ LEGACY definition XML  │   │  ctm-remediate (standalone)            │   │ GREENFIELD   │
│  (Control-M export)    │──▶│  1. import/parse legacy XML            │──▶│ def XML =    │
│  • psgmgr.* tables     │   │  2. classify variables (taxonomy)      │   │  legacy +    │
└────────────────────────┘   │  3. resolve offline (AutoEdit sim)     │   │  greenfield +│
                             │  4. parse commands / paths / facts     │   │  equivalence │
   STG_ tables  ◀────────────│  5. document LEGACY (current state)    │   │  evidence    │
   (data contract)           │  6. design GREENFIELD (target state)   │   └──────┬───────┘
        │                    │  7. PROVE equivalence (legacy≡green)   │          │
        ▼                    │  8. emit Jira package                  │          ▼
┌────────────────────────┐   └──────────────────────────────────────┘   ┌──────────────┐
│ DryDocs (stays)         │                                              │  Dev team    │
│  • graph loaders        │  consumes STG_ + greenfield facts            │  implements  │
│  • PAT/SEAL ontology    │                                              │  & releases  │
│  • Neo4j                │                                              └──────────────┘
└────────────────────────┘
```

Steps 2–4 exist today (C3 Phases A/B/C). **New build:** legacy XML **import/parse** (1) and greenfield XML **export** (8), the legacy documenter (5), greenfield design (6), and the equivalence prover (7). DryDocs keeps the graph/ontology and consumes the same staging output it does now — **no behavior change for DryDocs**.

### Definition interchange format — XML now, JSON later

9.0.21.300 imports/exports job & folder *definitions* as **XML** → the spin-off's primary source and sink (legacy in, greenfield out; the greenfield XML is the Jira artifact). **XML is being phased out:** BMC's SaaS direction replaces it with the **JSON Automation API** (name-as-key notation; see `vendor-bmc/controlm-api-*.md`). Build import/export behind a **format-agnostic interface** so a JSON backend slots in at platform migration — never hardcode XML assumptions. *(The same note is in the engine base code, `drydocs/controlm/__init__.py`.)*

---

## 4. What moves vs. what stays

| Asset | LOC | Move to `ctm-remediate` | Stays in DryDocs | Notes |
|---|---|---|---|---|
| `drydocs/controlm/` (8 modules) | 1,696 | ✅ | | Engine core (taxonomy, resolver, parser, staging, facts, paths) |
| `models/controlm.py` (`ControlMVariableRow` etc.) | 418 | ✅ (or shared lib) | | The one upward dep; move with core or extract a tiny shared models pkg |
| `loaders/sql/controlm_variables.sql`, `ddl/controlm_staging_ddl.sql` | — | ✅ | | Extract query + staging DDL = the read + output contract |
| **XML import / export** (legacy in, greenfield out) | — | ✅ **NEW** | | Net-new — the primary I/O + the Jira artifact. Behind a format-agnostic interface (JSON backend later). Oracle/graph reconcile both directions |
| `adapters/` (csv, oracle) | small | copy / shared lib | ✅ | Generic; vendor a copy or publish a shared internal lib |
| `loaders/controlm*.py` (6) | 189 | | ✅ | Graph loaders — consumers of staging; DryDocs-owned |
| `tests/unit/test_variable_*`, `test_command_parser`, `test_controlm_*` | (in 3,678) | ✅ | | Engine tests follow the engine |
| `vendor-bmc/` (26 docs) | — | ✅ | | BMC capability corpus (validates the model) |
| `internal-standards/` (5 plans) | — | ✅ | | Conformance corpus (naming, DC time, metadata, calendar, this plan) |
| `docs/controlm-c3-normalization-status.md` | — | ✅ | | Runbook |
| `cli.py` (Control-M commands) | — | split | ✅ | Carve `analyze-variables` / `ingest-controlm` into the new CLI; leave graph commands |
| PAT/SEAL ontology, `relationship_vocabulary.yaml`, schema, `neo4j_client` | — | | ✅ | Not Control-M; the SEAL join is via staging facts |

**Integration contract after split:** `ctm-remediate` writes STG_ tables + a `STG_APP_FACT`-style SEAL/metadata feed; DryDocs loaders read them. Versioned schema = the interface.

---

## 5. Effort estimate (indicative — refine with dev team)

Sizing basis: measured LOC + "is it new or a move." Ranges, not commitments.

| Workstream | Size | Rough effort | Confidence |
|---|---|---|---|
| **A. Extract engine** (package + models + SQL + tests → new repo; sever model dep; pyproject/CI; vendor adapters) | M | 1–2 wk | High — it's a near-leaf |
| **B. Read-only ingest hardening** (XML-export path, not just CSV/psgmgr; confirm `psgmgr.*` table names — currently unverified) | M | 1–2 wk | Med — depends on XML export access |
| **C. Legacy documenter** (step 5: emit current-state report per job/folder/app from resolved model) | M | 1–2 wk | Med |
| **D. Greenfield authoring + templates** (step 6: canonical var names, direct paths, Description metadata, SEAL var; the *template engine*) | L | 3–5 wk | Low — most new design |
| **E. Equivalence prover** (step 7: assert greenfield ≡ legacy resolved behavior; diff watched paths/deps/commands) | M | 2–3 wk | Med — builds on resolver/parser we own |
| **F. Jira packager** (step 8: render the ticket template + evidence; optional Jira API) | S–M | 1 wk | High |
| **G. Docs move + cross-links + provenance preserved** | S | 2–3 days | High |
| **Total** | | **~9–16 wk** one engineer, phaseable | |

**Cheapest proof of value first:** a thin vertical slice — one real legacy FileWatcher (the concat-dot job) → documented → greenfield authored → equivalence proven → one Jira. That exercises A+C+E+F minimally and de-risks the rest. ~2–3 wk.

---

## 6. The templated remediation workflow (repeatable, per unit)

A "unit" = a job, a folder, or a job *pattern*/application. Run the same 5 gates each time. The [concat-dot fix](description-field-metadata-plan.md) is the worked example.

| Gate | Action | Output artifact | SoD-safe? |
|---|---|---|---|
| **1. Capture** | Pull the legacy definition (read-only) | `legacy/<unit>.md` — raw definition + metadata | ✅ read |
| **2. Validate** | Classify variables, resolve offline, flag hazards (`value_is_delimiter` dot-smuggling, name drift, indirection, unresolved refs) | Hazard report + **resolved behavioral baseline** (watched filenames, deps, commands) | ✅ analyze |
| **3. Design** | Author greenfield: canonical names, direct paths, Description key:value metadata, declared `SEAL` var | `greenfield/<unit>.md` — proposed definition | ✅ author |
| **4. Prove** | Resolve greenfield offline; assert it produces the **same runtime artifacts** as the baseline (or document intended deltas) | Equivalence report (legacy ≡ greenfield, or justified diff) | ✅ validate |
| **5. Package** | Render Jira (below) with before/after + acceptance criteria + rollback + equivalence evidence | Jira ticket → dev team | ✅ handoff |

### Jira ticket template (fill-in)

```
Title:        [Control-M Remediation] <unit> — <one-line: e.g. eliminate dot-smuggling vars>
Component:    Control-M / <application code, e.g. PRARA> / SEAL <id>
Requested by: Production Support (analysis pre-validated; implementation only)

── Why ──────────────────────────────────────────────
<legacy hazard, plain language. e.g. "FILE_NM_SUFFIX='.' smuggles a literal
dot through Control-M's concatenation operator; brittle and undocumented.">

── Scope ────────────────────────────────────────────
Folder(s):    <name(s)>          Job(s): <name(s)>
Data center:  <P0xx-Exxxx-...>   SEAL:   <id> (<application>)

── Change (BEFORE → AFTER) ──────────────────────────
Variables:    <table of removed/renamed/added, before→after>
Watch/cmd:    <legacy template>  →  <greenfield template>

── Equivalence evidence (attached) ──────────────────
Resolved watched filename:  legacy = <...>   greenfield = <...>   ✅ identical
Resolved dependencies/cmds: <diff or "identical">
Tool:        ctm-remediate vX.Y, offline resolver (AutoEdit-equivalent)

── Acceptance criteria ──────────────────────────────
[ ] Greenfield definition checked in to <env path>
[ ] Resolves to the filename/behavior above (re-verify with ctm-remediate)
[ ] No change to ODATE/scheduling/SEAL associations
[ ] <smoke test / first-run watch confirmed>

── Rollback ─────────────────────────────────────────
Restore prior version via Control-M Changes History (180-day window).

── Out of scope / notes ─────────────────────────────
<e.g. var.text dot edge case not addressed; .. escaping; etc.>
```

---

## 7. Risks & open questions

1. **`psgmgr.*` table names unverified** (flagged in git-readme) — confirm the extract source before B.
2. **XML export access** — do we have read access to definition XML exports, or only the client UI? Determines ingest path (B).
3. **Shared `adapters`/`models`** — vendor a copy vs. publish an internal shared lib; copy is simpler, lib avoids drift. Recommend copy now, lib later.
4. **Staging-contract versioning** — once split, DryDocs and `ctm-remediate` must agree on STG_ schema; version it explicitly.
5. **Greenfield naming reconciliation** — how the modern long auto-generated names reconcile with [PRAOCG](folder-naming-convention.md) (open item there).
6. **Dev-team intake** — confirm the Jira template fields match their definition-of-ready; co-design gate 5 with them.
7. **Resolver edge** — `var.text` dot handling + `..` escaping are not covered (see resolver docstring); document per-unit in "out of scope" until confirmed.

---

## 8. Phasing / milestones

- **M0 — Decision & PoC (2–3 wk):** thin vertical slice on the concat-dot job (A+C+E+F minimal) → one real Jira. Proves the model end-to-end and the SoD handoff.
- **M1 — Engine spin-off (1–2 wk):** extract `controlm/` + models + SQL + tests into `ctm-remediate`; DryDocs consumes staging unchanged; docs moved.
- **M2 — Documenter + Prover (3–5 wk):** robust legacy documentation + equivalence proving across job types.
- **M3 — Greenfield templates + Jira packager (3–5 wk):** the modernization template engine + repeatable Jira output; batch through an application (e.g. SEAL 111027 PRARA).
- **M4 — Scale:** run per application/data center; feed greenfield facts back to the DryDocs graph.

Related: [[project-drydocs-scrape-two-corpus]], [[project-controlm-xml-not-json]], [[project-description-metadata-plan]], [[project_controlm_c3_normalization]], [[project-folder-naming-praocg]]
