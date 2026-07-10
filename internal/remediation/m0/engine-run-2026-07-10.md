# M0 engine run — 2026-07-10 (drydocs_remediation, first mechanized pass)

**INTERNAL.** The M0 unit executed through the new `drydocs_remediation` component
(G3 / ADR 0002-B), replacing the 2026-06-11 by-hand run in
[`../m0-poc-worked-example.md`](../m0-poc-worked-example.md). Inputs: the two
transcripts in this directory (gate-1 fallback format,
`drydocs.remediation.transcript.v1`). Engine: `TranscriptDefinitionFormat` →
`detect_findings` → `resolved_watch`/`prove_equivalence`, all resolution via
`drydocs_core.controlm` (the same engine the loaders trust).

## Result — the engine reproduces the by-hand gates verbatim

```
== Gate 2: detect + baseline ==
finding: R1 sev=should-fix ratified=False target=PARAD00010_MLCM_ORIGINATIONS_DAILY_CRM_INDICATOR_TOK_ONPM_FW:FILE_NM_SUFFIX
LEGACY watch = /data/uds/mlc/dropbox/MLCM/Originations_Daily_CRM_Indicator_{ODATE}.tok

== Gate 4: equivalence (legacy vs the shipped modern rewrite) ==
MODERN watch = /data/uds/mlc/dropbox/MLCM/.Originations_Daily_CRM_Indicator_.{ODATE}.tok
MATCH        = False (compared_jobs=1)
```

Point-for-point identical to the worked example's Gate 2 baseline and Gate 4 finding:
the dot-smuggling detector fires on `FILE_NM_SUFFIX='.'`, the legacy baseline is clean,
and the shipped `PARAD0011b` rewrite still resolves to a DIFFERENT watched filename
under the current resolver.

## Status

- ✅ Gates 1/2/4 are now **mechanized** (were by-hand); sanitized twins of this run are
  pinned as unit tests (`tests/unit/test_remediation_m0.py`) so the behavior is
  regression-guarded without real values.
- ⏸ **Verdict unchanged: PENDING A3 + B1.** The adjudicator remains the ground-truth
  watched filename from Control-M monitoring (company-side). The resolver's `var.text`
  dot rule was deliberately NOT changed — that is a ground-truth-gated core change.
- ⏸ Gate 3 (greenfield authoring) + Gate 5 (Jira) remain as in the worked example:
  template finalization and ticket submission wait on A3/B1.
- Still stubbed in the component: `XmlDefinitionFormat` (vendor schema acquisition —
  see the corpus stub), `transform`, `jira` (M1).
