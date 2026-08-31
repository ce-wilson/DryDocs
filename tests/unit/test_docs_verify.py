"""Q7 — `docs-verify` reconciliation, driven entirely against a fake client.

No Neo4j: `verify()` takes `run(database, cypher, params)` as its only I/O seam,
so every status below is exercised offline. The fake answers from a dict keyed by
database, which is what makes the wrong-db case testable at all — it is the one
status you cannot observe by querying a single database.
"""

from __future__ import annotations

import pytest

from drydocs_core.docs_verify import (
    DB_ABSENT,
    LOADED,
    MISSING,
    STALE,
    UNSHAPED,
    WRONG_DB,
    CorpusRow,
    Summary,
    count_query,
    exit_code,
    locator_of,
    verify,
)

# The available-databases fixture. `ddlineage` was in this tuple until its retirement
# (2026-08-04, ADR 0002 X1 amendment); no test keyed on its presence.
DATABASES = ("drydocs", "ddcontext")


def _fake(graph: dict[str, dict[str, dict]]):
    """`graph[database][value] = {documents, chunks, captured_at}`.

    Keyed by the locator VALUE rather than by parsing Cypher: the test is about
    the reconciliation logic, and pinning the exact query text here would make
    every future query tweak look like a behaviour change.
    """

    def run(database: str, cypher: str, params: dict) -> list[dict]:
        hit = graph.get(database, {}).get(params["value"])
        if hit is None:
            return [{"documents": 0, "chunks": 0, "captured_at": []}]
        return [
            {
                "documents": hit.get("documents", 0),
                "chunks": hit.get("chunks", 0),
                "captured_at": hit.get("captured_at", []),
            }
        ]

    return run


def _src(cid: str, db: str, match: str = "corpus_id", value: str | None = None, **extra) -> dict:
    out = {
        "id": cid,
        "target_db": db,
        "graph_locator": {"match": match, "value": value if value is not None else cid},
    }
    out.update(extra)
    return out


# --------------------------------------------------------------------------- #
# the four statuses the acceptance names
# --------------------------------------------------------------------------- #
def test_loaded_when_present_in_the_declared_database() -> None:
    rows = verify(
        [_src("bmc-utils", "ddcontext", captured_at="2026-07-31")],
        DATABASES,
        _fake(
            {
                "ddcontext": {
                    "bmc-utils": {
                        "documents": 1016,
                        "chunks": 4200,
                        "captured_at": ["2026-07-31T00:00:00Z"],
                    }
                }
            }
        ),
    )
    assert [(r.status, r.documents, r.chunks) for r in rows] == [(LOADED, 1016, 4200)]
    assert exit_code(rows) == 0


def test_missing_when_present_nowhere() -> None:
    rows = verify([_src("ghost", "ddcontext")], DATABASES, _fake({}))
    assert rows[0].status == MISSING
    assert rows[0].found_in == ()
    # missing is a real finding but NOT a failure — a queued corpus is allowed
    # to be unloaded; only a corpus in the wrong place breaks the topology.
    assert exit_code(rows) == 0


def test_wrong_db_when_the_corpus_landed_somewhere_else() -> None:
    rows = verify(
        [_src("strays", "ddcontext")],
        DATABASES,
        _fake({"drydocs": {"strays": {"documents": 26, "chunks": 300}}}),
    )
    assert rows[0].status == WRONG_DB
    assert rows[0].found_in == ("drydocs",)
    assert "declared ddcontext, found in ['drydocs']" in rows[0].detail
    assert exit_code(rows) == 1  # the acceptance's non-zero rule


def test_stale_when_the_graph_capture_does_not_match_the_registry() -> None:
    rows = verify(
        [_src("bmc-utils", "ddcontext", captured_at="2026-07-31")],
        DATABASES,
        _fake(
            {"ddcontext": {"bmc-utils": {"documents": 5, "captured_at": ["2026-06-01T00:00:00Z"]}}}
        ),
    )
    assert rows[0].status == STALE
    assert "2026-07-31" in rows[0].detail and "2026-06-01" in rows[0].detail


# --------------------------------------------------------------------------- #
# the two the item did not name, and why they are not `missing`
# --------------------------------------------------------------------------- #
def test_declared_but_unprovisioned_database_is_db_absent_not_missing() -> None:
    """Two live entries declare `dddocs`, which 01_databases.cypher never creates.

    Calling that `missing` would blame the load for an unmade decision — the
    topology is G32's open ruling. It reports, and does not fail.
    """
    rows = verify(
        [_src("bmc-docs", "dddocs", match="path_prefix", value="external/")], DATABASES, _fake({})
    )
    assert rows[0].status == DB_ABSENT
    assert "does not exist on this server" in rows[0].detail
    assert "not found in any existing database either" in rows[0].detail
    assert exit_code(rows) == 0


def test_db_absent_still_says_where_the_corpus_actually_is() -> None:
    """bmc-docs declares dddocs (unprovisioned) but its own registry note says it
    is in `drydocs` today. "Your target is missing" is a far weaker finding than
    "...and it is sitting over here meanwhile" — the second says what to do."""
    rows = verify(
        [_src("bmc-docs", "dddocs", match="path_prefix", value="external/")],
        DATABASES,
        _fake({"drydocs": {"external/": {"documents": 26, "chunks": 300}}}),
    )
    assert rows[0].status == DB_ABSENT
    assert rows[0].found_in == ("drydocs",)
    assert rows[0].documents == 26
    assert "meanwhile present in ['drydocs'] (26 docs)" in rows[0].detail


def test_corpus_off_the_lexical_backbone_is_unshaped_not_missing() -> None:
    """jpmc-reports loaded as :DataAsset slices — its documents are not missing,
    they were never documents."""
    rows = verify(
        [_src("jpmc-reports", "ddcontext", match="none", value=None)], DATABASES, _fake({})
    )
    assert rows[0].status == UNSHAPED
    assert "match: none" in rows[0].detail  # a ruling, not a silence
    assert exit_code(rows) == 0


def test_entry_with_no_locator_at_all_reads_differently_from_match_none() -> None:
    """Both are `unshaped`, but only one of them is an answer — the detail must
    not claim the entry said nothing when it said `none` deliberately."""
    rows = verify([{"id": "undeclared", "target_db": "ddcontext"}], DATABASES, _fake({}))
    assert rows[0].status == UNSHAPED
    assert "nobody has ruled" in rows[0].detail


# --------------------------------------------------------------------------- #
# the cases worth being precise about
# --------------------------------------------------------------------------- #
def test_right_database_plus_a_stray_copy_is_still_wrong_db() -> None:
    """Present where declared AND somewhere else. Reporting `loaded` would hide
    the stray copy, which is the actual defect."""
    rows = verify(
        [_src("dupe", "ddcontext")],
        DATABASES,
        _fake(
            {
                "ddcontext": {"dupe": {"documents": 10}},
                "drydocs": {"dupe": {"documents": 10}},
            }
        ),
    )
    assert rows[0].status == WRONG_DB
    assert "also present in ['drydocs']" in rows[0].detail
    assert exit_code(rows) == 1


def test_freshness_is_never_silently_reported_as_fresh() -> None:
    """The older loaders write no captured_at. That is 'cannot check', not 'fresh'."""
    rows = verify(
        [_src("old", "ddcontext", captured_at="2026-07-31")],
        DATABASES,
        _fake({"ddcontext": {"old": {"documents": 26, "captured_at": []}}}),
    )
    assert rows[0].status == LOADED
    assert "freshness uncheckable" in rows[0].detail


def test_captured_at_matches_on_date_prefix() -> None:
    """The registry records a date; the graph records a full timestamp."""
    rows = verify(
        [_src("c", "ddcontext", captured_at="2026-07-31")],
        DATABASES,
        _fake({"ddcontext": {"c": {"documents": 1, "captured_at": ["2026-07-31T14:43:32Z"]}}}),
    )
    assert rows[0].status == LOADED


def test_unavailable_databases_are_never_probed() -> None:
    """`available` narrows the sweep — probing a database that does not exist
    would raise from the driver, not return zero rows."""
    probed: list[str] = []

    def run(database: str, cypher: str, params: dict) -> list[dict]:
        probed.append(database)
        return [{"documents": 0, "chunks": 0, "captured_at": []}]

    verify([_src("x", "ddcontext")], DATABASES, run, available=["ddcontext"])
    assert probed == ["ddcontext"]


def test_locator_of_separates_declared_none_from_undeclared() -> None:
    assert locator_of({"id": "a", "graph_locator": {"match": "none"}}) == ("none", None, True)
    assert locator_of({"id": "b"}) == ("none", None, False)


def test_locator_of_rejects_an_unknown_match_kind() -> None:
    with pytest.raises(ValueError, match="not in"):
        locator_of({"id": "bad", "graph_locator": {"match": "regex", "value": "x"}})


def test_count_query_parameterises_the_value() -> None:
    """No interpolation: a corpus id is registry data, and the query must not
    become a place where registry data is executed."""
    for kind in ("corpus_id", "doc_id", "path_prefix"):
        assert "$value" in count_query(kind)


def test_summary_counts_by_status() -> None:
    rows = [
        CorpusRow("a", "ddcontext", LOADED),
        CorpusRow("b", "ddcontext", LOADED),
        CorpusRow("c", "ddcontext", MISSING),
    ]
    assert Summary.of(rows).line() == "2 loaded · 1 missing"  # sorted by status name
