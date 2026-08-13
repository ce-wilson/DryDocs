"""catalog_crosscheck.py — G43: what the data catalog and its neighbours disagree about.

The puzzle-pieces deliverable while lineage completes: **measured lists instead of
guesses**, following the G25 precedent in :mod:`.dpl_registry` (``RegistryCrossCheck``)
— every bucket is COUNTED **and** LISTED, never silent, because a bare count tells you
a disagreement exists and nothing about which rows to go look at.

Four reports, all READ-ONLY. Nothing here writes the graph, stages a node, or emits a
relationship: attribution in particular is a **census, a fact and not an edge** — Epic K
owns what a producing-app id *means*.

1. :func:`dpl_guid_crosscheck` — catalog datasets that claim DPL origin vs the G25
   registry (both / catalog-only / registry-only).
2. :func:`placement_crosscheck` — catalog distribution URNs vs G41 Glue placements, on
   the canonical lowercase ``db.table`` path.
3. :func:`attribution_census` — ``producedby_app_id`` vs SEAL BusinessApplication ids.
4. :func:`registration_census` — registration-source origins + instrumentation coverage.

WHY EACH REPORT CARRIES AN "UNJOINABLE" BUCKET. A row that cannot participate in a join
is not evidence of agreement, and folding it into either side is how a cross-check comes
back clean on a population it never actually compared. A catalog distribution with no
URN, or a DPL-origin dataset with no registry ref, is counted on its own and kept out of
the set arithmetic entirely.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field

from ..model import LineageGraph
from .glue_tables import ZONES
from .snowflake_catalog import CatalogExtract

#: The URN the catalog derives per distribution:
#: ``urn:drydocs:dataasset:{platform}:{namespace}:{asset}``, already lowercased at the
#: source — so EXACTLY six colon-separated fields.
_URN_PREFIX = "urn:drydocs:dataasset:"
_URN_SEGMENTS = 6

#: A dotted ``db.schema`` namespace is fine and needs no special handling: the dot is
#: not the separator, so it rides inside field 5 untouched. A COLON in the platform or
#: namespace is the case that matters, and it is UNPARSEABLE rather than merely awkward
#: — with seven fields, taking the last two silently drops ``db`` and taking fields 4-5
#: silently drops the table, so both readings are wrong and neither is detectably so.
#: Refusing is the only answer that does not manufacture a path. Found by injecting a
#: left-indexed split and watching the suite stay green (J26): the test that was supposed
#: to cover this used a dotted namespace, which cannot tell the two implementations
#: apart, and the module's own comment asserted a reason that was not the real one.


def canonical_path(namespace: str, asset: str) -> str:
    """The join key both sides reduce to: ``db.table``, lowercased and stripped.

    Deliberately dumb — it does NOT try to reconcile a ``db.schema`` namespace against a
    Glue ``database`` that carries only ``db``. A key that quietly normalises away a real
    structural difference manufactures agreement, which is the failure this whole module
    exists to avoid. Mismatches of that shape land in the ``*_only`` buckets, where they
    are visible and countable.
    """
    return f"{namespace.strip().lower()}.{asset.strip().lower()}"


def path_from_urn(urn: str) -> str | None:
    """``urn:drydocs:dataasset:snowflake:db:tbl`` -> ``db.tbl``; ``None`` if unparseable.

    ``None`` is a real answer and callers must bucket it — an unparseable URN is neither
    a match nor a miss.
    """
    text = (urn or "").strip().lower()
    if not text.startswith(_URN_PREFIX):
        return None
    parts = text.split(":")
    if len(parts) != _URN_SEGMENTS:  # too few OR too many — see the note above
        return None
    namespace, asset = parts[4], parts[5]
    if not namespace or not asset:
        return None
    return canonical_path(namespace, asset)


def glue_placement_paths(graph: LineageGraph) -> dict[str, list[str]]:
    """Every G41 placement in *graph*, as ``{db.table: [node_id, ...]}``.

    G41 stamps placements as per-zone node PROPERTIES (``glue_database_<zone>`` /
    ``glue_table_<zone>``) rather than as nodes of their own, so this reads them back the
    same way it wrote them. One path can carry several node ids — the same physical table
    reached from two datasets is a finding, not a key collision, so the ids are kept.
    """
    found: dict[str, list[str]] = {}
    for node_id, node in graph.data_assets.items():
        for zone in ZONES:
            db = node.properties.get(f"glue_database_{zone}", "")
            table = node.properties.get(f"glue_table_{zone}", "")
            if not db or not table:
                continue
            found.setdefault(canonical_path(db, table), []).append(node_id)
    return {path: sorted(set(ids)) for path, ids in found.items()}


# --------------------------------------------------------------------------- (1)


@dataclass
class DplGuidCrossCheck:
    """Catalog DPL-origin datasets vs the G25 DPL registry."""

    catalog_dpl_datasets: int = 0
    registry_datasets: int = 0
    both: list[str] = field(default_factory=list)
    catalog_only: list[str] = field(default_factory=list)
    registry_only: list[str] = field(default_factory=list)
    #: origin=dpl but no registration_source_ref — cannot join, so it is held OUT of the
    #: arithmetic and listed here by catalog GUID rather than counted as a miss.
    catalog_dpl_without_ref: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        return (
            f"catalog_dpl={self.catalog_dpl_datasets} "
            f"registry={self.registry_datasets} | "
            f"both={len(self.both)} "
            f"catalog_only={len(self.catalog_only)} "
            f"registry_only={len(self.registry_only)} | "
            f"unjoinable(no ref)={len(self.catalog_dpl_without_ref)}"
        )


def dpl_guid_crosscheck(catalog: CatalogExtract, registry_dataset_guids) -> DplGuidCrossCheck:
    """Join catalog DPL-origin datasets to the registry on the DPL GUID.

    The join key comes from :meth:`CatalogExtract.dpl_refs`, which G42 published for
    exactly this consumer, rather than being re-derived here. The rule it encodes is not
    obvious and must have ONE home: the catalog's own ``guid`` is a CATALOG identifier
    while the DPL GUID lives in ``registration_source_ref`` (that field's contract reads
    "DPL rows: the DPL GUID"). Joining on the wrong one of the two returns a
    clean-looking zero overlap — a confident wrong answer of precisely the kind this
    report exists to prevent — and a second copy of the rule here is how the two would
    later drift apart.
    """
    dpl_datasets = [r for r in catalog.datasets if r.origin == "dpl"]
    refs = catalog.dpl_refs()
    without_ref = [r.guid for r in dpl_datasets if not (r.registration_source_ref or "").strip()]

    registry = {g for g in registry_dataset_guids if g}
    return DplGuidCrossCheck(
        catalog_dpl_datasets=len(dpl_datasets),
        registry_datasets=len(registry),
        both=sorted(refs & registry),
        catalog_only=sorted(refs - registry),
        registry_only=sorted(registry - refs),
        catalog_dpl_without_ref=sorted(without_ref),
    )


# --------------------------------------------------------------------------- (2)


@dataclass
class PlacementCrossCheck:
    """Catalog distribution URNs vs G41 Glue placements, on ``db.table``."""

    catalog_paths: int = 0
    glue_paths: int = 0
    both: list[str] = field(default_factory=list)
    catalog_only: list[str] = field(default_factory=list)
    glue_only: list[str] = field(default_factory=list)
    #: Distributions that cannot reach a path at all, held out of the arithmetic.
    distributions_no_urn: int = 0
    distributions_urn_unparsed: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        return (
            f"catalog_paths={self.catalog_paths} glue_paths={self.glue_paths} | "
            f"both={len(self.both)} "
            f"catalog_only={len(self.catalog_only)} "
            f"glue_only={len(self.glue_only)} | "
            f"unjoinable: no_urn={self.distributions_no_urn} "
            f"unparsed={len(self.distributions_urn_unparsed)}"
        )


def placement_crosscheck(catalog: CatalogExtract, graph: LineageGraph) -> PlacementCrossCheck:
    """Join catalog distributions to G41 placements on the canonical path. READ-ONLY."""
    catalog_paths: set[str] = set()
    no_urn = 0
    unparsed: list[str] = []
    for dist in catalog.distributions:
        urn = (dist.candidate_asset_urn or "").strip()
        if not urn:
            no_urn += 1
            continue
        path = path_from_urn(urn)
        if path is None:
            unparsed.append(dist.distribution_guid)
            continue
        catalog_paths.add(path)

    glue = set(glue_placement_paths(graph))
    return PlacementCrossCheck(
        catalog_paths=len(catalog_paths),
        glue_paths=len(glue),
        both=sorted(catalog_paths & glue),
        catalog_only=sorted(catalog_paths - glue),
        glue_only=sorted(glue - catalog_paths),
        distributions_no_urn=no_urn,
        distributions_urn_unparsed=sorted(unparsed),
    )


# --------------------------------------------------------------------------- (3)


@dataclass
class AttributionCensus:
    """``producedby_app_id`` vs SEAL BusinessApplication ids — FACT ONLY.

    No edges, no ruling on what attribution means: Epic K owns that. This says which
    ids the catalog asserts and whether SEAL has heard of them.
    """

    datasets: int = 0
    datasets_with_app_id: int = 0
    datasets_without_app_id: int = 0
    distinct_app_ids: int = 0
    known_to_seal: list[str] = field(default_factory=list)
    unknown_to_seal: list[str] = field(default_factory=list)
    #: How many catalog datasets each asserted id carries — an id on one dataset and an
    #: id on four hundred are different findings, and a bare list hides that.
    datasets_by_app_id: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        return (
            f"datasets={self.datasets} with_app_id={self.datasets_with_app_id} "
            f"without={self.datasets_without_app_id} | "
            f"distinct={self.distinct_app_ids} "
            f"known={len(self.known_to_seal)} unknown={len(self.unknown_to_seal)}"
        )


def attribution_census(catalog: CatalogExtract, seal_app_ids) -> AttributionCensus:
    """Census the catalog's producing-app claims against known SEAL ids."""
    known = {str(a).strip() for a in seal_app_ids if str(a).strip()}
    counts: Counter[str] = Counter()
    without = 0
    for record in catalog.datasets:
        app_id = (record.producedby_app_id or "").strip()
        if app_id:
            counts[app_id] += 1
        else:
            without += 1

    asserted = set(counts)
    return AttributionCensus(
        datasets=len(catalog.datasets),
        datasets_with_app_id=sum(counts.values()),
        datasets_without_app_id=without,
        distinct_app_ids=len(asserted),
        known_to_seal=sorted(asserted & known),
        unknown_to_seal=sorted(asserted - known),
        datasets_by_app_id=dict(sorted(counts.items())),
    )


# --------------------------------------------------------------------------- (4)


@dataclass
class RegistrationCensus:
    """Where records claim to come from, and how much of the estate is instrumented."""

    datasets: int = 0
    distributions: int = 0
    #: The ruled three-way origin split (§3): dpl | authority2 | catalog.
    origin_dpl: int = 0
    origin_authority2: int = 0
    origin_other: int = 0
    #: Verbatim upstream authority names, never normalised — a new spelling is a finding.
    dataset_sources: dict[str, int] = field(default_factory=dict)
    distribution_sources: dict[str, int] = field(default_factory=dict)
    #: Instrumentation coverage, carried through from the extract's own accounting.
    not_instrumented: int = 0
    shape_unresolved: int = 0
    shape_ambiguous: int = 0
    urn_underived: int = 0

    def as_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        return (
            f"datasets={self.datasets} distributions={self.distributions} | "
            f"origin: dpl={self.origin_dpl} authority2={self.origin_authority2} "
            f"other={self.origin_other} | "
            f"sources: datasets={len(self.dataset_sources)} "
            f"distributions={len(self.distribution_sources)} | "
            f"not_instrumented={self.not_instrumented} "
            f"shape: unresolved={self.shape_unresolved} ambiguous={self.shape_ambiguous} "
            f"urn_underived={self.urn_underived}"
        )


#: The empty registration source, kept as a NAMED bucket rather than dropped: "no
#: authority claimed" is a census answer, and an absent key would read as zero rows.
NULL_SOURCE = "(null)"


def registration_census(catalog: CatalogExtract) -> RegistrationCensus:
    """Origin + authority census, plus the instrumentation coverage already measured.

    The instrumentation numbers are READ OFF the extract's coverage rather than
    recomputed. They are counted during parse, where the sentinel and the unresolved
    shape are actually observed; recounting from the staged records would silently
    report zero, because staging is exactly where those values were nulled.
    """
    cov = catalog.coverage

    def census(records) -> dict[str, int]:
        counter: Counter[str] = Counter()
        for record in records:
            counter[(record.registration_source or "").strip() or NULL_SOURCE] += 1
        return dict(sorted(counter.items()))

    origins: Counter[str] = Counter((r.origin or "").strip() for r in catalog.datasets)
    return RegistrationCensus(
        datasets=len(catalog.datasets),
        distributions=len(catalog.distributions),
        origin_dpl=origins.get("dpl", 0),
        origin_authority2=origins.get("authority2", 0),
        origin_other=len(catalog.datasets) - origins.get("dpl", 0) - origins.get("authority2", 0),
        dataset_sources=census(catalog.datasets),
        distribution_sources=census(catalog.distributions),
        not_instrumented=cov.sentinel_not_instrumented,
        shape_unresolved=cov.shape_unresolved,
        shape_ambiguous=cov.shape_ambiguous,
        urn_underived=cov.urn_underived,
    )
