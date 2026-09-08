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

**The cleanest escape-hatch counts in the sweep**, and one guard that reintroduces a
defect class this repo fixed on `main` earlier today.

| hatch | count | slot 4 | slot 3 | slot 2 |
|---|---|---|---|---|
| `# type: ignore` | **0** | 1 | 0 | 6 |
| `# noqa` | **0** | 2 | 0 | 2 |
| `cast(` | **0** | 0 | 0 | 0 |
| `: Any` / `-> Any` | **0 / 0** | 1 / 0 | 4 / 0 | 41 / 16 |
| `TODO` / `FIXME` | **0** | 0 | 0 | 0 |
| `# pragma: no cover` | 4 | 2 | 0 | 9 |

Zero on every axis but `pragma`, and all four of those are on genuinely unreachable
branches, each explaining itself at the site (`equivalence.py:73` *"the probe always
resolves"*; `xml_io.py:421` *"expat errors first"*; `xml_io.py:1215` *"binary I/O is
exact"*). `ruff` clean, 311 scoped tests green.

### L2-1 — a guard reads raw source where the AST guard beside it already covers the same marker

`tests/unit/test_remediation_changes.py:322-323`:

```python
assert not hasattr(changes, "write_transaction")
assert "execute_write" not in open(changes.__file__, encoding="utf-8").read()
```

The first line reads the imported object and is correct. **The second is a raw substring
scan over source text**, comments and string literals included — the exact shape J66
names: *a guard that greps for a forbidden pattern also matches the comment explaining
why it is forbidden, so it fails on the explanation and teaches people to stop writing
explanations.* In a repo whose comments carry its rulings, that is the expensive kind of
brittleness. Add a line to `changes.py` explaining why `execute_write` must never appear
there and this test goes red on the explanation.

**It is also redundant.** `tests/unit/test_remediation_no_graph_write.py` declares
`WRITE_MARKERS = {"execute_write", "write_transaction", "begin_transaction"}` (`:17`) and
**walks the whole `drydocs_remediation` package AST** (`:24-34`) checking referenced
names. `changes.py` is inside that package, so `execute_write` is already guarded
correctly, by name, one file away — and the test containing the substring line even
imports that guard module deliberately (`:319`) to pin the claim that the structural
guards needed zero changes. The substring assertion is not the point of the test; it is a
belt-and-braces line that reintroduces the defect class the AST guard exists to avoid.

**This is the same defect class as LOAD5**, found by slot 2 this morning and fixed on
`main` at `e15d319a` — `test_recursive_sql_cyclic_type_disabled` asserted that a comment
phrase was present rather than that the predicate was absent from executable SQL. **Two
slots, two independent instances, one class.** That is the second pattern this sweep has
found recurring across modules, and unlike the completeness one it has a mechanical
remedy already in the repo: `tests/source_scan.py` (`code_only`, `called_names`).

**Cheapest correction:** delete line 323. The AST guard covers it, by name, package-wide.
If a belt-and-braces check is still wanted at this site, route it through
`source_scan.code_only` so it reads code rather than prose. Line 322 stays as it is.

### What was checked and cut

- **`xml_io.py` is 1,277 lines, 29% of the module.** Cut: it is a purpose-built lossless
  splicer that parses only to LOCATE, using `expat` byte offsets, because
  `fix-package.md` §XML requires the emitted file to diff by exactly the approved changes
  and — measured on this repo's own fixtures — both `ElementTree` and `lxml` rebuild
  start tags from an attribute dict, producing *"the 100%-diff file no developer can
  review"*. A justified reimplementation with its measurement recorded is not debt.
- **Two XML readers in one component.** Cut: `xml_bridge.py` says of itself that
  *"reading was solved twice over"*, but it adapts the LINEAGE component's staged
  `controlm_xml` output while `xml_io` reads definition XML directly — different inputs,
  and `xml_bridge` has a live caller (`drydocs/cli.py`).
- **`jira.py` and `changedoc.py` have no producer-side caller** (496 lines). Cut, and the
  reason is in the code: `jira.py` is *"the component's ONLY side-effect boundary"* and
  its REST implementation is **company-side configuration** — credentials never live in
  the engine (PUBLISH-BOUNDARY.md). Absent here is not-yet-ported, not broken.

## Ranked

*(step 6 — the ranked list; its presence is what marks this report complete)*

## Cross-links

*(step 6 — to the other lens in this firing, and to earlier slots)*

## Candidates for grooming

*(step 6)*
