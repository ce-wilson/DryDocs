# P4 revision — docmeta load path on the single-database topology, local embeddings first

**Status:** DRAFT / GATE-BOUND — nothing here is applied; the three decisions in §7 go
through the HITL gate before any loader lands.
**Date:** 2026-08-14.
**Classification:** Internal-Public.
**Revises:** the P4 row and §2 graph targets of
[`docmeta-component.md`](docmeta-component.md) (ADR 0006 shape).
**Relates to:** [`../../docs/decisions/0011-single-database-contingency.md`](../../docs/decisions/0011-single-database-contingency.md)
(the fold-down mechanisms this revision builds on),
[`docmeta-p0-verdict.md`](docmeta-p0-verdict.md) (traversal-first, fulltext supplement,
vector deferred), [`graphrag-llm-navigation.md`](graphrag-llm-navigation.md)
(refinements #1–#3, adopted here), ADR 0002 (D1 — superseded in direction by the
consolidation decision this revision assumes).

---

## 1. What changed since the P4 row was written

Two things, one decision-level and one technique-level:

1. **The single-database consolidation is now the working direction.** ADR 0011 wrote
   the fold-down as a contingency; the SME has since set the plan to consolidate back
   to one database. This revision therefore targets **one database** and drops the
   `dddocs` provisioning delta entirely. ADR 0011's mechanisms — the `:Uncertain`
   label namespace, the watermark re-key from *where a query runs* to *what a query
   matches*, and the `config/dev-environment.yaml` `neo4j.databases` map as the single
   name seam — are taken as given, not re-argued.
2. **The `neo4j-document-import` and `neo4j-graphrag` reference skills were evaluated
   against P4 (2026-08-14).** Verdict: keep the hand-built loader (the P0 BUILD verdict
   stands — the provenance envelope and gate discipline are exactly what
   `SimpleKGPipeline` does not provide), but adopt its proven parameters and
   sequencing: chunk sizing for dense technical text, constraint-first index ordering,
   MERGE-idempotency shape, and — the unblocker — **local sentence-transformer
   embeddings, which need no API key** and therefore dissolve the LLM-key blocker
   that had the vector arm deferred. §8 records what was evaluated and rejected.

---

## 2. Revised graph target (supersedes docmeta-component.md §2)

- **One database.** Document/Chunk nodes load into the ground-truth database named by
  the `dev-environment.yaml` map. No `CREATE DATABASE dddocs`, no composite update, no
  proxy nodes. `drydocs/docs_coverage.py`'s `target_db ∈ {dddocs, ddcontext}` guard set
  collapses per ADR 0011 clause 3 (the `dddocs` row was already PLANNED-not-provisioned).
- **`target_db` in `config/doc-source-registry.yaml` becomes a trust routing, not a
  physical routing.** The field is kept (the registry schema does not churn) but its
  values resolve through the map; what actually varies per tier is the label set:
  - T1 vendor / confirmed T2–T3 content → plain `(:Document)` / `(:Chunk:Searchable)`,
    no `:Uncertain`.
  - T4 SME-context and any pre-confirmation content → additionally `:Uncertain`,
    stamped **by the loader at write time** (the ADR 0011 clause 1 rule: the label is
    applied at the write boundary, never optional). Specs touching these chunks are
    watermarked by the clause 3 re-key.
- **Real edges instead of composite joins.** In one database
  `(:Chunk)-[:DESCRIBES]->(:ControlMJob)` can be a direct relationship to the actual
  estate node — no `{folder_id, job_id}` proxy. This is the single largest win of the
  consolidation for this component: traversal-first retrieval reaches estate context
  in one hop. Chunk-level `DESCRIBES` remains **deferred to its own gate at extraction
  design** (the ADR 0006 ruling stands); this revision only notes that its
  implementation cost dropped from "proxy + composite join" to "one MERGE".
- **Edge shape unchanged:** `(:DocSource)-[:HAS_DOCUMENT]->(:Document)`,
  `(:Chunk)-[:PART_OF]->(:Document)`, `(:Document)-[:FIRST_CHUNK]->(:Chunk)`,
  `(:Chunk)-[:NEXT_CHUNK]->(:Chunk)`, `(:Document)-[:GOVERNED_BY]->(:OntologyTerm)` —
  the ADR 0006 reconciliation (`HAS_CHUNK` superseded). `HAS_DOCUMENT`/`GOVERNED_BY`
  stay `status: planned` until gated.
- **Provenance envelope unchanged and non-negotiable:** every Document/Chunk carries
  `classification`, `trust` (VERBATIM/GROUNDED/SYNTHESIZED), `sha256`, `captured_at`,
  `curation_status`. SYNTHESIZED is never citable as vendor ground truth.

## 3. Load path (`drydocs_docmeta/` additions)

```
drydocs_docmeta/
  chunker.py           # P4 — splits cleaner.py output into ordered chunks
  embedder.py          # P4 — embedding protocol + local backend (§4)
  loaders/
    cypher/
      document.cypher  # MERGE (:Document {doc_id}) + envelope + HAS_DOCUMENT
      chunk.cypher     # UNWIND batch → MERGE (:Chunk {chunk_id}) + PART_OF + envelope
      links.cypher     # FIRST_CHUNK + NEXT_CHUNK linked list
      embeddings.cypher# UNWIND batch → db.create.setNodeVectorProperty (§4)
```

- **Chunker parameters** (adopted from the document-import reference; the BMC corpus is
  dense technical text): target **256–512 tokens** per chunk, overlap **10–15%**,
  splits respect sentence/heading boundaries (never mid-sentence). Token counts come
  from the existing `tokenizer.py` (with its labeled fallback); the chunker stores
  `token_count`, `tokenizer` provenance per chunk. `chunk_id` = `doc_id#<index>`,
  deterministic, so re-chunking an unchanged document is a no-op under MERGE.
- **Idempotency mechanism** (the P4 acceptance "re-run adds nothing"): uniqueness
  constraints on `Document.doc_id` and `Chunk.chunk_id` created **before** first load;
  all loaders MERGE on those keys; a changed `sha256` re-queues curation
  (`manifest.diff()`) rather than silently overwriting — invariant 4 unchanged.
- **Batching:** chunk and embedding writes go through `UNWIND $rows` batches
  (500–1000 rows), one transaction per batch — the graphrag-llm-navigation
  refinement #2, now applied to the docs corpus instead of the entity layer.

## 4. Embeddings — local model now, server-side key later

**Decision (gate item G-2, §7): embed with a local sentence-transformers model until a
server-side LLM/embedding key is provisioned.** This unblocks the vector arm without
resolving the open LLM-key-strategy question — the model runs in-process, no data
leaves the machine, no credential exists to manage. The p0 verdict's "vector deferred"
was blocked on the key decision, not on vectors being wrong; the block dissolves.

- **Backend:** `sentence-transformers` (new optional dependency group
  `embeddings` in `pyproject.toml`; not installed by default — Track-1 tests never
  import it). Default model **`all-MiniLM-L6-v2`** (384 dims, fast, CPU-fine for the
  corpus size). `embedder.py` defines a small protocol
  (`embed(texts: list[str]) -> list[list[float]]` + `model_id` + `dimensions`) so the
  server-side backend later implements the same interface behind config.
- **Dimension is derived from the live embedder, never hardcoded** — refinement #3.
  The vector index is created (or dropped and recreated) from `embedder.dimensions`
  at `docs-load` time; a dimension mismatch between index and embedder fails fast
  before any write.
- **Embedding provenance on every embedded node:** `embedding_model`,
  `embedding_dimensions`, `embedded_at`. This is what makes the later key-swap safe:
  mixed-model states are queryable, and the migration is
  "re-embed WHERE embedding_model <> $new, then drop/recreate the index" — a
  mechanical sweep, not an archaeology project.
- **Write API:** `db.create.setNodeVectorProperty(n, 'embedding', $emb)` inside the
  UNWIND batch — refinement #1. One property name `embedding` graph-wide; chunks get
  `:Searchable` (the existing generic-label design), so the one vector index covers
  chunks today and entities later.
- **Swap path when the server-side key lands (recorded now, executed then):**
  add the API-backed embedder behind the same protocol, flip the config, run the
  re-embed sweep, recreate the index at the new dimension. Nothing in the loaders
  changes. Until then the local model's quality ceiling is accepted — it serves the
  *fulltext-supplement* role beside traversal, not the primary retrieval arm.

## 5. Index and constraint sequence (run before first load, in this order)

1. `CREATE CONSTRAINT ... FOR (d:Document) REQUIRE d.doc_id IS UNIQUE`
2. `CREATE CONSTRAINT ... FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE`
3. `CREATE FULLTEXT INDEX chunk_text ... FOR (c:Chunk) ON EACH [c.text]` — the
   fulltext **supplement** of the p0 verdict; costs nothing, needs no key.
4. `CREATE VECTOR INDEX chunk_embedding ... ON (c:Searchable) ... vector.dimensions:
   <embedder.dimensions>, similarity: cosine` — engine is 5.26, so retrieval uses the
   `db.index.vector.queryNodes` procedure path (the Cypher 25 `SEARCH` clause is a
   2026.x feature; note for the eventual engine upgrade).
5. Poll `SHOW INDEXES YIELD name, state WHERE state <> 'ONLINE'` until empty —
   **`docs-load` refuses to start while any listed index is not ONLINE** (adopted
   sequencing; prevents the half-indexed-corpus state).

## 6. Retrieval implication (post-P4, direction only)

Traversal-first stands. The first retriever added after the corpus loads should be
**text-to-Cypher** (no embedder in the loop, plays to the `:SchemaMeta` +
`:OntologyTerm` strength; the neo4j-graphrag `Text2CypherRetriever` runs `EXPLAIN`
on generated Cypher and rejects writes — the safety property the gate discipline
wants). Hybrid vector+fulltext retrieval becomes worth wiring once §4's embeddings
exist; both are follow-on items, not P4 scope.

## 7. Gate items (nothing below lands until confirmed)

| # | Decision | What confirmation means |
|---|---|---|
| G-1 | **P4 targets the single database; the `dddocs` provisioning delta is cancelled.** Amends ADR 0006's `dddocs` ruling; assumes the ADR 0011 fold-down (incl. its clause 1 residual-risk acceptance, which is its own SME call and is NOT bundled into this gate). | ADR 0006 gets a dated amendment note; `docs_coverage.py` guard set re-keyed |
| G-2 | **Local embeddings via sentence-transformers (`all-MiniLM-L6-v2`, 384d) until a server-side key is provisioned**; embedding-provenance fields (`embedding_model`, `embedding_dimensions`, `embedded_at`) join the envelope. | `pyproject.toml` gains the optional group; vocab/registry untouched (properties, not edges) |
| G-3 | **T4 / pre-confirmation doc content carries `:Uncertain` from the docmeta loader** — extends the ADR 0011 clause 1 writer boundary (today `drydocs_deepdoc` only) to a second authorized writer, which the clause 1(b) boundary test must then permit. | `test_module_boundary.py` label guard updated in the same commit as the loader |

Already-gated items this revision does **not** re-open: the PART_OF/FIRST_CHUNK/
NEXT_CHUNK shape (ADR 0006), chunk-level `DESCRIBES` deferral (ADR 0006),
`HAS_DOCUMENT`/`GOVERNED_BY` as `planned`, the curation ladder (P5).

## 8. Evaluated and rejected (so the next session doesn't re-litigate)

- **`SimpleKGPipeline` (neo4j-graphrag) as the load path** — rejected. Its core value
  is LLM entity extraction (`Chunk-[:MENTIONS]->entity` + entity–entity edges), which
  is precisely what §1.2's import rule forbids: relationship meaning is an ontology
  decision through the gate, never invented at import. It also cannot stamp the
  provenance envelope, and it hard-requires an embedder object even when embeddings
  are unwanted. Revisit **constrained to a `GraphSchema` generated from the
  gate-approved relationship vocabulary** as a possible P6+ extraction stage — that
  is the one configuration in which its extraction is not an end-run around the gate.
- **Automatic entity resolvers (`SinglePropertyExactMatchResolver`,
  `FuzzyMatchResolver`)** — rejected for the same reason: an unattended bulk merge is
  a promotion that skipped the gate. Any dedup proposal routes through HITL.
- **`LLM Graph Builder` web UI** — not applicable; no-code ingestion bypasses the
  registry, the classification requirement, and the envelope entirely.

## 9. Revised P4 row (drop-in for the docmeta-component.md phase table)

| Phase | Work | Acceptance |
|-------|------|------------|
| **P4 — Load path (single-db revision)** | chunker (256–512 tok, 10–15% overlap, boundary-respecting) + `document/chunk/links/embeddings.cypher` loaders + `embedder.py` local backend; constraints + fulltext + vector indexes per §5; load BMC corpus end-to-end locally; G-1/G-2/G-3 gated first | `docs-load` idempotent re-run adds nothing; refuses to run with any index not ONLINE; trust + embedding provenance queryable per chunk; T4 chunks carry `:Uncertain`; Track-1 suite green with `embeddings` group NOT installed; composite smoke replaced by a single-db smoke reading docs + estate in one query |
