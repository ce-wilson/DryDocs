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

## 2026-07-07 — Control-M Q1–Q3 resolutions + phase-1 load scope (controlm-q1q3-phase1)
- **Presented:** 15 confirmations across 4 sections (gate page
  `config/gate-prompts/controlm-q1q3-phase1.yaml`, first use of the meta + provenance
  source-vs-derived renderer). **SME accepted the page in full** (chad.wilson).
- **Confirmed: 15 · Edited: 0 · Rejected: 0.** Key decisions:
  - **Q1 joins:** conditions (LNKI/LNKO) + SETVAR extracts join `CM_DEF_VJOB` in SQL
    (current-version guaranteed in-extract); folder header rows = `JOB_ID=1` / SMART Table.
    Two-pass load: pass 1 = folder+job nodes, pass 2 = dependencies via recursive
    in/out-condition query.
  - **Q2 audit envelope:** `CREATION_USER/CREATION_DATE` + `CHANGE_USERID/CHANGE_DATE`;
    `VERSION_USER/VERSION_TIMESTAMP` duplicate the CHANGE pair — excluded. `USER`=`USER_ID`.
    Trailing-'p' SID strip approved as a *derived* property. `IS_CURRENT_VERSION` needs a
    domain-value probe before it stays a hard filter (legacy-folder caveat).
  - **Q3 labels:** two-labels-per-folder-row confirmed (`ControlMFolder` + one
    `ControlMServer` per unique `DATA_CENTER`). **New label `ControlMApplication:Collection`**
    (Control-M grouping ≠ business `:Application`); **new edge `CONTAINS_FOLDER`** registered
    `m3_contains_folder status: planned`; map entry `application-contains-folder` confirmed.
    Variables stay staging-only (node-vs-property deferred).
  - **Phase-1 scope:** initial load = active folders only (`USER_DAILY IS NOT NULL`) as a
    readability choice, NOT semantics (manual-order/-PRPL folders run in production; support
    ownership = escalation-DB rule). `CTLM_ID` (`TABLE_ID||'.'||JOB_ID`) approved as derived
    identity alongside the `(folder_id, job_id)` key. `MEMNAME` demoted to informational.
- **Effect:** loader changes (VJOB joins, audit-envelope projection, ControlMApplication
  MERGE) are ungated; 06a updated with the resolutions.

## 2026-07-08 — SEAL ontology reshape + scraped-docs source-of-record (GATE-BOUND, PENDING)
- **Presented:** draft only — the `ontology-mapper` has drafted the proposal per the 2026-07-08
  review write-ups (`knowledge/upgrade-plans/docmeta-component.md` top callout, `git-readme.md`
  heads-up bullet, `docs/restructure/IDEAS.md` 2026-07-08 [question] entry). The gate page
  (`config/gate-prompts/seal-tom-attribution-reshape.yaml`, 7 sections A–G) has NOT yet been
  reviewed by an SME. **STATUS: PENDING SME CONFIRMATION.**
- **Items drafted (all `status: proposed` / `status: planned` — nothing applied, nothing
  active flipped):**
  - **(a)** `:Application` node reclass: `prov:SoftwareAgent` → `prov:Entity`/`dprod:DataProduct`
    — recorded as `proposed_reclass` note on `relationship_vocabulary.yaml#node_classifications
    #Application`; the live `class`/`prov_type` fields are untouched (still SoftwareAgent/Agent).
  - **(b)** SEAL Technical Operating Model (TOM) role-holders (cto, application_owner,
    information_owner, data_owner, operate_manager, risk_compliance_officer) re-shaped as
    attribution on the asset: `prov:wasAttributedTo` (simple) + `prov:qualifiedAttribution` +
    `prov:agent` + `prov:hadRole` (reified) against a new `TOMRole` (`skos:Concept`) vocabulary,
    distinct from `:Role` (`org:Role`, PAT hierarchy only). New `status: planned` vocabulary
    entries: `seal_had_primary_source`, `seal_app_attributed_to_employee`,
    `seal_qualified_attribution`, `seal_attribution_has_agent`, `seal_attribution_had_role`; new
    `node_classifications` entries `Document`, `Attribution`, `TOMRole`.
  - **(c)** Proposed deprecation of `seal_has_membership` / `seal_of_role` / `seal_held_by`
    (org:Membership/org:Role pattern) — recorded as `proposed_deprecation` notes; all three stay
    `status: active`. `seal_has_port` (dprod) explicitly KEPT, untouched.
  - **(d)** `prov:hadPrimarySource` (Entity→Entity, sub-property of `wasDerivedFrom`) registered
    for scraped SEAL/PAT page → extracted fact provenance (depends on the future
    `drydocs-docmeta` component, not yet built).
  - **(e)** SEAL/PAT proposed as the source-of-record authority for internal product/business
    identity — recorded in `config/precedence.yaml#proposed_additions` as a documented block
    OUTSIDE the live `order:`/`active:` chain the resolver reads; no ranking/activation change.
  - **(f)** K1/K2 (`job-seal-app-ref` / `m3_seal_app_ref`, `job —wasAssociatedWith→ Application`)
    re-opened: annotated with a `type_conflict_note` (wasAssociatedWith requires an Agent target;
    no longer type-checks once (a) is confirmed) and a `proposed_reshape` (two undecided
    candidates: `USED` vs. a local domain edge) — kept `status: proposed`.
- **New map entries (`config/taxonomy-ontology-map.yaml`, all `status: proposed`):**
  `application-as-dataproduct`, `seal-tom-attribution`, `seal-doc-source-of-record`. Summary
  counts updated: `proposed: 3 → 6`; `applied`/`confirmed`/`rejected` untouched.
- **Verification:** no `status: active`/`confirmed` entry was flipped in either
  `relationship_vocabulary.yaml` or `config/taxonomy-ontology-map.yaml`; every new vocabulary
  entry carries `supplement: ~` / `loader: ~` (no supplement/loader claims for a planned-only
  proposal — the drift guard `test_vocabulary_active_entries_declared_in_supplements` only checks
  `status: active` entries, so it is unaffected); `config/precedence.yaml`'s live `order:`/
  `active:` block (read by `PrecedenceResolver`) is unchanged — the new authority lives in a
  separate `proposed_additions` key the resolver never reads.
- **Next step:** an SME must review `config/gate-prompts/seal-tom-attribution-reshape.yaml`
  (sections A–G) and record Confirm / edit / reject per item. Nothing here is confirmed until
  that review happens and this entry is updated (or a follow-up entry added) with the outcome.

## 2026-07-08 — bmc-docs lexical load (bmc-docs-lexical-load)
- **Presented:** 13 confirmations (gate page `config/gate-prompts/bmc-docs-lexical-load.yaml`;
  sections: A source+scope, B lexical model, C trust tiers, D software-ontology hook, E sign-off)
- **Confirmed:** 13 — SME acceptance 2026-07-08 ("I accept").
- **Edited:** 0 · **Rejected:** 0
- **Decisions now binding:**
  - Node types `Document` + `Chunk` = `prov:Entity`; llm-graph-builder lexical model
    (H2 chunking, seq-0 preamble; deterministic, no LLM/embeddings).
  - `PART_OF` (dcterms:isPartOf pattern), `FIRST_CHUNK`/`NEXT_CHUNK` (null-term sequence,
    out-degree <= 1) — structural, deliberately NOT prov:hadMember.
  - `DESCRIBES` (Document -> SoftwareProduct) = dcterms:subject / foaf:primaryTopic pattern,
    NOT wasDerivedFrom; `target_version` on the edge; vendor hop rides MADE_BY.
  - Per-chunk trust tier VERBATIM|GROUNDED|SYNTHESIZED per the SOURCE-MANIFEST default rule
    (tier_rule stamped); SYNTHESIZED never vendor ground truth; api-* files load unspecial-cased.
  - Load order: software registry FIRST; DESCRIBES MATCHes the product, never MERGEs.
  - Documents co-locate with the registry nodes (in-DB DESCRIBES); a dedicated docs DB is
    the docmeta component's future call.
- **Transcription:** vocabulary `docs_describes`/`docs_chunk_part_of`/`docs_first_chunk`/
  `docs_next_chunk` planned -> active (supplement: ontology_supplement.cypher, loader:
  bmc_docs.cypher); 4 map entries confirmed; source `bmc-docs` confirmed: true.

## 2026-07-09 — CM_HOSTS host topology (controlm-hosts-topology)
- **Presented:** 18 confirmations (gate page `config/gate-prompts/controlm-hosts-topology.yaml`;
  sections: A naming, B resolution rule, C data-center normalization, D use case, E sign-off)
- **Confirmed:** 18 — SME acceptance 2026-07-09 ("I've reviewed and agree / sign off").
- **Edited:** 0 · **Rejected:** 0
- **Decisions now binding:**
  - New label `ControlMHostGroup` (prov:Collection) for CM_HOSTS.GRPNAME groups; member hosts
    REUSE `ExecutionHost` (one node per distinct NODEID). "ControlMGroup" rejected as a name —
    collides with the CM_DEF_VJOB.GROUP_NAME application-group concept.
  - NODE_ID resolution rule: GRPNAME match → `RUNS_ON {role: host_group}` (2-hop via
    CONTAINS_HOST); member-NODEID match → `RUNS_ON {role: agent_host}` (1-hop hard-coded);
    GROUP MATCH WINS (mirrors Control-M's own resolution); UNMATCHED reported as coverage,
    never guessed; NULL NODE_ID → no edge. Rerun host-affinity deferred to phase-2 runtime.
  - `CONTAINS_HOST` = prov:hadMember (CONTAINS_JOB family), carries participation_type +
    last_capture_date.
  - Section C resolved via the EXISTING internal standard
    `knowledge/standards/technology/data-center-naming-convention.md` (tier-2, SME-asserted
    2026-06-11): DC name = `<env><instance>-E<hhmm>-<suffix>` — P = Production, E#### =
    default execution time (EST) applied when a folder declares no time, suffix ignored.
    The standard's observed inventory shows LONG-FORM names are the native DATA_CENTER
    values → ControlMServer key rule = exact long-form match, parsed segments
    (environment, instance, default_time) as candidate properties.
  - Use case: server-patching / maintenance-window planning; timing half depends on the
    planned temporal runtime supplement (cm_avg_run) — separate pass, not this gate.
- **Residual verifications before the loader ships (not new decisions):**
  1. P3 probe (adhoc/profile_cm_hosts.sql) — confirm CM_HOSTS vs CM_DEF_VTAB DATA_CENTER
     value domains actually match exactly.
  2. DC scope call — load all 22 data centers or production-only (`P` prefix); the 22
     observed (vs 4 production) supports the standard's open item 1 (environments beyond P).
  3. P4 resolution census — BOTH-match collisions expected zero; P2a participation-type domain.
- **Transcription:** 3 map entries (`job-runs-on-host-group`, `host-group-contains-host`,
  `host-group-defined-on`) proposed → confirmed; vocabulary terms stay `status: planned`
  (correct lifecycle — supplement/loader not yet built); CM_HOSTS extract stays staging-only
  until the hosts loader + RUNS_ON resolution pass are built against these decisions.
