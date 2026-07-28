<#
  snapshot.ps1 — produce a depgraph snapshot named <project>-<date>.json with a
  `meta` header (git commit / branch / PR / capture date) so each snapshot is
  self-identifying and comparable. Run after a push.

    .\snapshot.ps1                       # code graph: the 7 package roots  -> drydocs-YYYYMMDD.json
    .\snapshot.ps1 -Tree                 # full file tree (repo root)       -> drydocs-tree-YYYYMMDD.json
    .\snapshot.ps1 -Project myproj       # override the project name

  The header is prepended to depgraph's JSON (formatting preserved, no BOM) so the
  viewer (viewer.html) shows the version and JSON diffs stay clean.

  Two post-processing steps keep the series trustworthy rather than merely present:
    U7 — record the INSTRUMENT (depgraph commit/branch/capabilities) in the header,
         and refuse to scan when the sibling checkout cannot do what the run needs.
    U8 — strip machine-absolute abs_path, so snapshots taken on different machines
         (or in an agent worktree) are comparable instead of 100% false-diffing.
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
  & poetry run python scripts/render_board.py | Write-Host
  Pop-Location
} catch {
  Pop-Location -ErrorAction SilentlyContinue
  Write-Warning "board refresh skipped: $($_.Exception.Message)"
}

# --- refresh the design docs (best-effort; part of the session-end ritual) ----
# docs/design/*.md -> <stem>.html (one surface: screen + @media print; Epic L / L13). Deterministic render:
# a resulting git diff on a doc render means the committed HTML was stale — commit it.
try {
  Push-Location $repo
  $env:PYTHONPATH = "."
  $designDocs = Get-ChildItem "$repo\docs\design\*.md" -ErrorAction SilentlyContinue
  if ($designDocs) { & poetry run python scripts/render_design_doc.py @($designDocs.FullName) | Write-Host }
  Pop-Location
} catch {
  Pop-Location -ErrorAction SilentlyContinue
  Write-Warning "design-doc refresh skipped: $($_.Exception.Message)"
}

$dep  = (Resolve-Path "$here\..\..\..\depgraph").Path

# --- instrument identity + capability probe (U7) -----------------------------
# The scan runs in a SIBLING REPO, so the revision checked out there decides what
# the snapshot can see. On 2026-07-28 a checkout without the multi-root resolver
# wrote 105 edges instead of 370 and looked entirely normal. Two defences: record
# which instrument ran (below, into the meta header), and refuse to scan when it
# cannot do what this run needs. The probe is behavioural, never a version string
# — capability is what matters, and depgraph's 0.1.0 spans both the broken and
# the fixed resolver, so a version string says nothing.
Push-Location $dep
$depCommit = (git rev-parse --short HEAD).Trim()
$depFull   = (git rev-parse HEAD).Trim()
$depBranch = (git rev-parse --abbrev-ref HEAD).Trim()
$depDirty  = ((git status --porcelain | Measure-Object).Count -gt 0)
$env:PYTHONPATH = "."
$capsJson  = (& python (Join-Path $here "probe_instrument.py")) -join ""
Pop-Location

$caps = $null
try { $caps = $capsJson | ConvertFrom-Json } catch { }
if (-not $caps) {
  throw "depgraph capability probe produced no JSON (instrument at $dep). Cannot establish what a scan would see; refusing rather than writing an unverifiable snapshot."
}
$needed = @("multi_root") + $(if ($Tree) { @("tree") } else { @() })
$absent = @($needed | Where-Object { -not $caps.$_ })
if ($absent.Count -gt 0) {
  $why = @{
    multi_root = "cross-root and same-package absolute imports resolve only when every scan root shares one namespace; without it the edge count silently collapses (U6)"
    tree       = "``scan --tree`` walks the full file tree (-Tree snapshots)"
  }
  $lines = $absent | ForEach-Object { "    - {0}: {1}" -f $_, $why[$_] }
  throw @"
Refusing to scan — the checked-out depgraph cannot do what this run needs.

  instrument : $dep
               $depBranch @ $depCommit$(if ($depDirty) { ' (dirty)' })
  missing    :
$($lines -join "`n")

  Expected branch/commit are recorded in config/dev-environment.yaml.
  Fix: git -C "$dep" fetch && git -C "$dep" checkout main && git -C "$dep" pull.
  main has carried every capability since the fork was consolidated 2026-07-28
  (depgraph 5006567); a checkout stranded on an older revision is the likely cause.

A snapshot written by a regressed scanner is worse than no snapshot: it is
plausible, diffable, and wrong (the 105-edge near-commit of 2026-07-28).
"@
}

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
# + drydocs_lineage + drydocs_deepdoc (G4/G9, 2026-07-11) + drydocs_api (U6,
# 2026-07-28 — was invisible to every code-graph metric until the U2 census).
if ($Tree) { $targets = @($repo);                       $tag = "-tree" }
else       { $targets = @("$repo\drydocs","$repo\drydocs_core","$repo\drydocs_api","$repo\drydocs_remediation","$repo\drydocs_lineage","$repo\drydocs_deepdoc","$repo\tests"); $tag = "" }
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
  # WHICH INSTRUMENT PRODUCED THIS (U7). Without it a scanner regression is
  # invisible in the artifact and shows up only as numbers nobody questions.
  depgraph    = [ordered]@{ commit=$depCommit; full=$depFull; branch=$depBranch; dirty=$depDirty; version=$caps.version; capabilities=[ordered]@{ multi_root=[bool]$caps.multi_root; tree=[bool]$caps.tree } }
}
$metaJson = ($meta | ConvertTo-Json -Depth 6 -Compress)
$raw = Get-Content $tmp -Raw

# --- drop machine-absolute paths (U8) ----------------------------------------
# depgraph stamps abs_path with the checkout location, so the same code snapshot
# taken from the desktop, the laptop, or an agent worktree differs on EVERY node
# while the edges stay byte-identical — a 100%-false structural diff that made
# the ritual unrunnable from a worktree. file_id + rel_path already carry the
# stable identity, and the G33 loader drops abs_path at load anyway (§H4).
# Removed TEXTUALLY, like the meta header is injected, so formatting is untouched.
$before = ([regex]::Matches($raw, '"abs_path"')).Count
$raw    = [regex]::Replace($raw, '(?m)^[ \t]*"abs_path":[ \t]*"[^"]*",[ \t]*\r?\n', '')
$after  = ([regex]::Matches($raw, '"abs_path"')).Count
if ($after -gt 0) {
  throw "abs_path strip incomplete: $after of $before remain (unexpected JSON shape). Refusing to write a snapshot that still carries machine-absolute paths."
}

$i   = $raw.IndexOf('{')
$new = $raw.Substring(0, $i+1) + "`n  ""meta"": $metaJson," + $raw.Substring($i+1)
try { $null = $new | ConvertFrom-Json } catch {
  throw "post-processed snapshot is not valid JSON: $($_.Exception.Message)"
}
[System.IO.File]::WriteAllText($out, $new, (New-Object System.Text.UTF8Encoding $false))
Remove-Item $tmp -ErrorAction SilentlyContinue

$prTxt = if ($pr) { ", PR#$pr" } else { "" }
Write-Host "wrote $(Split-Path $out -Leaf)  (commit $commit, branch $branch$prTxt)" -ForegroundColor Green
