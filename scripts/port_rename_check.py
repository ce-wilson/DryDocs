"""port_rename_check.py — J72: a rename reads as a CLEAN-ADD on the receiving side.

Run this from the CONSUMER (company) repo, BEFORE applying a slice of clean-adds.
It reads the producer tree at the recorded port base (a git ref — the
``port-base-YYYYMMDD`` tag, never ``HEAD``), takes every path that is absent
here, and compares its CONTENT against the files you already hold under a
different name.

Usage, from the company checkout with the producer remote fetched:

    poetry run python scripts/port_rename_check.py --producer-ref port-base-20260901

    # limit to the slice you are about to apply
    poetry run python scripts/port_rename_check.py --producer-ref port-base-20260901 \\
        --path-prefix config/

    # both known traps were in-directory; widen only for a deliberate sweep
    poetry run python scripts/port_rename_check.py --producer-ref cewilson/main --any-directory

Exit 0 = no proposed clean-add resembles a file you already hold. Exit 1 = at
least one does; READ BOTH before applying either. Exit 2 = a side could not be
read, which is a failure and never an empty set — the same rule
``port_backlog_union.py`` follows, and for the same reason: a check that reports
"nothing found" when it actually found nothing to look at is worse than no check.

WHY IT EXISTS (2026-09-01, two instances in one apply): ``41-local-seal.yaml``
became ``41-local-business-application.yaml`` and ``fcdo-crosswalk.yaml`` became
``cdo-crosswalk.yaml``. Both were clean-adds BY PATH. The first duplicated 16
vocabulary ids and cost 62 failures; the second would have imported a gate
sign-off the company deliberately withholds, into a ``canonical-company`` path.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from drydocs.port_rename_detect import rename_candidates, report
from drydocs_core.repo_paths import repo_root

REPO = repo_root(Path(__file__).resolve().parents[1])

#: Text-ish files only. A rename of a PNG is not a thing this can reason about,
#: and decoding one wastes the run.
READABLE_SUFFIXES = {".yaml", ".yml", ".json", ".md", ".py", ".cypher", ".sql", ".ts", ".tsx"}


def _git(*args: str) -> str:
    """Git output, decoded as UTF-8 EXPLICITLY.

    ``text=True`` alone decodes with the platform locale, which on Windows is
    cp1252 — it raises on a byte it cannot map and, worse, silently mojibakes an
    em-dash when it can. That is not hypothetical here: a company-side comparison
    script did exactly this on 2026-09-01 and fabricated 18 of 25 reported
    "differences", and the first run of THIS script raised
    ``UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d`` on the same
    repo. A similarity check that mis-decodes one side compares a corrupted
    document against a clean one and reports the corruption as a difference —
    the precise failure it exists to prevent, wearing the opposite sign.
    """
    result = subprocess.run(
        ["git", *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout


def producer_files(ref: str, prefix: str) -> dict[str, str]:
    """``{path: text}`` for every readable file under ``prefix`` at ``ref``."""
    paths = [
        p
        for p in _git("ls-tree", "-r", "--name-only", ref).splitlines()
        if p.startswith(prefix) and Path(p).suffix in READABLE_SUFFIXES
    ]
    if not paths:
        raise SystemExit(
            f"exit 2: no readable files under {prefix!r} at {ref!r}. "
            "An empty producer side is a failure, not agreement — check the ref."
        )
    out: dict[str, str] = {}
    for path in paths:
        try:
            out[path] = _git("show", f"{ref}:{path}")
        except SystemExit:
            continue  # unreadable blob; skipped rather than fatal
    return out


def consumer_files(prefix: str) -> dict[str, str]:
    """``{path: text}`` for every readable tracked file under ``prefix`` HERE."""
    out: dict[str, str] = {}
    for path in _git("ls-files").splitlines():
        if not path.startswith(prefix) or Path(path).suffix not in READABLE_SUFFIXES:
            continue
        try:
            out[path] = (REPO / path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--producer-ref", required=True, help="port-base-YYYYMMDD tag, never HEAD")
    parser.add_argument("--path-prefix", default="", help="limit to the slice being applied")
    parser.add_argument(
        "--any-directory",
        action="store_true",
        help="compare across directories too (slower; both known traps were in-directory)",
    )
    args = parser.parse_args(argv)

    producer = producer_files(args.producer_ref, args.path_prefix)
    consumer = consumer_files(args.path_prefix)
    if not consumer:
        raise SystemExit(
            f"exit 2: no readable tracked files under {args.path_prefix!r} HERE. "
            "An empty consumer side cannot be compared against."
        )

    proposed = {path: text for path, text in producer.items() if path not in consumer}
    print(
        f"producer {args.producer_ref}: {len(producer)} readable file(s); "
        f"here: {len(consumer)}; proposed clean-adds: {len(proposed)}"
    )
    candidates = rename_candidates(proposed, consumer, same_directory_only=not args.any_directory)
    print()
    print(report(candidates))
    return 1 if candidates else 0


if __name__ == "__main__":
    sys.exit(main())
