# Technical Design — DryDocs (the platform: layers, components, governance, and the graph)

<!-- anchor: front-matter -->
**Status:** DESCRIPTIVE — documents the built system as of **Rev 2, 2026-07-12** (Rev 1 +
expanded module topology + C4-model views), authored at commit `ac2ea2e` (post G2 core
extraction, G3 remediation component, G4 scaffolds, G9 lineage re-home). ·
**Classification:** Internal-Public — mechanism only; real folder/job/host/SEAL values live
company-side or in gitignored twins. ·
**Audience:** engineers joining the project (any surface), and the company-side maintainer
reconciling ports. ·
**Companion:** `CLAUDE.md` (the operating guide this design formalizes);
`docs/design/controlm-ingestion-tdd.md` (the ingestion pipeline in depth);
`docs/design/drydocs-remediation-tdd.md` (the C1 component); `MODULE_MAP.md` + ADR 0002
family (component topology); `docs/whitepaper/drydocs-whitepaper.md` (the external framing).

Worked example throughout (the sanitized sample family already committed in
`config/taxonomy/controlm.yaml`): folders `PRARAG-HLDM-70011-PEX-TRUST-{DLY,CYC}` on server
`P32`, their jobs, conditions, and the `ARA` application grouping.

> **Read-me-first.** DryDocs is a *governance machine that happens to load a graph*, not a
> graph with governance bolted on. Every section below reduces to one pattern: a
> machine-readable ledger, a test that fails on drift, and a human gate wherever meaning is
> assigned. When extending the system, find the ledger first.

---

<!-- anchor: purpose-scope -->
## Purpose & scope

**Purpose.** Specify the DryDocs platform end-to-end: the four-layer model, the
configuration ledgers, the HITL gate, the loader/provenance contract, the component
topology, verification, and the two-repository operating model — the design a new
contributor must hold to work on any part safely.

**In scope.**
- The four layers and their enforced separation (taxonomy → ontology → graph → context).
- The config layer as the system of record: registries, classifications, dispositions,
  precedence, crosswalks, the port manifest.
- The ontology contract: vocabulary, PROV decision matrix, mapping lifecycle, gates.
- The load contract: BaseLoader provenance (delta diet), audit envelope, verify suites.
- Component topology (post ADR 0002 Phase B) and its boundary guard.
- The producer→consumer port model.

**Out of scope** (delegated): column-level Control-M ingestion detail
(`controlm-ingestion-tdd.md`); the remediation loop (`drydocs-remediation-tdd.md`); the web
console (Epic O, design in flight); company-side wiring (Confluence, Kerberos config, real
gate specs — consumer-canonical by the port manifest).

<!-- anchor: context-frame -->
## Where this sits — the four-layer frame

This TDD covers the *whole frame* rather than one layer:

| Layer | Answers | System of record | Guard |
|---|---|---|---|
| 1 Taxonomy | what category | `config/taxonomy/*.yaml` | importers classify only — no meaning edges |
| 2 Ontology | what edges mean | `drydocs_core/ontology/relationship_vocabulary.yaml` + `config/taxonomy-ontology-map.yaml` | `test_schema.py`, `test_taxonomy_ontology_map.py`, the HITL gate |
| 3 Knowledge graph | what is connected & what it means | Neo4j (`drydocs` DB; EE container) | `graph-tests/*.yaml` acceptance, `m3-verify` |
| 4 Context graph | what matters now | planned projections (SOSA runs, timing, windows) | gate E1 pending; phase 13 |

Upstream neighbours: the orchestrator replica (read-only `CM_` schema), org/app registries
(SEAL, PAT), vendor/standards corpora. Downstream consumers: review & verify toolkit,
generated documents (docgen), lineage/deepdoc passes, the remediation component, the future
web console.

<!-- anchor: definitions -->
## Definitions, acronyms & references

- **CM_ replica** — read-only copy of the orchestrator's runtime DB in an Oracle schema;
  the canonical structural source. **Baseline** = the vendor's own physical model semantics.
- **HITL gate** — the SME sign-off step (`docs/restructure/03-hitl-sme-flow.md`): rendered
  gate page → recorded decision in `config/gate-log.md` (append-only) → statuses flip.
- **Ledger** — a machine-readable config file with a guarding test (the house pattern).
- **SEAL / PAT** — internal application registry / product-and-team catalog (values
  confidential; mechanism public).
- **Trust tiers** — VERBATIM / GROUNDED / SYNTHESIZED epistemic provenance per corpus
  (`SOURCE-MANIFEST` convention); orthogonal to sensitivity.
- **Standards** — PROV-O (provenance), W3C ORG (organizations), DPROD/DCAT (data products),
  SKOS (concept schemes), SOSA/SSN (observations; experimental adoption).
  Index: `reference/standards/`.
- **ADRs** — 0001 ontology base scope; 0002(+a/b/c) component & database topology, core
  extraction, remediation rebase, lineage re-home; 0003 label rename; 0004 software
  registry. `docs/decisions/`.
- **Port** — producer→company apply across disjoint git histories; dispositions in
  `PORT-MANIFEST.yaml`.

<!-- anchor: design-summary -->
## Design summary

```
 sources ──► config ledgers ──► taxonomy ──► ontology map ──► HITL GATE
 (replica,    (registry,         (capture)    (vocabulary +     (SME; gate-log)
  registries,  classification,                 PROV matrix)          │ confirmed
  corpora)     dispositions)                                         ▼
                                                            loaders (MATCH/MERGE,
                                                            delta provenance,
                                                            audit envelope)
                                                                     ▼
                                                            Neo4j knowledge graph
                                                                     ▼
                              review/verify · docgen · plan · lineage · remediation
```

A source becomes graph content only by traversing every stage left-to-right; each stage has
a ledger and a test, and the one stage that assigns *meaning* has a human. Components
surround the graph and import a slim core; only loaders write ground truth, only the
lineage writer will write curated lineage (gate-bound), and remediation writes nothing.

<!-- anchor: detailed-design -->
## Detailed design

**1. Config layer — the system of record.**
`config/source-registry.yaml` declares every source (kind, orchestrator, adapter,
`confirmed:` gate, structured `locator:` — application → platform → service → schema →
mapping); loads fail closed on unconfirmed sources. `config/classification.yaml` defines the
four sensitivity tiers; every source must carry one. `config/source-mappings/<source>.yaml`
is the column ledger: one disposition per profiled column
(projected / filter-only / excluded+reason / deferred) with staging-vs-graph targets.
`config/precedence.yaml` resolves inter-source disagreement (baseline → internal standards →
org catalog). `config/crosswalks/` normalizes future orchestrators to the baseline.
`PORT-MANIFEST.yaml` (root) carries cross-repo dispositions. Each file: schema id + guard
test.

**2. Taxonomy capture.** Importers write pure classification into `config/taxonomy/`
(servers/folders/jobs/conditions, business apps, LOB→Product→Team, software registry,
platforms). Rule: no relationship types at import time — a capture that needs an edge is an
ontology question and stops.

**3. Ontology contract.** `relationship_vocabulary.yaml` holds node classifications
(each label → a standards CURIE + PROV behavioural type) and the relationship registry
(lifecycle planned → active → deprecated; every active entry must have its supplement block —
drift-guarded). New edges are chosen via the 9-row PROV decision matrix, then proposed in
`config/taxonomy-ontology-map.yaml` (lifecycle proposed → confirmed → applied, computed
summary, `vocab_id` referential check, map↔vocabulary label agreement — all test-enforced).
Confirmation happens only at a gate; the gate log is append-only audit.

**4. Load contract.** Loaders (component `drydocs-load`) read extracts (scope-bound,
read-only SQL against the replica), map rows through pydantic models, and MERGE per the
confirmed mapping. Provenance: every run is a `:JobRun` activity; `WAS_GENERATED_BY` edges
are **delta-only** (per-row `row_checksum`; edge on create/content-change only — the
supernode diet), while pull provenance stays node properties (`last_seen_at`, `last_run_id`)
and run totals live on the `:JobRun`. Source authorship rides the gate-approved audit
envelope (`source_created_by/_at`, `source_updated_by/_at` per `config/audit-fields.yaml`).
Supplements (software registry, SOSA experimental, future timing stats) are opt-in passes
that MATCH existing nodes and never MERGE identity.

<!-- anchor: design-data-mapping -->
### Source → column-level field mapping

N/A at this altitude — the per-column dispositions are the ledgers themselves
(`config/source-mappings/controlm-psgmgr.yaml`) and the pipeline TDD
(`controlm-ingestion-tdd.md` §4) renders the field→node/edge map; duplicating either here
would create a third copy to drift.

**5. Component topology (ADR 0002, executed).** One slim core, eight components, one
enforced rule set: *core imports no component; components import only core; every module
classifies into exactly one bucket or the build fails* (default-deny,
`test_module_boundary.py`); `cli.py` is the exempted composition root. Note the codename
collision up front: the project's component codenames **C1–C3** (remediation, lineage,
deepdoc) are unrelated to the **C4 model's** levels 1–4 used in the appendix diagrams.

| Package / module | Codename | Role | Writes | Notes / guards |
|---|---|---|---|---|
| `drydocs_core` | — | typed row models; adapters (csv, oracle); Neo4j client; config accessors (registry, precedence, classification); ontology vocabulary + namespaces; the **shared Control-M parser** (`commands`/`paths`/`variables`/`resolver`/`staging`) | nothing | imports no component; lineage and deepdoc wrap its parser (an AST guard proves lineage carries no parse code of its own) |
| `drydocs-load` (`drydocs/loaders/**` + `cli.py`) | main | SQL extracts → models → MERGE per confirmed mappings; delta provenance; the CLI | `drydocs` DB (sole ground-truth writer) | J9 testcontainers e2e; graph-tests acceptance |
| `drydocs-review` | — | `graph_review`/`graph_verify`, `review_labels`, `source_mappings` accessor, `gate_pages`, `sme_notes`, `publishing/` | HTML / Confluence artifacts | consumer-canonical wiring (port manifest); gate-page format test-enforced |
| `drydocs-plan` | — | `plan_board` — backlog.yaml → board render | `docs/plan/board.html` | pure/offline; own boundary bucket |
| `drydocs-docgen` | — | `doc_outline` validator, `design_doc` deterministic renderer, `doc_pdf`, markup transcription | `docs/design/*` renders, PDFs | outline auto-discovery test covers every committed TDD |
| `drydocs_lineage` | **C2** | extractors (Control-M inventory) → `LineageGraph` candidates; curated-write boundary | curated lineage only — **gate-bound** (writer refuses until the rel vocabulary confirms) | G9 re-home; candidates never ground truth |
| `drydocs_deepdoc` | **C3** | on-demand deep-dive passes (scaffold) | `drydocs_context` (future) | G4 scaffold |
| `drydocs_remediation` | **C1** | detect → classify → transform → prove → package | **Jira packages only** — no graph, no production | separation of duties is structural (ADR 0002-B) |
| `drydocs-web` | — | JS/TS console + graph viz (design in flight, Epic O) | — | not a Python package; outside the boundary guard by design |

The import direction is the architecture (this is also the C4 Level-3 view):

```
                        ┌────────────────────────────┐
                        │        drydocs_core        │
                        │ models · adapters · config │
                        │ ontology · Control-M parser│
                        └──────────────▲─────────────┘
          imports core only ──────────┤ (core imports NO component)
   ┌──────────┬──────────┬────────────┼───────────┬──────────┬─────────────┐
   │          │          │            │           │          │             │
 load      review      plan        docgen     lineage(C2) deepdoc(C3) remediation(C1)
   │                                                                       │
   └── cli.py = composition root (ENTRYPOINT exemption: may wire any) ─────┘
        components NEVER import each other · default-deny classification
```

**6. Two-repository operating model.** Producer (public, sanitized mechanism) → company
(private, wired) across disjoint histories; applies are cherry-picks/checkouts driven by
`PORT-MANIFEST.yaml` dispositions (clean-add / canonical-producer / canonical-company /
union-append / per-entry / evaluate / never-port), with `git-readme.md` and
`docs/port-prompt.md` as narrative. Back-flow is re-derived mechanism only, never values.

<!-- anchor: classification-security -->
## Classification & security

The repo is private-but-sometimes-published. Tiers: External / Internal-Public (publishable)
vs Internal / Internal-Confidential (excluded; `internal/` twins + gitignored
`internal-local/`). Enforced by `test_classification.py` (every source classified),
`test_publishing.py` (publish pipeline validation), root-image/`internal-local/` gitignore
safety nets, and CI (J5) running the guards on every push. Mechanism-not-instance is the
writing rule: object/column names are public vocabulary; SIDs, hosts, folder names, service
names, and rosters never leave the internal side. Secrets: architecture-level only; external
auth (Kerberos) config lives in the consumer's environment, never in git.

<!-- anchor: qa-tests -->
## QA & tests

- **Unit suite** (~590 tests, CI-gated): model/parser behavior, every config ledger's guard,
  renderer determinism, boundary default-deny.
- **End-to-end** (J9): testcontainers Neo4j load proving the CSV→graph path (found 2 real
  bugs on introduction).
- **Graph acceptance**: `graph-tests/*.yaml` invariant suites (`graph-verify` runner) — e.g.
  the provenance-diet invariants (a zero-change refresh writes zero provenance edges).
- **CLI smoke**: `import drydocs.cli` + `drydocs --help` + `m3-verify` against the sample.
- **Renders**: board/design HTML are deterministic; the session ritual's stale-render check
  (`git diff --quiet` after re-render) catches uncommitted drift.
- **Port acceptance**: Track-1 portable suite (no data files; skips, never fails, without
  samples) + Track-2 with the bundled sample's exact counts.

<!-- anchor: hitl-gate -->
## HITL gate & open questions

Every edge-meaning, reclass, or match-policy decision routes through the gate; prepared
pages carry numbered confirmations, provenance blocks, and options with a recommendation;
outcomes transcribe to `config/gate-log.md`; only then do lifecycle statuses flip
(vocabulary stays `planned` until a loader exists — `active` requires the supplement block).
Signed to date: Control-M Q1–Q3, software registry, bmc-docs lexical load, CM_HOSTS host
topology, K3 BusinessApplication entity reshape (apply = K4). Awaiting SME: E1 SOSA
jobrun-observation, F1/F2 orchestrator crosswalks, K2 SEAL match policy, plan-07 invocation
patterns, CM_AVG_RUN timing supplement (P2). Open questions live in the gate specs and the
backlog — never resolved silently.

<!-- anchor: traceability-matrix -->
## Requirements traceability matrix

| Requirement / capability | Design section | Component / ledger | Test / verify | Status |
|---|---|---|---|---|
| Four-layer separation; no meaning at import | context-frame | `config/taxonomy/` + importer rule | tests/unit/test_schema.py (vocab↔supplement drift) | active |
| Loads fail closed on unregistered/unconfirmed sources | detailed-design | `config/source-registry.yaml` | tests/unit/test_source_registry.py | active |
| Every source carries a sensitivity classification | classification-security | `config/classification.yaml` | tests/unit/test_classification.py | active |
| No edge loads before SME confirmation | hitl-gate | `config/taxonomy-ontology-map.yaml` | tests/unit/test_taxonomy_ontology_map.py | active |
| Per-column source dispositions | detailed-design | `config/source-mappings/` | tests/unit/test_source_mappings.py | active |
| Delta-only run provenance (no `:JobRun` supernode) | detailed-design | loaders `base.py` (`row_checksum`) | tests/unit/test_row_checksum.py + graph-tests/provenance-diet.yaml | active |
| Source audit envelope (authorship properties) | detailed-design | `config/audit-fields.yaml` | tests/unit/test_audit_fields.py | active |
| Component boundary, default-deny | detailed-design | `MODULE_MAP.md` | tests/unit/test_module_boundary.py | active |
| Cross-repo port dispositions machine-readable | detailed-design | `PORT-MANIFEST.yaml` | tests/unit/test_port_manifest.py | active |
| Backlog roll-ups are computed views | qa-tests | `docs/restructure/backlog.yaml` | tests/unit/test_backlog.py | active |
| CSV→graph load proven end-to-end | qa-tests | `drydocs-load` | tests/unit (J9 testcontainers e2e) | active |
| Design docs conform to canonical outlines | design-summary | `drydocs-docgen` outlines | tests/unit/test_doc_outline.py | active |

<!-- anchor: decisions-discussions -->
## Decisions & discussions

ADR 0001 (PROV spine as ontology base) · ADR 0002 + a/b/c (component/database topology; core
extraction — executed; remediation rebase — executed; lineage re-home — in flight, G9) ·
ADR 0003 (`JobFolder`→`ControlMFolder`) · ADR 0004 (software registry, vendor = brand only).
Live discussions ride the backlog and gate specs; the recurring architectural theme —
guarded surfaces stay clean, unguarded surfaces cause incidents — is documented in
`docs/reviews/tech-debt-*.md`.

<!-- anchor: appendices -->
## Appendices

### Appendix A — C4-model views (Levels 1–4)

*(C4 model = Context / Container / Component / Code — unrelated to the component codenames
C1–C3 above. ASCII on purpose: the renderer is deterministic and JS-free, so these render
identically in repo, print/PDF, and hosted views.)*

**Level 1 — System context.** Who uses DryDocs and what it touches.

```
  Production-support SME            Source-app dev teams
  (gate sign-off, queries,          (receive fix packages;
   doc annotation)                   hold deploy rights)
        │                                  ▲
        ▼                                  │ Jira handoff
 ┌───────────────────────────────────────────────────────┐
 │                       DryDocs                         │
 │   governed knowledge graph for batch production       │
 │   support: ingest → gate → load → answer → repair     │
 └───────────────────────────────────────────────────────┘
    │ read-only        │ read           │ publish        │ port (one-way)
    ▼                  ▼                ▼                ▼
 Orchestrator DB    Org/app         Confluence /     Company repo
 replica (CM_       registries      generated docs   (consumer; real
 schema, Oracle)    (SEAL, PAT)                      wiring + data)
```

**Level 2 — Containers.** Runnable things and stores.

```
 ┌─ Python monorepo (this repo) ───────────────────────────────┐
 │  drydocs_core + 8 components (§5) · pytest + CI gates (J5)  │
 └───────────────┬─────────────────────────────┬───────────────┘
                 │ bolt                        │ writes files
                 ▼                             ▼
 ┌─ Neo4j EE container ─────────┐   ┌─ Repo doc surfaces ───────┐
 │  drydocs         (ground     │   │  docs/design/* renders    │
 │                   truth)     │   │  docs/plan/board.html     │
 │  drydocs_docs    (lexical    │   │  gate pages (rendered to  │
 │                   corpus)    │   │  internal-local/)         │
 │  drydocs_context (future)    │   └───────────────────────────┘
 └──────────────────────────────┘
 ┌─ Config ledgers (git) ──────────────────────────────────────┐
 │  source-registry · classification · source-mappings ·       │
 │  taxonomy-ontology-map · precedence · PORT-MANIFEST         │
 └──────────────────────────────────────────────────────────────┘
```

**Level 3 — Components.** The import-direction diagram in §5 *is* the L3 view.

**Level 4 — Code (exemplar: the load/provenance path).** The pattern every loader follows —
chosen because it carries the two hardest guarantees (fail-closed config, delta provenance):

```
 cli.py: ingest-controlm
   └► FoldersLoader(BaseLoader).run()
        ├─ source_registry.require_confirmed(source)      # fail closed
        ├─ adapter.fetch(sql, scope_binds)                # read-only extract
        ├─ Model.model_validate(row)  → to_params()
        │     └─ compute_row_checksum(row, exclude=volatile)   # sha256
        ├─ cypher template per row:
        │     MERGE (n:Label {key…}) SET n += props
        │     FOREACH (CASE row_checksum changed-or-new →
        │        MERGE (n)-[:WAS_GENERATED_BY]->(run))    # delta diet
        │     SET n.row_checksum, n.last_seen_at, n.last_run_id
        └─ _close_run(): (:JobRun) rows_processed / rows_rejected;
              rows_changed = count(WAS_GENERATED_BY to this run)   # exact
```

### Appendix B — Component ↔ write-target summary

`drydocs-load` → `drydocs` DB (sole ground-truth writer); `drydocs_lineage` → curated
lineage only, gate-bound (writer stubbed until the vocabulary gate); `drydocs-review` →
HTML/Confluence artifacts; `drydocs-docgen` → `docs/design/*` renders; `drydocs-plan` →
`docs/plan/board.html`; `drydocs_remediation` → Jira packages only; `drydocs_deepdoc` →
(future) `drydocs_context`.
