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

## 2026-07-10 — BusinessApplication entity-reshape gate — SIGNED OFF (K3; resolves the 2026-07-08 PENDING entry)
- **Gate:** `config/gate-prompts/seal-tom-attribution-reshape.yaml` (sections A–G). **SME: chad.wilson.**
  Backlog **K3** (renamed 2026-07-10 "SEAL entity-reshape" → "BusinessApplication entity-reshape gate").
- **§A — CONFIRMED.** `:Application` reclass `prov:SoftwareAgent` → `prov:Entity` / `dprod:DataProduct`.
- **§B — CONFIRMED, role model REVISED by the SME into two families at two node scopes:**
  - **SEAL Technical Operational Contacts** — attach to `:Application` via `prov:qualifiedAttribution` +
    `prov:hadRole` against the `TOMRole` skos scheme. **Complete + fixed** set: Application Owner,
    Primary Information Owner, Backup Information Owner (1–2 persons), CTO, Technology Risk & Controls,
    Design Authority, Operate Manager L1 / L2 (one or both; 1–3 persons for 24h / 2–3 locations).
    Multi-person roles ⇒ the **qualified/reified form is loaded** (simple `wasAttributedTo` optional/
    derivable). The spec's old flat 6 are subsumed: `data_owner` → Information Owner;
    `risk_compliance_officer` → Technology Risk & Controls; **Design Authority** is new.
  - **Product Cabinet** — a SEPARATE family on the PAT `:Product`/`:AreaProduct` scope (NOT on
    `:Application`): Area Product Owner (`:AreaProduct`, does not tie to an app), Product Owner,
    Product Architect, Tech Partner (**manages** the Application Owner), Data Owner (TOM Information
    Owner may report to it), Data Certifier (relates to the app Information Owner), Analytics Lead.
  - **CTO is in BOTH families** (the shared concept). **DevTeam→BusinessApplication is a matrix (M:N).**
  - **DECISION (SME "ok to split"):** the Product Cabinet is split to its own follow-up item + gate →
    backlog **K5**, keeping K3 scoped to the SEAL app reshape.
- **§C — CONFIRMED** (in line with §A): deprecate `seal_has_membership` / `seal_of_role` / `seal_held_by`
  for the qualifiedAttribution + hadRole pattern; `seal_has_port` KEPT.
- **§D — CONFIRMED:** add `prov:hadPrimarySource`; SME requires scraped source documentation to be
  **reachable and extracted for accuracy in DryDocs** → promotes `drydocs-docmeta` (Document/Chunk +
  scraper/extractor) from parked to a REQUIRED dependency of K3's provenance goal.
- **§E — DECIDED (flip):** now that `:Application` is an Entity, flip `arch_develops` from the local
  `(:DevTeam)-[:DEVELOPS]->(:Application)` (`prov_maps_to: ~`) to the PROV-valid inverse
  `(:Application)-[:WAS_ATTRIBUTED_TO {role: developed_by}]->(:DevTeam)` (Entity→Agent = `prov:wasAttributedTo`).
- **§F / K2 — DEFERRED:** the re-shape IS needed and in-scope (post-reclass `wasAssociatedWith` no longer
  type-checks), but the edge shape — (a) `prov:used` vs (b) a local `BELONGS_TO_APPLICATION` domain edge —
  is deferred to a K2 follow-up gate. `job-seal-app-ref` / `m3_seal_app_ref` stay `status: proposed`.
  K2's independent match-policy gate (`seal-attribution-match-policy.yaml`) is unchanged and still required.
- **NEW gate decision — label normalization:** alongside the class reclass, the node LABEL normalizes
  `:Application` → `:BusinessApplication` (the taxonomy concept name for internally-developed apps).
  Confirmed-direction; the label change is gate-bound and lands with K4.
- **§G — SIGNED OFF** (chad.wilson, 2026-07-10). **Confirmed: A, B, C, D · Decided: E (flip), label · Edited: 1 (§B two-family model + Product-Cabinet split) · Deferred: 1 (§F/K2 edge shape) · Rejected: 0.**
- **Lifecycle (per §G — flips are SEPARATE logged follow-ups, NOT applied in this commit):** this commit
  records the gate outcome (this entry) + K3 → done. The mechanical application of every flip — the
  `:Application` class reclass + label normalization, the `TOMRole` scheme + qualifiedAttribution
  supplement (planned→active), the three `seal_*` deprecations, `seal_had_primary_source` activation,
  the `arch_develops`→`WAS_ATTRIBUTED_TO` flip, the map entries `application-as-dataproduct` /
  `seal-tom-attribution` / `seal-doc-source-of-record` proposed→confirmed→applied (with `vocab_id` +
  `capture` per F5/C7), and the SEAL/PAT precedence wiring — is **backlog K4**. The Product Cabinet is
  **K5**. K2's edge shape stays deferred.

## 2026-07-14 — Airflow/MWAA → BMC baseline crosswalk gate — SIGNED OFF (F2)

- **Gate:** `config/gate-prompts/airflow-crosswalk.yaml` (17 confirmations), reviewed via the rendered
  page; **ACCEPTED IN FULL** (chad.wilson, 2026-07-14). Same-day pre-sign-off context (commit 9334bf3):
  row 8 split 8a/8b/8c at the SME wording review; Software/§A registry linkage added (the vendor/product
  remediation gap); registry rows `airflow`/`apache` created for it.
- **§A — CONFIRMED** (crosswalk-only scope; public concepts only; bmc-baseline stays authority 1).
  **Registration ratified:** SoftwareProduct `airflow` MADE_BY `apache` (ADR 0004, vendor = the brand).
  **MWAA disposition ratified:** NOT a separate product — stock Airflow object model, AWS-managed
  deployment.
- **§B — CONFIRMED.** Rows 2, 3 exact; rows 1, 4, 5, 6, 8a, 8c, 9, 10 approximate, caveats accepted.
  **Row 8a cardinality confirmed 1-to-many:** queue → `:ControlMHostGroup -[:CONTAINS_HOST]->
  :ExecutionHost` (the controlm-hosts-topology pattern, signed off 2026-07-09); hard-pinned worker =
  the 1-hop `RUNS_ON {role: agent_host}` case; never queue → single ExecutionHost.
  **DEFERRED: 3 open questions, all to loader design** (stay live in the crosswalk's `open_questions`,
  must be resolved before/with the future loader gate): row 5 (richer Condition property set for
  datasets), row 6 (per-operator INVOKES crosswalk table), row 8c (Connection target-system landing —
  DataAsset reference vs job properties).
- **§C — CONFIRMED NO-EQUIVALENT:** rows 7 (trigger-rule vocabulary), 11 (XCom — never modeled),
  12 (dynamic task mapping — the flagged drift risk), 8b (Pool → Quantitative Resource, unmodeled —
  never folded into ExecutionHost). Nothing silently approximated.
- **§D — SIGNED OFF.** **Confirmed: A, B, C · Deferred: 3 (§B rows 5/6/8c) · Edited: 0 · Rejected: 0.**
- **Lifecycle (applied in this commit):** `config/crosswalks/airflow-to-bmc.yaml` status proposed →
  **confirmed** (file-level + all 14 rows); source-registry `airflow-mwaa` → **confirmed: true**
  (source-row status ONLY — no loader exists; a loader must be implemented and separately gated before
  any load runs); backlog **F2 → done**. AutoSys (F1) unchanged — its gate remains pending.

## 2026-07-14 — AutoSys → BMC baseline crosswalk gate — SIGNED OFF (F1)

- **Gate:** `config/gate-prompts/autosys-crosswalk.yaml` (13 confirmations), reviewed via the rendered
  page; **ACCEPTED IN FULL** (chad.wilson, 2026-07-14). Same-day pre-sign-off context (commit 9334bf3):
  row 6 demoted exact → approximate at the SME wording review (machine: polymorphism); Software/§A
  registry linkage added; registry rows `autosys`/`broadcom` created for it.
- **§A — CONFIRMED** (crosswalk-only scope; public JIL concepts only; bmc-baseline stays authority 1).
  **Registration ratified:** SoftwareProduct `autosys` (Broadcom Workload Automation, formerly CA
  Workload Automation AE) MADE_BY `broadcom` — today's brand, per ADR 0004; the CA lineage is name
  history, not the vendor.
- **§B — CONFIRMED.** Rows 1, 3, 7 exact; rows 2, 4, 5, 6, 8, 9, 11 approximate, caveats accepted.
  **Row 6 polymorphism acknowledged** (demoted from exact 2026-07-14): machine: names a real machine
  (1-hop `:ExecutionHost`) OR a virtual machine load-balancing a host set — 1-to-many via
  `:ControlMHostGroup -[:CONTAINS_HOST]-> :ExecutionHost`, mirroring the controlm-hosts-topology
  group-match-wins resolution. **LIVE-EXPORT FOLLOW-UPS (2, before any loader):** row 6
  (virtual-vs-real discrimination needs insert_machine definitions), row 9 (authoritative status
  vocabulary needs a live export). **DEFERRED: 1** — row 4 (does d(file) need its own FileWatcher-job
  baseline mapping?). All three stay live in the crosswalk's `open_questions`.
- **§C — CONFIRMED NO-EQUIVALENT:** row 10 (global/box-scoped variables — never modeled via this
  crosswalk; any variable-graph need routes through ontology-mapper). Nothing silently approximated.
- **§D — SIGNED OFF.** **Confirmed: A, B, C · Deferred: 1 (§B row 4) · Live-export follow-ups: 2
  (§B rows 6/9) · Edited: 0 · Rejected: 0.**
- **Lifecycle (applied in this commit):** `config/crosswalks/autosys-to-bmc.yaml` status proposed →
  **confirmed** (file-level + all 11 rows); source-registry `autosys-export` → **confirmed: true**
  (source-row status ONLY — no loader exists; a loader must be implemented and separately gated
  before any load runs); backlog **F1 → done**. Epic F crosswalk gates now both signed off.

## 2026-07-14 — CM_AVG_RUN runtime-stats supplement gate — SIGNED OFF (P2)

- **Gate:** `config/gate-prompts/controlm-avg-run-supplement.yaml` (20 confirmations after the §B edit),
  reviewed via the rendered page; **ACCEPTED with 1 SME edit** (chad.wilson, 2026-07-14).
- **SME EDIT — §B join policy upgraded (the edit of record):** the internal psgmgr changes derive
  **ctlm_id = folder_id.job_id** (e.g. `161015.7`) — the `(folder_id, job_id)` node key in composite
  form. The supplement loader joins on **ctlm_id where the replica exposes it** (split on `.` → the
  node key directly); the previously-proposed weak key (SCHED_TABLE, JOB_MEM_NAME = JOB_NAME) demotes
  to **fallback** for rows without a usable ctlm_id. P0 verifies ctlm_id presence/type on CM_AVG_RUN;
  P4 censuses its coverage; parsed ids must round-trip to the node key exactly (mismatch = census
  finding). MEMNAME stays NEVER a join key (q1q3 demotion).
- **§A — CONFIRMED:** property supplement onto existing :ControlMJob (no new labels/edges/vocabulary);
  MATCH-never-MERGE; property list = mappings n:1–n:3.
- **§C — CONFIRMED:** >24h clock normalized in Python; FileWatcher rows excluded from blended stats;
  day-of-week medians from SAMPLES_* arrays; ETA/window math critical-path, never path-sum.
- **§D — CONFIRMED:** P8 decides refresh strategy; residual probes (P0 types, P2 grain, P2b
  INSTANCE_NAME, P3b DSN, P7 parseability) remain REQUIRED before the loader ships — they ride
  backlog **P1** (user-run internal probes), which stays open.
- **§E — CONFIRMED:** maintenance-window computation (hosts-topology RUNS_ON → job windows → folder
  rollups + DC-default fallback) and the TDQ-failure ETA framing.
- **§F — SIGNED OFF.** **Confirmed: A, C, D, E · Edited: 1 (§B ctlm_id join upgrade) · Deferred: 0 ·
  Rejected: 0.**
- **Lifecycle (applied in this commit):** map entry `job-runtime-stats-supplement` proposed →
  **confirmed** (confirmed_by/confirmed_on set; vocab_id stays deliberately none — property
  supplement); backlog **P2 → done**. The loader is NOT authorized to ship until the P1 probes
  record their conclusions (§D) — build may start, load may not.

## 2026-07-14 — SOSA JobRun observation gate (E1) — DEFERRED by the SME

- Gate `config/gate-prompts/sosa-jobrun-observation.yaml` was presented alongside the F1/F2/P2
  sessions; **SME call: defer — not ready yet** (chad.wilson, 2026-07-14). No confirmations recorded,
  nothing flips: the four sosa_* vocabulary terms stay `status: planned`, the `jobrun-observation`
  map entry stays `status: proposed`, and the supplement stays opt-in/experimental. Re-present at a
  future session; the open design question (ControlMJobRun-as-Observation vs separate Observation
  node, run-history source) remains the gate's crux.

## 2026-07-14 — SEAL attribution match policy gate — SIGNED OFF (K2 gate; loader build unblocked)

- **Gate:** `config/gate-prompts/seal-attribution-match-policy.yaml` (24 confirmations, including the
  same-day §F manual-CSV additions), reviewed via the rendered page; **ACCEPTED IN FULL**
  (chad.wilson, 2026-07-14).
- **§A — CONFIRMED:** precedence SEAL > FID > APP_NAME > ALIAS; SEAL-tier hit attributes alone
  (lower tiers = corroboration only); one-to-one accept rule at the top available tier.
- **§B — CONFIRMED:** matched + unmatched counts checked against eligible jobs every run (no silent
  drops); unmatched surfaces for follow-up, never blocks; the invariant joins graph_verify.
- **§C — CONFIRMED; open question RESOLVED as the proposed default:** deterministic tie-break
  (most-recent run_id, then lexicographically lowest seal_id) applies as last resort — multi-hit
  cases do NOT pause for per-case SME calls at load time; every multi-hit is flagged on the coverage
  report for after-the-fact audit.
- **§D + §E — CONFIRMED, with the standing K3 rider:** MERGE edge shape (WAS_ASSOCIATED_WITH
  {role: seal_app_ref}) with ON CREATE/SET split as specified; loader creates no nodes on the
  automated path; runs only after jobs + SEAL loads; job.APPLICATION never a SEAL identity
  substitute; source/match_method explicit per edge. **Rider:** the shape type-checks TODAY
  (:Application is still prov:SoftwareAgent — the K3 reclass is unapplied, backlog K4); when K4
  applies the Entity/DataProduct reclass, the edge RE-SHAPES per the K3 §F deferred decision
  (prov:used vs domain edge — that follow-up gate, not this one). The match policy confirmed here
  (precedence, coverage, triage, pin semantics, provenance props) is shape-agnostic and carries
  over to whatever label the re-shape gate picks.
- **§F — CONFIRMED (manual CSV final option, tier 5, PIN semantics per the 2026-07-14 SME
  direction):** SME-authored CSV rows (template config/manual-loads/TEMPLATE-node-mapping.csv) map
  source -> PRE-EXISTING relationship -> target; a CSV can never mint a relationship type. Manual
  edges pin — automation NEVER silently supersedes (the data-incorrect / fix-module scenario);
  later automated matches surface as PIN-CONFLICTS; retirement (manifest -> superseded) is always a
  human act. Nodes a CSV forces into existence are stamped manually_created: true and counted
  separately. Every CSV registers in config/manual-loads/manifest.yaml BEFORE load with a named
  replaces_with automation path.
- **§G — SIGNED OFF.** **Confirmed: A, B, D, E, F · Decided: 1 (§C deterministic default) ·
  Deferred: 0 · Rejected: 0.**
- **Lifecycle (applied in this commit):** map entry `job-seal-app-ref` proposed → **confirmed**
  (confirmed_by/confirmed_on set); `config/manual-loads/manifest.yaml` proposed → **confirmed**.
  **Authorized, lands with the K2 loader build (the K3 flips-are-follow-ups pattern):**
  `m3_seal_app_ref` planned → active with its supplement + loader fields filled in, per the K2
  acceptance. Backlog **K2 stays in_progress** — it is the loader item; this gate was its
  precondition and the build is now unblocked.
- **Build landed (same day, branch feat/k2-seal-attribution-loader):** the authorized flips are
  now REAL — `m3_seal_app_ref` **active** (supplement `ontology_supplement.cypher`, loader
  `seal_attribution.cypher`); `stg-app-fact` source row **confirmed: true** per the activation
  condition that entry has carried since K1 (this gate, logged here) — taken as one unit with
  its audit-fields stub, LEDGER_PENDING entry, and the registry gate-state test pin; the §B
  coverage invariant joined graph_verify as `graph-tests/seal-attribution-coverage.yaml`.
  Backlog **K2 → done** (build scope; the live load is a Track-2 / company-graph concern).

## 2026-07-15 — Lineage rel vocabulary gate (G9 writer set) — CONFIRMED, reads/writes shapes EDITED

- **Scope:** the four gate-bound entries the `drydocs_lineage` curated writer needs —
  `m3_invokes`, `m3_triggers`, `m3_reads_from`, `m3_writes_to`. In-session review, no
  `config/gate-prompts/` spec (transcribed per the audit-trail §; chad.wilson, 2026-07-15).
  All four PAUSED per routing rules (open questions); none batched.
- **SME caveat (recorded — it drives the shapes):** the common case is one `.ksh` shell
  wrapper — the INVOKES target — that triggers the Informatica / Ab Initio / DPL process,
  passing the parameters those jobs need on CMD_LINE; the other case is a wrapper of pure
  unix file operations (move, gzip) with no ETL engine involved.
- **m3_invokes — CONFIRMED as registered** (ControlMJob → Script, prov:used). Registry,
  writer, extractor, and matrix all agree; the only shape the component produces today.
- **m3_triggers — CONFIRMED as registered** (Script → ETLProcess, inverse-of
  prov:wasStartedBy). The caveat validates the shape; TRIGGERS candidates are derivable
  from CMD_LINE wrapper parameters (primary feed) with ETL metadata as enrichment.
  **Residuals (loader blockers):** the ETLProcess business key (platform + workflow/graph/
  pipeline name from wrapper parameters) and an ETLProcess endpoint class in
  `drydocs_lineage.writer` (currently every non-job process maps to :Script).
- **m3_reads_from / m3_writes_to — CONFIRMED WITH EDIT:** endpoints re-pointed from the
  pre-G9 `ETLProcess → DataSource/DataTarget` shapes to the two-case reality —
  `from_node: ETLProcess | ControlMJob` (ETL case | file-ops case; Script is prov:Entity
  and cannot carry prov:used/generated, so the type-correct Activity for file ops is the
  job, resolved via its INVOKES edge), `to_node: DataAsset` (the D1 proxy URN carrying the
  composite-join constraint in all three data DBs). **DataSource / DataTarget RETIRED**
  (kept in node_classifications for audit; no loader ever shipped); **DataAsset added** to
  node_classifications (dcat:Dataset / Entity). **Residual:** the writer's file-ops
  resolution (script-level reads/writes attributed to the owning ControlMJob via INVOKES)
  is follow-up build work.
- **Signed off: Confirmed 4 · Edited 2 (the reads/writes shapes) · Deferred 0 · Rejected 0.**
- **Lifecycle (applied in this commit):** all four entries stay `status: planned` — the
  planned→active flips + `ontology_supplement.cypher` blocks land with the curated-load
  build (the K2 flips-are-follow-ups pattern; `writer.write_curated` keeps refusing a live
  load until then). Registry notes annotated; `schema_graph.cypher` mirror updated
  (DataAsset SchemaMeta node; two edges per reads/writes label; DataSource/DataTarget
  MERGEs removed with a retirement comment).

## 2026-07-16 — `cmdline-lineage-review` (in-session SME mini-gate: live CMDLINE patterns vs the planned m3_* lineage chain)

> **Cross-machine reconcile note (added at the 2026-07-16 `--no-ff` merge):** this session
> ran from a checkout that predated the 2026-07-15 vocabulary gate above (run on the other
> machine), so its "does the chain hold" framing re-derived some of that gate's outcome
> independently — the two sessions AGREE (chain holds; CMDLINE is the primary TRIGGERS
> feed). Deltas this entry ADDS: §b RESOLVES the 07-15 "ETLProcess business key" residual
> (kind-scoped stable token, implemented in the extractor); §a (kind property), §c (Script
> path-keyed), §d (DPL invocation_type) are new. Where this entry says reads/writes target
> DataSource/DataTarget, the 07-15 EDIT supersedes it: `ETLProcess | ControlMJob` →
> `DataAsset`. The 07-15 writer residuals (ETLProcess endpoint class, file-ops resolution)
> remain the open build blockers before the flips.

- **Trigger:** SME supplied 6 production folder/job screenshots (held local-only,
  `internal-local/screenshots/`) covering three invocation shapes: the abioncloud
  `runScript.sh` wrapper (-g pset), the DPL `dt-pipelines-launcher` jar (java -jar,
  -pipeline GUID + -dataflow), and a compound `ksh check; if…else sh wrapper…;fi`.
  Question: does the planned INVOKES → TRIGGERS → READS_FROM/WRITES_TO chain hold?
- **Verdict: the chain HOLDS — no edge-semantics change.** All four m3_* entries
  REMAIN `status: planned`; the live-load gate (planned→active flips + first curated
  write against a real extract) is still pending and unchanged.
- **§a — DECIDED: ETLProcess keeps its label + gains a `kind` property**
  (etl | utility | notification). Utility psets exist (script-exec/send-email);
  label rename (ManagedProcess) deliberately rejected for now — revisit at v1.0.
- **§b — DECIDED: ETLProcess identity = kind-scoped stable token** — Ab Initio
  pset/graph basename (sandbox mounts vary by env), DPL pipeline GUID (dataflow
  name + config JSON as properties). Implemented same day in the inventory
  extractor's `_stable_invocation_key` (test-pinned).
- **§c — DECIDED: Script identity stays PATH-keyed; duplicates surface, never
  auto-merge.** Live case: one logical .ksh at two mounts. Same-basename
  multi-path Scripts flag in lineage-review for SME merge via the curation ladder.
- **§d — DECIDED: DPL is its own invocation_type, NOT Ab Initio** (corrects the
  seeded `abinitio.dtlaunch_accelerator` rule). SME facts recorded: common path
  /apps/tenants/dpl_utils/dt-accelerators/, launcher spelling `dt-launcher.sh`
  (dtlaunch.sh kept as variant), originally the java zilo ETL framework, `-py`
  routes to a java-spark/pyspark framework. Feeds the PENDING plan-07 P3
  software-usage-patterns gate as a decided row.
- **§e — NOTE AMENDMENT:** the CMDLINE itself is a first-class TRIGGERS feed
  (-g pset / -pipeline GUID) alongside Informatica/Ab Initio/DPL metadata.
- **Requirement captured (not built):** the launcher registry must become
  human-configurable (SME: admin screen candidate for the web console) — IDEAS.
- **Code landed same day (no gate needed — parser/staging layer):** control-keyword
  stripping (if/then/else/fi — the else-branch main invocation was parsing UNKNOWN),
  abioncloud -g pset payload expansion (+ nested -run_prog_command_line), case-fix
  on the runScript.sh rule, java/.jar extraction with re-classification, `air` CLI
  rule, DPL rules, extractor stable keys. Sanitized mechanism-twins pinned in
  test_command_parser.py + test_lineage_inventory.py.
- **Side finding for K2:** FID + SEAL co-located in folder variables (SEAL also
  embedded in folder names) — a FID→seal reconciliation source candidate (IDEAS).

## 2026-07-18 — docmeta component + doc-graph gate — SIGNED OFF (Q4; ADR 0006 ACCEPTED)

- **Trigger:** the recorded Q4 gate — docmeta plan P1 decisions reserved for SME
  review, unblocked by the P0 benchmark verdict (BUILD, 2026-07-16). ADR 0006
  (`docs/decisions/0006-docmeta-component-and-doc-graph.md`) authored PROPOSED
  for the session; SME (chad.wilson) reviewed in-session and accepted all four
  decisions AS WRITTEN on the recommended options.
- **§a — DECIDED: docmeta stays its OWN component (`drydocs-docmeta`), no
  deepdoc fold-in.** Proactive registry-driven corpus pipeline vs deepdoc's
  reactive investigator; deepdoc becomes a consumer of the corpus. The modules
  registry drops the "working name" caveat at Q6.
- **§b — DECIDED: new `dddocs` database** — the plan's `drydocs_docs` renamed
  to the live `dd*` convention (ddlineage/ddcontext/ddall). G1 provisioning
  pattern + composite membership; bmc-docs/software-registry corpus re-targets
  from `drydocs` at the P4 loader build (idempotent reload); the Q2 book corpus
  stays in `ddcontext`.
- **§c — DECIDED: vocabulary reconciled, no double registration.** `HAS_CHUNK`
  SUPERSEDED by the active PART_OF/FIRST_CHUNK/NEXT_CHUNK shape (gate
  bmc-docs-lexical-load, twice-proven); `DESCRIBES` Document→SoftwareProduct
  already active, unchanged. NEW `status: planned` entries registered this
  session: `docs_has_document` (DocSource→Document, HAS_DOCUMENT; new
  `DocSource` node classification, prov Entity, DCAT-catalog-shaped) and
  `docs_governed_by` (Document→OntologyTerm, GOVERNED_BY). Chunk-level
  DESCRIBES to proxy nodes (ControlMJob/DataAsset) DEFERRED to its own gate at
  extraction design (P4+).
- **§d — DECIDED: curation-ladder→gate mapping adopted** — registry `curation:`
  none (T1) / sme-confirm (T2/T3) / sme-confirm+confidential (T4);
  `unapproved`→pre-gate, `ai_generated_review_needed`→gate-queued,
  `approved_by_sme`→confirmed; sha256 change on refetch RE-QUEUES curation
  (never silently overwrites confirmed content).
- **§e — ADOPTED from the P0 verdict:** lexical graph as spine; ch.8
  RAGAS-style harness (Cypher-as-ground-truth) as the component's own gate;
  fulltext index as standing infrastructure; embeddings/vector as a pluggable
  arm gated on the open LLM-key-strategy question; query-time hygiene rules;
  manifest stays provenance source of truth + fallback path.
- **Consequences:** Q4 done; Q5 (doc-source registry ledger) next_ready and
  keyed to this ADR's field semantics; Q6 builds the package under the
  confirmed name. Both new vocab entries stay planned until their loaders
  exist (the K2 flips-are-follow-ups pattern) — nothing flipped active today.

## 2026-07-18 — same-row-derived edges rule — SIGNED OFF (C5; gate `same-row-derived-edges`)

Gate session run in-session with the SME (drafting by the ontology-mapper agent;
audit of all 22 loader cypher files preceded the gate).

- **§a — CONFIRMED as written: the join-restatement rule** now in
  `docs/RELATIONSHIP_GUIDE.md` ("Same-row-derived nodes"): hierarchy → chain it,
  skip-level edges banned; star → satellites relate to the row's subject only;
  the author test is "does this edge carry a fact the chain doesn't already
  imply, with its own provenance?"; exceptions only via this gate with an
  independent asserting source. Methodology only — no vocabulary entry.
- **§b — live case resolved: NO direct ControlMApplication↔ControlMServer edge.**
  SME probe recorded: *what would the direct edge even mean* — two production
  Control-M servers can each run the same application's work (names withheld,
  Internal-Confidential). Resolution: nothing the folder-mediated traversal
  (app→CONTAINS_FOLDER→folder→SCHEDULED_ON→server) doesn't already answer
  per-folder and current; a stored shortcut flattens a many-to-many that
  changes as folders migrate. `m3-verify` gains the guard
  `no direct ControlMApplication<->ControlMServer edge`.
- **§c — audit finding → follow-up C9 (p1).** `pat_product_mapping.cypher`
  still unconditionally writes the 2026-06-21-DEPRECATED `catalog_supports`
  edge (DevTeam→SUPPORTS→Product) and the status-planned
  `catalog_has_application`. SME context given in-session (PAT screenshots —
  Internal-Confidential, held OUT of the repo): dev teams map to ONE OR MORE
  business applications via the PAT team report (the stable mapping);
  team→area-product ALIGNMENT is volatile and relationship-typed
  (dedicated/aligned/flex); supporting vs sponsoring are distinct fields; PAT
  itself carries Supporting Product and Supporting Area Product as SEPARATE
  columns — so the deprecated edge may be an independently-asserted source
  fact, i.e. the C5 rule's own exception path, not a pure join-restatement.
  That decision needs its own gate with the source in front of the SME: filed
  as C9 rather than fixed blind here. Nothing flipped in the vocabulary today.

## 2026-07-18 — PAT reconcile — SIGNED OFF (C9; gate `pat-reconcile`)

Gate session run in-session with the SME (follow-up to the C5 audit finding;
SME-supplied PAT screenshots held OUT of the repo — Internal-Confidential).

- **§a — DECIDED: the ladder, reconciled.** The SME proposed a cascade
  (team→apps first, then area product, then product); reconciled against the
  vocabulary so rung 1 rides the ACTIVE `arch_develops` entry rather than
  minting a second SUPPORTS label (no double registration): the team report's
  team-scoped seal_ids write
  `(:BusinessApplication)-[:WAS_ATTRIBUTED_TO {role:developed_by}]->(:DevTeam)`.
  SME confirmed **apps + alignment** over a strict either/or ladder: alignment
  loads ALONGSIDE apps (PAT asserts both on the same row; alignment is not
  derivable from apps since apps are often unmapped to products).
- **§b — DECIDED: home-product SUPPORTS is fallback-only.** `catalog_supports`
  re-activated NARROWED (was deprecated 2026-06-21 "not modeled"): written only
  when the row carries no area_product_id — the C5 sole-assertion path; with an
  area product present the direct edge is a banned join-restatement. m1-verify
  gains the guard `no join-restating DevTeam->Product SUPPORTS`.
- **§c — DECIDED: Product→HAS_APPLICATION write REMOVED** from the team-row
  loader (team-scoped seal_ids were mis-attributed to the Product);
  `catalog_has_application` stays `status: planned` until a product-scoped
  extract (the PAT product "Mapped Applications" tab) is onboarded.
- **§d — DECIDED: sponsoring extended** — sponsored_area_product_id added to
  the row model; both sponsoring forms load as `SUPPORTS {sponsored:true}`
  (independent facts: different target than the alignment chain).
- **§e — Volatility mechanics** (implementation, not edge meaning): each load
  sweeps the batch teams' stale pat-sourced SUPPORTS/developed_by edges
  (last_run_id scoping, the D7 philosophy) — alignment tracked, never frozen.
  One-time cleanup of pre-C9 edges: `migrate_pat_alignment_c9.cypher` (applied
  to the live sample graph this session). Anchor apps MERGEd from seal_ids
  carry `source: pat`; the m1-verify ports invariant is now scoped to
  `source: SEAL` apps (anchors are legitimately port-less until the SEAL
  extract covers them).
- **Verification:** synthetic 4-row sample exercises every ladder branch;
  live refresh-reference run shows the exact expected shape (apps + area
  alignment with NO home-product edge; product fallback only where no area
  product; both sponsored forms; HAS_APPLICATION count 0); m1-verify +
  m3-verify green; suite 718.

## 2026-07-20 — K5 · Product Cabinet attribution model (product-cabinet-attribution)
- **Presented:** 24 confirmations across 6 sections (gate page
  `config/gate-prompts/product-cabinet-attribution.yaml`, gate_pages.py render; split from
  the 2026-07-10 BusinessApplication entity-reshape gate §B). SME session ran in-chat
  2026-07-20 — sections answered individually, **§F signed off** (chad.wilson).
- **Confirmed: 24 · Edited: 0 · Rejected: 0** — 5 open questions resolved in-session:
  - **§A — product_roles scheme FIXED + families INDEPENDENT.** EXACTLY the fixed 7
    (area_product_owner, product_owner, product_architect, tech_partner, data_owner,
    data_certifier, analytics_lead); new roles require a new gate (the tom_roles precedent).
    The 2026-07-10 §B "CTO is in BOTH families" record is **SUPERSEDED**: the shared-cto
    concept is dropped for now; SEAL's cto stays a TOM role on :BusinessApplication.
    Rename history (skos:changeNote on tech_partner): in PAT the mapping changed slightly —
    the area-product Tech Partner was formerly named "CTO" in SEAL, and SEAL's CTO now
    denotes the product-level role.
  - **§B — scope:** attribution attaches to :Product / :AreaProduct only, never
    :BusinessApplication; area_product_owner AND tech_partner attach ONLY to :AreaProduct.
    AreaProduct data gap noted, not resolved (loader entries stay planned; independent
    lifecycles).
  - **§C — BOTH attribution forms load:** the reified chain
    (catalog_cabinet_qualified_attribution / seal_attribution_has_agent REUSED /
    catalog_cabinet_attribution_had_role) AND the collapsed simple form
    catalog_cabinet_attributed_to ((:Product|:AreaProduct)-[:WAS_ATTRIBUTED_TO
    {role: product_cabinet_role_holder}]->(:Employee), twin of
    seal_app_attributed_to_employee) — a deliberate deviation from the K4 TOM
    qualified-only resolution; the reified form remains the multi-person carrier.
  - **§D — cross-family reporting edges DEFERRED (option b):** tech_partner MANAGES
    application_owner; information_owner MAY REPORT TO data_owner; data_certifier RELATES
    TO information_owner — preserved verbatim, nothing registered. SME: "that can be done
    internally" — person-level population is internal/company-side once a person-level PAT
    cabinet extract exists.
  - **§E — DevTeam↔BusinessApplication M:N CONFIRMED** in both directions on the existing
    applied arch_develops edge (C9 PAT team-report evidence corroborating); no new edge, no
    cardinality constraint; multiple developed_by teams on one application is VALID data —
    verify rules must not flag it.
- **Effect:** map entry `product-cabinet-attribution` proposed → **confirmed** (summary
  proposed 3 / confirmed 21); the three catalog_cabinet_* vocabulary entries + the
  ProductRole classification stay **planned** until the supplement lands (honest-lifecycle)
  — supplement groomed as **K6**; any Product Cabinet loader stays blocked company-side
  (no person-level cabinet extract exists). Sign-off note corrections applied as their own
  logged change: seal_attribution_has_agent rescoped family-agnostic; TOMRole notes + the
  seal supplement's shared-cto references corrected (c4.shared_with REMOVEd — a supplement
  re-apply refreshes already-loaded graphs).

## 2026-07-20 — L7 · Documentation traceability + review feedback (doc-traceability-feedback) — SIGNED OFF

- **Scope:** the PRODUCT-PLANE documentation ontology — six source-agnostic node classes
  (DesignDoc, DocSection, Requirement, Component, TestCase, FeedbackNote) + six `doc_`
  relationship entries (PART_OF, SPECIFIED_IN, IMPLEMENTED_BY, VERIFIED_BY, ANNOTATES,
  WAS_ATTRIBUTED_TO {role: feedback_author}), validated on DryDocs' own outline system as
  source connector #1 ("tenant 0"). Gate spec:
  `config/gate-prompts/doc-traceability-feedback.yaml` (ontology-mapper draft, then the
  same-day SaaS-reframe amendments at SME direction). SME session ran in-chat 2026-07-20.
- **Confirmed: 21 · Edited: 0 · Rejected: 0** — A1-A7, B1-B4, C1-C4, D1-D7 all confirmed
  as recommended (chad.wilson). Key decisions:
  - **§A — product-plane, source-agnostic classes** with an `origin` discriminator and
    SOURCE-NAMESPACED keys (no single-repo assumption); use cases fold into Requirement
    as kind FR|UC|NFR (Scenario deferred to a future BDD-connector gate); DesignDoc/
    DocSection vs Document/Chunk confirmed as a permanent MANAGED-vs-INGESTED product
    boundary; Component/TestCase are new classes (:Script/:PipelineService folds rejected);
    TestCase.kind is an OPEN enum.
  - **§B — PART_OF** containment (Document/Chunk precedent, C8-clean twin);
    **SPECIFIED_IN = prov:hadPrimarySource** (seal_had_primary_source reuse);
    IMPLEMENTED_BY / VERIFIED_BY stay LOCAL with Ramesh & Jarke reference-model backing
    (Satisfies/Allocated-to, Verifies); star shape off Requirement confirmed.
  - **§C — collapsed attribution** (FeedbackNote -[:WAS_ATTRIBUTED_TO {role:
    feedback_author}]-> Employee; no reified form — one author, no role scheme);
    doc_rev stays a PROPERTY (no Revision node); NEW lifecycle status on FeedbackNote
    (open|applied|rejected|superseded — the runbook rev1→Rev 2 loop is the precedent);
    correlation to Requirement rides the mixed-direction path (no ABOUT_REQUIREMENT
    shortcut edge).
  - **§D — dispositions:** same-basename-within-origin Components stay SME-merge (m3
    idiom); TestCase.kind free property; precedence_authority = internal-standards
    closest-fit (gap flagged, no new authority); oa: adoption deferred (heavier under the
    SaaS lens, still not declared); requirement-id pattern + loose/strict mode are
    PER-SOURCE connector config mirrored at load time (config surface = backlog O12's
    admin page); **Jira-board caveat recorded** — each BusinessApplication or DevTeam MAY
    have a Jira board, keyed off the JIRA PROJECT NAME (the future Jira connector's join
    key; board-to-owner mapping = per-tenant config in O12, captured before that
    connector's gate — the JiraBoard node class + edge belong to that future gate);
    linkage on the record (context-loop plan, generic-terminology research, O12) —
    whether the product-ontology weight re-tiers L7 or seeds a productization epic stays
    the SME's parked plan decision.
- **Effect:** map entry `doc-traceability-feedback` proposed → **confirmed** (summary
  confirmed 22 / proposed 3); all six classes + six `doc_` vocabulary entries planned →
  **active**; supplement terms landed same day in `ontology_supplement.cypher` (the
  docs-domain home — K6-style same-day landing); connector-#1 loader
  (`load-doc-traceability`: docs/design/*.md matrices + docs/design/feedback/*.yaml)
  follows under the same L7 item — no graph content exists until it runs.

## 2026-07-21 — CMD_LINE NFR ontology + variable standard (cmdline-nfr-vetting) — SIGNED OFF

- **Scope:** the company-side draft standards NFR (canonical Control-M variables +
  command-line structure, with its own ontology section) vetted against the producer m3
  vocabulary; the 2,384-variable gap analysis; the launcher-inventory review. Session ran
  in-chat 2026-07-21 (flow-doc §5–§6 hold the comparison + proposal); four calls, all
  ruled as recommended (chad.wilson).
- **Confirmed: 4 · Edited: 0 · Rejected: 0**
  - **SME-1 — TRIGGERS from-node = the invoked wrapper/LAUNCHER Script** (m3_triggers
    unchanged); the draft NFR's payload-sourced variant REJECTED — the `-pipeline` GUID
    literal rides the launcher's CMD_LINE (the extractor's parse surface) and payloads
    are often variable-held/unresolvable.
  - **SME-2 — USES_ARTIFACT registered** as new vocab entry `m7_uses_artifact`
    (ControlMJob→Script{payload}, prov:used, `status: planned`) — distinct label per the
    documented RUNS_ON-overload risk; the digested v2 standard's tooling table (its
    m7_etl_artifact_supplement target) already assumes it. Payload invocations migrate
    out of the m3_invokes 1..n fold at the m7 build.
  - **SME-3 — :Script refinements adopted** (with m7): script_role {launcher, payload} +
    platform / artifact_uri / artifact_kind / platform_flags / script_path properties
    (+ the 4 Informatica identifiers); Script identity stays PATH-keyed.
  - **SME-4 — variable-standard deltas adopted, all 7** (flow-doc §6.3): ETL_* prefix
    wins over the gap-analysis CTM_* spelling; NEW ETL_ARTIFACT_SHA canonical (digests
    are not URIs); the aliases-suggest-VALUES-DECIDE contract (a variable holding a
    registered launcher is a launcher ref regardless of name); alias-map completion from
    the 2,384-var evidence; TWO platform axes (%%ETL_PLATFORM = execution tech, extended
    with emr + reserved snowflake; ETLProcess.kind stays a separate launcher-derived
    graph axis — the perceived enum mismatch dissolves); FACT_REGISTRY migration incl.
    the IMAGE → ARTIFACT_URI clean break; mode flags stay CMD_LINE literals (only -py
    rides ETL_PLATFORM_FLAGS).
- **Effect:** vocab — m3_triggers + m3_invokes notes amended, `m7_uses_artifact` added
  `status: planned` (honest-lifecycle: no supplement block, no loader until its build);
  engine alignment groomed as **G16** (FACT_REGISTRY ETL_* canonicals + alias rollups +
  value contracts + ICDW_etl_run_interface.ksh launcher rule). Launcher-registry review
  verdict on record: value-based classification design CONFIRMED correct; open gaps =
  dpl_spark_processor (G15), ICDW ksh (G16), ecosystem_execution_engine.sh + the
  template ingestion jar (await samples). COMPANY runs its own gate on the draft NFR —
  this sign-off is producer-side only.

## 2026-07-21 — UI write-surface boundary, whole web console (ui-write-surface) — SIGNED OFF (O20)

- **Scope:** the write-surface boundary for the ENTIRE web console (all nine module
  pages + /mappings + /admin/config + drydocs-api), NOT just the /gates page — the SME
  scope clarification and the same-day direction amendments (gate-prompt header) are
  part of this record. Session ran in-chat 2026-07-21 pm, guided walk-through over the
  rendered page (var/gate-ui-write-surface.html, 11 confirmations); four calls, all
  ruled as recommended (chad.wilson).
- **Confirmed: 4 · Edited: 0 · Rejected: 0**
  - **SME-1 — doctrine + C4 + C5 confirmed as written:** the loader remains the ONLY
    graph writer; M3 (direct graph write from any console action) is REFUSED as a
    standing rule — any future exception is its own gate; drydocs-api stays
    read + artifact + derived-non-graph-store only; declining extensions is always a
    valid outcome. C4: admin config edits NEVER (the wf-admin-config-01 traceability-
    lens doctrine). C5: an admin/SUPER-USER page in the SaaS idiom is EXPECTED for
    UI-WEB — expectation recorded; scoping is follow-on backlog; any write it carries
    follows the tiers ruled here.
  - **SME-2 — C1 = M1 artifact-drafting:** gate pages are NECESSARY for building and
    confirming (no upfront spec — the model emerges through confirmation, the SME's
    own framing), and gain an M1 affordance: the rendered page assembles the gate-log
    entry snippet from ticked confirmations for the SME to review + commit. Zero
    server surface; ticks stay browser-local; upgradeable to M2 only by its own
    decision. Groomed as **O25**.
  - **SME-3 — C2 = M2 non-graph store:** SME annotations/user mappings persist in the
    mapping-store DATABASE TABLE (the file→table enhancement) with the ORIGIN FLAG
    (source vs user mapping) always visible, exported as artifacts/reports. First
    instance = the SEAL-contacts override list (**O24**, promoted same day). If notes
    ever become graph content, that shape routes through its own ontology gate first.
  - **SME-4 — C3 = defer server-side git:** overrides/mappings exit as downloads +
    SOURCE-CORRECTIONS REPORTS for the system owners (the fix-the-source doctrine —
    e.g. SEAL L1/L2 operate-manager fixes need the AO privilege in SEAL itself);
    server-side branch/PR creation waits on the company GHE posture + its own
    security review.
- **Effect:** O20 done — the Epic O phase-12 chain is complete end to end. The
  console-wide boundary is now a recorded decision: M1 gate-page drafting (O25) +
  M2 origin-flagged store with report exits (O24 first) + M3 refused standing +
  admin edits never + super-user page expected (scoping follow-on). gates.json
  regenerates with this entry (the O19 drift guard enforces it). No vocabulary or
  map changes — this gate ruled console affordances, not graph semantics.

## 2026-07-21 — Platforms taxonomy: SchedulerKind retires into the software-registry model (platforms-taxonomy) — SIGNED OFF (C12)

- **Scope:** the C6+C11 terminus — the platforms/SchedulerKind reconciliation, decided
  FROM the C11-captured company shape (their 2026-06-29 AIS gate) plus the same-day SME
  in-chat rulings (2026-07-21 pm). Guided in-chat session (chad.wilson); rendered page
  presented; 3 calls, all as recommended.
- **Confirmed: 3 · Edited: 0 · Rejected: 0**
  - **A + B1–B3 confirmed as written** (ratifies the 2026-07-21 pm pre-gate rulings):
    B1 USES_TOOL retired with the Ais* family — the app→orchestrator fact lands on the
    ACTIVE reg_uses_software edge (:BusinessApplication)-[:USES_SOFTWARE {source:
    ''batch-port''}]->(:SoftwareProduct {role: orchestrator}); seal_requires_scheduler
    (planned, never wired) RETIRES instead of reshaping — zero new edge or node types.
    B2 the capability node layer is NOT adopted — the registry role vocabulary carries
    the classification (''Orchestration'' = the intended highest level). B3 the tool
    class MERGES into :SoftwareProduct (supersedes the earlier distinct-view Q4
    direction). Q6 the Ais* spelling is removed both sides; AIS = ''Application
    Integration Streaming'' (a misnomer — the folder also carried ETL + file transfer)
    survives ONLY as software-registry.yaml#acronyms; the Integration* rename
    counter-proposal stays REJECTED. A: Q2 one app-level edge (hoisted to
    :BusinessApplication); Q3 :Scheduler retired unbuilt (:ControlMServer = the
    deployed layer); Q5 publishability split (class model + public vendors public;
    internal tool values + instances internal/); Q1 the batch/event capability seed
    stays withdrawn.
  - **B4 — existing typing covers the migrated fact:** reg_uses_software stays a LOCAL
    Agent→Entity edge with NO PROV row (PROV has no Agent→Entity usage term; the same
    null-PROV infrastructure family as SCHEDULED_ON / the arch_contains precedent).
    Only the source: ''batch-port'' property convention is new. IN_CAPABILITY moot (B2).
  - **B5 — the airflow row STAYS** as the F2 crosswalk placeholder (Apache Airflow is
    not in the company tool list; their AWS leg = EventBridge Scheduler + Glue).
- **Effect:** platforms.yaml flips confirmed: true (status: captured). Build follow-ups
  GROOMED, not built (the K2 flips-are-follow-ups pattern): **C13** (retire the
  SchedulerKind ontology.cypher seeds + scheduler_kind constraint; retire
  seal_requires_scheduler + the requires-scheduler map entry as superseded-by
  reg_uses_software; sweep the Ais* stragglers in README / NODE_QUICK_REFERENCE /
  LoadPlanV3 refs) and **C14** (the batch-port USES_SOFTWARE loader migration,
  source: ''batch-port''). Vocabulary statuses untouched at the gate itself. Company
  sign-off remains provenance only — company gates ≠ producer gates. C12 done.

## 2026-07-23 — ADR 0007 · agentic Q&A architecture — SIGNED OFF (R1)

- **Scope:** architecture acceptance (like the ADR 0002 entry) — no taxonomy/ontology
  mappings; no graph writes ruled in. Session: in-session ratification, SME chad.wilson.
- **Decision:** ADR 0007 **ACCEPTED as written** with the three open axes ruled:
  - **A — Tier-2 context-graph residency: in-process only.** The enhance branch's task
    graph is agent working memory (KGoT NetworkX shape); dies with the run; UI snapshots
    ephemeral. Persisting to `ddcontext` (SYNTHESIZED envelope, session tag, TTL sweep)
    considered and DEFERRED — re-proposing it is a new gate, never a default.
  - **B — `:AgentRun` telemetry envelope → `ddcontext`** (never `drydocs`), via a
    dedicated writer boundary in the agent service. Question text: sha256 + length only
    in-graph; full text solely in the DRYDOCS_LOGDIR ledger. Revisit trigger: telemetry
    volume/retention diverging from ddcontext policy → dedicated dd* DB (ADR 0002
    amendment).
  - **C — LLM key strategy: environment-split providers.** Producer/local runtime =
    **Anthropic API key** (root .env); company runtime = **Azure OpenAI**. Gemini is NOT
    the runtime default — supersedes the 2026-07-03 IDEAS assumption (Fusion-SmartSDK-
    on-ADK implied Gemini-shaped); GOOGLE_API_KEY survives only for the pre-existing
    demo agents until R2 rewires them. Both environments bind models through a provider
    adapter (LiteLLM-style); the usage-extractor seam normalizes Anthropic + Azure
    OpenAI token metadata from day one; model ids/endpoints live in config, never code.
- **Effect:** R1 done; R2 (graph_qa Tier-0/1) becomes next_ready. Build follow-ups stay
  groomed as R2–R8 — nothing built at the gate itself. O20 (UI zero graph writes)
  reconfirmed standing for the whole epic.

## 2026-07-23 — Folder property diet · naming-convention decode OFF nodes — RULED (in-session)

- **Scope:** :ControlMFolder node properties only (the property-diet rider parked in
  IDEAS 2026-07-22 — named a SEPARATE decision by gate-prompt
  `seal-app-ref-edge-reshape.yaml` §B, which keeps owning the app-code → SEAL/AreaProduct
  mapping tiers). Session: in-session ruling, SME chad.wilson.
- **Decision:** the folder-name convention (pos1=env, pos2=lob, pos3-5=app_code,
  pos6=folder_type) is the **internal Control-M app-code definition** — do NOT expand it
  onto nodes. `environment_code/environment/lob_code/lob/folder_type_code/folder_type`
  retired from the loader + cypher; **`app_code` KEPT** as the join key for the app-code
  → BusinessApplication defined mapping ("we can do that without adding P production
  R retail"). Rationale confirmed: `f.lob='Retail'` collides with the org-taxonomy LOB
  (same word, different taxonomy); env truth is the `data_center` prefix on
  :ControlMServer, not folder-name pos 1; the real access pattern is the rollup via
  containment + defined mapping, not property filters.
- **Mechanism:** decode lives ONCE in `folder_name.py` (parser unchanged — validation +
  app_code extraction still use it); node keeps `sched_table` raw + `app_code`.
  No property-retirement migration: pre-diet graphs are wiped and rebuilt from bootstrap
  (wipe-and-rebuild doctrine, 2026-07-23). Checksum inputs slim to app_code +
  prefix_recognized — moot under rebuild.
- **Effect:** loader + cypher + tests edited this commit; TDD Rev 5 follows. The tier-2
  platform-code enumeration stays parked in IDEAS (SME to supply). Staging DDL
  `fn_lob_code` (analysis staging, not graph) untouched.

## 2026-07-27 — BusinessApplication identity: `seal_id` → `app_id` on the canonical node (business-application-identity) — SIGNED OFF (S3)

- **Scope:** the identity PROPERTY CONTRACT of the canonical `:BusinessApplication` node —
  and the MERGE-key cutover eight loader sites share. Raised by ADR 0010 (pre-UI structure
  review §4.2 F2), groomed as backlog **S3**. Guided in-chat session (chad.wilson) across
  2026-07-25/26/27; spec revised v1→v3.3 during the walk. **No edge, no vocabulary term** —
  a node-property binding, property-supplement shape (`to_node: ~`, `vocab_id: ~`),
  precedent `job-runtime-stats-supplement` (2026-07-14).
- **Confirmed: 22 · Edited: 0 · Rejected: 0** (A1–A4, B0–B6, C1–C4, D1–D2, E1–E3, F1–F2, G1–G4)

- **B0 (premise) → B1(c) (the ruling):** SEAL remains the single issuing registry, so v1's
  `id_authority` stays WITHDRAWN and `app_urn` stays DEFERRED with its named trigger (B3).
  The canonical node takes **`app_id`**, plus a declared source-field ledger in
  `config/source-mappings/seal-extract.yaml` — the mechanism `controlm-psgmgr.yaml` already
  uses, guarded by `test_source_mapping_drift.py`. B6 records the honest limit: that ledger
  is DECLARATIVE and guard-reconciled, **not** a runtime mapping — loaders still hardcode,
  and making it load-bearing is a real build, scoped out.

- **B2 — THE RULE IS TWO-PART** (SME correction, the session's most consequential ruling):
  *(i) IDENTITY* — canonical nodes take neutral property names (ADR 0003 rule 1).
  *(ii) EVIDENCE* — provenance/match vocabulary KEEPS the source's own term.
  Why: SEAL's portal calls the field `Application ID`, but the wider ecosystem (Control-M
  CMDLINEs, internal docs) says SEAL / SEAL_ID. So `ATTRIBUTION_TIERS 'SEAL'` and
  `match_method: 'seal'` record **what another system literally wrote** — renaming them
  would make the graph misdescribe its own source, not tidy it.

- **B4/B5 — `SEALID` was never a source field name.** It appears nowhere in code, SQL or
  Cypher, only in prose; the row model was already `app_id`. The SME confirmed seal-extract
  reads the SEAL Reports export, whose header is `Application ID`. So `seal_id` was a
  DryDocs-era coinage over a value that was already neutral everywhere else, and
  `config/taxonomy/business-application.yaml`'s `identifier: SEALID` recorded a name the
  source does not use — **corrected at this sign-off**.

- **C1–C4 — the cutover.** Corrected inventory: **8 key-bearing sites**, not 7 — 4 MERGE
  (`seal_applications:19`, `manual_seal_attribution:32`, `pat_product_mapping:54`,
  `software_registry:52`) and 4 MATCH (`batch_port_orchestrator:25`,
  `manual_seal_attribution:41`, `seal_attribution:32`, `seal_contacts:27`). The key flips in
  ONE atomic change across all of them: a Neo4j uniqueness constraint IGNORES NULLS, so a
  partial cutover would **silently double** the canonical node rather than fail. Dual-write
  through phases 1–3 with a `graph-tests/` assertion that `app_id = seal_id`; existing graphs
  handled by REBUILD, not migration (wipe-and-rebuild doctrine, 2026-07-23).

- **D1 — (a), `:Port` follows NOW** (against the spec's own recommendation). Measured blast
  radius: three functional lines in two files §C already opens (`constraints.cypher:44`,
  `seal_applications.cypher:96,100`); zero references in `drydocs_api/`, `graph-tests/`,
  `web/src/`; `cli.py` binds ports through `HAS_PORT`, not the property. The spec's (b) rested
  on create-then-drop being awkward — which assumes in-place migration, and **C4 ruled that
  out**. **TRAP recorded for the implementing phase:** `CREATE CONSTRAINT <name> IF NOT
  EXISTS` matches on the NAME, so redefining `port_unique` under the same name SUCCEEDS AND
  DOES NOTHING, leaving the old definition live. DROP first or take a new name.

- **D2 — (a), the pin holds, now evidence-backed.** `attribution_id` keeps its 4-part shape
  `app_id|SEAL|role|sid` and the SOURCE role string (rename-orphaning cost accepted). SME
  screenshots of the live registry showed BOTH collision cases on a single application: one
  person holding L1 Operate manager, L2 Operate manager AND Operate Manager (drop the role →
  three collapse), and four different people holding Backup Information Owner (drop the sid →
  four collapse). Both are the normal case, not the edge case.

- **E1–E3 — surface contract.** API and console emit `app_id` (singular). `mappingsDemo.ts`
  loses `app_seal_id`; its stray `'seal_var'` corrects to the real `'seal'`. The SEAL
  match-tier vocabulary is SCOPED OUT per B2(ii) — it belongs to the signed
  `seal-attribution-match-policy` (2026-07-14), which A1 declares unchanged. E2 confirmed as
  a STANDING rule, not a fallback: the console never leaks an internal registry name
  regardless of what the graph stores. Diff is real — 22 `seal_id` lines in
  `query_specs.py`, 14 in `mappings.py`.

- **F1 — SIX legitimate homes** for the registry name after this gate: (1) taxonomy
  `source_of_record`, (2) `source-registry.yaml`, (3) the ledger FILENAME (its column row is
  `Application ID`), (4) module/file names, (5) CONSTRAINT NAMES (`businessapplication_seal`
  — the most operator-visible, it prints in `SHOW CONSTRAINTS` and every violation error),
  (6) EVIDENCE VOCABULARY. **(6) IS graph data** — `match_method` is a property on every
  automated attribution edge — which falsifies v3.1's "none is graph data" and is recorded so
  no future reviewer deletes it as drift. Clean outcome: **`SEALID` leaves the repo entirely**;
  `SEAL` survives in three non-overlapping roles — authority, source id, ecosystem convention.

- **F2 — glossary is DIRECTION, plus scaffolding is RAISED.** The SME's reason: the glossary
  is mostly internal (except industry-standard terms), and doing the scaffolding producer-side
  now prevents an internal-port collision later on **both** a name and a backlog slot. Handled
  as a raised backlog item rather than an act of this gate, so A1 ("creates no
  relationship-vocabulary term") stays intact — the `status: planned` registration is the
  documented pre-gate step (SOSA/SSN precedent). Split ruled: **schema public** (label, key,
  edge terms, YAML shape — portable to the company repo), **definitions internal**;
  industry-standard terms bind to SKOS, already a declared reference standard.

- **G1–G4 — sequencing.** Phase 1: loaders write both + new `app_id` constraint under a NEW
  name + the `:Port` flip (DROP-then-CREATE, per the trap above). Phase 2 (the one with the
  deadline, before more console routes land): API/console emit `app_id`. Phase 3: loader
  Cypher, `graph-tests/` (one line) and gate pages move over; `seal_id` becomes a deprecated
  alias still written. Module/file renames are phase 3+ and lowest value (G2). **Retiring
  `seal_id` is NOT decided here** (G3) — separate later gate, after the company side ports.
  This lands before any other wide structural port (G4).

- **A4 — CARVE-OUT.** Everything ruled here is SEALED except **§C1** (the site inventory,
  which goes stale if `seal-app-ref-edge-reshape` v2 re-targets `seal_attribution`) and
  **§D2** (whose "leave it" is judged against today's attribution grain). Those two — and
  only those — may be re-opened by the reshape v2 gate. D1 dropped off the carve-out: ruling
  (a) settles it either way. This is a THIRD disposition the spec did not offer; its own two
  were "rule both together" or "the later re-opens the earlier", both of which discard
  rulings the reshape never touches.

- **TEN SPEC DEFECTS found and fixed during the walk (v3.1–v3.3)** — every one the page
  misdescribing the repo it governs, which is the gate working as intended. Nine fall into
  two families: **a v2/v3 withdrawal whose dependents were never updated** (§D2's void
  option (b), §E1 + mapping n:7 + §G1's "neutral pair", §E2's stale option letter), and
  **an inventory that counted filenames instead of sites** (§D2's missing
  `seal_contacts:53` — the only site where the role segment is DATA; §C1's missing
  `manual_seal_attribution:41` — missed because that file already appears in the MERGE list;
  §F1's missing constraint names, then missing evidence vocabulary). The tenth is §B5's
  `SEALID` assumption. Recorded because the pattern predicts where the next one will be.

- **Effect:** map entry `business-application-identity` CREATED as `confirmed` (property-
  supplement shape). `config/taxonomy/business-application.yaml` `identifier` corrected to the
  source's real field name. Backlog **S3 unblocked** and its title/acceptance corrected — both
  still described the WITHDRAWN `app_id + id_authority` shape, so implementing to them would
  have written a property this gate deleted. **ADR 0010 must be AMENDED at S1** (its Option C
  and rules 2/3 assume the withdrawn shape). New items raised: glossary scaffolding, and the
  **TOM-roles gate** (the SME's live registry shows 9 distinct role classes against the signed
  7, with L1/L2/Operate Manager as three concepts — cannot fold into S3, because A1 declares
  the 2026-07-10 §B enumeration unchanged). Nothing written to the graph at the gate itself.

## 2026-07-27 — Self-documentation: DryDocs' own code in the graph (self-documentation-code-graph) — SIGNED OFF (G33 / Epic U)
- **Presented:** 36 confirmations across 9 sections (§A scope, §B Project root, §C node grain,
  §D dependency edge, §E SWO binding, §F collision safety, §G artifact shapes, §H ingestion, §I sign-off)
- **Confirmed:** 36 · **Edited:** 0 · **Rejected:** 0. SME took the agent recommendation on all
  eight decisions (B3, C3, D3, E1, F1, F3, G1, H4).
- **Ruling, in one line:** the code snapshot loads into `drydocs` under ONE `(:Project {project_id:'drydocs'})`
  root, as `:CodeModule` nodes keyed on `file_id`, with the six scan roots demoted to a property.

**THE GATE'S MAIN VALUE WAS CATCHING THAT G33 DESCRIBED AN ARTIFACT NOBODY HAD OPENED.** Three
stated premises did not survive reading the newest snapshot:
1. *"the `projects` key (=1)"* — it is **SIX** (drydocs, drydocs_core, drydocs_deepdoc,
   drydocs_lineage, drydocs_remediation, tests), and **142 of 183 nodes declare a project that is
   not `drydocs`**. The single root was therefore a modelling CHOICE presented as a read-off. §B1
   made it a choice and ruled (a).
2. *"664 nodes / 86 edges at the latest"* — that figure is from `tree-this-version.json`, a
   one-off **TREE-mode** capture (540 files + 124 dirs, `projects: ['drydocs1']`, a `CONTAINS`
   relationship). The rolling dependency snapshots are **183 files / 98 edges**. The real load is
   about a quarter the size the item implied.
3. Both shapes declare **the same schema string** `depgraph-machine-first/v1`. §G1 ruled the
   loader discriminates on `meta.tree` and refuses tree-mode, rather than trusting the string.

**Decisions and why:**
- **B1 (a)** — one `:Project`; the six are a `project` property. `HAS_MODULE` runs from the single
  root to all 183; "which of the six" is never answered by the edge.
- **B3 (a)** — a second `:Project` root from a company `snapshot.ps1` run is intended and fine.
  This makes §C5's deferral trigger LIVE; ruling (b) would have meant it could never fire.
- **C1 (a)** — `:CodeModule` keyed on `file_id`, one file = one module. **Decided by the SME's own
  question** — *"does the code carry a project-file-urn, so that `__init__.py` is attributed to the
  correct folder?"* Answering it killed dotted-module grain: there are **fifteen** `__init__.py`
  files, and `drydocs/loaders/__init__.py` **is** the package `drydocs.loaders`, which is also the
  directory name — so module-grain collapses file identity into package identity fifteen times over.
- **C4 evidence, from the same question** — the fifteen ARE correctly attributed today, but *only*
  by `file_id`. `name` collides fifteen ways; `rel_path` collides across the two roots. Folder
  attribution is a property of the key choice, not a separate mechanism.
- **C5 (NEW, DEFERRED)** — no URN exists in the artifact. `urn:dd:codemodule:<project>:<file_id>`
  deferred with a **named trigger**: when a second project tree enters the graph. Deliberately
  mirrors the `app_urn` precedent from the S3 gate — a deferral with a trigger is a more honest
  record than "not needed".
- **D2 (accepted limit)** — the snapshot cannot distinguish `import x` from `from x import y`, nor
  a `TYPE_CHECKING`-only import from a runtime one. **An `IMPORTS` edge must not be read as
  "breaks if removed".**
- **D3** — the M2 pull-provenance convention DOES apply; the no-edge-properties divergence rejected.
- **E1 (b)** — **first use of the SWO layer in the repo's history.** All 13 seeded terms had zero
  consumers. One edge, `IS_ENCODED_IN` → the seeded `SWO_0000118 Python`, realising the seeded
  `SWO_0000741 "is encoded in"`. Precedent set: bind to a seeded term that already means the thing,
  derive the value from data the artifact carries, invent nothing. Function-level binding rejected —
  a dependency snapshot does not know what a module implements.
- **F1** — `:CodeModule` and `:SoftwareProduct` are mutually exclusive, enforced as a **graph-test,
  not a constraint**: Neo4j cannot declare label mutual-exclusion. Second time this week a real
  invariant had to leave the constraint layer (cf. G35 §c singleton cardinality).
- **H4** — `abs_path` is **dropped**; producer-local machine state, and the same fact that made
  these files never-port in `PORT-MANIFEST.yaml` the same day.
- **H5 (scope honesty)** — the motivating query (module → loader → `:ControlMJob`) is **NOT
  delivered here.** Nothing in a dependency snapshot knows that `drydocs/loaders/controlm_jobs.py`
  produces `:ControlMJob` — that mapping lives in the loaders' Cypher, not their imports. The gate
  lands the subgraph and the shared database that make the join possible; the join is a second item.

**Two SME questions answered in the record rather than in chat:**
- *"do you have the Anthropic key needed for the software ontology API call during the load?"* —
  **There is no API call and no key is needed.** The 13 SWO terms are static `MERGE` statements;
  the IRIs are identifiers, not endpoints. Verified: `requests` / `httpx` / `urllib.request` /
  `aiohttp` appear **nowhere** in `drydocs/` or `drydocs_core/` — the load path has zero network
  egress. `ANTHROPIC_API_KEY` exists only for the **agents** module, which loaders never touch.
  Load-bearing, not trivia: offline + deterministic + re-runnable-from-committed-files is exactly
  what §H1's ADR 0002 D3 stateless test asserts, and a live lookup would break all three.
- **Dangling reference found while checking:** `ontology.cypher:109` says the ~250-term SDLC subset
  *"loads from `ontology/reference/swo_sdlc_ontology.cypher`"*. **That file does not exist.** Logged
  to IDEAS; it retroactively justifies §A4's exclusion — the wider set is not loadable, it is buildable.

**Enacted at sign-off (nothing written to the graph):** 2 node classifications (`:Project`,
`:CodeModule`) + 3 edge terms (`u1_has_module`, `u1_imports`, `u1_is_encoded_in`) registered
`status: planned`; `self-documentation-code-graph` map entry → `confirmed` (map now 22 confirmed);
`schema_graph.cypher`, `gates.json` and the enforcement matrix regenerated; backlog **G33 cleared to
build** with its three premise errors corrected.

## 2026-07-29 — FB-04 · Agent Test harness — UI surface ruling (SME sign-off)
- **Presented:** 1 decision — harness shape + delivery path for the real-time
  agent test view (the live twin of Under the Hood).
- **Confirmed (SME):** deliver as an **independent standalone page**
  (`web/public/agent-test.html`, ships verbatim inside `web/dist`) instead of a
  console fold-in: dark view only, **no authentication layer**, no shell, only
  working controls (module picker · agent readout · ADK URL · SME request ·
  Run). Five-section run anatomy stands: interpretation → Cypher → return path
  → answer → metrics. Read-only throughout (O20). Ship on `main` so the company
  port can test with live data — the page binds the real ADK URL through its
  own input, zero code edits on port.
- **Edited:** the same-day SPA fold-in (route + nav + `AgentTestRoute.tsx`)
  removed in favor of the standalone page. FB-03's role designation of
  `gates` / `under-the-hood` (registry `access` + guards) **stands** — the
  no-auth ruling applies to this standalone page only.
- **Rejected:** 0
- **Notes:** live path = ADK api_server (`list-apps → session → run`);
  unreachable → SYNTHESIZED demo trace behind the standard EXAMPLE DATA tag.
  R2's router should wire THIS harness when it lands (R5 Ask-spoke seat note in
  IDEAS.md, 2026-07-29).

## 2026-07-31 — Source-registry schema v2: system/dataset split, qualified replica ids, overlay, URN, reconcile guard (source-registry-v2) — SIGNED OFF (N7)

- **Scope:** the registry-redesign terminus — the four coupled decisions the N7
  acceptance names as ONE design, plus open questions Q1–Q6, decided FROM
  internal/registry-redesign/REGISTRY-PLAN.md (plan of record 2026-07-31).
  Guided in-chat session (chad.wilson); prompt authored from the session record
  (config/gate-prompts/source-registry-v2.yaml). 10 rulings; 2 SME amendments;
  1 explicit residual.
- **Confirmed: 10 · Amended: 2 (D1, Q1) · Rejected: 0 · Residual: 1**
  - **D1 — two-level identity, ADOPTED with amendment:** SYSTEM rows
    (connection/locator/classification/SDLC) split from DATASET rows
    (gate/crosswalk/feeds_taxonomy/authority, each with its OWN confirmed);
    loaders bind to the DATASET; datasets tagged by ontology domain.
    **AMENDMENT: seal_id is a standing PLACEHOLDER field on every committed
    system row** — real value internal-twin only (the ccb-twin convention).
  - **D2 — per-side loader→source_id overlay, ADOPTED:** per-repo config wins
    over class defaults, guarded to resolve to registered dataset ids
    (extends J21). The company T19 rebind seam — config, not code.
  - **D3 — URN handle, ADOPTED:** urn:drydocs:dataset:({carrier-or-origin},
    {artifact},prod), lowercase, derived deterministically (a render, never a
    hand-maintained field).
  - **D4 — reconcile guard, ADOPTED:** renamed rows carry replaces: <old-id>;
    retired ids land in a refusal list; SourceRegistry.from_yaml AND the
    overlay guard refuse any retired id — same-string-different-meaning (the
    T19 failure) becomes structurally impossible.
  - **Q1 — id grammar, @ KEPT with amendment:** replica/derived ids =
    **{origin}@{db}.{schema}.{table}** — all dots after @, and the qualified
    segment is the ACTUAL carrier locator, REPLACING the informal system
    nickname (SME worked example: controlm@[db].[schema].cm_def_vjob);
    born-here datasets = {system}:{artifact}; **lowercase throughout**.
    Real db/schema values are connection coordinates → internal twin only;
    committed producer ids carry [db].[schema] placeholders.
  - **Q2 — URN env segment: always prod** (promotion-clone/lag not modeled).
  - **Q3 — derived stores:** @ grammar + derived: true; authority OMITTED —
    not SOR/ADS, and FCDO SOC was checked (§H vocabulary: System of Capture =
    upstream ingestion feeding an SOR) and does not fit downstream transforms.
  - **Q4 — snow registers NOW as a SaaS system;** first dataset =
    snow:cmdb-ci-classes (the sampled CMDB class export), doubling as the
    crosswalk source for every system row's cmdb_ci field.
  - **Q5 — design-docs: pipeline-side only** (feeds graph classes beyond
    Document/Chunk); the doc-registry twin drops — one home per source.
  - **Q6 — signed-off gates TRANSFER across renames** (identity refactoring,
    not meaning change): one gate-log amendment entry maps old→new ids at the
    build; re-gating reserved for actual meaning changes (which D4 catches).
- **T19 naming note (recorded in the docs/port-prompt.md divergence ledger):**
  the catalog feed's replacement dataset name is **pat:product-catalog**
  (industry-standard naming — matches NEITHER legacy string, so neither
  repo's wrong value survives); the PAT people report splits out as
  pat:people-report. Feeds the company T19 gate review; producer sign-off
  never substitutes for it.
- **RESIDUAL (explicitly deferred with reason):** the 18-row migration table
  is NOT block-confirmed — the SME closed the session's HITL portion after
  the shape rulings; each row confirms individually at the build. Previously
  signed rows transfer per Q6; everything else lands confirmed: false.
- **Effect:** N7 done. The build grooms as **N9** (schema v2 + migration +
  overlay seam + retired-id refusal + URN render + render/guard updates + the
  doc-twin drops + the snow system row) — nothing changes shape before N9
  lands; J21's hardening of the CURRENT registry remains the interim
  guarantee. The classification collapse (J23) already landed pre-gate as
  machinery removal. Output feeds the company T19 review, not a port.

## 2026-07-31 — AMENDMENT: source-registry v2 id migration — old→new id map (N9 build; gate source-registry-v2 Q6)

**One amendment entry, per the Q6 ruling:** existing signed-off gates TRANSFER to the renamed
dataset rows as-is (rename = identity refactoring, not meaning change); this entry maps every
old id to its replacement so gate-log history keyed on v1 ids stays traceable. The D4 refusal
list in `config/source-registry.yaml` refuses every old id from here on.

| v1 flat id (retired) | v2 replacement(s) | transferred gate(s) |
|---|---|---|
| `controlm-psgmgr` | `controlm@[db].psgmgr.cm_def_vtab` · `cm_def_vjob` · `cm_def_lnki_p_vw` · `cm_def_lnko_p_vw` · `cm_def_setvar_vw` (confirmed: controlm-q1q3-phase1 2026-07-07) · `cm_hosts` (controlm-hosts-topology 2026-07-09) · `cm_avg_run` (controlm-avg-run-supplement 2026-07-14 — the v1 umbrella note still said AWAITING SME; stale since 07-14, corrected at this per-row sweep) | q1q3-phase1 · hosts-topology · avg-run-supplement |
| `catalog-pat` / `pat-catalog` | `pat:product-catalog` + `pat:people-report` (the T19 naming ruling — neither legacy string survives; BOTH retired) | catalog-hierarchy rulings 2026-06-21 · C9 2026-07-18 |
| `seal-extract` | `seal:app-extract` | (live M1 chain) |
| `stg-app-fact` | `controlm@[db].drydocs_stg.stg_app_fact` (derived: true, Q3) | seal-attribution-match-policy 2026-07-14 |
| `autosys-export` / `airflow-mwaa` | `autosys:export` / `airflow:dag-export` | autosys-crosswalk / airflow-crosswalk 2026-07-14 |
| `software-registry` | `repo:software-registry` | software-registry gate 2026-07-07 (ADR 0004) |
| `depgraph-snapshot` | `repo:depgraph-snapshot` | self-documentation-code-graph 2026-07-27 |
| `design-docs` | `repo:design-docs` | doc-traceability-feedback 2026-07-20 |
| `controlm-xml-export` | `controlm:deftable-xml-export` | (unconfirmed — open precedence ruling stands) |
| `rua-inventory` | `exec-hosts:rua-bundle` | (unconfirmed — G22 pending) |
| `dpl-registry` | `dpl:pipeline-registry` + `dpl:dataset-registry` | (unconfirmed — G22 f/g) |
| `snowflake-data-catalog` | `catalog@[db].[schema].datasets_v` + `distributions_v` | (unconfirmed — gate prompt not drafted) |
| `code-repo` | `bitbucket:repo-objects-manifest` | (unconfirmed — G22) |
| `oracle-schemas` / `snowflake` | `oracle:schema-inventory` / `snowflake:schema-inventory` | (unconfirmed placeholders) |
| `bmc-docs` / `essential-graphrag` / `fcdo-frameworks` | NOT renamed — pipeline twins dropped; ids stay live in `config/doc-source-registry.yaml` (one home), which now carries their `confirmed:` state | bmc-docs-lexical-load 2026-07-08 (covers essential-graphrag per the Q2 groom) |

**Per-row residual executed:** every row above was confirmed individually at the N9 build
(the N7 residual). New rows registered: `seal@[db].psgmgr.cm_escalation_db` (the gate's worked
example), `controlm@[db].psgmgr.cm_hist_vw` (gives jobrun-observation a citable feed),
`snow` system + `snow:cmdb-ci-classes` (Q4). Anything that would CHANGE meaning (not rename)
goes back to the SME — none arose.

## 2026-08-01 — PARTIAL RULING: PAT grain keying (C17; gate `seal-app-ref-edge-reshape` §G6-RIDER)

**Scope of this entry.** The §G6-RIDER questions only. The
`seal-app-ref-edge-reshape` gate as a whole is **still unsigned** — nothing in
§A–§F or the rest of §G is ruled here, and §H is untouched. This is logged as a
partial ruling rather than a sign-off because the SME answered one rider's
question in-chat, not the gate.

**The SME fact that decided it (2026-08-01, user, in-chat):** on the company
side **LoB, Sub-LoB, Product Line, Product and Area Product each carry a numeric
ID field.**

That inverts the rider's premise. The rider read the PAT team report's name-only
Product Line column as a property of the SOURCE; it is a property of the REPORT.
The id exists at every grain — the team report just does not project it.

- **§a — RULED: option (a). A product-line-scoped extract supplies
  `product_line_id`.** Name → id resolution (option b) is **not** adopted as the
  mechanism. It survives only as a bounded migration path for extracts already
  captured without the column, and even then reports ambiguity counts rather
  than picking a winner. `ProductLineRow.product_line_id` stays REQUIRED, which
  is what makes the ruling executable: while it is required, the name-only team
  report cannot load product lines at all, so a name cannot become the de-facto
  key by accident. Corroborated independently of the SME by
  `internal/fcdo-reference` (the PAT-catalog artifact described as a 5-level
  hierarchy with "native IDs at each level") and by the company's own 5-field
  `pat_lob_sublob_productline.csv` — an extract already at that grain.
- **§b — RECORDED: `area_product_id` is the SUPPORTING area product.**
  Sponsoring rides `sponsored_area_product_id`. The field name stays
  unqualified deliberately: the qualification is REPORT-SPECIFIC (a sibling
  member-level report carries a plain unqualified "Area Product" meaning the
  supporting one), so the unqualified name is the union of both spellings and
  the field description is the join key. The two sponsoring columns are
  **co-populated, not exclusive** — cypher §3a/§3b firing independently is
  correct and intended. No write changed.
- **§c — RULED OUT OF SCOPE: Sponsoring Product Line.** The third sponsoring
  form is name-only, and modelling it would mean MERGEing a `:ProductLine` on a
  name — exactly what §a forbids. It becomes modellable the day the extract
  carries a sponsoring product-line ID, and not before. Closes C9 §d's coverage
  question.
- **§d — BUILT.** `_catalog_id` on every id field across the catalog row models;
  `products.cypher` reworked; drift guards in `tests/unit/test_catalog_keying.py`.

**What the fact exposed that the rider did not ask about.** Our node keys are
strings and pydantic v2 does not coerce a number to a string, so a numerically
typed read of the real feed rejected **every** catalog row, not some of them —
verified against the shipped models before the fix. `attribution.py` already
carried this coercion for the Control-M keys; the catalog loaders never got it.
The coercion refuses a fractional id rather than rounding it, and normalizes
integral floats (a nullable numeric column read through pandas arrives as
float64, where a blind `str()` keys the node `'12345.0'` and MERGEs a duplicate
beside the real one).

**Corollary applied, and its limit.** Having ruled the join is BY ID, the id
join must not fail silently either — otherwise the silence just moves from
"which key?" to "did it match?". `products.cypher` had a hard `MATCH` on the
parent placed AFTER the Product `MERGE`, so an unresolvable parent produced a
real Product with no parent edge and `orphan: false` still set from `ON CREATE`
— unparented and reporting itself as fine, with an `orphan` flag no code path
could ever set true. It is now `OPTIONAL MATCH` + a per-run flag plus
`orphan_parent_product_line_id`, so the gap is a query. The **identical shape in
`product_lines.cypher` and `area_products.cypher` was left alone and inboxed**:
changing four loaders' write behaviour on one item's authority is the drive-by
this log exists to prevent.

**NOT decided here.** The SME fact names a **Sub-LoB** grain we do not model at
all (no `:SubLOB`, not even `status: planned`). Introducing it is an ontology
decision, and it already belongs to the parked company-catalog back-flow item
(`IDEAS.md`, 2026-07-27) whose trigger is the COMPANY gate's own sign-off.
Recorded, not built.

## 2026-08-03 — RECORD: schema meta-graph database `ddschema` provisioned (G51; SME direction "2 different graphs", 2026-08-02)

- **What this records:** the in-chat SME direction of 2026-08-02 that created a second
  graph — the schema meta-graph goes to its OWN database (`ddschema`), not `drydocs` —
  and its enactment at G51. Direction, not a gate session: no ontology edge, no vocab
  status change, zero writes to `drydocs`.
- **Why a second database:** exemplar nodes carry the REAL label beside `:SchemaMeta`
  (that is what `db.schema.visualization()` reads), and `drydocs`' NODE KEYs enforce
  property EXISTENCE the exemplars do not have — proven live on a throwaway label
  (`ZZProbe`) at the C21 build rather than inferred.
- **Enacted at G51:** `01_databases.cypher` creates `ddschema` (NOT aliased into
  `ddall` — schema description, not estate data); ADR 0002 amended (dated section);
  `test_database_names.py` widened from exact-identifier `DATABASE` to any
  `*DATABASE*` constant — the guard that let `SCHEMA_GRAPH_DATABASE` name an
  unprovisioned database through a green suite. `EXPECTED_CONSTRAINTS` unchanged:
  `schemameta_name` lives in `schema_graph.cypher` by design.


## 2026-08-03 -- GATE: dqv-seed-disposition (backlog C23) -- SME-RULED: DEFER

- **Question:** the DQV quality seed (10 `:Metric` + 5 `:Dimension` + 10 `IN_DIMENSION`
  edges, written at bootstrap by `ontology.cypher`) has no upstream measurement leg and
  predates the vocabulary discipline entirely. Build the designed writers, defer with a
  recorded trigger, or prune the seed? Raised by the SME post graph-wipe: the one query
  that survived showed metrics associated with nothing.
- **Ruling (SME in-chat, 2026-08-03): DEFER.** The seed stays as a REFERENCE catalog.
  BUILD was declined honestly -- no producer-side TDQ/control-file measurement feed
  exists, so writers would have nothing to write. PRUNE was declined because the catalog
  is not fully orphaned: the shipped SOSA `Result` and temporal-runtime `cm_avg_run`
  vocabulary notes both reference `dqv:QualityMeasurement` (`freshness_sla` is a seeded
  metric name), making the temporal-runtime freshness observations the catalog's first
  real customer.
- **Revival trigger (recorded in `ontology.cypher` above the seed):** the first
  measurement feed -- expected to be the temporal-runtime freshness observations. When
  it lands, groom the writer items and flip the planned edges.
- **Vocabulary gap closed:** four `c23_*` entries in `relationship_vocabulary.yaml`
  (new `quality` domain) -- `c23_in_dimension` ACTIVE (bootstrap-written, registered
  retroactively), `c23_is_measurement_of` / `c23_computed_on` / `c23_has_quality`
  PLANNED per LoadPlanV2 section 4.4 shapes (measurement -> Metric, measurement ->
  Dataset, Dataset -> measurement).
- **No graph write, no constraint change:** `measurement_id` / `metric_name` /
  `dimension_name` stay; `EXPECTED_CONSTRAINTS` unchanged at 52.
  `sdlc-neo4j-schema.md`'s declared-but-never-loaded row now cites this ruling.

## 2026-08-03 — GATE: seal-app-ref-edge-reshape (backlog K7) — SIGNED OFF, 24/24

**Scope.** The Application ↔ Control-M attribution CLOSE-OUT gate, opened by user
direction 2026-07-22 ("close out the mapping for any relationships that need to be
defined or manually overwritten until fixed — the application to Control-M folders").
Spec v3 (2026-07-27), 8 sections, 25 confirmations. §G6-RIDER was ruled earlier as a
PARTIAL RULING (2026-08-01, C17, PAT grain keying) and is NOT re-opened here; the
remaining 24 are ruled below. SME chad.wilson, in-session chat gate. Nothing in this
entry writes the graph — vocabulary lands `planned`, the loader follows at the build
items §F2 opens.

**Procedural note worth keeping.** The spec existed from 2026-07-15 and reached v3 on
2026-07-27, but no backlog item ever owned RUNNING it, so it sat unsigned for six weeks.
K7 was groomed the same day it was run. The renderer defect that hid it — a gate whose
prompt file is merely CITED by other entries never appears in the open-gates list — is
backlog J28.

### Per-item outcomes

| # | Outcome |
|---|---------|
| A1 | CONFIRMED — attribution grain is FOLDER-level; jobs inherit via `CONTAINS_JOB`; no per-job application edge is authored going forward. The K2 job-level model is corrected, not extended. |
| A2 | CONFIRMED — `explorer.folder-applications.v1` keeps deriving through job edges, and says so on the surface, until it re-binds to the gated folder edge at build. |
| B1 | CONFIRMED WITH EDIT — ONE authoring mechanism: code-level rows, loader fans out to folders via `m3_contains_folder`. `tier` is a ROW PROPERTY, not a structural split. Decided on NEW FOLDERS: under fan-out a new folder inherits attribution the moment it appears; per-folder authoring would leave it unmapped until a generator was re-run, and unmapped-by-default is how coverage silently rots. |
| B2 | CONFIRMED, THEN AMENDED IN SESSION — THREE tiers, not two: tier 1 seal-born (1:1 code to application); tier 2 shared platform code (resolved per folder); **tier 3 DUAL-CODED/MIGRATING (NEW)** — a team has stood up its own Control-M app code and is moving to it while still running workload under the platform code; both attributions are simultaneously correct. Tier 3 is DECLARED with an explicit end state, so a stalled migration cannot become permanent ambiguity. AMENDMENT: the original wording made `:AreaProduct` a 1:many TARGET; it is a ROUTING step (see below). Unresolved folders SURFACE to the steward and are never auto-picked. |
| B3 | CONFIRMED WITH A FENCE — the K2 fuzzy match policy (SEAL, then FID, then APP_NAME, then ALIAS; signed 2026-07-14) DEMOTES to fallback for codes with no defined row. Its internals are NOT re-opened. ADDED: every fallback-derived value is DISCLOSED via the origin flag (`defined`, `matched-fallback`, `override`, `manual-pin`) — matched attribution is never presented as though it were defined. |
| C1 | RULED (b) — the tier-1 target is the application's BatchProcessing `:Port`, not `:BusinessApplication`. **Rationale is supernode avoidance, not preference:** the app node already hubs TOM roles, contacts, product links and orchestrator edges; hanging every folder off it concentrates batch topology on the node that can least afford it. The port is the batch-facing side, the app node stays a record rather than a junction. Side effect: §G5 port confirmation becomes derivable with no separate trigger. |
| C2 | RULED — RETIRE. `arch_contains_batch` and `arch_contains_folder` flip `planned` to `deprecated`; the SME named no live use for a distinct `:Batch` node. **Do not confuse the twins:** `m3_contains_folder` (`:ControlMApplication` to `:ControlMFolder`) is a DIFFERENT, ACTIVE edge and is the fan-out path B1 depends on. |
| D1 | RULED (a) — LOCAL domain edge, `prov_maps_to: ~`, label **`BELONGS_TO_APPLICATION`**. `:ControlMFolder` (Collection, subclass of Entity) to `:Port` is an Entity-to-Entity governance/containment fact with no natural PROV verb (the `SCHEDULED_ON` / `reg_uses_software` precedent). Option (b) `prov:used` REJECTED: it type-checks only from an Activity, so it would force keeping a job-side edge alive and contradict A1. Label chosen over `ATTRIBUTED_TO_APPLICATION` because containment is what the fact is, and it reads beside `CONTAINS_FOLDER`. |
| D2 | CONFIRMED — one shape everywhere: loader edge, manual tier-5 writer `SUPPORTED_SHAPE`, migration target. |
| E1 | CONFIRMED — override mechanics reuse the O24 origin-flagged store verbatim: committed CSV in `config/overrides/` to `mapping.db` to the `/mappings` console (steward persona); every surface shows ORIGIN; corrections feed a source-corrections report addressed to whoever owns the actual fix. |
| E2 | CONFIRMED WITH EDIT — defined-mapping rows ARE a graph-loadable source of record; there is no machine feed to defer to, so refusing store-to-graph here would mean the mapping cannot exist. **EDIT: overrides may be PERMANENT in this domain** — the folder-to-application relation runs through a platform code, so an override is not patching a value awaiting an upstream fix; the arrangement is the arrangement. **Permanence is DOMAIN-DEPENDENT** (the SME fact that decided it): application-to-support-team and application-to-operate-manager overrides ARE temporary, months-long, and keep the corrected-in-source lifecycle. The GENERAL override-vs-precedence question (ui-write-surface) stays **OPEN** for other domains; this gate contributes the domain-dependence finding as evidence for whoever runs it. |
| E3 | CONFIRMED — store rows never write the graph directly; the loader remains the only graph writer (O20 unchanged). |
| F1 | CONFIRMED, RE-SCOPED — producer-side this is moot under wipe-and-rebuild: a reload at the new shape IS the migration, so no migration artifact is authored here. Company-side it is NOT moot (G4-RIDER (a): real legacy state, ports already active by derivation, manual pins a wipe would destroy). That migration is theirs under guardrail 6 and tracker T23, and becomes a port-ledger obligation rather than a producer build item. |
| F2 | CONFIRMED, AMENDED — the page listed a separate "tier-2 edge" to register; there is none now that `:AreaProduct` is routing. ADDED: the folder 1:1 graph-test. Change-set = folder edge registered `planned`; `:Batch` retirement; map entries `app-code-defined-mapping` and `job-seal-app-ref` updated; mapping-store domain and `K2_SHAPE` in `drydocs_api/mappings.py`; manual-loads template rekeyed to `app_code`; explorer specs re-bound; 1:1 graph-test; this transcription; `gates.json` regenerated. |
| G1 | CONFIRMED — the act is ORCHESTRATOR-FIRST: the steward picks the orchestrator before the folder filter, and that choice AUTHORS `(:BusinessApplication)-[:USES_SOFTWARE]->(:SoftwareProduct {role: orchestrator})`. The edge is created BY the confirmed mapping, never derived from a declaration. Folder filter is scoped to the picked orchestrator. |
| G2 | CONFIRMED, EXISTING EDGES RULED — the SEAL-declared `batch_orchestrator` string demotes to PREFILL. Existing `USES_SOFTWARE {source: 'batch-port'}` edges are **KEPT with `origin=declared` until a confirmation supersedes them** — no cleanup sweep. Forward-looking demotion: each edge is corrected when a steward actually confirms that mapping. Cheaper than the `migrate_pat_alignment_c9.cypher` precedent, and it never destroys a value nothing has replaced. |
| G3 | CONFIRMED — orchestrator cardinality is 1:N. (a) NEVER a uniqueness constraint — graph-TEST instead (the TOM-roles lesson); (b) the declared side is structurally 1:1 today and must become multi-valued before G2 can prefill honestly; (c) mid-migration is a NORMAL state and must never be reported as drift. |
| G4 | RULED (b) — `active_state` **PER PORT** (`declared` or `confirmed`) REPLACES the `active` boolean, with `declared_by/at` and `confirmed_by/at/run_id`. The boolean is safe to drop producer-side: it is created `false` and never written true or read anywhere. SME correction to the agent's proposal: activation state is per-PORT, not per-orchestrator — the port answers "does this app run batch", the 1:N `USES_SOFTWARE` edges answer "scheduled by whom". Nothing collapses, because the orchestrator dimension lives on its own edge instead of being duplicated into the port flag. |
| G4-RIDER | RULED — company ports already `active` by derivation are **GRANDFATHERED as `confirmed`**, provenance recorded as the Control-M app-code link. Because the initial series loads **Control-M only** (AutoSys follows once mapped better), the deriving orchestrator is unambiguous and no disambiguation pass is needed. |
| G5 | CONFIRMED — C1(b) makes the two consistent by construction: the folder attaches to the Batch `:Port`, so "the relationship to the folders is created" IS that edge and confirmation is derivable with no separate trigger; the company's existing app-code-link derivation lines up rather than needing re-pointing. EVENT PORT: **declared-only** until an event source is onboarded — evidence-backed, since neither app-code loader touches the event port. |
| G6 | RULED — the **COMPANY reading** of `(:Product)-[:HAS_APPLICATION]->(:BusinessApplication)`: a structural SUPPORT link, a Product supported by 2 or more applications (front-end/back-end), NOT the producer's "a Product owns a set of SEAL-registered applications". Chosen because the company reading is backed by a live extract and loader where the producer's is an unbuilt intention. Rider (ii) follows by entailment: the edge is 1:many by design, so the picker returns a LIST, never a single application. This is a BACK-FLOW to reconcile, not new build. |
| G7 | CONFIRMED — E3 verbatim: the screen drafts a mapping-store row, the loader writes. The SME check/approval plus notes/user/date ARE the O13 mandatory-rationale and lifecycle chips (draft, submitted, gated, loaded) and become the confirmed edge's provenance (`origin`, `confirmed_by`, `confirmed_at`) — which is also what satisfies G4's confirmation stamp, so the two mechanisms are ONE. "Available folders" = **unmapped only, with naming-pattern as an OPTIONAL filter layered on top** — the pattern cannot be primary, given the naming-convention doc's own warning that a folder name does not reliably identify an application. ADDED by SME: `run_as_user` surfaced on the screen as a sort option. |
| H | **SIGNED OFF** — chad.wilson, 2026-08-03. |

### Rulings that emerged in session and were not on the page

- **OWNER-NOT-USER.** A folder belongs to whoever OWNS it, not whoever USES it. Three SME
  cases collapse to this one rule: a batch data-processing folder attributes to its one
  application; a platform team's all-tenants utility folder attributes to the PLATFORM
  TEAM's application, not fanned out across the tenants it serves; the Control-M platform's
  own cross-data-center ordering folders attribute to one SEAL, the platform's own. The rule
  is worth more than the cases because it decides the next case nobody has thought of yet.
- **Folder to application is 1:1.** There is no legitimate 1:many, so a folder carrying two
  application edges is a DEFECT, not a state. Enforced as a GRAPH-TEST: Neo4j cannot declare
  relationship cardinality any more than it could declare the TOM-roles singleton. Note this
  points the OPPOSITE way to G3's 1:N orchestrator ruling and both are right — neither is
  declarable, and each follows its own reality.
- **`:AreaProduct` is a ROUTING step, not a target.** The SME fact that decided it: *there is
  no direct mapping of batch technical components to area product.* A folder and a job are
  technical objects; an area product is an org/catalog grain. Wiring them would assert a
  correspondence the source does not carry — the same failure C17's grain ruling turned on.
  Consequence: every folder edge lands on a `:Port`, uniformly, which is what makes D2's
  one-shape rule true rather than aspirational. The AreaProduct layer stays load-bearing as
  steward-UI routing rather than as graph structure — a materially smaller obligation than
  `lob-product-team.yaml` open question `area-product-missing` assumed.
- **Tier 3 and G3 are the same lesson on two axes:** mid-migration is a normal state, not a
  conflict. Dual-coded applications and multi-orchestrator applications both have to be
  representable without being reported as drift.
- **Bulk authoring CLOSED** — B1's fan-out already covers every folder under a code, so no
  naming-convention pattern persists as a first-class object. Revisit only if cross-code
  editing becomes a real burden.

### Evidence gathered during the session

- **Company-side implementation read (screenshot, structure only).** Both ports are seeded
  `active = false` `ON CREATE` on every `:BusinessApplication` (`seal_applications.cypher`);
  `ON CREATE` means a later SEAL reload will not reset it. **Two writers flip it true**, not
  one: `controlm_app_codes.cypher` when a Control-M 3-char app code resolves to that
  `seal_id`, and an AutoSys twin `autosys_app_codes.cypher`. G4-RIDER knew only about the
  Control-M one. Consequences: G1 is corroborated harder than the rider argued — AutoSys is
  not hypothetical company-side, the split has already been built twice; and the current
  boolean MERGES the two writers, so `active = true` today means "scheduled by Control-M or
  AutoSys, we do not know which", which is exactly what per-port state plus 1:N
  `USES_SOFTWARE` edges separates cleanly. Nothing from the capture is transcribed beyond
  mechanism (PUBLISH-BOUNDARY.md).
- **BMC vendor corpus searched for the platform-ordering folder token** (374 chunks,
  `drydocs` database). `Order Method` has three values — Automatic (Daily), None (Manual),
  **Specific User Daily** — and `User Daily name` defines "User Daily jobs whose sole purpose
  is to order jobs". No name EXAMPLES exist in the corpus, and the SaaS/API doc drops
  Specific User Daily entirely. This corroborates owner-not-user from the vendor side: a User
  Daily folder is scheduling INFRASTRUCTURE, not business workload, so attributing it to the
  Control-M platform's own SEAL is what the object actually is. The token's expansion is
  recorded SME-attested, not vendor-confirmed, in
  `knowledge/standards/technology/folder-naming-convention.md`. The extract carries the Order
  Method column, so deriving this folder class from a FIELD rather than a name pattern is
  available — deliberately NOT taken now, recorded so nobody rediscovers it cold.

### Guard-scope note

This is a GATE commit. Per port-prompt guardrail 7 the J7 no-downgrade guards are
PORT-scoped and must not be run across it: `arch_contains_batch` and `arch_contains_folder`
moving `planned` to `deprecated` is an AUTHORIZED downgrade, and this entry is its authority.

## 2026-08-04 — GATE: audit-envelope-phase4 (backlog M3) — SIGNED OFF, 13/13

**Spec:** `config/gate-prompts/audit-envelope-phase4.yaml` · **SME:** chad.wilson, in-chat
(desktop session). Doc 06 Phase 4 for the four remaining non-Control-M sources. The
controlm-family stubs (link views, setvar, cm_hosts, cm_avg_run, stg_app_fact) were
explicitly OUT of scope (A1) and stay stubs pending their own census/riders.

| Item | Ruling |
|---|---|
| A1 scope | **CONFIRMED** — four sources only. |
| A2 internal-twin clause | **CONFIRMED discharged** — the SEAL and PAT field inventories are already committed Internal-Public as loader-field mechanism (S3 §B1(c) ledger, catalog row models); nothing confidential remains to author internal-side. A future census that surfaces differing AND sensitive real headers owns its own split. |
| B1/B2 seal:app-extract | **B2 — RULED STUB**, on SME evidence that REVERSED the page's B1 recommendation (see below). |
| B3 certification columns | **CONFIRMED** — `last_certified_by_sid`/`last_certified_date` excluded: certification is attestation, not modification. `capture_date` stays excluded (standing CAPTURE_DATE rule). |
| B4 contact extract | **CONFIRMED** — 5 fields, no audit columns, nothing to map. |
| C1 pat:product-catalog | **CONFIRMED** — ruled stub-until-projected: the report extracts project zero audit columns; NOT permanent (the C17 lesson — the backing store has more than the report projects). |
| C2 pat:people-report | **CONFIRMED** — same ruling; `valid_from`/`valid_to` are role-validity, never authorship (recorded so nobody maps validity onto the envelope later). |
| D1 repo:software-registry | **CONFIRMED** — ruled PERMANENT stub: git history (commit author/date) is the audit envelope; closes the repo-committed trio with design-docs and depgraph-snapshot. |
| E1–E3 consequences | **CONFIRMED** — B2 branch: no cypher change; all four entries stay `status: stub` with this gate cited in their notes (the bmc-docs mechanism); Phase 4 recorded done for these sources in doc 06; the audit-fields port disposition is already covered mechanically by PORT-MANIFEST `config/**` canonical-producer. |

### The §B evidence (SME, in-session — the ruling's basis; mechanism only)

The SEAL registry's date fields are **onboarding-lifecycle milestones, not record audit**.
The registry has a two-era data story: under the current phased onboarding process
(develop → build → operate permits) the planned/actual lifecycle dates are captured;
**legacy applications lack those fields entirely** (SME showed three live examples —
one current-era record with full planned/actual pairs, two legacy records with sparse
actual-only dates). Until an application reaches its operate permit it is supported by
its dev teams; logical deployments follow the same pattern. The row model itself files
`creation_date` in its lifecycle block. So `creation_date` is a lifecycle fact with
era-dependent capture, not "when this record was created in the source" — it cannot
honestly feed `source_created_at`.

**Revisit trigger (recorded):** the registry UI exposes a per-application **audit
download** — a true record-audit trail exists source-side; the extract simply does not
carry it. If an audit export is ever ingested, THAT is the envelope source, and this
gate re-runs against its columns.

## 2026-08-04 — GATE: envelope-property-terms (backlog M4) — SIGNED OFF, 10/10

**Spec:** `config/gate-prompts/envelope-property-terms.yaml` · **SME:** chad.wilson,
in-chat (same session as audit-envelope-phase4). Property-level standard-term bindings
for the four frozen envelope properties, and the registry home for property-term
bindings. Documentation-grade: no graph write, no edge change, no loader change, no
rename of the frozen names.

| Item | Ruling |
|---|---|
| A1 binding is documentation-grade | **CONFIRMED**. |
| A2 SOSA ruled OUT | **CONFIRMED** — authorship provenance is not observation; SOSA stays in the experimental context-graph layer. |
| B1 the uncontested trio | **CONFIRMED** — `source_created_by` → `dct:creator`, `source_created_at` → `dct:created`, `source_updated_at` → `dct:modified`. |
| B2/B3 the contested row | **B2 — `source_updated_by` → `dct:contributor`**, with the imprecision recorded in the entry note (DCMI defines no "modifier"; nearest term, same vocabulary family as the trio). |
| C1/C2 registry home | **C1 — a new `property_terms` section in `relationship_vocabulary.yaml`** — the file already carries node_classifications, so it is the ontology registry; one file for the mapper agent and the drift guards. |
| D1–D2 consequences | **CONFIRMED** — `dct:` (http://purl.org/dc/terms/) registered in namespaces.py + the ontology.cypher comment sync; `reference/standards/dcmi-terms/` stub added; drift guards extend (every envelope property carries a binding; every binding CURIE expands via `namespaces.expand()`). |


## 2026-08-04 — RECORD: `ddlineage` retired from the deployed topology (X1; user ruling in-chat, 2026-08-04)

- **What this records:** the in-chat user ruling of 2026-08-04 retiring `ddlineage`
  from the provisioned topology, and its enactment path (Epic X). A record on the G51
  idiom — direction, not a gate session: no ontology edge, no vocabulary status
  change, zero writes to `drydocs`. ADR 0002 carries the dated amendment; the ADR's
  own residency clause routes topology change through an amendment, and this entry is
  the record it points at.
- **The evidence acted on (standing since G30, re-confirmed at the same-day census):**
  nothing writes `ddlineage` (writer pinned to `drydocs` with `TrustBoundaryError`,
  D2) and nothing reads it (the four specs repointed at G30; the read-set allow-list
  excludes it; `test_database_names.py` proves read targets have writers). Its only
  remaining function was to exist empty on every host — the exact gap the G28 and G30
  drift classes grew in.
- **What stays deferred:** the proxy-node-spine design question transfers intact to
  the residency clarification's named revisit trigger. Reopening now recreates the
  database (one DDL line + the `ddall` alias) instead of finding it waiting.
- **Enactment owned by:** X2 (live-surface repo sweep + port-ledger company caution —
  their `ddlineage` drops by their hand), X3/X4 (per-machine drops behind zero-node
  emptiness probes; a non-empty probe stops as a defect report).


## 2026-08-05 — GATE: fcdo-crosswalk (Epic W; drafted at W1) — SIGNED OFF, 13/13 (row 5 stays blocked-on-recapture)

**Spec:** `config/gate-prompts/fcdo-crosswalk.yaml` · **SME:** chad.wilson, in-chat
(section walkthrough; page rendered to `internal-local/gate-pages/`). The DryDocs ↔
firmwide-framework vocabulary crosswalk (`config/crosswalks/fcdo-vocabulary.yaml`,
8 rows). Ratifies the ALIGNMENT-PLAN verdict: already structurally aligned — every
row maps an EXISTING DryDocs term to a standard term; nothing renamed, reshaped,
or added.

| Item | Ruling |
|---|---|
| A1–A4 scope | **CONFIRMED** — review-only; mechanism-only surfaces (standard CURIEs, no internal names); nothing new minted; the ALIGNMENT-PLAN skip list is binding. **SME remark on A:** activation of the `fcdo-frameworks` corpus is UNDER CONSIDERATION now that alignment is verified — it remains a separate registry decision, NOT flipped by this gate. |
| B1 rows 1/2/3/7 exact | **CONFIRMED** — ControlMJob↔OL Job, JobRun/ControlMJobRun↔OL Run, DataAsset↔Dataset, SUBCLASS_OF/MAPS_TO↔rdfs bridging. |
| B2 row 2 scope note | **CONFIRMED** — the 2026-07-31 batch-history ruling restated; name conformance only, no run-event-ingestion mandate. |
| B3 row 4 grain split | **CONFIRMED** — their grain is the Run, ours the definition (ETLProcess \| ControlMJob); both grains recorded; any future run-grain lineage lands on ControlMJobRun without displacing the definition-grain edges. |
| B4 row 6 documentation-only | **CONFIRMED** — the adms:status reading is a translation aid; the proposed→confirmed→applied HITL machinery changes in no way. |
| B5 row 8 carrier difference | **CONFIRMED** — RECONCILES_TO {confidence} carries skos:closeMatch + mapping-confidence semantics on an edge property rather than an RDF mapping resource. |
| C1 row 5 blocked | **CONFIRMED** — stays OPEN, signed neither way, until the registered `fcdo-frameworks` scrape recaptures the Descriptive Metadata Framework. |
| C2 absence ≠ absence | **CONFIRMED** — transcript absence is never treated as absence from their standard. |
| D1–D2 sign-off | **CONFIRMED** — rows 1–4, 6–8 and the file status flip proposed → confirmed; row 5 stays `blocked-on-recapture`; the guard test moves to the post-gate state in the same commit (F1/F2 precedent); corpus activation stays a separate, later decision. |


## 2026-08-05 — RECORD: `fcdo-frameworks` corpus ACTIVATED (user ruling in-chat, same day as the fcdo-crosswalk sign-off)

- **What this records:** the in-chat user ruling activating the `fcdo-frameworks`
  doc corpus — `config/doc-source-registry.yaml` `confirmed: false → true`. A record
  on the G51/X1 idiom (direction, not a gate session): no ontology edge, no
  vocabulary status change, no graph write. The stated rationale: "settle our
  ontology with what they published" — the crosswalk gate this flip waited on
  (its `confirmed: false` comment named it) signed the same day, 13/13.
- **The Idea-70 sub-question, ruled with the flip:** activation proceeds
  INDEPENDENTLY of the row-5 recapture. Crosswalk row 5 stays
  `blocked-on-recapture` regardless — that is crosswalk-side state, untouched here;
  if anything, activation is the path that PRODUCES the recapture evidence
  (Descriptive Metadata is the first-priority recapture target in the entry's notes).
- **What activation does and does not do:** `require_confirmed("fcdo-frameworks")`
  now passes, so the docmeta pipeline may ingest the corpus when the Confluence
  connector runs — which is company-network-side only; nothing can be scraped from
  the producer machine. T4 `sme-confirm` curation still applies per ingested page,
  and `target_db: ddcontext` keeps the corpus out of ground truth.
- **Test moved with the flip** (same commit, the F1/K2 pattern):
  `test_doc_ledger_union_gates_doc_corpora` now pins the confirmed state where it
  previously pinned the `UnconfirmedSourceError` refusal.

## 2026-08-06 — RECORD: Operate Manager is THREE role classes (G35 §A5, confirmed in-chat 2026-08-05; the coercion fixed 2026-08-06)

- **Why this entry exists at all, and it is the useful part.** The confirmation
  happened on **2026-08-05** and lived only inside the gate-prompt YAML
  (`config/gate-prompts/tom-roles-enumeration-and-cardinality.yaml` §A5 and
  `sme_direction`), committed as `3df06de` on the **laptop** — the desktop has no
  G35 commits. It never reached this log, so the durable source of record held
  nothing while git held a dated, attributable ruling. It surfaced only because the
  SME asked, a day later, whether it had been confirmed. That is the
  "did the gate land?" failure mode arriving on schedule: **a CONFIRMED CLAUSE
  inside an UNSIGNED gate has no home in a log organised by sign-off.** Recorded on
  the G51/X1/`fcdo-frameworks` RECORD idiom — direction, not a gate session.
- **What was confirmed (2026-08-05, in-chat):** *"three separate role classes, not
  one concept with a level."* Restated 2026-08-06 with the cardinality attached:
  *"L1 Operate Manager, L2 Operate Manager, Operate Manager are 3 separate roles
  that could be distinct individuals or the same."* Three statements across two
  days, consistent each time.
- **What it settles inside G35:** mapping row 2 resolves RE-OPENED → SPLIT;
  `operate_manager` becomes three concepts; the `Attribution.level` property retires
  as a role discriminator rather than moving, because it never carried information
  the role NAME did not already have; `c7.levels = 'L1,L2'` retires with it. The
  count arithmetic closes exactly — the signed 7 with `operate_manager` split into 3
  IS the 9 the live registry shows.
- **What was APPLIED on 2026-08-06, ahead of sign-off and on explicit instruction**
  (`drydocs_core/models/seal.py`): `SealRole` gained `OPERATE_MANAGER =
  "Operate Manager"` and `_ROLE_CANONICAL["operate manager"]` was re-pointed from
  `"L2 Operate Manager"` to `"Operate Manager"`. **Two lines, not one** — deleting
  the bad alias alone leaves the bare name with no admissible value, and an
  unrecognised name is not flagged, it kills the row.
- **The defect that fix ends.** The alias asserted a level the source never stated.
  Because the same person routinely holds all three on one application (recorded at
  line 882 of this log, from the SME screenshots that pinned identity gate §D2), the
  rewritten row produced an `attribution_id` identical to that person's genuine L2
  row; `seal_contacts.cypher` MERGEs on `attribution_id`, so the two folded into one
  node. Three source holdings became two, silently, with the survivor decided by
  batch order. Measured on the bundled taxonomy sample, application 70001:
  **13 rows → 9 validating → 8 attributions before, 9 after. Zero merged.**
- **Scope — NO ONTOLOGY CHANGE, and this is the line that matters.** `SealRole` is
  the admission list for SOURCE NAMES, not the concept scheme. `tom_roles` still
  seeds 7 concepts, `seal_contacts.cypher` still has its 4-branch crosswalk, and no
  `:TOMRole` was created — so a bare Operate Manager row now loads and arrives
  flagged `unmapped_role = true`, which is the K4 policy working as designed:
  loaded, surfaced for review, never guessed. **Creating the three concepts is still
  §A's ruling to make, and G35 remains unsigned.**
- **Guarded by `tests/unit/test_seal_roles.py` (NEW).** The module had **no tests at
  all**, which is how an alias that destroyed a role holding survived long enough to
  be found by reading rather than by failing. Beyond pinning the three classes it
  asserts the invariant the defect violated: **no alias may resolve to a canonical
  name asserting a level the alias does not itself name.** A future
  `"ops manager" → L2` fails that test instead of silently merging.
- **Still open in G35, unchanged by any of this:** the bare class has no DEFINITION
  (§A5c), and four classes from the SME's 2026-08-06 thirteen-class list
  (Deployment Owner, Deployment Information Owner, Application Module Owner, Site
  Reliability Engineer) cannot be loaded at all — they hit the same
  `unrecognised SEAL role` refusal, which is §A3's question and is untouched by this
  fix.

## 2026-08-06 — RECORD: Tech Partner → CTO alias KEPT; Chief Business Technologist restored as an optional, deliberately unmapped role (G35 §A6 + G10)

- **What this records:** two in-chat SME rulings of 2026-08-06, on the G51/X1 RECORD
  idiom (direction, not a gate session). *"Leave the product catalog role 'Tech
  Partner' maps to seal contact 'Chief Technology Officer (CTO)'. Make one update for
  SEAL, add optional role: Chief Business Technologist (CBT) but do not create a
  cypher relationship mapping for it, in case it appears."* Between them they dispose
  of **§A6** and the whole of **G10** — the first register line answered outright.
- **Ruling 1 — the alias stays.** `_ROLE_CANONICAL["tech partner"] = "CTO"` is
  CONFIRMED as a deliberate name crosswalk rather than a stale leftover. What it
  asserts is narrow and is recorded that way: **the two role families use different
  names for the same accountable person**, so a contact row saying Tech Partner means
  the SEAL CTO contact. K5's own rename history corroborates it — the area-product
  Tech Partner was formerly named CTO in SEAL.
- **Ruling 2 — CBT is a class, and it is optional.** Chief Business Technologist is a
  role class in its own right, **not** an alias of Chief Technology Officer, and it is
  OPTIONAL. Admissible so a row is never refused; deliberately absent from the concept
  crosswalk so it arrives flagged for review.
- **NEITHER RULING NEEDED A CODE CHANGE, and that is the point.** The Tech Partner
  alias already exists. CBT is already admissible (`SealRole` plus its `cbt` alias)
  and has no Cypher branch, so a CBT row already loads with
  `unmapped_role = true`. The instruction turns an accident into an intention: the K4
  policy — *loaded, surfaced for review, never guessed* — used **on purpose**, to
  record a name the source may emit without minting a concept for it. Only
  `config/taxonomy/business-application.yaml` changed, which now carries CBT and Chief
  Technology Officer on the SAME application held by DIFFERENT people, so the sample
  states they are two classes instead of leaving it to be inferred.
- **A CORRECTION THE RULING FORCED, recorded because the overstatement is in committed
  history.** G35 §A6 had claimed a Tech Partner row *"becomes a TOM `cto` Attribution
  on a BusinessApplication — the exact shape K5 forbids."* **It does not.**
  `seal_contacts.cypher:75` mints `HAD_ROLE` only when the crosswalk returns non-null
  (*"never mint concepts here"*), and the crosswalk has four branches — Backup
  Information Owner, Design Authority, L1 and L2 Operate Manager. `cto` is not among
  them. A contact-side Tech Partner row therefore produces an Attribution carrying
  `role_source_name = 'CTO'` and **no concept edge of any kind**; the `cto` concept is
  reached only from `seal_applications.cypher` via the DECO row's own
  `chief_tech_officer_sid`, a BusinessApplication field. **K5's boundary was never
  crossed**, which makes "leave it" a safer ruling than the page had implied.
- **What stays open (§A6c):** the alias makes 'Tech Partner' and 'CTO'
  indistinguishable downstream — `role_source_name` records `'CTO'` for both — which
  collides with the identity gate's §B2 evidence rule (the source's own term is kept)
  and with §A4b's question about the canonicalizer generally. Harmless if the two
  names are genuinely one role; unrecoverable if a Product Cabinet Tech Partner ever
  lands in the contact extract.
- **The two rulings went opposite ways on the same kind of evidence, and that is the
  record worth keeping.** Tech Partner ↔ CTO: one role, two names. CBT ↔ CTO: two
  roles despite a shared name family. A shared naming history is evidence, not proof,
  and on 2026-08-06 it went each way once.
- **Still unruled:** Risk Manager (G12) is now the only name absent from the stated
  vocabulary and still emitted by the source, and it is the one whose absence costs
  something — §A2 pairs it with `technology_risk_controls`, a signed concept that
  nothing can write.

## 2026-08-06 — RECORD: rua load shapes, three partial rulings (G22; gate `rua-load-shapes`, still UNSIGNED)

- **Why a RECORD and not a sign-off.** The G22 session opened 2026-08-06 and ruled
  three of its ~25 clauses before pausing. The gate is not signed and its terminus
  still holds — nothing rua-shaped writes the graph. On the convention set the same
  day for G35: **a confirmed clause inside an unsigned gate has no home in a log
  organised by sign-off**, so it is written here in the same commit as the page
  edit, or it exists only in a YAML file nobody re-reads.
- **A1 — `m3_delegates_to` (AppUser -DELEGATES_TO-> ExecutionHost): HOLD, pending K17.**
  Not declined — *blocked on identity*. `ControlMJob.run_as` carries the **linux
  tenant name**, which is the functional-id NAME and not the directory key;
  `fid-identity-and-scope` §A1/§A2 keys `:AppUser` on `fid` with `fid_name` a
  property and an explicit, miss-rate-reported name→fid crosswalk. That gate is
  **drafted and unsigned** (K17, preceded by the K16 census). No `AppUser`
  constraint is deployed, so activating here would key the node on the NAME by
  default — the exact silent split §A1 exists to prevent, made worse by §A3 leaving
  name-reuse-after-retirement unresolved.
- **A1's second half, and the reason it is not merely a sequencing nit.** SME
  direction of 2026-08-05: a run-as account may be **registered to a different
  application than the job's Control-M app code**. Registration is not attribution
  (J32, the standing rule now in `docs/RELATIONSHIP_GUIDE.md`); no transitive read
  job→account→application is permitted (fid §G2); the K2 FID tier is **mis-specified
  rather than merely unimplemented**, harmless today only because the table is empty
  (fid §G3); the disagreement is a **finding** with three readings distinguished per
  case (fid §G4/§G5). The rua envelope corroborates presence and authors no identity.
- **A2 — `m3_runs_on_etl_host`: DECLINED as redundant (SME).** ETL placement is *the
  same fact* as job placement, so the entry would be a synonym splitting "where does
  this run?" across two labels. The job side is already built and **active** (P3,
  2026-07-27): `NODE_ID x CM_HOSTS.GRPNAME` → `RUNS_ON {host_group}` (2-hop, the
  Control-M in-application load balancer); else `NODE_ID x CM_HOSTS.NODEID` →
  `RUNS_ON {agent_host}` (1-hop, hard-coded); P4 census counts any NODE_ID matching
  both.
- **COLUMN CORRECTION, recorded because it nearly landed wrong.** The join is
  **`NODE_ID`, never `GROUP_NAME`**. `psgmgr CM_DEF_VJOB.GROUP_NAME` is the vendor
  `APPLGROUP` — the *application* group (schema-crosswalk §COL) — which is the exact
  collision gate `controlm-hosts-topology` named the class `ControlMHostGroup` to
  avoid (signed 2026-07-09; guarded in `controlm_hosts.cypher:8` and
  `ontology_supplement.cypher:104`). Two different fields, both spellable as
  "group": **J32's read-the-field's-job rule, third observed instance.**
- **A2's follow-up build (not done at the gate, per §I1):** `m3_runs_on_etl_host`
  goes `planned → deprecated` pointing at `m3_runs_on_agent_host` /
  `m3_runs_on_host_group`, and `ontology_supplement.cypher` trims its documented
  role enum from `(host_group | agent_host | etl_host)`. Grooms as an item; nothing
  in the vocabulary changed today.
- **H3 — CONFIRMED, added at the session.** A job resolving **1-hop** where its peers
  resolve 2-hop is a **finding**: it is pinned off its load-balanced host group and
  therefore **has no failover**. SME evidence: development teams do not always know
  what belongs in the Control-M GUI host field and hard-code a server name there, so
  a 1-hop edge is frequently a mis-filled field rather than a deliberate pin.
  Reported, never auto-corrected — the two are indistinguishable in the data and
  only a human knows which (the H2 / P5 remediation-feeder pattern). Costs no new
  machinery: the `role` property, `r.source`, and `drydocs/cli.py`'s `pinned_host`
  already carry it. What H3 adds is that the difference is a **finding**, not a
  formatting detail.
- **D3 SME INPUT (not a ruling): `CM_HOSTS.NODEID` is the REAL SERVER NAME.** So the
  rua envelope's host meets `:ExecutionHost` on `nodeid` directly, the deployed
  `executionhost_nodeid` UNIQUE constraint stands as the key, and the
  **not-replicated** `CMS_MACHINE_MAP` (NODEID → HOSTNAME + DOMAIN_NAME) is not on
  the critical path after all — the join that looked blocked is available. D3 still
  has to rule the spelling on each side (`rua_host` vs `rua_fqdn`), the AppUser half
  (blocked behind A1/K17), and what `cross_host_collisions` means.
- **Still open — everything else:** A3/A4/A5/A6, rider R2 (B1-or-B2 + B3), C1–C3,
  D1/D2/D4, E1–E3, F1–F2, G1–G2, H1–H2, I1–I3, and §J sign-off. G22 stays
  `in_progress`; the terminus holds.

## 2026-08-06 — RECORD: rua load shapes, second batch — rider R2 ruled B2, and section A closes (G22; gate `rua-load-shapes`, still UNSIGNED)

- **Scope:** the same session as the entry above, continued. Section A is now
  fully ruled and rider R2 is decided. The gate remains unsigned and the
  terminus holds — no loader exists, nothing rua-shaped writes the graph.
- **A CORRECTION TO HOW THE PREVIOUS BATCH WAS RECORDED, and it is the same
  failure this convention exists to prevent.** B2/B3 were ruled and written to
  the gate page in commit `45af31e`, which **did not touch this log**. For one
  commit the ruling existed only in a YAML file — precisely the state the entry
  above was written to end. Folded in here rather than left implicit. The rule
  is not "write a RECORD entry when a batch feels big enough"; it is **the same
  commit, every time a clause is confirmed.**
- **B2 CHOSEN — `m3_invokes.to_node` broadens to `Script|ETLProcess`.** One edge
  meaning, two endpoint classes, endpoint recorded per edge. On the record:
  the union-endpoint precedent already exists in this vocabulary
  (`m3_reads_from`/`m3_writes_to` take `ETLProcess | ControlMJob` as
  `from_node`); **G12 is done and already lands INVOKES directly on an
  `:ETLProcess`** for the abioncloud wrapper-payload expansion, so B1 would have
  meant re-modeling working code; and B1 splits "what does this job call?"
  across two labels chosen by what the callee happens to be — a two-query answer
  permanently. **B1 recorded as NOT CHOSEN, not deleted** — a page showing only
  the winner cannot be audited.
- **B3 CONFIRMED** — the raw evidence string is kept verbatim. It carries more
  weight under B2 than it would have under B1: when one label can land on two
  endpoint classes, the verbatim evidence is the only way to re-check that the
  class was chosen correctly.
- **A3 ACTIVATE — `m3_invokes`.** Feed verified at the ruling rather than
  assumed: `controlm_inventory` CMD_LINE facts (G14), the G39/G40 interim seam,
  G16 `SCRIPT_PATH` facts — all `done`. **Two signed rulings ride in with it and
  are not re-opened:** cardinality 1..n per job (cmdline-lineage-review,
  2026-07-16), and `:Script` identity stays **PATH-KEYED** with same-basename
  duplicates going to SME merge, never auto-merged. **That second one constrains
  D1** — the URN this gate rules must render that path key or amend a signed
  ruling; it cannot quietly replace it.
- **A4 ACTIVATE — `m7_uses_artifact` — and deliberately in the same breath as
  A3.** Feed is specific: `FACT_REGISTRY` carries `ETL_ARTIFACT_URI` /
  `ETL_ARTIFACT_KIND` / `ETL_ARTIFACT_SHA` plus `ETL_PLATFORM` /
  `ETL_PLATFORM_FLAGS` with alias rollups, under the aliases-suggest-values-decide
  contract — never the variable NAME alone (the 2,384-variable gap analysis
  found that names lie). **Why together:** the `m3_invokes` note says payload
  invocations MIGRATE onto this label at its build. Activating A3 alone would
  land payloads in the 1..n INVOKES fold first, so the migration would move
  edges already in the graph instead of routing them correctly on first load.
  Riders already SME-ruled at cmdline-nfr-vetting (2026-07-21, SME-3) come with
  it: `script_role {launcher, payload}` plus `platform` / `artifact_uri` /
  `artifact_kind` / `platform_flags` / `script_path`.
- **A4 note for §G2:** `ETL_ARTIFACT_SHA` is a **content hash arriving on the
  variable**, so a DPL-managed artifact can be hash-BEARING where the rua
  listing is hash-absent — a corroboration path G2 as drafted does not
  anticipate.
- **A5 ACTIVATE, WITH THE RESTRICTION RESTATED.** The SME changed the page's own
  words rather than ticking them. New wording: activate for **structured,
  launcher- or registry-grounded evidence — `dataset_flow` AND parsed CMD_LINE
  file-ops — but NOT script-body content grep.** Why: the drafted "never parsed
  prose" read as excluding the CMD_LINE feed, and **a signed gate already put
  that case here** — the `m3_triggers` note (confirmed 2026-07-15) says the pure
  unix file-operation wrapper case "is m3_reads_from / m3_writes_to with
  ControlMJob as the Activity." Excluding file-ops would have left a signed case
  with nowhere to land. Both feeds verified: `dpl_mac` maps `dataset_flow.json`
  input/output datasets to candidates; `controlm_inventory` (G14) parses
  MOVE/COPY/COMPRESS into the same, with counters for non-dataflow ops and
  missing operands.
- **A5's accepted consequence, which lands on D1/G1:** `local_file` DataAssets
  will be numerous and transient — one per MOVE operand — so whether they are
  the same node class as registered datasets is a real question this activation
  creates, and those clauses have to answer it.
- **A6 CONFIRMED, and exercised the same day.** Anything not ticked stays planned
  and candidate-side; declining is a normal outcome. Of the six candidates the
  G22 acceptance named: **one was already active before the session**
  (ControlMJob RUNS_ON ExecutionHost, P3 2026-07-27), **three activate** (A3, A4,
  A5), **one is declined** (A2, redundant), **one is held** (A1, on K17's
  unsigned AppUser identity).
- **Consequences are FOLLOW-UP BUILD work, not gate edits** (§I1, the K2/G27
  pattern): groomed 2026-08-06 as **G55** — flips to active WITH supplement
  blocks, declined entries retired, new meanings landing as `planned`. G55
  depends on G22 being **signed**, not merely opened. The loader itself stays
  G23.
- **Still open:** C1–C3, D1/D2/D4, E1–E3, F1–F2, G1–G2, H1–H2, I1–I3, §J
  sign-off.

## 2026-08-06 — RECORD: rua load shapes, third batch — section C mints the new meanings (G22; gate `rua-load-shapes`, still UNSIGNED)

- **Scope:** the only remaining section that MINTS vocabulary rather than ruling
  existing entries. All three clauses ruled as recommended. Everything lands
  `status: planned` via ontology-mapper per the RELATIONSHIP_GUIDE flow —
  **nothing active at this gate.**
- **C1 — THAT SHAPE.** `(:DataAsset)-[:WAS_ATTRIBUTED_TO {role:
  'directory_owner'}]->(:AppUser)`. Entity → Agent is the matrix row, and
  role-discrimination on the shared label is the house pattern — five entries
  use it, several active.
- **C1 precedent correction, recorded because the page overstates it.**
  `arch_owns_code`, the entry cited as the precedent, is **itself `status:
  planned` with `loader: ~`** and has never loaded anything. The shape is right;
  the load-bearing precedent is the role-discriminated label, not that entry.
- **C1 is BLOCKED AT BUILD, NOT AT RULING** — recorded explicitly so **G55 and
  G23 do not walk into it**. Its `to_node` is the `:AppUser` whose key A1 held on
  K17. The entry lands `planned` today and cannot be built before K17 signs.
- **C1 identity sub-ruling** (taken on the recommendation stated at the session):
  `directories.tsv` carries `owner` as a bare unix account name that may be a
  service account **or a person**. A directory owner resolves to `:AppUser`
  **only on a known functional-id match**; everything else stages **unresolved
  and counted** per the never-silent rule, never guessed onto an Agent.
- **C2 — two parts, both as recommended.** (i) **from_node:** a profile is a
  `:Script` carrying `script_role: profile` — a profile IS a shell script file,
  so this mints no new node class, reuses the discriminator A4 brought in
  (`launcher | payload`, now three values), and inherits C3's SWO typing free.
  (ii) **edge:** dot-sourcing gets its own local **`SOURCES`** type with
  `prov_maps_to: ~`, because the Entity→Entity matrix row is
  `prov:wasDerivedFrom` — "transformed or computed from another entity" — and
  **sourcing is not derivation**; mapping it there would assert something false.
  Precedent for a local label with no PROV row is active: `m3_scheduled_on`.
  `m3_invokes` is reused **only** for actual execution from a profile.
- **C2's evidence was staged deliberately unnamed.** `rua_code_ops.py` (G21)
  stages dependency candidates with `needs_vocabulary: True`, writes **no**
  relationships, and separates the verbs itself: `_SOURCE_VERBS = {".",
  "source"}`, annotated *"shell inclusion verbs, never an invocation"* and *"a
  profile is environment inclusion, not a gated Activity, so the edge MEANING is
  the G22 gate's."* The build refused to name the edge and left it here, which
  is the terminus working as designed.
- **C3 — ADOPT, and cheaper than the page describes.**
  `(:Script)-[:IS_ENCODED_IN]->(SwoClass)` by extension.
  `EXTENSION_LANGUAGE_IRI` **already** carries `.sh` → SWO_0000124 and `.sql` →
  SWO_0000126 beside `.py`, and the 2026-08-05 ruling added a parallel
  `EXTENSION_MEDIA_TYPE_IRI` layer under the same E1(b) discipline. So C3 is
  "point the existing adapter at `:Script` too," not "build a binding."
- **C3's addition — `.ksh` binds to the SAME Shell term as `.sh`** (SME ruling:
  a **peer**, not a separate language). Not cosmetic: the signed `m3_triggers`
  note names the `.ksh` wrapper as the **common case in this estate** — "one
  .ksh wrapper script that launches the Informatica / Ab Initio / DPL workload"
  — so leaving it out left the most frequent extension unbound and merely
  CLI-reported.
- **APPLIED at the session** (`drydocs/loaders/code_snapshot.py`), with a test
  asserting the two extensions resolve to the **same** IRI so they cannot drift
  apart later. This is adapter DATA that stands alone and improves `:CodeModule`
  typing today, independent of whether `:Script` ever loads — it is not a
  vocabulary flip. **The `IS_ENCODED_IN` edge itself still rides G55.**
- **Boundary re-confirmed as pre-ruled:** `run_as` / `J.OWNER` is Agent
  territory (PROV/ORG), **never** an SWO binding.
- **Still open:** D1/D2/D4, E1–E3, F1–F2, G1–G2, H1–H2, I1–I3, §J sign-off.
  Sections A, B, C and H3 are done.

## 2026-08-06 — RECORD: rua load shapes, D-AMENDMENT — shared storage breaks the independence assumption (G22; gate `rua-load-shapes`, still UNSIGNED)

- **Status of section D: D1, D2 and D4 REMAIN UNTICKED.** This entry records SME
  *direction* that constrains what they may say; it does not rule them. D3's
  ExecutionHost half is settled (NODEID is the real server name); its AppUser
  half holds behind K17 with A1 and C1.
- **The caveat.** A deployment path may be **shared** — the SME's case is roughly
  20 VSI hosts against one shared filesystem — and then the same path on N hosts
  is **one file seen N times**, not N deployments.
- **Not derivable from any bundle we hold.** The collector captures **no mount
  table** — no `findmnt`, no `/proc/mounts`, no `df`. The envelope carries
  `scan_roots` but never which filesystem a root sits on, and the ownership
  sweep's `-xdev` stays on one filesystem without recording which. So today this
  is a declaration, not an inference.
- **It reaches IDENTITY, not only semantics.** Path-keying merges
  same-path-across-hosts into one node — **correct** under shared storage,
  **ambiguous** under local storage, where two hosts may hold genuinely different
  content at the same path. That is two artifacts sharing a path, and a merge
  would report drift on things that were never the same file. Content hash is the
  only discriminator and the metadata-only listings (premise 2) carry none, so
  with scope unknown **and** no hash the case is undecidable from data.
- **THE CONSEQUENCE THAT MATTERS.** §G2 drift detection and the G24 corroboration
  both assume occurrences are **independent observations**. N views of one file
  are **one** observation — compare them and they always agree, which
  manufactures confidence rather than establishing it. So **`storage_scope:
  unknown` must not default to independent**: it suppresses the corroboration
  claim and counts the node identity-unconfirmed-across-hosts. That count is the
  review queue.
- **Correction to the session's own earlier reading.** `cross_host_collisions`
  was recommended as a measure of **deployment** breadth. Under shared storage it
  measures **mount** breadth — a different fact. Recorded because the wrong
  reading was already on the page.
- **Shape the amendment adds:** occurrences carry `mount_root` + `fstype` +
  `storage_scope` (local | shared | unknown). A storage-locus **node is
  DEFERRED, not declined** — minting it now would create an entity with no
  source, since no bundle carries a storage inventory. Carrying `mount_root`
  from the start makes promoting it later cheap; un-minting a node class is not.
- **THE COLLECTOR WORKAROUND (SME direction) — make it derived instead of
  declared.** Three refinements taken at the session:
  1. **`lsblk` cannot answer it.** `server:/path` is an **NFS** mount spec and
     NFS is not a block device, so it never appears in `lsblk`. The mount table
     is the only source: `findmnt -rn -o SOURCE,TARGET,FSTYPE,OPTIONS`, with
     `/proc/mounts` as the no-`findmnt` fallback. Both read-only; no privilege
     change to the collector's safety story.
  2. **`/etc/fstab` is configured INTENT, not actual state.** Autofs, systemd and
     manual mounts are mounted without appearing there; stale lines appear
     without being mounted. Capture actual state.
  3. **"On the SAN" does not mean shared** — the correction that changes the
     answer. Twenty hosts each with their **own LUN** from one array is twenty
     separate filesystems and twenty files that genuinely drift; twenty hosts
     mounting **one NFS export** is one file seen twenty times. **Sharing follows
     from FSTYPE, never from the array** — nfs/nfs4/cifs shared, xfs/ext4
     single-host unless gfs2/ocfs2 clustered. The `type` column the SME named is
     the load-bearing one, and `lsblk` alone would actively mislead.
- **T14 CAVEAT WITHDRAWN on SME correction:** nothing has been loaded yet and the
  company-side twin collector is **not present**, so a bundle schema bump costs
  no convergence debt. This is the cheapest moment it will ever be.
- **What the workaround does NOT remove:** bundles already collected stay
  scope-unknown, so the `unknown`-suppresses-corroboration rule stands either
  way. The collector change reduces how often that state occurs; it does not
  retire it.
- **Groomed, not built at the gate** — capturing a fact is an instrument change,
  not a decision about what an edge means, and the collector runs on production
  hosts. **G56** = the mount capture (schema v3, optional section, derived
  `storage_scope`). **G57** = the `rua_*` → `bkup_*` rename the SME made, which
  is cheap NOW precisely because nothing has been loaded: renaming a property
  already on nodes is a migration, renaming one never written is an edit. G57
  deliberately does **not** rewrite this log's history, and follows the
  source-registry v2 §Q6 precedent for the gate id — rename transfers with one
  amendment entry, nothing is re-gated.

## 2026-08-06 — RECORD: rua load shapes, section E — precedence, and "deployed" stops meaning "runs" (G22; gate `rua-load-shapes`, still UNSIGNED)

- **All three E clauses CONFIRMED**, two of them with SME refinements that change
  what the page said rather than merely ticking it.
- **E1 — the server extract is the truth for WHAT IS DEPLOYED AND WHERE.** The
  drafted phrase *"latest code that actually runs"* is an **overclaim and is
  retired.** SME at the session: a script may have been **deployed to the wrong
  server** — present, called by nothing on that host, and dead in place.
  Presence is a deployment fact and nothing more.
- **E1's caveat is also a feature.** A script present on host A and referenced by
  no job on host A, while its twin on host B *is* referenced, is a
  **misdeployment** and is detectable. It interacts with the D-amendment: under
  shared storage "deployed to the wrong server" is close to meaningless, because
  every host sees one file — so the misdeployment finding is only valid where
  `storage_scope` is **local**.
- **E2 — the flag's home is `config/source-registry.yaml`, on the DATASET row.**
  v2 already gives each dataset its own `confirmed` and `authority` fields, which
  is the per-instance grain this needs; the flag is per-repo, therefore
  per-dataset; and `precedence.yaml` has no per-instance grain at all — it
  governs *concepts* globally, so a per-repo flag there is a category error.
- **E2 is tri-state and defaults to `unknown`, never `trusted`** — `trusted |
  untrusted | unknown`. **SME refinement making it measurable rather than merely
  declared:** the Bitbucket/GitHub repos are cross-referenced, and if main or
  master is **significantly behind**, the team is most likely working on feature
  branches and never raising the PR. So main's lag is a computable proxy that
  should populate the flag where it can be measured, with the declared value able
  to override.
- **E2's second evidence instance**, from a different source and date than the
  one the page cites — `dpl_mac.py`, CLONE AUTHORITY CAVEAT (SME, 2026-07-23):
  *"the clone's main may LAG — the dev team pushes feature branches and does not
  reliably merge, so the folder listing is a FLOOR on the pipeline/dataset
  inventory, never the authority."* Two independent observations of one failure
  mode — repo state not reflecting deployed state — from the script side and the
  pipeline side. That is what makes the per-repo flag necessary rather than
  merely cautious.
- **A house rule is emerging and is worth naming: UNKNOWN MUST NOT DEFAULT TO THE
  CONVENIENT VALUE.** Twice in this session — `storage_scope: unknown` does not
  default to *independent* (D-amendment), and repo trust `unknown` does not
  default to *trusted* (E2).
- **E1/E2 in `precedence.yaml` terms** fit the file's existing **disjoint-governs**
  pattern (the `seal-pat` row already uses it): `rua-server-extract` governs
  `deployed-script-state`; `code-repo` governs `script-intent` + `script-history`.
  **Different axis from the file's existing four**, and the rationale must say so
  — the current rows arbitrate *what a thing IS*, these arbitrate *which source
  is right about a mutable artifact's state versus its history*. Without that,
  "authority 5" later reads as "less authoritative than naming conventions,"
  which is meaningless. `tests/unit/test_precedence.py` guards the file, so the
  rows arrive with a test — G55-adjacent build work, not a gate edit.
- **E3 — CONFIRMED, and the SME NAMED THE USE CASE: identifying unused,
  deprecated code for ARCHIVAL AND REMOVAL.** Consistent with H1 by construction
  — H1 says the three signals stay separate axes, E3 says presence is not usage;
  the same statement from two directions, recorded so neither is later read as
  narrowing the other.
- **The use case raises the bar, and that is why "flagged, never auto-judged" is
  a SAFETY property rather than tidiness:** the output drives deletion, so a
  false positive removes live code. **Three dispositions, not two** — genuinely
  dead (archive and remove), **misdeployed** (relocate, not delete — the E1
  caveat), and unreferenced-but-dynamically-called (keep).
- **KNOWN FALSE-POSITIVE MODE that must ride the report.** Script-to-script
  invocation is visible only where the bundle **carried the body**, and the
  metadata-only listings of premise 2 carry **no body copies at all**. On those
  bundles "unreferenced" means only "no CMD_LINE reference", never "nothing calls
  it". Any archival report must state its body-copy coverage, or it will propose
  deleting leaf scripts it was structurally unable to see callers for.
- **Still open:** D1/D2/D4, F1–F2, G1–G2, H1–H2, I1–I3, §J sign-off. Sections A,
  B, C, E and H3 are done.

## 2026-08-06 — RECORD: rua load shapes, F1 — a filesystem path is not confidential, and the URN survives (G22; gate `rua-load-shapes`, still UNSIGNED)

- **F1 RULED — the confidential set is HOSTNAMES and RUN-AS ACCOUNTS. A
  filesystem path is NOT confidential (SME).** The standing rules agree:
  CLAUDE.md's publish-boundary list names SIDs, credentials, server addresses,
  GHE org names and production data values — paths appear in none of them.
- **THE COLLISION THIS RESOLVES, and it was live.** D1's URN is **path-derived**.
  Had paths been confidential, `urn:drydocs:script:/opt/app/foo.ksh` would have
  been confidential too, and there would have been **no publishable layer for
  scripts at all** — F1's own claim that "the URN and structural facts are the
  publishable layer" would have been false. With this ruling that claim holds and
  **D1's grammar survives unchanged.**
- **The premise was broken twice, not once.** Beyond J23's tier collapse (which
  the page flags), the classification vocabulary has **no per-property grain at
  all** — `QuerySpec.classification` (O11, done) is one string for a whole spec.
  A per-property split was never expressible, in either the old four-level
  vocabulary or the new three-level one.
- **Output shape, and the mechanism already exists and is in use:** (a) a
  confidential-handling **note on the source-registry entry** — exactly what the
  `exec-hosts`, `bitbucket` and `dpl` system rows already carry post-J23; (b) an
  **export rule**, enforceable as a test over the QuerySpec registry — no spec
  classified publishable may return a column in the confidential set. Every spec
  is `internal` today, so the rule is vacuous now and guards forward.
- **CORRECTION TO §E2's RECORD, made after the fact.** The session recommended
  the repo-trust flag's home as the source-registry dataset row *as though it
  needed creating*. **It already exists** — `trusted_ref`, built at G24, on
  `bitbucket:repo-objects-manifest`, commented *"HUMAN-BLESSED intent line: the
  one ref this repo's team keeps clean. null = server-extract-only truth (the
  stale-main case). The corroboration sweep NAMES a candidate ref mechanically;
  only a human sets this field."* Its semantics already match the SME refinement
  exactly, so **the tri-state proposed at the session is not needed**: the field
  is two-state with the safe default, and null already means "untrusted or
  unknown, treat the same." The home reasoning stands and is why the existing
  placement is right.
- **A CONSEQUENCE OF §E1 APPLIED TO PROSE.** The `bitbucket` system note ended
  *"production servers always run the latest RUNNING code"* — the exact overclaim
  E1 retired. Corrected to "hold the latest **DEPLOYED** code", with the reason
  recorded on the entry: deployed is not running, because a script may have been
  deployed to the wrong server and is then present, called by nothing, and dead
  in place.
- **Related drift fixed the same day** (`3fb491d`): `docs/design/drydocs-project-tdd.md`
  still said `config/classification.yaml` defines **four** tiers and listed
  Internal-Confidential as live. Three since J23. A governed design doc carrying
  a superseded tier count is the same stale-premise problem F1 flags in its own
  text.
- **F2 NOT YET TICKED.** When it is, two restatements are needed: classification
  lives on the **SYSTEM** row, not the dataset row (v2's D1 split), and the page's
  ids `rua-server-extract` / `code-repo` are **retired** — the replacements are
  `exec-hosts:rua-bundle` and `bitbucket:repo-objects-manifest`, inheriting
  `Internal` from their systems. `confirmed: false` with this gate as the
  activation condition is already in place.
- **Still open:** D1/D2/D4, F2, G1–G2, H1–H2, I1–I3, §J sign-off.

## 2026-08-06 — RECORD: rua load shapes, F2 + section G — identity is a business key, the URN is a render (G22; gate `rua-load-shapes`, still UNSIGNED)

- **F2 CONFIRMED, with two restatements** the page needs because it predates
  source-registry v2. (1) **Classification lives on the SYSTEM row**, not the
  dataset row — v2's D1 split put connection/locator/classification/SDLC on
  systems and gate/crosswalk/authority/confirmed on datasets. (2) **The ids this
  clause names are RETIRED** — `rua-server-extract` and `code-repo` were replaced
  under the v2 born-here grammar by `exec-hosts:rua-bundle` and
  `bitbucket:repo-objects-manifest`, and the D4 refusal list refuses the old
  strings outright. **Verified in place at the ruling**, so the clause confirms
  state rather than requesting it: `exec-hosts`, `bitbucket` and `dpl` all carry
  `classification: Internal` with a confidential-handling note on the entry — the
  F1 output shape exactly — and the bitbucket dataset row carries
  `confirmed: false` naming this gate as the activation condition.
- **G1 RULED — BOTH, not either.** The drafted "URN segment vs keyed property" is
  a **false dichotomy** and is retired. The registry GUID sits as a **keyed
  property** — it IS the business key (ADR 0001: *"node identity is always a
  business key, never a URL"*, and that ADR seeds ontology terms carrying the IRI
  as a **property**) — and the URN is a **deterministic render** that includes it.
  Identity does not live in the URN: source-registry v2 §D3 already ruled the URN
  *"derived deterministically, a render, never a hand-maintained field."*
- **G1's split is MANAGED-vs-UNMANAGED**, not pipelines-vs-anything. Managed
  (registry-known) assets key on the **GUID alone**, with `version` and `zone` as
  properties, and render a GUID-bearing URN. Unmanaged assets fall back to the
  grammar-built URN from path/name — `urn:drydocs:script:{normalized-abs-path}`
  (publishable per F1) and `urn:drydocs:dataasset:{platform}:{namespace}:{name}`.
- **This was already the code's own assumption**, waiting on exactly this clause
  — `dpl_mac.py`: *"identity = dataset GUID alone (version/zone are properties),
  pending the G22 clause-f GUID-vs-URN."*
- **The `name#GUID` composite is NEVER stored as a unit, anywhere** (answering the
  SME's question at the session). It is a promotion-clone **folder-naming
  convention on disk** that `parse_clone_folder` **decomposes** into name + guid
  + kind, keeping the parts and discarding the whole; the folder **casing** is
  the kind discriminator (lowercase pipeline, UPPERCASE dataset, mixed ambiguous
  — counted, never guessed). The direction also runs opposite to "folder naming
  follows the URN": the folder name is one **source** of the GUID, and the URN is
  rendered **from** the GUID afterwards.
- **THREE different `#`-bearing strings, recorded because conflating them is the
  live risk:** `<name>#<guid>` is a folder locator on disk (not identity);
  `proc#dpl:{GUID}` is the **lineage staging** node id (staging only, never the
  graph key); `urn:drydocs:…` is the rendered graph-side name.
- **G2 CONFIRMED, and the no-version-nodes clause is SCOPED TO SCRIPTS.** As
  drafted for scripts: content hash rides on occurrence records as the version
  discriminator; same URN + different hashes = drift, queryable; **hash absence
  is a real state** — metadata-only occurrences stage hash-absent with the
  absence counted, drift compares only among hash-bearing occurrences, and a URN
  whose occurrences are all hash-absent is uncorroborable-yet, a coverage fact
  rather than an error. Scripts get **no version nodes**.
- **Why the scoping was necessary: left blanket, the clause would have SILENTLY
  OVERRIDDEN a codified ADR.** ADR 0001's second LPG rule: *"Versioned external
  objects are distinct nodes keyed by (object, versionId), linked
  WAS_DERIVED_FROM to the predecessor (prov:specializationOf). Never smuggle a
  version into a URL string — a string is not queryable."* **The distinction that
  resolves it: a content hash is a FINGERPRINT, not a source-assigned version.**
  Nobody issues a versionId for a script. DPL-managed pipelines and datasets DO
  carry an explicit `version` from the registry (G25 stages `pipelineId` +
  `version` + `active`), so they are versioned external objects in the ADR's
  sense and continue to follow rule 2 — untouched by this clause.
- **Two amendments G2 was drafted without.** (1) **`ETL_ARTIFACT_SHA` is a hash
  arriving on the VARIABLE** (A4, same day), so a DPL-managed artifact can be
  hash-bearing even where the rua listing is hash-absent — a second corroboration
  route for exactly the metadata-only bundles premise 2 describes. (2) **Drift
  comparison must check `storage_scope` FIRST** (the D-amendment): N views of one
  shared file always agree, so comparing them reports corroboration that was
  never observed. The scope check is a **precondition** of drift detection, not a
  footnote to it.
- **Still open:** D1/D2/D4, H1–H2, I1–I3, §J sign-off. Sections A, B, C, E, F, G
  and H3 are done.

## 2026-08-06 — RECORD: rua load shapes, section D — one file one node, and the second observation that was being thrown away

**Gate:** `rua-load-shapes` (backlog G22) · **still UNSIGNED** — a RECORD entry, not a
sign-off. D1, D2, D3 and D4 all ruled at the SME session; §D now closes.

- **D1 RULED — the segments are the NORMALIZED ABSOLUTE PATH, and a SIGNED gate had
  already answered it.** `cmdline-lineage-review` (2026-07-16) §c: *"Script identity
  stays PATH-keyed; duplicates surface, never auto-merge"*, with the live case recorded
  as *"one logical .ksh at two mounts"*. That retires **basename** outright, and G2
  (same session) put the content hash on occurrence records, so the path is the only
  surviving candidate. URN: `urn:drydocs:script:{normalized-abs-path}` — the **same
  grammar G1 stated for unmanaged assets**, so D1 and G1 land as one grammar, not two.
- **Normalization is mechanical only:** collapse duplicate slashes, strip the trailing
  slash, count-and-reject relative / `..`-bearing paths as malformed. **No symlink
  resolution and no case folding** — POSIX paths are case-sensitive and nothing on the
  capture side ever resolved a link, so both would be guesses dressed as normalization.
- **The cross-host case is the one thing §c does not cover**, and the D-amendment had
  already chosen the answer: §c is same-basename at *different* paths; the amendment is
  the *same* path on N hosts. **Keep one node and suppress the CLAIM rather than
  re-key** — `storage_scope` local-or-unknown marks the node
  identity-unconfirmed-across-hosts with no corroboration asserted. Putting the honesty
  in the claim layer keeps A3's signed path key intact instead of quietly amending it.

- **D2 RULED — reified occurrence records as their own node class, planned-first — AND
  THE CLAUSE EXPOSED A LIVE AS-BUILT DEFECT.** `rua_inventory._stage_artifact`, on a
  second arrival of the same staged id, increments `cross_host_collisions` and **drops
  the record**: first-write-wins, so the second host's origin, sha256, owner, perms,
  mtime and envelope never land at all. D2 was drafted against *"squashed into node
  properties that overwrite each other"* — **the real behaviour is worse than the
  failure the clause names**, because a discarded observation cannot be recovered by any
  later loader.
- The repo side keeps its occurrences but as a **packed string** — `code_repo.py`
  accumulates `ref|commit|commit_date|blob_sha` newline-delimited into one `occurrences`
  property. Fine as staging; ruled out as graph shape by ADR 0001's own words, *"a string
  is not queryable."*
- **Why a reified node and not edge properties:** it is the only shape that holds both
  origins uniformly. The server occurrence's locator is host+path, the repo occurrence's
  is repo+ref+commit — an edge-property shape hung off `:ExecutionHost` cannot carry the
  repo half at all, and one-file-from-three-sources is this gate's whole premise.
  Standards binding: **`prov:specializationOf`**, the term ADR 0001 already cites.
- **This does NOT contradict the D-amendment's deferral of the storage-locus node.** That
  one was deferred as *"an entity with no source"*; occurrences have a source in every
  bundle — every listing row IS one. The deferral reason does not transfer.
- **The extractor fix is a precondition of G23's existing acceptance, not new scope:**
  G23 already demands a two-source fixture proving single-node merge, and it cannot pass
  while the extractor drops the second occurrence. Merged into G23 rather than groomed
  as a new item.

- **D3 RULED — three parts.** (i) **The match is `rua_fqdn` → `ExecutionHost.nodeid`, NOT
  `rua_host`.** `config/source-mappings/psgmgr.yaml` records NODEID as *"member agent
  host FQDN (8,161 distinct); ExecutionHost node key (constraint
  `executionhost_nodeid`)"* — the deployed key already holds fully-qualified names, so
  the bare hostname would simply fail to match. The envelope stamps both spellings, so
  honouring this costs nothing. Where `rua_fqdn` is absent or unqualified the record
  stages **unresolved and counted**, never matched on the bare hostname: a cross-domain
  prefix match is the guess the never-silent house rule forbids, and its failure mode is
  binding a script to the **wrong server**, which is worse than not binding it. P3's
  `executionhost_nodeid` UNIQUE constraint stands as the key; rua mints no second host
  identity — which is what the SME's nodeid-is-the-real-server-name input implied.
- (ii) **The AppUser half is HELD** behind A1/K17, exactly as C1's `to_node` is. Ruling
  `(user, uid)` vs user-only while the `:AppUser` key is unsettled would re-create the
  silent split `fid-identity-and-scope` §A1 exists to prevent.
- (iii) **What `cross_host_collisions` means:** not "two scripts" and not "deployed
  twice". It is the **ambiguity signal** — one file seen N times under shared storage, or
  N genuinely different files under local storage, undecidable without fstype (G56) or a
  content hash (absent *by contract* in the metadata-only listings, premise 2). It is the
  review-queue feed, which is what it was built as. A rename (*collision* implies
  conflict; the counter measures repetition) rides G55/G23, not the gate.

- **D4 RULED STUB — ruled here rather than deferred to the envelope gate.** The deciding
  argument: **deferring and ruling produce identical load behaviour**, since
  `audit-fields.yaml`'s own rule is that loaders must not write envelope properties for
  stub sources. Ruling is strictly better — same behaviour, and the reason is recorded
  instead of re-derived later.
- **The reason is standing law already.** meta.txt is a **capture** envelope, not an
  authorship one: `collected_at` / `collected_by` fall under the CAPTURE_DATE rule signed
  at `controlm-q1q3-phase1` — *"replication time — never authorship"*. The two per-file
  candidates were considered and both rejected: **`mtime`** is when the inode was last
  written on that host, which a deployment `cp` resets, making it a **deploy** timestamp
  — and §E1 of this same gate ruled that presence is a deployment fact and nothing more,
  so mtime inherits that limit exactly; **`owner`** is an ACL fact and not the changer (it
  is C1's `directory_owner` input, never `source_updated_by`). Both stay **plain
  properties**, the same disposition AUTHOR has on the Control-M entry.
- **The as-built split is confirmed as built:** 12 envelope keys stamped on every staged
  record, the full meta.txt retained un-stamped in `coverage.meta`. Nothing is lost and
  nothing unratified is stamped.
- **Applied this session** as the `exec-hosts:rua-bundle` entry in
  `config/audit-fields.yaml` — documentary only (a stub writes nothing), matching the
  `audit-envelope-phase4` precedent where four ruled stubs landed the same day as their
  gate.
- **§J PRECONDITION FOUND, verified against the guard rather than assumed:**
  `tests/unit/test_audit_fields.py::test_every_confirmed_source_has_an_entry` requires
  every `confirmed: true` registry source to hold an audit-fields entry — and
  `exec-hosts:rua-bundle`, `bitbucket:repo-objects-manifest`, `dpl:pipeline-registry` and
  `dpl:dataset-registry` are **all `confirmed: false` today**. Flipping them at §J without
  entries **fails the suite**. §D4's authority covers the rua envelope only, so the other
  three are **not** ruled here; §J must rule or groom them. Likely quick: bitbucket is the
  git-history-IS-the-envelope permanent stub already used for `repo:software-registry` /
  `repo:design-docs` / `repo:depgraph-snapshot`, with the manifest's `commit` +
  `commit_date` as the **pointer into** that envelope rather than the envelope itself; the
  two dpl rows need their extract's columns looked at first.
- **Still open:** H1–H2, I1–I3, §J sign-off. Sections A, B, C, D, E, F, G and H3 are done.

## 2026-08-06 — RECORD: rua load shapes, section H — three axes that can each only prove presence

**Gate:** `rua-load-shapes` (backlog G22) · **still UNSIGNED** — a RECORD entry, not a
sign-off. H1 and H2 confirmed; with H3 (already recorded) **§H now closes**.

- **H1 CONFIRMED — and it confirms what the code was already written against**, the G1
  shape a second time. `dpl_registry.py`'s own docstring: the active flag is *"a THIRD
  usage signal (beside referenced and present-on-server), staged only: any conflation
  with 'used' is a G22 clause-(f)/(g) ruling, never decided here."* **Verified clean at
  the ruling** rather than assumed: no `used` property exists anywhere in the codebase,
  so H1 ratifies a state that already holds and requests no cleanup.
- **(i) Each axis is three-valued, not two.** The registry flag normalizes
  bool / ACTIVE / INACTIVE / Y / N to true or false, and **any other spelling stays empty
  and is counted** (`active_unknown`). Under the house rule set at the D-amendment —
  *unknown must not default to the convenient value* — an empty flag reads as neither
  active nor inactive. This constrains H2 directly.
- **(ii) No axis can prove absence.** All three are **positive-only** observations, each
  bounded by a *different* coverage limit:
  **referenced** by body-copy coverage (E3's named blind spot — the metadata-only
  listings of premise 2 carry no bodies, so script-to-script calls are structurally
  invisible); **present-on-server** by `scan_roots` — a script outside the scanned roots
  is absent-from-*bundle*, never absent-from-server; **registry-active** by which SEALs
  were exported, and G25's own note makes the registry a **backup discovery source**
  rather than a census, because the promotion clone's `main` may lag.
  So *"absent on axis X"* always means *"not observed by feed X"*, never *"does not
  exist."*
- **(iii) Why that matters here and not only in E3:** it makes E3's
  flagged-never-auto-judged a **structural** property of the three axes rather than a
  cautious choice someone could later optimize away.

- **H2 CONFIRMED — and the precedent it names was verified SIGNED**, checked rather than
  taken on the page's word: `controlm-avg-run-supplement` (2026-07-14, 20 confirmations;
  the source-registry row cites it as the confirming gate) §P5 — *"NODE_GROUP
  cross-validation vs CM_HOSTS/RUNS_ON is a bonus report feeding remediation,
  **non-blocking** for this supplement."* Non-blocking is the load-bearing word, and it
  is what *"not load errors"* means concretely.
- **(i) The mechanism already exists and has a name**, so H2 costs no new machinery:
  `drydocs_remediation/detect.py` emits findings with **`ratified=False`** — WARN-only
  downstream — until the machine-readable standards-rules registry drives that field, and
  detection is **failure-driven rather than scheduled** (ADR 0002-B §2). H2's two findings
  are candidate **rules** for that registry, and `ratified` IS the
  reported-never-auto-corrected mechanism in built form. Registry entries ride I1/G55, not
  the gate.
- **(ii) The two findings are not the same kind of finding**, and conflating them would be
  its own error given E3's deletion use case.
  **`active=false-but-referenced`** means *something still calls what the registry calls
  retired* — an **operational-risk** finding, a live caller against a decommission
  candidate. It is never a delete candidate; it points the opposite way.
  **`active=true-but-unreferenced`** means the registry says live and nothing was observed
  calling it — this is the one that *looks* like a delete candidate, and it is **the most
  dangerous false positive available**, because E3's known blind spot (no body copies, so
  script-to-script calls are invisible) is exactly what would hide the caller. It
  therefore inherits E3's body-copy coverage precondition in full: on a metadata-only
  bundle it may not be reported as a deletion candidate at all.
- **(iii) The third case the clause omits:** an **unknown** active flag produces *neither*
  finding. It must be reported as unclassifiable-and-counted, never silently dropped —
  otherwise the finding report understates by exactly the `active_unknown` count. The
  never-silent house rule applied to the report rather than to the load.
- **Still open:** I1–I3, §J sign-off. Sections A–H are done.
