# "Item premises keep failing against the tree" — three organs, three instruments

**Date:** 2026-09-09 · **Trigger:** the SME named this the next highest priority bug and
pointed at the `web` slot of the standing module sweep (`origin/review/module-sweep`, slot 9
closed the same day at `dcf41c32`), after a Lane B burst in which five of five backlog items
built on the laptop had a premise that was wrong against the tree. **Lens:** locate the
finding, measure its real size, propose the mechanism. **Classification:** Internal-Public
(mechanism only — path names, counts and manifest classes; no data values). **Pen:** reviews.
**Decides nothing** — no guard is written here and no item file is edited, because both are
Lane A's pens. This review exists to say what the bug is and how big it actually is.

- **Reviewed at:** commit `cf2ac76b` on `wip/v4-laptop`, port base `port-base-20260908`;
  venue NewThinkpad. *Absent here reads as not-yet-ported, not as broken
  (`docs/style/review-provenance.md`).*

**One convention this document follows on purpose.** A path that does not exist is quoted as
plain text, never in backticks. `tests/unit/test_runbook_currency.py` rules that backticks are
an existence claim and caught exactly that error in the note describing the error it was
written for. `docs/reviews/**` is outside that guard's scope today, so nothing enforces it here
— but a review *about* stale citations that seeds new ones would be its own subject matter.

*And the rule caught this document.* Running the guard's own idiom over this file before
committing it found 16 backticked paths, of which **2 were broken — and both were the exact
categories §4 names as the reason not to guard `acceptance:`**: one deliverable that does not
exist yet (V5's docgen runbook) and one citation relative to a skill directory rather than the
repo root. Both are now plain text. Treat that as the strongest evidence in this review that
the acceptance guard would produce false positives: the author who had just written the
argument still tripped it, twice, in the document making it.

**Method.** An eleven-agent fan-out: four locator agents over the sweep reports, the backlog,
the idea inbox and the current rules; three measurement agents that wrote and ran scripts
rather than estimating; and one adversarial re-count per measurement, each written from
scratch and instructed to default to disagreeing. The re-counts changed three numbers and
killed one methodological error — every count below is the post-verification number, and the
places where the two passes still disagree are flagged rather than averaged.

---

## 1. It is not one bug

The discriminating test is *does the same mechanism close it?* By that test there are three,
and filing them as one produces an item with no single acceptance clause.

| | What it is | Closed by |
|---|---|---|
| **(a) Path drift** | An item's `inputs:` or `acceptance:` cites a repo path; the tree moved, the citation did not | An existence check over structured data |
| **(b) Contract non-propagation** | A contract is declared in one place and consumers silently do not honour it | A shared return type that makes the wrong version unwritable |
| **(c) Wrong at birth** | The tree never moved — the claim was false the day it was written | Nothing mechanical. An authoring rule only |

They share a root, stated best by slot 10 (`seams-2026-09-08.md`): *"the knowledge exists, is
written down somewhere specific, and never becomes the thing the next author inherits."* They
share nothing else.

**The session's own evidence splits across two of the three, and conflating them was an error
in the report that prompted this review.** REM2's never-port `drydocs/data/samples/` and V4's
five ADR 0018 D4 shim paths are (a). V6's extractor miscount — a directory listing counted with
`__init__.py` in it — and V4's Confluence "base URL as config", which has no producer-side
existence at all, are (c): *the tree never moved under either.* "Re-check a claim when the tree
moves" and "measure before you assert" are different rules with different enforcement surfaces,
and only the first is guardable.

### Where the web review sits

Slot 9's ranked #1 is (b), and its diagnosis is the sharpest statement of the whole class:

> *"it shows the failure is not ignorance but absence of a mechanism: nothing told the author
> the field existed... A developer building a new spec consumer the day after `truncated`
> shipped had no way to learn it existed: it is not in a convention document, no lint rule
> mentions it, no shared hook surfaces it... **knowing is accidental**. A convention document
> would not have reached the author of RuntimeSpanMap either; a shared return type would have."*

The contract entered `drydocs_api/schemas.py` on 2026-09-05 (`95c89328`); the consumer that
discards the envelope was built 2026-09-06. The review dates the drift rather than inferring
it, which is why it calls the finding *the propagation event itself*.

Slot 9's ranked #3 is the entry that most literally matches the bug's title — backlog item
WEB13 pinned a coverage floor to a 22,715-line tree that is now 35,197 — and the report
deliberately refuses to assert it drifted, supplying the check and the decision rule instead.
That restraint is worth copying.

---

## 2. Measured size

### `inputs:` — solid, and smaller than it looks

**117 unresolved of 2,879 entries across all 711 items.** Both passes reached 117, and the
verifier reproduced the *identical 117 `(item, raw)` pairs* by set-difference rather than
matching a total — the J57 rule about comparing sets and not totals, applied to a measurement.

The split is what makes this tractable:

| Population | Unresolved | Reading |
|---|---|---|
| `done` items | 109 | Historical residue. `tests/unit/test_backlog.py` (I8 clause (c)) already rules a closed item's text a record of completed work |
| non-done, gitignored machine-local | 4 | `LIN3`, `MM5`, `MM7`, `MM9` — absent on every clone by construction |
| **non-done, actionable** | **4** | `C42`, `CFG4`, `DOC5`, `Y4` |

Three refactors account for **73** of the 117 (the verifier's correction; the first pass said
72, having counted the controlm move at 17 rather than 18): the relationship-vocabulary shard
(35), the taxonomy-map shard (20) and the `drydocs_core/orchestration/controlm/` move (18).

### `acceptance:` — the reported pairing was wrong

The first pass reported "711 examined / 2 broken". Those are different populations: the scan
ran over the 101 non-done items only. The honest statements are **2 of 101 non-done** or 9 of
711. Worse for the method, **both of the 2 are false positives** — they are the two S5-retired
names that item L19's own clause (f) exists to re-point away from.

**Genuine acceptance drift is 2, and the backtick idiom sees neither**, because item prose does
not follow the runbook backtick convention: 14 backticked path tokens across the whole corpus
against 96 bare ones. So the idiom scores 0-for-2 on real drift and 2-for-2 on false positives.

| Item | Stale citation (plain text, per the convention above) | Where it lives now |
|---|---|---|
| `C44`, `C42` | drydocs_core/description_tokens.py | `drydocs_core/orchestration/controlm/description_tokens.py` |
| `CFG4` | UI-WIP/two-track-ui-plan.md | `docs/design/ui-exploration/two-track-ui-plan.md` (re-homed at `c3cd5521`) |

`C42` and `C44` carry the same stale path, and `CFG4` carries UI-WIP/ in both fields — so the
actionable set is **five item files**, not four. `CFG4` is the sharpest of them: its acceptance
*instructs a future session* to add a dated note to a file whose whole parent directory is gone.

### Beyond the backlog — gate prompts are the concentration

**30 broken citations across 19 of 60 gate prompts**, and **25 of them are the same S5 pair**:
config/taxonomy-ontology-map.yaml (×15) and drydocs_core/ontology/relationship_vocabulary.yaml
(×10), both turned into directories of the same name by `d84d86bc`. Confirmed here: both
`config/taxonomy-ontology-map/` and `drydocs_core/ontology/relationship_vocabulary/` are
directories, and 19 prompt files still cite the retired file names.

That matters more than the raw count suggests, because **a gate prompt is acted on by a future
session, where a review is read once.** 18 of the 19 are recorded in `config/gate-log.md` as
signed, deferred or pending — so "defect" overstates the ones sitting in signed records, but
the deferred and pending ones are live instructions.

Two corrections the verifier made here, both load-bearing:

- **"0 remediated" is false.** `ecc1622c` (2026-09-07, "producer, pre-session stale-pointer
  sweep") fixed `config/gate-prompts/code-graph-package-layer.yaml`. Its three surviving
  mentions sit inside `[AMENDED 2026-09-07; was …]` markers — **the sanctioned edit shape
  preserves the old name**, so a bare scan reads a fix as an unremediated defect. 1 of 19.
- **"Sweep 47 backlog items" is wrong.** 45 of the 47 are `done`. The sweepable backlog surface
  is 2.

### Numbers that are *not* solid — flagged rather than averaged

1. The blast-radius headline (101 vs 147) is a **bucketing** disagreement, not a measurement
   one. Both raw sets agree (352 vs 334) and both conclude `docs/reviews/**` and
   `docs/decisions/**` contain approximately zero defects. Neither number should be quoted
   without its classification rules.
2. Slot 9 states its own propagation figure as both 3/8 and 4/8 in one file. It reconciles as
   3 direct readers + 1 delegating-and-covered + 4 droppers = 8, but the report never performs
   the reconciliation.
3. One `inputs:` entry (`R16`'s .mcp.json) is machine-local with no gitignore rule, so the
   strict drift figure is 111 or 112 of 117 depending on how it is counted. Immaterial to the
   actionable 4.

---

## 3. The gap, exactly

Two commands locate it, and both were run here:

```
grep -c inputs tests/unit/test_backlog.py                       -> 0
grep -c inputs .claude/skills/groom-backlog/validate.py         -> 0
```

**Enforced by a test.** `tests/unit/test_runbook_currency.py` is the only guard in the repo
that reads prose and asserts the tree back — existence only, by its own docstring: *"It cannot
check that a sentence is still true… A pointer cannot go stale; only a copy can."* Its scope is
`docs/design/*-runbook.md` by glob plus five named `EXTRA_DOCS`. It carries three exemption
tables — `HISTORICAL_PATHS`, `FOREIGN_PATHS`, `GENERATED_PATHS` — each requiring a written
reason, and `test_path_exemptions_carry_a_reason_and_are_still_cited` makes them **shrink-only**:
an exemption nothing still cites fails the suite. `tests/unit/test_backlog.py` enforces schema
and resolves exactly four *structured* references — `epic:`, `agent:`, `gates:`, `venue:`.

**Written down as a rule only.** Idea-93's `inputs:` check was run by hand three times
(2026-08-09, -12, -19); its author wrote that it was "worth keeping as a standing groom check";
it never became code. **All three runs were against the retired monolith `backlog.yaml` — it
has never once run against the sharded `items/`.** The "stale-premise sweep" clause appears in
the `notes:` of eighteen gate-run items, executed by a human, producing no artifact.

**So `inputs:` is the one drifting surface where the instrument already exists** (path
existence, solved in `test_runbook_currency.py`), **the data is structured rather than prose**
(a declared list — no backtick convention to depend on, no J66 comment-matching hazard), and
nothing has ever been pointed at it.

---

## 4. The mechanism — for Lane A to build, not written here

**One test in `tests/unit/test_backlog.py`, beside the existing dependency tests:** for every
item whose `status` is `todo` or `in_progress`, every string in `inputs:` must resolve.

Four things it must do differently from the runbook guard, each with its reason:

1. **Scope to non-done.** I8 clause (c) already rules a closed item's text a historical record.
   Without this the guard opens with 109 reds that are all correct-as-written. This *replaces*
   `HISTORICAL_PATHS` — status is the historical axis and needs no table.
2. **Assert against `git ls-files`, not `Path.exists()`.** The parent guard uses `.exists()`
   and documents the fresh-clone divergence as a known limit at its own lines 150-152. Both
   measurers hit it here: a glob "resolves" on this laptop to two gitignored files a clone
   would not have, and Windows `.exists()` is case-insensitive while CI is not.
3. **Classify gitignored inputs with `git check-ignore` and skip them with a stated reason.**
   `LIN3`, `MM5`, `MM7`, `MM9` are absent on every clone by construction, and `MM7` is
   `in_progress` — failing it would red the suite for whoever holds the claim.
   **Send bytes with `-z` on both sides, and say so in the docstring.** Both independent
   measurers hit the same Windows trap: Python's text pipe writes `\r\n`, git takes the CR as
   part of the pathname and C-quotes its echo. One of them silently got three wrong before
   catching it. This is J76 — check the instrument before the subject — and it belongs in the
   guard's own comment, not just in this review.
4. **Fail malformed entries loudly on non-done items** rather than heuristically skipping them.
   Fourteen entries today are prose-annotated (`config/launcher-registry (G26)`), cross-repo
   refs (`ce-wilson/depgraph@…`) or screenshot filenames. A pre-filter that discards anything
   containing a space is exactly how a stale annotated path would slip through unchecked.

Plus one `INPUT_EXEMPTIONS` table, ≥40-character reason per entry, shrink-only — copying
`test_path_exemptions_carry_a_reason_and_are_still_cited` verbatim in shape.

**Cost today: 4 reds, all genuine, all with a confirmed current location.** Fix the five item
files in the same commit and the mechanism ships with its own proof, green.

### Two things not to do

**Do not extend the guard to `acceptance:`.** That is where the pattern breaks. Five of the
eleven bare-path hits there are deliverables the item will *create* — V5's own
docs/design/drydocs-docgen-runbook.md among them — and two are subdirectory-relative
citations that are correct as written (PLAN8's references/er-model.md, relative to
`.claude/skills/controlm-db/`). A regex cannot separate a promise from a claim, and reddening
V5 would manufacture exactly the false finding this class is about. `C44` gets fixed by hand in
the same sweep.

**Do not guard the gate prompts. Sweep them.** They cite paths unbackticked (1 backticked claim
in roughly 410), and the sanctioned edit shape `[AMENDED <date>; was <old-path>]` preserves the
old path in the text — so a bare-path guard would red the annotation recording its own fix.

---

## 5. Pens, and what this review deliberately did not do

| Surface | Pen | Lane |
|---|---|---|
| `docs/restructure/backlog/items/{C42,C44,CFG4,DOC5,Y4}.yaml` | `backlog` | **Lane A** |
| `tests/unit/test_backlog.py` (the new guard) | undeclared by either lane | **ask first** |
| `.claude/skills/groom-backlog/validate.py` (mirror) | `backlog` | **Lane A** |
| minting the guard item and the sweep item | `backlog` | **Lane A** |
| `config/gate-prompts/**` (19 files) | `gates` | **Lane A** |
| `web/src/**` shared completeness hook | `code:drydocs-web` | Lane B, after Lane A mints it |
| this file | `reviews` | Lane B |

`tests/unit/test_backlog.py` is the sharp one. It is not among Lane B's seven pens; it is the
backlog surface's own guard. `docs/lane-b-handoff.md`: *"Any surface not declared is off-limits
to the other machine until it asks."* Writing it unilaterally because the bug is urgent is the
shape of the 2026-09-02 coordination failure `CLAUDE.md` §0 records, so it was not written.

**No PORT-MANIFEST row is owed.** `docs/reviews/**` already carries one — `evaluate`,
*"point-in-time review records — historical artifacts of the side that ran the review"* — which
is the right disposition for this file too.

---

## 6. What Lane A is being asked for

Three items, deliberately not one, because they close with three different mechanisms:

1. **The `inputs:` guard** in `tests/unit/test_backlog.py`, plus the five item-file fixes in
   the same commit so it ships green. Section 4 is the specification.
2. **A one-off sweep** of the 19 gate prompts and the 2 sweepable backlog items for the S5
   pair — explicitly a sweep and not a guard, for the `[AMENDED; was …]` reason above.
3. **The web completeness hook** (slot 9's own p1 grooming candidate) under
   `code:drydocs-web` — organ (b), sharing no acceptance clause with the other two.

### And one thing that needs no item at all

Organ (c) has no guard and cannot have one. The authoring rule that would have caught V6's
miscount, adopted in this session at zero cost:

> **Any count that reaches a page's thesis sentence cites the command that produced it.**

The V6 runbook asserted "twelve extractors" in the sentence its whole argument rested on. The
number came from reading a directory listing that included `__init__.py`. No guard proposed
above would have caught it; running `ls | wc -l` and pasting the command would have.
