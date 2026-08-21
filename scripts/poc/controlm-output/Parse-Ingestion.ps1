# Parse-Ingestion.ps1 - dt-launcher "Identified 'INGESTION' Job"
#
# What this hop contributes to the chain:
#   CONSUMES the placement's provenanceGuid as -proId (the join back to the PLACEMENT hop);
#   names the flow (-dataflow AND the task-service request's "DataFlow" - two readings of
#   one value, recorded with whether they agree); the container image + digest; the compute
#   target (namespace alias) and profile; the app id from -seal AND spark.kubernetes.seal.
#
# Patterns:
#   + <launcher> -env .. -pipeline <GUID> -appName .. -alias aws-eks -seal <APP_ID> -dataflow <FLOW> -img .. -proId <GUID> -i -conf .. -compute ..
#   CommandLineParser: Identified 'INGESTION' Job
#   dt-launcher: ===============Running JAVA Ingestion====================
#   UserConfiguration: Image <img> mapped to <registry>/<repo>@sha256:<digest>
#   TaskService: Task service request: { "DataFlow": "...", "ComputeParams": { "spark.kubernetes.seal": N, "spark.namespace.alias": "..." } }
#   (the panel often CUTS the JSON before it closes - task_request_closed says so)
param(
    [Parameter(Mandatory)][string]$Path,
    [switch]$AsTable
)
. "$PSScriptRoot\Common.ps1"

$red = Get-Redacted -Lines (Get-UnwrappedLog -Path $Path)
$lines = $red.Lines
$r = New-Result -Kind 'INGESTION' -SourceFile $Path -Redactions $red.Count
Set-HeaderFields -Result $r -Lines $lines
$a = Set-LauncherFields -Result $r -Lines $lines

$task = Get-TaskServiceRequest -Lines $lines
if ($null -ne $task) {
    $r.task_request_closed = $task.Closed
    if (-not $task.Closed) { $r.skip_reasons += 'truncated_json' }
    $k = $task.Keys
    # two readings of the flow name - agree?
    if ($k.Contains('DataFlow')) {
        if ($null -eq $r.dataflow) { $r.dataflow = $k['DataFlow'] }
        elseif ($r.dataflow -ne $k['DataFlow']) { $r.skip_reasons += "dataflow_mismatch:cmdline=$($r.dataflow);task=$($k['DataFlow'])" }
    }
    if ($k.Contains('spark.kubernetes.seal')) {
        if ($null -eq $r.app_id) { $r.app_id = $k['spark.kubernetes.seal'] }
        elseif ("$($r.app_id)" -ne "$($k['spark.kubernetes.seal'])") { $r.skip_reasons += 'app_id_mismatch_cmdline_vs_task' }
    }
    if ($k.Contains('spark.kubernetes.container.image') -and $null -eq $r.image_digest) {
        if ($k['spark.kubernetes.container.image'] -match 'sha256:([0-9a-f]{64})') { $r.image_digest = "sha256:$($Matches[1])" }
    }
    $r.compute_target = Get-ComputeTarget -Kind 'INGESTION' -TaskKeys $k -LauncherArgs $a
} else {
    $r.skip_reasons += 'no_task_service_request'
    $r.compute_target = Get-ComputeTarget -Kind 'INGESTION' -TaskKeys $null -LauncherArgs $a
}

if ($null -eq $r.pro_id_in) { $r.skip_reasons += 'no_pro_id_on_command_line' }

$sub = Get-FirstMatch -Lines $lines -Pattern 'TaskService: Submitting job to: (\S+)'
if ($null -ne $sub) { $r.submission_url = ($sub -replace '\?.*$', '') }
$r.submission_cluster = Get-FirstMatch -Lines $lines -Pattern "Submission response: .*'cluster': '([^']+)'"
$r.submission_job_id = Get-FirstMatch -Lines $lines -Pattern "Submission response: .*'jobID': '([^']+)'"

Write-Result -Result $r -AsTable:$AsTable
