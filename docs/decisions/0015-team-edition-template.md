# ADR 0015 — Team Edition: copier-templated per-team instances over a shared cherry-picked base

```yaml
status: PROPOSED        # PROPOSED | ACCEPTED | SUPERSEDED — the drafting session never accepts its own ADR
date: 2026-08-27
authored_by: cowork session (remote; SME-directed pull)
deciders: []            # acceptance requires an SME gate; nothing here is pre-approved
layer: cross-cutting    # product shape; touches every layer without amending any of them
relates_to:
  - 0002-component-database-topology.md    # stays ACCEPTED; TE reuses its proxy-node/composite pattern
  - 0009-configuration-substrate.md        # git-YAML source of truth carries into every instance
  - 0011-single-database-contingency.md    # the :Uncertain discipline TE inherits as its trust mechanism
  - 0012-data-named-load-surface.md        # the generalization goal TE is the first real consumer of
  - 0014-runtime-substrate.md              # per-machine settings group = per-INSTANCE settings group
  - MODULE_MAP.md                          # the boundary the cherry-pick is cut along
  - PORT-MANIFEST.yaml                     # disposition vocabulary reused as template file classes
  - docs/design/deepdoc-data-flow-overview.md   # the investigation that stated the support gap
trigger: >
  The drydocs_deepdoc research (one production deep-dive, 2026-08-20) exposed a
  support gap: the data applications are SECONDARY reporting products whose
  primaries (e.g. Auto) have true requirements, repos, testing, controls and
  re-pave — while the data apps barely track requirements and depend on
  trusting run-time state over what a repo or config declares. 5–10 such teams
  exist. One DryDocs cannot serve them all at the depth one warehouse needs.
```

## What this is, and is not

DryDocs (the producer repo) ingests metadata for 3–5 sample applications and may
scale past a hundred; its discipline is breadth — it deliberately refuses grains
like field-level transformation tracking. **Team Edition (TE) is the opposite
bet:** a lighter-weight cherry-pick of the same modules that documents a SINGLE
data warehouse deeply, with a tight DevOps focus, closer to the original
full-circle-docs intent.

This is **not a fork.** A fork diverges once and forever. TE is a **copier
template built from a cherry-picked base**, generated per team
(`auto`, `homelending`, `creditcards`, …), updatable in place
(`copier update`), with one composite graph federating every instance. Ten
instances, one base to maintain, one estate-wide graph.

This ADR does not amend 0002, 0009, 0011, 0012 or 0014. It composes them.

## Context

### The gap, stated once

The primary products can be documented against a source of truth: they have
requirements. The data applications cannot: their requirements are barely
tracked, their "code" is partly run-time configuration (Control-M job
definitions, launcher variables) that no repo governs, and the operational
knowledge that keeps them alive — gotchas, guardrails, workarounds — lives in
support threads and individual heads. The deepdoc data-flow overview record
documents one evening spent reassembling a single flow's story across email,
the Control-M client, Jira, Bitbucket, Confluence and a chat assistant: every
answer existed somewhere, none of it in one place, and the job names actively
misled.

### The thesis TE is built on

**If the inventory is provably complete, the requirements can be reconstructed
from it.** The word that carries the sentence is *provably*: an inventory that
is 80% complete and does not know which 80% produces reconstructed requirements
indistinguishable from guesses. So TE's first deliverable is not a loader — it
is a **completeness ledger**: per data application, per object class (repos,
jobs, folders, tables, views, datasets, servers, docs, tickets): declared,
inventoried, residual, and WHY the residual exists. `drydocs/docs_coverage.py`
already has the exact shape (declared vs loaded vs every blocker, `None` for
not-probed rather than `0`); TE generalizes it from the doc corpus to every
object class. Everything else in TE is downstream of this ledger.

> **Extension point (deliberate).** This Context section is written
> qualitatively and will be extended with METRICS for what counts as KNOWN —
> code/run-time-confirmed vs stale — once the coverage ledger (D1) produces
> them. The gap statement above stands as anecdote until numbers replace it;
> extending this section is the intended home for those numbers, not a new
> document.

### Why now, and why a template rather than one bigger DryDocs

- One graph serving a hundred apps at warehouse depth violates the producer's
  own granularity rule; ten graphs at depth do not.
- The teams own their instances (the DevOps-team model); a hosted service would
  invert that ownership.
- The port machinery (PORT-MANIFEST, reconcile-port) already proves the base
  can cross a repo boundary — but it proves it for ONE consumer, hand-reconciled.
  Ten consumers need generation + update, not ten ports per release.

## Decision

Six decisions, D1–D6.

### D1 — Charter: the completeness ledger is the product's core

TE's claim to a team is: *what exists is enumerated, what is missing is named,
and what was reconstructed says so.* Concretely:

- A `coverage` component (generalized `docs_coverage`) reports per-application,
  per-class: declared / inventoried / residual / blocker. Pure declaration join
  first, optional graph probe second, `not-probed` never rendered as zero.
- The three target gaps build ON the ledger, in order: (1) the complete
  code/object/context inventory, (2) the per-data-flow overview record
  (the deepdoc doc's proposed shape — its three unreconciled grains
  `%%DATAFLOW` / `:AppDataFlow` / "data series" resolve to ONE persisted
  identity), (3) the requirements chain
  commit → author → issue → epic → business justification, loadable as
  structure.

### D2 — Module cut (the cherry-pick, along the MODULE_MAP boundary)

| Disposition | Modules | Reason |
|---|---|---|
| **Keep whole** | `drydocs_core/**` (models, adapters, neo4j_client, config, precedence, source_registry, repo_paths, data_root, landing_zones, data_zones, ontology, schema, orchestration incl. the neutral/vendor seam) | Already the imports-nothing layer; cutting core saves nothing and costs the guard |
| **Keep, promoted** | `doc_outline`, `sme_notes`, `gate_pages`, `docs_coverage`, `docs_verify`, `design_doc`, `doc_pdf`, `publishing/**` | These ARE the requirements-gap tooling: outline completeness + traceability validation, `SME[sid] $FR/$UC/$OQ` harvest into requirement buckets, deterministic offline renders. For a team with no requirements process, this is one |
| **Keep, subset** | `loaders/**`: controlm\*, code_snapshot, software_registry, catalog, seal_applications/attribution/contacts, server_inventory/resolution, runs_on_resolution, app_identity, doc_traceability, folder_attribution, manual_loads | The inventory spine |
| **Keep, thin** | `drydocs_api`: QuerySpec registry + read guard only (drop personas, ephemeral_specs, sessions, exports for v1) | The spec catalog is the read contract; the rest is console surface TE v1 does not ship |
| **Keep** | `drydocs_lineage`, `cmdline_staging`, `code_graph_freshness`, `libs/oracle_kerberos` | The runtime-vs-repo truth axis and the staleness guard — the trust problem TE exists for |
| **Rewrite** | `drydocs_deepdoc` (today a 3-file scaffold), `drydocs_docmeta` connectors | Where the data-flow record and corpus capture land |
| **Cut** | `drydocs_remediation`, `plan_board`/`plan_ideas`/`plan_roadmap`, `port_preflight`/`port_backlog_union`, `backlog_store`, `agents/**`, `web/**`, `fid_census`, `run_as_detect`, loaders `email_extracts`/`essential_graphrag`/`bmc_docs`/`vendor_docs`/`business_segments`/`patch_window` | Remediation is a different product (fixing jobs ≠ documenting them; Jira stays its SoR in the producer). Plan/port/backlog are the producer's own project management. Agents + web are the heaviest surfaces to template — the offline HTML renderers give shareable output with zero runtime |

**One deliberate anti-cut:** `drydocs_core/orchestration/`'s neutral-vs-vendor
seam looks like pure generality tax in a single-team edition. It stays, because
across ten teams it is what lets an Autosys or Airflow team use the same base.
TE ships only the Control-M dialect; the others remain declared-not-built.

### D3 — Tenancy: instance-internal names never change; tenancy is an alias plus a URN segment

**No module becomes tenant-aware.** Each instance keeps the databases the code
already expects — `drydocs` (ground truth; content folded to one DB per the G32
gate) and `ddschema` (stays separate; ADR 0011 clause 2 deliberately never
fires). Two databases per instance, identical everywhere.
`config/dev-environment.yaml`'s name map and `test_database_names.py` port
unchanged. Nothing in core learns what an LOB is.

Tenancy enters at exactly two points:

1. **The estate composite.** One composite, `ddestate`, whose constituents are
   aliased `ddestate.auto`, `ddestate.homelending`, `ddestate.creditcards` — the
   `<team>.drydocs` intuition, expressed as Neo4j composite aliases. Local
   aliases if teams share a cluster; remote constituents if each team runs its
   own Neo4j (ADR 0002 already priced that: credential management, slower
   federation).
2. **The URN grammar.** A job in Auto and a job in Home Lending must never
   collide; a Snowflake table both teams read must resolve to ONE node in the
   composite. Therefore: a tenant segment for team-OWNED objects, a tenant-free
   canonical form for SHARED infrastructure — and which class an object falls
   into is **declared, not inferred**. Cross-instance identity uses the
   proxy-node-on-business-key pattern 0002 D1 built for `ddcontext`: same
   mechanism, new axis.

**The URN shared-vs-owned ruling is the Phase 0 gate and blocks all code.**
Wrong, the composite is ten disconnected graphs; right, the roll-up is free.

### D4 — Distribution: a copier template with three file classes

**Copier, not cookiecutter.** `copier update` re-applies template changes to
generated instances; cookiecutter has no update path, which silently defeats
"one base to maintain" the moment instance #1 diverges. (This amends the
in-chat cookiecutter selection of 2026-08-27 — same generation model, plus the
update lifecycle the program depends on.)

The PORT-MANIFEST disposition vocabulary transfers as the template's file
classification — not its mechanism, its grammar:

| Class | Contents | Rule |
|---|---|---|
| `canonical-template` | ontology, `relationship_vocabulary.yaml`, `schema/*.cypher`, URN builders, all of core, kept loaders, every guard test | **Frozen.** Overwritten on `copier update`; a team edit here is a build failure, enforced by a checksum manifest guard test |
| `instance-owned` | `source-registry.yaml`, `taxonomy/lob-product-team.yaml`, `business-application.yaml`, `oracle-schemas.yaml`, `data-zones.yaml`, `.env` | Scaffolded from the questionnaire at generation; never touched by update (the `canonical-company` disposition, renamed for N consumers) |
| `derived` | renders, `var/mapping.db`, snapshots | Regenerated, never carried — verbatim the J43 rule |

Questionnaire ≈ team name, LOB, URN tenant segment, orchestrator vendor,
warehouse, doc platform, ticket system, composite alias.

**The ontology is frozen without exception.** If Auto writes `:ControlMJob` and
Home Lending writes `:BatchJob`, `ddestate` is worthless. This is the one place
"configurable template" says no; vocabulary change happens in the base, through
the base's gate, and reaches every instance as an update.

Per ADR 0014, the per-machine settings group becomes the per-INSTANCE settings
group with zero design change: `.env` + `config/log-kinds.yaml` were already
scoped to "this machine's operational facts," which is exactly what "this
instance's operational facts" needs.

### D5 — Reconstructed requirements are `:Uncertain` by construction

Requirements inferred from the inventory are inferences, not requirements. Every
such node/edge carries `:Uncertain` + reliability/trust stamps at its single
write boundary, exactly as the deepdoc writer does today, and promotion to
ground truth is HITL-gated through the loader path — never a label strip. This
is not a limitation to engineer around: **for a team with no requirements
process, a gated inference queue IS the requirements process.** The SDLC join
hole the investigation found (COLLABORATION-type Jira projects carry
`Primary SEAL Application: N/A`, so the application binding does not exist to be
loaded) is modeled as a **declared, countable gap in the coverage ledger** —
never papered over with fuzzy matching. A reconstructed requirement honest about
its provenance is usable; one that is not gets the whole graph distrusted the
first time somebody checks.

### D6 — The agent layer ships in the template, and agent memory has a declared home

The producer repo already runs on an agent operating layer — `CLAUDE.md` (the
operating guide: session ritual, four-layers rule, classification boundary,
working agreements), ~38 skills under `.claude/skills/`, and five subagent
definitions under `.claude/agents/` (backlog-groomer, ontology-mapper,
pipeline-config, reference-librarian, taxonomy-importer). Left untemplated,
each instance grows its own agent behavior by drift — ten teams prompting ten
different DryDocs, which breaks consistency exactly where the estate needs it
(vocabulary, classification, gate discipline). So the agent layer is a
first-class template surface, classified into the same D4 file classes:

| Class | Agent-layer contents | Rule |
|---|---|---|
| `canonical-template` | The base `CLAUDE.md` operating guide (four layers, classification boundary, precedence, working agreements); the skills that drive KEPT modules — `run-drydocs`, `controlm-db`, `oracle-db`, `controlm-runbook-automation`(+excel), `add-source-object`, `verify`, `tech-debt`, `transcribe-doc-markup`, `consolidate-memory`; the subagent definitions (ontology-mapper, pipeline-config, reference-librarian, taxonomy-importer) | Frozen; overwritten on `copier update`. **The skill cut follows the module cut**: a skill that drives a cut module does not ship (`groom-backlog` → backlog machinery, `reconcile-port` → port machinery — both producer-only). A skill edit is a base change, gated in the base, reaching every instance as an update — the same rule as the ontology, for the same reason |
| `instance-owned` | An instance operating overlay (`CLAUDE.local.md` or equivalent), SEEDED by the copier questionnaire (team name, LOB terms, warehouse, orchestrator, composite alias) so the agent speaks the team's language from generation day. This overlay is CONFIG, not memory — session learning lands in the instance's memory graph (below), never accretes in this file | Scaffolded once, never touched by update; the base `CLAUDE.md` declares the overlay's existence and load order, so the seam is part of the frozen contract even though its contents never are |
| `derived` | Nothing — agent memory is never a render | — |

**Planned memory, consistently applied — graph-native, on the neo4j-labs plan.**
TE adopts the memory model of
[`neo4j-labs/agent-memory`](https://github.com/neo4j-labs/agent-memory)
(Apache-2.0) as its target shape — three tiers, all in the graph:

1. **Short-term** — session/conversation history, vector + text searchable;
2. **Long-term** — entities, preferences and facts as a knowledge graph
   (the project's POLE+O model: Persons, Objects, Locations, Events +
   Observations);
3. **Reasoning memory** — traces of agent decisions and tool usage, with
   `:TOUCHED` audit edges linking reasoning steps to the entities they read —
   the agent learns from its own past investigations.

The fit is named, not assumed: it is **Neo4j-native** (the platform every
instance already runs), its **multi-tenant scoping** aligns memory scope with
the per-team instance exactly as D3 aligns data, and its **MCP server** is the
mechanism by which ONE memory reaches every agent surface — Claude sessions,
the frozen skills, and any future ADK agent tier — instead of each surface
keeping its own notes. That MCP seam is what "consistently applied" means in
practice: ten instances, one memory contract.

Physical home: a per-instance memory scope, isolated from ground truth.
Whether that is its own database (working name `ddmemory`) or in-DB scoping
goes through the 0002 Q8 naming test at the gate — the test passes on its face
(conversation state and reasoning traces are NOT contents that belong in
`drydocs`), but Q8 rulings are the gate's, never a draft's.

What does NOT change from the trust architecture: **memory is a draft buffer,
never a second source of truth.** Anything durable a session learns — a
gotcha, a naming-token misuse, a workaround, a source quirk — is promoted out
of memory into its governed home (a `config/` declaration, a
standards-rules-registry rule, or an `:Uncertain` graph write through the
deepdoc path) via the gate, as a reviewable diff. The `consolidate-memory`
skill re-targets from markdown scrollback to the memory graph and ships frozen
as the promotion verb, so all ten instances consolidate the same way.
Promotion is the ONLY path from memory to ground truth; a fact that lives only
in memory for months is a defect of the same class as a value buried in a
Python literal (ADR 0014's governing principle) — unconsolidated memory is
where gotcha/guardrail/workaround knowledge went to die in the pre-DryDocs
world, and TE exists to end that.

Status caveat, cited honestly: agent-memory is an **experimental Neo4j Labs
project** (~380★, community-supported). TE commits to its MODEL — the three
tiers, POLE+O, reasoning traces with `:TOUCHED` audit edges — and treats the
library as replaceable behind that shape. The schema is the adoption; the
package is a dependency like any other, watched per the Sources register
below.

## Options Considered

### Distribution shape
| Option | Verdict |
|---|---|
| **Copier template from a cherry-picked base** (chosen) | One base, N generated instances, update-in-place, file classes carry the port grammar |
| Plain fork per team | Rejected — divergence is permanent; ten bases to maintain is the failure mode this ADR exists to avoid |
| Generalize PORT-MANIFEST to N consumers | Rejected as the primary mechanism — zero new machinery, but ten hand-reconciled ports per release does not scale; its disposition VOCABULARY survives as D4's file classes |
| Installed core packages + thin per-team config repo | Deferred, not rejected — stronger upgrade story long-term, but requires an internal package index and release engineering before instance #1 exists. Named trigger to revisit: when `copier update` conflicts in the frozen class become routine, that is the signal the frozen class wants to be a wheel |
| Cookiecutter | Rejected — no update path (see D4) |
| Hosted multi-tenant service | Rejected — inverts the team-owns-their-instance model and is a product build, not a documentation program |

### Scaffold substrate — copy the base INTO an existing SaaS template?
Surveyed 2026-08-27, and rejected on evidence: **the copier ecosystem and the
SaaS-features ecosystem are disjoint.** Copier-native templates
(pawamoy/copier-uv, superlinear-ai/substrate, serious-scaffold/ss-python)
scaffold repo behavior — uv, lint/type/CI, docs, semantic versioning,
`copier update` migrations — and ship NO logging, settings, auth or team layer.
Templates WITH teams/auth (fastapi/full-stack-fastapi-template ~45k★,
benavlabs/FastAPI-boilerplate, SaaS Pegasus) are clone-and-diverge repos or
proprietary generators with no update lifecycle. Deeper than packaging:
"teams" there means users-in-a-workspace rows behind JWT next to Stripe; TE's
"team" is a generated instance with its own databases — a different axis, so
adoption would inherit a users/orgs/billing model to rip out while gaining
nothing. And TE's logging/config substrate already exists and is better fitted
(ADR 0014, ADR 0009) than the structlog-plus-pydantic-settings such templates
ship. **Cherry-picked best practices, not adopted scaffolds:** TE takes the
template MECHANICS proven in copier-uv / ss-python — `_subdirectory` layout,
`_tasks` hooks, update migrations, and CI that generates an instance and runs
its suite (the "instance #2 proves the template" phase, automated) — as
practices to implement, with the source cited in the register below, never as
a scaffold to inherit.

### Tenancy shape
| Option | Verdict |
|---|---|
| **DB-per-team instance + estate composite** (chosen) | Reuses 0002's own pattern; isolation by physics between teams |
| One shared DB, tenant property | Rejected — re-runs the Community-single-DB argument 0002 already rejected, now with ten writers |
| Separate DBMS per team, app-side join | Rejected in 0002 (D1 alternatives); composite does the join natively |

## Trade-off Analysis

The central trade is **duplication vs depth**: ten instances duplicate the base
(mitigated by the frozen class + `copier update`) to buy per-warehouse depth the
one-graph producer deliberately refuses. The second trade is inherited from
G32 with interest: **the trust boundary is already discipline, not physics** —
the fold traded the transaction domain for three guards and an audit, and ten
instances multiply that audit surface by ten. Mitigation is structural
placement: the `:Uncertain` guards and the audit spec live in the frozen class,
un-editable per instance, and the estate roll-up gains one composite-level audit
(count of `:Uncertain` reachable from ground-truth-only traversals, expected 0,
summed across constituents).

The third trade is **infrastructure cost ownership, and it lands on the team.**
An instance is not free to run: each dev team is responsible for the cost of
its own AWS Neo4j deployment — the instance itself (self-managed on EC2 or
Aura), storage and backup, and the AWS PrivateLink / VPC endpoint connectivity
the bank's network requires. This is the price of the team-owns-their-instance
model, stated where it can be declined rather than discovered on the first
invoice. The consequence that matters: **the PrivateLink-connected `ddestate`
IS the goal, and it is what buys the coverage** — the estate roll-up only
answers cross-LOB questions over the instances it can reach, so a team that
lets its endpoint lapse silently drops out of the estate. The composite
therefore needs a reachability probe per constituent (absent ≠ empty), the
same absent-vs-zero honesty rule the coverage ledger already enforces. A team
for whom
this cost is the blocker has a declared cheaper path: ADR 0011's fold-down
runs an instance on a smaller footprint at the trust-discipline price that
record states plainly.

## Consequences

**Positive**
- One maintained base; a vocabulary or guard fix reaches ten teams as a version
  bump, not ten ports.
- The estate composite answers cross-LOB questions no single instance can, on
  the proxy-node pattern already proven.
- The completeness ledger converts "we think we documented it" into a number
  with a named residual — the exact artifact a support gap review asks for.
- Teams own their instances end to end; the base team owns only the base.

**Negative / trade-offs**
- Ten instances = ten Neo4j Enterprise footprints, each with its own AWS bill
  (instance, storage, backup, PrivateLink) owned by that team — cost ownership
  per the third trade above; only the deployment SHAPE (self-managed EC2 vs
  Aura vs a shared cluster) remains a per-team decision.
- The frozen class is a real constraint on teams: a team that NEEDS a
  vocabulary change must route through the base's gate. That queue is a
  governance cost, accepted deliberately — it is also what keeps `ddestate`
  meaningful.
- `copier update` conflict resolution in instance-owned files is each team's
  own work; the template can minimize the surface but not eliminate it.
- Discipline-not-physics trust boundary, ×10 (named above; residual risk stated
  in ADR 0011 clause 1 stands, per instance).

## Sources & tooling watch — a living register, not a bibliography

**Why this section exists in an ADR:** the GraphRAG and LLM/agent space is
moving faster than any decision record's shelf life. A practice adopted from an
open-source project in August 2026 may be superseded, abandoned, or absorbed
upstream within quarters. So TE's rule is: **every externally-sourced practice
is cherry-picked, cited, and watched** — the citation names what was taken and
the trigger that re-opens the choice. The mechanism is not new: rows enter
`config/doc-source-registry.yaml` and the external-capture flow
(`reference/` / `external/` with `SOURCE-MANIFEST`s), and the ADR 0007
stale-source rescrape queue is the keep-current loop. This table is the
seed set; the registry is the living surface.

| Source | What TE takes | Watch trigger |
|---|---|---|
| [neo4j-labs/agent-memory](https://github.com/neo4j-labs/agent-memory) (Apache-2.0, experimental Labs) | D6's memory model: three tiers (short-term / long-term POLE+O / reasoning traces), `:TOUCHED` audit edges, multi-tenant scoping, MCP server as the agent-surface seam | Labs graduation, archive, or schema break; any first-party Neo4j memory product absorbing it |
| [neo4j-labs/neocarta](https://github.com/neo4j-labs/neocarta) (Apache-2.0, Labs) — semantic layer in Neo4j for agents: schema metadata + glossary + metrics + query history as one graph, with MCP retrieval tools and a connector extract-transform-load pattern | Nothing adopted yet — WATCHED as the nearest open-source sibling to what DryDocs already is. Deep-dive comparison: `docs/reviews/neocarta-connector-comparison.md` (2026-08-27), which rules FOUR cherry-pick candidates: **CP-1** query-history ingestion as run-time EVIDENCE (`:Query`-family, timestamp-windowed — feeds the known-vs-stale metric the Context extension point reserves), **CP-2** a per-source connector façade over the existing adapter+loader+registry seam (`ingest()` still refuses through `require_confirmed()`), **CP-3** `export()`/OSI as the `ddestate` interchange candidate, **CP-4** embeddings as a post-load pass (the GraphRAG re-entry shape). On declaration, identity, validation, provenance and trust the traffic flows the other way | Convergence with the `drydocs_api` QuerySpec surface (two graph-grounded routing layers is one too many — if its patterns mature, adopt the pattern, keep our surface); Labs graduation or archive |
| [copier](https://github.com/copier-org/copier) (runtime dependency — the one adopted tool, not a cherry-pick) | D4's generation + `copier update` lifecycle | Major-version migration-format changes |
| [pawamoy/copier-uv](https://github.com/pawamoy/copier-uv) · [serious-scaffold/ss-python](https://github.com/serious-scaffold/ss-python) · [superlinear-ai/substrate](https://github.com/superlinear-ai/substrate) | Template mechanics as practices: `_subdirectory`, `_tasks`, update migrations, generate-and-test CI | New copier idioms worth back-porting (e.g. migration tooling changes) |
| [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) and the 2026-08-27 SaaS-scaffold survey | Nothing adopted — the surveyed evidence for the rejected scaffold-substrate option, kept so it is not re-litigated | Only re-opens if a shared estate console is chartered (the one legitimate use identified) |
| GraphRAG ecosystem — [Microsoft GraphRAG](https://github.com/microsoft/graphrag), [neo4j/neo4j-graphrag-python](https://github.com/neo4j/neo4j-graphrag-python), the producer's `essential_graphrag` loader lineage | Nothing in TE v1 (the loader is cut in D2); the space is WATCHED because retrieval over the estate composite is the obvious v2 pressure | A retrieval requirement landing on `ddestate`; either package's chunking/lexical-graph shape stabilizing enough to gate a vocabulary |
| [Model Context Protocol](https://modelcontextprotocol.io) | The seam D6's memory and any future tool surface speak through | Spec revisions that break pinned server versions |

Register discipline, stated once: a row names WHAT was taken (a practice, a
schema shape, a dependency) — never "we use X." A watched source that changes
does not auto-change TE; it opens a backlog item, and anything touching
vocabulary or the trust boundary routes through the gate like every other
change.

## Follow-up (phases; groom into the backlog as an epic)

| Phase | Work | Done when |
|---|---|---|
| **0** | URN tenancy grammar gate (shared-vs-owned object classes, tenant segment) + the D6 memory-scope name through the 0002 Q8 test | Ruled; blocks all code |
| **1** | Carve the base — subtraction only, no new code | Suite green, boundary guard passes on the reduced module set |
| **2** | Templatize (copier.yml, questionnaire, file classes, checksum guard, agent layer per D6) + generate instance #2 | A second LOB loads from the template — two instances prove a template; one does not — and its seeded `CLAUDE.local.md` speaks that LOB's terms |
| **3** | `ddestate` composite | One cross-team query works; one shared table resolves to one node from two instances |
| **4** | Coverage ledger (generalized `docs_coverage`) | Per-app completeness is a number with a named residual |
| **5** | Data-flow overview record | The three grains reconcile to one persisted identity; Output-tab enrichment pass lands |
| **6** | Requirements chain | commit→author→issue→epic→justification loadable, `:Uncertain`-stamped, promotable through the gate |

Phase 4 precedes 5 and 6 deliberately: both depend on knowing what you have.
