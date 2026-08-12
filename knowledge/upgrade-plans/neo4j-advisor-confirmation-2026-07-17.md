# Neo4j configuration confirmation — GraphAcademy MCP advisor review (2026-07-17)

The DryDocs schema (`drydocs_core/schema/constraints.cypher` + `provisioning/`), the
loader architecture (`drydocs/loaders/`), and the graphrag retrieval direction (docmeta
P0 verdict) were run through the **GraphAcademy MCP advisors** (`neo4j_graph_modeler`,
`neo4j_import_advisor`) for best-practice conformance. Every advisor claim below was
**verified against the repo** before being recorded — advisor misses are called out, not
silently dropped. Companion docs: [`docmeta-p0-verdict.md`](docmeta-p0-verdict.md),
[`graphrag-llm-navigation.md`](graphrag-llm-navigation.md) (now partially superseded —
see §4).

The DryDocs data model was also saved to the GraphAcademy course
`genai-context-graphs` (`save_data_model`), so future tutoring sessions load our real
schema as context.

## 1. Confirmed correct — no change needed

| Practice | DryDocs state | Advisor verdict |
|---|---|---|
| Driver `UNWIND`+`MERGE` for incremental loads (vs `LOAD CSV` / `neo4j-admin import`) | `BaseLoader._flush`, idempotent, re-runnable | ✅ "Right call" at 240K jobs / 1.1M vars; admin-import is offline-only dead-end for production |
| Batch size | `batch_size=1000` (`base.py`) | ✅ inside the recommended 500–1000 band |
| Constraints created **before** load; NODE KEY on natural business keys | `constraints.cypher`, all `IF NOT EXISTS` | ✅ correct pattern; NODE KEY auto-creates the backing index |
| Relationship MERGE anchored on indexed endpoints | jobs loader `MATCH (f:ControlMFolder {folder_id})` before `MERGE (f)-[:CONTAINS_JOB]->(j)` | ✅ required pattern; unanchored = full scan × 500K |
| Explicit property lists on `SET` (never `SET n = row` map-overwrite) | all loader cypher templates | ✅ protects cross-loader properties |
| Python-side variable resolution (not in-Cypher) | `drydocs/staging.py` | ✅ explicitly endorsed — in-Cypher resolution would force serial execution |
| Content-hash guard against no-op writes | `row_checksum` delta-only `WAS_GENERATED_BY` (doc 06 Phase 2 edge diet) | ✅ we already exceed the advisor's recommendation (they suggested it for chunks; we do it for jobs, folders, and chunks) |
| Composite-DB + proxy-node-on-business-key for the trust boundary | ADR 0002 D1: `drydocs`/`ddlineage`/`ddcontext` + `ddall`, `02_proxy_constraints.cypher` | ✅ "the correct Neo4j EE pattern" — ADR 0002 externally validated |
| No relationship-property indexes | none exist | ✅ correct — not needed for pure structural traversal; would add write overhead speculatively |
| PROV-O `JobRun` reification | `WAS_GENERATED_BY` → `:JobRun` | ✅ no redesign needed |

**Advisor misses (checked, not real):** "missing `Folder.folder_id` constraint" —
exists as `controlmfolder_id` (the advisor used a generic label); "`Condition` name
gap" — self-retracted, `(folder_id, name)` NODE KEY is correct.

## 2. Real findings (repo-verified)

### 2a. HIGH — data-center identity gap (verification required before the 4-DC load)

The staging layer keys every job by **`(data_center, folder_id, job_id)`**
(`staging.py:36-85`), but the graph identity is `(folder_id, job_id)` for jobs and
**`folder_id` alone** for folders — `data_center` survives only as the `:SCHEDULED_ON`
edge. If BMC `TABLE_ID` values collide across the 4 production DCs in the CM_ replica,
the full multi-DC load will **silently merge cross-DC folders/jobs into one node**.
The T012 single-DC pilot cannot expose this.

**Action (company-side verification query, before any multi-DC load):**

```sql
SELECT TABLE_ID, COUNT(DISTINCT DATA_CENTER) AS dc_count
FROM   psgmgr.CM_DEF_VTAB
GROUP  BY TABLE_ID
HAVING COUNT(DISTINCT DATA_CENTER) > 1;
```

Zero rows → current keys are safe; document the invariant in
`controlm_folders.cypher`. Any rows → identity change (`data_center` joins the folder
and job keys) — an **identity decision, therefore HITL-gated** (ADR 0001), with a
constraint migration and loader/cypher updates.

### 2b. MEDIUM — no incremental-delete path

Loaders refresh `last_seen_at`/`last_run_id` and derive `active` from
`IS_CURRENT_VERSION`, but a job **removed from the source entirely** is never touched
again — it stays `active` with a stale `last_seen_at` forever. Advisor recommendation
(agreed): full-diff ID set in Python (graph IDs − extract IDs) → soft-delete mark
(`deleted_at`, `is_active=false`) → separate scheduled hard-delete sweep
(`DETACH DELETE` after a validation window). Avoids the timestamp race (a job absent
from one extract due to replication lag getting wrongly deleted) and leaves an audit
trail.

### 2c. MEDIUM — pre-load index-ONLINE assertion

`MERGE` against a `POPULATING` index succeeds but collapses 10–100×. Cheap hardening
in `BaseLoader`: before the first batch, assert
`SHOW INDEXES WHERE state <> 'ONLINE'` returns nothing for the target labels.

### 2d. MEDIUM — `JobRun` time-range indexes

`JobRun.run_id` is constrained but `started_at`/`status` are unindexed — "failed runs
last 24h" style lineage queries will full-scan. **Fold into the provenance-audit-fields
plan** (docs 06/06a, currently at its Phase-0 gate) rather than adding standalone: that
plan already owns the `:JobRun` envelope shape.

### 2e. LOW — existence constraints on the trust axis

The provenance-audit answer ("how much is SYNTHESIZED") depends on
`Document.trust_default` / `Chunk.tier_rule` being non-null — a silent null is an
undercount, not an error. EE supports existence constraints; add
`REQUIRE ... IS NOT NULL` for both when the docmeta component lands.

### 2f. LOW — composite-DB write guard at the privilege layer

`ddall` write-blocking is currently by convention. When roles exist (beyond the dev
container's single user): `DENY WRITE ON DATABASE ddall` / per-DB `GRANT WRITE`, so
the trust boundary is enforced by auth, not discipline. Pairs with the ADR 0002
transaction-domain argument.

## 3. Explicitly rejected advisor suggestions

- **Composite `(data_center, job_name)` index** — premature until 2a resolves the
  identity question; if `data_center` joins the node key, its backing index changes the
  calculus anyway.
- **Label-as-tier (`:SynthesizedChunk`)** — conflicts with the property-based trust
  envelope (SOURCE-MANIFEST axis) and the 374-chunk scale doesn't justify it.
- **Fulltext contact/job indexes now** — retrieval-layer decisions belong to the
  docmeta P1+ grooming (the P0 verdict already positions fulltext as the
  zero-dependency paraphrase supplement); don't add outside that plan.

## 4. GraphRAG state correction

[`graphrag-llm-navigation.md`](graphrag-llm-navigation.md) (2026-06-19) describes a
"P0 vector + P1 fulltext" state on `feat/llm-nav-p0-vector` — **that branch no longer
exists and none of it is on main**: no vector index, no `:Searchable` label, no
embeddings loader anywhere in the repo. The only fulltext index ever created is the
benchmark throwaway (created + dropped, `benchmark_p0.py:192`). The doc's *refinements*
(vector-write API, UNWIND batching, dimension derivation, hybrid+text2cypher agent
design) remain valid **as future guidance** for when the vector arm unblocks on the
open LLM-key-strategy question — but its "already matches the reference" validation
table describes code that is not in the repo. The doc now carries a status note; the
authoritative retrieval direction is the **docmeta P0 verdict**: traversal-first,
fulltext supplement, vector deferred.
