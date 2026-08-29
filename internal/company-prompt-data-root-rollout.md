# DRYDOCS_DATA_ROOT rollout — the mandatory data root, set everywhere before it bites (SME note)

Status: SME direction following the G81 completion port. Record completion and the
invocation inventory in your own upgrade ledger; nothing needs to flow back from this note.

## The principle — do not soften the flip

The mandatory behavior is correct and stays. Exit 2 with a self-documenting message is the
designed replacement for silently writing to the home-directory default — the silent
fallback is how a write landed on source data on 2026-08-11. Never add a default back to
make a job pass; fix the job's environment instead.

## The one fact that shapes everything

The runtime reads the PROCESS ENVIRONMENT only. No first-party code loads `.env` — the
`.env` file is the recorded template plus the agent-server channel (that stack autoloads
it), never the CLI's source. So every plan step below is about getting the variable into
the process environment of each thing that invokes the CLI.

## Rollout, in blast-radius order

1. SCHEDULED INVOCATIONS FIRST. Scheduler contexts do not source shell profiles, so each
   scheduled job, wrapper script, or service definition sets the variable explicitly in
   its own environment. Inventory by searching scheduler definitions and wrappers for
   drydocs invocations; migrate each before its next fire time. An unmigrated job now
   fails loud at exit 2 — intended, but pre-empt it rather than discover it.

2. INTERACTIVE SHELLS: a machine-level user environment variable, so every shell and
   editor window inherits it. Set the same value in `.env` for the agent server and as
   the recorded template value — but never rely on `.env` for the CLI.

3. WORKTREES: ONE shared data root for all worktrees. The data lives out-of-repo by
   design; per-worktree roots would recreate the two-shells-two-trees ambiguity this
   whole mechanism exists to kill. Add a presence check to the worktree helper's seeding
   step so a missing variable fails at worktree CREATION with the same message, not at
   first run. The helper's `.env` copy stays — that is the per-worktree database
   credential channel, a deliberately divergent value; the data root is deliberately
   shared.

4. RECORD THE VALUE where the repo says to: `config/dev-environment.yaml` is the
   canonical per-instance record and never crosses repos.

5. CLEAR THE TWO RED GUARDS this unblocks: move the catalog-export CSV pulls out of the
   repo tree to `DRYDOCS_DATA_ROOT/catalog/` as part of the in-flight lineage work — the
   guard message already names the destination.

6. THE COMPANION FIX RIDES THE NEXT PORT. A producer-side fix (G111) makes env-declared
   zones actually resolve through their variable and widens the declared-equals-resolved
   guard to every zone, helper or not. Until it arrives, treat the landing-zones
   command's per-zone paths as declarations, not verified facts. Flag it in the port
   queue as the completion of the same guarantee.

## Baseline hygiene while you are here

Record the remaining known-red failures as a failing-test LIST, not a count — a list
shrinks visibly as fixes merge and distinguishes "my change broke X" from "X was already
red." Hold the load-map declaration cluster until the next port lands before fixing it
locally: the pending port range touches exactly those surfaces, and a local fix would
collide with the ported one.

Record the inventory, the per-surface settings, and the re-measured baseline in your
upgrade ledger.
