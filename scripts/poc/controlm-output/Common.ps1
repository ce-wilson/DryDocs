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
        order_id          = $null      # from the FILE NAME - the modern wrapper omits it from the body
        run_date          = $null      # from the FILE NAME; NOT assumed to be the launcher's -od
        run_stamp         = $null      # from the FILE NAME
        identity_source   = $null      # filename | header | filename+header | none
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

# --- identity from the FILE NAME -------------------------------------------------------------
#
# WHY THIS EXISTS (estate fact, 2026-08-21). The modern launcher wrapper does NOT write the job
# name, order id or run metadata into the Output body - the first real-log run showed a blank
# job column on all eleven logs. That is not a parser gap in the body reader and widening the
# header pattern would not fix it: this is a standard Control-M sysout, and the identity is in
# the FILE NAME (job name, order id, order date, run stamp). So identity is read from the name,
# and the body header - which older logs still carry - is a fallback and a cross-check.
#
# The default reader is a tolerant scan, not a fixed format, because sysout naming varies by
# site. Pass -NamePattern (a regex with named groups job/order/odate/stamp) via
# Set-CtmNamePattern to pin it for an estate. Whatever it derives is PRINTED, so a wrong parse
# is visible rather than silent - the same rule the joins follow.

$script:CtmNamePattern = $null

function Set-CtmNamePattern {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Pattern)
    if ([string]::IsNullOrWhiteSpace($Pattern)) { $script:CtmNamePattern = $null }
    else { $script:CtmNamePattern = $Pattern }
}

function Test-JobNameShape {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)
    return ($Value -match '^[A-Za-z][A-Za-z0-9]{2,}[0-9_][A-Za-z0-9_]+$')
}

function Get-IdentityFromFileName {
    param([Parameter(Mandatory)][string]$Path)
    $base = [System.IO.Path]::GetFileNameWithoutExtension($Path)
    # run_date is deliberately NOT called order_date: the launcher's own -od argument is a
    # different field and the two disagree on real logs. Which one the name carries is an open
    # question for the estate, so the reader records what it saw and claims nothing.
    $out = [ordered]@{ job_name = $null; order_id = $null; run_date = $null; run_stamp = $null; pattern = 'none' }

    if ($null -ne $script:CtmNamePattern) {
        if ($base -match $script:CtmNamePattern) {
            if ($Matches.Contains('job'))   { $out.job_name   = $Matches['job'] }
            if ($Matches.Contains('order')) { $out.order_id   = $Matches['order'] }
            if ($Matches.Contains('odate')) { $out.run_date = $Matches['odate'] }
            if ($Matches.Contains('stamp')) { $out.run_stamp  = $Matches['stamp'] }
            $out.pattern = 'override'
        }
        return $out
    }

    # Default scan. Sysout names put the job name first and the numeric fields after it, most
    # commonly dot-separated - job names themselves are full of underscores, so '.' is the field
    # separator and '_' is not.
    $parts = @($base -split '\.')
    if ($parts.Count -ge 2 -and (Test-JobNameShape -Value $parts[0])) {
        $out.job_name = $parts[0]
        $out.pattern = 'dotted'
        foreach ($seg in $parts[1..($parts.Count - 1)]) {
            if ($seg -match '^20\d{6}$' -and $null -eq $out.run_date) { $out.run_date = $seg; continue }
            if ($seg -match '^\d{9,17}$' -and $null -eq $out.run_stamp) { $out.run_stamp = $seg; continue }
            if ($seg -match '^\d{6}$'    -and $null -eq $out.run_stamp) { $out.run_stamp = $seg; continue }
            if ($seg -match '^[0-9A-Za-z]{3,10}$' -and $null -eq $out.order_id) { $out.order_id = $seg; continue }
        }
        return $out
    }

    # No dot fields: anchor on a delimited YYYYMMDD and take what precedes it as the job name.
    if ($base -match '^(?<job>.+?)[._-](?<odate>20\d{6})(?:[._-](?<rest>.*))?$' -and (Test-JobNameShape -Value $Matches['job'])) {
        $out.job_name = $Matches['job']
        $out.run_date = $Matches['odate']
        $out.pattern    = 'date-anchored'
        if ($Matches.Contains('rest') -and -not [string]::IsNullOrWhiteSpace($Matches['rest'])) {
            foreach ($seg in @($Matches['rest'] -split '[._-]')) {
                if ($seg -match '^\d{6,17}$' -and $null -eq $out.run_stamp) { $out.run_stamp = $seg; continue }
                if ($seg -match '^[0-9A-Za-z]{3,10}$' -and $null -eq $out.order_id) { $out.order_id = $seg }
            }
        }
        return $out
    }

    # A bare job name with no fields at all still gives identity.
    if (Test-JobNameShape -Value $base) { $out.job_name = $base; $out.pattern = 'name-only' }
    return $out
}

function Set-IdentityFromFileName {
    param([Parameter(Mandatory)]$Result)
    $id = Get-IdentityFromFileName -Path $Result.source_file
    if ($null -eq $id.job_name) { $Result.skip_reasons += 'identity_not_in_filename'; return }
    $Result.job_name   = $id.job_name
    $Result.order_id   = $id.order_id
    $Result.run_stamp  = $id.run_stamp
    $Result.run_date   = $id.run_date
    $Result.identity_source = 'filename'
    if ($null -eq $id.order_id) { $Result.skip_reasons += 'no_order_id_in_filename' }
}

function Set-HeaderFields {
    # "JOBNAME" / "00001 2026/08/20 15:37 - 2026/08/20 15:41 Size: 6745 Status: 0" header
    # lines, when the log was copied with the panel header. Optional.
    # Identity comes from the FILE NAME first (see Get-IdentityFromFileName). Older logs also
    # carry a bare job-name line here; it is a fallback when the name gave nothing, and a
    # cross-check when both are present.
    param([Parameter(Mandatory)]$Result, [Parameter(Mandatory)][AllowEmptyString()][string[]]$Lines)
    Set-IdentityFromFileName -Result $Result
    foreach ($l in $Lines) {
        if ($l -match '^([A-Z][A-Z0-9]{2,}[0-9_][A-Z0-9_]+)\s*$') {
            if ($null -eq $Result.job_name) {
                $Result.job_name = $Matches[1]
                $Result.identity_source = 'header'
            } elseif ($Result.job_name -ne $Matches[1]) {
                $Result.skip_reasons += "identity_mismatch:filename=$($Result.job_name);header=$($Matches[1])"
            } elseif ($Result.identity_source -eq 'filename') {
                $Result.identity_source = 'filename+header'
            }
        }
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
