# Greenfield Best-Practice Recommendations (D5)

**Corpus:** INTERNAL (governance, **synthesis/recommendation**). **Status:** 🟣 **RECOMMENDATION — 2026-06-17.** **Branch:** `controlm-spinoff`.

> 🟣 **This is a recommendation, not a ratified standard.** Everything here is *proposed* greenfield best practice, grounded in three sources and tagged accordingly:
> **[Ont]** = the DryDocs ontology / resolved-flow model · **[SDLC]** = software-engineering lifecycle practice (determinism, reviewability, change-safety, shift-left) · **[Corp]** = the existing CCB DAT/HLT Control-M standards already digested in this corpus.
> Each recommendation cites *why*. Nothing here changes production; it's the target the spin-off would author and the dev team would ratify. Companion to the cross-tower synthesis in [nfr-consistency-and-greenfield.md](nfr-consistency-and-greenfield.md); each item is destined for the [standards rules registry](../standards-rules-registry.md).

This deliverable is structured to grow. The first worked convention — **job naming & numbering** — is below in full; later conventions (folder structure, variable canonicalization, escalation/SCIM, metadata) follow the same template.

---

## 1. Job naming & numbering — make GUI order == execution order

### 1.1 The observation (what's true today)
Control-M's Planning/Monitoring GUI lists jobs **alphanumerically by job name, top to bottom**, within a (SMART) folder. The internal standard already exploits this: the HLT job name carries a numeric **`<JobCode>`** ordering segment — `P<AppCode><JobFreq><JobCode>_<SOR>_<DataSet_Process>_<Zone>_<Type>` — explicitly to "**group like functions and order jobs top→bottom in the GUI**" ([hlt-naming-standard §2b](hlt-naming-standard.md)):

| Code | Function | | Code | Function |
|---|---|---|---|---|
| 0001 | House Keeping | | 0050 | AWS Trust Ingestion |
| 0010 | AWS File Watcher | | 0060 | AWS CDC / ETL / intermediate |
| 0020 | AWS Placement | | 0070 | CDC / RFND |

DAT uses the same idea via `<SEQ_NO>` (a 3–4 digit job-order sequence, [dat-naming-standard §2c](dat-naming-standard.md)). **[Corp]**

### 1.2 The principle (the recommendation)
> **The job number must be a [linear extension](https://en.wikipedia.org/wiki/Topological_sorting) of the dependency graph, so that reading the folder top-to-bottom is reading a valid execution order.**

Concretely: if job **A** must run before job **B** (B waits on A's OUT condition / B is downstream of A in the resolved flow), then **`number(A) < number(B)`**. When that holds for *every* dependency edge, the GUI's alphanumeric sort is itself a topological sort of the batch — exactly what an operator or reviewer assumes when they read top-down. **[Ont]**

**Important nuance — the number *reflects*, it does not *enforce*.** Control-M's real run order is governed by **conditions/dependencies and scheduling**, not by the name. So the number is a *human-facing fidelity contract*: it makes the cosmetic display order a truthful picture of the dependency order. The greenfield's job is to keep these two in sync — never to let the displayed order lie about the real flow. **[Ont]**

### 1.3 Why (grounding)
- **[Ont]** The dependency edges (`ConditionsIn`/`ConditionsOut` → `DependenciesDerived` in the prerequisite loaders) define a DAG. A correct numbering is *any* topological sort of that DAG. This makes the naming convention a **projection of the ontology** — not a hand-assigned label. The number becomes *derivable*, not *invented*.
- **[SDLC] Reviewability:** a reviewer scanning a folder top-to-bottom should see the actual flow. If 0020 depends on 0050, the GUI misleads — high cognitive cost, real incident risk (operators rerun in the wrong order).
- **[SDLC] Determinism / reproducibility:** if the greenfield generator computes the number from the graph, two runs produce the same names — diffable, regenerable, no artistic drift.
- **[SDLC] Change-safety:** the existing **gap numbering** (0001, 0010, 0020, 0050 — not 1, 2, 3, 4) is good practice: gaps let you insert a new step (e.g. a 0015 pre-processor between FileWatcher and Placement) **without renumbering downstream jobs** — which would otherwise churn every dependent job name, its SCIM row, and its conditions. Keep ≥ a gap of 10 within a functional band. **[Corp]** already does this; the recommendation is to **mandate** it.
- **[Corp]** Functional banding (HK / FW / Placement / Trust / CDC / RFND ranges) groups like-function jobs into contiguous blocks — operationally legible and already the HLT convention.

### 1.4 The lexicographic gotcha (a concrete, checkable failure)
Alphanumeric (string) sort is **not** numeric sort. `"0010" < "0020" < "0100"` is correct **only because the widths are equal and zero-padded.** Un-padded numbers break it:

```
WRONG (unpadded):  _FW_1, _FW_2, ... _FW_10  →  GUI sorts: 1, 10, 2, 3, ...   (10 jumps above 2)
RIGHT (padded):    _FW_0001 ... _FW_0010     →  GUI sorts: 0001 ... 0010      (correct)
```

> **Recommendation:** the order segment is a **fixed-width, zero-padded** integer (4 digits, matching the current 0001–0070 scheme). This guarantees lexicographic order == numeric order — the property the whole convention depends on. **[SDLC]+[Corp]**

### 1.5 Parallel (unordered) jobs
Jobs with **no dependency** between them have no required order. Recommendation: give them **distinct adjacent numbers** within the band, ordered by a **stable, deterministic tiebreak** (e.g. SOR → dataset → type) so regeneration is reproducible, but **document that the order is cosmetic** (they may run concurrently). Don't imply a sequence that doesn't exist. **[Ont]+[SDLC]**

### 1.6 The ideal-greenfield rule (how the engine does it)
At **Gate 3 (Design)**, the generator:
1. Builds the dependency DAG from the resolved flow (conditions in/out).
2. Computes a topological order; assigns **functional band** by job `<Type>` (FW→0010s, Placement→0020s, …) per the governed JobCode map.
3. Assigns **zero-padded numbers with gaps** inside each band, tiebreaking parallel jobs deterministically.
4. Emits the name — so **display order == run order by construction.**

At **Gate 2 (Validate)**, the checker asserts the *existing* numbering is a linear extension of the DAG and flags **inversions** (a job numbered before one it depends on) and **width/pad violations**. → new registry rule **R29** (below).

### 1.7 Anti-patterns (do NOT)
| Anti-pattern | Why it hurts |
|---|---|
| Un-padded / variable-width sequence (`_2` vs `_10`) | Breaks the alphanumeric==numeric guarantee → GUI order is wrong (§1.4) |
| Number that contradicts the dependency order (0020 depends on 0050) | GUI lies about the flow; operators rerun in the wrong order |
| Consecutive numbering with no gaps (0001, 0002, 0003…) | Can't insert a step without renumbering + SCIM/condition churn |
| Hand-assigning numbers per job by eye | Non-deterministic, drifts, not regenerable; can't be validated |
| Reusing one code for several ordered jobs | Ambiguous GUI order; ties unresolved |
| Encoding order in the name but ignoring it in conditions (or vice-versa) | The two pictures diverge — the name stops being trustworthy |

---

## 2. Proposed registry rule

**R29 — Job numbering is a faithful, sortable execution order.**
- **Check (a) sortability:** the order segment is fixed-width zero-padded (no `_FW_10` next to `_FW_2`). **(b) fidelity:** the numbering is a *linear extension of the dependency DAG* — for every edge A→B, `number(A) < number(B)`; flag inversions. **(c) banding:** the number falls in the governed functional band for the job's `<Type>` (FW 0010s, Placement 0020s, …).
- **Engine:** dependency-DAG builder (prerequisite-loader output) + name parser; topological-order assertion. **Sev:** 🟡 should-fix (⚪ for pure cosmetic-tiebreak cases). **Status:** 🟡 provisional.
- **Source:** this doc; [hlt-naming-standard §2b](hlt-naming-standard.md) JobCode map; [dat-naming-standard §2c](dat-naming-standard.md) `<SEQ_NO>`.
- **Greenfield action:** derive the number from the resolved DAG at Gate 3 (display order == run order by construction); validate inversions/padding at Gate 2.

> Relationship to existing rules: complements **R12** (job-naming conformance) and **R13** (name token == derived intent). Where R13 says *the type token must match behavior*, R29 says *the order number must match the flow* — both are "the name must tell the truth about the resolved graph." **[Ont]**

---

## 3. Template for the next conventions (to extend D5)

Each future recommendation follows: **Observation (today, [Corp]) → Principle (the recommendation) → Grounding ([Ont]/[SDLC]/[Corp], with *why*) → Gotchas/anti-patterns → Engine rule (Gate 2 validate / Gate 3 generate) → proposed Rxx.** Candidates queued:
- **Folder structure & SMART-folder grouping** (one flow per folder; sub-folder by platform framework).
- **Variable canonicalization** (already has a ratification source — [command-line-and-variables-standard](command-line-and-variables-standard.md); fold into D5 as a worked convention).
- **Escalation/SCIM defaulting** (dev-queue default, R14) and **metadata single-source** (R16).

Related: [[project-controlm-remediation-spinoff]], [[project-folder-naming-praocg]], [[project-description-metadata-plan]]
