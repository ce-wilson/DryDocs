"""Offline equivalence proof — greenfield must re-derive legacy's resolved behavior.

Both sides resolve through ``drydocs_core.orchestration.controlm.resolve_job`` (the same engine the
loaders trust), so the comparison is apples-to-apples: each job's watch template AND
command line are resolved under its scope and the *resolved* strings are diffed —
cosmetic definition differences are fine, behavioral differences fail the proof. Jobs
are paired BY ORDER (legacy[i] vs greenfield[i]): a remediation unit is a deliberate
legacy→greenfield pairing, and names legitimately differ across the pair.

THE VERDICT IS THREE-VALUED (defect B′, found by the 2026-08-12 POC). The original
report collapsed "compared and equal" and "nothing to compare" into ``equivalent=True``:
``resolved_watch`` returns ``None`` for a job with no watch template, command jobs
compared ``None == None``, and a run that broke six CMDLINEs reported PASS 12/12. Now
every job lands in exactly one bucket — **proven** (at least one surface compared, all
equal), **diverged** (a compared surface differs), or **not proven** (no comparable
surface), and ``equivalent=True`` requires every job proven: no evidence is never
evidence.

Known limitation (M0 finding B1): the resolver consumes ``.`` only between
``%%var.%%var``; whether Control-M also consumes the dot in ``%%var.text``
(e.g. ``%%$ODATE.tok``) is UNCONFIRMED — a divergence involving that shape may be the
resolver, not the definition. The adjudicator is the ground-truth watched filename
from Control-M monitoring (M0 info item A3); do NOT change core resolver semantics
without it.

Corroboration context (0002-B §2 step 5, read-only): the legacy side must also
reconcile with the Oracle ``psgmgr`` extract and the loaded graph snapshot via
``drydocs_core`` adapters + ``Neo4jClient(database="drydocs")`` — this component
never writes either.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from drydocs_core.orchestration.controlm import resolve_job

from .formats import DefinitionSet, JobDefinition, VariableDefs

#: Synthetic definition appended to resolve a job's watch template / command line
#: through the same scope chain as its variables. Name chosen to be implausible
#: in real definitions.
_PROBE = "%%__DRYDOCS_PROBE__"
_PROBE_NAME = "__DRYDOCS_PROBE__"


@dataclass
class EquivalenceReport:
    """Outcome of the offline proof; attach to the Jira handoff.

    ``equivalent`` is True only when every paired job is PROVEN — at least one
    surface compared and all compared surfaces equal. A job with nothing to
    compare lands in ``not_proven`` and blocks the claim; it never passes by
    silence.
    """

    equivalent: bool
    compared_jobs: int = 0
    divergences: list[str] = field(default_factory=list)  # resolved-behavior diffs
    #: jobs with NO comparable surface, named — "we did not prove this",
    #: which is a different statement from "this is equivalent".
    not_proven: list[str] = field(default_factory=list)
    #: jobs where at least one surface compared and all compared surfaces matched
    proven_jobs: int = 0


def _resolve_text(folder_vars: VariableDefs, job: JobDefinition, text: str) -> str:
    """Resolve ``text`` under the job's folder+job scope via the core engine."""
    defs = [*list(job.variables), (_PROBE, text)]
    for rv in resolve_job(folder_vars, defs):
        if rv.name == _PROBE_NAME:
            return rv.resolved_value
    return text  # pragma: no cover - the probe always resolves


def resolved_watch(folder_vars: VariableDefs, job: JobDefinition) -> str | None:
    """Resolve ``job``'s watch template under its folder scope; None if no template."""
    if job.watch_template is None:
        return None
    return _resolve_text(folder_vars, job, job.watch_template)


def resolved_command(folder_vars: VariableDefs, job: JobDefinition) -> str | None:
    """Resolve ``job``'s command line under its folder scope; None if no command.

    The surface defect B′ was blind on: command jobs have no watch template, so
    without this they had NOTHING compared — and were reported equivalent.
    """
    if not job.command_line:
        return None
    return _resolve_text(folder_vars, job, job.command_line)


def prove_equivalence(legacy: DefinitionSet, greenfield: DefinitionSet) -> EquivalenceReport:
    """Prove ``greenfield`` re-derives ``legacy``'s resolved behavior.

    Surfaces compared per job pair: resolved watch path, resolved command line.
    A surface participates when EITHER side carries it — one side losing its
    command line is a divergence, not a skip.
    """
    divergences: list[str] = []
    not_proven: list[str] = []
    if len(legacy.jobs) != len(greenfield.jobs):
        divergences.append(
            f"job count differs: legacy={len(legacy.jobs)} greenfield={len(greenfield.jobs)}"
        )
    legacy_folder = legacy.folder_variables()
    greenfield_folder = greenfield.folder_variables()
    compared = 0
    proven = 0
    for lj, gj in zip(legacy.jobs, greenfield.jobs, strict=False):
        compared += 1
        surfaces_compared = 0
        job_diverged = False
        for surface, resolver in (("watch", resolved_watch), ("command", resolved_command)):
            lv = resolver(legacy_folder, lj)
            gv = resolver(greenfield_folder, gj)
            if lv is None and gv is None:
                continue
            surfaces_compared += 1
            if lv != gv:
                job_diverged = True
                divergences.append(
                    f"{lj.name} {surface} resolves {lv!r} but {gj.name} resolves {gv!r}"
                )
        if surfaces_compared == 0:
            not_proven.append(
                f"{lj.name}: no comparable surface (no watch template, no command line) "
                "— NOT proven equivalent"
            )
        elif not job_diverged:
            proven += 1
    return EquivalenceReport(
        equivalent=not divergences and not not_proven,
        compared_jobs=compared,
        divergences=divergences,
        not_proven=not_proven,
        proven_jobs=proven,
    )
