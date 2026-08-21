# Parse-Provision.ps1 - dt-launcher "Identified 'PROVISION' Job. Provision jobs execute on GKP not EKS!"
#
# What this hop contributes to the chain:
#   the COMPUTE TARGET switch stated by the launcher itself (GKP, not EKS); a smaller compute
#   profile with GKP-specific keys; the v2 task-service submission URL and its response
#   (jobID, httpStatus, cluster). It carries -t instead of -i, and -bd can equal -od.
#
# Patterns:
#   + <launcher> -env .. -pipeline <GUID> -appName .. -seal <APP_ID> -dataflow <FLOW> -img .. -t -compute <..GKP..> -conf ..
#   CommandLineParser: Identified 'PROVISION' Job. Provision jobs execute on GKP not EKS!
#   TaskService: Task service request: { ... "spark.gkp.sophia.fid": "...", "spark.kubernetes.seal": N ... }
#   TaskService: Submitting job to: https://<task-service>/.../v2/clusters/launch/pipelineId=<GUID>
#   TaskService: Submission response: {'pipelineID': '<GUID>', 'jobID': '<n>', ..., 'httpStatus': 'CREATED', 'cluster': '<cluster>'}
param(
    [Parameter(Mandatory)][string]$Path,
    [switch]$AsTable
)
. "$PSScriptRoot\Common.ps1"

$red = Get-Redacted -Lines (Get-UnwrappedLog -Path $Path)
$lines = $red.Lines
$r = New-Result -Kind 'PROVISION' -SourceFile $Path -Redactions $red.Count
Set-HeaderFields -Result $r -Lines $lines
$a = Set-LauncherFields -Result $r -Lines $lines

$r.compute_target = 'GKP'   # the launcher's own assertion on the kind line
$kindLine = Get-FirstMatch -Lines $lines -Pattern "Identified 'PROVISION' Job\.\s*(.+)$"
if ($null -ne $kindLine) { $r.launcher_args['_kind_note'] = $kindLine }

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
    if ($k.Contains('spark.gkp.sophia.fid')) { $r.launcher_args['_gkp_fid'] = $k['spark.gkp.sophia.fid'] }
} else {
    $r.skip_reasons += 'no_task_service_request'
}

$sub = Get-FirstMatch -Lines $lines -Pattern 'TaskService: Submitting job to: (\S+)'
if ($null -ne $sub) {
    $r.submission_url = $sub
    $urlGuid = Get-FirstMatch -Lines @($sub) -Pattern 'pipelineId=([0-9a-f-]{36})'
    if ($null -ne $urlGuid -and $null -ne $r.pipeline_id -and $urlGuid -ne $r.pipeline_id) { $r.skip_reasons += 'guid_mismatch_vs_cmdline' }
}
$r.submission_cluster = Get-FirstMatch -Lines $lines -Pattern "Submission response: .*'cluster': '([^']+)'"
$r.submission_job_id  = Get-FirstMatch -Lines $lines -Pattern "Submission response: .*'jobID': '([^']+)'"
$http = Get-FirstMatch -Lines $lines -Pattern "Submission response: .*'httpStatus': '([^']+)'"
if ($null -ne $http) { $r.launcher_args['_httpStatus'] = $http }
if ($null -eq $r.submission_job_id) { $r.skip_reasons += 'no_submission_response' }

Write-Result -Result $r -AsTable:$AsTable
