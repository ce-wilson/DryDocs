# DryDocs — project plan (context-graph restructure)

**Target repo:** https://github.com/ce-wilson/DryDocs.git
**Viewpoint:** production support / development support throughout.
**Date:** 2026-06-20 · **Cut to the founding narrative 2026-09-02** (ADR 0018 Q2: this file
keeps what YAML cannot hold; the phases live where they are maintained).

> **Where the phases are.** The authoritative phase list is `plan.phases` in
> [`backlog/plan.yaml`](backlog/plan.yaml) — eighteen phases as of 2026-09-02, from
> restructure scaffolding through the mind-map — rendered with per-module build-out
> judgments on [`docs/plan/roadmap.html`](../plan/roadmap.html) and with the live item counts
> on [`docs/plan/board.html`](../plan/board.html). This file documented phases 0–5 as prose
> from 2026-06-20 to 2026-09-02 and stopped there while the YAML grew to 18; a narrative copy of
> a list that is maintained elsewhere is how a routing document misdirects (the tech-debt review
> of 2026-09-02, finding Doc2). New phases are proposed through the groom loop, never here.

## Goal

Re-found DryDocs on the four-layer model (taxonomy → ontology → knowledge graph → context
graph), with a clean external/internal split, a configuration-driven pipeline, and an SME
guided gate — so that lower-cost sub-agents can implement work units safely.

> **Architecture decisions** live in [`docs/decisions/`](../decisions/README.md) (ADR index) —
> including the **rejected alternatives** (Community single-DB, two-`--mode` capability,
> polyrepo) with the structural reasons they fell, so they are not re-litigated here.

## The founding shape, in one paragraph

Phase 0 laid the scaffolding — `CLAUDE.md` as the routing brain, the four layers, the
external/internal split, the sub-agents. Phases 1–3 were the pipeline in layer order: capture
taxonomy first (pure classification), apply ontology through the HITL gate second, load through
configuration-driven loaders third — "never invent a relationship type during import" was the
rule that ordered them. Phase 4 was the context-graph pilot (layer 4, task-scoped projections);
Phase 5 the orchestrator expansion (AutoSys, Airflow mapped to the BMC baseline). Everything
after phase 5 — component topology, the review back-flow, release infrastructure, attribution,
doc infrastructure, governance ledgers, the web console, runtime topology, docmeta, agentic
Q&A, self-documentation, the mind-map — was proposed through the groom loop and is recorded in
`plan.yaml` with its status, not here.

## Carry-over from the prior consolidated plan

The streams of [`docs/reviews/drydocs-consolidated-plan.md`](../reviews/drydocs-consolidated-plan.md)
(Oracle ingestion, graph-schema fixes B.1–B.8, data-catalog C.1–C.6) slotted under phases 2–3.
Their P0 fixes — `RUNS_ON→SCHEDULED_ON` (B.1), `datetime()` (B.3), stale-edge cleanup (B.2) —
were prerequisites for any production load.

## Definition of done (restructure)

- A new contributor (or sub-agent) can read `CLAUDE.md` and know which layer/reference/agent
  applies to any task.
- No graph edge exists without a confirmed taxonomy→ontology mapping.
- The repo can be published by excluding `internal/` with zero confidential leakage.
