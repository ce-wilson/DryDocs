"""CodeSnapshotLoader + CodeTreeLoader — DryDocs' own snapshot into the graph.

G33 / Epic U (self-documentation); gate ``self-documentation-code-graph``
SIGNED OFF 2026-07-27 (config/gate-prompts/self-documentation-code-graph.yaml,
36/36). Reads the NEWEST ``knowledge/depgraph-snapshots/drydocs-*.json`` and
MERGEs it into ``drydocs``, in two passes over the same file:

* :class:`CodeSnapshotLoader` (``code_snapshot.v1``) — the FILE layer: one
  ``(:Project {project_id:'drydocs'})`` root, ``:CodeModule`` nodes keyed on
  ``file_id``, HAS_MODULE / IMPORTS / IS_ENCODED_IN / HAS_MEDIA_TYPE edges.
* :class:`CodeTreeLoader` (``code_tree.v1``) — the CONTAINMENT layer (SME
  ruling 2026-08-05, admitting the tree the G33 gate deferred):
  ``:CodeDirectory`` nodes + CONTAINS_ENTRY edges from the snapshot's v2
  ``rels`` section; the repo-root dir maps onto the existing :Project (§B1(a)
  holds — one root, no duplicate).

All idempotent, re-runnable from committed files (ADR 0002 D3).

THE DISCRIMINATOR IS A POSITIVE ASSERTION (§G1(a) + the 2026-07-27
post-sign-off review finding, half-REVERSED by SME direction when the
all-files tree became the ritual default): the historical tree-mode one-offs
declare the SAME schema string but carry NO ``meta`` key at all, and a naive
``*.json`` name-sort picks ``tree-this-version.json`` as "newest" ('t' > 'd').
So these loaders (1) glob ``drydocs-*.json`` ONLY, and (2) refuse — loudly,
:class:`CodeSnapshotError`, never a silent no-op — any file whose ``meta`` is
absent or whose ``meta.tree`` is not a boolean. The load-bearing half is the
POSITIVE ``meta`` assertion (those files carry no ``meta``, so a truthiness
test on ``meta.tree`` would ACCEPT them); do not weaken it.

snapshot.ps1 stays DECOUPLED (§H3): nothing here is imported by the session
ritual, which must keep working with no database running.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from drydocs_core.models.code_snapshot import CodeDirectoryRow, CodeModuleRow

from .base import BaseLoader

if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

LOGGER = logging.getLogger(__name__)

CYPHER_DIR = Path(__file__).resolve().parent / "cypher"
DEFAULT_SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "knowledge" / "depgraph-snapshots"
# v2 (first seen 2026-07-27, ritual snapshot 20260727-2019) is a SUPERSET of
# v1 for this loader's concern: nodes/edges/meta are unchanged; v2 adds
# lineage sections (processes/data_assets/hosts/rels) and stats. `rels` IS
# loaded since the 2026-08-05 ruling (CodeTreeLoader — the containment tree);
# the remaining lineage sections are not — read_snapshot warns when they
# carry content (never silent).
SNAPSHOT_SCHEMAS = ("depgraph-machine-first/v1", "depgraph-machine-first/v2")
SNAPSHOT_SCHEMA = SNAPSHOT_SCHEMAS[0]  # back-compat name (fixtures/tests)
_V2_UNLOADED_SECTIONS = ("processes", "data_assets", "hosts")
SNAPSHOT_GLOB = "drydocs-*.json"  # dated dependency snapshots ONLY — never tree-*.json

# §E1(b)/§E2: extension -> the ALREADY-SEEDED SwoClass term (ontology.cypher).
# Dependency mode only ever emits .py today; Shell/Java/SQL stay seeded-but-
# unbound until a scan emits them (§E2 — partial use accepted at the gate).
EXTENSION_LANGUAGE_IRI: dict[str, str] = {
    ".py": "http://www.ebi.ac.uk/swo/SWO_0000118",  # Python
    ".sh": "http://www.ebi.ac.uk/swo/SWO_0000124",  # Shell
    # .ksh binds to the SAME Shell term as .sh — SME ruling 2026-08-06 (gate
    # rua-load-shapes §C3). ksh IS a shell, so this binds a seeded term rather
    # than inventing one, and it is not a cosmetic addition: the signed
    # m3_triggers note names the .ksh wrapper as the COMMON case in this estate
    # ("one .ksh wrapper script that launches the Informatica / Ab Initio / DPL
    # workload"), so leaving it out left the most frequent extension unbound and
    # merely CLI-reported.
    ".ksh": "http://www.ebi.ac.uk/swo/SWO_0000124",  # Shell (ksh)
    ".sql": "http://www.ebi.ac.uk/swo/SWO_0000126",  # SQL
}

# Extension -> the ALREADY-SEEDED :MediaType format term (ontology.cypher;
# SME ruling 2026-08-05 — the non-.py majority of the tree gets typed the way
# .py gets a language). Same E1(b) discipline as EXTENSION_LANGUAGE_IRI: bind
# to a seeded term, derive from data the artifact carries, invent nothing.
# IANA-registered types use the registration page as iri (DCAT convention);
# conventional unregistered types (TypeScript, PowerShell, Cypher, Jupyter)
# use drydocs.local/format# — an IANA-shaped iri would fabricate a
# registration. Lookup is CASE-FOLDED ('.MD' binds like '.md'). Extensions
# with neither a language nor a media type stay unbound and are CLI-reported.
_IANA = "https://www.iana.org/assignments/media-types/"
_LOCAL_FORMAT = "https://drydocs.local/format#"
EXTENSION_MEDIA_TYPE_IRI: dict[str, str] = {
    ".md": _IANA + "text/markdown",
    ".html": _IANA + "text/html",
    ".css": _IANA + "text/css",
    ".js": _IANA + "text/javascript",
    ".csv": _IANA + "text/csv",
    ".txt": _IANA + "text/plain",
    ".json": _IANA + "application/json",
    ".yaml": _IANA + "application/yaml",
    ".yml": _IANA + "application/yaml",
    ".toml": _IANA + "application/toml",
    ".xml": _IANA + "application/xml",
    ".xsd": _IANA + "application/xml",  # an XSD document IS XML; no XSD-specific type exists
    ".pdf": _IANA + "application/pdf",
    ".sql": _IANA + "application/sql",  # format binding; the LANGUAGE binding rides IS_ENCODED_IN
    ".mermaid": _IANA + "application/vnd.mermaid",
    ".xlsx": _IANA + "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ts": _LOCAL_FORMAT + "typescript",
    ".tsx": _LOCAL_FORMAT + "typescript",
    ".ps1": _LOCAL_FORMAT + "powershell",
    ".cypher": _LOCAL_FORMAT + "cypher",
    ".ipynb": _LOCAL_FORMAT + "jupyter-notebook",
}

# SME ruling 2026-08-06 (two parts, same day): BINARY ASSETS ARE NOT
# CODE-GRAPH CONTENT — first images (.png/.svg/.webp), then fonts on revisit
# ("I didn't think of the font"). Both adapters skip them at load — counted
# and CLI-reported, never silent. The set is the two ruled ASSET CLASSES,
# images and fonts, listing the common extensions of each so the next stray
# .jpg or .woff2 cannot drift back in; a THIRD class (audio, video, archives)
# would be a new ruling, not a list edit. This is a LOAD-TIME rule, not an
# instrument change: the snapshot still carries the assets (scanner scope is
# the ritual's concern, and the committed artifact stays a faithful capture);
# the graph just declines to model them. Case-folded compare, like the
# media-type lookup.
ASSET_EXTENSIONS_SKIPPED: frozenset[str] = frozenset(
    {
        # images
        ".png", ".svg", ".webp", ".gif", ".jpg", ".jpeg", ".ico",
        # fonts
        ".ttf", ".otf", ".woff", ".woff2",
    }
)


class CodeSnapshotError(RuntimeError):
    """Loud refusal — the 'succeeds loudly, does nothing' family (§H2)."""


# Two naming shapes exist in the wild: drydocs-YYYYMMDD-HHMM.json (the ritual)
# and drydocs-YYYYMMDD.json (date-only one-offs). Ordinal sort mis-orders them
# ('.' > '-', so a STALE date-only file beats every timed file of the same
# day) — found live 2026-07-27 when the first load picked the 12:42 capture
# over the 17:33 one. Parse the timestamp instead; date-only keys as 0000.
_SNAPSHOT_NAME = re.compile(r"^drydocs-(\d{8})(?:-(\d{4}))?\.json$")


def select_newest_snapshot(snapshot_dir: Path | str = DEFAULT_SNAPSHOT_DIR) -> Path:
    """Newest dated dependency snapshot by filename timestamp (§H2).

    Globs ``drydocs-*.json`` only, so the tree-mode one-offs
    (tree-original.json, tree-this-version.json) are never candidates —
    selection safety does not rest on the meta check alone. Ordering is the
    PARSED (date, time) key, never raw string sort (see _SNAPSHOT_NAME).
    """
    snapshot_dir = Path(snapshot_dir)
    candidates: list[tuple[str, str, Path]] = []
    for path in snapshot_dir.glob(SNAPSHOT_GLOB):
        m = _SNAPSHOT_NAME.match(path.name)
        if not m:
            LOGGER.warning(
                "select_newest_snapshot: %s matches the glob but not the "
                "drydocs-YYYYMMDD[-HHMM].json pattern — skipped",
                path.name,
            )
            continue
        candidates.append((m.group(1), m.group(2) or "0000", path))
    if not candidates:
        raise CodeSnapshotError(
            f"no {SNAPSHOT_GLOB} dependency snapshot found in {snapshot_dir} — "
            "run knowledge/depgraph-snapshots/snapshot.ps1 first (nothing was loaded)"
        )
    return max(candidates)[2]


def read_snapshot(path: Path | str) -> dict:
    """Parse + validate one snapshot file; refuse anything but dependency mode.

    POSITIVE assertion (§G1(a), build note 2026-07-27): ``meta`` must be
    PRESENT and ``meta.tree`` must be exactly ``false``. The tree-mode files
    carry no ``meta`` key at all, so a truthiness check on ``meta.get('tree')``
    would accept them — this refuses them instead.
    """
    path = Path(path)
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CodeSnapshotError(f"cannot read snapshot {path}: {exc}") from exc

    schema = doc.get("schema")
    if schema not in SNAPSHOT_SCHEMAS:
        raise CodeSnapshotError(
            f"{path.name}: schema is {schema!r}, expected one of {SNAPSHOT_SCHEMAS!r} "
            "(nothing was loaded)"
        )
    for section in _V2_UNLOADED_SECTIONS:
        n = len(doc.get(section) or [])
        if n:
            LOGGER.warning(
                "%s: v2 section '%s' carries %d record(s) this loader does NOT "
                "load (code modules only) — a lineage-side consumer is needed "
                "for that content",
                path.name,
                section,
                n,
            )
    meta = doc.get("meta")
    if not isinstance(meta, dict):
        raise CodeSnapshotError(
            f"{path.name}: no `meta` block — this is the tree-mode shape "
            "(same schema string, materially different content; gate §G1). "
            "REFUSED: this loader loads dependency-mode snapshots only (nothing was loaded)"
        )
    # §G1(a) REVERSED by SME direction: the scanner now captures the WHOLE tree by
    # default (snapshot.ps1), so `meta.tree: true` is the normal shape and refusing
    # it would refuse every snapshot there is. What the original ruling was actually
    # protecting against survives untouched: the headerless one-off shape, caught by
    # the `meta` assertion above — that guard is the load-bearing half, and it stays
    # a POSITIVE assertion for the reason the build note gave (those files carry no
    # `meta` at all, so a truthiness test on meta.tree would ACCEPT them).
    # Still refused: a `tree` that is not a bool, i.e. an unrecognised third shape.
    if not isinstance(meta.get("tree"), bool):
        raise CodeSnapshotError(
            f"{path.name}: meta.tree is {meta.get('tree')!r}, expected a boolean — "
            "unrecognised snapshot shape (nothing was loaded)"
        )
    if not doc.get("nodes"):
        raise CodeSnapshotError(
            f"{path.name}: snapshot carries zero nodes — refusing an empty load "
            "(the 'succeeds loudly, does nothing' rule)"
        )
    return doc


class CodeSnapshotAdapter:
    """Yields one row per snapshot FILE node, imports nested, meta denormalized.

    §H4: ``abs_path`` is dropped here — it never reaches the row model, the
    Cypher, or the graph. ``unmapped_extensions`` counts nodes whose extension
    has NEITHER a seeded SWO language term NOR a seeded MediaType format term
    (both edges skipped, reported by the CLI — never silent; before the
    2026-08-05 ruling this counted "no SWO term", which was nearly every
    non-.py file).
    """

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.unmapped_extensions: dict[str, int] = {}
        self.skipped_directories = 0
        self.skipped_assets = 0  # SME ruling 2026-08-06 — images/fonts are not loaded

    def __enter__(self) -> CodeSnapshotAdapter:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    def rows(self) -> Iterator[dict]:
        doc = read_snapshot(self.path)
        meta = doc["meta"]
        git = meta.get("git") or {}
        # §B1(a): ONE root. meta.project names it ('drydocs'); the six scan
        # roots in doc['projects'] become the per-node `project` property.
        project_id = meta.get("project") or "drydocs"

        # KEY NORMALISATION — §C2 says file_id IS the repo-relative path, and the
        # two scan modes disagree about what the scanner puts there.
        #   roots scan: scan root = drydocs/ ...  file_id 'drydocs/cli.py'      (repo-relative)
        #   tree scan : scan root = the REPO  ...  file_id 'drydocs/drydocs/cli.py'
        # because the tree scan's project segment is the REPOSITORY directory, not
        # a package inside it. Loading that raw produced TWO nodes for one file
        # (verified live: drydocs/cli.py and drydocs/drydocs/cli.py side by side,
        # neither swept) and would have silently broken the file_id ruling plus
        # every stored reference to it. Stripping the project prefix in tree mode
        # restores the ruled key, so a mode switch merges instead of forking.
        strip = f"{project_id}/" if meta.get("tree") else ""

        def _key(file_id: str) -> str:
            if strip and file_id.startswith(strip):
                return file_id[len(strip) :]
            return file_id

        imports_by_source: dict[str, list[str]] = {}
        for edge in doc.get("edges", []):
            if not (isinstance(edge, list | tuple) and len(edge) == 2):
                raise CodeSnapshotError(
                    f"{self.path.name}: malformed edge {edge!r} — expected [source_file_id, target_file_id]"
                )
            imports_by_source.setdefault(_key(edge[0]), []).append(_key(edge[1]))

        for node in doc.get("nodes", []):
            # DIRECTORIES ARE NOT CODE MODULES. They are still not loaded HERE —
            # :CodeDirectory nodes + CONTAINS_ENTRY edges are CodeTreeAdapter/
            # CodeTreeLoader's job (SME ruling 2026-08-05 admitted the tree the
            # G33 gate deferred). Counted so the CLI can cross-check the two
            # loaders' row totals against the snapshot.
            if node.get("kind") == "dir":
                self.skipped_directories += 1
                continue
            extension = node.get("extension", "")
            # SME ruling 2026-08-06: image files are not code-graph content.
            if extension.lower() in ASSET_EXTENSIONS_SKIPPED:
                self.skipped_assets += 1
                continue
            language_iri = EXTENSION_LANGUAGE_IRI.get(extension)
            media_type_iri = EXTENSION_MEDIA_TYPE_IRI.get(extension.lower())
            if language_iri is None and media_type_iri is None:
                self.unmapped_extensions[extension] = self.unmapped_extensions.get(extension, 0) + 1
            file_id = _key(node.get("file_id") or "")
            # `project` (§B1(a)) was "the scan root, one of six" — a concept that
            # only existed because the scanner took a hand-maintained root list.
            # The all-files scan takes the REPO root, so there are no scan roots,
            # and the tree scan reports this field as the repository for every
            # node — collapsing a property whose whole job was to distinguish
            # drydocs / drydocs_core / tests. It generalises to the first path
            # segment, which is the value the roots scan reported for anything
            # inside a package. Repo-root files (README.md, pyproject.toml) have
            # no segment above them and carry '.' rather than being labelled a
            # "scan root" named after themselves.
            if strip:
                project = file_id.split("/", 1)[0] if "/" in file_id else "."
            else:
                project = node.get("project")
            yield {
                # abs_path deliberately NOT emitted (§H4)
                "file_id": file_id,
                "project": project,
                "rel_path": node.get("rel_path"),
                "name": node.get("name"),
                "extension": extension,
                "circular": bool(node.get("circular", False)),
                "imports": sorted(imports_by_source.get(file_id, [])),
                "language_iri": language_iri,
                "media_type_iri": media_type_iri,
                "project_id": project_id,
                "captured_at": meta.get("captured_at"),
                "git_commit": git.get("commit") or "",
                "git_full": git.get("full") or "",
                "git_branch": git.get("branch") or "",
                "git_dirty": bool(git.get("dirty", False)),
            }


class CodeSnapshotLoader(BaseLoader):
    """The G33 loader. Every snapshot is a FULL scan by construction, so the
    CLI passes ``full_extract=True`` and the D7 mark pass sweeps :CodeModule
    nodes that left the source tree between snapshots."""

    name: ClassVar[str] = "code_snapshot.v1"
    source_id: ClassVar[str | None] = "repo:depgraph-snapshot"
    cypher_path: ClassVar[Path] = CYPHER_DIR / "code_snapshot.cypher"
    row_model: ClassVar[type] = CodeModuleRow
    source_label: ClassVar[str] = "snapshot"
    sweep_label: ClassVar[str | None] = "CodeModule"


class CodeTreeAdapter:
    """Yields one row per snapshot DIRECTORY node, children from the ``rels``
    section (SME ruling 2026-08-05 — the containment layer).

    Children are classified by the child node's ``kind`` (dir vs file), never
    by path-string guessing — the tree instrument note's whole point (U9) is
    that the ``rels`` section reads containment FROM the tree. A rel naming an
    endpoint absent from ``nodes`` is malformed and refuses the load.

    Rows are yielded parents-before-children (sorted by path depth) so a
    multi-batch load MERGEs a parent's node statement before — or in the same
    flush as — its children's edge statements.
    """

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.skipped_assets = 0  # SME ruling 2026-08-06 — images/fonts are not loaded

    def __enter__(self) -> CodeTreeAdapter:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    def rows(self) -> Iterator[dict]:
        doc = read_snapshot(self.path)
        meta = doc["meta"]
        git = meta.get("git") or {}
        project_id = meta.get("project") or "drydocs"
        if not meta.get("tree"):
            raise CodeSnapshotError(
                f"{self.path.name}: meta.tree is false — a roots-only dependency "
                "snapshot carries no containment tree, so there is nothing for the "
                "tree loader to load (run the default all-files snapshot.ps1)"
            )
        rels = doc.get("rels") or []
        if not rels:
            raise CodeSnapshotError(
                f"{self.path.name}: tree snapshot carries zero rels — refusing an "
                "empty containment load (the 'succeeds loudly, does nothing' rule)"
            )

        # Key normalisation (§C2), with a subtlety the module adapter never
        # faces: after stripping the leading project segment, the repo ROOT
        # ('drydocs', rel_path '.') and the top-level `drydocs/` PACKAGE dir
        # ('drydocs/drydocs') would COLLIDE on 'drydocs'. So the maps below
        # key on the snapshot's RAW ids (unique by construction) and the strip
        # happens only at emission — root rows emit file_id = project_id and
        # is_root=True, which the Cypher maps onto :Project, never a node key.
        strip = f"{project_id}/"

        def _emit_key(raw_id: str) -> str:
            if raw_id.startswith(strip):
                return raw_id[len(strip) :]
            return raw_id

        kind_by_raw: dict[str, str] = {}
        node_by_raw: dict[str, dict] = {}
        for node in doc.get("nodes", []):
            raw = node.get("file_id") or ""
            kind_by_raw[raw] = node.get("kind") or "file"
            node_by_raw[raw] = node

        child_dirs: dict[str, list[str]] = {}
        child_files: dict[str, list[str]] = {}
        for rel in rels:
            if not (isinstance(rel, list | tuple) and len(rel) == 3 and rel[1] == "CONTAINS"):
                raise CodeSnapshotError(
                    f"{self.path.name}: malformed rel {rel!r} — expected "
                    "[parent_file_id, 'CONTAINS', child_file_id]"
                )
            parent_raw, child_raw = rel[0], rel[2]
            child_kind = kind_by_raw.get(child_raw)
            if kind_by_raw.get(parent_raw) != "dir" or child_kind is None:
                raise CodeSnapshotError(
                    f"{self.path.name}: rel {rel!r} names an endpoint absent from "
                    "nodes (or a non-dir parent) — snapshot is inconsistent, refusing"
                )
            # SME ruling 2026-08-06: an image child must not become a stub
            # :CodeModule via the containment edge — same skip as the module
            # adapter, counted here because this pass sees its own rels.
            if child_kind != "dir" and (
                str(node_by_raw[child_raw].get("extension") or "").lower()
                in ASSET_EXTENSIONS_SKIPPED
            ):
                self.skipped_assets += 1
                continue
            bucket = child_dirs if child_kind == "dir" else child_files
            bucket.setdefault(parent_raw, []).append(_emit_key(child_raw))

        dir_raws = sorted(
            (k for k, kind in kind_by_raw.items() if kind == "dir"),
            key=lambda k: (k.count("/"), k),
        )
        for raw in dir_raws:
            node = node_by_raw[raw]
            is_root = node.get("rel_path") == "."
            file_id = project_id if is_root else _emit_key(raw)
            if is_root:
                project = "."
            else:
                project = file_id.split("/", 1)[0] if "/" in file_id else file_id
            yield {
                "file_id": file_id,
                "is_root": is_root,
                "name": node.get("name"),
                "rel_path": node.get("rel_path"),
                "project": project,
                "child_dir_ids": sorted(child_dirs.get(raw, [])),
                "child_file_ids": sorted(child_files.get(raw, [])),
                "project_id": project_id,
                "captured_at": meta.get("captured_at"),
                "git_commit": git.get("commit") or "",
                "git_full": git.get("full") or "",
                "git_branch": git.get("branch") or "",
                "git_dirty": bool(git.get("dirty", False)),
            }


class CodeTreeLoader(BaseLoader):
    """The containment-tree loader (SME ruling 2026-08-05). Runs AFTER
    CodeSnapshotLoader in ``load-code-snapshot`` — same snapshot file, same
    full-scan-by-construction property, so the CLI passes ``full_extract=True``
    and the D7 mark pass sweeps :CodeDirectory nodes that left the tree."""

    name: ClassVar[str] = "code_tree.v1"
    source_id: ClassVar[str | None] = "repo:depgraph-snapshot"
    cypher_path: ClassVar[Path] = CYPHER_DIR / "code_tree.cypher"
    row_model: ClassVar[type] = CodeDirectoryRow
    source_label: ClassVar[str] = "snapshot"
    sweep_label: ClassVar[str | None] = "CodeDirectory"
