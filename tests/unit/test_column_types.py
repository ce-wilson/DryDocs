"""API2 — the column type vocabulary, and the guard that keeps a list declared as one.

WHAT THIS REPLACES. WEB6 found two specs returning a collected LIST under
``type: "string"`` — ``runbooks.series.v1.lands`` and
``lineage.schema-definition.v1.properties`` — because ``ColumnDef`` had no list
type to declare. The console could not refuse those rows without blanking two
panels, so it carried a two-spec exemption in ``web/src/data/rowShape.ts`` and a
bidirectional guard lived here to keep the exemption honest. API2 gave the server
the type; the exemption is deleted, and with it the half of this file that read
the console's TypeScript.

WHAT REPLACES IT is the clause the item asks for: a column whose Cypher COLLECTS
or COMPREHENDS must not be declared a scalar. There is no exemption to reach for
any more, which is what makes the check worth having — and also why the scan
underneath it has to be accurate rather than merely present.

IT READS THE SPEC OBJECT (J37). ``QUERY_SPECS`` is imported and each spec's own
``cypher`` and ``columns`` attributes are read. The OpenAPI document and the
generated TypeScript are RENDERS of this declaration; reading either to check the
declaration would be reading the render of the thing under test.
"""

from __future__ import annotations

import re
from typing import get_args

from drydocs_api.query_specs import COLUMN_TYPES, QUERY_SPECS
from drydocs_api.schemas import ColumnOut

#: Clause boundaries. A projection list runs from RETURN/WITH to the next one of
#: these, which is what lets an alias be matched to ITS OWN expression rather
#: than to whatever text precedes it.
_CLAUSE = re.compile(
    r"\b(RETURN|WITH|MATCH|WHERE|UNWIND|ORDER\s+BY|SKIP|LIMIT|CALL|MERGE|CREATE|SET|DELETE|"
    r"DETACH|FOREACH|UNION(?:\s+ALL)?|OPTIONAL\s+MATCH)\b",
    re.IGNORECASE,
)
_AS_TAIL = re.compile(r"\bAS\s+([A-Za-z_][A-Za-z0-9_]*)\s*$", re.IGNORECASE)
_COLLECT = re.compile(r"collect\s*\(", re.IGNORECASE)
_OPEN, _CLOSE = "([{", ")]}"


def _depths(text: str) -> list[int]:
    depth, out = 0, []
    for ch in text:
        if ch in _OPEN:
            depth += 1
        elif ch in _CLOSE:
            depth -= 1
        out.append(depth)
    return out


def _split_top_level(text: str) -> list[str]:
    items, item, depth = [], "", 0
    for ch in text:
        if ch in _OPEN:
            depth += 1
        elif ch in _CLOSE:
            depth -= 1
        if ch == "," and depth == 0:
            items.append(item)
            item = ""
        else:
            item += ch
    items.append(item)
    return items


def projections(cypher: str) -> dict[str, str]:
    """Every ``<expression> AS <name>`` in a RETURN or WITH, as name -> expression.

    A FORWARD PARSE, not a regular expression over the whole query, and the
    difference is not stylistic. The scan this replaces matched ``collect(``
    followed by ``AS name`` on the SAME LINE; it happened to find exactly the two
    real cases because this registry writes its aliases on one line, and it would
    have started reporting a neighbouring column the first time a spec's Cypher
    was reflowed. Splitting clauses and then top-level commas ties each alias to
    its own expression whatever the whitespace does.
    """
    marks = [(m.start(), m.end(), m.group(1).upper()) for m in _CLAUSE.finditer(cypher)]
    depth_at = _depths(cypher)
    marks = [mark for mark in marks if depth_at[mark[0]] == 0]
    found: dict[str, str] = {}
    for index, (_, body_start, keyword) in enumerate(marks):
        if not keyword.startswith(("RETURN", "WITH")):
            continue
        body_end = marks[index + 1][0] if index + 1 < len(marks) else len(cypher)
        for item in _split_top_level(cypher[body_start:body_end]):
            tail = _AS_TAIL.search(item.strip())
            if tail:
                found[tail.group(1)] = item.strip()[: tail.start()].strip()
    return found


def produces_list(expression: str) -> bool:
    """Does this projection return a LIST?

    Only when the collect or the comprehension is the OUTERMOST thing. That
    qualifier is the whole accuracy of the guard: ``size(collect(x)) AS n``
    returns an integer, is correctly declared ``int``, and a scan that matched
    ``collect(`` anywhere in the expression would fail the registry for a correct
    declaration — with no exemption left to absorb it.
    """
    text = expression.strip()
    return text.startswith("[") or bool(_COLLECT.match(text))


def _list_columns() -> dict[str, set[str]]:
    """Declared columns whose projection returns a list, by spec id."""
    found: dict[str, set[str]] = {}
    for spec in QUERY_SPECS.values():
        declared = {column.name for column in spec.columns}
        listed = {
            name
            for name, expression in projections(spec.cypher).items()
            if name in declared and produces_list(expression)
        }
        if listed:
            found[spec.id] = listed
    return found


def test_the_scan_finds_the_columns_it_was_written_for() -> None:
    """Instrument check (J76) before either assertion below is believed.

    The guard is "every list column is declared list", and a scan that matched
    NOTHING would satisfy it vacuously — the exact defect class CORE2 closed one
    item earlier in this lane. So the two known cases are named here: if a spec
    is retired the names change and this test says so, rather than the guard
    quietly going green over an empty set.
    """
    found = _list_columns()
    assert found, "the list-projection scan matched nothing -- check the parser, not the registry"
    assert found.get("runbooks.series.v1") == {"lands"}
    assert found.get("lineage.schema-definition.v1") == {"properties"}


def test_the_scan_reads_the_outermost_call_and_not_any_collect() -> None:
    """The positive-and-negative control for `produces_list`, pinned as a test
    because there is no exemption left to absorb a false positive."""
    assert produces_list("collect(DISTINCT d.assetId)")
    assert produces_list("[k IN keys(d) WHERE NOT k IN ['assetId']]")
    assert not produces_list("size(collect(DISTINCT x))")
    assert not produces_list("count(j)")

    # and the parser ties each alias to its own expression across clauses
    parsed = projections("MATCH (a) WITH collect(a) AS xs RETURN a.name AS name, xs AS lands")
    assert parsed == {"xs": "collect(a)", "name": "a.name", "lands": "xs"}


def test_no_list_column_is_declared_a_scalar() -> None:
    """The clause. A console that has to render a list under a `string`
    declaration either refuses every row of that spec or stops checking the
    column -- WEB6 chose the second and paid for it with a two-spec exemption."""
    offenders: dict[str, dict[str, str]] = {}
    for spec_id, columns in _list_columns().items():
        declared = {column.name: column.type for column in QUERY_SPECS[spec_id].columns}
        wrong = {name: declared[name] for name in sorted(columns) if declared[name] != "list"}
        if wrong:
            offenders[spec_id] = wrong
    assert not offenders, (
        f"these columns return a list and declare a scalar: {offenders}. Declare them "
        "'list'. There is no console-side exemption to add: API2 deleted it along with "
        "the server defect it described."
    )


def test_the_vocabulary_and_its_openapi_twin_agree() -> None:
    """`ColumnOut.type` is a Literal, because pydantic needs static values to put
    an enum in the OpenAPI document — so the vocabulary exists twice.

    The same arrangement `CLASSIFICATIONS` has with config/classification.yaml,
    and the same reason it is guarded: two copies with nothing comparing them is
    how J23's collapse to three classification levels went unnoticed here for a
    day. A drift here is quieter still, because the generated client would simply
    stop offering a type the server sends.
    """
    literal = set(get_args(ColumnOut.model_fields["type"].annotation))
    assert literal == set(COLUMN_TYPES), (
        f"drydocs_api.query_specs.COLUMN_TYPES is {sorted(COLUMN_TYPES)} and "
        f"schemas.ColumnOut.type is {sorted(literal)}. Both, in the same commit, "
        "and regenerate web/src/generated/openapi.json + api.d.ts."
    )


def test_every_declared_column_type_is_in_the_vocabulary() -> None:
    """`_validate_registry` asserts this at IMPORT, so this test can only fail if
    that assertion is removed -- which is exactly what it is here to catch."""
    for spec in QUERY_SPECS.values():
        for column in spec.columns:
            assert column.type in COLUMN_TYPES, (spec.id, column.name, column.type)
