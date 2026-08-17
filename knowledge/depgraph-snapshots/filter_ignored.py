"""U9 — drop git-ignored paths from an all-files snapshot, in place.

`depgraph scan --tree` walks the filesystem. It excludes `.git` and `.venv` but
knows nothing about `.gitignore`, so a whole-repo scan picks up build caches --
384 `.ruff_cache/` entries and `var/` in the first run of the all-files ritual,
~18% of the artifact. Those are not the project; loading them makes every
per-directory count wrong and puts tool droppings in a graph that is supposed to
describe the repository.

Placed here rather than in the loader on purpose: the artifact itself should be
clean, so the committed JSON and viewer.html show the same thing the graph does.
Placed here rather than in depgraph because the ignore rules are this repo's, not
the scanner's -- depgraph is a general instrument and has no opinion about them.

Classification uses `git check-ignore`, so the rule set is exactly the repo's own
(.gitignore + excludes + global config) and cannot drift from it.

Usage:  python filter_ignored.py <snapshot.json> <repo-root>
Writes the file back only when something was removed; prints a one-line summary.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def ignored_paths(repo: Path, rel_paths: list[str]) -> set[str]:
    """Return the subset git considers ignored. One batched call, not one per file.

    NUL-separated and BINARY on purpose, both halves load-bearing on Windows:
    `text=True` translates \\n to \\r\\n on the way into stdin, so git receives
    '.env\\r' as the path name; and in line mode git QUOTES any name it considers
    unusual, handing back '".env\\r"'. Either alone silently breaks the match --
    the filter reported "no git-ignored paths" against a snapshot holding 386 of
    them. `-z` removes the quoting and the newline translation together.
    """
    if not rel_paths:
        return set()
    proc = subprocess.run(
        ["git", "check-ignore", "-z", "--stdin"],
        cwd=repo,
        input="\0".join(rel_paths).encode("utf-8"),
        capture_output=True,
        check=False,
    )
    # exit 0 = some ignored, 1 = none ignored, >1 = real error
    if proc.returncode > 1:
        raise SystemExit(
            f"git check-ignore failed ({proc.returncode}): {proc.stderr.decode(errors='replace')}"
        )
    out = proc.stdout.decode("utf-8", errors="replace")
    return {p.replace("\\", "/") for p in out.split("\0") if p}


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    path, repo = Path(sys.argv[1]), Path(sys.argv[2])
    doc = json.loads(path.read_text(encoding="utf-8"))

    nodes = doc.get("nodes") or []
    # rel_path is repo-relative in tree mode; file_id carries a project prefix.
    by_rel = {n["file_id"]: (n.get("rel_path") or "").replace("\\", "/") for n in nodes}
    ignored = ignored_paths(repo, sorted({r for r in by_rel.values() if r and r != "."}))
    drop = {fid for fid, rel in by_rel.items() if rel in ignored}
    if not drop:
        print("no git-ignored paths in snapshot")
        return 0

    doc["nodes"] = [n for n in nodes if n["file_id"] not in drop]
    doc["edges"] = [e for e in (doc.get("edges") or []) if e[0] not in drop and e[1] not in drop]
    rels = doc.get("rels")
    if isinstance(rels, list):
        # A rel is [src, TYPE, dst] — endpoints are [0] and [2], NOT [0]/[1].
        # The original check read [1] (the TYPE string, never in drop), so every
        # CONTAINS rel to a dropped node survived, leaking git-ignored FILENAMES
        # into the committed artifact (caught 2026-08-04 by the J15 value guard:
        # gitignored workbook screenshots in the repo root). Belt and braces:
        # after the drop, also require both endpoints to EXIST as nodes, so any
        # future shape drift dangles nothing instead of leaking names.
        kept_ids = {n["file_id"] for n in doc["nodes"]}
        doc["rels"] = [
            r
            for r in rels
            if isinstance(r, list | tuple) and len(r) >= 3 and r[0] in kept_ids and r[2] in kept_ids
        ]

    stats = doc.get("stats")
    if isinstance(stats, dict):
        kinds = [n.get("kind") for n in doc["nodes"]]
        stats["files"] = kinds.count("file")
        stats["directories"] = kinds.count("dir")
        stats["edges"] = len(doc["edges"])
        if isinstance(doc.get("rels"), list):
            stats["rels"] = len(doc["rels"])

    # newline="\n" or Python text mode emits \r\n on Windows and the committed
    # artifact lands CRLF against an LF index (Idea-129, the Idea-121 class in the
    # snapshot pipeline). This is the LAST writer on the ritual path, so it decides
    # the committed bytes — except on the early return above, which is why
    # snapshot.ps1 normalizes too.
    path.write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"dropped {len(drop)} git-ignored node(s); {len(doc['nodes'])} remain")
    return 0


if __name__ == "__main__":
    sys.exit(main())
