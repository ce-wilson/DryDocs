# DryDocs — project plan (context-graph restructure)

**Target repo:** https://github.com/ce-wilson/DryDocs.git
**Viewpoint:** production support / development support throughout.
**Date:** 2026-06-20

> **Phase authority note (2026-07-22).** This doc is the founding narrative for phases 0–5.
> The **authoritative, current phase list** is `plan.phases` in
> [`backlog.yaml`](backlog.yaml) (rendered on [`docs/plan/board.html`](../plan/board.html)),
> which has since grown through phase 13+ (component topology, review back-flow, release
> infra, attribution, doc infra, governance ledgers, web console, runtime topology).
> Phases 0/1/3 are done; 2 re-opened for C5; 4–5 pending. New phases are proposed through
> the groom loop, never added here.

## Goal

Re-found DryDocs on the four-layer model (taxonomy → ontology → knowledge graph → context
graph), with a clean external/internal split, a configuration-driven pipeline, and an SME
guided gate — so that lower-cost sub-agents can implement work units safely.

> **Architecture decisions** live in [`docs/decisions/`](../decisions/README.md) (ADR index) —
> including the **rejected alternatives** (Community single-DB, two-`--mode` capability,
> polyrepo) with the structural reasons they fell, so they are not re-litigated here.

## Phases

### Phase 0 — Restructure scaffolding ✅ (done in this change)
- Four-layer model documented (`00-conceptual-model.md`).
- External reference made symmetrical: `reference/` (platforms + standards + research) and
  `external/orchestration/` (BMC baseline + AutoSys/Airflow placeholders). `vendor/` retired.
- Configuration layer created (`config/`: precedence, source-registry, taxonomy-ontology-map).
- Publish boundary defined (`PUBLISH-BOUNDARY.md`, `internal/`).
- Sub-agents defined (`.claude/agents/`), routing brain written (`CLAUDE.md`).
- HITL SME flow defined (`03-hitl-sme-flow.md`).

### Phase 1 — Taxonomy capture (sub-agents: taxonomy-importer)
Import the existing live sources into `config/taxonomy/` as pure classification: Control-M
folders/jobs/conditions, SEAL applications/ports, Catalog LOB→Product→Team. Backfill — these
already load, but capturing them as taxonomy makes the ontology mapping auditable.
**Gate:** each taxonomy file faithful to source; no meaning edges. **Acceptance:** counts match
the live loaders' sample output.

### Phase 2 — Ontology mapping + HITL (sub-agents: ontology-mapper)
For each captured taxonomy, draft `taxonomy-ontology-map.yaml` entries (PROV matrix / standards),
run the guided gate, mark confirmed. Reconcile the existing `relationship_vocabulary.yaml`
`planned` entries through the same gate so the registry and the map agree.
**Gate:** every active graph edge type traces to a confirmed mapping. **Acceptance:**
`test_schema.py` drift guard green; map `summary:` matches vocabulary `status: active`.

### Phase 3 — Configuration-driven loaders (sub-agents: pipeline-config + loaders)
Make loaders read `config/` for precedence + source selection instead of hardcoding. Wire the
precedence resolver (BMC baseline → internal standards → LOB→Product→Team) into the
reconciliation steps (e.g. catalog `RECONCILES_TO`).
**Gate:** no precedence logic hardcoded in loaders. **Acceptance:** changing `precedence.yaml`
changes resolution with no code edit; tests green.

### Phase 4 — Context graph (layer 4) pilot (main session + ontology-mapper)
Introduce SOSA/SSN observation modeling for one production-support question (e.g. "current
health + freshness of folder X"). Register `sosa:*` terms via the gate; build the
`ControlMJobRun` → observation projection. This is the genuinely new capability.
**Gate:** SOSA terms registered before any label written. **Acceptance:** one context query
answers a real support question end-to-end on sample data.

### Phase 5 — Orchestrator expansion (sub-agents: pipeline-config)
Activate AutoSys and/or Airflow: complete crosswalk → HITL confirm → `confirmed: true` → loader
emitting baseline types only.
**Gate:** crosswalk confirmed; no new concepts invented. **Acceptance:** sample AutoSys/Airflow
data lands as baseline `ControlMJob`/`ControlMFolder`/`Condition` nodes.

## Sequencing
```
Phase 0 (done)
   ├─▶ Phase 1 (taxonomy capture) ─▶ Phase 2 (ontology + HITL) ─▶ Phase 3 (config-driven loaders)
   │                                          └─▶ Phase 4 (context graph pilot)
   └─▶ Phase 5 (orchestrator expansion)  [needs Phase 2 mapping discipline; otherwise parallel]
```

## Carry-over from the prior consolidated plan
The existing `docs/reviews/drydocs-consolidated-plan.md` streams (Oracle ingestion, graph-schema
fixes B.1–B.8, data-catalog C.1–C.6) remain valid and slot under Phases 2–3 here. The
`RUNS_ON→SCHEDULED_ON` (B.1), `datetime()` (B.3), and stale-edge-cleanup (B.2) P0 fixes are
prerequisites for any production load and should land first within Phase 3.

## Definition of done (restructure)
- A new contributor (or sub-agent) can read `CLAUDE.md` and know which layer/reference/agent
  applies to any task.
- No graph edge exists without a confirmed taxonomy→ontology mapping.
- The repo can be published by excluding `internal/` with zero confidential leakage.
