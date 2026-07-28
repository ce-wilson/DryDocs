# internal/dsi-reference — Data State Intelligence screenshots (data-management view)

**classification: Internal-Confidential** (screenshots of an internal company web tool
that include real internal hostnames/URLs, a real person's name in the signed-in
header, and real dataset/distribution identifiers — stricter than the DataLens set,
per the pat-evidence precedent: names/identifiers ⇒ Internal-Confidential. Tracked in
the private repo only; never ports, never publishes, per `PUBLISH-BOUNDARY.md`).

User-supplied screenshots of **Data State Intelligence (DSI)** — the data-management
view over the same estate — captured 2026-07-28. Third point of the ecosystem triangle
the console sits in: **DataLens** (job-run execution view, `internal/datalens-reference/`)
· **DSI** (dataset readiness / platform catalog / cost view) · **DryDocs** (the knowledge
graph joining job ↔ dataset ↔ application ↔ owner between them). Kept as design-pattern
shape references; per the two-track back-flow rule patterns are reproduced generically,
never copied.

| File | What it shows | Findings it feeds |
|---|---|---|
| `DSI-ui-readiness.png` | Data Flow Intelligence → Readiness Engine: status + stage KPI card rows with Apply-filter footers, dataset-distribution grid (AG-Grid idiom), icon+word status chips | DL-10 (tile→filter), DL-11 (stage taxonomy), DL-12 (status vocabulary) |
| `DSI-ui-platform.png` | Data Platform Intelligence: Backstage-style catalog of observability dashboards (Category/Pillars/Views metadata, Grafana/Datadog tool tags, bookmarks) | catalog idiom notes; O28 adjacency |
| `DSI-ui-home.png` | DSI home: question-led entry cards, module cards, Alert Center, embedded assistant | Epic R precedent note (ADR 0007 / R1) |

Groomed findings live in the continuity doc's DSI addendum:
`internal/datalens-reference/continuity.md` §"Addendum — Data State Intelligence".
