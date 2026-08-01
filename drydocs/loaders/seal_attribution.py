"""SEAL attribution loader — STG_APP_FACT facts -> job WAS_ASSOCIATED_WITH edges.

Backlog K2. The match policy implemented here is the one SME-confirmed at the
``seal-attribution-match-policy`` gate (config/gate-log.md, 2026-07-14):

- §A  Fact-type precedence SEAL > FID > APP_NAME > ALIAS; a SEAL-tier hit
      attributes alone (lower tiers = corroboration only); one-to-one accept
      at the top available tier.
- §B  Coverage invariant: matched + unmatched (+ pinned) reconciles against
      the eligible-job count every run — report, never drop. Unmatched never
      blocks the run.
- §C  Multi-hit (>1 distinct seal_id at the SAME tier) resolves by
      deterministic tie-break, last resort only: (a) most-recent feed row
      (app_fact_sk — the extract orders by stg_run.started_at so feed order
      IS run recency), then (b) lexicographically lowest seal_id. Every
      multi-hit is flagged on the coverage report for after-the-fact audit.
- §D  Edge shape: MERGE (j)-[r:WAS_ASSOCIATED_WITH {role:'seal_app_ref'}]->(a)
      with ON CREATE first_seen_at/source/match_method, SET last_seen_at/
      last_run_id — see seal_attribution.cypher. The loader creates NO nodes.
- §E  Runs only after jobs + SEAL reference loads; job.APPLICATION is never
      a SEAL-identity substitute (this module never reads it).
- §F  Manual mappings PIN: a job carrying a manual edge is excluded from the
      automated write; a derived match for it surfaces as a PIN-CONFLICT
      (agreeing or disagreeing) — retirement is a human act (manual_loads.py).

The resolver (:func:`resolve_attributions`) is pure — offline-testable with
no Neo4j. Reconciliation for the FID / APP_NAME / ALIAS tiers is an injected
seam (:class:`TierReconcilers`): APP_NAME reconciles against the loaded SEAL
reference names by default (:func:`fetch_app_name_reconciler`); FID and ALIAS
have no producer-side reconciliation source yet, so their facts stay
unresolved (counted, never guessed) until a table is wired company-side.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import ValidationError

from drydocs_core.models import SealAttributionRow, StgAppFactRow

from .base import BaseLoader

if TYPE_CHECKING:
    from drydocs_core.neo4j_client import Neo4jClient

LOGGER = logging.getLogger(__name__)

# Precedence order, highest confidence first (gate §A).
ATTRIBUTION_TIERS: tuple[str, ...] = ("SEAL", "FID", "APP_NAME", "ALIAS")

# fact_type tier -> the match_method recorded on the edge (gate §D/§E).
MATCH_METHOD_BY_TIER: dict[str, str] = {
    "SEAL": "seal",
    "FID": "fid",
    "APP_NAME": "app_name",
    "ALIAS": "alias",
}

# Fixed loader-identity string on every automated edge (gate provenance block).
AUTOMATED_SOURCE = "controlm-variable-normalization"


# ---------------------------------------------------------------------------
# Reconciliation seam (tiers 2-4)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TierReconcilers:
    """Value -> seal_id lookups for the non-SEAL tiers.

    Keys must be normalized ``value.strip().upper()``. The SEAL tier needs no
    table — its fact_value IS the candidate seal_id (gate mapping n:1).
    An empty table means that tier's facts stay unresolved (reported in
    coverage), never silently guessed.
    """

    fid: Mapping[str, str] = field(default_factory=dict)
    app_name: Mapping[str, str] = field(default_factory=dict)
    alias: Mapping[str, str] = field(default_factory=dict)

    def resolve(self, fact_type: str, fact_value: str) -> str | None:
        value = fact_value.strip()
        if not value:
            return None
        if fact_type == "SEAL":
            return value
        table = {
            "FID": self.fid,
            "APP_NAME": self.app_name,
            "ALIAS": self.alias,
        }.get(fact_type)
        if table is None:
            return None
        return table.get(value.upper())


# ---------------------------------------------------------------------------
# Coverage report (gate §B / §C / §F — report, never drop)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MultiHit:
    """A flagged multi-hit case: >1 distinct seal_id at the winning tier."""

    folder_id: str
    job_id: str
    tier: str
    candidates: tuple[str, ...]  # sorted, for reproducible reports
    accepted: str
    tie_break: str  # 'run_recency' | 'lowest_seal_id'


@dataclass(frozen=True)
class PinConflict:
    """A manually-pinned job the automated run derived a match for (§F.3).

    ``derived_seal_id`` is None when the feed carried facts for the pinned
    job but none resolved — the pin simply holds, nothing to compare.
    """

    folder_id: str
    job_id: str
    pinned_seal_id: str
    derived_seal_id: str | None
    agrees: bool | None  # None when nothing was derived


@dataclass
class AttributionCoverage:
    """Per-run coverage accounting. Invariant (gate §B):
    matched + unmatched + pinned == eligible_jobs."""

    eligible_jobs: int = 0
    matched: int = 0
    unmatched: int = 0
    pinned: int = 0
    matched_by_method: dict[str, int] = field(default_factory=dict)
    multi_hits: list[MultiHit] = field(default_factory=list)
    pin_conflicts: list[PinConflict] = field(default_factory=list)
    corroboration_agree: int = 0  # lower-tier facts agreeing with the accepted match
    corroboration_disagree: int = 0  # lower-tier facts naming a DIFFERENT app (flag material)
    unresolved_facts_by_tier: dict[str, int] = field(default_factory=dict)
    ignored_fact_rows: int = 0  # non-attribution fact types (DS_ID, DATAFLOW, ...)
    fact_rows_rejected: int = 0  # raw rows failing StgAppFactRow validation

    def reconciles(self) -> bool:
        return self.matched + self.unmatched + self.pinned == self.eligible_jobs

    def as_dict(self) -> dict:
        return {
            "eligible_jobs": self.eligible_jobs,
            "matched": self.matched,
            "unmatched": self.unmatched,
            "pinned": self.pinned,
            "matched_by_method": dict(self.matched_by_method),
            "multi_hit_count": len(self.multi_hits),
            "pin_conflict_count": sum(1 for c in self.pin_conflicts if c.agrees is not None),
            "corroboration_agree": self.corroboration_agree,
            "corroboration_disagree": self.corroboration_disagree,
            "unresolved_facts_by_tier": dict(self.unresolved_facts_by_tier),
            "ignored_fact_rows": self.ignored_fact_rows,
            "fact_rows_rejected": self.fact_rows_rejected,
            "reconciles": self.reconciles(),
        }


# ---------------------------------------------------------------------------
# The match policy (pure)
# ---------------------------------------------------------------------------


def resolve_attributions(
    rows: Iterable[StgAppFactRow],
    *,
    reconcilers: TierReconcilers | None = None,
    pinned: Mapping[tuple[str, str], str] | None = None,
) -> tuple[list[SealAttributionRow], AttributionCoverage]:
    """Apply the gate-confirmed match policy to a batch of fact rows.

    ``pinned`` maps (folder_id, job_id) -> seal_id for jobs carrying a
    manually-asserted edge (match_method 'manual'); those jobs produce no
    decision — a derived match surfaces as a :class:`PinConflict` instead.
    Deterministic: same feed (same recency keys) -> same decisions.
    """
    reconcilers = reconcilers or TierReconcilers()
    pinned = pinned or {}
    coverage = AttributionCoverage()

    # Group per job, preserving feed order; assign each row its recency key.
    jobs: dict[tuple[str, str], list[tuple[int, StgAppFactRow]]] = {}
    for ordinal, row in enumerate(rows):
        recency = row.app_fact_sk if row.app_fact_sk is not None else ordinal
        jobs.setdefault((row.folder_id, row.job_id), []).append((recency, row))

    coverage.eligible_jobs = len(jobs)
    decisions: list[SealAttributionRow] = []

    for (folder_id, job_id), job_rows in jobs.items():
        winner, winning_tier = _resolve_job(folder_id, job_id, job_rows, reconcilers, coverage)

        pin = pinned.get((folder_id, job_id))
        if pin is not None:
            coverage.pinned += 1
            coverage.pin_conflicts.append(
                PinConflict(
                    folder_id=folder_id,
                    job_id=job_id,
                    pinned_seal_id=pin,
                    derived_seal_id=winner,
                    agrees=None if winner is None else winner == pin,
                )
            )
            continue

        if winner is None:
            coverage.unmatched += 1
            continue

        method = MATCH_METHOD_BY_TIER[winning_tier]
        coverage.matched += 1
        coverage.matched_by_method[method] = coverage.matched_by_method.get(method, 0) + 1
        decisions.append(
            SealAttributionRow(
                folder_id=folder_id,
                job_id=job_id,
                seal_id=winner,
                match_method=method,
            )
        )

    return decisions, coverage


def _resolve_job(
    folder_id: str,
    job_id: str,
    job_rows: list[tuple[int, StgAppFactRow]],
    reconcilers: TierReconcilers,
    coverage: AttributionCoverage,
) -> tuple[str | None, str]:
    """Tier-walk one job's facts. Returns (seal_id | None, winning_tier)."""
    by_tier: dict[str, list[tuple[int, StgAppFactRow]]] = {}
    for recency, row in job_rows:
        if row.fact_type in MATCH_METHOD_BY_TIER:
            by_tier.setdefault(row.fact_type, []).append((recency, row))
        else:
            coverage.ignored_fact_rows += 1

    winner: str | None = None
    winning_tier = ""
    for tier in ATTRIBUTION_TIERS:
        candidates: dict[str, int] = {}  # seal_id -> max recency at this tier
        for recency, row in by_tier.get(tier, []):
            seal_id = reconcilers.resolve(tier, row.fact_value)
            if seal_id is None:
                coverage.unresolved_facts_by_tier[tier] = (
                    coverage.unresolved_facts_by_tier.get(tier, 0) + 1
                )
                continue
            candidates[seal_id] = max(recency, candidates.get(seal_id, recency))
        if not candidates:
            continue

        winning_tier = tier
        if len(candidates) == 1:
            winner = next(iter(candidates))
        else:
            # §C deterministic tie-break, last resort only: (a) most-recent
            # feed row, then (b) lexicographically lowest seal_id.
            top_recency = max(candidates.values())
            top = sorted(s for s, r in candidates.items() if r == top_recency)
            winner = top[0]
            tie_break = "run_recency" if len(top) == 1 else "lowest_seal_id"
            coverage.multi_hits.append(
                MultiHit(
                    folder_id=folder_id,
                    job_id=job_id,
                    tier=tier,
                    candidates=tuple(sorted(candidates)),
                    accepted=winner,
                    tie_break=tie_break,
                )
            )
        break

    # §A: lower-tier facts are corroboration only — recorded, never override.
    if winner is not None:
        tier_rank = ATTRIBUTION_TIERS.index(winning_tier)
        for tier in ATTRIBUTION_TIERS[tier_rank + 1 :]:
            for _, row in by_tier.get(tier, []):
                seal_id = reconcilers.resolve(tier, row.fact_value)
                if seal_id is None:
                    continue
                if seal_id == winner:
                    coverage.corroboration_agree += 1
                else:
                    coverage.corroboration_disagree += 1

    return winner, winning_tier


# ---------------------------------------------------------------------------
# Adapter + loader
# ---------------------------------------------------------------------------


class SealAttributionAdapter:
    """Wraps a raw STG_APP_FACT adapter (CSV or Oracle) and yields resolved
    attribution decisions. The wrapped adapter's rows are validated to
    :class:`StgAppFactRow` here (rejects counted in coverage — reported,
    never dropped silently); BaseLoader then re-validates the emitted
    decisions against :class:`SealAttributionRow`.
    """

    def __init__(
        self,
        inner: Any,
        *,
        reconcilers: TierReconcilers | None = None,
        pinned: Mapping[tuple[str, str], str] | None = None,
        max_rejects_kept: int = 20,
    ) -> None:
        self.inner = inner
        self.reconcilers = reconcilers or TierReconcilers()
        self.pinned = dict(pinned or {})
        self.max_rejects_kept = max_rejects_kept
        self.coverage: AttributionCoverage | None = None
        self.fact_rejects: list[dict] = []

    def __enter__(self) -> SealAttributionAdapter:
        enter = getattr(self.inner, "__enter__", None)
        if enter is not None:
            enter()
        return self

    def __exit__(self, *exc: Any) -> None:
        exit_ = getattr(self.inner, "__exit__", None)
        if exit_ is not None:
            exit_(*exc)

    def rows(self) -> Iterator[dict]:
        facts: list[StgAppFactRow] = []
        rejected = 0
        for idx, raw in enumerate(self.inner.rows()):
            try:
                facts.append(StgAppFactRow.model_validate(raw))
            except ValidationError as exc:
                rejected += 1
                if len(self.fact_rejects) < self.max_rejects_kept:
                    self.fact_rejects.append({"row_index": idx, "errors": exc.errors(), "raw": raw})
        decisions, coverage = resolve_attributions(
            facts, reconcilers=self.reconcilers, pinned=self.pinned
        )
        coverage.fact_rows_rejected = rejected
        self.coverage = coverage
        for decision in decisions:
            yield decision.model_dump(mode="json")


class SealAttributionLoader(BaseLoader):
    """Writes the gate-confirmed WAS_ASSOCIATED_WITH {role: seal_app_ref}
    edges and stamps the run's coverage counts onto its :JobRun so the
    graph_verify coverage invariant (graph-tests/seal-attribution-coverage.yaml)
    can reconcile them (§B: the invariant joins graph_verify)."""

    name: ClassVar[str] = "seal_attribution.v1"
    source_id: ClassVar[str | None] = "controlm@[db].drydocs_stg.stg_app_fact"
    cypher_path: ClassVar[Path | None] = (
        Path(__file__).resolve().parent / "cypher" / "seal_attribution.cypher"
    )
    row_model: ClassVar[type] = SealAttributionRow
    source_label: ClassVar[str] = "csv"  # 'oracle' when fed from DRYDOCS_STG

    def load(self):
        summary = super().load()
        coverage = getattr(self.adapter, "coverage", None)
        if coverage is not None:
            self._stamp_coverage(coverage)
        return summary

    def _stamp_coverage(self, coverage: AttributionCoverage) -> None:
        # edges_written counts what this run actually touched; the shortfall
        # vs matched (decisions whose job or Application node was absent) is
        # surfaced as dropped_in_graph — reported, never silent (§B).
        result = self.client.run(
            """
            MATCH (run:JobRun {run_id: $run_id})
            OPTIONAL MATCH (:ControlMJob)-[r:WAS_ASSOCIATED_WITH {role: 'seal_app_ref'}]->(:BusinessApplication)
              WHERE r.last_run_id = $run_id
            WITH run, count(r) AS edges_written
            SET run.eligible_jobs      = $eligible_jobs,
                run.matched            = $matched,
                run.unmatched          = $unmatched,
                run.pinned             = $pinned,
                run.multi_hit_count    = $multi_hit_count,
                run.pin_conflict_count = $pin_conflict_count,
                run.edges_written      = edges_written,
                run.dropped_in_graph   = $matched - edges_written
            RETURN edges_written
            """,
            run_id=self.run_id,
            eligible_jobs=coverage.eligible_jobs,
            matched=coverage.matched,
            unmatched=coverage.unmatched,
            pinned=coverage.pinned,
            multi_hit_count=len(coverage.multi_hits),
            pin_conflict_count=sum(1 for c in coverage.pin_conflicts if c.agrees is not None),
        )
        if result:
            dropped = coverage.matched - result[0].get("edges_written", 0)
            if dropped:
                LOGGER.warning(
                    "seal_attribution: %d decision(s) found no graph endpoints "
                    "(job or Application missing) — surfaced as "
                    "JobRun.dropped_in_graph, follow up via the coverage suite.",
                    dropped,
                )


# ---------------------------------------------------------------------------
# Live-graph helpers (thin; the CLI wires these into the adapter)
# ---------------------------------------------------------------------------


def fetch_pinned_attributions(client: Neo4jClient) -> dict[tuple[str, str], str]:
    """Jobs carrying a manually-asserted seal_app_ref edge (gate §F: PIN)."""
    rows = client.run(
        """
        MATCH (j:ControlMJob)-[r:WAS_ASSOCIATED_WITH {role: 'seal_app_ref'}]->(a:BusinessApplication)
        WHERE r.match_method = 'manual'
        RETURN j.folder_id AS folder_id, j.job_id AS job_id, a.seal_id AS seal_id
        """
    )
    return {(str(r["folder_id"]), str(r["job_id"])): str(r["seal_id"]) for r in rows}


def fetch_app_name_reconciler(client: Neo4jClient) -> dict[str, str]:
    """APP_NAME tier table from the loaded SEAL reference (exact, normalized
    match on Application.name / app_short_name). Ambiguous names — two
    applications sharing one normalized name — are dropped from the table:
    an ambiguous name can never reconcile deterministically, so its facts
    stay unresolved (counted in coverage) rather than guessed."""
    rows = client.run(
        """
        MATCH (a:BusinessApplication)
        RETURN a.seal_id AS seal_id, a.name AS name, a.app_short_name AS short_name
        """
    )
    table: dict[str, str] = {}
    ambiguous: set[str] = set()
    for r in rows:
        seal_id = str(r["seal_id"])
        for key in (r.get("name"), r.get("short_name")):
            if not key:
                continue
            normalized = str(key).strip().upper()
            if not normalized:
                continue
            if normalized in table and table[normalized] != seal_id:
                ambiguous.add(normalized)
                continue
            table[normalized] = seal_id
    for name in ambiguous:
        table.pop(name, None)
    if ambiguous:
        LOGGER.info(
            "seal_attribution: %d ambiguous application name(s) excluded from "
            "APP_NAME reconciliation.",
            len(ambiguous),
        )
    return table


def check_sequencing_preconditions(client: Neo4jClient) -> tuple[int, int]:
    """Gate §E: the loader runs only after jobs + SEAL reference exist.
    Returns (job_count, application_count); the CLI refuses on zeros."""
    rows = client.run(
        """
        OPTIONAL MATCH (j:ControlMJob) WITH count(j) AS jobs
        OPTIONAL MATCH (a:BusinessApplication) RETURN jobs, count(a) AS apps
        """
    )
    if not rows:
        return 0, 0
    return int(rows[0].get("jobs") or 0), int(rows[0].get("apps") or 0)
