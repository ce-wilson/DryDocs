# ADR 0016 — jpmc-reports corpus shape: lexical backbone, or the DataAsset slices it has

```yaml
status: PROPOSED          # never accepted from a groom — the user rules it (the U16 precedent)
date: 2026-08-27
authored_by: Q17 session (laptop, Lane B)
deciders: []              # awaiting the user's ruling; nothing here is pre-approved
layer: drydocs-docmeta
relates_to:
  - 0006-docmeta-component-and-doc-graph.md
  - 0011-single-database-contingency.md    # EXECUTED-BY-CHOICE at G32 — it moved this decision's ground
  - config/doc-source-registry.yaml        # the jpmc-reports row
  - knowledge/upgrade-plans/docmeta-p4-revision-single-db.md
trigger: >
  A real question was asked of this corpus and the SHAPE was the reason it could
  not be answered: the 2026-08-08 business-layer experiment wanted GraphRAG
  retrieval over jpmc-reports and could not have it (Idea-90, groomed as Q17).
```

**No corpus is re-ingested by this record.** It states the choice, what each
branch costs, and what moves in the registry under each — the user rules which
branch runs, and the build is its own groomed item afterward.

## Context

`jpmc-reports` was the FIRST doc ingestion this project ever ran — before the
docmeta component existed. It loaded JPMC annual-report sections as
**`:DataAsset` slices** seeding the effective-dated `BusinessSegment` context,
NOT the lexical `Document → Chunk` backbone every corpus since has used. The
registry row records the consequences honestly: `graph_locator.match: none`
(docs-verify cannot even look for it), `confirmed: false`, and a `source:`
pointing at a one-off ingest script **removed 2026-07-22**. So "re-ingest"
means THROUGH the docmeta component — capture, convert, load, registered and
gated like every other corpus — never by recovering the script from history.

**The consumer that forced the question.** On 2026-08-08 the business-layer
experiment wanted GraphRAG retrieval over this corpus. It could not have it,
and the reason is the shape, not the database: a `:DataAsset` slice has no
chunks, no lexical spine, and nothing to embed — **no vector retrieval is
possible regardless of the database state.** A corpus of public filings that
cannot answer retrieval questions is carrying storage cost without its use.

**The ground moved under the original precondition — recorded, not assumed
away.** When Q17 was groomed (2026-08-09), the corpus's home was `ddcontext`,
which was probed EMPTY on the desktop (`neo4jtest`, 2026-08-08), and any
re-ingest gated on the provisioning ruling Idea-49 is parked on. **That
precondition is OVERTAKEN**: gate `document-content-topology` (G32, signed
2026-08-18) executed ADR 0011's fold by choice, and doc corpora now target
`drydocs` — the row's `target_db` already says so. Under the current topology a
re-ingest gates on the P4 single-db load path
(`docmeta-p4-revision-single-db.md`), not on provisioning a database that no
longer hosts doc content.

**The editions.** The row names two local-only 2024 PDFs (annual report +
MD&A 10-K; never committed — the root `/*.pdf` gitignore precedent). Newer
2025/2026 editions sit at the repo root on the DESKTOP (machine-local,
gitignored; not present on this laptop's checkout — recorded from the item, not
verified here). Whether they ride a re-ingest is part of this ruling.

## Option A — reshape onto the lexical Document → Chunk backbone (RECOMMENDED)

Re-capture and re-ingest through docmeta onto the same backbone every other
corpus uses (the Q13 loader family: capture-scoped `doc_id`, trust and
`doc_version` on every grain).

- **What it buys.** The only branch under which the 2026-08-08 question — and
  every retrieval question after it — becomes answerable. GraphRAG retrieval,
  the Q15 navigation specs' family, and docs-verify reconciliation all assume
  this shape.
- **Registry row.** `graph_locator` becomes `{match: corpus_id, value:
  jpmc-reports}` (the Q13 idiom, so docs-verify can finally look for it);
  `confirmed` STAYS `false` until a doc-graph gate signs the shape — the
  vendor-docs-entity-core precedent: every corpus's doc-graph gate is a page an
  SME signs, and this one has never had one.
- **The editions ride.** The re-ingest is the natural moment the 2025/2026
  editions join (desktop-local payload; the load is venue-bound there, J18) —
  and capture-scoped `doc_id` exists precisely so multiple editions coexist
  without overwriting `doc_version`.
- **The displaced consumer, stated rather than dropped.** The `:DataAsset`
  slices seeded the effective-dated `BusinessSegment` context. The ruling
  should say what happens to that seeding — retired (if the C28-family
  business-layer work supersedes it) or rebuilt as a derivation over the
  lexical corpus. Silently deleting the one thing the old shape DID feed would
  repeat the class this repo keeps killing.
- **Cost.** A full docmeta pass (capture manifest, converter run, load,
  gate page), desktop-bound for the payload; and the old slices' migration or
  retirement is its own small ruling.

## Option B — keep the DataAsset slice shape

- **What it keeps.** The `BusinessSegment` context seeding as originally built;
  no new work.
- **What it costs.** The consumer stays unanswerable FOREVER by design — no
  chunks, nothing to embed, no retrieval; `graph_locator` stays `none`, so
  docs-verify permanently cannot reconcile the corpus (a registered corpus no
  check can see — the exact false-negative class the Q13 close repaired for
  every other corpus); `confirmed: false` stays meaningless because there is no
  doc-graph shape for a gate to sign; and the 2025/2026 editions have no
  ingestion path at all (the script is gone by design).

## The P4 rider (Idea-130): end-to-end candidacy

`docmeta-p4-revision-single-db.md` names only the BMC corpus for the end-to-end
local load today. **Under Option A, jpmc-reports is the natural SECOND
candidate — and for the public demo, arguably the better one**: it is
External-PUBLIC (SEC filings / investor-relations PDFs), `source_url` present,
`trust_default: VERBATIM` — so it exercises the whole P4 path (chunker,
embeddings, trust provenance, the `:Uncertain` routing) with **zero
publish-boundary risk**, none of the redaction care an Internal corpus forces.
Under Option B it cannot be a candidate at all — there is nothing for the P4
path to load.

## Recommendation

**Option A.** It is the only branch with a live consumer, it gives the registry
row a locator a check can act on, it is the only path the newer editions can
enter by, and it converts a publish-boundary-free corpus into the P4 path's
second end-to-end candidate. Option B preserves a seeding mechanism whose own
future is already in question — if the ruling keeps it, keep it as a stated
derivation over the lexical corpus, not as the reason retrieval stays
impossible.
