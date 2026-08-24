# Company-side prompt — apply the port that carries the backlog shard (Y2, ADR 0013)

> Producer-drafted 2026-08-20 for the company-side assistant. Paste or read whole.
> **Filled at base certification 2026-08-20.** The remaining `⟨…⟩` are YOUR values
> (your apply date, your branch/backup names) — fill them as you start. This port is different from every prior one in exactly one
> place: **the backlog step**. The `docs/restructure/backlog.yaml` you hold is a
> 21k-line monolith; the producer's is an 11-line tombstone beside a directory of
> one-file items. The manifest row for that path carries a ONE-TIME sequence, spelled
> out below, and the `reconcile-port` skill's generic per-entry rule does **not**
> apply to it this once. Everything you record lives in **your** upgrade ledger
> (`port-exec-state.md`, your PORT-REPORT) and stays there; nothing is sent back.

## Range and preconditions

| | |
|---|---|
| Certified base | tag **`port-base-20260820`** (producer preflight 7/7 green 2026-08-20; a tag is immutable — `git rev-parse port-base-20260820` is the sha, fetch it fresh) |
| Range | `7c18ff4b..port-base-20260820` — 25 commits incl. the roll, 544 paths; six ledger steps 171-176 |
| Your branch / backup | `drydocs-port-⟨your date⟩`; tag `pre-cewilson-port-⟨your date⟩` before anything |
| Read authorities at | `cewilson/port-base-20260820` (the tag, never a cached ref): `PORT-MANIFEST.yaml`, `docs/decisions/0013-backlog-sharding.md`, `docs/restructure/backlog/README.md` |

**Freeze precondition — check it before step 1, not after.** The backlog sequence
below is only safe on a **committed, quiet** monolith. Last port your tree carried
uncommitted `.py` captures and three stashed HR files. Before you begin: commit or
stash everything, confirm `git status` is clean, and confirm no other session on
your side is editing `docs/restructure/backlog.yaml`. If a port range is **already
mid-apply** when you read this, finish that range on the monolith and make this
sequence the first step of the next one — never splice it in (ADR 0013 Clause 6).

## The backlog step — the ONE-TIME sequence, in this order

This replaces the per-entry union you ran for `backlog.yaml` at the last four ports.
It is four steps and the third one is a gate.

**1. Union the monolith under the OLD rule, one last time.** Your `backlog.yaml`
vs. the producer's last monolith state — which is the parent of the Y2 merge commit
in the range, `git show 4040c47e:docs/restructure/backlog.yaml` (`4040c47e` is the Y2 claim commit,
the last commit that touched the monolith as a monolith; the tombstone itself holds no items). Id-keyed `items[]`; never drop
an entry; **your `status` stands** — a port never writes status (the F4 ruling,
Clause 4: same id, same work, two independent completions); the producer's status +
date fold into `notes` as information. Company-only items stay. Write the result
back to `docs/restructure/backlog.yaml` and **commit it** as its own commit — this
is the last monolith state on your side and the splitter's input, and it must be
recoverable on its own.

**2. Run the PORTED splitter on that union.**

```
poetry run python scripts/shard_backlog.py --date ⟨your apply date, YYYY-MM-DD⟩
```

It writes `docs/restructure/backlog/` (items/, epics/, plan.yaml, modules.yaml,
README.md) beside the monolith and prints the header-block → epic attachments.
Company-only items and your statuses survive by construction — they were in the
input. Do **not** copy any file from the producer's `backlog/` tree; the tree is
each side's own output, never the thing that ports.

**3. The proof must pass.** The same command runs it and prints `PROOF OK` or a
list of failures: every item deep-equals its monolith entry (minus the one
additive `annotations` field, which must equal the harvested inline comments),
`plan` and `modules` identical, the derived summary equal to the union's stored
counts and `next_ready` set. **A failed proof stops the port at this step** —
record the failure lines in your ledger and leave the monolith in place; do not
hand-edit the tree to make the proof pass. The two known benign causes are a
stored roll-up that was already stale in your union (recount it in step 1 and
re-run) and a duplicate mapping key the old loader tolerated (fix it in step 1).

**4. Tombstone.**

```
poetry run python scripts/shard_backlog.py --date ⟨your apply date, YYYY-MM-DD⟩ --tombstone
```

Re-runs the proof, then replaces `backlog.yaml` with the 11-line pointer. Commit
the tree + tombstone together. `tests/unit/test_backlog.py` now guards that the
tombstone never regrows an `items:` key.

From this commit on, your backlog is the tree, and every later port resolves it by
the new rows: `backlog/items/*.yaml` **per-entry where the entry is the file**
(disjoint ids are plain git; the same id is one small conflict, your status stands),
`backlog/epics/*.yaml` union-append, `plan.yaml` / `modules.yaml` per-entry.

## What changes for you after this port

- **A claim is one file.** `status: todo → in_progress` in `items/<id>.yaml`,
  commit, push. No summary block to recount; `test_backlog.py` now FAILS if one is
  stored anywhere.
- **`next_ready` is on the board.** `render_board.py` derives it — the "Ready to
  pull" strip — and `python .claude/skills/groom-backlog/validate.py` prints it.
- **The reconcile-port before-snapshot for the backlog is no longer a `cp`.**
  Step 1 of the skill now dumps the assembled tree under the old filename:
  `drydocs_core.backlog_store.dump_document()` → `<before-dir>/backlog.yaml`. The
  status-regression guard compares that against the post-port tree.
- **Your own helpers that opened `backlog.yaml`** (claim/close scripts, any board
  tooling of yours) re-point to `drydocs_core.backlog_store.load_backlog_document()`.
  The producer's desktop-local ones were re-pointed the same day; yours are yours.

## Also in this range (the rest is ordinary)

Six ledger steps 171-176 — the file is `docs/port/port-prompt.md` at producer HEAD
and `docs/port-prompt.md` at the tag (S9 moved it after this base was certified);
read them in order, they are short:

- **171** — `constraints.cypher` is now per-entry by constraint name (your two
  snow-hpsm constraints stay); the `fcdo-frameworks` doc-source row reads VERBATIM
  and its LOAD is a hand prompt you already hold.
- **172** — ADR 0013, the sharding design (clean-add).
- **173** — the 7c18ff4b port review + the two follow-up prompts (clean-add; their
  conditions are already in your ledger).
- **174** — **J51's six PER-ENTRY rows land in `PORT-MANIFEST.yaml`** for
  `description_tokens.py`, `detect.py` + `__init__.py`, `test_runbook_currency.py`,
  `email-dl-contact-point.yaml`, `ui-components.yaml`, `doc-source-registry.yaml` —
  the six files caa0406 unioned by hand. The manifest is canonical-producer: take it
  FIRST, then resolve those six by their new rows. Also the F4 ruling (status is
  per-repo at a port — what your 2026-08-11 union already did).
- **175** — the shard itself: this prompt.
- **176** — C34: `lob-product-team.yaml` gains a `concept_scheme` block (per-entry —
  your real LOB rows stay, the block is mechanism); a new gate prompt
  `dcat-theme-subject-scheme.yaml` (clean-add; you run your own gate); two PLANNED
  vocabulary entries. The ui-workstream merge trio rides here as ritual.

Apply those by the manifest as usual — read it first (`git show port-base-20260820:
PORT-MANIFEST.yaml`), per-entry rows resolve inside the file, canonical-company rows
keep yours. Nothing else in this range has a special sequence.

## Acceptance

Track-1 as always (`tests/unit/`), plus the three guards this port adds:
`test_backlog.py::test_monolith_is_a_tombstone`, `::test_no_stored_rollup`,
`::test_path_is_the_identity`. The J7 per-entry guards run around the merge with
the dumped before-snapshot. Board regenerated from the tree.

## Done when

Tree + tombstone committed on your branch with the proof line in the commit
message; the step-1 union commit recoverable beneath it; Track-1 green; PORT-REPORT
written with every kept divergence in the census and a line stating the backlog
sequence ran (steps 1–4, the proof's item count). **Record it in
`port-exec-state.md` as you have been** — that ledger is the record and it is
yours. Nothing is reported back. The `--no-ff` merge to `main` is the SME's call.

---

## Producer-side record (not part of the paste)

Drafted 2026-08-20 on the day Y2 merged (`01cfd7dc`), ahead of base certification,
so the one new mechanic is written while it is fresh. To fill at certification:
the base tag + sha, the range, the Y2-parent sha (`git rev-parse 01cfd7dc^1` is
`4040c47e` today — re-derive if history moves), and the "also in this range" list.
Authority for the sequence is the `PORT-MANIFEST.yaml` row for
`docs/restructure/backlog.yaml`; this prompt restates it, it does not replace it.
Written under the 2026-08-20 rule: nothing asked back, instance names nowhere.
