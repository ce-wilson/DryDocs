# DryDocs — The Whole-Project Review

**Project review · Rev 1 · 2026-07-14 · commit `97ee81c` · Classification: Internal-Public
(mechanism only — no customer names, hosts, schedules, SIDs, or real identifiers appear in
this document).**

> This is the one document that explains the whole project — what DryDocs is, why it is
> built the way it is, what is in the graph, how data gets there, who decides what things
> mean, and where the work stands today. It sits between the two-page white paper (the
> pitch) and the technical design documents (the full specifications): friendlier than a
> TDD, deeper than a summary. If you read only one DryDocs document end to end, read this
> one.

<!-- anchor: how-this-fits -->
## How this document fits

| If you want… | Read… |
|---|---|
| The elevator pitch (2 pages) | `docs/whitepaper/drydocs-whitepaper.md` |
| **The whole project, explained (this document)** | `docs/design/drydocs-project-review.md` |
| How to install and run the pipeline | `README.md` |
| The full platform specification | `docs/design/drydocs-project-tdd.md` |
| The Control-M ingestion specification | `docs/design/controlm-ingestion-tdd.md` |
| The day-to-day operating rules for agents | `CLAUDE.md` |

<!-- anchor: how-to-read -->
## How to read (and mark up) this document

This document is itself a product of the DryDocs documentation pipeline (Epic L — see
chapter 9). The Markdown file is the source of truth; the `.html` and `.print.html` files
beside it are deterministic renders.

- **On paper:** print `drydocs-project-review.print.html`. Every section carries a small
  tag in the left margin (its anchor id). Write your notes in pen, referencing those tags;
  a scanned copy can be transcribed back into structured feedback keyed to the same ids.
- **On screen:** open `drydocs-project-review.html`. A ✎ button beside each section stores
  notes locally; the *Copy feedback* bar exports them as YAML for
  `docs/design/feedback/drydocs-project-review-rev1.yaml`.
- **As PDF:** `python scripts/doc_to_pdf.py docs/design/drydocs-project-review.print.html`
  (PDFs are build-on-demand and not committed).

---

<!-- anchor: the-problem -->
## 1 · The 3 a.m. problem

Large enterprises run their overnight business on batch estates: hundreds of thousands of
scheduled jobs, millions of configuration variables, spread across data centers and owned
by dozens of teams. When a job fails at 3 a.m., the questions are always the same:

1. **What does this job actually do?**
2. **What depends on it — can this wait until 9 a.m., or is a regulatory feed now late?**
3. **Who owns it, and who do I call?**
4. **Which application does it belong to?**

And the answers are always scattered: some in the scheduler's own database, some in a wiki
that trailed off two years ago, some in a spreadsheet, and some only in the head of the one
engineer who remembers. Batch production support fails in a specific, repeatable way:

- **Documentation debt.** Runbooks are written once, at go-live, by people who move on.
  The scheduler's definitions keep changing; the pages do not.
- **Tribal ownership.** Job-naming conventions encode team, application, and schedule —
  but only veterans can read them, and the conventions drift.
- **Invisible blast radius.** Job-to-job dependencies exist as prerequisite conditions
  inside the scheduler — perfectly legible to the scheduler, illegible to the human
  deciding whether a failure can wait.
- **Metadata rot compounds.** Empty description fields, stale escalation routing,
  hard-coded hosts nobody remembers. Each defect makes the next incident slower, and
  nothing repairs them.

The conventional responses — more wiki pages, a CMDB import, a one-off lineage project —
share one flaw: they create a *second copy* of the truth that immediately starts diverging
from the scheduler that actually runs the business.

DryDocs starts from the opposite observation: **the scheduler already knows.** Its
database holds every folder, every job, every prerequisite condition, every owner field.
The knowledge is there; it is just locked in a form only the scheduler can read. DryDocs
turns that metadata into a governed knowledge graph — and where the metadata itself is
wrong or missing, turns the defects into fix packages routed to the owning team.

<!-- anchor: big-idea -->
## 2 · The big idea

The one-line thesis, from the project TDD: **DryDocs is a governance machine that happens
to load a graph.** The graph is the visible product; the machinery that decides *what is
allowed into the graph and what it is allowed to mean* is the actual invention. Three
commitments define it, and each one is backed by a concrete, testable mechanism — not a
convention in prose:

| Commitment | In plain terms | The mechanism |
|---|---|---|
| **The graph is derived, not authored.** | Nobody hand-writes dependency maps; they are computed from the scheduler's live definitions, so they cannot rot the way wiki pages do. | Loaders read a governed replica of the orchestrator database (`psgmgr` views); re-running the pipeline refreshes the graph. |
| **No meaning enters the graph without a human decision.** | Software may *propose* that an edge means "depends on"; only a subject-matter expert may *confirm* it. | The relationship vocabulary, the taxonomy→ontology map, and the HITL gate with its append-only `config/gate-log.md` (chapter 7). |
| **Every governance rule is a machine-readable ledger with a test.** | Rules that live in prose get skipped; rules that live in YAML with a pytest guard fail the build when violated. | `config/*.yaml` + the guard tests in `tests/unit/` (classification, backlog schema, module boundaries, schema drift…). |

The project's operating experience is blunt about why the third commitment exists: the
guarded surfaces stay clean, and the unguarded ones are where incidents happen. So
surfaces get guards.

The first customer is the application-support team. The architecture is deliberately
shaped so the same graph later serves data-governance and lineage programs without rework.

<!-- anchor: four-layers -->
## 3 · Four layers, kept apart

Most of the confusion in the project's early life came from treating *taxonomy*,
*ontology*, *knowledge graph*, and *context* as one blurry thing. DryDocs keeps them as
four distinct layers (grounded in the Neo4j taxonomy/ontology/knowledge-graph series;
fixed in `docs/restructure/00-conceptual-model.md`):

| # | Layer | Question it answers | Where it lives |
|---|---|---|---|
| 1 | **Taxonomy** | *What category is this?* | `config/taxonomy/` — imported hierarchies: apps, products, LOB→Product→Team, schemas, variables |
| 2 | **Ontology** | *What do the connections mean?* | `drydocs_core/schema/`, `drydocs_core/ontology/`, `knowledge/ontology/` |
| 3 | **Knowledge graph** | *What is connected, and what does it mean?* | the populated Neo4j graph |
| 4 | **Context graph** | *What matters right now, for this decision?* | task-scoped projections — under design |

A library makes a decent analogy. The shelving scheme is the **taxonomy** (this is a
history book; that is chemistry). The rules of what a citation or an edition *means* are
the **ontology**. The stocked library — every book shelved, every citation resolvable —
is the **knowledge graph**. And the librarian answering *your* question at the desk right
now, with the reading room's current state in mind, is the **context graph**.

Why so much ceremony? Because the project's proof-of-concept demonstrated the failure
mode: when import and meaning-assignment happen in one step, relationships get invented on
the fly and the graph silently fills with edges nobody agreed on. The fix is a strict
order, enforced by role separation:

```
import as taxonomy   →  classification only, no meaning edges   (taxonomy-importer)
        ↓
map to ontology      →  PROV matrix / standards, SME-confirmed  (ontology-mapper + gate)
        ↓
load                 →  loader writes confirmed edges to Neo4j  (loaders)
        ↓
project context      →  task-scoped, time-aware views           (layer 4, future)
```

The configuration layer (`config/`) is the seam between layers 1 and 2: it records every
taxonomy→ontology binding and its confirmation state, so nothing reaches the graph
unconfirmed. As of this writing, layers 1–3 exist and are strong; layer 4 is the missing
piece and the destination (chapter 12).

<!-- anchor: graph-tour -->
## 4 · A guided tour of the graph

The knowledge graph spans several domains, loaded by independent command chains. A
simplified map:

```
  ORG / CATALOG                    SEAL                       CONTROL-M
  -------------                    ----                       ---------
  CatalogLOB                    Application ◄———————————— ControlMJob
    └─ ProductLine                ├─ Port ×2                  WAS_ASSOCIATED_WITH
         └─ Product               │  (Batch / Event)          {role: seal_app_ref}
  DevTeam ─SUPPORTS→ AreaProduct  └─ Membership
  DevTeam ─DEVELOPS→ Application       ├─ Role             ControlMServer
                                       └─ Employee            ▲ SCHEDULED_ON
                                                           ControlMFolder
  PROVENANCE                                                  │ CONTAINS_JOB
  ----------                                                  ▼
  every node ─WAS_GENERATED_BY→ JobRun                     ControlMJob
  (only when created or changed)                              │ REQUIRES_IN / EMITS_OUT
                                                              ▼
                                                           Condition
                                       ControlMJob ─WAS_INFORMED_BY→ ControlMJob
```

<!-- anchor: tour-controlm -->
### Control-M structural lineage

The heart of the graph. From the orchestrator's replicated database (`psgmgr.*` views),
the loaders build:

- **`:ControlMFolder`** — the scheduler's containers, plus the **`:ControlMServer`** mesh
  they are scheduled on, and **`:ControlMApplication`** grouping nodes taken from folder
  header rows. (That last label is deliberately *not* the SEAL `:Application` — see the
  naming decision below.)
- **`:ControlMJob`** — the jobs themselves, keyed `(folder_id, job_id)` because job ids
  are folder-scoped in Control-M.
- **`:Condition`** — the prerequisite tokens jobs wait on and emit. In-conditions carry
  the boolean-expression metadata (`AND_OR`, parentheses, order); out-conditions carry the
  add/remove sign. Both sides converge on the same node when `(folder_id, name)` matches —
  which is exactly what makes dependencies traversable.
- **`:WAS_INFORMED_BY`** — the payoff: *derived* job-to-job dependency edges, materialized
  by a recursive SQL walk that matches emitted out-conditions to required in-conditions.
  Each edge records the condition it travelled through, its recursion depth, and the full
  dependency path (which is also the cycle guard). This is the edge that turns "what is
  downstream of this job?" from tribal knowledge into a one-hop query.

This pass is **structural only** — definitions, not execution history. Runtime statistics
and host topology are the in-flight Epic P (chapter 11).

<!-- anchor: tour-seal -->
### SEAL applications, people, and the org

The application-registry domain answers *which application is this, and who is behind
it*: **`:Application`** nodes keyed by SEAL id, each with exactly two **`:Port`** nodes
(one batch-processing, one event-processing — the DPROD-inspired "two-port" pattern), and
a reified org structure — **`:Membership`** joining **`:Employee`** to **`:Role`** —
following the W3C ORG ontology, so that "who is the application owner vs. the support
lead" survives as data rather than as a column heading.

The catalog domain adds the business view: **`:CatalogLOB` → `:ProductLine` →
`:Product`**, plus **`:AreaProduct`** and **`:DevTeam`**, with `SUPPORTS` and `DEVELOPS`
edges aligning teams to products and applications, and `RECONCILES_TO` mapping catalog
lines of business onto the company's effective-dated business segments.

<!-- anchor: tour-attribution -->
### The newest edge: jobs attributed to applications

Landed the very day of this review (2026-07-14): the **SEAL attribution loader** connects
the two worlds above. It reads staged attribution facts and writes
`(:ControlMJob)-[:WAS_ASSOCIATED_WITH {role: 'seal_app_ref'}]→(:Application)` edges —
never nodes. Its match policy is SME-confirmed and deterministic: fact tiers are tried in
precedence order (SEAL id > FID > application name > alias), one-to-one matches are
accepted at the top available tier, ties break deterministically, and every multi-hit is
flagged. A coverage invariant — `matched + unmatched + pinned == eligible jobs` — is
stamped onto the load's provenance node, and the CLI fails if it doesn't reconcile. For
the stubborn tail there is a manifest-gated manual loader whose edges *pin* an attribution
(`match_method: 'manual'`); the automated loader respects pins and surfaces conflicts.

This is the pattern the whole project is built around, in miniature: a useful edge, a
human-confirmed meaning, a deterministic algorithm, and an invariant that must reconcile
before anyone trusts the result.

<!-- anchor: tour-other -->
### The supporting cast

- **Provenance.** Every load run is itself a graph node (`:JobRun`, a PROV Activity).
  Nodes link to the run that generated them via `WAS_GENERATED_BY` — but *only when
  created or actually changed* (a per-row checksum decides), so provenance stays queryable
  at estate scale instead of collapsing into supernodes.
- **Software registry.** `:Vendor` and `:SoftwareProduct` nodes from a curated YAML
  taxonomy — small today, but the anchor for "what software does this estate run on."
- **Documentation corpus.** Vendor documentation chunked into `:Document` → `:Chunk`
  lexical chains (the llm-graph-builder pattern) — the seed of the GraphRAG ambitions in
  chapter 12.
- **Naming discipline.** ADR 0003 settles a real confusion: source terms are kept
  verbatim, BMC-derived labels carry the `ControlM` prefix, and the bare `:Application`
  label is reserved for the SEAL registry. The scheduler's "application" grouping field
  and the company's application registry are different things, and the graph says so.

<!-- anchor: pipeline -->
## 5 · How data gets in

Every loader follows one lifecycle, inherited from a single base class:

```
 raw source ────► source-registry gate ────► adapter ────► pydantic validation
 (bundled CSV      confirmed: true,           (CsvAdapter /   (bad rows logged,
  sample, or        or exit 2 —                OracleAdapter)   never loaded)
  Oracle psgmgr)    fail closed)                    │
                                                    ▼
              :JobRun (PROV Activity) ◄──── BaseLoader, batches of 1 000
                 ▲   WAS_GENERATED_BY               │
                 │   (create/change only)           ▼
               Neo4j ◄──────────── UNWIND $batch + MERGE (.cypher template)
```

Walking the stages:

1. **The gate comes first.** `config/source-registry.yaml` declares every source — its
   classification, its adapter, what it feeds — and nothing loads until the source is
   `confirmed: true`. An unconfirmed source exits with an error before any database write.
   The pipeline *fails closed*.
2. **Adapters make dev and prod the same code path.** A `CsvAdapter` serves the bundled
   sanitized samples; an `OracleAdapter` runs the extract SQL against the replicated
   scheduler views. The loader neither knows nor cares which one fed it — so everything is
   testable offline.
3. **Validation before write.** Every row passes through a typed pydantic model; rejects
   are logged with their index and reason.
4. **Idempotent writes.** Cypher templates use `UNWIND $batch` + `MERGE` keyed on the
   business keys that the schema's ~40 constraints enforce. Re-running a load converges;
   it does not duplicate.
5. **Provenance closes the loop.** The run's `:JobRun` node records what happened, and
   `rows_changed` is derived *from the graph itself* (counting provenance edges written),
   not from Python bookkeeping.

Every Oracle extract also writes a per-run SQL log — run metadata, the exact SQL, the
result — outside the repo, so a reviewer can verify precisely what was extracted.

<!-- anchor: pipeline-variables -->
### The second stream: variable normalization

A separate workstream digs one level *below* job-to-job lineage: the job definitions'
variables, command lines, ETL launcher invocations, file operations, and notifications.
Its architecture is deliberately different — **SQL extract → Python classify/resolve/parse
→ staging tables (QA'd in SQL Developer) → graph load later**. The Python side (a variable
taxonomy, an offline variable resolver, a command-line parser) is complete and emits eight
`STG_*` staging CSVs; the staged facts already feed the attribution loader from chapter 4.
The final graph load of this stream (Phase D) is not started — staging first, graph
second, on purpose: the staging tables are where a human can inspect the normalization
before it ever becomes graph.

<!-- anchor: ontology -->
## 6 · The ontology: borrowed meaning

DryDocs does not invent its semantics. Every relationship label is grounded in a public
W3C (or W3C-adjacent) standard, for one forward-looking reason: **a provenance edge should
mean what PROV-O says it means, so a governance tool written years from now can read the
graph without archaeology.**

The standards, and what each buys:

| Standard | What it contributes | In the graph |
|---|---|---|
| **PROV-O** (W3C) | Activities, Entities, Agents, and who-did-what | job dependencies, load provenance, attribution edges |
| **ORG** (W3C) | organizations, reified memberships, roles | Application ↔ Employee via `:Membership` + `:Role` |
| **DPROD / EKGF** | data products with input/output ports | the two-port pattern on `:Application` |
| **DCAT** (W3C) | dataset/catalog vocabulary | dataset and distribution nodes |
| **SKOS** (W3C) | concept schemes, aliases | precedence losers become `skos:closeMatch` aliases |
| **SOSA/SSN** (W3C) | observations, sensors, results | *experimental, opt-in* — the layer-4 bridge |

The workhorse is the **PROV decision matrix**. First, every node label is classified by
behavioral type — is this thing an *Activity* (it runs), an *Entity* (it is data or
definition), an *Agent* (it can be responsible), or a *Collection*? Then a nine-row matrix
answers, for each from-type/to-type pair, what the edge is allowed to be called:

| From → To | PROV term | Neo4j label |
|---|---|---|
| Activity → Activity | `prov:wasInformedBy` | `WAS_INFORMED_BY` |
| Activity → Entity | `prov:used` | `USED` |
| Activity → Entity | `prov:generated` | `GENERATED` |
| Activity → Agent | `prov:wasAssociatedWith` | `WAS_ASSOCIATED_WITH` |
| Entity → Activity | `prov:wasGeneratedBy` | `WAS_GENERATED_BY` |
| Entity → Entity | `prov:wasDerivedFrom` | `WAS_DERIVED_FROM` |
| Entity → Agent | `prov:wasAttributedTo` | `WAS_ATTRIBUTED_TO` |
| Agent → Agent | `prov:actedOnBehalfOf` | `ACTED_ON_BEHALF_OF` |
| Collection → Entity | `prov:hadMember` | `HAD_MEMBER` |

So when a new relationship is needed, the question is never "what shall we call it?" but
"which matrix row is this?" — and edge *roles* (`role: seal_app_ref`) specialize a generic
term without inventing a new one.

All of this is recorded in a single registry —
`drydocs_core/ontology/relationship_vocabulary.yaml` — where every declared edge type
carries a lifecycle status: **planned → active → deprecated → removed**. A pytest guard
cross-checks the registry against the actual schema files, so the vocabulary and the
database can never silently disagree. New relationship types follow the eight-step
checklist in `docs/RELATIONSHIP_GUIDE.md`, enter as `planned`, and only flip `active`
through the gate described next.

<!-- anchor: governance -->
## 7 · Governance: three axes and one gate

Every artifact in DryDocs is governed along three independent axes. Keeping them separate
is half the design; conflating "secret," "trusted," and "authoritative" is how governance
schemes usually collapse.

<!-- anchor: governance-axes -->
### Axis 1 — Sensitivity (may this leave the building?)

Four levels, declared per source in `config/classification.yaml`, CI-enforced:
**External** and **Internal-Public** are publishable; **Internal** and
**Internal-Confidential** never leave the private boundary. The public repository carries
*mechanism* — schemas, rules, code, sanitized samples; real identifiers exist only in
private twins. `PUBLISH-BOUNDARY.md` is the contract; a guard test fails the build on any
unclassified source.

### Axis 2 — Trust (whose words are these?)

Every ingested corpus is tiered **VERBATIM** (the vendor's own words, citable),
**GROUNDED** (a paraphrase of content present in the source), or **SYNTHESIZED**
(AI-authored inference — useful, but *never* to be mistaken for source ground truth). The
rationale is the "two-corpus rule": the vendor corpus is what validates the model's
legality, and if synthesized material loads as verbatim, the legality layer is polluted.
This axis runs so deep it becomes physical infrastructure — the database topology in
chapter 8 gives uncertain data its own database, so it *cannot* contaminate ground truth.

### Axis 3 — Precedence (when sources disagree, who wins?)

An ordered authority chain in `config/precedence.yaml`: the **BMC baseline** (the
orchestrator's own canonical semantics) outranks **internal standards** (our naming and
normalization conventions), which outrank the **LOB→Product→Team** org taxonomy. Conflict
policy: highest authority wins, the loser is preserved as a SKOS alias (never silently
dropped), and contested calls require SME confirmation.

<!-- anchor: governance-gate -->
### The gate: where humans decide

The human-in-the-loop gate is an architectural element, not a review habit. When the
ontology-mapper proposes a mapping, when an orchestrator crosswalk is onboarded, or when
a precedence conflict needs resolving, the SME is presented one decision at a time as a
fixed card: the taxonomy element, the proposed meaning as `(From)-[:LABEL]→(To)`, the
standard term, the matrix row, a confidence, and open questions — with four calls:
**Confirm / Edit / Reject / Skip**. Routine confirmations batch; anything novel (a new
label, a new standard term, disagreeing authorities, low confidence, confidential data)
pauses for a real conversation.

Three invariants make the gate binding rather than ceremonial:

1. No taxonomy element becomes a graph edge while any of its mappings are unconfirmed.
2. Every confirmed label must trace to a matrix row or standard term, and exist in the
   relationship vocabulary before it can be applied.
3. Every gate run appends to `config/gate-log.md` — an append-only ledger that is the
   audit trail of every meaning decision ever made.

The division of labor is strict and worth stating plainly: **AI agents prepare gates,
render the review pages, and apply the outcomes. The decision itself is never automated.**

<!-- anchor: architecture -->
## 8 · The shape of the code: components and databases

<!-- anchor: architecture-components -->
### A slim core, six components, one enforced boundary

The codebase is a monorepo of five Python packages arranged around a dependency rule:
**`drydocs_core`** (models, adapters, config, the Neo4j client, the shared Control-M
parser, the schema and ontology files) imports nothing from anyone; components import the
core and *never each other*.

| Component | Job | Writes |
|---|---|---|
| `drydocs-load` (in `drydocs/`) | loaders + Cypher/SQL templates | the `drydocs` ground-truth graph |
| `drydocs-review` | SME review toolkit, gate pages, publishing | rendered HTML, no graph |
| `drydocs-plan` | backlog → HTML board renderer | `docs/plan/board.html` |
| `drydocs-docgen` | doc outlines, design-doc renderer, PDF | `docs/design/*.html` |
| `drydocs_remediation` | defect → fix package → ticket | **Jira only — never the graph** |
| `drydocs_lineage` | command-line-derived lineage, SME curation | gate-bound writer |
| `drydocs_deepdoc` | on-failure deep investigation | the `ddcontext` DB only |

The boundary is not a diagram — it is a test. An AST-based guard walks every module's
imports and fails the build if core imports a component, if components entangle, or —
the default-deny clause — if any module exists that is not classified into exactly one
bucket. Unclassified code is a build failure, not a shrug.

<!-- anchor: architecture-databases -->
### Four databases, and why trust is a transaction domain

DryDocs runs Neo4j Enterprise with a deliberate multi-database topology (ADR 0002):

| Database | Holds | Trust tier |
|---|---|---|
| `drydocs` | ground truth: Control-M, SEAL, catalog | VERBATIM / GROUNDED |
| `ddlineage` | cross-platform lineage | curated |
| `ddcontext` | uncertain, exploratory, AI-inferred material | SYNTHESIZED |
| `ddall` | a *composite* database aliasing all three | read-only view |

The point of `ddcontext` is architectural honesty: uncertain data lives in its own
transaction domain, so it is *physically impossible* to write it into ground truth by
accident. The composite database joins the three by **business key** (a proxy-node
pattern), never by internal node id — so context records survive a full rebuild of the
ground-truth database and simply re-link. Promotion from `ddcontext` to `drydocs` is only
ever a gate-confirmed load, never a cross-database edit.

The ADR trail (`docs/decisions/`) records the load-bearing decisions and their rejected
alternatives: ontology base scope (0001), component/database topology (0002 family),
application-naming disambiguation (0003), vendor terminology (0004), and the browser→
Neo4j access path (0005 — thin API for deployment, bolt-from-browser as dev mode only).

<!-- anchor: beyond-loading -->
## 9 · Beyond loading: what the other components do

The loaders get the headlines, but more than half the machinery exists for what happens
*around* the graph:

- **Review & backflow** (`drydocs-review`). The SME toolkit: graph verification suites
  (data-driven YAML acceptance tests — coverage reconciliation, lexical-graph shape,
  provenance-diet checks), review-label management, and the gate-page renderer that turns
  a gate spec into a self-contained interactive HTML review — while the repo, not the web
  page, remains the system of record.
- **Lineage** (`drydocs_lineage`). Parses job command lines into *candidate* invocation
  lineage, renders an SME review page (job cards, dependencies, an assertion panel), and
  holds writes behind a gate-bound writer until the vocabulary entry flips active. The
  shared command-line parser lives in the core, so lineage and deepdoc cannot drift apart.
- **Deep documentation** (`drydocs_deepdoc`). The reactive investigator: when something
  fails, it digs — and its findings land in `ddcontext`, clearly marked as inference,
  eligible for promotion only through the gate.
- **Remediation** (`drydocs_remediation`). The self-repair loop: detect metadata defects
  (empty descriptions, stale routing, hard-coded hosts), build corrected greenfield
  definitions, prove equivalence offline, and hand a fix package to the owning team via
  ticketing. Separation of duties is structural — support authors, developers deploy, the
  next ingest confirms closure — and the component writes neither production nor graph.
- **Documentation generation** (`drydocs-docgen`, Epic L). The pipeline rendering the
  document you are reading: Markdown as the single source of truth; deterministic,
  byte-identical renders (no timestamps, no randomness); a canonical outline whose stable
  anchors are one id namespace shared by the completeness validator, the rendered element
  ids, the traceability matrix, and the feedback loop. The print render was designed for
  a pen: margin tags beside every section, so a scanned markup can be transcribed back to
  structured, anchor-keyed feedback. Digital and paper annotation land in the same format.

<!-- anchor: operating-model -->
## 10 · How the project runs itself

DryDocs applies its own philosophy — ledgers with tests, humans at the gates — to its own
process.

- **The backlog is a schema, not a wishlist.** `docs/restructure/backlog.yaml` (schema
  `drydocs.backlog.v2`) holds every work item with type, module, epic, owning agent,
  model, priority, status, dependencies, and acceptance criteria. A guard test enforces
  the schema, unique ids, acyclic dependencies, valid agents — and even that the summary
  counts and the computed next-ready list match the items exactly. The human view is a
  rendered HTML board; the idea inbox (`IDEAS.md`) is groomed into the yaml by a dedicated
  skill.
- **Agents work scoped items; the session orchestrates.** Sub-agents own layers — a
  taxonomy importer that may only classify, an ontology mapper that may only propose, a
  config maintainer, a reference librarian — and pull well-specified items whose
  dependencies are done. Anything ambiguous goes to the gate, never auto-decided.
- **A session ritual keeps every machine identical.** Pull, work, re-render the board and
  design docs (renders are deterministic, so a stale committed render is detectable by
  `git diff`), commit, push, snapshot the code-dependency graph for drift comparison.
- **Tests are the enforcement arm.** Roughly 540 test functions across 51 files, and the
  most characteristic ones guard *process*, not code: the publish boundary, the backlog
  schema, the module boundary, schema/vocabulary drift, the port manifest. An opt-in
  end-to-end suite spins a throwaway Neo4j in Docker and runs the real CLI chain.
- **Two repos, one direction.** Development happens in a public **producer** repo carrying
  the sanitized, generalizable platform; a private company **consumer** repo carries real
  wiring and data. The histories are disjoint, so work *ports* (cherry-pick style, never a
  merge) under a machine-readable manifest that says, path by path, what applies
  wholesale, what is company-canonical, and what merges entry-by-entry — with guard tests
  on the manifest itself. The end-state goal: a standalone template another organization
  could adopt — bring your orchestrator replica and org registries, keep your identifiers
  private, inherit the governance machinery intact.

<!-- anchor: status -->
## 11 · Where the project stands (2026-07-14)

The backlog counts as of this document's commit: **63 done · 20 to do · 3 in progress ·
0 blocked** (86 items across 16 epics). By epic:

| Epic | Theme | Status |
|---|---|---|
| A — reference hygiene | registries, source manifests audited | **Done** |
| B — taxonomy capture | Control-M, SEAL, org, schemas as pure classification | **Done** |
| C — ontology mapping + HITL | every edge traces to a confirmed mapping | In progress — C5, C7 open |
| D — config-driven loaders | precedence + fail-closed source gating | **Done** |
| E — context-graph pilot | SOSA/SSN observation modeling | In progress — E1 gate deferred; E2 open |
| F — orchestrator expansion | AutoSys + Airflow crosswalks to the BMC baseline | **Done** (gates signed 2026-07-14; loaders separately gated) |
| G — component topology | multi-DB, core extraction, component split | **Done** |
| H — review backflow | the SME/HITL toolkit, generic and offline | **Done** |
| I — board + release infra | backlog v2, board, CI, v0.3.0 | Nearly done — J10 (lint burn-down) open |
| K — SEAL attribution | jobs → applications, end to end | In progress — loader live; K4, K5 open |
| L — doc infrastructure | outlines, deterministic renders, HITL markup | In progress — L7, L8, L9, L12 open |
| M — provenance audit | audit envelope + provenance-edge diet | In progress — M2–M4 open |
| N — source column mappings | per-source column ledgers | Core items landed |
| O — web console | browser front-end over the graph | **Active** — design pass + ADR ratification in flight; O4–O6 queued |
| P — runtime topology | hosts, run statistics, maintenance windows | Started — gate signed; P1, P3–P5 open |

**What just landed** (the week of this review): the SEAL attribution loader built and
active the same day as its gate sign-off; the AutoSys/Airflow crosswalk gates and the
runtime-topology gate signed; the Enterprise multi-database topology provisioned; the
core-extraction rename wave completed; and a first working web-console design pass (mock
sign-in, landing view, tower drill-down) merged alongside this document.

**The open work, grouped:** two ontology-rule refinements (C5, C7); the first true
context-graph query (E2); applying the application entity-reshape gate outcome and the
Product Cabinet attribution model (K4, K5); four documentation items including the runbook
doc-type capstone (L7–L9, L12); migrating old graphs to the audit envelope and extending
it to the remaining sources (M2–M4); the runtime-topology build-out through the
maintenance-window query (P1, P3–P5); the web-console access-path refit and thin API
(O4–O6); and one lint burn-down (J10).

<!-- anchor: roadmap -->
## 12 · The road ahead

The near-term threads converge on a single destination: **the context graph** — layer 4,
the missing piece from chapter 3.

- **Runtime reality** (Epic P) brings host topology and normalized run statistics into the
  graph, cross-validating definition-time claims against observed placement — and pays off
  immediately with the maintenance-window query: *the best time to patch this host, from
  its jobs' actual timing.*
- **Attribution completed** (K4, K5) finishes the chain from a 3 a.m. job failure to a
  named application, its owning team, and its product cabinet.
- **The audit envelope** (Epic M) extends who-changed-what provenance across every source.
- **The context pilot** (E2) then asks the first genuinely layer-4 question — *is this
  folder healthy and fresh, right now?* — over SOSA/SSN observations.
- **The web console** (Epic O) puts a browser on top: a thin read API over the composite
  database (per ADR 0005), persona-gated views, a live graph rendering.
- **GraphRAG navigation** (an upgrade plan on the shelf) builds on the lexical
  document graph so that natural-language questions can be answered *with citations* —
  the vendor's words and the graph's structure, never uncited inference.

The strategic bet behind all of it is worth restating: standards-grounding (PROV, ORG,
DPROD) is optionality that costs little now and avoids a remodel later — the same graph
that serves the support desk is already legible to the data-governance and lineage
programs that will eventually want it.

<!-- anchor: glossary -->
## Glossary

| Term | Plain-English meaning |
|---|---|
| **Control-M** | BMC's enterprise job scheduler — the orchestrator whose metadata DryDocs ingests; the semantic *baseline* all other orchestrators map to. |
| **Folder / Job / Condition** | Control-M's containers, units of work, and the named tokens jobs wait on / emit — conditions are how dependencies exist. |
| **psgmgr** | The replicated (read-only) Oracle schema of the Control-M database that production extracts read. |
| **AutoEdit variable** | A Control-M job-definition variable (`%%VAR`), resolved and classified by the normalization stream. |
| **SEAL** | The internal application registry; a SEAL id names an application. `:Application` nodes are keyed by it. |
| **FID** | A functional/service account id — a tenant a job runs as; one of the attribution fact tiers. |
| **PAT / Catalog** | The internal product-alignment taxonomy: LOB → Product Line → Product, area products, dev teams. |
| **LOB** | Line of business. |
| **Neo4j / Cypher / APOC** | The graph database, its query language, and its standard procedure library (used for multi-statement templates). |
| **MERGE / UNWIND** | Cypher's idempotent create-or-match, and its batch iteration — together the loaders' write pattern. |
| **Supernode** | A node with so many edges it degrades queries — the reason provenance edges are written on change only. |
| **PROV-O** | The W3C provenance ontology: Activities act, Entities exist, Agents are responsible. The nine-row matrix comes from it. |
| **ORG / DPROD / DCAT / SKOS / SOSA-SSN** | W3C(-adjacent) vocabularies for organizations, data products, catalogs, concept aliases, and observations, respectively. |
| **Taxonomy → Ontology → Knowledge graph → Context graph** | The four layers: categories → meaning rules → the populated graph → what matters right now. |
| **HITL / the gate** | Human-in-the-loop: the SME decision point (Confirm/Edit/Reject/Skip) every meaning change must pass; logged append-only. |
| **VERBATIM / GROUNDED / SYNTHESIZED** | The trust tiers: source's words / faithful paraphrase / AI inference. |
| **Classification** | The sensitivity axis: External, Internal-Public (publishable) vs Internal, Internal-Confidential (never published). |
| **Precedence** | The authority chain when sources disagree: vendor baseline > internal standards > org taxonomy. |
| **JobRun** | The graph node representing one load execution — every load is itself provenance. |
| **Producer / consumer port** | The one-way flow of work from the public platform repo to the private company repo, governed by a manifest. |
| **Backlog / board** | The machine-readable work ledger (`backlog.yaml`) and its rendered HTML view. |
| **TDD** | Technical design document — the deep-specification genre this review complements. |

<!-- anchor: reading-map -->
## Appendix A · Reading map

| Document | What it gives you |
|---|---|
| `README.md` | Install, configure, and run the pipeline; CLI reference; Control-M loader detail |
| `docs/whitepaper/drydocs-whitepaper.md` | The two-page external-facing case |
| `docs/design/drydocs-project-tdd.md` | The platform specification (layers, ledgers, gate, components) |
| `docs/design/controlm-ingestion-tdd.md` | The M3 ingestion chain, end to end |
| `docs/design/drydocs-remediation-tdd.md` | The fix-package component design |
| `docs/restructure/00-conceptual-model.md` | The four-layer model, first principles |
| `docs/restructure/03-hitl-sme-flow.md` | The gate, step by step |
| `docs/RELATIONSHIP_GUIDE.md` | How a new relationship type is born |
| `docs/decisions/` | The ADRs — decisions and their rejected alternatives |
| `docs/plan/board.html` | The live work board (render of `backlog.yaml`) |
| `PUBLISH-BOUNDARY.md` | What may leave the private boundary, and how that's enforced |
| `git-readme.md` + `PORT-MANIFEST.yaml` | The two-repo port: why and what |
| `MODULE_MAP.md` | The authoritative code-boundary map |
| `CLAUDE.md` | The agent operating guide (read first in any session) |

<!-- anchor: colophon -->
## Colophon

Authored as Markdown (`docs/design/drydocs-project-review.md`) and rendered by the Epic L
documentation pipeline (`scripts/render_design_doc.py`) into a screen surface with
built-in annotation and this print surface with margin anchor tags. Renders are
deterministic: same source, same bytes. Feedback — digital or pen-on-paper — keys to the
anchor ids in the margins and lands in
`docs/design/feedback/drydocs-project-review-rev1.yaml`. Facts reflect the repository at
commit `97ee81c`, 2026-07-14.
