"""Offline equivalence proof — greenfield must re-derive legacy's resolved behavior.

Both sides resolve through ``drydocs_core.controlm.resolve_job`` (the same engine the
loaders trust), so the comparison is apples-to-apples: each FileWatcher job's watch
template is resolved under its folder scope and the *resolved* watched paths are
diffed — cosmetic definition differences are fine, behavioral differences fail the
proof. Jobs are paired BY ORDER (legacy[i] vs greenfield[i]): a remediation unit is a
deliberate legacy→greenfield pairing, and names legitimately differ across the pair.

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

from drydocs_core.controlm import resolve_job

from .formats import DefinitionSet, JobDefinition, VariableDefs

#: Synthetic definition appended to resolve a job's watch template through the same
#: scope chain as its variables. Name chosen to be implausible in real definitions.
_WATCH_PROBE = "%%__DRYDOCS_WATCH__"
_WATCH_PROBE_NAME = "__DRYDOCS_WATCH__"


@dataclass
class EquivalenceReport:
    """Outcome of the offline proof; attach to the Jira handoff."""

    equivalent: bool
    compared_jobs: int = 0
    divergences: list[str] = field(default_factory=list)  # resolved-behavior diffs


def resolved_watch(folder_vars: VariableDefs, job: JobDefinition) -> str | None:
    """Resolve ``job``'s watch template under its folder scope; None if no template."""
    if job.watch_template is None:
        return None
    defs = list(job.variables) + [(_WATCH_PROBE, job.watch_template)]
    for rv in resolve_job(folder_vars, defs):
        if rv.name == _WATCH_PROBE_NAME:
            return rv.resolved_value
    return None


def prove_equivalence(
    legacy: DefinitionSet, greenfield: DefinitionSet
) -> EquivalenceReport:
    """Prove ``greenfield`` re-derives ``legacy``'s resolved behavior (watch paths)."""
    divergences: list[str] = []
    if len(legacy.jobs) != len(greenfield.jobs):
        divergences.append(
            f"job count differs: legacy={len(legacy.jobs)} greenfield={len(greenfield.jobs)}"
        )
    legacy_folder = legacy.folder_variables()
    greenfield_folder = greenfield.folder_variables()
    compared = 0
    for lj, gj in zip(legacy.jobs, greenfield.jobs):
        compared += 1
        lw = resolved_watch(legacy_folder, lj)
        gw = resolved_watch(greenfield_folder, gj)
        if lw != gw:
            divergences.append(
                f"{lj.name} resolves {lw!r} but {gj.name} resolves {gw!r}"
            )
    return EquivalenceReport(
        equivalent=not divergences,
        compared_jobs=compared,
        divergences=divergences,
    )
