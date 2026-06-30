# schema/provisioning — multi-DB topology (Epic G1 · ADR 0002 D1)

Provisions the three-database topology from
[ADR 0002](../../../docs/decisions/0002-component-database-topology.md) on a **Neo4j
Enterprise** DBMS. Authoring + structure only — **no data load** here.

| File | Run against | Purpose |
|---|---|---|
| `01_databases.cypher` | `system` | `CREATE DATABASE drydocs`, `ddcontext`, `CREATE COMPOSITE DATABASE ddall` + aliases |
| `02_proxy_constraints.cypher` | **each** of `drydocs`, `ddcontext` | proxy-node business keys: `DataAsset.assetId` UNIQUE, `ControlMJob (folder_id, job_id)` NODE KEY |
| `smoke_ddall.cypher` | `ddall` | read-only federated query — reads both constituents, writes neither |
| `provision.ps1` | — | runner: applies 01 → 02 (×2) → smoke via `cypher-shell` |

## Run

```powershell
# local dev Enterprise (free eval license) — see provision.ps1 header for the docker line
.\provision.ps1 -Uri bolt://localhost:7687 -User neo4j -Password password
```

Idempotent (`IF NOT EXISTS` throughout). On a fresh topology the smoke returns `0 / 0`;
success is that the federated query **runs** (both aliases resolve, no write).

## Why these keys (no identity invented)

The composite joins `ddcontext` → `drydocs` by **business key** (proxy-node
pattern), never internal node id — so context records survive every `drydocs`
rebuild and re-link automatically. Keys are the **existing canonical** ones
(ADR 0001: "identity is always a business key"): `DataAsset.assetId` (the URN) and
`ControlMJob (folder_id, job_id)` (from `../constraints.cypher`). A single-property
`jobId` URN for cleaner joins would be a separate identity decision through the HITL
gate — out of scope for G1.

## Edition + rollout caveats

- **Enterprise required.** Multi-DB + composite are Enterprise-only; Community is one DB.
  The live production deploy is tracked separately as **G7** (blocked on a multi-DB-capable
  target — procurement/ops gate, not code). G1 is authored + validated on a **local**
  Enterprise instance.
- **`drydocs` is ephemeral today** (created/tested/destroyed). `ddcontext` is writable
  now (isolated). **Promotion** `ddcontext → drydocs` stays **paused** until core
  stabilizes (ADR 0002 rollout state; promotion path = Epic G5).

## Validation status

Scripts authored and self-consistent. **Live validation pending** a Neo4j Enterprise
instance (Docker not available in the authoring environment) — run `provision.ps1`
against a local Enterprise and confirm the smoke returns without error to close G1's
acceptance.
