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

    rule_id: str          # registry key (company-supplied; synthetic in tests)
    description: str      # mechanism-only summary
    ratified: bool        # gate outcome — only True rules may change definitions
    apply: Callable[[DefinitionSet], DefinitionSet]


@dataclass
class TransformResult:
    """Outcome of a Tier-1 pass."""

    greenfield: DefinitionSet
    applied: list[str] = field(default_factory=list)              # rule ids that ran
    skipped_unratified: list[str] = field(default_factory=list)   # governance skips


def propose_greenfield(
    definitions: DefinitionSet, rules: Sequence[Tier1Rule]
) -> TransformResult:
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
    reference (other variable values + watch templates). Behavior-preserving by
    construction — the equivalence proof is still asserted by the caller's tests.

    ``mapping`` uses bare names (no ``%%``), old → canonical. The real map is a
    company-side ratified value (command-line-and-variables standard); tests use
    synthetic pairs. Renaming onto a name that already exists in the same job is a
    conflict and raises — a conflicting rename is Tier-2 judgment, not Tier-1.
    """

    def _apply(definitions: DefinitionSet) -> DefinitionSet:
        def rename_job(job: JobDefinition) -> JobDefinition:
            existing = {_strip_pfx(n) for n, _ in job.variables}
            for old, new in mapping.items():
                if old in existing and new in existing:
                    raise ValueError(
                        f"{rule_id}: rename {old!r} -> {new!r} conflicts with an "
                        f"existing definition in job {job.name!r} (Tier-2 territory)"
                    )
            variables = []
            for name, value in job.variables:
                bare = _strip_pfx(name)
                bare = mapping.get(bare, bare)
                new_value = value
                if new_value is not None:
                    for old, new in mapping.items():
                        new_value = _rename_in_text(new_value, old, new)
                variables.append((f"%%{bare}", new_value))
            template = job.watch_template
            if template is not None:
                for old, new in mapping.items():
                    template = _rename_in_text(template, old, new)
            return replace(job, variables=variables, watch_template=template)

        return replace(
            definitions,
            jobs=[rename_job(j) for j in definitions.jobs],
        )

    return Tier1Rule(
        rule_id=rule_id,
        description="rename variables to canonical names; rewrite all references",
        ratified=ratified,
        apply=_apply,
    )
