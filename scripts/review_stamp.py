"""Print the review-provenance stamp for the current tree (J63).

    poetry run python scripts/review_stamp.py           # markdown bullet
    poetry run python scripts/review_stamp.py --yaml    # YAML front-matter keys

WHY IT EXISTS. The convention (docs/style/review-provenance.md) asks a review to
name the commit, branch and port base it ran against. Looking those up by hand is
three commands and a judgement about which `port-base-*` tag applies, which is
enough friction to make a stamp get skipped -- and a convention that gets skipped
is not a convention.

NOTHING DEPENDS ON THIS. It is a convenience, not a gate: no guard asserts the
stamp and no surface fails without it. J63 clause (f) makes generating it for one
surface in scope and asserting it across all of them out of scope, deliberately,
because a repo-wide assertion would fail on every historical document and
back-filling those would put a present-day SHA on a document written against a
different tree -- the exact failure the convention exists to prevent, applied to
itself.
"""

from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _git(*args: str) -> str:
    """Run git at the repo root; "" on any failure.

    UTF-8 explicitly rather than ``text=True``: the locale codec is cp1252 on the
    machines this runs on, and a tag or subject line with an em dash would raise
    (the same defect I6 found in the allocator).
    """
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=str(REPO_ROOT),
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def stamp() -> dict[str, str]:
    """The four fields, each falling back to a HONEST unknown rather than a guess."""
    commit = _git("rev-parse", "--short", "HEAD") or "unknown"
    branch = _git("rev-parse", "--abbrev-ref", "HEAD") or "unknown"
    # The most recent port base REACHABLE from HEAD -- not the newest tag in the
    # repo. A tag cut on another branch says nothing about what this tree carries.
    port_base = _git("describe", "--tags", "--match", "port-base-*", "--abbrev=0") or "n/a"
    venue = platform.node() or "unknown-host"
    return {
        "reviewed_commit": commit,
        "reviewed_branch": branch,
        "reviewed_port_base": port_base,
        "venue": venue,
    }


def render(fields: dict[str, str], as_yaml: bool) -> str:
    if as_yaml:
        return "\n".join(f"{k}: {v}" for k, v in fields.items())
    return (
        f"- **Reviewed at:** commit `{fields['reviewed_commit']}` on "
        f"`{fields['reviewed_branch']}`, port base `{fields['reviewed_port_base']}`; "
        f"venue {fields['venue']}. *Absent here reads as not-yet-ported, not as broken "
        f"(docs/style/review-provenance.md).*"
    )


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    print(render(stamp(), as_yaml="--yaml" in args))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
