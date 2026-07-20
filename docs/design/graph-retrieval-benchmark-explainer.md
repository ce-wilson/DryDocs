# Why We're Betting on Graph Traversal — A Retrieval Benchmark, Explained

**Explainer · Rev 2 · 2026-07-17 · commit `0e036ff` · Classification: Internal-Public
(mechanism only — no customer names, hosts, schedules, SIDs, or real identifiers appear in
this document).**

> On 2026-07-16 we ran a head-to-head benchmark of three ways an AI support agent can
> retrieve knowledge from our vendor documentation corpus, and the result — *"traversal
> won 12/12 at ~27× manifest token efficiency"* — decided that DryDocs will BUILD its
> document-ingestion component rather than shrink it. This document explains what that
> sentence means, how the test was run, and why the outcome matters for anyone building
> or supporting AI-assisted operations. The full scoring record is
> [`knowledge/upgrade-plans/docmeta-p0-verdict.md`](../../knowledge/upgrade-plans/docmeta-p0-verdict.md);
> the script and raw results are committed beside it.

<!-- anchor: the-question -->
## 1. The question we needed to answer

When a batch job fails at 3 a.m., a support engineer asks questions like *"what does the
%%LIBMEMSYM variable do?"*, *"how do I make a job wait for another job?"*, or *"which
documents cover pool variables?"*. DryDocs wants an AI agent to answer those questions
from the vendor's own documentation — in our case, a corpus of 26 Control-M reference
documents (about 313,000 characters) that we converted to markdown and govern with
per-chunk trust labels.

There are three fundamentally different ways to hand that corpus to an agent, and they
have very different costs. Before investing in a full document-ingestion component
(internally: *docmeta*), we required a written verdict: does querying the documents **as a
graph** actually beat the simpler alternatives on our real support questions — or should
we shrink the plan to a simple file registry?

A quick vocabulary note for readers new to this space. A **token** is the unit language
models read and bill by (roughly 4 characters of text); everything an agent "reads" for a
question must fit in its limited context window, so retrieval cost is measured in tokens.
**RAG** (retrieval-augmented generation) is the umbrella term for fetching relevant text
and placing it in front of the model instead of hoping it memorized the answer.

<!-- anchor: three-strategies -->
## 2. Three retrieval strategies

**Strategy A — manifest-routed reading (today's baseline).** The corpus has a
human-maintained index file (the source manifest) describing what each document covers.
The agent reads the manifest, picks the likely file(s), and reads them whole. This is
what a capable AI agent does with a folder of markdown today. It works — but the unit of
retrieval is *the entire file*, and the agent pays for every character it reads.

**Strategy B — full-text search.** Build a keyword index (Lucene, built into Neo4j) over
the text and return the top-3 matching chunks. Cheap, fast, no external dependencies —
this is classic search-engine retrieval.

**Strategy C — lexical graph traversal.** Load the corpus into the knowledge graph as
structured data: each `Document` node connects to its `Chunk` nodes (one per section),
chained in reading order, each chunk carrying properties — its heading, its size, its
**trust tier** (VERBATIM / GROUNDED / SYNTHESIZED — is this the vendor's text, grounded
restatement, or our inference?), and a `DESCRIBES` edge to the software product it
documents:

```
(:Document {name, source_url})-[:FIRST_CHUNK]->(:Chunk {heading, text, tier, seq})
        │                                          │
        │                                     [:NEXT_CHUNK]->(:Chunk)-> …
        └-[:DESCRIBES {target_version}]->(:SoftwareProduct {id: "controlm"})
   every chunk also: (:Chunk)-[:PART_OF]->(:Document)
```

Retrieval is then a **Cypher query**: fetch exactly the chunks that answer the question,
or *compute over them* — count, group, filter by property. The document set stops being a
pile of files and becomes a database.

The industry name for Strategy C is **GraphRAG**, and our test design deliberately
follows the patterns in Neo4j's *Essential GraphRAG* book (which we also loaded into the
graph as a second corpus, as both a dry run and a source of evaluation practice).

<!-- anchor: the-test -->
## 3. The test

We wrote **12 fixed support questions** in six classes, chosen to represent what support
actually asks — not to flatter any one strategy:

| Class | Count | Example |
|---|---|---|
| Structure / aggregation | 2 | "How much of this corpus is SYNTHESIZED (our inference, not vendor text)?" |
| Exact lookup | 3 | "What does %%LIBMEMSYM do?" |
| Paraphrase / conceptual | 3 | "How do I make a job wait for another job?" (the docs say *prerequisite condition*, not "wait") |
| Multi-document | 2 | "Which documents cover pool variables?" |
| Provenance | 1 | "Are the JSON API examples vendor ground truth?" |
| Out-of-scope | 1 | An AutoSys question this corpus cannot answer — the *correct* response is to say so |

All three strategies ran **live** against the same corpus, freshly loaded into our local
Neo4j Enterprise container (374 chunks, zero rejects). Scoring was per question, per
strategy: did the retrieved context contain the ground-truth answer (**recall**), how
many characters did the agent have to ingest (**token cost**), and how long did retrieval
take (**latency**). A fourth strategy — vector embeddings, the other classic RAG
technique — could not run because we have no approved embedding key yet; it was assessed
analytically and is discussed in §6.

Honest-methods note, exactly as recorded in the verdict: this was a spike, not a lab
study. The author wrote the Cypher queries (standing in for the automated
text-to-Cypher layer a production agent would use) and served as the judge, both
disclosed; two traversal answers that the mechanical scorer missed (correct answers whose
output didn't echo the marker string) were adjudicated by hand and recorded as such.

<!-- anchor: results -->
## 4. What happened

| | Traversal (graph) | Full-text (top-3) | Manifest-routed reading |
|---|---|---|---|
| **Recall** | **12/12** — including correctly *abstaining* on the out-of-scope question | 7/12 | 10/12 (2 partial) |
| **Total context ingested** | ≈16,400 chars (**~4.1k tokens**) | ≈31,400 chars (~7.9k tokens) | ≈449,500 chars (**~112k tokens**) |
| **Median retrieval latency** | 75 ms | 12 ms | ~instant to route, then whole files to read |

That is where the headline comes from. **"12/12"**: graph traversal retrieved correct
answer context for every question, and was the only strategy with a perfect score.
**"~27× manifest token efficiency"**: to answer the same 12 questions, the
manifest-routed baseline made the agent ingest ~449,500 characters of documentation —
about 27 times the ~16,400 characters traversal needed (per question the gap ranged from
28× to 60×).

Why the token number is the one to care about:

- **The costs are per question, and they pile up in the conversation.** No single answer
  fills the window — file-reading averaged ~9.4k tokens per question (worst case ~21k,
  a version question that read two whole files) versus ~340 for traversal. But in a
  continuous incident conversation, retrieved text doesn't vanish after each answer: it
  stays in the agent's history. Twelve file-read answers leave **~112k tokens of
  documentation riding along in context** — most of a typical window consumed before the
  incident's own logs and timeline are counted, and re-processed on every later turn.
  Traversal's residue after the same session: ~4.1k tokens.
- **Run stateless instead (a fresh call per question) and the window never fills — but
  the bill recurs.** Retrieval is re-paid on every question, every shift, forever, and
  the cumulative spend is the same 112k-vs-4.1k comparison. A 27× multiplier on the
  retrieval bill is the difference between an always-on assistant and a tool you ration.
- **Dilution is a quality problem, not just a cost problem.** A model handed 80,000
  characters to find one paragraph is measurably more likely to miss it than a model
  handed the right 1,500 characters. Smaller, better-targeted context is *more* accurate,
  not just cheaper.

<!-- anchor: only-the-graph -->
## 5. The four questions only the graph could answer

The most important finding is not the efficiency ratio — it is that **four of the twelve
questions were only answerable at all from the graph**: corpus structure ("largest
document?"), aggregation ("what share is SYNTHESIZED?"), the version property ("which
product version do these docs target?"), and per-chunk provenance ("is this specific
example vendor ground truth?").

The reason is structural. In a pile of files, "how much of this corpus is SYNTHESIZED" is
not written down anywhere — answering it means opening all 26 files and tallying by hand
(the baseline could only reply with *the rule* for how tiers are assigned, not the
numbers). In the graph, the trust tier is a **property on every chunk**, so the answer is
one aggregate query returning 179 characters in 49 ms. No amount of file reading competes
with that, because file reading would have to *rebuild the graph's job by hand on every
question*.

For a support organization, that class of question is not exotic. "Which of these answers
can I trust as vendor-verbatim?" is exactly what you ask before acting on an AI answer at
3 a.m. Governance questions are aggregate questions, and aggregate questions need a
database — which is what the graph is.

<!-- anchor: honest-limits -->
## 6. Where the graph has to be honest

**The paraphrase gap is real.** Support asks "make a job wait for another job"; the docs
say *prerequisite condition*. Two of the three paraphrase questions failed with naive
keyword matching inside Cypher and succeeded only after mapping support vocabulary to
document vocabulary — the graph is only as good as the query layer in front of it. Our
existing mitigation is that the graph carries its own schema and terminology inventory
for the agent to consult; the long-term answer is the next paragraph.

**Vector embeddings are the named missing arm.** Embeddings — the other classic RAG
technique, which retrieves by *meaning* rather than by keyword — are precisely what
closes the paraphrase gap. We could not run them (no approved embedding key yet — an open
decision, not an oversight), so the plan treats vectors as a **pluggable arm behind that
key decision**: expected to improve paraphrase recall, and expected to need a
guard-threshold, because vector search *always returns nearest neighbors* — even for
questions the corpus cannot answer.

**Which is the other lesson: abstention is a feature.** On the out-of-scope AutoSys
question, traversal returned empty (correct — the graph is scoped, so "no rows" is an
honest "not covered here") and the manifest router also declined. Full-text returned
3,700 characters of *confident, irrelevant* Control-M text — for a support agent, the
single worst failure mode, because confident noise at 3 a.m. becomes a wrong action. Any
retrieval component we ship scores abstention as a first-class behavior.

**And the caveats stay attached:** 12 questions, one corpus, single warm-run latencies,
author-as-judge. Spike-grade evidence for a build/no-build decision — not a published
benchmark. The committed script and loaders make the run repeatable, and the component's
first milestone includes an automated evaluation harness so future numbers don't depend
on anyone's judgment.

<!-- anchor: what-we-build -->
## 7. What we're building because of this

The verdict — **BUILD** — translates into a component design with clear roles rather
than a single retriever:

1. **The lexical graph is the spine.** Document→Chunk with governed trust tiers, proven
   twice now (the Control-M corpus and the GraphRAG book load).
2. **Full-text search stays as standing infrastructure** — keyless, ~10 ms, covers most
   exact-term lookups — as the keyword half of a future hybrid, never the sole retriever.
3. **Vector embeddings plug in when the key decision lands**, with an out-of-scope
   threshold test in place from day one.
4. **An evaluation harness becomes part of the component itself**: fixed question sets,
   Cypher-as-ground-truth, recall/faithfulness scoring — so every future retrieval change
   re-runs this benchmark automatically instead of relying on a one-time spike.
5. **The human-maintained manifest remains the provenance source of truth** and the
   fallback path. The graph doesn't replace the governance surface; it makes it queryable.

For the support workflow, the practical promise is this: the agent answering your 3 a.m.
question reads *tens of times less* text per answer, can tell you *how trustworthy* each
answer is (because trust is data, not vibes), and says *"that's not in scope"* instead of
guessing — and each of those three properties was demonstrated live, not asserted.

<!-- anchor: read-more -->
## 8. Read more / reproduce

| If you want… | Read / run… |
|---|---|
| The full scoring tables + per-question adjudication | `knowledge/upgrade-plans/docmeta-p0-verdict.md` |
| The benchmark script + raw mechanical results | `knowledge/upgrade-plans/p0-benchmark/` |
| The GraphRAG pattern inventory behind the test design | `reference/research/essential-graphrag-notes.md` |
| The traversal dry-run on the book corpus (7/7) | `docs/reviews/essential-graphrag-traversal-experiment.md` |
| The component plan this verdict un-gates | `knowledge/upgrade-plans/docmeta-component.md` |
| Reproduce the corpus load | `poetry run drydocs load-software-registry` then `poetry run drydocs load-bmc-docs` (374 chunks) |
