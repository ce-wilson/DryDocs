"""Legacy → greenfield definition transform (TDD Stage D; the Tier-1 lane, FR-REM-3).

**Tier 1 = deterministic Python** (TDD Stage C): a fix whose rule is fully expressible in
code — idempotent, unit-tested per rule, batch-safe, no LLM anywhere. Tier-2 (agentic,
judgment-requiring) fixes never run here; they arrive as *proposed* transforms through
mandatory HITL review and, when a pattern recurs identically, get promoted INTO a Tier-1
rule with its own test.

**Governance (registry rule, recorded at the doc port):** only ✅-ratified rules may
change a definition — :func:`propose_greenfield` SKIPS unratified rules and reports them,
it never silently applies. Rule *mechanism* is producer-side (this module); rule *values*
(real name maps, real registry ids/ratification) are company-side and injected by the
caller — the registry data shape is HITL open question OQ-2 and is deliberately not
settled here.

High-blast-radius actions (folder renames, watch-template rewrites pending the ``var.text``
rule B1) are NOT Tier-1 material — propose only, via the Tier-2 path.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace

from .formats import DefinitionSet, JobDefinition


@dataclass(frozen=True)
class Tier1Rule:
    """One deterministic, idempotent transform rule.

    ``apply`` must be pure (input set → new set, no side effects) and idempotent
    (``apply(apply(ds)) == apply(ds)``) — the per-rule tests assert both.
    """

    rule_id: str  # registry key (company-supplied; synthetic in tests)
    description: str  # mechanism-only summary
    ratified: bool  # gate outcome — only True rules may change definitions
    apply: Callable[[DefinitionSet], DefinitionSet]


@dataclass
class TransformResult:
    """Outcome of a Tier-1 pass."""

    greenfield: DefinitionSet
    applied: list[str] = field(default_factory=list)  # rule ids that ran
    skipped_unratified: list[str] = field(default_factory=list)  # governance skips


def propose_greenfield(definitions: DefinitionSet, rules: Sequence[Tier1Rule]) -> TransformResult:
    """Apply the ratified Tier-1 ``rules`` to ``definitions``; skip the rest, loudly."""
    current = definitions
    result = TransformResult(greenfield=definitions)
    for rule in rules:
        if not rule.ratified:
            result.skipped_unratified.append(rule.rule_id)
            continue
        current = rule.apply(current)
        result.applied.append(rule.rule_id)
    result.greenfield = current
    return result


# --------------------------------------------------------------------------- #
# Concrete Tier-1 rules (mechanism; values injected by the caller)
# --------------------------------------------------------------------------- #


def _rename_in_text(text: str, old: str, new: str) -> str:
    """Rewrite ``%%OLD`` / ``%%$OLD`` references without touching longer names
    (``%%DIR`` must not rewrite inside ``%%DIR_A``)."""
    return re.sub(rf"%%(\$?){re.escape(old)}(?![A-Za-z0-9_])", rf"%%\1{new}", text)


def _strip_pfx(name: str) -> str:
    return name[2:] if name.startswith("%%") else name


def canonical_variable_rename(
    mapping: Mapping[str, str], *, rule_id: str, ratified: bool
) -> Tier1Rule:
    """Tier-1 rule: rename variables to their canonical names, rewriting every
    reference on EVERY text-bearing surface and EVERY scope.

    ``mapping`` uses bare names (no ``%%``), old → canonical. The real map is a
    company-side ratified value (command-line-and-variables standard); tests use
    synthetic pairs. Renaming onto a name that already exists in the same scope is
    a conflict and raises — a conflicting rename is Tier-2 judgment, not Tier-1.

    HISTORY (defect A′, found by the 2026-08-12 POC): the original rewrote only
    job variable declarations/values and watch templates — ``command_line``,
    ``post_command``, ``description``, folder- and sub-folder-scope variables,
    and ``scope_chain`` all kept the old name, so the "behavior-preserving by
    construction" claim was false exactly where ``prove_equivalence`` was blind
    (command jobs). The rewrite below is surface-complete, and the DOCUMENT-level
    guarantee lives in ``xml_io``'s post-conditions (``no-dangling-reference``
    et al.), which scan the whole emitted file — modeled fields or not — so a
    future field added to :class:`JobDefinition` cannot silently reopen the gap.
    """

    def _rename_all(text: str) -> str:
        for old, new in mapping.items():
            text = _rename_in_text(text, old, new)
        return text

    def _rename_defs(defs) -> list:
        out = []
        for name, value in defs:
            bare = mapping.get(_strip_pfx(name), _strip_pfx(name))
            out.append((f"%%{bare}", _rename_all(value) if value is not None else None))
        return out

    def _check_conflicts(scope_desc: str, defs) -> None:
        existing = {_strip_pfx(n) for n, _ in defs}
        for old, new in mapping.items():
            if old in existing and new in existing:
                raise ValueError(
                    f"{rule_id}: rename {old!r} -> {new!r} conflicts with an "
                    f"existing definition in {scope_desc} (Tier-2 territory)"
                )

    def _apply(definitions: DefinitionSet) -> DefinitionSet:
        def rename_job(job: JobDefinition) -> JobDefinition:
            _check_conflicts(f"job {job.name!r}", job.variables)
            template = job.watch_template
            if template is not None:
                template = _rename_all(template)
            return replace(
                job,
                variables=_rename_defs(job.variables),
                watch_template=template,
                command_line=_rename_all(job.command_line),
                post_command=_rename_all(job.post_command),
                description=_rename_all(job.description),
                # scope_chain layers carry the same defs the folder/job entries
                # do — resolution_chain() PREFERS this chain when populated, so
                # leaving it stale hands downstream consumers the old names.
                scope_chain=[
                    (scope, container, _rename_defs(defs))
                    for scope, container, defs in job.scope_chain
                ],
            )

        def rename_folder(folder):
            _check_conflicts(f"{folder.scope.lower()} {folder.name!r}", folder.variables)
            return replace(
                folder,
                variables=_rename_defs(folder.variables),
                description=_rename_all(folder.description),
            )

        return replace(
            definitions,
            folders=[rename_folder(f) for f in definitions.folders],
            jobs=[rename_job(j) for j in definitions.jobs],
        )

    return Tier1Rule(
        rule_id=rule_id,
        description="rename variables to canonical names; rewrite all references",
        ratified=ratified,
        apply=_apply,
    )
