# HITL gate log

Append-only audit of guided-gate runs (see `docs/restructure/03-hitl-sme-flow.md`). Each run
records the date, the item, confirmed / edited / rejected counts, and reasons for any rejection.

## 2026-06-21 — C1 · Control-M ontology mapping
- **Presented:** 4 (batch — all reuse `status: active` vocabulary terms from the M3 model)
- **Confirmed:** 4 — `folder-scheduled-on`, `job-requires-in-condition`, `job-emits-out-condition`,
  `job-was-informed-by`
- **Edited:** 0 · **Rejected:** 0
- **Notes:** `SCHEDULED_ON` confirmed with a **null PROV mapping** on purpose — `ControlMServer`
  is local infrastructure, not an Agent, so `prov:wasAssociatedWith` would be invalid.
  `Folder CONTAINS_JOB → prov:hadMember` was already `applied`/live and not re-gated.
  Confirmed by SME (Confirm all 4).

## 2026-06-21 — C2 + C3 · BusinessApplication + LOB→Product→Team
- **Presented:** 8 batch (reuse active vocab) + 1 decision (SUPPORTS range)
- **Confirmed (8 batch):** app-has-port, app-has-membership, membership-of-role, membership-held-by
  (C2 — DPROD/ORG); lob-has-product-line, product-line-has-product, product-has-dev-team,
  lob-reconciles-to-segment (C3 — local + skos:closeMatch)
- **Decision resolved (SME):** `SUPPORTS` range = **AreaProduct** (not Product) — Product reached
  via Product▸AreaProduct▸DevTeam; "aligned to" = `team_type=aligned`. PLUS a new edge:
  **DevTeam DEVELOPS BusinessApplication, joined by SEALID** (cross-source, via catalog↔SEAL
  ownership reconciliation). Both recorded `confirmed`.
- **Edited:** 1 (SUPPORTS retargeted + DEVELOPS added) · **Rejected:** 0
- **C4 follow-up:** set `catalog_supports_area_product` + `arch_develops` active in the
  vocabulary; deprecate `catalog_supports` (DevTeam→Product).

## 2026-06-21 — C4 · vocabulary reconciliation (no gate decisions)
- `catalog_supports_area_product` → **active** (SUPPORTS range = AreaProduct)
- `arch_develops` → **active** (DevTeam DEVELOPS Application by SEALID; added a `DEVELOPS`
  LocalRelationship block to `catalog_ontology_supplement.cypher` so the drift guard passes)
- `catalog_supports` (DevTeam→Product) → **deprecated** (kept for audit)
- Drift guard `test_schema.py` green (9 passed); full suite 164 passed.
- Phase-2 `planned` entries (m3_invokes/triggers, p2_*, …) left planned — no taxonomy captured
  yet, not re-gated. **Epic C complete (C1–C4).**

## 2026-06-26 — ADR 0002 · component & database topology (architecture acceptance)
- **Presented:** 1 ADR for acceptance (`docs/decisions/0002-component-database-topology.md`) +
  1 real sub-decision (Neo4j edition / license commitment).
- **Decision (SME):** **Accept as-is** — `PROPOSED → ACCEPTED`. D1 (Enterprise multi-DB +
  composite), D2 (two components: `drydocs-lineage` + `drydocs-deepdoc`), D3 (monorepo +
  `drydocs-core`) all confirmed.
- **Edition:** **Committed to Neo4j Enterprise** — accepted the recurring license cost; trust
  isolation is structural (separate transaction domains), the ADR's core value. Community
  single-DB stays a **rejected alternative** only (not an interim fallback).
- **Edited:** 0 · **Rejected:** 0
- **Effect:** the `drydocs-core` extraction (0002-A) and spinoff rebase (0002-B) plans are
  **ungated** (still `PLANNED`, now ready to execute). ADR follow-ups 1–6 ready to groom into
  `backlog.yaml`. Confirmed by SME (chad.wilson).
- **Note:** ADRs are architecture decisions, not taxonomy→ontology mappings — gated here by the
  same SME-control principle (`03-hitl-sme-flow.md`), logged for the same audit trail.

## 2026-07-07 — Plan 07 Phase 0 · software-registry terminology + vocabulary (ADR 0004)
- **Presented:** 5 items, all new types → all paused for individual decision (0 batched):
  ADR 0004 terminology bundle + 2 node classifications + 2 edges.
- **Decisions (SME, chad.wilson): 5× Confirm, 0 edited, 0 rejected, 0 skipped.**
  - ADR 0004 **ACCEPTED**: vendor = brand only; `SoftwareProduct.role` absorbs Tier-1/Tier-2;
    trust-axis prose drops "vendor's words"; `vendor-bmc` tooling id → `bmc-docs`.
  - `Vendor` = `org:Organization` (Agent); `SoftwareProduct` = `dd:SoftwareProduct` (Entity).
  - `MADE_BY` → `prov:wasAttributedTo` (Entity → Agent matrix row).
  - `USES_SOFTWARE` → local domain edge (`prov_maps_to: ~`; Agent → Entity has no PROV row;
    precedent `arch_contains`). Properties: version, source, status.
- **Effect:** plan-07 Phases 1 (registry seed + loader) and 2 (`bmc-docs` rename) are
  **ungated**. Vocabulary entries `reg_made_by` / `reg_uses_software` registered
  `status: planned` (supplement + loader land in Phase 1, per invariant 3).
