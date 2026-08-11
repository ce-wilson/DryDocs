# Standards Rules Registry (machine-checkable) — DRAFT

**Corpus:** INTERNAL. **Status:** 🟠 DRAFT — 2026-06-11; governance rules added 2026-06-17; **R30–R40 (the greenfield job standard) added 2026-08-11 with a working detector — G67**.
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

# R30–R40 — the greenfield job standard (G67, 2026-08-11)

The first block of rules with a **working detector**: `drydocs_remediation.detect.detect_conformance`,
run over real staged definitions through `xml_bridge` (the G47 extractor's output adapted; reading
definition XML stopped being blocked at G47, only emitting still needs the vendor schema). All 🟡
provisional, all emitted `ratified=False` — machine-readable ratification is still the M1 deliverable.

**Source:** [controlm-greenfield-job-standard](../standards/technology/controlm-greenfield-job-standard.md)
(values twin) and its Internal-Public mechanism half; evidence in
[controlm-job-metadata-standards-capture](../controlm-config/reference/controlm-job-metadata-standards-capture.md)
and [controlm-pipeline-stub-capture §B4–B7](../controlm-config/reference/controlm-pipeline-stub-capture.md).
Backlog: C30 (standard) · G67 (detectors).

**Two failure classes, deliberately not merged.** Name drift produces **silence** — the name misses
`FACT_REGISTRY`, no `STG_APP_FACT` row is written, lineage is simply absent (R2). A value-contract
breach produces a **confidently wrong row** — the name resolves, so the graph gains a false fact
(R34). The second is 🔴 and must never be filed as a lint warning beside a rename suggestion.

**Two rules that deliberately do NOT exist.** Nothing binds `%%NOTIFY` to a distribution list:
notification is being removed as a mechanism and the ServiceNow incident is the call to action, so
a rule that "fixed" the unset destination would re-wire what REQ-2 removes — an unset `%%NOTIFY` is
an ordinary R30 unresolvable reference, nothing more. And nothing asserts a ServiceNow queue on a
Control-M object: technician routing belongs to the escalation DB via the `EJOBNAME` join.

## R30 — Every `%%` reference resolves somewhere in the scope chain
- **Check:** a plain `%%NAME` in `CMDLINE`, the watch path, `POSTCMD`, or any variable value in the job's chain, with no declaration at folder, sub-folder or job scope. System variables and `%%$`-tokens are excluded; `%%\GLOBAL` and `%%\\POOL\VAR` are out of view and never accused.
- **Engine:** `_check_references` over `DefinitionSet.resolution_chain`. **Sev:** 🔴 **Status:** 🟡
- **Why 🔴:** the vendor resolves an undefined reference to the reserved word `CTMERR`, so it reaches the agent as literal text — a runtime defect, not a lint.
- **Greenfield:** declare at the widest scope that holds it (R35), or delete the reference.

## R31 — No orphan declarations
- **Check:** a job-scope variable referenced nowhere on that job, **excluding** registered facts (`FACT_REGISTRY`) and standard metadata fields (the `FILE_*` components, `DEVX_KEY`, `EMAIL_DL_*`).
- **Engine:** `_check_references`. **Sev:** ⚪ **Status:** 🟡
- **Why the exclusions:** a fact declared for the record is the standard working as designed — `FILE_EXTENSION` exists so the SQL parse can read it into `CM_JOB_FILE_NAME_STANDARD`, and flagging it would fight the rule that requires it. An orphan is a name that is BOTH unregistered and unused.
- **Greenfield:** wire it up or drop it.

## R32 — The required declaration set per job type
- **Check:** command jobs carry `LAUNCHER_SCRIPT_PATH`, `ETL_PLATFORM`, `ETL_ARTIFACT_URI`, `ETL_ARTIFACT_KIND` (REQ-4; `ETL_PLATFORM_FLAGS` optional); FileWatchers carry `FILE_DIR`, `FILE_PREFIX`, `FILE_BUSINESS_DATE`, `FILE_EXTENSION`. Satisfied at ANY scope in the chain.
- **Engine:** `_check_required`. **Sev:** 🟡 **Status:** 🟡
- **Why any-scope:** under the ladder most of these live on the folder; demanding them locally would fight the standard this enforces.
- **Greenfield:** add the missing declaration at its owning scope.

## R33 — Exactly one carrier per fact
- **Check:** a value present BOTH as a command literal and as a declared variable. The standard names the carrier per fact; for `pipelineId` it is the **literal**, so a `PIPELINE_ID` variable is the finding.
- **Engine:** `_check_carriers` (`LITERAL_CARRIER_FACTS`). **Sev:** 🟡 **Status:** 🟡
- **Source:** the DPL generator declares no `PIPELINE_ID` variable and its undefined-token list does not name one — the GUID is baked in at generation time from `PipelineDetails`. NFR-CTM-001 §6.1/§6.2 say `-pipeline %%PIPELINE_ID` and are wrong.
- **Greenfield:** remove the variable. Two carriers can disagree silently; the command wins and the variable lies. **Rider:** the GUID is the DPL `dataset_flow` join key, so the standard grants one anchored `-pipeline <uuid>` extractor as a named exception to NFR §10 — otherwise the key never reaches `STG_APP_FACT`.

## R34 — Value contract per canonical fact
- **Check:** `DS_ID` is a UUID, `DS_VER` is dotted-numeric, an artifact URI is a URI and not a bare image name.
- **Engine:** `_check_values` (`VALUE_CONTRACTS`). **Sev:** 🔴 **Status:** 🟡
- **Why 🔴:** the NAME resolves, so a fact row IS written — with a false value. Catches the sibling-swap shape where two canonicals hold each other's values.
- **Greenfield:** correct the value; check the sibling for the other half of the swap.

## R35 — Invariants live at the widest scope that holds them
- **Check:** the same `(name, value)` declared at JOB scope on two or more sibling jobs.
- **Engine:** `_check_hoistable`. **Sev:** ⚪ **Status:** 🟡
- **Why it matters more than ⚪ suggests:** this is the defect CLASS behind the drift the other rules catch one instance at a time. The generator emits a partial job and expects a folder `AUTOEDIT` block; where that block is missing, people hand-copy per job and one copy eventually differs.
- **Greenfield:** hoist to folder (flow-invariant) or sub-folder (dataset identity).

## R36 — A composed path is derived, never retyped
- **Check:** one declaration's path value ends with another declaration's whole basename value (basename ≥ 12 chars, no `/`).
- **Engine:** `_check_retyped_paths`. **Sev:** 🟡 **Status:** 🟡
- **Greenfield:** declare the components once and derive the composed handle from them, so there is one place to change. Referencing rather than retyping is why the greenfield shape passes this rule structurally.

## R37 — No adjacent `%%` references
- **Check:** `ADJACENT_REF_RE` on any variable value, command line, watch path or post-command.
- **Engine:** `_check_names`, reusing the core classifier's `DYNAMIC_NAME` hazard regex. **Sev:** 🟡 **Status:** 🟡
- **Greenfield:** separate them with the concatenation delimiter; two abutting references may be read as one composed variable NAME.

## R38 — Vendor charset legality of user-defined names
- **Check:** forbidden characters ``< > [ ] { } ( ) = ; ` ~ | : ? . + - * / & ^ # @ ! , " '`` and blanks; length ≤ 38; and a user declaration inside a vendor application prefix (`FileWatch-`, `UCM-`, the `%%SAPR3-` form).
- **Engine:** `_check_names`. **Sev:** 🔴 **Status:** 🟡
- **Source:** [controlm-variables](../../external/orchestration/bmc-controlm/controlm-variables.md), authoritative section.
- **Catches two requirements-page defects:** REQ-1's `DevX-project` and REQ-3's `%%FileWatch-FILE_PATH` are both illegal; the live build already uses the legal `DEVX_KEY` and `FILE_PATH`, so the standards page changes, not the jobs.

## R39a — A TOK/CTL watcher cats the file it watched
- **Check:** `post_command == "cat " + watch_path`, exactly.
- **Engine:** `_check_post_exec` + `DISTRIBUTION_ROLES`. **Sev:** 🟡 **Status:** 🟡
- **Source:** [filewatcher-postexec-token-cat](../../knowledge/standards/technology/filewatcher-postexec-token-cat.md).
- **Note:** the old wording was "references the watch-path variable expression", which is hard to check. Once both sides are one derived handle (`%%F_FQN`) it becomes string equality — a rule you can actually enforce.

## R39b — A DAT watcher does NOT cat
- **Check:** a watcher whose DistributionRole is DAT with a `cat` post-command.
- **Engine:** `_check_post_exec`. **Sev:** 🔴 **Status:** 🟡
- **Why 🔴:** the same NFR's MUST NOT — data files can be multi-GB, and echoing one into sysout floods the log and can breach sysout limits. The operational risk sits in the *forbidden* clause, not the required one. REQ-3 says "for job type file_watcher" unqualified and needs this scope correction.

## R40 — REQ-2: zero `SHOUT` / `DOSHOUT`
- **Check:** either tag present on a folder or a job.
- **Engine:** `_check_notifications`, over notification tags the extractor records BY NAME (a count cannot answer "which"), scanning into `ON` blocks but stopping at nested job/sub-folder boundaries.
- **Sev:** 🟡 **Status:** 🟡
- **Scope:** `DOMAIL` is **not** flagged. REQ-2 puts it out of scope and whether mail goes too is an SME ruling; the detector does not presume it.

---

## How the registry is used
- **Gate 2 (Validate):** run all rules → per-unit conformance report (pass/flag + severity).
- **Gate 3 (Design):** each rule's *greenfield action* drives the modernized definition.
- **Single source of truth:** author once; both validation and generation consume it. As a rule moves ❓→🟡→✅, both gates tighten automatically.

## Ratification backlog (maps to information-needed register)
B1 (var.text → R10), B2 (Description keys → R9), B3 (job naming → R12), B4 (canonical var map → R2), B5 (PRAOCG codes → R4), B6 (SEAL mandatory? → R7). See [information-needed](controlm-remediation-information-needed.md).

Related: [[project-description-metadata-plan]], [[project-folder-naming-praocg]], [[project-datacenter-naming-time]], [[project-controlm-remediation-spinoff]]
