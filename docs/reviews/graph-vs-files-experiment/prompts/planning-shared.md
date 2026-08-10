# Task (identical for both tracks): groom-backlog PLANNING run — Ideas 96–103

You are producing a GROOM PLAN, not performing the groom. Nothing is committed;
your deliverable is a single markdown report returned as your final message AND
written to the results path given in your track block.

Input: `docs/restructure/IDEAS.md`, the ungroomed cohort Idea-96 through
Idea-103 (top of file). Backlog conventions: schema `drydocs.backlog.v2` in
`docs/restructure/backlog.yaml` (read its header comment for the field contract;
the `summary` block is computed; `type` enum is bug/chore/requirement/task).

For EACH idea, decide and justify:
1. Disposition: promote to a backlog item / merge into an existing item (name
   it) / park / needs-SME (say what question).
2. If promote: draft the item — id (next free in the right epic series), epic,
   module, agent, model, priority, depends_on, and a one-sentence acceptance.
3. Code-context sizing: which files/modules the item touches, HOW YOU LOCATED
   them (this is the experiment's core — show your navigation), and a
   S/M/L size call.

Constraints:
- Follow your TRACK RULES (below) for all code-context navigation. Task inputs
  (IDEAS.md, backlog.yaml) are exempt and may be read directly.
- Do not edit any repo file except writing your report to the results path.
- No git commands that mutate state. No commits.
- End with the METRICS block (verbatim keys):

```
METRICS
files_read: <n>  [list]
searches_or_queries: <n>  [each one, verbatim]
tool_calls_total: <n>
started/finished: <ISO timestamps>
blocked_on: <anything the track rules prevented, or "nothing">
```
