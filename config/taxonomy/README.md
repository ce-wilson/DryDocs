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

> **`platforms.yaml`** is a *placeholder*, not a source import — the reconciliation surface for the
> platform / execution-technology taxonomy (`:SchedulerKind`, slated for deprecation →
> `:AisCapability` + `:AiTool`). Held until the HITL gate; see its header for the open questions.

## Format
One file per taxonomy, e.g. `lob-product-team.yaml`:
```yaml
taxonomy: lob-product-team
source: catalog-pat
authority: lob-product-team        # from precedence.yaml
nodes:
  - id: LOB:CCB
    type: CatalogLOB
    children: [ProductLine:Auto, ProductLine:Card]
  # ... classification only — ownership/meaning edges come via the ontology map
```

> Confidential rosters (real team names, people) do **not** go here — they live in
> `internal/org/`. This dir holds structure/shape, safe to publish.
