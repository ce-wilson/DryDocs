# NFR Consistency & Greenfield Best Practices (synthesis)

**Corpus:** INTERNAL (governance, synthesis). **Status:** 🟠 RECOMMENDATION — 2026-06-17.
Goal-2 deliverable: what's **consistent** across the standards (Vendor / Platform / DAT / HLT), then — using **ontology + SDLC + corporate best practices** — recommended improvements, anti-patterns, and worked examples that form the **ideal greenfield**.

> §2 (consistency) is digested fact. **§3–§5 are recommendations** (my synthesis), not ratified standard — they're the candidate greenfield the spin-off would author and prove. Maps onto the [standards rules registry](../standards-rules-registry.md) (R1–R12), extended by R13–R16 (§5), **R17–R20** (self-heal / severity / tier / 1:1 SCIM — [critical-batch-and-self-heal](critical-batch-and-self-heal.md)), and **R21–R25** (NFR catalog — structured logging / runbook / monitoring binding / lifecycle / NFR evidence gate — [nfr-catalog](nfr-catalog.md)).

> The DAT NFR requirements this synthesis sits on are catalogued in full in [nfr-catalog.md](nfr-catalog.md) (by category, with the Operation-Risk weighting and the ICDW/Snowflake *Evidence Required* discipline). The eight design principles below should be checked against that catalog so no high-risk NFR is dropped.

---

## 1. The common spine (consistent across DAT + HLT)

Both tower standards share one positional skeleton and one escalation contract — the stable base to build the greenfield on:

**Name skeleton (1-based):** `P`(env) · `XXX`(3-char code, pos 2–4) · `F`(frequency D/M/Q/Y, pos 5) · `NNNN`(sequence, pos 6–9) · `_…`(descriptor tokens) · `_<platform>`(AWS/ONPM) · `_<type>`(FW/SFTP/CPY/HK/PREPROC/RFND/…) · optional `_<freq-long>`(DLY) · optional `_<designation>`(PRPL/VERF).

**Escalation contract (SCIM):** `ESYSTEM=APPLICATION`; `ECOMPONENT=SEAL`; `EITEM=Tier-1/2/3`; `ESEVERITY=P2–P6 by impact`; `EAPPLICATION` **must match the name** (column-Y validation); pipe-delimited `ESPECIALINSTRUCTIONS` (Folder/Flow/SLA-EST/Restartable/Full-Delta/Impact/URL).

**Shared semantics:** EST times, `Odate+N` SLAs; SEAL **source-vs-processing** rule; the Description-field metadata mirrors the SCIM special-instructions.

## 1b. Where they diverge (the deltas to reconcile)

| Dimension | DAT (platform view) | HLT (application view) |
|---|---|---|
| pos 2–4 code | **platform** (DCL/AOC) | **application** (SRV) |
| No-SCIM-entry default | platform L1 `C1CCBDATAECO` | **owning dev queue** |
| Middle vocabulary | data-lake stages (RFND/DPL) | file-pipeline stages (SRC/FW/CPY) |
| Optimized for | one central Grafana | per-application ownership |

---

## 2. Design principles for the greenfield (ontology + SDLC + corporate)

1. **Separate the three concerns the name currently overloads.**
   - **Identity** = the name (stable, parseable).
   - **Routing** = SEAL + escalation (SCIM).
   - **Intent** = derived from the *resolved flow* (ontology), **not** the name token.
   This directly fixes the `_FW`-that-is-really-an-API gotcha.
2. **Declare, don't encode-only.** Authoritative facts (SEAL, tier, SLA, source/processing role, data flow) live in **declared metadata** (Description + SCIM, single source), with the name a parseable *convenience*. The graph is the source of truth for intent.
3. **Default to ownership, always.** Adopt HLT's rule org-wide: an un-configured failure routes to the **owning dev queue**, never a silent platform L1. (Corporate best practice: every alert has an accountable owner.)
4. **SEAL is first-class and role-aware.** Mandatory `SEAL` folder variable; **FW folder = source SEAL, processing folder = processing SEAL**; model both edges in the graph.
5. **Stay tool-compatible.** The greenfield name must remain parseable by DAT's Grafana tooling (HLT piggybacks) — make it a **strict superset** both platform and application tooling can read.
6. **Right-size rigidity (the SME's core problem).** A **small mandatory positional core** (env · app-code · frequency · sequence) + an **enumerated-but-extensible descriptor vocabulary** (stages/types from a governed list that can grow) — not a frozen full-string. Rigid where it must be (identity, routing), flexible where reality varies (descriptors).
7. **Make naming↔escalation a pre-commit gate.** The column-Y validation (`EAPPLICATION` must match the name) becomes a **greenfield gate**: a non-conforming name can't ship. (Shift-left, SDLC.)
8. **Intent from resolved flow.** Classify true behavior (file transfer vs API-triggered) from the **resolved predecessor graph + command parse**; tag the ontology node with derived intent and **flag where the name token disagrees** (catch the FW/API cases automatically).

---

## 3. Anti-patterns — things NOT to do

| Anti-pattern | Why it hurts | Seen in |
|---|---|---|
| Smuggle data in punctuation / pure-punctuation var values (`FILE_NM_SUFFIX='.'`) | Brittle, undocumented, breaks parsing | concat-dot ([resolver](../../drydocs/controlm/resolver.py)) |
| Encode behavior in a name token you can't guarantee (`_FW` = API) | Name lies about intent → wrong ontology/monitoring | HLT gotcha |
| Default failures to a generic **platform** queue | Loses ownership; nobody accountable | `C1CCBDATAECO` default |
| Put a **platform** code where an **application** code belongs | Breaks SEAL/ownership resolution | PRAOC/PRDCL sprawl |
| Treat the **name** as SEAL source of truth | Names drift; platform-coded names can't identify the app | folder-naming caveat |
| Hand-maintain **parallel** metadata (Description vs SCIM) | Divergence, double work | escalation ⟷ Description overlap |
| Free-text variable names for one concept (`DRPBX_DIR` vs `DROPBOX_DIR`) | Defeats joins, drift | name-drift (R2) |
| Make the standard so rigid teams **can't** comply | Forces ad-hoc drift — the opposite of the goal | SME's NFR struggle |

---

## 4. Worked greenfield example (the concat-dot FileWatcher)

Legacy `PARAD00010_…_FW` (SEAL 111027) — see [M0 worked example](../m0-poc-worked-example.md). Ideal greenfield:

- **Name:** application-coded, parseable core + governed descriptors; `_FW` only if it truly watches a transferred file — else `_APIPOLL` (or similar) so the token matches intent.
- **SEAL:** declared folder var `SEAL=<source SEAL>` (this is a File Watcher → **source** SEAL), processing folders carry the processing SEAL.
- **Variables:** no dot-smuggling; canonical names (`DROPBOX_DIR`); direct path (`%%var.%%var` delimiters consumed; smuggled dot eliminated).
- **Metadata (single source → Description + SCIM):** `datasetSeriesName | SeriesSLA:<…EST> | Flow:<name> | Restartable:<Y/N> | Full/Delta:<…>`.
- **Escalation:** `ESYSTEM=APPLICATION`, `ECOMPONENT=<SEAL>`, `EITEM=Tier-<n>`, `ESEVERITY=P<n by impact>`; **default to the owning dev queue**, not `C1CCBDATAECO`.
- **Intent (ontology):** behavior derived from the resolved flow (predecessor PREPROC? API? file transfer?), not assumed from `_FW`; node flagged if token ≠ derived intent.
- **Gate:** name passes the column-Y `EAPPLICATION` validation before the Jira is raised.

---

## 5. How this becomes the greenfield engine

- Each principle (§2) and anti-pattern (§3) is a **rule** in the [standards rules registry](../standards-rules-registry.md): validation in Gate 2, generation in Gate 3.
- New rules surfaced here to add: **R13** name-token-matches-derived-intent (FW/API), **R14** escalation routes to owning dev queue by default, **R15** EAPPLICATION↔name column-Y gate, **R16** single metadata source (Description≡SCIM). Plus **R17–R20** (self-heal eligibility / severity sane / tier matches `go/dat6am` / 1:1 SCIM) and **R21–R25** (structured-log fields / runbook completeness / monitoring binding / lifecycle state / NFR evidence gate) — the full proposed set spans **R1–R25**.
- The greenfield is **deterministic + provable**: author from the rules, prove equivalence offline, package the Jira (the SoD-safe path).
- **Deep-dives → [greenfield-recommendations.md (D5)](greenfield-recommendations.md):** where this doc states principles broadly, D5 works each convention in full (Observation→Principle→Grounding→Anti-patterns→Engine rule), clearly marked 🟣 recommendation. First worked: **job naming & numbering** — the number must be a *linear extension of the dependency DAG* and fixed-width zero-padded, so the Control-M GUI's top-to-bottom alphanumeric order *is* a valid execution order (R29).

---

## 6. Open items / to ratify
- ~~The governed **descriptor vocabulary** (stages/types)~~ **✅ FOUND** — it exists as a real artifact: the zone (`TRUST/RFND/OVRH/PROV/TECH`) and ~60-token job-type enumerations in [dat-naming-standard §2c](dat-naming-standard.md), **shared by HLT**. Design-principle 6 (small mandatory core + governed-extensible descriptors) is therefore *confirmed*, not aspirational. Remaining: validate completeness against the live estate.
- ~~Confirm DAT stage tokens (`RFND`/`DPL`)~~ **✅** — confirmed in §2c (RFND = Refined zone; DPL = the framework, appcode `DCL`).
- The **canonical variable registry + per-framework command-line templates** are likewise authored (not just aspirational): [command-line-and-variables-standard](command-line-and-variables-standard.md). Principles 2 (declare-don't-encode) and 7 (naming↔escalation pre-commit gate) now have a concrete spec + verifier (`m7-verify`, `NF-VAL-1..7`).
- Token for **API-triggered** "watchers" (vs `_FW`) — still open (`_MON`/`_PREPROC` exist but no dedicated API-poll token); the R13 gap.
- Org adoption of the **dev-queue default** (needs DAT/Platform agreement — the unresolved dialogue; E1).
- Numeric LOB codes beyond R=41/S=5/K=3/B=82.

Related: [[project-folder-naming-praocg]], [[project-description-metadata-plan]], [[project-controlm-remediation-spinoff]], [[project-drydocs-scrape-two-corpus]]
