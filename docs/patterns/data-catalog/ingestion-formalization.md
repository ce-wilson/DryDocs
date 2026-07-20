# DryDocs Ingestion — Compare, Contrast & Formalization

> **Sanitized pattern doc.** Generic functional names only. The identifier-bearing
> SME sourcing lookup (real system code-names, API endpoints, SEAL IDs) is the
> gitignored twin at `drydocs/data/data-catalog/ccb-ingestion-sme-sourcing.md`
> (see [`PUBLISH-BOUNDARY.md`](../../../PUBLISH-BOUNDARY.md)).
>
> Companion to: [dataset-registration-architecture.md](dataset-registration-architecture.md)
> (the enterprise platform reference) and
> [data-catalog-drydocs-crosswalk.md](data-catalog-drydocs-crosswalk.md) (node-level mapping).

---

## Executive Summary

**Who this is for, first.** The immediate customer is **application support teams** — the
people who keep scheduled workloads running. They face operational questions the enterprise
catalog cannot answer: *what jobs feed this asset, what runs before and after this job, who
owns it, and what breaks downstream if tonight's run fails?* DryDocs builds that
**job → data dependency graph from the scheduler** (Control-M) and turns it into something a
support engineer can query for impact analysis, incident triage, and onboarding. That value
**stands on its own** — it requires no enterprise pipeline, no governance program, and no one
ingesting DryDocs output.

**Built aligned, not coupled.** No enterprise system consumes DryDocs today, and nothing in
this design assumes one will. DryDocs is nonetheless **modeled to the enterprise governance
spine** on purpose: same backbone (`Application → flow → job → Dataset`), same key (the
application / SEAL ID). The enterprise platform's own reference model defines a
`dataFlow → dataJob` layer under each application that today sits **unfilled** — there is no
automated source for run-time job-to-dataset lineage. By speaking that model from day one,
DryDocs can **dock into the governance program later without a rebuild** if and when that
program is ready to populate the layer. That alignment is **optionality**, not an obligation.

**Where it would supplement governance (future optionality).** *If* adopted later, DryDocs
feeds three of the ten platform capabilities with job-level truth they cannot otherwise get —
without competing with any of them:

| Platform capability | What DryDocs is positioned to supply |
|---|---|
| **5 — Data Lineage** | Run-time, job-to-dataset lineage extracted from the actual scheduler, not hand-drawn design lineage. |
| **9 — Data Audit, Compliance & Controls** | "Which job, owned by which app/team, last wrote this asset" — provenance for ownership & controls reporting. |
| **10 — Data Observability** | Job execution history and dependency topology — the signal source for readiness/anomaly views. |

The join — today latent, tomorrow live — is the **Application node (SEAL ID)**, the same
real-world entity in both planes. DryDocs references catalog datasets/distributions by key; it
never copies them.

---

## Compare & Contrast

| Dimension | Enterprise D&A Platform | DryDocs |
|---|---|---|
| **Primary object** | Dataset / Distribution (data at rest) | Orchestration Job (a process) |
| **Question answered** | What data exists, who owns it, is it governed | How data is produced & moved; what depends on what |
| **Lineage type** | Design-time data lineage (source → sink) | Run-time process lineage (job → job, job → asset) |
| **Source of truth** | Catalog APIs, model workflow, glossary, DQ platform | Scheduler export (Control-M XML), staging tables |
| **Scope** | Enterprise-wide governance platform (10 capabilities) | One focused layer: process → asset graph |
| **Identity scheme** | Catalog URNs + Application/SEAL IDs | Composite keys `(data_center, folder_id, job_id)` |
| **Build posture** | Large, multi-system, multi-year program | Small, single-pipeline, reuse-not-rebuild |

**The shared backbone (why a clean handshake is possible).** Both models hang everything off
the same spine: `Application → (flow) → (job) → produces/consumes → Dataset`. The enterprise
platform owns the right side (Dataset and below); DryDocs owns the middle (flow/job). Same
Application node, same direction of flow — they snap together at the Application key.

**The deliberate divergence (what we do NOT duplicate).** Keeping with *don't boil the
ocean*, DryDocs explicitly declines to rebuild:

- ❌ the **Business/Technical Catalog** — we reference cataloged datasets by key, not re-store them;
- ❌ the **glossary / ontology / data-model authoring** — those have systems of record;
- ❌ **data-quality rule authoring** and **access policy** — owned by the DQ and access systems;
- ❌ **column/field-level schema** — out of scope for a process graph today.

DryDocs ingests **only process-side metadata** and links outward by reference.

---

## How This Formalizes DryDocs Ingestion

A single, scoped ingestion contract — small enough to hold in your head:

1. **Ingest one source per asset class.** Process metadata comes from the scheduler export
   only. We do not poll catalog/glossary/DQ APIs during ingestion — those are *referenced*,
   not *imported*.
2. **Three node families, one bridge.** Produce `Application → AppDataFlow → Job → DataAsset`.
   `Application` is **MERGE-only** against the existing node (the SEAL ID); never mint a new
   application node, never a `CatalogApplication`.
3. **Reference, don't copy, the data plane.** Where a job touches a cataloged dataset, attach
   a typed edge to a *reference* node carrying the catalog key (URN / app-id), so a downstream
   join can resolve it without DryDocs holding catalog content.
4. **Reuse the existing extractor format.** All ingestion inputs are authored in the
   established machine-first sections — `§META §DATAASSETS §JOBS §UC §CYPHER §OQ` — via the
   `data-context-extractor` skill. No new format.
5. **Classifiers are shared, not forked.** When process metadata carries `<OrgCatalog>:*`
   classifier values, MERGE them onto the same `:CatalogClassifier` nodes the catalog uses.

> Net effect: ingestion is a **thin, well-bounded pipe** (scheduler → process graph) that
> *plugs into* enterprise governance at the Application key and the classifier namespace,
> rather than a parallel governance stack.

---

## SME Guidance — "What Does What" at the Company Level

Use this to know which enterprise function owns which fact, so you can hand-write targeted
collection prompts later. (Generic names here; **real system names + endpoints + SEAL IDs are
in the gitignored twin** `ccb-ingestion-sme-sourcing.md`.)

| Enterprise function | Owns / answers | DryDocs needs it for | Reference, not import? |
|---|---|---|---|
| **Reference Data system** | Reference data, term valid values, authoring governance | Resolving coded values seen in jobs | Reference |
| **Vocabulary / Glossary** | Business terms, data concepts, definitions | Mapping a data element's *term id* → business meaning | Reference |
| **Model Workflow system** | Logical/physical models, model certification | Understanding what a dataset *should* contain | Reference |
| **Business/Technical Catalog** | Datasets, distributions, ownership, domain | The **anchor** a job produces/consumes; the Application key | **Bridge** (key only) |
| **Publishing & Processing platform** | Data jobs, distributions, schedules | Cross-check vs. our scheduler-derived jobs | Compare |
| **Data Quality platform** | DQ rules, contracts, BDQ/TDQ results | Linking a job/asset to its quality signal | Reference |
| **Lineage / Observability (state insight)** | Run/observability reports, metrics | Where our process lineage feeds *in* | Supplies-to |
| **Access governance** | Access policy, RBAC roles, audit | Out of scope for ingestion | Out of scope |

**Where to get info (sanitized pointers — real locations in the twin):**

- **Datasets / data elements / distributions / DQ rules for an application** → the Catalog
  collection API (`Dataset` → `Data Element` → `Distribution` → `DQ rules` chain, filtered by
  application id). This is the same path the enterprise *Semantic Engine* uses to hydrate its
  graph — we reuse it for *reference resolution*, not for re-cataloging.
- **Data concepts / domains** → the data-concepts system of record.
- **Glossary term for a term id** → the glossary details snapshot.
- **Ontology blueprint (versioned)** → the ontology repository.
- **Application ↔ owner / SEAL facts** → the operational registry (SEAL).

---

## Open Questions for the SME

1. Does the Catalog collection API let us resolve a Dataset/Distribution key → Application ID
   automatically (so DryDocs links by reference without manual mapping)?
2. Are `<OrgCatalog>:` classifiers available as a machine-readable registry for direct MERGE?
3. Should our process-side `Worker`/`Team` identities merge into the catalog's, or bridge via
   a `SAME_IDENTITY` edge?
4. Can the platform team accept DryDocs as the **source** that populates their unfilled
   `dataFlow → dataJob` layer (capability 5/10), or do they expect to build their own?
