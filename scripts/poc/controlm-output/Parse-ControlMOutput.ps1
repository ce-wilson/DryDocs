# Parse-ControlMOutput.ps1 - dispatcher: detect the job kind, hand off to the per-kind parser.
#
#   .\Parse-ControlMOutput.ps1 -Path <log>                 JSON to stdout
#   .\Parse-ControlMOutput.ps1 -Path <log> -AsTable        field/value table for eyeballing
#   .\Parse-ControlMOutput.ps1 -Path <dir> -OutDir <dir>   every *.log / *.txt in a folder -> one .json each
#
# Kind detection is ONE rule (Common.ps1 Get-LogKind): the launcher's own
# "Identified '<KIND>' Job" line; ctmfw -> FILEWATCHER; a .ksh + curl -> PREPROC. A log that
# matches none is reported as UNKNOWN with skip_reason kind_unknown - never guessed from the
# job name (that is exactly the R13 trap this PoC exists to get past).
param(
    [Parameter(Mandatory)][string]$Path,
    [string]$OutDir,
    [switch]$AsTable
)
. "$PSScriptRoot\Common.ps1"

$parsers = @{
    PLACEMENT   = "$PSScriptRoot\Parse-Placement.ps1"
    INGESTION   = "$PSScriptRoot\Parse-Ingestion.ps1"
    TRANSFORM   = "$PSScriptRoot\Parse-Transform.ps1"
    PROVISION   = "$PSScriptRoot\Parse-Provision.ps1"
    FILEWATCHER = "$PSScriptRoot\Parse-FileWatcher.ps1"
    PREPROC     = "$PSScriptRoot\Parse-Preproc.ps1"
}

function Invoke-One {
    param([string]$File, [switch]$Table)
    $kind = Get-LogKind -Lines (Get-UnwrappedLog -Path $File)
    if (-not $parsers.ContainsKey($kind)) {
        $r = New-Result -Kind 'UNKNOWN' -SourceFile $File
        $r.skip_reasons += 'kind_unknown'
        Set-HeaderFields -Result $r -Lines (Get-UnwrappedLog -Path $File)
        return (Write-Result -Result $r -AsTable:$Table)
    }
    Write-Host ("[{0,-11}] {1}" -f $kind, (Split-Path -Leaf $File)) -ForegroundColor DarkCyan
    & $parsers[$kind] -Path $File -AsTable:$Table
}

if (Test-Path -LiteralPath $Path -PathType Container) {
    $files = Get-ChildItem -LiteralPath $Path -File | Where-Object { $_.Extension -in '.log', '.txt', '.out' }
    if ($OutDir) { New-Item -ItemType Directory -Force -Path $OutDir | Out-Null }
    foreach ($f in $files) {
        $json = Invoke-One -File $f.FullName
        if ($OutDir) {
            $target = Join-Path $OutDir ($f.BaseName + '.json')
            [System.IO.File]::WriteAllText($target, ($json -join "`n"), (New-Object System.Text.UTF8Encoding $false))
            Write-Host "    -> $target" -ForegroundColor DarkGray
        } else {
            $json
        }
    }
} else {
    Invoke-One -File $Path -Table:$AsTable
}
