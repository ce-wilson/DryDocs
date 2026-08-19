# Technical Design — Control-M Ingestion (the `ingest-controlm` M3 chain)

<!-- anchor: front-matter -->
**Status:** DESCRIPTIVE — **Rev 5, 2026-07-23** (folder property diet: naming-convention
decode off the node, `app_code` kept as the join key — SME ruling 2026-07-23; on top of
Rev 4's two-phase loader, same day; reflects commit `c1c3a0a`) ·
**Classification:** Internal (mirrors `config/taxonomy/controlm.yaml`; uses only the
committed sample fixtures — no real SIDs/servers) ·
**Audience:** production-support / development-support engineers reading the graph. ·
**Companion:** `docs/controlm-staging-ingestion-flow.md` (§3a is the load-order contract).

Worked example throughout:

```bash
poetry run drydocs ingest-controlm --use-oracle --folder 'PRARAG-HLDM-70011-PEX%'
```

> **What changed in Rev 5 (2026-07-23) — folder property diet (SME ruling).** The
> folder-name convention (pos1=env, pos2=lob, pos3–5=app_code, pos6=folder_type) is the
> internal Control-M app-code *definition* — expanding it onto nodes confused users:
> `f.lob='Retail'` collided with the org-taxonomy LOB (same word, different taxonomy),
> and env truth is the `data_center` prefix on `:ControlMServer`, not folder-name pos 1.
> The loader now forwards **`app_code` only** (the join key for the app-code →
> BusinessApplication defined mapping — the open seal-app-ref v2 gate);
> `environment*/lob*/folder_type*` are retired from the node. The decode lives once in
> `folder_name.py`. No migration — pre-diet graphs are wiped and rebuilt from bootstrap.
> Ruling recorded in `config/gate-log.md` (2026-07-23 folder property diet).
>
> **What changed in Rev 4 (2026-07-23) — ported from the company repo.** Cross-folder
> dependency edges were dropping when folders loaded one at a time: the `WAS_INFORMED_BY`
> edge links jobs across *different* folders, so a per-folder scoped ingest MATCHed a
> second endpoint that wasn't loaded yet and the edge silently never got created. The fix
> splits the ingest into two passes — `--phase nodes` (labels/nodes + intra-folder edges;
> self-contained rows, safe to run scoped, folder by folder) and `--phase relationships`
> (the deferred `WAS_INFORMED_BY` pass ONLY: run once, UNSCOPED, after all nodes exist);
> `--phase all` (default) preserves prior behavior. In the same change the dependency SQL
> + cypher emit **DIRECT edges only**, keyed by ctlm_id composites (`folder_id.job_id`):
> the recursive CTE is gone — transitive reach is a graph traversal, not a stored closure
> — and `recursion_level` / `dependency_path` are no longer stored on the edge.
> `ControlMDependencyRow` slims to `(in_table_job_id, out_condition, out_table_job_id)`;
> `m3-verify` now checks `via_condition` on each edge.
>
> **What changed in Rev 3 (2026-07-08).** Restructured to the canonical TDD outline
> (`docs/design/templates/tdd.outline.yaml`, Epic L): added Purpose & scope, Definitions,
> Classification & security, QA & tests, and a **requirements traceability matrix**, and
> tagged every section with a stable `<!-- anchor -->`. Documentation-only — no code change.
>
> **What changed in Rev 2**
> 1. The chain order is now **contractual** (a test enforces it) and framed as the
>    standard Neo4j import discipline — see §3b.
> 2. The **folder pass now derives two grouping labels**, not one: `DATA_CENTER →
>    :ControlMServer` *and* header-row `APPLICATION → :ControlMApplication` (+ `CONTAINS_FOLDER`).
>    See §2, §4 Stage 1, §6.

> **Read-me-first correction (unchanged).** The `--folder` value is **not** interpolated
> into SQL. Every `.sql` file is read verbatim and executed with `:folder_filter` as a
> **bind variable** (`cursor.execute(query, binds)` — `oracle_adapter.py:61`). Your `%` is
> an ordinary `LIKE` wildcard and, being bound, injection-safe.

---

<!-- anchor: purpose-scope -->
## Purpose & scope

**Purpose.** Document the `ingest-controlm` chain (the "M3" load) end to end — how the
Control-M scheduler definitions in the `psgmgr` replica become the DryDocs knowledge graph
— so a support engineer can read, trust, and extend the loader.

**In scope.** The five-pass load (constraints → folders → jobs → conditions → derived
dependencies), the source tables + filters, the field→node/edge mapping, the enforced
load-order contract, and the taxonomy→ontology binding each edge traces to.

**Out of scope.** SEAL application attribution (`WAS_ASSOCIATED_WITH {role: seal_app_ref}`)
— separate, tracked as **K2** (now **live**: gate `seal-attribution-match-policy` confirmed
2026-07-14, loader `drydocs load-seal-attribution`), running only after this chain;
vector/embedding passes; and the live multi-DB deploy (**G7**). These are named where they
touch the chain but specified elsewhere.

<!-- anchor: context-frame -->
## 1. Where this sits — the four-layer frame

DryDocs is built in four layers (`CLAUDE.md` §1). Control-M ingestion walks the first three,
in order:

| Layer | This chain's contribution | Artifact |
|-------|---------------------------|----------|
| **1. Taxonomy** (what *category*) | `ControlMApplication`, `ControlMServer > ControlMFolder > ControlMJob`; `Condition` entity | `config/taxonomy/controlm.yaml` |
| **2. Ontology** (what edges *mean*) | PROV binding per edge, HITL-confirmed | `config/taxonomy-ontology-map/` (fragment dir; S5) |
| **3. Knowledge graph** (both) | the populated Neo4j nodes + edges | Neo4j |
| **4. Context graph** (what matters *now*) | — (future) | — |

**The rule the chain obeys:** import as taxonomy first (pure classification), apply the
confirmed ontology rule, *then* load. Every edge below traces to a confirmed row in the
taxonomy→ontology map.

---

<!-- anchor: definitions -->
## Definitions, acronyms & references

| Term | Meaning |
|---|---|
| `psgmgr` | the read-only Control-M metadata replica (grantee `CM_RO_USER`) DryDocs reads |
| `CM_DEF_VTAB` / `CM_DEF_VJOB` | folder (schedule) table / job-definition table on the replica |
| `CM_DEF_LNKI_P_VW` / `CM_DEF_LNKO_P_VW` | IN-condition (consumed) / OUT-condition (emitted) views |
| header row | `CM_DEF_VJOB` where `JOB_ID = 1` — the SMART-table header carrying folder-grain `APPLICATION` |
| `:ControlMApplication` | Control-M `APPLICATION` grouping node — **not** the SEAL business app |
| SEAL `:Application` | the business application (SEALID); a different concept, attributed via K2 |
| PROV | W3C PROV-O; label duals (`:Collection`/`:Activity`/`:Entity`) encode PROV type |
| `m3-verify` | the post-load graph-invariant check (`drydocs … m3-verify`) |

**References.** Companion `docs/controlm-staging-ingestion-flow.md` (§3a — the load-order
contract); `config/taxonomy/controlm.yaml` (taxonomy); `config/taxonomy-ontology-map/` (confirmed bindings — the fragment directory;
the former single YAML was split at S5, 2026-08-06); `CLAUDE.md` §1 (four-layer model); ADR 0003 (`ControlMFolder` naming).

<!-- anchor: detailed-design -->
## 2. Source system — the `psgmgr` CM_ replica

Production reads a **read-only replica** (`psgmgr`, grantee `CM_RO_USER`). The chain touches
four objects — and, new in Rev 2, reads `CM_DEF_VJOB` a *second* way (the folder header row):

| # | Concept | Vendor poster (6.4.01) | Company replica (`psgmgr`) | Grain / use |
|---|---------|------------------------|----------------------------|-------------|
| 1 | Folder / schedule table | `CMS_SCHEDT` | **`CM_DEF_VTAB`** | one row / folder |
| 2 | Job definition | `CMS_JOBDEF` | **`CM_DEF_VJOB`** | one row / (folder, job, version) |
| 2b | **Folder header row** | (SMART table hdr) | **`CM_DEF_VJOB` where `JOB_ID = 1`** | folder-grain `APPLICATION` — LEFT-JOINed into the folder extract |
| 3 | IN-conditions (consumed) | `CMS_CON_J` (in) | **`CM_DEF_LNKI_P_VW`** | one row / (job, condition) |
| 4 | OUT-conditions (emitted) | `CMS_CON_J` (out) | **`CM_DEF_LNKO_P_VW`** | one row / (job, condition) |

**Two filters apply almost everywhere:**

- `IS_CURRENT_VERSION = 'Y'` — **string** literal (`VARCHAR2(1)`; domain `'Y'` live-verified
  2026-07-15 via the finalized company ingestion TDD — was assumed `'1'`, D4). On jobs, conditions, and
  the header-row join. **Not** on folders (`CM_DEF_VTAB` has no version column).
- `USER_DAILY IS NOT NULL` — the only "actively scheduled" gate on a folder.

**Join keys**

- Job ↔ folder: `CM_DEF_VJOB.TABLE_ID = CM_DEF_VTAB.TABLE_ID`
- **Header row ↔ folder (new):** `CM_DEF_VJOB.(TABLE_ID, JOB_ID=1, IS_CURRENT_VERSION='Y')` — LEFT JOIN
- Condition ↔ job: `CM_DEF_LNK{I,O}_P_VW.(TABLE_ID, JOB_ID, VERSION_SERIAL)`
- **Dependency edge is derived, not stored:** B depends on A when `LNKI(B).CONDITION = LNKO(A).CONDITION`.

**Three naming traps** (all load-bearing):

- Authoritative folder **name** = `CM_DEF_VTAB.SCHED_TABLE`; `CM_DEF_VJOB.PARENT_TABLE` carries
  it denormalized on the job — property only, never the FK.
- `CM_DEF_VJOB.APPLICATION` is the **Control-M app code**, *not* the SEAL business app. It does
  **not** reconcile to `Application.seal_id`. It *does* now become a `:ControlMApplication`
  grouping node (a different concept from SEAL `:Application`).
- The header-row `APPLICATION` (a *Control-M* grouping) is distinct again from the 3-char
  appcode parsed out of the folder name (positions 3–5). Keep the three apart.

---

<!-- anchor: design-summary -->
## 3. ER diagram & the order the tables are used

### 3a. Source ER (physical, incl. the header-row LEFT JOIN)

```
        CM_DEF_VTAB  (folder)                    PK: TABLE_ID
        │  SCHED_TABLE (name), DATA_CENTER,      filter: USER_DAILY IS NOT NULL
        │  USER_DAILY, TABLE_STATUS
        │
        │  LEFT JOIN CM_DEF_VJOB H  ON H.TABLE_ID=TABLE_ID AND H.JOB_ID=1
        │            (SMART-table header row → H.APPLICATION)   IS_CURRENT_VERSION='Y'
        │
        │  TABLE_ID (1)──────────────(many)
        ▼
        CM_DEF_VJOB  (job)                        PK: (TABLE_ID, JOB_ID, VERSION_SERIAL)
        │  JOB_NAME, APPLICATION, OWNER,          filter: IS_CURRENT_VERSION='Y'
        │  AUTHOR, NODE_ID, CMD_LINE, CYCLIC
        │
   ┌────┴────┐  (TABLE_ID, JOB_ID, VERSION_SERIAL)
   ▼         ▼
 LNKI_P_VW  LNKO_P_VW                             filter: IS_CURRENT_VERSION='Y'
 (IN cond)  (OUT cond, SIGN +/-)

     └──── derived: LNKI.CONDITION = LNKO.CONDITION (successor consumes predecessor's emit) ────┘
```

### 3b. Load order — now a **contract** (`test_ingest_chain_order_is_enforced`)

The rule is standard Neo4j import discipline: **constraints first; all nodes before any
relationships; relationship-only passes `MATCH` their endpoints (never `MERGE` them), so a
missing endpoint surfaces instead of creating a ghost node.**

| # | Pass | Nodes MERGEd | Relationships written | Endpoint rule |
|---|------|--------------|-----------------------|---------------|
| **0** | `constraints.cypher` (bootstrap, once) | — | — | every key below is constraint-backed |
| **1** | **folders** | `:ControlMFolder` + **two field-derived grouping labels** — `DATA_CENTER → :ControlMServer`, header `APPLICATION → :ControlMApplication` | `SCHEDULED_ON`, `CONTAINS_FOLDER` | self-contained — every endpoint created here |
| **2** | **jobs** | `:ControlMJob` | `CONTAINS_JOB` | `MATCH` folder (from pass 1); job dropped if folder absent |
| **3** | **conditions in / out** | `:Condition` (shared `(folder_id, name)`) | `REQUIRES_IN_CONDITION`, `EMITS_OUT_CONDITION` | `MATCH` job `(folder_id, job_id)` |
| **4** | **dependencies (DEFERRED `--phase relationships`, edge-only)** | *none* | `WAS_INFORMED_BY` | `MATCH` **both** endpoint jobs — pure edge pass, never creates nodes; **run once, UNSCOPED, after all nodes exist** |
| later | SEAL attribution (K2, **live 2026-07-14**) | *none* | `WAS_ASSOCIATED_WITH {role: seal_app_ref}` | only after jobs **and** `:Application` exist |

Passes 1–3 are the `--phase nodes` set (self-contained rows — safe to repeat per folder);
pass 4 is the `--phase relationships` set (Rev 4). `--phase all` (default) runs both;
`--skip-part2` still stops after folders + jobs. Both grouping nodes exist **before** the
jobs pass, keeping pass 2 a pure child pass. `m3-verify` gained a
no-orphan-`:ControlMApplication` check. (Contract detailed in
`docs/controlm-staging-ingestion-flow.md` §3a.)

### 3c. Target graph model (Rev 2)

```
 (:ControlMApplication:Collection {name})          ← NEW: from header-row APPLICATION
        │ CONTAINS_FOLDER                             (prov:hadMember)
        ▼
 (:ControlMServer:Platform {name})
        ▲ SCHEDULED_ON {since}                        (no PROV — infra placement)
        │
 (:ControlMFolder:Collection {folder_id, sched_table, app_code, active})   ← decode diet, Rev 5
        │ CONTAINS_JOB                                (prov:hadMember)
        ▼
 (:ControlMJob:Activity {folder_id, job_id, job_name, application, owner, author, node_id, cmd_line, …})
        │  REQUIRES_IN_CONDITION {odate,and_or,parentheses,isn}   (prov:used)
        │  EMITS_OUT_CONDITION   {odate,sign,isn}                 (prov:generated)
        ▼
 (:Condition:Entity {folder_id, name, version_serial})

 (:ControlMJob) ──WAS_INFORMED_BY {via_condition, derived:true}──▶ (:ControlMJob)
                                     (prov:wasInformedBy; direct pairs only — Rev 4)
 every node ──WAS_GENERATED_BY {source:'BMC'}──▶ (:JobRun {run_id, kind:'load'})   (prov:wasGeneratedBy)
```

---

<!-- anchor: design-data-mapping -->
## 4. Field → Label / Node / Edge mapping

### Stage 1 — folders → `:ControlMFolder:Collection` + `:ControlMServer:Platform` + **`:ControlMApplication:Collection`**

Source `CM_DEF_VTAB` **LEFT JOIN** `CM_DEF_VJOB` header row. `SCHED_TABLE` is pre-parsed by
`folder_name.py` before the batch reaches Cypher.

| SQL column (`controlm_folders.sql`) | Node property | Notes |
|---|---|---|
| `T.TABLE_ID` | `ControlMFolder.folder_id` | **node key** (UNIQUE) |
| `T.SCHED_TABLE` | `.sched_table` | authoritative folder name |
| `T.DATA_CENTER` | `ControlMServer.name` | server key (P12/P14/P32/P33) |
| **`H.APPLICATION`** | **`ControlMApplication.name`** | **NEW** — from header row (`JOB_ID=1`); may be NULL |
| `T.USER_DAILY` | `.user_daily`, `.active` | `active = USER_DAILY not null/empty` |
| `T.TABLE_STATUS/TABLE_TYPE/INSTANCE_NAME` | `.table_status`,`.table_type`,`.instance_name` | |
| `T.LAST_UPDATED/LAST_UPDATED_USER/CAPTURE_DATE` | `.last_updated`(dt),`.last_updated_user`,`.capture_date`(dt) | |
| *(parsed `SCHED_TABLE`)* | `.app_code` **only** | via `folder_name.py` (§7b); the rest of the decode stays OFF the node — Rev 5 property diet |

Edges from this pass:
- `(:ControlMFolder)-[:SCHEDULED_ON {since}]->(:ControlMServer)`
- **`(:ControlMApplication)-[:CONTAINS_FOLDER]->(:ControlMFolder)`** — **only when** `row.application`
  is non-null/non-empty (`WHERE` guard in the cypher; the null-key-MERGE safeguard). Header-less
  folders load normally without an application node.

### Stage 2 — jobs → `:ControlMJob:Activity`

Source `CM_DEF_VJOB ⋈ CM_DEF_VTAB`. Node key **`(folder_id, job_id)`** — `JOB_ID` is
folder-scoped. `VERSION_SERIAL` is an audit property, not identity.

| SQL column | → property |
|---|---|
| `TABLE_ID`, `JOB_ID` | `.folder_id`, `.job_id` (node key; folder MATCHed) |
| `VERSION_SERIAL` | `.version_serial` (audit only) |
| `JOB_NAME`, `APPLICATION`, `GROUP_NAME`, `TASK_TYPE` | `.job_name`, `.application` (**≠ SEAL**), `.group_name`, `.task_type` |
| `OWNER`, `AUTHOR`, `NODE_ID`, `CMD_LINE` | `.owner` (run-as FID), `.author` (CtM team FID), `.node_id`, `.cmd_line` |
| `CYCLIC/CYCLIC_TYPE`, `PRIORITY`, `CRITICAL`, `ACTIVE_FROM/TILL`, `END_FOLDER` | corresponding props |
| `IS_CURRENT_VERSION`, `VERSION_OPCODE/TIMESTAMP/USER`, `CAPTURE_DATE` | version/audit; `.active = IS_CURRENT_VERSION='Y'` |

Edge: `(:ControlMFolder)-[:CONTAINS_JOB]->(:ControlMJob)`.

### Stages 3 & 4 — conditions → `:Condition:Entity`

Same `:Condition` node shared by IN and OUT when `(folder_id, name)` matches — the seam the
dependency walk exploits. Node key **`(folder_id, name)`**.

| Stage | Source view | Edge (job → condition) |
|---|---|---|
| 3 IN | `CM_DEF_LNKI_P_VW` | `[:REQUIRES_IN_CONDITION {odate, and_or, parentheses, order_, isn}]` |
| 4 OUT | `CM_DEF_LNKO_P_VW` | `[:EMITS_OUT_CONDITION {odate, sign(+/-), isn}]` |

### Stage 4 (pass 4) — derived dependencies → `:WAS_INFORMED_BY` (edge-only, deferred)

A **pure edge pass**: MERGEs no nodes. Rows are pure ctlm_id composites
(`in_table_job_id`, `out_condition`, `out_table_job_id`); the cypher splits each composite
on `'.'` to recover the `(folder_id, job_id)` NODE KEY and `MATCH`es both endpoint jobs.
Direction **successor → predecessor**. **Direct pairs only (Rev 4)** — the recursive CTE,
`recursion_level`, and `dependency_path` are gone; transitive reach is a graph traversal.
Edge key `via_condition` de-dupes parallel condition seams. Runs in the deferred
`--phase relationships` pass: once, unscoped, after all nodes exist.

### Identity & provenance

| Node | Key constraint (`constraints.cypher`) |
|---|---|
| **`:ControlMApplication`** | **`name` UNIQUE** *(new — `controlmapplication_name`; EXPECTED_CONSTRAINTS 37→38)* |
| `:ControlMServer` | `name` UNIQUE |
| `:ControlMFolder` | `folder_id` UNIQUE |
| `:ControlMJob` | `(folder_id, job_id)` NODE KEY |
| `:Condition` | `(folder_id, name)` NODE KEY |

Every touched node also gets `-[:WAS_GENERATED_BY {source:'BMC'}]->(:JobRun)` + `last_seen_at`
/ `last_run_id`. *(The provenance-diet plan — `docs/restructure/06-provenance-source-audit-fields.md`
— proposes to demote this blanket edge.)*

---

## 5. Taxonomy (layer 1)

`config/taxonomy/controlm.yaml` — **pure classification, no meaning edges**
(`classification_only: true`; `authority: bmc-baseline`; `classification: Internal`).
Hierarchy `ControlMServer > ControlMFolder > ControlMJob`; `Condition` keyed `(folder_id, name)`.
The `controlm-q1q3-phase1` gate (2026-07-07) added **`ControlMApplication`** as a folder
grouping (Control-M `APPLICATION`, *not* the SEAL business app).

Example folders in the sample: **161015** `PRARAG-HLDM-70011-PEX-TRUST-DLY` (P12) & **161016**
`PRARAG-HLDM-70011-PEX-TRUST-CYC` (P14).

---

<!-- anchor: hitl-gate -->
## 6. Ontology (layer 2) — HITL gate & what's not yet live

`config/taxonomy-ontology-map/` (the fragment directory — one file per domain since the S5 split) is the HITL-confirmed bridge. Lifecycle
`proposed → confirmed → applied` — a taxonomy never becomes edges until confirmed.

| Edge (Neo4j) | From → To (PROV) | Decision-matrix row | PROV term | Status |
|---|---|---|---|---|
| **`CONTAINS_FOLDER`** | **Collection → Collection** | Collection → any | `prov:hadMember` | **applied (Rev 2)** |
| `CONTAINS_JOB` | Collection → Activity | Collection → any | `prov:hadMember` | applied |
| `SCHEDULED_ON` | Collection → Platform | infra (no PROV) | — | confirmed |
| `REQUIRES_IN_CONDITION` | Activity → Entity | Activity → Entity | `prov:used` | confirmed |
| `EMITS_OUT_CONDITION` | Activity → Entity | Activity → Entity | `prov:generated` | confirmed |
| `WAS_INFORMED_BY` | Activity → Activity | Activity → Activity | `prov:wasInformedBy` | confirmed |
| `WAS_GENERATED_BY` | Entity/Activity → JobRun | — | `prov:wasGeneratedBy` | applied |

`CONTAINS_FOLDER` reuses vocabulary `m3_contains_folder` (flipped **planned → active** this
gate); the loader that lands it is the **folder pass** (`controlm_folders.cypher`), not jobs.

**Label duals encode PROV type:** `:ControlMApplication:Collection`, `:ControlMFolder:Collection`,
`:ControlMJob:Activity`, `:Condition:Entity`, `:JobRun` (Activity). `ControlMServer` is a local
**Platform**, deliberately *not* a `prov:Agent` (so `SCHEDULED_ON` carries no PROV term). Anchor
terms seeded by `drydocs_core/schema/ontology.cypher`; the `m3_contains_folder` supplement in
`ontology_supplement.cypher`.

*Since gone live:* `WAS_ASSOCIATED_WITH` job→SEAL app (K2 — `confirmed` at gate
`seal-attribution-match-policy`, 2026-07-14; loader `load-seal-attribution` active; the edge
*shape* re-opens at the K4 `:Application` reclass gate). *Not yet live:* `OBSERVES` job-run
SOSA observation (`proposed`, gate not run).

---

## 7. Worked example — `--folder 'PRARAG-HLDM-70011-PEX%'`

### 7a. What the pattern matches
`SCHED_TABLE LIKE 'PRARAG-HLDM-70011-PEX%'` is a **prefix** match → selects **both** 70011
folders: `161015` (…-DLY, P12) and `161016` (…-CYC, P14). It does **not** match `161014`
(…-**70002**-…). Drop the `%` for a single exact folder.

### 7b. Folder-name parse (app_code join key; decode stays off the node)
`folder_name.py` decodes `PRARAG-HLDM-70011-PEX-TRUST-DLY` from its first segment `PRARAG`:

| Position | Char | Meaning |
|---|---|---|
| 1 | `P` | environment = **Production** |
| 2 | `R` | LOB = **Retail** |
| 3–5 | `ARA` | app_code = **ARA** |
| 6 | `G` | folder_type = **Group Table / Smart folder** |

**Only `app_code` lands on the node** (Rev 5, SME ruling 2026-07-23): the convention is the
internal Control-M app-code *definition*, and expanding it onto nodes confused users —
`f.lob='Retail'` collided with the org-taxonomy LOB, and env truth is the `data_center`
prefix on `:ControlMServer`, not folder-name pos 1. `app_code` stays as the join key for
the app-code → BusinessApplication defined mapping (the open seal-app-ref v2 gate).

**Trap:** folder *type* comes from prefix position 6 (`G`), **not** the `DLY`/`CYC` suffix — so
both example folders parse to `folder_type = Smart folder` (parser-level; not a node
property). (This parsed `app_code = ARA` is a *third*, separate thing from the header-row
`:ControlMApplication` in §7d.)

### 7c. The five SQL steps (one shared bind dict)

```python
binds = {"folder_filter": "PRARAG-HLDM-70011-PEX%",
         "run_as": None, "developer_sid": None, "row_cap": None}
```

**Step 1 — folders (Rev 2: LEFT JOIN the header row for APPLICATION)**
```sql
SELECT T.TABLE_ID AS folder_id, T.SCHED_TABLE AS sched_table, T.DATA_CENTER AS data_center,
       H.APPLICATION AS application, T.USER_DAILY, …
FROM   psgmgr.CM_DEF_VTAB T
LEFT JOIN psgmgr.CM_DEF_VJOB H
       ON  H.TABLE_ID = T.TABLE_ID
       AND H.JOB_ID   = 1                 -- SMART-Table header row
       AND H.IS_CURRENT_VERSION = 'Y'
WHERE  T.USER_DAILY IS NOT NULL
  AND  T.SCHED_TABLE LIKE :folder_filter;  -- 161015, 161016
```

**Step 2 — jobs**, **Step 3 — IN-conditions**, **Step 4 — OUT-conditions**: each joins
`CM_DEF_VTAB` and filters `SCHED_TABLE LIKE :folder_filter`. **Step 5 — direct
dependencies (Rev 4):** one IN=OUT condition join, no recursion; the scope binds filter
the SUCCESSOR side only, and the predecessor side is always unscoped — which is exactly
why its loader belongs to the deferred `--phase relationships` pass (a scoped Pass-1-style
run would MATCH-miss predecessors in folders not yet loaded).

### 7d. What lands in the graph (from the sample)
- **2 folders** (`161015`,`161016`) → `SCHEDULED_ON` P12, P14; both carry `app_code=ARA`
  (the env/lob/folder_type decode stays off the node — Rev 5 property diet).
- **`:ControlMApplication` (Rev 2):** in `--use-oracle` mode, each folder's header row
  (`JOB_ID=1`) supplies `APPLICATION`; where present, a `:ControlMApplication {name}` node is
  merged and `CONTAINS_FOLDER` links it to the folder. *(In CSV sample mode without header
  rows, `application` is NULL → the `WHERE` guard skips the app node — folders still load.)*
- **8 jobs** (5 in 161015 + 3 in 161016), each `CONTAINS_JOB` from its folder.
- **`:Condition` nodes** for the 5 (DLY) + 3 (CYC) names, wired by `REQUIRES_IN_CONDITION` /
  `EMITS_OUT_CONDITION` (shared node where names match).
- **`WAS_INFORMED_BY`** edges among ARA jobs whose IN-condition = another's OUT-condition
  (e.g. `…_PLCT → …_PREPROC → …_FW`).
- Every node gets one `WAS_GENERATED_BY` edge to this run's `:JobRun`.

### 7e. Execution path (code)
```
cli.ingest_controlm(use_oracle=True, folder='PRARAG-HLDM-70011-PEX%', phase='nodes')
  → validate phase in (nodes | relationships | all)      # exit 2 on a bad value
  → _gate_source("controlm-psgmgr")                     # D3 confirmed-gate
  → scope = _scope_binds(folder, None, None, None)
  → node_stages = [folders, jobs, cond_in, cond_out]     # Pass 1 — safe to scope
    rel_stages  = [deps]                                 # deferred — once, unscoped
    stages = node_stages | rel_stages | both, by phase   # order is the contract
  → for stage in stages:
        sql     = (SQL_DIR / stage.sql).read_text()      # static file, verbatim
        adapter = OracleAdapter(query=sql, bind_params=scope)
        cursor.execute(sql, scope)                        # ← BIND, not string-format
        rows → Loader.load() → UNWIND $batch … MERGE      # the .cypher for that stage

# then, after every folder scope has run its nodes pass:
cli.ingest_controlm(use_oracle=True, phase='relationships')   # once, no --folder
```

---

<!-- anchor: classification-security -->
## 8. Classification & security

**Classification: Internal** (`config/classification.yaml`; mirrors
`config/taxonomy/controlm.yaml`). This doc uses only the committed sample fixtures — no real
SIDs, server names, or schema values — so it is publishable under `PUBLISH-BOUNDARY.md`;
real values live in `internal/`.

**Injection-safety.** The `--folder` value is never string-interpolated into SQL. Every
`.sql` file is read verbatim and executed with `:folder_filter` as a **bind variable**
(`cursor.execute(query, binds)`, `oracle_adapter.py:61`); `%` is an ordinary bound `LIKE`
wildcard. The source is a **read-only** replica (`psgmgr`, grantee `CM_RO_USER`) — the chain
has no write path back to Control-M.

<!-- anchor: qa-tests -->
## 9. QA & tests

| What it proves | Test / verify |
|---|---|
| Load order is contractual (constraints → folders → jobs → conditions → deps) | `test_ingest_chain_order_is_enforced` |
| No orphan `:ControlMApplication` (every app node reaches a folder) | `m3-verify` no-orphan check |
| `SCHEDULED_ON` written (not the retired `RUNS_ON`); every folder placed on a server | `m3-verify` |
| Constraints present (37 → **38** with `controlmapplication_name`) | `EXPECTED_CONSTRAINTS`, bootstrap |
| Dependency pass creates no ghost nodes (MATCH both endpoints) | `m3-verify` dependency check |
| Every edge traces to a confirmed taxonomy→ontology row | `test_schema.py` drift guard |

`m1/m3-verify` require a live Neo4j (+ APOC); the unit and contract tests run offline.

<!-- anchor: traceability-matrix -->
## 10. Requirements traceability matrix

The ingestion-chain requirements this design satisfies, each traced to the design section
that realizes it and the test that proves it. (Reverse traceability for a DESCRIPTIVE doc:
ids are `FR/NFR-CMI-*`, scoped to this chain; the SEAL row is spec-level, gated as K2.)

| Requirement | Description | Design section | Component / module | Test / verify | Status |
|---|---|---|---|---|---|
| FR-CMI-001 | Read Control-M defs from the read-only `psgmgr` replica via bound SQL | detailed-design | `adapters/oracle_adapter.py`, `controlm_*.sql` | injection-safety note (`oracle_adapter.py:61`) | done |
| FR-CMI-002 | Enforce the load order (constraints → folders → jobs → conditions → deps) | design-summary | `cli.ingest_controlm`, loaders | `test_ingest_chain_order_is_enforced` | done |
| FR-CMI-003 | Folder pass derives two grouping nodes: `:ControlMServer` + `:ControlMApplication` | design-data-mapping | `controlm_folders.cypher`, `folder_name.py` | `m3-verify` no-orphan-`:ControlMApplication` | done |
| FR-CMI-004 | Job identity is folder-scoped `(folder_id, job_id)`; child pass MATCHes its folder | design-data-mapping | `controlm_jobs.cypher`, `constraints.cypher` | `m3-verify`; NODE KEY constraint | done |
| FR-CMI-005 | Derive job→job `WAS_INFORMED_BY` from the IN=OUT condition seam, edge-only | design-data-mapping | `controlm_dependencies_derived.cypher` | `m3-verify` `via_condition` check | done |
| FR-CMI-006 | Every edge traces to a HITL-confirmed taxonomy→ontology binding | hitl-gate | `config/taxonomy-ontology-map/`, `gate-log.md` | `test_schema.py` drift guard | done |
| NFR-CMI-001 | No real SIDs/servers committed; Internal classification; SQL injection-safe | classification-security | `config/classification.yaml`, `oracle_adapter.py` | `test_classification.py` | done |
| FR-CMI-007 | SEAL attribution runs only after jobs + `:Application` exist, gate-confirmed | hitl-gate | K2 loader (`seal_attribution.cypher`, `load-seal-attribution`) | gate `seal-attribution-match-policy` (2026-07-14); `graph-tests/seal-attribution-coverage.yaml` | done |
| FR-CMI-008 | Cross-folder dependency edges load in a deferred, unscoped `--phase relationships` pass (direct pairs only; ctlm_id-keyed) | design-summary | `cli.ingest_controlm --phase`, `controlm_dependencies_recursive.sql` | `test_dependencies_sql_is_direct_only`, `test_dependencies_match_on_the_composite_node_key` | done |

<!-- anchor: appendices -->
## Appendix — sticky-note gotchas

1. Load order is **contractual** (`test_ingest_chain_order_is_enforced`): constraints → folders
   → jobs → conditions → **deps (edge-only)** → K2 (gated).
2. Folder pass now makes **two** grouping nodes: `:ControlMServer` (DATA_CENTER) and
   `:ControlMApplication` (header-row APPLICATION, `JOB_ID=1`, LEFT JOIN + `WHERE` guard).
3. Three different "applications": header-row `:ControlMApplication` ≠ SEAL `:Application` ≠
   folder-name `app_code`.
4. `IS_CURRENT_VERSION = 'Y'` is a **string** (`VARCHAR2(1)`); folders use `USER_DAILY IS NOT NULL`.
5. Folder name = `SCHED_TABLE` (truth) vs `PARENT_TABLE` (denormalized on job).
6. `JOB_ID` is **folder-scoped** → job identity is `(folder_id, job_id)`.
7. Folder *type* = prefix position 6 (`G`), not the `DLY`/`CYC` suffix.
8. `--folder` is a **bind**, prefix `LIKE`; `%` matches DLY *and* CYC of one series.
9. Dependencies pass **creates no nodes** — MATCHes both jobs; a missing endpoint surfaces, no ghost node.
10. **Two-phase contract (Rev 4):** `--phase nodes` per folder as needed; `--phase relationships`
    once, UNSCOPED, after all nodes — a scoped dependency run silently drops cross-folder edges.
    Direct pairs only; transitive reach is a traversal, not a stored closure.
