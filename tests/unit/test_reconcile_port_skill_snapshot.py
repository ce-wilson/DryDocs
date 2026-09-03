"""The reconcile-port skill's before-snapshot one-liners RUN (P5, port test review 2026-09-02).

The skill tells the company session to snapshot six files with ``poetry run python -c "..."``
one-liners before applying a port. Two of them shipped with an escaped newline rendered as
a real line break inside the ``-c`` string and failed as written - found by the company on
2026-09-02, chunk 1 of the apply, exactly the gap the test review named (G4). The prose IS
the subject here (J37's exception): this test reads the fenced block, extracts every
``python -c`` command, runs each in a subprocess with ``TEMP`` pointed at a tmp dir, and
asserts the file it names comes out non-empty. A one-liner whose import path moves (S2, S5
and O58 each moved one) fails HERE, not at the consumer.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / ".claude" / "skills" / "reconcile-port" / "SKILL.md"

_ONE_LINER = re.compile(r'^poetry run python -c "(?P<code>.*)"\s*$', re.M)

#: The files the six one-liners write, so the test knows what to expect.
EXPECTED = {
    "backlog.yaml",
    "detect-rule-ids.txt",
    "runbook-exemption-keys.txt",
    "relationship_vocabulary.yaml",
    "taxonomy-ontology-map.yaml",
}


def _one_liners() -> list[str]:
    text = SKILL.read_text(encoding="utf-8")
    start = text.index("# 1. BEFORE applying the port")
    end = text.index("# 2. apply the range", start)
    block = text[start:end]
    return [m.group("code") for m in _ONE_LINER.finditer(block)]


def test_the_block_still_has_its_one_liners() -> None:
    codes = _one_liners()
    assert len(codes) >= 4, f"expected the snapshot one-liners in SKILL.md, found {len(codes)}"
    for code in codes:
        assert (
            "\n" not in code
        ), "a one-liner carries a real line break - the 2026-09-02 mangling; use chr(10)"


@pytest.mark.parametrize("code", _one_liners(), ids=lambda c: c[:60])
def test_every_snapshot_one_liner_runs_and_writes_its_file(code: str, tmp_path: Path) -> None:
    before = tmp_path / "reconcile-before"
    before.mkdir()
    env = dict(os.environ, TEMP=str(tmp_path), PYTHONIOENCODING="utf-8")
    env.pop("VIRTUAL_ENV", None)
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, f"one-liner failed:\n{code}\n--- stderr ---\n{proc.stderr[-2000:]}"
    written = {p.name for p in before.iterdir()}
    assert written, f"one-liner ran but wrote nothing into {before}:\n{code}"
    assert written <= EXPECTED, f"unexpected snapshot file(s) {written - EXPECTED} from:\n{code}"
    for p in before.iterdir():
        assert p.stat().st_size > 0, f"{p.name} is empty"
