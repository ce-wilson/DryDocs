# config/overrides/ — user override lists (the M2 origin-flagged store)

Ratified at the **ui-write-surface gate** (SME-3, 2026-07-21, `config/gate-log.md`):
some source systems carry values DryDocs users know to be wrong but cannot fix —
only the source system's own privileged role can. The worked example is SEAL
contact data: the L1/L2 Operate Manager assignments drift, and only the
application owner (AO privilege) can correct them **in SEAL**.

DryDocs therefore keeps **both** values, never a silent replacement:

- the **source** value (what SEAL says today), and
- the **user override** (what the support team knows to be correct),

flagged by ORIGIN on every surface that shows them. Overrides feed a
**source-corrections report** — an artifact addressed to the application
owners so the fix lands in the source system. Overrides NEVER write the
graph (the loader stays the only graph writer) and NEVER enter attribution
precedence — whether they ever could is an explicitly open gate question
(ui-write-surface / K-family), not decided here.

## Mechanics (the file-to-table enhancement)

The committed CSV here is the source of truth; `var/mapping.db` (the derived,
rebuildable mapping-store materialization) ingests it into the
`seal_contact_override` table, which serves the `/mappings` console domain
`seal-contact-override` and the report export. Drafting an override in the
console returns the UPDATED file content as an artifact — commit it here to
persist it (git review is the review; no HITL gate is needed because nothing
touches edge meaning or the graph).

## seal-contact-overrides.csv columns

| column | required | meaning |
|---|---|---|
| `app_seal_id` | yes | the application's SEAL id |
| `role_name` | yes | canonical SEAL role name (`L1 Operate Manager`, `L2 Operate Manager`, …) |
| `seal_holder_sid` | no | the holder SID **SEAL currently shows** (captured at authoring — the side-by-side source value; empty = SEAL has nobody assigned) |
| `override_holder_sid` | yes | the corrected holder SID |
| `override_holder_name` | no | corrected holder display name |
| `rationale` | yes | why the SEAL value is wrong — becomes the report's justification column |
| `authored_by` | yes | steward persona (server-stamped in console drafts) |
| `authored_on` | no | ISO date |
| `status` | yes | `active` (outstanding correction) or `corrected-in-seal` (AO applied the fix; row kept for audit, dropped from the report) |

No real SIDs or company values may be committed here (PUBLISH-BOUNDARY.md) —
this repo's copy stays mechanism-only; real override lists live company-side.
