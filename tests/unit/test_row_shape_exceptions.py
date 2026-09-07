"""WEB6: the console's row-shape exemptions must still name a real server defect.

`web/src/data/rowShape.ts` checks a spec result's rows against the column TYPES
drydocs_api declares. Two declarations are wrong today — a collected list under
``type: "string"`` — so the validator exempts those two columns from the type
check, and the console renders them instead of refusing every row.

An exemption nobody re-checks is how a workaround outlives its cause. This guard
is bidirectional, and both directions matter:

* an exemption that no longer describes a defect FAILS, so fixing the server
  declaration forces the console's exemption out in the same change;
* a NEW list-under-a-scalar-declaration that nobody exempted also FAILS, so the
  next one is found here rather than by a blank panel.

It lives on the python side because only python can import the registry — J37's
rule, not a convenience: parsing the rendered OpenAPI or the TypeScript would be
reading a render of the thing whose declaration is the subject.
"""

from __future__ import annotations

import re
from pathlib import Path

from drydocs_api.query_specs import QUERY_SPECS

REPO = Path(__file__).resolve().parents[2]
ROW_SHAPE = REPO / "web" / "src" / "data" / "rowShape.ts"

#: The scalar vocabulary ColumnDef declares. A list value under any of these is
#: the defect this guard is about.
SCALAR_TYPES = frozenset({"string", "int"})

#: `collect(...) AS name` or `[x IN ... ] AS name` — the two ways a spec in this
#: registry produces a list. Matched against the cypher, which is the code.
_LIST_ALIAS = re.compile(
    r"(?:collect\s*\(|\[\s*[A-Za-z_]\w*\s+IN\b)[^\n]*?\bAS\s+([A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)

_TS_COMMENTS = re.compile(r"/\*[\s\S]*?\*/|//[^\n]*")
_EXCEPTION_BLOCK = re.compile(r"DECLARED_TYPE_EXCEPTIONS[^=]*=\s*\{(.*?)\n\}", re.DOTALL)
_ENTRY = re.compile(r"'([^']+)'\s*:\s*\[([^\]]*)\]")


def _declared_exceptions() -> dict[str, set[str]]:
    """The console's exemption map, read from its CODE (comments stripped).

    J66: the module's own header quotes the two spec ids while explaining them,
    so a scan over raw source would read the explanation as a second entry.
    """
    code = _TS_COMMENTS.sub(" ", ROW_SHAPE.read_text(encoding="utf-8"))
    block = _EXCEPTION_BLOCK.search(code)
    assert block, "DECLARED_TYPE_EXCEPTIONS not found in rowShape.ts"
    out: dict[str, set[str]] = {}
    for spec_id, columns in _ENTRY.findall(block.group(1)):
        out[spec_id] = set(re.findall(r"'([^']+)'", columns))
    return out


def _list_columns_declared_scalar() -> dict[str, set[str]]:
    """Every column the registry returns as a LIST while declaring it scalar."""
    out: dict[str, set[str]] = {}
    for spec in QUERY_SPECS.values():
        declared = {c.name: c.type for c in spec.columns}
        listed = {
            name for name in _LIST_ALIAS.findall(spec.cypher) if declared.get(name) in SCALAR_TYPES
        }
        if listed:
            out[spec.id] = listed
    return out


def test_the_scan_finds_the_defect_it_was_written_for() -> None:
    """Instrument check (J76) before either assertion below is believed.

    Both halves of this guard are set comparisons, and a regex that matched
    nothing would make them agree on two empty sets and pass. So: the registry
    really does contain the case, and the exemption map really does parse.
    """
    found = _list_columns_declared_scalar()
    assert found, "the list-under-scalar scan matched nothing — check the regex, not the registry"
    assert _declared_exceptions(), "the exemption map parsed empty — check the block regex"


def test_every_console_exemption_still_describes_a_real_server_defect() -> None:
    """Fixing the declaration must retire the exemption in the same change."""
    real = _list_columns_declared_scalar()
    for spec_id, columns in _declared_exceptions().items():
        assert (
            spec_id in QUERY_SPECS
        ), f"rowShape.ts exempts columns on '{spec_id}', which is not a registered spec"
        stale = columns - real.get(spec_id, set())
        assert not stale, (
            f"rowShape.ts still exempts {sorted(stale)} on '{spec_id}', but the server no "
            "longer declares a list column there as a scalar. Remove the exemption."
        )


def test_no_unexempted_list_column_is_declared_a_scalar() -> None:
    """A NEW one is found here, not by a panel that refuses to render."""
    exempt = _declared_exceptions()
    for spec_id, columns in _list_columns_declared_scalar().items():
        missing = columns - exempt.get(spec_id, set())
        assert not missing, (
            f"'{spec_id}' returns {sorted(missing)} as a list while declaring it a scalar "
            "type, and web/src/data/rowShape.ts does not exempt it — so the console's row "
            "check will refuse every row of that spec. Fix the ColumnDef, or exempt it."
        )
