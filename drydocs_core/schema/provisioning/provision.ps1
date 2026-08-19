<#
  provision.ps1 — apply the G1 multi-DB topology (ADR 0002 D1) to a Neo4j ENTERPRISE
  DBMS, then run the read-only smoke. Idempotent (safe to re-run).

  REQUIRES:
    * a Neo4j ENTERPRISE instance — multi-database + composite are Enterprise-only.
      Community edition (exactly one database) CANNOT host this topology.
    * a way to REACH it, and the script picks one for you (G54, 2026-08-04):
        - `cypher-shell` on the host PATH, if present; otherwise
        - `docker cp` + `docker exec <container> cypher-shell -f`, with the container
          name read from config/dev-environment.yaml (`neo4j.container`), overridable
          with -Container. `-ForceDockerExec` takes that path unconditionally.
      cypher-shell ships INSIDE the image (/var/lib/neo4j/bin/cypher-shell), so a host
      whose only Neo4j is the container has none — this header used to claim the image
      satisfied the requirement, which is true of the IMAGE and not of the PATH.

  OTHER ENVIRONMENTS — THIS STEP HAS TO BE RE-CREATED, NOT COPIED. Everything below
  (container name, ports, image tag, credentials) is producer-local. config/dev-environment.yaml
  is `canonical-company` in PORT-MANIFEST for exactly this reason: each side keeps its own
  file. The SCRIPT is portable and needs no edit — it reads the container name from
  whatever that file says on your side; the docker run lines below are the part you
  re-author against your own names, ports, image source and secret handling.

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
  [string]$Password = $env:NEO4J_PASSWORD,
  # G54: only used when cypher-shell is absent from the host PATH. Left empty it is
  # read from config/dev-environment.yaml (neo4j.container).
  [string]$Container,
  # Force the docker-exec path even where a host cypher-shell exists - for a mixed
  # install whose client version does not match the server, and to exercise the
  # fallback on a machine that would otherwise never take it.
  [switch]$ForceDockerExec
)
$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
if (-not $Uri)      { $Uri  = "bolt://localhost:7687" }
if (-not $User)     { $User = "neo4j" }
if (-not $Password) { throw "Set -Password or the NEO4J_PASSWORD environment variable." }

# --- transport selection (G54): host cypher-shell, or docker exec into the container --
# cypher-shell ships INSIDE the Neo4j image, not on the host, so a machine whose only
# Neo4j is the container has no such binary on PATH and the documented invocation could
# not complete. The header above already owns the `docker run` lines, so this path
# already assumes Docker; detect and fall back rather than making the operator translate.
$useDocker = $false
if (-not $ForceDockerExec -and (Get-Command cypher-shell -ErrorAction SilentlyContinue)) {
  Write-Host "transport: host cypher-shell" -ForegroundColor DarkGray
} else {
  if (-not $Container) {
    # Read the container name from config/dev-environment.yaml rather than hardcoding
    # it: that file is the canonical per-environment record, and it is canonical-company
    # in PORT-MANIFEST precisely because the value differs per side.
    $cfgPath = Join-Path $here "..\..\..\config\dev-environment.yaml"
    if (Test-Path $cfgPath) {
      $cfg = Get-Content $cfgPath -Raw
      # Scoped to the `neo4j:` block so a same-named key elsewhere cannot match.
      if ($cfg -match '(?ms)^neo4j:[\r\n]+(.*?)(?=^\S|\Z)') {
        $block = $Matches[1]
        if ($block -match '(?m)^\s+container:\s*(\S+)') { $Container = $Matches[1] }
      }
    }
  }
  if (-not $Container) {
    throw @"
cypher-shell is not on PATH and no container name could be resolved.

  cypher-shell ships inside the Neo4j image (/var/lib/neo4j/bin/cypher-shell), so a
  Docker-only host has none. Either install the Neo4j tarball/client, or pass
  -Container <name>, or set neo4j.container in config/dev-environment.yaml.
"@
  }
  if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Neither cypher-shell nor docker is on PATH - nothing can reach the DBMS from here."
  }
  $useDocker = $true
  # INSIDE the container the server is on its own bolt port, always 7687 - the host
  # port mapping in dev-environment.yaml is a HOST fact and is irrelevant here. Passing
  # the host URI through would break on any container whose ports were remapped, which
  # has happened before (the 7476/7689 container, retired 2026-07-23).
  $execUri = "bolt://localhost:7687"
  Write-Host "transport: docker exec [$Container] (cypher-shell absent from host PATH - G54)" -ForegroundColor Yellow
  Write-Host "           in-container address $execUri; host port mapping does not apply" -ForegroundColor DarkGray
}

function Invoke-CypherFile([string]$Db, [string]$File) {
  Write-Host "-> [$Db] $File" -ForegroundColor Cyan
  $local = Join-Path $here $File
  if ($useDocker) {
    # COPY THE FILE IN, then -f. Do NOT pipe it (J29) - but the reason is narrower
    # than it first looked, and the narrower version is the useful one.
    #
    # `Get-Content x | docker exec -i ... cypher-shell` injects a BOM ONLY where the
    # console output encoding carries one. On a UTF-8 console (chcp 65001)
    # [Console]::OutputEncoding is UTF-8 WITH a 3-byte preamble, written ahead of the
    # first line on stdin redirection, so cypher-shell rejects a CLEAN file with
    # "Invalid input '<BOM>'" at line 1 col 1 and blames the file. On a default
    # ANSI-codepage console there is no preamble and the pipe works - verified on a
    # company host 2026-08-04, which is why this comment no longer says "PS 5.1 pipes
    # are broken". Check your own with:
    #     [Console]::OutputEncoding.GetPreamble().Length     # 3 = the pipe will BOM you
    #
    # docker cp sidesteps console encoding entirely, so it works on both - which is
    # why it is what this script does rather than something conditional. Also measured:
    # -Raw fails identically where the preamble exists, $OutputEncoding is a different
    # setting and is already preamble-free, and reassigning [Console]::OutputEncoding
    # mid-session is too late because the redirection is already configured.
    $remote = "/tmp/$File"
    docker cp $local "${Container}:$remote"
    if ($LASTEXITCODE -ne 0) { throw "docker cp failed for $File (exit $LASTEXITCODE)" }
    try {
      docker exec $Container cypher-shell -a $execUri -u $User -p $Password -d $Db -f $remote
      $code = $LASTEXITCODE
    } finally {
      docker exec $Container rm -f $remote | Out-Null
    }
    if ($code -ne 0) { throw "cypher-shell failed on [$Db] $File (exit $code)" }
  } else {
    cypher-shell -a $Uri -u $User -p $Password -d $Db -f $local
    if ($LASTEXITCODE -ne 0) { throw "cypher-shell failed on [$Db] $File (exit $LASTEXITCODE)" }
  }
}

# 1. databases + composite (run on the system database)
Invoke-CypherFile "system" "01_databases.cypher"

# 2. (RETIRED at G31/G102, 2026-08-18) — the proxy-constraint pass ran
#    02_proxy_constraints.cypher against drydocs AND ddcontext so the composite
#    could join them by business key. The fold left one database; the keys live
#    in constraints.cypher (applied by `drydocs bootstrap`), and the federated
#    smoke retired with `ddall`. `ddschema` remains deliberately outside every
#    constraint pass (G51): its one constraint ships in schema_graph.cypher.

Write-Host "OK  topology provisioned (drydocs, ddschema - the G102 fold; constraints ride drydocs bootstrap)." -ForegroundColor Green
