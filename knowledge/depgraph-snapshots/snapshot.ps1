<#
  snapshot.ps1 — produce a depgraph snapshot named <project>-<date>.json with a
  `meta` header (git commit / branch / PR / capture date) so each snapshot is
  self-identifying and comparable. Run after a push.

    .\snapshot.ps1                       # code graph: drydocs/ + tests/  -> drydocs1-YYYYMMDD.json
    .\snapshot.ps1 -Tree                 # full file tree (repo root)      -> drydocs1-tree-YYYYMMDD.json
    .\snapshot.ps1 -Project myproj       # override the project name

  The header is prepended to depgraph's JSON (formatting preserved, no BOM) so the
  viewer (viewer.html) shows the version and JSON diffs stay clean.
#>
[CmdletBinding()]
param(
  [string]$Project = "drydocs1",
  [switch]$Tree
)
$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$repo = (Resolve-Path "$here\..\..").Path
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
if ($Tree) { $targets = @($repo);                       $tag = "-tree" }
else       { $targets = @("$repo\drydocs","$repo\tests"); $tag = "" }
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
