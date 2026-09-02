---
name: groom-backlog
description: Groom raw notes into the DryDocs backlog. Use when the user pastes rough to-dos or a photo of paper notes, says "groom my notes" / "groom the backlog" / "add this to the backlog", or when IDEAS.md inbox lines need promoting into backlog/items/<id>.yaml v3 items (title/type/module/phase). Also the weekly grooming ritual.
context: fork
agent: backlog-groomer
background: false
---

# groom-backlog — raw notes → the backlog database

**The mental model (CLAUDE.md §0):** `docs/restructure/backlog/` is the DATABASE — one item per
file, `items/<id>.yaml` (schema `drydocs.backlog.v3`, ADR 0013; guarded by `tests/unit/test_backlog.py`);
`docs/restructure/IDEAS.md`
is the zero-schema INBOX; `docs/plan/board.html` is a deterministic RENDER of the database.
Grooming is the transcription step in between — the user brain-dumps, this skill does the rest.
The user should never have to hand-edit YAML.

## How this skill executes (fork)

This skill runs as a dispatched **`backlog-groomer`** agent (`context: fork`, model pinned to
opus in `.claude/agents/backlog-groomer.md`). The fork does NOT see the chat transcript or any
pasted image — the notes to groom must arrive **inside the skill invocation** (`$ARGUMENTS`)
or **already be in the repo** (`IDEAS.md`). Main session, before dispatching: a photo of paper
notes → transcribe it faithfully in-chat, show the user the transcription, and pass the
transcription text as the arguments; pasted/spoken notes → pass them through verbatim.

## Inputs this skill accepts

1. **Pasted rough text** — bullet lists, sentence fragments, shorthand (passed as arguments).
2. **A photo of paper notes** — main session transcribes first (see above); the fork grooms
   the transcription.
3. **The IDEAS.md inbox** — the standing weekly ritual: groom every line in `## Inbox`
   (no arguments needed; the fork reads the repo).
4. **A single thought in chat** ("add X to the backlog" — passed as arguments).

## Per-note decision procedure

For each note, decide: **promote** (full backlog item), **inbox** (park in IDEAS.md), or
**merge** (fold into an existing item's acceptance/notes — `grep -rl <keyword> docs/restructure/backlog/items/` first).

**Promote** when the note is actionable and scoped enough to write a pass/fail acceptance test.
**Inbox** when it is a direction, question, or needs a decision the user hasn't made — format
as `- [tag] one line. (why/where seen)` with tag ∈ idea | bug | doc | source | question | chore.
**Merge** when an existing item already covers it (note the merge in the audit trail).

### Fields for a promoted item (all REQUIRED — the schema test enforces them)

| Field | How to choose |
|---|---|
| `id` | **Ask the allocator — do not read it off the tree** (I6): `python .claude/skills/groom-backlog/validate.py --next-id --module <module>`. **The series IS the module** (ruling 2026-09-02): the allocator derives the code from `modules.yaml` `series:` — `drydocs-load` → `LOAD12` — and you never pick a letter. The 27 legacy letters (A..Z, GN, MM) are FROZEN at their 2026-09-02 max; the allocator refuses them and so does `test_backlog.py` (the company's six legacy band ids, `G10001-G10003` / `DD10001-DD10003`, are frozen at the band's own max by `FROZEN_BAND` — PLAN3 — and read as legacy, not strays). Free in YOUR tree is not free: it unions the local items, every remote ref's tree listing, and every id ever added in history, then returns max+1 (a gap is usually a BURNED id, not a free one). It refuses the DD-series and the company band by itself. A new MODULE (not a new theme) is a `modules.yaml` edit — name + series code together. Then **mint the way a pull is claimed: write the stub, commit and PUSH it, then write the body** — and give the stub its **FINAL title**, because the collision guard compares titles, so a title refined between the two pushes reads as two machines minting one number and reds the guard until the body lands. The stub commit also carries the refreshed board and roadmap: Y5 tolerates status-only drift, not a new item, so a render-less stub reds the roadmap guard until the body lands. |
| `title` | Plain English, understandable in 6 months with zero context. Never rely on codenames. |
| `type` | `requirement` (future capability ask) / `task` (concrete work) / `chore` (hygiene, docs, renames) / `bug` (defect). |
| `module` | From `docs/restructure/backlog/modules.yaml`. Code work → the MODULE_MAP component; non-code → a work area (taxonomy/ontology/config/reference/graph-infra/docs). |
| `phase` | From `plan.phases`. A note that fits no phase is a **plan change** — propose a new phase to the user, never invent one silently. |
| `agent` | A `.claude/agents/` name for scoped layer work, else `main`. |
| `model` | The model matrix: **fable** (Mythos-class, the top tier since 2026-07-10) only where a decision changes schema/ontology/boundary; **opus** = the former top tier, still valid on existing items (re-tier to fable when a groom touches them); **sonnet** for work with a written acceptance test; **haiku** for lookups, renames, ritual wiring. |
| `priority` | p0 blocker / p1 / p2 / p3. |
| `depends_on` | Ids that must be `done` first; `[]` if startable now. |
| `acceptance` | A pass/fail test. If you cannot write one, the note is not ready — inbox it. |

### The two hard rules

- **Park (never guess) ONLY when `module` or `phase` is genuinely ambiguous** — two+ plausible
  assignments with different consequences. The fork cannot ask the user mid-run: leave the note
  in the `IDEAS.md` inbox as `- [question] …` and flag it in the final report for the user to
  rule on. Everything else: pick sensibly and record the choice in `notes:`. (Grooming that
  parks everything is worse than paper notes.)
- **Never groom an ontology/relationship-semantics decision into a done deal.** Anything
  touching edge meaning routes through the HITL gate (`docs/restructure/03-hitl-sme-flow.md`)
  — the item's acceptance must say "via the gate", and the mapping stays `planned` until confirmed.

## Mechanics of a groom run (in order)

1. **Write one file per promoted item**: `docs/restructure/backlog/items/<id>.yaml`, a
   standalone mapping (`id`, `epic`, `title`, `type`, `module`, `phase`, `agent`, `model`,
   `priority`, `status`, `depends_on`, `inputs`, `acceptance`, `notes`). The filename IS the
   id. Merges edit the existing item's file. A groom note about the epic goes to
   `epics/<epic>.yaml` → `groom_log` (date + note) — that replaces the old comment headers.
2. **Nothing to recompute.** Roll-ups (`summary`, `next_ready`) are DERIVED by
   `render_board.py` and never stored (ADR 0013 Clause 3) — a stored one FAILS the guard.
   `python .claude/skills/groom-backlog/validate.py` prints the derived counts.
3. **Update `IDEAS.md`**: new parked notes go to `## Inbox` (top); every groomed line MOVES to
   `## Recently groomed (audit trail)` with the date and resulting id(s), e.g.
   `- 2026-07-01 — [chore] fragment cleanup → J1.`
4. **Validate** — the acceptance gate for this skill:
   ```bash
   poetry run pytest tests/unit/test_backlog.py -q
   # poetry/pytest absent (some authoring envs)? Standalone equivalent (same checks):
   python .claude/skills/groom-backlog/validate.py
   ```
5. **Regenerate the board** so the committed render matches the database:
   ```bash
   PYTHONPATH=. python scripts/render_board.py
   # PowerShell equivalent: $env:PYTHONPATH = "."; python scripts/render_board.py
   ```
6. **Commit**: `chore(backlog): groom — <n> promoted, <n> inboxed, <n> merged`, listing new ids
   in the body. Push per the session ritual.

## Graph cross-check (optional, needs Neo4j)

Purely optional enrichment — a groom with no database running is NEVER blocked by
this section; skip it silently when the local `drydocs` DB is down (the offline flow
above is complete on its own).

When the container IS up, two cheap checks catch transcription mistakes:

- **Module sanity:** for a code item, compare its `module:` against the code-graph
  census (`MATCH (m:CodeModule) WHERE NOT m:SchemaMeta AND m.removed_from_source_at
  IS NULL RETURN m.project, count(*)` — tombstones filtered per U13, or a swept
  package still counts under its old root) — an item filed against a module whose
  files the graph places in a different root is probably mis-binned.
- **Close-note claims:** before flipping an item `done`, spot-check file paths named
  in its close note against `:CodeModule.file_id`, RETURNing
  `removed_from_source_at` — tombstones belong in this answer (U13 note): a
  tombstoned hit means the file existed and was removed (fine for history),
  where no hit at all means the claim names a file the graph has never seen and
  deserves a manual look before it becomes history.

Run both via a scratchpad script using `Neo4jSettings` from `drydocs_core.config`
(never raw env vars); the guarded-query conventions live in
`.claude/skills/tech-debt/SKILL.md`. The validator/test flow above is unchanged
either way.

## Model guidance

This skill was authored on opus (I3). Since 2026-08-07 every groom runs on **opus** via the
`backlog-groomer` fork — the model is pinned in `.claude/agents/backlog-groomer.md`, not here
(a skill-level `model:` field governs the main turn, not the fork). A groom that implies a
plan change (new phase, new epic with cross-cutting scope, priority conflicts) is still a
user decision: propose it in the final report, never enact it silently.

## Gotchas

- YAML titles containing `:` must be quoted.
- Adding an item with `depends_on` on a non-`done` item? Fine — it just stays out of `next_ready`.
- `validate.py` and `test_backlog.py` implement the same checks; if they ever disagree,
  `test_backlog.py` wins — fix the validator.
- Do not renumber or delete existing ids — ids are stable references (audit trail, gate log,
  commit messages).
