# K7 — how a folder gets its application

Working diagram for the `seal-app-ref-edge-reshape` gate session (backlog K7).
Rulings §A–§E. Dashed boxes are **not yet ruled**. Mechanism only — no real app
codes, SEAL ids, or folder names.

```mermaid
flowchart TD
    F["Control-M FOLDER<br/>sits under one app code"] --> ROW["ONE defined row, authored at CODE level<br/>(B1 — one mechanism, one row kind)"]
    ROW --> FAN["LOADER FANS OUT to folders<br/>through the existing CONTAINS_FOLDER edge"]
    FAN --> TIER{"tier property<br/>on the row"}

    TIER -->|"TIER 1 — seal-born<br/>code created FOR one SEAL app"| T1["Fan-out COMPLETES on its own<br/>every folder under the code attributed<br/>NEW folders inherit automatically"]
    TIER -->|"TIER 2 — shared platform code<br/>e.g. the DPL launcher spine"| T2["Cannot resolve alone —<br/>fan-out SURFACES N folders<br/>for steward completion<br/>NEVER auto-picked (B2)"]
    TIER -->|"TIER 3 — dual-coded<br/>team migrating to its own code"| T3["BOTH at once: a tier-1 row for the<br/>new code + the platform code's<br/>per-folder completions<br/>DECLARED, with an explicit end state"]
    TIER -->|"no defined row exists"| FB["K2 FALLBACK — fuzzy match<br/>SEAL then FID then APP_NAME then ALIAS<br/>origin = matched-fallback<br/>always DISCLOSED, never silent (B3)"]

    T1 --> P["TARGET: the application's<br/>BatchProcessing :Port"]
    T3 --> P
    T2 --> COMP["steward completion, stored per folder<br/>PERMANENT in this domain (E2)"]
    T3 --> COMP
    COMP --> AP["TARGET: :AreaProduct"]

    FB --> R{"resolved to<br/>one app?"}
    R -->|yes| P
    R -->|no| COMP

    OV["OVERRIDE row<br/>per-folder exception to a code-level row<br/>origin = override"] -->|"wins over derived"| P

    P --> E1["EDGE: ControlMFolder — BELONGS_TO_APPLICATION → Port<br/>local domain edge, prov_maps_to null<br/>role=seal_app_ref, match_method=defined or fallback<br/>first_seen_at, source, last_seen_at"]
    AP --> E2{"same edge label?<br/>an AreaProduct<br/>is not an application"}

    E1 --> INH["JOBS INHERIT through CONTAINS_JOB<br/>no per-job application edge<br/>is ever authored (A1)"]
    E2 -.-> INH

    E1 --> W["LOADER is the only graph writer<br/>store rows never write directly<br/>(E3 — not yet confirmed)"]

    classDef open stroke-dasharray: 6 4,stroke-width:2px;
    class E2,W open;
```

## Ruled so far

| § | Ruling |
|---|--------|
| A1 | Grain is FOLDER-level; jobs inherit via `CONTAINS_JOB`; no per-job edge authored going forward |
| A2 | UI crosswalk keeps deriving through job edges, and says so, until it re-binds at build |
| B1 | ONE mechanism: code-level rows, loader fans out via `CONTAINS_FOLDER`; `tier` is a row property |
| B2 | Three tiers — seal-born (1:1), platform (1:many), dual-coded/migrating; never auto-picked |
| B3 | K2 fuzzy match DEMOTES to fallback, and is always DISCLOSED via the origin flag |
| C1 | Tier-1 target is the application's BatchProcessing `:Port` (not the app node — supernode avoidance) |
| C2 | The `:Batch` bridge (`arch_contains_batch` / `arch_contains_folder`) is RETIRED |
| D1 | Local domain edge, `prov_maps_to: ~`, label `BELONGS_TO_APPLICATION` |
| D2 | One shape everywhere — loader edge, manual tier-5 writer, migration target |
| E2 | Defined rows are graph-loadable source of record; overrides may be PERMANENT in this domain |

Tier 3 is the same lesson §G3 proposes for orchestrators: **mid-migration is a normal
state, not a conflict.** Two axes, one rule.

## Still open

1. **The `:AreaProduct` edge label.** §D signed one edge, `BELONGS_TO_APPLICATION`, but
   tier-2 completions land on an `:AreaProduct`, which is not an application. Either the
   tier-2 edge needs its own name, or `:AreaProduct` is a routing step rather than a target.
2. **Bulk authoring** — is a folder naming-convention pattern a row generator, or a
   screen-level convenience?
3. **§E1** override mechanics, **§E3** write path, **§F** migration, **§G1–G7** the mapping act.
