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

## app-code-mappings.csv — the K7 defined-mapping store (K9)

Ratified at the **seal-app-ref-edge-reshape gate** (K7, SIGNED OFF 2026-08-03,
`config/gate-log.md`): the steward-DEFINED Control-M app-code → application
mapping. This domain differs from the contact overrides above in two ruled
ways: the store **IS a graph-loadable source of record** (§E2 — no machine
feed exists to defer to), and **override rows may be PERMANENT** — the
folder-to-application relation runs through a platform code, so there is no
pending source fix to wait for and no corrected-in-source lifecycle (hence
no `status` column). Rows still never write the graph directly; the K8
loader is the only graph writer (§E3), fanning each code-level row out to
its folders via `scheduler_contains_folder` (§B1) as
`(:ControlMFolder)-[:BELONGS_TO_APPLICATION {role: seal_app_ref}]->(:Port)`.

| column | required | meaning |
|---|---|---|
| `app_code` | yes | the Control-M app code (the `:ControlMApplication` authoring key) |
| `folder_id` | no | empty = code-level row; set = a per-folder platform resolution |
| `row_kind` | yes | `seal-born` (1:1, code-level fan-out) · `platform` (shared code — the code-level row is a DECLARATION, resolved per folder) · `dual-coded` (migrating — both attributions simultaneously correct). Renamed from `tier` at K18 to stop colliding with the K2 match-precedence tiers |
| `app_id` | yes | the target application — required on EVERY row (K18). On a platform code-level DECLARATION it is the platform's OWN SEAL (a fact about the code, never fanned out — the loader suppresses fan-out by row_kind, not by app_id emptiness); on a per-folder resolution it is the consuming application |
| `declared_end_state` | dual-coded only | REQUIRED on dual-coded rows (§B2) — the explicit end state that keeps a stalled migration visible |
| `origin` | yes | `defined` · `override` · `manual-pin`. `matched-fallback` is refused here — it is derived by the K2 fallback at load and disclosed on the edge, never authored |
| `rationale` | override/pin/declaration | required when origin ≠ `defined` (permanence makes the why load-bearing) and on every platform code-level DECLARATION (K18 — the shared-code claim needs its why) |
| `authored_by` | yes | steward persona (server-stamped in console drafts) |
| `authored_on` | no | ISO date |

Folder → application is **1:1** (OWNER-NOT-USER): a duplicate row for the
same (app_code, folder_id, origin) is refused at materialization. Mechanism
only in this repo — real code rows live company-side.
