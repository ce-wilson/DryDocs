"""N15 — agreement-candidate detection (gate pending-source-correction, SIGNED
2026-08-18, §B). The load PROPOSES, a steward confirms; an unattended run can
only ever leave an OPEN DRAFT, and detection never flips an override's status.
Offline (J18): the store builds in memory from fixture CSVs; no graph, no API.
Synthetic values only (publish boundary)."""

from __future__ import annotations

import pytest

from drydocs.loaders.seal_contacts import (
    _RETIREMENT_DOMAIN,
    SealContactsLoader,
    detect_agreement_candidates,
    propose_agreement_retirements,
)
from drydocs_core import mapping_store as ms

_HEADER = (
    "app_seal_id,role_name,seal_holder_sid,override_holder_sid,"
    "override_holder_name,rationale,authored_by,authored_on,status,"
    "agreement_run_id,agreement_source_value,agreement_observed_on"
)


@pytest.fixture()
def store_conn(tmp_path):
    """In-memory store over a three-row fixture: two active overrides and one
    already corrected-in-seal (which detection must never scan up)."""
    fix = tmp_path / "seal-contact-overrides.csv"
    fix.write_text(
        _HEADER + "\n"
        "APP-1111,L2 Operate Manager,U100001,U200002,Sam Steward,"
        "person left the team,kchen2190,2026-07-21,active,,,\n"
        "APP-2222,L1 Operate Manager,U100003,U200004,,role unassigned,"
        "kchen2190,2026-07-22,active,,,\n"
        "APP-3333,L2 Operate Manager,U100005,U200006,,already fixed,"
        "kchen2190,2026-06-01,corrected-in-seal,run-x,U200006,2026-06-15\n",
        encoding="utf-8",
    )
    conn = ms.build(":memory:", overrides_path=fix)
    yield conn
    conn.close()


def _statuses(conn) -> list[tuple]:
    return conn.execute(
        "SELECT app_seal_id, status FROM seal_contact_override ORDER BY app_seal_id"
    ).fetchall()


def test_agreement_detected_leaves_open_draft_with_evidence(store_conn):
    """(a)+(b)+(c): the source now carries the corrected holder for APP-1111 —
    one retirement candidate, proposed as an open draft carrying the agreement
    evidence a confirming steward archives onto the row."""
    seen = {("APP-1111", "L2 Operate Manager"): "U200002"}
    written = propose_agreement_retirements(
        seen, run_id="run-abc-12345678", observed_on="2026-08-28T00:00:00", conn=store_conn
    )
    assert written == 1
    drafts = ms.open_drafts(store_conn, domain=_RETIREMENT_DOMAIN)
    assert len(drafts) == 1
    payloads = ms.draft_payloads(store_conn, drafts[0]["draft_id"])
    assert payloads[0]["app_seal_id"] == "APP-1111"
    assert payloads[0]["proposed_status"] == "corrected-in-seal"
    assert payloads[0]["agreement_run_id"] == "run-abc-12345678"
    assert payloads[0]["agreement_source_value"] == "U200002"
    assert payloads[0]["agreement_observed_on"].startswith("2026-08-28")
    assert drafts[0]["authored_by"] == SealContactsLoader.name


def test_disagreement_is_ignored(store_conn):
    seen = {("APP-1111", "L2 Operate Manager"): "U999999"}
    assert detect_agreement_candidates(seen, store_conn) == []


def test_corrected_in_seal_rows_are_skipped(store_conn):
    """An already-archived row cannot become a candidate again — the WHERE
    clause scans active rows only."""
    seen = {("APP-3333", "L2 Operate Manager"): "U200006"}
    assert detect_agreement_candidates(seen, store_conn) == []


def test_detection_never_flips_any_status(store_conn):
    """§B2's structural no-flip: a detection run leaves every
    seal_contact_override.status value untouched — there is no UPDATE path."""
    before = _statuses(store_conn)
    seen = {
        ("APP-1111", "L2 Operate Manager"): "U200002",
        ("APP-2222", "L1 Operate Manager"): "U200004",
    }
    propose_agreement_retirements(
        seen, run_id="run-def-00000000", observed_on="2026-08-28T00:00:00", conn=store_conn
    )
    assert _statuses(store_conn) == before


def test_repeat_runs_do_not_duplicate_open_candidates(store_conn):
    """A candidate already on an open retirement draft is not proposed again —
    an unattended nightly load accumulates ONE proposal, not one per run."""
    seen = {("APP-1111", "L2 Operate Manager"): "U200002"}
    first = propose_agreement_retirements(
        seen, run_id="run-aaa-11111111", observed_on="2026-08-28T00:00:00", conn=store_conn
    )
    second = propose_agreement_retirements(
        seen, run_id="run-bbb-22222222", observed_on="2026-08-29T00:00:00", conn=store_conn
    )
    assert (first, second) == (1, 0)


def test_no_candidates_is_a_clean_zero(store_conn):
    """§C3 class: 'no candidates' is a normal answer, never an error."""
    assert (
        propose_agreement_retirements(
            {}, run_id="run-eee-33333333", observed_on="2026-08-28T00:00:00", conn=store_conn
        )
        == 0
    )


def test_loader_collects_holders_through_to_params():
    """The collection hook: to_params tees (app_id, role_name) -> employee_sid
    without changing what it returns."""
    loader = object.__new__(SealContactsLoader)
    loader._seen_holders = {}
    model = SealContactsLoader.row_model(
        app_id="APP-1111",
        role_name="L2 Operate Manager",
        employee_sid="U200002",
    )
    params = loader.to_params(model)
    assert params["app_id"] == "APP-1111"
    assert loader._seen_holders[("APP-1111", "L2 Operate Manager")] == "U200002"


def test_evidence_columns_ingest_from_the_committed_list(store_conn):
    """§B4 round-trip: the archived fixture row's evidence columns survive the
    CSV -> mapping.db materialization, so the committed list stays the source
    of record and the store stays rebuildable."""
    row = store_conn.execute(
        "SELECT agreement_run_id, agreement_source_value, agreement_observed_on "
        "FROM seal_contact_override WHERE app_seal_id = 'APP-3333'"
    ).fetchone()
    assert row == ("run-x", "U200006", "2026-06-15")
