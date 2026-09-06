"""The reconcile-port skill's before-snapshot step RUNS (P5, port test review 2026-09-02).

The skill tells the company session to snapshot the consumer copies before applying a
port. That step shipped first as six ``poetry run python -c "..."`` one-liners, two of
which carried an escaped newline rendered as a real line break and failed as written -
found by the company on 2026-09-02, chunk 1 of the apply, exactly the gap the test review
named (G4). Since 2026-09-05 the step is ONE call, ``scripts/reconcile_before.py``, which
also writes the ``BASE.sha`` stamp the guards now refuse to run without. The prose IS the
subject here (J37's exception): this test reads the fenced block, extracts the step-1
command the skill prints, runs it in a subprocess with ``TEMP`` pointed at a tmp dir, and
asserts every file the guards read comes out non-empty and stamped. A script that moves,
or an import path inside it that moves (S2, S5 and O58 each moved one), fails HERE, not
at the consumer.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / ".claude" / "skills" / "reconcile-port" / "SKILL.md"

_STEP1 = re.compile(
    r'^poetry run python (?P<script>scripts/reconcile_before\.py) "\$env:TEMP/(?P<dir>[\w-]+)"\s*$',
    re.M,
)

#: What the guards read: the four mandatory snapshots, the two optional J51 lists (both
#: modules import on the producer side, so both must appear here), and the stamp.
EXPECTED = {
    "backlog.yaml",
    "gate-log.md",
    "relationship_vocabulary.yaml",
    "taxonomy-ontology-map.yaml",
    "detect-rule-ids.txt",
    "runbook-exemption-keys.txt",
    "BASE.sha",
}


def _step1_block() -> str:
    text = SKILL.read_text(encoding="utf-8")
    start = text.index("# 1. BEFORE applying the port")
    end = text.index("# 2. apply the range", start)
    return text[start:end]


def test_the_block_has_the_one_snapshot_call_and_no_leftover_one_liners() -> None:
    block = _step1_block()
    matches = list(_STEP1.finditer(block))
    assert (
        len(matches) == 1
    ), f"expected exactly one scripts/reconcile_before.py call in step 1, found {len(matches)}"
    assert (
        "python -c" not in block
    ), "step 1 is one call now; a leftover one-liner is a second, unstamped path"
    assert (REPO_ROOT / matches[0].group("script")).is_file()


def test_the_step1_call_runs_and_writes_every_file_the_guards_read(tmp_path: Path) -> None:
    m = _STEP1.search(_step1_block())
    assert m is not None
    if subprocess.run(
        [
            "git",
            "status",
            "--porcelain",
            "--",
            "config/gate-log.md",
            "docs/restructure/backlog",
            "drydocs_core/ontology/relationship_vocabulary",
            "config/taxonomy-ontology-map",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip():
        import pytest

        pytest.skip("snapshot sources are dirty in this checkout; the writer refuses by design")
    before = tmp_path / m.group("dir")
    env = dict(os.environ, TEMP=str(tmp_path), PYTHONIOENCODING="utf-8")
    env.pop("VIRTUAL_ENV", None)
    proc = subprocess.run(
        [sys.executable, m.group("script"), str(before)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, f"step 1 failed:\n--- stderr ---\n{proc.stderr[-2000:]}"
    written = {p.name for p in before.iterdir()}
    assert written == EXPECTED, f"step 1 wrote {written}, the guards read {EXPECTED}"
    for p in before.iterdir():
        assert p.stat().st_size > 0, f"{p.name} is empty"
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()
    assert (before / "BASE.sha").read_text(encoding="utf-8").strip() == head

    describe = subprocess.run(
        [sys.executable, m.group("script"), "--describe", str(before)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert describe.returncode == 0, describe.stderr[-2000:]
    assert head[:7] in describe.stdout and "commits behind HEAD" in describe.stdout
