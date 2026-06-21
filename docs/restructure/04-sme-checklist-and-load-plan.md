# SME checklist + sequential load plan

**Date:** 2026-06-21. Written after D1 (P0 graph fixes). The D1 caveat: `m3-verify` and any
real load need a **live Neo4j + APOC** (and production ingest needs **Oracle**), which aren't
available to the autonomous agent. This doc separates **what can proceed without you/data** from
**what needs you (SME), a live DB, or new data**, and gives the **order to load** the graph.

---

## A. Can proceed now — no SME input, no new data, no live DB

These are code/config/doc tasks, unit-testable offline (text/Python tests, no Neo4j):

| Item | What | Why it's autonomous |
|------|------|---------------------|
| **D2** | Precedence resolver: a small Python module that reads `config/precedence.yaml`; wire it into the catalog `RECONCILES_TO` step so flipping `order:` changes resolution with no code edit. | Pure Python + unit test (`pytest`); no graph write needed to prove the resolver. |
| **D3** | Confirmed-gating: a loader/CLI guard that refuses to run a source whose `source-registry.yaml#confirmed` is `false` (fails fast with a clear message). | Pure Python + unit test; no graph needed. |
| **E1 (draft only)** | Draft the `sosa:*` terms (Observation/Sensor/Result/FeatureOfInterest/observedProperty) into `relationship_vocabulary.yaml` as `status: planned` + a supplement block. | Writing is autonomous; the drift guard ignores `planned`. **Confirmation is SME (→ B3).** |
| **F1/F2 (draft only)** | Flesh out the AutoSys & Airflow native→baseline crosswalk tables. | Drafting is autonomous. **Confirmation + activation need SME + data (→ B3/B4).** |
| Hygiene | Add a unit test asserting the `datetime(replace(...))` CASE guards exist; fix the stale `apply-m3-supplement` reference in `RELATIONSHIP_GUIDE.md`; prune old-format `depgraph.*.json` baselines. | Doc/test only. |

> **Recommended next autonomous step: D2 then D3** — they finish Epic D's config-driven loaders
> and are fully testable offline. Say the word and I'll do them.

---

## B. SME checklist — needs you, a live DB, or new data

### B1 · Verify D1 + stand up the graph (live Neo4j + APOC)
- [ ] `poetry install`; copy `.env.example` → `.env`, set `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD`.
- [ ] `poetry run drydocs check` — confirms connectivity + **APOC present**.
- [ ] **Existing graph only:** run `drydocs/loaders/cypher/migrate_runs_on_to_scheduled_on.cypher` **once**
      (idempotent; renames `RUNS_ON` → `SCHEDULED_ON`).
- [ ] `poetry run drydocs m3-verify` — confirm **"every folder has a server"** now passes
      (this is the D1 fix; the loader now writes `SCHEDULED_ON`, which m3-verify expects).

### B2 · Oracle / data (production ingest)
- [ ] **Oracle preflight** (consolidated-plan A.0): Q0.1 `TABLE_ID` collision across DCs · Q0.2 `MEMLIB`/`OVERLIB`
      exist · Q1 real variable-source object name · Q2 `CAPTURE_DATE` per-row vs per-snapshot · Q3 `CREATION_USER`/`CHANGE_USERID` exist.
- [ ] **Confirm Oracle timestamp format** for the `datetime()` wrapping. The sample is `YYYY-MM-DD HH:MM:SS`
      (handled by `replace(' ','T')`); if production differs, adjust. `version_timestamp` is left a **string**
      (compact `YYYYMMDDHHMMSS`, not ISO) — confirm that's acceptable or supply a parser.
- [ ] **Regenerate the Control-M sample from psgmgr** — resolves the count drift (docs said 15 jobs/5 conditions;
      bundled sample has 13/15, and 2 active folders `161020`/`160501` are jobless → `m3-verify empty=2`).

### B3 · HITL gate confirmations (ontology decisions — `docs/restructure/03-hitl-sme-flow.md`)
- [ ] **E1:** confirm the `sosa:*` terms before any context-graph label is written.
- [ ] **AreaProduct:** confirm whether the `Product ▸ AreaProduct ▸ DevTeam` layer applies, or the sample's
      direct `Product ▸ DevTeam` is canonical (open question from B3/C3).
- [ ] **F1:** confirm the AutoSys crosswalk; **F2:** the Airflow/MWAA crosswalk (native object → BMC baseline).

### B4 · Provide data / access to activate placeholders
- [ ] AutoSys export + adapter details → set `source-registry.yaml#autosys-export.confirmed: true`.
- [ ] Airflow/MWAA DAG export details → `airflow-mwaa.confirmed: true`.
- [ ] Oracle schema access (real names → `internal/schemas/`) → activates B4 oracle-schemas + DataAsset.
- [ ] Snowflake (future).

---

## C. Sequential load plan (runbook)

Order to stand up or refresh the graph. Sample mode needs no Oracle; production adds the gated steps.

```
Phase 0 · Prereqs
  poetry install ; .env set ; Neo4j 5.x + APOC
  poetry run drydocs check                      # connectivity + APOC

Phase 1 · Bootstrap (schema backbone)
  poetry run drydocs bootstrap                  # constraints.cypher + ontology.cypher

Phase 2 · Ontology supplements (order matters)
  poetry run drydocs apply-ontology-supplement  # Control-M anchor terms
  poetry run drydocs apply-seal-supplement      # SEAL / BusinessApplication terms
  poetry run drydocs apply-catalog-supplement   # Catalog/PAT terms + all Role seeds
                                                #   (now includes SUPPORTS→AreaProduct + DEVELOPS, C4)

Phase 3 · Migration (EXISTING graphs only — skip on a fresh DB)
  run migrate_runs_on_to_scheduled_on.cypher    # one-time, idempotent (D1/B.1)

Phase 4 · Load reference data
  poetry run drydocs refresh-reference          # catalog + SEAL + dev-teams (+ snapshots)

Phase 5 · Load Control-M structural lineage
  poetry run drydocs ingest-controlm            # folders → jobs → conditions in/out → derived deps
  #   --use-oracle --folder "<LIKE>"  for production (gated on B2 preflight)

Phase 6 · Verify invariants
  poetry run drydocs m1-verify
  poetry run drydocs m3-verify                  # expect SCHEDULED_ON links; note empty=2 until B2 sample fix

Phase 7 · (Optional) embeddings / GraphRAG
  scripts/embed.sh                              # vector pass (separate from bulk MERGE; finding T7)
```

### Gates inside the load plan
- **Confirmed-gate (D3, once built):** a source with `source-registry.yaml#confirmed: false`
  (autosys, airflow, oracle-schemas, snowflake) **will not load** — activate via B4.
- **Mapping-gate (HITL):** only `confirmed` taxonomy→ontology mappings are applied. Confirmed today:
  **C1–C4** (Control-M, BusinessApplication, LOB→Product→Team incl. SUPPORTS→AreaProduct + DEVELOPS).
  Pending: **E1** (SOSA), **F1/F2** (orchestrators) — see B3.
- **Precedence (D2, once built):** when sources conflict, resolve `bmc-baseline → internal-standards →
  lob-product-team` from `config/precedence.yaml`.

### Production go-live order (summary)
1. B2 Oracle preflight answered → 2. fresh sample regenerated → 3. Phases 1–2 →
4. Phase 3 migration (if existing graph) → 5. `ingest-controlm --use-oracle` (scoped) →
6. m1/m3-verify green → 7. confirm pending gates (E1/F) as data lands.
