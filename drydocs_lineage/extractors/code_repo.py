"""Code-repo source seam + server/repo corroboration (G24).

The SECOND provenance origin for script artifacts. G20 stages what is ON the
server (``origin=server-extract``: host + path + mtime, content copies where
the collector carried them); this seam stages what is IN the code repo
(``origin=code-repo``: repo + ref + commit + path), in the SAME staging shape
— :class:`~drydocs_lineage.model.ProcessNode` records on the same
:class:`~drydocs_lineage.model.LineageGraph` — differing only in provenance.

Real Bitbucket/GitHub access stays company-side BEHIND this seam: the input is
a MANIFEST file the company tooling produces with one object sweep
(``git rev-list --all --objects`` + ref tips — never branch guesswork),
mechanism-only here, SYNTHETIC in fixtures. Manifest contract
(``repo_objects.tsv``, tab-separated, header required)::

    repo    ref    commit    commit_date    path    blob_sha

    - one row per (ref-tip, path): ``ref`` names a live ref whose TIP
      contains the blob at ``path``;
    - one row with an EMPTY ``ref`` per blob that appears only in HISTORY
      (the --all sweep saw it at ``commit``, no live tip carries it).

The CORROBORATION report joins the two origins on CONTENT HASH — the git blob
sha1 of each carried-back server copy (``sha1("blob <len>\\0" + content)``)
against the manifest's ``blob_sha`` — into verdict buckets:

    found_at_refs    server blob at >=1 live ref tip, WITH the refs + commit
                     dates: the most recent match names the DE-FACTO current
                     branch mechanically (``candidate_ref``);
    behind           only historical commits match — the running code is
                     ahead of everything committed;
    never_committed  the observed failure mode: production code absent from
                     the repo (path-tail hints listed as weak fallback until
                     the G22 URN ruling);
    repo_only        repo blobs no server copy matches.

Honest limit: locally EDITED running code matches no repo object at all, so
pure content hashing cannot tell edited-after-checkout from never-committed —
both land in ``never_committed``, and the path-tail hints are the weak signal
that a same-named ancestor exists in the repo. Precedence between the origins
is a G22 ruling, not a bucket.

TRUST is never inferred: ``trusted_ref`` is the nullable human-blessed field
on the source-registry entry (null = server-extract-only truth — the
stale-main case). The report only CHECKS the blessed ref against the
mechanical findings. Identity stays origin-scoped (``repo_script`` vs
``rua_script``) — whether the two are ONE node is the G22 identity/dedup
ruling. NO graph writes, no new relationship types; every unmatched or
uncomputable record is counted, never dropped.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from pathlib import Path

from ..model import LineageGraph, ProcessNode, process_id
from .rua_inventory import RUA_SCRIPT_KIND, RuaInventoryExtractor

#: staged kind for repo-origin script artifacts — deliberately NOT rua_script
#: (cross-origin identity is the G22 ruling; the join is the corroboration
#: report, never an id collision)
REPO_SCRIPT_KIND = "repo_script"

MANIFEST_COLUMNS = ("repo", "ref", "commit", "commit_date", "path", "blob_sha")


def git_blob_sha1(content: bytes) -> str:
    """The git blob object id of *content* — ``sha1('blob <len>\\0' + content)``.

    Computed over the server copies so both origins speak the same content
    hash; git's own object ids on the repo side come for free from the sweep.
    """
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


@dataclass
class RepoManifestCoverage:
    """Per-manifest accounting — every skip counted by reason, never silent."""

    rows_read: int = 0
    staged: int = 0
    malformed: int = 0  # wrong cell count / empty path or blob_sha
    historical_rows: int = 0  # empty ref — history-only blob occurrences
    duplicate_rows: int = 0  # same (path, blob_sha, ref) seen again

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class CorroborationReport:
    """Server vs repo content-hash join, bucketed. ``trusted_ref`` is copied
    from the source-registry field (human-blessed), NEVER derived here;
    ``candidate_ref`` is the mechanical naming (most recent matching tip)."""

    found_at_refs: list[dict] = field(default_factory=list)
    behind: list[dict] = field(default_factory=list)
    never_committed: list[dict] = field(default_factory=list)
    repo_only: list[dict] = field(default_factory=list)
    server_uncomputable: int = 0  # no carried-back copy -> no content hash
    candidate_ref: str | None = None
    trusted_ref: str | None = None
    trusted_ref_confirmed: bool | None = None  # None == no trusted_ref declared

    def as_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        return (
            f"found_at_refs={len(self.found_at_refs)} behind={len(self.behind)} "
            f"never_committed={len(self.never_committed)} "
            f"repo_only={len(self.repo_only)} "
            f"uncomputable={self.server_uncomputable} | "
            f"candidate_ref={self.candidate_ref or '~'} "
            f"trusted_ref={self.trusted_ref or '~'}"
            + (f" confirmed={self.trusted_ref_confirmed}" if self.trusted_ref is not None else "")
        )


class CodeRepoExtractor:
    """Manifest → repo-origin script staging records (candidates only)."""

    name = "code-repo"

    def extract(self, manifest: str | Path, into: LineageGraph) -> RepoManifestCoverage:
        coverage = RepoManifestCoverage()
        lines = Path(manifest).read_text(encoding="utf-8", errors="replace").splitlines()
        if not lines:
            return coverage
        header = lines[0].split("\t")
        if any(col not in header for col in MANIFEST_COLUMNS):
            coverage.malformed += 1
            return coverage
        idx = {name: i for i, name in enumerate(header)}
        seen: set[tuple[str, str, str]] = set()
        for line in lines[1:]:
            if not line.strip():
                continue
            coverage.rows_read += 1
            cells = line.split("\t")
            if len(cells) != len(header):
                coverage.malformed += 1
                continue
            row = {name: cells[i] for name, i in idx.items()}
            if not row["path"] or not row["blob_sha"]:
                coverage.malformed += 1
                continue
            key = (row["path"], row["blob_sha"], row["ref"])
            if key in seen:
                coverage.duplicate_rows += 1
                continue
            seen.add(key)
            if not row["ref"]:
                coverage.historical_rows += 1
            # one staged record per (repo, path); ref/commit occurrences
            # accumulate on the record's properties for the report
            pid = process_id(REPO_SCRIPT_KIND, f"{row['repo']}:{row['path']}")
            existing = into.processes.get(pid)
            if existing is None:
                into.add_process(
                    ProcessNode(
                        node_id=pid,
                        kind=REPO_SCRIPT_KIND,
                        name=row["path"].rstrip("/").rsplit("/", 1)[-1],
                        path=row["path"],
                        properties={
                            "origin": "code-repo",
                            "repo": row["repo"],
                            "occurrences": self._occurrence(row),
                        },
                    )
                )
                coverage.staged += 1
            else:
                occ = existing.properties.get("occurrences", "")
                existing.properties["occurrences"] = (
                    f"{occ}\n{self._occurrence(row)}" if occ else self._occurrence(row)
                )
        return coverage

    @staticmethod
    def _occurrence(row: dict[str, str]) -> str:
        # ref|commit|commit_date|blob_sha — parsed back by corroborate()
        return "|".join((row["ref"], row["commit"], row["commit_date"], row["blob_sha"]))


def _occurrences(node: ProcessNode) -> list[tuple[str, str, str, str]]:
    out = []
    for line in node.properties.get("occurrences", "").splitlines():
        parts = line.split("|")
        if len(parts) == 4:
            out.append(tuple(parts))
    return out


def corroborate(
    graph: LineageGraph,
    bundle_dir: str | Path,
    *,
    trusted_ref: str | None = None,
) -> CorroborationReport:
    """Join the two origins on content hash; bucket every server script.

    ``graph`` holds BOTH origins (run the G20 inventory pass and
    :class:`CodeRepoExtractor` first); ``bundle_dir`` locates the server
    copies to hash. ``trusted_ref`` is the source-registry field, passed
    through verbatim — this function never infers trust.
    """
    bundle = RuaInventoryExtractor()._resolve_bundle_dir(Path(bundle_dir))
    report = CorroborationReport(trusted_ref=trusted_ref)

    # index the repo side by blob sha
    by_sha: dict[str, list[tuple[ProcessNode, tuple[str, str, str, str]]]] = {}
    repo_nodes: list[ProcessNode] = []
    for node in graph.processes.values():
        if node.kind != REPO_SCRIPT_KIND:
            continue
        repo_nodes.append(node)
        for occ in _occurrences(node):
            by_sha.setdefault(occ[3], []).append((node, occ))

    matched_shas: set[str] = set()
    best: tuple[str, str] | None = None  # (commit_date, ref) — mechanical naming
    for node in graph.processes.values():
        if node.kind != RUA_SCRIPT_KIND:
            continue
        copy_rel = node.properties.get("rua_copy", "")
        if not copy_rel:
            report.server_uncomputable += 1
            continue
        try:
            content = (bundle / copy_rel.lstrip("/")).read_bytes()
        except OSError:
            report.server_uncomputable += 1
            continue
        sha = git_blob_sha1(content)
        hits = by_sha.get(sha, [])
        if hits:
            matched_shas.add(sha)
        ref_hits = [
            {
                "repo": n.properties.get("repo", ""),
                "ref": occ[0],
                "commit": occ[1],
                "commit_date": occ[2],
                "repo_path": n.path,
            }
            for n, occ in hits
            if occ[0]
        ]
        if ref_hits:
            report.found_at_refs.append(
                {
                    "server_path": node.path,
                    "blob_sha": sha,
                    "refs": ref_hits,
                }
            )
            for h in ref_hits:
                key = (h["commit_date"], h["ref"])
                if best is None or key > best:
                    best = key
        elif hits:
            report.behind.append(
                {
                    "server_path": node.path,
                    "blob_sha": sha,
                    "commits": [
                        {"commit": occ[1], "commit_date": occ[2], "repo_path": n.path}
                        for n, occ in hits
                    ],
                }
            )
        else:
            # weak fallback until the G22 URN ruling: same path tail in the repo
            tail = node.path.rstrip("/").rsplit("/", 1)[-1]
            hints = sorted(
                {n.path for n in repo_nodes if n.path.rstrip("/").rsplit("/", 1)[-1] == tail}
            )
            report.never_committed.append(
                {
                    "server_path": node.path,
                    "blob_sha": sha,
                    "path_tail_hints": hints,
                }
            )

    for node in repo_nodes:
        unmatched = [occ for occ in _occurrences(node) if occ[3] not in matched_shas]
        if unmatched and len(unmatched) == len(_occurrences(node)):
            report.repo_only.append(
                {
                    "repo": node.properties.get("repo", ""),
                    "repo_path": node.path,
                }
            )

    report.candidate_ref = best[1] if best else None
    if trusted_ref is not None:
        report.trusted_ref_confirmed = any(
            h["ref"] == trusted_ref for entry in report.found_at_refs for h in entry["refs"]
        )
    return report
