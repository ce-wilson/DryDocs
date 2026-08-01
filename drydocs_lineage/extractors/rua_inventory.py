"""Run-As-User bundle extractor (G20) — the ingest half collect/README promised.

Reads one collector bundle — a ``rua_*.tar.gz`` tarball or an already-extracted
directory, normally from the G19 landing zone (:mod:`drydocs_core.data_root`:
``rua/incoming/`` → ``rua/extracted/<bundle>/``) — and stages CANDIDATES in the
``controlm_inventory`` idiom: nothing here writes the graph, activates
vocabulary, or invents a relationship type. G20 stages NODES only; the
code-operations pass over captured content is G21, and every edge MEANING
(ownership, profile dependencies, cross-source script identity) is the G22
gate's — never auto-decided here.

What each bundle section becomes:

- ``meta.txt``            → the PROVENANCE ENVELOPE (schema version,
  collected_at/by, user, uid, groups, shell, host, fqdn, os/kernel, scan
  roots), parsed once and stamped as ``rua_*`` properties on EVERY staged
  record — the "metadata as nodes" raw material the G23 curated load turns
  into real provenance nodes per the G22 rulings.
- ``directories.tsv``     → :class:`~drydocs_lineage.model.DataAssetNode`
  candidates, ``kind="rua_path"``, location = the path as captured.
- ``ownership_dirs.tsv``  → the same ``rua_path`` kind when present (the
  optional sweep lists dirs AND files; ``type`` stays a property, and a path
  already staged from ``directories.tsv`` dedups by id — first seen wins).
- ``profiles.tsv`` + ``profiles/`` → profile artifacts:
  :class:`~drydocs_lineage.model.ProcessNode`, ``kind="rua_profile"``.
- ``scripts.tsv`` + ``scripts/``   → script artifacts, ``kind="rua_script"``.
  OPTIONAL — a v1 bundle has no scripts section and stays fully ingestible
  (the collector's compat contract); likewise the ``sha256`` columns.
- ``scripts.csv``                  → the same ``rua_script`` artifacts,
  METADATA-ONLY (G45): real bundles ship a pipe-delimited LISTING
  (``path|script|permission|date|size`` — no sha256 column, no body mirror)
  while still wearing the v1 schema tag. A listing is a fact, never implied
  content: rows stage with ``hash_missing`` and ``script_copies_missing``
  counted. Presence dispatch: ``scripts.tsv`` (v2, richer) WINS when both
  exist; the csv is the fallback; neither present files optional-absent.

Identity is deliberately rua-scoped (``rua_script`` / ``rua_profile`` /
``rua_path``), NOT shared with the CMD_LINE invocation namespace: whether a
script found on the server, the same path referenced in a CMD_LINE, and a repo
blob (G24) are ONE node is exactly the G22 identity/dedup ruling. Until it
rules, the join material is properties — ``path`` on the artifact, and the
``(rua_host, rua_user)`` envelope pair that later meets ``ControlMJob.run_as``
/ ``node_target`` (Epic P hosts-topology).

Coverage follows the house rule: every malformed row, missing section, absent
copy, and cross-host id collision is COUNTED by reason, never silent.
"""

from __future__ import annotations

import tarfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

from drydocs_core.data_root import rua_extracted_dir

from ..model import DataAssetNode, LineageGraph, ProcessNode, asset_id, process_id

#: bundle member files (the collector's output contract)
META_TXT = "meta.txt"
DIRECTORIES_TSV = "directories.tsv"
PROFILES_TSV = "profiles.tsv"
SCRIPTS_TSV = "scripts.tsv"  # v2 only — OPTIONAL on ingest; WINS over the csv
SCRIPTS_CSV = "scripts.csv"  # metadata-only listing fallback (G45; pipe-delim)
OWNERSHIP_TSV = "ownership_dirs.tsv"  # only when OWNERSHIP_SWEEP=yes

#: staged kinds — rua-scoped on purpose (cross-source identity is G22's ruling)
RUA_PATH_KIND = "rua_path"
RUA_PROFILE_KIND = "rua_profile"
RUA_SCRIPT_KIND = "rua_script"

#: meta.txt key → the rua_* property stamped on every record (the acceptance's
#: envelope field list; anything else in meta.txt stays in coverage.meta)
_ENVELOPE_KEYS = (
    ("schema", "rua_schema"),
    ("collected_at", "rua_collected_at"),
    ("collected_by", "rua_collected_by"),
    ("user", "rua_user"),
    ("uid", "rua_uid"),
    ("groups", "rua_groups"),
    ("login_shell", "rua_shell"),
    ("hostname", "rua_host"),
    ("fqdn", "rua_fqdn"),
    ("os", "rua_os"),
    ("kernel", "rua_kernel"),
    ("scan_roots", "rua_scan_roots"),
)

#: required columns per section (extras ignored; ``sha256`` is v2-optional and
#: handled separately so v1 bundles keep parsing)
_REQUIRED_COLS = {
    DIRECTORIES_TSV: ("path", "type", "owner", "group", "perms", "size", "mtime"),
    PROFILES_TSV: ("name", "path", "size", "mtime", "perms", "owner"),
    SCRIPTS_TSV: ("path", "owner", "group", "perms", "size", "mtime"),
    OWNERSHIP_TSV: ("path", "type", "perms", "size", "mtime"),
}

#: the metadata-only listing contract (G45): path = containing directory,
#: script = filename; permission/date/size are the only facts it carries
_SCRIPTS_CSV_COLS = ("path", "script", "permission", "date", "size")

_TARBALL_SUFFIXES = (".tar.gz", ".tgz", ".tar")


@dataclass
class RuaCoverage:
    """Per-bundle accounting — every skip/miss is counted BY REASON, never
    silent (the STG_PARSE_QUALITY / UNMATCHED house rule, candidate side)."""

    meta_missing: int = 0  # no meta.txt — records carry rua_bundle only
    meta_fields_missing: int = 0  # named envelope fields absent from meta.txt
    sections_missing: list[str] = field(default_factory=list)  # required file absent
    sections_optional_absent: list[str] = field(default_factory=list)  # v1/sweep-off
    directories_rows: int = 0
    directories_staged: int = 0
    directories_malformed: int = 0
    profiles_rows: int = 0
    profiles_staged: int = 0
    profiles_malformed: int = 0
    profile_copies_present: int = 0  # copy found under profiles/
    profile_copies_missing: int = 0  # listed but no copy (COPY_PROFILES=no, or lost)
    scripts_rows: int = 0
    scripts_staged: int = 0
    scripts_malformed: int = 0
    script_copies_present: int = 0  # copy found under scripts/ (tree-mirrored)
    script_copies_missing: int = 0  # listed but no copy (over-cap or COPY_SCRIPTS=no)
    ownership_rows: int = 0
    ownership_staged: int = 0
    ownership_malformed: int = 0
    hash_missing: int = 0  # artifact row without a sha256 (v1, or unreadable)
    cross_host_collisions: int = 0  # id already staged from a DIFFERENT host
    meta: dict[str, str] = field(default_factory=dict)  # the FULL parsed meta.txt
    # (G23's metadata-as-nodes raw material)

    def as_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        return (
            f"paths={self.directories_staged}+{self.ownership_staged} "
            f"profiles={self.profiles_staged} scripts={self.scripts_staged} | "
            f"copies: profile={self.profile_copies_present}/"
            f"{self.profile_copies_present + self.profile_copies_missing} "
            f"script={self.script_copies_present}/"
            f"{self.script_copies_present + self.script_copies_missing} | "
            f"missing: sections={len(self.sections_missing)} "
            f"optional_absent={len(self.sections_optional_absent)} "
            f"meta={self.meta_missing} hashes={self.hash_missing} | "
            f"malformed: dirs={self.directories_malformed} "
            f"profiles={self.profiles_malformed} scripts={self.scripts_malformed} "
            f"ownership={self.ownership_malformed} | "
            f"cross_host={self.cross_host_collisions}"
        )


def _basename(path: str) -> str:
    return path.rstrip("/").rsplit("/", 1)[-1] or path


def _read_delimited(path: Path, required: tuple[str, ...], sep: str):
    """Yield row dicts keyed by header name; ``None`` first yield = bad header.

    Header-name mapping (not positional) so the v2 ``sha256`` column — and any
    future additive column — never breaks older parsers. One reader for every
    delimited section (G45): tab for the tsv contract, pipe for the
    metadata-only ``scripts.csv`` listing."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines:
        yield None
        return
    header = lines[0].split(sep)
    if any(col not in header for col in required):
        yield None
        return
    idx = {name: i for i, name in enumerate(header)}
    for line in lines[1:]:
        if not line:
            continue
        cells = line.split(sep)
        if len(cells) != len(header):
            yield {}  # malformed row marker — counted by the caller
            continue
        yield {name: cells[i] for name, i in idx.items()}


def _read_tsv(tsv: Path, required: tuple[str, ...]):
    """Thin wrapper — the tab-delimited half of :func:`_read_delimited`."""
    yield from _read_delimited(tsv, required, "\t")


class RuaInventoryExtractor:
    """One rua bundle → provenance-stamped node candidates (no edges — G21/G22
    own everything with meaning)."""

    name = "rua-inventory"

    def extract(
        self,
        source: str | Path,
        into: LineageGraph,
        *,
        unpack_dir: str | Path | None = None,
    ) -> RuaCoverage:
        """``source`` is a ``rua_*.tar.gz`` tarball or an extracted bundle dir.
        Tarballs unpack into ``unpack_dir`` (default: the G19 landing zone's
        ``rua/extracted/<bundle>/``). Returns the run's :class:`RuaCoverage`;
        callers report it — nothing drops silently."""
        src = Path(source)
        coverage = RuaCoverage()
        if src.is_file() and src.name.endswith(_TARBALL_SUFFIXES):
            src = self._unpack(src, unpack_dir)
        bundle_dir = self._resolve_bundle_dir(src)

        env_props = self._read_envelope(bundle_dir, coverage)
        self._stage_paths(bundle_dir / DIRECTORIES_TSV, DIRECTORIES_TSV, into, coverage, env_props)
        self._stage_paths(bundle_dir / OWNERSHIP_TSV, OWNERSHIP_TSV, into, coverage, env_props)
        self._stage_profiles(bundle_dir, into, coverage, env_props)
        self._stage_scripts(bundle_dir, into, coverage, env_props)
        return coverage

    # -- bundle resolution ----------------------------------------------------
    def _unpack(self, tarball: Path, unpack_dir: str | Path | None) -> Path:
        name = tarball.name
        for suffix in _TARBALL_SUFFIXES:
            if name.endswith(suffix):
                name = name[: -len(suffix)]
                break
        dest = Path(unpack_dir) if unpack_dir else rua_extracted_dir(name, create=True)
        dest.mkdir(parents=True, exist_ok=True)
        with tarfile.open(tarball) as tf:
            # filter="data": strips absolute paths / traversal / specials — a
            # carried-back tarball is data, never something to trust blindly
            tf.extractall(dest, filter="data")
        return dest

    def _resolve_bundle_dir(self, path: Path) -> Path:
        """The dir holding meta.txt: ``path`` itself, or its single child (the
        tarball carries the ``rua_<host>_<user>_<ts>/`` dir at top level)."""
        if (path / META_TXT).is_file():
            return path
        children = [c for c in path.iterdir() if (c / META_TXT).is_file()] if path.is_dir() else []
        if len(children) == 1:
            return children[0]
        return path  # no meta.txt anywhere — counted by _read_envelope

    # -- the provenance envelope ------------------------------------------------
    def _read_envelope(self, bundle_dir: Path, coverage: RuaCoverage) -> dict[str, str]:
        props = {"rua_bundle": bundle_dir.name}
        meta_path = bundle_dir / META_TXT
        if not meta_path.is_file():
            coverage.meta_missing += 1
            return props
        for line in meta_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            coverage.meta[key.strip()] = value.strip()
        for meta_key, prop in _ENVELOPE_KEYS:
            value = coverage.meta.get(meta_key, "")
            if value:
                props[prop] = value
            else:
                coverage.meta_fields_missing += 1
        return props

    # -- directories.tsv / ownership_dirs.tsv → rua_path DataAssets --------------
    def _stage_paths(
        self,
        tsv: Path,
        section: str,
        graph: LineageGraph,
        coverage: RuaCoverage,
        env_props: dict[str, str],
    ) -> None:
        optional = section == OWNERSHIP_TSV
        if not tsv.is_file():
            (coverage.sections_optional_absent if optional else coverage.sections_missing).append(
                section
            )
            return
        for row in _read_tsv(tsv, _REQUIRED_COLS[section]):
            if row is None:
                coverage.sections_missing.append(f"{section}:bad-header")
                return
            if not row or not row.get("path"):
                self._count_malformed(section, coverage)
                continue
            if optional:
                coverage.ownership_rows += 1
            else:
                coverage.directories_rows += 1
            path = row["path"]
            aid = asset_id(RUA_PATH_KIND, path)
            props = dict(env_props)
            for col in ("type", "owner", "group", "perms", "size", "mtime"):
                if row.get(col):
                    props[col] = row[col]
            props["rua_section"] = section
            existing = graph.data_assets.get(aid)
            if existing is None:
                graph.add_data_asset(
                    DataAssetNode(
                        node_id=aid,
                        kind=RUA_PATH_KIND,
                        location=path,
                        properties=props,
                    )
                )
                if optional:
                    coverage.ownership_staged += 1
                else:
                    coverage.directories_staged += 1
            else:
                self._check_cross_host(existing.properties, env_props, coverage)

    # -- profiles.tsv + profiles/ → rua_profile artifacts -------------------------
    def _stage_profiles(
        self,
        bundle_dir: Path,
        graph: LineageGraph,
        coverage: RuaCoverage,
        env_props: dict[str, str],
    ) -> None:
        tsv = bundle_dir / PROFILES_TSV
        if not tsv.is_file():
            coverage.sections_missing.append(PROFILES_TSV)
            return
        for row in _read_tsv(tsv, _REQUIRED_COLS[PROFILES_TSV]):
            if row is None:
                coverage.sections_missing.append(f"{PROFILES_TSV}:bad-header")
                return
            if not row or not row.get("path"):
                coverage.profiles_malformed += 1
                continue
            coverage.profiles_rows += 1
            copy_rel = f"profiles/{row['name']}"
            self._stage_artifact(
                RUA_PROFILE_KIND,
                row["path"],
                row.get("name") or _basename(row["path"]),
                row,
                bundle_dir,
                copy_rel,
                graph,
                coverage,
                env_props,
            )

    # -- scripts.tsv | scripts.csv → rua_script artifacts (OPTIONAL) --------------
    def _stage_scripts(
        self,
        bundle_dir: Path,
        graph: LineageGraph,
        coverage: RuaCoverage,
        env_props: dict[str, str],
    ) -> None:
        """Presence dispatch (G45): the v2 ``scripts.tsv`` (abs-path rows,
        sha256, ``scripts/`` body mirror) WINS when both files exist; else the
        metadata-only ``scripts.csv`` listing stages; else the bundle carries
        no scripts section and stays ingestible (optional-absent)."""
        if (bundle_dir / SCRIPTS_TSV).is_file():
            self._stage_scripts_tsv(bundle_dir, graph, coverage, env_props)
        elif (bundle_dir / SCRIPTS_CSV).is_file():
            self._stage_scripts_csv(bundle_dir, graph, coverage, env_props)
        else:
            coverage.sections_optional_absent.append(SCRIPTS_TSV)

    def _stage_scripts_tsv(
        self,
        bundle_dir: Path,
        graph: LineageGraph,
        coverage: RuaCoverage,
        env_props: dict[str, str],
    ) -> None:
        tsv = bundle_dir / SCRIPTS_TSV
        for row in _read_tsv(tsv, _REQUIRED_COLS[SCRIPTS_TSV]):
            if row is None:
                coverage.sections_missing.append(f"{SCRIPTS_TSV}:bad-header")
                return
            if not row or not row.get("path"):
                coverage.scripts_malformed += 1
                continue
            coverage.scripts_rows += 1
            copy_rel = f"scripts{row['path']}"  # the collector mirrors the abs tree
            self._stage_artifact(
                RUA_SCRIPT_KIND,
                row["path"],
                _basename(row["path"]),
                row,
                bundle_dir,
                copy_rel,
                graph,
                coverage,
                env_props,
            )

    def _stage_scripts_csv(
        self,
        bundle_dir: Path,
        graph: LineageGraph,
        coverage: RuaCoverage,
        env_props: dict[str, str],
    ) -> None:
        """The metadata-only listing (G45): ``path`` is the containing
        directory and ``script`` the filename, so the staged identity is the
        JOINED absolute path — the same ``rua_script`` node path the tsv route
        produces. No sha256 column and no body mirror exist by contract:
        ``_stage_artifact`` counts ``hash_missing`` and
        ``script_copies_missing`` for every row (a LISTING is a fact, never
        implied content)."""
        csv = bundle_dir / SCRIPTS_CSV
        for row in _read_delimited(csv, _SCRIPTS_CSV_COLS, "|"):
            if row is None:
                coverage.sections_missing.append(f"{SCRIPTS_CSV}:bad-header")
                return
            if not row or not row.get("path") or not row.get("script"):
                coverage.scripts_malformed += 1
                continue
            coverage.scripts_rows += 1
            abs_path = f"{row['path'].rstrip('/')}/{row['script']}"
            mapped = {
                "perms": row.get("permission", ""),
                "mtime": row.get("date", ""),
                "size": row.get("size", ""),
            }
            copy_rel = f"scripts{abs_path}"  # never shipped for a listing —
            self._stage_artifact(  # counted missing, not implied
                RUA_SCRIPT_KIND,
                abs_path,
                row["script"],
                mapped,
                bundle_dir,
                copy_rel,
                graph,
                coverage,
                env_props,
            )

    # -- shared artifact staging ---------------------------------------------------
    def _stage_artifact(
        self,
        kind: str,
        path: str,
        name: str,
        row: dict[str, str],
        bundle_dir: Path,
        copy_rel: str,
        graph: LineageGraph,
        coverage: RuaCoverage,
        env_props: dict[str, str],
    ) -> None:
        props = dict(env_props)
        # the provenance-origin discriminator (G24): this record says what is
        # ON THE SERVER; the code-repo seam stages origin=code-repo twins and
        # the corroboration report joins them on content hash — never by id.
        props["origin"] = "server-extract"
        for col in ("owner", "group", "perms", "size", "mtime"):
            if row.get(col):
                props[col] = row[col]
        sha = (row.get("sha256") or "").strip()
        if sha:
            props["sha256"] = sha  # the version discriminator (G24 anchor)
        else:
            coverage.hash_missing += 1
        copy_path = bundle_dir / copy_rel.lstrip("/")
        is_profile = kind == RUA_PROFILE_KIND
        if copy_path.is_file():
            props["rua_copy"] = copy_rel
            if is_profile:
                coverage.profile_copies_present += 1
            else:
                coverage.script_copies_present += 1
        else:
            # over-cap / copy gate off / lost in transport — the LISTING is
            # still a fact; the missing content is counted, not implied
            if is_profile:
                coverage.profile_copies_missing += 1
            else:
                coverage.script_copies_missing += 1
        pid = process_id(kind, path)
        existing = graph.processes.get(pid)
        if existing is None:
            graph.add_process(
                ProcessNode(
                    node_id=pid,
                    kind=kind,
                    name=name,
                    path=path,
                    properties=props,
                )
            )
            if is_profile:
                coverage.profiles_staged += 1
            else:
                coverage.scripts_staged += 1
        else:
            self._check_cross_host(existing.properties, env_props, coverage)

    @staticmethod
    def _count_malformed(section: str, coverage: RuaCoverage) -> None:
        if section == OWNERSHIP_TSV:
            coverage.ownership_malformed += 1
        else:
            coverage.directories_malformed += 1

    @staticmethod
    def _check_cross_host(
        existing_props: dict[str, str],
        env_props: dict[str, str],
        coverage: RuaCoverage,
    ) -> None:
        """First seen wins (setdefault semantics everywhere) — but the same id
        arriving from a DIFFERENT host is review material: whether same-path on
        two hosts is one node is a G22 identity question, so it is counted,
        never resolved here."""
        old_host = existing_props.get("rua_host", "")
        new_host = env_props.get("rua_host", "")
        if old_host and new_host and old_host != new_host:
            coverage.cross_host_collisions += 1
