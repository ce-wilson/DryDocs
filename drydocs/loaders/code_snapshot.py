"""CodeSnapshotLoader — DryDocs' own code-dependency snapshot into the graph.

G33 / Epic U (self-documentation); gate ``self-documentation-code-graph``
SIGNED OFF 2026-07-27 (config/gate-prompts/self-documentation-code-graph.yaml,
36/36). Reads the NEWEST ``knowledge/depgraph-snapshots/drydocs-*.json``
(dependency mode) and MERGEs it into ``drydocs``: one ``(:Project
{project_id:'drydocs'})`` root, ``:CodeModule`` nodes keyed on ``file_id``,
HAS_MODULE / IMPORTS / IS_ENCODED_IN edges — all idempotent, re-runnable from
committed files (ADR 0002 D3).

THE DISCRIMINATOR IS A POSITIVE ASSERTION (§G1(a) + the 2026-07-27
post-sign-off review finding): the two tree-mode files in the same directory
declare the SAME schema string but carry NO ``meta`` key at all, and a naive
``*.json`` name-sort picks ``tree-this-version.json`` as "newest" ('t' > 'd').
So this loader (1) globs ``drydocs-*.json`` ONLY, and (2) refuses — loudly,
:class:`CodeSnapshotError`, never a silent no-op — any file whose ``meta`` is
absent or whose ``meta.tree`` is not exactly ``false``. A negative
"refuse if tree is true" check would ACCEPT the tree files; do not weaken
this back to one.

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

from drydocs_core.models.code_snapshot import CodeModuleRow

from .base import BaseLoader

if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

LOGGER = logging.getLogger(__name__)

CYPHER_DIR = Path(__file__).resolve().parent / "cypher"
DEFAULT_SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "knowledge" / "depgraph-snapshots"
# v2 (first seen 2026-07-27, ritual snapshot 20260727-2019) is a SUPERSET of
# v1 for this loader's concern: nodes/edges/meta are unchanged; v2 adds
# lineage sections (processes/data_assets/hosts/rels) and stats, which this
# loader does NOT load — it warns when they carry content (never silent).
SNAPSHOT_SCHEMAS = ("depgraph-machine-first/v1", "depgraph-machine-first/v2")
SNAPSHOT_SCHEMA = SNAPSHOT_SCHEMAS[0]  # back-compat name (fixtures/tests)
_V2_UNLOADED_SECTIONS = ("processes", "data_assets", "hosts", "rels")
SNAPSHOT_GLOB = "drydocs-*.json"  # dated dependency snapshots ONLY — never tree-*.json

# §E1(b)/§E2: extension -> the ALREADY-SEEDED SwoClass term (ontology.cypher).
# Dependency mode only ever emits .py today; Shell/Java/SQL stay seeded-but-
# unbound until a scan emits them (§E2 — partial use accepted at the gate).
EXTENSION_LANGUAGE_IRI: dict[str, str] = {
    ".py": "http://www.ebi.ac.uk/swo/SWO_0000118",  # Python
    ".sh": "http://www.ebi.ac.uk/swo/SWO_0000124",  # Shell
    ".sql": "http://www.ebi.ac.uk/swo/SWO_0000126",  # SQL
}


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
    """Yields one row per snapshot node, imports nested, meta denormalized.

    §H4: ``abs_path`` is dropped here — it never reaches the row model, the
    Cypher, or the graph. ``unmapped_extensions`` counts nodes whose extension
    has no seeded SWO term (edge skipped, reported by the CLI — never silent).
    """

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.unmapped_extensions: dict[str, int] = {}
        self.skipped_directories = 0

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
            # DIRECTORIES ARE NOT CODE MODULES. An all-files snapshot carries
            # kind: 'dir' nodes; turning those into graph nodes is a NEW node class
            # and the CONTAINS edge is a NEW edge type, both of which are gate
            # decisions (CLAUDE.md §6) and neither of which this loader may invent.
            # They are counted, not dropped in silence — the count is reported by
            # the CLI so "the tree is not in the graph yet" is visible rather than
            # inferred from a node total nobody checks.
            if node.get("kind") == "dir":
                self.skipped_directories += 1
                continue
            extension = node.get("extension", "")
            language_iri = EXTENSION_LANGUAGE_IRI.get(extension)
            if language_iri is None:
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
