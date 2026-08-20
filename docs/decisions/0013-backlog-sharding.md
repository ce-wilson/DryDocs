# ADR 0013 — Shard the backlog: one item per file, roll-ups derived, git stays the claim channel

```yaml
status: ACCEPTED          # the design; execution is Y2 and holds on its own precondition
date: 2026-08-20
authored_by: Y1 session (desktop; decided with the user, model fable)
deciders: [user]          # four choices put and ruled in session 2026-08-20
layer: cross-cutting      # the claim channel both machines and both repos depend on
relates_to:
  - 0009-configuration-substrate.md            # git YAML stays the source of truth; S5 split precedent
  - docs/restructure/backlog.yaml              # the monolith this record retires (21,353 lines, 466 items)
  - drydocs_core/yaml_fragments.py             # S5's reader — its duplicate-key loader is reused
  - PORT-MANIFEST.yaml                         # the backlog.yaml per-entry row, rewritten by Y2
  - tests/unit/test_backlog.py                 # the guards, two of which invert
  - .claude/skills/groom-backlog/              # the writer that must re-point
executed_by: Y2           # nothing in this record moves a file
precondition_for_Y2: the in-flight port's PORT-REPORT is reviewed first (carried from the 2026-08-04 groom)
```

## Why this is an ADR and not a refactor

`docs/restructure/backlog.yaml` is the **only claim channel** between two machines
and, through the port, two repositories. Every session on either machine appends
to it, and every claim and close edits the same stored roll-up block at its foot.
The exhibit that shaped this item: on the afternoon of **2026-08-04 three rebases
conflicted in the same file** (X1-claim/V8, X2-close/V2, X3-close/V3), and every
one of the three was in the stored `summary` / `next_ready` block — a block that is
a pure function of the items above it. Disjoint work was colliding on a derived
number. Earlier, the 2026-07-09 merges left committed conflict markers and a
duplicate-id pair in the file (repaired at `ffc29b6f`); the phase-1 guard against
duplicate mapping keys (`c5b689e`) shipped from that defect.

Changing the file's shape changes how claims race, how ports reconcile, and what
the graph loads (Y3/Y4). That is a design decision with alternatives, and it is
recorded here so Y2 builds to a ruling rather than to taste.

---

## Clause 1 — File layout: one standalone mapping per item, flat

**Decided.** `docs/restructure/backlog/items/<id>.yaml`, one file per item, each
file a **standalone YAML mapping** whose top-level keys are the item's fields
(`id`, `epic`, `title`, `type`, `module`, `phase`, `agent`, `model`, `priority`,
`status`, `depends_on`, `inputs`, `acceptance`, `notes`, and the optional
`progress`, `output`, `closed`, `close_note`). The filename is the `id`; the
file's `id` field must equal it (guard).

**Standalone over S5 textual fragments.** S5's reader (`yaml_fragments.py`)
concatenates fragments textually and would carry a `  - id:` list element per
file with zero new mechanism. Rejected for this file: an item file that does not
parse on its own is useless to the two consumers this shard exists for — an agent
reading one item, and Y4's loader parsing one item into one node. The cost is a
small assembler (glob, parse each file, collect) that **reuses S5's
`_DuplicateKeySafeLoader`**, so the phase-1 duplicate-key guard survives the
split unchanged.

**Flat over per-epic directories, ruled on graph grounds.** `epic:` is a field
on every item, and Y4 mints `(:BacklogItem)-[:IN_EPIC]->(:Epic)` from that field;
a traversal never consults a path. A per-epic directory would put the same fact
in two places (path and field) that can disagree — the drift S5's fragments
already needed a consistency check for — and would turn a re-home into a rename,
which also moves whatever `prov:wasDerivedFrom` points at. Flat keeps one source
per fact: the path carries identity, the file carries everything else. The one
thing a per-epic directory buys, a clustered `git diff --stat`, is a query
(`epic:` on the board filter; `IN_EPIC` once Y4 lands).

**The non-item material** leaves the monolith for named files in the same
directory:

| Today (monolith key) | After Y2 | Consumer |
|---|---|---|
| `schema: drydocs.backlog.v2` | `backlog/plan.yaml` carries `schema: drydocs.backlog.v3` | `test_schema_is_v2` → `_is_v3` |
| `plan.phases` | `backlog/plan.yaml` | `test_plan_phases_shape`, board phase cards |
| `modules` (the census) | `backlog/modules.yaml` | `test_modules_registry`, `test_runbook_coverage.py` |
| `updated:` (hand-set date) | **dropped** — git holds the date of the last change | board/roadmap subtitles read it from `git log -1` or omit it |
| 57 epic header comment blocks | `backlog/epics/<epic>.yaml` — see Clause 2 | board epic cards, Y4 `:Epic` |
| `summary` + `next_ready` | **gone** — see Clause 3 | renderer output only |

**Order is a reader rule, not a storage fact.** The monolith's order (epic, then
groom sequence) is what the board renders within a column. A flat directory sorts
lexically (`C10` before `C2`), so the assembler sorts by epic order then by
**natural id** (`C2` < `C10`), and the board keeps its present look without the
filesystem being load-bearing.

## Clause 2 — Epic headers become data

**Decided.** Each epic gets `backlog/epics/<epic>.yaml` with `id`, `letter`,
`title`, and a `groom_log:` list of `{date, note}` entries carrying the header
prose that today sits in YAML comments nothing can render. The acceptance's
requirement — *headers MUST survive as something a renderer can show* — is met by
making them data: the board gains an epic card, and Y4's `:Epic` node gains
properties instead of being a bare id.

Migration rule for the splitter: a header block attaches to the epic of the
**first item that follows it**; blocks that name several epics (the cross-epic
groom runs) are attached to that epic and the splitter prints the
block → epic mapping for review before the tombstone. The alternative —
lifting the comments verbatim into a per-epic `_header.yaml` — was rejected as
lossless but invisible, which is the problem being solved.

## Clause 3 — Roll-ups are derived; nothing agents append to stores a count

**Decided, as the acceptance required.** The `summary` block and `next_ready` list
are **deleted from storage** and become `render_board.py` output (counts on the
board, `next_ready` as a board section and, once Y4 lands, a one-hop query). The
two guards that today check a stored block against the items
(`test_summary_rollup_matches_items`, `test_next_ready_is_computed`) invert to
assert that **no stored roll-up exists** — a recomputed-from-items rule is not
needed when there is nothing to recompute. `groom-backlog/validate.py` drops its
summary section the same way.

**What is lost, stated plainly.** The `next_ready` line carries a comment chain
("C34 leaves next_ready by being CLAIMED, not by closing; nothing depends on it")
that a derived list cannot hold. That narrative moves to where it already lives
in parallel — the claim and close **commit messages** — and to `IDEAS.md` when it
is a groom note. The step-134 rule ("recompute from items, never merge
textually") is retired with the block it governed.

## Clause 4 — Claim mechanics and the residual race

**Decided.** A claim is a **one-file, one-key edit**: `status: todo` →
`in_progress` in `backlog/items/<id>.yaml`, committed and pushed before work, as
CLAUDE.md §0 already requires. No roll-up edit accompanies it.

**What this removes:** two sessions claiming or closing **different** items no
longer touch a shared line, so the 2026-08-04 class of conflict cannot occur.

**What remains, and how it resolves:** two sessions claiming the **same** item
still race. That race is now a conflict on one small file that git reports as
such, and the resolution rule **within one repo** (two machines, one plan) is —
**a status never regresses** (`done` → `in_progress`/`todo` is forbidden); when
both sides advanced, keep the version that is further along and fold the other's
notes in.

**Across repos the rule is different, and this is the F4 ruling (2026-08-20,
port review `7c18ff4b`): status is per-repo; a port never writes it.** The same
id names the same *work* with two independent *completions* — the company runs
its own gates, its own loads, its own suite, and a port carries code and prose,
never the act of accepting them. At a port the company's `status` stands
untouched and the producer's status and date fold into `notes` as information
("producer: done 2026-08-11"). `type` cannot carry this distinction (it is only
task / chore / bug / requirement), so the rule is unconditional rather than
keyed. This is what the 2026-08-11 union already did for 12 shared ids ("done
never crosses"); the alternative — keep the further-along across repos — would
mark the company `done` on gates it has not signed. The 2026-07-28 C19 double-build was a *visibility*
failure (a local-only claim), which the push-before-work rule addresses; this
clause does not claim to prevent it.

## Clause 5 — Migration: splitter, proof, tombstone

**Decided, on the S5 pattern.** Y2 ships `scripts/shard_backlog.py`, a one-shot
splitter that writes the tree from the monolith, and a proof that runs **before
the monolith is deleted**: assemble the tree through the new reader and assert
**entry-level deep equality** with the monolith's parse — every item
field-for-field, `plan`, `modules`, and the epic-header attachment printed for
review (the S5 split proved 83 + 38 entries this way at `d84d86bc`). The only
permitted difference is the stored roll-up block, which the proof checks is the
**same value** the renderer now derives.

The monolith is then **tombstoned**, not merely deleted: `backlog.yaml` is
replaced by a short file that names this ADR and the new directory, and a guard
fails if the tombstone ever grows an `items:` key again — the same tombstone
pattern the S5 monoliths got.

**Y2 re-points, in the same commit** (the census that makes Y2 one unit): the
readers `drydocs/plan_board.py`, `drydocs/plan_roadmap.py`, `scripts/render_gates.py`,
`scripts/build_schema_matrix.py`; the guards `tests/unit/test_backlog.py`,
`test_runbook_coverage.py` (modules census), `test_port_reconcile_guards.py`
(the before/after snapshot now copies the directory); the writers
`.claude/skills/groom-backlog/` (`SKILL.md` + `validate.py`) and
`.claude/agents/backlog-groomer.md`; and the desktop-local claim/close helpers
under `internal-local/` (`_claim_ui.py`, `_close_ui.py`, `_read_accept.py`,
`_sme_pending.py` — machine-local, re-pointed on this machine, never ported).
Prose that names `backlog.yaml` (CLAUDE.md §0, `git-readme.md`, the skills) is
repointed in the same commit; the ~80 historical mentions in reviews, gate
prompts, and the port-prompt archive stay as history.

## Clause 6 — Port sequencing: the splitter ports as code; each side splits its own monolith

**Decided.** The company does **not** receive the producer's sharded tree. Both
repositories hold the same ids with different statuses and company-only items
(the reason the `backlog.yaml` row is per-entry today), so 466 clean-adds would
recreate the overlapping-id hazard at 466 sites. Instead, at the **first port
whose range contains the Y2 commit**, the apply runs in this order:

1. **Per-entry union** the monolith exactly as today's row says (union the items,
   never regress a status, keep the further-along copy, fold notes).
2. **Run the ported `shard_backlog.py` on the unioned monolith.** Company-only
   items and company-ahead statuses survive by construction — they were in the
   input.
3. **Run the proof** against that union; it must pass on the company side as it
   did on the producer side.
4. **Tombstone** the company monolith.

The PORT-MANIFEST row `docs/restructure/backlog.yaml` is rewritten by Y2 to
describe exactly that one-time sequence, and a new row
`docs/restructure/backlog/items/*.yaml` takes over for every port after it with
disposition **per-entry where the entry is the file**: disjoint ids are ordinary
git adds and modifications; the same id on both sides is one small conflict
resolved by the Clause 4 **cross-repo** rule — the company's `status` stands, the
producer's folds into `notes`. The one-time step 1 union above applies the same
rule. `backlog/epics/*.yaml` is union-append
(`groom_log` is an audit trail; both sides append). `plan.yaml` and
`modules.yaml` keep the monolith's present per-entry semantics.

**A port mid-flight when Y2 lands.** Y2's precondition exists for this case and
holds: the splitter does **not** land while a range containing the monolith is
being applied. If it happens anyway, the rule is simple — the company finishes
the in-flight range on the monolith, and the split is the **first step of the
next range**, never spliced into a range already in progress. The proof is what
makes that safe: whatever union the in-flight port produced is the splitter's
input, and deep equality is checked against it.

---

## Consequences

- The claim channel stops colliding on derived numbers. Same-item claims remain a
  conflict git can see, resolved by a rule already written down.
- Y3 registers `:BacklogItem` and `DEPENDS_ON` (and now `:Epic` / `IN_EPIC`) via
  the gate as **projection** vocabulary: the graph is a read model, **git stays
  the claim channel** — a loader never writes a status back to a file.
- Y4's loader parses one file into one node; the Clause 1 form is chosen for
  that consumer.
- The board loses a hand-set `updated:` date and gains an epic card and a derived
  `next_ready` section.
- One-time port cost: the next port after Y2 has a four-step backlog sequence
  instead of a per-entry union; every port after it is cheaper than today.

## Rejected alternatives worth not re-litigating

1. **S5 textual fragments for items** — zero new code, but no item parses alone
   and filename order becomes load-bearing; the shard's consumers read one item.
2. **Per-epic directories** — the path duplicates the `epic:` field; the graph
   makes the clustered-diff advantage a query.
3. **Comments in a per-epic `_header.yaml`** — lossless, invisible; fails the
   acceptance clause.
4. **Port the sharded tree** — recreates the overlapping-id hazard at file grain.
5. **Keep a stored `summary` and bump it on every claim** — the exhibit.
