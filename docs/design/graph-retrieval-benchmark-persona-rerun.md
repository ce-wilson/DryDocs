# The Persona Re-Run — What the 12/12 Looks Like Without the Author in the Loop

**Explainer · Rev 1 · 2026-08-19 · backlog Q19 · Classification: Internal-Public
(mechanism only — no customer names, hosts, schedules, SIDs, or real identifiers appear in
this document).**

> The P0 benchmark's headline — *traversal won 12/12* — carried two disclosed caveats: the
> author hand-wrote the Cypher (as a text2cypher stand-in) and the author judged the
> answers. On 2026-08-19 we re-ran the same 12 questions against the same corpus with a
> real persona in the loop: an agent that saw only the schema and the question, generating
> its own Cypher, scored by the original regex ground truths with no human judge. The
> SME's prompt for this run: *"the accuracy was 100% in the graph, but in practice our own
> personas are not getting that close based on the last few days of gotchas."* This
> document reports what the gap actually is — and it is not where the caveats pointed.
> The parent explainer is
> [`graph-retrieval-benchmark-explainer.md`](graph-retrieval-benchmark-explainer.md); the
> persona queries, runner and raw results are committed beside the originals in
> `knowledge/upgrade-plans/p0-benchmark/`.

<!-- anchor: headline -->
## 1. The headline: recall held, efficiency did not

**Persona recall: 11/12 mechanical.** Original hand-written traversal on the *same
mechanical rule*: **10/12**, published as 12/12 after two disclosed author adjudications.
So on the only apples-to-apples comparison available — the mechanical scorer both runs
share — the persona *matched* the hand-written queries within one question, in both
directions.

**The gap the stand-in actually hid is context volume.** The persona retrieved
**102,060 chars (~25.5k tokens)** of context across the 12 questions where the
hand-written queries retrieved **15,354 (~3.8k tokens)** — **6.6× more**. Not knowing
the corpus, the persona compensated with breadth: `LIMIT 25`, multi-term `OR` clauses,
and whole-chunk excerpts. Every one of those choices is individually reasonable, and
collectively they spend the token-efficiency advantage that was the P0 verdict's second
headline (traversal at ~27× manifest efficiency). A persona in the loop keeps the
recall; it gives back a large slice of the efficiency.

| Q | Persona | Original (mechanical) | Persona chars | Original chars | Persona ms | Original ms |
|---|---------|----------------------|--------------:|---------------:|-----------:|------------:|
| SA1 | HIT | HIT | 149 | 67 | 215.6 | 110.4 |
| SA2 | HIT | HIT | 206 | 179 | 39.8 | 49.2 |
| EL1 | HIT | HIT | 2,482 | 3,526 | 75.0 | 51.7 |
| EL2 | **miss** | HIT | 882 | 1,312 | 82.1 | 20.1 |
| EL3 | HIT | HIT | 6,535 | 1,750 | 65.5 | 76.0 |
| PC1 | HIT | HIT | 20,434 | 1,309 | 68.7 | 48.8 |
| PC2 | HIT | HIT | 19,372 | 2,086 | 46.0 | 74.8 |
| PC3 | HIT | HIT | 9,933 | 2,118 | 50.3 | 75.0 |
| MD1 | HIT | **miss** (adjudicated ✔) | 14,364 | 446 | 82.5 | 108.5 |
| MD2 | HIT | HIT | 3,684 | 1,506 | 78.9 | 97.7 |
| PV1 | HIT | **miss** (adjudicated ✔) | 24,017 | 1,053 | 105.9 | 81.1 |
| OS1 | abstain ✔ | abstain ✔ | 2 | 2 | 49.3 | 16.5 |
| **Recall** | **11/12** | **10/12 mech · 12/12 adj** | **102,060** | **15,354** | med 74 | med 75 |

Latency is a wash — median 74ms vs 75ms, single warm runs, spike-grade.

<!-- anchor: el2 -->
## 2. The persona's one miss — and why it was not adjudicated up

**EL2 ("What does the ctmcreate utility do?") is the informative failure.** The persona's
query found the *right chunk* — the general-parameters chunk whose text defines
`ctmcreate` — and then handed over `left(c.text, 600)` as the excerpt. The term first
appears at **character 891**. The persona located the answer and truncated it out of the
context it returned; a downstream answerer reading the persona's output could not answer
the question.

The original hand-written query used a **1,200-character window** on the same chunk
family, comfortably past 891. That is not a coincidence and it is not cheating — it is
what a stand-in author does without noticing: **sizes the window to where the answer is,
because they know where the answer is.** The persona did not know, chose 600, and lost
the answer. This single question is the caveat made concrete.

**Adjudication considered and DECLINED, recorded per the P0 discipline.** The original
run's two adjudications (MD1, PV1) corrected a *scorer artifact*: the hand-written
queries returned correct answers — document lists, counts — whose output columns did not
echo the marker literal. The content handed to an answerer was sufficient; the regex was
looking in the wrong place. EL2 is the opposite class: the context handed to an answerer
is genuinely missing the answer. Scoring it up would erase exactly the persona behavior
this run exists to measure. Mechanical 11/12 stands.

There is a symmetric footnote on the other side of the table: the persona "won" MD1 and
PV1 mechanically by returning enormous windows (14k and 24k chars) that happened to
contain the marker literal. Breadth rescued the regex there the same way narrowness
killed it on EL2. Recall numbers this close are best read as *equal, with different
failure surfaces* — which is precisely the answer to the SME's question.

<!-- anchor: gotchas -->
## 3. The motivating gotchas, now with a number

Two observations prompted Q19, and the run reproduces both mechanisms:

- **The Idea-128 GitNexus lesson** — a tool claimed epistemic `exact` with
  `impactedCount=1` while a plain grep found call sites it missed: *success-shaped output
  with the substance absent.* EL2 is that lesson in retrieval form. The persona's answer
  for EL2 *looks* complete — one row, the right document, a clean excerpt — and the
  substance (the `ctmcreate` definition) is not in it. Nothing in the output's shape
  distinguishes it from a correct retrieval; only the ground-truth check catches it.
- **The SME's persona misses** — *"our own personas are not getting that close."* The
  measured answer: on recall the personas ARE that close (11/12 vs 10/12 mechanical, on
  the friendliest corpus we have — small, clean, single-vendor). The practical gap that
  reads as "missing" in daily use is the other two columns: 6.6× context volume (an
  answer buried in 20k chars of near-miss chunks reads as a miss to a human skimming it)
  and the EL2 class, where the retrieval is right and the handed-over context still
  lacks the answer.

<!-- anchor: method -->
## 4. Method, exactly

- **Corpus:** `bmc-docs` — 27 documents / 374 chunks, the id deliberately retained at the
  2026-08-18 corpus-id rename so the P0 record stays citable. Same corpus, same 12
  questions, same markers.
- **Persona (acceptance a):** a Sonnet subagent in a *fresh context* — it never saw the
  hand-written Cypher, the markers, or this repo (0 tool uses in its transcript). Input:
  the live schema (labels, properties, relationships, pulled from the database that
  morning) and the 12 question texts. Output: one read-only Cypher per question,
  committed verbatim as `persona_queries.json`.
- **Grading (acceptance b):** mechanical — `benchmark_p0_persona.py` executes each query
  inside `execute_read` (a write attempt fails rather than writes) and applies the
  original regexes unchanged. OS1 scores correct on abstention (empty result). No human
  judge; the one adjudication candidate is recorded and declined in §2, not applied.
- **Venue (J18):** desktop, Neo4j 5.26.27, database `drydocs`. Single warm runs;
  latency is spike-grade, not a load test.
- **Scope fences (acceptance e):** this is a throwaway spike beside the original, not a
  harness — O31 remains open and unblocked by this run, and `GRADES.md`'s re-run
  prerequisite belongs to the graph-vs-files code-graph experiment, untouched here.

<!-- anchor: verdict -->
## 5. What this changes

The P0 verdict — build docmeta, bet on traversal — **survives, with its second headline
revised**. Traversal's recall advantage is real and persona-robust. Traversal's token
advantage is not free: it was partly an artifact of author-written queries, and a real
persona spends a large fraction of it on breadth. Anyone quoting "~27× token efficiency"
should quote it as the *hand-written ceiling*, with ~4× less as the measured persona
floor on this corpus — and anyone building the answering side should assume the EL2
class exists: retrieval that is right, context that is wrong, and output whose shape
cannot tell you.
