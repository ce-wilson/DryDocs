"""K16 — the FID directory census method (doc 09 Phase 0). Pure; no Neo4j, no files.

Every fixture below is SYNTHETIC. The real counts are Internal and are produced
company-side (``docs/k16-fid-census-company-prompt.md``); what the producer repo
carries and guards is the METHOD.
"""

from __future__ import annotations

import pytest

from drydocs.fid_census import (
    DEMAND_SOURCES,
    G5_READINGS,
    UNRULED,
    DirectoryRow,
    FidCensus,
    FidCensusError,
    fid_census,
)

APP = "app-alpha"
OTHER = "app-beta"


def _rows(*specs: tuple[str, str, str, str]) -> list[DirectoryRow]:
    return [DirectoryRow(a, app, t, s) for a, app, t, s in specs]


# --- 1. the structural promise: counts only, never a row dump ------------------


def test_result_carries_no_row_level_data() -> None:
    """§D2 — 'reported as counts, never as a row dump'. Pinned STRUCTURALLY, because
    a later field holding account names would leak Internal values into an artifact
    the producer side can hold."""
    census = fid_census(APP, _rows(("svc.a", APP, "application", "active")))
    for name, value in census.as_dict().items():
        if name in {"application", "reconciles"}:
            continue
        assert isinstance(value, int) or (
            isinstance(value, dict)
            and all(isinstance(k, str) and isinstance(v, int) for k, v in value.items())
        ), f"{name} is not a count: {type(value).__name__}"


def test_application_is_required() -> None:
    with pytest.raises(FidCensusError, match="ONE application"):
        fid_census("   ", [])


# --- 2. (a), (b), (c) ----------------------------------------------------------


def test_counts_a_b_and_c_reconcile() -> None:
    rows = _rows(
        ("svc.a", APP, "application", "active"),
        ("svc.b", APP, "application", "active"),
        ("svc.c", APP, "platform", "active"),
        ("svc.d", APP, "application", "retired"),
        ("svc.z", OTHER, "application", "active"),  # another application — out of scope
    )
    census = fid_census(APP, rows, run_as_owners=["svc.a"], unresolved_fid_facts=["svc.b"])

    assert census.directory_rows_total == 4  # (a) — the OTHER-application row excluded
    assert census.demand_in_application == 2  # (b)
    assert census.remainder_total == 2  # (c)
    assert census.remainder_by_type == {"platform": 1, "application": 1}
    assert census.remainder_by_status == {"active": 1, "retired": 1}
    assert census.reconciles()


def test_demand_set_is_the_union_but_each_source_is_reported() -> None:
    """The union is the pull list (doc 09), yet an overlapping account must not hide
    which feed demanded it — that is what makes 'no fourth set' auditable."""
    rows = _rows(("svc.a", APP, "application", "active"))
    census = fid_census(
        APP,
        rows,
        run_as_owners=["svc.a"],
        unresolved_fid_facts=["svc.a"],
        adhoc_accounts=["svc.a"],
    )
    assert census.demand_total == 1
    assert census.demand_by_source == dict.fromkeys(DEMAND_SOURCES, 1)
    assert census.demand_in_application == 1


def test_demanded_but_absent_from_the_directory_is_counted() -> None:
    census = fid_census(APP, _rows(("svc.a", APP, "application", "active")), run_as_owners=["svc.ghost"])
    assert census.demand_not_in_directory == 1
    assert census.demand_in_application == 0


def test_a_true_duplicate_row_is_counted_not_merged() -> None:
    """Same account AND same owner twice — a real duplicate, distinct from the
    multi-owner repeat below."""
    rows = [
        DirectoryRow("svc.a", APP, "application", "active", owner="ada"),
        DirectoryRow("svc.a", APP, "platform", "retired", owner="ada"),
    ]
    census = fid_census(APP, rows)
    assert census.directory_rows_total == 2
    assert census.directory_accounts_total == 1
    assert census.duplicate_directory_rows == 1
    assert census.multi_owner_rows == 0


# --- the two-human-owners rule (SME 2026-08-07) --------------------------------


def test_owner_grain_rows_are_not_duplicates_and_do_not_break_the_invariant() -> None:
    """THE grain fix. The export may be one row per (account, owner), and the SME
    rule is that every FID carries at least two human owners — so a two-owner
    account legitimately contributes TWO rows. Counting those as duplicates would
    turn ~200 accounts into ~200 phantom defects, and balancing the invariant on
    ROWS instead of ACCOUNTS would report a correct census as broken."""
    rows = [
        DirectoryRow("svc.a", APP, "application", "active", owner="ada"),
        DirectoryRow("svc.a", APP, "application", "active", owner="grace"),
    ]
    census = fid_census(APP, rows, run_as_owners=["svc.a"])
    assert census.directory_rows_total == 2
    assert census.directory_accounts_total == 1
    assert census.multi_owner_rows == 1
    assert census.duplicate_directory_rows == 0
    assert census.accounts_below_owner_minimum == 0
    assert census.reconciles(), "the invariant must balance on ACCOUNTS, not rows"


def test_an_account_with_one_owner_violates_the_rule_and_is_counted() -> None:
    census = fid_census(APP, [DirectoryRow("svc.a", APP, owner="ada")])
    assert census.owner_rule_measurable
    assert census.accounts_below_owner_minimum == 1
    assert census.accounts_with_no_owner_recorded == 0


def test_no_owner_column_is_unmeasurable_never_reported_as_compliant() -> None:
    """"fewer than two owners" and "the export carried no owner column" are
    different facts. Folding them would report an UNMEASURED estate as a
    compliant one — the never-silent rule applied to a rule check."""
    census = fid_census(APP, _rows(("svc.a", APP, "application", "active")))
    assert census.owner_rule_measurable is False
    assert census.accounts_below_owner_minimum == 0
    assert census.accounts_with_no_owner_recorded == 1


# --- 3. case: reported, never folded -------------------------------------------


def test_case_only_mismatch_is_reported_and_never_folded() -> None:
    """The directory and the scheduler are separate systems. Folding case would turn
    an identity question the gate must rule into an invisible match."""
    census = fid_census(APP, _rows(("SVC.A", APP, "application", "active")), run_as_owners=["svc.a"])
    assert census.case_only_mismatches == 1
    assert census.demand_not_in_directory == 1
    assert census.demand_in_application == 0, "a case-only near-miss must NOT count as a match"


# --- 4. gate §Q5 — non-application types among run-as owners -------------------


def test_run_as_owner_types_answers_q5() -> None:
    rows = _rows(
        ("svc.a", APP, "application", "active"),
        ("svc.p", APP, "platform", "active"),
    )
    census = fid_census(APP, rows, run_as_owners=["svc.a", "svc.p"])
    assert census.run_as_owner_types == {"application": 1, "platform": 1}, (
        "a non-application type appearing as a run-as owner is exactly what §Q5 asks; "
        "if it happens, type cannot be used even as an explanatory filter"
    )


# --- 5. Q0 — registration vs attribution ---------------------------------------


def test_agreement_disagreement_and_undecidable_are_three_outcomes() -> None:
    rows = _rows(
        ("svc.agree", APP, "application", "active"),
        ("svc.disagree", APP, "application", "active"),
        ("svc.noattr", APP, "application", "active"),
    )
    census = fid_census(
        APP,
        rows,
        run_as_owners=["svc.agree", "svc.disagree", "svc.noattr"],
        attribution_by_account={"svc.agree": APP, "svc.disagree": OTHER},
    )
    assert (census.agreements, census.disagreements, census.undecidable) == (1, 1, 1)
    assert census.comparable == 2, "an account with no attribution is not comparable"
    assert census.reconciles()


def test_an_unruled_disagreement_stays_unruled() -> None:
    """§G5 — three readings 'distinguished per case and never globally'. The module
    counts; a human rules. Nothing may be inferred."""
    census = fid_census(
        APP,
        _rows(("svc.d", APP, "application", "active")),
        run_as_owners=["svc.d"],
        attribution_by_account={"svc.d": OTHER},
    )
    assert census.disagreements == 1
    assert census.disagreements_by_reading[UNRULED] == 1
    assert all(census.disagreements_by_reading[r] == 0 for r in G5_READINGS)


def test_an_sme_ruling_moves_a_disagreement_out_of_unruled() -> None:
    census = fid_census(
        APP,
        _rows(("svc.d", APP, "application", "active")),
        run_as_owners=["svc.d"],
        attribution_by_account={"svc.d": OTHER},
        rulings={"svc.d": "stale_directory"},
    )
    assert census.disagreements_by_reading["stale_directory"] == 1
    assert census.disagreements_by_reading[UNRULED] == 0
    assert census.reconciles()


def test_an_invented_reading_is_refused() -> None:
    with pytest.raises(FidCensusError, match="unknown"):
        fid_census(
            APP,
            _rows(("svc.d", APP, "application", "active")),
            run_as_owners=["svc.d"],
            attribution_by_account={"svc.d": OTHER},
            rulings={"svc.d": "probably-fine"},
        )


def test_disagreement_is_not_treated_as_an_error_either_way() -> None:
    """Registration and attribution answer DIFFERENT questions (doc 09), so neither
    source corrects the other. The census must not resolve, rank or drop anything —
    the disagreement survives as a finding."""
    census = fid_census(
        APP,
        _rows(("svc.d", APP, "application", "active")),
        run_as_owners=["svc.d"],
        attribution_by_account={"svc.d": OTHER},
    )
    assert census.demand_in_application == 1, "a disagreeing account is still in the demand set"
    assert census.remainder_total == 0


# --- 6. the empty case ---------------------------------------------------------


def test_empty_inputs_reconcile_and_report_zero() -> None:
    census = fid_census(APP, [])
    assert isinstance(census, FidCensus)
    assert census.directory_rows_total == 0 and census.demand_total == 0
    assert census.disagreements_by_reading == {UNRULED: 0, **dict.fromkeys(G5_READINGS, 0)}
    assert census.reconciles()
