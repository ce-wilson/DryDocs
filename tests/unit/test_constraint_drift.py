"""The INVERSE of the D8 bootstrap guard: live constraints nothing declares (G130).

WHY IT IS A DETECTOR AND NOT A FIX. Constraints outlive data wipes. A wipe is a
data delete, not a database drop, so a census taken at a TRUE-ZERO node baseline
still found 62 constraints. A clean graph is not a clean schema, and a retired
label's uniqueness key goes on enforcing an old identity rule against the next
load that reuses the label -- with nothing anywhere reporting it, because the
existing guard only ever asked "did every DECLARATION land".

THE PURE HALF IS UNIT-TESTED AND THE LIVE HALF SKIPS. Reading the schema tree is
pure and always testable; comparing it against a database is not, so that test
skips with a named message where no database is reachable (the U26 precedent) and
names its venue where one is (J18). A test that FAILED without a database would
be a test people learn to deselect.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from drydocs_core.schema.constraints import (
    declared_constraint_names,
    declared_constraint_names_in_tree,
    undeclared_constraints,
)
from tests.source_scan import ATTRIBUTE, called_names, code_only

REPO = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO / "drydocs_core" / "schema"
CONSTRAINTS_FILE = SCHEMA_DIR / "constraints.cypher"


# ---------------------------------------------------------------------------
# (a) The inverse, over the whole tree.
# ---------------------------------------------------------------------------
def test_the_tree_scan_is_a_superset_of_the_single_file() -> None:
    """The drift check must read the TREE, not constraints.cypher alone.

    schema_graph.cypher declares one of its own and a supplement may declare
    more; keying on one file would report those as undeclared and make the
    warning noise on its very first run -- which is how an operator learns to
    ignore it.
    """
    single = set(declared_constraint_names(CONSTRAINTS_FILE))
    tree = set(declared_constraint_names_in_tree(SCHEMA_DIR))
    assert single, "expected constraints.cypher to declare something"
    assert single < tree, (
        "the tree scan found nothing beyond constraints.cypher -- if that is now "
        "genuinely true the single-file scan would do, and this test should be "
        "re-derived rather than relaxed"
    )


def test_every_declaration_reports_the_file_it_came_from() -> None:
    """A drift warning is only actionable if the reader can find the declaration."""
    declared = declared_constraint_names_in_tree(SCHEMA_DIR)
    assert all(v.endswith(".cypher") for v in declared.values())
    assert declared.get("role_name") == "constraints.cypher"


def test_undeclared_is_the_live_set_minus_the_declared_set() -> None:
    live = [
        {"name": "role_name", "labelsOrTypes": ["Role"], "properties": ["name"]},
        {"name": "ghost_id", "labelsOrTypes": ["Ghost"], "properties": ["ghost_id"]},
    ]
    extra = undeclared_constraints(live, SCHEMA_DIR)
    assert [row["name"] for row in extra] == ["ghost_id"]


def test_undeclared_is_empty_when_everything_live_is_declared() -> None:
    declared = declared_constraint_names_in_tree(SCHEMA_DIR)
    live = [{"name": n} for n in sorted(declared)]
    assert undeclared_constraints(live, SCHEMA_DIR) == ()


def test_the_scan_opens_no_session_and_reads_only_files() -> None:
    """Pure by construction: it takes the live rows as an argument.

    That is what lets the whole rule be unit-tested, and it is why the database
    read lives on the client rather than inside the comparison.

    Checked over the AST rather than the source text. A text scan fails on this
    function's own DOCSTRING, which names the thing it forbids -- and a guard that
    fails on the explanation teaches people to stop writing explanations.
    """
    import inspect

    called = called_names(inspect.getsource(undeclared_constraints), kind=ATTRIBUTE)
    assert not (called & {"run", "session", "execute_query", "execute_file"}), (
        f"the comparison calls the database: {sorted(called)}. It must stay pure -- "
        "the live rows are an argument, which is what makes the rule unit-testable."
    )


# ---------------------------------------------------------------------------
# (d) The three cases the item names, RE-VERIFIED here rather than asserted.
# ---------------------------------------------------------------------------
def test_the_membership_key_is_declared_nowhere_in_the_tree() -> None:
    """Dropped at G99 (2026-08-18), WITH its last writer rather than ahead of it.

    So a live `membership_id` is residue, not a producer defect -- and on this
    desktop it IS live, which is the detector's first real finding rather than a
    hypothetical. The drop is recorded in constraints.cypher's own comment.
    """
    assert "membership_id" not in declared_constraint_names_in_tree(SCHEMA_DIR)
    text = CONSTRAINTS_FILE.read_text(encoding="utf-8")
    assert "membership_id DROPPED at G99" in text, (
        "the drop's rationale is what makes a live membership_id readable as residue; "
        "if that comment goes, the next reader has to re-derive it"
    )


@pytest.mark.parametrize("label", ["AisCapability", "AisTool"])
def test_the_typo_labels_appear_nowhere_in_the_schema_tree(label: str) -> None:
    """Confirmed typo leftovers, dropped company-side after a zero-node check.

    Verified here as ABSENT FROM THE DECLARATIONS, which is the only half producer
    can verify -- what any given database still enforces is a fact about that
    database, and the detector is what reports it.
    """
    hits = [
        p.name
        for p in sorted(SCHEMA_DIR.rglob("*.cypher"), key=lambda q: q.as_posix())
        if label in p.read_text(encoding="utf-8")
    ]
    assert not hits, f"{label} is declared in {hits} -- it was a typo leftover"


# ---------------------------------------------------------------------------
# (b) Never a drop. Asserted statically, because it is the safety property.
# ---------------------------------------------------------------------------
def test_nothing_in_the_drift_path_can_drop_a_constraint() -> None:
    """The company-side procedure was a zero-node count AND a human decision.

    Dropping a constraint that still guards live data is unrecoverable in a way
    that leaving one in place is not, so the asymmetry is deliberate: this whole
    path reports and never acts.
    """
    import inspect

    from drydocs.cli_schema import _report_undeclared_constraints

    source = inspect.getsource(_report_undeclared_constraints)
    # Two different questions, so two different reads (J66). "does it DROP" is
    # about behaviour and goes through the helper -- otherwise this very
    # function's explanation of why it never drops would fail it. "does the
    # OUTPUT say so" is about the prose, so it reads the raw source on purpose.
    assert "DROP CONSTRAINT" not in code_only(source).upper()
    assert "drops NOTHING" in source, "the output must say so, not just be so"


def test_the_warning_carries_the_mechanism_and_the_human_check() -> None:
    """(c): a warning that says what drifted and not why is not actionable."""
    import inspect

    from drydocs.cli_schema import _report_undeclared_constraints

    source = inspect.getsource(_report_undeclared_constraints)
    for phrase in ("outlive data wipes", "62 constraints", "a human checks"):
        assert phrase in source, f"the drift output no longer explains {phrase!r}"


def test_the_bootstrap_calls_the_inverse_after_the_presence_check() -> None:
    """Order matters: a failed apply exits before this, so drift is never reported
    against a database the apply did not reach."""
    import inspect

    from drydocs.cli_schema import bootstrap

    source = inspect.getsource(bootstrap)
    assert source.index("declared_constraint_names") < source.index(
        "_report_undeclared_constraints"
    )


# ---------------------------------------------------------------------------
# (e) The live half. Skips with a named message; names its venue.
# ---------------------------------------------------------------------------
def test_the_live_graph_agrees_with_the_declarations_or_says_what_drifted() -> None:
    import platform

    from drydocs_core.config import Neo4jSettings
    from drydocs_core.neo4j_client import Neo4jClient

    settings = Neo4jSettings()
    password = settings.password
    secret = password.get_secret_value() if hasattr(password, "get_secret_value") else password
    if not (settings.uri and settings.user and secret):
        pytest.skip("no Neo4j settings on this machine - live constraint check skipped")

    try:
        client = Neo4jClient(settings.uri, settings.user, secret, database=settings.database)
    except Exception as exc:  # pragma: no cover - depends on the machine
        pytest.skip(f"Neo4j not reachable here ({type(exc).__name__}) - live check skipped")

    try:
        with client as cli:
            live = cli.constraints_detail()
    except Exception as exc:  # pragma: no cover - depends on the machine
        pytest.skip(f"Neo4j not reachable here ({type(exc).__name__}) - live check skipped")

    venue = f"{platform.node()} / {settings.uri} / {settings.database}"
    extra = undeclared_constraints(live, SCHEMA_DIR)

    # NOT an assertion that the set is empty. Undeclared is a STATE -- provisioning
    # and older experiments legitimately leave constraints behind -- and failing on
    # one would make the operator's next move "skip the check". What is asserted is
    # that the detector RUNS and that every row it returns is reportable.
    assert isinstance(extra, tuple)
    for row in extra:
        assert row.get("name"), f"undeclared row with no name at {venue}"
        assert "labelsOrTypes" in row and "properties" in row, (
            f"a drift row at {venue} carries no label or property, so the warning "
            "could not tell a human what it enforces"
        )
