"""render_port_dispositions.py — classify a port range's changed paths by DISPOSITION (J69).

WHY THIS EXISTS. `docs/port/port-prompt.md` is organized as a chronological step
ledger, and a port is not applied chronologically. The 2026-09-01 company apply
bucketed 88 diverged paths into the manifest's disposition classes and worked them
class by class; the step ledger was reference material while that happened. The
file's spine and the consumer's spine were different, and this renders the
consumer's.

WHY IT IS DERIVED AND NOT WRITTEN BY HAND. A hand-kept copy of the manifest inside
the port-prompt would be a SECOND source of disposition truth — which is the exact
defect J68 removed from the reconcile-port skill, where four hand-kept disposition
assertions had drifted and two were wrong. The rule that came out of J68 is that
`PORT-MANIFEST.yaml` owns disposition and nothing else may assert it; a generated
table obeys that rule, a typed one does not.

Output is `docs/port/port-dispositions.md` and it is DELIBERATELY NOT COMMITTED.
Its range is `<base>..HEAD`, so a committed copy would go stale on every commit and a
drift guard over it would red the suite constantly — a guard people learn to work
around is worse than no guard. The file is gitignored working state; the MECHANISM is
what carries guards (`tests/unit/test_port_dispositions.py`). Regenerate it per apply,
naming the base you are applying FROM.
"""

from __future__ import annotations

import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import yaml

from drydocs_core.repo_paths import repo_root

REPO = repo_root(Path(__file__).resolve().parents[1])
MANIFEST = REPO / "PORT-MANIFEST.yaml"
OUT = REPO / "docs" / "port" / "port-dispositions.md"

#: Apply order, and it is not alphabetical — it is the order a session works them.
#: Wholesale takes first (they are mechanical), hand-merges in the middle, and
#: `derived` last because a render regenerated before its sources land is a render
#: that has to be thrown away. The company's own 2026-09-01 apply ran this order.
APPLY_ORDER: tuple[tuple[str, str], ...] = (
    ("clean-add", "apply untouched — the path is absent your side, so there is nothing to merge"),
    ("canonical-producer", "take wholesale — `git checkout <producer-ref> -- <path>`"),
    ("canonical-company", "NO ACTION by rule — keep yours, do not diff"),
    ("never-port", "NO ACTION by rule — never crosses, in either direction"),
    ("per-entry", "MERGE BY ENTRY — read the row's `entry_rule` before touching the file"),
    ("union-append", "append the producer's entries; never reorder or drop yours"),
    ("evaluate", "HAND-MERGE — an un-made decision until a human makes it"),
    (
        "DEFAULT",
        "the manifest `default:` rule — clean-add when absent, evaluate when both sides have it",
    ),
    ("default_ok", "the default ON PURPOSE (J16) — the row exists to say someone thought about it"),
    ("derived", "REGENERATE LAST, never carry — the J43 rule"),
)


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def newest_base_tag() -> str:
    """The most recent `port-base-*` tag — the base a consumer applies FROM."""
    tags = [t for t in _git("tag", "--list", "port-base-*").split() if t]
    return sorted(tags)[-1] if tags else ""


def changed_paths(base: str, head: str = "HEAD") -> list[str]:
    return sorted(p for p in _git("diff", "--name-only", f"{base}..{head}").splitlines() if p)


def classify(path: str, doc: dict) -> tuple[str, str, str]:
    """``(disposition, matching pattern, entry_rule)`` — first match wins.

    Rows are checked in file order because the manifest is first-match-wins and
    `test_no_row_is_shadowed_by_an_earlier_glob` already guarantees a specific row
    precedes the glob that would swallow it. `default_ok` is consulted only after
    every row misses, which is what makes "deliberately default" distinguishable
    from "nobody thought about it" — the distinction J16 exists for.
    """
    from tests.unit.test_port_reconcile_guards import glob_to_regex

    for row in doc["rows"]:
        pattern = row["path"]
        if pattern == path or glob_to_regex(pattern).match(path):
            return row["disposition"], pattern, (row.get("entry_rule") or "").strip()
    for row in doc.get("default_ok") or []:
        pattern = row["path"]
        if pattern == path or glob_to_regex(pattern).match(path):
            return "default_ok", pattern, ""
    return "DEFAULT", "(no row)", ""


def render(base: str, paths: list[str], doc: dict) -> str:
    buckets: dict[str, list[tuple[str, str]]] = defaultdict(list)
    rules: dict[str, str] = {}
    for path in paths:
        disposition, pattern, entry_rule = classify(path, doc)
        buckets[disposition].append((path, pattern))
        if entry_rule:
            rules[pattern] = entry_rule

    out: list[str] = [
        "# Port dispositions — the apply order",
        "",
        "<!-- GENERATED by scripts/render_port_dispositions.py — do not edit by hand.",
        "     PORT-MANIFEST.yaml owns disposition (J68); this file only sorts by it. -->",
        "",
        f"Range `{base}..HEAD` — **{len(paths)} changed paths** in "
        f"**{len([d for d, _ in APPLY_ORDER if buckets.get(d)])} classes**.",
        "",
        "Work the classes in the order below. Within a class the paths are"
        " alphabetical, not prioritized — the class carries the rule, the path does not.",
        "",
        "| Class | Paths | Rule |",
        "|---|---:|---|",
    ]
    for disposition, rule in APPLY_ORDER:
        if buckets.get(disposition):
            out.append(f"| `{disposition}` | {len(buckets[disposition])} | {rule} |")
    unknown = sorted(set(buckets) - {d for d, _ in APPLY_ORDER})
    for disposition in unknown:
        out.append(
            f"| `{disposition}` | {len(buckets[disposition])} | (not in APPLY_ORDER — add it) |"
        )

    for disposition, rule in (*APPLY_ORDER, *((u, "") for u in unknown)):
        rows = buckets.get(disposition)
        if not rows:
            continue
        out += [
            "",
            f"## `{disposition}` — {len(rows)} path(s)",
            "",
            f"**{rule}**" if rule else "",
            "",
        ]
        patterns = sorted({pattern for _, pattern in rows})
        for pattern in patterns:
            governed = [p for p, pat in rows if pat == pattern]
            out.append(f"- **`{pattern}`** — {len(governed)} path(s)")
            out += [f"  - `{p}`" for p in governed]
            if pattern in rules:
                out.append(f"  - *entry_rule:* {' '.join(rules[pattern].split())}")
    return "\n".join(out).rstrip() + "\n"


def main(argv: list[str]) -> int:
    base = argv[0] if argv else newest_base_tag()
    if not base:
        print("no port-base-* tag found and no base given", file=sys.stderr)
        return 1
    doc = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    paths = changed_paths(base)
    OUT.write_text(render(base, paths, doc), encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(REPO)} — {len(paths)} paths from {base}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
