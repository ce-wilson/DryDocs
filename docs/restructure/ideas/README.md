# docs/restructure/ideas/ - branch-side idea capture (PLAN4 d)

`pending-<branch>.md` files live here: the candidates a session captures while it works on
a branch or in a worktree, so that the inbox top of `../IDEAS.md` - the one surface two
machines collide on in a burst - is written only at LANDING, by one allocator pass.

- **Shape.** One candidate per bullet, in the inbox header shape with `Idea-?` for the
  number, appended at the BOTTOM (top = oldest capture = lowest number at landing):
  `- **`Idea-?`** · 2026-09-05 · `[tag]` · **open** · prio? **Med** — **title.** body`
- **Never a real id.** A pending file never contains an `Idea-<n>` header; an id exists
  only from the landing pass. Guarded by `tests/unit/test_plan_ideas.py`.
- **Landing.** `python .claude/skills/groom-backlog/validate.py --mint-pending <file>`
  allocates every candidate consecutively through `next_idea_id()` (the same three rules
  every id gets: max+1 over local, every remote ref and history; the floor; the venue
  check), inserts the headers at the top of `## Inbox` newest first, and empties the file.
  Then render, commit and push - the mint is a claim like any other (I6).
- **Disposition.** `pending-*.md` is never-port; this README is canonical-producer
  (`PORT-MANIFEST.yaml`). The sharded inbox that R6 may one day put in this directory
  gets its own rows when it lands.

Owned by the `backlog` pen (CLAUDE.md §0). The allocator that reads these files is
`.claude/skills/groom-backlog/validate.py`; the edit rule for an entry another venue
owns is in the same file (`--check-venue-edits`) and in the groom-backlog skill.
