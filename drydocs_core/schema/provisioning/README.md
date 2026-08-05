# schema/provisioning — multi-DB topology (Epic G1 · ADR 0002 D1)

Provisions the multi-database topology from
[ADR 0002](../../../docs/decisions/0002-component-database-topology.md) — three estate
databases, the schema meta-graph, and one composite — on a **Neo4j Enterprise** DBMS.
Authoring + structure only — **no data load** here.

| File | Run against | Purpose |
|---|---|---|
| `01_databases.cypher` | `system` | `CREATE DATABASE drydocs`, `ddlineage`, `ddcontext`, `ddschema`, `CREATE COMPOSITE DATABASE ddall` + aliases |

> **`ddlineage` is provisioned but not live** (G30 ruling, 2026-07-26 — see ADR 0002
> "Residency clarification"). Curated lineage writes land in `drydocs` per ADR 0002 D1/D2;
> nothing writes `ddlineage` today and no query spec reads it. It stays created and
> composite-aliased so the decision stays cheap to revisit — it is empty, so moving
> lineage into it later is a design change, not a data migration.

| `02_proxy_constraints.cypher` | **each** of `drydocs`, `ddlineage`, `ddcontext` | proxy-node business keys: `DataAsset.assetId` UNIQUE, `ControlMJob (folder_id, job_id)` NODE KEY |
| `smoke_drydocs_all.cypher` | `ddall` | read-only federated query — reads all three constituents, writes none |

> **`ddschema` is in the topology but in neither the proxy-constraint pass nor `ddall`**
> (G51, 2026-08-03). It holds the schema meta-graph written by `drydocs
> bootstrap-schema-graph`, where exemplar nodes carry a real label beside `:SchemaMeta`.
> Two consequences, both deliberate: the `drydocs` NODE KEYs would reject those exemplars,
> so its one constraint (`schemameta_name`) lives in `schema_graph.cypher` rather than
> here; and it is not a `ddall` constituent, because it describes the schema, not the
> estate — a federated support query would present labels as data.
| `provision.ps1` | — | runner: applies 01 → 02 (×3) → smoke via `cypher-shell` |

## Run

```powershell
# local dev Enterprise (free eval license) — see provision.ps1 header for the docker line
.\provision.ps1 -Uri bolt://localhost:7687 -User neo4j -Password password
```

Idempotent (`IF NOT EXISTS` throughout). On a fresh topology the smoke returns `0 / 0 / 0`;
success is that the federated query **runs** (both aliases resolve, no write).

**Docker-only host? Nothing to do — the script handles it (G54, fixed 2026-08-04).**
`cypher-shell` ships inside the image at `/var/lib/neo4j/bin/cypher-shell`, so a machine
whose only Neo4j is the container has none on PATH. `provision.ps1` now detects that and
falls back to `docker cp` + `docker exec … -f`, reading the container name from
`config/dev-environment.yaml` (`neo4j.container`). Override with `-Container <name>`;
force the path with `-ForceDockerExec`. It announces which transport it took.

> **Other environments re-create this step, they do not copy it.** The SCRIPT is portable
> and needs no edit — it reads whatever container name your own `config/dev-environment.yaml`
> declares. What is **not** portable is everything the header's `docker run` block names:
> container, ports, image tag and source, credential handling. `config/dev-environment.yaml`
> is `canonical-company` in PORT-MANIFEST precisely so each side keeps its own; re-author the
> container step against your names and secret handling, then run the script unchanged.

### Running each file by hand

Only needed to apply one step in isolation, or to diagnose a failing one — `provision.ps1`
does all of this for you. From this directory:

```powershell
cd drydocs_core\schema\provisioning
$c  = "<your-container>"
$pw = "<your-password>"     # or read it from .env; never commit it

# 1. databases + composite  ->  the SYSTEM database (this is what creates ddschema)
docker cp .\01_databases.cypher "${c}:/tmp/01_databases.cypher"
docker exec $c cypher-shell -u neo4j -p $pw -d system -f /tmp/01_databases.cypher

# 2. proxy-node constraints  ->  each ESTATE database, one call per database.
#    ddschema is NOT in this list on purpose: its exemplar nodes would fail the
#    NODE KEYs, so its one constraint ships in schema_graph.cypher and is applied
#    by `drydocs bootstrap-schema-graph` (G51). Its absence is a decision.
docker cp .\02_proxy_constraints.cypher "${c}:/tmp/02_proxy_constraints.cypher"
docker exec $c cypher-shell -u neo4j -p $pw -d drydocs   -f /tmp/02_proxy_constraints.cypher
docker exec $c cypher-shell -u neo4j -p $pw -d ddlineage -f /tmp/02_proxy_constraints.cypher
docker exec $c cypher-shell -u neo4j -p $pw -d ddcontext -f /tmp/02_proxy_constraints.cypher

# 3. read-only smoke  ->  the COMPOSITE
docker cp .\smoke_drydocs_all.cypher "${c}:/tmp/smoke_drydocs_all.cypher"
docker exec $c cypher-shell -u neo4j -p $pw -d ddall -f /tmp/smoke_drydocs_all.cypher

# 4. populate the meta-graph (creates nothing — step 1 already made the database)
cd ..\..\..
poetry run drydocs bootstrap-schema-graph

docker exec $c sh -c "rm -f /tmp/*.cypher"    # tidy up
```

Verified end to end 2026-08-04 (laptop, container `neo4jtest`, Neo4j 2026.05.0 Enterprise):
all six `cypher-shell` calls exit 0 and the smoke federates `2218 / 0 / 46` across the
composite.

> **Copy the file in and use `-f`. Piping works on some hosts and not others.**
>
> `Get-Content .\01_databases.cypher | docker exec -i $c cypher-shell …` succeeds on a
> default ANSI-codepage console (verified on a company host, 2026-08-04) and **fails** on a
> UTF-8 one, where the error blames the file:
>
> ```
> Invalid input '﻿' … "﻿// ====…"  (line 1, column 1)
> ```
>
> The file is clean — J29 byte-scans every tracked `.cypher` and this directory passes. The
> BOM comes from the PIPE, and only when the console output encoding carries a preamble.
> Check yours:
>
> ```powershell
> [Console]::OutputEncoding.GetPreamble().Length   # 3 = the pipe will BOM you; 0 = it won't
> ```
>
> On `chcp 65001` that is 3, and the preamble is written ahead of the first line on stdin
> redirection. Also measured, since each looks like it should help and none does: `-Raw`
> fails identically, `$OutputEncoding` is a *different* setting and is already preamble-free,
> and reassigning `[Console]::OutputEncoding` mid-session is too late because the redirection
> is already configured. `docker cp` + `-f` sidesteps console encoding entirely and therefore
> works on both — which is why it is the documented form and what `provision.ps1` does. This
> replaces an earlier note here that called the pipe simply broken; it is host-dependent, and
> a rule stated too broadly gets ignored the first time someone sees it not apply.

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
