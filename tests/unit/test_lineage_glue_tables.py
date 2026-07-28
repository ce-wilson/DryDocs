"""G41 — the AWS Glue base-table inventory seam.

SYNTHETIC fixtures throughout (shape-faithful, value-fake; SEALs from the
70001-70099 synthetic block, GUIDs hand-rolled). Every case pins one design
clause: (a) header-variant resolution across the three observed sheets,
(b) GUID identity landing on the SAME dpl_dataset node the MAC seam stages —
including the shared RAW+TRUSTED GUID observation, (c) path-keyed fallback +
path→GUID join, (d) SEAL as a property FACT with cross-checks, (e) zero
relationships — the GUID/SEAL are join keys, edges belong to other seams.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from drydocs_lineage.extractors import (
    GlueInventoryCoverage,
    GlueTableInventoryExtractor,
    parse_database_name,
)
from drydocs_lineage.extractors.dpl_mac import MAC_DATASET_KIND
from drydocs_lineage.extractors.glue_tables import GLUE_TABLE_KIND
from drydocs_lineage.model import DataAssetNode, LineageGraph, asset_id

SEAL = "70011"
GUID_RT = "aaaa0001-dddd-4eee-8fff-000000000010"   # shared RAW+TRUSTED
GUID_RF = "aaaa0002-dddd-4eee-8fff-000000000020"   # REFINED's own GUID
GUID_LEGACY = "aaaa0003-dddd-4eee-8fff-000000000030"  # legacy 1_* family

DB_RAW = "RAW__CCB__SYNTH_AREA__EVENTS_DB"
DB_TRUSTED = "TRUSTED__CCB__SYNTH_AREA__EVENTS_DB"
DB_REFINED = "REFINED__CCB__SYNTH_AREA__EVENTS_DB"


def _write_csv(path: Path, header: list[str], rows: list[list[str]]) -> Path:
    lines = [",".join(header)] + [",".join(r) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


@pytest.fixture()
def guid_sheet(tmp_path: Path) -> Path:
    """Variant 1 — the GUID-bearing inventory (raw sheet headers)."""
    return _write_csv(
        tmp_path / "guid_inventory.csv",
        ["PlatformId", "databaseName", "tableName", "tableDatasetId",
         "tableDatasetIdSource", "databaseFullPath"],
        [
            ["104999", DB_RAW, f"{SEAL}_300000099_EVENTDATA_RAW_TRUSTED",
             GUID_RT, "datasetGuid",
             f"{DB_RAW.lower()}.{SEAL}_300000099_eventdata_raw_trusted"],
            ["104999", DB_TRUSTED, f"{SEAL}_300000099_EVENTDATA_RAW_TRUSTED",
             GUID_RT, "datasetGuid",
             f"{DB_TRUSTED.lower()}.{SEAL}_300000099_eventdata_raw_trusted"],
            ["104999", DB_REFINED, f"{SEAL}_300000099_EVENTDATA_REFINED",
             GUID_RF, "datasetGuid",
             f"{DB_REFINED.lower()}.{SEAL}_300000099_eventdata_refined"],
            # legacy family: bare numeric prefix that is NOT a SEAL, no appId
            ["104999", DB_RAW, "1_TM_SYNTH", GUID_LEGACY, "datasetGuid",
             f"{DB_RAW.lower()}.1_tm_synth"],
        ],
    )


def test_parse_database_name() -> None:
    assert parse_database_name(DB_RAW) == ("raw", "ccb")
    assert parse_database_name("REFINED__CCB__CAMP__SYNTH_DB") == ("refined", "ccb")
    assert parse_database_name("NOT_A_ZONE_DB") == ("", "")


# -- (b) GUID identity: one dataset, per-zone placements -------------------------

def test_shared_raw_trusted_guid_is_one_node_two_placements(guid_sheet) -> None:
    g = LineageGraph()
    cov = GlueTableInventoryExtractor().extract(guid_sheet, g)
    assert cov.files_read == 1 and cov.rows_read == 4
    assert cov.guid_rows == 4 and cov.path_rows == 0

    node = g.data_assets[asset_id(MAC_DATASET_KIND, GUID_RT)]
    assert node.kind == MAC_DATASET_KIND
    assert node.properties["glue_database_raw"] == DB_RAW
    assert node.properties["glue_database_trusted"] == DB_TRUSTED
    assert node.properties["glue_table_raw"].endswith("_RAW_TRUSTED")
    assert node.properties["lob"] == "ccb"
    assert node.properties["platform_id"] == "104999"
    # REFINED is its OWN dataset GUID — never merged into the RAW/TRUSTED node
    refined = g.data_assets[asset_id(MAC_DATASET_KIND, GUID_RF)]
    assert refined.properties["glue_database_refined"] == DB_REFINED
    assert "glue_database_refined" not in node.properties
    assert cov.placements_added == 4
    assert cov.datasets_created == 3      # RT + RF + legacy
    assert cov.datasets_enriched == 1     # the TRUSTED row landed on RT's node


def test_enriches_a_mac_staged_dataset_instead_of_duplicating(guid_sheet) -> None:
    g = LineageGraph()
    g.add_data_asset(DataAssetNode(
        node_id=asset_id(MAC_DATASET_KIND, GUID_RT), kind=MAC_DATASET_KIND,
        location=GUID_RT, properties={"zone": "RAW", "dataset_name": "eventdata"},
    ))
    cov = GlueTableInventoryExtractor().extract(guid_sheet, g)
    node = g.data_assets[asset_id(MAC_DATASET_KIND, GUID_RT)]
    # MAC facts survive; glue placements land beside them; no glue_only marker
    assert node.properties["dataset_name"] == "eventdata"
    assert node.properties["glue_database_raw"] == DB_RAW
    assert "glue_only" not in node.properties
    assert cov.datasets_created == 2 and cov.datasets_enriched == 2


def test_zero_relationships_are_created(guid_sheet) -> None:
    g = LineageGraph()
    GlueTableInventoryExtractor().extract(guid_sheet, g)
    assert g.rels == set()


def test_idempotent_rerun_counts_duplicates(guid_sheet) -> None:
    g = LineageGraph()
    ext = GlueTableInventoryExtractor()
    ext.extract(guid_sheet, g)
    before = {nid: dict(n.properties) for nid, n in g.data_assets.items()}
    cov2 = ext.extract(guid_sheet, g)
    after = {nid: dict(n.properties) for nid, n in g.data_assets.items()}
    assert before == after
    assert cov2.duplicate_rows == 4 and cov2.placements_added == 0


# -- (c) path-keyed fallback + path→GUID join -------------------------------------

@pytest.fixture()
def consumption_sheet(tmp_path: Path) -> Path:
    """Variant 2 — the consumption inventory: NO GUID column; 'database' is
    the PLATFORM and 'databaseName' the DB; fullPath is UPPERCASE."""
    return _write_csv(
        tmp_path / "consumption.csv",
        ["database", "databasePlatformId", "databaseName", "tableName",
         "databaseFullPath"],
        [
            ["AWS-S3", "104999", DB_REFINED, "ACCT_SYNTH",
             f"{DB_REFINED}.ACCT_SYNTH"],
            # overlaps the GUID sheet's refined placement — must JOIN, not fork
            ["AWS-S3", "104999", DB_REFINED,
             f"{SEAL}_300000099_EVENTDATA_REFINED",
             f"{DB_REFINED}.{SEAL}_300000099_EVENTDATA_REFINED"],
        ],
    )


def test_path_rows_stage_glue_tables_and_join_guid_placements(
    guid_sheet, consumption_sheet, tmp_path
) -> None:
    g = LineageGraph()
    ext = GlueTableInventoryExtractor()
    # a directory of sheets is one run: GUID rows pass 1, path rows pass 2
    cov = ext.extract(tmp_path, g)
    assert cov.guid_rows == 4 and cov.path_rows == 2
    # the overlapping row joined the GUID node (case-insensitive path match)
    assert cov.path_joined_guid == 1
    assert cov.glue_created == 1
    standalone = g.data_assets[
        asset_id(GLUE_TABLE_KIND, f"{DB_REFINED.lower()}.acct_synth")
    ]
    assert standalone.kind == GLUE_TABLE_KIND
    assert standalone.properties["glue_database_refined"] == DB_REFINED
    assert standalone.properties["platform"] == "AWS-S3"


def test_unknown_zone_is_counted_never_guessed(tmp_path) -> None:
    sheet = _write_csv(
        tmp_path / "odd.csv",
        ["databaseName", "tableName"],
        [["SOME_FLAT_DB", "T1"]],
    )
    g = LineageGraph()
    cov = GlueTableInventoryExtractor().extract(sheet, g)
    assert cov.zone_unknown == 1
    node = g.data_assets[asset_id(GLUE_TABLE_KIND, "some_flat_db.t1")]
    assert node.properties["glue_database_unzoned"] == "SOME_FLAT_DB"


# -- (a)+(d) normalized load sheet: appId, id-source routing ---------------------

@pytest.fixture()
def load_sheet(tmp_path: Path) -> Path:
    """Variant 3 — the normalized merge, annotated fullPath header included."""
    return _write_csv(
        tmp_path / "load.csv",
        ["databasePlatform", "databasePlatformId", "database", "schema",
         "table", "tableType", "appId", "tableDatasetId",
         "tableDatasetIdSource", "fullPath *formula except for AWS"],
        [
            ["AWS-S3", "104999", DB_RAW.lower(), "",
             f"{SEAL}_300000099_eventdata_raw_trusted", "", SEAL, GUID_RT,
             "datasetGuid",
             f"{DB_RAW.lower()}.{SEAL}_300000099_eventdata_raw_trusted"],
            # id source names ANOTHER scheme -> routed to path identity
            ["AWS-S3", "104999", DB_RAW.lower(), "", "other_keyed_table", "",
             "", "XK-000123", "vendorKey",
             f"{DB_RAW.lower()}.other_keyed_table"],
            # appId disagrees with the table-name numeric prefix
            ["AWS-S3", "104999", DB_RAW.lower(), "", "70022_synth_table", "",
             SEAL, GUID_LEGACY, "datasetGuid",
             f"{DB_RAW.lower()}.70022_synth_table"],
        ],
    )


def test_load_sheet_headers_seal_facts_and_idsource_routing(load_sheet) -> None:
    g = LineageGraph()
    cov = GlueTableInventoryExtractor().extract(load_sheet, g)
    assert cov.guid_rows == 2
    assert cov.idsource_not_guid == 1 and cov.path_rows == 1
    # the vendor-keyed row landed as a path-keyed glue_table, never GUID space
    assert asset_id(GLUE_TABLE_KIND, f"{DB_RAW.lower()}.other_keyed_table") \
        in g.data_assets
    node = g.data_assets[asset_id(MAC_DATASET_KIND, GUID_RT)]
    assert node.properties["seal"] == SEAL
    assert cov.seal_facts == 2
    # 70022_* prefix vs appId 70011: cross-check fires, column still wins
    assert cov.name_seal_disagreements == 1
    legacy = g.data_assets[asset_id(MAC_DATASET_KIND, GUID_LEGACY)]
    assert legacy.properties["seal"] == SEAL


def test_placement_conflict_first_wins(tmp_path) -> None:
    sheet = _write_csv(
        tmp_path / "conflict.csv",
        ["databaseName", "tableName", "tableDatasetId", "tableDatasetIdSource"],
        [
            [DB_RAW, "TABLE_A", GUID_RT, "datasetGuid"],
            [DB_RAW, "TABLE_B", GUID_RT, "datasetGuid"],  # same GUID+zone, new path
        ],
    )
    g = LineageGraph()
    cov = GlueTableInventoryExtractor().extract(sheet, g)
    node = g.data_assets[asset_id(MAC_DATASET_KIND, GUID_RT)]
    assert node.properties["glue_table_raw"] == "TABLE_A"
    assert cov.placement_conflicts == 1


def test_invalid_rows_and_files_are_counted(tmp_path) -> None:
    _write_csv(tmp_path / "bad_headers.csv", ["foo", "bar"], [["1", "2"]])
    _write_csv(
        tmp_path / "gaps.csv",
        ["databaseName", "tableName"],
        [[DB_RAW, ""], ["", "T2"], [DB_RAW, "OK_TABLE"]],
    )
    g = LineageGraph()
    cov = GlueTableInventoryExtractor().extract(tmp_path, g)
    assert cov.files_invalid == 1 and cov.files_read == 1
    assert cov.rows_invalid == 2
    assert len(g.data_assets) == 1
    assert isinstance(cov.summary(), str) and "invalid_rows=2" in cov.summary()
    assert cov.as_dict()["rows_invalid"] == 2


def test_coverage_dataclass_defaults() -> None:
    cov = GlueInventoryCoverage()
    assert cov.rows_read == 0 and cov.placements_added == 0
