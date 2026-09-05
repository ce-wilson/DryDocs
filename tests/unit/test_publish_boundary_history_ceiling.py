"""J74 publish-boundary guard, SECOND SURFACE — the retired org acronym in
COMMIT MESSAGES, held at a recorded ceiling.

The publish boundary is defined on the tracked TREE. A commit message is not a
file, so no tree guard can see one, and 34 of them carry the retired internal
org acronym. `test_publish_boundary_retired_org_acronym.py` (J55) is correct as
written and is NOT amended here: its scope is the tracked tree, that is the
right scope for a tree guard, and its own docstring already names git history
as an expected transient survivor of the 2026-08-26 sweep. This is a second
guard on a second surface, and that is the whole relationship between them.

WHY A CEILING AND NOT ZERO. Driving this number to zero means rewriting history
— and every `reviewed_commit` stamp in a review artifact, every sha cited
inside a SIGNED record in `config/gate-log.md`, every `port-base-*` tag, and
every sha pinned in a PORT-REPORT would then point at a commit that no longer
exists. The repo's own provenance discipline is built on those citations being
resolvable, so a rewrite trades a real, load-bearing property for a cosmetic
one. The 34 are ACCEPTED. The number exists to be WATCHED, so that a NEW
occurrence — a message written today — fails while the historical ones do not.
It is a ceiling, not a sweep.

The retired token is never written literally in this file, the same way J55
does it: it is read at test time from `internal/cdo-reference/README.md`, the
one place the old-to-new mapping is recorded. That file is Internal and never
publishes, so a guard that only ever holds the token in a local variable,
derived at runtime from an Internal-only source, cannot itself become a place
the retired string leaks from.

WHERE THIS ACTUALLY BITES: a full clone, which in practice means a developer's
machine running the pre-push suite. CI checks out shallow (`actions/checkout`
with no `fetch-depth`, so depth 1), where `git log` can see one commit and the
count would come back 0 — a pass that proves nothing. This guard detects that
and SKIPS LOUDLY rather than going green on an instrument that cannot measure
(CLAUDE.md section 6: check the instrument before the subject). The local
enforcement point is the right one regardless: a commit message cannot be
corrected after a push without the very rewrite this ceiling exists to avoid,
so the moment to catch it is before it leaves the machine that wrote it.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
MAPPING_FILE = REPO / "internal" / "cdo-reference" / "README.md"

#: Measured 2026-09-05 on a full clone: 34 of 2,057 commits reachable from
#: main carry the token in their subject or body. The same 34 the item recorded
#: at 1,816 commits — the repo grew and the count did not, which is the ceiling
#: behaving. RAISE THIS ONLY with a recorded reason: a rise means a message
#: written after the 2026-08-26 rename reintroduced the retired form, and the
#: fix is to stop writing it, not to move the line.
CEILING = 34

#: Field/record separators for a machine-readable log. Chosen because neither
#: can occur in a commit message, so a body containing a newline (every commit
#: here) cannot be misread as a record boundary and inflate the count.
_FIELD = "\x1f"
_RECORD = "\x1e"


def _retired_token() -> str | None:
    """Read the retired token from the Internal mapping file.

    Returns None (never the literal string) when the note is unreadable, so the
    caller decides between skip and fail rather than passing silently.
    """
    try:
        text = MAPPING_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    match = re.search(r"internal/([a-z0-9]+)-reference/", text)
    return match.group(1) if match else None


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=REPO,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    ).stdout


def _commit_messages() -> list[tuple[str, str]]:
    """(sha, subject+body) for every commit reachable from HEAD."""
    out = _git("log", f"--format=%H{_FIELD}%s%n%b{_RECORD}")
    records = []
    for chunk in out.split(_RECORD):
        chunk = chunk.strip("\n")
        if not chunk.strip():
            continue
        sha, _, message = chunk.partition(_FIELD)
        records.append((sha.strip(), message))
    return records


def test_no_new_commit_message_carries_the_retired_org_acronym() -> None:
    """At or below the recorded ceiling. A NEW occurrence fails."""
    try:
        shallow = _git("rev-parse", "--is-shallow-repository").strip()
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover
        pytest.skip("git unavailable — commit messages cannot be enumerated")

    if shallow == "true":
        pytest.skip(
            "shallow clone: git log sees a truncated history, so the count would come "
            "back near zero and pass without measuring anything. This is a SKIP, not a "
            "pass — it proves nothing about whether a new commit message carries the "
            "token. Run the suite on a full clone (the pre-push ritual), or give the "
            "CI checkout fetch-depth: 0 if this is wanted there."
        )

    token = _retired_token()
    if token is None:
        if not (REPO / "internal").is_dir():
            pytest.skip(
                "internal/ is absent from this clone (a published clone excludes it "
                "entirely), so there is nothing to read the retired acronym from. A "
                "SKIP, not a pass."
            )
        # Fail-closed, exactly as J55 does and for its reason: a clone that
        # carries internal/ is a full clone, and a guard that goes green and
        # silent on the tree that publishes is worse than no guard.
        pytest.fail(
            "internal/ is present but internal/cdo-reference/README.md is missing or "
            "carries no RENAMED note of the form `internal/<token>-reference/`. This "
            "guard derives the retired token from that note and never writes it; "
            "author the note so the guard can run."
        )

    pattern = re.compile(r"\b" + re.escape(token) + r"\b", re.IGNORECASE)
    offenders = [sha for sha, message in _commit_messages() if pattern.search(message)]

    assert len(offenders) <= CEILING, (
        f"{len(offenders)} commit messages carry the retired internal org acronym "
        f"(see internal/cdo-reference/README.md for the mapping) — above the recorded "
        f"ceiling of {CEILING}. A NEW one was written: amend it before pushing, which "
        f"is the only point it can be fixed without the history rewrite this ceiling "
        f"exists to avoid. Newest offenders: {', '.join(s[:8] for s in offenders[:5])}"
    )


def test_the_ceiling_is_not_stale_by_a_wide_margin() -> None:
    """A ceiling far above the real count stops being a tripwire.

    If history were ever rewritten for some unrelated reason, or a branch with
    a different past were merged, the count could drop well below the recorded
    line — and the guard would then tolerate several new occurrences before
    firing. Cheap to check, and it turns a silent loss of sensitivity into a
    prompt to re-record the number.
    """
    try:
        if _git("rev-parse", "--is-shallow-repository").strip() == "true":
            pytest.skip("shallow clone — see the sibling test")
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover
        pytest.skip("git unavailable")

    token = _retired_token()
    if token is None:
        pytest.skip("no mapping note here — the sibling test rules on that")

    pattern = re.compile(r"\b" + re.escape(token) + r"\b", re.IGNORECASE)
    actual = sum(1 for _, message in _commit_messages() if pattern.search(message))
    assert actual >= CEILING - 2, (
        f"the recorded ceiling is {CEILING} but only {actual} commit messages carry the "
        f"token — the ceiling has drifted above the real count and would now tolerate "
        f"{CEILING - actual} new occurrence(s) silently. Re-record CEILING at {actual} "
        f"with the reason it moved."
    )
