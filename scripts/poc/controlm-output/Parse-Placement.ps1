# Parse-Placement.ps1 - dt-launcher "Identified 'PLACEMENT' Job"
#
# What this hop contributes to the chain:
#   PRODUCES the provenanceGuid every later hop carries as -proId; names the dat/tok files it
#   placed; lists the landing targets (e.g. MERCURY_S3 / AWS_S3) and the S3-style key prefix
#   "<APP_ID>/raw/<dataflow>/<provenanceGuid>/<file>" once the AWS target completes.
#
# Patterns (one each, in log order):
#   + <launcher> -env .. -dataset <GUID> -version <v> -pipeline <GUID> -bd .. -od .. -datFile .. -tokFile .. -conf ..
#   CommandLineParser: Identified 'PLACEMENT' Job
#   PlacementService: Got placement response: {'provenanceGuid': '<GUID>', ... 'rowCount': N}
#   PlacementService: Got status for: ['MERCURY_S3', 'AWS_S3']
#   ... 'targetLocation': '<APP_ID>/raw/<dataflow>/<GUID>/<file>' ...
#   PlacementService: Placement for provenance id <GUID> is complete!
param(
    [Parameter(Mandatory)][string]$Path,
    [switch]$AsTable
)
. "$PSScriptRoot\Common.ps1"

$red = Get-Redacted -Lines (Get-UnwrappedLog -Path $Path)
$lines = $red.Lines
$r = New-Result -Kind 'PLACEMENT' -SourceFile $Path -Redactions $red.Count
Set-HeaderFields -Result $r -Lines $lines
$a = Set-LauncherFields -Result $r -Lines $lines

if ($null -ne $a) {
    $files = @()
    foreach ($k in @('datFile', 'tokFile')) { if ($a.Contains($k)) { $files += $a[$k] } }
    if ($files.Count -gt 0) { $r.data_files = $files }
}

$r.provenance_guid = Get-FirstMatch -Lines $lines -Pattern "placement response: \{'provenanceGuid': '([0-9a-f-]{36})'"
if ($null -eq $r.provenance_guid) {
    $r.provenance_guid = Get-FirstMatch -Lines $lines -Pattern 'ProvenanceID=([0-9a-f-]{36})'
}
$rc = Get-FirstMatch -Lines $lines -Pattern "'rowCount': (\d+)"
if ($null -ne $rc) { $r.launcher_args['_rowCount'] = [int]$rc }

$targets = Get-FirstMatch -Lines $lines -Pattern "Got status for: \[(.+?)\]"
if ($null -ne $targets) {
    $r.landing_targets = @([regex]::Matches($targets, "'([^']+)'") | ForEach-Object { $_.Groups[1].Value })
}
# Landing prefix = the directory part of the first slash-bearing targetLocation
$loc = Get-AllMatches -Lines $lines -Pattern "'targetLocation': '([^']*/[^']*)'" | Select-Object -First 1
if ($null -ne $loc) {
    $r.landing_prefix = ($loc -replace '/[^/]+$', '')
}
$complete = Get-FirstMatch -Lines $lines -Pattern 'Placement for provenance id ([0-9a-f-]{36}) is complete'
if ($null -eq $complete) { $r.skip_reasons += 'placement_not_confirmed_complete' }
if ($null -eq $r.provenance_guid) { $r.skip_reasons += 'no_provenance_guid' }

# Hop-consistency: the GUID in the URL must be the GUID in the response
$urlGuid = Get-FirstMatch -Lines $lines -Pattern 'pipelineId=([0-9a-f-]{36})'
if ($null -ne $urlGuid -and $null -ne $r.pipeline_id -and $urlGuid -ne $r.pipeline_id) { $r.skip_reasons += 'guid_mismatch_vs_cmdline' }

Write-Result -Result $r -AsTable:$AsTable
