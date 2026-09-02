<#
  snapshot.ps1 — produce a depgraph snapshot named <project>-<date>.json with a
  `meta` header (git commit / branch / PR / capture date) so each snapshot is
  self-identifying and comparable. Run after a push.

    .\snapshot.ps1                       # FULL FILE TREE (repo root)       -> drydocs-YYYYMMDD.json
    .\snapshot.ps1 -CodeOnly             # legacy: the 7 package roots, .py -> drydocs-code-YYYYMMDD.json
    .\snapshot.ps1 -Project myproj       # override the project name

  THE FULL TREE IS THE DEFAULT (SME direction). It is a strict SUPERSET of the
  old roots-only scan: same import edges, plus directories, plus CONTAINS, plus
  every non-.py file. That matters because the old scan could only ever see
  Python, so the .cypher a loader executes, the .sql an extractor runs and the
  .yaml a module reads were all invisible — and the containment tree had to be
  guessed from path strings instead of read from the artifact.
  -CodeOnly is kept for comparison against the retired series, not for the
  ritual; it writes a DIFFERENT filename so the two shapes can never collide in
  the directory or be mistaken for one another by the loader (`meta.tree`).

  The header is prepended to depgraph's JSON (formatting preserved, no BOM) so the
  viewer (viewer.html) shows the version and JSON diffs stay clean.

  U15 — `dirty` on both sides of the header means TRACKED changes only, and
        `untracked_present` is recorded beside it. One boolean over both used to
        say "dirty" when the only dirt was a scratch file, which reads as "the
        commit named here does not describe what was scanned" and is false.

  Post-processing steps keep the series trustworthy rather than merely present:
    U7 — record the INSTRUMENT (depgraph commit/branch/capabilities) in the header,
         and refuse to scan when the sibling checkout cannot do what the run needs.
    U8 — strip machine-absolute abs_path, so snapshots taken on different machines
         (or in an agent worktree) are comparable instead of 100% false-diffing.
    U9 — drop git-ignored paths, so build caches never masquerade as structure.
    U12 — ENFORCE the ruled retention (SME 2026-08-02): the newest all-files
         snapshot is the ONLY one kept; every older <project>-<date>[-HHmm].json
         is deleted after a successful write. Git history is the archive. Before
         this, a same-day rerun wrote a -HHmm sibling and relied on a human to
         delete it — which is exactly how a 101-file series accumulated once,
         and the sibling reappeared four times in the two days after the ruling.
         -CodeOnly comparison files keep their own name and are exempt.
#>
[CmdletBinding()]
param(
  [string]$Project = "drydocs",
  [switch]$CodeOnly
)
# The full tree is the default; $Tree stays as the internal name because it is
# what depgraph's flag and the meta header are both called.
$Tree = -not $CodeOnly
$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$repo = (Resolve-Path "$here\..\..").Path

# --- worktree state: TRACKED changes and UNTRACKED presence, kept apart (U15) -
# `git status --porcelain` with no flags lists untracked files too, so a single
# boolean read `dirty` whenever any stray scratch file sat in the tree. The
# 20260805 snapshot recorded dirty=true at exactly the pinned commit, the "dirt"
# being three untracked paths -- which tells a reader the opposite of the truth:
# that the committed code differs from what was scanned. The two facts answer
# different questions, so they are now two fields:
#
#   dirty             do TRACKED files differ from HEAD? This is the provenance
#                     question -- does the commit in this header actually
#                     describe the code that was measured?
#   untracked_present are there untracked paths in the worktree? Housekeeping
#                     for the repo side; for the INSTRUMENT side it is closer to
#                     provenance, because depgraph is run out of its checkout
#                     and an untracked .py there is code that could take part in
#                     the scan without appearing in any commit.
#
# `dirty` KEEPS ITS NAME rather than becoming dirty_tracked: it is loaded onto
# :Project as git_dirty (drydocs/loaders/cypher/code_snapshot.cypher) and every
# committed snapshot in the series carries it. What changes is that it now means
# what its readers already assumed it meant.
function Get-WorktreeState {
  param([string]$Path)
  # Two commands rather than one parse of --porcelain: each states its own
  # question, and neither depends on the caller's location.
  $tracked   = @(git -C "$Path" status --porcelain --untracked-files=no)
  $untracked = @(git -C "$Path" ls-files --others --exclude-standard)
  return [ordered]@{
    dirty             = ($tracked.Count   -gt 0)
    untracked_present = ($untracked.Count -gt 0)
  }
}

# --- refresh helpers (J53) ----------------------------------------------------
# Both refresh steps below are best-effort (they must never block the snapshot)
# but the OLD idiom could not say why a step failed. It ran the render under
# $ErrorActionPreference = "Stop" with no explicit stderr capture and printed
# $_.Exception.Message. For a failing NATIVE command that message is only the
# FIRST line PowerShell wrapped from stderr — and the first line a Python
# failure ever writes is the literal "Traceback (most recent call last):"
# banner (every traceback starts with it), never the exception itself. So the
# warning could name a cause only by accident, and in practice named none.
# Worse: on a partial render (2026-08-23: 3 of the renderer's 9 outputs were
# written, 6 were left stale) nothing said which was which, so the session
# ritual's stale-render diff ran against an unknown state.
#
# Fix: capture the FULL merged stdout+stderr of the render explicitly (never
# rely on PowerShell's console-dependent stderr-to-ErrorRecord wrapping — it is
# not even consistent: a native command's nonzero exit does not always throw
# under EAP=Stop, so the old catch block could also simply never fire and the
# traceback would print with no warning at all), read $LASTEXITCODE directly,
# and on failure report the LAST non-empty line (the exception type + message)
# rather than the exception's own .Message. Landed vs. stale is read from each
# expected output's mtime, compared before/after the run, so a partial render
# is reported by name instead of by guess.
#
# WORKED EXAMPLE (the reproduction this was built against, not the fix itself):
# on this desktop the trigger is $env:VIRTUAL_ENV being pre-set (to
# agents\.venv — see the "Desktop VIRTUAL_ENV Leak" project memory) before this
# script runs `poetry run python ...`. Poetry inherits it and resolves imports
# against that OTHER environment instead of the project's own, so the render
# gets partway through (writes board.html, gates.json, enforcement-matrix.json)
# before failing on a package the leaked environment lacks (observed:
# `ModuleNotFoundError: No module named 'typer'`, importing drydocs/cli.py from
# scripts/render_load_map.py, the 4th of 9 render steps). A user's own terminal
# does not pre-set VIRTUAL_ENV, so this was never seen interactively — which is
# exactly why the warning has to name the cause rather than assuming whoever
# reads it already knows it. This is not the fix; the fix is that the warning
# below would now say `ModuleNotFoundError: No module named 'typer'` instead of
# `Traceback (most recent call last):`.

function Write-RefreshFailure {
  param(
    [string]$Name,
    [string[]]$Output,
    [string[]]$ExpectedOutputs,
    [hashtable]$Before,
    [string]$Repo
  )
  $landed = @()
  $stale  = @()
  foreach ($rel in $ExpectedOutputs) {
    $p = Join-Path $Repo $rel
    $after = if (Test-Path $p) { (Get-Item $p).LastWriteTimeUtc } else { $null }
    if ($after -and $after -ne $Before[$rel]) { $landed += $rel } else { $stale += $rel }
  }
  # The LAST non-empty line names the cause: for a Python failure that is the
  # exception type + message (the traceback's FIRST line is always the banner,
  # never the cause); for a failing native command it is the last line of
  # stderr, which is the closest a shell gets to "the actual error".
  $causeLines = @($Output | Where-Object { $_.Trim() -ne "" })
  $cause = if ($causeLines.Count -gt 0) { $causeLines[-1] } else { "(process produced no output)" }
  $landedTxt = if ($landed.Count -gt 0) { $landed -join ", " } else { "(none)" }
  $staleTxt  = if ($ExpectedOutputs.Count -eq 0) { "(not tracked)" } elseif ($stale.Count -gt 0) { $stale -join ", " } else { "(none)" }
  Write-Warning @"
$Name refresh FAILED -- cause: $cause
  landed (written this run) : $landedTxt
  stale  (unchanged)        : $staleTxt
Full command output was printed above. The session ritual's stale-render diff
check should be read against this landed/stale split, not against an unknown
state -- a partial render is now distinguishable from a skipped one.
"@
}

function Invoke-RefreshStep {
  # Runs `poetry <Args>` best-effort: never throws past this function, always
  # reports a real cause on failure (see the header comment above for why the
  # old $_.Exception.Message idiom could not).
  param(
    [Parameter(Mandatory)][string]$Name,
    [Parameter(Mandatory)][string[]]$Args,
    [string[]]$ExpectedOutputs = @()
  )
  Push-Location $repo
  $env:PYTHONPATH = "."
  $before = @{}
  foreach ($rel in $ExpectedOutputs) {
    $p = Join-Path $repo $rel
    $before[$rel] = if (Test-Path $p) { (Get-Item $p).LastWriteTimeUtc } else { $null }
  }
  try {
    # Capture merged stdout+stderr explicitly rather than letting a native
    # command's stderr become a terminating ErrorRecord under EAP=Stop (see
    # the U22 code-graph-freshness block below for the same PS 5.1 hazard).
    $prevEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    $output = @(& poetry @Args 2>&1 | ForEach-Object { "$_" })
    $exit = $LASTEXITCODE
    $ErrorActionPreference = $prevEap
    $output | Write-Host
    if ($exit -ne 0) {
      Write-RefreshFailure -Name $Name -Output $output -ExpectedOutputs $ExpectedOutputs -Before $before -Repo $repo
    }
  } catch {
    # Something failed OUTSIDE the captured invocation (e.g. `poetry` itself
    # is not on PATH) -- there is no captured stdout/stderr to read a cause
    # from, so the exception message IS the real cause here.
    Write-Warning "$Name refresh FAILED (could not run): $($_.Exception.Message)"
  } finally {
    Pop-Location -ErrorAction SilentlyContinue
  }
}

# --- refresh the project board (best-effort; part of the session-end ritual) --
# docs/restructure/backlog/ -> docs/plan/board.html plus the eight sibling renders
# scripts/render_board.py chains (gates.json, enforcement-matrix.json, load-map.json
# + load-map.html, software-registry.json, context-types.json, remediation-diff.json,
# ideas.html, roadmap.html — nine outputs total). Deterministic render: a resulting
# git diff on any of them means the committed render was stale — commit the refresh.
Invoke-RefreshStep -Name "board" -Args @("run", "python", "scripts/render_board.py") -ExpectedOutputs @(
  "docs\plan\board.html",
  "web\src\generated\gates.json",
  "web\src\generated\enforcement-matrix.json",
  "web\src\generated\load-map.json",
  "docs\plan\load-map.html",
  "web\src\generated\software-registry.json",
  "web\src\generated\context-types.json",
  "web\src\generated\remediation-diff.json",
  "docs\plan\ideas.html",
  "docs\plan\roadmap.html"
)

# --- refresh MODULE_MAP.md's component-map section (ADR 0018 D1) -------------
# Rendered from drydocs_core/component_map.py; test_module_map_render.py fails on drift.
Invoke-RefreshStep -Name "module-map" -Args @("run", "python", "scripts/render_module_map.py") -ExpectedOutputs @(
  "MODULE_MAP.md"
)

# --- refresh the design docs (best-effort; part of the session-end ritual) ----
# docs/design/*.md -> <stem>.html (one surface: screen + @media print; Epic L / L13). Deterministic render:
# a resulting git diff on a doc render means the committed HTML was stale — commit it.
# Same catch idiom as the board refresh above (J53 clause c) — a half-rendered
# batch of design docs is exactly as silent a failure mode as a half-rendered
# board, so it gets the identical treatment rather than a second copy of the bug.
$designDocs = Get-ChildItem "$repo\docs\design\*.md" -ErrorAction SilentlyContinue
if ($designDocs) {
  $designOutputs = $designDocs | ForEach-Object { ($_.FullName -replace '\.md$', '.html').Substring($repo.Length + 1) }
  Invoke-RefreshStep -Name "design-doc" -Args (@("run", "python", "scripts/render_design_doc.py") + @($designDocs.FullName)) -ExpectedOutputs $designOutputs
}

# --- CI gate check (Idea-111) — runs BEFORE the snapshot ---------------------
# The verdict is a pure function of (runs, head) so every branch is exercisable
# without a network — the reporting half is the part that rots, and a check that
# only ever prints GREEN on the machine that wrote it is how this got missed.
function Get-CiVerdict {
  param($Runs, [string]$Head)
  $short = $Head.Substring(0, 7)
  if (@($Runs).Count -eq 0) {
    return @{ Color = "DarkGray"; Text = "ci: no runs readable (gh not authenticated?) - check skipped" }
  }
  $mine = @($Runs | Where-Object { $_.headSha -eq $Head })
  if ($mine.Count -eq 0) {
    $newest = @($Runs)[0]
    return @{ Color = "Yellow"; Text = ("ci: no run yet for HEAD {0} - newest on main is {1} ({2})" -f `
      $short, [string]$newest.conclusion, [string]$newest.displayTitle) }
  }
  # U24 (2026-08-21): the 2026-08-19 snapshot printed `ci: System.Object[] AT
  # HEAD ...` - PS 5.1 member enumeration stringified a nested property as an
  # array. Pin ONE run object and read each property as a scalar string; every
  # branch below, not only the RED one that was observed, shares the hazard.
  $first = @($mine)[0]
  $status = [string]$first.status
  $conclusion = [string]$first.conclusion
  if ($status -ne "completed") {
    return @{ Color = "Yellow"; Text = ("ci: run for HEAD {0} is {1} - re-check before you close the session" -f `
      $short, $status) }
  }
  if ($conclusion -eq "success") {
    return @{ Color = "Green"; Text = ("ci: GREEN at HEAD {0}" -f $short) }
  }
  return @{ Color = "Red"; Text = ("ci: {0} AT HEAD {1} - main is RED. Run 'gh run view --log-failed' before you stop." -f `
    $conclusion.ToUpper(), $short) }
}

# WARN-ONLY by design: this reports, it never blocks. A snapshot records repo
# STRUCTURE; refusing to record it because a lint gate is red would couple two
# unrelated jobs, and the failure mode this exists to fix is nobody LOOKING, not
# somebody snapshotting.
# Why it exists: CI is BLOCKING on `ruff check` + `ruff format --check` (J10
# stage 5) and was RED from 2026-08-05 to 08-12 — 100+ consecutive failing runs —
# while sessions kept pushing past it. It stayed invisible because the unit suite
# passed the whole time, so nothing LOCAL ever looked wrong. The ritual now asks.
# It matches on HEAD's sha, so "green" always means green AT WHAT YOU PUSHED,
# never green at somebody else's older commit.
try {
  $ghCmd = $null
  try { $ghCmd = Get-Command gh -ErrorAction Stop } catch { }
  if ($null -eq $ghCmd) {
    Write-Host "ci: gh not installed - check skipped" -ForegroundColor DarkGray
  } else {
    Push-Location $repo
    $head = (& git rev-parse HEAD).Trim()
    $raw = & gh run list --branch main --limit 10 --json headSha,conclusion,status,displayTitle
    Pop-Location
    $runs = @()
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($raw)) {
      # PS 5.1 trap (false GREEN, 2026-08-20): ConvertFrom-Json emits a JSON
      # array as ONE PSObject-wrapped item (argument form included), so the
      # verdict's scalar tests become member-enumeration FILTERS - '-eq
      # "success"' is truthy if ANY of the 10 runs succeeded, not if HEAD's
      # did. Enumerating the parsed object is what actually unrolls it here.
      $runs = @((ConvertFrom-Json ($raw -join "`n")) | ForEach-Object { $_ })
    }
    $verdict = Get-CiVerdict -Runs $runs -Head $head
    Write-Host $verdict.Text -ForegroundColor $verdict.Color
  }
} catch {
  Pop-Location -ErrorAction SilentlyContinue
  Write-Warning "ci check skipped: $($_.Exception.Message)"
}

# --- code-graph freshness (U22): warn-only, beside the CI check -------------
# Is the graph this snapshot will be compared against still the graph anyone
# has loaded? One line from `drydocs code-graph-freshness`; DATABASE
# UNREACHABLE prints as its own verdict, never as fresh; nothing here blocks the
# write or refreshes anything (a check that repairs what it measures has
# measured nothing).
try {
  Push-Location $repo
  # PS 5.1: a native command's stderr becomes an ErrorRecord under
  # $ErrorActionPreference = "Stop" (the neo4j driver logs its notifications
  # there), so relax it for the call and read stdout only.
  $prevEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
  $fresh = & poetry run drydocs code-graph-freshness 2>$null
  $ErrorActionPreference = $prevEap
  Pop-Location
  if ($LASTEXITCODE -eq 0 -and $fresh) {
    $line = (($fresh | Where-Object { "$_" -match "code graph:" }) -join " ") -replace "\s+", " "
    $color = if ($line -match "FRESH") { "Green" } else { "Yellow" }
    Write-Host $line -ForegroundColor $color
  } else {
    Write-Host "code graph: freshness check skipped (drydocs CLI not runnable here)" -ForegroundColor DarkGray
  }
} catch {
  Pop-Location -ErrorAction SilentlyContinue
  Write-Warning "code-graph freshness check skipped: $($_.Exception.Message)"
}

# (PS 5.1 reads this file as ANSI: an em dash inside a STRING decodes to a byte
# sequence containing a smart quote, which PowerShell honours as a string
# delimiter - keep string literals to ASCII; comments are safe.)
# U26 (2026-08-21): the instrument is a SIBLING OF THE MAIN CHECKOUT, so resolve
# the main working tree rather than counting directory hops. Three hops up from
# knowledge/depgraph-snapshots is right from the checkout and wrong from a git
# worktree under .claude/worktrees/<name> (it lands on .claude/worktrees/depgraph,
# which does not exist) — exactly the sessions CLAUDE.md sends to worktrees lost
# the ritual's last step. `git rev-parse --git-common-dir` is the SHARED .git,
# whose parent is the main checkout, and it answers the same from a worktree and
# from the checkout itself.
Push-Location $repo
$gitCommon = (& git rev-parse --path-format=absolute --git-common-dir).Trim()
Pop-Location
if ([string]::IsNullOrWhiteSpace($gitCommon)) { throw "cannot resolve the main working tree (git rev-parse --git-common-dir returned nothing) - is $repo a git checkout?" }
$mainTree = Split-Path -Parent $gitCommon
$depCandidate = Join-Path $mainTree "..\depgraph"
if (-not (Test-Path $depCandidate)) {
  throw "depgraph sibling checkout absent at $((Join-Path (Split-Path -Parent $mainTree) 'depgraph')) - config/dev-environment.yaml pins `repo: ../depgraph` beside the MAIN checkout ($mainTree). Clone it there; a worktree needs nothing of its own."
}
$dep  = (Resolve-Path $depCandidate).Path

# --- the configured instrument (config/dev-environment.yaml is the record) ----
# Read the pin BEFORE the probe, so the refusal below and the currency warning
# further down can both quote it and neither has to hardcode a SHA that goes
# stale — the 2026-08-04 bump found exactly that inside the refusal text.
$expCommit = $null
$expBranch = $null
try {
  $cfg = Get-Content (Join-Path $repo "config\dev-environment.yaml") -Raw
  # Scoped to the `depgraph:` block. A top-level key ends the block, so a
  # same-named key under another section can never be picked up by accident.
  if ($cfg -match '(?ms)^depgraph:[\r\n]+(.*?)(?=^\S|\Z)') {
    $block = $Matches[1]
    if ($block -match '(?m)^\s+expected_commit:\s*(\S+)') { $expCommit = $Matches[1] }
    if ($block -match '(?m)^\s+expected_branch:\s*(\S+)') { $expBranch = $Matches[1] }
  }
} catch {
  # Leave both null. The currency block below reports that it could not run,
  # rather than pretending the instrument was checked.
}
if ($expCommit) { $pinDesc = "$expBranch @ $expCommit" } else { $pinDesc = "unreadable" }

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
$depState      = Get-WorktreeState $dep
$depDirty      = $depState.dirty
$depUntracked  = $depState.untracked_present
# Rendered once, used in both the refusal and the drift warning below. Untracked
# paths are reported for the INSTRUMENT because depgraph runs out of this
# checkout, so an untracked module there can join the scan while belonging to no
# commit -- which is exactly the kind of thing the instrument header exists to
# make visible.
$depStateTxt = "$(if ($depDirty) { ' (tracked changes)' })$(if ($depUntracked) { ' (untracked present)' })"
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
               $depBranch @ $depCommit$depStateTxt
  missing    :
$($lines -join "`n")

  Expected branch/commit are recorded in config/dev-environment.yaml ($pinDesc).
  Fix: git -C "$dep" fetch && git -C "$dep" checkout main && git -C "$dep" pull.
  main has carried every capability since the fork was consolidated 2026-07-28;
  a checkout stranded on an older revision is the likely cause.

A snapshot written by a regressed scanner is worse than no snapshot: it is
plausible, diffable, and wrong (the 105-edge near-commit of 2026-07-28).
"@
}

# --- instrument CURRENCY: compare against the pin and WARN (ruled 2026-08-04) --
# The capability probe above cannot see a merely STALE sibling. A revision can
# pass every behavioural probe and still be behind, because new commits often
# add edge TYPES rather than capabilities — which is how 2026-08-04 happened:
# the laptop scanned on 5006567 while the desktop was already on 773fb1e, and no
# surface said so, leaving two snapshots that were not comparable by
# construction. `expected_commit` is the only record of the intended revision,
# so it is checked here.
#
# WARN, never refuse. A sibling legitimately AHEAD of the pin is the normal way
# a bump starts, so a hard failure would block the very work that fixes drift.
# The job of this block is to make drift visible in the run that would otherwise
# hide it; the meta header still records the instrument that actually ran, so
# the snapshot stays self-describing whichever way this goes.
if (-not $expCommit) {
  Write-Warning @"
instrument currency UNCHECKED — depgraph.expected_commit could not be read from
config/dev-environment.yaml. The scan proceeds and the meta header still records
the instrument that ran ($depBranch @ $depCommit), but nothing compared it to the
intended revision.
"@
} elseif (-not $depFull.StartsWith($expCommit)) {
  # Classify the drift, so the warning can say what to DO about it. Exit codes
  # only — no stderr redirection, which PowerShell 5.1 turns into error records.
  # Compare against $depFull, the revision captured above and written into the
  # meta header — NOT against a fresh `HEAD`. They are the same thing in a normal
  # run, but the recorded value is the one this snapshot is actually attributed
  # to, so it is the one the warning should reason about.
  $rel = "unknown"
  $null = git -C "$dep" rev-parse --verify --quiet "$expCommit^{commit}"
  if ($LASTEXITCODE -eq 0) {
    git -C "$dep" merge-base --is-ancestor $expCommit $depFull
    if ($LASTEXITCODE -eq 0) {
      $rel = "ahead"
    } else {
      git -C "$dep" merge-base --is-ancestor $depFull $expCommit
      if ($LASTEXITCODE -eq 0) { $rel = "behind" } else { $rel = "diverged" }
    }
  }
  # ASCII ONLY inside these double-quoted literals. This file is UTF-8 WITHOUT a
  # BOM, so PowerShell 5.1 decodes it as the ANSI codepage: a UTF-8 em dash
  # arrives as three CP1252 characters, the last of which is a smart quote that
  # PowerShell honours as a string delimiter. The string then ends early and the
  # whole script fails to parse. Em dashes in comments and here-strings are
  # harmless and appear elsewhere in this file; in a one-line "..." they are not.
  $advice = @{
    ahead    = "The sibling is AHEAD of the pin. Usually fine - this is how a bump starts - but the PIN is now the stale side: set depgraph.expected_commit to $depCommit once you are satisfied with this revision."
    behind   = "The sibling is BEHIND the pin, so this scan may not see what the pinned revision sees and will not be comparable to a snapshot taken on the pin. Fix: git -C `"$dep`" pull --ff-only"
    diverged = "The sibling and the pin have DIVERGED - neither is an ancestor of the other. That is the fork shape behind the 105-edge undercount of 2026-07-28; resolve it before trusting this snapshot."
    unknown  = "The pinned commit $expCommit is not in this checkout at all - unfetched, or rewritten away. Fix: git -C `"$dep`" fetch"
  }
  Write-Warning @"
instrument DRIFT — the depgraph checkout is not the revision config/dev-environment.yaml pins.

  checked out : $depBranch @ $depCommit$depStateTxt
  pinned      : $pinDesc
  relation    : $rel

$($advice[$rel])

Scanning anyway — this is a warning, not a refusal.
"@
} elseif ($expBranch -and $depBranch -ne $expBranch) {
  Write-Warning "instrument branch drift: checked out '$depBranch', config/dev-environment.yaml pins '$expBranch'. The commit matches, so this is most likely a detached HEAD or a local branch sitting at the same revision."
}

# --- git metadata (best-effort) ---------------------------------------------
Push-Location $repo
$commit   = (git rev-parse --short HEAD).Trim()
$full     = (git rev-parse HEAD).Trim()
$branch   = (git rev-parse --abbrev-ref HEAD).Trim()
$subject  = (git log -1 --format=%s).Trim()
try { $describe = (git describe --tags --always 2>$null).Trim() } catch { $describe = $commit }
if (-not $describe) { $describe = $commit }
$state     = Get-WorktreeState $repo
$dirty     = $state.dirty
$untracked = $state.untracked_present
$pr = $null
$m = [regex]::Match(((git log -20 --format="%s %b") -join "`n"), '(?:pull request |PR ?#|\(#)(\d+)')
if ($m.Success) { $pr = [int]$m.Groups[1].Value }
Pop-Location

# --- scan + name -------------------------------------------------------------
# DEFAULT = the whole repo. The -CodeOnly root list below is the LEGACY shape,
# retained only for comparison: it spans every top-level package since the Phase B
# relocate (ADR 0002-A-1, 2026-07-10) — drydocs (components) + drydocs_core +
# drydocs_remediation + drydocs_lineage + drydocs_deepdoc (G4/G9, 2026-07-11) +
# drydocs_api (U6, 2026-07-28 — invisible to every code-graph metric until the U2
# census). That last entry is the argument against the list: it had to be edited
# by hand when a package appeared, and a stale list silently under-scans. The
# tree scan takes the repo root and has no list to go stale.
if ($Tree) { $targets = @($repo);                       $tag = "" }
else       { $targets = @("$repo\drydocs","$repo\drydocs_core","$repo\drydocs_api","$repo\drydocs_remediation","$repo\drydocs_lineage","$repo\drydocs_deepdoc","$repo\tests"); $tag = "-code" }
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
  git         = [ordered]@{ commit=$commit; full=$full; branch=$branch; describe=$describe; subject=$subject; dirty=$dirty; untracked_present=$untracked; pr=$pr }
  # WHICH INSTRUMENT PRODUCED THIS (U7). Without it a scanner regression is
  # invisible in the artifact and shows up only as numbers nobody questions.
  depgraph    = [ordered]@{ commit=$depCommit; full=$depFull; branch=$depBranch; dirty=$depDirty; untracked_present=$depUntracked; version=$caps.version; capabilities=[ordered]@{ multi_root=[bool]$caps.multi_root; tree=[bool]$caps.tree; ts_imports=[bool]$caps.ts_imports } }
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
# Normalize to LF (Idea-129). $raw arrives CRLF from the depgraph tool while the
# meta line above is injected with a bare `n, so the file would land mixed-ending
# against an LF index. Safe as a byte replace: JSON forbids unescaped control
# characters inside strings, so every CRLF here is structural, and ConvertFrom-Json
# above has already proven the shape. filter_ignored.py rewrites this file on the
# -Tree path and normalizes too, but it early-returns when nothing is dropped, and
# a -CodeOnly run never calls it at all — so this is the only guarantee for both.
$new = $new -replace "`r`n", "`n"
[System.IO.File]::WriteAllText($out, $new, (New-Object System.Text.UTF8Encoding $false))

# --- drop git-ignored paths (U9) ---------------------------------------------
# depgraph excludes .git and .venv but knows nothing about .gitignore, so a
# whole-repo scan collects build caches — 384 .ruff_cache entries and var/ in the
# first all-files run, ~18% of the artifact. Those are not the project. Filtered
# HERE so the committed JSON, viewer.html and the graph all show the same thing.
if ($Tree) {
  & python (Join-Path $here "filter_ignored.py") $out $repo | Write-Host
  if ($LASTEXITCODE -ne 0) { throw "git-ignore filter failed; snapshot left unfiltered at $out" }
}
Remove-Item $tmp -ErrorAction SilentlyContinue

# --- ruled retention: newest all-files snapshot ONLY (SME 2026-08-02; U12) ----
# Runs AFTER the new snapshot is fully written and filtered, so a failed run can
# never delete the only good snapshot. Older snapshots stay recoverable from git
# history; the committed directory carries exactly one all-files snapshot so the
# ritual cannot re-grow a series. The pattern is anchored to the all-files shape:
# -CodeOnly files (<project>-code-*) and the retired drydocs1-* names never match.
if ($Tree) {
  $retain  = Split-Path $out -Leaf
  $pattern = ('^{0}-\d{{8}}(-\d{{4}})?\.json$' -f [regex]::Escape($Project))
  Get-ChildItem $here -File |
    Where-Object { $_.Name -match $pattern -and $_.Name -ne $retain } |
    ForEach-Object {
      Remove-Item $_.FullName -Force -Confirm:$false
      Write-Host "retention: removed $($_.Name) (newest-only ruling; recover from git history)" -ForegroundColor Yellow
    }
}

$prTxt = if ($pr) { ", PR#$pr" } else { "" }
Write-Host "wrote $(Split-Path $out -Leaf)  (commit $commit, branch $branch$prTxt)" -ForegroundColor Green

# --- debt-metrics ledger (U25): one append-only row per run, warn-only ---------
# Beside the snapshot just written: A3 top module + fan-in, A4 orphans, A5
# untested, live vs snapshot IMPORTS, the U22 verdict. No database = no row
# (the script says so); never a half-row, never a blocked snapshot. Retention
# above never touches the ledger (README, Housekeeping).
if ($Tree) {
  try {
    Push-Location $repo
    $prevEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"  # native stderr, see above
    & poetry run python (Join-Path $here "metrics_ledger.py") $out 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -match "debt-metrics" } | ForEach-Object {
      $c = if ($_ -match "appended row") { "Green" } else { "Yellow" }
      Write-Host $_ -ForegroundColor $c
    }
    $ErrorActionPreference = $prevEap
    Pop-Location
  } catch {
    Pop-Location -ErrorAction SilentlyContinue
    Write-Warning "debt-metrics row skipped: $($_.Exception.Message)"
  }
}
