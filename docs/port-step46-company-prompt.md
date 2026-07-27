# Step 46 — company-side port prompt (producer → company)

**Read this alongside `docs/port-prompt.md` step 46, not instead of it.** This file exists
because a company-side plan for this port was drafted, reviewed producer-side on
2026-07-27, and **confirmed sound with three corrections**. Those corrections are folded
into `docs/port-prompt.md` step 46 and into `PORT-MANIFEST.yaml`; this file states them in
one place so the executing session does not have to re-derive them.

**Lifecycle:** this is producer-side hand-off material, same class as the retired
`docs/port-T12-*.md` packs — **paste it into the executing session; do not clean-add it to
the company tree.** Retire it once the port lands and the PORT-REPORT is written.

Classification: **Internal-Public** — mechanism only. No SIDs, servers, org names, real
SEALIDs, rosters or file values appear here.

---

## 0. What was confirmed (do not re-litigate these)

The reviewed plan's structure was verified against the producer tree and is correct:

| Plan element | Verified |
|---|---|
| `46a` boundary hardening before any other sub-stream | ✔ matches the ledger's APPLY-FIRST marking |
| Both Tier B holds discharged (T12 SUPERSEDE) | ✔ steps 43 and 45b, discharged 2026-07-27 |
| Mechanism = tree-reconcile, not cherry-pick | ✔ correct — 58 commits, derived-dominated |
| `PORT-MANIFEST.yaml` first-matching glob wins | ✔ stated in the `config/**` row's note |
| `gate-log.md` union-append | ✔ explicit manifest row |
| `catalog.py` shadow unimported | ✔ true producer-side too; only the C18 guard names the path |
| `EXPECTED_CONSTRAINTS` stays company-based | ✔ the manifest row already ruled exactly this |

Phase ordering (0 setup → 1 boundary → 2 apply-by-disposition → 3 check-before-apply →
4 regenerate surfaces → 5 gate unification → 6 acceptance → 7 report) is right: boundary
before content, content before regenerated surfaces, surfaces before acceptance.

---

## 1. CORRECTION — the head is not `0ce7333`

The ledger originally declared the range end as `0ce7333`. **The true end is `78ba7fd`**,
and the tail is not inert:

- `5bb606f` (the step-46 ledger commit) **also repointed `config/taxonomy/platforms.yaml`**
  — a `canonical-producer` path carrying the T12 provenance pointer. Pinning to `0ce7333`
  silently drops the T12 follow-through that step 43 spends its length describing.

Everything else in the tail is safe to lose: `IDEAS.md` (union-append), one struck row in
`docs/reviews/doc-inventory-2026-07-22.md`, `docs/port-prompt.md` itself (producer
instruction doc, never ported), the two deleted `docs/port-T12-*.md` (step 43 says do NOT
re-add them), and one snapshot (never-port).

**Do this:** take whatever `ce-wilson/main` is at port-run time and record that exact hash
in the PORT-REPORT. **Do not pin a hash quoted from any document** — this one included.
It already went stale once inside this review: `378f4ba` landed after `78ba7fd` and carries
manifest rows you need (§3 below). `0ce7333` in particular is wrong.

---

## 2. CORRECTION — S3 is narrower than "Tier B candidate" implied

The plan spent a decision on whether to defer the `seal_id` → `app_id` key migration.
**There is no key migration in this range to defer.** A file-level check of the S3 series
found it touches **zero loader files and zero `.cypher` files**. `fc15191` is:

```
config/gate-log.md · config/taxonomy-ontology-map.yaml ·
config/taxonomy/business-application.yaml · docs/adr/0010-*.md ·
docs/plan/board.html · docs/restructure/backlog.yaml ·
web/src/generated/enforcement-matrix.json · web/src/generated/gates.json
```

The commit says so outright: *"Nothing is written to the graph at the gate itself — S3 is
now build work."* `seal_id` remains live in ten producer cypher files.

**So:** sub-stream (b) ports **the ruling and the build backlog**. Your live graph and your
app-code link path are untouched by applying it. Apply it as an ordinary
`canonical-producer` sub-stream — the plan's "Option A (DEFER)" is not a choice between
alternatives, it is simply what the range contains.

**The Tier B risk is real but belongs to the BUILD, not this port.** Carry it forward:

- The eventual flip touches the initial-load runbook's app-code link step, which parses
  `seal_id` out of each Control-M app code and MATCHes on it.
- Two traps bite on the rename itself: **constraint NAMES do not follow property renames**,
  and **Neo4j uniqueness constraints IGNORE nulls** — a half-renamed population passes its
  constraint silently.
- §C of the gate already rules the path: **rebuild, not migrate** — dual-write plus a
  graph-test through phases 1–3, because a partial cutover *silently doubles* the canonical
  node rather than failing.

Re-run T1 when the build happens, not now.

---

## 3. CORRECTION — the snapshot exclusion was never actually in the manifest

The plan listed "all depgraph snapshots" under Excluded. That call is right, but until
2026-07-27 **no manifest row said so** — and the manifest's `default:` is
`clean-add when absent on consumer`. So the manifest was, on its face, instructing you to
**port them**. Every prior port excluded them by planner judgment and none of that judgment
was written down, which is why your session had to re-derive it.

Now fixed producer-side, as two ordered rows (first match wins):

```yaml
- path: "knowledge/depgraph-snapshots/*.json"   # never-port  — the outputs
- path: "knowledge/depgraph-snapshots/**"       # canonical-producer — the tooling
```

The `*.json` row also catches `tree-original.json` / `tree-this-version.json`, which embed a
producer-local absolute path. `README.md`, `snapshot.ps1` and `viewer.html` **do** port.

**The same gap turned out to cover the port-control docs themselves.** `docs/port-prompt.md`,
its step archive, and the hand-off packs (including this file) also had no row and also fell
to `clean-add` — which is exactly why step 43 carried a prose *"do NOT re-add the T12 session
materials"* instruction. That workaround is now a manifest row: `docs/port-*.md` →
**never-port**. Your own `PORT-REPORT-<date>.md` is a company artifact and is not producer
content either.

**Do this:** take the manifest change with the rest of the port (`PORT-MANIFEST.yaml` is
`canonical-producer`), then re-check your exclusion list against the rows rather than against
the plan. If your tree already contains any `docs/port-*.md` from an earlier port, that is
the old gap showing — remove them; they are producer control docs, not shared content.

---

## 4. One more thing to read off YOUR files, not this document

`tests/unit/test_schema.py` — `EXPECTED_CONSTRAINTS`.

- Producer is at **49** (was 47 at the step-45 head; +2 from the P3 hosts loader, 46e).
- The plan quoted **52** for the company side. That number was not verifiable
  producer-side and should be read off your live file.
- The manifest row's standing rule: **keep the consumer count, take the producer
  drift-guard logic**, and raise the consumer number only for genuinely new active edges
  that ship their own supplement block.
- The row's own historical note ("45 ⊇ 40 at the 2026-07-20 bundle port") was stale and has
  been refreshed. Its warning stands and is the point: *counts drift every port — trust the
  live test files over any note.*

---

## 5. Sub-stream warnings that still stand unchanged

From the ledger, unmodified by this review — restated because they are the ones that bite:

- **(a) boundary hardening is apply-first and not optional.** The new guard matches on the
  **value shape**, not the field name, because the earlier field-name sweep is exactly what
  missed real SEALIDs hiding inside prose and folder-name strings. Expect it to find things
  in your tree on arrival; that is the guard working, not a port failure.
- **(c) G29 touches your initial-load runbook.** The individual `apply-*-supplement` verbs
  survive as aliases so the runbook keeps working unchanged, but the single verified chain
  is now canonical and the runbook should be revised to it — your doc, your rev.
- **(d) the loader refusals guard a failure your runbook currently documents as accepted
  operator discipline** ("out-of-order rows silently drop on the MATCH"). Two more loaders
  (`doc_traceability`, `doc_feedback`) carry the same unguarded idiom producer-side and were
  NOT fixed — check yours.
- **(e) P3 widens `ingest-controlm`** beyond what your runbook's step 9 describes.
- **(h) the shadow delete is a no-op only if nothing imports it.** True producer-side. Your
  session reported it true company-side as well — good, but let the C18 guard confirm it
  rather than the plan.

---

## 6. Acceptance

Unchanged from the ledger:

- **Track 1** (portable): producer reference 90 passed / 3 skipped. Your baseline is above
  this — compare against your own prior report, not the producer floor.
- **Full `pytest tests/unit/`**: zero failures is the contract. Producer reference at
  `78ba7fd` is **982 passed / 6 skipped**. Company reference at the last port was
  1174 / 21 / 0.
- CI guards green, including `test_schema.py` per §4 above.
- Regenerate your own derived surfaces after applying — the board, the design-doc renders,
  `gates.json`, `enforcement-matrix.json` — and re-apply your company-only SURFACES rows.
  G26 flips one row from `unguarded` to guarded, so the matrix WILL differ.

Write the PORT-REPORT with the exact producer hash you took, and send back anything where
§G4-RIDER or step 46 mis-describes your behaviour — divergences are the useful output.
