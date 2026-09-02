# Modular Architecture Plan — DryDocs Core + Independent Components, Grounded vs Uncertain Graphs

> Companion to `issue-driven-capture-loop.md`. Plans modularity BEFORE wiring (per request).
> Neo4j guidance fetched 2026-06-26 from operations-manual (multi-database, composite databases).
> ADR-worthy → offer to formalize as ADR 0002 (repo already has ADR 0001).
> All examples illustrative/synthetic (CLAUDE.md §3).

---

## 0. Component map (confirm this reading)

| # | Component | Trigger | Reads | Writes | Reliability | DB target |
|---|-----------|---------|-------|--------|-------------|-----------|
| **Main** | **DryDocs core** | daily/weekly schedule | Control-M export, Oracle, etc. | structured KG | ground truth | `drydocs` (primary) |
| **1** | **Control-M remediation** (rebase `controlm-spinoff`) | repeated failures | `drydocs` + run history | **Jira tickets only** | n/a (no graph write) | none (Jira = SoR) |
| **2** | **Dependency-graph extension** (cmd-line lineage) | support member, phased | `drydocs` jobs/scripts | structured lineage | reliable (curated) | `drydocs` (phased load) |
| **3** | **On-demand deep documentation** | failure needs depth | `drydocs` + sources | deep/uncertain context | **may be unreliable** | **`drydocs_context` (own DB)** |

**DECIDED 2026-06-26:** **two separate components** (not one/two-modes). C2 (`drydocs-lineage`,
proactive/curated → `drydocs`) and C3 (`drydocs-deepdoc`, reactive-on-failure/uncertain →
`drydocs_context`) are distinct packages & processes. Their **overlapping command-line/lineage parsing
lives in `drydocs-core`**; each component is thin and owns only its trigger + destination + trust
handling. Edition = **Enterprise**. Repo = **monorepo + `drydocs-core`**.

## 1. Neo4j guidance (the basis for the DB topology)

From the operations manual (quoted):
- **Multi-database:** a DBMS "can manage multiple isolated databases." Each is "an administrative
  partition" with its own transaction domain — "a transaction cannot span across multiple databases."
  **Edition limit:** Community = **exactly one** standard database; **Enterprise = unlimited.**
- **Composite databases:** "the means to access this partitioned data or graphs with a single Cypher
  query"; they "do not store data independently" — they hold **aliases** to constituent databases
  (local or remote). **Write rule:** they "allow only transactions with queries that read from
  multiple graphs, or read from multiple graphs and write to a single graph" — i.e. **read-many,
  write-one; no cross-DB writes.** Use cases: **federation** (disjoint graphs queried together) and
  sharding. Cross-graph linkage uses the **proxy-node pattern** (same label + an id property).

**Why this fits your intent exactly:** isolation keeps unreliable data from polluting ground truth;
composite federation lets a support query still see both at once; write-one preserves the rule that
ground truth is only written by trusted loaders.

## 2. Database topology (the core decision)

```
DBMS (Neo4j Enterprise)
├── drydocs            ← GROUND TRUTH. Main loads + Component-2 curated lineage. Trusted loaders only.
├── drydocs_context    ← UNCERTAIN. Component-3 on-demand deep docs. Wipe/rebuild freely. Trust=property.
└── drydocs_all        ← COMPOSITE (no own data). Aliases → {drydocs, drydocs_context}.
                          Support agents READ the union; WRITES still land in exactly one constituent.
```

- **Trust axis ↔ DB boundary** (the clean mapping): VERBATIM/GROUNDED data → `drydocs`;
  SYNTHESIZED/uncertain → `drydocs_context`. **Promotion** uncertain→ground-truth happens only via the
  HITL gate (`status: proposed`→loader), which means a *write to `drydocs`* — never an in-place edit
  across DBs.
- **Cross-DB linkage:** both DBs carry `:DataAsset {assetId}` / `:ControlMJob {jobId}` with the same
  URN. The composite joins them on that id (proxy-node pattern) — so `drydocs_context` can reference a
  real job without copying it.
- **Edition: DECIDED = Enterprise** → true multi-DB + composite as drawn above. (Community single-DB
  fallback no longer needed; recorded in ADR 0002 only as a rejected alternative.)

## 3. Code modularity (most overlaps, not all)

**Monorepo, shared core, thin components.** One repo, a `drydocs-core` package every component depends
on; each component is its own package with its own entrypoint and run cadence.

```
drydocs/                      (monorepo)
├── core/        drydocs-core      ← shared: models/adapters (Control-M parse, driver,
│                                     URN builders, ontology vocab, classification,
│                                     §-format read/write, AND the shared cmd-line/lineage
│                                     parser used by C2 & C3). NO component logic.
├── load/        drydocs-load      ← Main: scheduled structured loads → drydocs
├── remediation/ drydocs-remediation ← Component 1 (rebased spinoff): failures → Jira
├── lineage/     drydocs-lineage   ← Component 2: proactive cmd-line lineage → drydocs (curated)
└── deepdoc/     drydocs-deepdoc   ← Component 3: on-failure deep dive → drydocs_context (uncertain)
```

**Dependency rule (prevents tangling):** components depend **only on core**, never on each other. The
shared lineage parser lives in `core`; C2 and C3 each wrap it with their own trigger, destination DB,
and trust handling. Component 1 (the spinoff) **rebases by re-homing its Control-M parsing onto
`drydocs-core`** and keeping only its remediation logic.

**Run-independence:** each component is a separate process / schedule / trigger — main on cron,
remediation on failure-pattern detection, depgraph on demand. They communicate through the **graph and
Jira**, not in-process calls. That is the modular seam.

## 4. App-layer discipline ("don't store too much at the application layer")

**Principle: Neo4j is the system of record; the app layer is stateless transformation.** The Python
layer parses → maps → loads → queries. It must not become a second store.

Rules:
- **No long-lived app-side state or data caches.** Anything worth keeping is a graph property
  (provenance, trust, classification, reliability) or a machine-first §-file artifact — not app memory
  or a side DB.
- **Reliability/trust live in the graph, not the code.** Component 3's uncertainty is a property in
  `drydocs_context`, queryable and auditable — not a flag buried in app logic.
- **Config stays declarative and thin** (`config/`): precedence, source-registry, mappings. Business
  data never lives in config.
- **Remediation is stateless:** it re-derives "repeated failures" from run history each cycle; **Jira
  is the system of record** for handoffs (open/in-prod/done). No app-side ticket store.
- **The §-format reference files are staging/handoff, not state** — internal ones gitignored
  (`drydocs/data/...`), public ones sanitized. They feed loaders; they are not the store.

Net: the app can be redeployed or rebuilt with zero data loss because **all durable knowledge is in
Neo4j (or Jira)**. That is the test for "not too much at the app layer."

## 5. Per-component contracts

### Main — DryDocs core loads
- In: Control-M/Oracle exports. Out: `drydocs`. Cadence: daily/weekly. Pure layers 1→3 pipeline.
- Picks up Component-1 remediations automatically once the prod Control-M change appears in the export.

### Component 1 — Control-M remediation (rebase the spinoff)
- In: `drydocs` (lineage/config) + run/failure history. Out: **Jira tickets** to source app teams.
- Loop: detect repeated, Control-M-fixable failure → diagnose → propose change → Jira → dev implements
  → prod → next main load reflects it → ticket closed.
- **Writes no graph.** Rebase = re-home its Control-M parsing onto `drydocs-core`; keep remediation
  rules. Cleanest module — read + emit, no shared write surface.

### Component 2 — `drydocs-lineage` (proactive, curated)
- In: `drydocs` jobs + the **job command line** (→ scripts → files → deeper deps). Out: `drydocs`.
- Trigger: support member, **phased** as time allows. Reviewed → ground-truth grade.
- Wraps the shared `core` lineage parser; its job is curation + phased loading into the primary DB.

### Component 3 — `drydocs-deepdoc` (reactive, uncertain)
- In: `drydocs` + incident sources. Out: **`drydocs_context`** with `reliability`/`trust` properties.
- Trigger: a failure that needs deeper documentation than exists. Data **may be unreliable** → stays
  isolated; **promoted to `drydocs` only via the HITL gate.**
- Wraps the **same** `core` lineage parser as C2 — that shared dependency is exactly the "overlaps but
  not all"; the not-all is the trigger, destination DB, and trust handling, which each component owns.

## 6. How a support query uses it (the payoff)

A support agent asks the composite `drydocs_all`: *"what feeds POSITIONS and is any of it uncertain?"*
The single Cypher reads `drydocs` (trusted lineage) **and** `drydocs_context` (on-demand uncertain
deps), labels each result by source DB / trust, and never writes across them. Ground truth stays clean;
context is available when needed; the boundary is explicit in every answer.

## 7. Decisions (DECIDED 2026-06-26) → next action
- **D1 — Edition: Enterprise.** True multi-DB (`drydocs` + `drydocs_context`) + `drydocs_all` composite.
- **D2 — Components 2 & 3: two separate components** (`drydocs-lineage`, `drydocs-deepdoc`), sharing
  the `core` lineage parser.
- **D3 — Repo shape: monorepo + `drydocs-core`** + 4 component packages; spinoff rebased as
  `drydocs-remediation`.

**Next action:** formalize as **ADR 0002 (component & database topology)** recording D1–D3 + rejected
alternatives, then a thin **`drydocs-core` extraction plan** + the **spinoff rebase checklist**. Wiring
follows ADR acceptance.
