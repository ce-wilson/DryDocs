---
standard: control-m-data-center-naming
domain: technology
taxonomy_path: technology/orchestration/control-m/data-center
governs: ControlMServer.data_center   # DC name encodes the default execution time
authority: internal-standards         # config/precedence.yaml tier 2 — refines the BMC baseline
refines: bmc-baseline
applies_to_source: controlm-psgmgr
status: active
trust_tier: internal / SME-asserted / mutable
---

# Internal Standard — Control-M Data Center Naming Convention

**Corpus:** INTERNAL (company-specific standard) — *not* vendor documentation.
**Captured:** 2026-06-11, from SME (chat). Source of record: SME knowledge; confirm against the canonical internal standards page when available.
**Role:** Conformance + operational logic — the data center (Control-M/Server) name encodes the **default execution time** applied to a folder **when the folder does not declare its own time.**

> ⚠️ **Trust tier:** internal / mutable / SME-asserted. Items marked *(to confirm)* are gaps the SME did not enumerate — do **not** invent values.

---

## Key operational rule

**If a folder does not declare a time, the data center name supplies the default time.** **All times are EST (Eastern).**

This is the time-of-day counterpart to ODATE: ordering/scheduling sets the **date** (`%%ODATE`, see [controlm-order-parameters](../../../external/orchestration/bmc-controlm/controlm-order-parameters.md)); the **DC name supplies the default time** when the folder is silent on it.

---

## The convention

Example DC name: **`T032-E0700-DMA`**

| Segment | Example | Meaning |
|---|---|---|
| 1 | `T032` | **Environment + instance** — position 1 is the environment letter, `032` = data-center number/instance |
| 2 | `E0700` | **Default time** — `E` = Eastern (all times EST), `0700` = **07:00 = 7:00 AM EST** |
| 3 | `DMA` | **Ignored** — last 3 chars, out of scope for our use case |

So `T032-E0700-DMA` → **DC #032, default time 7:00 AM EST.**

> **PUBLISHED EXAMPLES USE A NON-PRODUCTION ENVIRONMENT LETTER (J13 class 2, SME ruling
> 2026-08-11).** Every data-center name and application code on this page carries a `T` in
> position 1. The real inventory is production — position 1 is `P` there — and the SME
> ruled that the publishable copy swaps that one character so no example names a live
> production object. **The grammar is untouched and is the whole point of the page:**
> position 1 encodes the environment, `E####` encodes the default time. Only the
> environment VALUE is swapped, so every parsing rule below still reads true. Do not
> "correct" these back to `P` — that is the sanitization, not a typo. The production
> inventory lives internal/-side.

Different data centers carry different `E####` times — the time segment is the meaningful part for scheduling defaults.

**Observed DC inventory (2026-06-11 job-inventory query — the 4 data centers in the C3
normalization scope; environment letter swapped per the note above):**

| Data Center | Default time | Suffix (ignored) |
|---|---|---|
| `T012-E0700-IB` | 7:00 AM EST | IB |
| `T014-E0700-ANY` | 7:00 AM EST | ANY |
| `T021-E0800-ANY` | **8:00 AM EST** | ANY |
| `T032-E0700-DMA` | 7:00 AM EST | DMA |

Application codes span DCs (e.g. TRICD in T012/T014/T032) — DC↔application is many-to-many.

---

## Why this matters for the knowledge graph

- A folder's effective run time = **declared folder time** if present, **else** the DC's `E####` default. Any timing analysis must apply this fallback, not assume folders always carry an explicit time.
- All times normalize to **EST** — no per-job timezone math needed for this default (timezone-specific ordering is a separate concern; see "Wait for Order Date to run" in [controlm-order-parameters](../../../external/orchestration/bmc-controlm/controlm-order-parameters.md)).
- The DC name parses into attributes (environment, instance, default time) — candidate node properties; a folder → data-center → default-time edge captures the fallback.

---

## Open items to confirm (do not fill speculatively)

1. Environments beyond `P` = Production (segment 1 prefix). *Evidence 2026-07-09:* the
   CM_HOSTS profile found **22 distinct DATA_CENTER values** (vs the 4 known production
   DCs) — non-production environment prefixes exist; enumeration still to confirm.
2. Range/meaning of the instance number (`032`).
3. Full set of `E####` default times across data centers.
4. Confirm `E` is always Eastern (SME stated all times are EST).
5. Precedence details: does any layer between folder and DC (e.g. job-level time) override first?

Related: [[project-folder-naming-praocg]], [[project-drydocs-scrape-two-corpus]], [[project-controlm-xml-not-json]]
