"""G25 — the DPL taxonomy-registry ingestion seam (per-SEAL Swagger exports).

SYNTHETIC fixtures throughout (shape-faithful, value-fake; the field names ARE
the assumed contract documented in ``dpl_registry.py`` — a real sample
validates or amends them; real exports are confidential (Internal, J23) and live in
the dpl-registry/ landing zone, never here). Each case pins one acceptance
clause: (a) taxonomy-first staging records with provenance, (b) v-shape
tolerance (bare list / wrapped) + malformed counted, (c) the active flag
staged-not-judged, (d) the GUID cross-check vs G15 observations, (e) the
clone-lag third column, (f) NO graph writes.

G135 adds (g): the accounting reports a contract that is WRONG, not only one
that is broken. Every case above (a)-(f) supplies the assumed field names, so
none of them can fail when the assumption itself is wrong — which is why the
guid-only fixture exists.
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
GUID_P1 = "11111111-aaaa-4bbb-8ccc-000000000001"  # registered + observed
GUID_P2 = "22222222-aaaa-4bbb-8ccc-000000000002"  # registered, NOT observed
GUID_P3 = "33333333-aaaa-4bbb-8ccc-000000000003"  # registered under SEAL_B
GUID_X = "99999999-aaaa-4bbb-8ccc-000000000009"  # observed, NOT registered
DS_1 = "aaaa0001-dddd-4eee-8fff-000000000010"


@pytest.fixture()
def registry_root(tmp_path: Path) -> Path:
    root = tmp_path / "dpl-registry"
    seal_a = root / SEAL_A
    seal_a.mkdir(parents=True)
    # bare-list shape, record-level seal, mixed active spellings
    (seal_a / "pipeline_id.json").write_text(
        json.dumps(
            [
                {
                    "pipelineId": GUID_P1,
                    "version": "3",
                    "active": True,
                    "ownerSealId": SEAL_A,
                    "name": "conform-accounts",
                },
                {"pipelineId": GUID_P2, "version": "1", "active": "INACTIVE", "sealId": SEAL_A},
            ]
        ),
        encoding="utf-8",
    )
    # wrapped shape
    (seal_a / "dataset_id.json").write_text(
        json.dumps(
            {"datasets": [{"datasetId": DS_1, "version": "2", "active": "ACTIVE"}]},
        ),
        encoding="utf-8",
    )
    # second SEAL: no seal field in the record — the folder name is the key
    seal_b = root / SEAL_B
    seal_b.mkdir()
    (seal_b / "pipeline_id.json").write_text(
        json.dumps(
            [
                {"pipelineId": GUID_P3, "active": "MAYBE"},  # unknown spelling
            ]
        ),
        encoding="utf-8",
    )
    return root


@pytest.fixture()
def run(registry_root: Path):
    return DplRegistryExtractor().extract(registry_root)


def _seed_graph() -> LineageGraph:
    """What ControlMInventoryExtractor would have left behind: G15-observed
    DPL launches keyed proc#dpl:{GUID}."""
    g = LineageGraph()
    for guid in (GUID_P1, GUID_X):
        g.add_process(
            ProcessNode(node_id=process_id("dpl", guid), kind="dpl", name="dt-launcher.sh")
        )
    return g


# -- (a) taxonomy-first staging records with provenance ------------------------------


def test_records_are_flat_classification_facts(run) -> None:
    by_guid = {r.guid: r for r in run.records}
    p1 = by_guid[GUID_P1]
    assert (p1.kind, p1.version, p1.active, p1.seal) == ("pipeline", "3", "true", SEAL_A)
    assert p1.name == "conform-accounts"
    assert p1.source_file.endswith(f"{SEAL_A}/pipeline_id.json")  # provenance
    ds = by_guid[DS_1]
    assert (ds.kind, ds.active) == ("dataset", "true")
    assert run.coverage.pipelines_read == 3 and run.coverage.datasets_read == 1


def test_seal_falls_back_to_the_per_seal_folder(run) -> None:
    p3 = next(r for r in run.records if r.guid == GUID_P3)
    assert p3.seal == SEAL_B  # no field — folder keyed it
    assert run.coverage.records_no_seal == 0


# -- (b) shape tolerance + malformed counted ------------------------------------------


def test_invalid_and_keyless_exports_counted(tmp_path: Path) -> None:
    root = tmp_path / "dpl-registry"
    bad = root / SEAL_A
    bad.mkdir(parents=True)
    (bad / "pipeline_id.json").write_text("not json", encoding="utf-8")
    (bad / "dataset_id.json").write_text(json.dumps({"unexpected": "shape"}), encoding="utf-8")
    other = root / SEAL_B
    other.mkdir()
    (other / "pipeline_id.json").write_text(
        json.dumps(
            [{"version": "9"}, "not-a-dict", {"pipelineId": GUID_P1}],
        ),
        encoding="utf-8",
    )
    result = DplRegistryExtractor().extract(root)
    assert result.coverage.files_invalid == 2
    assert result.coverage.records_no_guid == 2
    assert result.coverage.pipelines_read == 1  # the good record still lands


def test_duplicate_guids_counted_first_wins(registry_root: Path) -> None:
    dupe_dir = registry_root / "99999"  # sorts after SEAL_A: read second by design
    dupe_dir.mkdir()
    (dupe_dir / "pipeline_id.json").write_text(
        json.dumps(
            [{"pipelineId": GUID_P1, "version": "9"}],  # GUID_P1 again
        ),
        encoding="utf-8",
    )
    result = DplRegistryExtractor().extract(registry_root)
    assert result.coverage.duplicate_guids == 1
    p1 = next(r for r in result.records if r.guid == GUID_P1)
    assert p1.version == "3"  # first seen wins


# -- (c) the active flag: staged, never judged ----------------------------------------


def test_active_flag_normalized_and_unknown_counted(run) -> None:
    by_guid = {r.guid: r for r in run.records}
    assert by_guid[GUID_P1].active == "true"  # bool True
    assert by_guid[GUID_P2].active == "false"  # "INACTIVE"
    assert by_guid[GUID_P3].active == ""  # "MAYBE" — staged unknown
    assert run.coverage.active_unknown == 1
    assert "active_unknown=1" in run.coverage.summary()


# -- (d) the GUID cross-check vs G15 observations --------------------------------------


def test_cross_check_counts_and_lists_both_directions(run) -> None:
    report = cross_check(run, _seed_graph())
    assert report.registered_pipelines == 3
    assert report.observed_pipelines == 2
    assert report.observed_not_registered == [GUID_X]  # the code-fetch gap family
    assert report.registered_not_observed == sorted([GUID_P2, GUID_P3])
    assert report.clone_checked is False
    assert "observed_not_registered=1" in report.summary()


# -- (e) the clone-lag third column (SME 2026-07-23) ------------------------------------


def test_clone_column_measures_the_lag(run) -> None:
    clone_guids = {GUID_P1, GUID_X}  # clone lags: P2/P3 not merged yet
    report = cross_check(run, _seed_graph(), clone_guids=clone_guids)
    assert report.clone_checked is True
    assert report.clone_pipelines == 2
    assert report.registered_not_in_clone == sorted([GUID_P2, GUID_P3])  # the lag, listed
    assert report.clone_not_registered == [GUID_X]  # feature-branch-only material
    assert "registered_not_in_clone=2" in report.summary()


# -- (f) NO graph writes -----------------------------------------------------------------


def test_extract_and_cross_check_never_touch_the_graph(registry_root: Path) -> None:
    g = _seed_graph()
    before = g.stats()
    result = DplRegistryExtractor().extract(registry_root)
    cross_check(result, g, clone_guids={GUID_P1})
    assert g.stats() == before  # read-only, candidates stay flat
    assert g.rels == set()


# -- (g) G135: the accounting can see a WRONG contract, not only a broken one -----------
#
# Every counter above this section is a SKIP counter. These pin the half that
# reports a record which staged FINE and carried almost nothing — the shape a
# wrong field contract actually takes.


@pytest.fixture()
def guid_only_root(tmp_path: Path) -> Path:
    """The regression the original fixtures could not express: records whose
    only contract field is the guid. Every other assumed name is absent."""
    root = tmp_path / "guid-only" / "dpl-registry"
    seal_a = root / SEAL_A
    seal_a.mkdir(parents=True)
    (seal_a / "pipeline_id.json").write_text(
        json.dumps([{"pipelineId": GUID_P1}, {"pipelineId": GUID_P2}]),
        encoding="utf-8",
    )
    return root


def test_a_contract_wrong_on_every_optional_field_is_reported(guid_only_root: Path) -> None:
    result = DplRegistryExtractor().extract(guid_only_root)
    coverage = result.coverage

    # it staged cleanly — that is the point: no skip counter fires
    assert coverage.pipelines_read == 2
    assert (coverage.records_no_guid, coverage.files_invalid) == (0, 0)

    # ...and the census says so anyway, field by field, by name
    lines = coverage.contract_lines()
    for missing in ("version", "active", "ownerSealId", "sealId", "name"):
        assert f"pipeline.{missing}: absent 2/2" in lines
    assert "pipeline.pipelineId: present 2/2" in lines


def test_an_absent_active_flag_is_counted_apart_from_an_unreadable_one(
    guid_only_root: Path, run
) -> None:
    absent = DplRegistryExtractor().extract(guid_only_root).coverage
    assert (absent.active_absent, absent.active_unknown) == (2, 0)
    assert "active_absent=2" in absent.summary()
    # the mixed-spelling fixture is the other case: present but unreadable
    assert (run.coverage.active_absent, run.coverage.active_unknown) == (0, 1)


def test_a_seal_inferred_from_the_path_is_counted_as_inferred(guid_only_root: Path, run) -> None:
    inferred = DplRegistryExtractor().extract(guid_only_root)
    assert inferred.coverage.seal_from_folder == 2
    assert inferred.coverage.records_no_seal == 0  # it HAS one — from the path
    assert {r.seal_origin for r in inferred.records} == {"folder"}
    assert "seal_from_folder=2" in inferred.coverage.summary()
    # a record that carries its own seal is not counted as inferred
    p1 = next(r for r in run.records if r.guid == GUID_P1)
    assert p1.seal_origin == "record"
    assert run.coverage.seal_from_folder == sum(1 for r in run.records if r.seal_origin == "folder")


def test_json_passed_over_for_its_name_is_counted_and_listed(tmp_path: Path) -> None:
    root = tmp_path / "dpl-registry" / SEAL_A
    root.mkdir(parents=True)
    (root / "response_1788150600408.json").write_text("[]", encoding="utf-8")
    (root / "response_1788151602238.json").write_text("[]", encoding="utf-8")
    result = DplRegistryExtractor().extract(root.parent)
    # without this the run reads as an empty directory and complains about nothing
    assert result.coverage.files_read == 0
    assert result.coverage.files_skipped_by_name == 2
    assert result.coverage.skipped_file_names == [
        "response_1788150600408.json",
        "response_1788151602238.json",
    ]
    assert "by_name=2" in result.coverage.summary()


def test_the_census_survives_as_dict(guid_only_root: Path) -> None:
    """Coverage is reported through as_dict(); the census has to travel in it."""
    payload = DplRegistryExtractor().extract(guid_only_root).coverage.as_dict()
    assert payload["fields"]["pipeline"]["version"] == {
        "present": 0,
        "empty": 0,
        "absent": 2,
    }
