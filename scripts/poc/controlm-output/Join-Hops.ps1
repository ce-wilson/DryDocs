# Join-Hops.ps1 - read a folder of parsed .json results and print the chain between hops.
#
#   .\Join-Hops.ps1 -JsonDir <dir produced by Parse-ControlMOutput.ps1 -OutDir>
#
# This is the part the per-kind parsers deliberately do NOT do: each hop only records what
# its own log says; the joins below are where the data-flow record (gate data-flow-overview
# section 2) gets its DERIVED fields. Every join key is printed so a wrong join is visible.
#
#   PREPROC  --data_files-->  FILEWATCHER.watched_path        => internally fed?  (R13 second consequence)
#   PREPROC  --data_files-->  PLACEMENT.data_files (-datFile / -tokFile)
#   PLACEMENT.provenance_guid --> INGESTION.pro_id_in          => the provenance chain
#   INGESTION/TRANSFORM/PROVISION.dataflow                     => one flow, or siblings
#   TRANSFORM.provenance_warning                               => chain breaks here
#   every hop.pipeline_id                                      => the CMDLINE lineage join key
param(
    [Parameter(Mandatory)][string]$JsonDir
)
Set-StrictMode -Version 2.0

$hops = Get-ChildItem -LiteralPath $JsonDir -Filter *.json | ForEach-Object {
    Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
}
$hops = @($hops)
if ($hops.Count -eq 0) { Write-Error "no .json in $JsonDir"; exit 1 }

function Val($obj, $name) {
    if ($null -eq $obj) { return $null }
    $p = $obj.PSObject.Properties[$name]
    if ($null -eq $p) { return $null }
    return $p.Value
}
function Show($label, $value) {
    if ($null -eq $value -or "$value" -eq '') { $value = '-' }
    "{0,-26} {1}" -f $label, $value
}

Write-Host "`n== HOPS (by launcher_kind) ==" -ForegroundColor Cyan
$hops | Sort-Object { @('PREPROC','FILEWATCHER','PLACEMENT','INGESTION','TRANSFORM','PROVISION','UNKNOWN').IndexOf($_.launcher_kind) } |
    ForEach-Object {
        [pscustomobject]@{
            kind        = $_.launcher_kind
            job         = (Val $_ 'job_name')
            pipeline_id = (Val $_ 'pipeline_id')
            dataflow    = (Val $_ 'dataflow')
            app_id      = (Val $_ 'app_id')
            pro_id_in   = (Val $_ 'pro_id_in')
            prov_guid   = (Val $_ 'provenance_guid')
            compute     = (Val $_ 'compute_target')
            skips       = ((Val $_ 'skip_reasons') -join ', ')
        }
    } | Format-Table -AutoSize -Wrap

$pre  = @($hops | Where-Object { $_.launcher_kind -eq 'PREPROC' })
$fws  = @($hops | Where-Object { $_.launcher_kind -eq 'FILEWATCHER' })
$plc  = @($hops | Where-Object { $_.launcher_kind -eq 'PLACEMENT' })
$ing  = @($hops | Where-Object { $_.launcher_kind -eq 'INGESTION' })
$trf  = @($hops | Where-Object { $_.launcher_kind -eq 'TRANSFORM' })
$prv  = @($hops | Where-Object { $_.launcher_kind -eq 'PROVISION' })

Write-Host "== JOIN 1: watcher fed by a predecessor? (R13 second consequence) ==" -ForegroundColor Cyan
$written = @()
foreach ($p in $pre) { $written += @(Val $p 'data_files') }
foreach ($w in $fws) {
    $wp = Val $w 'watched_path'
    $fed = $false
    foreach ($f in $written) { if ($null -ne $f -and $null -ne $wp -and $f -ieq $wp) { $fed = $true } }
    $verdict = 'NOT matched to any predecessor write (external push, or the writer log is missing)'
    if ($fed) { $verdict = 'INTERNALLY FED -> load_bearing=false PROPOSED (SME rules; unruled until then)' }
    Show "watcher $(Val $w 'job_name')" $wp
    Show "  result" (Val $w 'watched_result')
    Show "  verdict" $verdict
}
if ($fws.Count -eq 0) { "  (no FILEWATCHER hop)" }

Write-Host "`n== JOIN 2: pre-processor files -> placement -datFile/-tokFile ==" -ForegroundColor Cyan
foreach ($pl in $plc) {
    foreach ($f in @(Val $pl 'data_files')) {
        $hit = $false
        foreach ($w in $written) { if ($null -ne $w -and $w -ieq $f) { $hit = $true } }
        $tag = 'no matching pre-processor output'
        if ($hit) { $tag = 'written by PREPROC' }
        Show "  placement file" "$f  [$tag]"
    }
}
if ($plc.Count -eq 0) { "  (no PLACEMENT hop)" }

Write-Host "`n== JOIN 3: provenance chain (placement provenanceGuid -> ingestion -proId) ==" -ForegroundColor Cyan
foreach ($pl in $plc) {
    $g = Val $pl 'provenance_guid'
    Show "placement produced" $g
    Show "  landing_prefix" (Val $pl 'landing_prefix')
    foreach ($i in $ing) {
        $proIn = Val $i 'pro_id_in'
        $ok = 'MISMATCH'
        if ($null -ne $g -and $proIn -eq $g) { $ok = 'MATCH' }
        Show "  ingestion $(Val $i 'job_name')" "-proId $proIn  [$ok]"
    }
}
foreach ($t in $trf) {
    $w = Val $t 'provenance_warning'
    if ($null -ne $w) { Show "transform $(Val $t 'job_name')" "CHAIN BREAKS: $w" }
    else { Show "transform $(Val $t 'job_name')" "-proId $(Val $t 'pro_id_in')" }
}
foreach ($p in $prv) { Show "provision $(Val $p 'job_name')" "-proId $(Val $p 'pro_id_in')  (GKP; submission $(Val $p 'submission_job_id') on $(Val $p 'submission_cluster'))" }

Write-Host "`n== JOIN 4: flow identity across hops (%%DATAFLOW as the launcher names it) ==" -ForegroundColor Cyan
$hops | Where-Object { $null -ne (Val $_ 'dataflow') } | Group-Object dataflow | ForEach-Object {
    $apps = ($_.Group | ForEach-Object { Val $_ 'app_id' } | Where-Object { $_ } | Sort-Object -Unique) -join ','
    Show "  $($_.Name)" ("{0} hop(s): {1}   app_id(s): {2}" -f $_.Count, (($_.Group | ForEach-Object { $_.launcher_kind }) -join '+'), $apps)
}
"  note: sibling flow names under different app_ids are the producer/consumer split; gate section A rules the key."

Write-Host "`n== JOIN 5: ingest mode (derived, never from the name token) ==" -ForegroundColor Cyan
foreach ($p in $pre) {
    $mode = Val (Val $p 'launcher_args') '_ingest_mode'
    Show "  $(Val $p 'job_name')" "$mode   via $(Val $p 'launcher')  host $(Val $p 'api_endpoint_host')"
}
if ($pre.Count -eq 0) { "  unknown (no PREPROC hop log supplied) - 'unknown' is a value, not a default" }

Write-Host "`n== FINDINGS / SKIPS ==" -ForegroundColor Cyan
foreach ($h in $hops) {
    foreach ($s in @(Val $h 'skip_reasons')) { Show "  $($h.launcher_kind)" $s }
    $red = Val $h 'redactions'
    if ($red -gt 0) { Show "  $($h.launcher_kind)" "redactions=$red (a secret was printed to job output)" }
}
