# Hand-off pack — review findings on PORT-REPORT-5f79d145

**Direction:** producer → company, ADVISORY (no payload). Nothing here is a port.
This pack carries three findings from a producer-side review of your
PORT-REPORT-5f79d145, plus one heads-up for the next range. One of the three
can cost you a capability silently, so it is ACTION 1.

**The report itself verified clean.** Nine mechanical claims were checked against
the producer repo and every one was exact: 71 commits, 187 changed paths,
63+81+38+5 = 187, exactly 5 deleted-in-head, exactly 2 in-range snapshot `.json`,
67 manifest rows, tracker highest row T23, and the T11/T12/T20 beliefs all match
the producer tracker verbatim. The findings below are gaps in what the report
*resolves*, not errors in what it claims.

**How to use it:** PASTE the block into the executing company session. Never commit
it company-side (`docs/port-*.md` is `never-port` in the manifest). Retire it from
the producer tree once the company confirms the actions are landed or declined.

---

```text
You are working COMPANY-SIDE on <company-org>/DryDocs. This is NOT a port — there is
no producer payload to apply. It is three actions on company-local state, arising from
a producer-side review of PORT-REPORT-5f79d145.

Context: the port is mechanically sound and the review confirmed every countable claim
in it. What follows are things the report does not RESOLVE, in priority order.

--------------------------------------------------------------------------------
ACTION 1 — Resolve the 5 deleted-in-head. Two of them are held-K8 artifacts.
(Do this first: it is the one finding that can remove a capability silently.)
--------------------------------------------------------------------------------

Your Classification section states "5 deleted-in-head" and the number is correct. The
report then never mentions those deletions again — not in Collisions, not in Governance
holds. That is the gap.

The five paths, and what deleted each one producer-side:

  config/taxonomy-ontology-map.yaml                 <- S5 split into fragment dirs
  drydocs_core/ontology/relationship_vocabulary.yaml <- S5 split into fragment dirs
  knowledge/depgraph-snapshots/drydocs-20260802.json <- never-port snapshot (guardrail 4)
  drydocs/loaders/cypher/seal_attribution.cypher     <- K8  ** HELD TIER-B **
  graph-tests/seal-attribution-coverage.yaml         <- K8  ** HELD TIER-B **

The last two are the problem. K8's own commit subject is "the K2 job-grain writer
retires" — those deletions ARE part of the reshape you held. Both files were verified
PRESENT at the port base 6713c142, so they are real in-range deletions your port had to
decide on, not phantom entries.

If the deletions were applied while the K8 replacement was held, you now have NEITHER
loader: the K2 job-grain writer is gone and the folder-grain writer was never shipped.
Your suite would not necessarily catch it, because seal-attribution-coverage.yaml — the
graph-test that would fail — is itself one of the two deletions.

DO:
  1. Verify on the port branch:
       git -C . cat-file -e HEAD:drydocs/loaders/cypher/seal_attribution.cypher
       git -C . cat-file -e HEAD:graph-tests/seal-attribution-coverage.yaml
     Both MUST resolve. If either does not, restore it from the pre-port baseline
     (`git checkout pre-cewilson-port-20260804 -- <path>`) before merging — the Tier-B
     hold is not applied until the K2 stack is intact.
  2. Confirm the other three deletions WERE applied: the two S5 monoliths must be gone
     (their fragment directories replace them; keeping both would double-load every
     entry), and the 20260802 snapshot is never-port either way.
  3. Amend PORT-REPORT-5f79d145 with one line per deleted path — applied or withheld,
     and why. A hold whose deletions leak through is the failure mode this costs
     nothing to close, and the report is the only place a future session can check it.

RULE WORTH ADOPTING: whenever a governance hold covers a reshape, the hold applies to
that reshape's DELETIONS as well as its additions. Deletions are the half that a green
suite is least likely to notice.

--------------------------------------------------------------------------------
ACTION 2 — Guard the duplicate-key class you just hit by hand.
--------------------------------------------------------------------------------

You found and fixed this: in test_module_boundary.py the producer's `drydocs_docmeta`
COMPONENT_GROUPS entry was clobbered by your `drydocs.docmeta`/`drydocs.scrapers`,
because a duplicated dict key keeps the LAST value silently.

That is the same failure mode as the duplicate `summary:` block that shipped through a
green suite in company 1a3aff20 — the one `test_no_duplicate_mapping_keys` was written
for on the YAML side. Same silence, different language. You fixed the instance; the
class is still unguarded, and a port merge is exactly what reintroduces it.

DO: add a Python-side twin. AST-parse the registry modules (at minimum
tests/unit/test_module_boundary.py; also worth covering any module holding a literal
registry dict) and fail on a duplicate key in any dict literal:

    import ast
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            keys = [k.value for k in node.keys
                    if isinstance(k, ast.Constant) and isinstance(k.value, str)]
            dupes = {k for k in keys if keys.count(k) > 1}
            ...

Prove it RED on a probe before keeping it — a guard nobody has seen fail is a guard
nobody knows works. That lesson is why the YAML twin carries its own regression note.

--------------------------------------------------------------------------------
ACTION 3 — Publish boundary: check your clone for scrubbed producer objects.
--------------------------------------------------------------------------------

On 2026-08-04 the producer rewrote its history to remove an internal identifier that had
reached a publishable-tier file, and force-pushed. Two commits were removed from the
producer line. Your port read authorities at 5f79d145, which is POST-scrub, so the port
itself is clean — but `git fetch` does not prune objects, so if this clone fetched
`cewilson` at ANY point before the force-push, those commits are still in your object
store, reachable by SHA and via the stale remote-tracking ref and reflog.

This is a token-free check — you do not need to know the value:

    git cat-file -e 21449d3^{commit} 2>/dev/null && echo "PRESENT - clean up" || echo absent
    git cat-file -e 63adc2b^{commit} 2>/dev/null && echo "PRESENT - clean up" || echo absent

21449d3 is the commit that carried the value, in a single file
(knowledge/depgraph-snapshots/drydocs-20260804-1338.json). 63adc2b sat downstream of it
and was rewritten only for that reason — its content was byte-identical before and after.

If either resolves:
    git remote prune cewilson
    git reflog expire --expire=now --expire-unreachable=now --all
    git gc --prune=now
then re-run the two checks; both must report absent. `git fsck` should be clean and
`git count-objects -v` should show `count: 0` loose objects.

If both report absent, record that in the PORT-REPORT so the next session does not
re-derive the question. Do NOT paste the identifier into any file, commit message, or
report to answer this — the check above is deliberately built to avoid needing it.

--------------------------------------------------------------------------------
HEADS-UP — what is already waiting in the next range (no action now)
--------------------------------------------------------------------------------

Producer HEAD has moved 9 commits past 5f79d145 since your report was written, so the
next range is 5f79d145..0f87fb2. Two items in it need deliberate handling:

- S4 (console draft substrate, ADR 0009 rule 5). It bumps the mapping-store schema to
  drydocs.mapping-store.v2 and CHANGES the /mappings/*/draft contract: the endpoints now
  write ROWS to a `draft` table and a new promote step emits a unified diff, instead of
  returning a whole replacement file. var/mapping.db is derived so the bump self-heals on
  the next read, but test_mapping_store.py pins the schema string AND EXPECTED_TABLES, and
  any company console caller of draftOverride/draftAppCode moves with it. The K9 app-code
  endpoint was converted alongside the O24 override endpoint — deliberately, so one module
  does not carry two write models. Treat the whole set as one unit or hold it as one unit;
  a half-applied S4 leaves a v2 schema with v1 endpoints.
- The depgraph pin bump (expected_commit 5006567 -> 773fb1e) plus a new instrument-currency
  WARNING in snapshot.ps1. config/dev-environment.yaml and snapshot.ps1 are both
  canonical-company — ADAPT BY HAND, do not take the producer values. For what it is
  worth your side was already on 773fb1e; the producer laptop was the stale one, which is
  what prompted the warning in the first place.

--------------------------------------------------------------------------------
NOT YOURS — being fixed producer-side
--------------------------------------------------------------------------------

The T20 tracker row's body says DISCHARGED 2026-08-03 while its status cell still reads
"pending (producer belief, as of 2026-08-01)". Your report read the row correctly, so
nothing is owed here; it is producer-side staleness of the same kind the T11 row already
documents, and the producer is correcting it. Do not open a company action for it.
```
