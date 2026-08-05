---
standard: control-m-folder-naming
domain: technology
taxonomy_path: technology/orchestration/control-m/folder
governs: ControlMFolder.name              # the 6-char folder name (SCHED_TABLE)
authority: internal-standards         # config/precedence.yaml tier 2 — refines the BMC baseline
refines: bmc-baseline
applies_to_source: controlm-psgmgr
status: active
trust_tier: internal / SME-asserted / mutable
---

# Internal Standard — Control-M Folder Naming Convention (PRAOCG)

**Corpus:** INTERNAL (company-specific standard) — *not* vendor documentation.
**Captured:** 2026-06-11, from SME (chat). Source of record: SME knowledge; confirm against the canonical internal standards page when available.
**Role:** Conformance layer — defines what a *valid* Control-M folder name is **here**. The vendor side only says the Folder Name field exists ([controlm-folder-definition-parameters](../../../external/orchestration/bmc-controlm/controlm-folder-definition-parameters.md)); this defines how we fill it.

> ⚠️ **Trust tier:** internal / mutable / SME-asserted. "The **majority** follow" this convention — it is a strong norm, not a guaranteed invariant. Items marked *(to confirm)* are gaps the SME did not fully enumerate; do **not** invent values for them.

> 🔒 **Split twin (J14, 2026-07-27):** this file is the publishable MECHANISM half.
> The real application-code registry, real SEAL ids/application names, and the real
> production job inventory live in the Internal-Confidential VALUES twin,
> `internal/standards/technology/folder-naming-convention.md`. Examples below use
> the sanitized sample ids (reserved synthetic SEAL block **70001–70099**,
> `config/taxonomy/business-application.yaml`); the twin holds the real↔synthetic key.

---

## The convention

Most Control-M folders follow a **6-character positional code**: **`PRAOCG`**

Worked example: **`PRAOCG`** = Production · Retail(CCB) · `AOC` (Ab Initio On Cloud) · `G` (Smart folder)

| Pos | Code (example) | Meaning | Notes |
|-----|----------------|---------|-------|
| 1 | `P` | **Environment** — `P` = Production | Other environment codes *(to confirm)* — e.g. non-prod codes not provided |
| 2 | `R` | **Line of business code** — `R` = **CCB Retail** | Other LOB codes *(to confirm)* |
| 3–5 | `AOC` | **3-char code** — chosen as close as possible to the acronym | Example: **A**b **I**nitio **O**n **C**loud → `AOC`. Mnemonic, not a registry lookup. ⚠️ **Often a *platform* name, not an application/area-application name** — see caveat below |
| 6 | `G` | **Folder type marker** — `G` = **Smart folder** | See historical note below |

So `P` + `R` + `AOC` + `G` → `PRAOCG`.

---

## TWO internal standards, not one (SME, 2026-08-05)

The `authority: internal-standards` in this file's frontmatter models **one** internal
tier. There are at least **two**, and they nest:

```
Vendor (BMC baseline)  →  Company / Platform team  →  Lower support group
   folder field exists      DAT SRE standard             HLT standard
                            (framework-coded)            (application-coded)
```

`refines:` is therefore a **chain, not a flag** — the HLT standard refines the DAT SRE
standard, which refines the BMC baseline. Both internal levels are `authority: tier 2`
under `config/precedence.yaml` today, which cannot express which of the two wins where
they differ. Recorded as a gap; not resolved here.

The two standards produce **different folder grammars off a shared 6-char prefix**:

| | DAT SRE (platform team) | HLT (support group) |
|---|---|---|
| Persona it serves | SRE — monitor **by application**, roll job failures up to the owning PAT product | L2/L3 app support — monitor by application and by the escalation queues that correlate to the SEAL CI |
| Prefix pos 3–5 | **framework/platform** code | **application** code |
| Prefix pos 6 | `G` (smart folder) | **frequency letter** — current, not legacy |
| SEAL | a **token inside the folder name** (the app code has none) | carried by the **app code itself** |
| Framework identity | *is* the app code | moves to a **sub-application**, `PR<Appcode>-<Platform App Code>` |
| Grammar | `PR<fw>G-AREA_PRODUCT-SEAL-PROCESS-ZONE-FREQ` | `PR<app><Freq>-HLDM\|HLDF-<SOR/Reporting Seal>-<DataSetGroup_BusProcess>-<Zone>-<Freq>` |

### Tier discrimination — mechanically derivable, NOT a steward act

**Positions 3–5 of the prefix discriminate the K7 tier.** Match them against the
platform-code list (six framework codes; real values in the VALUES twin):

- **pos 3–5 ∈ platform list** → **tier 2**. The `PR<fw>` application is a *framework with
  no direct SEAL*; its folders belong to many consuming applications. The resolving SEAL
  is the **SEAL token inside the folder name**, so per-folder resolution is derivable from
  the name for the common case. The `AREA_PRODUCT` token is *specified* to equal the **PAT
  Area Product name** exactly — no roll-ups, no breakings — but see the conformance caveat
  immediately below before treating that as a resolvable key.
- **pos 3–5 ∉ platform list** → **tier 1**, code carries the SEAL, fan-out is correct.

This closes the gap recorded against `folder_attribution.py` — a platform code is
declarable from the folder name plus a six-row list, instead of being discovered after
a silent tier-1 fan-out.

> ⚠️ **A specified "must" is not a data invariant (SME, 2026-08-05).** The
> `AREA_PRODUCT` ↔ PAT Area Product name equality holds for the **majority** of DAT
> products, **not all** — the standards page carries its own caveat ("exceptions exist —
> confirm with SME before relying on the product↔area-product mapping"), and the DAT
> standard governs only the Data & Analytics product line, with HLT following the same
> shape *by convention* under separate guidelines. The existence of an automated
> conformance checker for promotion is itself evidence that non-conformant folders are in
> the estate.
>
> **Consequence for any loader:** the token is a **resolution attempt with a residual**,
> never a lookup that must succeed. A folder whose `AREA_PRODUCT` token matches no PAT
> Area Product is **surfaced**, not guessed at and not dropped — which is exactly the K7
> steward path, so that fallback is a normal outcome rather than a rare one. Do not build
> anything that treats an unmatched token as a defect in the folder.

### The standing pattern: every cross-system join here is a norm, not an invariant

Five in this family so far, and they behave identically: the app-code `descr` prefix, a
functional id's registered SEAL, an alert's routing SEAL, the framework token in prefix
positions 3–5, and this `AREA_PRODUCT` ↔ PAT equality. Each is *usually* right, which is
the dangerous kind — hand-sampling confirms them and the tail fails silently.

**The rule that follows:** none of these may be used as a key that must resolve. Each
needs the same three-part handling — corroborate rather than validate, report the
residual as a count, and route disagreements to a human. Deriving from one, or reddening
a test on one, is a defect in the consumer, not in the data.

### The sub-application seam — a declared application→software link

Under the HLT standard the framework does not disappear; it becomes a **sub-application**
on the job: `PR<Appcode>-<Platform App Code>`. That is a *declared* statement that a given
application runs on a given ETL framework — i.e. an
`(:BusinessApplication)-[:USES_SOFTWARE]->(:SoftwareProduct)` fact already present in the
scheduling data, at scale, with an authoring standard behind it. Two of the six framework
codes have no `config/taxonomy/software-registry.yaml` product row yet (the DPL gap that
`invocation_patterns` already records, plus Snowflake ETL), so registering those products
is the prerequisite.

### `1 SEAL per folder` — independent corroboration of the K7 1:1 rule

The HLT data-classification rule states **one SEAL per folder**, using the Reporting App
SEAL where data is aggregated from multiple sources. That is the company's own naming
standard independently asserting what `graph-tests/folder-attribution-coverage.yaml`
enforces as folder→application 1:1 — arrived at from opposite directions.

## Position 6 — historical meaning (important context)

The 6th character was **originally a frequency indicator**, not a folder-type marker:

| Historical code | Meaning |
|---|---|
| `D` | Daily |
| `W` | Weekly |
| `M` | Monthly |
| … | others *(to confirm — SME said "etc.")* |

**Today, everything is a SMART folder**, so position 6 is now `G` (Smart folder) rather than a frequency code. Expect **legacy folder names still carrying frequency codes** (`…D`, `…W`, `…M`) in the existing estate — graph/analysis logic should treat position 6 as *either* frequency (legacy) *or* `G` (current), not assume one.

> **CORRECTED 2026-08-05 (SME standards pages).** "Frequency at position 6 = legacy" is
> true only of the **DAT SRE** standard, where `G` is current. Under the **HLT** standard a
> frequency letter at position 6 is the **CURRENT** convention — an HLT folder prefix is
> `PR<Appcode><Freq>`. So a frequency letter is *not* evidence of a legacy name; which
> standard the prefix follows decides how to read position 6, and pos 3–5 is what tells
> you the standard. The "treat as either, never assume" advice stands — the *reason* was
> wrong.
>
> Confirmed frequency tokens: `D` daily · `W` weekly · `M` monthly · `Q` quarterly ·
> `Y` yearly · `R` request/adhoc · `H` holiday · `G` smart/group folder. Zone tokens
> (folder = data layer, next-to-last token): `RAW` raw placement · `TRUS` trusted
> (placement + ingestion) · `RFND` refined (CDC + semantic) · `PROV` provision to
> consumption · `ONPM` on-premise · `TECH` tech-debt/workaround, removed after cutover.
> These close several *(to confirm)* gaps below.

---

## ⚠️ Platform-vs-application caveat (SME, 2026-06-11 — RESOLVED)

**The majority of folders carry a *platform* code in positions 3–5, not an application or area-application code.**

**Organizational background (why):** as the company grew, SDLC roles consolidated — QA teams phased out, support now split between developer-supported small apps and a **centralized batch team** for data warehousing, with silos between support and other groups. **Data-lake SRE teams dictated platform Control-M app codes** and hardcoded naming standards for data products on the data lake. Teams not supported by that SRE org created their own application-tied codes following similar standards.

### Application-code registry (SHAPE — sanitized rows; real registry in the values twin)

| Code | Type | Meaning | SEAL tie |
|---|---|---|---|
| `PRAOC` | **Platform** | Ab Initio ETL platform (data lake, SRE-dictated) | **No direct SEAL** |
| `PRDCL` | **Platform** | Java/PySpark jobs loading to AWS cloud (SRE-dictated) | No direct SEAL |
| `PRSRV` | **Application** | Servicing reporting & analytics — team-created, application-tied | direct SEAL — sanitized sample id **70003** (Consumer Servicing Reporting & Analytics) |
| `PRARA` | **Application** *(confirmed 2026-08-05)* | **A**dvice **R**eporting & **A**nalytics — mnemonic confirmed, code-type confirmed tier 1 | direct SEAL — sanitized sample id **70002** (Retail Advice Reporting & Analytics) |

**Completeness (2026-08-05):** the platform list is now **closed at six framework codes**
(real values in the VALUES twin), and the HLT application codes are enumerated at five.
"Extend as confirmed" no longer applies to the platform side — a seventh framework code
would be a change to the DAT SRE standard, not a discovery.

### Observed job inventory (2026-06-11 query — conclusions only; full real counts in the values twin)

- **The same app code spans multiple data centers** — code→DC is many-to-many
  (several codes observed in 2–3 DCs each).
- Four production DCs observed; one runs a different default-time code than the
  others (DC default times do vary — see [data-center convention](data-center-naming-convention.md)).
- One DC hosts `PC…` codes vs `PR…` elsewhere — consistent with position 2 = LOB
  (`R` = Retail; the second letter's decode *to confirm*).
- **JOBS_WITH_VARS ≈ JOB_TOTAL** almost everywhere — nearly every job carries
  variables, which sizes the variable-modernization effort at effectively the
  whole estate.

Consequences:
- A folder name does **not** reliably identify the business application. Do not derive folder→`:Application` joins from the name code alone.
- The original intent of embedding a **SEAL ID** in auto-generated folder names (sample shape: `PRARAG-HLDM-70002-…` — File Watchers carry the *source* SEAL, processing folders the *processing app's* SEAL) is **not valid estate-wide** for the same reason.
- **SEAL resolution hierarchy:** folder variable `SEAL` (primary) → *(planned)* SEAL derived from the data pipeline/dataset the job touches → name-embedded SEAL (weak hint only). Full detail: [description-field-metadata-plan](description-field-metadata-plan.md).

## Why this matters for the knowledge graph

- This convention makes a folder name **parseable into attributes** — environment, LOB, application, folder-type/frequency — which can become node properties or relationships (e.g., folder → `:Application` join via the 3-char app code).
- The **application-code → application-name** mapping (`AOC` → "Ab Initio On Cloud") is a candidate cross-graph link to SEAL `:Application` / business ontology. ⚠️ Beware the **"Application" name collision** with Control-M's own `Application` parameter — keep them namespaced (see [[project-drydocs-scrape-two-corpus]]).
- Enforcement path on the vendor side: **Site Standard + Business Parameters + Enforce Validations** (see the folder-definition-parameters doc) is where such a naming rule would be enforced in Control-M itself.

---
---

## Platform-ordering folders — `PUDLY` and the User Daily mechanism

**SME-attested 2026-08-03 (~99% confidence), corroborated by the vendor mechanism but NOT
vendor-confirmed.** `PUDLY` reads as **P**roduction **U**ser **D**ai**LY** — the Control-M
platform's own folders that set up mapping between data centers.

**What BMC actually documents** (searched 2026-08-03 across the loaded vendor corpus, 374
chunks; see `controlm-folder-definition-parameters`):

| Parameter | Meaning |
|---|---|
| **Order Method** | One of **Automatic (Daily)** — the New Day procedure orders the folder at New Day time; **None (Manual Order)**; or **Specific User Daily** — an identifier assigning the folder to a specific User Daily job, ordered at a set time of day for **load balancing across the day** rather than at New Day time. |
| **User Daily name** | "Defines User Daily jobs **whose sole purpose is to order jobs.** Instead of directly scheduling production jobs, the New Day procedure can schedule User Daily jobs, which in turn schedule the production jobs." Set when Order Method = Specific User Daily. |

**Three things to know before relying on this:**

1. **The corpus carries no User Daily NAME examples.** The mechanism is documented; naming is
   not. `PUDLY` is ours, like `PRAOCG` — BMC would never carry it. The expansion above is the
   SME's, recorded so the next session does not re-search the vendor docs for it.
2. **The SaaS/API surface drops the value entirely.** `controlm-api-folder-reference` exposes
   `OrderMethod` as only `"Automatic"` or `"Manual"`; Specific User Daily exists solely in the
   classic Parameter Reference. Anything reasoning about ordering from the API docs alone will
   silently miss this whole class of folder.
3. **The token does not fit the 6-character convention above.** `PUDLY` is five characters, and
   positions 3–5 read as a frequency word rather than a platform/application acronym. Treat it
   as an exception or a legacy name predating the convention — not as evidence the convention
   is wrong.

**Graph consequence (gate `seal-app-ref-edge-reshape` / K7, SIGNED OFF 2026-08-03).** A User
Daily folder's sole purpose is to order other jobs, so it is scheduling **infrastructure**, not
business workload. Under the gate's OWNER-NOT-USER rule — a folder belongs to whoever OWNS it,
not whoever USES it — these folders attribute to the Control-M platform's own SEAL, not to the
applications whose jobs they order. The vendor definition is what makes that a statement about
the object rather than a convention.

**Available but not taken:** the Control-M extract carries the Order Method column, so this
folder class could be identified by FIELD rather than by name pattern — which would be stronger
than name-parsing, given the caveat above that a folder name does not reliably identify
anything. Deliberately not pursued at K7 (SME: "we do not need to go down that path"); recorded
here so it is a choice rather than an oversight.


## Open items to confirm (do not fill speculatively)

1. Full list of **environment codes** (position 1) beyond `P` = Production.
2. Full list of **line-of-business codes** (position 2) beyond `R` = CCB Retail.
3. Full historical **frequency code** list (position 6) beyond D/W/M.
4. Is the app code **always exactly 3 chars**, and is there a governed registry or is it per-team mnemonic?
5. How non-conforming / legacy names are handled (exceptions, grandfathering).
6. `PUDLY` expansion — **Production User Daily** is SME-attested (2026-08-03, ~99%) and
   consistent with the vendor User Daily mechanism, but no source states it. Confirm against
   an internal Control-M standard or the platform team, not against BMC (searched, absent).

Related: [[project-drydocs-scrape-two-corpus]], [[project-controlm-xml-not-json]]
