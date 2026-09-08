---
name: lane-handoff
description: "PRODUCER-SIDE ONLY: run two DryDocs sessions on two machines without colliding — the dual-session / A-B protocol (the company repo never runs lanes; it ports with one pen, accuracy over speed). Lane A (the sender, usually the desktop) holds the backlog, port, adr, gates and snapshot pens; Lane B (the receiver, usually the laptop) gets a validated build queue on wip/ branches. Generates a self-retiring docs/lane-<x>-handoff.md with the queue, the pens to declare in the first commit, and the surface fence. Use this whenever the user says lane, A/B, dual session, handoff, burst, 'hand the laptop a queue', 'split the work between desktop and laptop', 'what should the other machine pick up', or asks to check or retire a lane handoff — even when they only mention running two sessions at once. Also use it at the START of any session handed a docs/lane-*-handoff.md, and at its CLOSE to decide whether the file retires."
---

# lane-handoff

Two machines, two sessions, one trunk. The claim rules in `CLAUDE.md` §0 (pushed claims, `wip/`
branches, the allocator) stop two sessions from building the same ITEM. Its "one pen per
surface" rule (2026-09-02) names what stops them writing the same SURFACE. This skill is the
protocol between the two, made into a file the receiving session can pull and act on.

On 2026-09-02 three sessions ran a burst without a partition and every collision landed on a
shared surface: two merge conflicts at the top of `IDEAS.md`, render conflicts on both merges,
a snapshot push that beat another by 75 seconds. The 2026-08-27 burst ran clean because it
had a `lane-b-handoff.md` under `docs/` — a queue, a fence, and a rule that the file deletes
itself when the queue empties. It was hand-written, so it could not be found again (it retired
on schedule) and its retyped rules had drifted from §0 by the time it went. This skill
regenerates that file from the tree.

## Producer-side only — the premise, not a caveat

Lanes exist to trade a little coordination for throughput on the PRODUCER trunk, where two
machines keep rolling `main` forward and the board has more ready work than one session can
take. The COMPANY repo has the opposite need: it applies a port, methodically, one pen,
where accuracy matters more than speed — a port applied from two lanes is two half-ports
that disagree. So:

- The company apply is a **third session in a different repo**, never Lane A or Lane B here.
  It picks up whatever the producer lanes landed at the next roll.
- **This skill never crosses.** `.claude/**` is canonical-producer by default, so three
  `never-port` rows in `PORT-MANIFEST.yaml` carve it out — the skill directory, its eval
  workspace, and the generated `docs/lane-*-handoff.md` — on the shape
  `docs/next-session-handoff.md` already uses. That is the mechanism, deliberately: a
  manifest row decides what crosses, and a runtime guard in the script would be reading a
  machine fact to enforce a port rule. The description says "producer-side only" as well,
  so the model does not reach for it on the wrong side by accident.
- The `port` pen is producer-side and stays with Lane A. Never run the port from the machine
  that holds it here.

## The five rules (the desktop session's, 2026-09-02 — the file carries them)

1. **Partition by module.** Since PLAN1 the id series IS the module, so Lane A takes items in
   one module set and Lane B another; two machines minting in disjoint series cannot collide
   on a number, and the title guard catches the one case they do. `--suggest` groups the
   Ready strip by module for exactly this.
2. **One pen for `backlog`, and only that machine renders.** B claims status-only (an item
   file, pushed — Y5 tolerates it un-rendered) and never runs `render_board.py`; A renders once
   at close. The depgraph snapshot is the same: A only.
3. **B works on `wip/<id>-<machine>`, pushed at the first substantive edit** (J31 verbatim —
   what would have saved K9). A merges `--no-ff` at close and deletes the branch.
4. **Declare the pens in the first commit.** `pen: backlog · port · adr · gates · snapshot` on A;
   `pen: code:<module>` per item on B. Any surface not declared is off-limits to the other
   machine until it asks. The generated file prints the exact line.
5. **The company apply is a third session in a different repo — not part of A/B.** The `port`
   pen is producer-side and stays with A; never run the port from the machine holding it.

## What the script does, and does not

`.claude/skills/lane-handoff/scripts/handoff.py` (run from the repo root) has three modes:

| Mode | Command | Reads | Writes |
|---|---|---|---|
| suggest | `--suggest [--other-queue …]` | the backlog, `config/dev-environment.yaml` | nothing — the Ready strip by module, marked V (machine-local input, or a declared `venue:` this machine lacks) / S (Lane A pen) / G (gate-bound) / O (input overlaps an item in `--other-queue`) |
| generate | `--lane B --machine laptop --queue LOAD12,CORE3 [--other-queue …] [--from …] [--out …]` | the backlog, `git` | one file, `docs/lane-<x>-handoff.md` |
| check | `--check docs/lane-b-handoff.md` | the backlog | nothing — each queued id's status, and the input overlaps still open between `queue:` and `other_queue:`; retire when all are `done` |

Readiness is `drydocs_core.backlog_store.derive_summary` — the board's own rule — so the queue
and the Ready-to-pull strip cannot disagree. The script **refuses** what the tree knows to be
wrong (an unknown id, an item not `todo`, dependencies not all `done`) and only **flags** what
the author has to rule: an input under `internal-local/` or the data root is venue-bound; for a
Lane B queue, an input under a Lane A pen (A owns those, so an A queue of gate sessions is the
normal case and is not flagged). Flagged queues need `--allow-flagged`, and the flags land in
the file. The `--other-queue` ids get the same check as **notes**, so the sender learns here
that MM4 was never ready or that MM5's input is machine-local, not on the other machine.

**Inputs against the other queue's inputs, not only against its pens (PLAN5, 2026-09-08).**
The 2026-09-05 burst queued ten Lane B items and four passed clean while sharing input paths
with items Lane A was building, because the check compared inputs against Lane A's PENS and
never against Lane A's QUEUE. Now every queued item's `inputs` are compared with every
`--other-queue` item's `inputs`, prefix-aware (`drydocs_api/` covers `drydocs_api/schemas.py`),
one row per collision naming both items, the shared prefix and which side supplied the coarse
path — a coarse input dominates (one `web/src` matched seven paths), so the reader has to see
whose it was. An overlap is a **flag**, not a refusal: Lane B took R12 and O68 knowingly, and
that is the author's call to make with the collision in front of them. Inputs under
`docs/reviews/` are skipped by convention — the review that spawned an item is provenance, not
a write target, and `inputs` is the only path field in the v3 schema; the ruling (2026-09-08)
was to exclude by convention rather than grow the schema with `outputs:`, so the convention is
one named constant, `PROVENANCE_PREFIXES`, pinned by a test. Generate records the other side
in an additive `other_queue:` front-matter line so `--check` re-runs the comparison over the
items still open on both sides without parsing the prose table (J37); a file generated before
the line says so and skips that part.

**A venue wall in acceptance prose is invisible; a declared one is not (PLAN6, 2026-09-08).**
The V mark read only input PATHS, so G132 — whose collector runs only on a Control-M server
host, and says so in clause (g) — passed clean and was queued to the laptop on 2026-09-05; the
lane hit the wall on read and left it `todo`. The fix is not to parse prose. An item may carry
an optional `venue:` list of codes, validated by the backlog schema guard against the `venues:`
map in `config/dev-environment.yaml`, where each code says whether THIS side has it
(`available:`) and what it is. `--suggest` and generate flag a queued item whose code this side
does not declare available, naming the code and the key that failed; an undeclared code is its
own flag; an item with no `venue:` is silent, exactly as before. The venue file is the
declared-not-inferred file already (PLAN2's `edition:` lives there), it is canonical-company in
`PORT-MANIFEST.yaml`, so the company's copy carries the company's own availability and adopts
new codes by hand. G132 is the worked example and carries `venue: [controlm-server]`. What this
does not do: tell two producer machines apart — the file is committed, so the laptop and the
desktop declare the same set; a per-machine difference (one lane without Neo4j) is still the
author's ruling at queue time.

**One vocabulary for surfaces.** `PENS` in the script is keyed by §0's pen names (`backlog`,
`port`, `adr`) plus two this skill adds and marks as additions (`gates`, `snapshot`). The
surfaces table AND the `pen:` line the receiving session commits are both generated from that
one structure, so the file and §0 cannot say different things. Change a surface's owner there,
with the reason — it is policy, not a guard. `tests/unit/test_lane_handoff.py` pins the refuse /
flag split, the lane-aware pens, path normalization, the other-queue notes, `--check`'s
MISSING state, the overlap check (the coarse-prefix case, the provenance exclusion, and a
file that predates `other_queue:`), and the declared venue (flag, silence, undeclared code, and
G132 as the worked example).

It does not claim items — the pull rule does that per item, at pull time. It does not render,
mint, or commit.

## The workflow

**1. Decide the burst with the user.** Which machine is Lane A (sender; holds the pens) and
which is Lane B (build lane). Ask for the plan's priority order — the queue is the user's
ordering, not the strip's.

**2. `--suggest`,** then pick the queue with the user, by module. Prefer items whose `inputs`
are disjoint from the other lane's, code+tests items for a lane without Neo4j, and never a
gate-runner item unless that machine is where the SME sits. A `V` mark means the data lives
somewhere: put the item on the machine that has it, or leave it out and say so. Once the
sender's own queue is known, re-run with `--other-queue <those ids>`: an `O` mark names the
collision and the coarse side, and the user rules whether the item moves lanes, waits, or is
taken knowingly.

**3. Generate,** passing `--other-queue` with the ids Lane A keeps for itself. Read the output
once as the receiving session would: is every "Notes from the check" cell actionable?

**4. Commit and push the file on `main` from the sender's session** — it is a `backlog`-pen
surface, and the receiving machine reads it at `git pull`. The commit message declares A's
pens; message shape: `docs(plan): Lane B handoff — build-lane queue for the laptop session`.

**5. At the receiving session's start,** the handoff IS the start ritual: the pens line goes
into its first commit, then §0 as cited, then the queue.

**6. At close, `--check`.** Exit 0: every queued item is `done` — delete the file in the closing
commit. Exit 1: what is still open (or MISSING — re-minted since; ask the sender) — the file
stays. B's close is push-and-report; A's close is merge `--no-ff`, delete the `wip/` branches,
render once, snapshot once.

## What this skill will not do

- Decide the partition for the user. It suggests; the ordering and the venue rulings are
  theirs, and the file records them as theirs.
- Replace the pull rule. A queue is a plan; the claim is still one item file, pushed, before
  work.
- Survive the burst. The file's own lifecycle deletes it; the item files are the record.

## Provenance

Built 2026-09-02 from the retired handoff file (`git show 7ed4eab2:docs/lane-b-handoff.md`),
the same day's three unpartitioned-burst collisions, the desktop session's five dual-session
rules, and the review of `fe120bf9` (pen-keyed surfaces, the unit test, path normalization,
the workspace gitignore). The I7 backlog item carries the in-checkout fan-out version of the
same rule. Iteration-1 eval: 100% with the skill vs 85% without; iteration 2: 100% vs 70% on
the tightened assertions.

First real burst 2026-09-03 (six items, laptop = Lane B, all six closed on `wip/` and merged
clean): the Lane B block now carries the three findings that report surfaced — a close commit
is red on the roadmap guard by design (Y5 covers a claim, not a close), a new tracked path
hands its manifest row back through the item notes (the `port` pen is A's), and an item that
owns its own generated artifact names the writer at close.
