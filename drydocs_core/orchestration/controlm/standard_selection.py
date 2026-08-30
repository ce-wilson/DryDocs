"""Which standard does a job validate against? (G94)

SELECTION IS NOT VALIDATION, and separating them is the point of this module.
:func:`drydocs_core.orchestration.controlm.description_tokens.validate` keeps
taking what it is given, so the decision tree here can be re-ruled without
touching the parser — and the parser cannot quietly acquire a policy opinion.

THE TREE, from the user direction of 2026-08-12 and guidelines §7.2. Today
``required_tokens(JobType)`` selects on ONE dimension, which is the gap this
closes:

1. **A file watcher validates against the FileWatcher standard.** One branch,
   no engine question — a file watcher runs no ETL engine.
2. **A command job selects on its ETL ENGINE FIRST** — DPL, Ab Initio,
   Informatica, which :func:`drydocs_core.orchestration.shell.classify_executable`
   already classifies as ``invocation_type``, so the engine dimension needs no
   new classifier.
3. **Anything else falls back to a GENERIC standard** carrying only the shared
   tokens, and says why it fell back.

THE ENGINE BRANCH IS DECLARED, NOT INVENTED (clause c). Each engine gets an
identity and a branch here; the CONTENT of each engine's token set is NOT ruled
by this module. :data:`ENGINE_TOKEN_SETS` is therefore **empty on purpose**: an
engine with no ruled set inherits the generic set and REPORTS that it did
(:attr:`StandardSelection.inherited_generic`), so an unruled engine is visible
rather than silently generic. Adding a per-engine required set here without a
ruling would be exactly the "grooming a policy into a done deal" this item's
own notes warn against.

THE GENERIC SET IS DERIVED, NEVER RETYPED (clause d). It is computed from
``TOKEN_REGISTRY`` and ``FOLDER_VARIABLES`` at call time, so it cannot drift
from the register the parser and the published document already share.

IDENTITIES ARE INTERIM (G95 §E2, verbatim: *"G94 BUILDS REGARDLESS: the selector
does not depend on this page — it can return interim identities derived from its
own branches until the carrier exists. What G94 may NOT do is invent the
carrier"*). So this module returns ids in the shape that gate PROPOSES —
``<domain>.<subject>.v<N>`` — and stores nothing, creates no config family, and
does not touch ``TOKEN_REGISTRY``. If the gate rules a different shape, the
constants below change and no caller does, because **the id is opaque to
selection**: this module RETURNS an id and never parses one.

THE DD DIGIT NEVER SELECTS (clause b). ``DD1|`` is a grammar VERSION; a future
``DD2|`` is read side by side through a migration. It is deliberately not an
input to any function here — not merely unused, but absent from the signature,
so the guard in ``tests/unit/test_standard_selection.py`` has something
structural to assert rather than a convention to trust.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final

from drydocs_core.orchestration.controlm.description_tokens import (
    FOLDER_VARIABLES,
    TOKEN_REGISTRY,
    JobType,
)
from drydocs_core.orchestration.shell import classify_executable

# ---------------------------------------------------------------------------
# Interim identities (G95 §E2). Shape proposed by gate `standard-identity-and-
# carrier` §A2 and NOT YET SIGNED -- versioned by CONTENT, never by grammar.
# ---------------------------------------------------------------------------
STANDARD_FILE_WATCHER: Final = "controlm.filewatcher.v1"
STANDARD_GENERIC: Final = "controlm.generic.v1"

#: Engine branch ids, keyed by the launcher registry's ``invocation_type``.
#: Only the three engines the direction names get a branch; every other
#: invocation type (JAVA, PYSPARK, FILE_TRANSFER, UNKNOWN) is generic, and the
#: selection says so in its reason rather than by silence.
ENGINE_STANDARDS: Final[dict[str, str]] = {
    "DPL": "controlm.engine-dpl.v1",
    "ABINITIO": "controlm.engine-abinitio.v1",
    "INFORMATICA": "controlm.engine-informatica.v1",
}

#: Per-engine required token sets. **EMPTY BY DECLARATION, not by omission.**
#: Clause (c) puts the CONTENT of each engine's set outside this item: an engine
#: with no ruled set inherits the generic set and reports that it did. An entry
#: appears here only when a ruling puts one here.
ENGINE_TOKEN_SETS: Final[dict[str, tuple[str, ...]]] = {}

#: Folder-variable spellings C30 §5.3 RENAMED, mapped to the current name. This
#: is read off the register's own notes ("Pre-C30 spelling of the folder-scope
#: ops support DL -- renamed EMAIL_DL_L2 by C30 §5.3; kept so live extracts
#: authored either way resolve"), declared as DATA here rather than left in
#: prose, because a required set that demanded both spellings of one fact would
#: be wrong in a way no reader could see. Both spellings still PARSE -- this
#: affects what is REQUIRED, never what resolves.
_PRE_RENAME_FOLDER_TWINS: Final[dict[str, str]] = {
    "L2_EMAIL_DL_NM": "EMAIL_DL_L2",
    "L3_EMAIL_DL_NM": "EMAIL_DL_L3",
}

#: Why a selection landed where it did. Coverage counts these (clause e) --
#: the adoption-not-compliance measure G84 established.
REASON_FILE_WATCHER: Final = "file-watcher job type"
REASON_ENGINE: Final = "ETL engine classified from the launcher"
REASON_ENGINE_UNRULED: Final = "ETL engine classified; no ruled token set for it yet"
REASON_ENGINE_UNCLASSIFIED: Final = "command job; launcher matched no ETL engine"
REASON_NO_EXECUTABLE: Final = "command job; no executable to classify"
REASON_UNSELECTABLE: Final = "no engine classified and no job role registered"


@dataclass(frozen=True)
class StandardSelection:
    """One answer: which standard, which tokens it requires, and why.

    ``unselectable`` is an ANSWER and not an error (clause e). A job whose
    engine cannot be classified and whose job role is absent still gets the
    generic standard; what it also gets is a reason, so the gap is countable
    instead of invisible.
    """

    standard_id: str
    branch: str
    required: tuple[str, ...]
    reason: str
    engine: str | None = None
    classifier_rule: str | None = None
    job_role: str | None = None
    #: True when an engine branch was selected but no token set is ruled for it,
    #: so the generic set was inherited. Visible, never silent (clause c).
    inherited_generic: bool = False
    #: True when neither the engine nor the job role could be established.
    unselectable: bool = False

    @property
    def is_generic(self) -> bool:
        return self.standard_id == STANDARD_GENERIC


def generic_required_tokens() -> tuple[str, ...]:
    """The shared set, DERIVED from the register (clause d).

    ``JobType.BOTH`` description tokens plus the folder variables, under the
    same filter :func:`required_tokens` uses — never retired, never optional —
    with C30's renamed folder spellings collapsed onto their current name. It is
    computed rather than listed so it cannot drift from ``TOKEN_REGISTRY``.

    RETIREMENT IS CARRIER-SCOPED, which is why the filter is applied PER TABLE
    rather than once over the union. C30 §5.3 retired ``EMAIL_DL_L2`` as a
    *description token* and kept it as a *folder variable* — one spelling, two
    carriers, two lifecycles. Filtering the union on "is this key retired
    anywhere" would drop a live folder variable, so each table is filtered by its
    own ``retired_by``. This is :class:`Carrier` doing the job it exists for.

    Today the two ``JobType.BOTH`` description tokens are both retired, so the
    result is the four folder variables — the DevX project key and the three
    EMAIL_DL contacts, exactly what the direction describes the generic standard
    as carrying. That agreement is asserted rather than assumed.
    """
    keys: list[str] = [
        spec.key
        for spec in TOKEN_REGISTRY.values()
        if spec.job_type is JobType.BOTH and not spec.retired_by and not spec.optional
    ]
    seen = set(keys)
    for spec in FOLDER_VARIABLES.values():
        if spec.retired_by or spec.optional:
            continue
        key = _PRE_RENAME_FOLDER_TWINS.get(spec.key, spec.key)
        if key not in seen:
            seen.add(key)
            keys.append(key)
    return tuple(keys)


def _file_watcher_required() -> tuple[str, ...]:
    from drydocs_core.orchestration.controlm.description_tokens import required_tokens

    return required_tokens(JobType.FILE_WATCHER)


def select_standard(
    job_type: JobType | None = None,
    *,
    job_role: str | None = None,
    executable: str | None = None,
) -> StandardSelection:
    """The decision tree. ONE function, ONE answer (clause a).

    ``job_type`` is the DERIVED TASKTYPE — the caller resolves the raw
    ``TASK_TYPE`` string into a :class:`JobType` before asking, because that
    derivation is the caller's data question and this module's job is policy.
    ``job_role`` is the registered ``JOB_ROLE`` token value; ``executable`` is
    the launcher token the engine is classified from.

    Note what is NOT a parameter: the grammar version. The DD digit is a
    version, never a selector (guidelines §7.5), and leaving it out of the
    signature is what makes that enforceable rather than merely stated.
    """
    if job_type is JobType.FILE_WATCHER:
        return StandardSelection(
            standard_id=STANDARD_FILE_WATCHER,
            branch="file-watcher",
            required=_file_watcher_required(),
            reason=REASON_FILE_WATCHER,
            job_role=job_role,
        )

    engine: str | None = None
    rule: str | None = None
    if executable:
        itype, rule = classify_executable(executable)
        if itype in ENGINE_STANDARDS:
            engine = itype

    generic = generic_required_tokens()

    if engine is not None:
        ruled = ENGINE_TOKEN_SETS.get(engine)
        return StandardSelection(
            standard_id=ENGINE_STANDARDS[engine],
            branch="engine",
            required=ruled if ruled is not None else generic,
            reason=REASON_ENGINE if ruled is not None else REASON_ENGINE_UNRULED,
            engine=engine,
            classifier_rule=rule,
            job_role=job_role,
            inherited_generic=ruled is None,
        )

    if not job_role:
        return StandardSelection(
            standard_id=STANDARD_GENERIC,
            branch="generic",
            required=generic,
            reason=REASON_UNSELECTABLE,
            classifier_rule=rule,
            unselectable=True,
        )

    return StandardSelection(
        standard_id=STANDARD_GENERIC,
        branch="generic",
        required=generic,
        reason=REASON_NO_EXECUTABLE if not executable else REASON_ENGINE_UNCLASSIFIED,
        classifier_rule=rule,
        job_role=job_role,
    )


@dataclass(frozen=True)
class SelectionCoverage:
    """Adoption, not compliance: the reasons, counted (clause e).

    ``unselectable`` is reported as its own number rather than folded into
    ``generic``, because "we chose the generic standard" and "we could not
    choose at all" are different findings and only the second is a gap.
    """

    total: int
    by_standard: dict[str, int]
    by_reason: dict[str, int]
    unselectable: int
    inherited_generic: int

    @property
    def selectable_ratio(self) -> float:
        return 0.0 if not self.total else (self.total - self.unselectable) / self.total


def selection_coverage(selections: Iterable[StandardSelection]) -> SelectionCoverage:
    """Count the reasons over a population."""
    rows = list(selections)
    return SelectionCoverage(
        total=len(rows),
        by_standard=dict(Counter(s.standard_id for s in rows)),
        by_reason=dict(Counter(s.reason for s in rows)),
        unselectable=sum(1 for s in rows if s.unselectable),
        inherited_generic=sum(1 for s in rows if s.inherited_generic),
    )
