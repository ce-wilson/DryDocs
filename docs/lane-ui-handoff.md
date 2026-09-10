# Handoff — the UI workstream, on `feat/web-completeness`

> Issued 2026-09-10 by Lane A (desktop, `main` at `1e50820b`) for the UI-workstream session
> running in `.claude/worktrees/ui-workstream` **on this same machine**.
>
> **Hand-written, not generated.** The `lane-handoff` skill builds a queue for TWO MACHINES
> coordinated by pushed claims; this is a third session in a second worktree on ONE machine, which
> is a different problem — the git object store and the ref namespace are shared, so the fence
> below does work the skill's PENS table does not have to. The skill's five rules still hold and
> are restated where they apply.
>
> **Lifecycle:** this file retires when its queue empties. Lane A deletes it in the closing commit.

---

## Why you have a branch now

Before this was issued, that worktree sat **detached** at `e9b22543`. A commit made there would
have landed on no branch, with no ref pointing at it, and the next checkout would have lost it
silently — the K9 failure mode CLAUDE.md records costing a full rebuild. Nothing was stranded; it
was caught first.

You are now on **`feat/web-completeness`**, created from `origin/main` and level with it. That is
the shape CLAUDE.md prescribes for *"a multi-commit stream you want to review or revert as a
unit"* — one branch for the whole queue, not `wip/<id>-<machine>` per item, because Lane A wants
**one merge**, not five.

---

## The queue

Four items. Ordering matters for the first two and is stated.

| # | id | model | what |
|---|---|---|---|
| 1 | **WEB19** (p1) | sonnet | One shared hook returns rows and `truncated` together; the four consumers that discard the flag migrate onto it; a consumer reading a list without the envelope fails a test |
| 2 | **WEB20** (p2) | sonnet | Retrofit `IntakeRoute`, `LocationMap`, `FileReport` to read the `truncated` flag they already receive — honoring consumers to 8 of 8 |
| 3 | **WEB23** (p2) | sonnet | The initial-chunk ceiling has under a kilobyte of headroom; re-measure and rule on whether `load-map.json` still belongs in the entry chunk |
| 4 | **WEB21** (p3) | haiku | Re-check the coverage ratchet — the statements floor is pinned at 9.8 against a tree that grew from 22,715 to 35,197 lines; read the three thresholds together before re-pinning |

### WEB19 and WEB20 overlap, and neither declares it

Read both acceptances before starting either. WEB19 migrates **four** consumers onto the shared
hook; WEB20 retrofits **three** surfaces — `IntakeRoute`, `LocationMap`, `FileReport` — and those
three are inside WEB19's four. Their `inputs:` lists overlap on all three files plus
`config/taxonomy/ui-components.yaml`, and **neither carries a `depends_on`**, which is a real gap
in the mint rather than something you should work around silently.

**Do WEB19 first. Then measure what is left of WEB20 before building it** — if the hook migration
already took those three surfaces to 8 of 8, WEB20 closes as done-by-WEB19 with the measurement in
its note, and that is a legitimate close. If it does not, the remainder is real and small. Either
outcome is fine; guessing between them is not.

### WEB22 is NOT in this queue, deliberately

`WEB22` (run the `console-auth-boundary` gate) carries `gates: [console-auth-boundary]` and names
`config/gate-log.md` in its inputs. **Writing the gate log is Lane A's `gates` pen, and a gate
session needs the SME in the room** — it is not a web build that happens to touch a gate. It stays
with Lane A. If your work turns up something the gate should rule, put it in the item's notes and
Lane A carries it into the sitting.

---

## Pens

| Surface | Holder | Note |
|---|---|---|
| `code:drydocs-web` — `web/src/**`, `web/scripts/**`, `web/package.json` | **you** | the whole console |
| `config/taxonomy/ui-components.yaml` | **you**, as of this handoff | **CHANGED.** The Lane B handoff fenced this to Lane B. The items that write it — WEB19 and WEB20, each adding its O42 row — are yours now, so the file moves with them. Lane B's current queue (LOAD13, LOAD14, DOC12) does not touch it. |
| `backlog` — `items/`, `IDEAS.md`, `epics/`, the plan renders | Lane A | with the ONE carve-out below |
| `port`, `adr`, `gates`, `snapshot` | Lane A | `PORT-MANIFEST.yaml`, `docs/port/**`, `docs/decisions/**`, `config/gate-log.md`, `config/gate-prompts/**` |
| `code:<other modules>` | Lane B (laptop) | `drydocs_core/**`, `drydocs/**`, `drydocs_api/**`, `tests/unit/**` outside web |

**The carve-out you do hold:** your own item file's `status`, claimed and pushed before you start
it. That is Lane B's rule verbatim (Y5 tolerates a status-only claim un-rendered), and it is how a
builder claims without holding the backlog pen wholesale.

---

## The fence — what not to touch, and why each one

- **`web/src/generated/**` is DERIVED.** `load-map.json`, `gates.json`,
  `enforcement-matrix.json`, `software-registry.json` and their siblings are written by Lane A's
  `render_board.py` from committed sources. WEB23 **reads** `load-map.json` to reason about the
  bundle; it never edits it. An edit there is overwritten at the next render and looks like a
  mystery diff to whoever renders next.
- **Do not run `scripts/render_board.py`, `render_design_doc.py`, or `snapshot.ps1`.** Renders have
  exactly one writer per cycle by construction; two produce conflicting versions of the same
  deterministic output. Lane A renders once at merge.
- **Do not touch `docs/plan/*.html`** for the same reason.
- **`config/gate-log.md` and `config/gate-prompts/**`** — Lane A's `gates` pen, and signed records
  besides.
- **Do not merge to `main` or delete this branch.** Lane A does both.

---

## Protocol

1. **Claim before you start.** Set `status: in_progress` in that one item file, commit, and
   **push** — on this branch. A local-only claim is invisible, which is the whole reason the rule
   exists.
2. **Push at the first substantive edit**, not at the end (J31). Work that exists only in that
   worktree is work nobody can see, and this machine already had one detached-HEAD near miss
   today.
3. **Never render.** See the fence.
4. **Rebase, do not merge, when you pick up main.** `git pull --rebase origin main` keeps the
   branch a clean stream for the `--no-ff` merge. Lane A is committing to `main` continuously.
5. **Run the guard family before you call an item done** (J57): `test_module_boundary.py`,
   `test_render_determinism.py`, `test_no_render_parsing.py`, `test_source_scan.py`,
   `test_runbook_currency.py` — plus `test_ui_components.py` and `test_load_map_console.py`, which
   are the two your surface actually moves. Compare the failing **set**, never two totals.
6. **`tsc -b` and `npm run test:coverage` need `web/node_modules`.** If this machine does not have
   them installed, say so in the item note rather than skipping silently — WEB21 cannot be judged
   without the real numbers, and a skipped check reported as a pass is the defect ADR 0021 exists
   for.

## Close

Push everything, set each item `done` with its note, and tell Lane A. Lane A merges `--no-ff`,
renders once, deletes `feat/web-completeness`, snapshots, and deletes this file.

**Expected red at your close, and it is not yours to fix:** a close commit that writes item notes
moves the roadmap's source fingerprint beyond Y5's status-only tolerance, so
`test_committed_roadmap_page_matches_its_sources` fails until Lane A's render lands. Name it in the
close report; do not render to make it green.
