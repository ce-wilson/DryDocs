# The sharded backlog (ADR 0013)

One item per file under `items/<id>.yaml`; epics under `epics/`; `plan.yaml` and `modules.yaml` carry what the monolith held outside `items:`. Read it through `drydocs_core.backlog_store.load_backlog_document()`. Roll-ups (counts, `next_ready`) are derived by `scripts/render_board.py` and never stored.

**Claiming work:** edit `status:` in the one item file, commit, push — before starting. Two machines claiming different items no longer touch a shared line; the same item is one small git conflict resolved by *status never regresses*. Across repos (a port) status is per-repo — see ADR 0013 Clause 4.

Sharded from `backlog.yaml` on 2026-08-20 by `scripts/shard_backlog.py` (entry-level deep-equality proof run before the tombstone).
