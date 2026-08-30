"""The internal-twin doctor: which variables exist, which are set HERE, which twin documents them (G129).

WHY THIS MODULE EXISTS. The registry said "the real value lives only in the
internal twin" and then stopped. It never said *which* twin file, *which*
variables, or *whether they are set* — so a null ``locator.service`` with a
comment beside it was an empty slot nobody could discover, and the machine-local
tree held roughly twenty directories with no way to tell which one carried which
system's settings. G125 built the enumerable list; this turns it into an answer.

THE THREE VERBS AND WHERE EACH LIVES. Find is here and is read-only. Document is
``scripts/render_env_example.py``, which GENERATES ``.env.example`` from the same
declarations so the two cannot drift again — the gap this closes is measured, not
asserted: the hand-maintained file declared 17 keys while first-party code read
eight more that were declared nowhere at all. Update is
``scripts/set_env_var.py``, a no-echo writer run by a person at a terminal. The
split is deliberate and matches G126: the machine-local tree is READ-mode for the
SYSTEM, and no load path may write it. An operator's hand is not the system, so
the writer is a script rather than a library function anything could call.

NO VALUE IS EVER PRINTED, BY ANY OF THE THREE. This module returns
:class:`VariableStatus` records that carry a NAME, a STATE and the name of
whichever alias answered — never the value, not even a truncated or hashed one. A
doctor that echoes a value is the defect it exists to prevent, so the record has
no field that could hold one, which is a stronger guarantee than a print site
that remembers to mask.

WHY THERE ARE THREE STATES AND NOT TWO. The two machines hold different subsets,
and an untagged report reads as a defect from the other machine (J18). So an
unset variable is only reported as a GAP when something on this machine actually
wants it: it is ``required``, or it belongs to a profile that is PARTIALLY
configured, which is the signature of a half-finished setup rather than of a
carrier this machine simply does not use. Everything else is
``not-applicable-on-this-machine`` — a state, exactly as ADR 0017 clause 7 rules
for the binding verdicts this reuses.

WHAT THIS DOES NOT DO. It does not test side (A). Nothing here asserts a variable
holds a correct host and nothing probes a credential; the check starts at the
registration and reports what is configured, never what is right.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from drydocs_core.env_refs import DECLARED_VARIABLES, EnvVar
from drydocs_core.repo_paths import repo_root
from drydocs_core.source_bindings import ConnectionProfile, load_profiles, venue

_REPO_ROOT = repo_root(Path(__file__).resolve().parent.parent)

#: The machine-local file every variable is ultimately set in. Named as a
#: constant because three surfaces say it and a fourth would eventually say
#: something else.
MACHINE_LOCAL_ENV: Final = ".env"

#: Where a profile's ``twin:`` pointer may point. Declared rather than left to a
#: guard's own string literals: the twin roots are a publish-boundary fact
#: (CLAUDE.md section 3), and a test that spelled them itself would be a second
#: opinion about which trees hold coordinates.
TWIN_ROOTS: Final = ("internal-local/", "internal/")

#: The two channels a variable can arrive through, and they are NOT the same
#: channel. The settings classes declare ``env_file=.env`` (drydocs_core/config.py),
#: so pydantic reads the machine-local file; :func:`drydocs_core.env_refs.expand`
#: reads ``os.environ`` and nothing else. A variable set ONLY in the file is
#: therefore visible to a loader and invisible to a binding check — a divergence
#: this doctor reports rather than papers over, because papering over it would
#: mean choosing which of the two lies to tell. Process wins where both carry a
#: value, which is pydantic's own precedence.
PROCESS: Final = "process"
DOTENV: Final = "dotenv"
CHANNELS: Final = (PROCESS, DOTENV)

#: States. Three, for the reason in the module docstring.
SET: Final = "set"
UNSET: Final = "unset"
NOT_APPLICABLE: Final = "not-applicable-on-this-machine"
STATES: Final = (SET, UNSET, NOT_APPLICABLE)


@dataclass(frozen=True)
class VariableStatus:
    """One declared variable, as it stands on THIS machine.

    There is deliberately no field that could hold a value. ``resolved_via``
    names WHICH of the variable's names answered — the canonical name or a
    deprecated alias — which is the one thing a reader needs that "set" alone
    does not tell them, and it is a name, not a value.
    """

    name: str
    purpose: str
    group: str
    secret: bool
    required: bool
    aliases: tuple[str, ...]
    state: str
    resolved_via: str
    channel: str
    profiles: tuple[str, ...]
    twins: tuple[str, ...]

    @property
    def is_gap(self) -> bool:
        """A variable this machine wants and does not have.

        ``not-applicable`` is never a gap: scoring the other machine's subset red
        is how a report becomes noise, and noise is how the original silence
        survived.
        """
        return self.state == UNSET

    @property
    def via_deprecated_alias(self) -> bool:
        return bool(self.resolved_via) and self.resolved_via != self.name

    @property
    def invisible_to_bindings(self) -> bool:
        """Set in the file, referenced by a profile, and unreachable by the expander.

        The one condition where two honest surfaces disagree: the loader will
        connect and ``landing-zones --check`` will call the binding
        not-configured-here. Naming it is the fix a doctor can make; changing the
        expander to read the file is NOT, because every test that monkeypatches a
        variable to empty would then silently pick up the author's own file.
        """
        return self.channel == DOTENV and bool(self.profiles)


@dataclass(frozen=True)
class EnvReport:
    """Every declared variable, plus the venue that produced the answer."""

    venue: str
    variables: tuple[VariableStatus, ...]
    env_file: str
    env_file_exists: bool

    @property
    def gaps(self) -> tuple[VariableStatus, ...]:
        return tuple(v for v in self.variables if v.is_gap)

    @property
    def is_failure(self) -> bool:
        return bool(self.gaps)

    @property
    def divergent(self) -> tuple[VariableStatus, ...]:
        """Variables a loader can read and a binding check cannot. See the property."""
        return tuple(v for v in self.variables if v.invisible_to_bindings)

    def by_name(self, name: str) -> VariableStatus | None:
        return next((v for v in self.variables if v.name == name), None)


def _profiles_by_variable(
    profiles: tuple[ConnectionProfile, ...],
) -> dict[str, list[ConnectionProfile]]:
    out: dict[str, list[ConnectionProfile]] = {}
    for prof in profiles:
        for name in prof.variables:
            out.setdefault(name, []).append(prof)
    return out


def _partially_configured(profile: ConnectionProfile, dotenv: frozenset[str]) -> bool:
    """Some of this profile's variables resolve here and some do not.

    That is the signature this module treats as a real local gap. A profile with
    NONE of its variables set is a carrier this machine does not use, which is a
    state; a profile with all of them set is configured. Only the middle is
    somebody's half-finished setup, and only the middle is worth a red line.
    """
    names = profile.variables
    if not names:
        return False
    declared = {v.name: v for v in DECLARED_VARIABLES}
    resolved = [
        bool(declared[n].is_set) or bool({declared[n].name, *declared[n].aliases} & dotenv)
        for n in names
        if n in declared
    ]
    return any(resolved) and not all(resolved)


def dotenv_names(path: Path | None = None) -> frozenset[str]:
    """The KEY NAMES carrying a non-empty value in the machine-local file.

    Names only. The value is compared against the empty string and dropped in the
    same expression that read it — nothing in this module ever holds one, which
    is why there is no place a later change could leak one from.

    A deliberately small parser rather than a dotenv dependency: it needs to
    answer "which keys are present", not to reproduce pydantic's quoting rules,
    and a parser that agreed on the hard cases would still be a second opinion
    about a file this module does not own.
    """
    target = path or (_REPO_ROOT / MACHINE_LOCAL_ENV)
    if not target.exists():
        return frozenset()
    found: set[str] = set()
    for line in target.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, raw = stripped.partition("=")
        key = key.removeprefix("export ").strip()
        if key and raw.strip().strip("\"'"):
            found.add(key)
    return frozenset(found)


def _state_for(
    var: EnvVar,
    referencing: list[ConnectionProfile],
    dotenv: frozenset[str],
) -> tuple[str, str, str]:
    """``(state, resolved_via, channel)`` — every one a NAME or a label, never a value.

    Process environment first, then the machine-local file, and aliases in
    declaration order within each. That is pydantic's precedence, so the answer
    here is the answer the settings classes would give.
    """
    import os

    for candidate in (var.name, *var.aliases):
        if os.environ.get(candidate, "").strip():
            return SET, candidate, PROCESS
    for candidate in (var.name, *var.aliases):
        if candidate in dotenv:
            return SET, candidate, DOTENV
    if var.required or any(_partially_configured(p, dotenv) for p in referencing):
        return UNSET, "", ""
    return NOT_APPLICABLE, "", ""


def report(profiles: tuple[ConnectionProfile, ...] | None = None) -> EnvReport:
    """The set-and-unset doctor over :data:`DECLARED_VARIABLES`.

    The variable list is the importable declaration, never a scan of the tree:
    the settings classes compose their names from a pydantic ``env_prefix``, so
    ``NEO4J_URI`` never appears as a literal anywhere and a text search would
    report a clean sweep over a name it cannot see (J37).
    """
    profs = load_profiles() if profiles is None else profiles
    by_var = _profiles_by_variable(profs)
    env_file = _REPO_ROOT / MACHINE_LOCAL_ENV
    dotenv = dotenv_names(env_file)

    statuses: list[VariableStatus] = []
    for var in DECLARED_VARIABLES:
        referencing = by_var.get(var.name, [])
        state, via, channel = _state_for(var, referencing, dotenv)
        twins = tuple(sorted({p.twin for p in referencing if p.twin}))
        statuses.append(
            VariableStatus(
                name=var.name,
                purpose=var.purpose,
                group=var.group,
                secret=var.secret,
                required=var.required,
                aliases=var.aliases,
                state=state,
                resolved_via=via,
                channel=channel,
                profiles=tuple(p.id for p in referencing),
                twins=twins,
            )
        )
    return EnvReport(
        venue=venue(),
        variables=tuple(statuses),
        env_file=MACHINE_LOCAL_ENV,
        env_file_exists=env_file.exists(),
    )
