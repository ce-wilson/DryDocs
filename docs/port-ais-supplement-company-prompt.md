# Hand-off pack — AIS platform supplement: the back-flow to REFUSE, and the fix to make

**Direction:** producer → company, ADVISORY (no payload). Nothing here is a port. This
pack exists because a company session, while re-publishing the runbook, found a stale
success message, fixed it, and then proposed a **back-flow to the producer that has no
target**. Producer-side verification (2026-07-28) is below, plus the producer precedent
for the *real* defect that same session surfaced in its own note #2.

**How to use it:** PASTE into the executing company session. Never commit it company-side
(`docs/port-*.md` is `never-port` in the manifest). Retire it from the producer tree once
the company confirms the actions are landed or declined.

---

```text
You are working COMPANY-SIDE on <company-org>/DryDocs. This is NOT a port — there is
no producer payload to apply. It is four actions on company-local code, three of which
correct a conclusion a previous company session reached.

CONTEXT: a company session re-published the Control-M Initial-Load Runbook to v19 and,
checking where "AIS platform supplement applied." came from, found it in cli.py at the
`apply-platforms-supplement` command (runbook step 7b). It correctly identified the line
as stale — AIS is T12-SUPERSEDED (2026-07-21) and the command is a no-op on a fresh
graph — and replaced it with an accurate SUPERSEDED message. It then raised two things:
a back-flow candidate, and a note that the supplement still creates constraints.

--------------------------------------------------------------------------------
ACTION 1 — REFUSE the back-flow. It has no target. (Do this first; it stops work.)
--------------------------------------------------------------------------------

The session recorded: "It's a company-local wording fix (producer's copy still says
'applied'), so it's also a back-flow candidate."

That premise is FALSE, and not by a wording margin — the producer has no such code at
all. Verified against the producer working tree at 2026-07-28:

  | Searched for                          | Producer result                       |
  |---------------------------------------|---------------------------------------|
  | "AIS platform supplement applied."    | no matches, repo-wide                 |
  | `apply-platforms-supplement` command  | does not exist                        |
  | `platforms_supplement.cypher`         | does not exist                        |
  | `ais_tool_id` / `ais_capability`      | no constraints, no references in code |
  | `:AisCapability` / `:AisTool`         | PROSE ONLY — gate-log, port-prompt,   |
  |                                       | backlog, gate-prompt spec             |

The AIS class layer is a COMPANY-LOCAL artifact of your 2026-06-29 AIS gate. The producer
reached the same destination by a different route: C12 (2026-07-21) retired
`:SchedulerKind` directly into the software-registry model, with no Ais* layer ever
existing in between. That asymmetry is exactly what T12 ruled on — SUPERSEDE, not
reconcile.

DO: drop the back-flow candidate. Do not open a producer issue, do not wait on a producer
commit, do not add it to a tracker as pending-producer. Record the refusal WITH the reason
("producer has no AIS layer; C12 took the direct route") so the next session does not
re-derive it from the same false premise.

WHY THIS MATTERS BEYOND THIS ONE LINE: "the producer's copy still says X" is a claim about
a repo the session cannot see. Divergence in a company-local layer reads identically to
producer staleness from inside the company tree. Any future back-flow candidate should
name the producer file and line it believes is wrong — a candidate that cannot cite one
is a guess.

--------------------------------------------------------------------------------
ACTION 2 — Keep the message fix, but know it patches a symptom the producer fixed
           structurally. Decide whether to adopt the structure.
--------------------------------------------------------------------------------

The corrected message is right and worth keeping. But a hand-maintained success line will
go stale again the next time a supplement is retired — that is precisely how this one got
here. The producer removed the failure mode at G29 rather than re-wording it:

  * `drydocs_core/schema/supplements.py` — the apply chain is DATA (a `SUPPLEMENTS`
    tuple), not one hand-written verb per file. Order is declared once; the legacy
    per-supplement verbs survive as delegating aliases.
  * `declared_terms(path)` PARSES the `:OntologyTerm` IRIs a .cypher actually MERGEs,
    with comments stripped by the shared comment/string-aware scanner first. So a
    commented-out MERGE — the normal way to retire a term, and the AIS pattern exactly —
    stops being a term the graph is required to hold.
  * `drydocs/cli.py::_apply_supplement_chain` applies each file, then asserts every
    declared IRI is PRESENT in the graph, and exits 1 naming the absent ones if not.
    The success line is therefore not a claim: it reads "N supplement(s) applied and
    verified." A comment-only supplement FAILS the command instead of printing "applied."

That is the structural version of the fix you just made by hand. Two honest options:

  (a) ADOPT — fold `apply-platforms-supplement` into a supplement-registry entry so it
      inherits the verification, or delete the verb outright if the layer is retired and
      the runbook no longer calls it. Note step 7b is already documented RETIRED in your
      runbook, so a deleted verb may cost you nothing.
  (b) KEEP AS-IS — a superseded verb kept for audit, with an accurate message. Legitimate.
      If you choose this, say so in the code comment, so the next reader knows the absence
      of verification is a decision and not an oversight.

Either way, the producer is NOT the source of a fix here — this is company-local code with
no producer counterpart. Do not expect a port to bring it.

--------------------------------------------------------------------------------
ACTION 3 — Your own note #2 is the REAL defect. The producer has already ruled on it.
--------------------------------------------------------------------------------

The session observed: the supplement file still creates the `ais_tool_id` /
`ais_capability` constraints (`CREATE CONSTRAINT ... IF NOT EXISTS`) even though the seed
rows are commented out — "so it's 'no-op' on data, not on schema" — and asked whether you
want a true no-op.

The producer hit the identical shape and SWEPT it. The precedent, verbatim:

  * `:SchedulerKind` seeds were commented out at C12 (2026-07-21), and the
    `scheduler_kind` constraint was initially KEPT with the rationale "for old graphs."
  * On 2026-07-23 the constraint and the supplement's double-check MERGE were REMOVED.
    Rationale recorded at `tests/unit/test_schema.py`: "pre-C13 graphs are wiped and
    rebuilt from bootstrap, the kept-for-old-graphs rationale no longer applies."
    `EXPECTED_CONSTRAINTS` went 48 -> 47 in the same commit, with the arithmetic and the
    reason written into the comment block above the constant.
  * Producer supplements today carry ZERO `CREATE CONSTRAINT` — verified 2026-07-28
    across all five (`ontology`, `seal`, `catalog`, `registry`, `sosa`).

So the answer to "want it to be a true no-op?" is YES, on a decided precedent: **if your
graphs are rebuilt from bootstrap rather than migrated in place, the kept-for-old-graphs
rationale is void and the constraints should go.** Test that premise before acting — if
any company environment IS carried forward in place rather than rebuilt, the rationale
still holds there and the constraints stay until it is retired. That is a question about
your environments, which the producer cannot answer.

IF YOU REMOVE THEM, the bookkeeping is the load-bearing part:
  * Decrement your own `EXPECTED_CONSTRAINTS` by the number of constraints you actually
    remove. COMPUTE IT FROM YOUR TREE — do not copy a producer number; your ledger has
    carried a documented divergence from the producer's since the 6fd3270 review, and the
    producer number moves independently (it is 51 producer-side at 2026-07-28 after the
    G33 code-graph pair, and that has nothing to do with your AIS pair).
  * Write the arithmetic AND the rationale into the comment block above the constant, the
    way the scheduler_kind sweep did. A bare number tells the next reader nothing about
    whether a future mismatch is a regression or an intended retirement.
  * Verify against a FRESHLY BOOTSTRAPPED graph, by constraint NAME and not by count —
    see the D8 guard in port-prompt step 48c if you have not yet ported it. Counts hid a
    silent DDL no-op on the producer side for two months.

--------------------------------------------------------------------------------
ACTION 4 — The uncommitted cli.py edit on `main` is a port hazard. Land it before the
           next port branch is cut.
--------------------------------------------------------------------------------

The session ended with the cli.py wording fix UNCOMMITTED on company `main`, asking
whether to commit it. Commit it (or stash it deliberately) before anything else touches
the repo: port guardrail 3 cuts `drydocs-port-<date>` from `main` and expects a clean
checkout, and an uncommitted company-local edit sitting in the tree during a
tree-reconcile is how a local fix gets attributed to the producer — or silently reverted
by a file-level checkout.

Suggested framing for the commit message, so the record survives without this pack:
  * it is a COMPANY-LOCAL fix to company-local code (no producer counterpart);
  * the message was stale because the AIS layer was T12-superseded on 2026-07-21;
  * the back-flow candidate raised alongside it was REFUSED — see Action 1's evidence.

--------------------------------------------------------------------------------
ACCEPTANCE
--------------------------------------------------------------------------------
1. The back-flow candidate is closed as REFUSED with the reason recorded, not left
   pending against the producer.
2. The apply-platforms-supplement verb is either folded into a verified chain, deleted,
   or explicitly kept-as-is with that decision written in the code.
3. The ais_tool_id / ais_capability constraints are either removed (with
   EXPECTED_CONSTRAINTS decremented, rationale written, and a fresh-bootstrap
   NAME-level verification) or explicitly retained against a named in-place environment.
4. The working tree is clean before the next port branch is cut.
5. Full company unit suite green.

SEND BACK to the producer: only the answer to "are any company Neo4j environments carried
forward in place rather than rebuilt from bootstrap?" — it is the one fact in this pack the
producer had to assume, and it decides whether the sweep precedent transfers cleanly.
Nothing else here needs to return.
```

---

## Producer-side record (not part of the paste)

Captured while verifying the above, and fixed producer-side in the same session:

Two live files still asserted `scheduler_kind`'s "constraint kept for old graphs" — true at
C12 (2026-07-21), false after the 2026-07-23 sweep. Same species as the AIS message: the
retirement landed, the assertions about it did not all move.

- `config/taxonomy-ontology-map.yaml` (`requires-scheduler` entry, `to_node`)
- `drydocs_core/ontology/relationship_vocabulary.yaml` (`seal_requires_scheduler`, `to_node`)

`drydocs_core/schema/ontology.cypher` was correct already — so this was two stragglers from
one sweep, not a systemic gap. Both now state the removal and its date.

**Not fixed, flagged only:** `drydocs_core/schema/constraints.cypher` labels
`role_name` / `role_id` / `membership_id` as "deprecated by K4; kept for old graphs", but
all three are actively written today — the catalog supplement seeds the canonical `:Role`
rows and `drydocs/loaders/cypher/pat_team_roles.cypher` MERGEs `:Membership`. K4 deprecated
the pattern *in the SEAL loaders* specifically, so the comment is most likely under-scoped
rather than wrong. It is a K4-scope question, not a sweep straggler, and is left for
whoever owns the K4 follow-up.
