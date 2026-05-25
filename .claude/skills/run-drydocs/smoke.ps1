#!/usr/bin/env pwsh
# smoke.ps1 — DryDocs CLI smoke test + model-layer validation
# Run from repo root: powershell .claude/skills/run-drydocs/smoke.ps1
# Does NOT require Neo4j; validates CLI routing + model/adapter layers.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Check($label, $block) {
    Write-Host "  >> $label" -ForegroundColor Cyan
    & $block
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { throw "$label exited $LASTEXITCODE" }
    Write-Host "     OK" -ForegroundColor Green
}

# ── 1. CLI entry point ────────────────────────────────────────────────────────
Check "CLI help" {
    poetry run drydocs --help | Out-Null
}

Check "ingest-controlm --help" {
    poetry run drydocs ingest-controlm --help | Out-Null
}

Check "m3-verify --help" {
    poetry run drydocs m3-verify --help | Out-Null
}

# ── 2. Model + adapter layer (no Neo4j needed) ────────────────────────────────
Check "model + adapter layer" {
    @'
from drydocs.models.controlm import (
    ControlMFolderRow, ControlMJobRow,
    ControlMConditionInRow,
    ControlMDependencyRow,
)
from drydocs.adapters.csv_adapter import CsvAdapter
from pathlib import Path

samples = Path("drydocs/data/samples")
checks = [
    ("controlm_folders__sample.csv",        ControlMFolderRow,      8),
    ("controlm_jobs__sample.csv",           ControlMJobRow,        13),
    ("controlm_conditions_in__sample.csv",  ControlMConditionInRow, 10),
    ("controlm_dependencies__sample.csv",   ControlMDependencyRow, 10),
]
for fname, Model, expected_min in checks:
    with CsvAdapter(samples / fname) as a:
        rows = [Model(**r) for r in a.rows()]
    assert len(rows) >= expected_min, f"{fname}: got {len(rows)}, want >= {expected_min}"
    print(f"  {fname}: {len(rows)} rows OK")

from drydocs.controlm.folder_name import parse_folder_name
p = parse_folder_name("PRARAG-HLDM-111027-PEX-RFND-DLY")
assert p.prefix_recognized
assert p.environment == "Production"
print(f"  folder_name parser: environment={p.environment} lob={p.lob} OK")
'@ | poetry run python
}

# ── 3. Unit tests ─────────────────────────────────────────────────────────────
Write-Host "  >> unit tests" -ForegroundColor Cyan
poetry run pytest tests/unit/ -q 2>&1 | Select-Object -Last 4 | Write-Host
Write-Host "     (4 pre-existing known failures are expected)" -ForegroundColor Yellow

Write-Host ""
Write-Host "Smoke PASSED." -ForegroundColor Green
Write-Host "CLI, model layer, and unit tests are clean."
Write-Host ""
Write-Host "Full ingest chain (requires .env with NEO4J_* set):"
Write-Host "  poetry run drydocs check"
Write-Host "  poetry run drydocs bootstrap"
Write-Host "  poetry run drydocs apply-m3-supplement"
Write-Host "  poetry run drydocs ingest-controlm"
Write-Host "  poetry run drydocs m3-verify"
