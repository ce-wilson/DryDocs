"""Guards for the G33 self-documentation code-snapshot loader.

Gate self-documentation-code-graph (SIGNED OFF 2026-07-27) + the post-sign-off
build note: the discriminator must be a POSITIVE assertion, because the
tree-mode files carry NO ``meta`` key at all and a naive ``*.json`` name-sort
picks ``tree-this-version.json`` as "newest". These tests pin exactly the
failure modes that literal reading would reintroduce, plus the §H4 abs_path
drop and the wiring declarations — all without a Neo4j connection.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from drydocs.loaders.code_snapshot import (
    DEFAULT_SNAPSHOT_DIR,
    EXTENSION_LANGUAGE_IRI,
    EXTENSION_MEDIA_TYPE_IRI,
    IMAGE_EXTENSIONS_SKIPPED,
    CodeSnapshotAdapter,
    CodeSnapshotError,
    CodeSnapshotLoader,
    CodeTreeAdapter,
    CodeTreeLoader,
    read_snapshot,
    select_newest_snapshot,
)
from drydocs_core.models.code_snapshot import CodeDirectoryRow, CodeModuleRow

REPO = Path(__file__).resolve().parents[2]
CYPHER_FILE = REPO / "drydocs" / "loaders" / "cypher" / "code_snapshot.cypher"
TREE_CYPHER_FILE = REPO / "drydocs" / "loaders" / "cypher" / "code_tree.cypher"
CONSTRAINTS_FILE = REPO / "drydocs_core" / "schema" / "constraints.cypher"
SUPPLEMENT_FILE = REPO / "drydocs_core" / "schema" / "ontology_supplement.cypher"


def _tree_snapshot() -> dict:
    """A minimal well-formed all-files TREE snapshot (v2, meta.tree true).

    Deliberately includes the nastiest real shape: a top-level package
    directory named after the repo ('drydocs/drydocs'), which after prefix
    stripping would collide with the repo-root node's raw id 'drydocs' if the
    adapter keyed its maps on stripped ids.
    """

    def _n(file_id: str, kind: str, rel_path: str, name: str, ext: str = "") -> dict:
        return {
            "file_id": file_id,
            "kind": kind,
            "rel_path": rel_path,
            "name": name,
            "extension": ext,
            "project": "drydocs",
            "circular": False,
        }

    return {
        "schema": "depgraph-machine-first/v2",
        "projects": ["drydocs"],
        "meta": {
            "project": "drydocs",
            "captured_at": "2026-08-05T17:25:33",
            "tree": True,
            "git": {"commit": "abc1234", "branch": "main", "dirty": False},
        },
        "nodes": [
            _n("drydocs", "dir", ".", "drydocs"),
            _n("drydocs/drydocs", "dir", "drydocs", "drydocs"),
            _n("drydocs/docs", "dir", "docs", "docs"),
            _n("drydocs/README.md", "file", "README.md", "README.md", ".md"),
            _n("drydocs/drydocs/cli.py", "file", "drydocs/cli.py", "cli.py", ".py"),
            _n("drydocs/docs/guide.md", "file", "docs/guide.md", "guide.md", ".md"),
        ],
        "edges": [],
        "processes": [],
        "data_assets": [],
        "hosts": [],
        "rels": [
            ["drydocs", "CONTAINS", "drydocs/drydocs"],
            ["drydocs", "CONTAINS", "drydocs/docs"],
            ["drydocs", "CONTAINS", "drydocs/README.md"],
            ["drydocs/drydocs", "CONTAINS", "drydocs/drydocs/cli.py"],
            ["drydocs/docs", "CONTAINS", "drydocs/docs/guide.md"],
        ],
    }


def _dep_snapshot(**overrides) -> dict:
    """A minimal well-formed dependency-mode snapshot document."""
    doc = {
        "schema": "depgraph-machine-first/v1",
        "projects": ["drydocs", "drydocs_core"],
        "meta": {
            "project": "drydocs",
            "captured_at": "2026-07-27T17:33:00",
            "tree": False,
            "git": {
                "commit": "abc1234",
                "full": "abc1234" + "0" * 33,
                "branch": "main",
                "dirty": False,
            },
        },
        "nodes": [
            {
                "file_id": "drydocs/cli.py",
                "project": "drydocs",
                "rel_path": "cli.py",
                "name": "cli.py",
                "extension": ".py",
                "kind": "file",
                "circular": False,
                "abs_path": "C:/somewhere/local/drydocs/cli.py",
            },
            {
                "file_id": "drydocs_core/models/seal.py",
                "project": "drydocs_core",
                "rel_path": "models/seal.py",
                "name": "seal.py",
                "extension": ".py",
                "kind": "file",
                "circular": False,
                "abs_path": "C:/somewhere/local/drydocs_core/models/seal.py",
            },
        ],
        "edges": [["drydocs/cli.py", "drydocs_core/models/seal.py"]],
    }
    doc.update(overrides)
    return doc


def _write(tmp_path: Path, name: str, doc: dict) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Newest-file selection (§H2) — tree files must never be candidates
# ---------------------------------------------------------------------------


def test_selection_ignores_tree_files_despite_name_sort(tmp_path: Path) -> None:
    """'t' > 'd': a bare *.json name-sort would pick tree-this-version.json.
    The glob is drydocs-*.json only, so it cannot."""
    _write(tmp_path, "drydocs-20260101-0000.json", _dep_snapshot())
    newest = _write(tmp_path, "drydocs-20260702-1200.json", _dep_snapshot())
    _write(tmp_path, "tree-this-version.json", {"schema": "depgraph-machine-first/v1"})
    _write(tmp_path, "tree-original.json", {"schema": "depgraph-machine-first/v1"})
    assert select_newest_snapshot(tmp_path) == newest


def test_selection_parses_timestamps_date_only_loses_to_timed(tmp_path: Path) -> None:
    """Found live 2026-07-27: 'drydocs-20260727.json' sorts ORDINALLY after
    'drydocs-20260727-1732.json' ('.' > '-'), so raw string sort picks the
    STALE date-only capture. The parsed (date, time) key must not."""
    _write(tmp_path, "drydocs-20260727.json", _dep_snapshot())
    newest = _write(tmp_path, "drydocs-20260727-1732.json", _dep_snapshot())
    _write(tmp_path, "drydocs-20260727-0900.json", _dep_snapshot())
    assert select_newest_snapshot(tmp_path) == newest


def test_selection_date_only_wins_when_genuinely_newest(tmp_path: Path) -> None:
    newest = _write(tmp_path, "drydocs-20260728.json", _dep_snapshot())
    _write(tmp_path, "drydocs-20260727-2359.json", _dep_snapshot())
    assert select_newest_snapshot(tmp_path) == newest


def test_selection_refuses_empty_dir_loudly(tmp_path: Path) -> None:
    _write(tmp_path, "tree-this-version.json", {"schema": "depgraph-machine-first/v1"})
    with pytest.raises(CodeSnapshotError, match="no drydocs-\\*.json"):
        select_newest_snapshot(tmp_path)


# ---------------------------------------------------------------------------
# The positive discriminator (§G1(a) + build note 2026-07-27)
# ---------------------------------------------------------------------------


def test_refuses_snapshot_with_no_meta_key(tmp_path: Path) -> None:
    """The ACTUAL tree-mode shape: same schema string, NO meta key at all.
    A negative 'refuse if tree is true' check would accept this."""
    doc = _dep_snapshot()
    del doc["meta"]
    path = _write(tmp_path, "drydocs-20260101-0000.json", doc)
    with pytest.raises(CodeSnapshotError, match="no `meta` block"):
        read_snapshot(path)


def test_accepts_all_files_mode(tmp_path: Path) -> None:
    """§G1(a) REVERSED by SME direction: the scanner captures the whole tree by
    default, so `meta.tree: true` is the normal shape. Refusing it would refuse
    every snapshot that exists."""
    doc = _dep_snapshot()
    doc["meta"]["tree"] = True
    path = _write(tmp_path, "drydocs-20260101-0000.json", doc)
    assert read_snapshot(path)["meta"]["tree"] is True


def test_directories_are_skipped_and_counted_not_silently_dropped(tmp_path: Path) -> None:
    """A directory is not a code module. The MODULE adapter still skips and
    counts them — since the 2026-08-05 ruling they are CodeTreeAdapter's rows,
    not dropped work, but the count remains the CLI's cross-check."""
    doc = _dep_snapshot()
    doc["meta"]["tree"] = True
    doc["nodes"].append(
        {
            "file_id": "drydocs/loaders",
            "project": "drydocs",
            "rel_path": "loaders",
            "name": "loaders",
            "extension": "",
            "kind": "dir",
            "circular": False,
        }
    )
    path = _write(tmp_path, "drydocs-20260101-0000.json", doc)
    with CodeSnapshotAdapter(path) as adapter:
        rows = list(adapter.rows())
    assert adapter.skipped_directories == 1
    assert all(r["file_id"] != "drydocs/loaders" for r in rows)


def test_refuses_meta_tree_absent(tmp_path: Path) -> None:
    """meta present but no `tree` key — an unrecognised third shape, still refused.
    This stays a POSITIVE assertion: the headerless one-offs carry no meta at all,
    so a truthiness test on meta.tree would ACCEPT them."""
    doc = _dep_snapshot()
    del doc["meta"]["tree"]
    path = _write(tmp_path, "drydocs-20260101-0000.json", doc)
    with pytest.raises(CodeSnapshotError, match="expected a boolean"):
        read_snapshot(path)


def test_refuses_wrong_schema(tmp_path: Path) -> None:
    path = _write(tmp_path, "drydocs-20260101-0000.json", _dep_snapshot(schema="other/v9"))
    with pytest.raises(CodeSnapshotError, match="schema"):
        read_snapshot(path)


def test_accepts_v2_schema_and_warns_on_unloaded_sections(tmp_path: Path, caplog) -> None:
    """v2 (ritual bump 2026-07-27): nodes/edges/meta unchanged, new lineage
    sections added. Empty sections load silently; NON-empty ones warn — this
    loader loads code modules only, and dropping content silently is the one
    thing the house rule forbids."""
    doc = _dep_snapshot(
        schema="depgraph-machine-first/v2",
        processes=[],
        data_assets=[],
        hosts=[],
        rels=[],
        stats={"nodes": 2},
    )
    path = _write(tmp_path, "drydocs-20260101-0000.json", doc)
    with caplog.at_level("WARNING", logger="drydocs.loaders.code_snapshot"):
        assert len(read_snapshot(path)["nodes"]) == 2
    assert not [r for r in caplog.records if "does NOT" in r.message]

    doc["processes"] = [{"node_id": "x"}]
    path2 = _write(tmp_path, "drydocs-20260102-0000.json", doc)
    with caplog.at_level("WARNING", logger="drydocs.loaders.code_snapshot"):
        read_snapshot(path2)
    assert any("processes" in r.getMessage() for r in caplog.records if r.levelname == "WARNING")


def test_refuses_zero_nodes(tmp_path: Path) -> None:
    """'Succeeds loudly, does nothing' — an empty load is a refusal, not an OK."""
    path = _write(tmp_path, "drydocs-20260101-0000.json", _dep_snapshot(nodes=[]))
    with pytest.raises(CodeSnapshotError, match="zero nodes"):
        read_snapshot(path)


def test_accepts_dependency_mode(tmp_path: Path) -> None:
    path = _write(tmp_path, "drydocs-20260101-0000.json", _dep_snapshot())
    doc = read_snapshot(path)
    assert len(doc["nodes"]) == 2


# ---------------------------------------------------------------------------
# Adapter semantics — abs_path drop (§H4), imports nesting (§D1), SWO (§E1b)
# ---------------------------------------------------------------------------


def test_adapter_drops_abs_path_and_rows_validate(tmp_path: Path) -> None:
    path = _write(tmp_path, "drydocs-20260101-0000.json", _dep_snapshot())
    with CodeSnapshotAdapter(path) as adapter:
        rows = list(adapter.rows())
    assert len(rows) == 2
    for raw in rows:
        assert "abs_path" not in raw, "§H4: abs_path must never leave the adapter"
        model = CodeModuleRow.model_validate(raw)
        params = model.model_dump(mode="json")
        assert "abs_path" not in params


def test_adapter_nests_imports_on_the_importer(tmp_path: Path) -> None:
    path = _write(tmp_path, "drydocs-20260101-0000.json", _dep_snapshot())
    with CodeSnapshotAdapter(path) as adapter:
        by_id = {r["file_id"]: r for r in adapter.rows()}
    assert by_id["drydocs/cli.py"]["imports"] == ["drydocs_core/models/seal.py"]
    assert by_id["drydocs_core/models/seal.py"]["imports"] == []


def test_adapter_maps_extension_to_seeded_swo_iri(tmp_path: Path) -> None:
    path = _write(tmp_path, "drydocs-20260101-0000.json", _dep_snapshot())
    with CodeSnapshotAdapter(path) as adapter:
        rows = list(adapter.rows())
    assert all(r["language_iri"] == EXTENSION_LANGUAGE_IRI[".py"] for r in rows)
    assert adapter.unmapped_extensions == {}


def test_adapter_counts_unmapped_extensions(tmp_path: Path) -> None:
    """Since the 2026-08-05 ruling 'unmapped' means NEITHER a language nor a
    media type — an extension with either binding is typed, not unmapped."""
    doc = _dep_snapshot()
    doc["nodes"][1]["extension"] = ".xyz"
    path = _write(tmp_path, "drydocs-20260101-0000.json", doc)
    with CodeSnapshotAdapter(path) as adapter:
        rows = list(adapter.rows())
    assert rows[1]["language_iri"] is None
    assert rows[1]["media_type_iri"] is None
    assert adapter.unmapped_extensions == {".xyz": 1}


def test_adapter_maps_extension_to_media_type_case_folded(tmp_path: Path) -> None:
    """SME ruling 2026-08-05: non-.py files bind a seeded MediaType term the
    way .py binds a language. Lookup case-folds ('.MD' binds like '.md'), a
    format-only extension is NOT counted unmapped, and .py gets no media type
    (language only — format-vs-language stay separate edges)."""
    doc = _dep_snapshot()
    doc["nodes"][1]["extension"] = ".MD"
    path = _write(tmp_path, "drydocs-20260101-0000.json", doc)
    with CodeSnapshotAdapter(path) as adapter:
        rows = list(adapter.rows())
    assert rows[0]["media_type_iri"] is None  # .py: language, not format
    assert rows[1]["media_type_iri"] == EXTENSION_MEDIA_TYPE_IRI[".md"]
    assert rows[1]["language_iri"] is None
    assert adapter.unmapped_extensions == {}
    model = CodeModuleRow.model_validate(rows[1])
    assert model.media_type_iri == EXTENSION_MEDIA_TYPE_IRI[".md"]


def test_image_files_are_skipped_by_both_adapters(tmp_path: Path) -> None:
    """SME ruling 2026-08-06: image files are not code-graph content. The
    module adapter emits no row for them; the tree adapter drops them from
    child lists (an image must not sneak back in as a CONTAINS_ENTRY stub);
    both COUNT what they skip — never silent."""
    doc = _tree_snapshot()
    doc["nodes"].append(
        {
            "file_id": "drydocs/docs/logo.PNG",  # case-folded like the media lookup
            "kind": "file",
            "rel_path": "docs/logo.PNG",
            "name": "logo.PNG",
            "extension": ".PNG",
            "project": "drydocs",
            "circular": False,
        }
    )
    doc["rels"].append(["drydocs/docs", "CONTAINS", "drydocs/docs/logo.PNG"])
    path = _write(tmp_path, "drydocs-20260101-0000.json", doc)

    with CodeSnapshotAdapter(path) as adapter:
        rows = list(adapter.rows())
    assert adapter.skipped_images == 1
    assert all("logo" not in r["file_id"] for r in rows)
    assert ".PNG" not in adapter.unmapped_extensions, "skipped, not unmapped"

    with CodeTreeAdapter(path) as tree_adapter:
        tree_rows = list(tree_adapter.rows())
    assert tree_adapter.skipped_images == 1
    all_children = [c for r in tree_rows for c in r["child_dir_ids"] + r["child_file_ids"]]
    assert "docs/logo.PNG" not in all_children


def test_media_type_map_never_fakes_an_iana_registration() -> None:
    """Two provenance tiers by construction: every IANA-shaped iri must point
    at the real registry tree, and the conventional unregistered types
    (TypeScript, PowerShell, Cypher, Jupyter) must stay under the local
    namespace — an IANA-shaped iri for them would fabricate a registration."""
    iana = "https://www.iana.org/assignments/media-types/"
    local = "https://drydocs.local/format#"
    for ext, iri in EXTENSION_MEDIA_TYPE_IRI.items():
        assert iri.startswith((iana, local)), f"{ext}: unexpected namespace {iri}"
    for ext in (".ts", ".tsx", ".ps1", ".cypher", ".ipynb"):
        assert EXTENSION_MEDIA_TYPE_IRI[ext].startswith(local), f"{ext} has no IANA registration"


def test_adapter_denormalizes_project_root_and_git(tmp_path: Path) -> None:
    path = _write(tmp_path, "drydocs-20260101-0000.json", _dep_snapshot())
    with CodeSnapshotAdapter(path) as adapter:
        row = next(iter(adapter.rows()))
    assert row["project_id"] == "drydocs"
    assert row["captured_at"] == "2026-07-27T17:33:00"
    assert row["git_commit"] == "abc1234"
    assert row["git_branch"] == "main"


def test_adapter_refuses_malformed_edge(tmp_path: Path) -> None:
    doc = _dep_snapshot(edges=[["only-one-element"]])
    path = _write(tmp_path, "drydocs-20260101-0000.json", doc)
    with CodeSnapshotAdapter(path) as adapter:
        with pytest.raises(CodeSnapshotError, match="malformed edge"):
            list(adapter.rows())


# ---------------------------------------------------------------------------
# Tree adapter — the containment layer (SME ruling 2026-08-05)
# ---------------------------------------------------------------------------


def test_tree_adapter_builds_rows_and_survives_the_root_name_collision(tmp_path: Path) -> None:
    """The repo root ('drydocs', rel_path '.') and the top-level package dir
    ('drydocs/drydocs' -> stripped 'drydocs') must stay DISTINCT rows: the
    root maps onto :Project (is_root), the package becomes :CodeDirectory
    {file_id:'drydocs'}."""
    path = _write(tmp_path, "drydocs-20260101-0000.json", _tree_snapshot())
    with CodeTreeAdapter(path) as adapter:
        rows = [CodeDirectoryRow.model_validate(r) for r in adapter.rows()]
    assert len(rows) == 3

    root = rows[0]  # parents-before-children: depth sort puts the root first
    assert root.is_root and root.file_id == "drydocs" and root.rel_path == "."
    assert root.child_dir_ids == ["docs", "drydocs"]
    assert root.child_file_ids == ["README.md"]

    by_rel = {r.rel_path: r for r in rows}
    package = by_rel["drydocs"]
    assert not package.is_root
    assert package.file_id == "drydocs", "package dir key must be the stripped repo-relative path"
    assert package.child_file_ids == ["drydocs/cli.py"]
    assert by_rel["docs"].child_file_ids == ["docs/guide.md"]

    # Every containment rel of the snapshot is accounted for, none invented.
    total_children = sum(len(r.child_dir_ids) + len(r.child_file_ids) for r in rows)
    assert total_children == 5


def test_tree_adapter_refuses_roots_only_snapshot(tmp_path: Path) -> None:
    """A dependency-mode (-CodeOnly) snapshot has no containment tree — the
    tree loader refuses it loudly; the MODULE loader still loads it."""
    path = _write(tmp_path, "drydocs-20260101-0000.json", _dep_snapshot())
    with CodeTreeAdapter(path) as adapter:
        with pytest.raises(CodeSnapshotError, match="meta.tree is false"):
            list(adapter.rows())


def test_tree_adapter_refuses_tree_with_no_rels(tmp_path: Path) -> None:
    doc = _tree_snapshot()
    doc["rels"] = []
    path = _write(tmp_path, "drydocs-20260101-0000.json", doc)
    with CodeTreeAdapter(path) as adapter:
        with pytest.raises(CodeSnapshotError, match="zero rels"):
            list(adapter.rows())


def test_tree_adapter_refuses_malformed_and_dangling_rels(tmp_path: Path) -> None:
    doc = _tree_snapshot()
    doc["rels"][0] = ["drydocs", "CONTAINS"]  # 2 elements
    path = _write(tmp_path, "drydocs-20260101-0000.json", doc)
    with CodeTreeAdapter(path) as adapter:
        with pytest.raises(CodeSnapshotError, match="malformed rel"):
            list(adapter.rows())

    doc = _tree_snapshot()
    doc["rels"][0] = ["drydocs", "CONTAINS", "drydocs/ghost-dir"]  # not in nodes
    path2 = _write(tmp_path, "drydocs-20260102-0000.json", doc)
    with CodeTreeAdapter(path2) as adapter:
        with pytest.raises(CodeSnapshotError, match="absent from"):
            list(adapter.rows())


# ---------------------------------------------------------------------------
# The committed artifact itself — the loader's real input stays loadable
# ---------------------------------------------------------------------------


def test_committed_newest_snapshot_is_accepted_and_clean() -> None:
    if not DEFAULT_SNAPSHOT_DIR.exists():  # pragma: no cover
        pytest.skip("snapshot dir absent")
    path = select_newest_snapshot(DEFAULT_SNAPSHOT_DIR)
    with CodeSnapshotAdapter(path) as adapter:
        rows = [CodeModuleRow.model_validate(r) for r in adapter.rows()]
    assert rows, "newest committed snapshot yielded no rows"
    # file_id is the key: unique across all rows (§C2).
    ids = [r.file_id for r in rows]
    assert len(ids) == len(set(ids))

    # §E2, RESTATED for the all-files scan. The old assertion here was
    # `unmapped_extensions == {}` — true only while the scan emitted nothing but
    # .py. An all-files snapshot carries .md, .json, .xsd, .ttf and ~40 more, and
    # only FOUR languages were ever seeded, so an empty-unmapped assertion would
    # now be a demand to seed an SWO term for every file type on disk. The intent
    # it was protecting is what is asserted instead: every extension that DOES
    # have a seeded term is bound, and everything else is COUNTED rather than
    # silently skipped (the CLI reports the counts; §E1(b) skips the edge).
    for ext in EXTENSION_LANGUAGE_IRI:
        assert ext not in adapter.unmapped_extensions, f"{ext} has a seeded term but was not bound"
    assert adapter.unmapped_extensions, (
        "an all-files snapshot must report unmapped extensions — an empty dict here "
        "means the skip is going unrecorded, which is what §E2 forbids"
    )
    bound = sum(1 for r in rows if r.language_iri)
    assert bound, "no row bound to a seeded SWO language term"
    # Media types (2026-08-05 ruling): every mapped extension binds, and the
    # residue with no binding at all stays small and NAMED — a new unmapped
    # extension should be a conscious decision, not silent drift.
    for ext in EXTENSION_MEDIA_TYPE_IRI:
        assert ext not in adapter.unmapped_extensions, f"{ext} has a seeded term but was not bound"
    assert sum(1 for r in rows if r.media_type_iri) > bound, (
        "the non-.py majority should out-bind the language rows"
    )


def test_committed_newest_snapshot_tree_loads_whole(tmp_path: Path) -> None:
    """The real ritual snapshot's containment layer: every dir becomes a row,
    exactly one root, and every rel lands in exactly one child list."""
    if not DEFAULT_SNAPSHOT_DIR.exists():  # pragma: no cover
        pytest.skip("snapshot dir absent")
    path = select_newest_snapshot(DEFAULT_SNAPSHOT_DIR)
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not doc.get("meta", {}).get("tree"):  # pragma: no cover
        pytest.skip("newest committed snapshot is roots-only")
    with CodeTreeAdapter(path) as adapter:
        rows = [CodeDirectoryRow.model_validate(r) for r in adapter.rows()]
    n_dirs = sum(1 for n in doc["nodes"] if n.get("kind") == "dir")
    assert len(rows) == n_dirs
    roots = [r for r in rows if r.is_root]
    assert len(roots) == 1
    # Every rel is either loaded or a COUNTED image skip — nothing vanishes.
    total_children = sum(len(r.child_dir_ids) + len(r.child_file_ids) for r in rows)
    assert total_children + adapter.skipped_images == len(doc.get("rels", []))
    n_images = sum(
        1
        for n in doc["nodes"]
        if n.get("kind") == "file"
        and str(n.get("extension") or "").lower() in IMAGE_EXTENSIONS_SKIPPED
    )
    assert adapter.skipped_images == n_images
    # Non-root keys unique and never equal to a key claimed by two dirs.
    ids = [r.file_id for r in rows if not r.is_root]
    assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# Wiring declarations — cypher, constraints, supplement, loader class
# ---------------------------------------------------------------------------


def test_loader_class_wiring() -> None:
    assert CodeSnapshotLoader.name == "code_snapshot.v1"
    assert CodeSnapshotLoader.cypher_path == CYPHER_FILE
    assert CodeSnapshotLoader.row_model is CodeModuleRow
    assert CodeSnapshotLoader.sweep_label == "CodeModule"
    assert CYPHER_FILE.exists()


def test_tree_loader_class_wiring() -> None:
    assert CodeTreeLoader.name == "code_tree.v1"
    assert CodeTreeLoader.cypher_path == TREE_CYPHER_FILE
    assert CodeTreeLoader.row_model is CodeDirectoryRow
    assert CodeTreeLoader.sweep_label == "CodeDirectory"
    assert CodeTreeLoader.source_id == CodeSnapshotLoader.source_id, (
        "both passes read the same registered source"
    )
    assert TREE_CYPHER_FILE.exists()


def test_cypher_writes_only_gated_edges_and_drops_abs_path() -> None:
    text = CYPHER_FILE.read_text(encoding="utf-8")
    for token in (
        "HAS_MODULE",
        "IMPORTS",
        "IS_ENCODED_IN",
        "HAS_MEDIA_TYPE",
        ":Project",
        ":CodeModule",
    ):
        assert token in text, f"cypher missing {token}"
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("//"))
    assert (
        "abs_path" not in code
    ), "§H4: abs_path must not appear in cypher CODE (comments may document the drop)"
    # M2 pull-provenance convention (§D3 — divergence rejected).
    for prop in ("first_seen_at", "last_seen_at", "last_run_id"):
        assert prop in text


def test_tree_cypher_writes_the_ruled_shape() -> None:
    text = TREE_CYPHER_FILE.read_text(encoding="utf-8")
    for token in ("CONTAINS_ENTRY", ":CodeDirectory", ":Project", ":CodeModule"):
        assert token in text, f"tree cypher missing {token}"
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("//"))
    assert "abs_path" not in code
    for prop in ("first_seen_at", "last_seen_at", "last_run_id"):
        assert prop in text


def test_constraints_declare_the_three_keys() -> None:
    text = CONSTRAINTS_FILE.read_text(encoding="utf-8")
    assert "REQUIRE p.project_id IS UNIQUE" in text
    assert "REQUIRE m.file_id IS UNIQUE" in text
    assert "REQUIRE d.file_id IS UNIQUE" in text  # CodeDirectory (ruling 2026-08-05)


def test_supplement_declares_terms_and_standard_mappings() -> None:
    text = SUPPLEMENT_FILE.read_text(encoding="utf-8")
    for iri_tail in (
        "#Project",
        "#CodeModule",
        "#CodeDirectory",
        "#hasModule",
        "#imports",
        "#isEncodedIn",
        "#containsEntry",
        "#hasMediaType",
    ):
        assert f"https://drydocs.local/ontology{iri_tail}" in text
    assert (
        "http://www.ebi.ac.uk/swo/SWO_0000741" in text
    ), "IS_ENCODED_IN must MAPS_TO the seeded SWO 'is encoded in' term (§E1(b))"
    assert (
        "http://www.w3.org/ns/dcat#mediaType" in text
    ), "HAS_MEDIA_TYPE must MAPS_TO the seeded dcat:mediaType term"
