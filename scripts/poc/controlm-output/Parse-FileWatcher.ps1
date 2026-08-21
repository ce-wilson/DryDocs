# Parse-FileWatcher.ps1 - Control-M ctmfw (the _FW jobs)
#
# What this hop contributes to the chain:
#   the WATCHED PATH and the result (exists / transfer completed / size). Joined against the
#   PREPROC hop's output files it answers R13's second question: is this watcher INTERNALLY
#   FED (watched path == a path a same-folder predecessor wrote)? The watcher cannot tell you
#   that itself - Join-Hops.ps1 does - so here it is only recorded.
#
# Patterns:
#   + ctmfw <path> CREATE <min-size> <interval> <cycles> <detect-stable> <timeout> N NOW 0 NO_MIN_AGE NO_MAX_AGE
#   <MMDD HH:MM:SS> : File '<path>' exists, it's current size is <n> bytes . id=1.
#   <MMDD HH:MM:SS> : File transfer was completed. The size of file '<path>' is <n> bytes. id=1. Modified <dd/mm/yyyy hh:mm>
param(
    [Parameter(Mandatory)][string]$Path,
    [switch]$AsTable
)
. "$PSScriptRoot\Common.ps1"

$red = Get-Redacted -Lines (Get-UnwrappedLog -Path $Path)
$lines = $red.Lines
$r = New-Result -Kind 'FILEWATCHER' -SourceFile $Path -Redactions $red.Count
Set-HeaderFields -Result $r -Lines $lines

$echo = Get-LauncherEcho -Lines $lines
if ($null -eq $echo) {
    $r.skip_reasons += 'no_launcher_banner'
} else {
    $r.launcher = $echo.Launcher
    $a = Get-LauncherArgs -ArgString $echo.ArgString
    $r.launcher_args = $a
    if ($a.Contains('_positional') -and $a['_positional'].Count -ge 2) {
        $p = $a['_positional']
        $r.watched_path = $p[0]
        # ctmfw positional contract: <path> <mode> <min-size> <interval> <cycles> <stable-cycles> <timeout> ...
        $r.launcher_args['_mode'] = $p[1]
        if ($p.Count -ge 3) { $r.launcher_args['_min_size'] = $p[2] }
        if ($p.Count -ge 4) { $r.launcher_args['_interval_s'] = $p[3] }
        if ($p.Count -ge 7) { $r.launcher_args['_timeout'] = $p[6] }
    }
}

$done = Get-FirstMatch -Lines $lines -Pattern "File transfer was completed\. The size of file '([^']+)' is (\d+) bytes"
if ($null -ne $done) {
    $r.watched_result = 'transfer_completed'
    foreach ($l in $lines) {
        if ($l -match "The size of file '[^']+' is (\d+) bytes.*Modified (.+)$") {
            $r.launcher_args['_final_size_bytes'] = [long]$Matches[1]
            $r.launcher_args['_modified'] = $Matches[2].Trim()
            break
        }
    }
} else {
    $exists = Get-FirstMatch -Lines $lines -Pattern "File '([^']+)' exists"
    if ($null -ne $exists) { $r.watched_result = 'exists_not_confirmed_stable'; $r.skip_reasons += 'watch_not_completed' }
    else { $r.watched_result = 'no_file_event'; $r.skip_reasons += 'watch_no_event' }
}

# Token vs data watcher: the _TOK_ / .tok convention
if ($null -ne $r.watched_path) {
    if ($r.watched_path -match '\.tok$') { $r.launcher_args['_watch_role'] = 'token' } else { $r.launcher_args['_watch_role'] = 'data' }
    $r.data_files = @($r.watched_path)
}

Write-Result -Result $r -AsTable:$AsTable
