# Lane B handoff — build lane (laptop), 2026-08-28

**From:** the desktop Lane A session (gate runway + sync intake), per the two
approved plans: the base close-out (gates + priority builds; TE strictly
after) and the source-registry two-issue redesign (WP-2 = the ungated
builds). **To:** the laptop session (`session_01D8bDeeseCJuG7rKSAbDhE8`,
sandbox checkout `C:\coding\projects\sandbox\DryDocs`).
**Lifecycle:** this file is a working handoff — when the queue below is
empty, delete it in the closing commit (it is not a durable record; the item
files are).

## Start ritual (your status said "11 behind" — it is 14+ now; plain ff)

1. `git pull` (fast-forward — your `c0ae3004` is an ancestor; nothing local
   conflicts). Then the normal ritual: read CLAUDE.md, board Ready strip.
2. Per-machine facts are yours to verify (ADR 0014): `DRYDOCS_DATA_ROOT` /
   `DRYDOCS_LOGDIR` env, and the sandbox checkout needs its own `.env`
   (settings anchor on the install, not the repo). None of the first three
   queue items needs Neo4j or Oracle — they are code+tests only.
3. `git branch --show-current` before every commit; claim pushed BEFORE
   work (status: in_progress in the ONE item file, commit+push, no render —
   Y5); unfinished work pushes to `wip/<id>-laptop`; explicit-path staging
   only.

## What you will pull (14 commits since your HEAD, all desktop Lane A)

Port close-out for PORT-REPORT-e33f8d02 + three adoption dossiers + groom;
two G68 remediation fixes; C28 evidence (the Chase leadership scrape +
doc-source-registry row); the SME-review-status capture protocol
(docs/port/profiling-sync-packet.md — reverse-channel rules) + the
never-port template; 13 run-the-gate items (K29, G116-G120, C35-C37, MM11,
N18, J56, D11); Ideas 180-184; the python-architect persona review of
Idea-181; relay discipline + the dual-generation cli.py divergence ledger
entry; and WP-1 of the two-issue plan: gate prompt
`source-connection-and-run-identity` (DRAFTED, unsigned) + items
N19/N20/N21/G121/G122 + the S13/S15 cross-cite.

KNOWN PROSE-VS-TREE GAP, not a defect: Idea-179/184 and two reviews cite
`docs/decisions/0015-team-edition-template.md` — that ADR is another
desktop session's UNCOMMITTED draft, so it will not exist in your tree.
Read the citations as forward references; do not create the file.

## Your queue, in order (claim one at a time)

1. **G121** (bug, p2) — close the undeclared `--csv` acquisition route.
   `drydocs load <name> --csv <path>` resolves through
   `data_zones.read_zone_containing()`; inside a declared read zone → loads,
   run record names the zone; outside every zone → REFUSE (exit 2, message
   points at landing-zones) unless an explicit override flag is passed, and
   the override records itself in BOTH the run record and the disk log.
   Reuse `drydocs/chain_inputs.py` as the resolution pattern — mint no
   second mechanism. Guard test proves refusal AND recorded override,
   **RED before the fix**. Dated discharge note on G78's "--csv untouched"
   close-note caveat.
2. **G122** (chore, p3) — `.env.example` completeness guard: every env-var
   name the `drydocs_core/config.py` settings groups imply
   (env_prefix + field names) appears in the committed `.env.example`.
   Names only; failure message names the missing key and the group.
3. **S13** (bug, p2) — the CLI circular-import fix. **S15 is the same
   defect and closes in the same commit** (cross-cite + depends_on landed
   2026-08-28; both files carry the note). Acceptance highlights: all six
   `cli_*` modules import FIRST in fresh interpreters; the guard runs each
   import in its OWN SUBPROCESS (in-process proves nothing), proven RED
   first; `tests/unit/test_repo_paths.py` passes standalone; the S8
   contracts survive (composition root, flat merge, `_client` through the
   root); no silent loosening of the module-boundary entrypoint exemption.
   Candidate shapes are in the item — the hoist-shared-state option is the
   only one that removes the cycle rather than reordering it.
4. Then the base-plan Lane B clusters, in the user-ruled priority order:
   **S14** (docs/Product → knowledge/org relocation, 4 living-reference
   fixes; the K20 gate is still unsigned, so the prompt citation repoints —
   read the item), then **seal-attribution** (G71, G72, G73, G74, K27,
   K28), then **docmeta** (Q15, Q17, Q18, Q21, Q23, Q24, Q26, Q27).

## Do NOT touch (Lane A surfaces — the desktop session owns them)

`config/gate-prompts/**`, `config/gate-log.md`, `PORT-MANIFEST.yaml`,
`config/crosswalks/**`, `docs/port/**`, `.claude/skills/reconcile-port/**`,
`docs/restructure/IDEAS.md`, and all grooming (no new items, no status edits
on items you have not claimed). **N20 and N21 are GATED — do not build them;
their gate (`source-connection-and-run-identity`) is drafted, unsigned, and
N19 (the sign-off session) has not run.** Gate-runner items (K29, G116-G120,
C35-C37, MM11, N18, J56, D11, N19) are SME sessions, not build items.

## Rules that have bitten this month (so they do not bite you)

- **Full suite before every push** — subset runs caused 3 CI reds
  (exact-set pins live outside the files you touched). And the set-not-count
  trap: agreeing on a failure TOTAL is not agreeing on its contents;
  "clean" claims also run the repo-wide guard family (module boundary,
  render determinism, no-render-parsing, repo paths).
- `ruff format --check .` **bare, never piped** (a pipe eats the exit code).
- Item done-notes: no `\n`-style escapes via heredoc — broke item YAML at
  the pushed sha twice; run `test_backlog.py` before committing any note.
- Session close: item statuses pushed (done included), board + design
  renders regenerated, commit+push, `gh run list` at YOUR pushed sha, then
  the depgraph snapshot (`knowledge/depgraph-snapshots/snapshot.ps1`) if
  your machine runs it. Anything unfinished or noticed → tell the desktop
  session or leave a `wip/` branch; do not append to IDEAS.md (Lane A owns
  the inbox — hand ideas back through the SME).
- Venue-stamp any live-verification claim (J18): your machine's graphs are
  independent of the desktop's.

## Coordination

The desktop Lane A session stays live on: sync-packet intake (packet #1 =
the company-amended K20 gate page, still awaited), gate-prompt surfaces,
grooming, and the SME gate queue prep. If you need a groom, a manifest row,
or an IDEAS entry, hand it back through the SME rather than editing Lane A
surfaces. Claim collisions are prevented by the pushed-claim rule — check
`git branch -r --list "wip/*"` before touching anything already
in_progress.
