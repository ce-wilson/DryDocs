# Common.ps1 - shared helpers for the Control-M Output-tab PoC parsers (MM7 framing).
# Dot-source from every Parse-*.ps1:   . "$PSScriptRoot\Common.ps1"
# Windows PowerShell 5.1 compatible: no ternary, no ??, no -AsHashtable.
#
# What lives here and why:
#   Get-UnwrappedLog   the Control-M Output panel soft-wraps long lines with a trailing "\";
#                      a log copied out of the client keeps those breaks. Join them FIRST or
#                      every regex below sees half a URL.
#   Get-LauncherArgs   "-key value" / bare "-flag" pairs from the "+ <launcher> ..." echo line.
#   Get-LogKind        the one line that names the job kind, or the launcher shape when the
#                      kind line is absent (ctmfw, ksh + curl).
#   Get-Redacted       bearer tokens / access tokens are REDACTED before any field is built
#                      and the count is reported (MM7 acceptance: token_redacted).
#   New-Result         the one output shape every parser returns.

Set-StrictMode -Version 2.0

function Get-UnwrappedLog {
    param([Parameter(Mandatory)][string]$Path)
    $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    # A trailing backslash immediately before a line break is the panel's wrap marker,
    # not content. Join the physical lines back into one logical line.
    $joined = [regex]::Replace($raw, '\\\r?\n', '')
    return ($joined -split '\r?\n')
}

function Get-Redacted {
    # Returns @{ Lines = <string[]>; Count = <int> }
    param([Parameter(Mandatory)][AllowEmptyString()][string[]]$Lines)
    $count = 0
    $out = foreach ($l in $Lines) {
        $r = $l
        # JWT-shaped bearer tokens (three base64url segments) and "Access Token ... : <blob>"
        $r2 = [regex]::Replace($r, 'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}(\.[A-Za-z0-9_-]{10,})?', '<REDACTED-JWT>')
        if ($r2 -ne $r) { $count++ ; $r = $r2 }
        $r2 = [regex]::Replace($r, '(?i)(Access Token receive step\s*:\s*)(\S.*)$', '$1<REDACTED>')
        if ($r2 -ne $r) { $count++ ; $r = $r2 }
        $r2 = [regex]::Replace($r, '(?i)(Authorization:\s*Bearer\s+)\S+', '$1<REDACTED>')
        if ($r2 -ne $r) { $count++ ; $r = $r2 }
        $r
    }
    return @{ Lines = @($out); Count = $count }
}

function Get-LauncherEcho {
    # The "+ /path/to/launcher args..." line (ksh set -x echo). First one wins.
    param([Parameter(Mandatory)][AllowEmptyString()][string[]]$Lines)
    foreach ($l in $Lines) {
        if ($l -match '^\+\s+(\S+)(.*)$') {
            return @{ Launcher = $Matches[1]; ArgString = $Matches[2].Trim(); Line = $l }
        }
    }
    return $null
}

function Get-LauncherArgs {
    # Tokenizes "-key value -flag -key2 'quoted value'" into an ordered hashtable.
    # A key followed by another "-key" (or end) is a bare flag = $true.
    param([Parameter(Mandatory)][string]$ArgString)
    $tokens = [regex]::Matches($ArgString, "'[^']*'|""[^""]*""|\S+") | ForEach-Object { $_.Value.Trim("'", '"') }
    $parsed = [ordered]@{}
    $i = 0
    while ($i -lt $tokens.Count) {
        $t = $tokens[$i]
        if ($t -match '^-(\w+)$') {
            $key = $Matches[1]
            $next = $null
            if ($i + 1 -lt $tokens.Count) { $next = $tokens[$i + 1] }
            if ($null -ne $next -and $next -notmatch '^-\w+$') {
                $parsed[$key] = $next
                $i += 2
            } else {
                $parsed[$key] = $true
                $i += 1
            }
        } else {
            # positional (ctmfw uses these) - keep them under _positional
            if (-not $parsed.Contains('_positional')) { $parsed['_positional'] = @() }
            $parsed['_positional'] += $t
            $i += 1
        }
    }
    return $parsed
}

function Get-LogKind {
    # PLACEMENT | INGESTION | TRANSFORM | PROVISION from the launcher's own assertion;
    # FILEWATCHER for ctmfw; PREPROC for the ksh/curl API-pull wrapper; else UNKNOWN.
    param([Parameter(Mandatory)][AllowEmptyString()][string[]]$Lines)
    foreach ($l in $Lines) {
        if ($l -match "CommandLineParser: Identified '([A-Z]+)' Job") { return $Matches[1] }
    }
    $echo = Get-LauncherEcho -Lines $Lines
    if ($null -ne $echo) {
        if ($echo.Launcher -match '(^|/)ctmfw$') { return 'FILEWATCHER' }
        if ($echo.Launcher -match '\.ksh$' -and ($Lines -join "`n") -match '(?i)curl|Bearer token|The API name is') { return 'PREPROC' }
    }
    return 'UNKNOWN'
}

function Get-FirstMatch {
    # First capture group of the first line matching $Pattern, or $null.
    param([Parameter(Mandatory)][AllowEmptyString()][string[]]$Lines, [Parameter(Mandatory)][string]$Pattern)
    foreach ($l in $Lines) {
        if ($l -match $Pattern) { return $Matches[1] }
    }
    return $null
}

function Get-AllMatches {
    # Every capture-1 across all lines for $Pattern (distinct, order kept).
    param([Parameter(Mandatory)][AllowEmptyString()][string[]]$Lines, [Parameter(Mandatory)][string]$Pattern)
    $seen = New-Object System.Collections.Generic.List[string]
    foreach ($l in $Lines) {
        foreach ($m in [regex]::Matches($l, $Pattern)) {
            $v = $m.Groups[1].Value
            if (-not $seen.Contains($v)) { [void]$seen.Add($v) }
        }
    }
    return @($seen)
}

function Get-TaskServiceRequest {
    # The launcher prints "TaskService: Task service request: {" then a pretty-printed JSON
    # block. The panel may CUT it before the closing brace - so parse the keys we need
    # line by line instead of ConvertFrom-Json, and report whether the block closed.
    param([Parameter(Mandatory)][AllowEmptyString()][string[]]$Lines)
    $start = -1
    for ($i = 0; $i -lt $Lines.Count; $i++) {
        if ($Lines[$i] -match 'TaskService: Task service request:\s*\{') { $start = $i; break }
    }
    if ($start -lt 0) { return $null }
    $depth = 0; $closed = $false; $body = New-Object System.Collections.Generic.List[string]
    for ($i = $start; $i -lt $Lines.Count; $i++) {
        $l = $Lines[$i]
        [void]$body.Add($l)
        $depth += ([regex]::Matches($l, '\{')).Count
        $depth -= ([regex]::Matches($l, '\}')).Count
        if ($i -gt $start -and $depth -le 0) { $closed = $true; break }
        if ($l -match '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}' -and $i -gt $start) { break }  # next log line = block was cut
    }
    $text = $body -join "`n"
    $kv = [ordered]@{}
    foreach ($m in [regex]::Matches($text, '"([^"]+)"\s*:\s*("([^"]*)"|[-0-9.]+|true|false|null)')) {
        $k = $m.Groups[1].Value
        if ($m.Groups[3].Success) { $kv[$k] = $m.Groups[3].Value } else { $kv[$k] = $m.Groups[2].Value }
    }
    return @{ Closed = $closed; Keys = $kv; Text = $text }
}

function Get-ComputeTarget {
    # GKP vs EKS: the launcher SAYS it on the kind line for PROVISION; otherwise the
    # namespace alias / compute profile name carry it.
    param([string]$Kind, [System.Collections.IDictionary]$TaskKeys, [System.Collections.IDictionary]$LauncherArgs)
    if ($Kind -eq 'PROVISION') { return 'GKP' }
    $alias = $null
    if ($null -ne $TaskKeys -and $TaskKeys.Contains('spark.namespace.alias')) { $alias = $TaskKeys['spark.namespace.alias'] }
    if ($null -eq $alias -and $null -ne $LauncherArgs -and $LauncherArgs.Contains('alias')) { $alias = $LauncherArgs['alias'] }
    if ($null -ne $alias) {
        if ($alias -match '(?i)eks') { return 'EKS' }
        if ($alias -match '(?i)gkp') { return 'GKP' }
        return "alias:$alias"
    }
    if ($null -ne $LauncherArgs -and $LauncherArgs.Contains('compute') -and $LauncherArgs['compute'] -match '(?i)gkp') { return 'GKP' }
    return $null
}

function New-Result {
    # The one shape every parser returns. Fields absent from a log are $null ON PURPOSE -
    # "not read" must stay distinguishable from "empty" (gate data-flow-overview section C).
    param(
        [Parameter(Mandatory)][string]$Kind,
        [Parameter(Mandatory)][string]$SourceFile,
        [int]$Redactions = 0
    )
    return [ordered]@{
        schema            = 'drydocs.poc.controlm-output.v0'
        source_file       = $SourceFile
        launcher_kind     = $Kind
        job_name          = $null
        run_number        = $null
        run_window        = $null
        exit_status       = $null
        host              = $null
        launcher          = $null
        launcher_args     = $null
        pipeline_id       = $null
        dataset_id        = $null
        dataset_version   = $null
        dataflow          = $null
        app_id            = $null      # -seal / spark.kubernetes.seal (sanitized name: APP_ID)
        app_name          = $null
        fid               = $null
        business_date     = $null
        order_date        = $null
        conf_path         = $null
        compute_profile_ref = $null
        compute_target    = $null
        image             = $null
        image_digest      = $null
        pro_id_in         = $null      # -proId the job was GIVEN (consumer side of the chain)
        provenance_guid   = $null      # provenanceGuid the job PRODUCED (placement response)
        provenance_warning = $null     # "No provenanceId is provided!" - EXPECTED off the placement->ingestion pair
        landing_targets   = $null
        landing_prefix    = $null
        data_files        = $null      # dat / tok / original file names the job names
        watched_path      = $null      # FILEWATCHER
        watched_result    = $null
        api_endpoint_host = $null      # PREPROC - host only, never the query string
        api_name          = $null
        submission_url    = $null
        submission_cluster = $null
        submission_job_id = $null
        task_request_closed = $null    # $false = the panel cut the JSON (truncated_json)
        redactions        = $Redactions
        skip_reasons      = @()
    }
}

function Set-HeaderFields {
    # "JOBNAME" / "00001 2026/08/20 15:37 - 2026/08/20 15:41 Size: 6745 Status: 0" header
    # lines, when the log was copied with the panel header. Optional.
    param([Parameter(Mandatory)]$Result, [Parameter(Mandatory)][AllowEmptyString()][string[]]$Lines)
    foreach ($l in $Lines) {
        if ($null -eq $Result.job_name -and $l -match '^([A-Z][A-Z0-9]{2,}[0-9_][A-Z0-9_]+)\s*$') { $Result.job_name = $Matches[1] }
        if ($l -match '^(\d{5})\s+(\d{4}/\d{2}/\d{2} \d{2}:\d{2})\s*-\s*(\d{4}/\d{2}/\d{2} \d{2}:\d{2}).*Status:\s*(\d+)') {
            $Result.run_number = $Matches[1]
            $Result.run_window = "$($Matches[2]) - $($Matches[3])"
            $Result.exit_status = [int]$Matches[4]
        }
    }
    $h = Get-FirstMatch -Lines $Lines -Pattern 'dt-launcher-py started on (\S+) with pid'
    if ($null -ne $h) { $Result.host = $h }
}

function Set-LauncherFields {
    # Shared across the four dt-launcher kinds: the echo line + the common arguments.
    param([Parameter(Mandatory)]$Result, [Parameter(Mandatory)][AllowEmptyString()][string[]]$Lines)
    $echo = Get-LauncherEcho -Lines $Lines
    if ($null -eq $echo) { $Result.skip_reasons += 'no_launcher_banner'; return $null }
    $a = Get-LauncherArgs -ArgString $echo.ArgString
    $Result.launcher = $echo.Launcher
    $Result.launcher_args = $a
    foreach ($pair in @(
        @('pipeline','pipeline_id'), @('dataset','dataset_id'), @('version','dataset_version'),
        @('dataflow','dataflow'), @('seal','app_id'), @('appName','app_name'), @('fid','fid'),
        @('bd','business_date'), @('od','order_date'), @('conf','conf_path'),
        @('compute','compute_profile_ref'), @('img','image'), @('proId','pro_id_in'))) {
        if ($a.Contains($pair[0])) { $Result[$pair[1]] = $a[$pair[0]] }
    }
    $d = Get-FirstMatch -Lines $Lines -Pattern 'mapped to \S+@sha256:([0-9a-f]{64})'
    if ($null -ne $d) { $Result.image_digest = "sha256:$d" }
    return $a
}

function Write-Result {
    param([Parameter(Mandatory)]$Result, [switch]$AsTable)
    if ($AsTable) {
        $Result.GetEnumerator() | Where-Object { $_.Key -notin @('launcher_args','schema') } |
            ForEach-Object {
                $v = $_.Value
                if ($v -is [System.Collections.IEnumerable] -and $v -isnot [string]) { $v = ($v | ForEach-Object { "$_" }) -join ' | ' }
                [pscustomobject]@{ field = $_.Key; value = $v }
            } | Format-Table -AutoSize -Wrap
    } else {
        $Result | ConvertTo-Json -Depth 6
    }
}
