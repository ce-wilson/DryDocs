# Home Lending — External Vendor Icon Registry

`manifest.json` is the single source of truth. Every consumer (HTML sheet,
Confluence, PowerPoint, C4-style diagrams, auto-reports, a future tool-picker)
reads from it, so an icon or colour changes in exactly one place.

    vendors/packaged/   pullable from a package; safe to regenerate
    vendors/external/   self-supplied / trademark-sensitive / cached — committed
    png/                raster exports
    manifest.json       id -> label, category, svg/raster path, brand hex, provenance, verified
    SOURCE.md           this file

## Colour + source status

verified:true means the brand hex is confirmed from the package's own metadata.
verified:false means **confirm the colour** (e.g. from brandcolorcode.com — I can't
reach that site) and/or supply an official asset; the sheet marks these with "?".

| Vendor | Icon source | Colour | Status |
|--------|-------------|--------|--------|
| BMC | Simple Icons | #FE5000 | verified |
| Splunk | Simple Icons | #000000 | verified (brand accent colour may differ — confirm) |
| Atlassian | Simple Icons | #0052CC | verified |
| Jira | Simple Icons | #0052CC | verified |
| GitHub | Simple Icons | #181717 | verified |
| Red Hat | Simple Icons | #EE0000 | verified |
| neo4j | Simple Icons | #4581C3 | verified |
| Amazon S3 | AWS Architecture Icons | #7AA116 | verified (multi-colour icon) |
| AWS Glue | AWS Architecture Icons | #7AA116 | verified (multi-colour icon) |
| AWS Lambda | AWS Architecture Icons | #D86613 | verified (multi-colour icon) |
| Snowflake | Simple Icons | #29B5E8 | verified |
| Teradata | Simple Icons | #F37440 | verified |
| SQL Server | Simple Icons — cached | #CC2927 | **confirm colour** (approx) |
| Subaru | self-supplied (transparent SVG) | #013C74 | verified |
| Maserati | self-supplied (webp → transparent PNG) | #0C2340 | verified |
| Ab Initio | self-supplied (red block + wordmark SVG) | #E31A2E | confirm official brand colour |
| Informatica | Simple Icons — cached | #FF4D00 | **confirm colour** (approx) |
| Alteryx | Simple Icons — cached | #0078C8 | **confirm colour** (approx) |
| Oracle (GOS) | Simple Icons — cached | #C74634 | **confirm colour** (approx) |
| Salesforce | Simple Icons — cached | #00A1E0 | **confirm colour** (approx) |
| Experian | **none available** | #632678 | **upload official logo** — placeholder shown |

## Generic (non-brand) icons

Infrastructure & Facilities (server, data center, database, storage, cloud, network,
building, campus, warehouse) and Users & Personas (developer, business, analyst,
admin/ops, security, customer/support, executive, team) come from **Material Design
Icons** (Pictogrammers, Apache-2.0) under `vendors/generic/`. These have no brand
colour: infrastructure uses a neutral steel `#475569`, and each persona is themed by
its own hex. Recolour or add roles by editing the manifest — the fill follows `hex`.

## To finalise

1. Paste the confirmed hex for: Ab Initio, Informatica, Alteryx, Oracle, Salesforce
   (Splunk too if brandcolorcode differs from #000000). I'll set them + flip verified:true.
2. Upload an Experian logo (SVG or PNG); I'll replace the placeholder.
3. Oracle is labelled with alias "GOS" — rename in the manifest if that's not right.

## Trademark note

Package licences (CC0, AWS icon terms) cover the icon *files*, not the trademarks.
All vendor names and logos remain their owners' property; this registry is for
internal architecture / reporting documentation. Confirm each vendor's brand
guidelines before external publication — this is especially relevant for the
car-manufacturer logos used in auto reports.
