# drydocs-port + drydocs-docgen + drydocs-docmeta — module review, 2026-09-08

reviewed_commit: b7fb5f54
reviewed_branch: review/module-sweep (worktree review-sweep; origin/main merged at the start of this firing — it had moved since slot 6, carrying tests/unit/test_never_port_citations.py and tests/unit/test_port_drops.py, both in this slot's subject area)
reviewed_port_base: port-base-20260908 — producer-side review
slot: 7 of 10 (slug `port-docgen-docmeta`)
lenses: system-design, tech-debt (the standing sweep's two; architecture was a one-off on the web slot)
scope: the dotted prefixes of `COMPONENT_GROUPS['port']`, `['docgen']` and `['docmeta']`, read from
  `drydocs_core/component_map.py` (J37, the importable object) at this firing — 10 prefixes:
  `drydocs.design_doc`, `drydocs.doc_outline`, `drydocs.doc_pdf`, `drydocs.docgen`,
  `drydocs.plan_ideas`, `drydocs.port`, `drydocs.port_backlog_union`, `drydocs.port_preflight`,
  `drydocs.port_rename_detect`, `drydocs_docmeta`
prior report: first pass

- **Reviewed at:** commit `b7fb5f54` on `review/module-sweep`, port base `port-base-20260908`; venue MSI. *Absent here reads as not-yet-ported, not as broken (docs/style/review-provenance.md).*

Opened before any module code was read (section 4 step 2): this file is the durable
memory for the firing, so a session that compacts mid-review resumes here rather than
starting again. Sections below are filled in order and each is committed as it closes.

**Three modules, and the port half is the repo's highest-consequence surface.** The port
component decides what crosses from this producer repo to the company one. A false
positive there is not a wrong number on a page — it is internal material leaving the
publish boundary, or a never-port document crossing it. `PUBLISH-BOUNDARY.md` and
CLAUDE.md §3 are the standard this half is measured against, and the sweep's own recurring
question ("does a result state the limits of its method") is unusually sharp for a
preflight that answers "safe to port".

**Known inheritance from slot 6, not to be re-reported here.** Ten of the eighteen ADR
0018 D4 re-export shims live in this slot's prefixes (`design_doc`, `doc_outline`,
`doc_pdf`, `plan_ideas`, `port_backlog_union`, `port_preflight`, `port_rename_detect` and
siblings). Slot 6 found that their stated removal trigger fired today and that no item was
minted, and recommended grooming it ONCE across all four components. This report counts
them and does not re-derive the finding.

## Measurements

Taken before any module code was read.

| module | lines | shape |
|---|---|---|
| `drydocs/port/` | **2,786** | 9 files — `port_rename_detect` 638, `port_preflight` 544, `port_completeness` 463, `port_drops` 317, `reconcile_before` 308, `port_backlog_union` 250, `gate_log_redactions` 178, `dispositions` 82 |
| `drydocs/docgen/` | **1,189** | 5 files |
| `drydocs_docmeta/` | **1,105** | package |
| ADR 0018 shims in scope | **84** | 7 files × 12 lines |
| **combined** | **5,164** | against the plan table's 3,770 — **+37%** |

| both halves | |
|---|---|
| tests naming any of the three | **26** files |
| scoped suite | **485 passed, 9 skipped**, 43s |
| `ruff check drydocs/port/ drydocs/docgen/ drydocs_docmeta/` | clean |

**Correction to this report's own skeleton.** The skeleton said ten of slot 6's eighteen
shims live in this slot's prefixes. The real count is **seven** — `design_doc`,
`doc_outline`, `doc_pdf`, `plan_ideas`, `port_backlog_union`, `port_preflight`,
`port_rename_detect`. The remaining eleven are slot 6's eight, slot 8's `plan_board` and
`plan_roadmap`, and one package `__init__`. Recorded rather than silently edited, because
a later reader comparing the two numbers should see which one was checked.

**Five of seven slots have now come in over the plan table** (+37% here, after +49%, +36%,
+16%, one exactly on). The pattern is stable enough to stop being a per-slot note; slot 6
already raised it as a candidate for slot 10.

## Lens 1 — system design

**The port preflight certifies a base that does not exist.** Every range-derived check
passes when the range is empty, and the range is empty whenever git fails — including when
the base ref is mistyped. This is the sweep's recurring pattern at the surface with the
highest consequence in the repo: the gate that decides what crosses the publish boundary.

### L1-1 — a bad base makes the preflight cleaner, not louder

`_git` (`port_preflight.py:359-366`) runs with `check=False` and returns **only
`.stdout.strip()`**. The return code and stderr are discarded, so a `git log` against a
nonexistent revision — which prints `fatal: bad revision` to stderr and exits non-zero —
returns the empty string, indistinguishable from a genuinely empty range.

`range_commits` (`:369-377`) iterates that empty string and returns `[]`. `run_checks`
(`:425`) then feeds it to the range-derived checks, and `CheckResult` (`:192-196`) is
**two-valued** — `name`, `passed: bool`, `detail: str`. There is no state for *could not
evaluate*.

**Demonstrated on this tree rather than argued:**

```
real base   (port-base-20260908)        -> 38 commits
bogus base  (port-base-NOPE-does-not-exist) -> 0 commits
added_documents(bogus)                  -> 0 docs
uncited_commits([], text)               -> []      # the check PASSES
```

So the uncited-commit check passes, the cited-path check (`unresolved_citations`, fed by
`added_documents`, same `_git` path) has nothing to resolve and passes, and any other
range-derived check passes. **The worse the base, the greener the certification.**

**Consequence, and why it ranks above every other finding this sweep has produced.** This
module exists because ports kept starting from uncertified bases — its own docstring
records the 2026-08-09 cycle lost to exactly that, and two real failures that *"would have
read as port-introduced"*. A preflight that answers "certified" for a base it could not
read reproduces the failure it was built to end, in the one direction nobody re-checks: a
green preflight is the signal to proceed, and what proceeds is material crossing from this
repo to the company one. The checks that go quiet are precisely the ones about
completeness and citations — what is in the range, and whether new documents cite paths
that resolve.

**Cheapest correction, and it is small.** Make `_git` fail loudly: capture `returncode`
and `stderr`, and raise (or return a sentinel) rather than returning `""` for a non-zero
exit. Every caller in this module already assumes success, so the failure currently has
nowhere to surface. A second, independent layer worth having: give `CheckResult` a third
state — the vocabulary already exists two slots over, in `equivalence.py`'s **not proven**
— so a check that could not evaluate reports as such instead of as a pass. A guard belongs
with it: nothing today would notice this regressing, because the wrong behaviour is
silence.

### L1-2 — the same two-valued shape, one layer up, in `port_completeness`

`port_completeness.py` (463 lines) is the module whose name is this sweep's throughline,
and it inherits the same input path: it reads the range through the same helpers. The
finding above is the root; this is where it surfaces to a human as a completeness claim.
Recorded separately so that fixing `_git` is understood to fix both, and so a later firing
does not read L1-1 as an isolated helper bug.

### L1-3 — what this slot gets right, recorded so no later firing re-audits it

- **Every check names the failure that motivated it.** The docstring is a list of dated
  incidents — the 2026-08-09 undoable-phase cycle, the `FORCE_COLOR` failure, the duplicate
  `Idea-101` from a two-session id collision, and Idea-110's doc branch whose *"Approved /
  canonical"* list still pointed at brand marks main had deleted. A reader can tell why
  each check exists, which is what stops a future session deleting one as noise.
- **The purity boundary is stated and held.** *"Pure functions here take TEXT, COMMIT LISTS
  and DOCUMENT MAPS, never a repository, so the guards can exercise them without one. Only
  `run_checks` shells out."* That is exactly why L1-1 was demonstrable in four lines of
  script — and it is also why the fix is cheap: there is one shelling-out seam.
- **`will_tag` resolves a real chicken-and-egg rather than papering it.** The tag check
  gates certification while `--tag` is how the tag gets made, so when the caller is about to
  create it the check *"reports intent instead of absence"* (`:431-434`). A lesser version
  would have skipped the check.

## Lens 2 — technical debt

**Perfect scores on every conventional axis, across all three modules** — and one finding
that matters more than any count, because it turns Lens 1's finding from a house style
into a single outlier.

| hatch | `port` | `docgen` | `docmeta` |
|---|---|---|---|
| `# type: ignore` | **0** | **0** | **0** |
| `# noqa` | **0** | **0** | **0** |
| `cast(` | **0** | **0** | **0** |
| `: Any` | **0** | **0** | **0** |
| `# pragma: no cover` | **0** | **0** | **0** |
| `TODO` / `FIXME` | **0** | **0** | **0** |

Zero in every cell, 5,164 lines, `ruff` clean, 485 scoped tests green. No slot in this
sweep has matched that.

### L2-1 — `_git` is the ONE subprocess call in this slot that discards its exit code

The slot makes four `subprocess.run(..., check=False)` calls. **Three of them read the
return code and say so; the fourth does not — and the fourth is the one Lens 1 turns on.**

| site | what it does with failure |
|---|---|
| `port_backlog_union.py:220` | `if result.returncode != 0:` → reports `stderr or stdout` with *"an unreadable producer side is a …"* |
| `port_preflight.py:483` (render check) | `render.returncode == 0` gates the result; detail distinguishes *"renderer failed"* from *"no drift after re-render"* |
| `port_preflight.py:502` (suite check) | reports `CheckResult("suite green", False, "SKIPPED — not a certification")` — **a skipped check is explicitly NOT a pass** |
| **`port_preflight.py:359` (`_git`)** | **returns `.stdout.strip()` only; `returncode` and `stderr` discarded** |

The third row is the important one. **This module already implements the exact remedy
Lens 1 recommends** — it refuses to let an unrun check count as a passed one, and says so
in the detail string a human reads. The vocabulary, the discipline and the precedent are
all present, in the same file, sixty lines below the helper that lacks them.

**Consequence.** This is not a module that does not know better; it is one place that was
written before or apart from the rule the rest of the file follows. That changes the fix
from "introduce a pattern" to "apply the file's own", and it changes the risk assessment:
a reader auditing this module would see three correct sites and reasonably assume the
fourth matched.

**Cheapest correction:** `_git` returns the `CompletedProcess`, or raises on a non-zero
exit. Callers in this module already assume success, so nothing downstream needs new
branching — the failure simply stops being silent. Doing it in the same change as L1-1's
`CheckResult` third state is natural but not required; the `_git` half alone removes the
demonstrated vacuous pass.

### What was checked and cut

- **`port_rename_detect.py` at 638 lines is the slot's largest file.** Cut: no consequence
  writable. It is a detector with a single job and the file carries no hatches at all.
- **Seven ADR 0018 shims in scope.** Cut *here* deliberately — slot 6 found the trigger
  fired and recommended one cross-component grooming for all eighteen. Re-reporting it
  would produce a duplicate item for the same action, which is the outcome slot 6
  explicitly warned against. Counted in Measurements, not re-derived.
- **`drydocs_docmeta/` (1,105 lines) was not read line by line.** Stated plainly: this
  firing spent its reading budget on the port half, because that is where the publish
  boundary is and where the finding was. `docmeta` shows zero hatches, clean lint and green
  tests, which is evidence of hygiene and not of design. A later firing wanting a docmeta
  design read should not treat this slot as having done one.

## Ranked

*(step 6 — the ranked list; its presence is what marks this report complete)*

## Cross-links

*(step 6 — to the other lens in this firing, and to earlier slots)*

## Candidates for grooming

*(step 6)*
