---
name: groom-backlog
description: Groom raw notes into the DryDocs backlog. Use when the user pastes rough to-dos or a photo of paper notes, says "groom my notes" / "groom the backlog" / "add this to the backlog", or when IDEAS.md inbox lines need promoting into backlog.yaml v2 items (title/type/module/phase). Also the weekly grooming ritual.
---

# groom-backlog — raw notes → the backlog database

**The mental model (CLAUDE.md §0):** `docs/restructure/backlog.yaml` is the DATABASE
(schema `drydocs.backlog.v2`, guarded by `tests/unit/test_backlog.py`); `docs/restructure/IDEAS.md`
is the zero-schema INBOX; `docs/plan/board.html` is a deterministic RENDER of the database.
Grooming is the transcription step in between — the user brain-dumps, this skill does the rest.
The user should never have to hand-edit YAML.

## Inputs this skill accepts

1. **Pasted rough text** — bullet lists, sentence fragments, shorthand.
2. **A photo of paper notes** — transcribe it faithfully first, show the transcription,
   then groom the transcription.
3. **The IDEAS.md inbox** — the standing weekly ritual: groom every line in `## Inbox`.
4. **A single thought in chat** ("add X to the backlog").

## Per-note decision procedure

For each note, decide: **promote** (full backlog item), **inbox** (park in IDEAS.md), or
**merge** (fold into an existing item's acceptance/notes — search `backlog.yaml` by keyword first).

**Promote** when the note is actionable and scoped enough to write a pass/fail acceptance test.
**Inbox** when it is a direction, question, or needs a decision the user hasn't made — format
as `- [tag] one line. (why/where seen)` with tag ∈ idea | bug | doc | source | question | chore.
**Merge** when an existing item already covers it (note the merge in the audit trail).

### Fields for a promoted item (all REQUIRED — the schema test enforces them)

| Field | How to choose |
|---|---|
| `id` | Next free number in the matching epic's letter; new theme → next free letter with an epic comment header. NEVER allocate the DD-series (`DD1`, `DD2`, …) — reserved for company-side-only items (cross-repo convention 2026-07-20, git-readme.md). |
| `title` | Plain English, understandable in 6 months with zero context. Never rely on codenames. |
| `type` | `requirement` (future capability ask) / `task` (concrete work) / `chore` (hygiene, docs, renames) / `bug` (defect). |
| `module` | From the `modules:` registry in backlog.yaml. Code work → the MODULE_MAP component; non-code → a work area (taxonomy/ontology/config/reference/graph-infra/docs). |
| `phase` | From `plan.phases`. A note that fits no phase is a **plan change** — propose a new phase to the user, never invent one silently. |
| `agent` | A `.claude/agents/` name for scoped layer work, else `main`. |
| `model` | The model matrix: **fable** (Mythos-class, the top tier since 2026-07-10) only where a decision changes schema/ontology/boundary; **opus** = the former top tier, still valid on existing items (re-tier to fable when a groom touches them); **sonnet** for work with a written acceptance test; **haiku** for lookups, renames, ritual wiring. |
| `priority` | p0 blocker / p1 / p2 / p3. |
| `depends_on` | Ids that must be `done` first; `[]` if startable now. |
| `acceptance` | A pass/fail test. If you cannot write one, the note is not ready — inbox it. |

### The two hard rules

- **Ask the user ONLY when `module` or `phase` is genuinely ambiguous** — two+ plausible
  assignments with different consequences. Everything else: pick sensibly and record the
  choice in `notes:`. (Grooming that asks about everything is worse than paper notes.)
- **Never groom an ontology/relationship-semantics decision into a done deal.** Anything
  touching edge meaning routes through the HITL gate (`docs/restructure/03-hitl-sme-flow.md`)
  — the item's acceptance must say "via the gate", and the mapping stays `planned` until confirmed.

## Mechanics of a groom run (in order)

1. **Edit `backlog.yaml`**: add promoted items under their epic (keep the epic comment headers);
   apply merges.
2. **Recompute the roll-ups** (test-enforced, they may not drift):
   - `summary:` counts = exact item counts per status;
   - `next_ready:` = exactly the `todo` items whose every `depends_on` is `done`.
3. **Update `IDEAS.md`**: new parked notes go to `## Inbox` (top); every groomed line MOVES to
   `## Recently groomed (audit trail)` with the date and resulting id(s), e.g.
   `- 2026-07-01 — [chore] fragment cleanup → J1.`
4. **Validate** — the acceptance gate for this skill:
   ```powershell
   poetry run pytest tests/unit/test_backlog.py -q
   # poetry/pytest absent (some authoring envs)? Standalone equivalent (same checks):
   python .claude/skills/groom-backlog/validate.py
   ```
5. **Regenerate the board** so the committed render matches the database:
   ```powershell
   $env:PYTHONPATH = "."; python scripts/render_board.py
   ```
6. **Commit**: `chore(backlog): groom — <n> promoted, <n> inboxed, <n> merged`, listing new ids
   in the body. Push per the session ritual.

## Model guidance

This skill was authored on opus (I3). **Routine grooming runs on sonnet** — the schema,
registries, and validator carry the judgment. Escalate to opus only when a groom implies a
plan change (new phase, new epic with cross-cutting scope, priority conflicts).

## Gotchas

- YAML titles containing `:` must be quoted.
- Adding an item with `depends_on` on a non-`done` item? Fine — it just stays out of `next_ready`.
- `validate.py` and `test_backlog.py` implement the same checks; if they ever disagree,
  `test_backlog.py` wins — fix the validator.
- Do not renumber or delete existing ids — ids are stable references (audit trail, gate log,
  commit messages).
