<#
  snapshot.ps1 — produce a depgraph snapshot named <project>-<date>.json with a
  `meta` header (git commit / branch / PR / capture date) so each snapshot is
  self-identifying and comparable. Run after a push.

    .\snapshot.ps1                       # code graph: drydocs/ + tests/  -> drydocs-YYYYMMDD.json
    .\snapshot.ps1 -Tree                 # full file tree (repo root)      -> drydocs-tree-YYYYMMDD.json
    .\snapshot.ps1 -Project myproj       # override the project name

  The header is prepended to depgraph's JSON (formatting preserved, no BOM) so the
  viewer (viewer.html) shows the version and JSON diffs stay clean.
#>
[CmdletBinding()]
param(
  [string]$Project = "drydocs",
  [switch]$Tree
)
$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$repo = (Resolve-Path "$here\..\..").Path

# --- refresh the project board (best-effort; part of the session-end ritual) --
# backlog.yaml -> docs/plan/board.html. Deterministic render: a resulting git
# diff on board.html means the committed board was stale — commit the refresh.
try {
  Push-Location $repo
  $env:PYTHONPATH = "."
  & python scripts/render_board.py | Write-Host
  Pop-Location
} catch {
  Pop-Location -ErrorAction SilentlyContinue
  Write-Warning "board refresh skipped: $($_.Exception.Message)"
}

# --- refresh the design docs (best-effort; part of the session-end ritual) ----
# docs/design/*.md -> <stem>.html + <stem>.print.html (Epic L). Deterministic render:
# a resulting git diff on a doc render means the committed HTML was stale — commit it.
try {
  Push-Location $repo
  $env:PYTHONPATH = "."
  $designDocs = Get-ChildItem "$repo\docs\design\*.md" -ErrorAction SilentlyContinue
  if ($designDocs) { & python scripts/render_design_doc.py @($designDocs.FullName) | Write-Host }
  Pop-Location
} catch {
  Pop-Location -ErrorAction SilentlyContinue
  Write-Warning "design-doc refresh skipped: $($_.Exception.Message)"
}

$dep  = (Resolve-Path "$here\..\..\..\depgraph").Path

# --- git metadata (best-effort) ---------------------------------------------
Push-Location $repo
$commit   = (git rev-parse --short HEAD).Trim()
$full     = (git rev-parse HEAD).Trim()
$branch   = (git rev-parse --abbrev-ref HEAD).Trim()
$subject  = (git log -1 --format=%s).Trim()
try { $describe = (git describe --tags --always 2>$null).Trim() } catch { $describe = $commit }
if (-not $describe) { $describe = $commit }
$dirty    = ((git status --porcelain | Measure-Object).Count -gt 0)
$pr = $null
$m = [regex]::Match(((git log -20 --format="%s %b") -join "`n"), '(?:pull request |PR ?#|\(#)(\d+)')
if ($m.Success) { $pr = [int]$m.Groups[1].Value }
Pop-Location

# --- scan + name -------------------------------------------------------------
# Code graph spans every top-level package since the Phase B relocate (ADR
# 0002-A-1, 2026-07-10): drydocs (components) + drydocs_core + drydocs_remediation
# + drydocs_lineage + drydocs_deepdoc (G4/G9, 2026-07-11).
if ($Tree) { $targets = @($repo);                       $tag = "-tree" }
else       { $targets = @("$repo\drydocs","$repo\drydocs_core","$repo\drydocs_remediation","$repo\drydocs_lineage","$repo\drydocs_deepdoc","$repo\tests"); $tag = "" }
$date = Get-Date -Format "yyyyMMdd"
$out  = Join-Path $here ("{0}{1}-{2}.json" -f $Project, $tag, $date)
if (Test-Path $out) { $out = Join-Path $here ("{0}{1}-{2}-{3}.json" -f $Project, $tag, $date, (Get-Date -Format "HHmm")) }
$tmp  = Join-Path $env:TEMP ("depgraph-{0}.json" -f ([guid]::NewGuid()))

Push-Location $dep
$env:PYTHONPATH = "."
$argList = @("-m","depgraph.cli","scan") + $targets + @("--project",$Project)
if ($Tree) { $argList += "--tree" }
$argList += @("-o",$tmp)
& python @argList | Out-Null
Pop-Location

# --- prepend meta header (no reformat, no BOM) -------------------------------
$meta = [ordered]@{
  project     = $Project
  captured_at = (Get-Date).ToString("s")
  date        = $date
  scan        = ($targets | ForEach-Object { Split-Path $_ -Leaf })
  tree        = [bool]$Tree
  git         = [ordered]@{ commit=$commit; full=$full; branch=$branch; describe=$describe; subject=$subject; dirty=$dirty; pr=$pr }
}
$metaJson = ($meta | ConvertTo-Json -Depth 6 -Compress)
$raw = Get-Content $tmp -Raw
$i   = $raw.IndexOf('{')
$new = $raw.Substring(0, $i+1) + "`n  ""meta"": $metaJson," + $raw.Substring($i+1)
[System.IO.File]::WriteAllText($out, $new, (New-Object System.Text.UTF8Encoding $false))
Remove-Item $tmp -ErrorAction SilentlyContinue

$prTxt = if ($pr) { ", PR#$pr" } else { "" }
Write-Host "wrote $(Split-Path $out -Leaf)  (commit $commit, branch $branch$prTxt)" -ForegroundColor Green
