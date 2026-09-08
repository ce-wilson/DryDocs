# drydocs-remediation — module review, 2026-09-08

reviewed_commit: 3da5dfbd
reviewed_branch: review/module-sweep (worktree review-sweep; origin/main merged at the start of this firing — it had moved since slot 4, carrying REV1.yaml and a new depgraph snapshot)
reviewed_port_base: port-base-20260905 — producer-side review
slot: 5 of 10 (slug `remediation`)
lenses: system-design, tech-debt (the standing sweep's two; architecture was a one-off on the web slot)
scope: the dotted prefixes of `COMPONENT_GROUPS['remediation']`, read from `drydocs_core/component_map.py`
  (J37, the importable object) at this firing — one prefix: `drydocs_remediation`
prior report: first pass

- **Reviewed at:** commit `3da5dfbd` on `review/module-sweep`, port base `port-base-20260905`; venue MSI. *Absent here reads as not-yet-ported, not as broken (docs/style/review-provenance.md).*

Opened before any module code was read (section 4 step 2): this file is the durable
memory for the firing, so a session that compacts mid-review resumes here rather than
starting again. Sections below are filled in order and each is committed as it closes.

**What this module is, from the plan and the component map only — before reading it.**
`drydocs-remediation` is the two-tier fix model spun out in G3 (ADR 0002-B): a detector
that finds standards violations in Control-M definitions, a transform engine for Tier-1
fixes, and a Jira handoff. Its output DRIVES CHANGES TO PRODUCTION JOB DEFINITIONS, which
sets the bar for this review: a false positive here is not a wrong number on a page, it
is a change proposed against a live job. The `archival.py` precedent in slot 3 (`no axis
proves absence`, because the output drives deletion) is the standard to hold this to.

## Measurements

Taken before any module code was read.

| measure | value |
|---|---|
| first-party Python in scope | **4,418 lines**, 11 files — exactly the plan-table size (4,418 on 2026-09-05), the **only slot so far that has not grown** |
| largest unit | `xml_io.py` — 1,277 lines, 29% of the module |
| next largest | `detect.py` 862 · `profile.py` 553 · `jira.py` 359 · `changes.py` 311 |
| rules in the registry | **45** (`internal/remediation/standards-rules-registry.md`, R1–R44 with R39a/R39b) |
| rules the detector implements | **17** — R1 (dot-smuggling) + R2 + R30–R38 + R39a/R39b + R40–R42 + R44 (read as the object, J37) |
| tests naming the module | 22 files |
| scoped suite | **311 passed, 9 skipped**, 23s |
| `ruff check drydocs_remediation/` | clean |

**The first slot to come in exactly at its plan size.** Slots 3 and 4 were +16% and +36%
over three days; this one is unchanged, which is consistent with a component whose last
build (G3) closed and whose open work is gated rather than in progress.

**The pipeline is six stages, and four of them are checks rather than transforms:**
`detect` → `transform` → `equivalence` (offline proof) → `corroborate` → `changes` /
`changedoc` → `jira`. That ratio is the right shape for a component whose output drives
changes to production job definitions, and Lens 1 tests whether each check says what it
actually proved.

## Lens 1 — system design

**This module holds itself to the highest evidence standard in the sweep, and one of its
outputs does not meet it.** The finding is measured against the module's OWN discipline,
not an external one — which is why it is worth reporting on a component this careful.

### L1-1 — a findings list is emitted with no declaration of its own rule coverage

`detect_all(definitions)` returns a bare `list[Finding]` (`detect.py:464`). Each finding
is well built — `rule_id` keys into the registry, `severity` uses the registry's
vocabulary, and `ratified: bool` gates action (*"only ratified rules may drive greenfield
changes"*, `:57`). What the return value does not carry is **what was checked**.

The numbers make the gap concrete:

| | |
|---|---|
| rules declared in `internal/remediation/standards-rules-registry.md` | **45** |
| rules `detect` implements | **17** (R1, R2, R30–R38, R39a, R39b, R40–R42, R44) |
| rules never evaluated | **28** — the contiguous block R3–R29, plus R43 |

`profile.py:340` embeds that list into the profile output — `findings=[asdict(f) for f in
detect_all(definitions)]` — and the profile explicitly *"asserts nothing"* about them;
they *"ride alongside"* (`:306`). Nothing in `detect.py`, `profile.py` or `changedoc.py`
states which rules produced the list or which were not run. Searched for it: `detect.py`
contains no `rules_checked`, `coverage` or equivalent; `CONFORMANCE_RULE_IDS` (`:90`) is
an internal tuple, not part of any output.

**Consequence, and it is this module's own stated failure mode.** A run over a folder set
that returns few findings — or none — reads as *"these jobs conform to the standard"*. It
means *"no violations among the 17 of 45 rules this build implements"*. Because the output
drives changes to production job definitions and a Jira handoff, "clean" is a result
someone acts on: it ends an inspection. A reader cannot distinguish a conforming estate
from an unevaluated one without opening `detect.py` and diffing its tuple against the
registry, which is what this firing had to do.

**Why it is a finding on THIS module rather than a general wish.** Its siblings all state
their own coverage, and one of them was fixed for exactly this defect:

- `equivalence.py:14-18` is **three-valued on purpose** — proven / diverged / not proven —
  and says why: the original collapsed "compared and equal" with "nothing to compare" into
  `equivalent=True`, so *"a run that broke six CMDLINEs reported PASS 12/12"* (defect B',
  found by the 2026-08-12 POC). Its rule is now **"no evidence is never evidence."**
- `profile.py:17-20` refuses to default an unknown: a slot with no value is
  `not-supplied`, **never** a default, because *"inventing one is how a proposal becomes a
  wrong fact nobody re-checks."*
- slot 3's `archival.py` states its body-copy coverage **in its own output**, so a
  metadata-only run says so.

So the standard exists, is written down three times, and was not applied to the findings
list itself.

**Cheapest correction:** return the coverage alongside the findings — the evaluated rule
ids (`CONFORMANCE_RULE_IDS` plus R1) and, ideally, the registry ids not evaluated, so an
empty list carries its own denominator. It is a return-shape change with one caller
(`profile.py:340`) and no gate question attached: stating what you checked asserts nothing
new about meaning.

### L1-2 — what this module already gets right, recorded so no later firing re-audits it

- **Action is gated separately from detection.** `ratified: bool` on every finding means
  an unratified rule can be reported without being allowed to drive a change. Detection
  and authority are different questions and the type keeps them apart.
- **The equivalence proof compares RESOLVED behaviour, not definitions.** Both sides go
  through `drydocs_core.orchestration.controlm.resolve_job` — *"the same engine the
  loaders trust"* — so cosmetic definition differences pass and behavioural ones fail
  (`equivalence.py:1-8`). Using the shared resolver rather than a local reimplementation
  is the G3/0002-B rule holding.
- **A known limitation is named at the point of use, with its adjudicator.** The `%%var.text`
  dot question is recorded in `equivalence.py:19-24` as UNCONFIRMED, with the warning that
  a divergence involving that shape *"may be the resolver, not the definition"*, and the
  instruction not to change core resolver semantics without the ground-truth watched
  filename. That is the same open B1 question the `smuggling-dot` eval case tracks — the
  module and the eval case agree, independently.

## Lens 2 — technical debt

*(step 5)*

## Ranked

*(step 6 — the ranked list; its presence is what marks this report complete)*

## Cross-links

*(step 6 — to the other lens in this firing, and to earlier slots)*

## Candidates for grooming

*(step 6)*
