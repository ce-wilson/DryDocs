<#
  provision.ps1 — apply the G1 multi-DB topology (ADR 0002 D1) to a Neo4j ENTERPRISE
  DBMS, then run the read-only smoke. Idempotent (safe to re-run).

  REQUIRES:
    * cypher-shell on PATH (bundled in the Neo4j Docker image and tarball).
    * a Neo4j ENTERPRISE instance — multi-database + composite are Enterprise-only.
      Community edition (exactly one database) CANNOT host this topology.

  Local dev Enterprise via Docker (free evaluation license), e.g.:
    docker run -d --name neo4j-ent -p 7474:7474 -p 7687:7687 `
      -e NEO4J_AUTH=neo4j/password `
      -e NEO4J_ACCEPT_LICENSE_AGREEMENT=eval `
      -e NEO4J_PLUGINS='["apoc"]' neo4j:5-enterprise

  Then:
    .\provision.ps1 -Uri bolt://localhost:7687 -User neo4j -Password password

  Target-agnostic: the same scripts run unchanged against any multi-DB-capable DBMS
  (self-managed Enterprise or an Aura tier that supports multiple databases).
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

# 2. proxy-node constraints in BOTH data databases
Invoke-CypherFile "drydocs"         "02_proxy_constraints.cypher"
Invoke-CypherFile "drydocs_context" "02_proxy_constraints.cypher"

# 3. read-only federated smoke over the composite
Invoke-CypherFile "drydocs_all" "smoke_drydocs_all.cypher"

Write-Host "OK  G1 topology provisioned + smoke passed (drydocs, drydocs_context, drydocs_all)." -ForegroundColor Green
