---
handoff: drydocs.lane-handoff.v1
lane: D
machine: desktop-gates
generated: 2026-09-11
generated_at: 4cee1bf7 (main)
queue: [C44, D11, K23, CFG4]
other_queue: [WEB24, API6, LOAD16, H8, L19, META1]
pens: [code:ontology, code:config, code:taxonomy]
---

# Lane D handoff — desktop-gates, 2026-09-11

**From:** the Lane A session (desktop). **To:** the Lane D session on the desktop-gates.
**Lifecycle:** a working handoff, not a durable record — the item files are. When
the queue below is empty, delete this file in the closing commit
(`python .claude/skills/lane-handoff/scripts/handoff.py --check <this file>` says when).

## Pens — declare them in your first commit (CLAUDE.md §0, one pen per surface)

Collisions come from two sessions writing the same surface, not from two sessions
existing. Your first commit message (or your `wip/` branch name) names what you hold:

```text
pen: code:ontology · code:config · code:taxonomy
```

Lane A holds: `backlog · port · adr · gates · snapshot`. Anything not declared by either lane
is off-limits to both until one asks. The item-file claim is the pen for ONE item; this
is the pen for a SURFACE.

## Start ritual — CLAUDE.md §0, cited, not restated

1. `git pull` (fast-forward), read CLAUDE.md, open the board's Ready-to-pull strip.
2. Claim ONE item at a time: push `status: in_progress` in that item file BEFORE work,
   no render (Y5). `git branch --show-current` before every commit (the branch
   guardrail). In-flight work pushes to `wip/<id>-desktop-gates` at the first
   substantive edit (J31).
3. Ids come from the allocator, never from your tree (I6) — but a lane does not mint:
   ideas and groom requests go back to the sender (see the pens above).
4. Per-machine facts are yours to verify: `DRYDOCS_DATA_ROOT`, `DRYDOCS_LOGDIR`, the
   `.env`, and whether Neo4j is reachable here. Venue-stamp any live claim (J18).

## Your queue, in order (4 items) — claim one at a time

Every item below is `todo` with every dependency `done` at the generating commit — the
same rule the board's Ready strip uses (`derive_summary`). Re-check on pull: the other
lane may have moved something. The split is by MODULE (the id series is the module
since PLAN1), so two lanes minting in disjoint series cannot collide on a number.

| # | Id | Title | Type / prio | Module | Model | Notes from the check |
|---|---|---|---|---|---|---|
| 1 | **C44** | The MFTS route ruling now has an evidence base instead of a coin-flip - convene it at the email-dl-contact-point gate, with route identity and the two-leg reading as its own clauses (after N27) | task / p1 | `ontology` | fable | input `config/gate-prompts/email-dl-contact-point.yaml` — pen `gates` (gate prompts — SME sessions run from Lane A); gate-bound: email-dl-contact-point (an SME session, not a build); overlap: C44 <-> WEB24: both name `docs/restructure/03-hitl-sme-flow.md` |
| 2 | **D11** | Run the controlm-definition-precedence gate (after D10) | task / p2 | `config` | fable | input `config/gate-prompts/controlm-definition-precedence.yaml` — pen `gates` (gate prompts — SME sessions run from Lane A); input `config/gate-log.md` — pen `gates` (the signed gate record); gate-bound: controlm-definition-precedence (an SME session, not a build) |
| 3 | **K23** | Are ServiceNow KB articles linked at Deployment Module grain ASSERTED or DEFAULTED? -- the check that decides whether the kb_* family is a real pull candidate | task / p2 | `taxonomy` | sonnet | gate-bound: document-supersession (an SME session, not a build); overlap: K23 <-> LOAD16: both name `config/source-registry.yaml`; overlap: K23 <-> H8: both name `config/source-registry.yaml` |
| 4 | **CFG4** | The software-registry has no schema slot for a governance status on its own dependencies, only on the estate it documents | task / p2 | `config` | sonnet | input `docs/restructure/backlog/items/C33.yaml` — pen `backlog` (items, epics, plan — the board's sources); input `docs/restructure/backlog/items/N24.yaml` — pen `backlog` (items, epics, plan — the board's sources); overlap: CFG4 <-> WEB24: both name `config/taxonomy/software-registry.yaml`; overlap: CFG4 <-> L19: `docs/design` (L19's input, coarse) covers `docs/design/ui-exploration/two-track-ui-plan.md` |

**Flags to rule before claiming** (the script flags; the author decides):

- C44: input `config/gate-prompts/email-dl-contact-point.yaml` — pen `gates` (gate prompts — SME sessions run from Lane A) — Lane A's pen; coordinate before editing.
- D11: input `config/gate-prompts/controlm-definition-precedence.yaml` — pen `gates` (gate prompts — SME sessions run from Lane A) — Lane A's pen; coordinate before editing.
- D11: input `config/gate-log.md` — pen `gates` (the signed gate record) — Lane A's pen; coordinate before editing.
- CFG4: input `docs/restructure/backlog/items/C33.yaml` — pen `backlog` (items, epics, plan — the board's sources) — Lane A's pen; coordinate before editing.
- CFG4: input `docs/restructure/backlog/items/N24.yaml` — pen `backlog` (items, epics, plan — the board's sources) — Lane A's pen; coordinate before editing.

## The `gates` pen moves to this lane for the burst

Three of the four items below are SME sittings, and a sitting writes
`config/gate-prompts/**` and `config/gate-log.md`. Those are Lane A's pens in the generated
surfaces table lower down, and for THIS burst Lane A yields them here. Declare it, because
that table is generated and still shows the default owner:

```text
pen: gates · code:ontology · code:config · code:taxonomy
```

Lane A keeps `backlog`, `port`, `adr` and `snapshot`, and holds no gate work while this file
is live. Two consequences, stated rather than discovered:

- **`config/gate-log.md` is append-only and it is the one file this lane will conflict on
  with itself.** Append at the tail, one record per sitting, and push before the next
  sitting starts. Do not batch three sittings into one commit.
- **A prompt file must exist on disk before an item's `gates:` field names its slug.**
  `test_declared_gates_are_lists_of_known_prompt_slugs` reads the disk, not the prose.

## These gates were SME-DEFERRED two days ago, and queuing them IS the re-arm

On **2026-09-09** nineteen drafted-unsigned gate pages were SME-DEFERRED in one sitting,
each with a NAMED re-arm trigger (`config/gate-log.md`, the record headed
`2026-09-09 — DEFERRED: ...`). That record also says "the lanes stop queuing them until a
trigger fires", so this file has to say which trigger fired for each, or it reads as a lane
ignoring a signed ruling.

| Item | Gate page | Its recorded re-arm | Fired by |
|---|---|---|---|
| **C44** | `email-dl-contact-point` | "C44 convenes it with the MFTS route evidence, as folded 2026-09-07" | the evidence is here and tracked — `internal/research/JOB-MFTS-MM-research.md` |
| **D11** | `controlm-definition-precedence` | **never deferred** — "stays ARMED for its own session per the 2026-09-07 ruling that folded D9 into it" | already armed |
| **K23** | `document-supersession` | K23, claimed when its subject is next needed | this queue |

**Every sitting opens with a stale-premise sweep, and it is not optional.** The deferral
record's own words are "after a stale-premise sweep of the page". The worked example is two
days old: `console-auth-boundary` was deferred in that same sitting, re-armed on 2026-09-10
by WEB22, and its sweep found three facts holding and two moved before a single clause was
ruled. A sitting that skips the sweep rules on a premise the tree has already changed. Date
every marker you move, in the page, in the same commit.

## Two preconditions this lane can clear at the desk, before the SME sits

- **D11 clause D3** — the publishable folder-naming standard's position-6 "frequency =
  legacy" claim is verified against BOTH source standards before the session. Both are
  tracked here: `knowledge/standards/technology/folder-naming-convention.md` and
  `internal/standards/technology/folder-naming-convention.md`. Real desk work; do it first.
- **D11's other precondition is NOT clearable here.** The page keys on an extract, and the
  rule is "older pull means re-pull first" — `config/dev-environment.yaml` says
  `oracle-replica: available: false`, so a re-pull is not possible on this side. If the
  sweep finds the extract stale, that is a BLOCKED outcome with a named blocker, which is a
  legitimate outcome and not a failure. Silence is the only non-outcome.
- **K23's research is already done and already here.** The acceptance as literally written
  is satisfied: `knowledge/upgrade-plans/servicenow-replica-evidence.md` section 11 carries
  the `kb_*` verdict from 2026-08-19. What stays open is a short list of rulings — the read
  path (Snowflake view, ServiceNow API or offline export, each with different freshness and
  permission consequences), the duplicate-test bar, and the rest of 11.4. Read section 11
  before the sitting; do not re-run the research.

## CFG4 is the one build item, and half of it is deliberately not ours

CFG4 has no sitting behind it. Read its own note before starting: "The company-side
enrichment itself is company-owned and does not port; only its schema half is producer work,
which is why (a) stops at the shape." The producer has no governance catalog to read, so
producer rows carry an empty governance value and the guard checks only that
`present implies as_of`. Building the guard against real values would be building against
data this side does not have.

CFG4 is also the only item here that WRITES a file another lane reads, and the overlap check
named both. `config/taxonomy/software-registry.yaml`: CFG4 clause (a) adds the governance
block, WEB24 only reads that file for its clause (e) note about the locked-stack guard, and
WEB24 clause (f) forbids it editing the pin — so the order is free, but tell Lane C when the
block lands so its note cites the shape that exists.
`docs/design/ui-exploration/two-track-ui-plan.md`: CFG4 clause (c) writes a dated paragraph
there and L19 (Lane B, laptop) carries a coarse `docs/design` input. L19 is a doc-drift
sweep, so it may re-read that file after you write it — land CFG4's note and push before
Lane B's sweep reaches it, or hand the paragraph to Lane A to sequence.

## What is NOT in this queue, and why — so nobody adds it back

Six of these were in the first draft of this file and came out on the evidence. The reasons
are recorded so the next pass does not re-add them.

- **G63** — its own notes say it: "Company-side session (real repo names and Bitbucket
  access are Internal)." Section A needs the SME's in-scope repo list, section B needs a
  Bitbucket/GHE census this side cannot run, and section C is the only venue where a human
  may bless `trusted_ref`. It shows on the Ready strip anyway — see the Y7 residue below.
- **K29** — its rider (2) is a hard precondition and it is UNMET: the producer page must
  first be the COMPANY-AMENDED revision, arriving through SME review status packet #1
  (`docs/port/profiling-sync-packet.md` intake step 6). The 5/9 producer draft argues from
  conflicting testimonies; the amended page argues from the source. Convening on the draft
  would rule from the weaker artifact.
- **G100** — a gate with **no gate page**, and the item disclaims drafting one: "wiring this
  one means drafting that prompt, which is its own unit of work and is NOT done here." Its
  clause (e) build also wants a ServiceNow/Snowflake read, and `config/dev-environment.yaml`
  declares no such venue. It needs a drafting item minted before it can be queued at all.
- **G64, G65, G136** — the three DPL gates. The 2026-09-09 record names their trigger as
  "a real DPL export in hand (company-side)". No export, no sitting. G64 also carries a
  `hold:` since 2026-09-07.
- **G132** — declares `venue: [controlm-server]`, and `config/dev-environment.yaml` says
  that venue is not available on this side. The collector runs where the server is.
- **K26** — its gate `fid-identity-and-scope` is **SIGNED 33/33** (`config/gate-log.md`,
  2026-08-19), so it is a BUILD and not a sitting and does not belong in a gate queue. The
  item draws its own line: "The pull itself runs company-side; producer-side this item ships
  mechanism + fixtures, the same split K16 uses." It wants a build-lane slot of its own.
- **C42** — depends on C40, which is `todo`. **E2** — depends on E1, which is `todo` and
  held. **N22** — depends on N23, which is `todo` and is sitting 2, not sitting 1.

**The Y7 residue that put four items on the Ready strip in the first place.** Y7
(2026-09-07) declared a `hold:` block on items whose acceptance opens "USER-GATED START —
the SME convenes the session; the pull loop SKIPS this item until then." Ten items carry
that sentence and six are `done`; of the four still open, **G62 and G64 got the hold while
CFG5, G63, G65 and PLAN11 did not**. A `hold:` is what the board's Ready strip reads (Y7),
so those four say in prose that the pull loop skips them and appear on the strip regardless.
That is why they read as ready. The fix is Lane A's `backlog` pen and is not this lane's to
make.

## Surfaces — who holds which pen this burst

The partition is by SURFACE, not only by item, because the collisions a burst
produces land on shared files rather than on claimed items: the inbox top, the
rendered pages, the snapshot. A lane touches the other lane's pens only by handing
the change back through the sender.

| Pen | Surface | Why |
|---|---|---|
| `backlog` | `docs/restructure/backlog/` | Lane A — items, epics, plan — the board's sources |
| `backlog` | `docs/restructure/IDEAS.md` | Lane A — the idea inbox — one file until R6 shards it |
| `backlog` | `docs/restructure/ideas/` | Lane A — the sharded inbox, once R6 lands (§0 names it already) |
| `backlog` | `docs/plan/` | Lane A — the plan renders: board, roadmap, ideas, load-map |
| `port` | `docs/port/` | Lane A — port prompt, relays, dossiers |
| `port` | `PORT-MANIFEST.yaml` | Lane A — port dispositions |
| `port` | `docs/company-prompts/` | Lane A — the company-facing prompts |
| `port` | `.claude/skills/reconcile-port/` | Lane A — the port skill |
| `adr` | `docs/decisions/` | Lane A — ADRs and their index |
| `gates` (this skill's addition to §0) | `config/gate-prompts/` | Lane A — gate prompts — SME sessions run from Lane A |
| `gates` (this skill's addition to §0) | `config/gate-log.md` | Lane A — the signed gate record |
| `gates` (this skill's addition to §0) | `config/crosswalks/` | Lane A — orchestrator crosswalks — gate-bound config |
| `snapshot` (this skill's addition to §0) | `knowledge/depgraph-snapshots/` | Lane A — the session snapshot — one writer per burst |
| Lane A's queue | the items WEB24, API6, LOAD16, H8, L19, META1 and their inputs | do not claim or edit |
| `code:<module>` | everything an item in YOUR queue names in `inputs` | this lane, claimed per item |
| — | `docs/plan/*.html`, `web/src/generated/**`, `docs/design/*.html` | derived renders — Lane A regenerates once at close; nobody merges them by hand (J43) |

**Lane D claims status-only and never renders.** A claim is one item file, pushed;
Y5 tolerates it un-rendered, and Lane A renders once at close. **Lane D does not
append to `IDEAS.md` while the inbox is one file** (until R6 shards it): even an
allocator-minted id conflicts at the inbox top when both machines insert there in
one burst (observed 2026-09-02, twice). Anything worth capturing goes back to the
sender in your close report.

**Three things the 2026-09-03 burst learned the hard way** (six items, one laptop):

- **Every Lane D CLOSE commit is red on the roadmap guard, and that is expected.** Y5
  tolerates status-only drift; a close writes notes, and Lane D does not render, so
  `test_committed_roadmap_page_matches_its_sources` fails on every `wip/` tip CI runs.
  Read CI for the OTHER jobs and say so in the close report; Lane A's render at merge
  is the fix.
- **A new tracked path that matches no `PORT-MANIFEST.yaml` row fails the fall-through
  guard, and the manifest is the `port` pen.** Hand the row back in the item's notes -
  path, disposition, the one-line reason - and leave the branch red on that guard;
  Lane A adds the row in the merge commit (J62, `.pre-commit-config.yaml`).
- **`render_board.py` refreshes only the plan renders and the generated files it owns.**
  An item that adds its own generated artifact with its own writer (O70's
  `openapi.json` / `api.d.ts` via `scripts/dump_openapi.py` and `npm run api:types`)
  names the writer in its close report, so Lane A runs it at merge if the source moved.

## Rules that have bitten — the durable ones live in CLAUDE.md

- Full suite before every push (`poetry run pytest -q`), plus `ruff check .` and a bare
  `ruff format --check .` — CI blocks on both and ran red for a week once while subsets
  passed locally (§0, Idea-111).
- A guard reads code, not prose (J66); never parse a render (J37); a review names its
  tree (J63). Read them in §6 — this file will not keep up with them.
- Item notes: no backslash escapes through a shell heredoc; write the note with the Write
  tool and run `tests/unit/test_backlog.py` before committing it.
- LANES ARE PRODUCER-SIDE ONLY. The company apply is a THIRD session in a different repo,
  never a lane: it ports methodically, one pen, accuracy over speed — this file never
  exists there. The `port` pen is producer-side and stays with Lane A; never run the port
  from the machine that holds it here.

## Close — in this order

1. Every claimed item `done` and pushed; unfinished work on `wip/<id>-desktop-gates`,
   pushed. No render, no snapshot — those are Lane A's pens.
2. `python .claude/skills/lane-handoff/scripts/handoff.py --check <this file>` — when it
   reports the queue empty, delete this file in the same closing commit.
3. Report back: what closed, what is on `wip/`, what you noticed (that is how ideas
   reach the inbox from Lane D). Lane A merges your `wip/` branches `--no-ff`, deletes
   them, renders once, snapshots once.
