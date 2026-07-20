# Q2 experiment — agent traversal over the Essential GraphRAG lexical graph

> **Point-in-time experiment record (2026-07-16).** Docmeta **P0 benchmark evidence,
> traversal arm**. Backlog item **Q2** (Epic Q / phase 14); the companion pattern
> inventory is [`reference/research/essential-graphrag-notes.md`](../../reference/research/essential-graphrag-notes.md) (Q1).
> Facts are pinned to the load run below; the corpus is reloadable deterministically.

## What was loaded

| | |
|---|---|
| Corpus | *Essential GraphRAG: Knowledge Graph-Enhanced RAG* (Bratanič & Hane, Manning 2025) — local gitignored PDF, cite [source_url](https://www.manning.com/books/essential-graphrag) |
| Source entry | `config/source-registry.yaml#essential-graphrag` (External; confirmed per the Q2 groom decision — pure reuse of the ACTIVE `docs_*` vocabulary, covering gate `bmc-docs-lexical-load` 2026-07-08) |
| Loader | `essential_graphrag.v1` (`drydocs/loaders/essential_graphrag.py` + `cypher/essential_graphrag.cypher`), CLI `drydocs load-essential-graphrag` |
| Chunking | `pdf-lexical-v1`, fully deterministic (no LLM, no embeddings): front matter → 8 chapter preambles → 28 monotonic numbered sections → appendix (A.1–A.4) → back matter = **43 chunks**, every chunk tier GROUNDED (`pdf-extract-grounded-v1` — pypdf is mechanical but lossy) |
| Target DB | **`ddcontext`** — execution decision: experiment/reference content stays out of the ground-truth `drydocs` DB; matches the user's "our own unstructured context graph" phrasing and the jpmc-reports precedent |
| Graph shape | 1 `:Document`, 43 `:Chunk`, 43 `PART_OF`, 42 `NEXT_CHUNK` (unbroken chain), 1 `FIRST_CHUNK`, **0 `DESCRIBES`** (deliberately omitted — no registry SoftwareProduct target) |
| Load run | JobRun `7c13b7e5-03b8-45d3-94e8-9a5ca15462eb`, 2026-07-16T22:38Z, 43/43 rows, 0 rejects; **idempotent re-run verified: `rows_changed: 0`** (the doc-06 delta pattern; meets the docmeta P4 "re-run adds nothing" standard) |

## Traversal session (MCP `read-cypher`, `USE ddcontext`)

Seven retrieval questions, each answered by graph traversal only — no embeddings, no
LLM retrieval. The `USE ddcontext` clause routes cleanly through the `neo4j-drydocs`
MCP connection (session DB remains `drydocs`), so agents need no second connector.

| # | Question | Traversal shape | Answer (verified) |
|---|---|---|---|
| 1 | What does chapter 3 cover, and what are its sections? | property filter `{chapter: 3}` + `ORDER BY seq` | "Advanced vector retrieval strategies": 3.1 Step-back prompting, 3.2 Parent document retriever, 3.3 Complete RAG pipeline |
| 2 | Why do we need agentic RAG, per the book? | direct section address `{section: '5.2'}` | §5.2 (PDF p.80): best-source routing across varied sources; specialized retrievers for broad/complex sources; generic (vector, text2cypher) vs specialized retrievers |
| 3 | What follows the parent-document retriever section? | lexical chain hop `(3.2)-[:NEXT_CHUNK]->` | 3.3 Complete RAG pipeline (PDF p.64) |
| 4 | Where does the book discuss RAGAS? | content scan `CONTAINS 'RAGAS'` + chapter property | Chapter 8 only: the ch.8 preamble (2 mentions) and §8.2 Evaluation (3 mentions) |
| 5 | Which chapter has the most sections; how big is each? | aggregation over chunk properties | Ch.4 most sections (6); ch.7 largest by text (59,454 chars); full table returned — the aggregation class vector RAG structurally cannot answer (the book's own §4.2 point) |
| 6 | Who/what/when produced this content? | provenance traversal `Chunk-[:WAS_GENERATED_BY]->JobRun` + Document fields | Full citation (title/authors/publisher/2025-07/URL/External) + loader `essential_graphrag.v1`, 2026-07-16T22:38Z, 43 rows |
| 7 | Find 'step-back' and give me its surrounding context | content hit → `NEXT_CHUNK` neighbors + chapter siblings (the book's own §3.2 oversample-then-collapse shape) | Hit = ch.3 preamble; before = 2.4 Concluding thoughts, after = 3.1 Step-back prompting; full chapter context returned |

**The instructive miss:** question 7's first attempt returned empty — the earliest
'step-back' hit by `seq` was the FRONT MATTER chunk (the TOC mentions every section
title), whose `chapter` is null, so the non-optional sibling `MATCH` dropped the row.
Fix: filter content scans to `chapter IS NOT NULL` (or `level = 2`). Lesson for the P0
verdict and any docs-corpus retriever: **front/back matter must be excluded or
down-ranked at query time** — the lexical model keeps them (faithfulness) so retrieval
has to handle them.

## Findings for the P0 verdict (traversal arm)

1. **Traversal answers structure, sequence, aggregation, and provenance questions
   exactly** (Q1, Q3, Q5, Q6) — the classes the book's §4.2 says vector search
   structurally cannot do. Zero index/embedding infrastructure was needed.
2. **Content questions work only at exact-substring strength** (Q4, Q7): `CONTAINS
   'RAGAS'` is fine; a paraphrase ("how do I score my RAG app?") would miss. This is
   the boundary where the ch.2 vector arm (or at minimum a full-text index) earns its
   keep — consistent with the Q1 notes' mapping.
3. **The chapter/section/page properties earn their cost**: direct section addressing
   (Q2) and citation-faithful answers (PDF page numbers) came straight from chunk
   properties the deterministic chunker computed — no retrieval step at all when the
   agent already knows the book's structure (which Q1's inventory gives it).
4. **Per ch.8's evaluation frame** (context recall / faithfulness / answer
   correctness): on this 7-question set, traversal scored 7/7 answerable with fully
   faithful context (the chunk IS the source text); the failure mode observed was
   retrieval-stage (front-matter pollution), not generation-stage — matching the
   book's own observation that retrieval, not generation, is usually the bottleneck.
5. **Operationally**: `USE ddcontext` through the existing MCP connection means agent
   traversal over the context DB needs no new plumbing; the composite (`ddall`) was
   not needed.

## Reproduce

```powershell
# constraints (once): document_id + chunk_id in ddcontext
poetry run drydocs load-essential-graphrag          # defaults: root PDF -> ddcontext
poetry run pytest tests/unit/test_essential_graphrag.py -q
```
