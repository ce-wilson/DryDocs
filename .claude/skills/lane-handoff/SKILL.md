---
name: lane-handoff
description: "Split a burst of DryDocs work between two machines (Lane A = the sender's session, usually the desktop; Lane B = the receiving session, usually the laptop) by generating a self-retiring handoff file with a validated queue and a surface-ownership table. Use this whenever the user says lane, A/B, handoff, 'hand the laptop a queue', 'split the work between desktop and laptop', 'what should the other machine pick up', 'start a burst', or asks to check or retire a lane handoff — even when they only mention running two sessions at once. Also use it at the START of any parallel session that was handed a docs/lane-*-handoff.md, and at its CLOSE to decide whether the file retires."
---

# lane-handoff

Two machines, two sessions, one trunk. The claim rules in `CLAUDE.md` §0 (pushed claims, `wip/`
branches, the allocator) stop two sessions from building the same ITEM. They do nothing about
the SURFACES both sessions touch between items — the inbox top, the rendered pages, the
snapshot. On 2026-09-02 three sessions ran a burst without a partition and every collision
landed on exactly those: two merge conflicts at the top of `IDEAS.md`, render conflicts on
both merges, a snapshot push that beat another push by 75 seconds.

The 2026-08-27 burst ran clean, and it had one thing today's did not: a `lane-b-handoff.md` under `docs/`
— a queue for the receiving machine, a list of surfaces the sending machine owned, and a rule
that the file deletes itself when the queue empties. It was written by hand, which is why it
could not be found again (it retired on schedule) and why its retyped rules had drifted from
§0 by the time it went. This skill regenerates that file from the tree.

## What the script does, and does not

`.claude/skills/lane-handoff/scripts/handoff.py` (run from the repo root) has three modes:

| Mode | Command | Reads | Writes |
|---|---|---|---|
| suggest | `--suggest` | the backlog | nothing — prints the Ready strip by module, with flags |
| generate | `--lane B --machine laptop --queue G106,G133 [--other-queue …] [--from …] [--out …]` | the backlog, `git` | one file, `docs/lane-<x>-handoff.md` |
| check | `--check docs/lane-b-handoff.md` | the backlog | nothing — reports each queued id's status and whether the file retires |

Readiness is `drydocs_core.backlog_store.derive_summary` — the board's own rule — so the queue
and the Ready-to-pull strip cannot disagree. The script **refuses** what the tree knows to be
wrong (an unknown id, an item not `todo`, dependencies not all `done`) and only **flags** what
the author has to rule (an input under `internal-local/` or the data root = venue-bound; for a
Lane B queue, an input under a Lane A surface — Lane A owns those, so a Lane A queue of gate
sessions is the normal case and is not flagged). Flagged queues need `--allow-flagged`, and the
flags land in the file where the receiving session will read them. The `--other-queue` ids get
the same check as notes, not refusals: a Lane A file for the desktop will say that the
laptop's MM4 is not ready or that MM5's input is machine-local, so the sender learns it here
rather than on the other machine.

It does not claim items — the pull rule does that per item, at pull time. It does not render,
mint, or commit.

## The workflow

**1. Decide the burst with the user.** Which machine is Lane A (the one keeping the port
prompt, gate sessions, grooming, the inbox, the snapshot) and which is Lane B (the build
lane). Lane A is the sender by default. Ask what the plan's priority order is — the queue is
the user's ordering, not the strip's.

**2. `--suggest`,** then pick the queue with the user. Prefer items whose `inputs` are disjoint
from the other lane's, code+tests items for a lane without Neo4j, and never a gate-runner
item (an SME session, not a build) unless that machine is where the SME sits. A venue flag
means the data lives somewhere: put the item on the machine that has it, or leave it out and
say so.

**3. Generate.** Pass `--other-queue` with the ids Lane A keeps for itself, so the file fences
them. Read the output once, as the receiving session would: is every "Notes from the check"
cell something that session can act on?

**4. Commit and push the file on `main`** from the sender's session — it is a Lane A surface
like the inbox, and the receiving machine reads it at `git pull`. Message shape:
`docs(plan): Lane B handoff — build-lane queue for the laptop session`.

**5. At the receiving session's start,** the handoff IS the start ritual: it cites §0 rather
than restating it, then the queue, then the fence.

**6. At close, `--check`.** Exit 0 means every queued item is `done`: delete the file in the
closing commit. Exit 1 lists what is still open: the file stays, and the close report names
it. Unfinished work on the receiving lane goes to `wip/<id>-<machine>` (J31), never to the
inbox — Lane B does not append to `IDEAS.md` during a burst; it hands captures back.

## Why the fence is by surface

An item claim protects one file the claimant is editing. A burst also produces edits that no
item names: an idea captured mid-task, a render refreshed at close, a snapshot rolled. Those
land on files both sessions write, and git merges them by text, which for the inbox top and
for derived renders is the wrong answer every time (the retired file said "regenerate, never
carry", and today's two merges proved it twice). Naming an owner per surface is what turns a
three-way merge into a fast-forward.

The fixed Lane A list (in the script, `LANE_A_SURFACES`) is the retired file's list plus the
snapshot directory. Change it there, with the reason, when a burst needs a different split —
it is policy, not a guard.

## What this skill will not do

- Decide the partition for the user. It suggests; the ordering and the venue rulings are
  theirs, and the file records them as theirs.
- Replace the pull rule. A queue is a plan; the claim is still one item file, pushed, before
  work.
- Survive the burst. The file's own lifecycle deletes it; the item files are the record.

## Provenance

Built 2026-09-02 from the retired handoff file (`git show 7ed4eab2:docs/lane-b-handoff.md`)
and the three collisions of the same day's unpartitioned burst; the I7 backlog item carries
the in-checkout fan-out version of the same rule.
