# Company-side prompt — close out `port/20260908`: what changes before the `--no-ff` merge

> Producer-drafted 2026-09-10 for the company-side assistant, at producer `main` `03e903eb`,
> venue MSI (desktop). Paste or read whole. **This answers every open question in your
> `PORT-REPORT-port-base-20260908.md` and carries the SME's rulings on the three you escalated.**
>
> **Verdict on the roll: it stands, and it is ready to close.** Nothing here reopens the apply
> or reverses a block. One item is a real tree change (section 2); the rest are corrections to
> the record so the merged report is true.
>
> **Guardrails stand: nothing here pushes to the producer remote, and no reply, sha or figure is
> wanted back through git.** Everything below is recorded in YOUR ledger and stays there.

---

## Before the merge — the whole list

Five things. Only the first is code; the rest make the permanent record match what was decided.

| # | Change | Why it is pre-merge |
|---|---|---|
| 1 | Remove the AIS typo labels from the schema tree (section 2) | it is a tree change, and it turns a red guard green — D8 closes instead of deferring |
| 2 | Delete or restate finding 12 (section 3) | as written it instructs a future session to break a correct file |
| 3 | Move the SQL out of "Blocking" into a recorded permanent divergence (section 4) | the blocking list must be empty at merge |
| 4 | Restate D7 and D9 as SME-ruled holds with a named re-arm (section 5) | they are ruled now, not undecided |
| 5 | Flip the status header and re-measure (section 6) | the report says IN PROGRESS |

Everything else in the report is correct and stands: D1, D2, D3, D4, D5 and D6 are all correctly
held, F1 is correctly named, and the seven "findings recorded" are sound apart from number 12.

---

## 1. The three SME rulings, verbatim in substance

- **D8 — the AIS typo labels.** *"On our side there should not be a test for the typo. It should
  no longer be active or referenced. The Neo4j constraints have been dropped; it is a fresh
  database."*
- **D7 and D9.** *"Hold for a SME gate."*
- **The recursive SQL.** *"The recursive query has been tuned internally. I did not change the
  producer side."*

## 2. D8 — remove the labels; do not narrow the guard

**This supersedes what both sides proposed.** Your report argued the labels must stay because the
retirement block cannot run without naming them, and the producer's earlier reading agreed and
suggested narrowing the guard to constraint names. Both of us were preserving a retirement block
for a database that no longer has anything to retire.

On the SME's statement that **the constraints are dropped and the database is fresh**, the
`MATCH (c:AisCapability) ... SET c.deprecated = true` block matches zero nodes and can never
match any. T12's "deprecate in place, do not drop" ruling was about retiring a class gracefully
in a LIVE graph that held those nodes. That premise is gone.

**Do this:**

1. Remove `:AisCapability` and `:AisTool` from `drydocs_core/schema/platforms_supplement.cypher`,
   including the retirement block, so the label class is neither active nor referenced.
2. Sweep for any remaining reference in the schema tree and remove those too.
3. `test_constraint_drift.py::test_the_typo_labels_appear_nowhere_in_the_schema_tree` then
   **passes on its own terms**, with no narrowing, no local exemption and no divergence.
4. Rewrite D8 in the report: not a deferral, but applied and closed, recording that the removal
   rests on the fresh-database statement. That dependency belongs in the record so a future
   reader knows what the removal assumed.

**One caution, stated because the removal depends on it.** This is safe only because no
environment still holds nodes carrying those labels. If any graph anywhere does, the retirement
block is the only thing that would have marked them, and it goes away with this change. The SME
has stated the database is fresh; the record should say so in the same breath as the removal.

**Producer-side, owed and not asked back:** the guard is the producer's defect twice over. Its
docstring asserts a fact about your tree that the producer's own
`docs/company-prompts/port-ais-supplement-company-prompt.md` disproves, and it is a raw
`p.read_text()` substring scan in a file that already imports `without_prose` for its other
tests — J66's exact failure mode. It also passes vacuously producer-side, because the labels
never existed there, so it looked green while being wrong. The producer will retire it rather
than narrow it. You do not need to wait for that: after step 1 your tree passes either version.

## 3. Finding 12 is a misread — settle it before the report merges

Your "Findings recorded" section carries:

> *"Taken verbatim despite being wrong: the README names `scripts/writeApiTypes.mjs`; both
> sides ship `scripts/writeApiTypes.ts` ... Owed upstream."*

**Measured against `port-base-20260908`, your own base:**

| checked | result |
|---|---|
| every `.mjs` the producer's `web/README.md` names at that tag | exactly one: `scripts/captureRoutes.mjs` |
| does the producer ship it | yes, `web/scripts/captureRoutes.mjs` |
| how the README names the API-types writer, line 325 | `scripts/writeApiTypes.ts` |
| what the producer ships | `web/scripts/writeApiTypes.ts` |
| what `package.json` line 16 invokes | `node scripts/writeApiTypes.ts` |

All three agree. The `.mjs` spelling was real once — introduced by O70 (`19537a17`), corrected by
WEB16 (`b905b892`) — and both predate your base, so the file you took verbatim was already
correct.

Nothing is owed upstream. Delete the item or restate it as measured and closed. The reason to do
it before the merge is narrow: as written it is a standing instruction for a future session to
"correct" a file that is right, which would make it wrong and cost the conflict the item was
trying to avoid.

## 4. `controlm_dependencies_recursive.sql` — keep yours; it is a permanent divergence

**SME ruling: the query was tuned internally, and the producer side was not changed to match.**

That settles it, and it also corrects the report's framing. Your report reads the two versions as
convergent evolution — *"both sides independently removed the recursion"* — which invited the
question of whose spelling to prefer. They are not convergent. Yours is a deliberate internal
tuning against the real replica; the producer's 98-line version is simply the file as it stands
producer-side, never updated with your work.

So there is nothing to adjudicate. **Keep yours.** The manifest's `canonical-producer` default
was never meant to decide a case where one side holds tuned SQL and live evidence and the other
does not, and only your spelling carries the 68-row MINUS equivalence proof.

Move it out of "Blocking" and record it as a permanent per-entry divergence, citing the
equivalence proof so the next reader does not re-litigate it.

**Producer-side, owed and not asked back:** a per-entry manifest row for
`drydocs/loaders/sql/controlm_dependencies_recursive.sql`. It has none today and falls through to
a default, which is why it presented to you as a conflict at all. That row is the producer's to
write, and until it lands this path will keep showing up on every roll — treat it as expected
rather than as a new question.

## 5. D7 and D9 — SME ruling: hold for a gate

Both are recorded as **held, pending an SME gate**, and that gate is the named re-arm condition.
Neither is a port question and neither blocks this merge.

- **D7 — N15 and `pending-source-correction`.** Held. Your framing was right: your two deferrals
  of 2026-08-20 scope different clauses than N15's §B, so §B is not settled by them — but
  applying it would write behaviour on a gate this venue has not adopted, and that is gate work.
  The two `test_env_refs_migration` failures stay named and accepted.
- **D9 — the relationship-vocabulary fragments.** Held. Four slots under two names is a naming
  reconciliation, not a stale-file problem, and your catalog fragment carries the C26/C27 Sub-LoB
  rulings the producer flattens. CLAUDE.md is explicit that ontology edges are not casual: this
  goes through `docs/RELATIONSHIP_GUIDE.md`, the vocabulary registry and the HITL gate as its own
  piece of work. `test_live_files_validate[relationship-vocabulary]` and the three
  `test_domain_registry` failures stay named behind that seam.

**The CI `web` job — agreed, keep declining it, and there is now a second reason.** Your own
reasoning stands: four network-dependent steps that have never executed in any venue reachable
from you. The producer has since measured something that sharpens it. The bundle ceiling in that
job is a hand-tuned constant, and on the producer's own tree it currently sits **808 bytes**
below the ceiling, already past the margin it was set with, so a single generated-data change
reddens it. That constant describes the producer's bundle, and your `web/` tree has diverged.
Keep the file and the note in place; re-measure against your own bundle if Actions is ever
switched on, before adopting the job rather than after.

## 6. Closing the record

- Flip the header from **IN PROGRESS** to closed, with the final measurement taken the way the
  rest of the report takes it: by test id, not by total.
- The "Blocking" section should be empty at merge. All three items are answered — the SQL in
  section 4, the `gate-log.md` ordering confirmed (**last**, and the live test failing on the
  redacted line is by design, exactly as you have it), and the merge itself below.
- Tear down the anchor worktree at `_dd_anchor` once the close-out comparison is recorded.
- `gate-log.md` goes last, as ruled.

## 7. What stays open after the merge, on purpose

- **The `auth.ts` persona ids.** Still open and correctly named as a publish-boundary question.
  The producer's argument for retiring the SID-shaped ids does not depend on whether they are
  synthetic, and you were right that "ours are synthetic" does not answer it. It is not a merge
  blocker; it belongs with the identifier work, not in front of a port.
- **D1, D2, D3, D4, D5, D6** — all correctly held, unchanged by this prompt. D2 and D5 remain
  discharged together by one CFG2 edition-gate ruling, which is yours to run and is the single
  highest-leverage thing waiting on your side.

## 8. What the next two rolls carry, so you do not debug it

| roll | range | state |
|---|---|---|
| the one you are closing | `port-base-20260905..port-base-20260908` | merging now |
| the eighth | `port-base-20260908..port-base-20260909` | certified producer-side, **175 commits**, waiting |
| the ninth | after `port-base-20260909` | not cut yet, 30 commits so far |

Take the eighth as its own apply after this one merges; do not fold it in. It carries its own
relay.

**The ninth roll will change a file you touch often.** `config/source-descriptors.yaml` gains a
REQUIRED per-side `wired:` block — one entry per registry-home dataset, `true` or
`{value: false, reason: ...}` with a reason of at least forty characters, refused at construction
if missing. `PORT-MANIFEST.yaml`'s `per_side_fields` names `wired`, so your entries are never
overwritten in either direction, and your two standing pins (`cm_hosts` and
`controlm:deftable-xml-export`) retire under it. `require_confirmed()` then refuses unless a
source is both confirmed and wired, and says which of the two failed. Its relay explains the
whole change; nothing on your current branch depends on it.

Also in the ninth roll and not in what you have: the eighteen ADR 0018 re-export shims are
removed, with their own relay, so no import path in your current range breaks; and a new core
module arrives carrying a shared three-outcome result type with a declared probe registry.

---

**Nothing is asked back.** Record what you decide in your own ledger. The producer's record of
this exchange is its own.
