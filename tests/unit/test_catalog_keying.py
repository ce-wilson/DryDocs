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
from drydocs_core.cypher_split import strip_comments

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
def _assert_orphan_shape(raw: str, var: str, parent_match: str, orphan_id_set: str) -> None:
    """The C22 orphan-shape guard, over the template's CODE only (J26): the
    negative assertions read comment-stripped text so the file can quote the
    old defect shape in a `//` comment without tripping its own guard."""
    # column-aligned SETs, so compare on collapsed whitespace rather than
    # pinning the alignment (a reformat is not a regression)
    code = re.sub(r"[ \t]+", " ", strip_comments(raw))
    assert parent_match in code
    assert f"{var}.orphan = true" in code
    assert orphan_id_set in code
    # written on every run, not just ON CREATE, so a parent that DISAPPEARS is
    # caught on the next load rather than staying false forever
    assert f"ON CREATE SET {var}.orphan" not in code
    # ...and no hard parent MATCH remains anywhere in the file — that is the
    # defect shape itself (a MATCH after the MERGE silently drops the row)
    assert not re.search(r"(?m)^\s*MATCH\b", code)


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
    _assert_orphan_shape(raw, var, parent_match, orphan_id_set)


# --------------------------------------------------------------------------- #
# C22 §b — a sparse refresh must not blank what a full extract loaded
# --------------------------------------------------------------------------- #
def _assert_sparse_name_coalesce(raw: str, var: str) -> None:
    code = re.sub(r"[ \t]+", " ", strip_comments(raw))
    assert f"{var}.name = coalesce(row.name, {var}.name)" in code
    assert f"{var}.name = row.name" not in code


@pytest.mark.parametrize(
    ("cypher_file", "var"),
    [
        ("products.cypher", "p"),
        ("product_lines.cypher", "pl"),
        ("area_products.cypher", "ap"),
        # C24 — the two files the C22 sweep stopped short of. EXTENDED here rather
        # than pinned in a second test, so the next loader added to this family is
        # caught by the same parametrization instead of by whoever remembers.
        ("catalog_lobs.cypher", "l"),
        ("dev_teams.cypher", "dt"),
    ],
)
def test_a_sparse_refresh_does_not_blank_the_name(cypher_file: str, var: str) -> None:
    """`SET x.name = row.name` blanks the stored name the first time a partial
    extract omits the column. coalesce keeps the existing value when the row
    carries none — the same-shape fix in all five catalog loaders."""
    _assert_sparse_name_coalesce((_CYPHER / cypher_file).read_text(encoding="utf-8"), var)


def test_the_catalog_lob_code_is_coalesced_too() -> None:
    """C24 §a, and the reason this file was the urgent half: `code` is a SECOND
    enrichment field on the same node, already declared `str | None` in the row
    model. Coalescing only `name` would leave the identical defect live one
    property over — and `code` is the human-readable LOB handle (AWMCIB, CCB),
    so blanking it is more visible than blanking the name, not less."""
    code = re.sub(r"[ \t]+", " ", strip_comments((_CYPHER / "catalog_lobs.cypher").read_text()))
    assert "l.code = coalesce(row.code, l.code)" in code
    assert "l.code = row.code" not in code


def test_a_dev_team_row_with_no_name_still_loads() -> None:
    """The model half of C24. DevTeamRow.name was REQUIRED (min_length=1), which
    C22 ruled the worse failure mode: a sparse refresh rejects the whole row, so
    `last_seen_at` never advances and an unrefreshed team is indistinguishable
    from a retired one. team_id stays required — optionality must not leak into
    keying (C17 §a)."""
    assert DevTeamRow(team_id=7).name is None
    assert DevTeamRow(team_id=7, name="   ").name is None
    assert DevTeamRow(team_id=7, name=" Payments ").name == "Payments"
    with pytest.raises(ValidationError):
        DevTeamRow(name="Payments")  # type: ignore[call-arg]


def test_the_guards_survive_the_file_describing_its_own_mechanism() -> None:
    """J26 regression pin. A guard that reads prose makes the file unable to
    explain itself — the repo's doctrine is that the reasoning IS the audit
    trail. Quote the ENTIRE pre-C17 defect verbatim in comments (the ON CREATE
    orphan flag, the unconditional name SET, the hard parent MATCH) and every
    negative assertion above must still hold, because comments are not code."""
    raw = (_CYPHER / "products.cypher").read_text(encoding="utf-8")
    described = raw + (
        "\n// the pre-C17 defect, quoted verbatim so the next reader sees the shape:\n"
        "//   ON CREATE SET p.orphan = false\n"
        "//   SET p.name = row.name\n"
        "// MATCH (pl:ProductLine {product_line_id: row.parent_product_line_id})\n"
    )
    _assert_orphan_shape(
        described,
        "p",
        "OPTIONAL MATCH (pl:ProductLine",
        "p.orphan_parent_product_line_id = row.parent_product_line_id",
    )
    _assert_sparse_name_coalesce(described, "p")


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
