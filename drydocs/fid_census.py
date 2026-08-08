"""FID directory census (K16) — the Phase-0 measurement doc 09 says to run FIRST.

Gate ``fid-identity-and-scope`` is DRAFTED AND UNSIGNED, and §D2 says why this runs
before it: *"about two hundred accounts per application"* is an estimate the gate
cannot rule on, and the census turns it into *"N of ~200, and here is what the other
rows are"*.

WHAT THIS MODULE IS. The METHOD only. Every input is INJECTED — this module opens no
file, contacts no database, and writes nothing. The counts it produces are Internal
and are computed company-side (backlog K16 notes; the runner is
``docs/k16-fid-census-company-prompt.md``). That split is the reason the module is
pure: the producer repo can hold, test and port the measurement without ever holding
the measured values.

COUNTS, NEVER A ROW DUMP (§D2, and the acceptance repeats it). :class:`FidCensus`
holds ``int`` and ``dict[str, int]`` fields ONLY, so a row dump is not merely
discouraged, it is UNEXPRESSIBLE in the return type. ``tests/unit/test_fid_census.py``
pins that structurally, because a later field carrying account names would leak
Internal values into a producer-side artifact.

THE FOUR MEASUREMENTS
---------------------
(a) ``directory_rows_total``   — total directory rows for the one application.
(b) ``demand_in_application``  — |demand set ∩ that application|, where the demand set
    is the union of doc 09's three sets, *all computable today*:
      i.   run-as owners (``run_as`` / ``J.OWNER``) in the Control-M extract
      ii.  distinct ``fact_value`` on ``STG_APP_FACT`` rows with ``fact_type='FID'``
           that the K2 resolver counts unresolved (the literal tier-2 backlog)
      iii. account names in registered adhoc evidence (corpus ``adhoc-sme-email``)
(c) the remainder (a) − (b), broken down by the directory's OWN type/status columns.
(Q0) the registration-vs-attribution DISAGREEMENT rate and its §G5 breakdown.

WHY Q0 IS THE PART THE GATE CANNOT SIGN WITHOUT. §Q4 was drafted asking *whether*
the directory's application assignment agrees with the Control-M-derived attribution;
it was ANSWERED IN THE NEGATIVE 2026-08-05 — it does not, in at least one confirmed
case. So the open question became the RATE and its breakdown, and that ratio decides
whether the directory is a trustworthy ownership source with expected consumer
divergence (§G5(a)) or a lagging record needing remediation (§G5(b)).

THE READING IS A HUMAN RULING, NEVER A COMPUTATION. §G5 is explicit: three readings,
*"distinguished per case and never globally… No single source distinguishes them. The
graph does, one disagreement at a time, with a human ruling each."* So this module
COUNTS disagreements mechanically and parks every one of them in ``unruled`` until an
SME ruling is supplied through ``rulings``. It will never infer a reading, and an
unruled disagreement is visible as its own number rather than being absorbed into a
neighbouring bucket — the never-silent house rule applied to the report.

TWO THINGS THE CENSUS SETTLES FOR FREE (doc 09, "Phase 0"):
  * gate §Q5 — whether non-application account types ever appear as run-as owners. If
    they do, type cannot be used even as an explanatory filter. See
    ``run_as_owner_types``.
  * the §Q4 disagreement rate above.

REGISTRATION IS NOT ATTRIBUTION. The two facts this module compares answer DIFFERENT
questions (doc 09, SME evidence 2026-08-05): the directory records who OWNS the
account (registration); the app-code mapping records whose work the FOLDER is
(attribution, K8-confirmed). A disagreement is therefore a FINDING, not an error, and
this module reports it as such — it resolves nothing, overrides nothing, and writes
nothing. Neither source is treated as correcting the other.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field

#: doc 09 §G5 — the three readings of a registration/attribution disagreement.
#: Order is the doc's own; it carries no precedence.
G5_READINGS: tuple[str, ...] = (
    "different_subjects",  # (a) both correct — a platform account serving a consumer app
    "stale_directory",  # (b) re-registration lagged a SEAL decomposition (remediation candidate)
    "wrong_attribution",  # (c) the folder attribution is wrong
)

#: Where every disagreement starts and stays until an SME rules it (§G5).
UNRULED = "unruled"

#: SME, 2026-08-07: EVERY functional id must carry at least two human owners.
#: Recorded here as a measurement threshold only — the RULE itself is a
#: graph-test, never a Neo4j constraint. Twice-established precedent: minimum
#: cardinality is not expressible in Neo4j ("NEVER a uniqueness constraint —
#: graph-TEST instead, the TOM-roles lesson"), so the census counts violations
#: and the enforcement lives in graph-tests/ once the account->owner edge exists.
#: It does not exist yet: doc 09's phase list models account->APPLICATION and
#: never account->PERSON, which is the gap this rule exposes.
OWNER_MINIMUM = 2

#: doc 09's three demand sets, in the doc's own order.
DEMAND_SOURCES: tuple[str, ...] = ("run_as_owners", "unresolved_fid_facts", "adhoc_evidence")


class FidCensusError(ValueError):
    """A census input the module refuses to guess its way past."""


@dataclass(frozen=True)
class DirectoryRow:
    """One row of the firm's functional-id directory, for ONE application.

    Field names are MECHANISM (the directory's column roles), never its real column
    spellings — those live company-side with the extract. ``application`` is the
    directory's own assignment: the REGISTRATION fact, not attribution.
    """

    account: str
    application: str
    account_type: str = ""
    status: str = ""
    #: The HUMAN owner of record, when the export carries one. Optional because
    #: the export's GRAIN is not known producer-side: an "idowner search" may
    #: return one row per account (filtered by owner) or one row per
    #: (account, owner) pair. Both are handled — see :data:`OWNER_MINIMUM`.
    owner: str = ""


@dataclass
class FidCensus:
    """The census result. Counts ONLY — see the module docstring.

    Invariant, checked by :meth:`reconciles`: every directory row lands in exactly
    one of ``demand_in_application`` or ``remainder_total``.
    """

    application: str = ""

    # (a) / (b) / (c)
    #: RAW ROWS read for this application. Distinct from `directory_accounts_total`
    #: because the export's grain is unknown: under (account, owner) grain a
    #: two-owner account contributes TWO rows, so reporting only one of these
    #: numbers as "(a) total directory rows" would be ambiguous by a factor of
    #: however many owners each account has.
    directory_rows_total: int = 0
    #: DISTINCT accounts — the grain (b) and (c) are actually computed at, and
    #: the one the reconciliation invariant balances against.
    directory_accounts_total: int = 0
    demand_total: int = 0  # |union of the three demand sets|
    demand_in_application: int = 0
    demand_by_source: dict[str, int] = field(default_factory=dict)
    demand_not_in_directory: int = 0
    remainder_total: int = 0
    remainder_by_type: dict[str, int] = field(default_factory=dict)
    remainder_by_status: dict[str, int] = field(default_factory=dict)

    # gate §Q5 — do non-application account types appear as run-as owners?
    run_as_owner_types: dict[str, int] = field(default_factory=dict)

    # Q0 / §G4-§G5
    comparable: int = 0  # accounts holding BOTH a registration and an attribution
    agreements: int = 0
    disagreements: int = 0
    undecidable: int = 0  # in the demand set + directory, but no attribution to compare
    disagreements_by_reading: dict[str, int] = field(default_factory=dict)

    # --- the two-human-owners rule (SME, 2026-08-07) --------------------------
    #: Accounts carrying fewer than OWNER_MINIMUM distinct human owners. A rule
    #: that CAN be violated, so the census measures compliance for free.
    accounts_below_owner_minimum: int = 0
    #: Accounts for which no owner was recorded at all. Kept SEPARATE from the
    #: line above: "fewer than two owners" and "the export carried no owner
    #: column" are different facts, and folding them would report an unmeasurable
    #: estate as a non-compliant one.
    accounts_with_no_owner_recorded: int = 0
    #: True only when at least one account carried owner data. Guards the reader
    #: against reading `accounts_below_owner_minimum: 0` as "compliant" when the
    #: real answer is "never measured".
    owner_rule_measurable: bool = False

    # never-silent counters
    case_only_mismatches: int = 0  # would match if case were folded — reported, never folded
    #: Rows beyond the first for an account that carry a DIFFERENT owner —
    #: EXPECTED under (account, owner) grain, not a defect.
    multi_owner_rows: int = 0
    #: Rows beyond the first with the SAME (account, owner) — a true duplicate.
    duplicate_directory_rows: int = 0

    def reconciles(self) -> bool:
        """(b) + remainder == distinct ACCOUNTS, and the disagreement split is complete.

        Balanced against `directory_accounts_total`, NOT `directory_rows_total`:
        (b) and (c) are computed per account, so under (account, owner) grain a
        row-based invariant would fail on every multi-owner account and report a
        correct census as broken.
        """
        rows_balance = (
            self.demand_in_application + self.remainder_total == self.directory_accounts_total
        )
        split_balance = sum(self.disagreements_by_reading.values()) == self.disagreements
        compare_balance = self.agreements + self.disagreements == self.comparable
        return rows_balance and split_balance and compare_balance

    def as_dict(self) -> dict:
        out = asdict(self)
        out["reconciles"] = self.reconciles()
        return out


def _normalize(name: str) -> str:
    """Trim only. Case is NOT folded: the directory and the scheduler are separate
    systems, and silently folding would convert a real identity question into an
    invisible match. Near-misses surface as ``case_only_mismatches`` instead — the
    same choice §D1 made for script paths, for the same reason."""
    return name.strip()


def fid_census(
    application: str,
    directory_rows: Iterable[DirectoryRow],
    *,
    run_as_owners: Iterable[str] = (),
    unresolved_fid_facts: Iterable[str] = (),
    adhoc_accounts: Iterable[str] = (),
    attribution_by_account: Mapping[str, str] | None = None,
    rulings: Mapping[str, str] | None = None,
) -> FidCensus:
    """Compute the doc-09 Phase-0 census for ONE application.

    ``attribution_by_account`` maps an account to the application its Control-M-derived
    FOLDER attribution names (K8's app-code mapping). Accounts absent from it are
    ``undecidable`` — counted, never assumed to agree.

    ``rulings`` maps an account with a disagreement to one of :data:`G5_READINGS`.
    Anything unruled stays in the ``unruled`` bucket; nothing is ever inferred.
    """
    if not application.strip():
        raise FidCensusError("application is required — the census is scoped to ONE application")

    attribution_by_account = attribution_by_account or {}
    rulings = rulings or {}

    unknown = {r for r in rulings.values() if r not in G5_READINGS}
    if unknown:
        raise FidCensusError(
            f"unknown §G5 reading(s) {sorted(unknown)}; expected one of {list(G5_READINGS)}"
        )

    census = FidCensus(application=application.strip())

    # ---- the directory side, scoped to this application ---------------------
    by_account: dict[str, DirectoryRow] = {}
    owners_by_account: dict[str, set[str]] = {}
    for row in directory_rows:
        account = _normalize(row.account)
        if not account:
            continue
        if _normalize(row.application) != census.application:
            continue  # another application's row — out of scope by construction
        census.directory_rows_total += 1
        owner = _normalize(row.owner)
        seen_owners = owners_by_account.setdefault(account, set())
        if account in by_account:
            # A repeat is EXPECTED under (account, owner) grain and is not a
            # defect: the SME rule is that every FID carries at least two human
            # owners, so a two-owner account legitimately contributes two rows.
            # Only a repeat of the SAME (account, owner) is a true duplicate.
            if owner and owner not in seen_owners:
                census.multi_owner_rows += 1
            else:
                census.duplicate_directory_rows += 1
        else:
            by_account[account] = row
        if owner:
            seen_owners.add(owner)
    census.directory_accounts_total = len(by_account)

    # ---- the two-human-owners rule (SME 2026-08-07), measured not assumed ----
    census.owner_rule_measurable = any(owners for owners in owners_by_account.values())
    for account in by_account:
        owners = owners_by_account.get(account, set())
        if not owners:
            # "no owner column in the export" is NOT "fewer than two owners".
            census.accounts_with_no_owner_recorded += 1
        elif len(owners) < OWNER_MINIMUM:
            census.accounts_below_owner_minimum += 1

    # ---- the demand set (doc 09's three sets; the union is the pull list) ----
    per_source = {
        "run_as_owners": {_normalize(a) for a in run_as_owners if _normalize(a)},
        "unresolved_fid_facts": {_normalize(a) for a in unresolved_fid_facts if _normalize(a)},
        "adhoc_evidence": {_normalize(a) for a in adhoc_accounts if _normalize(a)},
    }
    for source in DEMAND_SOURCES:
        census.demand_by_source[source] = len(per_source[source])
    demand = set().union(*per_source.values())
    census.demand_total = len(demand)

    # ---- (b) and the near-miss counter --------------------------------------
    folded = {a.casefold(): a for a in by_account}
    in_application: set[str] = set()
    for account in demand:
        if account in by_account:
            in_application.add(account)
        elif account.casefold() in folded:
            # reported, never folded — the directory and the scheduler disagree on
            # spelling, which is an identity question for the gate, not a bug to paper over
            census.case_only_mismatches += 1
            census.demand_not_in_directory += 1
        else:
            census.demand_not_in_directory += 1
    census.demand_in_application = len(in_application)

    # ---- (c) the remainder, by the directory's OWN columns -------------------
    for account, row in by_account.items():
        if account in in_application:
            continue
        census.remainder_total += 1
        key_type = row.account_type or "(blank)"
        key_status = row.status or "(blank)"
        census.remainder_by_type[key_type] = census.remainder_by_type.get(key_type, 0) + 1
        census.remainder_by_status[key_status] = census.remainder_by_status.get(key_status, 0) + 1

    # ---- gate §Q5: do non-application types appear as run-as owners? ---------
    for account in per_source["run_as_owners"]:
        row = by_account.get(account)
        if row is None:
            continue
        key = row.account_type or "(blank)"
        census.run_as_owner_types[key] = census.run_as_owner_types.get(key, 0) + 1

    # ---- Q0: registration vs attribution ------------------------------------
    census.disagreements_by_reading = {UNRULED: 0, **{r: 0 for r in G5_READINGS}}
    for account in sorted(in_application):
        attributed = attribution_by_account.get(account)
        if attributed is None:
            census.undecidable += 1
            continue
        census.comparable += 1
        registered = _normalize(by_account[account].application)
        if _normalize(attributed) == registered:
            census.agreements += 1
            continue
        census.disagreements += 1
        reading = rulings.get(account, UNRULED)
        census.disagreements_by_reading[reading] += 1

    return census
