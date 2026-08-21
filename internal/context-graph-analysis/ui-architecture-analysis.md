# context-graph — competitive / reference architecture analysis

> Internal-only (this directory is excluded from the public push boundary — see
> `PUBLISH-BOUNDARY.md`). Company details, real SEAL/JPMC references, and a live
> hostname are retained deliberately per the DryDocs classification model; no
> credentials are recorded anywhere below.
>
> Source material: three deep-analysis sessions performed against the
> `context-graph` repo (`H:\coding\projects\context-graph`, an internal JPMC "CCB"
> incubator project — not a DryDocs artifact), captured as screenshots
> `CCB-Context-Graph-1..8.png` (SESSION-1 org/pipeline, SESSION-2 UI/API/config,
> SESSION-3 MCP/agent integration) and `CCB-Context-Graph-ss1..11.png` (live UI,
> `https://context-graph.dev.aws.jpmchase.net/`). Claim tags in the source docs:
> **[V]** = verified against source, **[I]** = inferred/needs confirmation. Facts
> below carry the same confidence unless noted.

---

## 1. Executive summary

`context-graph` is a **production, internally-deployed** SDLC knowledge graph built
by a JPMC CCB incubator team. It answers a very similar question to DryDocs —
"what exists, what depends on what, who owns it" — but scoped to **software
engineering fleet management** (product lines → SEALs → repos → tech stack →
cross-app dependencies) rather than DryDocs' **batch/orchestration** domain
(Control-M jobs → data flow → ownership). Both are Neo4j-backed knowledge graphs
serving a support/governance audience; both distinguish declared-vs-observed
truth; neither is a general APM tool.

Maturity: **live and running at fleet scale** — 3,841 repositories, 217 SEALs, 10
product lines, daily refresh, one production consumer application. It reads as a
solid incubator-stage product with real usage, not a prototype: the UI is
polished and information-dense, the ingestion pipeline runs unattended, and it
has a deployed MCP server with audited write access. It also carries visible
scar tissue from iterating in place — two parallel ingestion stacks, an
undeployed refactor path, aspirational docs, and an unauthenticated API surface.

**Three takeaways for DryDocs:**

1. **The edge-provenance model is the single most valuable idea here** — every
   cross-app edge is tagged as HLDD-**declared** (aspirational/on-paper) vs
   code-**observed** (`CALLS`/`DEPENDS_ON`, parsed from source) vs
   contract-**evidence** (Pact/PactFlow), rendered with a visible legend and
   MATCH/UNDECLARED/UNBUILT verdicts. This is functionally the same idea as
   DryDocs' VERBATIM/GROUNDED/SYNTHESIZED trust tiers, independently arrived at,
   and proves the pattern is right. DryDocs should treat this as validation, not
   a feature to copy from scratch, and should surface its own trust tiers in the
   UI the same explicit way (§5).
2. **The "At-a-Glance" stat-tile row + per-node dossier page** (their Repo360 /
   SEAL detail) is a clean, reusable UI pattern DryDocs' node inspector should
   adopt directly — including the empty-state honesty convention (§4).
3. **DryDocs is ahead on governance rigor** — HITL gates, a `QuerySpec` registry
   with export provenance manifests, and a documented classification/publish
   boundary. `context-graph` has none of these: no gate concept, Cypher lives
   per-view with no shared contract, and its own `/api/**` surface is
   **unauthenticated as of 2026-07-15** (a live finding, not a hypothetical —
   flag this as a security note, not a design idea to adopt).

---

## 2. Architecture & tech stack

### 2.1 Two-language system — one production path, one aspirational path

| Language | Role | Status |
|---|---|---|
| **Python** (`scripts/`, ~130 files) | Ingestion + enrichment: discovery, business-domain graph load, drift detection, context/repo-360 generation, vector embedding | **Production data path** — the only thing the daily Jenkins pipeline runs |
| **Java 21 + Spring Boot 3.3** (`context-graph-core`, `-connectors`, `-server`, `-sync`), on an internal "Photon Boot 3.5.13" parent BOM | Query/serving REST API + MCP tools + hosts the React UI | Server/API is live and serving traffic; the **connector framework** (`context-graph-connectors/`, 13 modules, `GraphConnector` interface) is a **scaffolded, undeployed refactor path** — reachable only via a manual `POST /api/v1/sync/*`, no cron/schedule invokes it in production |

Key implication for DryDocs: this repo carries **two ingestion implementations**
simultaneously (Python production, Java connector-framework parallel/dormant) and
**two graph-backend adapter stacks** (Java `GRAPH_PROVIDER`, Python
`GRAPH_BACKEND`) with `TigerGraph` stub adapters on both sides that are never
invoked — the root `pom.xml` description still calls the project
"TigerGraph-backed," which is aspirational, not current **[V]**. This is a
caution, not a pattern to emulate: a lot of scaffolding/optionality accreted
around a single working Neo4j path. DryDocs' own current single-path Python
ingestion is the healthier state; resist the temptation to pre-build a second
"future" implementation before the first is fully proven.

### 2.2 Data platform

| Layer | Detail |
|---|---|
| Graph DB | Neo4j **5.25 Enterprise**, multi-database (docker-compose), HNSW vector indexes (384/1536 dims) + full-text indexes (`service_search`, `repo_search`, `story_search`) |
| Graph abstraction | Java `GRAPH_PROVIDER` / Python `GRAPH_BACKEND` factory pattern → Neo4j active, TigerGraph stubbed on both sides |
| Graph model | ~22 node types / ~21 edge types (the Python "designed model," verified). Core hierarchy: `ProductLine → AreaProduct → Service → CodeArea → Repository`, enriched with `Team`, `Story`, `Epic`, `ADR`, `API`, `Contract`, `DriftAlert`, `HLDDAttachment` |
| Java-side schema | A separate, **more formal edge vocabulary** (`NodeLabels`, `RelationshipTypes` constants: `DEPENDS_ON`, `BELONGS_TO`, `GROUPED_IN`, `IMPLEMENTS`, `DECIDES`, …) than the Python path uses — evidence the two runtimes are genuinely distinct, not shared code |
| Uniqueness/indexes | Constraints on business keys (`Service.sealId`, `Repository.id`, `Story.key`, `Epic.key`, `ADR.id`, `CodeArea.path`, `ProductLine.id`) — loading is idempotent `MERGE` on stable business keys, safe to re-run daily |

### 2.3 Ingestion pipeline

- **Orchestration:** Jenkins (`Jenkinsfile.pipeline`), daily **02:00 UTC**, Python
  only. Flow: `checkout → pip install → discover.py --all-etp --product-id 1087 →
  load_archimedes_neo4j.py → context generation / drift / embed / S3 sync`.
  Credentials injected as Jenkins secrets (`contextgraph-neo4j-password`,
  `-bitbucket-token`, `-confluence-token`, `-pactflow-token`). CD for the Java
  server is a separate **Spinnaker** pipeline (`spinnaker-trigger.yml`).
- **`discover.py`** is a 7-step source→target orchestrator pulling from: PAT
  (Team Central/Product Catalog, ADFS auth) → `ProductLine/AreaProduct/Team/Service`
  nodes; DevX Fabric (GraphQL) → `CodeArea`; Bitbucket (multi-cluster, PAT-per-cluster)
  → `Repository`; Jira → `Story/Epic`; Confluence → `ADR`; Code Agent (an internal
  source-code-indexing service) → `API` nodes + `EXPOSES` edges.
- Beyond the 7 core steps, additional scripts (not in the primary orchestration
  count but load-bearing): Archimedes security domains, FARM security findings,
  PactFlow contracts, Harmony HLDD parsers (docx/pdf/html), incident/SNOW
  linking, blast-radius BFS precompute, drift detection, vector embedding,
  context/site page generation, S3 sync.

### 2.4 MCP servers — two exist, only one is production

This is a real "which one is real" trap the source docs call out explicitly —
worth internalizing for DryDocs' own MCP surface design:

| Aspect | `context-graph/mcp_server/` (in-repo) | `context-graph-mcp` (standalone repo) |
|---|---|---|
| Role | **Prototype / origin** | **Production, deployable** |
| Tools | Same 12, `@mcp.tool()` flat in one file | Same 12, split across `tools/` modules |
| Transport | FastMCP, stdio only, port 8500 | Dual-mode: stdio (local dev) + streamable-HTTP (ECS, port 8080) |
| Neo4j auth | Hardcoded `bolt://localhost:7687` | Env-driven; basic **or** OIDC C2C bearer |
| Inbound auth | None | IDA C2C + multi-audience JWT |
| Resilience | Bare `[{error}]` return on failure, no breaker | Circuit breaker + tenacity retry + rate limiting |
| Fallback | Neo4j-or-empty | **3-tier**: Neo4j → Java API → S3/local cache |
| Audit | None | `ToolAuditLogger` → OpenSearch ingest (ECS) |
| Verdict | Superseded, not a fork-to-merge | **Supersedes** the prototype |

**12 MCP tools, only 1 write-capable:** `triage_alert` is the sole mutating tool
(`readOnlyHint: False`) — it extracts caller SID from MCP context for
attribution but everything else in the graph stays read-only, idempotent,
closed-world. The other 11 cover repo listing, stats, drift alerts, ADRs,
incidents, contract/blast-radius graphs, and migration-impact queries. All Neo4j
tools gate behind `NEO4J_ENABLED=true`; without it the server still serves 6
cache-backed context/search/discovery tools. Inputs are validated
(`validate_identifier`, `validate_enum`, `validate_query`, `validate_limit`)
before touching Cypher — parameterized queries + allow-listing, no string
concatenation.

Resilience details worth naming for DryDocs' own future MCP hardening decisions:
circuit breaker with cooldown window, retry-on-transient-only (never retries
auth or Cypher-syntax errors), connection pool tuning (25 conns, 30s acquire
timeout, 300s max lifetime — under a load balancer's ~350s idle limit), and a
per-tool 3-step fallback chain (`graph.is_available() → server_api.is_available()
→ cache (S3/local .md, last resort)`) mirrored in a `search_context.action` field
the client can inspect to know which tier answered.

### 2.5 Config, auth, and deploy

- **No relational database anywhere.** Config lives in YAML (`application.yml` +
  env for the Java server; `apps_product_lines.yml` / `apps/*.yml` for
  product-line targets) + `.env`/Jenkins secrets for ingestion tokens +
  `eac/eacdeployapp.yaml` for deploy descriptors. Application *data/state* is
  entirely Neo4j, including a `_SYNCSTATE` checkpoint node used by the connector
  framework for incremental sync bookkeeping. Caches are disk JSON
  (`repo360/*.json` — precomputed dossiers, falling back to live Cypher on a
  miss) and an in-process `ConcurrentHashMap` for compiled `.cypher` files.
- **Auth:** ingestion side uses ADFS tokens per resource URI (JPMC's internal
  federated auth) plus Bitbucket PATs per cluster. Server side uses a Photon
  **ADFS client**, with optional **C2C IDA** (client-to-client, internal OAuth-like
  service auth) gated by `application.yml`'s `C2C_IDA_ENABLED`. The standalone MCP
  server's inbound auth is IDA C2C + a **multi-audience JWT** patch
  (`multi_audience.py`) that lets the same server accept tokens whose `aud` claim
  is either the canonical IDA resource id (SDK clients) or the bare `SERVER_URL`
  (legacy/VS Code RFC 9728 clients) — one server, two client auth styles.
- **Deploy:** production target is ECS Fargate (per `eac/eacdeployapp.yaml` and
  the MCP server's ASGI middleware stack, which is explicitly "ECS mode" —
  `ReadinessMiddleware`, `CorrelationMiddleware` for `X-Request-Id`/`X-Run-Id`
  cross-service tracing, `RateLimitMiddleware`, CORS). One open item the source
  docs flag: the repo's own infra references (`Dockerfile`, `Jenkinsfile`,
  `jib.yml`, `spinnaker-trigger.yml`) mention K8s DNS in places vs ECS Fargate
  elsewhere — unreconciled at analysis time.

---

## 3. UI deep dive

### 3.1 Confirmed: NOT Backstage

Both the doc analysis and the live screenshots confirm this explicitly and
repeatedly — no `@backstage/*` dependency, no plugin/catalog model, no
Backstage theme. It is a **bespoke React 18 SPA** (Vite, react-router-dom v6,
Zustand, D3, Mermaid) that happens to resemble a Backstage-style internal
developer portal by convention, not by inheritance. Confirming this closes an
open question DryDocs itself had going in.

### 3.2 Route / page map

| Route | Page | Purpose |
|---|---|---|
| `/products` | `ProductLinesPage` | fleet entry — product-line cards grid |
| `/products/:id` | `ProductDetailPage` | area products under a line |
| `/area-products/:id` | `AreaProductDetailPage` | services under an area product |
| `/seals/:sealId` | `SealDetailPage` | per-SEAL app detail — the primary dossier page |
| `/hierarchy` | `HierarchyPage` | D3 drill-down tree (ProductLine→…→Repo) |
| `/repo360/:repoSlug` | `Repo360Page` | full 360° view of one repo |
| `/blast-radius` | `FullBlastRadiusPage` | live multi-hop dependency blast radius |
| `/drift` | `DriftPage` | drift alerts |
| `/fleet-drift` | `FleetDriftPage` | fleet-wide drift dashboard |
| `/tech-stack` | `TechStackPage` | fleet tech-stack aggregation |
| `/network` | `NetworkPage` | inter-service (cross-SEAL) network graph |
| `/agent-demo` | `AgentDemoPage` | in-UI agent demo (calls `/api/agent`) |

`Layout` wraps all routes; index redirects to `/products`.

### 3.3 Component anatomy

`Layout`, `ExploreNav`, `Breadcrumb`, `Repo360View`, `BlastRadiusGraph`,
`HierarchyGraph` — plus a `visualizations/` folder holding the D3 canvases
(`HierarchyGraph.tsx`, a second `BlastRadiusGraph` chain view). State is a
single tiny Zustand store (`ui/src/store/index.ts`) holding one thing: a
`ViewRole` = `'developer' | 'architect' | 'product'` role toggle, read by a
top-bar selector. This is a **role-lens**, not RBAC — it doesn't gate data, it
reframes the same graph for a different audience (confirmed live: the ss1/ss2/ss8
screenshots show the role dropdown reading "Architect", "Developer", "Product"
across different pages).

### 3.4 Design system

| Aspect | Detail |
|---|---|
| Base aesthetic | **GitHub-dark developer console** — dark palette lifted almost verbatim from GitHub's Primer dark theme |
| Token mechanism | CSS custom properties on `:root`, with `:root[data-theme="light"]` override; no CSS framework (no Tailwind/MUI/Bootstrap) — hand-rolled CSS Modules per component |
| Color split | **Two-accent split**: a single **teal** chrome/brand accent (`--accent` `#2dd4bf`, topbar brand mark, active nav, focus rings) vs a **categorical graph palette** (GitHub blue/purple/red/green/amber, one hue per node type: product-line=blue `#1f6feb`, area-product=purple `#a371f7`, SEAL=red `#da3633`, project=green `#3fb950`, repo=amber `#d29922`). Deliberately keeps navigation chrome visually distinct from data encoding — a genuinely good idea. |
| Dark palette | bg `#0d1117`, panel `#161b22`, panel-2 `#1c2129`, tertiary `#21262d`, border `#2a3038`/`#30363d`, text `#e6edf3`/`#c9d1d9`, dim `#8b949e`, faint `#6e7681` |
| Light palette | Primer-light remap of the same token names: bg `#f6f8fa`, panel `#ffffff`, text `#1f2328`, accent shifts to blue `#1f6feb`/`#0969da` |
| Components | **No component library, no icon font** — "icons" are Unicode glyphs (a `◆` brand mark, `☼/☾` theme toggle). Keeps the bundle lean and CSP-simple. |
| Fonts | System font stack (`-apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, Roboto`), mono stack (`Cascadia Code, Menlo, Consolas`) for IDs/code/Cypher/tabular data. No `@font-face`, no Google Fonts — fully offline-safe. |
| Density | Base 14px/1.5, brand 15px/700, section labels 11px uppercase with `0.06em` tracking — deliberately tight, console-density over marketing polish |
| Layout | Sticky topbar (z-30) + fixed 240px sidebar (`--panel-2`, grouped nav sections: Fleet Views / Analysis / Product Lines) + scrolling main content (`flex:1`, own overflow — only inner panes scroll, app never double-scrolls) |
| Theming persistence | `data-theme` attribute on `<html>`, persisted to `localStorage`; every color is a token, so theming is a single attribute swap, no per-component conditionals |

### 3.5 API contract

- Single typed `fetch` wrapper (`ui/src/api/client.ts`), base URL from
  `window.__APP_CONFIG__.apiBase` (Spring-injected at render) — **not
  hard-coded**, so the same build is environment-portable across dev/UAT/prod.
- ~16 `GET /api/*` endpoints consumed: `getHierarchy`, `getDependencies`,
  `getDrift`, `getRepos`, `getRepo360` (richest payload — see below),
  `runAgent`, `getFleetDrift`, `getTechStack`, `getNetwork`,
  `getProductLines`, `getProductDetail`, `getAreaProductDetail`,
  `getFullBlastRadius`, `getBlastRadiusPaths`.
- **`Repo360Data`** is the single-repo "everything we know" dossier: repo/
  service/SEAL, tools (Bitbucket/Jira/Confluence links), service-to-service +
  external connections, APIs, libraries, ADRs, incidents, FARM security
  findings, drift, epics/stories, PactFlow contracts (provided/consumed),
  classifications, languages/frameworks, published/consumed endpoints,
  messaging, AWS services, deployments.
- Server-side (`UiApiController`): Cypher lives in `.cypher` files under
  classpath `neo4j/queries/ui/*.cypher` (e.g. `hierarchy-areas.cypher`,
  `hierarchy-repos.cypher`), loaded once and cached in a
  `ConcurrentHashMap<String,String>` — no ORM, reuses the shared Neo4j
  `Driver`/`SessionConfig` bean. `repo-360` additionally has a **disk cache
  dir** (`ui.repo360.cacheDir`, default `repo360/`) — precomputed JSON
  snapshots served first, falling back to live Cypher on a cache miss. Pure
  map/tree shape-transformation happens in Java (`mergeRowIntoTree`,
  `sortTree`, `buildRoot`) — the controller does shaping, not querying logic.

---

## 4. What the live UI actually shows (ss1–ss11)

Live at `context-graph.dev.aws.jpmchase.net/contextgraph/...`, fleet-scale data
confirmed on screen: **10 product lines, 217 SEALs, 3,841 repositories**.

- **Product Lines grid** (`ss2`): 10 cards (Acquisition & Enablement, Banking
  Payments, Cash & Check, Digital Channels, Engineering/Tools/Productivity,
  Fraud Assessments, Global Customer Platform, Merchant Offers, Proprietary
  Wallets & Lending, Utilities), each showing area-product / SEAL / repo counts
  and an internal numeric ID. A CCB badge marks LOB.
- **SEAL detail page** (`ss1`, "Quick Deposit," SEAL 33616): the **At-a-Glance**
  stat-tile row (73 Repositories, 71 Backend Services, 1 User Interface, 0
  Libraries/Frameworks/Databases/Kafka Topics/AWS Services, 0 Decision Records,
  0 Past Incidents, 0 Open Stories, 1 Drift Alert) — a dense, scannable
  glance-ability pattern, followed by a **Mermaid** "Where This Lives" hierarchy
  diagram (Product Catalog → LOB code → SEAL → owned repos) and an "Explore"
  link list into sub-pages (Failure reach, Components, Connections, Inter-app,
  Journeys, Compliance, Implementation, Deployment). A "Where the data came
  from" footer links straight to the Bitbucket/Jira source URLs — provenance as
  a first-class page element, not a hidden metadata field.
- **Components list** (`ss3`): every node in the SEAL (1 Service + 72
  Repositories), flat linked list, click-through to a per-node dossier.
- **Per-node dossier** (`ss4`, `cockroachdb` repo): a property table (Slug,
  Project, Service, SEAL, Team, LOB, Bitbucket link, Node Type), a **Wiring**
  section (inbound/outbound ports-and-adapters view), a **Drift Alerts** table
  scoped to that node, and a Blast Radius link.
- **Empty-state honesty** (`ss4`, `ss5`, `ss6`, `ss7` — a *consistent, repeated*
  pattern worth calling out on its own): rather than hiding or faking missing
  data, every under-populated section says so in plain language: *"No inbound
  surfaces captured (Code Agent enrichment not available for this repo
  cluster.)"*, *"No inter-SEAL edges in the graph today... Either the SEAL
  really is self-contained, or its dependencies live behind interfaces our
  parsers can't yet see (binaries, MQ, shell-outs)."*, *"No infra repos parsed
  yet for this SEAL. Run `python scripts/scan_infra_repos.py --seal-id 33616`
  to populate."* This is a deliberate design stance: absence of data is
  distinguished from absence of the *feature*, and the UI tells the viewer
  exactly which upstream enrichment step would fill the gap.
- **Cross-SEAL Network** (`ss8`): a force-directed graph of Services with at
  least one declared or observed edge, filterable by product line, with stat
  tiles (Services/SEALs in view, edges by type, nodes/edges drawn) and an
  explicit **edge-type legend**: solid = `CONNECTS_TO` (HLDD-declared), solid
  arrow = `CALLS` (code-observed), dotted = `DEPENDS_ON` (contract evidence) —
  plus a "Top hubs" most-connected ranking and raw edge tables below the
  diagram.
- **Tech Stack fleet adoption** (`ss10`): 648 frameworks / 47 languages / 4,258
  repos tracked, ranked table of frameworks by repo count with a **version
  diversity badge** per row (e.g., Spring Boot: 695 repos, 3 versions
  observed — 3.5.9/3.5.12/3.5.13) — a fast way to answer "who's still on the
  old version" across the whole fleet without clicking through repos one at a
  time.
- **Repo 360° force graph** (`ss9`): pick any repo, see every connection it has
  (color-coded by type: dependency, test framework, Jira epic/story, PactFlow
  contract, drift finding) radiating from a center node, with a right-hand
  dossier sidebar (Owning Service description, Connected Services, Active
  Epics, In-Flight Stories linked to real Jira ticket keys e.g. `CASHIM-151`).
- **Hierarchy drill-down bubbles** (`ss11`): a D3 bubble/force layout,
  `Root → Banking Payments → {22 area products}`, bubble size = child count,
  color-keyed legend (product line=blue, area product=purple, SEAL=red,
  project=green, repo=amber) — click any bubble to drill one level deeper.

---

## 5. Adopt / adapt / avoid — judged against DryDocs' locked stack

DryDocs' stack (from `docs/design/ui-exploration/site-plan.md`, locked 2026-07-17): Vite + React +
TS, Tailwind 4 + CSS custom-property tokens, ReUI/shadcn components, React Flow
for graph canvases, `drydocs-api` (FastAPI) backend via a `GraphAccess` seam, a
`QuerySpec` registry with export provenance manifests, dark-first
`#0D1520`/panel `#111B29`/brand `#D62828` token set, and a persona model
(user < steward < admin) distinct from a role *lens*.

| Pattern | Verdict | Why |
|---|---|---|
| **At-a-Glance stat-tile row** on a node dossier | **Adopt** | Directly portable to DryDocs' node inspector (right-sidebar pattern in `site-plan.md` §3) — a fixed row of count tiles (jobs, conditions, dependents, open findings) above the graph/data-frame split gives instant "how big/how healthy is this thing" context before drilling in. |
| **Role-lens (Zustand `ViewRole`)** vs DryDocs personas | **Adapt, don't copy verbatim** | Their `developer/architect/product` toggle *reframes the same read-only data* — nice, cheap idea. DryDocs' persona set (`user < steward < admin`) is a **write-permission boundary** (O12/O13), a different and more consequential axis. DryDocs should keep persona as the security boundary, but *can* borrow the lightweight "view lens" idea as a separate, purely cosmetic toggle (e.g., ops-vs-dev framing of the same Explorer graph) — just don't conflate the two concepts the way a quick copy might. |
| **Repo360 dossier pattern** vs DryDocs node inspector | **Adopt the shape, not the storage** | The "one page = everything we know about this node" aggregation (tools, connections, contracts, findings, deploys) is exactly what DryDocs' per-node inspector sidebar should do. Skip their bespoke disk-JSON cache-first design (§5.7 below) — DryDocs already has a cleaner mechanism via QuerySpec + drydocs-api. |
| **Edge-provenance legend** (`CONNECTS_TO` declared / `CALLS` observed / `DEPENDS_ON` contract) | **Adopt — maps directly onto DryDocs trust tiers** | This is the single strongest transferable idea in the whole system. Their 3-way legend (declared/observed/contract-evidence) is structurally identical to DryDocs' VERBATIM (source-of-record, e.g. Control-M XML)/GROUNDED (derived, e.g. joined via SEAL)/SYNTHESIZED (LLM-inferred, e.g. `ddcontext`) trust tiers. DryDocs should put an equivalent **visible legend + verdict badge** (MATCH/UNDECLARED/UNBUILT-style) on every graph canvas and data-frame row wherever mixed-trust data is shown — the `QuerySpec.classification` + `trust_tiers_present` fields already in the export manifest (`site-plan.md` §4) are the right substrate; this just says "surface that in the live UI too, not only in the export manifest." |
| **Empty-state honesty** copy pattern | **Adopt verbatim as a UX convention** | "No X captured (Y enrichment not available for this cluster) — run `script.py` to populate" is a genuinely good pattern: never hide missing data behind a blank section, always name *which* upstream step would fill it. DryDocs' equivalent: when a QuerySpec returns zero rows because a source hasn't been ingested yet, say so and name the loader/backlog item, not just "no data." |
| **Disk-cache fallback tiering** (repo360 JSON → live Cypher; MCP's Neo4j→API→S3 3-tier) | **Adapt selectively** | Reasonable resilience pattern for a *read-serving* API under load, but DryDocs' `drydocs-api` doesn't yet have context-graph's traffic/SLA profile to justify the complexity. Worth revisiting if/when DryDocs adds a production MCP server with its own uptime target — borrow the *fallback chain + client-visible "which tier answered" field* idea then, not now. |
| **Cypher externalized per-view** (`.cypher` files in classpath, cached in a `ConcurrentHashMap`) vs DryDocs' `QuerySpec` registry | **DryDocs' approach is stronger — do not downgrade to theirs** | Their model keeps Cypher out of Java code (good) but each `.cypher` file is still a bespoke, unversioned, unclassified query with no declared column contract and no link to an export format. DryDocs' `QuerySpec` (`id`, versioned like a loader, `database`, `params`, `columns: ColumnDef[]`, `classification`) is a strict superset: it gets you the same "no Cypher in code" benefit *plus* a versioned contract, a classification tag enforced at the boundary, and export-manifest provenance for free. Keep DryDocs' design; there's nothing to backport from theirs here. |
| **Role dropdown as the only global state** (single Zustand store) | **Note, not adopt/avoid** | Reflects a genuinely small UI surface (12 routes, one cross-cutting concern). DryDocs' UI is larger (9 modules + persona-gated admin/mappings routes) and will need more shared state (theme, env toggle, selection linking between graph pane and data frame per `site-plan.md` §3) — not a criticism, just don't expect a single-store pattern to scale as-is. |
| **Two parallel ingestion implementations** (Python prod + dormant Java connector-framework) | **Avoid** | Don't pre-build a "future" ingestion path speculatively before the current one is fully proven — it accretes maintenance surface (13 connector modules, a second edge-type vocabulary, two graph-backend adapter factories) for a path that has never been invoked in production. |
| **Aspirational docs drift** (README claims Java 25 / 9 MCP tools / `ui/api.py`; code says Java 21 / 12 tools / no such file) | **Avoid** | A direct instance of the DryDocs working agreement "verify before asserting" — treat any doc as a hypothesis until checked against source. Worth a lightweight doc-drift check as part of DryDocs' own render/snapshot ritual (already partially covered by the stale-render check in `CLAUDE.md` §0). |
| **Hardcoded creds/URLs in the prototype** (`mcp_server/server.py`'s `bolt://localhost:7687`) | **Avoid** | Even in a "just the prototype" component, hardcoded connection strings are the kind of thing that leaks into a demo, a screenshot, or a copy-paste into the production repo. DryDocs' env-only config discipline (`config/`, no real values in commits) is the correct default from day one. |
| **`/api/**` unauthenticated** (Java server, live-verified 2026-07-15 per source code comment) | **Avoid / flag as risk, not a design choice** | Not an intentional pattern to weigh — a live gap in someone else's production system. Relevant to DryDocs only as a checklist item: when `drydocs-api` moves toward any externally-reachable deployment, auth must land *before* the API is reachable, not as a follow-up. |

---

## 6. Gap / risk notes

### Where context-graph is ahead of DryDocs today

- **Actually deployed and load-bearing.** One production application (their MCP
  server, ECS-hosted) already depends on it; DryDocs' equivalent UI/API surface
  is still pre-build (Phase P0 in `site-plan.md`).
- **Unattended daily pipeline in production.** Jenkins runs the Python ingest
  end-to-end every night without human intervention; DryDocs' ingestion is
  still manually run per source.
- **Agent integration is live in the product**, not just a backend capability —
  `AgentDemoPage` puts a working agent (tool calls + verdict) directly in the
  UI, and the standalone MCP server is a real, audited, dual-transport, C2C-authenticated
  service already serving JPMC's internal MCP Directory. DryDocs' agent/MCP
  layer (ADK 2.0) is explicitly deferred to a later phase.
- **Fleet-scale real data.** 3,841 repos / 217 SEALs / 10 product lines is a
  genuinely large graph exercising real query-performance and UI-density
  problems DryDocs hasn't hit yet at its current scale.
- **A working "declared vs observed" reconciliation pipeline** (`compare-seal-connections`
  stage) that runs on a schedule and produces MATCH/UNDECLARED/UNBUILT verdicts
  automatically — DryDocs has the trust-tier *concept* but not yet an automated
  reconciliation job that compares two independently-sourced views of the same
  edge.

### Where DryDocs is ahead

- **Governance is designed in, not absent.** HITL gates
  (`03-hitl-sme-flow.md`), a documented sensitivity classification
  (`config/classification.yaml`, `PUBLISH-BOUNDARY.md`), and a
  source-of-truth precedence config (`config/precedence.yaml`) have no
  equivalent anywhere in context-graph — there is no gate concept, no
  classification tag on any node/edge, and no precedence rule when two
  sources disagree.
- **`QuerySpec` + export provenance manifest** is a stronger, more disciplined
  version of context-graph's per-view `.cypher`-file pattern (§5) — versioned,
  classified, and self-documenting at export time (`cypher_sha256`,
  `trust_tiers_present`, `classification` banner). context-graph has no export
  feature at all in the surfaced UI.
- **Ontology rigor.** DryDocs' four-layer model (taxonomy → ontology →
  knowledge graph → context graph) and its PROV-O/ORG grounding is a
  considerably more deliberate modeling discipline than context-graph's
  "~22 node types / ~21 edge types, the designed model" — which reads as
  organically grown rather than standards-grounded. context-graph's Java-side
  edge vocabulary being *richer* than its Python-side vocabulary (§2.2) is a
  symptom of this: the two runtimes disagree on the model itself.
- **Explicit "verify before asserting" discipline** is written into DryDocs'
  working agreements; context-graph's own analysis surfaced multiple doc/code
  drift instances (Java version, tool count, a deleted dev-server file) that a
  documented discipline would have caught earlier.
- **Single source of truth for config precedence.** context-graph has no
  documented answer for "BMC-equivalent baseline vs internal override" — its
  config is scattered across YAML/env with no declared precedence order,
  whereas DryDocs' `config/precedence.yaml` makes this explicit.

---

*Compiled from three analysis sessions + 11 live-UI screenshots, 2026-07-23. No
credentials, tokens, or secrets are recorded in this document. Real Jira ticket
keys, SEAL IDs, and the dev hostname are retained as grounding evidence per the
internal/ classification rules in `CLAUDE.md` §3 — do not lift them into any
publishable surface.*
