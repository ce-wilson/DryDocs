# Upgrade plan — `drydocs-docmeta` (document ingestion component)

**Status:** P0–P3 DONE (benchmark verdict = BUILD, ADR 0006 accepted, registry ledger, and the component itself as of 2026-08-04 / Q6). P4 onward planned.
**Classification:** Internal-Public.
**Companion review:** [`../../docs/reviews/doc-knowledge-ingestion-review.md`](../../docs/reviews/doc-knowledge-ingestion-review.md)
(tiers T1–T4, gap analysis). IDEAS.md 2026-07-06 entries capture the tier to-dos.
**Owner:** `main` (component scaffolding = architecture); `reference-librarian` (registry
upkeep); `ontology-mapper` (doc→graph edge mappings via the gate).

`drydocs-docmeta` is the single document-ingestion component: it registers documentation
sources (external vendor + internal guidance + SME context), fetches/cleans/chunks them with
full provenance, runs them through the curation gate, and loads confirmed content into the
**software KG** (`drydocs_docs`) and unverified SME/business-application context into the
**context KG** (`drydocs_context`). One module for external AND internal — the split lives
in config (classification, connector, curation), not code.

This plan covers **two ports**:

- **Port A (bkup → producer):** resurrect the `drydocs.scrapers` machinery stranded in
  `DryDocs-bkup` into this component, under the restructure's governance.
- **Port B (producer → company):** the disposition rules for the company apply — what ports
  clean, what is Canonical-COMPANY, and what the company side must **supplement** because
  the producer environment cannot build or run it. §6 is written to be lifted into
  `git-readme.md` when the component lands.

---

> **Callout — SEAL/PAT docs as source of record + the SEAL entity reshape they drive**
> **(2026-07-08 review; GATE-BOUND — nothing applied, edge-meaning goes through the HITL gate).**
>
> **Documentation treatment (the source-of-record question).** Each scraped SEAL/PAT page is a
> `Document` Entity (`prov:Entity`; Document→Chunk with the sha256 / token-count / `curation_status`
> envelope), classified Internal / Internal-Confidential → `drydocs_context`; raw text stays under
> `internal/`. Trust axis: VERBATIM (scraped text) / GROUNDED (extractions that cite the page) /
> SYNTHESIZED (inference only). **"Source of record" is two mechanisms:** (1) register SEAL/PAT as the
> authoritative source in `config/precedence.yaml` (they win internal product/business conflicts);
> (2) every fact/record extracted from a page carries **`prov:hadPrimarySource → (that Document)`** —
> `Entity→Entity`, a sub-property of `prov:wasDerivedFrom`. Promotion context → ground-truth (`drydocs`)
> only via the **G5 gate** (a gate-confirmed write, never an in-place cross-DB edit).
>
> **The `:Application` reshape this feeds (fixes a real typing muddle).** The node is currently
> `prov:SoftwareAgent` yet also carries `dprod` ports (→ Entity), `org:Membership → org:Role`
> (→ Organization), and the proposed K1/K2 `wasAssociatedWith` (→ Agent) — three incompatible types.
> Because `hadPrimarySource` is `Entity→Entity`, an extracted app record MUST be an Entity — which is
> also *correct*: a SEAL application is a **data-product / asset (`prov:Entity` / `dprod:DataProduct`)**,
> not an Agent and not an Organization. Its **Technical-Operating-Model** role-holders (CTO, application
> owner, information owner, data owner, operate manager, risk & compliance officer — a governance model
> DISTINCT from the PAT product org) are **attribution on the asset**:
> `Application —prov:qualifiedAttribution→ (:Attribution){ prov:agent → Employee, prov:hadRole → Role }`,
> the TOM roles a shared `skos:Concept` vocabulary. `org:Membership`/`org:Role` stays for the **PAT
> hierarchy only** (DevTeam etc. — real organizations); the bug was reusing PAT's `org:` pattern for
> SEAL's TOM. Deprecate `seal_has_membership`/`seal_of_role`/`seal_held_by`; keep `seal_has_port`.
> **K1/K2** (`job —wasAssociatedWith→ Application`, needs Agent) must be re-shaped to an attribution/
> domain edge to the app-as-Entity — still `proposed`, so resolve it there.
>
> **Process (ontology-mapper via the gate):** deprecate the three `seal_*` membership terms; register
> `prov:hadPrimarySource` + `prov:wasAttributedTo`/`qualifiedAttribution` (+ `prov:hadRole`) + the TOM
> Role vocab as `status: planned`; flip the `:Application` node class (`SoftwareAgent` → `Entity`/
> `DataProduct`); re-open the K2 job→app mapping; log in `config/gate-log.md`. Nothing applied until
> SME-confirmed. Also flagged for the port in `git-readme.md`.

---

## 1. Component identity and boundary

### 1.1 `docmeta` vs the reserved `drydocs-deepdoc` (decision for the gate)

ADR 0002 already reserves `drydocs-deepdoc` (C3): **reactive**, on-failure, on-demand deep
dive writing uncertain findings to `drydocs_context`. Docmeta is **proactive corpus
ingestion** with a registry and refresh cadence. Recommended: **keep them separate** —
different duty cycles, different write targets (docmeta writes `drydocs_docs` for confirmed
content and `drydocs_context` only for T4; deepdoc writes `drydocs_context` only). Deepdoc
becomes a *consumer* of docmeta's corpus (its deep dives cite Document/Chunk nodes).
Alternative (fold docmeta into deepdoc) is rejected for the same reason review and load are
separate: one is a run-cadence pipeline, the other is an on-demand investigator. Confirm at
the Phase 1 gate; record as **the docmeta ADR** (number minted at authoring — 0004, reserved
here 2026-07-06, was since TAKEN by `0004-software-registry-vendor-terminology.md`, accepted
2026-07-07; corrected at the 2026-07-16 groom).

> **DECIDED 2026-07-18 — ADR 0006 ACCEPTED at the Q4 gate (config/gate-log.md):**
> SEPARATE component, as recommended. Also decided there: the docs DB is **`dddocs`**
> (this plan's `drydocs_docs` renamed to the live `dd*` convention), and the §2 edge
> list is reconciled — `HAS_CHUNK` superseded by the active PART_OF/FIRST_CHUNK/
> NEXT_CHUNK shape; `HAS_DOCUMENT`/`GOVERNED_BY` registered `planned`; chunk-level
> DESCRIBES deferred to its own gate at extraction design.

### 1.2 Boundary rules (MODULE_MAP invariants)

- New `docmeta` `COMPONENT_GROUP` in `tests/unit/test_module_boundary.py` + a row in
  `MODULE_MAP.md`. Default-deny forces every new module to classify — same discipline as
  `review` and `plan`.
- Imports **core only** (`drydocs_core.*` surface): config/classification helpers,
  `neo4j_client`, ontology namespaces. Never imports load/review/lineage/deepdoc.
- CLI commands (`docs-register`, `docs-fetch`, `docs-status`, `docs-diff`, `docs-load`) wire
  into `drydocs/cli.py` via the **entrypoint exemption** — do NOT create a separate CLI
  package (the MODULE_MAP canonical resolution; avoids company re-collisions).
- Layer discipline: registering a doc source is **taxonomy**; extracting entities/edges from
  doc content is an **ontology** decision → `relationship_vocabulary.yaml` `status: planned`
  first, then the HITL gate. No relationship type invented during import.

### 1.3 Package layout

> **BUILT 2026-08-04 (Q6) — and at `drydocs_docmeta/`, not the `drydocs/docmeta/`
> written below.** That path predates the Phase B relocate (2026-07-10): every
> component created since — `drydocs_remediation`, `drydocs_lineage`,
> `drydocs_deepdoc`, `drydocs_api` — is a top-level package, while the `drydocs`
> package is the component *remainder* (load / review / plan / docgen). Adding a
> fifth component inside the remainder would have run against the direction of
> travel, so docmeta follows the live precedent. The §6 port paths below read
> `drydocs_docmeta/**`.

```
drydocs_docmeta/
  __init__.py
  policy.py            # BUILT — the Q12 capture policy, read from config/doc-capture.yaml
  registry.py          # BUILT — typed view of the ledger + the two bkup ladders (§5)
  manifest.py          # BUILT — per-run manifest + sha256 + digest diff → re-gate queue
  cleaner.py           # BUILT — deterministic HTML→text cleaner (pure, stdlib only)
  tokenizer.py         # BUILT — token estimation, labeled fallback
  chunker.py           # P4 — Document→Chunk splitting (llm-graph-builder patterns)
  curation.py          # P5 — curation_status ladder → HITL gate integration (§3.3)
  freshness.py         # P5 — refetch cadence on top of manifest.diff() (§3.4)
  connectors/
    base.py            # BUILT — Connector protocol: fetch(source) -> list[RawPage]
    web.py             # BUILT — public http(s), injectable transport, SSRF allow-list, Q12 ceiling
    filedrop.py        # BUILT — a file or a directory of md/txt/html
    confluence.py      # company-side impl behind base.py (§6) — no producer stub
    sharepoint.py      # company-side (Graph API)
    teams.py           # company-side (Graph API)
    email.py           # company-side
  loaders/
    cypher/document.cypher, chunk.cypher, links.cypher   # P4
```

Two things landed differently from the sketch, both recorded here rather than
left as surprises:

- **`freshness.py` is not a separate module yet.** Its primitive — sha256 per
  page, and a diff that separates changed / added / removed — is
  `manifest.diff()`, because the digest and the comparison over digests are the
  same fact. What P5 adds is the *cadence* and the queue, not the comparison.
- **No connector stubs ship for the T4 sources.** A stub that raises is
  indistinguishable at a call site from a connector that is merely
  misconfigured, and this repo has spent three items (G29, G30, Q8) on things
  that succeed loudly and do nothing. The producer ships the protocol; the
  company implements against it.

### 1.4 Config (the governance the bkup scraper lacked)

`config/doc-source-registry.yaml` — schema `drydocs.doc-source-registry.v1`, guarded by a
new `tests/unit/test_doc_registry.py` (mirrors `test_classification.py`). Per source:

```yaml
- id: bmc-controlm-docs
  classification: External            # REQUIRED — config/classification.yaml level
  connector: web                      # web | filedrop | confluence | sharepoint | teams | email
  source_url: documents.bmc.com/...   # External ⇒ source_url + captured_at (existing rule)
  manifest: external/orchestration/bmc-controlm/SOURCE-MANIFEST.md
  trust_default: GROUNDED             # VERBATIM|GROUNDED|SYNTHESIZED default per manifest rules
  tier: T1                            # T1 vendor | T2 internal-platform | T3 product/process | T4 SME-context
  target_db: drydocs_docs             # drydocs_docs | drydocs_context — from classification+tier, never hardcoded
  refresh: manual                     # manual | on-demand | scheduled(cron)
  curation: none                      # none (T1) | sme-confirm (T2/T3) | sme-confirm+confidential (T4)
  taxonomy_path: technology/orchestration/control-m   # where knowledge/standards frontmatter declares it
```

Backfill entries at Phase 2: BMC corpus, `reference/` platforms+standards,
`knowledge/standards/**` (T2), `knowledge/org/` (ex-docs/Product, S14) + SDLC docs (T3), and the currently
unmanaged root-level strays (classify or evict them).

---

## 2. Graph targets

- **`drydocs_docs` (NEW data DB)** — the software KG. Extend `drydocs_core/schema/provisioning/`
  (G1 pattern): `CREATE DATABASE drydocs_docs`, add to the composite, uniqueness on
  `Document.doc_id` (URN from source id + path) and `Chunk.chunk_id`. Keeps docs out of the
  structural DB so core destroy/rebuild freedom survives.
- **`drydocs_context` (EXISTS)** — T4 landing zone, unverified-by-default; promotion via the
  documented G5 path (`drydocs_context → HITL gate → drydocs`/`drydocs_docs`).
- Node/edge model (all `status: planned` until gated):
  `(:DocSource)-[:HAS_DOCUMENT]->(:Document)-[:HAS_CHUNK]->(:Chunk:Searchable)`;
  `(:Chunk)-[:DESCRIBES]->` proxy nodes (`ControlMJob {folder_id,job_id}`,
  `DataAsset {assetId}` — the G1 canonical keys, joined through the composite);
  `(:Document)-[:GOVERNED_BY]->(:OntologyTerm)` where `taxonomy_path` is declared. Every
  Document/Chunk carries `classification`, `trust` (VERBATIM/GROUNDED/SYNTHESIZED),
  `sha256`, `captured_at`, `curation_status`. SYNTHESIZED chunks are labeled inference —
  never citable as vendor ground truth (the SOURCE-MANIFEST rule, graph-enforced).
- Retrieval reuses the proven P0/P1 design: `:Searchable.embedding` vector index (cosine) +
  fulltext, with the two adopted llm-graph-builder refinements
  (`db.create.setNodeVectorProperty`, batched `UNWIND` writes) — see
  [`graphrag-llm-navigation.md`](graphrag-llm-navigation.md); its "no documents to chunk"
  skip is obsolete for this corpus.

---

## 3. Phased execution

Per-phase gates: `poetry run pytest -q`, `python -c "import drydocs.cli"`, `drydocs --help`,
boundary + classification + doc-registry tests green.

| Phase | Work | Acceptance |
|-------|------|------------|
| **P0 — Benchmark spike** (IDEAS T1 entry) — **VERDICT WRITTEN 2026-07-16: [`docmeta-p0-verdict.md`](docmeta-p0-verdict.md) → BUILD** (12-question set, 3 arms live; traversal 12/12 recall at ~27× manifest token efficiency; vector arm assessed analytically behind the LLM-key decision) | Load the BMC corpus into a throwaway local Document→Chunk→Entity graph; benchmark traversal vs manifest-routed markdown vs vector RAG on a fixed support-question set. *Verdict input (Q1, 2026-07-16):* [`reference/research/essential-graphrag-notes.md`](../../reference/research/essential-graphrag-notes.md) — per-arm reference builds (ch.2 vector, ch.4 text2cypher, ch.5 agentic) and, for the verdict's own shape, ch.8's RAGAS metrics + Cypher-as-ground-truth benchmark design (the accuracy methodology this acceptance previously left unnamed). *Traversal-arm evidence (Q2, same day):* [`docs/reviews/essential-graphrag-traversal-experiment.md`](../../docs/reviews/essential-graphrag-traversal-experiment.md) — the book itself loaded as a 43-chunk lexical graph in ddcontext; 7/7 traversal-only questions answered (structure/sequence/aggregation/provenance exact; content questions bounded at exact-substring strength — the vector arm's case) | Written comparison (accuracy/latency/tokens) with a build / shrink-to-registry-only recommendation |
| **P1 — Gate + the docmeta ADR** | Gate session: component name (docmeta vs deepdoc fold-in), `drydocs_docs` DB, planned relationship entries (`HAS_DOCUMENT`, `HAS_CHUNK`, `DESCRIBES`, `GOVERNED_BY`), curation-ladder→gate mapping | docmeta ADR accepted (next free number — orig. 0004, since taken); vocab entries `status: planned`; gate-log updated |
| **P2 — Registry** | `config/doc-source-registry.yaml` + `test_doc_registry.py`; backfill all current corpora; classify/evict root-level strays | Test enforces classification+connector+tier on every entry; zero unregistered corpora |
| **P3 — Port A (bkup → producer)** — **DONE 2026-08-04 (Q6)** | Port cleaner/tokenizer/manifest/registry-models per §5; `web` + `filedrop` connectors; `docmeta` COMPONENT_GROUP + MODULE_MAP row | Track-1 portable tests for parse/clean/hash (no network); boundary guard green — 46 offline tests, no network and no data root |
| **P4 — Load path** — **REVISED 2026-08-14: [`docmeta-p4-revision-single-db.md`](docmeta-p4-revision-single-db.md)** (single-db target per the consolidation direction — no `dddocs` delta; local sentence-transformer embeddings until a server-side key lands; gate items G-1..G-3 there). The row below is the superseded multi-DB shape. | chunker + loaders + `drydocs_docs` provisioning delta; embeddings via P0 module; load BMC corpus end-to-end locally | `docs-load` idempotent re-run adds nothing; trust labels queryable; composite smoke reads docs+structural |
| **P5 — Curation + freshness** | `curation.py` gate wiring (T2/T3 require sme-confirm before `drydocs_docs`); `freshness.py` refetch→sha256-diff→re-gate queue | Changed page re-enters gate, does not silently overwrite; unconfirmed T2 source fails fast (D3 pattern) |
| **P6 — T2/T3 ingestion** | `knowledge/standards/**`, `knowledge/org/` (ex-docs/Product, S14), SDLC docs through the gate into `drydocs_docs` | Every loaded doc traces to a confirmed registry entry + curation record |
| **P7 — T4 connectors (company-side)** | Confluence impl, SharePoint/Teams (Graph API), email → `drydocs_context` | §6 Track-2; raw content never leaves `internal/`/gitignored paths |

P4's live deploy formerly inherited the **G7 blocker** (single-DB Aura couldn't host
`drydocs_docs` + composite) — **resolved**: Aura was dropped (2026-07-06) and the local EE
container (`config/dev-environment.yaml`) hosts the multi-DB topology, so P4 needs only a
`drydocs_docs` provisioning delta, same as deepdoc.

---

## 4. Invariants

1. No doc content loads to any graph while its registry entry or required mapping is
   unconfirmed (D3 fail-fast pattern extended to documents).
2. SYNTHESIZED content never loads as vendor ground truth; trust tier is a queryable label.
3. T4 raw content (Confluence/SharePoint/Teams/email bodies) is Internal-Confidential:
   gitignored or `internal/`-only; only stable ids, hashes, and graph writes leave.
4. Refresh never overwrites silently — a sha256 change re-queues curation, because a vendor
   doc change may invalidate SYNTHESIZED derivations built on it.
5. Precedence/targets come from config, never hardcoded in a connector or loader.

---

## 5. Port A — bkup `drydocs.scrapers` → producer `drydocs_docmeta/`

Inventory from the bkup retrieval notes (2026-07-05 session; bkup repo not mounted here —
**verify module names against `DryDocs-bkup` before porting**, per the verify-before-assert
agreement).

| Bkup asset | Disposition | Notes |
|---|---|---|
| `cleaner.py` (regex HTML cleaner, pure/deterministic) | **carry** | Port as-is + unit tests |
| `tokenizer.py` (tiktoken + labeled `whitespace_words × 1.3` fallback, no network) | **carry** | Keep provenance labels (tokenizer name/version/content-source) |
| `manifest.py` (sha256 per page, per-run manifest receipts) | **carry** | Becomes the freshness primitive |
| `registry.py` pydantic models (Project/SpaceMeta/curation fields) | **adapt** | Reshape to `doc-source-registry.yaml`; keep `curation_status/owner/date` ladder, `last_synced_from` authority ladder (`bootstrap→manual→jet`) |
| `confluence.py` (subprocess → Toby-bundled `confluence.exe`) | **adapt: interface only** | Producer ships `connectors/base.py` + a stub; the working impl is company-side (§6) — the exe/network don't exist here |
| `knowledge/spaces/<SPACE>.yaml` space-key namespacing | **adapt** | Space key becomes a registry-entry field, not a parallel registry |
| `prompts.json` append-only audit log (scrubbed args) | **carry pattern** | Per-run invocation log under the run manifest |
| `migrate.py` (subject→space re-pivot) | **drop** | One-shot; its lesson (namespace by source coordinates) is baked into the registry schema |
| Consolidated HTML doc grouped by purpose | **drop** | Regenerable output; graph + board views supersede it |
| Jira ontology (`HAS_BOARD`/`IN_INSTANCE`) | **defer** | Separate source class; register in the doc registry when wanted, gate the edges then |

**What the restructure supplies that bkup lacked** (do not re-invent in the port):
classification axis + publish boundary, precedence, trust tiers, the HITL gate (bkup's
`curation_status` maps onto it: `unapproved`→pre-gate, `approved_by_sme`→confirmed,
`ai_generated_review_needed`→gate-queued), module boundary tests, and actual graph loading —
bkup's ontology was declared but never wired.

---

## 6. Port B — producer → company (git-readme supplement)

*Lift this section into `git-readme.md` as a new stream when the component lands. Until
then it is a heads-up, like the ADR 0002 Phase B rename warning.*

### Stream: `drydocs-docmeta` — document ingestion (mixed: clean-add + Canonical-COMPANY + supplement)

**Clean-adds (take FROM producer wholesale):**

| Path | What |
|---|---|
| `drydocs_docmeta/**` (except the T4 connectors) | pipeline, registry models, policy/cleaner/tokenizer/manifest — plus `config/doc-capture.yaml`, the ONE home for the page ceiling, politeness delay and scheme allow-list |
| `config/doc-source-registry.yaml` + `tests/unit/test_doc_registry.py` | registry + guard (Track-1 portable) |
| `docmeta` group in `tests/unit/test_module_boundary.py` + `MODULE_MAP.md` row + the `drydocs_docmeta/**` PORT-MANIFEST row | default-deny forces your company-only connector modules to classify |
| `drydocs_core/schema/provisioning/` delta (`drydocs_docs` + composite update) | target-agnostic scripts, G1 pattern |
| `knowledge/upgrade-plans/docmeta-component.md`, the docmeta ADR (P1), review doc | plans/decisions |
| planned entries in `relationship_vocabulary.yaml` / `taxonomy-ontology-map.yaml` | **inert while `planned`** — but if company has already promoted any doc edge to `active`, that entry is a back-flow collision: keep your active version (same rule as `seal_app_ref`) |

**Canonical-COMPANY (keep YOUR version on collision — the `drydocs-review` rule applies):**
the working Confluence connector (your `toby_publish_confluence` / `confluence.exe` wiring,
real space keys, homepage ids), real `curation_owner` SIDs and curation records, any real
`doc-source-registry.yaml` entries carrying internal coordinates. The producer ships the
sanitized interface + stubs; yours is the wired original. If the old `drydocs.scrapers`
package (bkup lineage) exists on your side, prefer the producer's `docmeta` *structure* but
your connector *internals*; retire `drydocs.scrapers` after parity (Track-1 green).

**Company must SUPPLEMENT (cannot be built/run producer-side):**

1. **Vendor fetches blocked from producer** — documents.bmc.com 403 bot-protection: complete
   the XML-definition acquisition stub (`controlm-xml-definition-format.md`) from the company
   network, or from local `.dtd` files in `<EM home>\Default\data\Resource` + a real
   `exportdeftable` output. Same applies to any vendor portal requiring auth (Oracle
   support, AWS internal guidance).
2. **T4 connectors + credentials** — SharePoint/Teams need a Graph API app registration;
   email needs mailbox access; Confluence needs your Toby tooling. Producer ships stubs
   conforming to `connectors/base.py`; implement behind the interface so Track-1 tests pass
   unchanged.
3. **Enterprise Neo4j target** — `drydocs_docs` + composite need multi-DB (the G7 blocker).
   Until procurement lands, run local-Enterprise like the producer.
4. **Real registry entries** — internal space keys, SharePoint site ids, mailbox addresses:
   Internal/Internal-Confidential entries stay on your side only (publish boundary).
5. **SME curation** — the T2–T4 confirm ladder is inherently company-side; producer content
   arrives `unapproved`/`ai_generated_review_needed`.

**Acceptance oracle (two tracks, same pattern as Control-M):**
- *Track 1 — portable:* docmeta unit tests (clean/tokenize/hash/registry/boundary) pass with
  no network and no credentials; connector stubs skip, not fail.
- *Track 2 — wired:* `drydocs docs-fetch <company-source>` runs clean against real
  Confluence/SharePoint; `docs-load` populates `drydocs_docs`/`drydocs_context` locally;
  `docs-diff` on a re-fetch flags only genuinely changed pages.

---

## 7. Definition of done

- Every documentation corpus in the repo traces to a `doc-source-registry.yaml` entry with
  classification, connector, tier, trust default, and refresh policy — test-enforced.
- BMC corpus loaded to `drydocs_docs` locally with trust labels; benchmark verdict recorded.
- T2/T3 content enters the graph only through the curation gate; T4 lands in
  `drydocs_context` with confidential raw content contained.
- `git-readme.md` carries §6; company Track-1 passes with zero failures on a clone with no
  credentials.
