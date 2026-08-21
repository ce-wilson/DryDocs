# Parse-Transform.ps1 - dt-launcher "Identified 'TRANSFORM' Job"
#
# Same launcher and argument shape as INGESTION, two differences that matter to the chain:
#   * it usually carries NO -proId, and the launcher says so:
#       [WARNING] dt-launcher: No provenanceId is provided!
#     -> provenance_warning is set; the provenance chain BREAKS here and the record says so.
#   * the task-service request names the flow the transform WRITES (its own -dataflow), which
#     is typically a sibling of the ingestion flow (e.g. <X>_PARTY_DATA -> <X>_PARTY_INTM).
#
# Patterns:
#   + <launcher> -env .. -pipeline <GUID> -appName .. -alias .. -seal <APP_ID> -dataflow <FLOW> -img .. -i -conf .. -compute ..
#   CommandLineParser: Identified 'TRANSFORM' Job
#   dt-launcher: No provenanceId is provided!
#   dt-launcher: ===============Running JAVA Transformation====================
#   TaskService: Task service request: { ... }
param(
    [Parameter(Mandatory)][string]$Path,
    [switch]$AsTable
)
. "$PSScriptRoot\Common.ps1"

$red = Get-Redacted -Lines (Get-UnwrappedLog -Path $Path)
$lines = $red.Lines
$r = New-Result -Kind 'TRANSFORM' -SourceFile $Path -Redactions $red.Count
Set-HeaderFields -Result $r -Lines $lines
$a = Set-LauncherFields -Result $r -Lines $lines

$w = Get-FirstMatch -Lines $lines -Pattern '\[WARNING\] dt-launcher: (No provenanceId is provided!?)'
if ($null -ne $w) { $r.provenance_warning = $w }

$task = Get-TaskServiceRequest -Lines $lines
if ($null -ne $task) {
    $r.task_request_closed = $task.Closed
    if (-not $task.Closed) { $r.skip_reasons += 'truncated_json' }
    $k = $task.Keys
    if ($k.Contains('DataFlow')) {
        if ($null -eq $r.dataflow) { $r.dataflow = $k['DataFlow'] }
        elseif ($r.dataflow -ne $k['DataFlow']) { $r.skip_reasons += "dataflow_mismatch:cmdline=$($r.dataflow);task=$($k['DataFlow'])" }
    }
    if ($k.Contains('spark.kubernetes.seal') -and $null -eq $r.app_id) { $r.app_id = $k['spark.kubernetes.seal'] }
    if ($k.Contains('spark.kubernetes.container.image') -and $null -eq $r.image_digest) {
        if ($k['spark.kubernetes.container.image'] -match 'sha256:([0-9a-f]{64})') { $r.image_digest = "sha256:$($Matches[1])" }
    }
    $r.compute_target = Get-ComputeTarget -Kind 'TRANSFORM' -TaskKeys $k -LauncherArgs $a
    # Finding, not a field: a production transform whose appname / alias literally say "test"
    foreach ($probe in @('spark.kubernetes.appname', 'spark.namespace.alias')) {
        if ($k.Contains($probe) -and $k[$probe] -eq 'test') { $r.skip_reasons += "finding:${probe}=test" }
    }
} else {
    $r.skip_reasons += 'no_task_service_request'
    $r.compute_target = Get-ComputeTarget -Kind 'TRANSFORM' -TaskKeys $null -LauncherArgs $a
}

$sub = Get-FirstMatch -Lines $lines -Pattern 'TaskService: Submitting job to: (\S+)'
if ($null -ne $sub) { $r.submission_url = ($sub -replace '\?.*$', '') }
$r.submission_cluster = Get-FirstMatch -Lines $lines -Pattern "Submission response: .*'cluster': '([^']+)'"
$r.submission_job_id = Get-FirstMatch -Lines $lines -Pattern "Submission response: .*'jobID': '([^']+)'"

Write-Result -Result $r -AsTable:$AsTable
