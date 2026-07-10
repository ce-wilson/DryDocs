# Standards Rules Registry (machine-checkable) — DRAFT

**Corpus:** INTERNAL. **Status:** 🟠 DRAFT — 2026-06-11; governance rules added 2026-06-17. **Branch:** `controlm-spinoff`.
The prose standards turned into a **checkable rule set** — the single source for both *validation* (Gate 2) and *greenfield generation* (Gate 3). Each rule: how the engine detects it, severity, the standard it comes from, the greenfield action, and ratification status. Built in M2; seeded here. **R1–R12** = resolver/naming/metadata core; **R13–R28** = the tier ③/④ governance standards (escalation routing, self-heal, critical-batch tiering, NFR catalog, FW time-limit, command-line/canonical-variables, artifact-source security) digested from the [governance/](governance/) corpus; **R29** = the first 🟣 greenfield *recommendation* rule (job numbering — [D5](governance/greenfield-recommendations.md)).

**Status legend:** ✅ ratified · 🟡 provisional (observed, not signed off) · ❓ open (needs SME).
**Severity:** 🔴 must-fix · 🟡 should-fix · ⚪ advisory.

---

## R1 — No dot-smuggling (punctuation-as-value)
- **Check:** variable `value_is_delimiter == True` (value is wholly punctuation, e.g. `.`, `_`, `/`).
- **Engine:** `classify_variable` flag (live). **Sev:** 🔴 **Status:** ✅
- **Source:** [description-field-metadata-plan](description-field-metadata-plan.md) · resolver concat-dot rule.
- **Greenfield:** remove the smuggle; emit the literal in-place once the dot rule (R10) is confirmed. Detection is name-agnostic (catches every alias).

## R2 — Variable-name canonicalization / no name-drift
- **Check:** variable name not in the canonical map (e.g. `DRPBX_DIR` vs canonical `DROPBOX_DIR`; `img_path`/`IMAGE` → `ETL_ARTIFACT_URI`); same concept spelled multiple ways across the estate.
- **Engine:** name-drift detector against canonical map; `variables.py FACT_REGISTRY` alias rollup (WARN on non-canonical, never silent-merge). **Sev:** 🟡 **Status:** 🟡 (B4 — **ratification source now exists**: [governance/command-line-and-variables-standard](governance/command-line-and-variables-standard.md) §1)
- **Greenfield:** rename to canonical (uppercase ASCII, case-sensitive lookup).

## R3 — No deep indirection for near-static values
- **Check:** N variables composing a path/string that is effectively static + a system token (legacy FileWatcher used 5).
- **Engine:** resolver — count distinct user-var refs in a composed value vs literal content. **Sev:** 🟡 **Status:** 🟡
- **Greenfield:** collapse to a direct path + the one dynamic token (`%%$ODATE`).

## R4 — Folder name conforms to PRAOCG
- **Check:** 6-char positional prefix `P`(env)`R`(LOB)`AOC`(app/platform)`G`(type); regex on the prefix; frequency suffix at end.
- **Engine:** naming validator (M2). **Sev:** 🟡 **Status:** 🟡 (B5 — env/LOB code lists open)
- **Source:** [folder-naming-convention](folder-naming-convention.md). **Greenfield:** flag non-conforming; do NOT auto-rename (high blast radius) — propose only.

## R5 — Platform vs application code awareness
- **Check:** position 3–5 is a *platform* code (PRAOC, PRDCL) → folder name does NOT imply a business application/SEAL.
- **Engine:** code registry lookup. **Sev:** ⚪ (informational, prevents false joins) **Status:** 🟡
- **Greenfield:** never derive `:Application`/SEAL from a platform-coded name; require R7.

## R6 — Effective run time resolvable
- **Check:** folder declares a time; if not, the DC name supplies it (`E####`, EST). Flag if neither yields a time.
- **Engine:** scheduling/DC resolver. **Sev:** ⚪ **Status:** ✅ (rule), 🟡 (full DC time table)
- **Source:** [data-center-naming-convention](data-center-naming-convention.md).

## R7 — SEAL declared on the object
- **Check:** folder variable `SEAL` present (primary source). Fallback hierarchy: folder var → `cm_escalation_db.ECOMPONENT` (strip `.00`) → pipeline-derived → name-embedded (weak).
- **Engine:** SEAL resolver. **Sev:** 🟡 (mandatory? = B6) **Status:** ❓
- **Source:** [description-field-metadata-plan](description-field-metadata-plan.md). **Greenfield:** inject `SEAL=<id>` as a folder variable.

## R8 — SEAL format
- **Check:** integer, **variable width** (legacy 5-digit e.g. 89211, current 6-digit e.g. 110865/111027); normalize (strip `.00` from `ECOMPONENT VARCHAR2(40)`), compare as int.
- **Engine:** SEAL parser. **Sev:** 🔴 (correctness of joins) **Status:** ✅
- **Greenfield:** store normalized.

## R9 — Description carries structured metadata
- **Check:** Description is pipe-delimited `key: value` with required keys present (provisional: `datasetSeriesName`, `SeriesSLA`, + job-type keys); split on FIRST `:`; whitespace-tolerant.
- **Engine:** Description parser (M2). **Sev:** 🟡 **Status:** 🟡 (B2 — key list + escaping to ratify)
- **Source:** [description-field-metadata-plan](description-field-metadata-plan.md). **Greenfield:** author the metadata block.

## R10 — Concatenation-dot correctness
- **Check:** `.` between `%%var.%%var` is a consumed delimiter; `var.text` rule **pending B1**.
- **Engine:** resolver (var.var live; var.text open). **Sev:** 🔴 **Status:** 🟡 (var.var ✅, var.text ❓)
- **Source:** resolver docstring + [m0 worked example](m0-poc-worked-example.md). **Greenfield:** depends on confirmed rule.

## R11 — Source vs processing SEAL (two-SEAL flows)
- **Check:** File Watchers carry the *source* app's SEAL; processing folders the *processing* app's SEAL — model as distinct edges, not one association.
- **Engine:** graph-load policy (M4). **Sev:** ⚪ **Status:** 🟡
- **Source:** [description-field-metadata-plan](description-field-metadata-plan.md).

## R12 — Internal job-naming standard
- **Check:** job name conforms to the internal job-naming convention (the job-level analogue of PRAOCG).
- **Engine:** naming validator. **Sev:** 🟡 **Status:** ❓ (B3 — standard not captured; only BMC generic `AAA-TTT-FFFFFFFF`)
- **Greenfield:** propose conforming name.

---

## Governance-derived rules (R13–R29, from the tier ③/④ standards + D5 recommendations)

Surfaced while digesting the DAT/HLT governance corpus (2026-06-17). Provisional until ratified with DAT SRE + HLT.

## R13 — Name token matches derived intent (the FW/API gotcha)
- **Check:** the job-type token (`_FW`, `_PREPROC`, …) agrees with behavior **derived from the resolved flow** (predecessor graph + command parse). Flag where a `_FW` is actually API-triggered via a predecessor.
- **Engine:** ontology intent-deriver (M4) vs name token. **Sev:** 🟡 **Status:** 🟡
- **Source:** [governance/hlt-naming-standard §5](governance/hlt-naming-standard.md) · [README §4](governance/README.md). **Greenfield:** retoken to match intent (e.g. `_APIPOLL`) or flag node.

## R14 — Escalation defaults to the owning dev queue
- **Check:** a job with no/incomplete SCIM entry must route to the **owning dev queue (`C3…`/`CCB_HLT_SENG_*`)**, never silently to platform L1 `C1CCBDATAECO`.
- **Engine:** escalation-routing resolver over `CM_ESCALATION_DB` LEFT JOIN. **Sev:** 🟡 **Status:** ❓ (org adoption unresolved — DAT/HLT dialogue)
- **Source:** [governance/escalation-scim-reference §5](governance/escalation-scim-reference.md) · [governance/scim-hpsm-queue-registry §3](governance/scim-hpsm-queue-registry.md). **Greenfield:** emit owning-dev default routing.

## R15 — EAPPLICATION ↔ name validation (column-Y gate)
- **Check:** `EAPPLICATION` (= `SUBSTR(JOB_NAME,2,3)`) matches the naming convention; non-conforming name fails SCIM upload (column-Y).
- **Engine:** naming validator + SCIM derivation. **Sev:** 🔴 (blocks shipping) **Status:** ✅ (mechanism is enforced today)
- **Source:** [governance/escalation-scim-reference §2/§4](governance/escalation-scim-reference.md). **Greenfield:** pre-commit gate — name must pass before Jira raised.

## R16 — Single canonical metadata source (Description ≡ SCIM special-instructions ≡ structured-log fields)
- **Check:** the pipe-delimited metadata (Folder/Flow/SLA-EST/Restartable/Full-Delta/Impact/URL) is authored once and projected; no hand-maintained divergence between the Description and `ESPECIALINSTRUCTIONS`.
- **Engine:** metadata reconciler (M4); `variables.py FACT_REGISTRY` canonical/alias model. **Sev:** 🟡 **Status:** 🟡
- **Source:** [governance/escalation-scim-reference §3](governance/escalation-scim-reference.md) · [governance/nfr-catalog §2](governance/nfr-catalog.md) · [governance/command-line-and-variables-standard §1](governance/command-line-and-variables-standard.md). **Greenfield:** emit once → Description + SCIM + log key-set + canonical var.

## R17 — Self-heal eligibility is derived, not defaulted
- **Check:** mark self-heal-eligible **only** when (a) re-run is idempotent/safe **and** (b) no predecessor-rerun dependency. **Exclude** Info1/DB-function jobs (index/truncate) and predecessor-dependent jobs. `VR:` code present ⇒ must actually be recoverable.
- **Engine:** flow + command classifier. **Sev:** 🔴 (unsafe re-run risk) **Status:** 🟡
- **Source:** [governance/critical-batch-and-self-heal §3](governance/critical-batch-and-self-heal.md). **Greenfield:** `VR:` only when truly configured; else runbook in Description.

## R18 — Severity sane (business impact, not blank/P99)
- **Check:** `ESEVERITYFAILED ∈ {P2…P6}` set by **business impact**; flag blanks, `Missing Item/Module`, and P99/below-tier criticals.
- **Engine:** SCIM validator. **Sev:** 🟡 **Status:** 🟡
- **Source:** [governance/critical-batch-and-self-heal §1/§4](governance/critical-batch-and-self-heal.md).

## R19 — Tier matches the critical-batch dashboard
- **Check:** `EITEMFAILED` (Tier-1/2/3) for a critical-batch job matches `go/dat6am`; ~1k criticals currently mis-tiered below P2.
- **Engine:** dashboard-vs-SCIM diff. **Sev:** 🟡 **Status:** 🟡
- **Source:** [governance/critical-batch-and-self-heal §1](governance/critical-batch-and-self-heal.md).

## R20 — Exactly one SCIM per job (1:1 integrity)
- **Check:** each Control-M job maps to **exactly one** `CM_ESCALATION_DB` row (no orphan, no duplicate).
- **Engine:** join-cardinality check on `EJOBNAME`. **Sev:** 🔴 **Status:** ✅ (stated principle)
- **Source:** [governance/scim-hpsm-queue-registry §5](governance/scim-hpsm-queue-registry.md).

## R21 — Structured-log fields present
- **Check:** job/pipeline emits the mandatory key set (`PipelineId · Component · JobId · Event · Exception · ErrorCode · OrderDate · BusinessDate · OwnerSealId · Service · Path · Level · Userid · Message · Timestamp`); `ErrorCode` indexable.
- **Engine:** log-contract check (evidence-able). **Sev:** 🟡 **Status:** ❓ (DAT NFR — observability, not yet enforceable from definitions alone)
- **Source:** [governance/nfr-catalog §2](governance/nfr-catalog.md).

## R22 — Runbook completeness (non-self-heal jobs)
- **Check:** non-self-heal jobs carry SLO/SLA impact, SOR/downstream, support contacts, recovery steps (in Description per column-T discipline).
- **Engine:** Description-metadata validator. **Sev:** 🟡 **Status:** 🟡 (pairs with R17)
- **Source:** [governance/nfr-catalog §1/§5](governance/nfr-catalog.md).

## R23 — Monitoring binding declared (no observability orphan)
- **Check:** every job declares its monitoring product + dashboard (Grafana/Splunk) — the monitoring analogue of the L1-default gap.
- **Engine:** metadata presence check. **Sev:** ⚪ **Status:** ❓
- **Source:** [governance/nfr-catalog §1](governance/nfr-catalog.md).

## R24 — Lifecycle / decommission state valid
- **Check:** lifecycle designation (`PRPL`/`VERF`/`Decommissioned`) consistent across name, SCIM `EWORKGROUP`, and folder location; decommissioned ⇒ **Dev Resolver Group** assigned.
- **Engine:** cross-source consistency check. **Sev:** 🟡 **Status:** 🟡
- **Source:** [governance/nfr-catalog §4](governance/nfr-catalog.md) · [governance/dat-naming-standard §2b](governance/dat-naming-standard.md).

## R25 — NFR evidence gate (high-risk NFRs)
- **Check:** high-Operation-Risk NFRs (Monitoring, Alerting, Error Handling, Restartability, Escalation matrix) have **evidence** before a job is "greenfield-complete" — the ICDW *Evidence Required* discipline generalized.
- **Engine:** evidence aggregator over R14/R17/R21/R23. **Sev:** 🟡 **Status:** ❓
- **Source:** [governance/nfr-catalog §3/§5](governance/nfr-catalog.md).

## R26 — File-Watcher time limit bounded
- **Check:** every cloud File-Watcher job has a **time limit between 1 and 240 min (4 hr max)** and is **never 0/unlimited**; timeout sized to AVG SOR arrival, not a blanket max.
- **Engine:** FW-param validator (reads the FW time-limit). **Sev:** 🟡 **Status:** 🟡
- **Source:** [governance/dat-naming-standard §2c](governance/dat-naming-standard.md) (FW rules). **Greenfield:** set bounded time limit; FW only in ONPM/TRUST zone folders; fail+ticket-L2 on missed SLO.

## R27 — Command-line conforms to the per-framework template
- **Check:** the job command line matches the framework's canonical template (Python/Java/AbInitio/Informatica) with the **required canonical-variable declarations** present; no custom wrapper; `-p` order-prefix + DPL pipeline-id hardcoded; no hardcoded host/server.
- **Engine:** command-line template matcher + `m7-verify` (`NF-VAL-1..7`). **Sev:** 🟡 **Status:** 🟡 (authoritative template exists)
- **Source:** [governance/command-line-and-variables-standard §2](governance/command-line-and-variables-standard.md) + NFR-CTM-301. **Greenfield:** emit the framework template (Gate-3 generation target).

## R28 — Artifact source is a JPMC-approved repository (NF-SEC-2)
- **Check:** `ETL_ARTIFACT_URI` resolves to a JPMC-approved artifact repository (no arbitrary/external source) — supply-chain guard.
- **Engine:** verifier URI-allowlist check. **Sev:** 🔴 (security) **Status:** 🟡
- **Source:** [governance/command-line-and-variables-standard §5](governance/command-line-and-variables-standard.md) (NF-SEC-2).

## R29 — Job numbering is a faithful, sortable execution order
- **Check:** (a) **sortable** — order segment fixed-width zero-padded (alphanumeric sort == numeric sort; no `_FW_10` beside `_FW_2`); (b) **faithful** — numbering is a *linear extension of the dependency DAG* (for every edge A→B, `number(A) < number(B)`); flag inversions; (c) **banded** — number in the governed functional band for the job `<Type>` (FW 0010s, Placement 0020s, …).
- **Engine:** dependency-DAG builder (prerequisite-loader output) + name parser; topological-order assertion. **Sev:** 🟡 (⚪ for cosmetic-tiebreak-only cases). **Status:** 🟡 **(🟣 recommendation — D5)**
- **Source:** [governance/greenfield-recommendations §1](governance/greenfield-recommendations.md); HLT JobCode map; DAT `<SEQ_NO>`. Complements R12 (job naming) + R13 (token==intent): "the name must tell the truth about the resolved graph."
- **Greenfield:** derive the number from the resolved DAG at Gate 3 (display order == run order by construction); validate inversions/padding at Gate 2.

---

## How the registry is used
- **Gate 2 (Validate):** run all rules → per-unit conformance report (pass/flag + severity).
- **Gate 3 (Design):** each rule's *greenfield action* drives the modernized definition.
- **Single source of truth:** author once; both validation and generation consume it. As a rule moves ❓→🟡→✅, both gates tighten automatically.

## Ratification backlog (maps to information-needed register)
B1 (var.text → R10), B2 (Description keys → R9), B3 (job naming → R12), B4 (canonical var map → R2), B5 (PRAOCG codes → R4), B6 (SEAL mandatory? → R7). See [information-needed](controlm-remediation-information-needed.md).

Related: [[project-description-metadata-plan]], [[project-folder-naming-praocg]], [[project-datacenter-naming-time]], [[project-controlm-remediation-spinoff]]
