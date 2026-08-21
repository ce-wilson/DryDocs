# Parse-Preproc.ps1 - the ksh pre-processor that PULLS from an API (curl)
#
# What this hop contributes to the chain:
#   the INGEST MODE evidence R13 says the name token cannot give you: a resolved command that
#   is an HTTP client call = api-pull. It names the three files it writes (the _original_
#   CSV, the .tok token file, the trailer-stripped .csv) - the same paths the _FW watchers
#   wait on, which is how Join-Hops.ps1 decides "internally fed". It also prints a bearer
#   token with set -x on; that is REDACTED before anything else and counted.
#
# Patterns:
#   ++ cat <fields file>
#   + <wrapper>.ksh -t <api-name> -u <yyyymmdd> -e <ENV> -i <account> -z '<https://host/path?query>' -d <drop dir> -s <scripts dir>
#   INFO: The output data file name is      : <file>
#   INFO: The output tok file name is       : <file>
#   INFO: The output data without trailer  file name is     : <file>
#   INFO: The API name is                   : <name>
#   INFO:Access Token receive step: eyJ...          <- redacted
#   curl: (92) HTTP/2 stream 0 was not closed cleanly: INTERNAL_ERROR   <- the failure signature, when present
#   ERROR: API data pull step failed
param(
    [Parameter(Mandatory)][string]$Path,
    [switch]$AsTable
)
. "$PSScriptRoot\Common.ps1"

$red = Get-Redacted -Lines (Get-UnwrappedLog -Path $Path)
$lines = $red.Lines
$r = New-Result -Kind 'PREPROC' -SourceFile $Path -Redactions $red.Count
Set-HeaderFields -Result $r -Lines $lines
$r.launcher_args = [ordered]@{ _ingest_mode = $null }

$echo = Get-LauncherEcho -Lines $lines
if ($null -eq $echo) {
    $r.skip_reasons += 'no_launcher_banner'
} else {
    $r.launcher = $echo.Launcher
    $a = Get-LauncherArgs -ArgString $echo.ArgString
    $a['_ingest_mode'] = $null
    $r.launcher_args = $a
    if ($a.Contains('t')) { $r.api_name = $a['t'] }
    if ($a.Contains('u')) { $r.business_date = $a['u'] }
    if ($a.Contains('i')) { $r.fid = $a['i'] }
    if ($a.Contains('z')) {
        # host only - the query string is field lists and filters, never needed and never kept
        if ($a['z'] -match '^(https?://[^/?\s]+)') { $r.api_endpoint_host = $Matches[1] }
        $r.launcher_args['z'] = '<query-string-dropped>'
    }
    if ($a.Contains('d')) { $r.landing_prefix = $a['d'] }
}

$apiName = Get-FirstMatch -Lines $lines -Pattern 'INFO:\s*The API name is\s*:\s*(\S+)'
if ($null -ne $apiName) { $r.api_name = $apiName }

$files = @()
foreach ($pat in @(
    'INFO:\s*The output data file name is\s*:\s*(\S+)',
    'INFO:\s*The output tok file name is\s*:\s*(\S+)',
    'INFO:\s*The output data without trailer\s+file name is\s*:\s*(\S+)')) {
    $f = Get-FirstMatch -Lines $lines -Pattern $pat
    if ($null -ne $f) { $files += $f }
}
if ($files.Count -gt 0) {
    # data_files are the full paths the watchers will see: drop dir + file name
    if ($null -ne $r.landing_prefix) { $r.data_files = @($files | ForEach-Object { ($r.landing_prefix.TrimEnd('/')) + '/' + $_ }) }
    else { $r.data_files = $files }
} else {
    $r.skip_reasons += 'no_output_files_named'
}

# ingest mode - DERIVED from the resolved command, never from the job name
$joined = $lines -join "`n"
if ($joined -match '(?i)\bcurl\b|Bearer token generation|Status Code from token api') { $r.launcher_args['_ingest_mode'] = 'api-pull' }
else { $r.launcher_args['_ingest_mode'] = 'unknown'; $r.skip_reasons += 'ingest_mode_unknown:no_http_client_evidence' }

# failure signature, when this run is the failing one
$curlErr = Get-FirstMatch -Lines $lines -Pattern '(curl: \(\d+\) .+)$'
if ($null -ne $curlErr) { $r.launcher_args['_curl_error'] = $curlErr }
$apiFail = Get-FirstMatch -Lines $lines -Pattern '(ERROR: API data pull step failed.*)$'
if ($null -ne $apiFail) { $r.launcher_args['_api_error'] = $apiFail }
if ($red.Count -gt 0) { $r.skip_reasons += "finding:bearer_token_printed_to_output(x$($red.Count))" }

Write-Result -Result $r -AsTable:$AsTable
