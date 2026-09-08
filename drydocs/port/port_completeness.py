"""port_completeness.py — a roll close proves the clean-add class complete (PORT6).

THE DEFECT. A roll closes COMPLETE on the collision classes — the paths both trees hold
and that differ — and never on the clean-add class, the paths the producer holds and the
consumer does not. Seven paths and four per-entry rows present at ``port-base-20260902``
surfaced two carve-outs later as "not in this roll" AFTER that roll closed COMPLETE
(2026-09-07). Two mechanisms, both confirmed by the consumer session itself:

  1. its per-entry pass merged the RANGE DIFF where the entry_rule says union by id
     against the file at the tag, so a row added in an earlier range and never merged
     is in neither diff and stays invisible to every later pass;
  2. its attribution instrument — ``git diff --numstat <base> <next> -- <path>``, empty
     means "not this roll" — prints empty for a FORGOTTEN path exactly as for a deferred
     one, and only the lineage pair had a named deferral (T24). After a roll closes,
     deferred and missed are indistinguishable.

The consumer ran the by-hand recipe (RELAY-35) at ``port-base-20260905`` and found 113
survivors: 87 owed or deferred once never-port is removed, 82 of them already absent
at a roll closed COMPLETE, 51 falling to the manifest default with nothing recording a
decision. That run is this module's first real-values fixture (J76), and its table's
shape is this module's output shape.

WHAT THIS ANSWERS, AND WHAT IT DOES NOT. This is a PRESENCE check: every path at the
base tag that is absent from the consumer tree, bucketed by the disposition the
manifest resolves for it — through the ONE classifier in ``dispositions.py``, never a
second reading — and, for the union-append class, every ``## `` heading at the tag that
the consumer's copy lacks (entries by heading; the 2026-09-08 gate-log incident,
RELAY-37). It is blind to present-but-divergent content: the T24 shape (``writer.py``
present on both sides, different inside) does not show here, and the per-entry
delta-vs-union defect above is the reconcile guards' subject with a before-dir, not
this one's. Two instruments at every roll close, and neither alone: ``--numstat`` for
"this roll or not" (attribution), this for "ever applied or not" (completeness).

THE DEFERRAL LIST IS BY PATH. A survivor is either applied or named in the roll's
deferral section — a fenced ``deferred-paths`` block in ``docs/port/port-prompt.md``,
one row per path or glob, cumulative across rolls (a path deferred in roll N stays
deferred in roll N+1 until it is applied or the row is retired with a date). T24 is the
prose form of exactly one entry and is its first row. The consumer may pass its own
list too (``--deferrals``), in the same format, for the deferrals only it has ruled.

Pure functions take PATH SETS, TEXT and DOCUMENT MAPS, never a repository — the
``port_preflight`` rule, for the same reason: the guards run without a consumer tree,
which the producer does not have. Only the ``git_*`` helpers and ``main`` shell out.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from drydocs.port.dispositions import DEFAULT, DEFAULT_OK, classify, load_manifest, matches

#: The fenced-block language tag the deferral rows sit under, in the port-prompt and in
#: any ``--deferrals`` file. A fence, not a heading, so the rows are machine-shaped and
#: the prose around them is free.
DEFERRAL_FENCE = "deferred-paths"

#: Classes that never cross and so are never owed — dropped from the table entirely.
EXCLUDED_CLASSES: frozenset[str] = frozenset({"never-port"})

#: Classes listed but NOT owed: the company copy wins a collision, and an absent copy is
#: a ruling for the consumer to make, not a default to take. Shown so nobody mistakes
#: "not owed" for "not there".
RULING_CLASSES: frozenset[str] = frozenset({"canonical-company"})

#: Table order — the apply order, so the table reads as a work plan; ``DEFAULT`` sits
#: where the manifest's clean-add rule applies with nothing recording a decision.
CLASS_ORDER: tuple[str, ...] = (
    DEFAULT,
    "canonical-producer",
    "per-entry",
    "union-append",
    "evaluate",
    DEFAULT_OK,
    "derived",
    "canonical-company",
)

_FENCE_RE = re.compile(r"^```+\s*([A-Za-z0-9_-]*)\s*$")
_H2_RE = re.compile(r"^## (.+?)\s*$")


@dataclass(frozen=True)
class Deferral:
    """One row of a ``deferred-paths`` block: ``pattern | roll | ref | retired``."""

    pattern: str
    roll: str
    ref: str
    retired: str = "-"

    @property
    def active(self) -> bool:
        return self.retired.strip() in ("", "-")


def parse_deferrals(text: str) -> list[Deferral]:
    """Every row inside every ```deferred-paths``` fence in ``text``, in order.

    A row is ``pattern | roll | ref [| retired]``; ``#`` lines and blanks are skipped.
    Rows with fewer than three cells are refused by name — a malformed deferral that
    parsed as nothing would let its path through as un-deferred and fail the roll for
    the wrong reason (J76: the instrument first).
    """
    rows: list[Deferral] = []
    inside = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        fence = _FENCE_RE.match(line.strip())
        if fence:
            if inside:
                inside = False
            elif fence.group(1) == DEFERRAL_FENCE:
                inside = True
            continue
        if not inside:
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        cells = [c.strip() for c in stripped.split("|")]
        if len(cells) < 3 or not all(cells[:3]):
            raise ValueError(
                f"deferred-paths row {lineno} needs `pattern | roll | ref [| retired]`: {line!r}"
            )
        rows.append(Deferral(cells[0], cells[1], cells[2], cells[3] if len(cells) > 3 else "-"))
    return rows


def deferral_for(path: str, deferrals: Iterable[Deferral]) -> Deferral | None:
    """The first ACTIVE deferral whose pattern names ``path``, else None."""
    for d in deferrals:
        if d.active and matches(d.pattern, path):
            return d
    return None


@dataclass(frozen=True)
class Survivor:
    """A path at the base tag that the consumer tree does not hold."""

    path: str
    disposition: str
    pattern: str
    deferral: Deferral | None
    carried: bool | None  # True = also at the previous tag; None = no previous tag given

    @property
    def owed(self) -> bool:
        """Owed = must be applied or deferred; a ruling class is never owed."""
        return self.disposition not in RULING_CLASSES and self.deferral is None


def survivors(
    tag_paths: Iterable[str],
    tree_has: Callable[[str], bool],
    doc: dict,
    deferrals: Iterable[Deferral] = (),
    prev_tag_paths: set[str] | None = None,
) -> list[Survivor]:
    """Every tag path absent from the tree, classified, with its deferral if any."""
    deferrals = list(deferrals)
    out: list[Survivor] = []
    for path in sorted(set(tag_paths)):
        if tree_has(path):
            continue
        disposition, pattern, _ = classify(path, doc)
        if disposition in EXCLUDED_CLASSES:
            continue
        out.append(
            Survivor(
                path,
                disposition,
                pattern,
                deferral_for(path, deferrals),
                None if prev_tag_paths is None else path in prev_tag_paths,
            )
        )
    return out


def headings(markdown: str) -> list[str]:
    """The ``## `` headings of a markdown text, fenced code blocks excluded."""
    out: list[str] = []
    inside = False
    for line in markdown.splitlines():
        if _FENCE_RE.match(line.strip()):
            inside = not inside
            continue
        if inside:
            continue
        m = _H2_RE.match(line)
        if m:
            out.append(m.group(1))
    return out


def missing_headings(tag_text: str, tree_text: str) -> list[str]:
    """Headings the tag's copy has and the tree's copy lacks, in tag order."""
    have = set(headings(tree_text))
    return [h for h in headings(tag_text) if h not in have]


@dataclass(frozen=True)
class HeadingGap:
    path: str
    missing: tuple[str, ...]


def union_append_gaps(
    tag_paths: Iterable[str],
    doc: dict,
    read_tag: Callable[[str], str],
    read_tree: Callable[[str], str | None],
) -> list[HeadingGap]:
    """For every union-append MARKDOWN path present on both sides, the headings owed.

    Absent paths are the clean-add class and belong to ``survivors``; non-markdown
    union-append rows (the epic YAMLs) are unioned by id and are the reconcile guards'
    subject with a before-dir, not this one's.
    """
    out: list[HeadingGap] = []
    for path in sorted(set(tag_paths)):
        if not path.endswith(".md"):
            continue
        disposition, _, _ = classify(path, doc)
        if disposition != "union-append":
            continue
        tree_text = read_tree(path)
        if tree_text is None:
            continue
        missing = missing_headings(read_tag(path), tree_text)
        if missing:
            out.append(HeadingGap(path, tuple(missing)))
    return out


def complete(survivors_: Iterable[Survivor], gaps: Iterable[HeadingGap]) -> bool:
    """COMPLETE = no owed survivor and no union-append heading gap."""
    return not any(s.owed for s in survivors_) and not any(True for _ in gaps)


def render_table(
    base: str,
    survivors_: list[Survivor],
    gaps: list[HeadingGap],
    prev: str | None = None,
) -> str:
    """The consumer's 2026-09-08 table shape: one row per class, carried / new / total."""
    by_class: dict[str, list[Survivor]] = {}
    for s in survivors_:
        by_class.setdefault(s.disposition, []).append(s)
    classes = [c for c in CLASS_ORDER if c in by_class] + sorted(set(by_class) - set(CLASS_ORDER))

    out: list[str] = [f"Completeness at `{base}` — PRESENCE only (blind to present-but-divergent)"]
    if prev:
        out.append(f"carried = also absent at `{prev}` (a roll already closed); new = this roll's")
        out += [
            "",
            "| disposition | carried | new | deferred | owed | total |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    else:
        out += ["", "| disposition | deferred | owed | total |", "|---|---:|---:|---:|"]
    tot = {"carried": 0, "new": 0, "deferred": 0, "owed": 0, "total": 0}
    for c in classes:
        rows = by_class[c]
        n = {
            "carried": sum(1 for s in rows if s.carried),
            "new": sum(1 for s in rows if s.carried is False),
            "deferred": sum(1 for s in rows if s.deferral is not None),
            "owed": sum(1 for s in rows if s.owed),
            "total": len(rows),
        }
        for k in tot:
            tot[k] += n[k]
        label = f"{c} (manifest default)" if c == DEFAULT else c
        if c in RULING_CLASSES:
            label += " (ruling, not owed)"
        if prev:
            out.append(
                f"| {label} | {n['carried']} | {n['new']} | {n['deferred']} | {n['owed']} | {n['total']} |"
            )
        else:
            out.append(f"| {label} | {n['deferred']} | {n['owed']} | {n['total']} |")
    if prev:
        out.append(
            f"| TOTAL | {tot['carried']} | {tot['new']} | {tot['deferred']} | {tot['owed']} | {tot['total']} |"
        )
    else:
        out.append(f"| TOTAL | {tot['deferred']} | {tot['owed']} | {tot['total']} |")

    for c in classes:
        out += ["", f"## {c} — {len(by_class[c])} path(s)"]
        for s in by_class[c]:
            tag = "  [carried]" if s.carried else ("  [new]" if s.carried is False else "")
            if s.deferral is not None:
                out.append(f"- {s.path}{tag}  deferred: {s.deferral.roll} ({s.deferral.ref})")
            elif s.disposition in RULING_CLASSES:
                out.append(f"- {s.path}{tag}  ruling: yours to hold or take")
            else:
                out.append(f"- {s.path}{tag}  OWED")

    out += ["", f"## union-append headings — {len(gaps)} file(s) with headings owed"]
    for g in gaps:
        out.append(f"- {g.path}: {len(g.missing)} heading(s) at the tag absent here")
        out += [f"  - {h}" for h in g.missing]

    owed = sum(1 for s in survivors_ if s.owed)
    verdict = "COMPLETE" if complete(survivors_, gaps) else "NOT COMPLETE"
    out += [
        "",
        f"{verdict}: {owed} owed path(s) not deferred, {len(gaps)} union-append file(s) with "
        "headings owed. Apply each, or name it in a deferred-paths row.",
    ]
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- git-backed half


def git_out(repo: Path, *args: str) -> str | None:
    """stdout of a git call in ``repo``, or None when git fails — callers decide what
    None means; nothing here turns a failed call into an empty list (J76)."""
    try:
        return subprocess.run(
            ["git", *args], cwd=repo, capture_output=True, encoding="utf-8", check=True
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def git_ref_resolves(repo: Path, ref: str) -> bool:
    return bool(
        (git_out(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}") or "").strip()
    )


def git_ls_tree(repo: Path, ref: str) -> set[str]:
    out = git_out(repo, "ls-tree", "-r", "--name-only", "-z", ref)
    if out is None:
        raise RuntimeError(f"git ls-tree failed for {ref}")
    return {p for p in out.split("\0") if p}


def git_show(repo: Path, ref: str, path: str) -> str | None:
    return git_out(repo, "show", f"{ref}:{path}")


PORT_PROMPT = "docs/port/port-prompt.md"


def deferrals_from(repo: Path, base: str, tree: Path, extra: Iterable[Path]) -> list[Deferral]:
    """The deferral rows in force: the port-prompt AT THE TAG (the producer's roll record,
    which never ports and is read from the tag), the tree's own copy where one exists
    (producer-side it may be newer), and every ``--deferrals`` file."""
    texts: list[str] = []
    at_tag = git_show(repo, base, PORT_PROMPT)
    if at_tag is not None:
        texts.append(at_tag)
    local = tree / PORT_PROMPT
    if local.exists():
        texts.append(local.read_text(encoding="utf-8"))
    for p in extra:
        texts.append(Path(p).read_text(encoding="utf-8"))
    rows: list[Deferral] = []
    seen: set[tuple[str, str, str, str]] = set()
    for t in texts:
        for d in parse_deferrals(t):
            key = (d.pattern, d.roll, d.ref, d.retired)
            if key not in seen:
                seen.add(key)
                rows.append(d)
    return rows


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="port_completeness_check.py",
        description=(
            "Roll-close COMPLETENESS check (PORT6): every path at <base-tag> absent from the "
            "consumer tree, bucketed by the disposition PORT-MANIFEST.yaml resolves for it, "
            "plus every `## ` heading a union-append markdown file has at the tag and lacks "
            "here. Exit 0 only when every survivor is deferred by path or is a ruling class. "
            "PRESENCE ONLY: blind to present-but-divergent content (the T24 shape); pair it "
            "with `git diff --numstat <base> <next> -- <path>`, which answers 'this roll or "
            "not', never 'ever applied or not'."
        ),
    )
    p.add_argument("base", help="the producer base tag you are closing, e.g. port-base-20260905")
    p.add_argument(
        "--prev",
        help="the previous base tag; splits survivors into carried (already absent at a closed roll) / new",
    )
    p.add_argument(
        "--tree",
        type=Path,
        help="the consumer working tree to check (default: the repo the command runs in)",
    )
    p.add_argument(
        "--repo", type=Path, help="the git repository the tags resolve in (default: the tree)"
    )
    p.add_argument(
        "--manifest",
        type=Path,
        help="PORT-MANIFEST.yaml to classify with (default: <tree>/PORT-MANIFEST.yaml)",
    )
    p.add_argument(
        "--deferrals",
        type=Path,
        action="append",
        default=[],
        help="an extra file holding ```deferred-paths``` rows (your own rulings); repeatable",
    )
    p.add_argument(
        "--paths-only", action="store_true", help="print owed paths, one per line, and nothing else"
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    tree = (args.tree or Path.cwd()).resolve()
    repo = (args.repo or tree).resolve()
    manifest = args.manifest or tree / "PORT-MANIFEST.yaml"
    if not manifest.exists():
        print(f"no manifest at {manifest}", file=sys.stderr)
        return 2
    for ref in [args.base] + ([args.prev] if args.prev else []):
        if not git_ref_resolves(repo, ref):
            print(f"ref does not resolve in {repo}: {ref} — nothing checked", file=sys.stderr)
            return 2
    doc = load_manifest(manifest)
    tag_paths = git_ls_tree(repo, args.base)
    prev_paths = git_ls_tree(repo, args.prev) if args.prev else None
    try:
        deferrals = deferrals_from(repo, args.base, tree, args.deferrals)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    found = survivors(tag_paths, lambda p: (tree / p).exists(), doc, deferrals, prev_paths)

    def read_tree(path: str) -> str | None:
        f = tree / path
        return f.read_text(encoding="utf-8", errors="replace") if f.exists() else None

    gaps = union_append_gaps(
        tag_paths, doc, lambda p: git_show(repo, args.base, p) or "", read_tree
    )
    if args.paths_only:
        for s in found:
            if s.owed:
                print(s.path)
        for g in gaps:
            print(f"{g.path}  # {len(g.missing)} heading(s) owed")
    else:
        print(render_table(args.base, found, gaps, args.prev), end="")
    return 0 if complete(found, gaps) else 1
