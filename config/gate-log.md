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
    not SOR/ADS, and CDO SOC was checked (§H vocabulary: System of Capture =
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
| `bmc-docs` / `essential-graphrag` / `cdo-frameworks` | NOT renamed — pipeline twins dropped; ids stay live in `config/doc-source-registry.yaml` (one home), which now carries their `confirmed:` state | bmc-docs-lexical-load 2026-07-08 (covers essential-graphrag per the Q2 groom) |

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
  `internal/cdo-reference` (the PAT-catalog artifact described as a 5-level
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


## 2026-08-05 — GATE: cdo-crosswalk (Epic W; drafted at W1) — SIGNED OFF, 13/13 (row 5 stays blocked-on-recapture)

**Spec:** `config/gate-prompts/cdo-crosswalk.yaml` · **SME:** chad.wilson, in-chat
(section walkthrough; page rendered to `internal-local/gate-pages/`). The DryDocs ↔
firmwide-framework vocabulary crosswalk (`config/crosswalks/cdo-vocabulary.yaml`,
8 rows). Ratifies the ALIGNMENT-PLAN verdict: already structurally aligned — every
row maps an EXISTING DryDocs term to a standard term; nothing renamed, reshaped,
or added.

| Item | Ruling |
|---|---|
| A1–A4 scope | **CONFIRMED** — review-only; mechanism-only surfaces (standard CURIEs, no internal names); nothing new minted; the ALIGNMENT-PLAN skip list is binding. **SME remark on A:** activation of the `cdo-frameworks` corpus is UNDER CONSIDERATION now that alignment is verified — it remains a separate registry decision, NOT flipped by this gate. |
| B1 rows 1/2/3/7 exact | **CONFIRMED** — ControlMJob↔OL Job, JobRun/ControlMJobRun↔OL Run, DataAsset↔Dataset, SUBCLASS_OF/MAPS_TO↔rdfs bridging. |
| B2 row 2 scope note | **CONFIRMED** — the 2026-07-31 batch-history ruling restated; name conformance only, no run-event-ingestion mandate. |
| B3 row 4 grain split | **CONFIRMED** — their grain is the Run, ours the definition (ETLProcess \| ControlMJob); both grains recorded; any future run-grain lineage lands on ControlMJobRun without displacing the definition-grain edges. |
| B4 row 6 documentation-only | **CONFIRMED** — the adms:status reading is a translation aid; the proposed→confirmed→applied HITL machinery changes in no way. |
| B5 row 8 carrier difference | **CONFIRMED** — RECONCILES_TO {confidence} carries skos:closeMatch + mapping-confidence semantics on an edge property rather than an RDF mapping resource. |
| C1 row 5 blocked | **CONFIRMED** — stays OPEN, signed neither way, until the registered `cdo-frameworks` scrape recaptures the Descriptive Metadata Framework. |
| C2 absence ≠ absence | **CONFIRMED** — transcript absence is never treated as absence from their standard. |
| D1–D2 sign-off | **CONFIRMED** — rows 1–4, 6–8 and the file status flip proposed → confirmed; row 5 stays `blocked-on-recapture`; the guard test moves to the post-gate state in the same commit (F1/F2 precedent); corpus activation stays a separate, later decision. |


## 2026-08-05 — RECORD: `cdo-frameworks` corpus ACTIVATED (user ruling in-chat, same day as the cdo-crosswalk sign-off)

- **What this records:** the in-chat user ruling activating the `cdo-frameworks`
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
- **What activation does and does not do:** `require_confirmed("cdo-frameworks")`
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
  the G51/X1/`cdo-frameworks` RECORD idiom — direction, not a gate session.
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

## 2026-08-06 — RECORD: rua load shapes, section I — the consequences ledger, and a tracker that knew more than the clause

**Gate:** `rua-load-shapes` (backlog G22) · **still UNSIGNED** — a RECORD entry, not a
sign-off. I1, I2 and I3 confirmed; **§I closes, and every clause but §J is now ruled.**

- **I1 CONFIRMED — mechanism verified present, and two things fixed at the ruling.** G55
  exists (groomed at this session) and its acceptance already encodes the three
  dispositions: activated entries go planned → active **with** their supplement block (an
  entry cannot be active without one — that is what `active` MEANS in `00-header.yaml`'s
  lifecycle), new meanings land `status: planned` via ontology-mapper, declined entries
  retire with a note naming the ruling, date and replacement. No loader is built there
  either; that is G23.
- **Fix 1 — G55's `inputs` were incomplete, corrected at this session.** They named
  `40-local-controlm.yaml` only, which carries `m3_invokes` (B2's widening) but none of the
  rest this gate ruled. Added **`43-local-architecture.yaml`** — where C1's
  `WAS_ATTRIBUTED_TO {role: directory_owner}` belongs beside its own `arch_owns_code`
  precedent, where C2's `SOURCES` belongs, and where C3's `IS_ENCODED_IN` **already lives**
  — and **`10-node-classifications.yaml`**, where D2's occurrence node class belongs (the
  same file already holds the `:Script` and `:AppUser` labels). Not pedantry: an inputs
  list is what a sub-agent reads, so an unlisted fragment is an unedited fragment.
- **Fix 2 — D2 ruled a NODE class, not only an edge**, and the supplement discipline
  applies identically: `10-node-classifications.yaml`'s own header requires every `dd:*`
  class to be MERGEd as `:OntologyTerm:LocalClass` in a supplement, so the occurrence class
  needs label + class + prov_type + its supplement block exactly as an activated
  relationship does.
- **The G55 open question is raised here, which is what its notes asked for.** The
  lifecycle offers planned | active | deprecated | removed and **none** describes
  *"declared, never built, ruled unnecessary"* — `deprecated` asserts data is kept (false;
  `m3_runs_on_etl_host` never loaded), `removed` asserts data and code were deleted (also
  false; there was never any). **Recommendation for §J:** use `removed` with an explicit
  never-built note — the deletion clause is vacuously satisfied and no schema change is
  needed — rather than minting a fifth status, which would itself be a vocabulary change
  riding a gate. §J rules it; G55 must not decide it alone.

- **I2 CONFIRMED, with one correction the page needs because it predates source-registry
  v2.** *"precedence.yaml rows"* is a **pre-v2 drafting artifact and no row is owed.**
  `precedence.yaml` is an ordered **authority** chain about *what something IS* — four
  authorities, each with a `governs:` concept list and a conflict policy for when
  authorities disagree about an object's meaning. **§E is not that question:** both code
  feeds agree what a script IS and disagree about *which copy is current*, which is
  feed-level, and `precedence.yaml` has no grain for it.
- **Feed-level authority already has its home**, built at N7 and signed 2026-07-31:
  source-registry v2 **dataset rows carry an `authority` field** — verified in place,
  `exec-hosts:rua-bundle` carries `authority: SOR` today — beside `trusted_ref` on the repo
  row (built at G24). §E's ruling already landed there this session as the corrected
  `bitbucket` system note. Recorded deliberately so a later reader does not read the
  absence as an oversight and add a row that would mis-state what `precedence.yaml`
  governs.
- **gates.json verified live**, not assumed: `scripts/render_gates.py` regenerates it and
  the file has moved in every commit of this session. **The guard is stronger than the page
  describes, in exactly the way this gate needed** —
  `test_a_citation_or_partial_ruling_never_accounts_for_a_gate` means the RECORD entries do
  **not** make G22 count as accounted-for, and `test_unsigned_but_cited_gates_render_open`
  keeps G22 rendering **open** until §J signs. Status derives from the log heading
  **verbatim** (signed-off | deferred | pending | recorded), so the page never reinterprets
  the record — precisely the property the RECORD convention depended on, now confirmed
  rather than hoped for.
- F1's classification output is a **test** over the QuerySpec registry (no publishable spec
  returns a column in the confidential set), not a config row — vacuous today since every
  spec is Internal, and it guards forward.

- **I3 CONFIRMED, with a material amendment — the tracker records something the clause does
  not**, found by reading T16 rather than citing it.
- **(1) "The seam retires" is imprecise, and the halves differ.** T16 says the G39 **staging
  stand-in** retires *as the feed*, while the **G40 parse stays as a cross-check**. One is
  retired, one is kept; collapsing them would quietly delete a live check.
- **(2) The amendment that changes the clause — T16 records a SECOND retirement path that
  I3 does not:** *"if the XML export becomes a standing feed, this retirement gains a SECOND
  path — the unruled precedence question decides, not the port."* So *"no re-gate needed"*
  holds **only** for the single-path case where `CM_DEF_VJOB_DETAIL` lands and the staging
  seam steps aside. **Two standing feeds for the same CMD_LINE fact is a precedence
  question**, §E is its home, and §E did not rule it because it was never on the page — so
  the two-feed case **re-gates**. Note this is feed-level precedence, exactly the grain §I2
  just placed on the source-registry dataset row rather than in `precedence.yaml`.
- **(3) The premise is a belief, not a verified fact**, and I3 should say so: T16's status
  is *"pending (producer belief, as of 2026-08-01)"*, so the table being built for real
  company-side is expected, not confirmed.
- Everything else in the clause stands: the fact *shapes* are what a re-gate turns on, and
  a like-for-like feed swap disturbs no ruling this gate made.

- **Still open: §J sign-off only.** Sections A through I are done.

## 2026-08-07 — GATE: rua-load-shapes (G22) — SIGNED OFF, 28/28

**Gate:** `config/gate-prompts/rua-load-shapes.yaml` · **backlog G22** · SME sign-off
2026-08-07. THE TERMINUS of the G18–G21 / G24 / G25 candidate chain: nothing rua-shaped
wrote the graph before this entry, and the terminus held for the whole walk — five staging
seams, two real production bundles on the company side, zero graph writes.

Walked section by section 2026-08-06 → 2026-08-07, with each section transcribed to the page
and recorded here as it closed (nine `RECORD:` entries above this one, all of them still
accurate — this entry supersedes none of them, it closes the gate they left open).

### Per-item outcomes (28)

| Items | Outcome |
|---|---|
| **A1** | **HELD** behind K17 — `m3_delegates_to` may not activate while its subject has no agreed key |
| **A2** | **DECLINED** as redundant — ETL placement is the same fact as job placement |
| **A3 · A4 · A5** | **ACTIVATE** — `m3_invokes` (endpoint widened per B2), `m7_uses_artifact` (deliberately in the same breath), `m3_reads_from` / `m3_writes_to` with the restriction restated |
| **A6** | **CONFIRMED** — anything unticked stays planned and candidate-side |
| **B2 · B3** | **B2 CHOSEN** (B1 not chosen) · **B3 CONFIRMED** |
| **C1 · C2 · C3** | **RULED** — all three land `status: planned`; C3's `.ksh` adapter addition applied at the session |
| **D1 · D2 · D3 · D4** | **RULED** — normalized absolute path · reified occurrence nodes · three parts · stub |
| **E1 · E2 · E3** | **CONFIRMED** — E1 with the SME caveat that retires "latest code that actually runs" |
| **F1 · F2** | **F1 RULED** the confidential set · **F2 CONFIRMED** |
| **G1 · G2** | **G1 RULED** both-not-either · **G2 CONFIRMED**, scoped to scripts |
| **H1 · H2 · H3** | **CONFIRMED** — H3 added at the session on SME evidence |
| **I1 · I2 · I3** | **CONFIRMED** — I2 with one correction, I3 with a material amendment |

Count: A1–A6 (6) + B2+B3 (2) + C1–C3 (3) + D1–D4 (4) + E1–E3 (3) + F1–F2 (2) + G1–G2 (2) +
H1–H3 (3) + I1–I3 (3) = **28**. Of the six activation candidates the acceptance named, one was
already active before the session, **three activate, one is declined, one is held**.

### The three preconditions, all found during the walk rather than at drafting

**(1) The audit-fields entries §D4 refused to rule.** All three land `status: stub`, with
**three different reasons**, because they are not the same case.

- **`bitbucket:repo-objects-manifest`** carries no author field at all, and its one date is not
  what it looks like: a manifest row is one *(ref-tip, path)* pair, so `commit_date` is the
  **tip's** date — `corroborate()` ranks refs by it to name `candidate_ref`. It records when the
  **branch** last moved, never when the **file** changed, so `source_updated_at` would assert a
  change date belonging to an unrelated commit. That is the mtime error §D4 rejected on the rua
  side, arriving through a different column. Its reason also differs from the `repo:*` stubs it
  resembles: for our own repo "git IS the audit trail" is true **and reachable** via `git blame`,
  whereas this envelope lives in a repo DryDocs never holds — **out of reach rather than absent**,
  which is what makes its revisit trigger real, the manifest contract being ours to specify.
- **`dpl:pipeline-registry` / `dpl:dataset-registry`** stage no audit columns either, but the
  honest reason is that **the field contract is assumed and has never been validated**
  (`dpl_registry.py` says so in its own header; tracker **T13** is the named trigger, status
  *pending (producer belief, as of 2026-08-01)*). A real export may well carry `createdBy` /
  `lastModifiedBy`; until one parses, claiming either an envelope **or** its permanent absence
  would be a guess. Precedent verified rather than assumed: `autosys:export` and
  `airflow:dag-export` are both `confirmed: true` from signed crosswalk gates while their audit
  entries read that native columns are unknowable until a live export exists.

**(2) The G55 lifecycle question §I1 raised — RULED `deprecated`, which reverses this session's
own recommendation.** §I1 and the G55 notes both recommended `removed`. Checking the registry
before writing it into §J found the question **already answered by a signed gate**: four entries
retired never-built (`loader: ~`) sit at `deprecated` — `m3_seal_app_ref`,
`seal_requires_scheduler`, and `arch_contains_batch` + `arch_contains_folder`, the last two
retired at **K7** (`seal-app-ref-edge-reshape` §C2, **SIGNED OFF 2026-08-03**) with notes reading
verbatim *"never gated, never loaded"* — exactly the case §I1 said the lifecycle had no status
for. **Nothing in the registry is `removed`.**

`removed` is wrong rather than second-best: it means *code deleted*, so it would license deleting
the entry **and the note naming the ruling** — the opposite of retiring something on the record —
and it would split the retired set across two statuses that mean the same thing. **The real
defect was the gloss**, amended at this sign-off in `00-header.yaml`: the old one-line wording
described only the was-loaded case and read as *false* for never-built entries, which is what sent
two readers looking for a fifth status. Comment-only — no status, entry, direction or semantics
moves (the C15 carve-out class). A fifth status would additionally have failed
`tests/unit/test_lineage_writer.py`, which pins the vocabulary to the four values.

*Why the first pass missed it:* the fragments align their columns (`status:       deprecated`), so
a single-space grep matched nothing and read as "no precedent exists". The lesson is the one this
gate kept re-learning — D1 was the same shape, where `cmdline-lineage-review` §c had already
retired basename as a candidate.

**(3) The source-registry flips.** All four dataset rows go `confirmed: true`, each against the
activation condition its own row states: `exec-hosts:rua-bundle` (clauses a–g, all ruled),
`bitbucket:repo-objects-manifest` (§D1/§D2 identity + occurrence grain, §E precedence between
origins), `dpl:pipeline-registry` (§G clause f + §H clause g), `dpl:dataset-registry` (same
condition). **The flip is authority to load, not a loader:** every row keeps `adapter: ~` and G23
is the curated build — the autosys/airflow rows are the standing precedent for exactly that state.

### What this sign-off does NOT unblock

Recorded so it is not read as a clean release: **A1 stays held behind K17**, and **C1 lands
`planned` but cannot be built before K17 signs** — both need the `:AppUser` key that
`fid-identity-and-scope` owns.

### Follow-ups carried out of the gate

- **G55** — apply the vocabulary consequences (activations → `active` with supplement blocks; new
  meanings → `planned`; `m3_runs_on_etl_host` → `deprecated` per (2) above). Now unblocked.
- **A second inputs gap, the same class as §I1's:** `tests/unit/test_lineage_writer.py` is the
  terminus **in code** — `test_live_load_is_gate_bound_against_the_real_registry` asserts a live
  load **raises** `GateBoundVocabularyError` on `m3_invokes`, and its own docstring says it flips
  to the execution contract *deliberately, not silently*, once the gate activates those entries.
  The A3/A5 flips **are** that event, so the guard inverts at G55 and must be retired
  deliberately — never repaired by deleting the raises-check. `tests/unit/test_schema_graph.py`
  rides along, since deprecating `m3_runs_on_etl_host` drops it from `RENDERED_STATUSES`.
- **G23** — the curated rua load, carrying the extractor fix §D2 merged into it (the second
  arrival of a staged id is currently dropped, and G23's own two-source fixture cannot pass until
  it is fixed).
- **G56** (collector mount capture, schema v3 — the D-amendment's workaround) and **G57** (the
  `rua_*` → `bkup_*` rename).

## 2026-08-09 — GATE: software-version-context (C25) — SIGNED OFF, §A–§E + §G; §F BLOCKED

**Prompt:** `config/gate-prompts/software-version-context.yaml` (drafted 2026-08-04).
**Backlog:** C25. **Venue:** desktop, SME in session.
**Scope signed:** §A grain · §B edge shape and version cardinality · §C derivation ·
§D the evidence document · §E adhoc boundary · §G confirmations.
**Not signed, deliberately:** §F, the application-level rollup — it depends on gate
`fid-identity-and-scope` (K17) and is not written provisionally, not behind a flag.

### §A — GRAIN. The verb was the blocking question, and it held.

**A2 first, by the person who compiled the table: USAGE.** The rows assert that the functional
id RUNS workload on that install — not entitlement, not mere presence on a host. `USES_SOFTWARE`
is therefore the correct label, **§A3 did not fire**, and no second availability entry is needed.
Recorded because the recommendation guessed the other way: the gate's own advice said *"a
readiness review usually inventories availability"*, and the OWNER-NOT-USER distinction had
already cost a modeling round at K7. The SME's answer overrode the recommendation, which is
exactly why §A2 is asked of the compiler rather than reasoned from the document type.

**A1 CONFIRMED as drafted.** Load grain is the functional id: `(:AppUser)-[:USES_SOFTWARE]->
(:SoftwareProduct)`, one edge per (fid, install path). The application-level edge is DERIVED
(§F), never authored from this evidence — writing it directly would bake a mutable ownership
join into a fact and discard the only grain at which it can be re-derived when a fid transfers.

### §B — EDGE SHAPE and VERSION CARDINALITY. All four confirmed as drafted.

- **B1** — vocabulary entry `reg_appuser_uses_software` registered `status: planned`
  (`drydocs_core/ontology/relationship_vocabulary/44-local-registry.yaml`): AppUser →
  SoftwareProduct, label `USES_SOFTWARE`, `prov_maps_to: ~` (LOCAL — PROV has no Agent → Entity
  usage row). A separate entry sharing the label, not a widened range: the C8-clean precedent
  from `docs_chunk_part_of` / `doc_section_part_of`.
- **B2** — MERGE key is `{source, install_path}`. Not `{source}` (correct only while one source
  asserts one fact per pair, and wrong here), and not `{source, version}` — version is DERIVED
  from install_path, so keying on it would let a parser change silently re-key existing edges.
  Two installs that parse to the same version stay two edges, which is the truthful answer.
- **B3** — edge properties as drafted; the four audit-envelope properties are NOT written. An
  email has an author and a sent date, which is the DOCUMENT's provenance and not the row's. The
  `config/audit-fields.yaml` disposition stays `stub` (audit-envelope-phase4 precedent).
- **B4** — `as_of` is the email's SENT date, never the load date. `first_seen_at` /
  `last_seen_at` / `last_run_id` keep their standing when-WE-saw-it meaning and are not
  overloaded.

**§Q2 answered, and it makes B2 permanent rather than provisional: parallel installs are REAL.**
Migrations run old and new side by side, so several live edges per (fid, product) is the truth
and not an artifact of accumulated history. G3's 1:N ruling holds, no uniqueness constraint may
be added, and — the part worth recording — **no `current` discriminator is needed**. Had the
answer been "uncleaned installs", the graph would have required a discriminator this evidence
cannot supply, and the load would have shipped with a named gap.

### §C — DERIVATION. C1–C4 as drafted; C3 and C5 ruled.

- **C1** — the path → product match is a PATTERN TABLE row in the
  `software-registry.yaml#invocation_patterns` shape, not loader-embedded regex, so the two
  software-detection surfaces share one reviewable table. Ruled as SHAPE; authoring the rows is
  a build follow-up, not this item.
- **C2** — observed versions do NOT auto-append to the product's curated `versions:` list.
  What the product IS stays human-curated; what the estate is RUNNING lives on edges.
- **C3 RULED — never pad. Absent is not zero.** `V4-3-2-2` → `4.3.2.2`; `V4-3-2` → `4.3.2`,
  three components, as found. Both forms are stored: `version_raw` verbatim from the path,
  `version` normalized. Padding would assert a fourth component no source declared, and
  `4.3.2` / `4.3.2.0` may be genuinely different installs. The cost is accepted openly:
  comparison queries must handle ragged component counts.
- **C4** — a path matching no pattern row is reported unresolved and loads nothing. No
  nearest-match product assignment, ever.
- **C5 RULED — add the `evidence:` block** to the `abinitio` product row (corpus + as_of + a
  note that the rows are fid-grain and hand-compiled). §C2 correctly forbids observed versions
  from editing the ledger, but that left a real asymmetry: a row empty because nothing is known
  read identically to one empty because evidence exists and has not been reviewed. A pointer is
  not a version, so the ledger stays curated while the silence becomes visible. Same shape as
  the `documentation:` block on the `controlm` row.

### §D — THE EVIDENCE DOCUMENT. All five confirmed; D2 chose option (a).

- **D1** — ONE corpus `adhoc-sme-email`, already registered in `config/doc-source-registry.yaml`
  (connector `email`, tier T4, curation `sme-confirm`, target_db `ddcontext`, trust_default
  VERBATIM, refresh manual). Individual emails are `:Document` rows inside it; one corpus per
  email would turn the ledger into an inbox. **`confirmed:` stays `false`, for a NEW reason** —
  it no longer means "awaiting the SME", it means no loader exists. The flip belongs to the
  adhoc loader's own build.
- **D2 RULED (a) — PROPERTY POINTER `evidence_doc_id` on each edge.** Option (b), a node-grain
  `HAD_PRIMARY_SOURCE` edge, was rejected as answering the wrong question: it asserts the fid
  was sourced from that email, not that THIS VERSION claim was. Option (c), a reified
  `:SoftwareUsage` assertion, is correct and precise but heavier than one shared batch document
  justifies — `doc_feedback_authored_by` set the precedent that reification waits for a
  disambiguating payload the collapsed form cannot carry. (a) and (c) are not exclusive over
  time: (c) is the named upgrade path if a recurring version feed arrives, and the pointer is
  what makes that migration mechanical.
- **D3** — trust is SPLIT and the split is the point: the DOCUMENT is VERBATIM (the SME's own
  words, stored as sent); FACTS DERIVED FROM IT are GROUNDED at best, because the attachment is
  hand-compiled with a known-mislabeled identifier column (gate `fid-identity-and-scope` §A).
  The defect is recorded ON the corpus entry so no later reader treats the attachment as clean.
- **D4** — CITATION-ONLY: one `:Document` carrying doc_id / subject / sent_at / custodian /
  source_digest / corpus_id, with NO body text and NO `:Chunk` chain. The body carries named
  individuals and internal addresses, and no connector exists to refetch it reproducibly.
- **D5** — the raw email and attachment stay company-side under `internal/`, with the stored
  path on the registry entry. Never committed to this repo.

### §E — ADHOC BOUNDARY. All four as drafted.

`source` is `adhoc-abinitio-version-<yyyymmdd>` — dated, so the batch is one MATCH away from
being found, re-run or swept, and a second readiness review cannot collide with the first (E1).
`origin` is `declared` — human-asserted, superseded rather than swept when a derived edge for
the same pair arrives (E2). The NAMED REPLACEMENT is plan-07 Phase 3 CMD_LINE detection (gate
`software-usage-patterns`), with version detection from resolved paths as the extension this
evidence justifies asking for (E3) — recording the replacement is what keeps the adhoc row from
becoming permanent by default. The load registers in `config/manual-loads/manifest.yaml` even
though its payload is not the tier-5 CSV shape, so one queue holds every human-authored fact
(E4).

### §F — NOT SIGNED. Blocked on `fid-identity-and-scope` (K17).

The rollup is the fact a support user actually wants ("which versions is my application on?")
and it is one join away — but that join is the whole subject of K17. Until it signs, the
application-level edge is not written **at all**: not provisionally, not behind a flag.

### §G — CONFIRMATIONS

Signed for §A–§E. Nothing was written to the graph, no loader was built, and the one vocabulary
entry landed `planned`. The two prerequisite product rows (`snowflake`, `dpl`) were registered
before the gate ran, as taxonomy capture only — a product row says the product exists, never
that any application uses it or at what version.

### Follow-ups carried out of the gate

- **The adhoc loader** — build `reg_appuser_uses_software`'s loader, flip the entry to `active`,
  register the load in `config/manual-loads/manifest.yaml`, and mint the `:Document` from a
  hand-recorded citation. Groomed as a follow-up; nothing was built here.
- **The §C1 pattern rows** for the install-path → product match, in the `invocation_patterns`
  shape. Now unblocked for DPL specifically: the missing `dpl` product row was what the
  2026-07-27 G26 guard catch cited when it removed `abinitio-dtlaunch-wrapper`.
- **§F stays open** and is the item to re-run once K17 signs.
- **Q3 DEFERRED with its consequence stated** (not asked, not guessed): is `install_path` stable,
  or do symlinks re-point the same logical install? If a symlinked estate is later confirmed,
  path is a poor MERGE key and identity would move to (fid, version) — a re-key, so the answer
  is worth having before the loader is built rather than after.
- **PORT RELAY** — the producer is now canonical for the `dpl` and `snowflake` product rows, the
  `in-house` vendor, and the `DPL` acronym expansion. The SME began the same expansion
  company-side on 2026-08-07 and stopped so the two would match; this entry is the producer-side
  half. The relay is NOT written into `docs/port-prompt.md` yet because a port is in flight
  against a fetched head and that file is a hand-merge surface — add it once that port merges.

## 2026-08-12 — RECORD: the downstream consumer contact attaches to a `:Port`, not to job/folder (email-dl-contact-point §G5; SME direction in-chat, 2026-08-12)

- **What this records:** in-chat SME direction answering §G5 of the DRAFTED-AND-UNSIGNED
  `email-dl-contact-point` gate. It is logged as a RECORD rather than a sign-off because a
  confirmed clause inside an unsigned gate reaches no log otherwise — the failure mode found
  2026-08-06. The gate stays unsigned; nothing else in it moves.
- **The ruling:** the downstream consumer contact attaches to a **`:Port`** (the DPROD shape
  the captured MFTS standard already uses), not to the job or folder (the §B1 contact-point
  shape).
- **Why, and the second reason is a constraint rather than a preference:** (i) the contact is
  **unstructured** data; (ii) **no supernodes** — the B1 shape produces one at estate scale,
  because a shared distribution list becomes a single node accreting an inbound edge from
  every job or folder that notifies it, and the most-shared DLs are precisely the ones the
  whole batch estate points at. Port-scoping bounds the fan-in by construction.
- **Also a direction on §G2 (grain):** the **known `email_dl` comes from FOLDER METADATA** —
  the folder variables (`L2_EMAIL_DL_NM` / `L3_EMAIL_DL_NM`) carry the known value, not the
  per-job Description tokens. This does NOT settle the rest of G2: precedence when folder and
  job disagree, whether both spellings survive, and what a loader does on disagreement are
  all still open.
- **Still open in §G5:** whether the port leg splits off into its own gate. Direction answers
  the "which home" half only.
- **Consequence for G44 (data catalog):** the fork §G5 warned about — "picking one without
  seeing the other is how the two plans fork" — is now resolved in one direction, so the
  data-catalog gate's clause A gains an A6 cross-reference recording that the sibling gate
  has ruled `:Port` for the same class of downstream fact. Nothing loads from either gate.
- **Nothing enacted:** no vocabulary entry registered, no status changed, no graph write. The
  DPROD port shape still has no entries in the relationship vocabulary.

## 2026-08-11 — RECORD: TOM roles (G35), walk round 1 — six rulings, one of which changes the port

**Gate:** `tom-roles-enumeration-and-cardinality` (backlog G35) · **still UNSIGNED** — a RECORD
entry, not a sign-off. Six clauses confirmed at a live SME walk; §H2 still governs and no graph
write is authorized. Recorded now rather than at sign-off because §H1b's finding is this repo's
own: a confirmed clause inside an unsigned gate has no home in a log organised by sign-off, and one
was stranded that way on 2026-08-05.

Evidence behind all six: `knowledge/upgrade-plans/servicenow-replica-evidence.md` (K21, §§7–8) —
the SQL probe run of 2026-08-11 and the ServiceNow API evidence of the same day.

- **§A RULED — BOTH REGISTERS, WITH A SURFACE DISCRIMINATOR.** The ServiceNow TOM catalog holds
  **100+ role types** carrying `Scope` (Individual/Group) and `Type` (Accountable/Operational/
  Approval/Assignment); the SEAL contact extract surfaces 13. The long-running 7-vs-9-vs-13 dispute
  was therefore never about the register — it was about what one feed surfaces. Both are modelled,
  and every attribution records which surface asserted it. **Two consequences promoted from optional
  to required by this ruling:** §D4 precedence is now mandatory (two ingested surfaces that disagree
  with no rule is the one outcome §D4 refuses), and §G's register must state which register each
  line belongs to, because the ServiceNow side brings Scope/Type and the SEAL 13 do not.
- **§E RULED — AUTHORED ROWS ONLY; INHERITANCE IS COMPUTED.** Of the three `Inheritance` states,
  only **Direct** (blank) and **Overridden** are authored; **Inherited** rows are derived copies
  carrying two lineage pointers (`inherited_from_ci`, `inherited_from`). The load stores the
  authored rows and derives the rest, rather than materialising a derived fact as though asserted.
  **This crosses a scope boundary deliberately:** reconstructing an inherited holder requires
  ancestor CIs, which sit ABOVE the ~200 applications DryDocs supports — including CIs owned by
  teams it does not. The pull widens to take ancestor CIs **for their TOM rows only**, and K21 §7.4
  is amended to say so rather than stretched in silence.
- **GROUP-SCOPED ROLES RULED — VOCABULARY YES, GRAPH SHAPE DEFERRED.** The group-scoped family
  (service ownership, change ownership, several change-approval teams, an eCAB team, five
  incident-resolver tiers, four problem-owner variants) enters the register with `Scope: Group` so
  the vocabulary is complete. **G35 mints NO group→application graph shape.** That shape is owned by
  the company-signed gate `snow-hpsm-queue-to-group` (2026-07-15), which already builds
  `(:BusinessApplication)-[:HAS_SUPPORT_QUEUE]->(:HpsmQueue)-[:RESOLVED_BY]->(:ServiceNowGroup)`.
  Minting a second shape for the same fact would collide at the next port.
- **§D3 RULED — A THREE-VALUED SURFACE DISCRIMINATOR, REUSING EXISTING VERIFICATION FIELDS.** The
  surfaces are **hand-verified crosswalk**, **SEAL contact extract**, and **ServiceNow TOM** — three,
  not the two §D1 described. Trust level rides on the crosswalk's existing `verified` /
  `cert_status` / `cert_next_date` vocabulary rather than a newly minted one, on the same discipline
  that reads `cmdb_rel_type`'s descriptor columns instead of splitting `name`.
- **§D4 RULED — HAND-VERIFIED > SERVICENOW TOM > SEAL EXTRACT.** Human verification outranks both
  automated surfaces; the operating-model source outranks the contact extract. This is the order
  `config/precedence.yaml` gains, and it is the reason the crosswalk was built by hand in the first
  place.
- **THE PORT GAP RULED — STANDING RELAY PLUS AN EVIDENCE-DOC RECORD.** See the finding below; no
  code moves.

**THE FINDING THAT PROMPTED THE LAST RULING, recorded because the doctrine has no slot for it.**
`snow_support_crosswalk.py`, `snow_support_crosswalk.cypher`, the `load-snow-support-crosswalk` CLI,
the `:ServiceNowGroup` and `:HpsmQueue` node classes, and the signed gate `snow-hpsm-queue-to-group`
(2026-07-15) exist **company-side only**. Verified this session: they appear nowhere in the producer
working tree and nowhere in producer git history. So G35 was being drafted over a company-signed
modelling position that the producer repo cannot see.

Guardrail 6 covers the company adopting a PRODUCER-signed gate (Tier A / Tier B). It has no
provision for the reverse — a company-signed gate with a built ontology that the producer lacks.
"Company-only" elsewhere in the port-prompt means paths and config rows, which are inert; a
modelling position is not inert, because the producer can independently invent a competing one. That
is exactly what this walk nearly did.

**Also worth recording: the two models are the same fact from different sources.** The company
crosswalk is hand-verified YAML, per-machine and gitignored; the TOM tables carry the same
app→group→technician mapping from the source, and the crosswalk's `l2`/`l3` tiers correspond to
TOM's incident-resolver tiers. That is §D1's roster-disagreement problem again, for groups rather
than people — and a real upgrade path for the crosswalk, owned by `snow-hpsm-queue-to-group` rather
than by this gate.

**Nothing is applied.** The `tom_roles` scheme keeps its 7 concepts, both loader crosswalks are
unchanged, `config/precedence.yaml` gains nothing yet, and no node class is created. Each follow-up
lands as its own logged change after this gate is signed.

## 2026-08-11 — RECORD: TOM roles (G35), walk rounds 2 and 3 — the register is ruled, and multiplicity turns out to be geography

**Gate:** `tom-roles-enumeration-and-cardinality` (backlog G35) · **still UNSIGNED** — a RECORD
entry. Eight further clauses confirmed at the same live walk; §H2 governs and nothing is applied.
Continues the round-1 entry above.

### The four modelling rulings

- **§A2 / §G5 / §G12 RULED — RISK MANAGER AND `technology_risk_controls` ARE ONE CLASS.** The SEAL
  extract's `Risk Manager` is the source's own name for the concept the scheme seeds as
  `technology_risk_controls`; the crosswalk gains that branch. This closes both halves of the
  longest-standing arithmetic problem on the page at once — the orphan concept nothing could write
  gains a source, the orphan source name flagged unmapped on every load gains a concept, and §A5b's
  count closes. **The ServiceNow evidence is what made this rulable:** Technology Risk & Controls is
  a LIVE role type with a LIVE holder there, so the class is not a fiction of our scheme, and ruling
  it required (below) no longer puts every application in breach on the first run.
- **§E4 RULED — THE ANCESTOR IS A MODELLED EDGE, not a property.** Following the §E ruling that
  inheritance is computed from authored rows, the lineage is load-bearing and the ancestor is a real
  node. An edge makes "why does this application show a different owner than its parent" TRAVERSABLE,
  which is precisely what §D2 says an operator cannot do today. The ancestor CIs this requires are
  the same ones §E already commits the pull to taking.
- **§C6 RULED — THE DENOMINATOR IS APPLICATIONS THE SOURCE ACTUALLY COVERED.** The completeness
  graph-test runs only where a feed asserted something. An application no feed mentioned is a
  CAPTURE gap and is reported separately, exactly as §C6 warned: a capture gap wearing a roster
  gap's costume produces a noisy check, and the first response to a noisy check is to weaken it.
- **§F3 / §F4 RULED — A NEW DEDICATED FILE, AND THE ORPHANED LIST IS DELETED.** The declared
  vocabulary takes its own `config/taxonomy/` file, holding both registers (§A), `Scope`, `Type`,
  the `required` flag and retirement state, with a reader and a drift guard. `roles:` in
  `config/taxonomy/business-application.yaml` — read by NO code, and the surface that drifted twice
  inside one gate without a test noticing (§A1b) — is **deleted**, not reinterpreted. §F3 named
  leaving both as the one outcome to refuse.

### The register (§G) — fourteen lines ruled

**REQUIRED** (the application must carry at least one holder): **G1** Application Owner · **G2**
Primary Information Owner · **G3** Backup Information Owner · **G4** CTO · **G5** Technology Risk &
Controls · **G6** Design Authority · **G11** Backup Application Owner · **G16** Site Reliability
Engineer.

**OPTIONAL**: **G7** L1 Operate Manager · **G8** L2 Operate Manager · **G9** Operate Manager (bare) ·
**G10** Chief Business Technologist *(ruled 2026-08-06)* · **G13** Deployment Owner · **G14**
Deployment Information Owner · **G15** Application Module Owner.

**G12** Risk Manager does not take a line of its own — it resolves into G5 per §A2 above.

**G13/G14/G15 also gain their SUBJECT**, which §G15 asked for before required-ness could be ruled:
the **Deployment Module** CI. The positional "these are optional" note from 2026-08-06 is now
confirmed explicitly rather than left to be inferred from where it sat in a list.

### Two riders on the register that are not ticks

- **G5 CARRIES A CAVEAT, recorded rather than absorbed: the mapping between the SEAL risk role and
  the ServiceNow groups is NOT KNOWN, and the direction is to implement the simplest thing that
  works.** So G5 is required as a CLASS, and the loader should crosswalk `Risk Manager` to it and
  stop there — no group resolution is designed for it in this gate. Note the ServiceNow evidence
  shows Technology Risk & Controls held by an INDIVIDUAL, not a group, which is consistent with
  there being no group mapping to find. **Open until confirmed.**
- **G16 SRE was ruled REQUIRED, and its KIND question (§G16: accountable role, or a staffing fact
  recorded on the same extract?) was not separately answered.** Ruling it required implies
  accountable — a staffing fact would not belong in a completeness report. Recorded as an inference
  to confirm, not as a ruling made.

### §G7/§G8/§G9 — the answer explains the multiplicity, and the model has nowhere to put it

The three Operate Manager classes are **OPTIONAL**, and the reason given is the finding:

> *"In our apps there could be 1, 2, 3 depending on when coverage is needed"* — the holders differ by
> **coverage window and geography** (an L2 in one region, an L2 in another).

**This is a THIRD explanation for a multi-holder role class**, and the page had only two. §B1 says
cardinality is one-or-more; §D2 asks how an operator can tell whether five holders means one roster
with five people or two rosters disagreeing; §E adds inheritance as a third source of apparent
duplication. Now there is a fourth, and it is the most benign and the most invisible: **the holders
are genuinely different people covering different regions or hours, and nothing in the model records
which.** An operator asking "who is the L2 Operate Manager" gets three names and no way to know that
the right answer depends on the time of day.

**Recorded as a candidate, not ruled:** a region / coverage-window qualifier on the holding. It is
not in scope for this gate, it is not in the SEAL extract, and whether ServiceNow carries it is
unknown. But §C4's completeness check counts to one and stops, which means it cannot tell a genuine
24h gap from a satisfied one — and that is exactly the kind of finding that check exists to make.

### And a second dimension, from the same answer

> *"We created 4 HPSM technician queues so that when we had 4 support teams covering different
> platforms the incidents would route to the correct team and associate with the correct business
> application — but we are on the path to consolidate teams again."*

Two things follow, both outside G35 and both worth having on the record. **The company crosswalk's
per-platform `l2` array is not a modelling choice, it is a routing artifact** — the queues were split
by PLATFORM so incidents reach the right team and bind to the right application. And **that split is
being consolidated**, so the tier/platform dimension in the hand-verified crosswalk is in flux. Any
model built to mirror four queues will be modelling a transitional state. This belongs to
`snow-hpsm-queue-to-group` (see §9 of the K21 evidence doc and RELAY-6), and it strengthens the
round-1 decision not to mint a competing shape here.

**Nothing is applied.** The scheme keeps its 7 concepts, both loader crosswalks are unchanged, the
new vocabulary file does not exist yet, and no graph write is authorized.

## 2026-08-11 — GATE: tom-roles-enumeration-and-cardinality (G35) — SIGNED OFF

**Gate:** `tom-roles-enumeration-and-cardinality` (backlog G35) · **SIGNED OFF** at a live SME walk,
2026-08-11. Sections A–H ruled. The two RECORD entries above this one carry rounds 1–3 in full and
are not repeated; this entry closes the remaining clauses, states the residuals, and names the
follow-up set.

**Subject — the statuses this entry flips:** `tom-roles-enumeration-and-cardinality` UNSIGNED →
SIGNED OFF. It AMENDS §B of `seal-tom-attribution-reshape` (signed 2026-07-10, applied at K4
2026-07-15); the original ruling stays readable and this amendment states what changed. It does NOT
reopen the business-application-identity fence (§A1, 2026-07-27), the attribution_id 4-part key, the
ATTRIBUTION_TIERS vocabulary, or K5/K6's Product Cabinet family.

### The closing rulings

- **§A3 / §F4 RULED — ADMIT FLAGGED, AND `SealRole` IS RETIRED AS THE ADMISSION GATE.** An
  unrecognised role name LOADS, flagged undeclared, and surfaces on the review page — the existing
  `unmapped_role` precedent used on purpose. The enum stops being the gate, because an enum cannot
  admit a name declared at load (§F1); it is demoted to an alias convenience. `_ROLE_CANONICAL`
  survives either way, since alias tolerance is a separate concern from vocabulary membership — and
  it is where the §A4 and §A6 defects actually lived. **This reverses today's behaviour, which
  silently costs four of the SME's thirteen classes (§A1d measured it).**
- **§B7 RULED — THE DEFERRAL GETS AN OWNER.** A backlog item is groomed for employee-hierarchy
  placement, so §B7 defers TO something rather than at nothing. The finding stands as written:
  `:Employee` has no Employee-to-Employee edge anywhere in the vocabulary, no `REPORTS_TO`, and until
  now no item that would create one.
- **§G9 DEFINED — and the definition arrives with a live correction attached.** The bare Operate
  Manager class is **defined by RESPONSIBILITY SCOPE, not by level**: it covers **change, problem and
  incident resolution**. That is what distinguishes it from L1 and L2, which are levelled coverage
  tiers. §A5c asked for exactly this and can be closed.

  **THE CORRECTION IS THE MORE IMPORTANT HALF, and it is a caveat on the data rather than on the
  model.** The SME reports the assignments are currently **wrong in a known way** — the team is
  recorded as carrying responsibilities it does not own — and is working with the owners to scope it
  so the team holds L1, L2 or OM **only for platforms it owns**. So **the TOM Operate Manager
  assignments are mid-correction at source.** Any load taken now captures a state that is being
  actively changed. This does not block the gate: the MODEL is what is signed here, and a model that
  can represent the corrected state can represent the current one. But it means (a) the first load's
  Operate Manager rows should not be treated as a baseline to reconcile against, and (b) §C4's
  completeness report will produce findings that are real defects being fixed elsewhere, which the
  report should say rather than imply DryDocs found them.

### Residuals — signed WITH these open, deliberately

1. **G5 Technology Risk & Controls is required, and the SEAL-risk ↔ ServiceNow-group mapping is NOT
   known.** Direction: simplest thing that works — crosswalk `Risk Manager` to the class and stop; no
   group resolution is designed for it here. Consistent with the evidence, which shows the role held
   by an INDIVIDUAL. Confirm if that changes.
2. **G16 SRE is required; its KIND was not separately ruled.** Required implies accountable, since a
   staffing fact would not belong in a completeness report. Recorded as an inference.
3. **`tom-subject-class` is unresolved and is settled by a query, not a ruling** — `GROUP BY
   cmdb_ci.sys_class_name` over the TOM rows says whether the subject is a business-application CI
   or a deployment-module CI. §G0e's fork turns on it. Signed without it because every ruling here
   is about the register and its attributes, none of which move on the answer.
4. **A REGION / COVERAGE-WINDOW QUALIFIER IS A CANDIDATE, NOT A RULING** (rounds 2–3 entry). Operate
   Manager multiplicity is geography, and nothing records which holder covers which region. §C4
   counts to one and stops, so it cannot distinguish a genuine 24h gap from a satisfied one.
5. **The replica's completeness is unconfirmed** (K21 open question 9). Every ruling here is about
   SHAPE, which survives a partial copy; counts do not — and §C4's report is a count by construction.

### The follow-up set

**§H3's rule holds: the vocabulary reshape lands as ONE unit**, because the surfaces are mutually
inconsistent if it lands piecemeal. Groomed as **G70**. The genuinely separable pieces are **G71**
(completeness report + graph-test), **G72** (three-valued surface discriminator + the precedence
order), **G73** (inheritance: assertion mode, modelled ancestor edge, and the ancestor-CI pull
widening), and **G74** (employee-hierarchy placement, §B7's new owner). K21 §7.4 is amended by G73
rather than stretched in silence.

**Nothing is applied by this entry.** Every surface named above changes in its own logged commit
under the items just listed. No graph write is authorized by signing.

## 2026-08-11 — AMENDMENT to the G35 sign-off: G16 SRE is OPTIONAL and DERIVED, not required

**Gate:** `tom-roles-enumeration-and-cardinality` (G35) · **SIGNED OFF above; this amends one
register line.** The sign-off entry named G16 as a **residual — "required, with its KIND inferred
rather than ruled"** — precisely so it could be corrected cheaply. The SME corrected it the same
day. The original ruling stays readable above; this states what changed and why.

**Subject — the status this entry flips:** register line **G16 Site Reliability Engineer**:
`REQUIRED` → **`OPTIONAL`, and DERIVED rather than asserted**. No other line moves. Nothing else in
the sign-off is reopened.

### The correction

> **SME, 2026-08-11:** ServiceNow has four default technician groups and our team is **reusing one**.
> If there is an SRE team, it can be **derived from the TEAM NAMING CONVENTION** — a function
> segment distinguishes support, development and support-SRE groups. **An SRE team serves 1:many
> applications, roughly 20 to 60.**

**Three reasons the required ruling was wrong, and they compound.**

1. **The cardinality is inverted from every other line in the register.** Every other role class is a
   per-application holding: the application has an Application Owner, a CTO, a Design Authority.
   An SRE team covers **20–60 applications**. It is a shared function pointing at many applications,
   not an accountability held by one. §B's required/optional split is about whether an application
   must carry at least one holder, and that question does not apply cleanly to a many-to-one team.
2. **It is DERIVABLE, so asserting it is the wrong mechanism.** The group naming convention encodes
   the team's function class, so "does this application have SRE cover" is answerable by reading the
   group name. A required flag would demand an assertion for a fact that is already computable —
   and would put every application in breach until somebody made the assertion redundantly.
3. **§G16's KIND question is now answered, and the answer is 'staffing, not accountable.'** The
   sign-off inferred accountable from required-ness. It is the other one: a shared operational team
   recorded on the same extract, which §G16 explicitly warned "is a different kind of fact" from
   accountability for an application.

### The evidence that makes this more than a preference

**The role label and the group's function segment DISAGREE in the sampled data, and the group is
right.** The TOM role `Incident Resolver – SRE / DevOps Team` resolves to a group whose function
segment marks it a SUPPORT group, not a support-SRE one. That is the SME's "reusing one" visible in
the data: an SRE-named role slot filled by a support technician group.

**So a crosswalk that reads the ROLE NAME to decide whether SRE cover exists returns the wrong
answer.** Only the GROUP NAME's function segment is reliable. This is the same defect class as §A3b
(a role name that does not survive the canonicalizer) and §3.3 of the K21 evidence (a relationship
type whose forward label does not identify it): **the label is not the identity.** Recorded here
because the temptation to pattern-match on `%SRE%` in a role name is obvious and it is wrong.

### Consequences

- **G16 is OPTIONAL** in the register that G70 seeds, and carries a note that it is DERIVED.
- **G70's acceptance is amended** to seed it that way rather than as required.
- **G71's completeness report must not check it.** A derived, many-to-one fact has no place in a
  per-application required-contact report; including it would generate a finding on every
  application whose SRE team simply was not asserted.
- **The naming convention becomes a real mechanism worth capturing** — it is how an abstract role
  catalog gets realized as concrete groups, and it is the only reliable route to the team's function
  class. Recorded in K21 §8.3 and §10; whether DryDocs parses it is a question for the
  group-membership work under `snow-hpsm-queue-to-group`, not for this gate.

**One residual from the sign-off remains open:** G5's unknown SEAL-risk ↔ ServiceNow-group mapping
(simplest thing that works — crosswalk `Risk Manager` and stop). Unchanged by this amendment.

## 2026-08-11 — NOTE on the G35 sign-off: the role catalog is 83 rows, and one open question on G16

**Gate:** `tom-roles-enumeration-and-cardinality` (G35) · **SIGNED OFF; this changes no ruling.** The
catalog §A ruled DryDocs would model was exported the same day. Recorded because G70 seeds its
vocabulary file from it, and two facts about it are worth having before that happens.

- **THE COUNT IS 83, not "100+"** — the sign-off carried the SME's initial estimate. Corrected in
  K21 §10.7. Nothing in §A turns on the number.
- **THE CATALOG CARRIES ITS OWN REGISTER MARKER.** A block of the Individual-scoped rows are
  described "… from SEAL" in the source's own description text. **That is the two-register mapping
  §A asked for, already written down** — G70 can READ which register a role belongs to and verify,
  rather than reconstruct it.
- **`type` is weakly populated.** It takes Accountable / Operational / Approval / Assignment / other
  / NULL, and the overwhelming majority are `other`. Present, but not a reliable classifier alone —
  §3.2's rule on a new column.
- **Most of the catalog is not ours**: third-party-website ownership, an RTM pair for external
  e-bonding, capacity planning, legal-entity approvals, a universal-request fulfilment ladder. G70
  should MARK out-of-scope rather than silently drop, so the file's coverage is legible.

**OPEN QUESTION — TWO DIFFERENT SREs, and it decides what G70 seeds.** The export shows
`Site Reliability Engineer (SRE)` at **Individual** scope AND `Incident Resolver – SRE / DevOps Team`
at **Group** scope. The G16 amendment argued OPTIONAL-and-DERIVED from the GROUP one (a team serving
20–60 applications). Register line G16 came from the SME's thirteen-class list, which reads as the
INDIVIDUAL one. **If so the RULING stands — G16 is OPTIONAL either way — but its REASONING described
the other row**, and an Individual-scoped SRE is a per-person holding like the other Individual
roles rather than something derived from a group name. Flagged, not ruled; no register line moves
and the gate is not reopened.

## 2026-08-11 — CLOSE-OUT of the G35 residuals: G16 stands, G5 closed, and one recorded revisit trigger

**Gate:** `tom-roles-enumeration-and-cardinality` (G35) · **SIGNED OFF; both remaining residuals now
closed.** No register line moves and no ruling changes. This entry exists so the residuals do not
outlive the gate as open questions nobody owns.

- **G16 STANDS AS RULED — OPTIONAL.** SME 2026-08-11: *SRE depends on how teams implement it; G16
  stands for us as far as I know, but if something changes it would require a revisit.*
  **The two catalog rows are not a contradiction to resolve — they are both live**, and which one an
  application uses is a per-team implementation choice. So the earlier framing was wrong to treat it
  as "which one did we mean": the answer is both, and the register does not have to choose.
  **CONSEQUENCE FOR G70, and it makes the build simpler rather than harder: seed BOTH rows** — the
  Individual-scoped Site Reliability Engineer and the Group-scoped SRE/DevOps incident-resolver team
  — each with its own `scope` from the catalog. A team that changes how it implements SRE then moves
  DATA, not VOCABULARY, which is the whole point of §F's "the vocabulary becomes data" direction.
  A register that had picked one would need re-ruling every time a team reorganised.
- **THE REVISIT TRIGGER, recorded rather than left as "we'll see"** — the repo grooms on stated
  triggers, and an unstated one is an omission with better wording. **Revisit G16 when the HOLDER
  SHAPE FLIPS for an application DryDocs supports** — an SRE accountability that was a named person
  becoming a shared team, or the reverse. Two known reasons that could cause it, both from the SME:
  SRE alignment differing across LOBs, and the in-flight consolidation of the support teams (see the
  rounds 2–3 entry). Neither is a defect; both are ordinary reorganisation, and the model should
  absorb them without a gate. If one ever forces a gate, that is itself the finding.
- **G5 CLOSED on evidence already in hand.** The residual asked whether a SEAL-risk ↔
  ServiceNow-group mapping exists. **It does not, and it cannot**: the catalog shows Technology Risk
  & Controls at **Individual** scope, so there is no group to map to. The ruling is unchanged and now
  unconditional — crosswalk `Risk Manager` to `technology_risk_controls` (§A2) and stop. No group
  resolution is designed for it, and none is missing.

**Three residuals remain from the sign-off and are NOT closed here**, each because it belongs
elsewhere rather than because it is unresolved: `tom-subject-class` (answered by the API evidence —
TOM rows exist at every level of the chain, so the subject is whichever CI the row sits on); the
region / coverage-window qualifier (a candidate for a future gate, not this one); and the replica's
unconfirmed completeness (K21 Q9 — it touches counts, and every ruling here is about shape).

## 2026-08-11 — RECORD: J13 publish-ceiling value classes 2, 3, 4 (no gate; SME ruled in-session)

Not a gate sign-off. J13's acceptance carries a USER-GATED START — the user rules which
flagged identifiers are real before any sweep — and three of its four value classes were
still unruled. Recorded here so the rulings live somewhere durable rather than only in a
backlog note. Class (1) (platform tokens) was ruled and recorded 2026-08-11 in
`internal/standards/technology/folder-naming-convention.md`.

- **CLASS 2 — data-center codes: RULED, SWEPT.** SME: *"change data center P to a T. and
  job naming also."* Position 1 of a Control-M data-center name is the environment letter;
  the publishable tree now carries a NON-PRODUCTION letter so no published example names a
  live production object, while the grammar the page teaches (position 1 = environment,
  `E####` = default time) is untouched. Swept across 19 tracked files outside `internal/`:
  the four DCs, the application code, and the one real job name the J15 realness table had
  PARKED for exactly this ruling (`internal/standards/technology/folder-naming-convention.md`,
  "string-vocab ruling parked with the platform-vocabulary residual" — that park is now
  discharged). Real values moved to the new internal twin
  `internal/standards/technology/data-center-inventory.md`.
  - **A FIFTH DATA CENTER WAS FOUND BY THE NEW GUARD, NOT BY THE SWEEP.** J13 named four
    and the standards page inventories four; a `P045` DC sat in a test fixture and the web
    demo data. The token-list sweep could not have caught it — only the shape scan did.
    This is the J15 lesson arriving a third time: **enumerate the SHAPE, never the values.**
  - **VOLUMETRICS ARE A DISTINCT CLASS AND ARE *NOT* RULED.** `controlm_staging_ddl.sql`
    carried real per-data-center folder/job counts. The identifier swap alone would have
    left production counts sitting under test-environment labels — inaccurate as well as
    still disclosed — so the per-DC split was pulled to the internal twin and the totals
    kept, because the sizing rationale rests on the totals and not on the split. Flagged
    for the SME; reverse it if volumetrics are ruled publishable.
- **CLASS 3 — schema/table/column identifiers: NO SWEEP OWED; already covered by a SIGNED
  ruling.** J13 lists `psgmgr` / `cm_escalation_db` / `EJOBNAME` / `ECOMPONENT` as open. They
  are not. The N9 `source-registry-v2` gate (SIGNED 2026-07-31, §Q1 id grammar) publishes
  `{origin}@{db}.{schema}.{table}` with the DATABASE redacted to `[db]` and the schema kept
  when it is established public vocabulary — and it names `psgmgr` as exactly that. **The
  trap in J13's own framing:** `cm_escalation_db` reads as a database name because of the
  `_db` suffix, but it is a TABLE inside `psgmgr` (`seal@[db].psgmgr.cm_escalation_db`), so
  the signed grammar already covers it; `EJOBNAME` / `ECOMPONENT` are columns in that table.
  The connection coordinate — the database — is redacted already. Class 3 is CLOSED as
  ruled-elsewhere, not as newly decided.
- **CLASS 4 — sample product/LOB names: RULED PUBLISHABLE (assistant's call under the SME's
  "no preference").** `config/taxonomy/lob-product-team.yaml` pairs synthetic ids with real
  LOB names and generic industry product names. LOB names are public company structure and
  the product/team names are generic terms; the ids — the identity-bearing half — are already
  in the reserved block and are pinned by the guard. The guard asserts IDS stay synthetic and
  deliberately does not police NAMES. Recorded as a judgement call, not an SME ruling: flip it
  if the SME disagrees, and the change would be a fixture rename with no id impact.

**Guard grown so none of this can drift back:** `tests/unit/test_publish_boundary_values.py`
gains Scan E — no publishable file may carry a data-center name whose position 1 is the
production environment letter. Shape-guarded like every scan there, so the test embeds no
real value and cannot leak the inventory it protects.

## 2026-08-12 — GATE: vocabulary-domains-and-id-policy — SIGNED OFF, 19/19

Ratifies the vocabulary's domain axis, the id convention, and the never-ruled planned tier.
Prompt: `config/gate-prompts/vocabulary-domains-and-id-policy.yaml`; session run in-session
(SME = user), rulings pre-taken 2026-08-12 for §A/§B and confirmed here.

- **A1 CONFIRMED** — domain `controlm` → `scheduler` on all 27 entries; fragment renamed
  `40-local-scheduler.yaml`. The partition is the scheduler tier, tool-agnostic (AutoSys/
  Airflow file here via the BMC-baseline crosswalk). Node labels keep vendor prefixes —
  ADR 0003/0008 unchanged; the retired `:Scheduler`/`:SchedulerKind` node concept stays retired.
- **A2 CONFIRMED** — domain `seal` → `business_application` on all 10 entries; fragment
  renamed `41-local-business-application.yaml`. Matches the canonical `:BusinessApplication`
  label (K4) and the standalone-template goal.
- **A3 CONFIRMED** — `human` registered in the domain enum for people/org edges (the G74
  `:Employee` spine files there). No existing entries move; relocation rides the §B3 tech-debt
  cleanup.
- **A4 CONFIRMED** — the stale header enum (omitted registry/docs/quality) corrected to
  `scheduler | business_application | catalog | architecture | registry | docs | quality |
  context | all | human`; the JSON schema gains a matching enum.
- **B1 CONFIRMED** — NEW entries use a domain-derived id prefix (`scheduler_*`,
  `business_application_*`, `human_*`, plus the existing catalog_/arch_/reg_/docs_/doc_
  conventions). Documented in the header and RELATIONSHIP_GUIDE Step 6.
- **B2 CONFIRMED** — status is NEVER encoded in an id (a `planned_` prefix would force a
  rename at every lifecycle flip; ids are the append-only audit join).
- **B3 CONFIRMED** — existing epoch-tag ids (m3_ 21, p2_ 5, m7_ 1, u1_/u2_ 5, g22_ 1,
  c23_ 4, prov_ 1, sosa_ 4) stay valid now; FORCED migration (add-new + deprecate-old across
  the four ledgers) is a groomed tech-debt item, not natural attrition. SME ruling 2026-08-12.
- **C1a KEEP-PLANNED** — the p2_ deployment tier (p2_deployed_by, p2_deployed_to,
  p2_deploys_folder, p2_authored_by, p2_instance_of): the model is coherent and K22 feeds it.
- **C1b HELD FOR REVIEW** — m3_depends_on_file, m3_executed_by: SME directed a file-based
  review instead of an in-session ruling → `docs/reviews/vocabulary-planned-review.md`.
  Entries stay planned until that review is ruled and transcribed back here.
- **C1c DEFERRED** — seal_app_attributed_to_employee defers to the open
  `seal-tom-attribution-reshape` gate, which owns that territory. Stays planned.
- **C1d HELD FOR REVIEW** — catalog_has_area_product, catalog_area_product_has_dev_team,
  catalog_dev_team_has_membership: same review file as C1b.
- **C1e KEEP-PLANNED** — the architecture-mermaid trio (arch_owns_code, arch_stored_in,
  arch_contains_service): SME kept all three (overriding the drafted deprecate
  recommendation) — architecture-doc ingestion is still intended; the U1/U2 code graph
  covers structure, not ownership/storage/services.
- **C2 RECORDED** — the 16 gate-held / gate-ruled planned entries are not re-ruled here:
  m3_delegates_to (rua-load-shapes §A1 hold → K17), arch_owns_directory + arch_sources
  (rua-load-shapes §C1/§C2, registered at G55), m3_triggers (confirmed 2026-07-15, build
  pending), m3_host_group_defined_on (confirmed 2026-07-09, loader blocked on DC-key parse),
  sosa_* ×4 (E1 deferred), c23_* ×3 (C23 defer — no writer until a measurement feed),
  catalog_has_application (K7 §G6), reg_appuser_uses_software (software-version-context;
  build = C33), docs_has_document + docs_governed_by (held for the docmeta P4+ loader).
- **C3 RECORDED (tech-debt)** — m3_triggers is planned yet live-consumed by a QuerySpec
  (`drydocs_api/query_specs.py`, `MATCH …-[:TRIGGERS]->`): the spec returns empty rather
  than wrong, but the surface implies data that cannot exist yet. Tech-debt item groomed:
  demote the spec to demo-only or prioritize the build.
- **D1 CONFIRMED** — the follow-up commit applies §A (git mv both fragments, 37 domain
  edits, header enum + §B note), regenerates schema_graph.cypher, updates changed test pins.
  No §C deprecations were ruled this session, so no status flips land.
- **D2 CONFIRMED** — hygiene rides the build: JSON-schema domain enum + `removed` status +
  required `inverse_label`; RELATIONSHIP_GUIDE Step 6 gains `inverse_label` + the new domain
  list; `agents/graph_qa/schema_context.py` repointed from the retired monolith to the
  fragment reader.
- **D3 CONFIRMED** — tech-debt items groomed: forced id migration (§B3), human-domain
  relocation (§A3), the m3_triggers QuerySpec conflict (§C3), plus the review-file
  follow-up (§C1b/§C1d).
- **D4 CONFIRMED** — this transcription; gates.json and the enforcement matrix regenerate
  (default-paths render_board.py run).
- **E SIGNED** — safe to transcribe.

## 2026-08-12 — GATE: remediation-fix-tracking — SIGNED OFF, 10/10

Rules the fix-tracking vocabulary the write-authorized loader applies from
`drydocs.remediation.fix-tracking.v1` change-sets. Prompt:
`config/gate-prompts/remediation-fix-tracking.yaml`; the SoD half (emit change-set,
loader applies) was ruled 2026-08-12 at the xml_io epic and is unchanged here.

- **A1 RECORDED** — fix tracking is OUR intervention record, a fourth axis beside envelope
  authorship, pull tracking, and load provenance. The envelope names
  (source_created_by/at, source_updated_by/at) are never reused — fence already ratified
  at controlm-q1q3-phase1 / envelope-property-terms.
- **A2 RECORDED** — the emitting component stays no-graph-write: NFR-REM-1, the AST guard,
  and the corroborate write-clause regex all UNCHANGED.
- **B1 RULED as proposed** — `remediation_fix_id` (string, fix package / Jira reference),
  `remediation_status`, `remediation_status_date`; the `remediation_` prefix keeps the axis
  visually separate from `source_*` and `*_seen_at`.
- **B2 RULED as proposed** — enum `proposed | in_progress | applied | verified`.
  `applied` = the dev team imported the updated XML; `verified` = the equivalence proof
  re-ran against the re-exported live definition. No `rejected` state on the node: a
  rejected fix removes the properties (the package records the rejection).
- **B3 RULED** — one `remediation_status_date` carrying the LAST transition; the full
  history lives in the fix package.
- **C1 RULED** — a dedicated drydocs-load loader consuming fix-tracking.v1 change-sets:
  UNWIND $batch, MATCH on the NODE KEY (never MERGE-creating a target — a missing target
  is an error, not a node to invent), SET the three properties, remove them on rejection.
  Standard JobRun provenance applies. C2 (pass in an existing loader) declined.
- **D1 RULED** — `dd:` local property_terms entries with prose definitions; standard-term
  bindings revisited when an RDF export exists. `dct:` authorship terms are NOT candidates
  (the envelope's family).
- **E1 CONFIRMED** — the loader build is groomed as a backlog follow-up (not built at
  sign-off); the fix-tracking.v1 artifact's GATE-BOUND banner flips to cite this gate;
  property_terms gains the §D entries with the build.
- **E2 CONFIRMED** — this transcription; gates.json and the enforcement matrix regenerate.
- **F SIGNED** — safe to transcribe.

## 2026-08-13 — RECORD: rua bundle data profile, §A opened — one bundle identified, the rest is company-side (G62; gate `rua-bundle-data-profile`, still UNSIGNED)

- **Why a RECORD and not a sign-off.** The SME convened the G62 session 2026-08-13
  (the USER-GATED START; backlog claim `c480d570`) and walked part of §A before the
  session reached the venue boundary: the remaining identify work and all of §B run
  COMPANY-SIDE, where the bundles are. The gate is not signed; the G23 terminus
  holds — no population beyond the walked samples loads.
- **A1 — PARTIAL: 1 bundle named, by count and date.** The SME produced a partial
  inventory identifying one bundle: **172 scripts / 1,528 directories, collected
  2026-07-27T20:40Z**, single host, two scan roots, depth 4, ownership_sweep=no.
  Real host/user/path values are recorded machine-local on the SME's desktop
  (`internal-local/`, the company-side session note is the durable home), never
  here. Outstanding: the rest of the population — at minimum the second walked
  bundle, plus any bundles collected since.
- **A1 finding — the named bundle IS G22 bundle #1.** Its script count (172) and
  collection date (the evening before the 2026-07-28 company dry run) match the
  walked-shapes baseline of 561 rows across two bundles (172 + 389). The SME's
  A3 blocker — "I don't know what was captured then to compare against" — is
  resolved by that record: the comparison basis is the 172 + 389 pair, and the
  389-script twin's identity lives company-side.
- **A2 — DEFERRED (SME).** Per-bundle collector provenance waits on the
  company-side meta.txt sweep. Evidence in hand for bundle 1: `schema=
  rua-inventory/v1`, collected by the run-as account — a v1 capture.
- **PROFILE EVIDENCE, ahead of §B (recorded, not ruled): bundle 1 is hash-absent
  AND body-absent.** Its listing is `scripts.csv` (`path|script|permission|date|size`
  — no sha256, no owner/group) and the archive carries **no `scripts/` body
  mirror**. Under the signed G22 rules that means: metadata-only staging (the
  listing-is-a-fact rule), exclusion from G2 drift corroboration (hash-bearing
  only), and nothing for the G21 code-ops parse or the G24 repo corroboration to
  read. If the whole population is v1, the first real load is metadata-only end to
  end. The v2 collector (`drydocs_lineage/collect/rua_inventory.sh`,
  `COLLECTOR_VERSION=rua-inventory/v2`) emits `scripts.tsv` with sha256 and copies
  bodies (≤ 1 MiB cap) — re-collection would make the population hash-bearing.
- **A3 — DEFERRED (SME), with the comparison resolved.** Whether the two walked
  bundles are in / out / re-collected is held until the full A1 population is
  named company-side. The agent's recorded observation (not a ruling): the v1
  evidence above argues re-collect.
- **NEXT: company-side.** Complete A1 (name every bundle, by host, company-side),
  run the A2 meta.txt sweep, then §B — the G20 extractor over the full population
  in staging, zero graph writes — and bring the §B counters back to the page for
  the §C rulings. G62 stays `in_progress` under the awaiting-HITL convention.


## 2026-08-17 — RECORD: the corporate backbone, three partial rulings (G98; gate `corporate-backbone-vocabulary`, still UNSIGNED)

- **Why a RECORD and not a sign-off.** The G98 session opened 2026-08-17 (laptop) and
  ruled three clauses of eighteen before pausing. The gate is not signed and nothing is
  registered: `:Company`, `HAS_BUSINESS_SEGMENT` and `HAS_BUSINESS_SEGMENT_HISTORICAL`
  remain absent from the relationship vocabulary. Same convention as G22/G35 — a
  confirmed clause inside an unsigned gate has no home in a log organised by sign-off,
  so it is written here in the same commit as the page edit or it exists only in a YAML
  file nobody re-reads.
- **C1 — the `:Company` label is RIGHT and STAYS (SME).** A company is a real
  ontological class; the fact that this deployment holds ONE instance is a property of
  the deployment, not of the model, and another deployment seeds its own. The two
  readings offered against it were declined: (b) drop the label and hang segments off an
  existing org class, and (c) keep the class but move the instance out. This unblocks
  clause A — the label is registrable — and moots nothing else.
- **C2 — "JPMC" stays SEED DATA in `ontology.cypher` (SME).** Not config-resolved. The
  cost is stated rather than hidden: `ontology.cypher` is canonical-producer and ports
  wholesale, so a consuming deployment inherits this company's name in its schema
  bootstrap until it edits the file, and that sits against ADR 0012's
  standalone-generalization goal. Ruled the simpler way deliberately — **clause C3 is
  therefore MOOT**: there is no seed change, so nothing to ledger as a bootstrap
  behaviour change.
- **A5 — the short name STAYS the uniqueness key (SME).** `name:'JPMC'` remains the key
  and `constraints.cypher:29` is untouched, so nothing migrates and the four
  `.claude/skills/data-context-extractor/` files' `{name:'JPMC'}` queries keep working.
  The two alternatives were declined: adding `short_name`/`common_name`/`legal_name`
  alongside the existing key, and re-keying onto a neutral identifier.
- **What A5 leaves open, recorded because the session raised it and then ruled the
  minimal way.** The clause exists because the SME supplied the fact at the walk:
  **"JPMC is the short name of the company JP Morgan Chase."** So the identity property
  holds an ABBREVIATION, `legal_name` holds "JPMorgan Chase & Co.", and the common name
  the abbreviation stands for is **in this record and nowhere in the graph** — A5(ii),
  whether a property carries it, was not taken up. That is a deliberate minimal ruling,
  not an oversight, but it means the SKOS prefLabel/altLabel distinction W3C ORG
  inherits is unmodelled here. A6 stands as written: an abbreviation is the least stable
  of the three strings and the one that changes on a rebrand, so if this is revisited it
  will be revisited as a re-key.
- **Still open (15 clauses):** A1 (which org class — `org:FormalOrganization` per the
  registered `:BusinessSegment` sibling, or `org:Organization`), A2, A3, A6, all of B
  (one edge type discriminated by `effective_to`, or the two types the M0 seed wrote by
  accident; plus which per-domain fragment houses them), C4, all of D (the endpoint
  cross-check guard, explicitly SEPARABLE and not sequenced behind this page), and E
  (the External-PUBLIC recording). G98 stays `in_progress` under the awaiting-HITL
  convention.


## 2026-08-17 — GATE: corporate-backbone-vocabulary (backlog G98) — SIGNED OFF 19/19

- **Supersedes the partial RECORD above** (same date). That entry captured C1/C2/A5
  mid-walk under the unsigned-gate convention; the walk then completed and the SME
  signed at 19/19. Both are kept: the RECORD is the audit trail of what was ruled
  before the signature, which is the point of writing it in the first place.
- **§C1 — the `:Company` label is RIGHT and STAYS.** One instance is a property of
  THIS deployment, not of the model. Declined: dropping the label, and keeping the
  class while moving the instance out.
- **§C2 — "JPMC" stays SEED DATA in `ontology.cypher`**, not config-resolved. The
  cost is accepted on the record: a consuming deployment inherits this company's
  name in its schema bootstrap until it edits the file, which sits against ADR
  0012's standalone-generalization goal. **§C3 is MOOT** — no seed change, so
  nothing to ledger as a bootstrap behaviour change.
- **§A1 — `:Company` registers as `org:FormalOrganization`, prov_type Agent.** Same
  class and same reasoning as its own child `:BusinessSegment`: the more precise
  term for a legally-recognized organization. `org:Organization` declined. APPLIED
  to `10-node-classifications.yaml`.
- **§A5 — `name` stays the uniqueness key**, `constraints.cypher:29` untouched,
  nothing migrates. **The key is an ABBREVIATION and that is now on the record:**
  the SME supplied the fact at the walk — "JPMC is the short name of the company JP
  Morgan Chase" — so `name` holds the short form, `legal_name` holds "JPMorgan
  Chase & Co.", and **the common name is in this log and NOT in the graph**. A5(ii)
  (add `short_name`/`common_name`/`legal_name` as distinct properties) and the
  re-key onto a neutral identifier were both offered and declined. §A6 stands: an
  abbreviation is the least stable of the three strings, so a revisit is a re-key.
- **§B1 — TWO edge types, as the M0 seed writes them.** `HAS_BUSINESS_SEGMENT`
  (open-ended) and `HAS_BUSINESS_SEGMENT_HISTORICAL` (closed-dated) stay distinct;
  the one-type, date-discriminated alternative was declined on legibility and on
  the existing skill-file queries.
- **§B2 — the cost of §B1, and the SME ruled a GRAPH-TEST for it.** Currency is now
  encoded twice (type name AND `effective_to`) and the two can disagree; Neo4j
  cannot express "this type implies this property is null", so it is a test, not a
  constraint — the TOM-roles-singleton precedent. APPLIED to `drydocs m3-verify`.
  **The first draft of that check was WRONG and live-running it caught it:** chained
  MATCHes returned NO ROWS on a clean graph, so the `if rows:` guard skipped the
  check and reported a silent pass. Rewritten with `COUNT {}` subqueries and
  verified on the laptop / `neo4jtest` / `drydocs` DB — 0 and 0, with a row.
- **§B3 — a NEW `corporate` domain and fragment**, `49-local-corporate.yaml`, with
  `corporate_*` ids per the id policy ratified at vocabulary-domains-and-id-policy
  §B1. Folding into `42-local-catalog.yaml` was declined: the segment appears there
  as `RECONCILES_TO`'s to_node, but corporate structure is not the catalog domain
  and a `catalog_*` prefix would misdescribe it. Both edges land **status: planned**
  — no loader, nothing activates.
- **§D3 — the endpoint guard reads BOTH directions**, and this is the clause with
  the widest reach. Registry-side: every declared edge's endpoints must be
  registered labels. Seed-side: every relationship type MERGEd in a schema
  `.cypher` must have a vocabulary entry — the direction that would actually have
  caught this gap, since the registry-side check sees nothing while an edge is
  absent entirely. APPLIED as `tests/unit/test_vocabulary_endpoints.py`.
- **WHAT THE GUARD FOUND ON ITS FIRST RUN, recorded because it is the real yield.**
  Three false-positive classes in the guard itself, each fixed and pinned: endpoint
  ALTERNATION (`"Script | ETLProcess"`, the rua-load-shapes §B2 two-endpoint-classes
  convention) read as one opaque label; Cypher COMMENTS read as code; and string
  LITERALS read as code (`n.notes = "Was DevTeam-[:DEVELOPS]-> pre-K4."`). Then the
  genuine findings: **eight endpoint labels** named by declared edges and never
  registered (QualityMeasurement, Dataset, Metric, Dimension, OntologyTerm,
  SchedulerKind, SwoClass, MediaType) and **one seeded edge** with no entry
  (`CAN_ACT_AS`, `sosa_experimental_supplement.cypher:86,91`). All are the same
  defect class as `:Company`. **None is ruled here** — each needs its own gate, and
  `CAN_ACT_AS` belongs to E1 (SOSA, in_progress). They are carried as DECLARED DEBT
  lists that the guard fails against on anything new, so the debt can only shrink.
- **§E1/§E2 — publish boundary RECORDED, not reopened.** The source is
  External-PUBLIC (`doc-source-registry.yaml#jpmc-reports`: classification External,
  public SEC filings / IR PDFs, `source_url`, trust VERBATIM), so the JPMC literals
  in `ontology.cypher` are publishable and this gate page carries real spellings
  rather than placeholders. The ingestion half — that entry's `confirmed: false`,
  the `:DataAsset`-vs-lexical-`Document`/`Chunk` reshaping — is **Idea-130 / P4
  territory and NOT ruled here**: the ingest script was removed 2026-07-22 and the
  PDFs were never committed, so it needs a re-fetch and a new loader before it can
  run at all.
- **Terminus.** Both edges are `status: planned` and no loader writes them; the M0
  seed is unchanged. Nothing about this sign-off puts data in the graph that was not
  already there — it declares what was already being written.


## 2026-08-18 — RECORD: the held planned-entry review, four of five ruled (G91; gate `vocabulary-domains-and-id-policy` §C1b/§C1d follow-up)

- **Why a RECORD.** §C1b/§C1d held five entries out for a file-based review
  (`docs/reviews/vocabulary-planned-review.md`). Four are ruled here; entry 5
  (`catalog_dev_team_has_membership`) stays open, so G91 stays `in_progress` and this
  is a follow-up entry rather than a sign-off.
- **A CAUTION ABOUT THE REVIEW FILE ITSELF, recorded because it shaped the walk.** Its
  "Evidence for keeping / Against" lines are PRODUCER-DRAFTED prompts, not SME positions,
  and the file landed in one commit (`26d7c395`) with the gate sign-off. Two were checked
  against the code and did not survive: entry 3's "if AreaProduct is no longer wanted, all
  three retire together" (never stated by anyone, and already false — three ACTIVE entries
  touched `:AreaProduct`), and entry 4's "stands or falls with entry 3" (3 was written, 4
  had no writer). Read those lines as questions, never as findings.
- **§C1b entry 1 — `m3_depends_on_file`: KEEP-PLANNED.** The FileWatcher model is built
  producer-side *except* this edge: `:File` carries a hand-written index
  (`constraints.cypher:140`), the job type parses (`JobType.FILE_WATCHER`), the watched-path
  role resolves (`paths.py`, `FILEWATCH|WATCH|FW_` → `WATCH_INPUT`); only the metadata
  LOADER is company-only. And the AutoSys crosswalk already depends on the ruling — its
  `d(file)` row is flagged approximate, "may need a FileWatcher-job mapping instead"
  (`autosys-crosswalk.yaml:102`), with §115 making resolve-or-defer a gate condition.
- **§C1b entry 2 — `m3_executed_by`: KEEP-PLANNED, HOLD ON K17.** Matches `m3_delegates_to`
  at rua-load-shapes §A1 — *"not declined — blocked on identity"* — on the same to-node and
  the same blocker: `:AppUser` is keyed on `fid` per fid-identity-and-scope §A1/§A2 while
  `run_as` carries the linux TENANT NAME, and no `:AppUser` constraint is deployed. Second
  blocker: the run layer is absent (`:ControlMJobRun` has no loader; `p2_instance_of` is
  planned).
- **NEW ENTRY RAISED — `scheduler_runs_as` (ControlMJob → AppUser), planned.** Answering the
  grain question exposed that the DEFINITION-level run-as (`CM_DEF_VJOB.OWNER`) had **no
  registered edge at all** — every `:AppUser` entry was run-grain, host-side, or unrelated.
  It is loadable from psgmgr today and needs no runtime ingestion, unlike its run-grain
  sibling. Lands planned with the SAME K17 fence: OWNER is the tenant name, not the
  directory key. `prov_maps_to: ~` deliberately — a plan's configured agent is a qualified
  association, not a direct PROV property (the m3_belongs_to_application precedent for
  declining a weak term).
- **THE `m3_` EPOCH-TAG IDS ARE RETIRED FOR THESE TWO (SME direction, same session).**
  `m3_depends_on_file` → `scheduler_depends_on_file`; `m3_executed_by` →
  `scheduler_executed_by`. Add-new + deprecate-old per vocabulary-domains-and-id-policy
  §B1/§B3 — **never renamed in place**, because the id is the join key across the
  taxonomy-ontology-map, the generated `schema_graph.cypher`, the SQLite mirror and this
  append-only log. Done under G91 rather than G87 because a planned, loaderless, dataless
  entry migrates for free; **G87 stays open** for the remaining epoch-tag ids.
  **READ THE DEPRECATIONS CORRECTLY:** both old rows are `deprecated` as an ID MIGRATION,
  not as a rejection — the concepts were kept and held respectively, and each
  `deprecation_note` says so.
- **§C1d entry 3 — `catalog_has_area_product`: ACTIVATED.** It already met this file's own
  bar (`active = supplement + loader both exist`): the supplement declares `#hasAreaProduct`
  and `area_products.cypher` MERGEs it with the C22 orphan sweep. It was carried as `planned`
  on a DATA gap — a different axis, and one K5 §B had already dispositioned ("loader entries
  stay planned; independent lifecycles"). That gap is now closed: the lob-product-team SAMPLE
  has `area_products: 0`, the production PAT extract carries the layer (SME, 2026-08-17).
  Counts are Internal and stay in the internal twin. Shape backed by C2+C3 (SUPPORTS range =
  AreaProduct, Product reached via Product ▸ AreaProduct ▸ DevTeam) and K5 §B (AreaProduct is
  an attribution scope).
- **§C1d entry 4 — `catalog_area_product_has_dev_team`: DEPRECATED as REDUNDANT.**
  DevTeam↔AreaProduct is already carried by the ACTIVE `catalog_supports_area_product`
  (`DevTeam -[:SUPPORTS]-> AreaProduct`, active since C4 2026-06-21). This entry declared the
  same pair in the opposite direction under a second label. **Never built** — nothing is
  deleted; the entry and its note stay as the audit trail (the never-built deprecate case,
  rua-load-shapes §J). Its named loader never wrote it, and `area_products.cypher`'s header
  claimed it did until corrected in the same commit. **NOT a rejection of `:AreaProduct`** —
  its sibling activated in the same ruling.
- **Still open — entry 5, `catalog_dev_team_has_membership`.** Not ruled. Two facts for
  whoever takes it: `pat_team_roles.cypher` ALREADY writes the full n-ary triple
  (`HAS_MEMBERSHIP`, `OF_ROLE`, `HELD_BY`) while only `HAS_MEMBERSHIP` is registered — the
  other two legs exist solely as the DEPRECATED SEAL entries. And K4's own deprecation note
  (2026-07-15) explicitly carved this one out: *"org: stays for the PAT product hierarchy
  only (e.g. catalog_dev_team_has_membership — SAME labels, different vocab id, NOT
  deprecated)"*. So the review's "strongest re-shape candidate" framing runs against a
  ruling that already spared it. G91's acceptance stands: a re-shape routes through
  RELATIONSHIP_GUIDE as a NEW proposal, not an edit of the held entry.


## 2026-08-18 — GATE: the held planned-entry review — CLOSED 5/5 (G91; `vocabulary-domains-and-id-policy` §C1b/§C1d follow-up)

- **Completes the RECORD above** (same date, four entries). Entry 5 is now ruled, so the
  §C1b/§C1d hold is discharged and G91 closes.
- **§C1d entry 5 — `catalog_dev_team_has_membership`: RE-SHAPE onto qualified attribution.**
  The DevTeam leg was the LAST HOLDOUT on the reified W3C ORG Membership pattern: SEAL moved
  at K4 (2026-07-10 §B/§C), the PAT product / area-product side at K5 (2026-07-20). One
  employee was therefore reaching the graph by two different routes — `HAS_AGENT` off an
  `:Attribution` for two families, `HELD_BY` off a `:Membership` for this one. Replaced by
  `catalog_dev_team_qualified_attribution` (DevTeam → Attribution) and
  `catalog_dev_team_attribution_had_role` (Attribution → Role), both **planned**.
- **THE `HAS_AGENT` HOP IS REUSED, NOT TWINNED — and that is the rule, not a shortcut.**
  `Attribution -[HAS_AGENT]-> Employee` is IDENTICAL to `seal_attribution_has_agent`, and the
  C8 meta-graph refuses ambiguous duplicate (from, label, to) triples (enforced at
  `schema_graph.py:248`). The K5 header block states the rule: siblings register only *where
  the triples differ*; an identical triple REUSES the existing entry as shared
  qualified-attribution infrastructure, rescoped family-agnostic. So OF_ROLE / HELD_BY being
  separately unregistered was **correct by design** — the walk's first reading of it as a
  "registration gap" was wrong and is corrected here.
- **THE ACTUAL DEFECT, and why the entry could not simply activate.**
  `pat_team_roles.cypher` writes all three legs, and the two it would reuse — `seal_of_role`,
  `seal_held_by` — are DEPRECATED, i.e. "no longer loaded". A loader minting retired edge
  types on every run is the contradiction. **The estate is TRUNCATE-AND-RELOAD** (SME,
  2026-08-18; the same C13 precedent `constraints.cypher` already cites — "graphs rebuild
  from bootstrap, they are never migrated"), so there is no legacy-data reading under which
  that is benign: anything that should not be loaded does not stay.
- **TWO CARVE-OUTS SUPERSEDED, named so this does not read as an oversight.** K4's own
  deprecation note spared this entry verbatim — *"org: stays for the PAT product hierarchy
  only (e.g. catalog_dev_team_has_membership — SAME labels, different vocab id, NOT
  deprecated)"* — and C20 (2026-07-28, `constraints.cypher`) scoped the K4 retirement to the
  SEAL attribution loaders, keeping `:Role` / `:Membership` load-bearing for the catalog
  paths. Both are now overtaken. `constraints.cypher` carries a dated amendment saying so.
- **WHY `:Role` RATHER THAN A THIRD ROLE SCHEME.** PAT team roles are ENGINEERING roles, a
  different register from `TOMRole` (SEAL) and `ProductRole` (Product Cabinet). `:Role`
  already has seeded canonical rows and live keys, and `Attribution -[HAD_ROLE]-> Role` is a
  new triple against both existing HAD_ROLE entries, so it registers cleanly. This also gives
  `:Role` a live purpose again — the thing C20's retention had been holding open for the
  shape this ruling retires.
- **CONSEQUENCES APPLIED IN THE RULING COMMIT.** `pat_team_roles.cypher` carries a
  DO-NOT-RUN banner (it is inert by intent until rewritten); `constraints.cypher`'s C20 note
  is amended; the `membership_id` key is deliberately LEFT IN PLACE — the loader rewrite
  decides whether `:Membership` survives, and dropping a constraint ahead of its loader is
  the S3 ordering trap run backwards.
- **NOT RULED HERE — the two join paths, recorded because the SME named them.** The
  traditional path DevTeam → SEAL is already established and untouched by this ruling
  (`arch_develops`, ACTIVE: `BusinessApplication -[WAS_ATTRIBUTED_TO {role: developed_by}]->
  DevTeam`, joined by SEAL id per C2+C3/C4). The SECOND path is a support-team case that
  reaches applications through PEOPLE — team members, by SID, holding an operate-manager
  role on the applications — rather than through a develops edge. It rides the same
  `:Employee` spine this re-shape unifies (`:Employee {employee_id}` IS the SID,
  `constraints.cypher:79`), which is what makes the re-shape load-bearing rather than
  cosmetic. Modelling that path, and the ServiceNow technician-group family beside it, is
  NOT in this gate — see the follow-up items.


## 2026-08-18 — RECORD: the :Employee creation policy — STUB-AND-ENRICH (SME direction in-chat; G74 clause 2 owns the formal transcription)

- **What this records.** SME direction, given while ruling the company's
  `snow-tom-responsibility` §C (unresolved agent): *"the HR database has ~300k
  [people]; my expectation is that it will be the stub and supplemented with HR data
  later."* On the G51/X1 RECORD idiom — direction, not a gate session — written here
  because a direction that lives only in a chat stops existing when the chat does
  (the 2026-08-06 Operate-Manager lesson, arriving again on schedule).
- **What it settles.** G74's second clause named the contradiction: the runbook's
  spine-and-enrich rule ("a SID not in the roster gets no edge, NEVER a stub") vs
  `seal_applications.cypher`, which MERGEs `:Employee` placeholders. Both were
  defensible; the direction sides with the LOADER: **a people-referencing load MERGEs
  a stub `:Employee {employee_id: <SID>}` and the HR supplement enriches it later.**
  The rationale is scale-and-sequencing, not preference — the roster is ~300k rows
  and its load is deferred, so no-stub would leave every people edge waiting on a
  load that has not been scheduled, or silently dropped.
- **What it does NOT settle, so G74 stays open.** The runbook text still says the
  opposite and must be harmonized (both v2 and published v3); the stub property
  idiom (what marks a node as awaiting enrichment beyond `source`) is unruled; and
  clause 1 — the REPORTS_TO hierarchy edge and its source — is untouched. G74 owns
  all of it.
- **Applied in the same commit:** `pat_team_roles.cypher`'s strict `MATCH (e:Employee)`
  flips to the MERGE-stub idiom. It was written yesterday (G99) citing the runbook's
  no-stub reading; under this direction that strict match is the silent-drop defect
  the company's §C clause exists to avoid — a PAT staffing row for a person the HR
  gap misses would vanish without a trace. Now it stubs and counts, matching
  `seal_applications.cypher`. The GROUP side of the company's §C (an unloaded
  `:ServiceNowGroup`) is load-ORDER, not roster coverage, and is not covered by this
  direction.


## 2026-08-18 — GATE: pending-source-correction — SIGNED OFF 12/12 (N13)

- **One ruling for both flips**, because they are one lifecycle: acquisition
  `manual → automated` (N12's field; Idea-132's ServiceNow re-sourcing is the live
  case) and O24's override → source-corrected (the flip K7 §E2 explicitly deferred —
  "it belongs to the domains where permanence is temporary" — which nothing owned
  until N13).
- **§A1 — ONE VOCABULARY.** A single `pending_source_correction` concept spans both
  surfaces: on a manual acquisition row it reads "hand-fed until the pull exists";
  on an override row, "modelled correctly here until the source is fixed". One
  report, one lifecycle, one query for "what are we carrying?". Two domain-local
  flags were offered and declined.
- **§A2/§A3 confirmed** — the O24 origin discipline is not renegotiated (the
  placeholder state is ALWAYS VISIBLE; a flip is a dated EVENT, never an overwrite),
  and the vocabulary lives in CONFIG AND STORES only. Nothing enters the graph at
  this gate; graph-side pending-ness would be a new RELATIONSHIP_GUIDE proposal.
- **§B1 confirmed** — acquisition flips BY THE COMMIT THAT LANDS THE BUILD (the
  pull's SQL/adapter + the mode change in one change; flips-are-follow-ups). Intent
  never flips anything.
- **§B2 — TWO HANDS.** A load observing override == source value surfaces a
  retirement CANDIDATE; a STEWARD confirms, and the row archives dated with the
  agreement evidence. Auto-retire was offered and declined: coincidental agreement
  must not silently retire a correction that was masking a different defect.
- **§B3/§B4 confirmed** — no flip is automatic-and-silent (an unattended job may
  PROPOSE, never perform), and the flipped state keeps its history (archived
  override rows; manual-era provenance in registry notes).
- **§C1/§C2/§C3 — ONE UNION REPORT, NO DEADLINE, NEVER A GATE.** One report class
  lists every live placeholder across both domains, ordered by AGE, read at the
  SME's cadence — no alerting, no SLA, no review_by dates (per-row clocks were
  offered and declined: they manufacture urgency the exploratory-phase framing says
  is false — `mode: manual` is the EXPECTED first state, N12 §f). The report never
  gates loads, blocks CI, or fails tests: a placeholder is recorded state, not an
  error.
- **§D1/§D2 — the K7 §E2 exemption CONFIRMED, plus the boundary rule.** The
  app-code mapping domain stays exempt (overrides MAY be permanent — the mapping IS
  the authored truth), as a PER-DOMAIN property. The rule for every future store:
  pending-by-nature when an authoritative external source exists that could catch
  up; permanent-by-nature when DryDocs/the steward IS the authority — declared at
  store creation, never re-litigated per row.
- **Terminus.** This gate rules the LIFECYCLE; it builds nothing. The mechanics —
  the union report surface and the agreement-candidate detection in the loads — are
  follow-up builds (inboxed at sign-off), each of which flips nothing on its own
  authority per §B3.


## 2026-08-18 — GATE: document-content-topology — SIGNED OFF 32/32 (G32)

- **THE COUNT FOLDS TO ONE (§A).** One content-bearing database. The SME's own
  retrieval argument carried it: an agent that cannot see captured context beside the
  structured graph in a single vector search may not answer at all — a silent,
  constant failure where the isolation failure is loud and rare. ADR 0002 D1
  optimized for a load pipeline; the product is an agent. §F supplied the decisive
  precedent: the graph's MOST governed edges (manual pins) always lived inside one
  database, protected by per-edge `origin` + precedence + required rationale — the
  wall never protected them. The fold EXTENDS a proven mechanism.
  Pre-walk rulings stand: R1 `dddocs` rejected and retired; R2 bmc-docs reloads from
  source; R3 the 27 DESCRIBES edges delete (the reload re-establishes them).
  `ddschema` stays OUT (deliberate — ADR 0011 clause 2 never fires). The 2026-07-26
  three-database direction is superseded; load-separation and blast-radius are
  satisfied by corpus_id scoping. The ONE-WAY-DOOR asymmetry was presented and
  accepted. THE HARD PRECONDITION: ADR 0011's three clause-1 guards (QuerySpec
  ground-truth exclusion, the writer boundary, the live :Uncertain audit spec) land
  BEFORE the fold build, not after — staged as G102 with guards-first sequencing.
  The instrument is a LABEL at the single uncertain write boundary, never a
  property on every node; docs-verify's `wrong-db` check re-points at the realm
  label rather than silently retiring.
- **§B — B-DURABLE IS FORCED, and that counted FOR the fold.** With one database,
  WATERMARKED_DATABASES has no subject: the watermark re-keys on the source's
  declared trust_default, per row — the honest fix, made mandatory instead of
  optional. The live false claim (VERBATIM SME email exported "SYNTHESIZED —
  unverified") and the latent ddall instance both end in the same change. Staged in
  G102 (the export path must learn which corpus a row came from).
- **§C — the seven registry rows land in the ONE database** (final names, renamed
  the same day to the doc-registry id grammar: bmc-docs, bmc-docs-controlm-utilities,
  neo4j-docs-essential-graphrag, essential… reference set intact). The re-target is
  a REGISTRY DECLARATION whose graph half only becomes real per machine (J18);
  bmc-docs-controlm-utilities has never loaded and needs no migration.
  `cli.DOC_SWEEP_DATABASES` rewrites; `traversable-until-move` retires from the
  docs-coverage ladder. R3's delete + reload sequence in ONE session per machine.
- **§D — COLLAPSED BY THE FOLD**, exactly as the section provided: no boundary
  remains to price; the accepted cost is §F's discipline, not §D's wall. The
  analytical projection is MOOT (the live store is one). Recorded as the §D single
  confirmation.
- **§E — deepdoc is a CORPUS-DRIVEN RETRIEVER seeded from the grounded graph.** The
  hard constraint is chartered: NO relationship is created unless its subject
  already exists in the grounded graph (the ADR 0002 D1 proxy-node pattern). The
  parser-driven command-line path is an INPUT (one more seed), not a rival
  definition. GRAPH-SEEDED RETRIEVAL is named a REUSABLE PATTERN — second instance,
  after the 2026-07-23 HR-hierarchy graph-seeded resolution. The scaffold unblocks.
- **§F — TWO TRUST AXES, kept distinct and now load-bearing.** `origin` = AUTHORITY
  (who asserted; manual-pin is the HIGHEST standing), `:Uncertain` = CONFIDENCE
  (machine-derived, unverified; the LOWEST). Never conflated, never collapsed into
  one flag; every guard/filter/surface states WHICH axis it reads. `:Uncertain`
  never applies to an authored mapping. **Q9 RULED: `origin` is the GENERAL
  authority vocabulary**, declared now, adopted per-surface as each is touched —
  the PAT support-team edge (source:'pat', no origin flag today) is first in line.
- **Q6 — vendor_docs' DESCRIBES refusal STANDS.** It was about corpus shape, not
  residency; bmc-docs-controlm-utilities is confirmed:false and its doc-graph gate
  is unsigned. The fold made the write legal, not ruled.
- **Q16(b) — SUCCESSOR MINTED (Q20):** check FIRST whether the live DESCRIBES edges
  already satisfy the product→documentation pointer under the fold; only if not,
  build. Ends the prose-only trace open since 2026-08-07.
- **Q8 — THE NAMING RULE enters ADR 0002's amendment:** `drydocs` is the ORIGINAL;
  `dd*` names are its extensions. The test every future database proposal passes.
- **Q10 — ADR 0011 flips PLANNED → EXECUTED-BY-CHOICE**, amended with the REAL
  rationale (retrieval), never the false trigger (Enterprise unavailability).
- **Terminus.** Signing moves NO data and writes NO graph. The apply is staged:
  G102 (guards first, then the fold build + registry re-target + watermark re-key +
  the pinned test_load_map_json alarm treated as a task), G103 is folded INTO G102's
  watermark clause, Q20 (the Q16(b) check-first). G31 unblocks; the deepdoc
  scaffold unblocks.


## 2026-08-18 — RECORD: Q16 clause (b) — SATISFIED BY THE FOLD (Q20; the G32 sign-off's minted successor, closed)

- **What this records.** Gate `document-content-topology` minted Q20 at sign-off to
  run Q16's own "cheapest possible answer, check FIRST" before any pointer build.
  The check ran 2026-08-18 against the live graph (laptop, `neo4jtest`, `drydocs`
  DB — J18 venue; the declaration-layer half is sample-reproducible via
  `drydocs docs-coverage` with the database off).
- **THE TRAVERSAL CLAUSE (b) ASKED FOR EXISTS, LIVE AND DURABLE.**
  `(:SoftwareProduct {product_id:'controlm'})<-[:DESCRIBES]-(:Document)` returns
  the 27 bmc-docs documents. An agent can traverse from the product to the docs
  describing it in one hop, in ground truth, under the ruled shape — and the fold
  made it PERMANENT (the `traversable-until-move` rung retired at G102; these are
  the R3-reloaded edges, not the residency-accident residue). Q16(b) is
  **satisfied-by-fold**; no pointer build is needed.
- **WHAT IS DELIBERATELY NOT CLAIMED, because the coverage census says so:**
  `products_traversable: 0`. The DECLARATION layer does not yet bind the live
  edges — the software registry's `controlm` row declares the SCRAPE corpus
  (`bmc-docs-controlm-utilities`, ungated), while `bmc-docs`, the corpus actually
  carrying the edges, is declared by no product row; and the loader still writes
  DESCRIBES from a hardcoded `SUBJECT_PRODUCT_ID` rather than a registry field.
  That is **Q18's existing scope** (the `describes_product` field the loader
  READS; Idea-88's parked mechanism), now HALF-unblocked: G32 ruled, Q14 (the
  entity-spine term) still owed. Nothing new is minted — the successor for the
  declaration half predates this check and keeps its dependencies.
- **The Q16(b) trace is now CLOSED end to end:** partial close (2026-08-07, prose
  only) → G32 close-checklist entry (2026-08-07, the user's ruling) → Q20 minted
  at the sign-off (2026-08-18) → checked and recorded here. No prose-only link
  remains.


## 2026-08-19 — RECORD: the Essential GraphRAG re-file — VENDOR documentation for Neo4j (Q9; ADR 0006 §2 amendment)

- **What this records.** The SME decision of 2026-07-26, applied at Q9: the book
  (`neo4j-docs-essential-graphrag`, renamed 2026-08-18) is re-filed from "reference/
  methodology" to VENDOR documentation, reasoning verbatim: *"it's not written to
  load into a competitor like TigerGraph"* — Neo4j-sponsored, teaches implementation
  ON their graph, tier T1, same class as bmc-docs. This OVERTURNS a filing inside a
  signed decision (ADR 0006 §2, 2026-07-18), so it lands as an ADR amendment note,
  never an edit — the G30 discipline.
- **Applied:** `taxonomy_path: technology/graph-platform/neo4j`; the "deliberately
  no DESCRIBES" note replaced with the vendor rationale; the loader gains the
  bmc-docs product hook — `(:Document)-[:DESCRIBES]->(:SoftwareProduct
  {product_id: neo4j})`, MATCH-only, once per document on the seq-0 tail, no
  target_version (a book documents the platform, not a pinned release). The old
  test that PINNED the omission flipped to pin the hook.
- **Overtaken, recorded not re-done:** the acceptance's `target_db: dddocs` half —
  `dddocs` was rejected at G32 R1 and every corpus lands in the one database since
  the G102 fold. Satisfied-by-fold.
- **Q18 NOTE:** the hook uses the bmc idiom deliberately, hardcoded
  `SUBJECT_PRODUCT_ID` included — Q18 (the `describes_product` registry field,
  behind Q14) now covers TWO call sites instead of one, and sweeping both in one
  change is exactly why the idiom was matched rather than half-fixed here.


## 2026-08-19 — GATE: email-folder-assignment — SIGNED OFF 8/8 (Q10's gated half)

The gate Q10 drafted and deliberately did not run: the corpus loads TODAY as the
lexical shape (covering-gate reuse, unassigned a valid resting state), and this
page ruled only the assignment edge. All eight confirmations, no held clauses.

- **§A1 — CONCERNS.** Aboutness semantics, the docs_describes family. ASSIGNED_TO
  was offered and declined: it names the workflow act rather than the meaning, and
  a source-signal edge was never "assigned" by anyone. The assertion mechanics live
  in edge properties, not the type name. `docs_email_concerns` survives unchanged.
- **§A2 — ETLProcess confirmed** as the process endpoint class:
  `ControlMFolder | ETLProcess`, two endpoint classes, one meaning, the endpoint
  class recorded on the edge (rua §B2 — the same pair rua already uses).
- **§A3 — the recorded basis is REQUIRED**: `assigned_by` (sme | source-signal)
  plus the evidence pointer (the extract line, or the ruling note) on every write.
  No anonymous assignments — the O24 origin-visibility discipline. "assigned_by
  only" was offered and declined.
- **§B1 — STRUCTURED FIELD ONLY performs.** An extraction pass may PROPOSE, never
  perform: prose mentions anywhere (body OR subject line) are candidates surfaced
  to the SME, not edges. Only a folder/process name in a structured field of the
  extract qualifies as a source signal — and the assumed contract (the G47
  synthetic samples) has no such field, so in practice every assignment starts
  SME-performed. Exact-match-subject was offered and declined.
- **§B2 — the SME surface CONTRACT confirmed** (the build is a later slice,
  inboxed Idea-138): present the email (subject, sent_at, the msg/extract
  CITATIONS), the candidates WITH their evidence, and the unassigned state as
  first-class — never a nag, never a default.
- **§B3 — UNASSIGNED NEVER DECAYS INTO GUESSED.** No batch job sweeps old
  unassigned emails onto best-match folders; the count is REPORTED — natural home
  the pending-source-correction union report once its mechanics build (N13's
  lifecycle; Idea-134) — never auto-drained.
- **§C1 — the K7 §A1 fence CONFIRMED.** This edge says what an email is ABOUT; it
  never authors folder→application attribution, ownership, or support routing.
  The cm_escalation_db correction (2026-08-17) is the standing precedent: email
  and job-name evidence SUPPLEMENTS the human mapping. Traversing
  email→folder→application is legitimate READING; writing a shortcut edge from it
  is not — no derived ownership edge may ever cite a CONCERNS edge as its basis.
- **§C2 — RETENTION RIDES THE ASSIGNMENT.** Purge is project/process-scoped, so
  the assignment is also the retention key: an unassigned email is UNPURGEABLE by
  scope — surfaced by the report, never deleted by a default. After the 6-18
  month Outlook purge the file-server pair is the only copy; a default-expiry
  sweep of unassigned would be unrecoverable. A future purge build inherits this
  clause as a constraint, not a suggestion.
- **What flipped, what didn't (flips-are-follow-ups, N13 §B1):** the map row
  `email-concerns-subject` → `status: confirmed`; the vocab entry
  `docs_email_concerns` stays `status: planned` until the writer build lands
  (Idea-137) — this gate ruled the meaning, it built nothing.
  `email_extracts.cypher` stays test-guarded against ever gaining the write.


## 2026-08-19 — GATE: medallion-stage-vocabulary — SIGNED OFF 6/6 (B5)

The Epic B capture gate: the canonical stage set the estate's neighbor tools
already display, confirmed before any graph attribution can ever cite it. All
six confirmations (A1-A3, B1-B2, C1), no held clauses.

- **§A1 — THE SET: RAW -> TRUSTED -> REFINED -> PROVISIONED.** The 2026-08-09
  correction stands as ruled vocabulary: the terminal stage is PROVISIONED,
  never a platform name. The pre-correction set ended in SNOWFLAKE — a
  consumption TARGET promoted into a STAGE slot, the C25 error class one level
  up (Snowflake is one of several targets a Provision pipeline can write to).
- **§A2 — NOT FOUR OF A KIND, recorded structurally.** RAW/TRUSTED/REFINED are
  S3 zone PREFIXES (one bucket, zone prefixes; each hop its own DPL pipeline —
  the Idea-20 trace); PROVISIONED is a stage with NO prefix (a DB-load into a
  consumption target). The capture carries zone_prefix per stage — present on
  three, null on the fourth — so a flat enum can never misrepresent the last
  stage. A flat-enum capture was offered and declined.
- **§A3 — THE C25 FENCE RIDES THE CAPTURE:** no platform, warehouse or
  target-DB name may ever occupy a stage slot; a consumption target is a
  load-time property of a provision hop, never a stage.
- **§B1 — ONE VOCABULARY, PLATFORM-SCOPED ZONES.** The estate has ONE stage
  vocabulary; zone names (on-prem AND S3) are platform-local spellings that
  map into stages — zones are physical residency, stages are logical.
  Two-vocabularies-plus-crosswalk and evidenced-set-only were both offered and
  declined. Faithfulness rider on the apply: of the on-prem set
  (conformed / semantic / analytic, observed at the 2026-08-09 vendor-doc
  read), only `conformed` has an in-repo mapping basis (legacy dataset_flow
  FILE->CONFORMED ≈ the RAW->TRUSTED hop, Idea-20) — `semantic` and `analytic`
  are captured with stage: ~ until evidence lands, per the
  keep-imports-faithful rule; their mapping is a capture UPDATE when a real
  artifact arrives, not a re-gate.
- **§B2 — CDO IS CONTEXT, NOT ESTATE TRUTH:** the Raw / Conformed-Silver /
  Consumable-Gold mesh framing (internal/cdo-reference/) is a third, external
  vocabulary — crosswalk context only; nothing from it enters the stage set.
- **§C1 — THE FENCE: NO EDGE, NOT EVEN PLANNED.** This capture declares no
  dataset/job stage-attribution edge anywhere. When a consumer actually needs
  stage attribution in the graph, the edge enters the relationship vocabulary
  as status: planned behind its own gate. Register-planned-now was offered and
  declined — pure classification today, the ontology decision stays whole for
  its own gate.
- **What landed at the apply:** config/taxonomy/medallion-stages.yaml
  (schema drydocs.medallion-stages.v1; source: dpl; authority:
  internal-standards). Nothing loads it; the UI half stays O38.

## 2026-08-19 — GATE: server-location-ontology — SIGNED OFF 12/12 (Z2)

**Prompt:** `config/gate-prompts/server-location-ontology.yaml` · **Backlog:** Z2
(Epic Z, server location & geography; user directive 2026-08-08) · **Session:**
producer laptop, three AskUserQuestion rounds + one reshape follow-up, same
session as the Z1 registration. All twelve confirmations ruled; one clause (C2)
was ruled in an SME-RESHAPED form — the reshape is the ruling of record and the
prompt page keeps the original proposal as history (the N13 rule: sign-offs
never edit the prompt).

- **§A1 — THE SERVER SPINE.** An export row mints a NEW `:Server` label (the
  inventory spine); the join to Control-M's `:ExecutionHost` is the
  evidence-carrying EDGE `infra_resolves_to_server`, never a node merge — a
  tiered match can be wrong, and an edge is reversible/auditable where a MERGE
  is neither (K2 precedent). Four labels, four concepts: ExecutionHost =
  Control-M's view (often an LB alias, not 1:1 with hardware), ControlMServer =
  scheduler instance, ControlMHostGroup = load-balancing set, Server = the
  physical/virtual box. Label-union and enrich-in-place were offered and
  declined.
- **§A2 — THE OS.** os_product/os_version land as plain `:Server` properties at
  Z3. The software-registry tie (an OS row + USES_SOFTWARE per the C25
  version-context ruling — the patching query) is RECORDED as a follow-up
  direction, not built: the registry has no OS row today and minting one is a
  registry decision this gate records but does not execute.
- **§A3 — PROD/DR.** `designation` is a PROPERTY on `:Server` (PROD | DR), not
  a node, not an edge property. Both prod and DR servers attach; queries filter
  the property. No DR-pairing edge is invented — not in the export's contract.
- **§B1 — THE GEOGRAPHY GRAIN.** `:DataCenter` is the ONLY new geography node;
  building/city/state/country are PROPERTIES on it; rack rides the
  `infra_located_in` edge. NO City/State/Country nodes at Z2 — promotion is a
  future ruling if a real query needs the traversal. THE Z5 MAP CONTRACT: "a
  located label" = reaches-geography-via-LOCATED_IN; one contract, no per-label
  special cases.
- **§B2 — MIXED GRAIN DECLARED (Idea-90 i).** Every `:DataCenter` carries
  `location_grain` naming the FINEST level its source actually supplied
  (building | city | state | country); absent levels stay null and are never
  inferred; consumers render at the declared grain, never below it.
- **§B3 — AGGREGATE PRESENCE CLAIMS (Idea-90 ii).** "N locations" is a claim
  ABOUT sites: recorded as a claim (property/annotation + source + date) on the
  claiming node, NEVER exploded into N nodes. Placeholder-node explosion was
  offered and declined.
- **§B4 — THE TWO-DCs FENCE, ruled explicitly** (the Z2 acceptance requires it
  by name): the export's data-center field and the Control-M same-named field
  are DISTINCT CONCEPTS that never crosswalk by field name.
  CM_HOSTS.DATA_CENTER / ControlMServer.data_center / ControlMHostGroup's DC
  key = SCHEDULING (default-run-time grammar); `:DataCenter` = PHYSICAL
  geography. Any future association is its own SME-mapped decision (the
  orchestrator-mapping steward-cascade precedent) — never a name join, never
  automated. The fixture guard already enforces the fence in test form
  (tests/unit/test_server_inventory_fixture.py).
- **§C1 — THE JOIN RULE (K2: tiers + evidence, nothing silent).** T1 exact
  (nodeid == server_name, case-normalized); T2 normalized (deterministic
  short-name/FQDN suffix-strip, nothing fuzzier); T3 dns-resolved (the Z4
  nslookup evidence file, resolved names matched at T1/T2). Every
  `infra_resolves_to_server` edge records match_tier + match_evidence +
  resolved_at; unmatched hosts get NO edge and appear explicitly unmatched in
  the Z3 coverage query. Two-tiers-only and an added manual tier were offered;
  the three-tier form was confirmed as proposed.
- **§C2 — THE TECHNOLOGY PORT (SME-RESHAPED, the ruling of record).** The
  proposal was a direct (BusinessApplication)-[:RUNS_ON {role:
  application}]->(:Server) edge. The SME redirected: model it through the PORT
  pattern — "similar to dataport, but technology port." Ruled shape:
  `(BusinessApplication)-[:HAS_PORT]->(:Port {kind: Technology})-[:RUNS_ON
  {role: technology_port}]->(:Server)`. The HAS_PORT hop REUSES the active
  `seal_has_port` edge (identical triple — the C8 reuse rule; its note gains a
  ruled amendment widening kinds from EventProcessing | BatchProcessing to
  include Technology). The planned entry is `infra_port_runs_on_server`
  (Port -> Server), REPLACING the drafted `infra_app_runs_on_server` before
  anything ever joined on that id (registered planned same-day, reshaped at
  the gate — the replacement is recorded in the entry note, not a rename of a
  live join key). The Z3 loader mints ONE technology port per application;
  prod/DR stays on `:Server` per §A3. Port-per-environment was offered and
  declined. Placement, not attribution — unchanged from the proposal.
- **§C3 — THE REFUSAL, confirmed rather than assumed.** NO direct job ->
  Server placement edge exists, not even planned ("where does this run"
  already has its label — RUNS_ON roles agent_host | host_group, ACTIVE since
  P3; rua-load-shapes §A2 killed the synonym split). A job's physical location
  is the TRAVERSAL: job -RUNS_ON-> host/group -RESOLVES_TO_SERVER-> server
  -LOCATED_IN-> data center. A derived convenience edge without a gate was
  offered and declined.
- **§C4 — SITE PROVENANCE (parked at Z1).** infra:server-export keeps
  authority: SOR with the recorded caveat; the flip to ADS happens only on
  evidence, recorded on the registry row when it lands — PRE-AUTHORIZED as an
  update-not-ruling, no re-gate needed.
- **§C5 — THE DOMAIN.** `infrastructure` is REGISTERED as a vocabulary domain
  (fragment 51-local-infrastructure.yaml, prefix infra_; schema enum + header
  twin updated at the draft). Physical placement/geography is neither
  scheduler nor architecture.
- **What lands at the apply:** the C2 reshape in the vocabulary fragment
  (infra_port_runs_on_server replaces infra_app_runs_on_server; seal_has_port
  note amendment; Port node-classification kind note widened), gate_spec on
  the infra:server-export registry row, PENDING -> signed citations in the
  fragment and node-classification notes. ALL THREE infra_ entries stay
  status: planned — the flips belong to the Z3 build (N13: flips are
  follow-ups). The dataset stays confirmed: false until Z3.

## 2026-08-19 — RECORD: FID gate round 1 — census classes ruled, Q5 answered, the case fence corrected (K17; gate `fid-identity-and-scope`, still UNSIGNED)

- **Venue and evidence (J18).** The SME ran doc 09's five Session SQL queries
  (S1–S5, committed at `8ae771de`) on the replica where it lives and brought the
  results to the session as captures. The captures carry real account names and
  scheduling-DC codes, so they stay machine-local (repo-root, ignore-covered,
  never committed); this record is counts and shapes only. Population measured:
  **2,003 distinct owner values, 518,744 current-version jobs in
  actively-scheduled folders** (S5's two rows sum to the whole). The SME notes
  the estate concentrates on 3–4 scheduling data centers — the Control-M
  server dimension, which per the server-location gate's §B4 fence never joins
  physical geography.
- **RULED — §D2 amendment: non-account owner values become named census
  classes,** outside the directory-join denominator: null/inherited (8,501
  jobs / 7,297 folders / 810 app codes — owner unset at job grain),
  folder-header rows (the 63 SMART Table entries — excluded entirely, a folder
  header does not execute), variable-deferred (a profile variable as the owner
  value, 1,232 jobs), template placeholders, and the connection-profile
  placeholder class below. Counted, reported, never joined.
- **ANSWERED — Q5, YES: personal-shaped ids run jobs.** 143 personal-id-shaped
  owners / 11,948 jobs (2.3%); one SID-shaped owner alone carries 8,411 jobs on
  a single application code (recorded as a §G4-style report candidate).
  Consequence confirmed: the directory type column is never a pull filter, only
  the §D2 breakdown lens. SME kept the triage regex as-is — domain-prefixed and
  machine-account forms stay in the service bucket; the real answer joins the
  directory type column at census time.
- **CORRECTED (evidence) — the ALL-UPPER fence.** OWNER is mixed-case at rest
  estate-wide; the recorded 2026-08-12 Q6 half conflated the normalization PLAN
  (SME this session: "force everything to upper ... to make sure joins work")
  with the storage state. The consequence lands on the build: the `--run-as`
  bind's unconditional upper-case against an exact-match predicate now CAUSES
  the silent-zero-rows trap for every lower-stored owner — fix rides K16, not
  this gate. The precise join clause (raw retained, upper join key, fold counts
  reported) is restated for tick in round 2; the stale fence's eight committed
  surfaces sweep with that tick.
- **SME DIRECTION (recorded; class ruling restated for tick in round 2) — the
  top-1 owner value is the Connection Profile placeholder.** 62,936 jobs (12%
  of the estate), 698 application codes, ~11–12 jobs per code — a stamped
  uniform spread. Per the SME: the value comes from the Connection Profile form
  bound to plugin job types (APPL_TYPE families; estate example K8SEPV), where
  identity is the profile's vault-managed credential and OWNER carries no
  account — corroborated by the BMC corpus (connection profiles = centralized
  credential management; `controlm-api-connection-profiles.md`). APPL_TYPE is
  the classification axis (FileWatch = watchers, OS = command), which also
  redirects K25's detection off TASK_TYPE. Build note: `controlm_jobs.sql` does
  not project APPL_TYPE today — only the variables extract does; the projection
  change rides K25/K16.
- **HOMEWORK handed to the SME (counts only, replica-side, same WHERE clause):**
  (a) global `GROUP BY TASK_TYPE` census — does a watcher type exist at that
  column at all; (b) the null-owner bucket cut by TASK_TYPE — tests the
  folder-inheritance hypothesis; (c) `GROUP BY UPPER(OWNER) HAVING
  COUNT(DISTINCT OWNER) > 1` — whether 2,003 owners double-counts casings of
  one account.
- **SCOPE FENCE for the session:** S4 supplies only the Control-M half of the
  §Q0/§G5 disagreement census; the directory half does not exist yet, so the
  designed-vs-stale ratio CANNOT be ruled this session — pending, with the
  Control-M numbers stated. Also fixed: the page carried two questions numbered
  Q6; the roll-up question is renumbered Q8.

## 2026-08-19 — RECORD: FID gate round 2 — four clauses ticked, the case-fence sweep executed (K17; gate `fid-identity-and-scope`, still UNSIGNED)

- **TICKED — the amended Q6 join clause.** OWNER is mixed-case at rest; every
  join to the directory normalizes to UPPER on BOTH sides; DryDocs stores the
  RAW owner value as the property and keys joins/crosswalks on the upper-cased
  form; the census still reports fold counts. Swept in this commit: the psgmgr
  ledger note, source-registry, the K16 company prompt, doc 09's fence, the
  K17 backlog note. NOT swept, deliberately: `cli._scope_binds` /
  `fid_census.py` docstrings and the bind fix itself — K16 is desktop-claimed
  and the fix is build work; the company-side ledger correction rides the
  port channel.
- **TICKED — §G7, the connection-profile-resolved run_as class.** Plugin-typed
  jobs (APPL_TYPE families; estate example K8SEPV) carry their identity in the
  Connection Profile's vault-managed credential; OWNER is vestigial. Excluded
  from the FID directory join (12% of the estate rides on this — 62,936 jobs).
  APPL_TYPE is K25's classification axis; `controlm_jobs.sql` must project it
  (build rides K25/K16). The variable-deferred bucket stays separate until
  evidence says otherwise.
- **TICKED — §G8, ranked-then-curated platform recognition.** S3 breadth
  ranking feeds SME curation; confirmed literals live values-twin under
  internal/ (K18 precedent); review threshold app_codes >= 10 plus the
  per-server scheduler family; the directory's type columns become a check,
  never the primary recognition.
- **TICKED — §D6, estate-wide demand set with a per-scheduling-DC census cut.**
  The pull list stays the union; every census output gains the DC breakdown
  (platform accounts are per-server-instance; the estate concentrates on 3-4
  scheduling DCs). The server-location §B4 fence rides along.
- **Session state after round 2:** closed or amended — §D2 (census classes),
  §D6, §G7, §G8, Q5, Q6 (amended + ticked), Q8 renumbered. Still to walk —
  §A1-A4, §B1-B5, §C1-C4, §E1-E3, §F1-F3, §G1-G6, and open questions Q0
  (pending on the directory half by scope fence), Q1, Q2, Q7, Q8.

## 2026-08-19 — RECORD: FID gate rounds 3-5 — §A closed 4/4, §B closed 5/5, §C1-C3 (K17; gate `fid-identity-and-scope`, still UNSIGNED)

- **§A CLOSED 4/4 — identity.** A1: :AppUser keyed on the directory id (the
  id-owner application's own record key, Source B); Source A's employee-id is
  the HR carrier's per-row key, never the identity; uniqueness constraint on
  AppUser.fid. A2: fid_name is a property; name -> id resolution is an explicit
  crosswalk reported like a match tier, run AFTER the G7/G8 class gate so the
  miss rate measures real accounts only — the 171-way platform name is the
  measured proof it is never 1:1. A3: the uniqueness half is now SETTLED BY
  MEASUREMENT (54 distinct names on 227 rows — names are not unique at a point
  in time); the crosswalk carries a time qualifier and reports multi-candidate
  names, never picks one; the reuse-after-retirement half stays open as Q1
  with assume-not-safe standing. A4: the environment triplet stays three
  :AppUser nodes; a logical-service grouping node is deferred, not decided.
- **§B CLOSED 5/5 — ownership over time.** B1: as-of assertion, extract date,
  origin declared, inherited by every derived fact. B2: snapshot disagreement
  is a TRANSFER, reported, current edge updated, trail never silently
  overwritten. B3: extracts retained as dated snapshots (depgraph precedent);
  Q2 (a real history surface?) stays worth one question before diffing is
  built. B4: originating application UNKNOWN, never inferred — no back-dating,
  no name-prefix origin. B5: retired accounts IN scope; status is a property,
  never a pull filter.
- **§C1-C3 CONFIRMED — the edge.** C1: `seal_appuser_belongs_to_application`
  registered status: planned (AppUser -> BusinessApplication,
  BELONGS_TO_APPLICATION, role service_account, LOCAL Agent -> Entity, domain
  business_application; the C8 identical-triple rule on the shared label; the
  N13 flips-are-follow-ups pattern — no loader inside K17). C2: target is
  :BusinessApplication, not the BatchProcessing Port — an ownership-record
  fact, not batch wiring. C3: N:1, never a schema constraint — a graph test if
  anything (the TOM-roles lesson); mid-transfer states are normal.
- C4 (the K2 reconciler feeds from the SAME crosswalk) walks next round with §E.

## 2026-08-19 — RECORD: FID gate rounds 6-7 — §C closed 4/4, §E closed 3/3 (E1 reshaped), §F closed 3/3, §G1 (K17; gate `fid-identity-and-scope`, still UNSIGNED)

- **C4 CONFIRMED — one crosswalk.** TierReconcilers.fid populates from this
  ingest (name -> app_id via §A2 then §C1); no second mapping table;
  match_method 'fid' unchanged. The tier's re-scope is §G3's business.
- **§E CLOSED 3/3 — registration, with E1 RESHAPED by Q3's answer.** E1: the
  directory is a table in the replica already in scope, so the registration is
  a DATASET on the existing replica system (layer human on the dataset row),
  not a new system row — no new connection surface; classification Internal,
  authority SOR for account identity, confirmed: false until sign-off. E2:
  audit-fields entry status stub until confirmed object-by-object; the
  envelope says the record changed, never what it changed from. E3: extracts
  live under internal/ company-side; this repo carries mechanism only.
- **§F CLOSED 3/3 — the mislabeled evidence.** F1 verbatim (a corrected copy
  is no longer evidence); F2 the correction is a recorded mapping (column
  labeled FID reads as fid_name through the §A2 crosswalk, noted on the
  corpus's known-defect note); F3 unresolved rows load nothing, never fuzzy.
- **G1 CONFIRMED — registration, never consumption,** with
  `assignment_kind: 'registration'` explicit on the edge data.

## 2026-08-19 — GATE: fid-identity-and-scope — SIGNED OFF 33/33 (K17)

- **Walked in one session, ten rounds, evidence-first**: the SME ran doc 09's
  five Session SQL queries (S1–S5, `8ae771de`) on the replica and the walk
  started from the numbers — population 2,003 distinct owner values / 518,744
  current-version jobs in actively-scheduled folders. Tally: §A 4/4 · §B 5/5 ·
  §C 4/4 · §D 6/6 (D6 added in-session) · §E 3/3 (E1 reshaped
  dataset-on-replica) · §F 3/3 · §G 8/8 (G7/G8 added in-session). Round
  details in the four session RECORD entries above (rounds 1–7); this entry
  closes rounds 8–10 and the sign-off.
- **§G2 CONFIRMED** — no transitive read of registration onto jobs; the two
  facts meet on the job and nowhere else.
- **§G3 RULED — the K2 FID tier is re-scoped**; formal amendment to the
  signed seal-attribution-match-policy gate recorded in the next entry.
- **§G4/§G5/§G6 CONFIRMED** — the disagreement is a first-class finding;
  three readings distinguished per case by a human; no derived third fact
  authored (a report until its own gate).
- **Open questions closed or held**: Q0 PENDING by the session scope fence
  (only the Control-M half of the disagreement join exists; consequence: the
  §G5 designed-vs-stale ratio waits on the directory half). Q1 STILL OPEN
  (name reuse after retirement; consequence: the crosswalk keeps its time
  qualifier and multi-candidate reporting — A3's assume-not-safe stands).
  Q2 ANSWERED: NO history surface exists — §B3's snapshot diffing is the
  design, not the fallback, and D4's retention is the only transfer record
  anywhere. Q5 ANSWERED YES (round 1). Q6 ANSWERED + AMENDED (rounds 1–2).
  Q7 RULED: the recertifying manager is the OWNER-OF-RECORD — an
  accountability fact, never swept into the contact deferral; the
  account -> person edge registers planned and the two-human-owners rule
  becomes a graph test against it. Q8 ANSWERED: the id-owner application
  supports by-application roll-up (the four listing captures prove it);
  the census is one query per surface.
- **Vocabulary minted, N13 flips-are-follow-ups**: `seal_appuser_belongs_to_application`
  (AppUser -> BusinessApplication, BELONGS_TO_APPLICATION role
  service_account, assignment_kind 'registration' on the data, as_of +
  origin declared) and `seal_appuser_owned_by` (AppUser -> Employee,
  OWNED_BY role fid_owner, the Q7 ruling) — both status: planned in
  41-local-business-application.yaml; NOTHING loads inside K17.
- **Held-entry consequence recorded**: `scheduler_executed_by`'s identity
  blocker (blocker 1) is CLEARED by §A1/§A2; its run-layer blocker stands —
  the entry remains planned.
- **Build groomed as K26** (the acceptance's follow-up): dataset-on-replica
  registration per E1, the demand-set pull with the D2/G7 class gate, the
  crosswalk + TierReconcilers.fid under the amended scope, retained
  snapshots per B3/D4, the owner-of-record leg, and the planned-entry flips
  in the build commit. The `--run-as` bind fix, the APPL_TYPE projection,
  and the code docstring sweep ride K16 (desktop-claimed).
- **Unblocked by this sign-off**: seal-attribution-match-policy tier 2
  (under the amended scope) and software-version-context §F (the
  application-level version rollup) — both wait on the K26 build, not on
  further rulings.

## 2026-08-19 — AMENDMENT to the seal-attribution-match-policy sign-off: the FID tier is re-scoped (fid-identity-and-scope §G3)

- **What changes.** The signed gate (2026-07-14) ordered SEAL > FID >
  APP_NAME > ALIAS as evidence of the JOB's application. The
  fid-identity-and-scope evidence (§G, 2026-08-05 counterexample; §G7's
  platform/connection-profile classes, 2026-08-19) shows the FID tier
  carries REGISTRATION, not attribution — filling it as specified would
  resolve a job to the account's owning application and contradict
  confirmed app-code mappings.
- **The amendment (G3, ruled 2026-08-19).** FID evidence resolves ONLY where
  no confirmed folder attribution exists, and never overrides one; a
  FID-tier result that disagrees with a confirmed mapping is reported as a
  disagreement (§G4's report), never written. The class gate (§D2/§G7/§G8)
  runs BEFORE the tier fires, so placeholder and platform classes never
  enter it.
- **What does NOT change.** The precedence ORDER and the match_method
  vocabulary are untouched; `match_method: 'fid'` keeps its meaning; the
  signed gate's yaml is not edited (N13) — this entry is the amendment
  record, on the G35-amendment precedent.


## 2026-08-22 — GATE: vendor-docs-entity-spine — SIGNED OFF 21/21 (Q14)

The SME session for the gate Q14 drafted the same day — all 21 confirmations,
one clarification exchange recorded (§A2), no held clauses, no edits to the
drafted proposals. Venue for the live evidence: laptop, `neo4jtest`, `drydocs`
DB, 2026-08-22 (J18). Signing moves NO data and writes NO graph; every
activation is a groomed follow-up (Q24/Q25, minted at this sign-off).

- **§A — ControlMUtility IS a first-class node (A1), a NEW dd:ControlMUtility
  class (A2).** A2 carried the session's one clarification: the SME's condition
  — "I agree if it contains ControlMJob, ControlMFolder and is not a sibling" —
  was confirmed to mean FAMILY PLACEMENT: ControlMUtility files IN the
  Control-M class family (the 10-node-classifications group holding
  ControlMJob/ControlMFolder/ControlMServer) and is NEVER a SoftwareProduct
  row; the rejected alternative would have put each utility beside controlm/
  neo4j/oracle-db as a peer product ("sibling"), and the SME's own reading was
  that the corpus documents Control-M's parts, so peerhood never made sense.
  Restated and confirmed as drafted. A3: the docs_utility_part_of bridge
  (PART_OF -> SoftwareProduct {controlm}, third triple of the label, C8)
  confirmed with direction. A4: name-keyed identity + deterministic
  family/kind derivation with unclassified counts reported, confirmed.
- **§B — REUSE DESCRIBES (B1), bare edge (B2), title-match basis (B3).** The
  aboutness label is not duplicated: docs_describes_utility is a new triple
  beside the ACTIVE Document -> SoftwareProduct entry; a DOCUMENTS mint was
  offered and declined. No version properties ride the edge — the caveat is
  node-grain per the Q13 close. Derivation is deterministic title-match,
  unmatched count reported, never defaulted (the email-folder-assignment
  structured-signal bar; here the structured signal IS the title).
- **§C — vendor cross-links ARE assertions we carry (C1), basis REQUIRED
  (C2), rdfs:seeAlso ADOPTED (C3).** docs_see_also carries href + anchor
  evidence on every edge (O24 / email-folder-assignment §A3 — no anonymous
  assertions); vendor-asserted origin, never :Uncertain. C3 is a real ruling,
  not a note: the rdfs namespace is declared in namespaces.py, so the mapping
  is ADOPTED on the entry rather than parked as a candidate (the ANNOTATES
  local-pending pattern explicitly NOT followed here, because its blocker —
  an undeclared namespace — does not exist). C4 acknowledged (the decline
  path was priced; the choice was made knowingly).
- **§D — the overtaken premise RECORDED (D1), the real chain ruled (D2), NEW
  TRIPLE over widening (D3), no-demo registration accepted (D4).** Q14's
  acceptance required the layer-3 join "recorded as BLOCKED on G32"; G32
  signed 2026-08-18 and the G102 fold executed, so the record here is the
  dissolution (the Q9 overtaken-not-re-done idiom), and what now gates the
  join is: §A/§B (this page), the §E load, and the CMD_LINE -> utility
  parser work (G14 feed pattern under the G32 §E graph-seeded charter).
  scheduler_invokes_utility stays a separate planned triple — the ACTIVE
  scheduler_invokes is untouched (PATH-keyed Script vs NAME-keyed utility;
  no blast radius on the shipped extractor). The sample estate carries zero
  utility invocations (17/17 jobs with cmd_line, none matching) — registered
  with no demo, stated plainly.
- **§E — THIS page is the corpus's doc-graph gate (E1), the Q13 shape
  confirmed (E2), the two unregistered loader edges registered (E3), the
  flip authorized-not-performed (E4), scope fenced (E5).** E1 resolves the
  chicken-and-egg Q14's close named: the acceptance's LOADED-spine evidence
  premise was unmeetable because the load waited on this very page; G32's Q6
  clause left the doc-graph gate unsigned and no other backlog item owned
  it. E2 confirms the layer-1 shape exactly as Q13 shipped it (capture-scoped
  doc_id; :DocSection reused from the design-doc family, second use recorded
  on its classification). E3 closes the loader-without-vocabulary gap found
  at the draft: docs_in_section / docs_subsection_of registered planned.
  E4: signing AUTHORIZES bmc-docs-controlm-utilities -> confirmed: true; the
  flip and the first live load are Q24 (the machine holding the capture is
  the desktop — the load is venue-bound, J18). E5: Q15 QuerySpecs, Q18
  describes_product, all loader code, and the bmc-docs corpus are out of
  scope.
- **Terminus.** Signing changes vocabulary NOTES and the map entry status
  only. All seven entries STAY `planned` — they flip active WITH their build
  (K2/G55 flips-are-follow-ups): Q24 (registry confirmed flip + first live
  layer-1 load, desktop) and Q25 (the entity-spine build: utility minting +
  DESCRIBES title-match + SEE_ALSO parse + PART_OF bridge, flipping those
  entries active with supplement blocks). scheduler_invokes_utility stays
  planned past Q25 — its flip rides the future parser work per §D2(iii).
  Map entry vendor-docs-entity-spine: proposed -> confirmed (summary 9->8
  proposed, 25->26 confirmed).


## 2026-08-22 — RECORD: gate vendor-docs-entity-core — RENAMED from vendor-docs-entity-spine, the same day's SIGNED OFF 21/21 TRANSFERS (user ruling; Q6 precedent)

- **What this records.** Minutes after signing the gate above, the SME ruled the
  id itself: "spine" is on the US-business-English banned list
  (docs/style/us-business-english.md; CLAUDE.md §6 — "backbone"/"core", never
  "spine"), so `vendor-docs-entity-spine` becomes **`vendor-docs-entity-core`**.
  A signed-off gate TRANSFERS across a rename — the Q6 / source-registry-v2
  precedent — so the 21/21 sign-off, its one §A2 clarification, and every ruling
  stand unchanged under the new id. This entry's heading carries the new slug so
  the gates surface accounts for the renamed prompt file; the SIGNED OFF entry
  above is the ruling record and is not edited (L25 riders-not-edits).
- **Scope of the rename — pointers, never the signed record.** The prompt file
  (`git mv`), its `id:` and `title:`, the taxonomy-ontology-map entry id +
  `gate_spec:` path, the map header/summary comments, the vocabulary-note gate
  references (7 entries + banners), Q14's close-note annotation, Q24/Q25 (unsigned
  items — their prose de-spines too), and NODE_QUICK_REFERENCE. The signed
  confirmations' body prose retains "spine" as the SME saw it; the mechanism-name
  boundary (CLAUDE.md §6: a style pass never renames identifiers) is not crossed
  because this IS the identifier's owner renaming it, not a style pass.
- **History.** Everything before this entry is filed under the old id; the yaml's
  header note points here.
## 2026-08-25 — RULING: catalog Sub-LoB label — `CatalogSubLOB` (C27 item (b); SME, Option 1)

- **What this rules.** The company built the Sub-LoB grain as node label `:SubLOB`; the
  producer reserved `CatalogSubLOB` at C26. Two labels for one concept — divergence #3 of the
  C26 ledger repeating one level below the LOB question. **RULED: `CatalogSubLOB`, Option 1 —
  the company relabels, the producer's reserved label stands, one shape both sides.** The
  vocabulary id `catalog_has_sub_lob` is unchanged and shared; only the target label moves.
- **Why Option 1 and not the other two.** The LOB precedent is six weeks old and went the same
  way: the company's own **GATE REVERSAL of 2026-08-06** (`gate-log.md:1678`, port
  `drydocs-port-20260806`, producer head `a14a8028`) retired the 2026-06-25 "Option A" gate and
  adopted the full producer catalog model — `:LOB` → `:CatalogLOB`, `code` reinstated. Ruling
  Sub-LoB the other way would leave the hierarchy inconsistent with itself one level down.
  Option 2 (company renames its vocab id, keeps `:SubLOB`) removes the id ambiguity but freezes
  the two-label divergence permanently; Option 3 (producer adopts `:SubLOB`) reverses the LOB
  ruling for one level only.
- **NOT a port break, and an earlier producer note that said so was wrong.**
  `drydocs_core/ontology/relationship_vocabulary/**` is `per-entry`, and its entry rule is
  explicit: *"NEVER downgrade a consumer entry whose status is active (or a node class a live
  loader depends on) to the producer's planned/deprecated."* The company entry is `active` with
  `sub_lobs.cypher` behind it; the producer's is `planned`. The merge keeps the company's — no
  duplicate id, no `FragmentSourceError`. What the divergence actually was is a mismatch with
  no expiry, which is why it needed a ruling rather than a deadline.
- **FLIPS ARE FOLLOW-UPS.** This authorizes; it performs nothing. The producer's
  `catalog_has_sub_lob` and `catalog_sub_lob_has_product_line` stay `planned` — the producer
  models no Sub-LoB grain and has no loader, and an `active` entry with no loader is the claim
  this repo does not allow. The build is groomed separately.
- **Three of C27's four questions were already settled outside it,** which is why this entry is
  a ruling rather than a gate session: (b) the LOB label by the 2026-08-06 reversal; (a) the
  Sub-LoB grain by the company build; (c) the map ids by the company adding company-only rows
  rather than renaming producer ones. (d) the S3 `app_id` cutover is NOT closed here — it is
  Tier-B HELD company-side under their own tracker T1, rebuild-not-migrate, and pulling it into
  a catalog ruling would give it a second owner.
- **Map-id correction made with this ruling.** C26's two reservations named ids nobody uses:
  it reserved `sub-lob-org-unit` and `catalog-lob-reconciles-segment` while the company built
  `lob-has-sub-lob` and `sub-lob-has-product-line` and KEPT the producer's
  `lob-reconciles-to-segment`. A placeholder that guards a name nobody mints guards nothing, so
  both are moved to `rejected` (superseded, kept for audit — the C12 `requires-scheduler`
  lifecycle) with the real company ids recorded as the names the producer must not mint.
## 2026-08-25 — RECORD: gate `standard-identity-and-carrier` DRAFTED, unsigned (G95)

- **What this records.** The G95 prompt is drafted (5 sections, 17 confirmations) and
  NOTHING is decided: no config family exists, TOKEN_REGISTRY is untouched, and its every
  entry stays `proposed` exactly as its own header says. This stub exists because the G95
  acceptance names it as part of the deliverable — the gates surface should show the gate
  as awaiting-SME rather than the question living only in a YAML file nobody re-reads.
- **The four questions on the page.** (A) whether a validation standard gets a stable id
  (proposed `<domain>.<subject>.v<N>`, opaque to selection), with the CONTRACT CHANGE said
  plainly — an id outside TOKEN_REGISTRY turns the registry-vs-standard agreement test from
  a two-way guard (code == document) into a three-way one (code == document == carrier),
  both directions. (B) the carrier, three candidates priced and none pre-picked: versioned
  YAML on the launcher-registry/G26 precedent; SQLite-as-primary, which collides with ADR
  0009 rule 1 and ADR 0014's domain-fact line and is PRICED rather than forbidden; and
  0009's own hybrid (YAML truth + mapping.db derived read model + rule-5 draft flow), which
  is the shape the floated "config table" can have without breaching anything. The port
  disposition of BY-TEAM rows is part of the ruling (the 2026-08-25 alias lesson: company
  values in a canonical-producer file are overwritten wholesale). (C) the §7.5/G84 fence
  ratified explicitly — the DD digit is a grammar version and selects nothing, ruled NOW
  because a per-team registry is exactly the pressure that would break it. (D) divergence
  policy: ADD is the C16 case and stays free; RELAXING a company-required token is put as
  forbidden vs permitted-with-ratification, with recorded-only recommended against in the
  page's own text.
- **Registered: nothing, deliberately.** Identity and carrier are config-layer; no
  vocabulary term, node class, property term or map row is proposed. §E1 makes the
  absence a decision on the record; a future :Standard graph presence would be its own
  ontology gate.
- **Related:** G94 (the selector — builds regardless, may not invent the carrier), G84
  (adoption measurement + the fence's origin), the etlprocess-kind-enum rider (where
  engine names must agree if per-engine standards get ids).

## 2026-08-26 — RECORD: gate `tech-partner-attach-level` DRAFTED, unsigned (K20)

- **What this records.** The K5-amendment prompt is drafted (5 sections, 9 confirmations,
  `config/gate-prompts/tech-partner-attach-level.yaml`) and NOTHING is decided: K5 stays
  signed, the supplement stays unedited, the ProductRole scheme stays exactly the fixed 7.
  An amendment gate is how a signed clause is re-opened (the G35 precedent); drafting one
  decides nothing (G27/W1/N10/G61).
- **The four questions on the page.** (A) the attach level — K5 §B signed tech_partner
  AreaProduct-only; the SME (2026-08-06) and the company role guidance both read it as
  PRODUCT-level, and Area Tech Partner is separately defined. (B) whether area_tech_partner
  is admitted as the eighth concept — the fixed-scheme rule exercised, not broken — with
  fold-into-one and defer-for-extract laid out and priced. (C) the consequence restated
  against current facts: G91 (2026-08-18) activated catalog_has_area_product after the item
  was groomed, so Idea-75's no-rows-no-loader measurement is half-stale — what stands is
  that no cabinet attribution loader exists on either side; plus the proposed
  seeded-concept-reachability guard (the G35 §A2 + Idea-75 pair would both have surfaced at
  seed time). (D) the change_note re-read — if the level moves, the note's two halves may
  describe one role, and the CTO rename history may belong to whichever concept §B admits.
- **Fences.** G35 §A6 (the SEAL-side tech partner -> CTO alias STAYS) is explicitly
  unaffected; the TOM family, the three active attribution forms, the other five concepts
  and area_product_owner's scope are named untouched.
- **Authority note.** This stub is a RECORD, not a ruling — J43's reconcile check treats
  DRAFTED stubs as non-authority; no vocabulary status may cite this heading.

## 2026-08-26 — RECORD: org-acronym sanitization — the `cdo-*` rename (user direction, in-chat)

- **What this records:** a four-letter internal org acronym was retired from every
  publishable surface (user direction 2026-08-26, this session). The gate formerly named
  for it is now `cdo-crosswalk` (spec `config/gate-prompts/cdo-crosswalk.yaml`); the
  vocabulary crosswalk is `config/crosswalks/cdo-vocabulary.yaml`; the doc corpus id is
  `cdo-frameworks`; the Epic W id is `cdo-alignment`; the reference capture moved to
  `internal/cdo-reference/`. Prior entries in this log were swept IN PLACE — read `cdo-*`
  (or "CDO") in any pre-2026-08-26 entry as the renamed id, signed under its former name.
- **The old↔new mapping** is recorded once, in `internal/cdo-reference/README.md`
  (Internal — the old string may not appear in this publishable file). The retired
  strings can never re-mint with a different meaning (doc-source-registry `retired:`
  carries the placeholder entry).
- **What this does NOT do:** no ruling is reopened. The 2026-08-05 crosswalk sign-off
  (13/13, row 5 blocked-on-recapture) stands unchanged under the new name. CDO on these
  surfaces is the industry C-suite sense (chief data office/officer) — the sense
  collisions are recorded in `config/glossary/terms-public.yaml` (fifth pass).

## 2026-08-27 — RECORD: extract-vintage convention + the SME-review-status capture protocol (user direction, in-chat)

- **What this records:** two standing conventions, neither a ruling on any mapping.
  (1) **Extract-vintage** — a gate keyed on an extract names the pull it rests on, and a
  sign-off session working from an older pull re-pulls first. Generalized from the PAT
  cabinet session's §G1 finding (2026-08-27): a role class present in the August pull did
  not exist in the June pull, so a June-keyed ruling would have been correct on its
  evidence and wrong in fact, with no signal anything was missing. Convention text lives
  in docs/restructure/03-hitl-sme-flow.md (gate-page format section).
  (2) **SME review status** — the company→producer profiling capture protocol is defined
  at docs/port/profiling-sync-packet.md: one shape-only status per company review
  session, hand-carried, landed in internal-local/company-backflow/, intaken by the
  producer checklist (ledger → manifest → item flags → crosswalks → page adoption →
  receiving tables). Wording rule: always "SME review status," never "what to send
  back" — the hand-prompts-ask-nothing-back rule extended to the reverse channel.
- **Pending ruling flagged, not made:** the volumetrics boundary (totals + ratios +
  all-N-of-N publishable; disaggregated per-entity splits stay in the twin) remains
  precedent-only per config/classification.yaml's own NOT-ruled flag; it rides the
  tech-partner-attach-level sign-off session as a rider question.
- **Authority note.** RECORD, not a ruling; no vocabulary status may cite this heading.

## 2026-08-28 — RECORD: gate `source-connection-and-run-identity` DRAFTED, unsigned (WP-1 of the source-registry two-issue plan)

- **What this records:** the prompt file config/gate-prompts/source-connection-and-run-identity.yaml
  exists (6 sections, 19 confirmations, 2 provenance blocks). It puts to the SME: (A) the
  `connection:` block on SYSTEM rows — settings group + secret REFERENCES by env-var name +
  restricted-record pointer, values never; (B) the RESTRICTED CONNECTION RECORD term replacing
  the connection/values sense of "internal twin" only, plus a `handling: restricted` marker on
  Internal (J23 note-class); (C) `acquisition.since:` + the dated transition history on top of
  N13's signed flip ruling, and the ADR-0012-vs-N12 acquisition-vocabulary reconcile; (D) the
  :JobRun input-identity envelope (dataset id, zone-relative path, input sha256 — M3/M4
  family); (E) declare-or-refuse as standing acquisition policy with a recorded override;
  (F) fence + the profiler-as-typed-run rider parked to the review-status protocol.
- **Evidence base:** the 2026-08-28 registry/acquisition survey (as-built state: the psgmgr
  row's nulled connection field; the :JobRun envelope's missing input identity; the `load
  --csv` undeclared route) + DataHub/OpenMetadata as cited external models, not adoptions.
- **Authority note.** This stub is a RECORD, not a ruling — J43's reconcile check treats
  DRAFTED stubs as non-authority; no registry field, envelope property, or term may cite this
  heading. Sign-off item: N19. The --csv closure (G121) and the S13 import fix build as plain
  defects and do not wait for this gate.

---

## 2026-09-01 — RECORD: gate `replica-derivation-edge` DRAFTED, unsigned (C38)

- **What this records:** the prompt file `config/gate-prompts/replica-derivation-edge.yaml`
  exists (5 sections, 11 confirmations). It puts to the SME: (A) the gap — replica-ness is
  spelled three ways and all three are attributes, plus the prior question of whether
  TRAVERSAL is actually wanted, since a reporting-only need is already answered; (B) the
  candidate typed derivation edge `reg_derived_from` (DataAsset → DataAsset,
  prov:wasDerivedFrom), its direction and its DATASET grain; (C) the sibling/same-as
  anti-pattern, rejected knowingly rather than by omission; (D) whether the derivation KIND is
  also kept redundantly as an edge property, and its value set; (E) the fence.
- **Evidence base:** `docs/design/datahub-substrate-review.md`, anchors `replica-note` and
  `what-changes` row 11 — cited by anchor, never summarized, so the reasoning is re-read rather
  than re-derived. As-built counts confirmed against `config/source-registry.yaml` at this
  commit: `authority: ADS` on 12 rows against `SOR` on 17.
- **Why the anti-pattern is in the prompt and not only in the review:** DataHub's
  `SiblingGraphService` actively DELETES any lineage relationship between two siblings from the
  merged read path, which is the default. Modelling replica-ness as aliasing destroys the fact
  being recorded, so the sibling shape must be rejected knowingly. A gate that omits it invites
  the SME to reach for the obvious construct.
- **Vocabulary state:** `reg_derived_from` is registered `status: planned` in
  `drydocs_core/ontology/relationship_vocabulary/44-local-registry.yaml`, domain `registry`,
  `supplement: ~` and `loader: ~` because nothing loads until this gate rules.
  `drydocs_core/schema/schema_graph.cypher` regenerated.
- **Authority note.** This stub is a RECORD, not a ruling — J43's reconcile check treats DRAFTED
  stubs as non-authority; no registry field, envelope property, or term may cite this heading.
  Sign-off item: a follow-up to C38, not yet minted.

## 2026-09-01 — RECORD: the schema segment's publish ceiling is re-asked for Teams Edition (`schema-identifier-publish-ceiling-teams-edition`, DRAFTED, UNSIGNED)

- **Status:** DRAFTED 2026-09-01, awaiting the SME walk. Nothing is renamed, swept or
  redacted. J70 clause (a) is the item; this is the escalation it routes to.
- **What this is NOT.** It is not a claim that J13 class 3 (2026-08-11) was wrong. That
  record closed class 3 as *ruled-elsewhere*, deferring to the SIGNED N9 `source-registry-v2`
  grammar (§Q1, 2026-07-31), and it was right on the evidence it had — including its own
  correct catch that `cm_escalation_db` is a TABLE inside `psgmgr` and not a database.
- **What is actually re-asked: a CONDITION inside the clause it defers to.** N9 §Q1 keeps the
  schema segment "when it is established public vocabulary — and it names `psgmgr` as exactly
  that". Established *for whom*. Today's answer is this company's estate. **ADR 0015 Team
  Edition (PROPOSED 2026-08-27) changes the audience** — copier-templated per-team instances
  generated from a cherry-picked base, plus the standing standalone-template goal — and a
  name that is ordinary vocabulary inside an estate is a local coinage outside it. New
  evidence postdating a signed ruling is the only legitimate reason to reopen one, and this
  is the first exercise of **C40**, the item minted to give a signed ruling that route.
- **The motive is GENERALIZATION, not sanitization, and the distinction is fenced (§B2).**
  The connection coordinate — the database — is already redacted, and `psgmgr` alone fails the
  standing "could someone connect with this string alone" test. J13 **class 1** ruled platform
  tokens AUTHORED with no sweep owed; if this gate is later misread as a sanitization
  precedent, someone sweeps those tokens on the same reasoning and collides with a signed
  ruling. §B2 exists to make that misreading fail.
- **Blast radius, measured 2026-09-01 (producer desktop, this worktree), not estimated:**
  `psgmgr` 242 tracked files, `cm_escalation_db` 28, `seal:app-extract` 21,
  `dpl:pipeline-registry` 16. Several are tests pinning the literal — the class-1 `PRARAG`
  sweep was stopped for exactly that reason. §C2 makes the SME choose ids-only, ids-plus-prose,
  or everything, because those are three different pieces of work.
- **Mechanism if it rules `no` (§C1):** mint the new id, set `replaces:`, add the retired-ids
  row — the mechanism the 17 existing retired ids already use. Never a find-and-replace: the
  derived URN moves with the id, so a textual sweep leaves the old string unresolvable with
  nothing recording that it existed.
- **One adjacent fact that may moot part of it (§C4):** ADR 0017 ruled `spiderdb` PUBLISHES
  (it is the name, not the coordinate) while the ids still carry `[db]`. Resolving that in the
  same change avoids touching the same 242 files twice.
- **Residue kept deliberately (§D1):** `cm_escalation_db` is correctly formed and still
  misreads, because the `_db` suffix makes a table look like a database — a LEGIBILITY defect
  rather than a publish-ceiling one, and it survives whatever this gate rules, including a
  ruling that closes the gate with no other work.
- **Authority note.** This stub is a RECORD, not a ruling — J43's reconcile check treats
  DRAFTED stubs as non-authority; no registry field, envelope property or term may cite this
  heading. Sign-off item: J70 (`feat/ui-web`), whose `gates:` field takes this slug.

## 2026-09-02 — RECORD: the backlog series is the MODULE; the 27 letter series are FROZEN (PLAN1; SME ruling in-chat, 2026-09-02)

**What was ruled.** New backlog item ids take the code of the module they belong to
(`LOAD12`, `WEB3`, `PLAN1`), derived by the allocator from `docs/restructure/backlog/modules.yaml`
`series:`; nobody picks a letter. The 27 legacy series — A..Z, GN, MM — are frozen at the
highest number each had ever taken across local, every remote ref and history, measured through
the allocator on the day: A4 B5 C44 D11 E2 F2 G136 GN2 H8 I8 J78 K30 L29 M4 MM14 N28 O92 P6 Q28
R23 S16 U27 V11 W3 X4 Y7 Z9. The snapshot is a committed constant (validate.py and
test_backlog.py, asserted equal), never the current max. **No id moves** — ids are join keys
and this file cites them inside signed records.

**Why.** The letter was an epoch tag: `plan.yaml` mapped phases 1:1 to epics and to letters,
so a series recorded WHEN a phase opened, not what an item is about. G held 136 of ~630 items
across six epics. Every item already carried the topic as a REQUIRED field (`module:`, 611 of
611 on the day), so the prefix was the only thing missing. The SME's direction was to retire the
letters and start by module BEFORE Teams Edition, because the problem compounded with every
groom — 18 more letter ids landed the same morning.

**Module, not domain — the departure from C41.** C41 (2026-09-01) designed a DOMAIN registry
as the item-series source, blocked on a Teams Edition ruling. Domain is the ontology topic;
module is the MODULE_MAP component an agent pulls against and the field every item already
carries. Item series take the module. The domain registry remains an ontology concern and is
decoupled from item numbering by this record; C41 is re-scoped accordingly and its `gates:`
no longer cites `schema-identifier-publish-ceiling-teams-edition`, a prompt that asks about
`psgmgr` and never asked C41's questions.

**Code rules.** Three or more uppercase letters, so no code can be read as a frozen letter;
never DD, which the company side occupied in a series this repo cannot see (Idea-162); one
code per module, because two modules sharing a series is the G problem under a new name. A
new module is one `modules.yaml` edit — name and code together.

**What this does NOT rule, deliberately.** The edition prefix (`[<ED>-]<MODULE><n>`, base
unprefixed) that retires the DD reserve (`git-readme.md`, 2026-07-20) and the numeric band
(2026-08-18) — that needs the port relay and is the next item. The inbox shard. The Teams
Edition D2 amendment. Each is recorded when it is ruled, not here.

**Built.** PLAN1 (`feat/backlog-series-by-module`): `modules.yaml` `series:`, the allocator's
`FROZEN_SERIES` + `--next-id --module`, five guards in `test_backlog.py`, the mint rule in
CLAUDE.md and the groom-backlog skill.

## 2026-09-02 — GATE: ontology-domain-registry-and-edition-grain — SIGNED OFF 14/14 (C41)

**Prompt:** `config/gate-prompts/ontology-domain-registry-and-edition-grain.yaml` ·
**Backlog:** C41 (clause e; the item-series half was ruled the same day as PLAN1) ·
**Session:** producer desktop, in-chat walkthrough of the six sections, SME answered
the five rulings in one message; the other nine confirmations were presented as
restating prior rulings (PLAN1, the 2026-09-01 in-chat directions, I6, G87, K5) and
are recorded as confirmed-as-drafted — any of them can be reopened under C40. One
ruling (C2) carries an SME-supplied DEFINITION the prompt did not have; that
definition is the ruling of record. B5's second question ("wanted at all?") was not
answered and stays open as a rider. Nothing renumbers; no id moves.

- **§A1/§A2 — CONFIRMED.** PLAN1 is closed and not reopened; a domain partitions the
  vocabulary, an edition partitions the id space, and the two registries never share.
- **§B1 — CONFIRMED.** `config/taxonomy/domains.yaml` as data: id, title,
  vocabulary_fragment, minted_by, registered_at, authority, status/superseded_by. No
  `series` column. Seeded with the 13, each citing its real ruling; the header comment
  becomes a pointer.
- **§B2 — CONFIRMED.** A base mints, an instance requests; the company base mints its own
  domains at its own gate (per-entry row on the tom-role-vocabulary pattern); the mint
  protocol is I6's.
- **§B3 — RULED: `vocabulary_fragment` is REQUIRED.** SME: "the vocabulary should be
  required." A domain is a file/loader partition of the vocabulary and nothing else;
  the fragment-less domain the 2026-09-01 design allowed has no consumer after PLAN1
  and is not permitted.
- **§B4 — RULED: SPLIT NOW (option a).** SME: "split now." `code` and `requirements`
  become minted domains through the G87 shape (add-new + deprecate-old; no entry moves;
  `replaces:` on every re-homed entry); the `:Requirement`→`:Code` reconciliation edge
  is registered `status: planned` in the same change and ruled at its own gate; the
  spec-kit / spec-driven-development sources are registered by the reference-librarian
  BEHIND the split (REF1), not before it. Whether `test` is a third domain is NOT ruled
  and rides with ONT1's proposal.
- **§B5 — CONFIRMED as drafted; rider OPEN.** `acronyms` and `ontology` are not minted
  here and go through §B2 if ever wanted; whether either is wanted was not answered.
- **§C1 — CONFIRMED.** `[<EDITION>-]<MODULE><n>`, edition first, base unprefixed; the
  segment is optional so every existing id parses; both halves must be declared.
- **§C2 — RULED: THE GRAIN IS THE AREA PRODUCT**, with the SME's definition as the
  ruling of record: *an Area Product is where two or three applications are delivering
  on the same business topic.* That definition is what qualifies a row in
  editions.yaml — not the Product Catalog tier name by itself. Finer instances
  (per-DevTeam, per-application) were not asked for and are not provided for; if one
  is ever wanted it is a re-mint of every code and a new ruling. The Area Product list
  is still to be transcribed to a named file under `internal-local/` before CFG2
  writes real rows (the image-provenance rule); the count (~20) stays SME-REPORTED
  until then.
- **§C3 — CONFIRMED.** `config/taxonomy/editions.yaml`, Internal, synthetic sample
  producer-side, per-entry manifest row; code / title / area_product_id / minted_by /
  registered_at / authority / legacy_band. The company base is an edition and mints
  its own code at its own gate.
- **§C4 — RULED: BOTH PARTITION RULES RETIRE, forward-only.** SME: "retire both." The
  DD reserve (git-readme.md:197) and the 10000 band (PRODUCER_BAND_CEILING) govern no
  new mint; DD1–DD10, DD10001–DD10003 and G10001–G10003 stay readable and listed;
  the allocator's band check becomes an edition-segment check; the git-readme sentence
  is retired with a pointer here. The company mints nothing new until it has minted
  its edition code.
- **§D1 — RULED: AMEND ADR 0015 D2/D6.** SME: "amend for an instance-owned backlog."
  Team Edition ships a thin instance-owned backlog (items + inbox + per-instance board)
  under the copier `instance-owned` class; the base backlog stays `canonical-template`
  and frozen; `groom-backlog` ships with a mandatory `--scope`; an instance item
  carries its edition segment; `depends_on` may point instance→base, never
  base→instance.
- **§E1 — CONFIRMED.** Build items minted the same day under PLAN1, in their module
  series: CFG1 (domains.yaml), CFG2 (editions.yaml), PLAN2 (the edition segment in the
  id grammar + band-check replacement + git-readme retirement), DOC1 (the ADR 0015
  amendment text), DOC2 (RELAY-23, the port relay), REF1 (spec-kit / SDD registered),
  ONT1 (the code/requirements split + the planned reconciliation edge). C41 closes on
  the mint, per E1.
- **§F1 — CONFIRMED.** Not reopened: PLAN1, the psgmgr publish ceiling, the 13 domains'
  membership, G102, the reconciliation edge's semantics.
