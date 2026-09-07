# docs/reviews — the second-review protocol between lanes

**Status:** convention, 2026-09-04. Companion to [`../style/review-provenance.md`](../style/review-provenance.md)
(J63: a review names the tree it ran against) and to the `lane-handoff` skill (build queues
between lanes). This file covers the third thing the lanes do: **one lane builds or drafts, the
other reviews.** It is a prompt and a commit shape, not a skill — there is nothing to load.

## The shape: four commits, each citing the last

| Step | Who | What lands | Commit cites |
|---|---|---|---|
| **SUBJECT** | the first lane | the work under review — an item's range, or a paper in `docs/reviews/` | (the item / paper) |
| **REVIEW** | the second lane | `docs/reviews/<subject>-review-<date>.md`, stamped at SUBJECT (`python scripts/review_stamp.py`), findings numbered `R1..Rn` | SUBJECT's sha |
| **APPLY** | the first lane | the fixes, each naming the `R` it closes; for an item, the `LANE REVIEW (<venue>, reviewed at <sha>, range <a>..<b>)` block in the item's `notes:` (the LIN1 precedent) | REVIEW's sha |
| **VERIFY** | the second lane, optional | one dated line appended to the review file: what was re-read at APPLY's sha, what held | APPLY's sha |

**Why a commit at every step.** On 2026-09-03/04 the same session ran the loop twice. The LIN1
review was delivered in chat and never committed, so the builder had to transcribe it into
`LIN1.yaml` by hand and the verify pass had nothing to cite. The options-paper review was
committed (`0015fcfa` at subject `0cc996cf`), so the user's correction landed as `1b615dc7`
citing `R8` by number. The second shape is the one to keep: a chat paste is a request, never a
record.

## The reviewing lane's rules

1. **Pen: `reviews` only** — `docs/reviews/`. Declared in the first commit. The reviewer touches
   no item file, mints nothing, and holds no other pen unless the request grants one. A reviewer
   who also fixes is a builder, and then the `wip/<id>-<machine>` rule applies.
2. **Read the tree, not the paste.** The request's narrative is context. Every premise it makes
   — an id, a relay number, a line cite, a "the code does X" — is verified against the tree
   before it is used. The 2026-09-03 Ideas→Backlog request carried three false premises
   (`RELAY-26`, `Idea-10015..10017`, a conflated refusal); the review's value was catching them.
3. **Name the lens as well as the tree.** A review says which skill ran, or `none`. Lens skills
   are machine-gated by `.claude/settings.local.json` `skillOverrides` (`code-review` and
   `verify` are `off` on the laptop today); if the requested lens is off, the reviewer says so
   and states which lens actually ran. Nothing about the skill tree changes per review.
4. **Decides nothing.** A review proposes; a gate rules; the builder applies. Every new
   label, type, edge property, id shape or process rule in a review is written as gate or
   acceptance material.
5. **Rank by what changes the recommendation**, then mechanics, then nits. Say up front how
   many premises were verified and how many held.

## Request template (paste into the reviewing session, edit the slots)

```
SECOND REVIEW — lane <A|B> asks lane <B|A>

SUBJECT   <sha>  or  <sha>..<sha>            # what to review; for an item, its claim..close range
ITEM      <id or none>                         # anchors the APPLY block; none for a paper
LENS      none | /system-design | /architecture | /tech-debt | /code-review
PEN       reviews                              # add code:<module> ONLY if fixes are wanted here
LANDS     docs/reviews/<subject>-review-<date>.md, stamped at SUBJECT
GOAL      <one sentence: what a good review changes>
DO NOT    touch items/, mint, render, or run the port; the other lane holds those pens
CONTEXT   <the narrative — premises to VERIFY, not to trust>
```

## Return template (the reviewing session's closing message)

```
REVIEW <sha>  docs/reviews/<file>  — stamped at <SUBJECT sha>, lens <x>, venue <machine>
Premises verified: <n> of <n> held; did not hold: <list or none>
Changes the recommendation: R1 <one line> … Rk <one line>
Mechanics / nits: R<k+1>..Rn (in the file)
Pens touched: reviews. Items touched: none. Minted: none.
Next: APPLY on lane <x> cites the R-ids; for <ITEM>, the LANE REVIEW block goes in its notes.
```

## What this deliberately does not do

- **No new skill, no skill-tree change.** The lens is a slot in the prompt; per-machine
  enablement is already `skillOverrides`. Both lanes carry the same `.claude/` tree.
- **No `reviews` row in `lane-handoff`'s `PENS` yet.** The pen is declared in commit messages,
  which is what §0 requires. Adding the row so a generated handoff can print it is a one-line
  change with a test, and a separate item when a burst needs it.
- **No guard.** Like J63, applied at authoring time and by review.
