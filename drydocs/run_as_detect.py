"""Cross-application run_as detection (K25) — the measurable half of §G's
registration-vs-attribution problem.

The gate's §G MALCOLM counterexample proved one INSTANCE (an account
registered to the platform, attributed to a product); this module makes the
CLASS measurable. It is ``fid_census``'s sibling and follows the same
discipline end to end:

- **THE METHOD ONLY.** Every input is injected — no file, no database, no
  writes. The counts are Internal and are computed company-side against the
  doc-09 S1-S4 query results; producer-side it is tested on synthetic rows.
- **COUNTS, NEVER A ROW DUMP.** :class:`RunAsDetection` holds ``int``,
  ``bool`` and ``dict[str, int]`` / ``dict[str, dict[str, int]]`` fields
  only, so a row dump is unexpressible in the return type (tested
  structurally).
- **NOTHING TOUCHES THE GRAPH and no edge is proposed** (acceptance (c)):
  if the SME wants cross-application run_as expressed as an edge or a
  property, that is a K17-gate amendment, and this output is the evidence
  it would cite.

THE FIRST CUT IS RUN_AS CLASS, NOT OUTCOME (SME clarification 2026-08-19).
Every job's run_as account is classed:

- ``platform_user``  — the account jobs run as when they run as the platform
  itself (the 171-way Control-M platform user; the class is cross-platform —
  Informatica carries several). EXPECTED to disagree with folder attribution
  BY CONSTRUCTION, so these jobs never enter the same/different comparison:
  they resolve through the platform's own attribution chain, not the
  directory. How much of the estate runs as the platform is itself a
  deliverable — a number nobody has.
- ``application_fid`` — resolvable through the id-owner listing (doc 09
  Source B). Only this class is compared: directory application assignment
  vs the folder's confirmed attribution.
- ``unresolvable``   — neither; counted by reason, never guessed.

HOW A PLATFORM ACCOUNT IS RECOGNIZED IS **NOT DECIDED HERE** — that is a K17
§D/§G ruling this module must not preempt. ``platform_accounts`` is an
INJECTED set: doc 09's S3 query (owners ranked by application/folder spread,
the SME confirming the top of the list) is the standing evidence-backed
proposal for how the caller fills it, and whatever K17 rules — curated list
or the directory's type/purpose columns — feeds the same parameter. An
empty set is legal and simply means no job classes as platform.

PER JOB, NEVER PER FOLDER (acceptance (e), from the SME's job-grain captures
2026-08-19): the class splits INSIDE one folder — the live example runs its
FileWatcher as the platform account while the folder default (the payload
jobs) runs as the application's account. A folder-grain read would report
that folder as application-run and miss the split entirely. So
classification is per job, the report carries class × job type, and:

- FileWatcher × platform is the DESIGNED PATTERN (file watching is a
  platform service) — counted as ``platform_designed_pattern``;
- the countable anomaly is a PAYLOAD job running as the platform —
  ``platform_payload_anomaly``, broken down by job type.

THE §G5 READING IS A HUMAN RULING, NEVER A COMPUTATION (acceptance (b), the
K16 discipline verbatim): every different-application CASE — a distinct
(account, folder attribution) pair — starts ``unruled``; an SME ruling is
injected per case, and the number still sitting unruled is itself
reportable.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field

#: doc 09 §G5 — the three readings of a registration/attribution disagreement.
#: The same vocabulary fid_census uses; K16 owns the census-side split.
G5_READINGS: tuple[str, ...] = (
    "different_subjects",  # (a) both correct
    "stale_directory",  # (b) re-registration lagged
    "wrong_attribution",  # (c) the folder attribution is wrong
)

#: Where every different-application case starts and stays until ruled.
UNRULED = "unruled"

#: Job types for which platform-account run_as is the DESIGNED pattern, not an
#: anomaly (SME job-grain evidence 2026-08-19: file watching is a platform
#: service). Kept a declared constant so widening it is a visible edit with
#: this citation next to it, never a silent reclassification.
PLATFORM_EXPECTED_JOB_TYPES: tuple[str, ...] = ("FileWatcher",)

#: The three run_as classes of the 2026-08-19 clarification.
CLASS_PLATFORM = "platform_user"
CLASS_APPLICATION = "application_fid"
CLASS_UNRESOLVABLE = "unresolvable"
RUN_AS_CLASSES: tuple[str, ...] = (CLASS_PLATFORM, CLASS_APPLICATION, CLASS_UNRESOLVABLE)

#: Comparison outcomes for application_fid-class jobs (acceptance (a)).
OUTCOME_SAME = "same_application"
OUTCOME_DIFFERENT = "different_application"
OUTCOME_UNRESOLVED = "unresolvable"


class RunAsDetectError(ValueError):
    """An input the detector refuses to guess its way past."""


@dataclass(frozen=True)
class JobRow:
    """One Control-M job, at the grain the detection classifies (per JOB).

    Field names are mechanism, not source column spellings (``run_as`` is
    ``CM_DEF_VJOB.OWNER``; ``job_type`` is ``TASK_TYPE``; ``folder`` is the
    scheduling table name the confirmed attribution is keyed on).
    """

    run_as: str
    job_type: str = ""
    folder: str = ""


@dataclass
class RunAsDetection:
    """The detection result. Counts ONLY — see the module docstring."""

    jobs_total: int = 0
    accounts_total: int = 0  # distinct run_as accounts observed

    # ---- the first cut: run_as CLASS (SME 2026-08-19) ------------------------
    jobs_by_class: dict[str, int] = field(default_factory=dict)
    accounts_by_class: dict[str, int] = field(default_factory=dict)
    #: class × job type — the (e) report. Nested counts, never rows.
    class_by_job_type: dict[str, dict[str, int]] = field(default_factory=dict)

    # ---- the platform bucket (expected to disagree BY CONSTRUCTION) ----------
    platform_designed_pattern: int = 0  # platform run_as on a PLATFORM_EXPECTED job type
    platform_payload_anomaly: int = 0  # platform run_as on any other job type
    platform_payload_anomaly_by_job_type: dict[str, int] = field(default_factory=dict)
    #: A platform account ALSO registered in the directory is EXPECTED (the
    #: 171-way name IS a directory row — 171 of them); counted so the class
    #: precedence (platform wins) is visible, never silent.
    platform_accounts_also_in_directory: int = 0

    # ---- the comparison, application_fid class only (acceptance (a)) ---------
    outcomes_by_job: dict[str, int] = field(default_factory=dict)
    outcomes_by_account: dict[str, int] = field(default_factory=dict)
    #: unresolvable, BY REASON — the house rule. An application-class job can
    #: still be unresolvable on the folder side (no confirmed attribution).
    unresolvable_by_reason: dict[str, int] = field(default_factory=dict)

    # ---- the §G5 split, parked until ruled (acceptance (b)) ------------------
    #: distinct (account, folder-attributed application) pairs that disagree —
    #: the CASE grain a human rules at.
    different_application_cases: int = 0
    cases_by_reading: dict[str, int] = field(default_factory=dict)

    # ---- never-silent counters ----------------------------------------------
    jobs_with_no_run_as: int = 0  # counted and excluded, never guessed
    case_only_mismatches: int = 0  # would resolve if case were folded — reported, never folded

    def reconciles(self) -> bool:
        """Every job lands in exactly one class; every application-class job in
        exactly one outcome; every different-application case in exactly one
        reading bucket."""
        class_balance = sum(self.jobs_by_class.values()) == self.jobs_total
        app_jobs = self.jobs_by_class.get(CLASS_APPLICATION, 0)
        outcome_balance = sum(self.outcomes_by_job.values()) == app_jobs
        reading_balance = sum(self.cases_by_reading.values()) == self.different_application_cases
        unresolved_balance = self.unresolvable_by_reason == {} or sum(
            self.unresolvable_by_reason.values()
        ) == self.outcomes_by_job.get(OUTCOME_UNRESOLVED, 0)
        return class_balance and outcome_balance and reading_balance and unresolved_balance

    def as_dict(self) -> dict:
        out = asdict(self)
        out["reconciles"] = self.reconciles()
        return out


def _normalize(name: str) -> str:
    """Trim only — fid_census._normalize's reasoning applies verbatim: the
    2026-08-12 ruling makes case-folding the CALLER's job on the way in
    (``UPPER(EMP_LAST_NAME) = OWNER``), so a surviving near-miss here is a
    REAL spelling difference, surfaced as ``case_only_mismatches`` and never
    folded silently."""
    return name.strip()


def run_as_detection(
    jobs: Iterable[JobRow],
    *,
    directory_application: Mapping[str, str],
    folder_attribution: Mapping[str, str],
    platform_accounts: Iterable[str] = (),
    rulings: Mapping[tuple[str, str], str] | None = None,
) -> RunAsDetection:
    """Classify every job's run_as and count the cross-application seam.

    ``directory_application``  account -> the directory's application assignment
                               (doc 09 Source B — REGISTRATION, not attribution).
    ``folder_attribution``     folder -> the confirmed application attribution
                               (K8's app-code mapping). Folders absent from it
                               make their jobs' outcome unresolvable BY REASON.
    ``platform_accounts``      the injected platform-user set — see the module
                               docstring; this parameter is the seam K17 rules
                               into, not a decision made here.
    ``rulings``                (account, attributed_application) -> a
                               :data:`G5_READINGS` value. Anything unruled
                               stays ``unruled``; nothing is ever inferred.
    """
    rulings = rulings or {}
    unknown = {r for r in rulings.values() if r not in G5_READINGS}
    if unknown:
        raise RunAsDetectError(
            f"unknown §G5 reading(s) {sorted(unknown)}; expected one of {list(G5_READINGS)}"
        )

    platform = {_normalize(a) for a in platform_accounts if _normalize(a)}
    directory = {_normalize(k): _normalize(v) for k, v in directory_application.items()}
    attribution = {_normalize(k): _normalize(v) for k, v in folder_attribution.items()}
    # near-miss detection covers BOTH joins: an account that would resolve
    # into the directory OR the platform set if case were folded is reported,
    # never folded — a silent case-miss on the platform side would leak
    # platform jobs into unresolvable with no counter saying so.
    directory_folded = {k.casefold() for k in directory}
    platform_folded = {a.casefold() for a in platform}

    result = RunAsDetection(
        jobs_by_class={c: 0 for c in RUN_AS_CLASSES},
        outcomes_by_job={o: 0 for o in (OUTCOME_SAME, OUTCOME_DIFFERENT, OUTCOME_UNRESOLVED)},
        cases_by_reading={UNRULED: 0, **{r: 0 for r in G5_READINGS}},
    )
    result.platform_accounts_also_in_directory = len(platform & set(directory))

    accounts_seen: dict[str, str] = {}  # account -> class
    account_outcomes: dict[str, set[str]] = {}
    different_cases: set[tuple[str, str]] = set()

    for job in jobs:
        account = _normalize(job.run_as)
        if not account:
            result.jobs_with_no_run_as += 1
            continue
        result.jobs_total += 1
        job_type = _normalize(job.job_type) or "(blank)"

        # ---- class first (the 2026-08-19 clarification). Platform WINS over
        # directory presence: the 171-way platform name IS in the directory,
        # which is exactly why recognition cannot be "is it registered".
        if account in platform:
            cls = CLASS_PLATFORM
        elif account in directory:
            cls = CLASS_APPLICATION
        else:
            cls = CLASS_UNRESOLVABLE
            if account.casefold() in directory_folded or account.casefold() in platform_folded:
                result.case_only_mismatches += 1
        result.jobs_by_class[cls] += 1
        accounts_seen.setdefault(account, cls)
        by_type = result.class_by_job_type.setdefault(job_type, dict.fromkeys(RUN_AS_CLASSES, 0))
        by_type[cls] += 1

        if cls == CLASS_PLATFORM:
            if job_type in PLATFORM_EXPECTED_JOB_TYPES:
                result.platform_designed_pattern += 1
            else:
                result.platform_payload_anomaly += 1
                result.platform_payload_anomaly_by_job_type[job_type] = (
                    result.platform_payload_anomaly_by_job_type.get(job_type, 0) + 1
                )
            continue  # expected to disagree by construction — never compared
        if cls == CLASS_UNRESOLVABLE:
            continue

        # ---- application_fid: registration vs attribution, per job ----------
        folder = _normalize(job.folder)
        attributed = attribution.get(folder) if folder else None
        if not attributed:
            outcome = OUTCOME_UNRESOLVED
            reason = "folder_unattributed" if folder else "job_carried_no_folder"
            result.unresolvable_by_reason[reason] = result.unresolvable_by_reason.get(reason, 0) + 1
        elif directory[account] == attributed:
            outcome = OUTCOME_SAME
        else:
            outcome = OUTCOME_DIFFERENT
            different_cases.add((account, attributed))
        result.outcomes_by_job[outcome] += 1
        account_outcomes.setdefault(account, set()).add(outcome)

    # ---- account-grain roll-ups (derived; the job grain stays primary) -------
    result.accounts_total = len(accounts_seen)
    result.accounts_by_class = dict.fromkeys(RUN_AS_CLASSES, 0)
    for cls in accounts_seen.values():
        result.accounts_by_class[cls] += 1
    for outcomes in account_outcomes.values():
        for outcome in outcomes:
            result.outcomes_by_account[outcome] = result.outcomes_by_account.get(outcome, 0) + 1

    # ---- the §G5 split, at CASE grain, parked until ruled --------------------
    result.different_application_cases = len(different_cases)
    for case in sorted(different_cases):
        reading = rulings.get(case, UNRULED)
        result.cases_by_reading[reading] += 1

    return result
