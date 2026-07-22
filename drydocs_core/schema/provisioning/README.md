# schema/provisioning — multi-DB topology (Epic G1 · ADR 0002 D1)

Provisions the multi-database topology from
[ADR 0002](../../../docs/decisions/0002-component-database-topology.md) — three data
databases plus one composite — on a **Neo4j Enterprise** DBMS. Authoring + structure
only — **no data load** here.

| File | Run against | Purpose |
|---|---|---|
| `01_databases.cypher` | `system` | `CREATE DATABASE drydocs`, `ddlineage`, `ddcontext`, `CREATE COMPOSITE DATABASE ddall` + aliases |
| `02_proxy_constraints.cypher` | **each** of `drydocs`, `ddlineage`, `ddcontext` | proxy-node business keys: `DataAsset.assetId` UNIQUE, `ControlMJob (folder_id, job_id)` NODE KEY |
| `smoke_drydocs_all.cypher` | `ddall` | read-only federated query — reads all three constituents, writes none |
| `provision.ps1` | — | runner: applies 01 → 02 (×3) → smoke via `cypher-shell` |

## Run

```powershell
# local dev Enterprise (free eval license) — see provision.ps1 header for the docker line
.\provision.ps1 -Uri bolt://localhost:7687 -User neo4j -Password password
```

Idempotent (`IF NOT EXISTS` throughout). On a fresh topology the smoke returns `0 / 0 / 0`;
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

**Live-validated 2026-07-07** against a local Docker Enterprise instance
(`neo4j:5.26-enterprise-ubi10`): 01 → 02 (×3) → smoke all succeeded; smoke returned
`0 / 0 / 0` on the fresh topology and `SHOW DATABASES` shows all four DryDocs
databases online. This closes G1's acceptance.

Note: nothing runs this at container startup — provisioning is a deliberate one-time
step after the DBMS is up (re-runnable safely thanks to `IF NOT EXISTS`).
