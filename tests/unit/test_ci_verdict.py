"""U27 (2026-09-08) — the snapshot ritual's CI verdict, driven as the pure
function its design comment always said it was.

``knowledge/depgraph-snapshots/ci_verdict.ps1`` holds ``Get-CiVerdict``, which
maps (runs, head, gh exit code, branch) to one line and a colour. ``snapshot.ps1``
dot-sources it and owns the measurement; this file owns the words. From Idea-111
(2026-08) to U27 the function claimed to be "exercisable without a network" and
nothing exercised it — the 2026-08-20 false GREEN (U24: a JSON array arriving as
one PSObject, so ``-eq "success"`` was true if ANY run had passed) is the case
the EMPTY fixture here would have caught.

There is no Pester in this repo, so the harness is pytest invoking PowerShell:
``pwsh`` first, ``powershell`` (5.1, the desktop's) second, and a clean skip that
names both where neither is installed (the U26 precedent in
``test_probe_instrument.py``). The fixtures are fed through the SAME
``ConvertFrom-Json ... | ForEach-Object { $_ }`` idiom the live caller uses, so
the PS 5.1 unrolling trap is exercised, not bypassed.

The caller-side half of U27 — ask ``gh run list`` about the branch HEAD is on,
never ``main`` by literal — is pinned by reading the code (J66: comments and
strings stripped where the assertion is about code, kept where the assertion
IS about the operator-facing string).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SNAP_DIR = REPO / "knowledge" / "depgraph-snapshots"
VERDICT = SNAP_DIR / "ci_verdict.ps1"
SNAPSHOT = SNAP_DIR / "snapshot.ps1"

HEAD = "0123456789abcdef0123456789abcdef01234567"
OLDER = "fedcba9876543210fedcba9876543210fedcba98"


def _shell() -> str:
    for name in ("pwsh", "powershell"):
        found = shutil.which(name)
        if found:
            return found
    pytest.skip(
        "neither `pwsh` (PowerShell 7) nor `powershell` (Windows PowerShell 5.1) is on PATH - "
        "the verdict function is PowerShell and cannot be driven here; the five fixtures run "
        "where either shell is installed"
    )


def _run(status: str, conclusion: str | None, sha: str, title: str = "ci") -> dict:
    return {"headSha": sha, "status": status, "conclusion": conclusion, "displayTitle": title}


def _verdict(
    tmp_path: Path,
    runs: list[dict],
    head: str = HEAD,
    gh_exit: int = 0,
    branch: str = "main",
) -> tuple[str, str]:
    """Dot-source the verdict file and return (colour, text) for one fixture."""
    shell = _shell()
    fixture = tmp_path / "runs.json"
    fixture.write_text(json.dumps(runs), encoding="utf-8")
    command = "; ".join(
        [
            f". '{VERDICT}'",
            f"$raw = Get-Content -Raw -LiteralPath '{fixture}'",
            "$runs = @()",
            # the live caller's idiom, verbatim: an array must UNROLL here (U24)
            "if (-not [string]::IsNullOrWhiteSpace($raw)) { $runs = @((ConvertFrom-Json $raw) | ForEach-Object { $_ }) }",
            f"$v = Get-CiVerdict -Runs $runs -Head '{head}' -GhExit {gh_exit} -Branch '{branch}'",
            "Write-Output ($v.Color + '|' + $v.Text)",
        ]
    )
    proc = subprocess.run(
        [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )
    assert proc.returncode == 0, f"{shell} exited {proc.returncode}:\n{proc.stdout}\n{proc.stderr}"
    lines = [ln for ln in proc.stdout.splitlines() if "|" in ln]
    assert len(lines) == 1, f"expected one verdict line, got:\n{proc.stdout}"
    color, text = lines[-1].split("|", 1)
    return color.strip(), text.strip()


# --- the five fixtures (U27 b) --------------------------------------------------


def test_green_at_head(tmp_path: Path) -> None:
    color, text = _verdict(tmp_path, [_run("completed", "success", HEAD)])
    assert color == "Green"
    assert text == f"ci: GREEN at HEAD {HEAD[:7]}"


def test_failed_at_head_with_an_older_success_in_the_list(tmp_path: Path) -> None:
    """The false-GREEN shape: HEAD's run failed and an OLDER run in the same list
    succeeded. The verdict is HEAD's, never the list's."""
    runs = [
        _run("completed", "failure", HEAD, "the push under test"),
        _run("completed", "success", OLDER, "the previous push"),
    ]
    color, text = _verdict(tmp_path, runs, branch="feat/example")
    assert color == "Red"
    assert text.startswith(f"ci: FAILURE AT HEAD {HEAD[:7]} - feat/example is RED")


def test_in_progress_at_head(tmp_path: Path) -> None:
    color, text = _verdict(tmp_path, [_run("in_progress", None, HEAD)])
    assert color == "Yellow"
    assert text.startswith(f"ci: run for HEAD {HEAD[:7]} is in_progress")


def test_no_run_yet_for_head(tmp_path: Path) -> None:
    """Runs exist for the branch, none for HEAD: UNVERIFIED, naming the newest
    run's state and the BRANCH it was listed for, never GREEN or RED."""
    runs = [_run("completed", "success", OLDER, "older commit")]
    color, text = _verdict(tmp_path, runs, branch="wip/example-desktop")
    assert color == "Yellow"
    assert text.startswith(f"ci: UNVERIFIED at HEAD {HEAD[:7]} - no run exists for it")
    assert "newest on wip/example-desktop is success (older commit)" in text


def test_empty_runs_is_unverified_not_green(tmp_path: Path) -> None:
    """The case behind the 2026-08-20 false GREEN and the J76 guessed cause: gh
    exit 0 and an empty list is a workflow that never ran for that branch. Say
    that, for THAT branch; guess nothing."""
    color, text = _verdict(tmp_path, [], branch="feat/never-pushed")
    assert color == "Yellow"
    assert text.startswith(
        f"ci: UNVERIFIED at HEAD {HEAD[:7]} - the remote reports ZERO runs on feat/never-pushed"
    )


# --- the two the fixtures imply ----------------------------------------------------


def test_gh_failure_is_a_named_skip_distinct_from_an_empty_list(tmp_path: Path) -> None:
    color, text = _verdict(tmp_path, [], gh_exit=4)
    assert color == "DarkGray"
    assert text.startswith("ci: gh run list exited 4")
    assert "check skipped" in text


def test_cancelled_at_head_is_unverified_not_red(tmp_path: Path) -> None:
    """J78: a run GitHub cancelled has a matching sha and no result."""
    color, text = _verdict(tmp_path, [_run("completed", "cancelled", HEAD)])
    assert color == "Yellow"
    assert "UNVERIFIED" in text and "the run was cancelled" in text


# --- the caller asks about the branch it is on (U27 a) -----------------------------


def _code(path: Path) -> str:
    return "\n".join(
        ln
        for ln in path.read_text(encoding="utf-8").splitlines()
        if not ln.lstrip().startswith("#")
    )


def test_the_caller_lists_runs_for_the_branch_head_is_on_never_main_by_literal() -> None:
    code = _code(SNAPSHOT)
    assert "gh run list --branch main" not in code, (
        "the CI check pinned `main` by literal, so from any branch HEAD could never appear "
        "in the list and the verdict degraded to no-run-yet permanently (Idea-156)"
    )
    assert "git rev-parse --abbrev-ref HEAD" in code
    assert "gh run list --branch $branchName" in code
    assert (
        "-Branch $branchName" in code
    ), "the branch must reach the verdict so its messages name it"
    assert (
        'if ($branchName -eq "HEAD")' in code
    ), "a detached HEAD degrades to a named skip, never a crash"
    assert (
        'ci_verdict.ps1")' in code
    ), "snapshot.ps1 dot-sources the verdict rather than defining it"


def test_the_verdict_file_reads_nothing_but_its_arguments() -> None:
    """Pure function, enforced: if the verdict starts reading git or gh, the
    fixtures above stop meaning anything."""
    code = _code(VERDICT)
    for forbidden in (
        "& git",
        "& gh",
        "$LASTEXITCODE",
        "Push-Location",
        "Get-Content",
        "Get-Command",
    ):
        assert (
            forbidden not in code
        ), f"ci_verdict.ps1 must not measure anything itself: found {forbidden!r}"
    assert "function Get-CiVerdict" in code
    assert '[string]$Branch = "main"' in code


def test_readme_documents_the_branch_pin_and_the_fixtures() -> None:
    readme = (SNAP_DIR / "README.md").read_text(encoding="utf-8")
    assert "git rev-parse --abbrev-ref HEAD" in readme
    assert "ci_verdict.ps1" in readme
    assert "test_ci_verdict.py" in readme
