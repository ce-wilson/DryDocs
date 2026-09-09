"""port_drops.py — the file-level port DROP check, with the accepted-drop seam (PORT4).

THE DEFECT. A port apply removes files: a canonical-producer take of a directory retires
every path the producer retired, and the consumer's own rulings retire more (their
port-prompt stub, their pre-J34 `default_ok` rows). The consumer's chunk-by-chunk audit
of what a take REMOVED is a diff against the pre-port tag — `git diff --diff-filter=D
<pre-port-tag> HEAD` — which is cumulative by construction: a path retired at chunk 1 is
still absent at chunk 5, so it is reported again at every chunk, and a retirement the
port already RULED reads like a new finding each time (the company's chunk-5 apply of
`port-base-20260902`, their idea inbox, relayed 2026-09-04; groomed to PORT4). Nothing
recorded that a specific drop was ruled, so "not yet looked at" and "looked at and
accepted" rendered identically.

THE SEAM. An ``accepted_drops:`` block in the SIDE-LOCAL overlay (``PORT-MANIFEST.*.yaml``,
the J34 slot), one row per ruled path, carrying the ruling's provenance: the report that
ruled it, the date, and the reason. Side-local on purpose: an accepted drop is one side's
ruling about its own tree, and the J34 rule is that a side's rulings never cross. The block
is NOT one of the manifest blocks the guards union (``UNIONED_BLOCKS`` in the reconcile
guards): it declares no disposition and adds no coverage, it records decisions, and only
this check reads it.

THE SHAPE is ``UNION_EXCLUSIONS`` from ``port_backlog_union`` one level down, and it has
three states, none of them silence:

  1. a dropped path with no row is a FINDING — reported exactly as before;
  2. a dropped path with a row is LISTED under its own heading as ruled — never silence
     and never a failure, so a ruled omission cannot read the same as no omission;
  3. a STALE row FAILS: the path exists again (the drop it describes is no longer true),
     or nothing dropped it (the row describes no drop at all). This clause is what makes
     the block safe to have — an allowance that outlives its fact is caught by the check
     it was written for.

Each dropped path is bucketed by the disposition the manifest resolves for it, through
the ONE classifier in ``dispositions.py``: a canonical-producer drop is the take's doing
(the producer retired the path); a DEFAULT or canonical-company drop is the consumer's
own retirement and needs the consumer's own ruling. The disposition is context on the
row, never a filter — a drop in any class is reported until it is ruled.

Pure functions take PATH SETS and a loaded document, never a repository — the
``port_preflight`` rule, so the guards run without a consumer tree, which the producer
does not have. Only the ``git_*`` helpers and ``main`` shell out.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import yaml

from drydocs.port.dispositions import classify, load_manifest
from drydocs.port.port_completeness import git_out, git_ref_resolves

#: The overlay block this check reads. Deliberately absent from the reconcile guards'
#: ``UNIONED_BLOCKS``: rulings are side-local and never join the manifest view.
ACCEPTED_DROPS_BLOCK = "accepted_drops"

#: Every row names the path and the ruling's provenance — which report, when, and why.
#: A row without a report id is a drop somebody remembers, not one somebody ruled.
REQUIRED_FIELDS = ("path", "report", "date", "reason")


class AcceptedDropError(ValueError):
    """The block is malformed — a ruling that cannot be read excuses nothing."""


@dataclass(frozen=True)
class AcceptedDrop:
    path: str
    report: str
    date: str
    reason: str
    #: which overlay file declared it — the report names the file so a stale row can be
    #: found and retired
    source: str = ""


def parse_accepted_drops(overlay_doc: object, source: str = "") -> list[AcceptedDrop]:
    """The ``accepted_drops`` rows of one loaded overlay, validated.

    An overlay with no block declares nothing (the block is optional — most overlays
    exist for `default_ok` rows and never rule a drop). A block that is present must be
    a list of complete rows; a duplicate path is a guard error, because two rulings for
    one path is a contradiction, not extra coverage.
    """
    if overlay_doc is None:
        return []
    if not isinstance(overlay_doc, dict):
        raise AcceptedDropError(f"{source or 'overlay'}: the overlay is not a mapping")
    rows = overlay_doc.get(ACCEPTED_DROPS_BLOCK)
    if rows is None:
        return []
    if not isinstance(rows, list):
        raise AcceptedDropError(
            f"{source or 'overlay'}: `{ACCEPTED_DROPS_BLOCK}:` must be a list (empty is fine)"
        )
    out: list[AcceptedDrop] = []
    seen: set[str] = set()
    for i, row in enumerate(rows, start=1):
        where = f"{source or 'overlay'} {ACCEPTED_DROPS_BLOCK}[{i}]"
        if not isinstance(row, dict):
            raise AcceptedDropError(f"{where} is not a mapping")
        missing = [k for k in REQUIRED_FIELDS if not str(row.get(k, "") or "").strip()]
        if missing:
            raise AcceptedDropError(
                f"{where} is missing {missing} — a ruled drop names the path, the report "
                "that ruled it, the date, and the reason"
            )
        path = str(row["path"]).strip()
        if any(ch in path for ch in "*?["):
            raise AcceptedDropError(
                f"{where}: {path!r} is a glob — a ruling names ONE path; a pattern would "
                "excuse drops nobody looked at"
            )
        if path in seen:
            raise AcceptedDropError(f"{where}: {path!r} is ruled twice — one ruling per path")
        seen.add(path)
        out.append(
            AcceptedDrop(
                path=path,
                report=str(row["report"]).strip(),
                date=str(row["date"]).strip(),
                reason=str(row["reason"]).strip(),
                source=source,
            )
        )
    return out


def load_accepted_drops(manifest_doc: dict, repo: Path) -> list[AcceptedDrop]:
    """Every accepted drop declared in an EXISTING overlay the manifest names.

    Reads the manifest's own ``overlay.files`` declaration rather than globbing for
    ``PORT-MANIFEST.*.yaml``, so the set of files that may rule a drop is the set the
    J34 seam declares. The other side's slot is absent here by design and contributes
    nothing; a side with no overlay has ruled nothing, and the check then reports every
    drop as a finding — exactly the pre-seam behavior.
    """
    out: list[AcceptedDrop] = []
    for declared in (manifest_doc.get("overlay") or {}).get("files", []):
        overlay_file = repo / declared["path"]
        if not overlay_file.exists():
            continue
        doc = yaml.safe_load(overlay_file.read_text(encoding="utf-8"))
        out.extend(parse_accepted_drops(doc, source=declared["path"]))
    dupes = sorted({d.path for d in out if sum(1 for e in out if e.path == d.path) > 1})
    if dupes:
        raise AcceptedDropError(f"a path is ruled in more than one overlay: {dupes}")
    return out


@dataclass(frozen=True)
class DropReport:
    """The answer, with ruled drops kept distinct from findings and from silence."""

    #: the ref the drops were measured against — printed so the report is reproducible
    since: str
    #: (path, disposition) for every drop with NO ruling — the findings
    findings: tuple[tuple[str, str], ...]
    #: (path, disposition, ruling) for every drop a row covers — listed, never failed
    accepted: tuple[tuple[str, str, AcceptedDrop], ...]
    #: rows that describe no drop any more: (ruling, what is wrong)
    stale: tuple[tuple[AcceptedDrop, str], ...]

    @property
    def passed(self) -> bool:
        return not self.findings and not self.stale

    def render(self) -> str:
        """The port-report block. States the ruled drops even when there are no findings —
        a ruled retirement must never read the same as no retirement."""
        lines = [
            f"PORT DROP CHECK (PORT4) -- paths removed since {self.since}, "
            "against the side-local accepted_drops rulings",
        ]
        if self.findings:
            lines.append(f"  DROPPED, UNRULED ({len(self.findings)}) -- findings:")
            lines.extend(f"    - {path}  [{disp}]" for path, disp in self.findings)
        else:
            lines.append("  dropped, unruled: none")
        if self.accepted:
            lines.append(f"  accepted drops ({len(self.accepted)}) -- ruled, not findings:")
            lines.extend(
                f"    - {path}  [{disp}]  {r.report} {r.date}: {r.reason}"
                for path, disp, r in self.accepted
            )
        else:
            lines.append("  accepted drops: none declared")
        if self.stale:
            lines.append(f"  STALE ACCEPTED-DROP ROWS ({len(self.stale)}) -- retire them:")
            lines.extend(
                f"    - {r.path} ({r.source or 'overlay'}): {why}" for r, why in self.stale
            )
        lines.append("  RESULT: " + ("PASS" if self.passed else "FAIL"))
        if self.findings:
            lines.append(
                "  An unruled drop is a path the apply removed and nobody ruled on. Restore it, "
                f"or rule it: add its path to the `{ACCEPTED_DROPS_BLOCK}:` block of your "
                "side-local overlay (PORT-MANIFEST.<side>.yaml) with the report, date and reason."
            )
        if self.stale:
            lines.append(
                "  A stale row excuses nothing and fails the check until it is retired: the path "
                "is back, or nothing ever dropped it."
            )
        return "\n".join(lines) + "\n"


def check_drops(
    dropped: Iterable[str],
    present: Iterable[str],
    accepted: Iterable[AcceptedDrop],
    manifest_doc: dict,
    since: str = "<since>",
) -> DropReport:
    """Pure: the dropped paths, the paths present now, the rulings, the manifest.

    ``dropped`` is every path the tree held at the since-ref and does not hold now;
    ``present`` is every path it holds now. A ruling is stale when its path is present
    (the drop is no longer true) or when its path is neither present nor dropped
    (nothing dropped it — the row describes no drop).
    """
    dropped_set = set(dropped)
    present_set = set(present)
    rulings = {a.path: a for a in accepted}

    def disp(path: str) -> str:
        return classify(path, manifest_doc)[0]

    findings = tuple((p, disp(p)) for p in sorted(dropped_set - set(rulings)))
    ruled = tuple((p, disp(p), rulings[p]) for p in sorted(dropped_set & set(rulings)))
    stale: list[tuple[AcceptedDrop, str]] = []
    for path in sorted(rulings):
        if path in present_set:
            stale.append(
                (rulings[path], "the path exists again — the accepted drop is no longer true")
            )
        elif path not in dropped_set:
            stale.append((rulings[path], "nothing dropped this path — the row describes no drop"))
    return DropReport(since=since, findings=findings, accepted=ruled, stale=tuple(stale))


# ---------------------------------------------------------------- git-backed half


def git_dropped_paths(repo: Path, since: str) -> set[str]:
    """Paths tracked at ``since`` and not at HEAD — the cumulative drop set."""
    out = git_out(repo, "diff", "--name-only", "--diff-filter=D", "-z", since, "HEAD")
    if out is None:
        raise RuntimeError(f"git diff --diff-filter=D failed for {since}..HEAD")
    return {p for p in out.split("\0") if p}


def git_tracked_paths(repo: Path) -> set[str]:
    """Paths tracked at HEAD — the working index, so a restored-but-uncommitted path
    counts as present (the index is the tree an apply commits)."""
    out = git_out(repo, "ls-files", "-z")
    if out is None:
        raise RuntimeError("git ls-files failed")
    return {p for p in out.split("\0") if p}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="port_drop_check",
        description=(
            "List every path removed since a ref, bucketed by disposition, against the "
            "side-local accepted_drops rulings. Run from the consumer apply tree."
        ),
    )
    p.add_argument(
        "since",
        help="the ref the drops are measured from — the pre-port tag, never HEAD",
    )
    p.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="the consumer repository (default: the working directory)",
    )
    p.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="PORT-MANIFEST.yaml to classify with (default: <repo>/PORT-MANIFEST.yaml)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo: Path = args.repo.resolve()
    manifest_path = args.manifest or repo / "PORT-MANIFEST.yaml"
    if not manifest_path.exists():
        print(f"no manifest at {manifest_path}", file=sys.stderr)
        return 2
    if not git_ref_resolves(repo, args.since):
        print(f"{args.since!r} does not resolve to a commit in {repo}", file=sys.stderr)
        return 2
    manifest_doc = load_manifest(manifest_path)
    try:
        rulings = load_accepted_drops(manifest_doc, repo)
        report = check_drops(
            git_dropped_paths(repo, args.since),
            git_tracked_paths(repo),
            rulings,
            manifest_doc,
            since=args.since,
        )
    except (AcceptedDropError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    sys.stdout.write(report.render())
    return 0 if report.passed else 1
