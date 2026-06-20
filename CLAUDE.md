# DryDocs1 — agent operating guide

**DryDocs is a production-support / development-support knowledge graph for D&A batch
processing.** It answers: *what runs, what it depends on, who owns it, which application
it belongs to* — and increasingly, *what matters right now for this support decision.*

This file is the routing brain. Read it first. It tells you **which layer you are working
in**, **which external reference to call**, and **which sub-agent owns the task**.

---

## 1. The four layers (read this before modeling anything)

DryDocs is built in four conceptual layers. Most past confusion came from collapsing them.
Keep them distinct. (Grounded in the Neo4j taxonomy/ontology/knowledge-graph/context-graph
series — see `docs/restructure/00-conceptual-model.md`.)

| Layer | Answers | Where it lives | Owner agent |
|-------|---------|----------------|-------------|
| **1. Taxonomy** | "What *category* is this?" | `config/taxonomy/`, imported hierarchies (apps, products, Oracle schemas, scripts, Control-M variables, LOB→Product→Team) | `taxonomy-importer` |
| **2. Ontology** | "What do the connections *mean*?" | `drydocs/schema/*.cypher`, `drydocs/ontology/`, `knowledge/ontology/` | `ontology-mapper` |
| **3. Knowledge graph** | "What is connected *and* what does it mean?" | the populated Neo4j graph | (loaders) |
| **4. Context graph** | "What matters *right now* for this task?" | task-scoped projections: temporal state, ownership, permissions, current health | (future) |

**Rule of thumb:** import as **taxonomy first** (pure classification, no edges that imply
meaning), then **apply ontology** (the PROV-O / ORG / DPROD rules that give edges meaning),
*then* load. Never invent a relationship type during import — that is an ontology decision
and goes through the `ontology-mapper` + the HITL gate (`docs/restructure/03-hitl-sme-flow.md`).

---

## 2. External reference — call ALL of these, not just BMC

> **Known failure mode:** agents used to "see" only BMC because it was the only vendor with
> files in the repo. Neo4j, Oracle, and the ontology standards lived only as plugin skills,
> so a repo survey missed them. They are now **all** first-class. When a task touches a
> platform, **consult its reference before writing code.**

External reference is split into two tiers by *role*:

### Tier 1 — Reference source *platforms* (you build WITH these)
Index: [`reference/REGISTRY.yaml`](reference/REGISTRY.yaml)

| Platform | What it is | How to call it |
|----------|-----------|----------------|
| **Neo4j** | the graph platform itself | `neo4j-skills` plugin (cypher, modeling, import, graphrag, vector-index, gds, aura, …) + [`reference/platforms/neo4j/`](reference/platforms/neo4j/README.md) |
| **Ontology standards** | PROV-O, W3C ORG, DPROD/EKGF, **SOSA/SSN**, DCAT, SKOS | [`reference/standards/`](reference/standards/README.md) |
| **Academic research** | papers backing modeling choices | [`reference/research/`](reference/research/README.md) |

### Tier 2 — Orchestration *vendors* (you ingest FROM these — one level lower)
Index: [`external/orchestration/README.md`](external/orchestration/README.md)

| Vendor | Status | Reference |
|--------|--------|-----------|
| **BMC Control-M** | **BASELINE** (the canonical orchestrator; truth for folder/job/condition semantics) | [`external/orchestration/bmc-controlm/`](external/orchestration/bmc-controlm/) |
| **AutoSys (CA/Broadcom)** | placeholder — map to baseline | [`external/orchestration/autosys/`](external/orchestration/autosys/README.md) |
| **AWS Airflow / MWAA** | placeholder — map to baseline | [`external/orchestration/airflow/`](external/orchestration/airflow/README.md) |

Oracle (source DB) and Snowflake (future) are **data platforms**, referenced via the Oracle
`db` skill and [`reference/platforms/`](reference/platforms/README.md).

---

## 3. Internal vs external — the publish boundary

This repo is **private but sometimes published**. Keep the boundary clean:

| Bucket | Provenance | Publishable? |
|--------|-----------|--------------|
| `reference/`, `external/` | external (vendor / standards / public knowledge) | **Yes** |
| `knowledge/` | internal, graph-*defining* design prose | Yes (no secrets) |
| `internal/` | internal, **confidential** (real LOB→Product→Team rosters, SEAL data, real SIDs/schemas) | **NO — stripped on publish** |
| `drydocs/` | code | Yes (no embedded secrets) |

**Never** commit real SIDs, credentials, server addresses, GHE org names, or production data
values outside `internal/` (which is git-ignored from any public push). See
[`PUBLISH-BOUNDARY.md`](PUBLISH-BOUNDARY.md).

---

## 4. Source-of-truth precedence (the config layer)

When sources disagree about what something *is*, resolve in this order (configurable in
[`config/precedence.yaml`](config/precedence.yaml)):

1. **BMC baseline** — orchestration vendor's canonical object semantics.
2. **Internal standards** — `knowledge/standards/` naming/normalization conventions that
   refine the baseline for our environment.
3. **LOB → Product → Team** — the org taxonomy that assigns ownership & context.

The configuration layer (`config/`) is where taxonomy meets ontology: it records, per source,
*which orchestrator it uses* and *which ontology rule applies* — confirmed by the SME through
the guided gate before any graph write.

---

## 5. Sub-agents (delegate; they run on cheaper models)

Defined in [`.claude/agents/`](.claude/agents/). Dispatch by layer:

| Agent | Use for | Model |
|-------|---------|-------|
| `reference-librarian` | look up vendor/standard/platform facts; keep `reference/REGISTRY.yaml` current | haiku |
| `taxonomy-importer` | import raw hierarchies into `config/taxonomy/` as pure classification | sonnet |
| `ontology-mapper` | propose taxonomy→ontology rule bindings (PROV matrix), drive the HITL gate | sonnet |
| `pipeline-config` | maintain `config/` (precedence, source-registry, mappings); never writes graph directly | sonnet |

**Orchestration stays with the main (Opus) session.** Sub-agents do scoped, well-specified
units from `docs/restructure/02-backlog.md`. Each backlog item names its agent + acceptance test.

---

## 6. Working agreements

- **Verify before asserting.** A recalled fact or stale doc that names a file/flag/column may
  be wrong — confirm it exists before relying on it.
- **Taxonomy imports are reversible; ontology edges are not casual.** New relationship types
  go through `docs/RELATIONSHIP_GUIDE.md` + the `relationship_vocabulary.yaml` registry +
  the HITL gate. Set `status: planned` first.
- **Tests gate every change:** `poetry run pytest -q`, `python -c "import drydocs.cli"`,
  `drydocs --help`.
- **Secrets discipline:** architecture-level only. No real data values in commits.

See `README.md` for the runnable pipeline and `docs/restructure/01-project-plan.md` for the plan.
