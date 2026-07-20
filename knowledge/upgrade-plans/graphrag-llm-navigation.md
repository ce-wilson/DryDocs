# Upgrade plan — GraphRAG / LLM-navigation (benchmarked vs `llm-graph-builder`)

> **Status 2026-07-17 — partially superseded.** `feat/llm-nav-p0-vector` no longer
> exists and its vector/fulltext work is **not on main** (no vector index, no
> `:Searchable`, no embeddings loader in the repo). The "already matches the
> reference" table below describes that branch, not current code. The refinements
> (§1–§4) remain valid future guidance for when the vector arm unblocks on the open
> LLM-key-strategy question. Authoritative retrieval direction is now the docmeta P0
> verdict ([`docmeta-p0-verdict.md`](docmeta-p0-verdict.md)): traversal-first,
> fulltext supplement, vector deferred. Full audit:
> [`neo4j-advisor-confirmation-2026-07-17.md`](neo4j-advisor-confirmation-2026-07-17.md).

Compares DryDocs (after the P0 vector + P1 fulltext work on `feat/llm-nav-p0-vector`)
against Neo4j Labs' production reference **`llm-graph-builder`**, to decide what to
adopt. Source analysis 2026-06-19.

## Framing
`llm-graph-builder` is a **document → KG ingestion + GraphRAG** tool; DryDocs is an
**already-structured** KG. Only the vendor repo's **retrieval / entity / index**
layers transfer — its `Document → Chunk` text-chunking layer does **not** apply
(DryDocs has no documents to chunk). Adopt the retrieval patterns; skip the chunking.

## Validation — P0/P1 already matches the reference

| Best practice (`llm-graph-builder`) | DryDocs after P0/P1 | Status |
|---|---|---|
| Entity vector index, **cosine** (`entity_vector` on `__Entity__.embedding`) | vector index, cosine, on `:Searchable.embedding` | ✅ same |
| **Generic base label** so one index covers all entities (`__Entity__`) | `:Searchable` plays that role | ✅ aligned |
| Embed `id + description` per entity | `embed_text` = name + description/notes | ✅ aligned |
| **Fulltext entity index** on `[id, description]` | `entity_text` over name/label/description/notes | ✅ aligned |
| One property name `embedding` graph-wide | DryDocs uses `embedding` | ✅ aligned |

**Conclusion: direction is correct.** The items below are refinements, not a rewrite.

## Refinements to adopt (prioritized)

1. **Write vectors with `db.create.setNodeVectorProperty(n,'embedding',$emb)`**
   instead of `SET n.embedding = $emb` — the recommended Neo4j 5.x API for vector
   properties (`make_relationships.py`, `communities.py:145`). One-line change in
   `drydocs/loaders/embeddings.py`. *Highest value / lowest effort.*
2. **Batch the embedding writes via `UNWIND`** (current P0 writes one node per
   round-trip). Combine with #1: `UNWIND $rows AS r MATCH (n) WHERE elementId(n)=r.eid
   CALL db.create.setNodeVectorProperty(n,'embedding',r.emb) SET n:Searchable, n.embed_text=r.text`.
3. **Derive the vector-index dimension from the live embedder + a drop/recreate
   path** rather than hardcoding 1536 (`post_processing.py:89-91`,
   `graphDB_dataAccess.py:523-556`). POC drops/recreates DBs, so low urgency, but
   it's the production-correct pattern.
4. **Design the agent for hybrid + text2cypher retrieval** (vendor default mode is
   `graph_vector_fulltext`; `graph` mode = `GraphCypherQAChain(validate_cypher=True)`).
   *Agent-side, not a graph change.* DryDocs is unusually strong for text2cypher
   because of its `:SchemaMeta` meta-graph + `:OntologyTerm` layer — lean on it.

## Skip / defer

- **Chunk/Document layer & chunking** — N/A; DryDocs isn't document-derived.
- **GDS Leiden community detection + summaries** (`communities.py`) — the vendor's
  "global sense-making" layer. **Lower priority** for DryDocs: the ontology +
  `:SchemaMeta` layers already provide the global/topic map that communities
  synthesize for *extracted* graphs. It would also add a **GDS** dependency
  (currently only APOC is required). Revisit only if global aggregate questions
  prove weak.

## Verdict
Update DryDocs **lightly**: fold refinements #1–#2 into the P0 embeddings module,
optionally #3, and design the future agent around hybrid + text2cypher (#4). Treat
communities as optional. The comparison is mostly reassuring — P0/P1 already mirrors
the vendor's proven entity-retrieval design.

### Reference files (in `../../../llm-graph-builder/backend/src/`)
`post_processing.py` (indexes, entity embeddings), `make_relationships.py` (chunk
embeddings, vector write API), `communities.py` (GDS Leiden + summaries),
`constants.py` (`CHAT_MODE_CONFIG_MAP`, retrieval queries), `QA_integration.py`
(hybrid retriever wiring), `common_fn.py` (model→dimension table).
