# External-tool review — neocarta's connector ETL shape vs `drydocs_core/adapters/` + the source registry

**Date:** 2026-08-27 · **Scope:** [`neo4j-labs/neocarta`](https://github.com/neo4j-labs/neocarta)
(Apache-2.0, Neo4j Labs) connector/ingestion architecture, compared against DryDocs'
adapter/loader/registry pipeline · **Method:** docs-level review of neocarta (README +
DeepWiki; code-level MERGE/batching/error-handling detail NOT reachable — stated in §5)
beside a source-level read of `drydocs_core/adapters/`, `drydocs/loaders/base.py`, and
`config/source-registry.yaml` (v2) · **Classification:** Internal-Public (mechanism only)
· **Feeds:** ADR 0015 sources-and-tooling-watch register (the neocarta row cites this
review); precedent: `gitnexus-depgraph-comparison.md`.

**Verdict up front: on declaration, identity, validation, provenance and trust, the
traffic flows one direction — neocarta could cherry-pick DryDocs, not the reverse. But
neocarta holds four patterns DryDocs lacks, and one of them — query-history ingestion as
run-time evidence — serves the Team Edition thesis directly.** The register stance stands:
adopt patterns, never the package.

---

## 1. The structural difference in one sentence

neocarta puts the whole pipeline **inside one object** — a connector class owning
`extract() → transform() → load()` behind an `ingest()` façade (protocol-based:
`SourceConnectorProtocol` / `FormatConnectorProtocol`) — while DryDocs **separates the
pipeline into three layers with a declaration gate in front**:

1. **`Adapter`** (`drydocs_core/adapters/base.py`, 30 lines) — a Protocol: context-managed,
   yields raw dict rows, keys lowercased, values left as strings; transform only, no graph
   write. Reusable across loaders (`CsvAdapter`, `OracleAdapter` + per-run SQL log, the
   G96 Control-M API-call framework).
2. **`BaseLoader`** (`drydocs/loaders/base.py`) — pydantic row model per loader (rejects to
   a side log with row index), batch UNWIND into a per-loader Cypher template, `:JobRun`
   PROV envelope, row-checksum-gated `WAS_GENERATED_BY` (the provenance-edge diet),
   `sweep_removed`.
3. **Source registry v2** (`config/source-registry.yaml` + `source_registry.py`) — SYSTEM
   vs DATASET rows, per-dataset `confirmed` gate (`require_confirmed()`), classification,
   SOR/ADS authority, derived URNs (hand-carried `urn:` refused at parse), retired-id
   refusal (D4).

neocarta has **no equivalent of layer 3 at all**, and layers 1–2 are welded together
inside its connectors.

## 2. Dimension by dimension

| Dimension | neocarta | DryDocs | Ahead |
|---|---|---|---|
| Unit of composition | One connector class per source; uniform verbs `extract/transform/load/ingest` (+`export()` on format connectors) | Adapter + loader + Cypher template + registry row + CLI chain — five artifacts per source, composed by convention | neocarta on ONBOARDING ERGONOMICS; DryDocs on separation (adapters reusable; theirs welded in) |
| Source declaration | Env vars + constructor args + CLI; nothing committed | Registry v2: SYSTEM/DATASET split, per-dataset `confirmed` gate, classification, authority, locator, SDLC link | **DryDocs, decisively** — neocarta has nothing here |
| Identity | Dot-paths (`db.schema.table`); optional custom `*_id` override; a PROSE WARNING not to mix id strategies across files | URNs derived at parse; `urn:` in a row refused; retired-id refusal list | **DryDocs.** Their mixed-strategy warning is the T19 collision class, solved by discipline where DryDocs solved it by refusal — independent confirmation the problem is real |
| Row validation | A transformer stage; no documented row contract | Pydantic model per loader; rejects side-logged with row index; strings-in, coercion downstream | **DryDocs** |
| Provenance / runs | None documented | `:JobRun` per load; checksum-gated `WAS_GENERATED_BY`; per-run SQL logs for HITL verification; removal sweep | **DryDocs** — and in a bank this is not optional |
| Incremental | Query-log connectors take `start_timestamp`/`end_timestamp`/`limit`; schema connectors full-load | Full refresh + checksum no-op detection + `sweep_removed` | Different philosophies; roughly even |
| Trust axis | None | `confirmed` gate; `:Uncertain` boundary; precedence | **DryDocs** |
| Graph model | Fixed backbone `Database→Schema→Table→Column→Value` + `Query`, glossary (`BusinessTerm`, `TAGGED_WITH`) | The full ontology (PROV/ORG/DPROD, medallion, taxonomy families) | Not comparable — theirs is a floor, ours is a vocabulary. Any mapping of their five-node backbone routes through the crosswalk gate |

## 3. The four cherry-picks (the register row's authoritative list)

Each is a PATTERN to implement against DryDocs' own surfaces, cited here per the ADR 0015
register discipline; none is a dependency. Backlog items are minted under the TE epic when
groomed, not by this review.

### CP-1 — Query-history ingestion as run-time evidence (the sleeper; serves TE directly)
neocarta ingests warehouse query logs as first-class graph:
`(:Query)-[:USES_TABLE]->(:Table)`, `(:Query)-[:USES_COLUMN]->(:Column)`, windowed by
timestamp. Nothing in the DryDocs loader fleet does this. The TE context makes it load-bearing:
the data applications "depend on trusting the code from run time tracking" — and query
logs (Oracle audit, Snowflake `ACCESS_HISTORY`) ARE run-time truth, captured as EVIDENCE
rather than trusted as folklore. A TE loader in this shape yields what is ACTUALLY read
and written per dataset, joinable against what the Control-M command lines DECLARE —
which is precisely the known (code/run-time-confirmed) vs stale metric the ADR 0015
Context extension point reserves. Build shape: a normal `BaseLoader` over a windowed
adapter; the `Query`-family vocabulary goes through the gate before any label lands.

### CP-2 — A per-source connector façade (ergonomics, never a replacement)
Onboarding a source in DryDocs touches five artifacts; that is the guard discipline and it
stays. But TE hands onboarding to ten teams, and "add your team's source" is the
template's hardest UX moment. A thin `SourceConnector` façade — one object per source
exposing `extract/transform/load/ingest`, COMPOSED FROM the existing adapter + loader +
registry row, with `ingest()` still refusing through `require_confirmed()` — keeps every
guard while giving a team one thing to implement and one verb to run. Aligns with ADR
0012's subject-named load surface: the façade is the natural home for `load-<subject>`.

### CP-3 — `export()` / OSI as the estate interchange candidate
neocarta's format connectors both ingest AND export a neutral format (Open Semantic
Interchange). DryDocs has no export/interchange story, and `ddestate` will want one:
shared-object descriptors crossing instances (the warehouse table two LOBs read) are
better exchanged in a neutral wire format with the tenant question already settled than
resolved composite-side. Watch OSI specifically; if it stabilizes, it is a candidate for
the estate's exchange grammar (a gate decision, since it touches identity).

### CP-4 — Embeddings as a post-load connector pass
`LiteLLMEmbeddingsConnector` enriches ALREADY-LOADED nodes as a separate stage, never
baked into loaders. TE v1 cut `essential_graphrag`; when retrieval pressure lands on
`ddestate` (the register's named GraphRAG trigger), this decoupled shape is the re-entry
pattern: loaders stay deterministic, the LLM-touching pass sits behind its own boundary.

## 4. What NOT to take (recorded so it is not re-litigated)

- **Connector-owns-everything composition, taken literally** — dissolves the
  adapter/loader seam `test_module_boundary.py` enforces and re-welds transform to load;
  the tangle ADR 0002 D3 exists to prevent. CP-2 is the bounded version: façade OVER the
  seam, never instead of it.
- **Its configuration story** (env vars + constructor args) — behind even the ADR 0014
  env/declared-YAML split, let alone registry v2. Nothing to adopt.
- **Its graph model as a model** — a floor, not a vocabulary; adopting it would be a
  regression. Only a gated crosswalk mapping is ever on the table.

## 5. Evidence limits, stated plainly

Code-level detail — MERGE semantics, batching, idempotency, error handling inside
neocarta's loaders — was not reachable through docs-level review; this review compares
ARCHITECTURE as documented, not implementation as built. At ~41★ / 271 open issues it is
a young Labs project. Both facts are consistent with the register stance this review
feeds: adopt the pattern, keep our surface, watch the project (triggers on the ADR 0015
register row: convergence with the `drydocs_api` QuerySpec surface; Labs graduation or
archive).

## Sources

- [neo4j-labs/neocarta](https://github.com/neo4j-labs/neocarta) (README; DeepWiki docs view)
- Local ground truth read at review time: `drydocs_core/adapters/{base,csv_adapter,oracle_adapter}.py`,
  `drydocs_core/adapters/controlm/README.md`, `drydocs/loaders/base.py`,
  `drydocs_core/source_registry.py`, `config/source-registry.yaml`
