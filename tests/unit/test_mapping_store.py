"""Mapping-store guards (plan M0-M4, knowledge/upgrade-plans/mapping-store-plan-2026-07-17.md).

- M0: build is deterministic (byte-identical dumps), tables mirror the sources.
- M1/M3: the SQL read path is row-identical to the legacy CSV parse (parity),
  and the DRYDOCS_MAPPING_READ=yaml fallback still works.
- M4: the analytics views exist and answer.
- The store refuses what the loader refuses (shared validation chain).
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from drydocs.loaders.manual_loads import ManualLoadError, mapping_rows, parse_mapping_csv
from drydocs_core.mapping_store import (
    ONTOLOGY_MAP_PATH,
    build,
    dump_csv,
    manual_mapping_rows_from_store,
    tables,
)

EXPECTED_TABLES = [
    "manual_load_file",
    "manual_mapping",
    "meta",
    "node_classification",
    "ontology_mapping",
    "relationship_vocabulary",
]


# ---------------------------------------------------------------------------
# M0 — build from the real committed sources
# ---------------------------------------------------------------------------

def test_build_materializes_all_tables():
    conn = build(":memory:")
    try:
        assert list(tables(conn)) == EXPECTED_TABLES
        ontology_count = conn.execute("SELECT count(*) FROM ontology_mapping").fetchone()[0]
        yaml_count = len(
            (yaml.safe_load(ONTOLOGY_MAP_PATH.read_text(encoding="utf-8")) or {})["mappings"]
        )
        assert ontology_count == yaml_count  # one row per YAML entry, no drops
        assert conn.execute("SELECT count(*) FROM relationship_vocabulary").fetchone()[0] > 0
        assert conn.execute("SELECT count(*) FROM node_classification").fetchone()[0] > 0
    finally:
        conn.close()


def test_quintuple_row_shape_matches_known_entry():
    """job-contains is the seed applied mapping — its quintuple must survive
    the relationalization intact."""
    conn = build(":memory:")
    try:
        row = conn.execute(
            "SELECT source_label, relationship_type, target_label, prov_maps_to, status "
            "FROM ontology_mapping WHERE id = 'job-contains'"
        ).fetchone()
        assert row == ("ControlMFolder", "CONTAINS_JOB", "ControlMJob", "prov:hadMember", "applied")
    finally:
        conn.close()


def test_build_is_deterministic(tmp_path: Path):
    """Two builds from identical sources dump byte-identical CSVs — the
    gate-reviewable text twin can never drift nondeterministically."""
    dumps = []
    for i in (1, 2):
        conn = build(":memory:")
        try:
            paths = dump_csv(conn, tmp_path / f"dump{i}")
        finally:
            conn.close()
        dumps.append({p.name: p.read_bytes() for p in paths})
    assert dumps[0] == dumps[1]
    assert set(dumps[0]) == {f"{t}.csv" for t in EXPECTED_TABLES}


def test_meta_records_source_hashes():
    conn = build(":memory:")
    try:
        meta = dict(conn.execute("SELECT key, value FROM meta"))
        assert meta["schema_version"] == "drydocs.mapping-store.v1"
        assert "source:taxonomy-ontology-map.yaml" in meta
        assert "source:relationship_vocabulary.yaml" in meta
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# M4 — analytics views
# ---------------------------------------------------------------------------

def test_views_answer():
    conn = build(":memory:")
    try:
        statuses = dict(conn.execute("SELECT status, n FROM v_status_summary"))
        assert statuses  # at least one lifecycle bucket populated
        assert set(statuses) <= {"proposed", "confirmed", "applied", "rejected"}
        active = conn.execute("SELECT count(*) FROM v_vocab_active").fetchone()[0]
        assert active > 0
        labels = [r[0] for r in conn.execute("SELECT label FROM v_label_options")]
        assert "ControlMJob" in labels
        quintuple = conn.execute(
            "SELECT count(*) FROM v_mapping_quintuple WHERE relationship_type IS NOT NULL"
        ).fetchone()[0]
        assert quintuple > 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# M1/M3 — manual-mapping read seam parity (fixture manifest + CSV)
# ---------------------------------------------------------------------------

@pytest.fixture()
def manual_fixture(tmp_path: Path) -> dict[str, Path]:
    """A tmp repo-root with a registered, loadable manual CSV (K2 shape)."""
    loads_dir = tmp_path / "config" / "manual-loads"
    loads_dir.mkdir(parents=True)
    csv_path = loads_dir / "jobs-to-apps.csv"
    header = (
        "source_label,source_key,relationship,rel_props,target_label,target_key,"
        "create_target_if_missing,note,authored_by,authored_on"
    )
    row = (
        "ControlMJob,folder_id=F0001;job_id={job},WAS_ASSOCIATED_WITH,"
        "role=seal_app_ref,BusinessApplication,seal_id=APP-9876,{create},"
        "{note},steward01,2026-07-18"
    )
    csv_path.write_text(
        "\n".join([
            header,
            row.format(job="J0002", create="false", note="support team confirmed owner"),
            row.format(job="J0003", create="true", note="same series as J0002"),
            "",
        ]),
        encoding="utf-8",
    )
    manifest = loads_dir / "manifest.yaml"
    manifest.write_text(textwrap.dedent("""\
        schema: drydocs.manual-loads.v1
        status: confirmed
        files:
          - file: config/manual-loads/jobs-to-apps.csv
            scope: fixture
            status: pending-load
            replaces_with: seal-attribution automation (fixture)
            authored_by: steward01
        """), encoding="utf-8")
    return {"csv": csv_path, "manifest": manifest}


def test_store_read_parity_with_legacy_parse(manual_fixture):
    legacy = parse_mapping_csv(
        manual_fixture["csv"], manifest_path=manual_fixture["manifest"]
    )
    via_store = manual_mapping_rows_from_store(
        manual_fixture["csv"], manifest_path=manual_fixture["manifest"]
    )
    assert [r.model_dump() for r in via_store] == [r.model_dump() for r in legacy]


def test_mapping_rows_default_is_store_and_yaml_fallback_works(
    manual_fixture, monkeypatch
):
    monkeypatch.delenv("DRYDOCS_MAPPING_READ", raising=False)
    default_rows = mapping_rows(
        manual_fixture["csv"], manifest_path=manual_fixture["manifest"]
    )
    monkeypatch.setenv("DRYDOCS_MAPPING_READ", "yaml")
    yaml_rows = mapping_rows(
        manual_fixture["csv"], manifest_path=manual_fixture["manifest"]
    )
    assert [r.model_dump() for r in default_rows] == [r.model_dump() for r in yaml_rows]
    assert len(default_rows) == 2


def test_store_refuses_unregistered_csv(tmp_path: Path):
    """The store inherits the loader's manifest gate — an unregistered CSV
    never materializes."""
    loads_dir = tmp_path / "config" / "manual-loads"
    loads_dir.mkdir(parents=True)
    rogue = loads_dir / "rogue.csv"
    rogue.write_text("source_label\nControlMJob\n", encoding="utf-8")
    manifest = loads_dir / "manifest.yaml"
    manifest.write_text(
        "schema: drydocs.manual-loads.v1\nstatus: confirmed\nfiles: []\n",
        encoding="utf-8",
    )
    with pytest.raises(ManualLoadError):
        manual_mapping_rows_from_store(rogue, manifest_path=manifest)


def test_build_ingests_registered_manual_rows(manual_fixture):
    conn = build(":memory:", manifest_path=manual_fixture["manifest"])
    try:
        rows = conn.execute(
            "SELECT folder_id, job_id, seal_id FROM manual_mapping ORDER BY line_no"
        ).fetchall()
        assert rows == [("F0001", "J0002", "APP-9876"), ("F0001", "J0003", "APP-9876")]
        conflicts = conn.execute("SELECT count(*) FROM v_manual_conflicts").fetchone()[0]
        assert conflicts == 0  # both rows agree on the target
    finally:
        conn.close()
