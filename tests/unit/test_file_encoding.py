"""J29 — UTF-8 no-BOM is the repo standard for loader-read text formats.

THE STANDARD (SME ruling, 2026-08-04): every ``.cypher``, ``.sql``, and ``.csv``
file in the tree is UTF-8 WITHOUT a byte-order mark. UTF-8 itself was the SME's
deliberate readability choice; the BOM is never part of that choice — it is a
writer artifact (PowerShell's ``Out-File``/``>`` default, Excel CSV export)
that the readers on these paths do not tolerate:

- ``cypher-shell -f`` rejects a BOM outright ("Invalid input '\\ufeff'") — the
  2026-08-04 M3-reload incident. The in-repo files were clean that day; the BOM
  was injected by a PowerShell 5.1 pipe into ``docker exec``, which is exactly
  why the guard exists: the failure is invisible until the file meets the one
  reader that refuses it.
- Python's plain ``utf-8`` codec keeps ``\\ufeff`` glued to the first CSV
  header, so a BOM'd import silently breaks ``populate_by_name`` field matching
  (rows validate against a header that is not the name the model declares).

Vendor ``.xsd`` captures are deliberately OUT of scope: XML self-declares its
encoding and its parsers consume BOMs, and the files are VERBATIM-trust vendor
captures we do not edit (the same fidelity rule that keeps their content
byte-exact).

The walk covers tracked AND untracked-but-not-ignored files (the J22 lesson:
a tracked-only walk passes on a new file before ``git add`` and fails after).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent

GUARDED_SUFFIXES = {".cypher", ".sql", ".csv"}
BOM = b"\xef\xbb\xbf"


def _walked_files() -> list[str]:
    try:
        tracked = subprocess.run(
            ["git", "ls-files"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover
        pytest.skip("git unavailable — the tree cannot be enumerated")
    return sorted({line for line in (tracked + untracked).splitlines() if line})


def test_no_bom_on_loader_read_formats() -> None:
    offenders = []
    for rel in _walked_files():
        if Path(rel).suffix.lower() not in GUARDED_SUFFIXES:
            continue
        path = REPO / rel
        if not path.is_file():  # racing a concurrent delete is not a finding
            continue
        with path.open("rb") as fh:
            if fh.read(3) == BOM:
                offenders.append(rel)
    assert not offenders, (
        "UTF-8 BOM on loader-read files (the standard is UTF-8 WITHOUT BOM — "
        "cypher-shell rejects it and csv header matching silently breaks): "
        f"{offenders}. Strip the first three bytes; if the writer was "
        "PowerShell, use [System.IO.File]::WriteAllText with "
        "UTF8Encoding($false) instead of Out-File/'>'."
    )
