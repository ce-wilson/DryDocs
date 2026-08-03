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
