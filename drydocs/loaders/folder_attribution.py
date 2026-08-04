"""Folder-grain attribution loader (backlog K8) — app-code defined mapping
plus the demoted K2 fallback -> (:ControlMFolder)-[:BELONGS_TO_APPLICATION
{role: seal_app_ref}]->(:Port) edges.

Gate seal-app-ref-edge-reshape (SIGNED OFF 2026-08-03, config/gate-log.md):

- §A1  Attribution grain is the FOLDER; jobs inherit via CONTAINS_JOB and no
       per-job application edge is authored.
- §B1  ONE authoring mechanism: a steward-defined row per Control-M app code
       (drydocs_core.mapping_store, K9); this loader fans a code-level row
       out over m3_contains_folder. A per-folder row (folder_id set) narrows
       to one folder — the tier-2 platform resolution path.
- §B2  Tiers seal-born | platform | dual-coded ride the row; a code-level
       PLATFORM declaration row (empty app_id) attributes nothing itself —
       its folders resolve per folder or SURFACE to the steward, never
       auto-picked.
- §B3  The K2 match policy (seal_attribution.resolve_attributions) DEMOTES
       to a fallback tier for codes with NO authored row: a folder whose
       jobs' K2 decisions are UNANIMOUS gets the edge with
       origin=matched-fallback (disclosed, never presented as defined);
       disagreement is a conflict on the coverage report, not a write.
- §C1  The target is the application's BatchProcessing :Port (supernode
       avoidance), key (parent_app_id, kind). The automated path creates NO
       nodes.
- §E3  Store rows never write the graph directly — this loader is the only
       writer of the edge.
- §F1  Producer-side migration of the K2 job edges is the reload itself
       (wipe-and-rebuild); the edge property family (origin / match_method /
       tier / first_seen_at / last_seen_at / source) preserves the K2
       provenance vocabulary at the new grain. The company-side migration is
       theirs (guardrail 6 / tracker T23).

The 1:1 rule (OWNER-NOT-USER, ruled in session at K7): a folder belongs to
exactly one application. Enforced as a GRAPH-TEST
(graph-tests/folder-attribution-coverage.yaml) because Neo4j cannot declare
relationship cardinality; the resolver refuses to emit two rows for one
folder by construction.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from drydocs_core.models import FolderAttributionRow, StgAppFactRow

from .base import BaseLoader
from .seal_attribution import (
    ATTRIBUTION_TIERS,
    TierReconcilers,
    resolve_attributions,
    validate_fact_rows,
)

if TYPE_CHECKING:
    from drydocs_core.neo4j_client import Neo4jClient

LOGGER = logging.getLogger(__name__)

# Authored-origin precedence when one folder is covered by several store
# rows: a manual pin beats an override beats the defined baseline. Highest
# wins; a TIE between two DIFFERENT app_ids at the same precedence is a
# conflict (surfaced, never auto-picked).
ORIGIN_PRECEDENCE: dict[str, int] = {"manual-pin": 3, "override": 2, "defined": 1}

# origin -> the match_method recorded on the edge. Fallback rows carry the
# winning K2 tier method instead (seal | fid | app_name | alias).
MATCH_METHOD_BY_ORIGIN: dict[str, str] = {
    "defined": "defined",
    "override": "override",
    "manual-pin": "manual",
}

# Edge provenance strings (source property): where the VALUE came from.
AUTHORED_SOURCE = "config/overrides/app-code-mappings.csv"
FALLBACK_SOURCE = "controlm-variable-normalization"


# ---------------------------------------------------------------------------
# Coverage report (report, never drop — the K2 §B doctrine at folder grain)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FolderConflict:
    """A folder the resolver refused to attribute: two candidates at equal
    standing named different applications, or its platform code declared it
    without resolving it. Steward queue material — never auto-picked."""

    folder_id: str
    app_code: str | None
    kind: str  # 'authored-tie' | 'fallback-disagreement' | 'platform-unresolved'
    candidates: tuple[str, ...]


@dataclass(frozen=True)
class FolderPinConflict:
    """A pinned folder (existing manual edge) the automated run derived a
    different (or agreeing) value for — parity with the K2 §F report."""

    folder_id: str
    pinned_app_id: str
    derived_app_id: str | None
    agrees: bool | None


@dataclass
class FolderAttributionCoverage:
    """Per-run accounting. Invariant: attributed + unmatched + conflicts +
    pinned == eligible_folders."""

    eligible_folders: int = 0
    attributed: int = 0
    unmatched: int = 0
    pinned: int = 0
    attributed_by_origin: dict[str, int] = field(default_factory=dict)
    conflicts: list[FolderConflict] = field(default_factory=list)
    pin_conflicts: list[FolderPinConflict] = field(default_factory=list)
    fact_rows_rejected: int = 0

    def reconciles(self) -> bool:
        return (
            self.attributed + self.unmatched + len(self.conflicts) + self.pinned
            == self.eligible_folders
        )

    def as_dict(self) -> dict:
        return {
            "eligible_folders": self.eligible_folders,
            "attributed": self.attributed,
            "unmatched": self.unmatched,
            "pinned": self.pinned,
            "attributed_by_origin": dict(self.attributed_by_origin),
            "conflict_count": len(self.conflicts),
            "pin_conflict_count": sum(1 for c in self.pin_conflicts if c.agrees is not None),
            "fact_rows_rejected": self.fact_rows_rejected,
            "reconciles": self.reconciles(),
        }


# ---------------------------------------------------------------------------
# The folder resolver (pure)
# ---------------------------------------------------------------------------


def resolve_folder_attributions(
    authored: Iterable[Mapping[str, Any]],
    folder_codes: Mapping[str, str | None],
    k2_decisions: Iterable[Any],
    *,
    pinned: Mapping[str, str] | None = None,
) -> tuple[list[FolderAttributionRow], FolderAttributionCoverage]:
    """Resolve every folder to at most ONE application (the 1:1 rule).

    ``authored`` — app-code store rows (mapping_store.app_code_rows_from_store
    dicts: app_code / folder_id / tier / app_id / origin, all authored
    origins). ``folder_codes`` — folder_id -> app_code (None for a folder
    with no app-code grouping), the graph fan-out index; its keys define the
    ELIGIBLE folder population. ``k2_decisions`` — job-grain
    SealAttributionRow decisions from the demoted K2 policy (§B3 fallback).
    ``pinned`` — folder_id -> app_id for folders carrying an existing
    manual-pin edge; excluded from the automated write, disagreements
    surfaced (§F parity).
    """
    pinned = pinned or {}
    coverage = FolderAttributionCoverage()
    coverage.eligible_folders = len(folder_codes)

    # Index authored rows: per-folder rows and code-level rows.
    by_folder: dict[str, list[Mapping[str, Any]]] = {}
    by_code: dict[str, list[Mapping[str, Any]]] = {}
    declared_platform_codes: set[str] = set()
    for row in authored:
        code = str(row.get("app_code") or "").strip()
        folder_id = row.get("folder_id")
        if folder_id:
            by_folder.setdefault(str(folder_id).strip(), []).append(row)
        elif row.get("app_id"):
            by_code.setdefault(code, []).append(row)
        else:
            # A code-level platform DECLARATION (empty app_id): attributes
            # nothing; marks the code so its unresolved folders surface as
            # platform-unresolved instead of falling back (§B2 — a declared
            # code HAS a defined row, so §B3's "no defined row" fallback
            # does not apply).
            declared_platform_codes.add(code)

    # Index K2 fallback decisions per folder (unanimity required).
    k2_by_folder: dict[str, dict[str, str]] = {}  # folder -> app_id -> best method
    method_rank = {t.lower(): i for i, t in enumerate(ATTRIBUTION_TIERS)}
    for decision in k2_decisions:
        folder_id = str(decision.folder_id)
        candidates = k2_by_folder.setdefault(folder_id, {})
        prev = candidates.get(decision.seal_id)
        if prev is None or method_rank.get(decision.match_method, 99) < method_rank.get(prev, 99):
            candidates[decision.seal_id] = decision.match_method

    rows: list[FolderAttributionRow] = []
    for folder_id, app_code in folder_codes.items():
        candidates: list[tuple[int, Mapping[str, Any]]] = []
        for row in by_folder.get(folder_id, []):
            candidates.append((ORIGIN_PRECEDENCE.get(str(row.get("origin")), 0), row))
        if app_code:
            for row in by_code.get(app_code, []):
                candidates.append((ORIGIN_PRECEDENCE.get(str(row.get("origin")), 0), row))

        derived: FolderAttributionRow | None = None
        conflict: FolderConflict | None = None
        if candidates:
            top = max(rank for rank, _ in candidates)
            winners = {str(r.get("app_id")): r for rank, r in candidates if rank == top}
            if len(winners) > 1:
                conflict = FolderConflict(
                    folder_id=folder_id,
                    app_code=app_code,
                    kind="authored-tie",
                    candidates=tuple(sorted(winners)),
                )
            else:
                app_id, row = next(iter(winners.items()))
                origin = str(row.get("origin"))
                derived = FolderAttributionRow(
                    folder_id=folder_id,
                    app_id=app_id,
                    origin=origin,
                    match_method=MATCH_METHOD_BY_ORIGIN[origin],
                    tier=row.get("tier"),
                    source=AUTHORED_SOURCE,
                )
        elif app_code and app_code in declared_platform_codes:
            conflict = FolderConflict(
                folder_id=folder_id,
                app_code=app_code,
                kind="platform-unresolved",
                candidates=(),
            )
        else:
            k2 = k2_by_folder.get(folder_id, {})
            if len(k2) == 1:
                app_id, method = next(iter(k2.items()))
                derived = FolderAttributionRow(
                    folder_id=folder_id,
                    app_id=app_id,
                    origin="matched-fallback",
                    match_method=method,
                    tier=None,
                    source=FALLBACK_SOURCE,
                )
            elif len(k2) > 1:
                conflict = FolderConflict(
                    folder_id=folder_id,
                    app_code=app_code,
                    kind="fallback-disagreement",
                    candidates=tuple(sorted(k2)),
                )

        pin = pinned.get(folder_id)
        if pin is not None:
            coverage.pinned += 1
            coverage.pin_conflicts.append(
                FolderPinConflict(
                    folder_id=folder_id,
                    pinned_app_id=pin,
                    derived_app_id=derived.app_id if derived else None,
                    agrees=None if derived is None else derived.app_id == pin,
                )
            )
            continue
        if conflict is not None:
            coverage.conflicts.append(conflict)
            continue
        if derived is None:
            coverage.unmatched += 1
            continue

        coverage.attributed += 1
        coverage.attributed_by_origin[derived.origin] = (
            coverage.attributed_by_origin.get(derived.origin, 0) + 1
        )
        rows.append(derived)

    return rows, coverage


# ---------------------------------------------------------------------------
# Adapter + loader
# ---------------------------------------------------------------------------


class FolderAttributionAdapter:
    """Yields folder-grain attribution rows to BaseLoader.

    ``fact_source`` is the optional raw STG_APP_FACT adapter feeding the §B3
    fallback (validated here, rejects counted); with no fact source only the
    authored store rows resolve — an authored-only run is legitimate.
    """

    def __init__(
        self,
        authored: Iterable[Mapping[str, Any]],
        folder_codes: Mapping[str, str | None],
        *,
        fact_source: Any = None,
        reconcilers: TierReconcilers | None = None,
        pinned: Mapping[str, str] | None = None,
        max_rejects_kept: int = 20,
    ) -> None:
        self.authored = list(authored)
        self.folder_codes = dict(folder_codes)
        self.fact_source = fact_source
        self.reconcilers = reconcilers or TierReconcilers()
        self.pinned = dict(pinned or {})
        self.max_rejects_kept = max_rejects_kept
        self.coverage: FolderAttributionCoverage | None = None
        self.fact_rejects: list[dict] = []

    def __enter__(self) -> FolderAttributionAdapter:
        enter = getattr(self.fact_source, "__enter__", None)
        if enter is not None:
            enter()
        return self

    def __exit__(self, *exc: Any) -> None:
        exit_ = getattr(self.fact_source, "__exit__", None)
        if exit_ is not None:
            exit_(*exc)

    def rows(self):
        decisions: list[Any] = []
        rejected = 0
        if self.fact_source is not None:
            facts: list[StgAppFactRow]
            facts, rejected, self.fact_rejects = validate_fact_rows(
                self.fact_source.rows(), max_rejects_kept=self.max_rejects_kept
            )
            decisions, _k2_coverage = resolve_attributions(facts, reconcilers=self.reconcilers)
        rows, coverage = resolve_folder_attributions(
            self.authored,
            self.folder_codes,
            decisions,
            pinned=self.pinned,
        )
        coverage.fact_rows_rejected = rejected
        self.coverage = coverage
        for row in rows:
            yield row.model_dump(mode="json")


class FolderAttributionLoader(BaseLoader):
    """Writes the K7-ruled BELONGS_TO_APPLICATION {role: seal_app_ref}
    folder edges and stamps the run's coverage counts onto its :JobRun so
    the graph_verify invariant (graph-tests/folder-attribution-coverage.yaml)
    can reconcile them."""

    name: ClassVar[str] = "folder_attribution.v1"
    source_id: ClassVar[str | None] = "controlm@[db].drydocs_stg.stg_app_fact"
    cypher_path: ClassVar[Path | None] = (
        Path(__file__).resolve().parent / "cypher" / "folder_attribution.cypher"
    )
    row_model: ClassVar[type] = FolderAttributionRow
    source_label: ClassVar[str] = "csv"  # 'oracle' when the fallback feed is live

    def load(self):
        summary = super().load()
        coverage = getattr(self.adapter, "coverage", None)
        if coverage is not None:
            self._stamp_coverage(coverage)
        return summary

    def _stamp_coverage(self, coverage: FolderAttributionCoverage) -> None:
        # edges_written counts what this run actually touched; the shortfall
        # vs attributed (rows whose folder or Port was absent) is surfaced
        # as dropped_in_graph — reported, never silent.
        result = self.client.run(
            """
            MATCH (run:JobRun {run_id: $run_id})
            OPTIONAL MATCH (:ControlMFolder)-[r:BELONGS_TO_APPLICATION {role: 'seal_app_ref'}]->(:Port)
              WHERE r.last_run_id = $run_id
            WITH run, count(r) AS edges_written
            SET run.eligible_folders   = $eligible_folders,
                run.attributed         = $attributed,
                run.unmatched          = $unmatched,
                run.pinned             = $pinned,
                run.conflict_count     = $conflict_count,
                run.pin_conflict_count = $pin_conflict_count,
                run.edges_written      = edges_written,
                run.dropped_in_graph   = $attributed - edges_written
            RETURN edges_written
            """,
            run_id=self.run_id,
            eligible_folders=coverage.eligible_folders,
            attributed=coverage.attributed,
            unmatched=coverage.unmatched,
            pinned=coverage.pinned,
            conflict_count=len(coverage.conflicts),
            pin_conflict_count=sum(1 for c in coverage.pin_conflicts if c.agrees is not None),
        )
        if result:
            dropped = coverage.attributed - result[0].get("edges_written", 0)
            if dropped:
                LOGGER.warning(
                    "folder_attribution: %d row(s) found no graph endpoints "
                    "(folder or BatchProcessing Port missing) — surfaced as "
                    "JobRun.dropped_in_graph, follow up via the coverage suite.",
                    dropped,
                )


# ---------------------------------------------------------------------------
# Live-graph helpers (thin; the CLI wires these into the adapter)
# ---------------------------------------------------------------------------


def fetch_folder_codes(client: Neo4jClient) -> dict[str, str | None]:
    """Every live folder with its app-code grouping (the fan-out index,
    §B1). A folder outside any :ControlMApplication grouping maps to None —
    it can only resolve through a per-folder row or the K2 fallback."""
    rows = client.run(
        """
        MATCH (f:ControlMFolder) WHERE NOT f:SchemaMeta
        OPTIONAL MATCH (ca:ControlMApplication)-[:CONTAINS_FOLDER]->(f)
        RETURN f.folder_id AS folder_id, ca.name AS app_code
        """
    )
    return {str(r["folder_id"]): (str(r["app_code"]) if r.get("app_code") else None) for r in rows}


def fetch_pinned_folders(client: Neo4jClient) -> dict[str, str]:
    """Folders carrying a manually-asserted folder edge (§F PIN, folder
    grain): the automated write never touches them."""
    rows = client.run(
        """
        MATCH (f:ControlMFolder)-[r:BELONGS_TO_APPLICATION {role: 'seal_app_ref'}]->(p:Port)
        WHERE r.match_method = 'manual'
        RETURN f.folder_id AS folder_id, p.parent_app_id AS app_id
        """
    )
    return {str(r["folder_id"]): str(r["app_id"]) for r in rows}


def check_folder_preconditions(client: Neo4jClient) -> tuple[int, int]:
    """The loader runs only after folders + the SEAL reference exist.
    Returns (folder_count, application_count); the CLI refuses on zeros."""
    rows = client.run(
        """
        OPTIONAL MATCH (f:ControlMFolder) WITH count(f) AS folders
        OPTIONAL MATCH (a:BusinessApplication) RETURN folders, count(a) AS apps
        """
    )
    if not rows:
        return 0, 0
    return int(rows[0].get("folders") or 0), int(rows[0].get("apps") or 0)
