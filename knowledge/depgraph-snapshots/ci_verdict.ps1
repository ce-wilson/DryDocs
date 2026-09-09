<#
  ci_verdict.ps1 — the CI verdict as a pure function, dot-sourced by snapshot.ps1.

  Get-CiVerdict maps (runs, head, gh exit code, branch) to ONE line and a colour.
  It lives in its own file so pytest can drive it without a network or a git
  remote: tests/unit/test_ci_verdict.py dot-sources this file under pwsh or
  powershell (skipping, by name, where neither exists) and feeds it the five
  fixtures U27 names - green-at-head, failed-at-head with an older success in
  the list, in-progress-at-head, no-run-yet-for-head, and EMPTY runs. The
  design comment below claimed this function was "exercisable without a
  network" from the day it was written (Idea-111) and nothing exercised it
  until U27 (2026-09-08); the 2026-08-20 false GREEN (U24) is the case the
  EMPTY fixture would have caught.

  Nothing in here reads git, gh, or the tree. The caller in snapshot.ps1 owns
  the measurement (which branch, which sha, what gh returned); this file owns
  only the words. Keep it that way, or the tests stop meaning anything.
#>

# --- CI gate check (Idea-111) — the verdict -----------------------------------
# The verdict is a pure function of (runs, head) so every branch is exercisable
# without a network — the reporting half is the part that rots, and a check that
# only ever prints GREEN on the machine that wrote it is how this got missed.
# $Branch (U27, 2026-09-08) is the branch the runs were listed for; every message
# that used to say "main" now names it, because the caller no longer asks about
# main by literal - it asks about the branch HEAD is on.
function Get-CiVerdict {
  param($Runs, [string]$Head, [int]$GhExit = 0, [string]$Branch = "main")
  $short = $Head.Substring(0, 7)
  # Two empty-list cases, two different facts (J76, 2026-09-08). The old single
  # message guessed a cause - "gh not authenticated?" - and on a remote whose
  # workflow is registered but has NEVER executed (zero runs, ever: the company
  # remote at its 2026-09-08 close-out) it named a cause that was false while the
  # real one went unreported. Report the measurement; list the causes; pick none.
  if ($GhExit -ne 0) {
    return @{ Color = "DarkGray"; Text = ("ci: gh run list exited {0} - the run list could not be read (authentication, network, or no GitHub remote; 'gh auth status' tells which) - check skipped" -f $GhExit) }
  }
  if (@($Runs).Count -eq 0) {
    return @{ Color = "Yellow"; Text = ("ci: UNVERIFIED at HEAD {0} - the remote reports ZERO runs on {1}. The workflow has never executed for that branch (a fresh remote, a workflow that is registered but has never triggered, or a branch never pushed); nothing pushed to it has been checked." -f $short, $Branch) }
  }
  # J78 (2026-09-06): three outcomes, not two. The sha match added after
  # Idea-111 catches STALE GREEN - a green run that belongs to an older
  # commit. A CANCELLED run (GitHub cancels a push run when the next push
  # supersedes it) has a MATCHING sha and NO result, so the sha match sees
  # nothing wrong and the old two-way split filed it under RED - which it is
  # not. Different failure, same channel: the commit was never checked, and
  # the next push that does run will attribute any failure to whoever made
  # it. So no verdict is reported AS no verdict - UNVERIFIED, by name - and
  # a MISSING run for HEAD is the same state whatever the reason (not yet
  # scheduled, workflow skipped, run deleted). Still warn-only.
  $unverified = "ci: UNVERIFIED at HEAD {0} - {1}. This commit has not been checked; the next push that runs will attribute its failure to whoever made it."
  $mine = @($Runs | Where-Object { $_.headSha -eq $Head })
  if ($mine.Count -eq 0) {
    $newest = @($Runs)[0]
    $newestState = [string]$newest.conclusion
    if ([string]::IsNullOrEmpty($newestState)) { $newestState = [string]$newest.status }
    return @{ Color = "Yellow"; Text = ($unverified -f $short, ("no run exists for it; newest on {0} is {1} ({2})" -f `
      $Branch, $newestState, [string]$newest.displayTitle)) }
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
  if ($conclusion -eq "cancelled" -or $conclusion -eq "skipped" -or [string]::IsNullOrEmpty($conclusion)) {
    $reason = if ([string]::IsNullOrEmpty($conclusion)) { "the run completed with no conclusion" } else { "the run was " + $conclusion }
    return @{ Color = "Yellow"; Text = ($unverified -f $short, $reason) }
  }
  return @{ Color = "Red"; Text = ("ci: {0} AT HEAD {1} - {2} is RED. Run 'gh run view --log-failed' before you stop." -f `
    $conclusion.ToUpper(), $short, $Branch) }
}
