# Essential GraphRAG — pattern inventory & docmeta P0 input

**Citation:** Tomaž Bratanič & Oskar Hane, *Essential GraphRAG: Knowledge Graph-Enhanced RAG*,
Manning Publications, 2025 (Neo4j-sponsored ebook), ISBN 9781633436268, 176 pp.
<https://www.manning.com/books/essential-graphrag> (link verified 2026-07-16). Code repo cited
in the book: <https://github.com/tomasonjo/kg-rag>.

**Classification:** External (per `config/classification.yaml` — vendor-adjacent published book,
cite-don't-seed like every other `reference/research/` entry).

**Local PDF is gitignored** — never commit it or paste passages longer than a phrase/sentence.
This note is a derived pattern inventory, not a summary/excerpt of the copyrighted text.

**Provenance:** written for backlog item **Q1** ("Mine the Essential GraphRAG ebook for
applicable patterns; feed the docmeta P0 benchmark verdict"), by `reference-librarian`,
2026-07-16. Feeds `knowledge/upgrade-plans/docmeta-component.md` Phase P0 (benchmark spike:
graph traversal vs manifest-routed markdown vs vector RAG) and the planned backlog **Q2**
experiment (load this book as a Document→Chunk lexical graph, run an agent-traversal test
session over it).

---

## 1. Chapter/section pattern inventory

Book-page cites use the book's own internal pagination (matches the brief's chapter map), not
PDF page numbers.

### Ch.1 — Improving LLM accuracy (pp.1–16)
Motivational chapter: LLM limitations (knowledge cutoff, staleness, hallucination, no private
data), why RAG > continuous finetuning. **§1.4 "Knowledge graphs as the data storage for RAG
applications" (p.14)** is the one durable claim: a KG can hold *both* structured properties
(precise filter/count/aggregate queries) and unstructured content (`embedding` on an
`Article`/`Chunk`-like node) "in a single database system" — explicit argument for **not**
splitting a docs corpus and an entity/structured KG into separate stores.

### Ch.2 — Vector similarity search and hybrid search (pp.17–29)
The reference recipe for a **vector-RAG arm**: text corpus → sliding-window chunking (500 chars,
40-char overlap, split-on-whitespace only, p.21) → embedding model (OpenAI
`text-embedding-3-small`, 1536-dim, p.22) → `CREATE VECTOR INDEX ... FOR (c:Chunk) ON
c.embedding` (p.23–24) → `db.index.vector.queryNodes` (p.24–25) → LLM answer generation with a
"only use the provided documents" system message (p.26). **§2.3 hybrid search (p.27–28)**: adds
a `CREATE FULLTEXT INDEX`, runs vector + fulltext as a `UNION`, normalizes each branch's scores
by its own max, dedupes by node, `ORDER BY score DESC LIMIT k` — the exact union-and-normalize
shape DryDocs already uses for the P0/P1 entity `:Searchable` index (per
`graphrag-llm-navigation.md`). **§2.4 concluding thoughts (p.29)** is explicit that hybrid search
over unstructured chunks alone is "still quite limited... as the data complexity grows" —
motivates chapters 3–7's move toward structure.

### Ch.3 — Advanced vector retrieval strategies (pp.30–44)
- **§3.1 Step-back prompting (p.34–36):** query-rewriting technique — LLM rewrites a specific
  question ("Which team did X play for 2007–2008?") into a broader one ("What is X's career
  history?") before embedding it, to widen recall. Zero-shot → few-shot prompt shown verbatim
  (p.35).
- (unlabeled sidebar, p.32–33) **Hypothetical-question embedding**: embed LLM-generated
  questions-the-document-can-answer (`HAS_QUESTION` edges) instead of the document text itself —
  contrasted with the parent-document strategy below; not implemented in the book's code, only
  diagrammed.
- **§3.2 Parent document retriever (p.36–42):** three-tier graph — `PDF -[:HAS_PARENT]->
  Parent -[:HAS_CHILD]-> Child`; embeddings live only on `Child` (500-char chunks); retrieval
  queries `k*4` children via vector index, then `MATCH (node)<-[:HAS_CHILD]-(parent)`,
  dedupes to parent, `LIMIT k` — oversampling-then-collapse-to-parent so the LLM gets full
  context, not a fragment (p.41–42, Listing 3.11).
- **§3.3 Complete RAG pipeline (p.43):** chains step-back rewrite → parent-document retrieval →
  answer generation into one `rag_pipeline()` function.
- Sidebar (p.33–34): finetuning the embedding model, reranking, metadata-based filtering, and
  hybrid retrieval named as further options but "beyond the scope of this book" except hybrid
  (already covered ch.2).

### Ch.4 — Generating Cypher queries from natural language questions (text2cypher, pp.45–55)
The graph-traversal arm's reference implementation. **§4.2 (p.47)**: explicit framing —
text2cypher exists for questions vector search structurally cannot answer (aggregation, filter,
count, "top 3 highest-rated movies directed by X"); can double as a **catch-all retriever** when
no specialized retriever fits. **§4.3 Useful practices (p.47–52)**: (a) few-shot examples,
knowledge-graph-specific, added reactively as failure patterns are observed (p.47–48); (b)
**schema in the prompt**, inferred live via `apoc.meta.data()` (node/rel properties + rel
topology, p.48–51) rather than hand-maintained; (c) terminology mapping — a short glossary block
translating user vocabulary ("who acted" → `Person`) to graph vocabulary, "knowledge graph
specific... hard to reuse between different knowledge graphs" (p.51); (d) format instructions
("ONLY RESPOND WITH CYPHER — NO CODE BLOCKS", p.51–52). **§4.4 (p.52–54)**: full prompt template
combining all four. **§4.5 (p.54–55)**: Neo4j ships finetuned text2cypher models (Gemma2,
Llama 3.1) on Hugging Face — "still pretty far behind... latest GPT and Gemini" but cheaper/
faster for production.

### Ch.5 — Agentic RAG (pp.56–69)
Three foundational parts (p.57–58): **retriever router** (LLM w/ tool/function-calling picks the
best retriever(s) for a question), **retriever agents** (generic — vector search, text2cypher —
plus narrow hardcoded-query specialists added over time as text2cypher failure patterns emerge,
p.57–59), **answer critic** (checks whether retrieved answers actually satisfy the question;
generates follow-up questions if not, with an exit condition to avoid infinite loops, p.58,
66–68). Implementation notes: retriever tools described in OpenAI's tools/function-calling JSON
schema (p.59–62); a mandatory generic `answer_given` tool for "the answer is already in the
question/context" (p.62); **continuous query updating** — questions processed one at a time so
answers-so-far can rewrite pending follow-up questions ("Who won the most Oscars, and is that
person alive?" → two atomic questions where the second depends on the first's answer, p.63–65);
router + critic tied together in a single-pass loop, critiqued once, not indefinitely (p.68–69).

### Ch.6 — Constructing knowledge graphs with LLMs (pp.70–87)
**§6.1 (p.71–80):** motivating failure mode — naive chunk-and-retrieve across *multiple* legal
contracts risks mixing chunks from unrelated documents (p.71–72), and aggregation questions
("how many active contracts") can't be answered by embeddings at all — both push toward
structured extraction. LLM structured extraction via OpenAI Structured Outputs + Pydantic models
(p.73–78): mark attributes `Optional` explicitly or the model may hallucinate to fill gaps;
`enum` constrains categorical fields; free-text `description` per field is "good practice, even
when some attributes seem obvious"; nested objects allowed but "avoid too many levels" (p.75–78).
Demonstrated end-to-end on the CUAD legal-contract dataset (p.79–80). **§6.2 (p.81–87):** unique
constraints before import (p.82); import Cypher is explicitly called out as **non-idempotent**
when using `randomUUID()` for the merge key — "running the query multiple times will create
duplicate... entries" (p.83, a caution directly relevant to any DryDocs loader design). **Entity
resolution (p.84–85):** "highly use case and domain specific... a generic, one-size-fits-all
solution rarely works"; recommends domain-specific rules/ontologies plus SME-defined matching
criteria and "iterative feedback loops — where potential matches are verified or corrected."
**§6.2.3 (p.85–86):** combining structured + unstructured — attach a `Chunk` layer via
`HAS_CHUNK` alongside the structured entities, and prefer **domain-aware structural chunking**
(e.g., split contracts by clause) over naive token-count splitting: "splitting a contract by its
clauses preserves its semantic structure and improves the quality of downstream analysis."

### Ch.7 — Microsoft's GraphRAG implementation (pp.88–115)
Two-stage pipeline: entity/relationship extraction+summarization, then community
detection+summarization, then two retrieval modes. **§7.1 (p.89–90):** entity types are
configurable and must be decided in advance from the target question set — "shapes the entire
downstream process." **§7.2.1 Chunking (p.90–92):** the MS GraphRAG paper's own ablation shows
**smaller chunk sizes (600 tokens) extract markedly more entity references than larger ones
(2,400 tokens)**, and repeated "self-reflection" extraction passes over the same chunk keep
finding more entities each pass (Figure 7.2) — a quantified chunk-size/recall tradeoff. **§7.2.2
(p.92–96):** extraction prompt yields `("entity", name, type, description)` and
`("relationship", source, target, description, strength)` tuples; the same entity/relationship
pair commonly accrues *multiple* descriptions across chunks (repeated near-duplicate sentences
observed for "ORESTES," p.94–96). **§7.2.3 Summarization (p.96–99):** an LLM pass merges all
descriptions of one entity (or one relationship pair) into one coherent third-person paragraph,
resolving contradictions; flags **super-nodes** (entities with overwhelming relationship/
description counts — e.g., "Athens" in a full Greek-history corpus) as needing a
ranking/filtering step before summarization to avoid blowing the context window (p.99 sidebar).
**§7.2.4 Community detection (p.100–103):** Louvain (book's code) / Leiden (original MS
GraphRAG paper) clustering into `IN_COMMUNITY`-linked groups; each community gets an LLM-written
report with a fixed schema (TITLE, SUMMARY, IMPACT SEVERITY RATING 0–10, RATING EXPLANATION,
5–10 DETAILED FINDINGS) — this is the closest the book gets to "generate a structured document
about a cluster of things," directly transferable to a future DryDocs domain-community report.
**§7.3.1 Global search (p.104–109):** map-reduce over **all** community summaries above a rating
threshold — map step produces scored key-points per community, reduce step merges into one
answer; explicitly a "broad, thematic query" retriever, not for narrow lookups. **§7.3.2 Local
search (p.109–115):** vector search finds entry-point entities, then graph traversal expands to
connected chunks (`HAS_ENTITY`), relationships (`SUMMARIZED_RELATIONSHIP`), and community reports
(`IN_COMMUNITY`) — each expansion ranked and **capped** (`topChunks`, `topCommunities`,
`topInsideRels`) before being handed to the LLM. This vector-entry-point → bounded graph-expansion
shape is the single closest published pattern to "agent traversal over a Document→Chunk lexical
graph" (backlog Q2's stated goal).

### Ch.8 — RAG application evaluation (pp.116–126)
**§8.1 Designing the benchmark dataset (p.118–121):** decompose the pipeline into evaluable
stages — tool/retriever selection accuracy, retrieved-context relevance, answer-generation
quality, end-to-end correctness (Figure 8.1) — and build the question set to *deliberately*
exercise each stage plus entity/value mapping, multi-step (chained) retrieval, edge cases, and
conversational/out-of-scope handling. **Key design choice: ground truth is a Cypher query, not a
static string** (Figures 8.2–8.3) — "even if the underlying data changes, the benchmark remains
valid" (p.119). Benchmark had 17 examples total (p.121). **§8.2 Evaluation via RAGAS (p.121–124):**
three metrics — **context recall** (does the retrieved context contain what the answer needed,
p.121–122), **faithfulness** (decompose the answer into atomic statements, then verify each is
directly inferable from the retrieved context — an LLM-as-judge two-pass check, p.121–122), and
**answer correctness** (classify each answer statement TP/FP/FN against ground-truth statements,
p.122–123). Latency is captured per query alongside the three scores (p.123–124, Listing 8.2).
**§8.2.6 Observations (p.124–125):** worked example scores — answer_correctness 0.7774, context_
recall 0.7941, faithfulness 0.9657 — with an explicit reading: high faithfulness + lower recall/
correctness means "the model rarely makes things up" but the *retrieval* stage, not the
generator, is the bottleneck; failure analysis drills into individual failing questions (e.g., a
text2cypher miss traced to a missing few-shot example) rather than stopping at the aggregate
score.

---

## 2. DryDocs consumer mapping

| Pattern (chapter) | P0 benchmark arm it informs | Confirms or corrects current DryDocs practice | Q2 relevance |
|---|---|---|---|
| Ch.2 vector+hybrid RAG recipe | **vector RAG arm** — this is the reference build for that arm wholesale (chunk→embed→vector index→hybrid union) | **Confirms**: the union+per-branch-normalize hybrid-search Cypher shape (p.27–28) matches what P0/P1 already built for `:Searchable` per `graphrag-llm-navigation.md`. **Gap, not correction**: `bmc-docs` deliberately has NO embeddings (deterministic-only, per the 2026-07-08 gate) — ch.2 is the missing "vector RAG over docs corpus" arm DryDocs still needs to *build*, not one it got wrong. |  |
| Ch.3.2 parent-document retriever | vector RAG arm (a refinement) | **Corrects/extends**: DryDocs' `bmc-docs` chunking is flat two-tier (Document→Chunk, H2-split, no oversample-then-collapse-to-parent). If a vector arm is built for the P0 benchmark, the book's k*4-then-dedupe-to-parent pattern (p.41–42) is a stronger retrieval shape than a bare per-chunk vector hit. |  |
| Ch.4 text2cypher (schema-in-prompt, terminology mapping, few-shot, format instructions) | **graph traversal arm** — this chapter *is* that arm's reference implementation | **Confirms** the general direction (`graphrag-llm-navigation.md` #4 already flags DryDocs as "unusually strong for text2cypher because of `:SchemaMeta` + `:OntologyTerm`") and gives concrete practices to borrow: live `apoc.meta.data()` schema inference, a terminology-mapping block, explicit format instructions. None of this exists yet for a docs-corpus text2cypher retriever specifically. |  |
| Ch.5 agentic RAG (router / retriever agents / answer critic, continuous query updating) | cuts across all three arms — this is the orchestration layer *above* them | **Net-new**: DryDocs has no retriever-router or answer-critic today. Directly names the shape of "agent traversal" the P0 verdict and Q2 both invoke. | **High** — router+critic+continuous-query-update is the closest worked pattern to the planned Q2 "agent-traversal test session." |
| Ch.6 entity resolution (domain-specific, SME-in-the-loop, no generic solution) | n/a (construction, not retrieval) | **Confirms** DryDocs' HITL-gate-before-graph-write philosophy — the book independently arrives at "SME + iterative feedback loop," matching `config/gate-log.md`'s pattern, not a correction. |  |
| Ch.6.2.3 domain-aware structural chunking (clauses, not naive token count) | manifest-routed markdown arm (chunking strategy) | **Confirms** `bmc_docs.py`'s H2-heading chunking rule (deterministic, structure-aware, not fixed-token-window) — the book's stated preference for structural over naive chunking validates that choice independently. |  |
| Ch.6.2 non-idempotent import caution (`randomUUID()` merge keys) | n/a (implementation hygiene) | **Corrects nothing in DryDocs** (the `docmeta` plan's Phase P4 acceptance already requires "`docs-load` idempotent re-run adds nothing" — stricter than the book's own example code, which the book flags as non-idempotent). Worth citing as a documented anti-pattern to avoid when the `docmeta` chunker/loader is built. |  |
| Ch.7.2.1 chunk-size vs. entity-recall tradeoff (quantified) | n/a directly (entity extraction, which DryDocs' `bmc-docs` loader explicitly skips — "NO LLM extraction") | Informational: if DryDocs ever adds an LLM entity-extraction pass over docs (`docmeta` Phase P4+, SYNTHESIZED tier), this is a citable data point that smaller chunks + repeat passes recover materially more entities. | Relevant if Q2's experiment layers entity extraction on top of the lexical load. |
| Ch.7.2.4/7.3 communities + global/local search | agentic/graph-traversal arm (advanced) | **Confirms** `graphrag-llm-navigation.md`'s existing call to **defer** GDS/Leiden community detection for DryDocs' entity KG — the book shows it is a real, working pattern, just correctly scoped as "later," not urgent. | **High for local search specifically** — vector-entry-point → bounded graph-expansion (chunks/relationships/communities, each ranked+capped) is the strongest single template for Q2's agent-traversal session over the book's own lexical graph. |
| Ch.8 RAGAS evaluation design (Cypher-as-ground-truth, per-stage metrics, latency capture) | **the P0 verdict's shape itself** | **Corrects a gap**: DryDocs' P0 acceptance criterion ("written comparison — accuracy/latency/tokens... with a build/shrink recommendation," `docmeta-component.md` line 174) has no named accuracy methodology yet. Ch.8 supplies one directly: context recall / faithfulness / answer-correctness per arm, Cypher-query ground truth (survives data changes — matches a Neo4j-native corpus), and per-stage failure attribution (retrieval vs. generation) rather than one aggregate number. | Also usable as Q2's evaluation harness once an agent-traversal test session exists to score. |

---

## 3. "Are there more examples of how to do it properly?" — SME's standing question

**Yes.** Beyond what `bmc-docs` already implements (deterministic H2 chunking, no LLM, no
embeddings, VERBATIM/GROUNDED/SYNTHESIZED trust tiers, `PART_OF`/`FIRST_CHUNK`/`NEXT_CHUNK`/
`DESCRIBES`), the book supplies eight concrete, worked patterns DryDocs does not yet have any
version of:

1. **Full vector-similarity RAG pipeline** — embedding model + Neo4j vector index + hybrid
   full-text union query (ch.2, pp.20–28). `bmc-docs` has zero embeddings by design; this is the
   missing "vector RAG" P0 benchmark arm's reference build.
2. **Step-back query rewriting** — rewrite a specific question into a broader one before vector
   search (ch.3.1, pp.34–36). Not present anywhere in DryDocs.
3. **Parent-document retriever** — three-tier chunking with oversample-and-collapse-to-parent
   retrieval (ch.3.2, pp.36–42). `bmc-docs` is flat two-tier only.
4. **Production text2cypher recipe** — live schema inference (`apoc.meta.data()`), terminology
   mapping, few-shot examples, format instructions, combined into one prompt template (ch.4,
   pp.46–54). This is the "graph traversal" P0 arm's reference implementation; DryDocs has no
   docs-corpus text2cypher retriever yet.
5. **Full agentic RAG loop** — LLM-driven retriever router (function-calling), continuous query
   updating for dependent follow-up questions, and a bounded answer-critic retry loop (ch.5,
   pp.57–69). Nothing like this exists in DryDocs; it is the closest template for the "agent
   traversal" side of the P0 verdict and for backlog Q2.
6. **LLM-based structured extraction with entity resolution discipline** — Pydantic Structured
   Outputs models, `Optional`-vs-required field discipline to prevent hallucinated fills, and a
   documented SME-in-the-loop entity-resolution process (ch.6, pp.71–85). `docmeta`'s plan defers
   this to a later phase (SYNTHESIZED tier only, P4+); the book is the concrete "how" for when
   that phase starts.
7. **Microsoft GraphRAG community detection + global/local search** — Louvain/Leiden clustering,
   structured community reports, map-reduce global search, and vector-entry-point bounded
   graph-expansion local search (ch.7, pp.88–115). Explicitly the item `graphrag-llm-navigation.md`
   already flags as **deferred** for DryDocs' entity KG — the book validates it as real and
   working, correctly scoped as future, not urgent.
8. **RAGAS-based multi-stage evaluation harness with Cypher-as-ground-truth** — context recall /
   faithfulness / answer correctness scored per pipeline stage, ground truth defined as a Cypher
   query (survives data drift) rather than a static string, plus per-query latency capture (ch.8,
   pp.116–126). DryDocs' P0 acceptance criterion currently has no named accuracy methodology;
   this is the most directly actionable gap the book closes for the P0 written verdict itself.

None of these eight require abandoning what `bmc-docs` already does — 1, 3, 4, 8 are additive
retrieval/evaluation arms to *benchmark against* the existing deterministic lexical load (which
is exactly what P0 asks for), and 5–7 are consumer-side (agent/retrieval) patterns that sit on
top of, not instead of, the existing Document→Chunk graph.
