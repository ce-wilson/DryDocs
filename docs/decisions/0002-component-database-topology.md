# ADR 0002 — Component & database topology: modular components over isolated graphs

```yaml
status: PROPOSED        # PROPOSED | ACCEPTED | SUPERSEDED
date: 2026-06-26
deciders: [chad.wilson, SME-gate]
layer: cross-cutting    # architecture; affects layers 3 (KG) and 4 (context)
affects:
  - drydocs/            # → monorepo: drydocs-core + component packages
  - external repo: ce-wilson/DryDocs-v0-archive@controlm-spinoff (to be rebased)
  - deployment: Neo4j edition (Enterprise) + database provisioning
supersedes_plan: SDLC-Docs/extracted/modular-architecture-plan.md
```

## Context

DryDocs is growing from a single batch loader into a small **family of processes** that share most
code but differ in trigger, write target, and — critically — **data reliability**:

- **Main load** — daily/weekly scheduled ingestion building the structured, **ground-truth** graph
  (actual `USED`/`GENERATED`/`ORCHESTRATES` relationships).
- **Control-M remediation** — an independent process (today the `controlm-spinoff` branch of the
  archived `ce-wilson/DryDocs-v0-archive`) that detects repeated, Control-M-fixable job failures and
  hands them to source application teams as **Jira tickets**; once the prod change lands, the next main
  load reflects it.
- **Dependency-graph extension** — deepens job lineage starting from the **job command line**; built
  proactively and incrementally by a support member; **structured/reliable**, loaded in phases.
- **On-demand deep documentation** — the same dependency analysis run **reactively when a failure needs
  more documentation than exists**; its output **may or may not be reliable**.

Two forces drive this ADR. (1) **Reliability must not commingle:** uncertain, failure-time data cannot
be allowed to pollute the ground-truth graph, but it must still be **available for support context**.
(2) **Code overlaps but is not identical:** we want shared code without the components tangling into
each other, and we must avoid the anti-pattern of **accumulating durable state in the application
layer** instead of the graph. This ADR fixes the component boundaries and the database topology before
any wiring.

## Decision

**Three databases on Neo4j Enterprise, a monorepo with a shared core, and four thin components — with
the trust axis mapped onto the database boundary.**

### D1 — Database topology (Neo4j Enterprise multi-database + composite)

| Database | Role | Written by | Trust |
|---|---|---|---|
| `drydocs` | **Ground truth** — structured KG | main load + `drydocs-lineage` (curated) | VERBATIM / GROUNDED |
| `drydocs_context` | **Isolated uncertain** context graph | `drydocs-deepdoc` (on-demand) | SYNTHESIZED / unverified |
| `drydocs_all` | **Composite** (no own data) — aliases → the two above | n/a (read federation) | mixed, labelled by source |

- Neo4j multi-database gives each DB its own transaction domain — *"a transaction cannot span across
  multiple databases."* Uncertain data in `drydocs_context` therefore **cannot** be written into
  `drydocs` by accident.
- The composite `drydocs_all` lets a single support query **read both** while the platform enforces
  *"read from multiple graphs, write to a single graph"* — no cross-DB writes.
- **Cross-DB linkage = proxy-node pattern:** both DBs carry `:DataAsset {assetId}` / `:ControlMJob
  {jobId}` on the same DryDocs URN; the composite joins on that business key — `drydocs_context`
  references a real job without copying it.
- **Promotion** uncertain → ground truth is a *write to `drydocs`* through the **HITL gate**
  (`status: proposed` → loader), never an in-place cross-DB edit. **The trust axis IS the DB
  boundary.**

### D2 — Two separate dependency-graph components (not one capability in two modes)

- `drydocs-lineage` — **proactive/curated**, phased, writes ground truth to `drydocs`.
- `drydocs-deepdoc` — **reactive on failure**, writes uncertain context to `drydocs_context` with
  `reliability`/`trust` properties.
- They **share the command-line/lineage parser in `drydocs-core`**; each owns only its trigger, write
  target, and trust handling. This is the literal "overlaps, but not all."

### D3 — Monorepo + `drydocs-core`; app layer stays stateless

```
drydocs/ (monorepo)
├── core/        drydocs-core        ← shared models/adapters, URN builders, ontology vocab,
│                                       classification, §-format I/O, shared lineage parser. No component logic.
├── load/        drydocs-load        ← main scheduled load → drydocs
├── remediation/ drydocs-remediation ← rebased controlm-spinoff: failures → Jira (no graph write)
├── lineage/     drydocs-lineage     ← C2: curated cmd-line lineage → drydocs
└── deepdoc/     drydocs-deepdoc     ← C3: on-demand deep dive → drydocs_context
```

- **Dependency rule:** components depend **only on `core`**, never on each other; they integrate
  through the **graph and Jira**, not in-process calls.
- **Stateless app layer:** Neo4j is the system of record for knowledge; **Jira is the system of record
  for remediation handoffs.** No app-side data caches or side stores. Reliability/trust/provenance are
  **graph properties**, not application state. Test: any component can be rebuilt with zero data loss.

## Options Considered

### D1 alternatives — where uncertain data lives
| Option | Complexity | Cost | Isolation | Verdict |
|---|---|---|---|---|
| **Enterprise multi-DB + composite** (chosen) | Med | Enterprise license | **Strong** — separate transaction domains | **Chosen** |
| Community single DB + `reliability` property + `:Candidate` label namespace | Low | Free | Weak — same DB, easy to query wrong | Rejected — commingles trust; one bad query promotes noise |
| Separate DBMS instances + app-side join | High | High ops | Strong | Rejected — app-layer join violates D3; composite does this natively |

### D2 alternatives — dependency-graph shape
**One capability, two `--mode` flags** — *Rejected.* Convenient, but a single process writing to either
the ground-truth or the uncertain DB depending on a flag is exactly the commingling risk D1 removes; a
flag bug crosses the trust boundary. Two components make the boundary structural.

### D3 alternatives — repo shape
**Polyrepo (one repo per component, core published as a dependency)** — *Rejected for now.* Stronger
isolation but heavy version/dependency management for a small team; the monorepo + `core` gives DRY
sharing with independent run/deploy. Revisit if a component needs an independent release cadence.

## Trade-off Analysis

The central trade is **license cost (Enterprise) vs. structural trust isolation.** We accept the
Enterprise cost because the project's entire value proposition is *grounded, non-hallucinating* answers
(see `feasibility-memo-context-sufficiency.md`): allowing uncertain data to share a transaction domain
with ground truth would undermine that at the storage layer, where it is hardest to police. Multi-DB
moves the guarantee from discipline (a property everyone must remember to filter on) to **physics**
(a transaction literally cannot cross). The composite database then buys back the convenience —
support still gets one-query federation — without buying back the risk.

## Consequences

**Positive**
- Uncertain data is **structurally** unable to corrupt ground truth; promotion is an explicit,
  gated write.
- Support gets a single federated read surface (`drydocs_all`) without cross-DB write exposure.
- Shared `core` keeps the overlap DRY; components stay independently runnable and testable.
- Stateless app layer → trivially redeployable; no hidden state to migrate or lose.
- The archived `controlm-spinoff` gets a clean home (`drydocs-remediation`) instead of drifting.

**Negative / trade-offs**
- **Requires Neo4j Enterprise** (Community allows exactly one DB). Real license cost.
- Composite queries run client/server (Bolt/HTTP), not embedded; remote constituents (if ever used)
  add credential management.
- A monorepo with a shared `core` needs packaging discipline (clear public API, no component→component
  imports) or the modular seam erodes.

## Rollout state (2026-06-26)

`drydocs` (core/ground-truth DB) is **still in active development — created/tested/destroyed
repeatedly**, not production. `drydocs_context` **can be written now** precisely because it is isolated
(D1). This is safe and requires no change to the design, because:

- Context references core **only by business-key URN** (`assetId`/`jobId`), never internal node IDs, so
  `drydocs_context` records **survive every core destroy/rebuild** and **re-link automatically** through
  the composite once core exists again.
- While core is ephemeral, a composite query may find a context node whose core target is **temporarily
  absent** — treat that as *"core target not currently present,"* not an error. (This is itself a
  graceful-degradation signal, per `issue-driven-capture-loop.md` §6.)
- **Promotion is paused:** do **not** promote `drydocs_context` → `drydocs` until core stabilizes — you
  don't write ground truth into a DB you are still destroying. Capture context freely now; gate
  promotion later.

## Follow-up (small, bounded)

1. **Provision now:** `drydocs_context` (writable) and the `drydocs_all` composite with constraints/
   indexes on `assetId`/`jobId` (proxy-node keys). Keep `drydocs` as the **ephemeral dev DB** it is
   today — re-create/destroy freely; defer treating it as a provisioned production DB until core is
   stable. Hold promotion (follow-up 5) until then.
2. **Extract `drydocs-core`** from current `drydocs/` (models, adapters, driver, URN, §-format,
   classification, lineage parser); leave loaders as `drydocs-load`. Thin extraction plan first.
   → **plan: `docs/decisions/0002-a-drydocs-core-extraction-plan.md`.**
3. **Control-M remediation (`drydocs-remediation`).** Rebase **planned in
   `0002-b-spinoff-rebase-checklist.md`** (re-home onto `drydocs-core`; reads `core` API, writes no
   graph, emits Jira only). **Execution happens in a separate module/effort**, not this main session,
   and is gated on 0002-a being DONE; 0002-b tracks it.
4. **Scaffold** `drydocs-lineage` and `drydocs-deepdoc` as separate packages sharing the core parser;
   `deepdoc` targets `drydocs_context` and stamps `reliability`/`trust`.
5. Record the **promotion path** (`drydocs_context` → HITL gate → `drydocs`) in
   `docs/restructure/03-hitl-sme-flow.md`.
6. Add a "considered & rejected" note (Community single-DB, two-mode capability, polyrepo) so the
   alternatives are not re-litigated.
7. Route through the SME gate (`docs/restructure/03-hitl-sme-flow.md`) to move this ADR
   `PROPOSED → ACCEPTED` before any wiring.
```
