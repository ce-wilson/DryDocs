# Incremental Context-Loop Plan — AI-supplemented SDLC Knowledge/Context Graph

> Machine-first continuation artifact. Resume from the latest unchecked loop in §LOOPS.
> Regenerated from `FCD-Requirements.doc.txt` (2018 intent) + context-graph research
> (`reference/research/README.md`, `docs/restructure/00-conceptual-model.md`).
> Persona for any agent resuming this: expert in SDLC, data warehousing, and AI/LLM systems.

## §INTENT

Original idea (Full Circle Docs, 2018): convert waterfall requirements + documentation +
code into a **knowledge graph with full traceability** (requirement → process → code →
table/proc → test case → release), reducing documentation effort by editing *deltas* against
a versioned graph instead of rewriting whole documents.

What changed since 2018:
- Teams moved to **Agile** without learning to document "just enough."
- **Jira story content is now the de-facto project plan** — but thin and unstructured.
- The real SDLC artifacts (requirement discussions, SLAs, decisions, approvals) live in
  **email / chat**, not in any document repository.
- New practices exist that are inherently structured: **BDD/Cucumber (Gherkin)**,
  conventional commits, PR templates, CI logs.

Core thesis to evaluate: **we will not make humans document more.** Instead, **AI agents
supplement the SDLC and document as work happens** — extracting structured traceability from
the byproducts teams already produce (stories, commits, PRs, Gherkin, email threads), and
writing it into the graph.

Goal of this artifact: review that idea for **feasibility** and **use cases**, and — because
the corpus is too big to ingest at once — drive the work as **small, resumable loops**, each
saving its output here (or beside it) as a continuation checkpoint.

## §FEASIBILITY (verdict: feasible, with scope discipline)

> RESCOPED 2026-06-26 → see `feasibility-memo-context-sufficiency.md`. Real question: which dev
> method (Waterfall / Agile / BDD-Cucumber / Spec-Driven) deposits the **missing propositions —
> intent · requirements · use cases · test cases** — as machine-readable byproduct, enough for an
> agent to answer without hallucinating. Finding: the Agile user story adds no context; BDD + SDD
> are the adoption targets. Answered by the memo's §6 four-condition experiment. Table below is the
> layer-mapping background for that memo.


Mapped onto the DryDocs four-layer model (`00-conceptual-model.md`). The 2018 POC failed by
collapsing import and meaning into one step; this plan keeps them separate.

| 2018 FCD concept | DryDocs layer | Feasibility note |
|---|---|---|
| Import docs/code/schema as "base nodes" | **1 Taxonomy** | High. Pure classification, reversible. `taxonomy-importer` owns it. |
| Requirement→code→test "traceability" links | **2 Ontology** | Medium. These are *meaning* edges (PROV-O `wasDerivedFrom`/`used`/`wasGeneratedBy`); must go through `ontology-mapper` + HITL gate, never auto-invented. |
| The populated, queryable portal graph | **3 Knowledge graph** | High once 1–2 are confirmed; loaders write confirmed edges only. |
| "What matters right now for this change?" | **4 Context graph** | The genuinely new value. Task-scoped, time-aware projection (SOSA/SSN temporal + ownership + health). This is where AI-supplemented support pays off. |

Why feasible **now** when it wasn't in 2018:
- **LLM extraction** turns unstructured byproducts (email, story prose, commit messages) into
  candidate structured edges — the manual copy/paste bottleneck of the 2018 MVP is gone.
- **Graph-native catalog+glossary linked** is a validated pattern (NeoCarta, Neo4j Labs):
  metadata subgraph + glossary subgraph + hybrid vector/full-text retrieval. We borrow the
  *tool pattern*, not a new standard.
- **Query/orchestration logs as a lineage source** (NeoCarta infers JOIN lineage; we already
  derive lineage from Control-M conditions / script reads-writes) — extends to SDLC events.

Hard constraints / risks to respect:
- **R1 Meaning edges are not casual.** Any new relationship type → `RELATIONSHIP_GUIDE.md` +
  `relationship_vocabulary.yaml` + HITL gate, `status: planned` first. (CLAUDE.md §6)
- **R2 Sensitivity boundary.** Email/SLA/roster content is likely **Internal /
  Internal-Confidential** → `internal/`, excluded from public push. Set `classification` at
  ingestion; never commit real SIDs/credentials/PII. (CLAUDE.md §3)
- **R3 Trust axis.** Each ingested source needs VERBATIM/GROUNDED/SYNTHESIZED in its
  SOURCE-MANIFEST. AI-extracted edges are SYNTHESIZED and must be SME-confirmable.
- **R4 Hallucinated traceability is worse than none.** Every AI-proposed edge stays a
  *candidate* until confirmed; provenance (which source span produced it) is mandatory.
- **R5 Email ingestion** has the highest legal/privacy and signal-to-noise cost — defer past
  the first pilots; prove the loop on already-structured byproducts first.

## §USECASES (ranked by value × feasibility)

1. **Production-support "what matters right now"** (layer 4). Given a job/change, surface:
   what it depends on, who owns it, is the data fresh, who to call. Highest value; builds on
   layers 1–3 that already exist in DryDocs.
2. **Story → code → test traceability, auto-maintained.** Link Jira story ↔ commits/PRs ↔
   changed tables/procs ↔ Gherkin scenarios, extracted from byproducts, not hand-authored.
3. **Release / audit diff (SOX-style).** "What requirements, code, and tests changed between
   release N and N+1" — the 2018 Release Manager use case, now generated from the graph.
4. **QA coverage gap detection.** Which requirements/stories have no linked test case or
   Gherkin scenario; which changed code has stale tests.
5. **Decision/SLA recovery from email** (deferred, R5). Promote requirement-discussion and
   SLA threads into linked, classified evidence nodes.

## §APPROACH — incremental loop protocol

Each loop is small enough to run in one session and leaves a resumable checkpoint.

```
pick ONE narrow scope (1 story / 1 job / 1 question)
   → ingest its byproducts as TAXONOMY (classification only)      [taxonomy-importer]
   → AI-extract candidate MEANING edges, with provenance spans    [ontology-mapper, status: proposed]
   → HITL confirm / reject at the gate                            [03-hitl-sme-flow.md]
   → load confirmed edges                                         [loaders]
   → (optional) project the layer-4 "right now" view             [future]
   → record outcome + next scope in §LOOPS, snapshot, commit
```

Rules: stay inside one layer per step; never invent relationship types during import; set
`classification` on every source; keep AI output as candidates until confirmed.

## §LOOPS — checkpoint log (resume from first unchecked)

- [x] **L0 — Frame.** Feasibility + use cases captured (this file). DONE.
- [ ] **L1 — Pick the pilot scope (DECISION NEEDED).** Choose ONE:
      (a) one Jira story + its commits/PRs/Gherkin → traceability slice;
      (b) one Control-M job/change → layer-4 "what matters right now" slice;
      (c) one requirement-discussion email thread → decision/SLA recovery (highest risk, R5).
      Recommend **(b)** — it leverages the layers DryDocs already has and proves the highest-
      value use case fastest; defer (c).
- [ ] **L2 — Source inventory for the pilot.** List the concrete byproducts available for the
      chosen scope, set each source's `classification` and trust axis. No graph writes.
- [ ] **L3 — Taxonomy ingest.** Import the pilot's objects as pure classification into
      `config/taxonomy/`. Acceptance: nodes exist, zero meaning edges.
- [ ] **L4 — Candidate meaning edges.** AI-extract traceability edges with PROV-O typing and
      source-span provenance; write as `status: proposed` in `config/taxonomy-ontology-map.yaml`.
- [ ] **L5 — HITL confirm + load.** SME confirms/rejects; loader writes confirmed edges only.
- [ ] **L6 — Project + evaluate.** Answer the pilot's "right now" question from the graph;
      compare against ground truth; record precision of AI-proposed edges.
- [ ] **L7 — Decide scale-out.** Generalize the loop or adjust; promote to a backlog.yaml epic.

## §NEXTACTION

Resume at **L1**: confirm the pilot scope (recommend option (b) — one Control-M job/change).
Then produce, on request, either a formal feasibility memo or a concrete `backlog.yaml` entry
seeding L2–L3. Do not advance past a checkpoint without updating §LOOPS and committing.

## §REFS

- Intent: `SDLC-Docs/extracted/FCD-Requirements.doc.txt`
- Layer model: `docs/restructure/00-conceptual-model.md`
- Research: `reference/research/README.md` (Neo4j taxonomy/ontology/KG/context series; NeoCarta)
- Gate: `docs/restructure/03-hitl-sme-flow.md` · Backlog: `docs/restructure/backlog.yaml`
- Guardrails: `CLAUDE.md` §1 (layers), §3 (sensitivity), §6 (relationship discipline)
