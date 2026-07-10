# M0 PoC — Worked Example (executed offline)

**Corpus:** INTERNAL. **Status:** 🟠 DRAFT-EXECUTED — 2026-06-11, blocked on ground truth (A3) + `var.text` rule (B1).
**Branch:** `controlm-spinoff`. **Unit:** `PARAD00010_MLCM_ORIGINATIONS_DAILY_CRM_INDICATOR_TOK_ONPM_FW`.
This runs the 5 gates as far as is possible without live-system access, using the real definition (from production screenshots) and the actual `ctm-remediate`/DryDocs resolver. It demonstrates the workflow **and** surfaces a real finding.

---

## Gate 1 — Capture (legacy, read-only)

| | |
|---|---|
| Job | `PARAD00010_MLCM_ORIGINATIONS_DAILY_CRM_INDICATOR_TOK_ONPM_FW` (FileWatcher, Create) |
| Folder | `PRARAG-HLDM-89211-MLCM-ORIG-CRM-TRUST-DLY` (SMART) · DC `P032-E0700-DMA` · Run as `mlc_p` |
| App / SEAL | PRARA / **111027** (HL Advice & Reporting) |
| Watch template | `%%DRPBX_DIR.%%FILE_NM_PREFIX.%%BUS_DATE.%%FILE_NM_SUFFIX.%%EXTENSION` |
| Variables | `DRPBX_DIR=/data/uds/mlc/dropbox/MLCM/` · `FILE_NM_PREFIX=Originations_Daily_CRM_Indicator_` · `BUS_DATE=%%$ODATE` · `FILE_NM_SUFFIX=.` · `EXTENSION=tok` |

---

## Gate 2 — Validate (classify + resolve offline)

**Classifier:** `FILE_NM_SUFFIX` → kind `LITERAL`, **`value_is_delimiter = True`** ✓ — the dot-smuggling detector fires correctly.

**Resolver (baseline):**
```
LEGACY watch = /data/uds/mlc/dropbox/MLCM/Originations_Daily_CRM_Indicator_{ODATE}.tok
```
Clean: every `.` between `%%refs` is consumed as the concatenation delimiter; the only surviving dot is the smuggled `FILE_NM_SUFFIX='.'` value. `{ODATE}` is the canonical token (resolves to the order date at runtime).

**Hazards flagged:** dot-smuggling (`FILE_NM_SUFFIX='.'`); 5-variable indirection for a near-static path; `DRPBX_DIR` name drift vs the modern `DROPBOX_DIR`.

---

## Gate 3 — Design (greenfield, proposed)

Target resolved filename (must equal the Gate-2 baseline):
`/data/uds/mlc/dropbox/MLCM/Originations_Daily_CRM_Indicator_{ODATE}.tok`

Proposed greenfield (canonical name, no dot-smuggling, declared metadata):
- `DROPBOX_DIR = /data/uds/mlc/dropbox/MLCM/` (canonical name)
- Watch template → **pending B1** (see Gate 4): the exact safe template depends on the confirmed `var.text` dot rule.
- Description (key:value): `datasetSeriesName: MLCM CRM | SeriesSLA: 17:00 EST`
- Folder variable: `SEAL = 111027`

Reference: the dev team's existing modern rewrite is `PARAD0011b_MLCM_ORIG_DAILY_CRM_INDICATOR_TOK_ONPM_FW`, watch template `%%DROPBOX_DIR.Originations_Daily_CRM_Indicator_.%%$ODATE.tok`.

---

## Gate 4 — Prove (equivalence) — ⚠️ FINDING

Resolving the dev team's modern rewrite through the same engine:
```
LEGACY watch = /data/uds/mlc/dropbox/MLCM/Originations_Daily_CRM_Indicator_{ODATE}.tok
MODERN watch = /data/uds/mlc/dropbox/MLCM/.Originations_Daily_CRM_Indicator_.{ODATE}.tok
MATCH        = False
```

**The modern rewrite does NOT resolve to the same filename as legacy under our resolver** — it gains a `.` after `MLCM/` and before `{ODATE}`, and the extension dot shifts. Three possible explanations, in priority order:

1. **`var.text` dot rule (B1) — most likely.** Our resolver consumes `.` only between `%%var.%%var`; the modern template uses `%%var.text` (`%%DROPBOX_DIR.Originations…`, `%%$ODATE.tok`). If Control-M *also* consumes the period after a variable that precedes literal text, the modern path would resolve differently (and possibly cleanly). The rule is unconfirmed.
2. **The modern rewrite is genuinely not behavior-preserving** — it really does watch a different filename than legacy. If so, this is a production discrepancy worth raising independently.
3. Transcription artifact from the screenshots.

**Adjudicator = A3 (ground-truth filename).** One fact — the filename Control-M actually watches for each job — settles which explanation holds, fixes the resolver if needed, and unblocks a trustworthy greenfield. **This is the PoC's headline result: an offline engine caught a behavior-equivalence question on a change the dev team already shipped.**

Equivalence verdict: **PENDING** (blocked on A3 → B1).

---

## Gate 5 — Package (Jira draft)

```
Title:        [Control-M Remediation] PARAD00010…_FW — remove dot-smuggling, canonicalize path
Component:    Control-M / PRARA / SEAL 111027 (HL Advice & Reporting)
Requested by: Production Support (analysis pre-validated; implementation only)

── Why ──────────────────────────────────────────────
Legacy watch path smuggles a literal '.' via FILE_NM_SUFFIX='.' through
Control-M's concatenation operator, across a 5-variable indirection chain.
Brittle, undocumented, and inconsistent with the DROPBOX_DIR naming used
elsewhere. value_is_delimiter detector confirms the smuggle.

── Scope ────────────────────────────────────────────
Folder: PRARAG-HLDM-89211-MLCM-ORIG-CRM-TRUST-DLY   Job: PARAD00010…_FW
DC: P032-E0700-DMA   SEAL: 111027

── Change (BEFORE → AFTER) ──────────────────────────
Vars:  remove FILE_NM_SUFFIX='.', BUS_DATE, FILE_NM_PREFIX, EXTENSION;
       rename DRPBX_DIR → DROPBOX_DIR
Watch: %%DRPBX_DIR.%%FILE_NM_PREFIX.%%BUS_DATE.%%FILE_NM_SUFFIX.%%EXTENSION
   →   <greenfield template — finalize after B1>
Add:   Description "datasetSeriesName: MLCM CRM | SeriesSLA: 17:00 EST"; folder var SEAL=111027

── Equivalence evidence ─────────────────────────────
Legacy resolves to: /data/uds/mlc/dropbox/MLCM/Originations_Daily_CRM_Indicator_{ODATE}.tok
Greenfield must resolve identically — VERIFICATION PENDING ground-truth (A3) + var.text rule (B1).
⚠️ NOTE TO DEV: the existing PARAD0011b rewrite resolves DIFFERENTLY under offline analysis —
   please confirm the intended watched filename.

── Acceptance criteria ──────────────────────────────
[ ] Greenfield resolves to the filename above (re-verify with ctm-remediate)
[ ] No change to ODATE/scheduling/SEAL association
[ ] First-run watch confirmed against a real arriving file

── Rollback ─────────────────────────────────────────
Restore prior version via Control-M Changes History (180-day window).

── Status ───────────────────────────────────────────
DRAFT — do not submit until A3/B1 resolved and greenfield template finalized.
```

---

## M0 status & exit

- ✅ Gates 1–3 executed offline; classifier + resolver work on the real unit; detector confirmed.
- ⚠️ Gate 4 produced the headline finding (modern ≠ legacy under our resolver) → **blocked on A3 + B1**.
- ⏸ Gate 5 Jira drafted; not submittable until equivalence is proven.
- **Single unblock:** obtain the ground-truth watched filename(s) from Control-M monitoring/history (info item A3). That closes B1, finalizes the greenfield template, and completes M0.

Related: [[project-controlm-remediation-spinoff]], [[project-description-metadata-plan]], [[project_controlm_c3_normalization]]
