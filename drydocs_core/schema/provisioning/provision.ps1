<#
  provision.ps1 — apply the G1 multi-DB topology (ADR 0002 D1) to a Neo4j ENTERPRISE
  DBMS, then run the read-only smoke. Idempotent (safe to re-run).

  REQUIRES:
    * cypher-shell on PATH (bundled in the Neo4j Docker image and tarball).
    * a Neo4j ENTERPRISE instance — multi-database + composite are Enterprise-only.
      Community edition (exactly one database) CANNOT host this topology.

  Local dev Enterprise via Docker (free evaluation license). Canonical names/ports/
  plugins live in config/dev-environment.yaml — change them THERE, then here
  (tests/unit/test_dev_environment.py fails if this command drifts from that file).

  STEP 1 — populate the plugins volume ONCE, from the image itself:
    docker volume create neo4j-testplugins
    docker run --rm --entrypoint sh -v neo4j-testplugins:/plugins neo4j:2026.05.0-enterprise `
      -c 'cp /var/lib/neo4j/labs/apoc-*-core.jar /plugins/ && cp /var/lib/neo4j/products/neo4j-graph-data-science-*.jar /plugins/'

  STEP 2 — create the container, mounting BOTH volumes:
    docker run -d --name neo4jtest --restart unless-stopped -p 7474:7474 -p 7687:7687 `
      -v neo4j-testdata:/data `
      -v neo4j-testplugins:/plugins `
      -e NEO4J_AUTH=neo4j/<password> `
      -e NEO4J_ACCEPT_LICENSE_AGREEMENT=eval `
      -e NEO4J_dbms_security_procedures_unrestricted=apoc.*,gds.* `
      -e NEO4J_dbms_security_procedures_allowlist=apoc.*,gds.* `
      neo4j:2026.05.0-enterprise

  DO NOT use `-e NEO4J_PLUGINS='["apoc"]'` (what this header said until 2026-07-28).
  That asks the entrypoint to DOWNLOAD the plugin at startup; when the download cannot
  happen the container starts anyway and the plugin is silently absent — the failure
  mode actually observed, for weeks, with the env var set the whole time. The jars ship
  inside the image and are version-matched to the server, so STEP 1 needs no network.
  The volume is what makes it survive `docker rm` + `docker run`; a jar copied into a
  running container lives in its writable layer and dies on recreate.

  Then:
    .\provision.ps1 -Uri bolt://localhost:7687 -User neo4j -Password password

  Target-agnostic: the same scripts run unchanged against any multi-DB-capable
  self-managed Enterprise DBMS (Aura was ruled out 2026-07-06).
#>
[CmdletBinding()]
param(
  [string]$Uri      = $env:NEO4J_URI,
  [string]$User     = $env:NEO4J_USER,
  [string]$Password = $env:NEO4J_PASSWORD
)
$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
if (-not $Uri)      { $Uri  = "bolt://localhost:7687" }
if (-not $User)     { $User = "neo4j" }
if (-not $Password) { throw "Set -Password or the NEO4J_PASSWORD environment variable." }

function Invoke-CypherFile([string]$Db, [string]$File) {
  Write-Host "-> [$Db] $File" -ForegroundColor Cyan
  cypher-shell -a $Uri -u $User -p $Password -d $Db -f (Join-Path $here $File)
  if ($LASTEXITCODE -ne 0) { throw "cypher-shell failed on [$Db] $File (exit $LASTEXITCODE)" }
}

# 1. databases + composite (run on the system database)
Invoke-CypherFile "system" "01_databases.cypher"

# 2. proxy-node constraints in the three ESTATE databases.
#    `ddschema` is created by step 1 and deliberately skipped here (G51): the schema
#    meta-graph's exemplars would fail the ControlMJob NODE KEY, so its one constraint
#    (`schemameta_name`) ships in schema_graph.cypher and is applied by
#    `drydocs bootstrap-schema-graph`. Its absence below is a decision, not an omission.
Invoke-CypherFile "drydocs"    "02_proxy_constraints.cypher"
Invoke-CypherFile "ddlineage"  "02_proxy_constraints.cypher"
Invoke-CypherFile "ddcontext"  "02_proxy_constraints.cypher"

# 3. read-only federated smoke over the composite (ddschema is not a constituent)
Invoke-CypherFile "ddall" "smoke_drydocs_all.cypher"

Write-Host "OK  G1 topology provisioned + smoke passed (drydocs, ddlineage, ddcontext, ddschema, ddall)." -ForegroundColor Green
