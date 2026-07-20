# knowledge/ — internal unstructured knowledge that **defines** the graph

DryDocs-owned, human-authored knowledge that determines what the graph *means*:
the ontology, naming standards, and design decisions that the loaders and schema
encode. This is the "source of truth" prose behind the structured graph.

Contrast with [`../external/orchestration/`](../external/orchestration/README.md), which holds **external vendor**
reference material that merely supports building the project.

## Contents

| Path | What it is |
|------|-----------|
| `ontology/` | The DryDocs ontology documentation (`DryDocs_Ontology_Documentation.md`) — the canonical class/relationship model the `drydocs_core/schema/*.cypher` and `drydocs_core/ontology/` code implement. |
| `standards/` | Internal conventions: data-center & folder naming, calendar-resolution and description-field plans. The rules loaders apply when normalizing source data. |
| `upgrade-plans/` | Forward-looking improvement plans (e.g. GraphRAG / LLM-navigation upgrade). |

## Related (left in place to avoid link churn)

- `../docs/patterns/data-catalog/` — enterprise data-catalog ontology + crosswalk
  (DCAT/DataHub alignment). Conceptually part of this bucket; see the migration
  note in [`ARCHITECTURE.md`](ARCHITECTURE.md).
- `../docs/` — engineering process, history, reviews, and product docs (neither
  vendor reference nor graph-defining knowledge).

## Why this split

Previously, vendor reference (BMC Control-M docs) and internal graph-defining
knowledge (ontology, standards) were intermixed at the repo root. Separating them
makes it unambiguous which prose is *ours and authoritative for the graph* vs
*captured external reference* — important now that an LLM agent will read this
corpus. See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full rationale and the
planned (not-yet-executed) code-module reorganization.
