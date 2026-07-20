# external/orchestration/ — Tier 2: the orchestrators we ingest FROM

The batch-scheduling vendors whose job/dependency metadata DryDocs ingests. **One level lower**
than `reference/` platforms: these are *sources of pipeline data*, not platforms we build with.

All content here is captured **vendor reference** (public product docs) — not graph content,
not loaded into Neo4j directly. It documents the external systems the loaders read from.

## The vendors

| Vendor | Role | Status | Maps to baseline via |
|--------|------|--------|----------------------|
| **BMC Control-M** | **BASELINE** — canonical orchestrator semantics | live | (is the baseline) |
| **AutoSys** (CA/Broadcom) | alternate orchestrator | placeholder | [`autosys/`](autosys/README.md) crosswalk |
| **AWS Airflow / MWAA** | cloud orchestrator | placeholder | [`airflow/`](airflow/README.md) crosswalk |

## Why BMC is the baseline

BMC Control-M is the established orchestrator; its object model (Folder → Job → Condition →
dependency) is the **canonical vocabulary** every other orchestrator is mapped onto. When
AutoSys or Airflow is onboarded, we do **not** invent new graph concepts — we crosswalk their
native objects to the BMC-baseline concepts (see each placeholder's crosswalk table). This
keeps the knowledge graph orchestrator-agnostic.

## "A way to confirm they are correct"

Each orchestrator has a **crosswalk** (native object → baseline concept) and a **confirmation
check**. Before a new orchestrator's data loads, the `pipeline-config` agent renders the
crosswalk and the SME confirms each mapping through the guided gate
(`docs/restructure/03-hitl-sme-flow.md`). The confirmed crosswalk is recorded in
`config/source-registry.yaml`. Precedence when a mapping is ambiguous: BMC baseline wins
(`config/precedence.yaml`).

## Adding a vendor
One subdir per product. Keep a `SOURCE-MANIFEST.md` (provenance + version) and a
`crosswalk.md` (native → baseline). Until both exist and are SME-confirmed, the vendor stays a
placeholder and its loader is not activated.
