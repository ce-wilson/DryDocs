"""S5 — the concatenating fragment reader and the two split registries.

The split-time proof (2026-08-04, recorded in the S5 commit) compared the
merged fragments against the pre-split monoliths entry-by-entry: 83
local_relationships and 38 mappings deep-equal, sections identical, the only
change being domain-grouped entry order. These tests carry the standing half
of that guarantee: the merge is deterministic, loud on duplicates, and both
committed directories parse into the documents their consumers expect.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from drydocs_core import yaml_fragments
from drydocs_core.yaml_fragments import (
    FragmentSourceError,
    fragment_paths,
    load_yaml_source,
    merged_text,
)

REPO = Path(__file__).resolve().parents[2]
VOCAB_DIR = REPO / "drydocs_core" / "ontology" / "relationship_vocabulary"
MAP_DIR = REPO / "config" / "taxonomy-ontology-map"


# ---- the reader --------------------------------------------------------------


def test_single_file_input_stays_first_class(tmp_path: Path) -> None:
    f = tmp_path / "one.yaml"
    f.write_text("a: 1\nb: [2, 3]\n", encoding="utf-8", newline="\n")
    assert load_yaml_source(f) == {"a": 1, "b": [2, 3]}
    assert merged_text(f) == "a: 1\nb: [2, 3]\n"


def test_fragments_merge_in_sorted_filename_order(tmp_path: Path) -> None:
    (tmp_path / "10-open.yaml").write_text("items:\n  - id: a\n", encoding="utf-8")
    (tmp_path / "20-more.yaml").write_text("  - id: b\n", encoding="utf-8")
    (tmp_path / "05-header.yaml").write_text("# just a comment\n", encoding="utf-8")
    doc = load_yaml_source(tmp_path)
    assert [e["id"] for e in doc["items"]] == ["a", "b"]
    assert [p.name for p in fragment_paths(tmp_path)] == [
        "05-header.yaml",
        "10-open.yaml",
        "20-more.yaml",
    ]


def test_missing_source_and_empty_directory_are_loud(tmp_path: Path) -> None:
    with pytest.raises(FragmentSourceError, match="not found"):
        merged_text(tmp_path / "absent")
    empty = tmp_path / "emptydir"
    empty.mkdir()
    with pytest.raises(FragmentSourceError, match="no \\*.yaml"):
        merged_text(empty)


def test_duplicate_top_level_key_is_loud(tmp_path: Path) -> None:
    """Two fragments both declaring the same section must never last-wins."""
    (tmp_path / "10-a.yaml").write_text("items:\n  - id: a\n", encoding="utf-8")
    (tmp_path / "20-b.yaml").write_text("items:\n  - id: b\n", encoding="utf-8")
    with pytest.raises(FragmentSourceError, match="duplicate key 'items'"):
        load_yaml_source(tmp_path)


def test_duplicate_entry_id_across_fragments_is_loud(tmp_path: Path) -> None:
    (tmp_path / "10-a.yaml").write_text("items:\n  - id: twin\n", encoding="utf-8")
    (tmp_path / "20-b.yaml").write_text("  - id: twin\n", encoding="utf-8")
    with pytest.raises(FragmentSourceError, match="duplicate items\\[\\].id"):
        load_yaml_source(tmp_path, unique={"items": "id"})


# ---- the two committed registries --------------------------------------------


def test_vocabulary_directory_parses_with_unique_ids() -> None:
    doc = load_yaml_source(
        VOCAB_DIR,
        unique={"local_relationships": "id", "node_classifications": "label"},
    )
    assert set(doc) == {
        "node_classifications",
        "property_terms",
        "prov_matrix",
        "local_relationships",
    }
    assert len(doc["prov_matrix"]) == 9  # the stable decision table
    assert len(doc["local_relationships"]) >= 83


def test_ontology_map_directory_parses_with_unique_ids() -> None:
    doc = load_yaml_source(MAP_DIR, unique={"mappings": "id"})
    assert doc["schema"] == "drydocs.taxonomy-ontology-map.v1"
    assert len(doc["mappings"]) >= 38
    assert set(doc["summary"]) <= {"proposed", "confirmed", "applied", "rejected"}


# ---- the vocabulary lifecycle invariants (G55 acceptance) ---------------------


def _vocab_entries() -> list[dict]:
    doc = load_yaml_source(VOCAB_DIR, unique={"local_relationships": "id"})
    return doc["local_relationships"]


# Semantics seeded by the CORE schema (ontology.cypher), not a supplement:
# all_was_generated_by realises a pure PROV property whose ProvProperty term
# is a core seed; quality_in_dimension is written at bootstrap by ontology.cypher
# itself (loader: ontology.cypher — registered retroactively at C23, before
# the vocabulary discipline existed). Nothing enters this set without the
# same core-seeded justification in its entry note.
# ids repointed at G87 (2026-08-21): prov_ -> all_, c23_ -> quality_ (add-new + deprecate-old).
CORE_SEEDED = {"all_was_generated_by", "quality_in_dimension"}


def test_no_entry_is_active_without_a_supplement() -> None:
    """00-header.yaml's lifecycle: active means the supplement block EXISTS —
    an active entry with `supplement: ~` would claim graph semantics nobody
    seeded (the G55 acceptance's first invariant). Core-seeded entries are the
    documented exception: their terms live in ontology.cypher itself."""
    offenders = [
        e["id"]
        for e in _vocab_entries()
        if e.get("status") == "active" and not e.get("supplement") and e["id"] not in CORE_SEEDED
    ]
    assert not offenders, f"active without a supplement: {offenders}"


def test_g22_dispositions_are_terminal() -> None:
    """Gate rua-load-shapes (SIGNED OFF 2026-08-07, 28/28), applied at G55:
    activated entries are active, the declined entry is deprecated (a declined
    entry left `planned` would silently read as still-a-candidate — the state
    the G55 acceptance names), and the held entry stays planned until K17."""
    status = {e["id"]: e.get("status") for e in _vocab_entries()}
    assert status["scheduler_invokes"] == "active"  # §A3
    assert status["scheduler_uses_artifact"] == "active"  # §A4
    assert status["scheduler_reads_from"] == "active"  # §A5
    assert status["scheduler_writes_to"] == "active"  # §A5
    assert status["m3_runs_on_etl_host"] == "deprecated"  # §A2 declined
    assert status["scheduler_delegates_to"] == "planned"  # §A1 held behind K17
    assert status["arch_owns_directory"] == "planned"  # §C1 — build blocked on K17
    assert status["arch_sources"] == "planned"  # §C2
    assert status["scheduler_triggers"] == "planned"  # not a G22 candidate — unchanged


def test_fragment_files_each_end_with_a_newline() -> None:
    """Concatenation must never glue one fragment's last line to the next
    fragment's first — a missing trailing newline corrupts the merged text."""
    for d in (VOCAB_DIR, MAP_DIR):
        for p in fragment_paths(d):
            assert p.read_bytes().endswith(b"\n"), f"{p} lacks a trailing newline"


def test_fragment_directories_hold_only_yaml() -> None:
    """A stray file in a fragment directory is invisible to the merge — refuse
    it the L20 way rather than silently ignoring it."""
    for d in (VOCAB_DIR, MAP_DIR):
        stray = [p.name for p in d.iterdir() if p.is_file() and p.suffix != ".yaml"]
        assert not stray, f"{d}: non-fragment files would be silently unmerged: {stray}"


def test_monoliths_are_gone() -> None:
    """The single-file forms must not quietly return — a resurrected monolith
    beside the directory would fork the source of truth."""
    assert not (VOCAB_DIR.parent / "relationship_vocabulary.yaml").exists()
    assert not (MAP_DIR.parent / "taxonomy-ontology-map.yaml").exists()
    assert yaml_fragments is not None
