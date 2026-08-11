"""Failure-pattern / standards-finding detection (Gate 2 — validation).

M0 scope: the ONE mechanized detector — **dot-smuggling** (a variable whose value is
pure punctuation, smuggled through Control-M's concatenation operator), rule id ``R1``
in the rules registry. Detection runs on the core classifier's ``value_is_delimiter``
feature so remediation and the loaders share one truth for the pattern.

G67 adds a second, separate pass: :func:`detect_conformance`, the **greenfield job
standard** rules R2 + R30-R40. It is a distinct entry point rather than more checks
inside :func:`detect_findings` for a contract reason — M0 pins
``detect_findings(modern) == []``, and a conformance pass legitimately has plenty to
say about a minimal transcript. :func:`detect_all` runs both for callers that want
everything.

The registry-driven rules ENGINE (reading statuses out of
``internal/remediation/standards-rules-registry.md``) is still the M1 deliverable.
Findings here stay ``ratified=False`` — WARN-only downstream — until that registry is
machine-readable and its per-rule ratification drives the field; hardcoding those
judgments in public code would leak gate decisions.

TWO FAILURE CLASSES, REPORTED APART. Name drift produces **silence**: the variable
misses the fact registry, no ``STG_APP_FACT`` row is written, and lineage is simply
absent. A value contract breach produces a **confidently wrong row**: the name hits,
so the graph gains a fact whose value is false. The second is worse and is severity
``must-fix``; filing it as a lint warning next to a rename suggestion would bury it.

Cadence note (0002-B §2 step 1): detection is failure-driven (small batches picked
from real failures), not cron.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from drydocs_core.orchestration.controlm import classify_job_variables
from drydocs_core.orchestration.controlm.variables import (
    ADJACENT_REF_RE,
    CANONICAL_FACT_NAMES,
    FACT_REGISTRY,
    KNOWN_SYSTEM_VARIABLES,
    PLAIN_REF_RE,
)

from .formats import DefinitionSet, JobDefinition

#: The M0 detector: registry rule R1 ("No dot-smuggling").
DOT_SMUGGLING_RULE_ID = "R1"


@dataclass(frozen=True)
class Finding:
    """One rule hit on one definition object."""

    rule_id: str  # key into the rules registry (e.g. "R1")
    severity: str  # must-fix | should-fix | advisory (registry vocabulary)
    ratified: bool  # only ratified rules may drive greenfield changes
    target: str  # "<job>:<variable>" the finding is on
    message: str  # human-readable finding, mechanism-only


def detect_findings(definitions: DefinitionSet) -> list[Finding]:
    """Evaluate the M0 detector against every job in ``definitions``."""
    findings: list[Finding] = []
    for job in definitions.jobs:
        for cv in classify_job_variables(job.variables):
            if cv.value_is_delimiter:
                findings.append(
                    Finding(
                        rule_id=DOT_SMUGGLING_RULE_ID,
                        severity="should-fix",
                        ratified=False,  # registry ratification is gate territory (M1)
                        target=f"{job.name}:{cv.name}",
                        message=(
                            "variable value is pure punctuation smuggled through the "
                            "concatenation operator (dot-smuggling); resolve and inline "
                            "the literal instead"
                        ),
                    )
                )
    return findings


# =============================================================================
# G67 — greenfield job standard conformance (R2 + R30-R40)
# =============================================================================

#: Rules this pass implements, in report order. R2 pre-dates G67 and is
#: EXTENDED here (case- and separator-exactness) rather than duplicated.
CONFORMANCE_RULE_IDS = (
    "R2",
    "R30",
    "R31",
    "R32",
    "R33",
    "R34",
    "R35",
    "R36",
    "R37",
    "R38",
    "R39a",
    "R39b",
    "R40",
)

#: Declaration sets the standard requires, by job type. Checked against the
#: WHOLE resolution chain, not job scope — under the scope ladder most of
#: these live on the folder, and demanding them locally would fight the
#: standard this enforces. ETL_PLATFORM_FLAGS is absent on purpose: REQ-4
#: marks it optional.
REQUIRED_DECLARATIONS: dict[str, tuple[str, ...]] = {
    "command": (
        "LAUNCHER_SCRIPT_PATH",
        "ETL_PLATFORM",
        "ETL_ARTIFACT_URI",
        "ETL_ARTIFACT_KIND",
    ),
    "filewatcher": (
        "FILE_DIR",
        "FILE_PREFIX",
        "FILE_BUSINESS_DATE",
        "FILE_EXTENSION",
    ),
}

#: Facts whose carrier the standard rules to be the COMMAND LITERAL, not a
#: variable. pipelineId is generator-owned and immutable per pipeline; a
#: variable makes it hand-editable and lets two copies disagree silently.
#: name -> the command flag that carries it.
LITERAL_CARRIER_FACTS: dict[str, str] = {"PIPELINE_ID": "-pipeline"}

#: File extension -> DistributionRole (file-name component standard §5).
#: Drives the two-clause post-exec rule: TOK/CTL must be cat'd, DAT must not.
DISTRIBUTION_ROLES: dict[str, str] = {
    ".dat": "DAT",
    ".csv": "DAT",
    ".txt": "DAT",
    ".tok": "TOK",
    ".ctl": "CTL",
    ".done": "DONE",
}

#: BMC forbids these in user-defined variable names, plus blanks
#: (external/orchestration/bmc-controlm/controlm-variables.md, authoritative
#: section). The dash is in the set, which is why REQ-1's `DevX-project` and
#: REQ-3's `%%FileWatch-FILE_PATH` are both illegal as user declarations.
FORBIDDEN_NAME_CHARS = frozenset("<>[]{}()=;`~|:?.+-*/&^#@!,\"' \t")

#: ...except as a VENDOR application prefix (`%%` + app abbreviation + `-`,
#: the `%%SAPR3-` form). These namespaces belong to Control-M, so a
#: hand-declared variable inside one is a different finding, not a legal one.
VENDOR_NAME_PREFIXES = ("FileWatch-", "UCM-", "SAPR3-", "OAP-")

#: user-defined variable name length ceiling (the `Name` parameter allows 40;
#: user-defined names are capped at 38)
MAX_USER_NAME_LEN = 38

#: Names that are DECLARED FOR THE RECORD and legitimately referenced by
#: nothing at runtime — the file-name components the SQL parse reads into
#: CM_JOB_FILE_NAME_STANDARD, and the contact/ownership variables extracted
#: later for runbooks. Exempt from the orphan rule: flagging these would fight
#: the standard that requires them. Registered facts (FACT_REGISTRY) are
#: exempt for the same reason and are checked separately, so a name has to be
#: BOTH unregistered and unused before it counts as an orphan.
METADATA_DECLARATIONS = frozenset(
    {
        "FILE_DIR",
        "FILE_PREFIX",
        "FILE_BUSINESS_DATE",
        "FILE_SEQUENCE",
        "FILE_EXTENSION",
        "FILE_COMPRESSION",
        "FILE_SUFFIX",
        "FILE_NAME",
        "FILE_PATTERN",
        "DEVX_KEY",
        "EMAIL_DL_L2",
        "EMAIL_DL_L3",
        "EMAIL_DL_PDN",
    }
)

#: A basename shorter than this is too generic to accuse of duplication —
#: every path ends with '.txt'. R36 is about a whole filename appearing twice.
MIN_RETYPED_BASENAME = 12

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
_SEMVER_RE = re.compile(r"^\d+(\.\d+)*$")
_UUID_ARG_RE = re.compile(
    r"-pipeline\s+([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", re.I
)

#: Value contracts per canonical name. A hit here is the CONFIDENTLY WRONG
#: class: the name resolves, so the graph gains a fact — with a false value.
VALUE_CONTRACTS: dict[str, tuple[re.Pattern[str], str]] = {
    "DS_ID": (_UUID_RE, "a dataset id is a UUID"),
    "DS_VER": (_SEMVER_RE, "a dataset version is dotted-numeric"),
}


def _finding(rule: str, severity: str, target: str, message: str) -> Finding:
    return Finding(
        rule_id=rule,
        severity=severity,
        ratified=False,  # registry ratification is gate territory (M1)
        target=target,
        message=message,
    )


def _strip(name: str) -> str:
    """Variable name without its ``%%`` prefix."""
    return name[2:] if name.startswith("%%") else name


def _refs(text: str | None) -> list[str]:
    """Plain ``%%NAME`` references in ``text``, system variables removed.

    ``%%$ODATE`` and ``%%\\GLOBAL`` / ``%%\\\\POOL\\VAR`` are excluded by the
    core regex itself: the first is a century-format system token, the other
    two are scopes this pass cannot see into and must not accuse.
    """
    if not text:
        return []
    out: list[str] = []
    for name in PLAIN_REF_RE.findall(text):
        upper = name.upper()
        if upper in KNOWN_SYSTEM_VARIABLES or upper.startswith("ODATE"):
            continue
        if name not in out:
            out.append(name)
    return out


def _declared(definitions: DefinitionSet, job: JobDefinition) -> dict[str, str | None]:
    """Every name visible to ``job``, narrowest scope winning — the BMC
    resolution order (local, then SMART folder, then global)."""
    visible: dict[str, str | None] = {}
    for _scope, _container, defs in definitions.resolution_chain(job):
        for name, value in defs:
            visible[_strip(name)] = value
    return visible


def _reference_sites(job: JobDefinition) -> list[tuple[str, str]]:
    """(label, text) pairs on a job that may carry ``%%`` references."""
    sites = [
        ("command_line", job.command_line),
        ("watch_template", job.watch_template or ""),
        ("post_command", job.post_command),
    ]
    return [(label, text) for label, text in sites if text]


def _distribution_role(declared: dict[str, str | None], job: JobDefinition) -> str | None:
    """DistributionRole for a watcher, from FILE_EXTENSION if declared, else
    from the tail of the watch template. ``None`` when neither says."""
    extension = declared.get("FILE_EXTENSION")
    if extension:
        role = DISTRIBUTION_ROLES.get(extension.strip().lower())
        if role:
            return role
    template = (job.watch_template or "").strip().lower()
    for suffix, role in DISTRIBUTION_ROLES.items():
        if template.endswith(suffix):
            return role
    return None


def _is_watcher(job: JobDefinition) -> bool:
    return (job.job_type or "").strip().lower() in {"filewatch", "filewatcher", "detached"}


def _is_command(job: JobDefinition) -> bool:
    return (job.job_type or "").strip().lower() in {"command", "os", "cmd"}


def detect_conformance(definitions: DefinitionSet) -> list[Finding]:
    """Evaluate the greenfield job standard (R2 + R30-R40) over a whole set.

    Whole-SET, not per-job: three of the rules are cross-job by nature —
    hoistable invariants, retyped composed paths, and the name-drift census
    only mean anything with the siblings in view.
    """
    findings: list[Finding] = []
    findings.extend(_check_names(definitions))
    findings.extend(_check_references(definitions))
    findings.extend(_check_required(definitions))
    findings.extend(_check_carriers(definitions))
    findings.extend(_check_values(definitions))
    findings.extend(_check_hoistable(definitions))
    findings.extend(_check_retyped_paths(definitions))
    findings.extend(_check_post_exec(definitions))
    findings.extend(_check_notifications(definitions))
    return _deduped(findings)


def _deduped(findings: list[Finding]) -> list[Finding]:
    """One report per distinct finding. A folder-scope defect is visible from
    every job that resolves through it, and saying so twelve times would bury
    the eleven other things wrong with the folder."""
    seen: set[tuple[str, str, str]] = set()
    out: list[Finding] = []
    for finding in findings:
        key = (finding.rule_id, finding.target, finding.message)
        if key in seen:
            continue
        seen.add(key)
        out.append(finding)
    return out


def detect_all(definitions: DefinitionSet) -> list[Finding]:
    """The M0 failure-pattern detector plus the conformance pass."""
    return detect_findings(definitions) + detect_conformance(definitions)


def _all_declarations(definitions: DefinitionSet):
    """(target, name, value) for every declaration anywhere in the set."""
    for folder in definitions.folders:
        for name, value in folder.variables:
            yield f"{folder.name}:{_strip(name)}", _strip(name), value
    for job in definitions.jobs:
        for name, value in job.variables:
            yield f"{job.name}:{_strip(name)}", _strip(name), value


# -- R2 (extended) + R37 + R38: the name rules ---------------------------------------


def _check_names(definitions: DefinitionSet) -> list[Finding]:
    findings: list[Finding] = []
    for target, name, value in _all_declarations(definitions):
        findings.extend(_name_drift(target, name))
        findings.extend(_charset(target, name))
        if value and ADJACENT_REF_RE.search(value):
            findings.append(
                _finding(
                    "R37",
                    "should-fix",
                    target,
                    "value places two %% references side by side, which Control-M may "
                    "read as one composed variable NAME; separate them with the "
                    "concatenation delimiter",
                )
            )
    for job in definitions.jobs:
        for label, text in _reference_sites(job):
            if ADJACENT_REF_RE.search(text):
                findings.append(
                    _finding(
                        "R37",
                        "should-fix",
                        f"{job.name}:{label}",
                        f"{label} places two %% references side by side — ambiguous by "
                        "construction; use the concatenation delimiter",
                    )
                )
    return findings


def _name_drift(target: str, name: str) -> list[Finding]:
    """R2 — canonicalization. Reports the SILENCE class: a drifted name misses
    the fact registry entirely, so no row is written and lineage is absent."""
    if name in FACT_REGISTRY:
        canonical = CANONICAL_FACT_NAMES.get(FACT_REGISTRY[name])
        if canonical and canonical != name:
            return [
                _finding(
                    "R2",
                    "advisory",
                    target,
                    f"registered ALIAS of {canonical}; materializes with a rename WARN, "
                    f"canonical is WARN-free",
                )
            ]
        return []
    for candidate, how in (
        (name.upper(), "case"),
        (name.replace("_", "").upper(), "separator"),
    ):
        if candidate in FACT_REGISTRY:
            return [
                _finding(
                    "R2",
                    "should-fix",
                    target,
                    f"{how} drift from canonical {candidate}; registry lookup is exact, "
                    f"so this name produces NO fact row at all — the lineage is missing, "
                    f"not wrong",
                )
            ]
    return []


def _charset(target: str, name: str) -> list[Finding]:
    """R38 — vendor legality of a user-defined name."""
    findings: list[Finding] = []
    vendor_prefix = next((p for p in VENDOR_NAME_PREFIXES if name.startswith(p)), None)
    if vendor_prefix:
        return [
            _finding(
                "R38",
                "must-fix",
                target,
                f"declares a variable inside the vendor plugin namespace "
                f"'{vendor_prefix}' — that prefix form belongs to Control-M, and a "
                f"hand-declared user variable may not carry it",
            )
        ]
    bad = sorted(FORBIDDEN_NAME_CHARS.intersection(name))
    if bad:
        findings.append(
            _finding(
                "R38",
                "must-fix",
                target,
                f"name contains {bad!r}, forbidden by the vendor in user-defined "
                f"variable names",
            )
        )
    if len(name) > MAX_USER_NAME_LEN:
        findings.append(
            _finding(
                "R38",
                "must-fix",
                target,
                f"name is {len(name)} chars; user-defined names are capped at "
                f"{MAX_USER_NAME_LEN}",
            )
        )
    return findings


# -- R30 + R31: references and orphans ------------------------------------------------


def _check_references(definitions: DefinitionSet) -> list[Finding]:
    findings: list[Finding] = []
    for job in definitions.jobs:
        declared = _declared(definitions, job)
        used: set[str] = set()
        for label, text in _reference_sites(job):
            for ref in _refs(text):
                used.add(ref)
                if ref not in declared:
                    findings.append(
                        _finding(
                            "R30",
                            "must-fix",
                            f"{job.name}:{label}",
                            f"references %%{ref}, declared at no scope in the chain; "
                            f"Control-M resolves an undefined reference to the reserved "
                            f"word CTMERR, so this reaches the agent as literal text",
                        )
                    )
        for _name, value in job.variables:
            used.update(_refs(value))
        # A derivation can break at ANY scope, and a broken folder-scope value
        # is only visible from a job that resolves through it — so walk the
        # whole chain. Duplicate reports across siblings collapse in _deduped.
        for scope, container, defs in definitions.resolution_chain(job):
            for name, value in defs:
                for ref in _refs(value):
                    if ref not in declared:
                        findings.append(
                            _finding(
                                "R30",
                                "must-fix",
                                f"{container or scope}:{_strip(name)}",
                                f"value references %%{ref}, declared at no scope in the "
                                f"chain (resolves to CTMERR)",
                            )
                        )
        for name, _value in job.variables:
            bare = _strip(name)
            if bare in used or bare in FACT_REGISTRY or bare in METADATA_DECLARATIONS:
                continue  # a fact declared for the record is not an orphan
            findings.append(
                _finding(
                    "R31",
                    "advisory",
                    f"{job.name}:{bare}",
                    "declared on the job, referenced nowhere on it, and not a registered "
                    "fact or a standard metadata field — either wire it up or drop it; an "
                    "orphan is a claim the job does not make",
                )
            )
    return findings


# -- R32: the required declaration set ------------------------------------------------


def _check_required(definitions: DefinitionSet) -> list[Finding]:
    findings: list[Finding] = []
    for job in definitions.jobs:
        if _is_command(job):
            required = REQUIRED_DECLARATIONS["command"]
        elif _is_watcher(job):
            required = REQUIRED_DECLARATIONS["filewatcher"]
        else:
            continue
        declared = _declared(definitions, job)
        for name in required:
            if name not in declared:
                findings.append(
                    _finding(
                        "R32",
                        "should-fix",
                        f"{job.name}:{name}",
                        f"the standard requires {name} on every {job.job_type} job, at "
                        f"some scope in the chain; it is declared at none",
                    )
                )
    return findings


# -- R33: exactly one carrier per fact -------------------------------------------------


def _check_carriers(definitions: DefinitionSet) -> list[Finding]:
    findings: list[Finding] = []
    for job in definitions.jobs:
        if not job.command_line:
            continue
        declared = _declared(definitions, job)
        for name, flag in LITERAL_CARRIER_FACTS.items():
            literal = _UUID_ARG_RE.search(job.command_line) if flag == "-pipeline" else None
            if literal and name in declared:
                findings.append(
                    _finding(
                        "R33",
                        "should-fix",
                        f"{job.name}:{name}",
                        f"the command carries {flag} as a literal AND {name} is declared "
                        f"— two carriers for one fact. The standard rules the literal the "
                        f"carrier (generator-owned, immutable per pipeline); remove the "
                        f"variable, which can drift out of agreement while the command wins",
                    )
                )
    return findings


# -- R34: value contracts (the CONFIDENTLY WRONG class) --------------------------------


def _check_values(definitions: DefinitionSet) -> list[Finding]:
    findings: list[Finding] = []
    for target, name, value in _all_declarations(definitions):
        if not value:
            continue
        contract = VALUE_CONTRACTS.get(name)
        if contract and not contract[0].match(value.strip()):
            pattern_desc = contract[1]
            findings.append(
                _finding(
                    "R34",
                    "must-fix",
                    target,
                    f"value does not satisfy the contract for {name} ({pattern_desc}). "
                    f"The NAME resolves, so this writes a fact row with a false value — "
                    f"a wrong row, not a missing one. Check for a swap with a sibling",
                )
            )
    return findings


# -- R35: hoistable invariants ----------------------------------------------------------


def _check_hoistable(definitions: DefinitionSet) -> list[Finding]:
    """A (name, value) pair repeated at JOB scope across siblings belongs at
    the widest scope that holds it. This is the defect CLASS behind the live
    folder's drift: ~17 variables hand-copied per job, one of them mistyped."""
    seen: dict[tuple[str, str | None], list[str]] = {}
    for job in definitions.jobs:
        for name, value in job.variables:
            seen.setdefault((_strip(name), value), []).append(job.name)
    findings: list[Finding] = []
    for (name, _value), jobs in sorted(seen.items()):
        if len(jobs) > 1:
            findings.append(
                _finding(
                    "R35",
                    "advisory",
                    f"{jobs[0]}:{name}",
                    f"declared identically at JOB scope on {len(jobs)} jobs; hoist to the "
                    f"widest scope that holds it so there is one copy to maintain",
                )
            )
    return findings


# -- R36: the same file composed twice --------------------------------------------------


def _check_retyped_paths(definitions: DefinitionSet) -> list[Finding]:
    """Two declarations where one value is a proper suffix of the other are
    the same file written as a path and as a basename — the shape that let
    DAT_FILE and DAT_FILE_NM drift apart. Derive one from the other instead."""
    declarations = [
        (target, name, value.strip())
        for target, name, value in _all_declarations(definitions)
        if value and value.strip()
    ]
    findings: list[Finding] = []
    for target, _name, value in declarations:
        if "/" not in value:
            continue  # only a full path can CONTAIN a basename
        for other_target, other_name, other_value in declarations:
            if other_target == target or "/" in other_value:
                continue  # comparing two paths says nothing about duplication
            if len(other_value) < MIN_RETYPED_BASENAME or not value.endswith(other_value):
                continue
            findings.append(
                _finding(
                    "R36",
                    "should-fix",
                    target,
                    f"this path ends with the whole value of {other_name}: the same file "
                    f"is written twice, as a path and as a basename, and the two can drift "
                    f"apart. Declare the components once and DERIVE the composed handle, "
                    f"so there is one place to change",
                )
            )
            break
    return findings


# -- R39a / R39b: the two-clause post-exec cat rule --------------------------------------


def _check_post_exec(definitions: DefinitionSet) -> list[Finding]:
    findings: list[Finding] = []
    for job in definitions.jobs:
        if not _is_watcher(job):
            continue
        declared = _declared(definitions, job)
        role = _distribution_role(declared, job)
        watch = (job.watch_template or "").strip()
        post = job.post_command.strip()
        if role in {"TOK", "CTL"}:
            if post != f"cat {watch}" or not watch:
                findings.append(
                    _finding(
                        "R39a",
                        "should-fix",
                        f"{job.name}:post_command",
                        f"a {role} watcher must cat the file it watched, using the SAME "
                        f"expression, so the file detected is the file echoed; expected "
                        f"'cat <watch path>', found {post or '(none)'!r}",
                    )
                )
        elif role == "DAT" and post.startswith("cat "):
            findings.append(
                _finding(
                    "R39b",
                    "must-fix",
                    f"{job.name}:post_command",
                    "cats a DAT file. Data files can be multi-GB; echoing one into sysout "
                    "floods the log and can breach sysout limits. The cat belongs on the "
                    "TOK/CTL watcher, which is where the declared record count lives",
                )
            )
    return findings


# -- R40: notification removal (REQ-2, extended to DOMAIL 2026-08-11) ---------------------


def _check_notifications(definitions: DefinitionSet) -> list[Finding]:
    """Generated notification is removed outright: the ServiceNow incident the
    failure raises is the call to action, so a shout or a mail is a second,
    weaker signal nobody acts on.

    DOMAIL is flagged alongside the shouts as of the SME ruling 2026-08-11.
    REQ-2 originally left it out of scope; the ruling extends REQ-2 rather than
    reinterpreting it, so the whole ``ON``/``DOMAIL`` block goes. The unresolved
    destination that block references (``%%NOTIFY``, ``%%EMAIL_GRP``, or
    whatever a given job spells it) is deleted WITH the block — never declared
    to make it resolve. That repair would re-wire the mechanism being removed,
    so no detector here proposes it.
    """
    findings: list[Finding] = []
    banned = {"SHOUT", "DOSHOUT", "DOMAIL"}
    for folder in definitions.folders:
        present = sorted(banned.intersection(folder.notification_tags))
        if present:
            findings.append(
                _finding(
                    "R40",
                    "should-fix",
                    f"{folder.name}:notifications",
                    f"emits {', '.join(present)}; the standard requires zero of these "
                    f"— the incident is the call to action, not the mail",
                )
            )
    for job in definitions.jobs:
        present = sorted(banned.intersection(job.notification_tags))
        if present:
            findings.append(
                _finding(
                    "R40",
                    "should-fix",
                    f"{job.name}:notifications",
                    f"emits {', '.join(present)}; the standard requires zero of these "
                    f"— delete the block, do not declare its destination",
                )
            )
    return findings
