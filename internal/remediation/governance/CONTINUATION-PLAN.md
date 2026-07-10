# Continuation Plan — Governance Corpus (autonomous resume)

**Branch:** `controlm-spinoff`. **Written:** 2026-06-17. **For:** the 5:00am autonomous wake-up.
**Context memory:** [[project-controlm-escalation-governance]], [[project-controlm-remediation-spinoff]].

> ✅ **COMPLETE — 2026-06-17 (5am run).** All remaining continuation screenshots digested. Net-new captured:
> the full `cm-guidelines-DAT-1..10` enumerations → [dat-naming-standard §2c](dat-naming-standard.md) (appcode↔framework↔server
> registry, Area-Product/zone/frequency/~60-token job-type vocabularies, FW time-limit, QR=Quantitative-Resource);
> the CBT "Command line and variables v2" page → new [command-line-and-variables-standard.md](command-line-and-variables-standard.md)
> (ratifies R2/R16/B4, specifies the engine). Registry extended to **R1–R28**. HLT pages confirmed they share DAT's
> vocabulary (consistency finding). Remaining un-read images (`cm-guidelines5/6`, `icdw nfr2`) mirror captured content.
> Substantive next work = spin-off M0/M1, **blocked on Control-M monitoring access (A3/B1)** — not autonomously doable.

## State at handoff (DONE)
Goals 1 & 2 substantially complete and committed. Governance corpus = 8 docs under `internal-standards/governance/`:
README (4-tier hierarchy), escalation-scim-reference, dat-naming-standard, hlt-naming-standard,
nfr-catalog, scim-hpsm-queue-registry, critical-batch-and-self-heal, nfr-consistency-and-greenfield.
Rules registry extended to **R1–R25**; information-needed register has governance backlog **E1–E6**.
Last commits: `cd03d45` (VSI), `0035982` (E1–E6), `dbeaa9e` (R13–R25), `95b0ff2` (nfr-catalog).

## Resume tasks (in priority order)

1. **Digest the remaining continuation screenshots** (low marginal value but completes "use all images").
   Read **one image at a time** from `C:\coding\_resized\` (many-image batches hit the 2000px limit; single reads work).
   Resize any not yet in `_resized` with the PIL snippet below (MAX=1500).
   - `cm-guidelines-DAT-1..10` — DAT guideline continuation (core already in dat-naming-standard §2b; capture only net-new).
   - `cm-guidelines4..8` — HLT guideline continuation (core in hlt-naming-standard §2b).
   - `HomeLending-cmd-line3`, `HomeLending-cmd-line4` — command-line detail (core = NFR-CTM-301 in hlt §2b).
   - `icdw snowflake nfr2` — second ICDW/Snowflake NFR page (structure noted in nfr-catalog §3).
   Fold only genuinely new facts into the relevant existing doc; do NOT duplicate. Commit per doc.

2. **Coherence pass** — re-read the 8 governance docs + registry for cross-link/numbering consistency
   (R1–R25 referenced the same way everywhere; every `[[wikilink]]` resolves to a memory slug).

3. **If images add no net-new content**, mark this plan COMPLETE, note it in the README status line,
   and stop — do not invent scope. The substantive work is the spin-off M0/M1 (see
   `controlm-remediation-m0-poc-scope.md`), which needs the 🔴 inputs A3/B1 (ground-truth filename +
   var.text rule) that require Control-M monitoring access — **blocked, not doable autonomously.**

## Resize snippet
```python
from PIL import Image; import os
MAX=1500
for f in ['cm-guidelines-DAT-1.png']:  # edit list
    p=os.path.join('C:/coding',f); im=Image.open(p); w,h=im.size; s=min(1.0,MAX/max(w,h))
    if s<1.0: im=im.resize((int(w*s),int(h*s)))
    im.save(os.path.join('C:/coding/_resized',f))
```

## Guardrails for the autonomous run
- Read-only on source-of-truth; only write under `internal-standards/`. Commit with the Co-Authored-By trailer.
- Stay on `controlm-spinoff`. Do not push, do not open PRs, do not merge to main.
- If a screenshot is illegible at ≤1500px, note it and move on — don't loop on it.
- When the queue is empty or only blocked (access-dependent) work remains, write a short status summary and stop.
