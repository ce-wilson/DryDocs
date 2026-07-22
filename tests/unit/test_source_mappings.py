"""Unit tests for the source column ledger (drydocs/source_mappings.py) — pure, no Neo4j.

Covers the accessor's own validation (schema id, classification, disposition/origin
enums, excluded-must-carry-reason) plus the committed `controlm-psgmgr.yaml` ledger
(doc 08 Phase 0): every profiled column of the five psgmgr CM_ objects gets exactly
one disposition, traced to the SQL projections / controlm-q1q3-phase1 gate /
config/audit-fields.yaml — never invented.
"""
from __future__ import annotations

import pytest

from drydocs.source_mappings import (
    SourceMapping,
    SourceMappingError,
    UnknownMappingObjectError,
)

_DOC = {
    "schema": "drydocs.source-mapping.v1",
    "source": "test-source",
    "classification": "Internal-Public",
    "objects": [
        {
            "name": "SWEPT_OBJ",
            "kind": "table",
            "profile": {"profiled_on": None, "via": "unit test", "column_count": None, "census": "pending"},
            "columns": [
                {"name": "A", "disposition": "projected", "origin": "source", "target": "Thing.a"},
                {"name": "B", "disposition": "excluded", "reason": "scope", "note": "not needed"},
            ],
            "default_disposition": {"disposition": "excluded", "reason": "scope", "note": "sweep"},
        },
        {
            "name": "UNSWEPT_OBJ",
            "kind": "view",
            "columns": [
                {"name": "X", "disposition": "projected", "origin": "source", "target": "Thing.x"},
                {"name": "Y", "disposition": "filter-only", "note": "WHERE clause only"},
            ],
        },
    ],
}


# ---------------------------------------------------------------------------
# Accessor behavior (synthetic fixture)
# ---------------------------------------------------------------------------


def test_from_dict_parses_objects() -> None:
    sm = SourceMapping.from_dict(_DOC)
    assert sm.objects() == ["SWEPT_OBJ", "UNSWEPT_OBJ"]
    assert sm.source == "test-source"
    assert sm.classification == "Internal-Public"


def test_projected_is_ordered_and_filtered() -> None:
    sm = SourceMapping.from_dict(_DOC)
    assert sm.projected("SWEPT_OBJ") == ["A"]
    assert sm.projected("UNSWEPT_OBJ") == ["X"]


def test_unaccounted_with_default_sweep_is_empty() -> None:
    """A declared default_disposition sweeps the long tail — nothing is unaccounted,
    even for a wholly-unknown profiled column."""
    sm = SourceMapping.from_dict(_DOC)
    assert sm.unaccounted("SWEPT_OBJ", ["A", "B", "Z_NEVER_MENTIONED"]) == []


def test_unaccounted_without_default_sweep_reports_gaps() -> None:
    """No default_disposition on UNSWEPT_OBJ — a profiled column absent from the
    explicit list is genuinely unaccounted."""
    sm = SourceMapping.from_dict(_DOC)
    assert sm.unaccounted("UNSWEPT_OBJ", ["X", "Y"]) == []
    assert sm.unaccounted("UNSWEPT_OBJ", ["X", "Y", "Z_NEVER_MENTIONED"]) == ["Z_NEVER_MENTIONED"]


def test_unknown_object_raises() -> None:
    sm = SourceMapping.from_dict(_DOC)
    assert "SWEPT_OBJ" in sm
    assert "NOPE" not in sm
    with pytest.raises(UnknownMappingObjectError):
        sm.projected("NOPE")


def test_to_records_is_flat_dataframe_ready_view() -> None:
    sm = SourceMapping.from_dict(_DOC)
    records = sm.to_records()
    assert len(records) == 4  # A, B, X, Y
    assert all(r["source"] == "test-source" for r in records)
    first = records[0]
    assert set(first) == {
        "source", "object", "column", "disposition", "origin",
        "target", "reason", "decided_by", "note",
    }


@pytest.mark.parametrize(
    "bad,match",
    [
        ({**_DOC, "schema": "wrong.schema"}, "schema"),
        ({**_DOC, "source": ""}, "source"),
        ({**_DOC, "classification": ""}, "classification"),
        ({**_DOC, "objects": []}, "objects"),
        (
            {
                **_DOC,
                "objects": [
                    {"name": "DUP", "columns": [{"name": "A", "disposition": "projected"}]},
                    {"name": "DUP", "columns": [{"name": "A", "disposition": "projected"}]},
                ],
            },
            "duplicate object",
        ),
        (
            {
                **_DOC,
                "objects": [
                    {
                        "name": "O",
                        "columns": [
                            {"name": "A", "disposition": "projected"},
                            {"name": "A", "disposition": "excluded", "reason": "scope"},
                        ],
                    }
                ],
            },
            "duplicate column",
        ),
        (
            {
                **_DOC,
                "objects": [{"name": "O", "columns": [{"name": "A", "disposition": "not-a-real-value"}]}],
            },
            "invalid disposition",
        ),
        (
            {
                **_DOC,
                "objects": [
                    {"name": "O", "columns": [{"name": "A", "disposition": "projected", "origin": "made-up"}]}
                ],
            },
            "invalid origin",
        ),
        (
            {
                **_DOC,
                "objects": [{"name": "O", "columns": [{"name": "A", "disposition": "excluded"}]}],
            },
            "must carry a `reason:`",
        ),
        (
            {
                **_DOC,
                "objects": [
                    {"name": "O", "columns": [{"name": "A", "disposition": "excluded", "reason": "made-up"}]}
                ],
            },
            "invalid reason",
        ),
        (
            {
                **_DOC,
                "objects": [
                    {
                        "name": "O",
                        "columns": [{"name": "A", "disposition": "projected"}],
                        "default_disposition": {"disposition": "excluded"},
                    }
                ],
            },
            "default_disposition excluded must carry a `reason:`",
        ),
    ],
)
def test_malformed_docs_raise(bad: dict, match: str) -> None:
    with pytest.raises(SourceMappingError, match=match):
        SourceMapping.from_dict(bad)


# ---------------------------------------------------------------------------
# The committed controlm-psgmgr.yaml ledger (doc 08 Phase 0)
# ---------------------------------------------------------------------------

_EXPECTED_OBJECTS = [
    "CM_DEF_VTAB",
    "CM_DEF_VJOB",
    "CM_DEF_LNKI_P_VW",
    "CM_DEF_LNKO_P_VW",
    "CM_DEF_SETVAR_VW",
    "CM_HOSTS",
    "CM_AVG_RUN",
]


@pytest.fixture(scope="module")
def controlm() -> SourceMapping:
    return SourceMapping.load_source("controlm-psgmgr")


def test_committed_ledger_loads(controlm: SourceMapping) -> None:
    assert controlm.source == "controlm-psgmgr"
    assert controlm.classification == "Internal-Public"
    assert controlm.schema == "drydocs.source-mapping.v1"
    assert controlm.objects() == _EXPECTED_OBJECTS


def test_every_object_has_a_profile_and_default_sweep(controlm: SourceMapping) -> None:
    """Every object carries a profile and sweeps its long tail. The census is
    either the Phase-0 `pending` placeholder (no count recorded) or `complete`
    with a real column_count — the first completed census landed 2026-07-22
    (CM_AVG_RUN P0 probe); count reconciliation is census_failures()' job."""
    censused = set()
    for oname in _EXPECTED_OBJECTS:
        obj = controlm.get(oname)
        assert obj.profile is not None, oname
        assert obj.profile.census in ("pending", "complete"), oname
        if obj.profile.census == "pending":
            assert obj.profile.column_count is None, oname
        else:
            assert obj.profile.column_count is not None, oname
            censused.add(oname)
        assert obj.default_disposition is not None, oname
        assert obj.default_disposition["disposition"] == "excluded"
        assert obj.default_disposition["reason"] == "scope"
    assert censused == {"CM_AVG_RUN"}  # extend as further P0 censuses land


def test_vjob_projected_includes_the_audit_envelope(controlm: SourceMapping) -> None:
    """controlm_jobs.sql now projects the four audit-envelope columns
    (creation_user/creation_date/change_userid/change_date) alongside the rest."""
    projected = controlm.projected("CM_DEF_VJOB")
    for col in ("CREATION_USER", "CREATION_DATE", "CHANGE_USERID", "CHANGE_DATE", "JOB_ID", "CMD_LINE"):
        assert col in projected, col


def test_memname_is_projected_and_demoted(controlm: SourceMapping) -> None:
    memname = controlm.get("CM_DEF_VJOB").get("MEMNAME")
    assert memname.disposition == "projected"
    assert memname.decided_by == "controlm-q1q3-phase1"
    assert "demot" in memname.note.lower()


def test_version_star_are_non_envelope_audit_properties(controlm: SourceMapping) -> None:
    """VERSION_USER/VERSION_TIMESTAMP are current-version duplicates of
    CHANGE_USERID/CHANGE_DATE (config/audit-fields.yaml) — still projected as
    plain properties, just not part of the four-field envelope."""
    vjob = controlm.get("CM_DEF_VJOB")
    for col in ("VERSION_USER", "VERSION_TIMESTAMP"):
        disp = vjob.get(col)
        assert disp.disposition == "projected"
        assert disp.decided_by == "controlm-q1q3-phase1"
        assert "duplicate" in disp.note.lower()


def test_employee_sid_is_a_proposed_unbuilt_derived_also(controlm: SourceMapping) -> None:
    creation_user = controlm.get("CM_DEF_VJOB").get("CREATION_USER")
    assert creation_user.derived_also is not None
    assert creation_user.derived_also["target"] == "ControlMJob.employee_sid"


def test_is_current_version_and_user_daily_decided_by_the_gate(controlm: SourceMapping) -> None:
    vjob_flag = controlm.get("CM_DEF_VJOB").get("IS_CURRENT_VERSION")
    assert vjob_flag.disposition == "projected"
    assert vjob_flag.decided_by == "controlm-q1q3-phase1"

    user_daily = controlm.get("CM_DEF_VTAB").get("USER_DAILY")
    assert user_daily.disposition == "projected"
    assert user_daily.decided_by == "controlm-q1q3-phase1"


def test_lnki_lnko_is_current_version_is_staging_only(controlm: SourceMapping) -> None:
    """Selected in the SQL (current-version filter) but never SET onto the
    :Condition node or edge in the cypher — staging, not a graph landing."""
    for oname in ("CM_DEF_LNKI_P_VW", "CM_DEF_LNKO_P_VW"):
        disp = controlm.get(oname).get("IS_CURRENT_VERSION")
        assert disp.disposition == "projected"
        assert disp.target == "staging:is_current_version"


def test_setvar_object_name_is_confirmed(controlm: SourceMapping) -> None:
    setvar = controlm.get("CM_DEF_SETVAR_VW")
    assert setvar.note is not None
    assert "VERIFY NAME" not in setvar.note
    assert "confirmed" in setvar.note.lower()
    assert setvar.columns  # TABLE_ID, JOB_ID, NAME, VALUE
    assert setvar.projected() == ["TABLE_ID", "JOB_ID", "NAME", "VALUE"]


def test_cm_hosts_is_staging_only_pending_the_topology_gate(controlm: SourceMapping) -> None:
    """CM_HOSTS (host-group membership) landed 2026-07-09 via add-source-object:
    all five columns projected, but staging-only — the graph landing
    (ControlMHostGroup/ExecutionHost/CONTAINS_HOST/RUNS_ON resolution) is
    gate-bound (controlm-hosts-topology), the CM_DEF_SETVAR_VW precedent."""
    hosts = controlm.get("CM_HOSTS")
    assert hosts.projected() == [
        "DATA_CENTER", "GRPNAME", "NODEID", "PARTICIPATION_TYPE", "CAPTURE_DATE",
    ]
    for col in hosts.columns:
        assert col.target is not None and col.target.startswith("staging:"), col.name
    assert "controlm-hosts-topology" in (hosts.note or "")


def test_cm_avg_run_is_staging_only_with_the_weak_join_key_documented(controlm: SourceMapping) -> None:
    """CM_AVG_RUN (runtime stats) landed 2026-07-09 via add-source-object:
    14 columns projected, staging-only pending gate controlm-avg-run-supplement;
    the join key is (SCHED_TABLE, JOB_MEM_NAME = JOB_NAME) — never MEMNAME."""
    stats = controlm.get("CM_AVG_RUN")
    assert len(stats.projected()) == 14
    for col in stats.columns:
        assert col.target is not None and col.target.startswith("staging:"), col.name
    assert "controlm-avg-run-supplement" in (stats.note or "")
    assert "never MEMNAME" in stats.note


def test_all_columns_have_a_valid_disposition_and_origin(controlm: SourceMapping) -> None:
    from drydocs.source_mappings import VALID_DISPOSITIONS, VALID_ORIGINS

    for oname in _EXPECTED_OBJECTS:
        for col in controlm.get(oname).columns:
            assert col.disposition in VALID_DISPOSITIONS, (oname, col.name)
            if col.origin is not None:
                assert col.origin in VALID_ORIGINS, (oname, col.name)
            if col.disposition == "excluded":
                assert col.reason, f"{oname}/{col.name}: excluded without a reason"
