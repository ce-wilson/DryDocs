# knowledge/standards/ — internal standards, defined by taxonomy path

**Corpus: INTERNAL** — company-specific configurations, standards, and conventions. This is the
**conformance** corpus: it answers *"is this how we do it / are we allowed to do it here?"*,
as distinct from the external **capability** corpus
([`external/orchestration/bmc-controlm/`](../../external/orchestration/bmc-controlm/)) which
answers *"is this legal/possible in Control-M?"*. A validation flow runs both stages — vendor
legality, then internal conformance — so the two are never merged.

**Trust tier:** internal / mutable / SME-asserted — **lower authority than vendor capability
statements, but authoritative for *our* standards.** In `config/precedence.yaml` this is the
`internal-standards` tier (authority 2): it **refines the BMC baseline**, it does not redefine it.

---

## Each standard is defined by its taxonomy path

Every standard declares, in YAML frontmatter, **where in the taxonomy it applies** and **what it
governs**. This binds the prose standard to the structured model (`config/taxonomy/` +
`config/precedence.yaml` + the ontology) so an agent can find the right rule for a given element.

```yaml
---
standard:       control-m-folder-naming
domain:         technology                              # top taxonomy domain
taxonomy_path:  technology/orchestration/control-m/folder   # where it applies
governs:        JobFolder.name                          # the taxonomy element it constrains
authority:      internal-standards                      # config/precedence.yaml tier 2
refines:        bmc-baseline                            # sits on top of the vendor baseline
applies_to_source: controlm-psgmgr
status:         active | planned
trust_tier:     internal / SME-asserted / mutable
---
```

### The taxonomy domains (path roots)

Standards are organized under the three top-level taxonomy domains (the "Business / Technology /
Data" layers):

| Domain | Folder | Governs | Precedence authority |
|--------|--------|---------|----------------------|
| **technology** | [`technology/`](technology/) | orchestration objects, platforms (Control-M folders, jobs, DCs, calendars) | `internal-standards` (refines `bmc-baseline`) |
| **business** | [`business/`](business/README.md) | org taxonomy: LOB → Product → Team naming & ownership rules | `lob-product-team` |
| **data** | [`data/`](data/README.md) | data platforms: Oracle/Snowflake schema, dataset, data-product rules | `internal-standards` |

> A `taxonomy_path` reads root-to-leaf: `domain / area / system / element`. The folder a standard
> lives in is its `domain`; the full `taxonomy_path` in frontmatter pins the exact element.

---

## Index (by taxonomy path)

### technology/orchestration/control-m/
| Standard | `taxonomy_path` | governs | status |
|----------|-----------------|---------|--------|
| [folder-naming-convention](technology/folder-naming-convention.md) | `…/control-m/folder` | `JobFolder.name` — PRAOCG 6-char code (env · LOB · app/platform · type) | active |
| [data-center-naming-convention](technology/data-center-naming-convention.md) | `…/control-m/data-center` | `ControlMServer.data_center` — DC name encodes the default execution time (EST) | active |
| [description-field-metadata-plan](technology/description-field-metadata-plan.md) | `…/control-m/job` | `ControlMJob.description` — repurposed as pipe-delimited key:value metadata | 🔵 planned |
| [calendar-resolution-projection-plan](technology/calendar-resolution-projection-plan.md) | `…/control-m/calendar` | `ControlMJob.schedule` — resolve calendars to project when jobs run | 🔵 planned |

### business/  ·  data/
Placeholders — no standards captured yet. See each domain's README for what belongs there.

---

## Adding a standard

1. Pick the **domain** (`technology` / `business` / `data`) and write the full `taxonomy_path`.
2. Create the file under that domain folder with the **frontmatter block** above.
3. Set `governs` to the precise taxonomy element (a node label + property, or a node/edge type).
4. Set `authority` from `config/precedence.yaml`; standards `refine` the baseline, they don't
   redefine it.
5. Add a row to the index above.
6. If the standard constrains a value the loaders apply, the matching normalization lives in
   `drydocs/` and should cite this `taxonomy_path`.

> Longer term, Confluence ingestion (the `drydocs-scrape` build) feeds this corpus; manually
> captured SME standards live here too. Tag provenance (`trust_tier`) on graph load.
> See project memory `project-drydocs-scrape-two-corpus` for the two-corpus rationale.
