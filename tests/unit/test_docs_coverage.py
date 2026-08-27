"""Q16 (a) — the software→documentation coverage report. Pure; no Neo4j, no files.

Fixtures are synthetic. The one test that reads the real config files is the
census pin at the bottom, which asserts the KNOWN state rather than failing on
it — drift in the coverage picture must be LOUD without being red, the same
discipline `test_software_registry.py` uses for the version drift itself.
"""

from __future__ import annotations

import yaml

from drydocs.docs_coverage import (
    CROSS_DB_BLOCKED,
    CURRENT,
    DIVERGENCE_EDGE_CORPUS_UNKNOWN,
    DIVERGENCE_EDGES_UNDECLARED,
    DRIFTED,
    EDGE_CORPUS_UNKNOWN,
    FAILING,
    LADDER,
    NO_CORPUS,
    NO_DOCS,
    NOT_LOADED,
    NOT_PROBED,
    REGISTRY_DB,
    TRAVERSABLE,
    UNGATED,
    UNREGISTERED_CORPUS,
    UNVERIFIED,
    coverage,
)

ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
SOFTWARE_REGISTRY = ROOT / "config" / "taxonomy" / "software-registry.yaml"
DOC_REGISTRY = ROOT / "config" / "doc-source-registry.yaml"


def _product(pid: str, **kw) -> dict:
    return {"id": pid, "vendor": "acme", "role": "orchestrator", "versions": ["1.0"], **kw}


def _corpus(cid: str, **kw) -> dict:
    base = {
        "id": cid,
        "classification": "External",
        "tier": "T1",
        "target_db": "dddocs",
        "confirmed": True,
        "graph_locator": {"match": "corpus_id", "value": cid},
    }
    base.update(kw)
    return base


def _fake_run(products_in_graph=(), edges=()):
    """edges: iterable of (product_id, corpus_id, count)."""

    def run(_db, cypher, _params):
        if "RETURN sp.product_id AS product_id" in cypher and "DESCRIBES" not in cypher:
            return [{"product_id": p} for p in products_in_graph]
        return [{"product_id": p, "corpus_id": c, "edges": n} for p, c, n in edges]

    return run


# --- 1. the row this report exists to print ------------------------------------


def test_a_product_with_no_documentation_block_is_a_row_not_an_absence() -> None:
    """The original Q16 scope printed only products CARRYING a documentation
    block — one of thirteen. This is the widening, asserted structurally."""
    report = coverage([_product("airflow")], [])
    assert [r.product_id for r in report.products] == ["airflow"]
    row = report.products[0]
    assert row.coverage == NO_CORPUS
    assert row.currency == NO_DOCS
    assert row.blockers == (NO_CORPUS,)


def test_every_product_appears_exactly_once() -> None:
    report = coverage([_product("a"), _product("b"), _product("c")], [])
    assert [r.product_id for r in report.products] == ["a", "b", "c"]
    assert report.reconciles()


def test_an_unregistered_doc_locator_is_surfaced_on_the_product() -> None:
    """The Airflow answer: 'no corpus' must not read as 'no docs'. The locator
    lives on the source-registry SYSTEM row and joins via the C12-confirmed
    platforms crosswalk."""
    report = coverage(
        [_product("airflow")],
        [],
        systems=[{"id": "airflow", "locator": {"internal_docs": "internal/x/mwaa.md"}}],
        platforms=[{"id": "airflow", "software_registry_ref": "airflow"}],
    )
    row = report.products[0]
    assert row.coverage == NO_CORPUS
    assert row.unregistered_doc_locators == ("internal/x/mwaa.md",)
    assert "locator(s) exist" in row.detail


# --- 2. the five distinctions the acceptance names -----------------------------


def test_unregistered_corpus_is_a_broken_pointer_and_fails() -> None:
    report = coverage([_product("p", documentation={"corpus": "ghost"})], [])
    assert report.products[0].coverage == UNREGISTERED_CORPUS
    assert report.exit_code() == 1


def test_ungated_corpus() -> None:
    report = coverage(
        [_product("p", documentation={"corpus": "c"})],
        [_corpus("c", confirmed=False)],
    )
    assert report.products[0].coverage == UNGATED


def test_cross_db_blocked() -> None:
    report = coverage(
        [_product("p", documentation={"corpus": "c"})],
        [_corpus("c", target_db="dddocs")],
    )
    assert report.products[0].coverage == CROSS_DB_BLOCKED


def test_loaded_and_traversable_when_everything_lines_up() -> None:
    report = coverage(
        [_product("p", documentation={"corpus": "c"})],
        [_corpus("c", target_db=REGISTRY_DB)],
        run=_fake_run(products_in_graph=["p"], edges=[("p", "c", 5)]),
    )
    row = report.products[0]
    assert row.coverage == TRAVERSABLE
    assert row.describes_edges == 5


def test_traversable_until_move_when_resident_off_declaration() -> None:
    """Edges exist, but the corpus declares a different database than the one it
    is loaded in. The traversal works and is NOT durable — the bmc-docs shape."""
    report = coverage(
        [_product("p", documentation={"corpus": "c"})],
        [_corpus("c", target_db="ddcontext")],
        run=_fake_run(products_in_graph=["p"], edges=[("p", "c", 3)]),
    )
    # cross-db-declared governs, so the row reports the blocker rather than the
    # accident — the ladder position is the point.
    assert report.products[0].coverage == CROSS_DB_BLOCKED
    assert "cross-db-declared" in report.products[0].blockers


# --- 3. the honesty properties -------------------------------------------------


def test_cross_db_is_decided_without_touching_the_graph() -> None:
    """THE load-bearing test. The cross-DB determination is arithmetic on two
    YAML fields, so it must hold with the database off — and the row must NOT
    degrade into `not-loaded`, which would read as a data gap rather than a
    ruled topology."""
    report = coverage(
        [_product("p", documentation={"corpus": "c"})],
        [_corpus("c", target_db="dddocs")],
        run=None,
    )
    row = report.products[0]
    assert row.coverage == CROSS_DB_BLOCKED
    assert row.coverage != NOT_LOADED
    assert row.documents is None and row.describes_edges is None
    assert "G32" in row.detail


def test_unprobed_is_none_never_zero() -> None:
    report = coverage(
        [_product("p", documentation={"corpus": "c"})],
        [_corpus("c", target_db=REGISTRY_DB)],
        run=None,
    )
    row = report.products[0]
    assert row.coverage == NOT_PROBED
    assert row.describes_edges is None
    assert row.describes_edges != 0, "0 would be a false claim of absence"


def test_blockers_lists_every_wall_not_just_the_first() -> None:
    report = coverage(
        [_product("p", documentation={"corpus": "c"})],
        [_corpus("c", confirmed=False, target_db="dddocs", graph_locator={"match": "none"})],
    )
    row = report.products[0]
    assert row.coverage == UNGATED, "one governing state"
    assert {"ungated", "cross-db-declared", "no-locator"} <= set(row.blockers)


def test_a_corpus_no_product_names_is_reported_not_dropped() -> None:
    report = coverage([_product("p")], [_corpus("orphan")])
    assert [c.corpus_id for c in report.corpora] == ["orphan"]
    assert report.reconciles()


def test_edges_from_an_undeclared_corpus_are_named() -> None:
    """The live bmc-docs finding: edges arrive from a corpus the product does not
    declare, attributed by a loader constant rather than the registry."""
    report = coverage(
        [_product("p", documentation={"corpus": "declared"})],
        [_corpus("declared", target_db=REGISTRY_DB), _corpus("other", target_db=REGISTRY_DB)],
        run=_fake_run(products_in_graph=["p"], edges=[("p", "other", 27)]),
    )
    row = report.products[0]
    assert DIVERGENCE_EDGES_UNDECLARED in row.divergence
    assert "other" in row.edge_corpora
    orphan = next(c for c in report.corpora if c.corpus_id == "other")
    assert orphan.attribution == "edge-without-declaration"


def test_edge_corpus_unidentifiable_is_its_own_bucket() -> None:
    """`bmc_docs.cypher` writes no corpus_id, so the graph genuinely cannot say
    which corpus produced those documents. A named bucket, not a defect."""
    report = coverage(
        [_product("p", documentation={"corpus": "c"})],
        [_corpus("c", target_db=REGISTRY_DB)],
        run=_fake_run(products_in_graph=["p"], edges=[("p", EDGE_CORPUS_UNKNOWN, 27)]),
    )
    row = report.products[0]
    assert EDGE_CORPUS_UNKNOWN in row.edge_corpora
    assert DIVERGENCE_EDGE_CORPUS_UNKNOWN in row.divergence


def test_a_system_with_no_product_row_is_reported() -> None:
    """Where Snowflake appears — a registered system absent from the software
    registry entirely. A candidate list for a human, not a claim."""
    report = coverage(
        [_product("controlm")],
        [],
        systems=[{"id": "controlm"}, {"id": "snowflake", "layer": "technology"}],
        platforms=[{"id": "controlm", "software_registry_ref": "controlm"}],
    )
    assert [s.system_id for s in report.systems] == ["snowflake"]


# --- 4. classification (acceptance (e)) ----------------------------------------


def test_no_registry_free_text_reaches_the_output() -> None:
    """Structural, the fid_census pattern: three corpora are classification
    Internal and their prose describes internal systems."""
    sentinel = "SENTINEL-INTERNAL-PROSE"
    report = coverage(
        [_product("p", documentation={"corpus": "c"}, notes=sentinel)],
        [_corpus("c", source=sentinel, notes=sentinel, source_url=sentinel)],
        systems=[{"id": "p", "notes": sentinel}],
    )
    assert sentinel not in repr(report.as_dict())


def test_internal_entries_are_counted_and_named_never_dropped() -> None:
    report = coverage([_product("p")], [_corpus("secret", classification="Internal")])
    row = next(c for c in report.corpora if c.corpus_id == "secret")
    assert row.classification == "Internal", "labelled so a consumer can filter"
    assert report.summary()["corpora_total"] == 1, "counted, not dropped"


# --- 5. currency (the original Q16 (a) columns) --------------------------------


def test_currency_drifted_when_a_runtime_version_is_not_confirmed() -> None:
    report = coverage(
        [
            _product(
                "p",
                versions=["9.0.20", "9.0.21"],
                documentation={"corpus": "c", "docs_version": "9.0.20", "current_for": ["9.0.20"]},
            )
        ],
        [_corpus("c", target_db=REGISTRY_DB)],
    )
    row = report.products[0]
    assert row.currency == DRIFTED
    assert row.versions_not_current == ("9.0.21",)
    assert report.exit_code() == 1, "a version bump must not pass unnoticed"


def test_currency_unverified_when_current_for_is_empty() -> None:
    report = coverage(
        [_product("p", documentation={"corpus": "c", "docs_version": "1", "current_for": []})],
        [_corpus("c", target_db=REGISTRY_DB)],
    )
    assert report.products[0].currency == UNVERIFIED


def test_currency_is_never_derived_from_version_strings() -> None:
    """Acceptance (c): current_for is a human assertion. An exact runtime match
    that nobody confirmed is UNVERIFIED, never CURRENT."""
    report = coverage(
        [_product("p", versions=["1.0"], documentation={"corpus": "c", "docs_version": "1.0"})],
        [_corpus("c", target_db=REGISTRY_DB)],
    )
    assert report.products[0].currency == UNVERIFIED


def test_currency_current_when_every_runtime_version_is_confirmed() -> None:
    report = coverage(
        [
            _product(
                "p",
                versions=["1.0"],
                documentation={"corpus": "c", "docs_version": "1.0", "current_for": ["1.0"]},
            )
        ],
        [_corpus("c", target_db=REGISTRY_DB)],
    )
    assert report.products[0].currency == CURRENT
    assert report.exit_code() == 0


# --- 6. what fails, and what deliberately does not -----------------------------


def test_no_corpus_and_cross_db_do_not_fail_the_run() -> None:
    """They are true statements about the world that G32 owns. Failing CI on an
    open design ruling trains people to ignore the verb."""
    assert NO_CORPUS not in FAILING and CROSS_DB_BLOCKED not in FAILING
    report = coverage(
        [_product("a"), _product("b", documentation={"corpus": "c"})],
        [_corpus("c", target_db="dddocs")],
    )
    assert report.exit_code() == 0


def test_summary_counts_reconcile() -> None:
    report = coverage(
        [_product("a"), _product("b", documentation={"corpus": "c"})],
        [_corpus("c"), _corpus("orphan")],
    )
    assert report.reconciles()
    assert report.summary()["products"] == 2
    assert set(report.summary()) >= {f"products_{s}" for s in LADDER}


# --- 7. the G32 fact, pinned ---------------------------------------------------


def test_every_corpus_declares_the_one_database() -> None:
    """THE ALARM FIRED AND WAS ANSWERED. This test's previous form asserted the
    inverse (no corpus may declare the registry database) precisely so it would
    fail the day G32 ruled — it did, 2026-08-18, and the ruling was the FOLD.
    Now the pin is the ruled state: every corpus declares the ONE database, so
    `traversable` is reachable by declaration and the until-move rung is gone."""
    doc = yaml.safe_load(DOC_REGISTRY.read_text(encoding="utf-8"))
    declared = {s.get("target_db") for s in doc["sources"] if s.get("target_db")}
    assert declared == {REGISTRY_DB}, (
        f"corpora declare {declared} — post-G102 the content topology is ONE "
        "database and a second value means a row missed the fold (or a new realm "
        "arrived without a gate)."
    )


def test_the_live_coverage_census_is_pinned() -> None:
    """Known-state pin over the REAL config. Not a failure condition — a change
    to the coverage picture must be LOUD without being red."""
    software = yaml.safe_load(SOFTWARE_REGISTRY.read_text(encoding="utf-8"))
    doc = yaml.safe_load(DOC_REGISTRY.read_text(encoding="utf-8"))
    report = coverage(software["products"], doc["sources"])
    s = report.summary()
    assert (
        (
            s["products"],
            s["products_no-corpus"],
            s["corpora_total"],
            s["corpora_unclaimed"],
            # PIN MOVED 2026-08-09 (C25): 13 -> 15 products and 12 -> 14 without a
            # documentation pointer. Both deltas are the two prerequisite rows the
            # software-version-context gate needed — `snowflake` and `dpl` — neither of
            # which has a docs corpus. Corpora counts are unchanged.
            # WORTH KNOWING, because the number looks like it should have moved: the
            # same commit added an `evidence:` block to the `abinitio` row, and abinitio
            # still counts as having NO documentation pointer. That is correct rather
            # than a miss — `evidence:` points at hand-compiled rows that inform the
            # product, `documentation:` points at a docs corpus that describes it. The
            # gate's §C5 ruling turns on exactly that distinction.
        )
        == (
            15,
            14,
            9,  # 8->9 at chase-leadership-scrape (2026-08-27) — prior move: Q10 ops-email-extracts, 2026-08-19
            8,  # unclaimed 7->8 — org-structure gate evidence, not product documentation (same class as the email corpus before it)
        )
    ), (
        f"coverage census changed: {s['products']} products, "
        f"{s['products_no-corpus']} with no documentation pointer, "
        f"{s['corpora_total']} corpora of which {s['corpora_unclaimed']} are claimed by no "
        "product. Update this pin deliberately and say why in the commit."
    )
