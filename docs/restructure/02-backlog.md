# DryDocs1 — sub-agent backlog

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
- **D2** ☐ Wire the precedence resolver into catalog reconciliation (`RECONCILES_TO`) — read
  `config/precedence.yaml` instead of hardcoded order.
  *Accept:* flipping `order:` in `precedence.yaml` changes resolution with no code edit.
- **D3** ☐ Make `source-registry.yaml#confirmed` gate loader activation (a source with
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

---

## Review checklist for the dispatcher (run after each item)
1. Did the sub-agent stay in its layer? (importer wrote no edges; mapper wrote no graph; config
   wrote no graph.)
2. Did anything confidential land outside `internal/`? (`PUBLISH-BOUNDARY.md` grep.)
3. Did ambiguous decisions go through the HITL gate, not get auto-decided?
4. Tests: `poetry run pytest -q`, `python -c "import drydocs.cli"`, `drydocs --help`.
