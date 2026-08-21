"""Folder-grain attribution loader (backlog K8) — app-code defined mapping
plus the demoted K2 fallback -> (:ControlMFolder)-[:BELONGS_TO_APPLICATION
{role: seal_app_ref}]->(:Port) edges.

Gate seal-app-ref-edge-reshape (SIGNED OFF 2026-08-03, config/gate-log.md):

- §A1  Attribution grain is the FOLDER; jobs inherit via CONTAINS_JOB and no
       per-job application edge is authored.
- §B1  ONE authoring mechanism: a steward-defined row per Control-M app code
       (drydocs_core.mapping_store, K9); this loader fans a code-level row
       out over scheduler_contains_folder. A per-folder row (folder_id set) narrows
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

K18 (2026-08-05) — the two silent-fan-out routes closed:

- DERIVATION: the K7 row kind is mechanically derivable — prefix positions
  3-5 of an app code / folder name matched against the CLOSED platform-code
  list (six framework codes; values in the Internal twin, see
  knowledge/standards/technology/folder-naming-convention.md §Tier
  discrimination). A code-level row that carries a SEAL is NOT read as an
  application attribution when the name says platform: fan-out is blocked
  and the disagreement queues (the claim-time ruling: two row-kind signals
  never resolve silently; derivation wins for BLOCKING, a human rules the
  row).
- AUTHORING: the platform declaration is an explicit row kind carrying the
  platform's OWN app_id (declare-by-absence retired at the store, K18) —
  the declaration attributes nothing BY KIND, not by a missing field.
- `tier` renamed `row_kind` end to end (store column, wire, model, edge
  property) before the ambiguous name could surface in a QuerySpec — the K2
  match-precedence tiers keep their name; the value spaces never collided,
  the prose did.

K19 (2026-08-05) — a mapping is an AS-OF assertion, not a fact. The 3-char
app-code namespace is scarce, so codes are retired and REISSUED with a
different meaning (`DDC`: created for one purpose, repurposed, the original
gone). Nothing structural stops a reused code from silently inheriting its
predecessor's mapping, so folders authored under the NEW meaning keep an
attribution that is now wrong. The check: any authored row whose
``authored_on`` PREDATES the first-seen date of folders it is being applied
to queues as a ``MappingAgeSuspect`` — a REVIEW queue with counts, never an
automatic re-attribution, because a reissued code and a genuinely growing
application are indistinguishable without a human. Detection only:
effective dating (valid_from/valid_to) would preserve mapping history,
which is an ontology question for a gate (the item's own scope note).
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from drydocs_core.models import FolderAttributionRow, StgAppFactRow
from drydocs_core.repo_paths import repo_root

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

# §G1 (K11): the confirmed mapping act authors the app -> orchestrator
# USES_SOFTWARE edge. This module IS the Control-M attribution domain (§G:
# AutoSys drops in as a SIBLING domain with its own loaders), so the
# orchestrator is a per-domain constant — resolved from the C12-confirmed
# platforms taxonomy, never hardcoded in Cypher.
ORCHESTRATOR_PLATFORM_ID = "controlm"

# K18: the closed platform-code list (six framework codes, DAT SRE standard —
# closed means a seventh is a standards change, not a discovery). VALUES live
# in the Internal twin; this mechanism is publishable and the tests use
# synthetic codes. A missing file degrades to an EMPTY set: the derivation
# guard goes inert (pre-K18 behavior), it never invents codes.
_REPO_ROOT = repo_root(Path(__file__).resolve().parents[2])
PLATFORM_CODES_PATH = _REPO_ROOT / "internal" / "standards" / "technology" / "platform-codes.yaml"


def load_platform_codes(path: Path | None = None) -> frozenset[str]:
    """The 3-char platform codes from the values twin, upper-cased. Empty
    when the file is absent (public clone / pre-capture environment) — the
    caller's derivation guard simply never fires."""
    import yaml

    path = Path(path) if path is not None else PLATFORM_CODES_PATH
    if not path.exists():
        return frozenset()
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    codes = frozenset(
        str(row.get("code") or "").strip().upper()
        for row in doc.get("platform_codes", [])
        if row.get("code")
    )
    return codes


def platform_prefix(name: str | None) -> str | None:
    """Positions 3-5 of a Control-M app code (``PRAOC`` -> ``AOC``) or folder
    name (``PRAOCG`` -> ``AOC``) — the segment the PRAOCG convention assigns
    the framework/application mnemonic. None when the name is too short to
    carry one (e.g. the 5-char ``PUDLY`` platform-ordering exception still
    parses; a 4-char name does not)."""
    if not name:
        return None
    text = str(name).strip().upper()
    if len(text) < 5:
        return None
    return text[2:5]


def orchestrator_product_ref(
    platform_id: str = ORCHESTRATOR_PLATFORM_ID,
    platforms_path: Path | None = None,
) -> str:
    """The domain orchestrator's software-registry product id, from
    config/taxonomy/platforms.yaml (the C12 crosswalk seed rows). Raises if
    the row or its ref is missing — an attribution domain without an
    orchestrator ref cannot honor §G1, so this fails loudly at wiring time
    rather than silently skipping the edge forever."""
    import yaml

    if platforms_path is None:
        from .batch_port_orchestrator import DEFAULT_PLATFORMS_PATH

        platforms_path = DEFAULT_PLATFORMS_PATH
    doc = yaml.safe_load(Path(platforms_path).read_text(encoding="utf-8"))
    for row in doc.get("platforms", []):
        if row.get("id") == platform_id:
            ref = row.get("software_registry_ref")
            if ref:
                return str(ref)
            raise ValueError(
                f"platforms.yaml row '{platform_id}' has no software_registry_ref "
                "— the §G1 orchestrator edge cannot be authored without it"
            )
    raise ValueError(f"platforms.yaml has no platform row '{platform_id}'")


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


@dataclass(frozen=True)
class RowKindDisagreement:
    """A CODE-level disagreement between the name-derived row kind and the
    authored row's declared kind (K18 claim-time ruling: never resolved
    silently — derivation wins for BLOCKING fan-out, a human rules the row).

    ``blocked_fan_out`` is True for the dangerous direction (row claims an
    application kind, the name says platform — fan-out suppressed); False for
    the inverse (row declares platform, the name says application — nothing
    was going to fan out, but the list or the row is still wrong)."""

    app_code: str
    declared_kind: str
    derived_kind: str
    app_id: str | None
    blocked_fan_out: bool


@dataclass(frozen=True)
class MappingAgeSuspect:
    """An authored row older than folders it is being applied to (K19).

    The code may have been REISSUED since the row was authored — or the
    application simply grew. The two are indistinguishable without a human,
    so this is review-queue material with counts, never a re-attribution.
    One suspect per authored ROW (each row is its own as-of assertion), so a
    fresh override on a stale defined row shows exactly which assertion aged.
    Same-day is NOT postdating — only a folder first seen strictly after
    ``authored_on`` counts."""

    app_code: str
    origin: str
    authored_on: str
    app_id: str | None
    folders_postdating: int
    folders_covered: int
    earliest_postdating_first_seen: str
    sample_folders: tuple[str, ...]


@dataclass
class FolderAttributionCoverage:
    """Per-run accounting. Invariant: attributed + unmatched + conflicts +
    pinned == eligible_folders. Row-kind disagreements are CODE-grain review
    material — their folders land in ``conflicts`` as platform-unresolved,
    so they ride the invariant through that count, not their own."""

    eligible_folders: int = 0
    attributed: int = 0
    unmatched: int = 0
    pinned: int = 0
    attributed_by_origin: dict[str, int] = field(default_factory=dict)
    conflicts: list[FolderConflict] = field(default_factory=list)
    pin_conflicts: list[FolderPinConflict] = field(default_factory=list)
    row_kind_disagreements: list[RowKindDisagreement] = field(default_factory=list)
    # K19: review-only, OUTSIDE the invariant — a suspect folder is still
    # attributed (the mapping stands until a human rules it), so it already
    # rides the invariant through `attributed`.
    mapping_age_suspects: list[MappingAgeSuspect] = field(default_factory=list)
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
            "row_kind_disagreement_count": len(self.row_kind_disagreements),
            "mapping_age_suspect_count": len(self.mapping_age_suspects),
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
    platform_codes: frozenset[str] | None = None,
) -> tuple[list[FolderAttributionRow], FolderAttributionCoverage]:
    """Resolve every folder to at most ONE application (the 1:1 rule).

    ``authored`` — app-code store rows (mapping_store.app_code_rows_from_store
    dicts: app_code / folder_id / row_kind / app_id / origin, all authored
    origins). ``folder_codes`` — folder_id -> app_code (None for a folder
    with no app-code grouping), the graph fan-out index; its keys define the
    ELIGIBLE folder population. ``k2_decisions`` — job-grain
    SealAttributionRow decisions from the demoted K2 policy (§B3 fallback).
    ``pinned`` — folder_id -> app_id for folders carrying an existing
    manual-pin edge; excluded from the automated write, disagreements
    surfaced (§F parity). ``platform_codes`` — the K18 closed list
    (load_platform_codes()); empty/None leaves the derivation guard inert.
    """
    pinned = pinned or {}
    platform_codes = platform_codes or frozenset()
    coverage = FolderAttributionCoverage()
    coverage.eligible_folders = len(folder_codes)

    # Index authored rows: per-folder rows and code-level rows. Code-level
    # discrimination is BY ROW KIND (K18) — a platform declaration carries
    # the platform's own app_id and still attributes nothing; the legacy
    # empty-app_id shape is honored as a declaration for back-compat.
    by_folder: dict[str, list[Mapping[str, Any]]] = {}
    by_code: dict[str, list[Mapping[str, Any]]] = {}
    declared_platform_codes: set[str] = set()
    for row in authored:
        code = str(row.get("app_code") or "").strip()
        folder_id = row.get("folder_id")
        kind = str(row.get("row_kind") or "").strip()
        derived_platform = platform_prefix(code) in platform_codes
        if folder_id:
            by_folder.setdefault(str(folder_id).strip(), []).append(row)
        elif kind == "platform" or not row.get("app_id"):
            # The code-level platform DECLARATION: attributes nothing BY
            # KIND; marks the code so its unresolved folders surface as
            # platform-unresolved instead of falling back (§B2 — a declared
            # code HAS a defined row, so §B3's "no defined row" fallback
            # does not apply). The row's app_id (the platform's own SEAL) is
            # a recorded fact, never a fan-out target.
            declared_platform_codes.add(code)
            if platform_codes and not derived_platform:
                # Inverse disagreement: declared platform, name says
                # application. Nothing was going to fan out — but either the
                # row or the closed list is wrong, so a human rules it.
                coverage.row_kind_disagreements.append(
                    RowKindDisagreement(
                        app_code=code,
                        declared_kind=kind or "platform",
                        derived_kind="application",
                        app_id=(str(row.get("app_id")) if row.get("app_id") else None),
                        blocked_fan_out=False,
                    )
                )
        elif derived_platform:
            # THE K18 GUARD — the silent fan-out this item exists to stop.
            # The row claims an application kind (seal-born/dual-coded) but
            # prefix positions 3-5 name a platform framework: `AOC -> SEAL`
            # is true of the platform and false of every hosted consumer
            # folder it would stamp. Derivation wins for BLOCKING (claim-time
            # ruling): no fan-out; the code is treated as declared platform
            # (folders resolve per folder or surface platform-unresolved)
            # and the disagreement queues for a human.
            declared_platform_codes.add(code)
            coverage.row_kind_disagreements.append(
                RowKindDisagreement(
                    app_code=code,
                    declared_kind=kind or "?",
                    derived_kind="platform",
                    app_id=str(row.get("app_id")),
                    blocked_fan_out=True,
                )
            )
        else:
            by_code.setdefault(code, []).append(row)

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
                    row_kind=row.get("row_kind"),
                    source=AUTHORED_SOURCE,
                    authored_by=row.get("authored_by"),
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
                    row_kind=None,
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
# K19 — mapping-age detection (pure; review queue, never a write)
# ---------------------------------------------------------------------------


def detect_mapping_age_suspects(
    authored: Iterable[Mapping[str, Any]],
    folder_codes: Mapping[str, str | None],
    folder_first_seen: Mapping[str, str],
    *,
    max_sample: int = 10,
) -> list[MappingAgeSuspect]:
    """Answer "is this mapping older than the folders it is being applied
    to?" — one :class:`MappingAgeSuspect` per authored row with at least one
    folder first seen strictly AFTER the row's ``authored_on``.

    ``folder_first_seen`` maps folder_id -> ISO first-seen date (the graph's
    ``ControlMFolder.first_seen_at``, date part). Comparison is on the date
    part only, so a folder first seen the same day the row was authored does
    not count. Rows without ``authored_on`` and folders without a first-seen
    date are skipped — no date, no age claim. Every row KIND is checked
    (a platform declaration ages the same way an attribution does); a
    per-folder row is checked against its one folder only.
    """
    suspects: list[MappingAgeSuspect] = []
    for row in authored:
        authored_on = str(row.get("authored_on") or "").strip()[:10]
        if not authored_on:
            continue
        code = str(row.get("app_code") or "").strip()
        folder_id = row.get("folder_id")
        if folder_id:
            covered = [str(folder_id).strip()]
        else:
            covered = sorted(f for f, c in folder_codes.items() if c == code)
        postdating = sorted(
            f for f in covered if str(folder_first_seen.get(f) or "")[:10] > authored_on
        )
        if not postdating:
            continue
        suspects.append(
            MappingAgeSuspect(
                app_code=code,
                origin=str(row.get("origin") or ""),
                authored_on=authored_on,
                app_id=(str(row.get("app_id")) if row.get("app_id") else None),
                folders_postdating=len(postdating),
                folders_covered=len(covered),
                earliest_postdating_first_seen=min(
                    str(folder_first_seen[f])[:10] for f in postdating
                ),
                sample_folders=tuple(postdating[:max_sample]),
            )
        )
    return suspects


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
        platform_codes: frozenset[str] | None = None,
        folder_first_seen: Mapping[str, str] | None = None,
        max_rejects_kept: int = 20,
    ) -> None:
        self.authored = list(authored)
        self.folder_codes = dict(folder_codes)
        self.fact_source = fact_source
        self.reconcilers = reconcilers or TierReconcilers()
        self.pinned = dict(pinned or {})
        self.platform_codes = platform_codes if platform_codes is not None else frozenset()
        # K19: folder_id -> ISO first-seen date; empty leaves the age check inert.
        self.folder_first_seen = dict(folder_first_seen or {})
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
            platform_codes=self.platform_codes,
        )
        coverage.fact_rows_rejected = rejected
        coverage.mapping_age_suspects = detect_mapping_age_suspects(
            self.authored, self.folder_codes, self.folder_first_seen
        )
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

    def extra_cypher_params(self) -> dict[str, Any]:
        # §G1 (K11): the domain orchestrator ref for the confirmed
        # USES_SOFTWARE authoring — a per-domain constant, not a row value.
        return {"orchestrator_product_id": orchestrator_product_ref()}

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
            OPTIONAL MATCH (:BusinessApplication)-[u:USES_SOFTWARE {source: 'app-code-mapping'}]->(:SoftwareProduct)
              WHERE u.last_run_id = $run_id
            WITH run, edges_written, count(u) AS orchestrator_edges
            SET run.eligible_folders   = $eligible_folders,
                run.attributed         = $attributed,
                run.unmatched          = $unmatched,
                run.pinned             = $pinned,
                run.conflict_count     = $conflict_count,
                run.pin_conflict_count = $pin_conflict_count,
                run.row_kind_disagreements = $row_kind_disagreements,
                run.mapping_age_suspects   = $mapping_age_suspects,
                run.edges_written      = edges_written,
                run.orchestrator_edges = orchestrator_edges,
                run.dropped_in_graph   = $attributed - edges_written
            RETURN edges_written, orchestrator_edges
            """,
            run_id=self.run_id,
            eligible_folders=coverage.eligible_folders,
            attributed=coverage.attributed,
            unmatched=coverage.unmatched,
            pinned=coverage.pinned,
            conflict_count=len(coverage.conflicts),
            pin_conflict_count=sum(1 for c in coverage.pin_conflicts if c.agrees is not None),
            row_kind_disagreements=len(coverage.row_kind_disagreements),
            mapping_age_suspects=len(coverage.mapping_age_suspects),
        )
        # K19: reported, never re-attributed — a reissued code and a growing
        # application look identical from here; a human rules each suspect.
        if coverage.mapping_age_suspects:
            LOGGER.warning(
                "folder_attribution: %d mapping(s) predate folders they were "
                "applied to (codes: %s) — possible reissued code(s), review "
                "queue in the coverage report.",
                len(coverage.mapping_age_suspects),
                ", ".join(sorted({s.app_code for s in coverage.mapping_age_suspects})),
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
            # §G1: attribution landed but no orchestrator edge did — the
            # software registry (product ref from platforms.yaml) is not in
            # this graph. Reported, never silent.
            if result[0].get("edges_written", 0) and not result[0].get("orchestrator_edges", 0):
                LOGGER.warning(
                    "folder_attribution: attribution edges landed but NO "
                    "orchestrator USES_SOFTWARE edge was authored — the "
                    "'%s' SoftwareProduct is not loaded (run "
                    "load-software-registry first).",
                    orchestrator_product_ref(),
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


def fetch_folder_first_seen(client: Neo4jClient) -> dict[str, str]:
    """Every live folder's first-seen DATE (K19 age-check input). The date
    part only — same-day authoring must not read as postdating. A folder
    without the stamp is simply absent (no date, no age claim)."""
    rows = client.run(
        """
        MATCH (f:ControlMFolder)
        WHERE NOT f:SchemaMeta AND f.first_seen_at IS NOT NULL
        RETURN f.folder_id AS folder_id, toString(date(f.first_seen_at)) AS first_seen
        """
    )
    return {str(r["folder_id"]): str(r["first_seen"]) for r in rows}


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
