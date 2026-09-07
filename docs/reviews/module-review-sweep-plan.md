# Module review sweep — plan

**Status:** ACTIVE from 2026-09-05
**Venue:** worktree `.claude/worktrees/review-sweep`, branch `review/module-sweep`
**Cadence:** one slot every two days, ten slots, a twenty-day cycle
**Lenses:** `/system-design` then `/tech-debt`, in that order, one firing
**Pen (CLAUDE.md section 0):** `review:sweep` — this branch and
`docs/reviews/modules/` only

---

## 1. What this is

A standing, rotating review of every first-party module, two lenses per module,
one module family per firing. It exists because the three-pass review of `web/`
on 2026-09-05 found eight issues in a module nobody thought was in trouble, and
because the most valuable finding of that review was only visible across passes:
the same root cause appeared eight times in three different lenses.

Each firing produces one committed report. The reports accumulate as a series, so
the second pass over a module in a later cycle can say what moved.

### What this is not

- **Not a gate.** Nothing here blocks a commit, a push, or a release. Findings are
  input to grooming, not verdicts.
- **Not a backlog writer.** The sweep never mints an id, never edits
  `docs/restructure/backlog/`, never renders the board. Findings worth items are
  named in the report's final section and groomed by a human through the normal
  `groom-backlog` path.
- **Not an ADR author.** A report may nominate ADR candidates. It does not write
  them, and it does not renumber anything.
- **Not a refactor.** The sweep changes no module code. Ever. It reads, measures,
  and writes one file.

---

## 2. The rotation

Ten slots. Sized so a firing spends roughly comparable effort on each, which flat
per-module rotation does not: the largest module is forty times the smallest.

| slot | slug | module family | first-party lines |
|------|------|---------------|-------------------|
| 1 | `core` | drydocs-core | 14,876 |
| 2 | `load` | drydocs-load | 14,538 |
| 3 | `lineage` | drydocs-lineage | 6,984 |
| 4 | `api` | drydocs-api | 6,717 |
| 5 | `remediation` | drydocs-remediation | 4,418 |
| 6 | `review-agents` | drydocs-review + drydocs-agents | 4,851 |
| 7 | `port-docgen-docmeta` | drydocs-port + drydocs-docgen + drydocs-docmeta | 3,770 |
| 8 | `plan-deepdoc-libs` | drydocs-plan + drydocs-deepdoc + drydocs-libs | 2,188 |
| 9 | `web` | drydocs-web | 22,715 |
| 10 | `seams` | cross-module seams | the boundary itself |

The **slug is the key** the derivation in the next subsection reads and the report
filename carries (`docs/reviews/modules/<slug>-<YYYY-MM-DD>.md`). It is fixed here so
two firings cannot spell one family two ways and each conclude the other never ran.

A slot's **scope is read, never retyped.** For slots 1 to 8 it is the dotted prefixes of
every `COMPONENT_GROUPS` group whose `COMPONENT_MODULE` value is one of the family's
modules, plus `CORE_PREFIXES` for slot 1 - all three from
`drydocs_core/component_map.py`, the importable object (J37), so a module that moves
between components moves slot with it. Slot 9 is the two `drydocs-web` directories in
`MODULE_MAP.md`'s top-level table (`web/`, `drydocs-icons/`); slot 10 is
`tests/unit/test_module_boundary.py` and `component_map.py` themselves. The report's
`scope:` line records what was resolved at that firing.

Sizes measured 2026-09-05, excluding `.venv`, `node_modules`, `dist` and
`__pycache__`. They are a sizing aid, not a contract; re-measure when a slot feels
wrong rather than trusting the table.

**Slot 9 (`drydocs-web`) was reviewed on 2026-09-05** across three lenses
(`/architecture`, `/system-design`, `/tech-debt`); the report is
`docs/reviews/modules/web-2026-09-05.md`, landed by the secondary review so the
derivation below sees it and the second pass has something to move against. It sits
at the end of the first cycle deliberately, so the sweep covers unreviewed ground
before returning to it.

**Slot 10 is not a module.** It reviews what per-module slots structurally cannot
see: whether the module boundary invariant actually holds
(`tests/unit/test_module_boundary.py` and `drydocs_core/component_map.py`), whether
two modules disagree about a shared contract, and whether a finding recorded in one
earlier slot has a twin somewhere else. The `web/` review's strongest conclusion —
one root cause recurring across eight findings — was of exactly this kind and could
not have been reached from inside a single lens.

### Slot state is derived, never stored

There is no cursor file. Consistent with how the backlog derives `next_ready` and
never stores it, each firing computes its own slot:

1. List `docs/reviews/modules/`.
2. For each slot, find the most recent report date whose filename starts with the
   slot's slug.
3. If that most recent report has no `## Ranked` section, it is a partial report:
   resume it (section 5) instead of deriving a new slot.
4. Otherwise take the slot with no report, or the oldest report; break ties by slot
   number.

This is self-correcting. A missed firing does not desynchronise anything, a firing
that dies halfway leaves a partial report that the next firing finishes rather than
duplicating, and two firings can never silently review the same slot twice in a row.

---

## 3. The two lenses

The lenses are already defined as skills (`.claude/skills/system-design/`,
`.claude/skills/tech-debt/`). What follows is the scoping that made the `web/` pass
useful, not a redefinition of them.

### Lens 1 — system design

Asks what happens when the module is under load, partly down, slow, or shared
between people. Concretely, for each module:

- **Contracts at the edges.** What does this module promise its callers, and where
  is that promise written down rather than implied? Does the code agree with it?
- **Completeness and truncation.** Does any path return a partial answer that reads
  like a complete one? Limits, caps, page sizes, silent fallbacks. This was the
  top `web/` finding and it generalises: a governance product that quietly
  truncates is worse than one that fails.
- **Failure behaviour.** What does a caller see when a dependency is down? Is
  loading distinguishable from hung? Is there a timeout, a cancel, a retry?
- **State and lifetime.** What persists, keyed by what, cleared by what.
- **Provenance and trust.** Can a consumer tell whether an answer came from the
  graph, a fixture, or a constant? This is the product thesis, so it outranks
  ordinary correctness findings.
- **Observability.** If this module started producing wrong answers, what would
  notice?

### Lens 2 — technical debt

Asks what it costs to keep the module going, and answers with numbers rather than
judgement wherever a number exists.

- **Run the repo's own instruments first, before asserting anything.**
  `poetry run pytest -q` scoped to the module, coverage if it can be measured, the
  guard tests that cover this module, `ruff check`, the boundary test. A review
  that reports a measurement beats one that reports an impression, and the `web/`
  pass found that the instruments were installed and simply never read.
- **Escape hatches.** Casts, ignores, suppressions, untyped seams, `Any`. Count
  them and locate the cluster; they cluster at exactly one seam and that seam is
  the finding.
- **Duplication with a governing abstraction beside it.** The recurring shape in
  this repo: a correct helper exists, and the call sites reimplement its body.
  Count the copies.
- **Dead weight.** Unimported modules, declared-and-unused dependencies, one-file
  directories, misplaced files.
- **Suppressions that suppress nothing.** Directives for tools that are not
  installed, thresholds not enforced, warnings with no gate under them.
- **Test topology against risk.** Not coverage percentage alone: whether the tests
  are where the complexity is.

### Both lenses, both times

- **Open with what holds.** A defect list is not a review. The `web/` passes each
  led with what was working and why, which is what made the findings credible.
- **Rank the findings.** A flat list forces the reader to re-derive priority.
- **Separate chosen debt from unnoticed debt.** This repo records its rulings in
  code comments. A thing explained in a comment is a decision; treat it as one, and
  say so. Report it only as the cost of a decision, never as an oversight.
- **Cross-link.** To the other lens in the same firing, and to earlier slots.

---

## 4. Per-firing protocol

Every step below runs in `.claude/worktrees/review-sweep`, on branch
`review/module-sweep`, and nowhere else.

**0. Establish the venue.**
Confirm the branch with `git branch --show-current` — it must be
`review/module-sweep`. Confirm the tree is clean. Then `git pull --ff-only` and
`git merge --no-edit origin/main`, so the review reads current code, not the code as
of the last firing. **Merge, never rebase**: the branch is pushed and both machines
may run a firing, so rewriting its history strands the other machine's copy (the J31
shape) and the guard in step 6 is `git push` without `--force`, ever. Only this plan
and `docs/reviews/modules/` can conflict; resolve on the branch.

**1. Derive the slot** by the rule in section 2. Announce it.

**2. Open the report file immediately, before reading any module code.**
Path: `docs/reviews/modules/<slug>-<YYYY-MM-DD>.md`. Write the J63 stamp and the
empty section skeleton. Commit it. This is not ceremony — see section 5. If step 1
derived a partial report instead, re-read it and continue from its first empty
section; do not open a second file for the same slot.

**3. Measure before reading.** Run the module's tests, the guards that cover it,
the linter, and whatever counts the lenses call for. Record raw numbers into the
report as they arrive.

**4. Lens 1 — system design.** Fill its section. Commit when the section is done.

**5. Lens 2 — technical debt.** Fill its section. Commit when the section is done.

**6. Close.** Write the ranked list, the cross-links, and the "candidates for
grooming" section. Commit and **push** — `git push -u origin review/module-sweep`
the first time, `git push` after. An unpushed report is invisible to the other
machine, which is the J31 failure this repo has already paid for twice.

**7. Report to the terminal** what slot ran, the top three findings, and the file
path. Nothing else.

---

## 5. Surviving autocompact

A two-lens review of a large module will exceed one context window. The session
compacts itself mid-run. The protocol above is built for that, and the mechanism is
step 2: **the report file on disk is the durable memory, not the conversation.**

Rules that follow from it:

- **Write findings into the file as they are established, never at the end.** A
  finding that exists only in the conversation is lost at the next compaction.
- **Commit at every section boundary.** A firing that dies after lens 1 leaves lens
  1 landed and pushed; the next firing sees a partial report and finishes it rather
  than starting over.
- **Never hold a list of files-still-to-read in the conversation.** Put it in the
  report as a checklist section and tick it in the file. Delete the section before
  the final commit.
- **After a compaction, re-read the report file first.** It states the slot, the
  stamp, what is done, and what is not. Resume from it; do not reconstruct from the
  summary.
- **Re-verify anything a summary asserts before repeating it.** A recalled fact
  about a file or a flag may be a summary artifact. This is the standing
  verify-before-asserting rule, and compaction is exactly where it bites.

---

## 6. Isolation — what the sweep must never touch

The repo runs concurrent sessions on two machines with a lane protocol. The sweep
is a third writer and stays inside its own fence.

- **Only** `docs/reviews/modules/` and this plan file, **only** on branch
  `review/module-sweep`, **only** in the `review-sweep` worktree.
- **Never** `main`. Never a `feat/`, `fix/`, `port/` or `wip/` branch. Never
  another worktree's directory.
- **Never** `docs/restructure/backlog/` — no item files, no `IDEAS.md`, no epics.
- **Never** a governed render: `docs/plan/board.html`, `docs/plan/roadmap.html`,
  `docs/design/*.html`, `web/src/generated/*`. The sweep does not run
  `render_board.py` and does not need to.
- **Never** module code, config, or tests. The sweep is read-only outside its
  report.
- **Never** `git stash` in any form. The worktree stack is shared.
- **Never the session ritual's close steps** (CLAUDE.md section 0, step 3): no
  `render_board.py`, no `render_design_doc.py`, no CI check, and **no
  `knowledge/depgraph-snapshots/snapshot.ps1`**. Those record the state of TRUNK after
  a trunk push; the sweep pushes no trunk commit, so there is nothing for them to
  record, and `snapshot` is a Lane A pen (`lane-handoff` skill, rule 2: the machine
  holding `backlog` renders once and snapshots once at its close). A firing that ran
  the snapshot would write a trunk artifact from a branch venue. Ruled by the
  secondary review, 2026-09-05.
- **No merge to main by the sweep.** The branch accumulates; a human merges when the
  findings are wanted in trunk. The first such merge was the secondary review's own
  (2026-09-05, `--no-ff`, docs-only), which put this plan and the slot 9 report on
  `main` so DOC4's `inputs` resolve there and backlog items can cite the report file.

If a firing finds something genuinely urgent — a live credential, a data-loss path,
a broken publish boundary — it still writes only the report, and says so at the top
of the terminal summary in one line. Acting on it is a human call.

---

## 7. Publish boundary

Reports live under `docs/`, so their ceiling is **Internal-Public**
(`PUBLISH-BOUNDARY.md`, `config/classification.yaml`).

A report reviewing a module that reads from `internal/` or `internal-local/`
describes **mechanism, never values**. No SIDs, no credentials, no server
addresses, no schema-qualified real identifiers, no roster names, no production
data. "The extractor joins on the escalation table's component column" is
publishable; the column's contents are not. When a finding cannot be stated without
a protected value, state the shape and note that the value is withheld.

Two style rules ride along, both already standing: US business-technical English
per `docs/style/us-business-english.md`, and no decorative or enclosed glyphs as
labels — plain numbers and letters, because the enclosed forms render unreadably
small in a terminal.

---

## 8. Report template

```markdown
# <family> — module review, <YYYY-MM-DD>

reviewed_commit: <sha>
reviewed_branch: review/module-sweep (merged origin/main <sha>)
reviewed_port_base: n/a — producer-side review
slot: <n> of 10
lenses: system-design, tech-debt
scope: <the dotted prefixes and directories this family covers, resolved from
       component_map.py at this firing - section 2>
prior report: <path, or "first pass">

## Measured

<raw numbers first: test counts, pass/fail, coverage, file and line counts,
guard results, lint results. Numbers before prose, so the prose has to answer
to them.>

## What holds

<what is working, and why it works. Lead here.>

## Lens 1 — system design

### S1 — <one-line claim>
<evidence with file:line, then consequence, then the cheapest correction>

## Lens 2 — technical debt

### T1 — <one-line claim>
<same shape>

## Ranked

1. <id> <claim>

## Cross-links

- to the other lens in this firing
- to findings in earlier slots that share a root cause
- to the open ADR candidates list

## Candidates for grooming

<Findings a human might turn into backlog items. NAMED ONLY — no ids minted,
no item files written, no epic assigned. The groom-backlog skill owns that.>
```

---

## 9. Quality bar for a finding

A finding that does not meet all four is cut before the report is committed.

1. **Located.** A path and a line, or a command and its output. Not "several
   places" — the count and the list.
2. **Consequential.** States what goes wrong for whom. A finding whose consequence
   cannot be written down is a preference.
3. **Verified on this tree.** Not recalled, not inferred from a doc, not carried
   from a prior report. The doc may be stale; the tree is not.
4. **Correctable.** Names the cheapest correction, even when the correction is
   "decide and record", and says so plainly when the cheapest correction is a gate
   decision rather than a code change.

Two repo guards apply to the reviewer as much as to the code being reviewed. Read
the importable object rather than a human-facing render — `app.registered_commands`,
`LOADER_REGISTRY`, `QUERY_SPECS`, `component_map.py` — never `--help` output (J37).
And read code rather than the prose around it: use `tests/source_scan.py`
(`code_only`, `imported_modules`, `called_names`) when a claim depends on what the
source actually does, because a raw substring search matches the comment explaining
why something is forbidden (J66).

---

## 10. Limits, and re-arming

The cron that drives this is **session-only**. It lives in one Claude session's
memory, disappears when that session exits, and auto-expires after seven days.
At a two-day cadence that is roughly three firings per arming. It also fires only
while that session's REPL is idle.

So the cron is a convenience, and **this plan is the durable half**. Any session,
on any machine, can run a slot by hand: read this file, follow section 4. Nothing
in the protocol depends on the cron having fired.

To re-arm in a fresh session, ask for the module review sweep to be scheduled and
point at this file; the standing schedule is 06:47 on odd-numbered days
(`47 6 */2 * *`), which yields a two-day gap all month and a one-day gap across the
31st-to-1st boundary. That irregularity is not worth correcting.

---

## 11. Provenance of this plan

Written 2026-09-05, from the three-pass lens review of `web/` run the same day
(`/architecture`, `/system-design`, `/tech-debt`, reviewed_commit 738028d7). The
lens scoping in section 3, the finding bar in section 9, and the compaction
mechanism in section 5 are all distilled from what worked and what nearly failed in
that run.

Secondary review 2026-09-05 (`docs/reviews/module-review-sweep-plan-review-2026-09-05.md`,
Lane A desktop, subject `e44cc5b4`): added the slug column and the read-not-typed
scope rule (section 2), the partial-report resume rule (sections 2 and 4), replaced the
rebase in step 0 with a merge, excluded the trunk close ritual and the depgraph
snapshot from the sweep (section 6), and landed the slot 9 report the derivation had no
way to see.
