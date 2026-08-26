"""Folder-set PROFILE over a staged Control-M definition set (G68).

WHAT THIS IS FOR, and why it is not a report. The SME is assumed to KNOW the
process. What they cannot see is what the export actually SAYS — which FIDs are
in play, which variable names really exist and at what scope, which contacts are
carried, which wrapper scripts twenty jobs share. Show them that, and they can
supply the DEVX_KEY, the MFTS routes and the contacts that get substituted in.
That division — **the machine reports what IS, the SME supplies what is NOT
THERE** — is what keeps this out of the guessing that produced the drift C32
documents.

So the output has two halves:

* four censuses plus an invocation census, every one of them carrying
  WHERE-USED rather than bare distinct values, because the SME's next question
  is always *which jobs*; and
* a SUBSTITUTION SLOT list — the facts the export does not carry and only a
  human can supply. A slot with no current value is ``not-supplied``, NEVER a
  default. Inventing one is how a proposal becomes a wrong fact nobody
  re-checks.

THE PROFILE ASSERTS NOTHING ABOUT MEANING. It is a census; findings stay
:func:`drydocs_remediation.detect.detect_all`'s output and ride alongside. It
ratifies nothing, writes no graph and no file (the caller owns the artifact),
and it reads a :class:`~drydocs_remediation.formats.DefinitionSet` — so it runs
on anything ``xml_bridge`` already stages and adds NO new parser.

Feeds the Excel runbook rather than competing with it: the
``controlm-runbook-automation-excel`` skill consumes these same facts.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any

from drydocs_core.orchestration.controlm import parse_command
from drydocs_core.orchestration.controlm.variables import (
    KNOWN_SYSTEM_VARIABLES,
    PLAIN_REF_RE,
)

from .detect import detect_all
from .formats import DefinitionSet, JobDefinition

#: job-type buckets the shape census counts by. "other" is deliberate and
#: reported: an unbucketed type is a fact about the folder set, not a gap in
#: this list, and silently folding it into a neighbour would hide it.
_WATCHER_TYPES = ("filewatcher", "file_watcher", "file watcher")
_PLACEMENT_HINT = "PLCT"
_TRUST_HINT = "TRUST"

#: identity facts the census reports, in report order. Every one is read from
#: the DECLARED variables (the scope chain), never inferred from a name — the
#: 2,384-variable gap analysis' durable finding is that names lie, and a census
#: that guessed would be worse than one that reports a blank.
_IDENTITY_FACTS = ("FID", "SEAL")

#: contact variables, and WHICH KIND each is. The shared EMAIL_DL_ prefix hides
#: two different audiences (guidelines §7.3): L2/L3 are internal SUPPORT tiers,
#: PDN is downstream BUSINESS USERS on a Production Delay Notification. The
#: page says MUST NOT collapse them, so the census does not.
_CONTACT_KINDS = {
    "EMAIL_DL_L2": "support-tier",
    "EMAIL_DL_L3": "support-tier",
    "EMAIL_DL_PDN": "delay-notification-consumer",
}

#: the mail-destination spellings observed in the estate (R40's own note). They
#: are censused as DOMAIL destinations, not as contacts: R40 deletes the block
#: that would have used them.
_DOMAIL_DESTINATION_NAMES = ("NOTIFY", "EMAIL_GRP", "EMAIL_GRP_S")

#: the closed slot list, each with the rule the guidelines page states for it.
#: SHAPE RULES ARE QUOTED FROM THE PAGE, not invented here — a slot whose rule
#: this module made up would be a standard nobody ratified.
_SLOT_RULES: tuple[tuple[str, str, str], ...] = (
    (
        "DEVX_KEY",
        "folder",
        "the DevX project key; hyphens are illegal in a Control-M name, "
        "so `DevX-project` becomes DEVX_KEY (guidelines §5.3)",
    ),
    (
        "DELIVERY_MECHANISM",
        "watcher-description",
        "one of MFTS_AGENT | SFTP_DIRECT | API_GENERATED (guidelines §7.1)",
    ),
    ("USER", "watcher-description", "the transfer service account (guidelines §7.1)"),
    (
        "FTS_ID",
        "watcher-description",
        "the BARE File Transfer id, shape ^FTS[A-Z]*[0-9]+$ — drop version fragments "
        "(`ST 6.0 - FTS2` is FTS2). Open but governed vocabulary, so a shape and not a "
        "closed list (guidelines §7.1)",
    ),
    (
        "REC_ID",
        "watcher-description",
        "source-system reference id(s), comma-separated (guidelines §7.1)",
    ),
    (
        "SOURCE_CONTACT",
        "watcher-description",
        "who owns the file at the ORIGINATING system; whether it must be a DL rather than "
        "a named individual is an OPEN question on the page (§7.1, open list)",
    ),
    (
        "EMAIL_DL_L2",
        "folder",
        "internal support tier 2. A FOLDER variable, documentation-only — MUST NOT be bound "
        "to a DOMAIL destination (guidelines §7.3)",
    ),
    (
        "EMAIL_DL_L3",
        "folder",
        "internal support tier 3. Same folder-scope, documentation-only rule (guidelines §7.3)",
    ),
    (
        "EMAIL_DL_PDN",
        "folder",
        "downstream BUSINESS USERS for Production Delay Notification — a different audience "
        "from L2/L3, and MUST NOT be collapsed with them (guidelines §7.3)",
    ),
)

#: what a slot with no value in the export says. A single spelling, used
#: everywhere, so "the SME has not supplied this" can never be confused with
#: "the export carried an empty string".
NOT_SUPPLIED = "not-supplied"


def _strip(name: str) -> str:
    return name[2:] if name.startswith("%%") else name


def _refs(text: str | None) -> list[str]:
    """Plain ``%%NAME`` references, system tokens removed — the same reading
    :mod:`.detect` uses, so the census and the defect list agree about what a
    reference IS."""
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


def _job_type(job: JobDefinition) -> str:
    """The shape census bucket for one job."""
    task = (job.job_type or "").strip().lower()
    if task in _WATCHER_TYPES:
        return "file-watcher"
    upper = job.name.upper()
    if _PLACEMENT_HINT in upper:
        return "placement"
    if _TRUST_HINT in upper:
        return "trust"
    return "other"


def _reference_sites(job: JobDefinition) -> list[tuple[str, str]]:
    sites = [
        ("command_line", job.command_line),
        ("watch_template", job.watch_template or ""),
        ("post_command", job.post_command),
    ]
    return [(label, text) for label, text in sites if text]


def _visible(definitions: DefinitionSet, job: JobDefinition) -> dict[str, str | None]:
    """Every name visible to ``job``, narrowest scope winning."""
    visible: dict[str, str | None] = {}
    for _scope, _container, defs in definitions.resolution_chain(job):
        for name, value in defs:
            visible[_strip(name)] = value
    return visible


# =============================================================================
# the censuses
# =============================================================================


@dataclass
class ShapeCensus:
    """(a) What is in the set: containers, job counts by type, datasets."""

    data_centers: list[str] = field(default_factory=list)
    folders: list[str] = field(default_factory=list)
    subfolders: list[str] = field(default_factory=list)
    jobs: int = 0
    jobs_by_type: dict[str, int] = field(default_factory=dict)
    #: datasets INFERRED from the sub-folder ladder — the standard puts dataset
    #: identity on the sub-folder, so the ladder is where they read from. Named
    #: "inferred" because that is what it is: a reading of the shape, not a
    #: declared fact, and the SME can correct it.
    datasets_inferred: list[str] = field(default_factory=list)


@dataclass
class IdentityRow:
    """One identity value and the jobs carrying it."""

    fact: str  # FID | SEAL | RUN_AS | APPLICATION
    value: str
    jobs: list[str] = field(default_factory=list)
    #: RUN_AS only — the job types this account appears on. THE 2026-08-19 SME
    #: EVIDENCE: a FileWatcher on the Control-M platform account beside a
    #: payload job on the application account is the DESIGNED pattern; a flat
    #: distinct list blurs that into "two accounts" and loses the finding.
    job_types: list[str] = field(default_factory=list)


@dataclass
class VariableRow:
    """(c) One declared name, with its state inline.

    The census and the defect list are ONE table here, not two the reader has to
    join by hand: `unreferenced` is R31's question and `unresolved_refs` is
    R30's, both answered on the row that names the variable.
    """

    name: str
    scope: str  # FOLDER | SUBFOLDER | JOB
    containers: list[str] = field(default_factory=list)
    distinct_values: int = 0
    reference_count: int = 0
    #: R31 state: declared at job scope and referenced nowhere on that job
    unreferenced: bool = False
    #: R30 state: referenced somewhere but declared nowhere in the chain
    unresolved: bool = False


@dataclass
class ContactRow:
    """(d) One contact value found. Always documentation-only."""

    name: str
    value: str
    kind: str  # support-tier | delay-notification-consumer | domail-destination
    containers: list[str] = field(default_factory=list)
    #: R40 deletes the block that would have used a DOMAIL destination, so
    #: EVERY row here is documentation, never a wiring instruction.
    documentation_only: bool = True


@dataclass
class InvocationRow:
    """(e) One invoked script path, with its fan-out and what varies under it.

    WHY FAN-OUT IS THE MEASUREMENT. On the Informatica platform the invoked
    .ksh wrappers are the same generic few for ALL business applications (SME
    2026-08-19), so script-path identity distinguishes nothing there — and the
    G12 wrapper-payload family (Ab Initio / DPL: kind-scoped token, path never
    identity) likely needs a third kind. WHICH parameter is the token is a
    LINEAGE-GATE ruling; this census informs it and never makes it.

    A wrapper with fan-out 1 is reported TOO: one-to-one wrappers are the
    evidence that path identity IS sufficient for that kind, which is as
    decision-relevant as the converse.
    """

    target: str
    invocation_type: str
    fan_out: int = 0
    jobs: list[str] = field(default_factory=list)
    #: names referenced in the sharing jobs' command lines whose VALUES differ
    #: across those jobs — the identity-grade candidates
    varying_variables: list[str] = field(default_factory=list)
    #: names referenced by every sharing job that resolve to the SAME value —
    #: reported because "constant across the fan-out" rules a candidate OUT
    constant_variables: list[str] = field(default_factory=list)


@dataclass
class SubstitutionSlot:
    """A fact the export does not carry and only the SME can supply."""

    name: str
    home: str  # folder | watcher-description
    rule: str  # the vocabulary / shape rule, quoted from the guidelines page
    status: str  # "present" | NOT_SUPPLIED
    #: the current value, or None. NEVER "" and never a placeholder: a slot with
    #: no value must be structurally distinguishable from one carrying a blank.
    value: str | None = None
    applies_to: list[str] = field(default_factory=list)


@dataclass
class FolderSetProfile:
    """The whole census. JSON-serializable via :meth:`as_dict`."""

    source: str
    shape: ShapeCensus
    identity: list[IdentityRow]
    variables: list[VariableRow]
    contacts: list[ContactRow]
    invocations: list[InvocationRow]
    substitution_slots: list[SubstitutionSlot]
    #: detect_all()'s findings RIDE ALONGSIDE — the profile asserts nothing
    #: about meaning, so the defect list stays the detector's output and is
    #: carried, not restated.
    findings: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def summary(self) -> str:
        slots_open = sum(1 for s in self.substitution_slots if s.status == NOT_SUPPLIED)
        shared = sum(1 for i in self.invocations if i.fan_out > 1)
        return (
            f"folders={len(self.shape.folders)} subfolders={len(self.shape.subfolders)} "
            f"jobs={self.shape.jobs} | identity={len(self.identity)} "
            f"variables={len(self.variables)} contacts={len(self.contacts)} | "
            f"wrappers={len(self.invocations)} (shared={shared}) | "
            f"slots: {slots_open}/{len(self.substitution_slots)} not-supplied | "
            f"findings={len(self.findings)}"
        )


# =============================================================================


def profile(definitions: DefinitionSet) -> FolderSetProfile:
    """Census one staged folder set. PURE — reads only, writes nothing."""
    return FolderSetProfile(
        source=definitions.source or "",
        shape=_shape(definitions),
        identity=_identity(definitions),
        variables=_variables(definitions),
        contacts=_contacts(definitions),
        invocations=_invocations(definitions),
        substitution_slots=_slots(definitions),
        findings=[asdict(f) for f in detect_all(definitions)],
    )


def _shape(definitions: DefinitionSet) -> ShapeCensus:
    census = ShapeCensus(jobs=len(definitions.jobs))
    for folder in definitions.folders:
        bucket = census.folders if folder.scope == "FOLDER" else census.subfolders
        if folder.name not in bucket:
            bucket.append(folder.name)
        if folder.data_center and folder.data_center not in census.data_centers:
            census.data_centers.append(folder.data_center)
    counts: Counter[str] = Counter(_job_type(job) for job in definitions.jobs)
    census.jobs_by_type = dict(sorted(counts.items()))
    # the sub-folder ladder is where the standard puts dataset identity, so the
    # leaf of each ladder is the dataset READING — labelled inferred, not fact
    for name in census.subfolders:
        leaf = name.rsplit("/", 1)[-1]
        if leaf and leaf not in census.datasets_inferred:
            census.datasets_inferred.append(leaf)
    return census


def _identity(definitions: DefinitionSet) -> list[IdentityRow]:
    """(b) Distinct identity values WITH the jobs carrying each."""
    rows: dict[tuple[str, str], IdentityRow] = {}

    def _row(fact: str, value: str) -> IdentityRow:
        key = (fact, value)
        if key not in rows:
            rows[key] = IdentityRow(fact=fact, value=value)
        return rows[key]

    for job in definitions.jobs:
        visible = _visible(definitions, job)
        for fact in _IDENTITY_FACTS:
            value = (visible.get(fact) or "").strip()
            if value:
                _row(fact, value).jobs.append(job.name)
        if job.run_as:
            row = _row("RUN_AS", job.run_as)
            row.jobs.append(job.name)
            job_type = _job_type(job)
            if job_type not in row.job_types:
                row.job_types.append(job_type)
        if job.application:
            _row("APPLICATION", job.application).jobs.append(job.name)
    return [rows[key] for key in sorted(rows)]


def _variables(definitions: DefinitionSet) -> list[VariableRow]:
    """(c) Every declared name by scope, with its R30/R31 state inline."""
    rows: dict[tuple[str, str], VariableRow] = {}
    values: dict[tuple[str, str], set[str]] = {}

    def _row(name: str, scope: str) -> VariableRow:
        key = (name, scope)
        if key not in rows:
            rows[key] = VariableRow(name=name, scope=scope)
            values[key] = set()
        return rows[key]

    for folder in definitions.folders:
        for raw_name, value in folder.variables:
            key = (_strip(raw_name), folder.scope)
            row = _row(*key)
            if folder.name not in row.containers:
                row.containers.append(folder.name)
            values[key].add(value or "")
    for job in definitions.jobs:
        for raw_name, value in job.variables:
            key = (_strip(raw_name), "JOB")
            row = _row(*key)
            if job.name not in row.containers:
                row.containers.append(job.name)
            values[key].add(value or "")

    # reference counts and the two defect states, read the way detect.py reads
    # them so the census cannot disagree with the finding list beside it
    for job in definitions.jobs:
        visible = _visible(definitions, job)
        referenced: set[str] = set()
        for _label, text in _reference_sites(job):
            referenced.update(_refs(text))
        for _name, value in job.variables:
            referenced.update(_refs(value))
        for name in referenced:
            for scope in ("JOB", "SUBFOLDER", "FOLDER"):
                if (name, scope) in rows:
                    rows[(name, scope)].reference_count += 1
                    break
            else:
                if name not in visible:
                    row = _row(name, "UNDECLARED")
                    row.unresolved = True
                    row.reference_count += 1
        for raw_name, _value in job.variables:
            name = _strip(raw_name)
            if name not in referenced and (name, "JOB") in rows:
                rows[(name, "JOB")].unreferenced = True

    for key, row in rows.items():
        row.distinct_values = len(values.get(key, ()))
    return [rows[key] for key in sorted(rows)]


def _contacts(definitions: DefinitionSet) -> list[ContactRow]:
    """(d) Contacts and mail destinations, split by kind, documentation-only."""
    rows: dict[tuple[str, str], ContactRow] = {}

    def _add(name: str, value: str, kind: str, container: str) -> None:
        key = (name, value)
        row = rows.setdefault(key, ContactRow(name=name, value=value, kind=kind))
        if container not in row.containers:
            row.containers.append(container)

    for folder in definitions.folders:
        for raw_name, value in folder.variables:
            name, val = _strip(raw_name), (value or "").strip()
            if not val:
                continue
            if name in _CONTACT_KINDS:
                _add(name, val, _CONTACT_KINDS[name], folder.name)
            elif name in _DOMAIL_DESTINATION_NAMES:
                _add(name, val, "domail-destination", folder.name)
    for job in definitions.jobs:
        for raw_name, value in job.variables:
            name, val = _strip(raw_name), (value or "").strip()
            if not val:
                continue
            if name in _CONTACT_KINDS:
                _add(name, val, _CONTACT_KINDS[name], job.name)
            elif name in _DOMAIL_DESTINATION_NAMES:
                _add(name, val, "domail-destination", job.name)
    return [rows[key] for key in sorted(rows)]


def _invocations(definitions: DefinitionSet) -> list[InvocationRow]:
    """(e) Wrapper fan-out, and what varies underneath a shared wrapper."""
    rows: dict[str, InvocationRow] = {}
    refs_by_target: dict[str, list[tuple[str, dict[str, str | None]]]] = {}

    for job in definitions.jobs:
        if not job.command_line:
            continue
        visible = _visible(definitions, job)
        for inv in parse_command(job.command_line).invocations:
            target = inv.target
            if not target:
                continue
            row = rows.get(target)
            if row is None:
                row = InvocationRow(target=target, invocation_type=inv.invocation_type.lower())
                rows[target] = row
                refs_by_target[target] = []
            if job.name not in row.jobs:
                row.jobs.append(job.name)
                row.fan_out = len(row.jobs)
            refs_by_target[target].append((job.name, visible))

    for target, row in rows.items():
        names: list[str] = []
        for job in definitions.jobs:
            if job.name in row.jobs:
                for name in _refs(job.command_line):
                    if name not in names:
                        names.append(name)
        for name in names:
            seen = {(visible.get(name) or "") for _job_name, visible in refs_by_target[target]}
            if len(seen) > 1:
                row.varying_variables.append(name)
            else:
                row.constant_variables.append(name)
    return [rows[key] for key in sorted(rows)]


def _slots(definitions: DefinitionSet) -> list[SubstitutionSlot]:
    """The half the census cannot produce: what only the SME can supply."""
    slots: list[SubstitutionSlot] = []
    folder_values: dict[str, str] = {}
    for folder in definitions.folders:
        for raw_name, value in folder.variables:
            val = (value or "").strip()
            if val:
                folder_values.setdefault(_strip(raw_name), val)

    watcher_jobs = [j.name for j in definitions.jobs if _job_type(j) == "file-watcher"]
    all_jobs = [j.name for j in definitions.jobs]

    for name, home, rule in _SLOT_RULES:
        value = folder_values.get(name)
        if value is None:
            # description-borne slots may also be declared as variables
            for job in definitions.jobs:
                for raw_name, raw_value in job.variables:
                    if _strip(raw_name) == name and (raw_value or "").strip():
                        value = raw_value.strip()
                        break
                if value:
                    break
        slots.append(
            SubstitutionSlot(
                name=name,
                home=home,
                rule=rule,
                # NEVER a default: absent is its own status, and `value` stays
                # None rather than "" so a blank in the export cannot be read
                # as "the SME supplied an empty value"
                status="present" if value else NOT_SUPPLIED,
                value=value,
                applies_to=watcher_jobs if home == "watcher-description" else all_jobs,
            )
        )
    return slots
