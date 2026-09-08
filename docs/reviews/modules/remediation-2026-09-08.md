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

*(step 4)*

## Lens 2 — technical debt

*(step 5)*

## Ranked

*(step 6 — the ranked list; its presence is what marks this report complete)*

## Cross-links

*(step 6 — to the other lens in this firing, and to earlier slots)*

## Candidates for grooming

*(step 6)*
