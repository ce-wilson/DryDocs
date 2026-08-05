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

from drydocs.loaders.manual_loads import ManualLoadError, mapping_rows, parse_mapping_csv
from drydocs_core import yaml_fragments
from drydocs_core.mapping_store import (
    ONTOLOGY_MAP_PATH,
    MappingStoreError,
    build,
    dump_csv,
    is_current,
    manual_mapping_rows_from_store,
    tables,
)

EXPECTED_TABLES = [
    "app_code_mapping",
    # S4: the write-ahead buffer — the one table not derived from git.
    "draft",
    "manual_load_file",
    "manual_mapping",
    "meta",
    "node_classification",
    "ontology_mapping",
    "relationship_vocabulary",
    "seal_contact_override",
]


# ---------------------------------------------------------------------------
# M0 — build from the real committed sources
# ---------------------------------------------------------------------------


def test_build_materializes_all_tables():
    conn = build(":memory:")
    try:
        assert list(tables(conn)) == EXPECTED_TABLES
        ontology_count = conn.execute("SELECT count(*) FROM ontology_mapping").fetchone()[0]
        yaml_count = len((yaml_fragments.load_yaml_source(ONTOLOGY_MAP_PATH) or {})["mappings"])
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
    # Every DERIVED table is dumped. `draft` is not: it is per-session user
    # state rather than a materialization of committed text, so dumping it
    # would make this very byte-identity assertion impossible to hold.
    assert set(dumps[0]) == {f"{t}.csv" for t in EXPECTED_TABLES if t != "draft"}


def test_meta_records_source_hashes():
    conn = build(":memory:")
    try:
        meta = dict(conn.execute("SELECT key, value FROM meta"))
        assert meta["schema_version"] == "drydocs.mapping-store.v3"  # v3 = the K18 row_kind format
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
    """A tmp repo-root with a registered, loadable manual CSV (the K7-ruled
    folder-grain shape, K8)."""
    loads_dir = tmp_path / "config" / "manual-loads"
    loads_dir.mkdir(parents=True)
    csv_path = loads_dir / "app-codes-to-apps.csv"
    header = (
        "source_label,source_key,relationship,rel_props,target_label,target_key,"
        "create_target_if_missing,note,authored_by,authored_on"
    )
    row = (
        "ControlMFolder,app_code={code},BELONGS_TO_APPLICATION,"
        "role=seal_app_ref,Port,app_id=APP-9876,{create},"
        "{note},steward01,2026-07-18"
    )
    csv_path.write_text(
        "\n".join(
            [
                header,
                row.format(code="ARA", create="false", note="support team confirmed owner"),
                row.format(
                    code="SRV:folder_id=F0002", create="true", note="per-folder platform pin"
                ),
                "",
            ]
        ),
        encoding="utf-8",
    )
    manifest = loads_dir / "manifest.yaml"
    manifest.write_text(
        textwrap.dedent("""\
        schema: drydocs.manual-loads.v1
        status: confirmed
        files:
          - file: config/manual-loads/app-codes-to-apps.csv
            scope: fixture
            status: pending-load
            replaces_with: app-code defined mapping (fixture)
            authored_by: steward01
        """),
        encoding="utf-8",
    )
    return {"csv": csv_path, "manifest": manifest}


def test_store_read_parity_with_legacy_parse(manual_fixture):
    legacy = parse_mapping_csv(manual_fixture["csv"], manifest_path=manual_fixture["manifest"])
    via_store = manual_mapping_rows_from_store(
        manual_fixture["csv"], manifest_path=manual_fixture["manifest"]
    )
    assert [r.model_dump() for r in via_store] == [r.model_dump() for r in legacy]


def test_mapping_rows_default_is_store_and_yaml_fallback_works(manual_fixture, monkeypatch):
    monkeypatch.delenv("DRYDOCS_MAPPING_READ", raising=False)
    default_rows = mapping_rows(manual_fixture["csv"], manifest_path=manual_fixture["manifest"])
    monkeypatch.setenv("DRYDOCS_MAPPING_READ", "yaml")
    yaml_rows = mapping_rows(manual_fixture["csv"], manifest_path=manual_fixture["manifest"])
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
            "SELECT app_code, folder_id, app_id FROM manual_mapping ORDER BY line_no"
        ).fetchall()
        assert rows == [("ARA", None, "APP-9876"), ("SRV", "F0002", "APP-9876")]
        conflicts = conn.execute("SELECT count(*) FROM v_manual_conflicts").fetchone()[0]
        assert conflicts == 0  # each authoring key names one target
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# O24 — SEAL-contact override list (ui-write-surface gate SME-3: the M2
# origin-flagged store). All values below are synthetic (publish boundary).
# ---------------------------------------------------------------------------

OVERRIDE_HEADER = (
    "app_seal_id,role_name,seal_holder_sid,override_holder_sid,"
    "override_holder_name,rationale,authored_by,authored_on,status"
)


def _override_csv(tmp_path: Path, *rows: str) -> Path:
    path = tmp_path / "seal-contact-overrides.csv"
    path.write_text("\n".join([OVERRIDE_HEADER, *rows, ""]), encoding="utf-8")
    return path


def test_override_round_trip_and_origin_flag(tmp_path: Path):
    """The committed list materializes into the table; the grid view emits the
    SEAL source value and the user override as ADJACENT origin-flagged rows
    (source first — never merged, never hidden); the corrections view carries
    only outstanding (active) rows."""
    fix = _override_csv(
        tmp_path,
        # L2 Manager exercises role canonicalization -> 'L2 Operate Manager'
        "APP-1234,L2 Manager,U111111,U222222,Sam Steward,person left the team,kchen2190,2026-07-21,active",
        # no SEAL value captured (nobody assigned) -> only the override row
        "APP-5678,L1 Operate Manager,,U333333,,role unassigned in SEAL,kchen2190,2026-07-21,active",
        # already fixed in SEAL -> kept for audit, out of the report
        "APP-9012,L2 Operate Manager,U444444,U555555,,fixed last sprint,kchen2190,2026-07-01,corrected-in-seal",
    )
    conn = build(":memory:", overrides_path=fix)
    try:
        stored = conn.execute(
            "SELECT app_seal_id, role_name, seal_holder_sid, override_holder_sid, status "
            "FROM seal_contact_override ORDER BY line_no"
        ).fetchall()
        assert stored == [
            ("APP-1234", "L2 Operate Manager", "U111111", "U222222", "active"),
            ("APP-5678", "L1 Operate Manager", None, "U333333", "active"),
            ("APP-9012", "L2 Operate Manager", "U444444", "U555555", "corrected-in-seal"),
        ]
        grid = conn.execute(
            "SELECT app_seal_id, origin, holder_sid FROM v_seal_contact_grid"
        ).fetchall()
        assert grid == [
            ("APP-1234", "source", "U111111"),  # side-by-side pair,
            ("APP-1234", "override", "U222222"),  # source first
            ("APP-5678", "override", "U333333"),  # no captured SEAL value
            ("APP-9012", "source", "U444444"),
            ("APP-9012", "override", "U555555"),
        ]
        report = conn.execute(
            "SELECT app_seal_id, seal_holder_sid, override_holder_sid, rationale "
            "FROM v_source_corrections"
        ).fetchall()
        assert report == [
            ("APP-1234", "U111111", "U222222", "person left the team"),
            ("APP-5678", None, "U333333", "role unassigned in SEAL"),
        ]  # corrected-in-seal is audit-only, not an outstanding correction
    finally:
        conn.close()


@pytest.mark.parametrize(
    "row,reason",
    [
        ("APP-1,Head Chef,U1,U2,,r,kchen2190,2026-07-21,active", "unknown role"),
        ("APP-1,L2 Operate Manager,U1,U2,,,kchen2190,2026-07-21,active", "missing rationale"),
        ("APP-1,L2 Operate Manager,U1,U1,,r,kchen2190,2026-07-21,active", "override == SEAL value"),
        ("APP-1,L2 Operate Manager,U1,U2,,r,kchen2190,2026-07-21,maybe", "bad status"),
        (",L2 Operate Manager,U1,U2,,r,kchen2190,2026-07-21,active", "missing app"),
    ],
)
def test_override_ingestion_fails_closed(tmp_path: Path, row: str, reason: str):
    with pytest.raises(MappingStoreError):
        build(":memory:", overrides_path=_override_csv(tmp_path, row)).close()


def test_override_edit_flips_is_current(manual_fixture, tmp_path: Path):
    """The override list is a tracked source: editing it makes the built file
    stale, so a committed override is always served on the next read (O14)."""
    fix = _override_csv(tmp_path)
    db = tmp_path / "store" / "mapping.db"
    build(db, manifest_path=manual_fixture["manifest"], overrides_path=fix).close()
    assert is_current(db, manifest_path=manual_fixture["manifest"], overrides_path=fix)
    with fix.open("a", encoding="utf-8", newline="") as fh:
        fh.write(
            "APP-1234,L2 Operate Manager,U111111,U222222,,added after build,"
            "kchen2190,2026-07-21,active\n"
        )
    assert not is_current(db, manifest_path=manual_fixture["manifest"], overrides_path=fix)


# ---------------------------------------------------------------------------
# K9 — the K7 defined-mapping store (gate seal-app-ref-edge-reshape §E1/§E2).
# All values synthetic (publish boundary).
# ---------------------------------------------------------------------------

APP_CODE_HEADER_LINE = (
    "app_code,folder_id,row_kind,app_id,declared_end_state,origin,rationale,authored_by,authored_on"
)


def _app_code_csv(tmp_path: Path, *rows: str) -> Path:
    path = tmp_path / "app-code-mappings.csv"
    path.write_text("\n".join([APP_CODE_HEADER_LINE, *rows, ""]), encoding="utf-8")
    return path


def test_app_code_round_trip_grid_and_migration_view(tmp_path: Path):
    """All three row kinds materialize; the grid orders code-level rows before
    their per-folder resolutions with defined/override adjacent (§B3); the
    dual-coded view surfaces every migration with its declared end state
    (§B2 — a stalled migration cannot hide). K18: the platform code-level
    DECLARATION carries the platform's OWN app_id."""
    fix = _app_code_csv(
        tmp_path,
        "PRA,,seal-born,APP-1234,,defined,,kchen2190,2026-08-03",
        "PLT,,platform,APP-9900,,defined,shared SRE-dictated code — resolves per folder,kchen2190,2026-08-03",
        "PLT,F0001,platform,APP-5678,,defined,,kchen2190,2026-08-03",
        "PLT,F0001,platform,APP-9012,,override,team split predates the row,kchen2190,2026-08-03",
        "PRB,,dual-coded,APP-3456,all workload under PRB by the drain,defined,,kchen2190,2026-08-03",
    )
    conn = build(":memory:", app_code_mappings_path=fix)
    try:
        stored = conn.execute(
            "SELECT app_code, folder_id, row_kind, app_id, origin FROM app_code_mapping "
            "ORDER BY line_no"
        ).fetchall()
        assert stored == [
            ("PRA", None, "seal-born", "APP-1234", "defined"),
            ("PLT", None, "platform", "APP-9900", "defined"),
            ("PLT", "F0001", "platform", "APP-5678", "defined"),
            ("PLT", "F0001", "platform", "APP-9012", "override"),
            ("PRB", None, "dual-coded", "APP-3456", "defined"),
        ]
        grid = conn.execute("SELECT app_code, folder_id, origin FROM v_app_code_grid").fetchall()
        assert grid == [
            ("PLT", None, "defined"),  # code-level before per-folder
            ("PLT", "F0001", "defined"),
            ("PLT", "F0001", "override"),  # adjacent, origin-flagged
            ("PRA", None, "defined"),
            ("PRB", None, "defined"),
        ]
        migrations = conn.execute(
            "SELECT app_code, app_id, declared_end_state FROM v_dual_coded_migrations"
        ).fetchall()
        assert migrations == [("PRB", "APP-3456", "all workload under PRB by the drain")]
    finally:
        conn.close()


@pytest.mark.parametrize(
    "row,reason",
    [
        (",,seal-born,APP-1,,defined,,u1,2026-08-03", "missing app_code"),
        ("PRA,,kind-9,APP-1,,defined,,u1,2026-08-03", "unknown row_kind"),
        ("PRA,,seal-born,APP-1,,matched-fallback,,u1,2026-08-03", "fallback never authored"),
        ("PRA,,seal-born,APP-1,,invented,,u1,2026-08-03", "unknown origin"),
        ("PRA,F1,seal-born,APP-1,,defined,,u1,2026-08-03", "seal-born is code-level"),
        ("PRA,,seal-born,,,defined,,u1,2026-08-03", "seal-born needs app_id"),
        # K18: app_id is required on EVERY row — declare-by-absence retired.
        ("PLT,,platform,,,defined,why,u1,2026-08-03", "declaration needs the platform's own app_id"),
        ("PLT,,platform,APP-1,,defined,,u1,2026-08-03", "declaration needs rationale"),
        ("PLT,F1,platform,,,defined,,u1,2026-08-03", "per-folder row needs app_id"),
        ("PRB,,dual-coded,APP-1,,defined,,u1,2026-08-03", "dual-coded needs end state"),
        ("PRA,,seal-born,APP-1,by friday,defined,,u1,2026-08-03", "end state is dual-coded only"),
        ("PRA,,seal-born,APP-1,,override,,u1,2026-08-03", "override needs rationale"),
        ("PRA,,seal-born,APP-1,,defined,,,2026-08-03", "missing authored_by"),
    ],
)
def test_app_code_ingestion_fails_closed(tmp_path: Path, row: str, reason: str):
    with pytest.raises(MappingStoreError):
        build(":memory:", app_code_mappings_path=_app_code_csv(tmp_path, row)).close()


def test_app_code_duplicate_row_is_a_defect(tmp_path: Path):
    """Folder → application is 1:1 (OWNER-NOT-USER): a second authoring row
    for the same (app_code, folder_id, origin) is refused loudly, never
    last-row-wins."""
    fix = _app_code_csv(
        tmp_path,
        "PRA,,seal-born,APP-1,,defined,,u1,2026-08-03",
        "PRA,,seal-born,APP-2,,defined,,u1,2026-08-03",
    )
    with pytest.raises(MappingStoreError, match="1:1"):
        build(":memory:", app_code_mappings_path=fix).close()


def test_app_code_edit_flips_is_current(tmp_path: Path):
    """The defined-mapping list is a tracked source (O14): editing it makes
    the built file stale, so a committed row is always served next read."""
    fix = _app_code_csv(tmp_path)
    db = tmp_path / "store" / "mapping.db"
    build(db, app_code_mappings_path=fix).close()
    assert is_current(db, app_code_mappings_path=fix)
    with fix.open("a", encoding="utf-8", newline="") as fh:
        fh.write("PRA,,seal-born,APP-1234,,defined,,kchen2190,2026-08-03\n")
    assert not is_current(db, app_code_mappings_path=fix)


# ---------------------------------------------------------------------------
# O14 — staleness guard: source-hash drift detection
# ---------------------------------------------------------------------------


def test_is_current_tracks_source_edits(manual_fixture, tmp_path: Path):
    """Editing a committed source makes the built file stale; a rebuild from
    the edited sources makes it current again and serves the edit."""
    db = tmp_path / "store" / "mapping.db"
    build(db, manifest_path=manual_fixture["manifest"]).close()
    assert is_current(db, manifest_path=manual_fixture["manifest"])

    with manual_fixture["csv"].open("a", encoding="utf-8", newline="") as fh:
        fh.write(
            "ControlMFolder,app_code=NEW,BELONGS_TO_APPLICATION,"
            "role=seal_app_ref,Port,app_id=APP-9876,false,"
            "added after build,steward01,2026-07-18\n"
        )
    assert not is_current(db, manifest_path=manual_fixture["manifest"])

    conn = build(db, manifest_path=manual_fixture["manifest"])
    try:
        codes = [r[0] for r in conn.execute("SELECT app_code FROM manual_mapping ORDER BY line_no")]
        assert codes == ["ARA", "SRV", "NEW"]  # the edit is served
    finally:
        conn.close()
    assert is_current(db, manifest_path=manual_fixture["manifest"])


def test_is_current_false_for_missing_or_foreign_file(manual_fixture, tmp_path: Path):
    """Missing and non-store files both answer False — every False means
    'rebuild', never an exception on the read path."""
    assert not is_current(tmp_path / "nope.db", manifest_path=manual_fixture["manifest"])
    foreign = tmp_path / "foreign.db"
    foreign.write_bytes(b"not a sqlite database")
    assert not is_current(foreign, manifest_path=manual_fixture["manifest"])


# ---------------------------------------------------------------------------
# S4 — the draft write-ahead buffer (ADR 0009 rule 5). The one table here that
# is NOT derived from git, and the only reason build() is not purely
# destructive.
# ---------------------------------------------------------------------------


def test_draft_table_is_not_in_the_deterministic_dumps():
    """The CSV dumps are the deterministic view of DERIVED state. Draft rows
    are neither derived nor deterministic (ids are per-session), so including
    them would make byte-identical dumps impossible for identical sources —
    the property test_build_is_deterministic exists to protect."""
    from drydocs_core.mapping_store import _DUMP_ORDER

    assert "draft" not in _DUMP_ORDER


def test_drafts_survive_a_rebuild(tmp_path: Path):
    """A rebuild is ROUTINE — any source edit makes the store stale — so it
    must not discard pending work. Everything else in the file is derived and
    is meant to be thrown away; this table is the deliberate exception."""
    from drydocs_core.mapping_store import add_draft, draft_payloads, open_drafts

    db = tmp_path / "mapping.db"
    conn = build(db)
    try:
        add_draft(
            conn,
            draft_id="kchen2190-aaaa",
            domain="seal-contact-override",
            payloads=[{"app_seal_id": "APP-1"}, {"app_seal_id": "APP-2"}],
            authored_by="kchen2190",
            authored_on="2026-08-04",
        )
    finally:
        conn.close()

    conn = build(db)  # the rebuild that used to be purely destructive
    try:
        assert [d["entries"] for d in open_drafts(conn)] == [2]
        assert [p["app_seal_id"] for p in draft_payloads(conn, "kchen2190-aaaa")] == [
            "APP-1",
            "APP-2",
        ]
    finally:
        conn.close()


def test_two_sessions_drafting_at_once_do_not_collide(tmp_path: Path):
    """The property commit-by-replace could not offer: concurrent editors."""
    from drydocs_core.mapping_store import add_draft, draft_payloads, open_drafts

    conn = build(tmp_path / "mapping.db")
    try:
        add_draft(
            conn,
            draft_id="alice-1111",
            domain="seal-contact-override",
            payloads=[{"app_seal_id": "A"}],
            authored_by="alice",
            authored_on="2026-08-04",
        )
        add_draft(
            conn,
            draft_id="bob-2222",
            domain="seal-contact-override",
            payloads=[{"app_seal_id": "B"}],
            authored_by="bob",
            authored_on="2026-08-04",
        )
        # Appending to one draft leaves the other alone and keeps seq ordering.
        add_draft(
            conn,
            draft_id="alice-1111",
            domain="seal-contact-override",
            payloads=[{"app_seal_id": "C"}],
            authored_by="alice",
            authored_on="2026-08-04",
        )
        assert [p["app_seal_id"] for p in draft_payloads(conn, "alice-1111")] == ["A", "C"]
        assert [p["app_seal_id"] for p in draft_payloads(conn, "bob-2222")] == ["B"]
        assert {d["draft_id"] for d in open_drafts(conn)} == {"alice-1111", "bob-2222"}
    finally:
        conn.close()


def test_promoting_keeps_the_rows_as_the_record(tmp_path: Path):
    """Promotion moves a draft out of `open` but does not DELETE it — the rows
    are what makes a promoted diff traceable back to its editing session."""
    from drydocs_core.mapping_store import add_draft, draft_payloads, open_drafts, set_draft_status

    conn = build(tmp_path / "mapping.db")
    try:
        add_draft(
            conn,
            draft_id="kchen2190-bbbb",
            domain="seal-contact-override",
            payloads=[{"app_seal_id": "APP-1"}],
            authored_by="kchen2190",
            authored_on="2026-08-04",
        )
        assert set_draft_status(conn, "kchen2190-bbbb", "promoted") == 1
        assert open_drafts(conn) == []
        assert draft_payloads(conn, "kchen2190-bbbb") == []  # no longer open
        assert len(draft_payloads(conn, "kchen2190-bbbb", status="promoted")) == 1
        with pytest.raises(MappingStoreError):
            set_draft_status(conn, "kchen2190-bbbb", "nonsense")
    finally:
        conn.close()


def test_carry_over_tolerates_a_pre_s4_database(tmp_path: Path):
    """A database built before the draft table exists must REBUILD, not crash:
    for a derived file every unreadable state means 'rebuild'."""
    import sqlite3

    from drydocs_core.mapping_store import _drafts_to_carry_over

    old = tmp_path / "old.db"
    sqlite3.connect(str(old)).close()  # no draft table at all
    assert _drafts_to_carry_over(old) == []

    foreign = tmp_path / "foreign.db"
    foreign.write_bytes(b"not a sqlite database")
    assert _drafts_to_carry_over(foreign) == []
