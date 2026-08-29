"""K25 — cross-application run_as detection. Synthetic throughout: invented
accounts, folders and applications; nothing here resembles a live value.

The structural tests mirror test_fid_census's: counts-only is enforced by the
RETURN TYPE, the §G5 reading is a parked human ruling, and every skip is
counted by reason.
"""

from __future__ import annotations

import json

import pytest

from drydocs.run_as_detect import (
    CLASS_APPLICATION,
    CLASS_PLATFORM,
    CLASS_UNRESOLVABLE,
    OUTCOME_DIFFERENT,
    OUTCOME_SAME,
    OUTCOME_UNRESOLVED,
    UNRULED,
    JobRow,
    RunAsDetectError,
    RunAsDetection,
    run_as_detection,
)

# ── the SME's live folder shape, synthetically ───────────────────────────────

DIRECTORY = {"FN70001A": "70001", "FN70002A": "70002"}
ATTRIBUTION = {"FLD-ALPHA": "70001", "FLD-BETA": "70002"}
PLATFORM = {"CTRLMPLAT"}


def _mixed_folder_jobs() -> list[JobRow]:
    """One folder, split INSIDE: the FileWatcher on the platform account, the
    payload jobs on the application's account — the 2026-08-19 captures'
    shape. A folder-grain read would call this folder application-run."""
    return [
        JobRow(run_as="CTRLMPLAT", job_type="FileWatcher", folder="FLD-ALPHA"),
        JobRow(run_as="FN70001A", job_type="Command", folder="FLD-ALPHA"),
        JobRow(run_as="FN70001A", job_type="Command", folder="FLD-ALPHA"),
    ]


def test_the_in_folder_split_is_captured_per_job_never_per_folder():
    result = run_as_detection(
        _mixed_folder_jobs(),
        directory_application=DIRECTORY,
        folder_attribution=ATTRIBUTION,
        platform_accounts=PLATFORM,
    )
    assert result.jobs_by_class == {
        CLASS_PLATFORM: 1,
        CLASS_APPLICATION: 2,
        CLASS_UNRESOLVABLE: 0,
    }
    # the class x job-type report is what a folder-grain read cannot produce
    assert result.class_by_job_type["FileWatcher"][CLASS_PLATFORM] == 1
    assert result.class_by_job_type["Command"][CLASS_APPLICATION] == 2
    # FileWatcher x platform is the DESIGNED pattern, not an anomaly
    assert result.platform_designed_pattern == 1
    assert result.platform_payload_anomaly == 0
    assert result.reconciles()


def test_a_payload_job_on_the_platform_account_is_the_countable_anomaly():
    jobs = [JobRow(run_as="CTRLMPLAT", job_type="Command", folder="FLD-ALPHA")]
    result = run_as_detection(
        jobs,
        directory_application=DIRECTORY,
        folder_attribution=ATTRIBUTION,
        platform_accounts=PLATFORM,
    )
    assert result.platform_payload_anomaly == 1
    assert result.platform_payload_anomaly_by_job_type == {"Command": 1}
    assert result.platform_designed_pattern == 0


def test_platform_jobs_never_enter_the_comparison():
    """The platform bucket is EXPECTED to disagree by construction — it
    resolves through the platform's own attribution chain, not the
    directory — so it produces NO same/different/unresolvable outcome."""
    result = run_as_detection(
        [JobRow(run_as="CTRLMPLAT", job_type="FileWatcher", folder="FLD-ALPHA")],
        directory_application=DIRECTORY,
        folder_attribution=ATTRIBUTION,
        platform_accounts=PLATFORM,
    )
    assert sum(result.outcomes_by_job.values()) == 0
    assert result.reconciles()


def test_platform_wins_over_directory_presence_and_the_precedence_is_counted():
    """The 171-way platform name IS a directory row — which is exactly why
    recognition cannot be 'is it registered'. Platform class wins, and the
    overlap is a visible counter, never silent."""
    directory = {**DIRECTORY, "CTRLMPLAT": "70099"}
    result = run_as_detection(
        [JobRow(run_as="CTRLMPLAT", job_type="Command", folder="FLD-ALPHA")],
        directory_application=directory,
        folder_attribution=ATTRIBUTION,
        platform_accounts=PLATFORM,
    )
    assert result.jobs_by_class[CLASS_PLATFORM] == 1
    assert result.jobs_by_class[CLASS_APPLICATION] == 0
    assert result.platform_accounts_also_in_directory == 1


def test_outcomes_same_different_unresolvable():
    jobs = [
        JobRow(run_as="FN70001A", job_type="Command", folder="FLD-ALPHA"),  # same
        JobRow(run_as="FN70001A", job_type="Command", folder="FLD-BETA"),  # different
        JobRow(run_as="FN70001A", job_type="Command", folder="FLD-UNKNOWN"),  # unresolvable
        JobRow(run_as="FN70001A", job_type="Command", folder=""),  # unresolvable, other reason
        JobRow(run_as="GHOST01", job_type="Command", folder="FLD-ALPHA"),  # class unresolvable
    ]
    result = run_as_detection(
        jobs,
        directory_application=DIRECTORY,
        folder_attribution=ATTRIBUTION,
        platform_accounts=PLATFORM,
    )
    assert result.outcomes_by_job == {
        OUTCOME_SAME: 1,
        OUTCOME_DIFFERENT: 1,
        OUTCOME_UNRESOLVED: 2,
    }
    # unresolvable BY REASON — "no attribution for the folder" and "the job
    # carried no folder at all" are different facts (the house rule)
    assert result.unresolvable_by_reason == {
        "folder_unattributed": 1,
        "job_carried_no_folder": 1,
    }
    assert result.jobs_by_class[CLASS_UNRESOLVABLE] == 1
    assert result.reconciles()


def test_the_g5_reading_is_parked_until_a_human_rules_it():
    jobs = [
        JobRow(run_as="FN70001A", job_type="Command", folder="FLD-BETA"),
        JobRow(run_as="FN70002A", job_type="Command", folder="FLD-ALPHA"),
    ]
    unruled = run_as_detection(
        jobs,
        directory_application=DIRECTORY,
        folder_attribution=ATTRIBUTION,
        platform_accounts=PLATFORM,
    )
    assert unruled.different_application_cases == 2
    assert unruled.cases_by_reading[UNRULED] == 2  # the unruled count IS reportable

    ruled = run_as_detection(
        jobs,
        directory_application=DIRECTORY,
        folder_attribution=ATTRIBUTION,
        platform_accounts=PLATFORM,
        rulings={("FN70001A", "70002"): "different_subjects"},
    )
    assert ruled.cases_by_reading["different_subjects"] == 1
    assert ruled.cases_by_reading[UNRULED] == 1
    assert ruled.reconciles()


def test_an_unknown_reading_is_refused():
    with pytest.raises(RunAsDetectError, match="unknown §G5 reading"):
        run_as_detection(
            [],
            directory_application={},
            folder_attribution={},
            rulings={("A", "B"): "obviously_fine"},
        )


def test_case_grain_not_job_grain_for_rulings():
    """Fifty jobs sharing one (account, attributed-app) disagreement are ONE
    case for a human to rule, not fifty."""
    jobs = [JobRow(run_as="FN70001A", job_type="Command", folder="FLD-BETA") for _ in range(50)]
    result = run_as_detection(
        jobs,
        directory_application=DIRECTORY,
        folder_attribution=ATTRIBUTION,
    )
    assert result.outcomes_by_job[OUTCOME_DIFFERENT] == 50
    assert result.different_application_cases == 1


def test_an_empty_platform_set_is_legal_not_preempting():
    """How a platform account is RECOGNIZED is a K17 ruling this module must
    not preempt — the injected set is the seam. Empty = no job classes as
    platform, and everything else still works."""
    result = run_as_detection(
        _mixed_folder_jobs(),
        directory_application=DIRECTORY,
        folder_attribution=ATTRIBUTION,
        platform_accounts=(),
    )
    assert result.jobs_by_class[CLASS_PLATFORM] == 0
    # the platform account, unrecognised, is now simply unresolvable — counted
    assert result.jobs_by_class[CLASS_UNRESOLVABLE] == 1
    assert result.reconciles()


def test_missing_run_as_is_counted_never_guessed():
    result = run_as_detection(
        [JobRow(run_as="  ", job_type="Command", folder="FLD-ALPHA")],
        directory_application=DIRECTORY,
        folder_attribution=ATTRIBUTION,
    )
    assert result.jobs_total == 0
    assert result.jobs_with_no_run_as == 1


def test_case_only_mismatch_is_reported_never_folded():
    """Both joins are covered: a case-only near-miss against the DIRECTORY and
    one against the PLATFORM SET each count — a silent platform-side case-miss
    would leak platform jobs into unresolvable with nothing saying so."""
    result = run_as_detection(
        [
            JobRow(run_as="fn70001a", job_type="Command", folder="FLD-ALPHA"),
            JobRow(run_as="ctrlmplat", job_type="FileWatcher", folder="FLD-ALPHA"),
        ],
        directory_application=DIRECTORY,
        folder_attribution=ATTRIBUTION,
        platform_accounts=PLATFORM,
    )
    assert result.jobs_by_class[CLASS_UNRESOLVABLE] == 2
    assert result.case_only_mismatches == 2


def test_counts_only_is_structural_no_account_folder_or_job_name_can_escape():
    """The K16 discipline: the result type holds ints, bools and str->int
    dicts (nested once for class x job type). A row dump is UNEXPRESSIBLE —
    and no injected identifier appears anywhere in the serialized output.
    Job-type strings are the one deliberate exception: they are vocabulary
    (TASK_TYPE values), not identifiers."""
    result = run_as_detection(
        _mixed_folder_jobs(),
        directory_application=DIRECTORY,
        folder_attribution=ATTRIBUTION,
        platform_accounts=PLATFORM,
    )
    payload = json.dumps(result.as_dict())
    for identifier in ("FN70001A", "CTRLMPLAT", "FLD-ALPHA", "70001"):
        assert identifier not in payload

    def only_counts(value) -> bool:
        if isinstance(value, int | bool):
            return True
        if isinstance(value, dict):
            return all(isinstance(k, str) and only_counts(v) for k, v in value.items())
        return False

    assert only_counts(result.as_dict())


def test_field_types_pin_the_counts_only_contract():
    """A later field carrying a list or a string (beyond nothing — there is no
    str field at all) would be the first step toward a row dump; refuse it
    here rather than at a review."""
    hints = RunAsDetection.__dataclass_fields__
    for name, f in hints.items():
        assert "list" not in str(f.type) and f.type not in (
            "str",
        ), f"{name}: {f.type} — RunAsDetection is counts-only by contract"
