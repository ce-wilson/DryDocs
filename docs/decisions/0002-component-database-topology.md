# ADR 0002 — Component & database topology: modular components over isolated graphs

> **Database names below are the ORIGINAL ones and are superseded — the decision stands,
> only the identifiers changed.** This ADR says `drydocs_context` and `drydocs_all`; the
> topology actually deployed at G6/G7 uses the `dd*` convention — **`drydocs`,
> `ddlineage`, `ddcontext`, `ddall`** — as created by
> [`drydocs_core/schema/provisioning/01_databases.cypher`](../../drydocs_core/schema/provisioning/01_databases.cypher).
> The rename is on the record in [ADR 0006 §1](0006-docmeta-component-and-doc-graph.md)
> ("the plan's working name predates the deploy") and the `config/gate-log.md` dd*-convention
> entry, which also adds the planned `dddocs`. The body text is left as written — an accepted
> decision record is not rewritten after the fact — but nothing should be COPIED from it as a
> live name. `tests/unit/test_database_names.py` enforces the deployed set in code
> (added 2026-07-26, backlog G28, after `drydocs_deepdoc.DATABASE` was found still pointing at
> a database provisioning never creates).

> **AMENDED 2026-08-18 — gate `document-content-topology` (G32), SIGNED 32/32: the
> CONTENT topology folds to ONE database.** D1's decision record stands as history;
> its multi-database conclusion is superseded FOR THE CONTENT AXIS by an argument it
> never weighed: retrieval. The product is now an agent answering support questions,
> and an agent that cannot see captured context beside the structured graph in one
> vector search fails silently and constantly, where the isolation failure D1 priced
> is loud and rare. The trust distinction D1 bought with a wall was ALREADY governed
> inside one database for the graph's most governed edges — the manual pins run on
> per-edge `origin` + precedence + required rationale, never on the boundary — so
> the fold extends a shipped mechanism (see the gate's §F). `ddschema` stays its own
> database (G51; ADR 0011 clause 2 deliberately never fires). `ddcontext`'s charter
> restates per the gate's §B: the watermark re-keys on each source's declared
> `trust_default`, never on database name. **THE NAMING RULE (gate Q8), recorded as
> a rule and not one rejection: `drydocs` is the ORIGINAL database; `dd*` names are
> its EXTENSIONS — a proposed database whose contents belong in the original fails
> this test, which is how `dddocs` was rejected and retired.** Apply is staged
> (backlog G102, guards-first); nothing moved at signing.

```yaml
status: ACCEPTED        # PROPOSED | ACCEPTED | SUPERSEDED
date: 2026-06-26
accepted_on: 2026-06-26
accepted_by: chad.wilson (SME gate)
deciders: [chad.wilson, SME-gate]
layer: cross-cutting    # architecture; affects layers 3 (KG) and 4 (context)
affects:
  - drydocs/            # → monorepo: drydocs-core + component packages
  - external repo: ce-wilson/DryDocs-v0-archive@controlm-spinoff — SUPERSEDED 2026-07-10
    # (G3 / 0002-B DONE: remediation re-homed as drydocs_remediation on drydocs_core;
    #  stop maintaining the archive branch — it remains readable as source material only)
  - external repo: ce-wilson/depgraph@feat/controlm-lineage (PR #2) — SUPERSEDED 2026-07-11
    # (G9 / 0002-C DONE: the lineage assets re-homed as drydocs_lineage on drydocs_core;
    #  stop maintaining the branch as a lineage source — readable source material only.
    #  depgraph's base/python-import layer is untouched by this record.)
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

## Residency clarification (2026-07-26, backlog G30) — where curated lineage lands

**Not an amendment. D1 and D2 stand as written: `drydocs-lineage` writes curated ground
truth to `drydocs`.** Recorded because the codebase had drifted into believing both answers
at once, and the drift was invisible while the lineage writer stayed gate-bound.

**What drifted.** G1 provisioning (2026-06-28, two days after this ADR was accepted) created
a *fourth* database, `ddlineage`, commented "cross-platform lineage (drydocs-lineage)" — a
name D1's three-row table never contemplated. The ADR was never amended to match. Each half
of the codebase then followed a different source: `drydocs_lineage/writer.py` followed the
ADR (`DATABASE = "drydocs"`, enforced by `TrustBoundaryError`), while four `drydocs_api`
query specs followed provisioning (`database="ddlineage"`). Those four specs read a database
nothing writes. Nothing produced wrong answers — the writer is gate-bound until the four
`m3_*` vocabulary ids flip `active`, and the specs honestly return zero rows — so it would
first have bitten on the first live curated write.

**Why D1/D2 win, rather than the ADR being amended to match provisioning:**

1. **The reason the boundary exists is the trust axis** — "the trust axis IS the DB
   boundary." Curated lineage is VERBATIM/GROUNDED, the same tier as the main load.
   Separating it serves no part of the rationale that justified paying for multi-DB.
2. **0002-C §5 already asserts it, ticked and tested** — *"Writes ground truth only:
   `drydocs-lineage` opens write transactions only against `drydocs` — the D2 trust
   boundary, asserted structurally."*
3. **It is not a constant flip.** `write_curated` **MATCHes** `:ControlMJob {folder_id,
   job_id}` and deliberately never MERGEs them — the M3 load owns those nodes, and a
   lineage-created job stub would violate the `m3-verify` "every job has a folder"
   invariant. A Neo4j transaction cannot span databases, so from `ddlineage` those MATCHes
   would match nothing and **every job-endpoint edge would vanish silently** (an unmatched
   MATCH yields zero rows, not an error). Moving lineage would first require a
   `:ControlMJob` proxy-node backbone in `ddlineage` and a redefinition of what "the M3 load
   owns them" means. That is a design, not a rename.

**What changes:** the four specs (`lineage.hops.v1`, `lineage.data-assets.v1`,
`lineage.schema-definition.v1`, `runbooks.series.v1`) repoint to `drydocs`. `ddlineage`
stays provisioned and aliased into `ddall`, documented as provisioned-for-later.
`tests/unit/test_database_names.py` now asserts read targets and write targets agree, so a
spec can never again read a database nothing writes.

**Named trigger to revisit** (as an amendment, through the SME gate — not by drift): the
docmeta gate (2026-07-18, ADR 0006 §b) adopted a `dddocs` component database on the G1
pattern and *re-targets* the bmc-docs corpus out of `drydocs`. If component-per-database
proves out there, and lineage grows a proxy-node backbone of its own, reopen this. Deferring
is the cheap direction: `ddlineage` is empty, so choosing it later costs a design, not a
data migration.

## Topology amendment (2026-08-03, backlog G51) — `ddschema`, the schema meta-graph database

**D1 gains a fifth database.** The SME direction of 2026-08-02 ("2 different graphs")
put the schema meta-graph — exemplar nodes carrying REAL labels beside `:SchemaMeta`,
read by `db.schema.visualization()` — into its own database, `ddschema`, written only
by `drydocs bootstrap-schema-graph`. It cannot live in `drydocs`: the exemplars carry
only `name`, and `drydocs`' NODE KEYs enforce property EXISTENCE, so bootstrap there
fails by construction (proven live on a throwaway label before the verb was re-homed).
`ddschema` is deliberately **not** aliased into `ddall` — it describes the schema, not
the estate, and a support query federating exemplars with real jobs would present
labels as data. Its single constraint (`schemameta_name`) lives in
`schema_graph.cypher`, not `constraints.cypher`, so `EXPECTED_CONSTRAINTS` does not
count it. Provisioned in `01_databases.cypher` at G51 — which also widened
`test_database_names.py`'s guard after `SCHEMA_GRAPH_DATABASE` walked past its
exact-identifier match while naming a database nothing created.

## Topology amendment (2026-08-04, backlog X1) — `ddlineage` retired

**D1 loses the database it never asked for.** User ruling 2026-08-04 (in-chat, recorded
in `config/gate-log.md`): `ddlineage` is removed from the provisioned topology. The
deployed set becomes **`drydocs`, `ddcontext`, `ddall`, `ddschema`**. This supersedes
the residency clarification's closing disposition ("stays provisioned and aliased into
`ddall`, documented as provisioned-for-later") — that section otherwise stands as
written, and the history above it is not rewritten.

**The standing evidence, unchanged since G30 and merely acted on now:** nothing writes
`ddlineage` and nothing reads it. The lineage writer pins `DATABASE = "drydocs"` and
raises `TrustBoundaryError` on any other binding (D2, asserted structurally per
0002-C §5); the four reader specs were repointed to `drydocs` at G30; the
`drydocs_api` read-set allow-list deliberately excludes it; and
`tests/unit/test_database_names.py` proves every read target has a writer. Since G30
its only function has been to exist, empty, on every provisioned host — a standing
invitation for the next drift class (G28's `drydocs_deepdoc.DATABASE` and the G30 spec
drift both grew in exactly this gap between "provisioned" and "used").

**What retirement answers — and what it deliberately does not.** It answers where the
database went. It does **not** answer the residency clarification's deferred design
question (a `:ControlMJob` proxy-node backbone in a lineage database, and a redefinition
of "the M3 load owns those nodes"); that question transfers intact to the named
revisit trigger, which stands: if component-per-database proves out at `dddocs` and
lineage grows a proxy backbone of its own, reopen — through the SME gate, as an
amendment. The only change to the reopening cost is direction: it now *recreates* the
database (one `CREATE DATABASE ... IF NOT EXISTS` plus the `ddall` alias line) rather
than finds it waiting. The ADR's own accounting priced this: "`ddlineage` is empty, so
choosing it later costs a design, not a data migration" — an empty database was never
the expensive part, and keeping one provisioned bought nothing the DDL diff doesn't.

**Enactment (owned by the Epic X items, not this record):** X2 sweeps the repo's live
surfaces (provisioning DDL + `ddall` alias, the CLI sweep tuple, the
`test_database_names.py` topology anchor 5 → 4, renders, and the port-ledger step
carrying the company-side caution — their `ddlineage` exists live and drops on their
side, by their hand). X3/X4 drop it per machine, each behind a zero-node emptiness
probe: a non-empty probe is a defect report, not a cleanup, because it would mean
something wrote a database nothing should write.

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
7. ~~Route through the SME gate (`docs/restructure/03-hitl-sme-flow.md`) to move this ADR
   `PROPOSED → ACCEPTED` before any wiring.~~ **DONE 2026-06-26** — accepted as-is by the SME;
   Enterprise edition committed (D1 firm, Community fallback stays a rejected alternative only).
   Gate run logged in `config/gate-log.md`. The extraction (0002-A) and rebase (0002-B) plans are
   now ungated; follow-ups 1–6 are ready to groom into `backlog.yaml`.
