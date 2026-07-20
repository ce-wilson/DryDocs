# Review — documentation & knowledge ingestion (external + internal)

**Date:** 2026-07-06
**Classification:** Internal-Public (design prose, no confidential identifiers)
**Scope:** how documentation/knowledge is currently ingested, tracked, mapped to source,
and kept current — and whether document ingestion needs its own module(s), loading into a
**software knowledge graph** (confirmed vendor/platform sources) and a **context knowledge
graph** (SME/business-application context).
**Companion capture:** the four-tier ingestion to-dos are in `docs/restructure/IDEAS.md`
(2026-07-06 entries) awaiting grooming into `backlog.yaml`.

---

## 1. The four ingestion tiers (target state)

| Tier | Content | Sensitivity (config/classification.yaml) | Graph target |
|------|---------|------------------------------------------|--------------|
| **T1** | Vendor/platform docs — Neo4j, Oracle, BMC, AWS, etc. (supports DryDocs itself *and* the data pipeline) | External | software KG |
| **T2** | Internal guidance for those same platforms (naming standards, conventions, config rules) | Internal-Public / Internal | software KG (SME-confirmed) |
| **T3** | Internal guidance on products, agile methods, internal software | Internal / Internal-Public | software KG (SME-confirmed) |
| **T4** | SME context correlated to business applications — SharePoint, Confluence, MS Teams, email | Internal-Confidential | context KG |

The tiers ascend in sensitivity and descend in verifiability: T1 is citable to a public URL;
T4 is tribal knowledge that only an SME can confirm. That gradient is exactly the **trust
axis** ADR 0002 already maps onto the database boundary — so the two-graph split the tiers
imply is not new architecture, it is the existing topology applied to documents.

---

## 2. Current state — what exists today

### 2.1 The corpora

- **T1 external vendor docs.** `external/orchestration/bmc-controlm/` is the mature example:
  23 curated markdown files + `SOURCE-MANIFEST.md`. `reference/` holds Tier-1 platform and
  standards material (Neo4j, PROV-O, ORG, DPROD, SOSA/SSN, DCAT, SKOS) indexed by
  `reference/REGISTRY.yaml`. AutoSys and Airflow are placeholders. Neo4j and Oracle depth
  comes from plugin skills plus local mirrors (`../llm-graph-builder`, `../sdw-sosa-ssn`)
  rather than in-repo files. **AWS has no corpus yet.**
- **T2 internal platform guidance.** `knowledge/standards/{technology,business,data}/` — the
  *conformance* corpus, deliberately kept separate from the vendor *capability* corpus so the
  two-stage validation (vendor legality → internal conformance) stays clean. Each standard
  carries YAML frontmatter binding it to a `taxonomy_path`, the element it `governs`, its
  precedence `authority`, and `applies_to_source`. This is the best-structured internal
  corpus in the repo.
- **T3 product/process guidance.** `docs/Product/`, `SDLC-Docs/`, `docs/reviews/sdlc-*.md`.
  Partially managed: the SDLC docs went through a checkpointed persona plan (now superseded,
  findings rolled into ADRs), but `docs/Product` and assorted root-level files (PDFs, PNGs)
  have no manifest, no classification stamp, no index.
- **T4 SME/business-application context.** Not yet ingested as documents. SME knowledge
  enters today only through the HITL gate (`config/gate-log.md`, curated notes via
  `sme_notes.py`) — decision-by-decision, not corpus-scale.

### 2.2 How sources are tracked (the three axes)

Tracking is genuinely mature — three independent axes, each with a home and an enforcing test:

1. **Sensitivity** — `config/classification.yaml`, required on every registered source,
   enforced by `tests/unit/test_classification.py`; drives the publish boundary
   (`PUBLISH-BOUNDARY.md`). External sources must carry `source_url` + `captured_at`.
2. **Trust/provenance** — VERBATIM / GROUNDED / SYNTHESIZED, decided at ingestion, recorded
   per corpus in `SOURCE-MANIFEST.md`. The BMC manifest is the reference implementation:
   per-file provenance blocks, default tier rules, explicit hazard callouts (e.g. the
   JSON-API files demoted to conceptual-only for the XML environment).
3. **Precedence** — `config/precedence.yaml` (BMC baseline → internal standards →
   LOB→Product→Team), consumed by loaders via config, never hardcoded.

**Gap:** these axes govern *data-pipeline* sources (`config/source-registry.yaml`) and the
one BMC corpus. Document sources as a class have no registry — `source-registry.yaml`
registers Oracle views and CSV extracts, not documents; `REGISTRY.yaml` registers platforms,
not individual docs; only BMC has a SOURCE-MANIFEST. T2/T3 corpora are tracked by
convention, not by schema.

### 2.3 How docs are kept current

- `REGISTRY.yaml` carries a `verified:` date; backlog **A1** (audit registry staleness) and
  **A2** (account for every BMC doc in the manifest) exist as manual audits.
- Each scraped BMC file records URL + `Date Scraped` (2026-06-11); the manifest records
  version caveats (SaaS source vs 9.0.21.300 target) and acquisition stubs for gaps
  (XML-definition docs blocked by bot protection).
- **There is no automated freshness mechanism.** Nothing detects that a vendor page changed
  since `captured_at`. Currency is a human ritual.

### 2.4 The scraper that didn't come over

The `drydocs.scrapers` subsystem (Confluence scraper, `drydocs-scrape` CLI) exists only in
**DryDocs-bkup** — it was not carried through the restructure. That is a real loss for this
review's purpose, because it already solved most of what T2–T4 ingestion needs:

- re-runnable registry of pages by URL, space-key namespacing (`knowledge/spaces/<SPACE>.yaml`)
- fetch → clean (deterministic regex cleaner) → token-count (tiktoken) → graph-shaped YAML/JSON
- per-page provenance: sha256 content integrity, tokenizer + content-source + page version,
  `computed_at`
- curation ladder: `curation_status` (unapproved | approved_by_sme | ai_generated_review_needed),
  `curation_owner`, `curation_date` — i.e. the HITL gate, pre-invented for documents
- append-only prompt/audit log; ontology explicitly "shaped to project later into Neo4j"
  (staging only — it never wrote to the graph)

Meanwhile the restructure matured exactly the things the scraper lacked: the classification
axis, the publish boundary, precedence, the HITL gate, and the module boundary discipline.
**The two halves are complementary:** the bkup scraper is the *mechanism*, the restructured
repo is the *governance*. Reconciling them is the core of the plan below.

### 2.5 Documents and the graph today

No documentation is loaded into Neo4j. The graph holds structural metadata (Control-M,
SEAL, PAT); agents navigate docs by reading markdown, routed by CLAUDE.md and the manifests.
`knowledge/upgrade-plans/graphrag-llm-navigation.md` explicitly skipped the vendor
`Document → Chunk` layer as "N/A — DryDocs has no documents to chunk." **That conclusion was
correct for the structural graph and is now obsolete for this initiative** — a docs corpus
is precisely a Document→Chunk workload, and the locally mirrored `llm-graph-builder` is the
reference implementation for it (chunking, entity extraction, `Document→Chunk→Entity`
retrieval patterns previously set aside).

---

## 3. Assessment

**Strengths.** Three-axis source tracking with test enforcement; the capability-vs-conformance
corpus split; the BMC manifest's provenance discipline; taxonomy-path frontmatter on internal
standards; a validated multi-DB topology (G1) whose trust boundary anticipates exactly the
software-KG / context-KG split being asked for.

**Gaps, in priority order:**

1. **No document-source registry.** Documents need the same "declared once, classified at
   ingestion, gated before load" treatment data sources get in `source-registry.yaml`.
2. **No ingestion mechanism in the live repo.** The scraper machinery (fetch, clean, hash,
   token-count, curation ladder) is stranded in DryDocs-bkup.
3. **No freshness detection.** `captured_at` + manual audits only; no re-fetch/diff (the
   scraper's sha256-per-page is the obvious primitive for change detection).
4. **Docs invisible to the graph.** Retrieval quality of graph traversal vs today's
   markdown navigation is untested (hence the T1 benchmark to-do).
5. **T3 is unmanaged.** Root-level PDFs/images and `docs/Product` have no manifest or
   classification stamps.
6. **T4 has no path at all** — no connectors (Confluence/SharePoint/Teams/email), no
   landing zone wired, though `drydocs_context` + the curation ladder are both designed.

---

## 4. Recommendation

### 4.1 One ingestion module, not two

**One document-ingestion component — `drydocs-docmeta` (or resurrect the name
`drydocs-deepdoc` per ADR 0002 C3) — handles both external and internal sources.** The
external/internal difference is *data on the source record* (classification, connector,
curation requirements), not a difference in pipeline shape. Splitting into two modules would
duplicate the fetch→clean→hash→chunk→stamp→load spine and put the publish boundary in code
instead of config, violating the repo's own rule that precedence/gating live in `config/`.

The pipeline, per source:

```
register (doc-source registry: classification, connector, trust default, refresh policy)
  → fetch (pluggable connector: web / confluence / sharepoint-teams (Graph API) / email / file-drop)
  → clean + chunk + token-count           (bkup scraper machinery, ported)
  → provenance stamp (sha256, captured_at, trust tier, taxonomy_path where declared)
  → curation gate (curation_status ladder; SME confirm for T2–T4)   [HITL]
  → load (target DB selected by classification + trust, from config)
```

It imports only `drydocs-core`, never other components (MODULE_MAP invariant), and follows
the layer rule: document *registration* is taxonomy; entity/edge extraction from doc content
is an ontology decision that goes through the gate.

### 4.2 Two graph targets, one existing topology

- **Software KG** — T1 vendor docs plus SME-**confirmed** T2/T3 internal guidance. Provision
  as a third data DB (`drydocs_docs`) beside `drydocs`, added to the `drydocs_all` /`ddall`
  composite. Keeping docs out of the structural DB preserves the destroy/rebuild freedom the
  core graph relies on. Only VERBATIM/GROUNDED content loads as vendor ground truth;
  SYNTHESIZED chunks load labeled as inference (the manifest's rule, now graph-enforced).
- **Context KG** — T4 SME/business-application context goes to the **existing**
  `drydocs_context`: it is Internal-Confidential, unverified-by-default, and survives core
  rebuilds there by design. Promotion to confirmed follows the already-planned
  `drydocs_context → HITL gate → drydocs` path (G5).
- Cross-links via the established proxy-node pattern: `(:Chunk)-[:DESCRIBES]->(:ControlMJob {jobId})`
  etc., joined on canonical identity through the composite — same mechanism G1 validated.

### 4.3 Prove it before building it (the benchmark first)

Before committing to the module, run the experiment the first to-do captures: load **one**
corpus (BMC Control-M — smallest lift: manifest and trust tiers already exist) into a local
Document→Chunk→Entity graph following `llm-graph-builder` patterns, and benchmark agent
retrieval — graph traversal vs today's manifest-routed markdown reading vs plain vector RAG —
on a fixed question set (support-style: "is X legal in Control-M?", "which doc governs Y?").
Accuracy, latency, tokens consumed. If traversal doesn't win, the module shrinks to
registry + freshness only, which is worth having regardless.

### 4.4 Staying current

Give every doc-source record a `refresh:` policy (`manual | on-demand | scheduled`). The
re-fetch pipeline diffs sha256 per page; changed pages re-enter the curation gate rather
than silently overwriting (a vendor doc change may invalidate SYNTHESIZED derivations built
on it). `REGISTRY.yaml` `verified:` and A1-style audits stay as the human backstop.

### 4.5 Sequencing (as captured in IDEAS.md, to be groomed)

1. **T1 benchmark** — vendor-doc KG traversal experiment (BMC corpus, local, throwaway DB).
2. **Doc-source registry** — schema + tests, backfill BMC/reference/knowledge-standards
   entries; port scraper provenance machinery into `drydocs-docmeta` behind the registry.
3. **T2/T3 ingestion** — internal platform + product/process guidance through the curation
   gate into the software KG; classify and manifest the unmanaged T3 strays.
4. **T4 connectors** — Confluence first (scraper exists), then SharePoint/Teams (Graph API),
   then email; land in `drydocs_context`. Confidential values respect the publish boundary:
   raw T4 content is gitignored/`internal/`-only; only stable ids and graph writes leave.

Dependencies to note when grooming: the software-KG DB rides on the G1 topology (local now,
live blocked on G7's Enterprise target); the module scaffold follows the G2 core extraction
pattern; T4 curation reuses the gate flow (03-hitl-sme-flow.md).
