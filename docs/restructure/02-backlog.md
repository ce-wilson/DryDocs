# DryDocs1 — sub-agent backlog

> **This is the human-readable view.** The machine source of truth agents pull from is
> [`backlog.yaml`](backlog.yaml); new ideas are captured in [`IDEAS.md`](IDEAS.md) and groomed
> into the yaml. Keep the two in sync (same ids). See `CLAUDE.md` §0 for the work ritual.

Work units sized for lower-cost sub-agents. Each item names: **agent**, **inputs**, **output**,
**acceptance test**, **precedence/HITL** touchpoints. The main (Opus) session dispatches and
reviews; it does not do these itself. Status: ☐ todo · ◐ in progress · ☑ done.

> Dispatch rule: give the sub-agent the item's *inputs* + *acceptance test* verbatim. Do not let
> a sub-agent cross layer boundaries (importer ≠ mapper ≠ config). Anything ambiguous → HITL gate.

---

## Epic A — Reference hygiene (agent: reference-librarian, haiku)

- **A1** ☐ Verify every path in `reference/REGISTRY.yaml` resolves (skills exist, local mirrors
  present). Fix or flag stale entries.
  *Accept:* a checklist with each entry marked ok/stale + fixes applied.
- **A2** ☐ Fill `external/orchestration/bmc-controlm/SOURCE-MANIFEST.md` gaps (version/provenance
  per doc) if any are missing.
  *Accept:* every `.md` in `bmc-controlm/` accounted for in the manifest.
- **A3** ☐ Seed `reference/research/README.md` with the 3 Neo4j blog summaries + PROV-O/SOSA
  primers as 1-line entries.
  *Accept:* table has ≥5 rows, each with a working link and a "why it matters".

## Epic B — Taxonomy capture (agent: taxonomy-importer, sonnet) — Phase 1

- **B1** ☐ Import Control-M taxonomy → `config/taxonomy/controlm.yaml` (folders ▸ jobs ▸
  conditions; variable classes) from the loader sample CSVs. Classification only.
  *Inputs:* `drydocs/data/samples/controlm_*.csv`, `config/source-registry.yaml#controlm-psgmgr`.
  *Accept:* node counts equal `m3-verify` sample expectations (8 folders, 15 jobs, 5 conditions);
  zero meaning edges in the file.
- **B2** ☐ Import SEAL taxonomy → `config/taxonomy/seal.yaml` (Application ▸ Port(kind);
  Membership ▸ Role ▸ Employee as classification).
  *Accept:* every Application has its two-port classification; no ownership semantics asserted.
- **B3** ☐ Import Catalog taxonomy → `config/taxonomy/lob-product-team.yaml`
  (LOB ▸ ProductLine ▸ Product ▸ AreaProduct ▸ DevTeam). Shape only; real rosters → `internal/`.
  *Accept:* hierarchy matches catalog samples; confidential names referenced by id, not value.
- **B4** ☐ Import Oracle-schema taxonomy *shape* → `config/taxonomy/oracle-schemas.yaml`
  (Schema ▸ Table; Script). Use placeholders for real object names (those live in `internal/`).
  *Accept:* structure present; no real schema/table/SID values committed outside `internal/`.

## Epic C — Ontology mapping + HITL (agent: ontology-mapper, sonnet) — Phase 2

- **C1** ☐ Draft `taxonomy-ontology-map.yaml` entries for `controlm.yaml` (reuse existing
  `relationship_vocabulary.yaml` active terms; mark them `confirmed` once SME agrees).
  *Accept:* each Control-M edge type traces to a matrix row or recorded alias; gate run logged.
- **C2** ☐ Same for `seal.yaml` (HAS_PORT/DPROD, HAS_MEMBERSHIP/ORG, HELD_BY).
  *Accept:* DPROD/ORG terms cited; mappings `confirmed`.
- **C3** ☐ Same for `lob-product-team.yaml`; resolve the existing `SUPPORTS` range ambiguity
  (Product vs AreaProduct) flagged in the consolidated plan (Stream E.2).
  *Accept:* no free-text union ranges; each edge has a precise from/to + authority tag.
- **C4** ☐ Reconcile all `status: planned` entries in `relationship_vocabulary.yaml` through the
  gate → `confirmed`/`rejected`. Keep the vocabulary and the map in agreement.
  *Accept:* `test_schema.py` drift guard green; map `summary:` == vocabulary active count.

## Epic D — Config-driven loaders (agent: pipeline-config + main) — Phase 3

- **D1** ☐ P0 graph fixes first (from consolidated plan): `RUNS_ON→SCHEDULED_ON` (B.1),
  `datetime()` wrapping (B.3), `stale_edge_cleanup.cypher` (B.2).
  *Accept:* migrations idempotent; `m3-verify` green; tests green.
- **D2** ☑ Wire the precedence resolver into catalog reconciliation (`RECONCILES_TO`) — read
  `config/precedence.yaml` instead of hardcoded order.
  *Accept:* flipping `order:` in `precedence.yaml` changes resolution with no code edit.
- **D3** ☑ Make `source-registry.yaml#confirmed` gate loader activation (a source with
  `confirmed: false` cannot run).
  *Accept:* attempting to load an unconfirmed source fails fast with a clear message.

## Epic E — Context graph pilot (agent: ontology-mapper + main) — Phase 4

- **E1** ☐ Register `sosa:*` terms (Observation/Sensor/Result/FeatureOfInterest/observedProperty)
  in `relationship_vocabulary.yaml` via the gate.
  *Accept:* terms present with IRIs; `status: planned`→`confirmed`.
- **E2** ☐ Build a `ControlMJobRun`→observation projection for one question: "current health +
  freshness of folder X" on sample data.
  *Accept:* one Cypher query returns latest result + resultTime per folder; documented in
  `docs/`.

## Epic F — Orchestrator expansion (agent: pipeline-config) — Phase 5

- **F1** ☐ Complete + SME-confirm the AutoSys crosswalk; set `confirmed: true`.
  *Accept:* crosswalk table fully mapped to baseline; no invented concepts; gate logged.
- **F2** ☐ Same for Airflow/MWAA.
  *Accept:* as F1.

## Epic G — Modular architecture / component topology (agent: main + ADR 0002)

Groomed 2026-06-26 from **ADR 0002** (`docs/decisions/0002-*.md`), accepted via the SME gate.
Edition = **Neo4j Enterprise** (committed). `core` extraction (G2) is the hinge — G3/G4 wait on it.
**Infra note:** the live Aura tier is capped at **1 node / 1 database**, so the multi-DB topology
is built + tested on a **local Enterprise** instance (G1); the live deploy (G7) is blocked on infra.

- **G1** ☐ P1 Author + **locally validate** the multi-DB topology (`drydocs`, `drydocs_context`,
  the `drydocs_all` composite + `assetId`/`jobId` proxy-node constraints) on a local Neo4j
  **Enterprise** (Docker, free dev license).
  *Accept:* the three DBs + composite exist locally; constraints in both data DBs; a `drydocs_all`
  smoke query reads both and writes neither; scripts are target-agnostic.
- **G2** ☐ P1 Extract `drydocs-core` from `drydocs/` per **0002-A** (thin, zero behavior change);
  remainder becomes `drydocs-load`.
  *Accept:* core imports with no component dep; load runs unchanged; `test_module_boundary.py`
  passes; gates green. **Blocks G3 + G4.**
- **G3** ☐ P2 Rebase the archived `controlm-spinoff` onto `drydocs-core` as `drydocs-remediation`
  per **0002-B**.
  *Accept:* detect→transform→prove→Jira on core only; no-graph-write + Jira-only + equivalence
  tests pass. (depends: G2)
- **G4** ☐ P3 Scaffold `drydocs-lineage` + `drydocs-deepdoc` as separate packages sharing the core
  parser; deepdoc → `drydocs_context` with `reliability`/`trust`.
  *Accept:* both import only core, neither imports the other; boundary test passes. (depends: G1, G2)
- **G5** ☐ P2 Document the promotion path `drydocs_context → HITL gate → drydocs` in
  `03-hitl-sme-flow.md` (gate-confirmed write, never a cross-DB edit).
  *Accept:* the promotion section exists with the decision presentation + audit requirement.
- **G6** ☐ P3 Add a durable "considered & rejected" pointer (Community single-DB, two-mode
  capability, polyrepo) from the architecture entry point so alternatives aren't re-litigated.
  *Accept:* the three rejected options are discoverable outside the ADR.
- **G7** 🚧 P2 *blocked* — Deploy the G1 topology to the **live** multi-DB target.
  *Blocked on:* the current Aura tier is capped at **1 node / 1 database**; needs a multi-DB-capable
  Enterprise instance (Aura VDC / Business Critical, or self-managed Enterprise). (depends: G1)

## Epic H — `drydocs-review` back-flow (main)

**REVERSE of the normal port.** Reproduce the company-authored generic SME-review / HITL toolkit
generically in this public producer (re-implement from screenshots/descriptions, never copy company
code). Full plan: [`05-drydocs-review-backflow.md`](05-drydocs-review-backflow.md).

- **H1** ☐ P2 Reproduce `graph_verify` + `review_labels` (the offline spine).
  *Accept:* `review_labels` typed accessor over a sanitized `review-labels.yaml` (vendor-bmc seed);
  `graph_verify` loads YAML `TC-*` suites, evaluate pure/offline, unit-tested; classification set;
  Track-1 green.
- **H2** ☐ P2 Reproduce `graph_review` (pure HTML renderer, no Neo4j in module).
  *Accept:* renders a fixture row set offline, `hidden_props` stripped, one section per DATA label. (depends: H1)
- **H3** ☐ P3 Reproduce `sme_notes` harvester (routes `$FR/$UC/$OQ/$NOTES`; synthetic SIDs only).
  *Accept:* unit test on a fixture tree; no real SIDs committed. (depends: H1)
- **H4** ☐ P3 Reproduce the HITL prompt-page **generator** (renderer over
  `04-sme-checklist-and-load-plan.md` + `taxonomy-ontology-map.yaml` + `classification.yaml`).
  *Accept:* emits interactive checklist pages (localStorage, no-write-until-confirmed, parent+child);
  example seeded from vendor-bmc. (depends: H1, H2)
- **H5** ☐ P3 Reproduce `drydocs/publishing/` with the Confluence push abstracted behind a pluggable publisher.
  *Accept:* assembler/validator/preview + local preview test; no `toby_publish_confluence`, no space coords. (depends: H4)
- **H6** ☐ P2 Close the boundary-guard blind spot: add a `review` `COMPONENT_GROUP` +
  flip `test_module_boundary.py` to **default-deny** (every module must classify).
  *Accept:* default-deny test passes on producer today (only `drydocs/__init__.py` exempt); Track-1 green.
  (depends: H1; default-deny half landable now)
- **H7** ✅ P3 *done 2026-07-01* — Document the **Canonical-COMPANY** back-flow reconciliation direction
  in `git-readme.md`, `port-prompt.md`, and the `reconcile-port` divergence ledger.

---

## Review checklist for the dispatcher (run after each item)
1. Did the sub-agent stay in its layer? (importer wrote no edges; mapper wrote no graph; config
   wrote no graph.)
2. Did anything confidential land outside `internal/`? (`PUBLISH-BOUNDARY.md` grep.)
3. Did ambiguous decisions go through the HITL gate, not get auto-decided?
4. Tests: `poetry run pytest -q`, `python -c "import drydocs.cli"`, `drydocs --help`.
