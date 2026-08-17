# Next-session handoff

> **Rolling file — overwrite it, do not append.** One screen of "where things stand"
> for picking the work up on the other machine. Durable state lives in
> `docs/restructure/backlog.yaml` (the claim channel) and `docs/port-prompt.md`; this
> is the narrative that git alone does not carry.
>
> **Written 2026-08-17 (laptop), producer head `2d107ce`.**

## 1. Read this first — the desktop is push-blocked and holds one stranded commit

The desktop's git credential helper cannot authenticate. **GCM stores tokens in
Windows Credential Manager, so this is per-machine**: signing in on the laptop
unblocked the laptop and did nothing for the desktop. The desktop stays blocked
until someone is physically at a desktop session to finish the browser sign-in.

**What is stranded there:** `5ca7dc8f`, "roadmap fix: Idea-23/47 rows retired +
re-render", committed on `main` and unpushed.

**It is already handled — do not redo it and do not worry about the collision.**
The identical fix was made on the laptop and pushed as `63551c8`. Same two row
deletions, same re-render, byte-identical. When the desktop's push finally lands:
**pull-and-merge leaves an ordinary duplicate commit** making the same two deletions
(harmless, but it IS a second commit); **`git pull --rebase` drops it as empty**.
Prefer the rebase. **Ledger step 156 records this** so a future range cut does not
read the duplicate as a second change.

**The one thing a desktop session must NOT do when it comes back:** draft the ledger
roll. That offer is superseded — the roll is done and pushed (§2). Pull first.

## 2. The port loop — a new base is CERTIFIED and pushed

`port-base-20260817` @ `0c355f5`, pushed to origin. Preflight **7/7 CERTIFIED**
(tree clean, relay basis tags, ledger coverage 116/116, cited paths resolve, renders
current, suite green, tag). Offer that tag as the port base — never a bare SHA.

Ledger rolled to **steps 135-157** (115 commits since `caa0406`: 93 cited, 22
ritual). Steps 106-123 collapsed; **124-134 deliberately stay live.**

**The finding worth carrying forward:** the `caa0406` port's close-out never reached
this repo. `ae21ee4` got an explicit "MERGED company-side, branch removed" commit
(`06d4469`); `caa0406` got a report, a producer review (`ca7a121`), and then silence.
So "Last completed port" is now split in two — the four J35 fields stay on `ae21ee4`
where all four are known, and a new "Last DELIVERED port" block names `caa0406` with
port commit / backup tag / acceptance marked **UNRECORDED rather than guessed**.
RELAY-7 and the four `ca7a121` divergences are producer *beliefs* about company state
until re-checked. **First action at the next port: fill those three fields.**

## 3. Ritual state — all green

- Suite **2150 passed / 8 skipped**. Both ruff gates clean.
- **CI GREEN at `0c355f5`** — and green at every commit this session. It had been RED
  on origin from 08-14 to 08-17 on `test_real_roadmap_cites_only_live_inbox_ideas`.
- Depgraph snapshot current: `drydocs-20260817.json` @ `0c355f5`, and it recorded
  **`dirty: false`** on its own — the Idea-121 LF fix holding, exactly as step 151
  predicted. Newest-only retention removed the 08-13 file.
- Renders verified deterministic: re-rendering board + design docs produced zero drift.

## 4. One new defect, filed not fixed

**Idea-129** — the snapshot JSON is still written CRLF (31,505 CRLF / 0 bare LF in
`drydocs-20260817.json`). `snapshot.ps1:391` passes the depgraph tool's `$raw`
through `WriteAllText` unchanged, so Idea-121's fix to the 11 Python `write_text(`
sites never reached it. Filed **Low** deliberately: `.gitattributes` normalizes the
blob, `meta.git.dirty` is computed *before* the write so it stays honest, and
newest-only retention means each snapshot is a new file rather than a re-dirtied one.
So it does **not** reproduce Idea-121's actual harm — burying the stale-render signal.
Same class, different surface, much smaller blast radius.

## 5. Board state

**119 todo · 4 in progress · 1 blocked · 313 done** (437 total).

In progress, all four SME/gate-bound rather than stalled builds: **E1** (SOSA),
**G32** (the database-count gate, reopened downward to ONE on retrieval grounds —
see step 143), **Y1**, **G62** (rua-bundle data profile; §A opened producer-side, §B
runs company-side).

## 6. The pattern from this session

The previous handoff named *a check that fires correctly but whose remedy is wrong*.
This session's is narrower and worth keeping: **an exemption list is a claim about
what does not matter, and it goes stale silently.** The port preflight's ledger-coverage
check surfaced 11 "uncited" commits I had classified as ritual — `chore(ideas):`, a
`chore(snapshot):` that should have been `chore(depgraph): snapshot`, `style(...)`,
and `chore(backlog): <id> done`. The check was right and my classification was wrong,
because the exemption matches on the commit SUBJECT and is deliberately narrow so a
substantive commit can never hide behind a prefix. Two of those "ritual" commits
turned out to carry real content for a consumer — two graph-instrument bugs, and a
sequencing constraint about `%%var` resolution. They are cited now, in step 157, which
says why they are there. **Prefer the guard that makes you rule on something over the
classification you find convenient.**
