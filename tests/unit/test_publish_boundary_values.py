"""J15 publish-boundary VALUE-shape guard (2026-07-27).

Lesson (backlog J15 notes): two sanitization sweeps failed the same way — they
grepped for the FIELD NAME (`seal_id`) while real ids survived for months as
VALUES inside Control-M folder-name strings (`PRARAG-HLDM-<id>-…`). A convention
violated twice needs an enforcement point. This guard scans the PUBLISHABLE
tree (git-tracked files outside `internal/`; the gitignored real extracts are
deliberately out of scope — they are *supposed* to hold real values and must
stay untracked) for the shapes real identifiers take:

  A. bare 5-6 digit ids in taxonomy / bundled-sample / knowledge files;
  B. the numeric segments of anything the folder-name parser recognizes as a
     Control-M folder name, ANYWHERE in the tree — the historical miss class;
  C. values paired with `%%SEAL` in test files — the other historical miss.

Every hit must fall inside the reserved synthetic block 70001-70099 or be
allowlisted here with a recorded reason. The guard deliberately embeds NO real
values — membership in the block is the whole check, so the test itself can
never leak what it protects against.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from drydocs_core.controlm.folder_name import parse_folder_name

REPO = Path(__file__).resolve().parents[2]

SYNTHETIC_BLOCK = range(70001, 70100)

# Scan A scope: files where bare numeric ids are identity-shaped by context.
BARE_ID_PREFIXES = ("config/taxonomy/", "drydocs/data/samples/", "knowledge/")
# Generated numeric metadata (node/edge/line counts, benchmark timings), not
# identity values.
BARE_ID_EXCLUDED_PREFIXES = (
    "knowledge/depgraph-snapshots/",
    "knowledge/upgrade-plans/p0-benchmark/",
)

BINARY_SUFFIXES = {
    ".png",
    ".webp",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".pdf",
    ".pyc",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".zip",
    ".gz",
    ".lock",
}

# --------------------------------------------------------------------------
# Allowlist: (path, value) pairs that may sit outside the synthetic block,
# each with a recorded reason. Ruling 2026-07-27 (J15 build; SME may flip):
# 6-digit Control-M surrogate TABLE KEYS (folder ids) are private-DB row
# keys with no external meaning — no SEAL/roster/credential semantics —
# so they stay. Identity-shaped values (SEAL/FID/roster/DL) never get
# allowlisted; they get resweeped into the block instead.
# --------------------------------------------------------------------------
CTM_FOLDER_KEYS = frozenset(
    {
        "161014",
        "161015",
        "161016",
        "161020",
        "160500",
        "160501",
        "162001",
        "161999",
    }
)
ALLOWLIST: dict[str, tuple[frozenset[str], str]] = {
    "config/taxonomy/controlm.yaml": (
        CTM_FOLDER_KEYS,
        "Control-M surrogate folder table keys of the sanitized sample family",
    ),
    "drydocs/data/samples/controlm_folders__sample.csv": (
        CTM_FOLDER_KEYS,
        "sample-family folder table keys",
    ),
    "drydocs/data/samples/controlm_jobs__sample.csv": (
        CTM_FOLDER_KEYS,
        "sample-family folder table keys",
    ),
    "drydocs/data/samples/controlm_conditions_in__sample.csv": (
        CTM_FOLDER_KEYS,
        "sample-family folder table keys",
    ),
    "drydocs/data/samples/controlm_conditions_out__sample.csv": (
        CTM_FOLDER_KEYS,
        "sample-family folder table keys",
    ),
    "drydocs/data/samples/controlm_dependencies__sample.csv": (
        CTM_FOLDER_KEYS,
        "sample-family folder table keys",
    ),
    "drydocs/data/samples/controlm_hosts__sample.csv": (
        CTM_FOLDER_KEYS,
        "sample-family folder table keys",
    ),
}

_BARE_ID = re.compile(r"\b\d{5,6}\b")
# Candidate Control-M folder-name tokens: 6-letter prefix + >=2 dash segments.
_FOLDER_TOKEN = re.compile(r"\b[A-Z]{6}(?:-[A-Z0-9]{2,20}){2,}\b")
_SEAL_PAIR = re.compile(r"%%SEAL\b[^0-9\n]{0,40}(\d{4,7})")


def _tracked_files() -> list[str]:
    try:
        out = subprocess.run(
            ["git", "ls-files"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover
        pytest.skip("git unavailable — publishable tree cannot be enumerated")
    return [
        line
        for line in out.splitlines()
        if line
        and not line.startswith("internal/")
        and Path(line).suffix.lower() not in BINARY_SUFFIXES
    ]


def _read(relpath: str) -> str:
    # Tracked-but-locally-deleted files (another session's staged work) scan
    # as empty — the committed tree is guarded by CI on the pushed state.
    try:
        return (REPO / relpath).read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        return ""


def _allowed(relpath: str, value: str) -> bool:
    entry = ALLOWLIST.get(relpath)
    return bool(entry and value in entry[0])


def _in_block(value: str) -> bool:
    return int(value) in SYNTHETIC_BLOCK


def test_bare_ids_in_taxonomy_samples_knowledge_are_synthetic() -> None:
    """Scan A: any bare 5-6 digit id in identity-bearing file families must be
    in the reserved block or allowlisted with a reason."""
    violations: list[str] = []
    for rel in _tracked_files():
        if not rel.startswith(BARE_ID_PREFIXES):
            continue
        if rel.startswith(BARE_ID_EXCLUDED_PREFIXES):
            continue
        for m in _BARE_ID.finditer(_read(rel)):
            v = m.group(0)
            if not _in_block(v) and not _allowed(rel, v):
                violations.append(f"{rel}: {v}")
    assert not violations, (
        "bare 5-6 digit ids outside the reserved synthetic block 70001-70099 "
        "(resweep the value or allowlist it WITH A REASON in "
        "test_publish_boundary_values.py):\n" + "\n".join(sorted(set(violations)))
    )


def test_folder_name_numeric_segments_are_synthetic_everywhere() -> None:
    """Scan B (the historical miss): every numeric segment of every string the
    folder-name parser recognizes, in EVERY tracked file, must be in-block."""
    violations: list[str] = []
    for rel in _tracked_files():
        text = _read(rel)
        for m in _FOLDER_TOKEN.finditer(text):
            parsed = parse_folder_name(m.group(0))
            if not parsed.prefix_recognized:
                continue
            for seg in parsed.segments:
                if (
                    seg.isdigit()
                    and 5 <= len(seg) <= 6
                    and not _in_block(seg)
                    and not _allowed(rel, seg)
                ):
                    violations.append(f"{rel}: {m.group(0)} -> segment {seg}")
    assert not violations, (
        "folder-name-embedded ids outside the reserved synthetic block "
        "70001-70099 — the exact class two sweeps missed. Resweep the value "
        "(and its internal/ twin key row) rather than allowlisting:\n"
        + "\n".join(sorted(set(violations)))
    )


def test_seal_variable_values_in_tests_are_synthetic() -> None:
    """Scan C: a value paired with %%SEAL in any tracked test file is a SEAL id
    by construction — it must come from the synthetic block."""
    violations: list[str] = []
    for rel in _tracked_files():
        if not rel.startswith("tests/"):
            continue
        for m in _SEAL_PAIR.finditer(_read(rel)):
            if not (m.group(1).isdigit() and _in_block(m.group(1))):
                violations.append(f"{rel}: %%SEAL value {m.group(1)}")
    assert not violations, (
        "%%SEAL values outside the reserved synthetic block 70001-70099 in "
        "test files:\n" + "\n".join(sorted(set(violations)))
    )
