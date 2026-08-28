"""Q15 — the four agent-navigation QuerySpecs over the vendor-docs backbone.

Plan (knowledge/upgrade-plans/vendor-docs-agent-navigation.md section 4): an
agent usually arrives knowing the noun, so the name-addressable path is
primary and similarity search is demoted to the FALLBACK. Registration in
QUERY_SPECS *is* /ask reachability — the graph_qa router's catalog
(agents/common/specs_catalog.catalog_lines) derives one line per registered
spec, so nothing here touches /raw-cypher.

Offline by design (J18): the corpus is loaded on NO machine yet (Q13 close;
the Q24 flip + first load is desktop-bound, Q25 mints the entity core), so
these tests pin the CONTRACT — citation columns, chunk-free rows, bounded
expansion, the fallback demotion — and the live rows arrive with the loads.
"""

from __future__ import annotations

import re

from drydocs_api.query_specs import QUERY_SPECS

LOOKUP = "docs.utility-lookup.v1"
BROWSE = "docs.section-browse.v1"
SIBLINGS = "docs.role-siblings.v1"
SEARCH = "docs.search.v1"
ALL_FOUR = (LOOKUP, BROWSE, SIBLINGS, SEARCH)

#: the R5 citation surface: every row must let the answer say where it came
#: from and WHICH RELEASE it describes (the 9.0.20-vs-9.0.21 caveat).
CITATION_COLUMNS = ("source_url", "doc_version", "trust")

_VARLEN = re.compile(r"\[[^\]]*\*")  # any [:REL*], [:REL*1..3], [*] form


def test_all_four_are_registered_and_internal() -> None:
    for spec_id in ALL_FOUR:
        spec = QUERY_SPECS[spec_id]
        assert spec.database == "drydocs"
        assert spec.classification == "internal"


def test_every_row_carries_the_citation_surface() -> None:
    for spec_id in ALL_FOUR:
        spec = QUERY_SPECS[spec_id]
        names = [c.name for c in spec.columns]
        for col in CITATION_COLUMNS:
            assert col in names, f"{spec_id}: missing citation column {col}"
        # O52 discipline: every declared column is a real RETURN alias
        for col in names:
            assert f"AS {col}" in spec.cypher, f"{spec_id}: {col}"


def test_chunk_text_is_never_returned_here() -> None:
    """Chunk-free by default — agent context is the scarce resource. Triage on
    abstract + page_role; docs.chunks.v1 is the deliberate second step."""
    for spec_id in ALL_FOUR:
        cy = QUERY_SPECS[spec_id].cypher
        assert ":Chunk" not in cy, f"{spec_id} touches chunk text"
        assert "text" not in [c.name for c in QUERY_SPECS[spec_id].columns]


def test_expansion_is_bounded() -> None:
    """No unbounded variable-length traversal anywhere, and every spec is
    LIMIT-bounded."""
    for spec_id in ALL_FOUR:
        cy = QUERY_SPECS[spec_id].cypher
        assert not _VARLEN.search(cy), f"{spec_id}: variable-length traversal"
        assert "LIMIT $limit" in cy, f"{spec_id}: no row bound"


def test_lookup_is_exact_match_primary_and_search_is_the_fallback() -> None:
    lookup = QUERY_SPECS[LOOKUP]
    assert "MATCH (u:ControlMUtility {name: $name})" in lookup.cypher
    search = QUERY_SPECS[SEARCH]
    assert "FALLBACK" in search.description
    assert LOOKUP in search.description  # the demotion names the primary path


def test_planned_terms_are_written_down_exactly_where_needed() -> None:
    """IN_SECTION / SUBSECTION_OF are planned-only until the Q24 load; naming
    them requires the written-down degradation (R20). Nothing else may carry
    the exemption — the list must shrink when the loader lands."""
    assert QUERY_SPECS[BROWSE].planned_terms == ("IN_SECTION", "SUBSECTION_OF")
    for spec_id in (LOOKUP, SIBLINGS, SEARCH):
        assert QUERY_SPECS[spec_id].planned_terms == ()


def test_required_params_and_the_shared_limit() -> None:
    by_first_param = {LOOKUP: "name", BROWSE: "section_id", SIBLINGS: "doc_id", SEARCH: "q"}
    for spec_id, first in by_first_param.items():
        params = QUERY_SPECS[spec_id].params
        assert params[0].name == first and params[0].type == "string"
        assert params[-1].name == "limit" and params[-1].default is not None
