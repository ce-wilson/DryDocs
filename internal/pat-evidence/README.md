# internal/pat-evidence — PAT screenshot evidence (extract-shape references)

**classification: Internal-Confidential** (real SEAL ids, application names, people; the
`internal/` home — tracked in the private repo, excluded from any public push per
`PUBLISH-BOUNDARY.md`).

SME-supplied screenshots from the Product Agility Tool, captured 2026-07-18 during the
C5/C9 gate sessions (`config/gate-log.md`: `same-row-derived-edges`, `pat-reconcile`).
The gate *decisions* stand on the gate log alone; these are kept as **shape references
for two open source-onboarding follow-ups**, not as decision evidence.

| File | What it shows | Open follow-up it feeds |
|---|---|---|
| `pat-team_active_sources_report.png` | The PAT **team report** (the C9 loader's intended real feed): Team ID, name, LOB, **SEAL IDs (semicolon-separated)**, JIRA instance/board, team type, status, agile framework | Onboarding the real team-report extract (`config/source-registry.yaml#catalog-pat`, `team_applications` feed). NOTE: the real report delimits SEAL ids with `;` — FIXED 2026-07-19: `PatProductMappingRow.seal_ids` normalizes `;` → `,` at the row boundary (guarded by `test_pat_product_mapping.py`). |
| `pat-dat-data-mgmt.png` / `-2` / `-3` | A product page's **Mapped Applications tab**: Seal ID, App Name, LoB, App State, Investment Strategy, Date Added (product-scoped) | The product-scoped extract that would activate `catalog_has_application` (left `status: planned` at the C9 gate until this source exists). |

Four further screenshots (dev-team pages + dataproduct listing, alignment-volatility
evidence) were deliberately deleted 2026-07-19 — their substance is fully recorded in the
gate log and vocabulary notes.
