# Next-session handoff

> **Rolling file — overwrite it, do not append.** One screen of "where things stand"
> for picking the work up on the other machine. Durable state lives in
> `docs/restructure/backlog/` (the claim channel — ONE FILE PER ITEM since today) and
> `docs/port-prompt.md`; this is the narrative that git alone does not carry.
>
> **Written 2026-08-20 (desktop, end of the post-reboot session), producer head `213e1d12`
> = tag `port-base-20260820`.**

## 1. A CERTIFIED BASE IS WAITING — the lull port is ready on our side

**`port-base-20260820` @ `213e1d12`**, preflight 7/7 green, range
**`7c18ff4b..port-base-20260820`** (25 commits, 544 paths, ledger steps 171-176).
Anything committed after the tag rides the NEXT port — normal, not a discrepancy.

**The hand prompt is `docs/port-backlog-shard-company-prompt.md`**, filled except
for the company's own dates/branch names. It leads with the one thing that makes
this port unlike every prior one: **step 175, the backlog shard**, applies by a
ONE-TIME sequence — union the monolith under the old rule → run the PORTED
`scripts/shard_backlog.py` on the union → the proof must print `PROOF OK` →
`--tombstone`. The tree is each side's own output; never copied. Everything else
in the range applies by the manifest as usual.

**Company-side precondition before it starts:** their 135-170 port
(`drydocs-port-20260820`, reviewed by us in
`docs/reviews/port-review-7c18ff4b-20260820.md`, verdict mergeable) must be
`--no-ff` MERGED to their main with its follow-ups done — the FID pair as ONE
gate-log commit, the not-port-introduced section, stash pop, `port-prompt.md`
retired (their prompt: `docs/port-7c18ff4b-followup-company-prompt.md`). A
mid-apply range finishes on the monolith; ours is the first step of the next.

**Standing rule from today (memory `hand-prompts-ask-nothing-back`):** producer-
facing text never asks for anything back — no SHAs, no replies, no instance names.
Records live in THEIR ledger. The user will clean `port-prompt.md`'s older wording.

## 2. What landed today (all pushed, CI green at every step checked)

- **The backlog is sharded (Y1 + Y2, ADR 0013).** `backlog.yaml` is an 11-line
  tombstone; items live in `docs/restructure/backlog/items/<id>.yaml`. Roll-ups are
  DERIVED (the board's "Ready to pull" strip = `next_ready`); nothing stores them
  and `test_backlog.py` fails if anything does. **A claim is a one-key edit of one
  item file, committed and pushed before work** — four claims/closes today were
  exactly that. Reader: `drydocs_core.backlog_store`. Groom skill, validator,
  CLAUDE.md §0, and the reconcile-port before-snapshot (now
  `backlog_store.dump_document()`) are re-pointed.
- **F4 ruled:** at a port, backlog `status` is PER-REPO — the consumer's stands,
  the producer's folds into notes (ADR 0013 Clause 4 + the manifest entry_rule).
  Intra-repo (two machines) keeps "never regress / keep the further-along".
- **J51 done:** six PER-ENTRY manifest rows for the paths the company legitimately
  extends (description_tokens, detect, test_runbook_currency, email-dl-contact-
  point, ui-components, doc-source-registry with a field split). Idea-142 closed.
- **C34 done:** `lob-product-team.yaml` declared a skos:ConceptScheme (layer 1);
  gate `dcat-theme-subject-scheme` DRAFTED unsigned (residency recorded as
  answered-by-fold; IS-vs-HAS, depth, detector-cap, pending-vs-out-of-scope posed);
  `catalog_has_theme` + `:Theme` registered PLANNED.
- Port review of 7c18ff4b (five findings) + two hand prompts; Idea-148 (scrape run
  <-> registry row join) inboxed.

## 3. Machine state (desktop)

- **`VIRTUAL_ENV` leak:** Claude Code's shell here pre-sets it to `agents\.venv`;
  prefix `unset VIRTUAL_ENV;` or `poetry run` silently uses the wrong venv. User
  terminals are NOT affected (memory `desktop-virtualenv-leak`). The handoff's
  earlier "repaired venv / S12" worry was this.
- **Worktree `ui-workstream`** (`feat/ui-workstream`) is MERGED and fast-forwarded
  to `213e1d12`, 0 ahead, clean, with its own `.venv`. The user has not worked it
  since; nothing pending there. Do not clean worktrees.
- The FID/port screenshots under the data root and the five `port-*.png` in the
  repo root are gitignored and carry SIDs/handles — never into a tracked surface.

## 4. Open claims

None under this session's name. Laptop claims per the board (`docs/plan/board.html`).
Next producer-side candidates: E1 / K16 / L19 / G62 stay `in_progress` from earlier
sessions; the board's Ready-to-pull strip lists 100+ dependency-ready items, p1s
first: D10, G68, G70.
