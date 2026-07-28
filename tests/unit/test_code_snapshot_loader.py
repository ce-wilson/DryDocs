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
    CodeSnapshotAdapter,
    CodeSnapshotError,
    CodeSnapshotLoader,
    read_snapshot,
    select_newest_snapshot,
)
from drydocs_core.models.code_snapshot import CodeModuleRow

REPO = Path(__file__).resolve().parents[2]
CYPHER_FILE = REPO / "drydocs" / "loaders" / "cypher" / "code_snapshot.cypher"
CONSTRAINTS_FILE = REPO / "drydocs_core" / "schema" / "constraints.cypher"
SUPPLEMENT_FILE = REPO / "drydocs_core" / "schema" / "ontology_supplement.cypher"


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


def test_refuses_meta_tree_true(tmp_path: Path) -> None:
    doc = _dep_snapshot()
    doc["meta"]["tree"] = True
    path = _write(tmp_path, "drydocs-20260101-0000.json", doc)
    with pytest.raises(CodeSnapshotError, match="tree-mode input is refused"):
        read_snapshot(path)


def test_refuses_meta_tree_absent(tmp_path: Path) -> None:
    """meta present but no tree key — still not `exactly false`, still refused."""
    doc = _dep_snapshot()
    del doc["meta"]["tree"]
    path = _write(tmp_path, "drydocs-20260101-0000.json", doc)
    with pytest.raises(CodeSnapshotError, match="required exactly false"):
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
    doc = _dep_snapshot(schema="depgraph-machine-first/v2",
                        processes=[], data_assets=[], hosts=[], rels=[],
                        stats={"nodes": 2})
    path = _write(tmp_path, "drydocs-20260101-0000.json", doc)
    with caplog.at_level("WARNING", logger="drydocs.loaders.code_snapshot"):
        assert len(read_snapshot(path)["nodes"]) == 2
    assert not [r for r in caplog.records if "does NOT" in r.message]

    doc["processes"] = [{"node_id": "x"}]
    path2 = _write(tmp_path, "drydocs-20260102-0000.json", doc)
    with caplog.at_level("WARNING", logger="drydocs.loaders.code_snapshot"):
        read_snapshot(path2)
    assert any("processes" in r.getMessage() for r in caplog.records
               if r.levelname == "WARNING")


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
    doc = _dep_snapshot()
    doc["nodes"][1]["extension"] = ".xyz"
    path = _write(tmp_path, "drydocs-20260101-0000.json", doc)
    with CodeSnapshotAdapter(path) as adapter:
        rows = list(adapter.rows())
    assert rows[1]["language_iri"] is None
    assert adapter.unmapped_extensions == {".xyz": 1}


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
# The committed artifact itself — the loader's real input stays loadable
# ---------------------------------------------------------------------------

def test_committed_newest_snapshot_is_accepted_and_clean() -> None:
    if not DEFAULT_SNAPSHOT_DIR.exists():  # pragma: no cover
        pytest.skip("snapshot dir absent")
    path = select_newest_snapshot(DEFAULT_SNAPSHOT_DIR)
    with CodeSnapshotAdapter(path) as adapter:
        rows = [CodeModuleRow.model_validate(r) for r in adapter.rows()]
    assert rows, "newest committed snapshot yielded no rows"
    # §E2: dependency mode emits only extensions with a seeded SWO term today.
    assert adapter.unmapped_extensions == {}, (
        "committed snapshot carries extensions with no seeded SwoClass term — "
        "either widen EXTENSION_LANGUAGE_IRI or accept the skipped edges consciously"
    )
    # file_id is the key: unique across all rows (§C2).
    ids = [r.file_id for r in rows]
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


def test_cypher_writes_only_gated_edges_and_drops_abs_path() -> None:
    text = CYPHER_FILE.read_text(encoding="utf-8")
    for token in ("HAS_MODULE", "IMPORTS", "IS_ENCODED_IN", ":Project", ":CodeModule"):
        assert token in text, f"cypher missing {token}"
    code = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("//")
    )
    assert "abs_path" not in code, "§H4: abs_path must not appear in cypher CODE (comments may document the drop)"
    # M2 pull-provenance convention (§D3 — divergence rejected).
    for prop in ("first_seen_at", "last_seen_at", "last_run_id"):
        assert prop in text


def test_constraints_declare_the_two_new_keys() -> None:
    text = CONSTRAINTS_FILE.read_text(encoding="utf-8")
    assert "REQUIRE p.project_id IS UNIQUE" in text
    assert "REQUIRE m.file_id IS UNIQUE" in text


def test_supplement_declares_terms_and_swo_mapping() -> None:
    text = SUPPLEMENT_FILE.read_text(encoding="utf-8")
    for iri_tail in ("#Project", "#CodeModule", "#hasModule", "#imports", "#isEncodedIn"):
        assert f"https://drydocs.local/ontology{iri_tail}" in text
    assert "http://www.ebi.ac.uk/swo/SWO_0000741" in text, (
        "IS_ENCODED_IN must MAPS_TO the seeded SWO 'is encoded in' term (§E1(b))"
    )
