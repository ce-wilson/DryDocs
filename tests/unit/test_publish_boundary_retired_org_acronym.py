"""J55 publish-boundary guard — the retired internal org acronym must not
come back into the publishable tree.

Direct precedent: J15 (`test_publish_boundary_values.py`). Same rule: the
convention ("don't publish this token") was violated once already (the
2026-08-26 sweep at commit 3c2bfcdd existed precisely because the token had
leaked into 60+ publishable files), so it needs an enforcement point or it
rots the same way twice.

The retired token is never written literally in this file. It is read at
test time from `internal/cdo-reference/README.md` — the ONE place the
old-to-new mapping is recorded (see that file's "RENAMED 2026-08-26" note) —
by parsing the retired directory name out of the sentence "this directory
was `internal/<token>-reference/`". That file is Internal and never
publishes, so a test that only ever holds the token in a local variable,
derived at runtime from an Internal-only source, cannot itself become a
place the retired string leaks from.

Scope: the git-tracked working tree outside `internal/` (the same
publishable-tree definition `test_publish_boundary_values.py` uses). Git
history and any pre-roll depgraph snapshot are explicitly out of scope for
THIS guard (commit 3c2bfcdd names them as expected transient survivors); as
of this guard's own first run neither carried a hit any more (the depgraph
snapshot had already rolled at commit d3f648ee, the next snapshot after the
sweep). The cross-repo half — whether the company's registry row or any
loaded graph doc id still carries the pre-rename string — is explicitly OUT
OF SCOPE here; it is a port-session question handled per-entry under the
port-review F-table (J55 acceptance clause e). This guard rules the producer
tree only.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
MAPPING_FILE = REPO / "internal" / "cdo-reference" / "README.md"

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
    ".svg",
}

# Enumerated on the first run of this guard (2026-08-28): zero hits outside
# internal/ in the current tree. The two candidate matches a bare
# case-insensitive substring search turns up (a compressed JS blob embedded
# in docs/design/ui-exploration/drydocs-console-mockup.html and a base64
# path segment in drydocs-icons/vendors/external/auto/subaru.svg) are both
# coincidental substrings inside long unbroken alphanumeric runs with no
# token boundary on either side — not the retired acronym as a token — and
# the word-boundary match below does not fire on either. Nothing here is a
# sweep miss to fix, and nothing needs a recorded allowlist entry; the set
# stays for the next run to compare against.
ALLOWLIST: dict[str, str] = {}


def _retired_token() -> str | None:
    """Read the retired token from the Internal mapping file. Returns None
    (never the literal string) when the file is unreadable so the caller can
    skip instead of silently passing."""
    try:
        text = MAPPING_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    # The RENAMED note states: "this directory was `internal/<token>-reference/`".
    m = re.search(r"internal/([a-z0-9]+)-reference/", text)
    if not m:
        return None
    return m.group(1)


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
    try:
        return (REPO / relpath).read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        # Tracked-but-locally-deleted (another session's staged work) scans
        # as empty — the committed tree is guarded by CI on the pushed state.
        return ""


def test_retired_org_acronym_is_not_published() -> None:
    """The retired acronym, as a whole token (case-insensitive), must not
    appear in any git-tracked file outside internal/."""
    token = _retired_token()
    if token is None:
        if not (REPO / "internal").is_dir():
            pytest.skip(
                "internal/ is absent from this clone (a published clone excludes it "
                "entirely), so there is nothing to read the retired acronym from and "
                "nothing Internal to leak. This is a SKIP, not a pass: it proves "
                "nothing about whether the token is published."
            )
        # FAIL-CLOSED (2026-09-03, from the company's chunk-1 report): a clone that
        # CARRIES internal/ is a full clone, and on a full clone this guard must have
        # its note. The company's retry found the guard skipping on their tree - the
        # README under internal/cdo-reference/ existed but carried no RENAMED note -
        # and a skip there is the guard sitting green and silent on exactly the tree
        # that publishes. Nobody may write the token here, so the note is the only
        # source; a missing note is the defect, and the fix is to author the sentence.
        pytest.fail(
            "internal/ is present but internal/cdo-reference/README.md is missing or "
            "carries no RENAMED note of the form `internal/<token>-reference/`. This "
            "guard derives the retired token from that note and never writes it; "
            "author the note (one sentence naming the former directory) so the guard "
            "can run. A skip here would be a green light on the tree that publishes."
        )

    pattern = re.compile(r"\b" + re.escape(token) + r"\b", re.IGNORECASE)
    offenders: list[str] = []
    for rel in _tracked_files():
        if rel in ALLOWLIST:
            continue
        body = _read(rel)
        if pattern.search(body):
            offenders.append(rel)

    assert not offenders, (
        "the retired internal org acronym (see internal/cdo-reference/README.md "
        "for the mapping) is published in file(s) outside internal/ — resweep the "
        "value to its replacement, or add a recorded-reason entry to ALLOWLIST in "
        "this file if it is a genuine expected survivor: " + ", ".join(sorted(offenders))
    )
