"""G42 — the Snowflake data-catalog ingestion seam (dataset/distribution views).

SYNTHETIC fixtures throughout (shape-faithful, value-fake; the column names
ARE the assumed contract documented in ``snowflake_catalog.py`` — a real
sample validates or amends them; real exports are confidential (Internal, J23) and
live in the catalog/ landing zone, never here — app ids come from the
synthetic 70001-70099 block). Each case pins one acceptance clause:
(a) taxonomy-first staging records with provenance, (b) origin routing
dpl | authority2 | catalog — never joining foreign ids into DPL GUID space,
(c) union duplicates latest-per-GUID with dupes counted (both observed
timestamp formats), (d) the three physical shapes discriminated + the
candidate URN as a fact column, (e) the NOT INSTRUMENTED sentinel nulled AND
counted, (f) unresolved/ambiguous shapes counted never guessed, (g) every
skip counted by reason, (h) ZERO graph writes — the API is graph-free.
"""
from __future__ import annotations

import csv
import dataclasses
import inspect
from pathlib import Path

import pytest

from drydocs_lineage.extractors import SnowflakeCatalogExtractor

APP_ID = "70001"                                       # synthetic SEAL block
DS_DPL = "aaaa0001-1111-4222-8333-000000000001"        # DPL-registered (3 union rows)
DS_AUTH2 = "aaaa0002-1111-4222-8333-000000000002"      # second-authority row
DS_NULL = "aaaa0003-1111-4222-8333-000000000003"       # legacy/manual registration
DPL_REF = "bbbb0001-1111-4222-8333-000000000099"       # the upstream DPL dataset GUID

_DS_HEADER = [
    "DATASET_NAME", "DATASET_BUSINESSNAME", "DATASET_IDENTIFIER",
    "BUSINESS_DESCRIPTION_TEXT", "PUBLISHER_COMPANY_NAME",
    "PRODUCEDBY_APPLICATION_IDENTIFIER", "EMAIL_ADDRESS_TEXT",
    "REGISTRATION_SOURCE_SYSTEMNAME",
    "REGISTRATION_SOURCE_SYSTEMDATAASSET_IDENTIFIER", "TIMESTAMP",
]

_DIST_HEADER = [
    "DATASET_IDENTIFIER", "DISTRIBUTION_IDENTIFIER", "DISTRIBUTION_NAME",
    "CONSUMABLE_INDICATOR", "PUBLICATIONMODE_TEXT",
    "REGISTRATION_SOURCE_SYSTEMNAME",
    "REGISTRATION_SOURCE_SYSTEMDATAASSET_IDENTIFIER",
    "REGISTRATION_SOURCE_PARENTDATAASSET_IDENTIFIER",
    "TABLE_DESCRIPTION_TEXT", "TIMESTAMP",
    "TABLE_NAME", "TABLETYPE_TEXT", "LOGICALDATABASE_NAME", "DATABASE_NAME",
    "DATABASE_STORAGE_RESOURCE_URI_TEXT", "DATATECHNOLOGY_NAME",
    "DATABASESCHEMA_NAME",
    "FILE_NAME", "FILE_SYSTEM_NAME", "FILE_STORAGE_RESOURCE_URI_TEXT",
    "FILE_SYSTEMTYPE_TEXT", "DIRECTORY_NAME",
    "S3BUCKET_NAME", "STORAGE_RESOURCE_URI_TEXT", "S3DATAASSET_NAME",
]


def _write_csv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def _dist(dist_guid: str, **cells: str) -> dict[str, str]:
    row = {h: "" for h in _DIST_HEADER}
    row.update({
        "DATASET_IDENTIFIER": DS_DPL,
        "DISTRIBUTION_IDENTIFIER": dist_guid,
        "CONSUMABLE_INDICATOR": "Y",
        "PUBLICATIONMODE_TEXT": "SNAPSHOT",
        "TIMESTAMP": "2026-07-05 12:00:00",
    })
    row.update(cells)
    return row


@pytest.fixture()
def catalog_root(tmp_path: Path) -> Path:
    root = tmp_path / "catalog"
    root.mkdir()
    _write_csv(root / "catalog_datasets_v.csv", _DS_HEADER, [
        # the union-dupe trio: ISO (oldest) -> unparseable -> DD-MON (latest)
        {"DATASET_NAME": "ACCOUNTS_CONFORMED", "DATASET_IDENTIFIER": DS_DPL,
         "BUSINESS_DESCRIPTION_TEXT": "rev-old",
         "PRODUCEDBY_APPLICATION_IDENTIFIER": APP_ID,
         "EMAIL_ADDRESS_TEXT": "dl-accounts@synthetic.example",
         "REGISTRATION_SOURCE_SYSTEMNAME": "DPL",
         "REGISTRATION_SOURCE_SYSTEMDATAASSET_IDENTIFIER": DPL_REF,
         "TIMESTAMP": "2026-07-01 10:00:00"},
        {"DATASET_NAME": "ACCOUNTS_CONFORMED", "DATASET_IDENTIFIER": DS_DPL,
         "BUSINESS_DESCRIPTION_TEXT": "rev-unparseable",
         "REGISTRATION_SOURCE_SYSTEMNAME": "DPL",
         "REGISTRATION_SOURCE_SYSTEMDATAASSET_IDENTIFIER": DPL_REF,
         "TIMESTAMP": "sometime last week"},
        {"DATASET_NAME": "ACCOUNTS_CONFORMED", "DATASET_IDENTIFIER": DS_DPL,
         "BUSINESS_DESCRIPTION_TEXT": "rev-latest",
         "PRODUCEDBY_APPLICATION_IDENTIFIER": APP_ID,
         "EMAIL_ADDRESS_TEXT": "dl-accounts@synthetic.example",
         "REGISTRATION_SOURCE_SYSTEMNAME": "DPL",
         "REGISTRATION_SOURCE_SYSTEMDATAASSET_IDENTIFIER": DPL_REF,
         "TIMESTAMP": "15-Jul-2026 10:00:00"},
        # second authority (generic name — the real one stays company-side)
        {"DATASET_NAME": "LEDGER_WAREHOUSE", "DATASET_BUSINESSNAME": "Ledger",
         "DATASET_IDENTIFIER": DS_AUTH2,
         "PUBLISHER_COMPANY_NAME": "Synthetic Product Line",
         "REGISTRATION_SOURCE_SYSTEMNAME": "WAREHOUSE_REG",
         "REGISTRATION_SOURCE_SYSTEMDATAASSET_IDENTIFIER": "TD-000123",
         "TIMESTAMP": "2026-07-02 08:00:00"},
        # null-source legacy registration -> keys on its own catalog GUID
        {"DATASET_NAME": "MANUAL_LEGACY", "DATASET_IDENTIFIER": DS_NULL,
         "TIMESTAMP": "2026-07-03 08:00:00"},
        # identity column missing -> skipped, counted
        {"DATASET_NAME": "GHOST_ROW", "TIMESTAMP": "2026-07-04 08:00:00"},
    ])
    _write_csv(root / "catalog_distributions_v.csv", _DIST_HEADER, [
        # (1) table shape — Snowflake, db + schema
        _dist("dddd0001-0000-4000-8000-000000000001",
              TABLE_NAME="ACCOUNTS_CONFORMED", TABLETYPE_TEXT="TABLE",
              LOGICALDATABASE_NAME="ANALYTICS_DB", DATABASESCHEMA_NAME="CONF",
              DATATECHNOLOGY_NAME="SNOWFLAKE",
              DATABASE_STORAGE_RESOURCE_URI_TEXT="jdbc:snowflake://synthetic.example"),
        # (2) table shape — Glue external table, NO schema: G41 db.table join
        _dist("dddd0002-0000-4000-8000-000000000002",
              TABLE_NAME=f"{APP_ID}_300000011_ACCOUNTS_RAW_TRUSTED",
              TABLETYPE_TEXT="EXTERNAL_TABLE",
              LOGICALDATABASE_NAME="TRUSTED__RLOB__ACCOUNTS",
              DATATECHNOLOGY_NAME="GLUE"),
        # (3) file shape — HDFS, with the sentinel in FILE_SYSTEM_NAME
        _dist("dddd0003-0000-4000-8000-000000000003",
              FILE_NAME="part-0000.parquet", FILE_SYSTEM_NAME="NOT INSTRUMENTED",
              FILE_SYSTEMTYPE_TEXT="HDFS", DIRECTORY_NAME="/data/refined/accounts",
              FILE_STORAGE_RESOURCE_URI_TEXT="hdfs://synthetic/data/refined/accounts"),
        # (4) s3 shape
        _dist("dddd0004-0000-4000-8000-000000000004",
              S3BUCKET_NAME=f"app-{APP_ID}-dep-0001-refined",
              S3DATAASSET_NAME="ACCOUNTS_REFINED",
              STORAGE_RESOURCE_URI_TEXT=f"s3a://app-{APP_ID}-dep-0001-refined/accounts"),
        # (5) no shape populated at all — plus a sentinel in a column the
        #     shape branch never reads (must still be counted)
        _dist("dddd0005-0000-4000-8000-000000000005",
              LOGICALDATABASE_NAME="NOT INSTRUMENTED"),
        # (6) contract violation: two shapes populated — counted, never guessed
        _dist("dddd0006-0000-4000-8000-000000000006",
              TABLE_NAME="AMBIGUOUS_T", LOGICALDATABASE_NAME="X_DB",
              DATATECHNOLOGY_NAME="SNOWFLAKE",
              FILE_NAME="ambiguous.dat", DIRECTORY_NAME="/tmp/x",
              FILE_SYSTEMTYPE_TEXT="HDFS"),
        # (7a/7b) union dupe — same distribution GUID, latest wins
        _dist("dddd0007-0000-4000-8000-000000000007",
              TABLE_NAME="DUPED_T", LOGICALDATABASE_NAME="D_DB",
              DATABASESCHEMA_NAME="S1", DATATECHNOLOGY_NAME="TERADATA",
              TABLE_DESCRIPTION_TEXT="rev-old", TIMESTAMP="2026-07-01 09:00:00"),
        _dist("dddd0007-0000-4000-8000-000000000007",
              TABLE_NAME="DUPED_T", LOGICALDATABASE_NAME="D_DB",
              DATABASESCHEMA_NAME="S1", DATATECHNOLOGY_NAME="TERADATA",
              TABLE_DESCRIPTION_TEXT="rev-latest", TIMESTAMP="2026-07-10 09:00:00"),
        # (8) parent dataset GUID missing — staged, counted
        _dist("dddd0008-0000-4000-8000-000000000008",
              DATASET_IDENTIFIER="",
              TABLE_NAME="ORPHAN_T", LOGICALDATABASE_NAME="O_DB",
              DATABASESCHEMA_NAME="S2", DATATECHNOLOGY_NAME="SNOWFLAKE"),
    ])
    return root


@pytest.fixture()
def run(catalog_root: Path):
    return SnowflakeCatalogExtractor().extract(catalog_root)


# -- (a) taxonomy-first staging records with provenance -------------------------------

def test_dataset_records_flat_with_provenance(run) -> None:
    by_guid = {r.guid: r for r in run.datasets}
    auth2 = by_guid[DS_AUTH2]
    assert auth2.name == "LEDGER_WAREHOUSE"
    assert auth2.business_name == "Ledger"
    assert auth2.publisher == "Synthetic Product Line"
    assert auth2.source_file.endswith("catalog_datasets_v.csv")   # provenance
    dpl = by_guid[DS_DPL]
    assert dpl.producedby_app_id == APP_ID          # the SEAL-shaped bridge FACT
    assert dpl.contact_email == "dl-accounts@synthetic.example"
    assert run.coverage.files_read == 2
    assert run.coverage.datasets_staged == 3


# -- (b) origin routing: dpl | authority2 | catalog ------------------------------------

def test_origin_routing_and_census(run) -> None:
    by_guid = {r.guid: r for r in run.datasets}
    assert by_guid[DS_DPL].origin == "dpl"
    assert by_guid[DS_DPL].registration_source_ref == DPL_REF   # the GUID-space join key
    assert by_guid[DS_AUTH2].origin == "authority2"             # foreign ids NEVER join DPL space
    assert by_guid[DS_AUTH2].registration_source == "WAREHOUSE_REG"  # verbatim, for the census
    assert by_guid[DS_NULL].origin == "catalog"                 # keys on its own GUID
    cov = run.coverage
    assert (cov.origin_dpl, cov.origin_authority2, cov.origin_catalog) == (1, 1, 1)
    assert run.dpl_refs() == {DPL_REF}


# -- (c) union duplicates: latest-per-GUID, dupes counted, both ts formats -------------

def test_union_duplicates_latest_per_guid(run) -> None:
    dpl = next(r for r in run.datasets if r.guid == DS_DPL)
    assert dpl.description == "rev-latest"          # the DD-MON row beat the ISO row
    assert dpl.timestamp == "15-Jul-2026 10:00:00"
    assert run.coverage.duplicate_datasets == 2
    assert run.coverage.timestamp_unparsed == 1     # "sometime last week" lost the tie
    assert "datasets=2" in run.coverage.summary()


def test_duplicate_distribution_latest_wins(run) -> None:
    duped = next(r for r in run.distributions
                 if r.distribution_guid.startswith("dddd0007"))
    assert duped.description == "rev-latest"
    assert run.coverage.duplicate_distributions == 1
    assert run.coverage.distributions_staged == 8


# -- (d) the three physical shapes + the candidate URN as a FACT column ----------------

def test_three_shapes_discriminated_with_urns(run) -> None:
    by_guid = {r.distribution_guid: r for r in run.distributions}
    table = by_guid["dddd0001-0000-4000-8000-000000000001"]
    assert (table.shape, table.platform) == ("table", "snowflake")
    assert table.namespace == "analytics_db.conf"
    assert table.candidate_asset_urn == (
        "urn:drydocs:dataasset:snowflake:analytics_db.conf:accounts_conformed")
    file_rec = by_guid["dddd0003-0000-4000-8000-000000000003"]
    assert (file_rec.shape, file_rec.platform) == ("file", "hdfs")
    assert file_rec.candidate_asset_urn == (
        "urn:drydocs:dataasset:hdfs:/data/refined/accounts:part-0000.parquet")
    s3 = by_guid["dddd0004-0000-4000-8000-000000000004"]
    assert (s3.shape, s3.platform) == ("s3", "s3")
    assert s3.candidate_asset_urn == (
        f"urn:drydocs:dataasset:s3:app-{APP_ID}-dep-0001-refined:accounts_refined")
    assert s3.consumable == "Y" and s3.publication_mode == "SNAPSHOT"


def test_glue_shaped_row_reuses_the_g41_canonical_namespace(run) -> None:
    """No schema -> namespace is the bare db, so the URN tail equals G41's
    canonical lowercase db.table join path (G43's join)."""
    glue = next(r for r in run.distributions
                if r.distribution_guid.startswith("dddd0002"))
    assert glue.namespace == "trusted__rlob__accounts"
    assert glue.candidate_asset_urn.endswith(
        f":trusted__rlob__accounts:{APP_ID}_300000011_accounts_raw_trusted")


# -- (e) the NOT INSTRUMENTED sentinel: nulled AND counted ------------------------------

def test_sentinel_nulled_and_counted(run) -> None:
    assert run.coverage.sentinel_not_instrumented == 2   # rows 3 and 5
    for rec in run.datasets + run.distributions:
        for value in dataclasses.asdict(rec).values():
            assert value != "NOT INSTRUMENTED"


# -- (f) unresolved / ambiguous shapes: counted, never guessed --------------------------

def test_shapeless_and_ambiguous_rows_counted(run) -> None:
    by_guid = {r.distribution_guid: r for r in run.distributions}
    empty = by_guid["dddd0005-0000-4000-8000-000000000005"]
    ambiguous = by_guid["dddd0006-0000-4000-8000-000000000006"]
    assert empty.shape == "" and empty.candidate_asset_urn == ""
    assert ambiguous.shape == "" and ambiguous.candidate_asset_urn == ""
    cov = run.coverage
    assert cov.shape_unresolved == 1
    assert cov.shape_ambiguous == 1
    assert cov.urn_underived == 2


# -- (g) every skip counted by reason ----------------------------------------------------

def test_no_guid_and_no_parent_counted(run) -> None:
    assert run.coverage.rows_no_guid == 1               # the GHOST_ROW dataset
    assert run.coverage.distributions_no_dataset == 1   # the ORPHAN_T distribution
    orphan = next(r for r in run.distributions
                  if r.distribution_guid.startswith("dddd0008"))
    assert orphan.dataset_guid == ""                    # staged anyway, counted


def test_invalid_files_counted(tmp_path: Path) -> None:
    root = tmp_path / "catalog"
    root.mkdir()
    (root / "not_a_view.csv").write_text("SOME,OTHER,HEADER\n1,2,3\n",
                                         encoding="utf-8")
    (root / "empty.csv").write_text("", encoding="utf-8")
    result = SnowflakeCatalogExtractor().extract(root)
    assert result.coverage.files_invalid == 2
    assert result.coverage.files_read == 0
    assert result.datasets == [] and result.distributions == []


# -- (h) ZERO graph writes: the API is graph-free ----------------------------------------

def test_staging_is_graph_free(run) -> None:
    """No LineageGraph parameter exists anywhere in the extractor API —
    staging cannot write what it never receives; the gate is the terminus."""
    params = inspect.signature(SnowflakeCatalogExtractor.extract).parameters
    assert set(params) == {"self", "source"}
    with pytest.raises(dataclasses.FrozenInstanceError):
        run.datasets[0].guid = "mutated"                # records are frozen facts
