"""Guards for the C17 PAT grain-keying rulings (gate `seal-app-ref-edge-reshape`
§G6-RIDER, 2026-08-01 — no Neo4j required) and the C22 catalog loader sweep
(2026-08-04: the orphan shape on all three hierarchy joins, coalesce on the
enrichment SETs, sparse-refresh-tolerant name fields).

Three rulings, three things a future edit must not undo:

  §a  every catalog grain is keyed on its NUMERIC source id, never on a name;
  §b  the team report's Supporting column feeds ``area_product_id`` and the
      Sponsoring one feeds ``sponsored_area_product_id`` — both load;
  §c  Sponsoring Product Line stays unmodelled while it is name-only.

The §a tests are the ones with teeth. The ids are numeric at source and our node
keys are strings, and pydantic v2 (unlike v1) does not coerce int -> str — so
before ``_catalog_id`` existed, a numerically-typed read of the real feed
rejected EVERY catalog row rather than some of them.
"""

from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from drydocs.loaders.catalog import (
    AreaProductRow,
    CatalogLOBRow,
    DevTeamRow,
    PatProductMappingRow,
    ProductLineRow,
    ProductRow,
)

_CYPHER = Path(__file__).resolve().parents[2] / "drydocs" / "loaders" / "cypher"


# --------------------------------------------------------------------------- #
# §a — numeric ids at source, string keys in the graph
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("numeric", [12345, Decimal("12345"), 12345.0])
def test_every_grain_accepts_the_numeric_id_the_source_actually_sends(numeric: object) -> None:
    """int / Decimal / float all normalize to the same string key.

    float is in this list deliberately: a nullable numeric column read through
    pandas arrives as float64, and a blind ``str()`` would key the node
    '12345.0' — no match against the real node, and a duplicate MERGEd beside
    it. Same input, same key, whichever numeric type the reader chose.
    """
    assert ProductLineRow(
        product_line_id=numeric, name="X", parent_lob_id=numeric
    ) == ProductLineRow(product_line_id="12345", name="X", parent_lob_id="12345")
    assert (
        ProductRow(product_id=numeric, name="X", parent_product_line_id=numeric).product_id
        == "12345"
    )
    assert (
        AreaProductRow(area_product_id=numeric, name="X", parent_product_id=numeric).area_product_id
        == "12345"
    )
    assert CatalogLOBRow(lob_id=numeric).lob_id == "12345"
    assert DevTeamRow(team_id=numeric, name="X", jira_board_id=numeric).jira_board_id == "12345"

    row = PatProductMappingRow(
        team_id=numeric,
        product_id=numeric,
        area_product_id=numeric,
        sponsored_area_product_id=numeric,
        team_type="aligned",
    )
    assert (row.team_id, row.product_id, row.area_product_id) == ("12345", "12345", "12345")


def test_a_fractional_id_is_refused_not_rounded() -> None:
    """An id with a fractional part is corruption. Rounding it would invent a
    key that resolves to the wrong node forever — refuse and let the row reject."""
    with pytest.raises(ValidationError):
        ProductRow(product_id=12345.5, name="X", parent_product_line_id="1")


def test_a_boolean_is_not_an_id() -> None:
    """bool subclasses int, so an unguarded coercion keys a node as '1'."""
    with pytest.raises(ValidationError):
        ProductRow(product_id=True, name="X", parent_product_line_id="1")


def test_product_line_id_stays_required_so_a_name_can_never_become_the_key() -> None:
    """The executable half of §a.

    The PAT team report projects the product line as a NAME with no id column.
    If this field ever goes optional, that report becomes loadable and the name
    becomes the de-facto key — after which a rename silently re-points every
    confirmed mapping hanging off it. That is the one failure the gate exists to
    prevent, so it is pinned here rather than left to review.
    """
    with pytest.raises(ValidationError):
        ProductLineRow(name="Payments Product Line", parent_lob_id="LOB1")  # type: ignore[call-arg]

    assert ProductLineRow.model_fields["product_line_id"].is_required()
    # ...and the name is NOT a key: it is an ordinary attribute the cypher SETs.
    assert "MERGE (pl:ProductLine {product_line_id:" in (
        _CYPHER / "product_lines.cypher"
    ).read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# §b — Supporting vs Sponsoring, and both load
# --------------------------------------------------------------------------- #
def test_supporting_and_sponsoring_area_products_are_separate_fields() -> None:
    """The team report splits them; the row model keeps them split. A row can
    carry BOTH (they are co-populated, not exclusive) — cypher §2 and §3b fire
    independently, which C17 confirmed is intended rather than a latent bug."""
    row = PatProductMappingRow(
        team_id="T1",
        product_id="P1",
        area_product_id="AP-SUPPORTING",
        sponsored_area_product_id="AP-SPONSORING",
        team_type="aligned",
    )
    assert row.area_product_id == "AP-SUPPORTING"
    assert row.sponsored_area_product_id == "AP-SPONSORING"


def test_the_supporting_qualification_is_recorded_on_the_field() -> None:
    """Which source column feeds the unqualified field name is the §b answer —
    and it is only an answer if it is attached to the field, not to a commit."""
    description = PatProductMappingRow.model_fields["area_product_id"].description or ""
    assert "Supporting" in description


def test_cypher_records_which_column_is_which() -> None:
    text = (_CYPHER / "pat_product_mapping.cypher").read_text(encoding="utf-8")
    assert "SUPPORTING area" in text
    assert "SPONSORING one" in text


# --------------------------------------------------------------------------- #
# §c — the third sponsoring form stays out until it has an id
# --------------------------------------------------------------------------- #
def test_sponsoring_product_line_is_deliberately_unmodelled() -> None:
    """Name-only, so modelling it would mean keying a :ProductLine on a name.

    ``extra='ignore'`` means the column is dropped silently when it appears —
    intended, but invisible. This pins the intent so nobody 'fixes' the omission
    by adding a name-keyed field, and it starts failing the day someone adds the
    field for real (which should only happen alongside an ID column).
    """
    assert "sponsoring_product_line" not in PatProductMappingRow.model_fields
    assert "sponsored_product_line_id" not in PatProductMappingRow.model_fields

    row = PatProductMappingRow(
        team_id="T1",
        product_id="P1",
        team_type="aligned",
        sponsoring_product_line="Payments",  # type: ignore[call-arg]
    )
    assert not hasattr(row, "sponsoring_product_line")


# --------------------------------------------------------------------------- #
# the join, having been ruled by-id, must not fail silently (C17 -> C22 sweep)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("cypher_file", "var", "parent_match", "orphan_id_set"),
    [
        (
            "products.cypher",
            "p",
            "OPTIONAL MATCH (pl:ProductLine",
            "p.orphan_parent_product_line_id = row.parent_product_line_id",
        ),
        (
            "product_lines.cypher",
            "pl",
            "OPTIONAL MATCH (l:CatalogLOB",
            "pl.orphan_parent_lob_id = row.parent_lob_id",
        ),
        (
            "area_products.cypher",
            "ap",
            "OPTIONAL MATCH (p:Product",
            "ap.orphan_parent_product_id = row.parent_product_id",
        ),
    ],
)
def test_an_unresolved_parent_is_recorded_on_the_node(
    cypher_file: str, var: str, parent_match: str, orphan_id_set: str
) -> None:
    """A parent id with no loaded parent node used to leave a real node with no
    parent edge and `orphan: false` still set from ON CREATE — unparented and
    reporting itself as fine, with a flag no code path could ever set true. C17
    fixed products.cypher; C22 swept the shape into the other two hierarchy
    loaders. The miss is now a queryable property on every grain."""
    raw = (_CYPHER / cypher_file).read_text(encoding="utf-8")
    # column-aligned SETs, so compare on collapsed whitespace rather than
    # pinning the alignment (a reformat is not a regression)
    text = re.sub(r"[ \t]+", " ", raw)
    assert parent_match in text
    assert f"{var}.orphan = true" in text
    assert orphan_id_set in text
    # written on every run, not just ON CREATE, so a parent that DISAPPEARS is
    # caught on the next load rather than staying false forever
    assert f"ON CREATE SET {var}.orphan" not in text
    # ...and no hard parent MATCH remains anywhere in the file — that is the
    # defect shape itself (a MATCH after the MERGE silently drops the row)
    assert not re.search(r"(?m)^\s*MATCH\b", raw)


# --------------------------------------------------------------------------- #
# C22 §b — a sparse refresh must not blank what a full extract loaded
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("cypher_file", "var"),
    [("products.cypher", "p"), ("product_lines.cypher", "pl"), ("area_products.cypher", "ap")],
)
def test_a_sparse_refresh_does_not_blank_the_name(cypher_file: str, var: str) -> None:
    """`SET x.name = row.name` blanks the stored name the first time a partial
    extract omits the column. coalesce keeps the existing value when the row
    carries none — the same-shape fix in all three hierarchy loaders."""
    text = re.sub(r"[ \t]+", " ", (_CYPHER / cypher_file).read_text(encoding="utf-8"))
    assert f"{var}.name = coalesce(row.name, {var}.name)" in text
    assert f"{var}.name = row.name" not in text


def test_a_row_with_no_name_still_loads_and_carries_none() -> None:
    """The model half of §b. A required name would make a sparse refresh WORSE
    than the blanking it replaces: the row would reject wholesale, so the node's
    last-seen bookkeeping never advances. Absent and empty both normalize to
    None, which is what lets the cypher's coalesce keep the stored value —
    and the id fields stay required, so optionality cannot leak into keying."""
    assert ProductRow(product_id=1, parent_product_line_id=2).name is None
    assert ProductLineRow(product_line_id=1, parent_lob_id=2, name="   ").name is None
    assert AreaProductRow(area_product_id=1, parent_product_id=2, name="").name is None
    # a row that DOES carry the name still loads it, stripped
    assert ProductRow(product_id=1, parent_product_line_id=2, name=" X ").name == "X"
