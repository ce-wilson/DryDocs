"""G43 — the four data-catalog cross-check reports.

Synthetic fixtures only: real exports stay in the landing zone (the source is
classified Internal — bundles and catalog exports carry real app ids and table
names). No Neo4j, no network, so these run anywhere (J18).

Every test here pins the SAME house rule from two sides: a bucket is counted AND
listed, and a row that cannot participate in the join is held OUT of the set
arithmetic instead of being folded into either side. The second half is the one
worth guarding — an unjoinable row silently counted as a match makes a
cross-check report agreement on a population it never compared.
"""

from __future__ import annotations

from drydocs_lineage.extractors.catalog_crosscheck import (
    NULL_SOURCE,
    attribution_census,
    canonical_path,
    dpl_guid_crosscheck,
    glue_placement_paths,
    path_from_urn,
    placement_crosscheck,
    registration_census,
)
from drydocs_lineage.extractors.snowflake_catalog import (
    CatalogCoverage,
    CatalogDatasetRecord,
    CatalogDistributionRecord,
    CatalogExtract,
)
from drydocs_lineage.model import DataAssetNode, LineageGraph


def _dataset(guid, *, origin="catalog", ref="", app="", source="") -> CatalogDatasetRecord:
    return CatalogDatasetRecord(
        guid=guid,
        origin=origin,
        registration_source_ref=ref,
        producedby_app_id=app,
        registration_source=source,
    )


def _dist(guid, urn="", *, source="") -> CatalogDistributionRecord:
    return CatalogDistributionRecord(
        dataset_guid="ds",
        distribution_guid=guid,
        candidate_asset_urn=urn,
        registration_source=source,
    )


def _graph(*placements: tuple[str, str, str, str]) -> LineageGraph:
    """``(node_id, zone, database, table)`` -> a graph carrying G41 placements."""
    graph = LineageGraph()
    for node_id, zone, db, table in placements:
        node = graph.data_assets.get(node_id) or DataAssetNode(
            node_id=node_id, kind="glue_table", location=""
        )
        node.properties[f"glue_database_{zone}"] = db
        node.properties[f"glue_table_{zone}"] = table
        graph.data_assets[node_id] = node
    return graph


# ---- the join keys -----------------------------------------------------------


def test_the_urn_yields_the_canonical_path() -> None:
    assert path_from_urn("urn:drydocs:dataasset:snowflake:mydb:mytbl") == "mydb.mytbl"


def test_a_dotted_namespace_rides_inside_its_field_untouched() -> None:
    """``db.schema`` needs no special handling — the dot is not the separator."""
    assert path_from_urn("urn:drydocs:dataasset:snowflake:mydb.myschema:mytbl") == (
        "mydb.myschema.mytbl"
    )


def test_an_over_segmented_urn_is_refused_rather_than_mis_split() -> None:
    """A COLON inside platform/namespace makes the URN ambiguous, and both readings
    of it are wrong: last-two drops ``db``, fields-4-5 drops the table. Refusing is
    the only answer that does not manufacture a path.

    This case exists because injecting a left-indexed split left the suite GREEN
    (J26) — the dotted-namespace test above cannot separate the two implementations,
    so it was guarding a property nobody had actually tested.
    """
    assert path_from_urn("urn:drydocs:dataasset:snow:db:schema:tbl") is None


def test_the_path_is_lowercased_on_both_sides() -> None:
    assert path_from_urn("URN:DRYDOCS:DATAASSET:SNOW:MyDb:MyTbl") == "mydb.mytbl"
    assert canonical_path("  MyDb ", "MyTbl") == "mydb.mytbl"


def test_an_unparseable_urn_is_none_rather_than_a_guess() -> None:
    """None is a real answer the caller must bucket — neither a match nor a miss."""
    assert path_from_urn("") is None
    assert path_from_urn("not-a-urn-at-all") is None
    assert path_from_urn("urn:drydocs:dataasset:snowflake") is None
    assert path_from_urn("urn:drydocs:dataasset:snow:db:") is None


def test_placements_are_read_back_from_the_per_zone_properties() -> None:
    graph = _graph(
        ("n1", "raw", "RawDb", "Tbl"),
        ("n1", "trusted", "TrustDb", "Tbl"),
        ("n2", "refined", "RefDb", "Other"),
    )
    assert glue_placement_paths(graph) == {
        "rawdb.tbl": ["n1"],
        "trustdb.tbl": ["n1"],
        "refdb.other": ["n2"],
    }


def test_a_half_stamped_placement_is_not_a_path() -> None:
    """Database without table (or vice versa) cannot make a key — it must not
    produce `db.` and silently join against nothing."""
    graph = LineageGraph()
    node = DataAssetNode(node_id="n1", kind="glue_table", location="")
    node.properties["glue_database_raw"] = "db"  # no glue_table_raw
    graph.data_assets["n1"] = node
    assert glue_placement_paths(graph) == {}


def test_one_path_reached_from_two_nodes_keeps_both_ids() -> None:
    """A finding, not a key collision."""
    graph = _graph(("n1", "raw", "db", "t"), ("n2", "raw", "db", "t"))
    assert glue_placement_paths(graph) == {"db.t": ["n1", "n2"]}


# ---- (1) catalog DPL-origin datasets vs the G25 registry ---------------------


def test_dpl_guids_bucket_three_ways_and_each_is_listed() -> None:
    catalog = CatalogExtract(
        datasets=[
            _dataset("c1", origin="dpl", ref="G-BOTH"),
            _dataset("c2", origin="dpl", ref="G-CATALOG"),
            _dataset("c3", origin="catalog", ref="G-IGNORED"),  # not DPL origin
        ]
    )
    report = dpl_guid_crosscheck(catalog, {"G-BOTH", "G-REGISTRY"})
    assert report.both == ["G-BOTH"]
    assert report.catalog_only == ["G-CATALOG"]
    assert report.registry_only == ["G-REGISTRY"]
    assert report.catalog_dpl_datasets == 2, "the non-DPL row must not be counted in"
    assert "G-IGNORED" not in report.catalog_only


def test_a_dpl_dataset_with_no_ref_is_held_out_of_the_arithmetic() -> None:
    """The load-bearing case: it is unjoinable, so it is neither a match nor a miss.

    Counting it as catalog_only would report a registry gap that does not exist;
    dropping it would hide a catalog defect. It gets its own list.
    """
    catalog = CatalogExtract(
        datasets=[_dataset("c1", origin="dpl", ref=""), _dataset("c2", origin="dpl", ref="G-1")]
    )
    report = dpl_guid_crosscheck(catalog, {"G-1"})
    assert report.catalog_dpl_without_ref == ["c1"]
    assert report.catalog_only == []
    assert report.both == ["G-1"]
    assert report.catalog_dpl_datasets == 2


def test_the_dpl_join_key_is_the_registry_ref_not_the_catalog_guid() -> None:
    """Joining on the catalog's own guid returns a clean-looking zero overlap."""
    catalog = CatalogExtract(datasets=[_dataset("CATALOG-GUID", origin="dpl", ref="DPL-GUID")])
    report = dpl_guid_crosscheck(catalog, {"DPL-GUID"})
    assert report.both == ["DPL-GUID"]
    assert report.catalog_only == []


# ---- (2) distribution URNs vs G41 glue placements ----------------------------


def test_placements_bucket_three_ways_on_the_canonical_path() -> None:
    catalog = CatalogExtract(
        distributions=[
            _dist("d1", "urn:drydocs:dataasset:snow:db:both"),
            _dist("d2", "urn:drydocs:dataasset:snow:db:catalogonly"),
        ]
    )
    graph = _graph(("n1", "raw", "db", "both"), ("n2", "raw", "db", "glueonly"))
    report = placement_crosscheck(catalog, graph)
    assert report.both == ["db.both"]
    assert report.catalog_only == ["db.catalogonly"]
    assert report.glue_only == ["db.glueonly"]


def test_case_only_differences_join_rather_than_splitting() -> None:
    catalog = CatalogExtract(distributions=[_dist("d1", "urn:drydocs:dataasset:snow:DB:TBL")])
    report = placement_crosscheck(catalog, _graph(("n1", "raw", "db", "tbl")))
    assert report.both == ["db.tbl"]
    assert report.catalog_only == []


def test_urnless_and_unparseable_distributions_stay_out_of_the_arithmetic() -> None:
    catalog = CatalogExtract(
        distributions=[
            _dist("d-none", ""),
            _dist("d-junk", "nonsense"),
            _dist("d-ok", "urn:drydocs:dataasset:snow:db:tbl"),
        ]
    )
    report = placement_crosscheck(catalog, _graph(("n1", "raw", "db", "tbl")))
    assert report.distributions_no_urn == 1
    assert report.distributions_urn_unparsed == ["d-junk"]
    assert report.both == ["db.tbl"]
    assert report.catalog_only == [], "an unjoinable row must not read as a catalog gap"
    assert report.catalog_paths == 1


def test_a_dotted_namespace_does_not_silently_match_a_bare_glue_database() -> None:
    """The key is deliberately dumb. `db.schema.tbl` != `db.tbl`, and the difference
    shows up as two visible one-sided rows rather than being normalised away."""
    catalog = CatalogExtract(
        distributions=[_dist("d1", "urn:drydocs:dataasset:snow:db.schema:tbl")]
    )
    report = placement_crosscheck(catalog, _graph(("n1", "raw", "db", "tbl")))
    assert report.both == []
    assert report.catalog_only == ["db.schema.tbl"]
    assert report.glue_only == ["db.tbl"]


def test_one_physical_table_reached_from_two_datasets_is_surfaced() -> None:
    """Gate clause A5's evidence. The set arithmetic collapses both distributions to
    ONE member of ``catalog_paths``, so without this the collision is invisible — and
    A5 rules what the model does about it under both the one-node and two-node readings.

    Found at the G44 ontology second pass: the gate cited a report field that did not
    exist yet, which is the dangling-reference class Idea-110/115 are about.
    """
    catalog = CatalogExtract(
        distributions=[
            CatalogDistributionRecord(
                dataset_guid="ds-A",
                distribution_guid="d1",
                candidate_asset_urn="urn:drydocs:dataasset:snow:db:shared",
            ),
            CatalogDistributionRecord(
                dataset_guid="ds-B",
                distribution_guid="d2",
                candidate_asset_urn="urn:drydocs:dataasset:snow:db:shared",
            ),
        ]
    )
    report = placement_crosscheck(catalog, _graph(("n1", "raw", "db", "shared")))
    assert report.paths_shared_by_datasets == {"db.shared": ["ds-A", "ds-B"]}
    assert report.catalog_paths == 1, "the set genuinely collapses them — hence the field"
    assert report.both == ["db.shared"]


def test_two_distributions_of_the_same_dataset_are_not_a_collision() -> None:
    """Two materializations of one logical dataset on one path is ordinary, not the
    A5 case — flagging it would bury the real finding in noise."""
    catalog = CatalogExtract(
        distributions=[
            CatalogDistributionRecord(
                dataset_guid="ds-A",
                distribution_guid="d1",
                candidate_asset_urn="urn:drydocs:dataasset:snow:db:t",
            ),
            CatalogDistributionRecord(
                dataset_guid="ds-A",
                distribution_guid="d2",
                candidate_asset_urn="urn:drydocs:dataasset:snow:db:t",
            ),
        ]
    )
    report = placement_crosscheck(catalog, _graph(("n1", "raw", "db", "t")))
    assert report.paths_shared_by_datasets == {}


def test_the_placement_crosscheck_never_mutates_the_graph() -> None:
    catalog = CatalogExtract(distributions=[_dist("d1", "urn:drydocs:dataasset:snow:db:tbl")])
    graph = _graph(("n1", "raw", "db", "tbl"))
    before = {k: dict(v.properties) for k, v in graph.data_assets.items()}
    placement_crosscheck(catalog, graph)
    assert {k: dict(v.properties) for k, v in graph.data_assets.items()} == before
    assert graph.rels == set()


# ---- (3) attribution census — FACT ONLY -------------------------------------


def test_attribution_census_counts_datasets_per_app_and_splits_on_seal() -> None:
    catalog = CatalogExtract(
        datasets=[
            _dataset("c1", app="70001"),
            _dataset("c2", app="70001"),
            _dataset("c3", app="99999"),
            _dataset("c4", app=""),
        ]
    )
    census = attribution_census(catalog, {"70001", "70002"})
    assert census.known_to_seal == ["70001"]
    assert census.unknown_to_seal == ["99999"]
    assert census.datasets_by_app_id == {"70001": 2, "99999": 1}
    assert census.datasets_without_app_id == 1
    assert census.datasets_with_app_id == 3
    assert census.distinct_app_ids == 2


def test_the_per_app_counts_are_kept_because_one_and_four_hundred_differ() -> None:
    catalog = CatalogExtract(datasets=[_dataset(f"c{i}", app="70001") for i in range(400)])
    census = attribution_census(catalog, set())
    assert census.datasets_by_app_id == {"70001": 400}
    assert census.unknown_to_seal == ["70001"]


def test_attribution_census_emits_no_edges_and_reads_as_fact() -> None:
    """Epic K owns what attribution MEANS; this report may only state it."""
    census = attribution_census(CatalogExtract(datasets=[_dataset("c1", app="70001")]), set())
    assert not hasattr(census, "rels")
    assert "70001" in census.as_dict()["datasets_by_app_id"]


# ---- (4) registration-source + instrumentation census ------------------------


def test_registration_census_splits_origin_three_ways() -> None:
    catalog = CatalogExtract(
        datasets=[
            _dataset("c1", origin="dpl"),
            _dataset("c2", origin="authority2"),
            _dataset("c3", origin="catalog"),
            _dataset("c4", origin=""),
        ]
    )
    census = registration_census(catalog)
    assert (census.origin_dpl, census.origin_authority2) == (1, 1)
    assert census.origin_other == 2, "catalog + blank both land in 'other', neither is dropped"


def test_the_empty_registration_source_is_a_named_bucket_not_a_missing_key() -> None:
    catalog = CatalogExtract(
        datasets=[_dataset("c1", source="AUTH-A"), _dataset("c2", source="")],
        distributions=[_dist("d1", source="AUTH-B")],
    )
    census = registration_census(catalog)
    assert census.dataset_sources == {"AUTH-A": 1, NULL_SOURCE: 1}
    assert census.distribution_sources == {"AUTH-B": 1}


def test_instrumentation_coverage_is_read_from_the_extract_not_recomputed() -> None:
    """Recomputing from staged records reports ZERO: staging is where the sentinel
    was nulled and the shape emptied, so the evidence only exists at parse time."""
    coverage = CatalogCoverage(
        sentinel_not_instrumented=7, shape_unresolved=3, shape_ambiguous=1, urn_underived=5
    )
    census = registration_census(CatalogExtract(coverage=coverage))
    assert census.not_instrumented == 7
    assert (census.shape_unresolved, census.shape_ambiguous) == (3, 1)
    assert census.urn_underived == 5


# ---- the shared house rule ---------------------------------------------------


def test_every_report_is_serializable_and_summarizes_without_a_graph() -> None:
    catalog = CatalogExtract(
        datasets=[_dataset("c1", origin="dpl", ref="G-1", app="70001")],
        distributions=[_dist("d1", "urn:drydocs:dataasset:snow:db:tbl")],
    )
    graph = _graph(("n1", "raw", "db", "tbl"))
    for report in (
        dpl_guid_crosscheck(catalog, {"G-1"}),
        placement_crosscheck(catalog, graph),
        attribution_census(catalog, {"70001"}),
        registration_census(catalog),
    ):
        assert isinstance(report.as_dict(), dict)
        assert isinstance(report.summary(), str) and report.summary()
