# The node-status envelope (O28)

**Classification:** Internal-Public. **Status:** adopted 2026-08-01.

One shape carries every health signal DryDocs shows about a node — the
inspector sidebar's status section and the landing hub's spoke health glyphs
both read it, and every future producer adds to it without changing it.

```jsonc
{
  "type":    "drydocs.loader/rows-rejected",  // REQUIRED, source-namespaced
  "level":   "warning",                       // REQUIRED, info | warning | error
  "message": "3 of 120 rows failed validation", // REQUIRED, human-readable
  "error":   "row 7: [{'loc': ...}]"          // OPTIONAL detail slot
}
```

## The two rules that keep it stable

**1. Always DERIVED by a producing system. Never hand-authored.**
A status item is a *measurement*, not an annotation. Nobody types one, and no
UI writes one. If a human judgement needs recording, that is a mapping or a
gate decision (`docs/restructure/03-hitl-sme-flow.md`) — a different mechanism,
deliberately. This is what lets the UI treat every item as current: an item
exists because a producer just observed the condition.

**2. New sources add NAMESPACED TYPES, never new shapes.**
`type` is `<source>/<slug>`. A new producer picks its own namespace and emits
whatever slugs it needs; it never adds a field, and it never has to negotiate a
global type vocabulary with anyone. The UI renders an unknown type without a
code change — namespace and level are enough to place and colour it.

This is Backstage's `status.items` precedent, and it is worth naming why that
design won: Backstage entities gather status from many independent processors
(ingestion, lint, orphan detection), and the shape held because the *extension
point was the type string*, not the object. Systems that instead extended the
object accumulated per-producer fields that every consumer had to learn.

## Reading the absence of items

| Graph state | Meaning |
|---|---|
| `:JobRun` exists, `status_items` empty | **Healthy** — a producer ran and found nothing to report |
| No `:JobRun` for the loader | **Unknown** — nothing has ever run |

No all-clear item is emitted, on purpose: an "everything fine" item would make
*healthy* and *never observed* render identically, which is the failure mode
where a dashboard is green because nothing is watching. Health glyphs must
distinguish them.

## Storage: a property on `:JobRun`, not a node and edge

Items ride as a **list of JSON strings** on the `:JobRun`
(`run.status_items`), written by `BaseLoader._close_run`.

Two decisions worth keeping:

- **Property, not a new node + relationship.** A relationship type is an
  ontology decision that goes through the HITL gate (CLAUDE.md §1) — and a
  derived health signal has no ontological meaning to gate. Modelling it as an
  edge would put an operational metric through a semantic review it does not
  need, and would make every producer's rollout gate-bound.
- **JSON strings because Neo4j cannot store a map inside a list property.**
  The alternative — parallel lists (`status_types`, `status_levels`, …) — puts
  the envelope's integrity in the *alignment of three lists*, where one
  mismatched append silently mislabels an item's severity. One string per item
  cannot desynchronise. The cost is that consumers parse; the shape is fixed,
  so that parse is safe.

## The wire: `loads.status-items.v1`

The QuerySpec unwinds the list to one row per item and returns the item JSON
alongside the run's identity. Consumers parse the `status_item` column.
Splitting into typed columns would need JSON parsing in Cypher (APOC), which
this repo deliberately does not depend on for read paths.

## Producers

| Source namespace | Producer | Types |
|---|---|---|
| `drydocs.loader` | `BaseLoader._close_run` via `status_items_for()` | `run-failed` (error), `rows-rejected` (warning), `removed-from-source` (warning), `reactivated` (info) |

`status_items_for()` is a pure function of the run summary, so the derivation is
unit-tested without a database — the property that makes "always derived"
enforceable rather than aspirational.

### Adding a producer

1. Pick a namespace (`<system>` or `<system>.<component>`).
2. Derive items from something you just measured.
3. Emit the four-key shape. Add no fields.
4. Add a row to the table above.

If the shape does not fit, that is the signal to ask whether the thing being
recorded is a *status* at all — an annotation, mapping, or gate ruling has its
own home.
