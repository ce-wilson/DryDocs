"""G25 — the DPL taxonomy-registry ingestion seam (per-SEAL Swagger exports).

SYNTHETIC fixtures throughout (shape-faithful, value-fake; the field names ARE
the assumed contract documented in ``dpl_registry.py`` — a real sample
validates or amends them; real exports are Internal-Confidential and live in
the dpl-registry/ landing zone, never here). Each case pins one acceptance
clause: (a) taxonomy-first staging records with provenance, (b) v-shape
tolerance (bare list / wrapped) + malformed counted, (c) the active flag
staged-not-judged, (d) the GUID cross-check vs G15 observations, (e) the
clone-lag third column, (f) NO graph writes.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from drydocs_lineage.extractors import (
    DplRegistryExtractor,
    cross_check,
)
from drydocs_lineage.model import LineageGraph, ProcessNode, process_id

SEAL_A = "88888"
SEAL_B = "77777"
GUID_P1 = "11111111-aaaa-4bbb-8ccc-000000000001"   # registered + observed
GUID_P2 = "22222222-aaaa-4bbb-8ccc-000000000002"   # registered, NOT observed
GUID_P3 = "33333333-aaaa-4bbb-8ccc-000000000003"   # registered under SEAL_B
GUID_X = "99999999-aaaa-4bbb-8ccc-000000000009"    # observed, NOT registered
DS_1 = "aaaa0001-dddd-4eee-8fff-000000000010"


@pytest.fixture()
def registry_root(tmp_path: Path) -> Path:
    root = tmp_path / "dpl-registry"
    seal_a = root / SEAL_A
    seal_a.mkdir(parents=True)
    # bare-list shape, record-level seal, mixed active spellings
    (seal_a / "pipeline_id.json").write_text(json.dumps([
        {"pipelineId": GUID_P1, "version": "3", "active": True,
         "ownerSealId": SEAL_A, "name": "conform-accounts"},
        {"pipelineId": GUID_P2, "version": "1", "active": "INACTIVE",
         "sealId": SEAL_A},
    ]), encoding="utf-8")
    # wrapped shape
    (seal_a / "dataset_id.json").write_text(json.dumps(
        {"datasets": [{"datasetId": DS_1, "version": "2", "active": "ACTIVE"}]},
    ), encoding="utf-8")
    # second SEAL: no seal field in the record — the folder name is the key
    seal_b = root / SEAL_B
    seal_b.mkdir()
    (seal_b / "pipeline_id.json").write_text(json.dumps([
        {"pipelineId": GUID_P3, "active": "MAYBE"},   # unknown spelling
    ]), encoding="utf-8")
    return root


@pytest.fixture()
def run(registry_root: Path):
    return DplRegistryExtractor().extract(registry_root)


def _seed_graph() -> LineageGraph:
    """What ControlMInventoryExtractor would have left behind: G15-observed
    DPL launches keyed proc#dpl:{GUID}."""
    g = LineageGraph()
    for guid in (GUID_P1, GUID_X):
        g.add_process(ProcessNode(
            node_id=process_id("dpl", guid), kind="dpl", name="dt-launcher.sh"))
    return g


# -- (a) taxonomy-first staging records with provenance ------------------------------

def test_records_are_flat_classification_facts(run) -> None:
    by_guid = {r.guid: r for r in run.records}
    p1 = by_guid[GUID_P1]
    assert (p1.kind, p1.version, p1.active, p1.seal) == ("pipeline", "3", "true", SEAL_A)
    assert p1.name == "conform-accounts"
    assert p1.source_file.endswith(f"{SEAL_A}/pipeline_id.json")   # provenance
    ds = by_guid[DS_1]
    assert (ds.kind, ds.active) == ("dataset", "true")
    assert run.coverage.pipelines_read == 3 and run.coverage.datasets_read == 1


def test_seal_falls_back_to_the_per_seal_folder(run) -> None:
    p3 = next(r for r in run.records if r.guid == GUID_P3)
    assert p3.seal == SEAL_B                          # no field — folder keyed it
    assert run.coverage.records_no_seal == 0


# -- (b) shape tolerance + malformed counted ------------------------------------------

def test_invalid_and_keyless_exports_counted(tmp_path: Path) -> None:
    root = tmp_path / "dpl-registry"
    bad = root / SEAL_A
    bad.mkdir(parents=True)
    (bad / "pipeline_id.json").write_text("not json", encoding="utf-8")
    (bad / "dataset_id.json").write_text(json.dumps({"unexpected": "shape"}),
                                         encoding="utf-8")
    other = root / SEAL_B
    other.mkdir()
    (other / "pipeline_id.json").write_text(json.dumps(
        [{"version": "9"}, "not-a-dict", {"pipelineId": GUID_P1}],
    ), encoding="utf-8")
    result = DplRegistryExtractor().extract(root)
    assert result.coverage.files_invalid == 2
    assert result.coverage.records_no_guid == 2
    assert result.coverage.pipelines_read == 1        # the good record still lands


def test_duplicate_guids_counted_first_wins(registry_root: Path) -> None:
    dupe_dir = registry_root / "99999"   # sorts after SEAL_A: read second by design
    dupe_dir.mkdir()
    (dupe_dir / "pipeline_id.json").write_text(json.dumps(
        [{"pipelineId": GUID_P1, "version": "9"}],    # GUID_P1 again
    ), encoding="utf-8")
    result = DplRegistryExtractor().extract(registry_root)
    assert result.coverage.duplicate_guids == 1
    p1 = next(r for r in result.records if r.guid == GUID_P1)
    assert p1.version == "3"                          # first seen wins


# -- (c) the active flag: staged, never judged ----------------------------------------

def test_active_flag_normalized_and_unknown_counted(run) -> None:
    by_guid = {r.guid: r for r in run.records}
    assert by_guid[GUID_P1].active == "true"          # bool True
    assert by_guid[GUID_P2].active == "false"         # "INACTIVE"
    assert by_guid[GUID_P3].active == ""              # "MAYBE" — staged unknown
    assert run.coverage.active_unknown == 1
    assert "active_unknown=1" in run.coverage.summary()


# -- (d) the GUID cross-check vs G15 observations --------------------------------------

def test_cross_check_counts_and_lists_both_directions(run) -> None:
    report = cross_check(run, _seed_graph())
    assert report.registered_pipelines == 3
    assert report.observed_pipelines == 2
    assert report.observed_not_registered == [GUID_X]     # the code-fetch gap family
    assert report.registered_not_observed == sorted([GUID_P2, GUID_P3])
    assert report.clone_checked is False
    assert "observed_not_registered=1" in report.summary()


# -- (e) the clone-lag third column (SME 2026-07-23) ------------------------------------

def test_clone_column_measures_the_lag(run) -> None:
    clone_guids = {GUID_P1, GUID_X}                   # clone lags: P2/P3 not merged yet
    report = cross_check(run, _seed_graph(), clone_guids=clone_guids)
    assert report.clone_checked is True
    assert report.clone_pipelines == 2
    assert report.registered_not_in_clone == sorted([GUID_P2, GUID_P3])  # the lag, listed
    assert report.clone_not_registered == [GUID_X]    # feature-branch-only material
    assert "registered_not_in_clone=2" in report.summary()


# -- (f) NO graph writes -----------------------------------------------------------------

def test_extract_and_cross_check_never_touch_the_graph(registry_root: Path) -> None:
    g = _seed_graph()
    before = g.stats()
    result = DplRegistryExtractor().extract(registry_root)
    cross_check(result, g, clone_guids={GUID_P1})
    assert g.stats() == before                        # read-only, candidates stay flat
    assert g.rels == set()
