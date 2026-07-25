# Databricks Unity Catalog — governance/semantic layer as a design precedent

**Classification:** External (public vendor documentation; cite `source_url`, do not paste full texts)
**Researched:** 2026-07-25 · **Trigger:** SME saw "Unity Catalog works so well in Databricks" and
asked what it is actually capturing. Not currently an ingest source — read this as a *tool pattern*
to borrow from, the same way [NeoCarta](README.md#neocarta--context-for-the-data-catalog-layer) is.

Companion to the NeoCarta write-up in [`README.md`](README.md): both are public builds of the
catalog/glossary layer we model in [`docs/patterns/data-catalog/`](../../docs/patterns/data-catalog/README.md).
Unity Catalog is the more useful of the two for us, because it is the only public example that puts
the **glossary, the domain grouping, the controlled tags, and the enforcement** in one governed
object model — which is the shape `enterprise-data-catalog-ontology.md` already describes.

---

## What it is

Unity Catalog is the governance and metadata layer built into the Databricks platform. The framing
that matters: it is not a documentation tool bolted onto the side of the data — **it is the
namespace**. Every table, view, volume, function, ML model, and (recently) dashboard or agent is a
*securable object* addressed as `catalog.schema.object`, and the object that resolves a SQL
reference is the same object carrying the permissions, the lineage, and the descriptions. Data
cannot be addressed without going through it.

That single decision explains most of the enthusiasm. What it replaced — one Hive metastore per
workspace — fragmented permissions, definitions, and discovery every time a team created a
workspace or entered a new cloud region. Unity Catalog collapses that to one metastore per region
per account with one ANSI-SQL `GRANT` model across all of it.

## Structure

```
metastore                 top-level container; storage credentials, external locations, shares
└── catalog               first level — unit of isolation (org unit, data domain, or prod/dev)
    └── schema            second level — project, use case, or team
        └── table | view | volume | function | model | service
```

Three-level namespace, uniform below. Tables and volumes are either **managed** (Unity Catalog owns
governance *and* storage) or **external** (governance only; data stays where it is) — the split
worth noting, because governing what you do not own is our problem too.

## What it captures — three tiers with different trust properties

Keep these separate. They are acquired differently and are trustworthy to different degrees.

**1. Technical metadata** — schemas, types, formats, storage locations, constraints. Declared.

**2. Observed metadata** — the interesting tier. Lineage is **not declared by developers**: Unity
Catalog intercepts Spark execution plans at runtime and derives table-level and column-level lineage
from what actually ran. No annotations, no agent to install, no hand-maintained DAG. It surfaces as
ordinary queryable tables (`system.access.table_lineage`, `system.access.column_lineage`) alongside
audit logs and usage. Metadata is a byproduct of doing the work rather than a documentation chore,
which is why it stays accurate. The documented limits are honest: column lineage breaks when a
source is referenced by path rather than table name, and UDFs obscure the source→target mapping.

**3. Business / semantic metadata** — newest, fastest-moving, and the tier that prompted this note:

| Feature | Status (as of DAIS 2026) | What it is |
|---|---|---|
| **Governed tags** | GA | Account-level tags with an attached **tag policy** constraining where/how they may be applied — a controlled vocabulary with enforcement, not free text |
| **Data classification** | GA | An agentic AI system that scans and tags tables for sensitive data |
| **Domains** | Public preview | Assets grouped "around how your business is structured — by function, business unit, or geography," explicitly *"organized by domain rather than by technical location"* |
| **Metric views** | Preview (materialization, multi-fact) | KPI definitions as governed reusable objects; measures separated from dimensions so "revenue" means one thing everywhere |
| **Agent metadata** | Shipping | Synonyms, display names, formatting rules — so AI tools read a column in business terms |
| **Glossary** | "Coming soon" | *"Authoritative concepts, terms, and taxonomies"*; *"glossary pages connect to the underlying data and to each other, capturing relationships"* |
| **ABAC** | GA (row filter / column mask) | Access policies that key on governed tags as attributes |

## Intent, and how it shifted

Original intent was **unification**: one permission model, one namespace, one discovery surface
across workspaces and clouds. Databricks then open-sourced it in 2024 (Apache 2.0, now an LF AI &
Data project) implementing the **Iceberg REST Catalog** and Hive metastore APIs — a bid to become
the neutral catalog rather than a lock-in point.

Current intent is openly about **AI agents**. Their line: *"Agents are only as good as the context
they have. Without a shared definition of what the business actually means, even a capable agent
will guess."* The semantic features above feed what they call the **Genie Ontology**, *"a
continuously learned enterprise context layer."*

> **Read that product name with care.** "Genie Ontology" denotes a *learned context layer*, **not an
> ontology in the PROV-O / W3C ORG sense**. There is no formal relationship vocabulary, no typed
> edges with defined semantics, no reasoning. It is a rich catalog with tags, domains, and
> definitions attached. Do not cite it as ontology precedent; cite it as *catalog* precedent.

---

## Crosswalk to DryDocs

The striking result: Unity Catalog's four semantic features land almost exactly on node types
[`enterprise-data-catalog-ontology.md`](../../docs/patterns/data-catalog/enterprise-data-catalog-ontology.md)
already defines. Independent convergence on the same four concepts is the strongest signal in this
note.

| Unity Catalog | DryDocs analogue | Note |
|---|---|---|
| Domains ("by domain, not technical location") | `CatalogDataDomain` (`BELONGS_TO`); LOB→Product→Team | precedence layer 3 in `CLAUDE.md` §4 — same instinct, arrived at separately |
| Glossary (terms, taxonomies, terms linked to each other) | `CatalogBusinessTerm` (`IS_REPRESENTED_AS`) | *terms linked to terms* is a concept scheme — SKOS-shaped |
| Governed tags + tag policy | `CatalogTag` (`IS_TAGGED_WITH`), `CatalogClassifier` | policy-constrained ≈ our "no unlabeled default" |
| Data classification (sensitivity) | `config/classification.yaml` + `tests/unit/test_classification.py` | ours is enforced by test, theirs by policy engine — same rule |
| Agent metadata (synonyms, display names) | *no analogue yet* — see the acronym-catalog idea in `IDEAS.md` | the gap this note surfaces |
| Lineage from Spark execution plans | lineage from Control-M folder/job/condition definitions | both **derived from what ran**, not asserted |
| `system.access.*` / `information_schema` | our loaders' source manifests | privilege-filtered, SQL-queryable metadata surface |
| Metric views | *no analogue* — DryDocs has no measure layer | out of scope for a support knowledge graph |
| Three-level `catalog.schema.object` | four-layer model (`CLAUDE.md` §1) | **not** analogous — see limits below |

## Takeaways

1. **Capture as a byproduct, not a chore.** The lineage design is the transferable idea: derive it
   from the execution record, never ask a human to declare it. Our equivalent is deriving
   dependencies from Control-M definitions rather than from documentation — which is what the
   VERBATIM/GROUNDED/SYNTHESIZED trust axis already encodes. Unity Catalog is a clean public
   demonstration that derived-from-what-ran is the only kind that stays true.

2. **A controlled vocabulary needs an enforcement point, or it rots.** Governed tags are only
   interesting because of the attached *policy*. Free-text tags were already possible and did not
   work. Our analogue is the classification test, and the lesson generalizes to any glossary we
   build: the entry and its enforcement ship together.

3. **The glossary parallel is external evidence for the acronym-catalog idea.** A well-resourced
   platform vendor looked at the agentic-era failure mode and shipped synonyms, display names,
   authoritative terms, taxonomies, *and terms that link to each other*. Their stated reason —
   agents guess when meaning is ambiguous — is the AIS collision generalized. Worth citing when the
   Q6 ruling is made, because it shows the catalog shape is a known answer to a known problem, not
   a reaction to one bad label.

4. **Limits — do not over-borrow.** Unity Catalog governs **data assets**. It has no model of
   orchestration and cannot answer *what runs, what does it depend on, who owns it, which
   application it belongs to* — which is DryDocs' entire question. Its semantic layer is attached
   metadata, not a graph with defined edge meanings, so it does no work that
   `relationship_vocabulary.yaml` exists to do. Adjacent precedent, not a substitute, and **not** a
   standard to seed (same verdict as NeoCarta).

5. **Possible future ingest source.** If the company runs Databricks anywhere,
   `system.access.table_lineage` and the per-catalog `information_schema` are privilege-filtered and
   SQL-queryable — a legitimate registered source, necessarily **Internal**-classified. Not
   proposed; noted so the option is on record.

---

## Sources

All public vendor documentation and blogs; links verified 2026-07-25.

| Topic | Link |
|---|---|
| Overview / object model | https://docs.databricks.com/aws/en/data-governance/unity-catalog/ |
| Lineage (capture + limits + system tables) | https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-lineage |
| Business semantics (metric views, agent metadata) | https://docs.databricks.com/aws/en/uc-semantics/ |
| Governed tags | https://docs.databricks.com/aws/en/admin/governed-tags |
| Data classification | https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-classification |
| Information schema | https://docs.databricks.com/gcp/en/sql/language-manual/sql-ref-information-schema |
| What's new at Data + AI Summit 2026 (statuses, Genie Ontology quote) | https://www.databricks.com/blog/whats-new-unity-catalog-data-ai-summit-2026 |
| Discover + Domains public preview | https://www.databricks.com/blog/announcing-public-preview-discover-and-domains-powered-unity-catalog |
| ABAC / governed tags / classification GA | https://www.databricks.com/blog/abac-row-filtering-and-column-masking-policies-governed-tags-and-data-classification-are-now |
| Open-sourcing announcement | https://www.prnewswire.com/news-releases/databricks-open-sources-unity-catalog-creating-the-industrys-only-universal-catalog-for-data-and-ai-302170787.html |
| Unity Catalog OSS docs (Iceberg REST / HMS interop) | https://docs.unitycatalog.io/ |
