# config/taxonomy/ — imported raw hierarchies (classification only)

Taxonomy = "what category is this?" These files hold imported hierarchies as **pure
classification**: parent/child, type-of, member-of. **No meaning-bearing edges** (no `USED`,
no `DEPENDS_ON`) — those are an *ontology* decision and live in `../taxonomy-ontology-map.yaml`
after SME confirmation.

The `taxonomy-importer` sub-agent writes here. Keep imports faithful to the source; do not
"improve" the hierarchy during import.

## What gets imported here
| Taxonomy | From source | Example shape |
|----------|-------------|---------------|
| Control-M folders/jobs/conditions | `controlm-psgmgr` | Folder ▸ Job ▸ Condition |
| Applications / Ports | `seal-extract` | Application ▸ Port(kind) |
| LOB → Product → Team | `catalog-pat` | LOB ▸ ProductLine ▸ Product ▸ AreaProduct ▸ DevTeam |
| Oracle schemas/tables/scripts | `oracle-schemas` | Schema ▸ Table; Script |
| Control-M variables | `controlm-psgmgr` | variable-class ▸ variable |

> **`platforms.yaml`** is the reconciliation surface for the platform / execution-technology
> taxonomy — CONFIRMED at the C12 platforms-taxonomy gate (2026-07-21): `:SchedulerKind` is
> deprecated and the model is the software registry (`software-registry.yaml` rows with
> `role: orchestrator`, reached via `USES_SOFTWARE {source: 'batch-port'}`); no capability/tool
> class layer (the interim Ais* family was removed unbuilt — role over class). Its seed rows
> carry the `software_registry_ref` crosswalk links.

> **`context-types.yaml`** is an authored vocabulary, not an import: the controlled list
> behind the SME intake page's context-type dropdown (O45; UI-WIP/sme-intake-page-plan.md §2).
> Values are retired, never deleted; the console reads the generated artifact
> `web/src/generated/context-types.json` (guard: `tests/unit/test_context_types.py`).

## Format
One file per taxonomy, e.g. `lob-product-team.yaml`:
```yaml
taxonomy: lob-product-team
source: pat                        # a v2 SYSTEM id (or a dataset id where the capture is single-feed)
authority: lob-product-team        # from precedence.yaml
nodes:
  - id: LOB:CCB
    type: CatalogLOB
    children: [ProductLine:Auto, ProductLine:Card]
  # ... classification only — ownership/meaning edges come via the ontology map
```

> Confidential rosters (real team names, people) do **not** go here — they live in
> `internal/org/`. This dir holds structure/shape, safe to publish.
