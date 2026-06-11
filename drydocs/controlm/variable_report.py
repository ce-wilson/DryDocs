"""Coverage report over classified Control-M variables (Phase A deliverable).

Aggregates classifier output into the numbers that validate the taxonomy
against the full population (~1.1M rows) and seed the Phase-C launcher
registry: kind distribution per data center, plugin namespaces, fact
types, system functions in use, and the most-referenced variable names
(the resolution hot set).
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .variables import ClassifiedVariable, VariableKind


@dataclass
class VariableCoverage:
    """Mutable accumulator — feed rows, then read the counters."""

    total: int = 0
    by_kind: Counter = field(default_factory=Counter)
    by_dc_kind: dict[str, Counter] = field(default_factory=dict)
    plugin_namespaces: Counter = field(default_factory=Counter)
    fact_types: Counter = field(default_factory=Counter)
    system_funcs: Counter = field(default_factory=Counter)
    referenced_names: Counter = field(default_factory=Counter)
    flow_targets: Counter = field(default_factory=Counter)
    malformed_samples: list[str] = field(default_factory=list)
    jobs_seen: set = field(default_factory=set)

    MAX_MALFORMED_SAMPLES = 25

    def add(
        self,
        cv: ClassifiedVariable,
        *,
        data_center: str = "UNKNOWN",
        job_key: tuple | None = None,
    ) -> None:
        self.total += 1
        self.by_kind[cv.kind.value] += 1
        self.by_dc_kind.setdefault(data_center, Counter())[cv.kind.value] += 1
        if cv.plugin_namespace:
            self.plugin_namespaces[cv.plugin_namespace] += 1
        if cv.fact_type:
            self.fact_types[cv.fact_type] += 1
        for fn in cv.system_funcs:
            self.system_funcs[fn] += 1
        for ref in cv.all_var_refs:  # %%VAR and %%$VAR user references alike
            self.referenced_names[ref] += 1
        for flow, _var in cv.flow_refs:
            self.flow_targets[flow] += 1
        if cv.kind is VariableKind.MALFORMED and len(self.malformed_samples) < self.MAX_MALFORMED_SAMPLES:
            self.malformed_samples.append(f"{cv.raw_name!r} = {(cv.raw_value or '')[:120]!r}")
        if job_key is not None:
            self.jobs_seen.add(job_key)

    @property
    def pct_by_kind(self) -> dict[str, float]:
        if not self.total:
            return {}
        return {
            k: round(100 * n / self.total, 2)
            for k, n in self.by_kind.most_common()
        }
