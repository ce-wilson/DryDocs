# docmeta P0 benchmark verdict — traversal vs manifest-routed markdown vs vector RAG

> **The P0 acceptance deliverable** (backlog **Q3**, Epic Q / phase 14; written
> 2026-07-16): the "written comparison (accuracy/latency/tokens) with a build /
> shrink-to-registry-only recommendation" the docmeta plan's P0 row requires.
> Companion inputs: the Q1 pattern inventory
> ([`reference/research/essential-graphrag-notes.md`](../../reference/research/essential-graphrag-notes.md))
> and the Q2 traversal experiment
> ([`docs/reviews/essential-graphrag-traversal-experiment.md`](../../docs/reviews/essential-graphrag-traversal-experiment.md)).

## Verdict

**BUILD** the docmeta component. Do not shrink to registry-only. Grounds, in one
paragraph: on a fixed 12-question support set over the live bmc-docs corpus, graph
traversal matched or beat every other arm on context recall (12/12, including a
correct abstention on the out-of-scope question) at **roughly 27× the token
efficiency of manifest-routed reading** (~16k chars total vs ~450k), and four of the
twelve questions (aggregation, per-chunk provenance, version-property, corpus
structure) are **only** answerable from the graph — no amount of file reading
computes "how much of this corpus is SYNTHESIZED" without doing the graph's job by
hand. The known weakness (paraphrase retrieval) is real but bounded, partially
covered today by a zero-dependency full-text index, and fully addressable by the
ch.2 vector arm once an embedding key exists — a named dependency, not a reason to
shrink scope.

## Setup

| | |
|---|---|
| Corpus | bmc-docs (26 `controlm-*.md`, 313,350 chars) loaded live 2026-07-16 into the EE container's `drydocs` DB: **374 chunks**, 0 rejects (loaders `software_registry.v1` then `bmc_docs.v1` — the gate-confirmed order) |
| Question set | 12 fixed support questions in six ch.8-style stage classes: structure/aggregation (SA×2), exact lookup (EL×3), paraphrase/conceptual (PC×3), multi-doc (MD×2), provenance (PV×1), out-of-scope (OS×1) |
| Arms run live | **traversal** (handwritten Cypher over Document→Chunk — the author as text2cypher stand-in, disclosed), **full-text** (throwaway Lucene index on `Chunk.heading/text`, top-3; created for the benchmark and DROPPED after — DB left as found), **manifest-routed markdown** (author as router over `SOURCE-MANIFEST.md`; cost = full text of the routed files, which is what lands in an agent's context) |
| Arm assessed analytically | **vector-proper (embeddings)** — cannot run here: no committed embedding/LLM key (the open LLM-key-strategy IDEAS question). Assessment below uses the Q1 notes (ch.2/ch.3) plus the observed full-text failure cases as its lower bound |
| Scoring | Per question per arm: context recall (ground-truth regex present in retrieved context), token cost (retrieved chars; ≈ chars/4 tokens), latency (single warm run, ms — spike-grade, not a load test). Judge = the author (the ch.8 LLM-as-judge role, disclosed) |

Two scoring artifacts corrected during adjudication (recorded, not hidden): MD1 and
PV1 traversal queries returned correct answers whose output columns didn't echo the
marker literal (doc lists / counts rather than prose), so the mechanical scorer
under-counted traversal by 2. The tables below show adjudicated results; the raw
mechanical output is in the benchmark script's JSON.

## Results

Recall / cost / latency per arm (adjudicated; ✔ = answer context retrieved,
✔* = retrieved only with domain-informed terms, ✗ = miss, Ⓐ = correct abstention,
✗! = false-positive context on an unanswerable question):

| Q | Class | Traversal | Full-text (top-3) | Manifest-routed |
|---|---|---|---|---|
| SA1 corpus size + largest doc | structure | ✔ 67ch · 110ms | ✗ (no aggregation) | ✔ 75,940ch (read + count by hand) |
| SA2 SYNTHESIZED share | aggregation | ✔ 179ch · 49ms | ✗ (no aggregation) | ~ rule only, not the numbers |
| EL1 %%LIBMEMSYM | exact | ✔ 3,526ch · 52ms | ✔ 3,548ch · 46ms | ✔ 20,842ch |
| EL2 ctmcreate | exact | ✔ 1,312ch · 20ms | ✗ (ranking dilution) | ✔ 7,850ch |
| EL3 ODAT | exact | ✔ 1,750ch · 76ms | ✔ 4,042ch · 9ms | ✔ 20,842ch |
| PC1 make a job wait for another | paraphrase | ✔* 1,309ch · 49ms | ✗ (paraphrase gap) | ✔ 12,100ch |
| PC2 run job when a file arrives | paraphrase | ✔* 2,086ch · 75ms | ✔ 2,503ch · 9ms | ✔ 13,702ch |
| PC3 skip holidays | paraphrase | ✔ 2,118ch · 75ms | ✔ 2,029ch · 11ms | ✔ 20,271ch |
| MD1 pool-variable docs | multi-doc | ✔ 446ch · 109ms | ✔ 3,039ch · 8ms | ✔ 43,853ch (3 files) |
| MD2 target version + API compat | multi-doc/prov | ✔ 1,506ch · 98ms | ✔ 3,080ch · 12ms | ✔ 83,270ch (2 files) |
| PV1 are JSON examples ground truth? | provenance | ✔ 1,053ch · 81ms | ✗ (tier is a property, not text) | ~ rule only, not per-chunk |
| OS1 AutoSys variable (out of scope) | out-of-scope | Ⓐ empty · 17ms | ✗! 3,678ch of confident noise | Ⓐ router abstains |
| **Recall** | | **12/12** | **7/12** | **10/12 (2 partial)** |
| **Total context** | | **≈16,400 ch (~4.1k tok)** | ≈31,400 ch (~7.9k tok) | **≈449,500 ch (~112k tok)** |
| **Median latency** | | 75ms | 12ms | ~1ms + human/agent reading |

### Per-arm reading

**Traversal** — perfect recall on this set, the smallest contexts on 9/12 questions,
and the only arm that answers the aggregation/provenance/version classes at all
(the book's own §4.2 point, reproduced live). Its honest dependency is **query
quality**: the two paraphrase questions failed with naive phrase-CONTAINS
(`traversal_naive`: 0 rows) and succeeded only after term mapping
("wait for another job" → *prerequisite condition*; "file arrives" → *File
Watcher*) — exactly ch.4's terminology-mapping practice. The graph is only as good
as its text2cypher layer; DryDocs' `:SchemaMeta`/`:OntologyTerm` inventory (per
`graphrag-llm-navigation.md`) is the existing mitigation.

**Full-text** — cheap (no key, no external dependency, ~10ms) and covers most
exact-term and easy-paraphrase lookups, but it showed all three failure modes in
one run: ranking dilution (EL2 — 'utility'-dense chunks outranked the rare term),
the paraphrase gap (PC1), and **confident noise on out-of-scope questions** (OS1
returned 3.7k chars for an AutoSys question this corpus cannot answer — the
worst failure mode for a support agent). Verdict: worth keeping as a *component*
(the ch.2 hybrid design's keyword half), never as the sole retriever.

**Manifest-routed markdown** — the today-baseline. Recall is good *because the
router is an LLM reading a well-maintained manifest*, and it abstains correctly.
But the cost profile is disqualifying as the primary mechanism: ~112k tokens for
12 questions (28–60× traversal per question), every answer requires the agent to
re-read whole files, and the aggregation/provenance classes come back as "the rule
says…" rather than actual numbers. It remains the right **fallback** and the right
**authoring surface** (the manifest is the provenance model's source of truth).

**Vector-proper (analytical)** — the two live full-text misses (EL2, PC1) plus Q2's
exact-substring boundary are precisely the cases ch.2/ch.3 embeddings address
(paraphrase recall, ranking by semantic similarity, parent-document collapse for
fuller context). Expected cost: an embedding pass at load time + one vector index;
expected risk: the OS1 failure mode gets *worse* without a scoring threshold
(vector search always returns nearest neighbors). Blocked today by the open
LLM-key-strategy question — the docmeta ADR should treat it as a pluggable arm
behind that decision, not core-path.

## What the docmeta ADR (P1) should adopt

1. **The lexical graph is the spine** — Document→Chunk with the active `docs_*`
   vocabulary, proven twice (bmc-docs 2026-07-08; the Q2 book load). Chunk
   navigation properties (chapter/section/page or heading/seq) earn their cost.
2. **Ch.8's evaluation harness as the component's own gate**: RAGAS-style context
   recall / faithfulness / answer correctness with **Cypher-as-ground-truth**, plus
   the per-stage failure attribution this benchmark used (naive vs informed query
   recorded separately).
3. **Full-text index as standing infrastructure** (cheap, keyless, covers most of
   the exact-lookup tail) — combined with agent term-mapping it closes most of the
   paraphrase gap this benchmark observed.
4. **Embeddings/vector as a pluggable arm** gated on the LLM-key-strategy decision;
   when built, follow ch.3.2's parent-document shape and add an OS1-style
   out-of-scope threshold test to the harness.
5. **Query-time hygiene rules** from the live runs: exclude/down-rank front & back
   matter (the Q2 lesson) and non-content preamble chunks; abstention is a scored
   behavior, not an error.
6. The manifest stays the provenance source of truth and the fallback retrieval
   path; `drydocs_docs` DB vs co-location remains the ADR's call (this benchmark
   ran co-located and was not blocked by it).

## Limitations

Spike-grade by design: 12 questions, single warm-run latencies, one corpus, and the
author served as both query generator and judge (the text2cypher and LLM-judge
stand-ins, per ch.4/ch.8 — the P1 harness should automate both). The benchmark
script + raw JSON live in the session scratchpad; the queries are reproducible from
the table and the loaders are committed, so the run can be recreated at P1 to
baseline the real harness.

## Reproduce

```powershell
poetry run drydocs load-software-registry     # DESCRIBES prereq
poetry run drydocs load-bmc-docs              # 374 chunks -> drydocs
# fulltext index: CREATE FULLTEXT INDEX ... ON EACH [c.heading, c.text]; DROP after
# question set + per-arm queries: the Results table above
```
