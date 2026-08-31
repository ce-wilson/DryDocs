"""The console's docs-verify surface cannot drift from the verb (O58).

THE DEFECT CLASS THIS GUARDS. ``drydocs docs-verify`` and the console page answer
the SAME question from the SAME reconciliation, but through two call sites with a
duplicated sweep list. Two things could silently diverge: the set of databases
swept, and the set of statuses the surface can render. Both are the kind of drift
that reports success — a page missing a status renders a blank cell, and a page
sweeping one fewer database reports "loaded" for a corpus sitting somewhere it
did not declare, which is the exact failure ``wrong-db`` exists to catch.

O58'S OWN WORDING IS THE EVIDENCE THAT THIS IS NEEDED. Its acceptance names "the
same six states"; ``docs_verify`` has had SEVEN since G102 added ``wrong-realm``.
A page built to the item's letter would have had no cell for the status that
replaced the wrong-db subject after the single-database fold.

WHY THE SWEEP LIST IS DUPLICATED RATHER THAN IMPORTED: ``drydocs.cli_docs`` is a
COMPONENT, and ``drydocs_api`` may not import it (the MODULE_MAP invariant). The
constant is therefore mirrored, and this guard is the mechanism that makes the
mirror safe — read from both modules, compared here.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi", reason="fastapi is an optional dep (the api group)")

from drydocs_api.corpus_status import SWEEP_DATABASES, corpus_status  # noqa: E402
from drydocs_core.docs_verify import STATUSES  # noqa: E402


class _FakeRunner:
    """A graph that answers SHOW DATABASES and nothing else.

    Deliberately returns NO rows for every corpus probe: the reconciliation's
    job is to report that as missing, and a fake that invented rows would test
    the fake.
    """

    def __init__(self, databases: list[str] | None = None, fail_show: bool = False) -> None:
        self._databases = databases if databases is not None else list(SWEEP_DATABASES)
        self._fail_show = fail_show
        self.queried: list[str] = []

    def run(self, cypher: str, params: dict, database: str):
        if cypher.startswith("SHOW DATABASES"):
            if self._fail_show:
                raise RuntimeError("permission denied")
            return ["name"], [{"name": db} for db in self._databases]
        self.queried.append(database)
        return [], []


SOURCES = [
    {
        "id": "demo-corpus",
        "target_db": "drydocs",
        "graph_locator": {"kind": "corpus_id", "value": "demo"},
    },
]


def test_the_two_call_sites_sweep_the_same_databases() -> None:
    """The mirrored constant, checked against its original.

    Read from the component's module rather than restated here, so this fails if
    either side changes alone.
    """
    from drydocs.cli_docs import DOC_SWEEP_DATABASES

    assert tuple(SWEEP_DATABASES) == tuple(DOC_SWEEP_DATABASES), (
        "the console sweep and the CLI verb no longer visit the same databases — a "
        "corpus in the database only ONE of them looks at is invisible to the other, "
        "which is the wrong-db failure class the sweep exists to catch"
    )


def test_the_payload_carries_every_status_the_reconciliation_can_return() -> None:
    """Not a hand-copied list. The page renders what this sends."""
    payload = corpus_status(SOURCES, _FakeRunner())
    assert set(payload["statuses"]) == set(STATUSES)
    assert len(payload["statuses"]) == 7, (
        "the status set changed size — the surface renders these, so a new status "
        "needs a look at the page's legend and colour map, not just this pin"
    )


def test_wrong_realm_is_present_because_the_item_said_six() -> None:
    """The specific miss O58's wording would have caused, pinned by name."""
    payload = corpus_status(SOURCES, _FakeRunner())
    assert "wrong-realm" in payload["statuses"]


def test_it_reports_which_databases_were_actually_queried() -> None:
    """The O56 honesty rule needs this: a database that was NOT queried renders
    "not queried", never 0 — and the rows alone cannot say which."""
    payload = corpus_status(SOURCES, _FakeRunner(databases=["drydocs"]))
    assert payload["databases_swept"] == list(SWEEP_DATABASES)
    assert payload["databases_queried"] == ["drydocs"]


def test_a_database_the_server_does_not_have_is_not_queried() -> None:
    runner = _FakeRunner(databases=["drydocs"])
    corpus_status(SOURCES, runner)
    assert "ddcontext" not in runner.queried


def test_a_refused_show_databases_does_not_report_everything_absent() -> None:
    """A failed PROBE must not become a false diagnosis about the world.

    Reporting every corpus as db-absent because the permission check failed is
    exactly the confidently-wrong shape this module exists to remove.
    """
    payload = corpus_status(SOURCES, _FakeRunner(fail_show=True))
    assert payload["databases_queried"] == list(SWEEP_DATABASES)
    assert all(r["status"] != "db-absent" for r in payload["rows"])


def test_the_payload_declares_its_own_classification() -> None:
    """It is not a spec result, so nothing else carries one for it."""
    assert corpus_status(SOURCES, _FakeRunner())["classification"] == "internal-public"


def test_rows_carry_the_fields_the_surface_renders() -> None:
    row = corpus_status(SOURCES, _FakeRunner())["rows"][0]
    assert set(row) == {
        "corpus_id",
        "target_db",
        "status",
        "documents",
        "chunks",
        "detail",
        "ok",
    }
