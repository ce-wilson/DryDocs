"""Session-wide teardown for process-global resources the suite touches.

Unit tests are pure; the one exception is the shared Neo4j driver in
``agents/common/neo4j_tool.py``, which is a deliberate per-process singleton
(drivers own a connection pool). Closing it belongs here, not in any one test.
"""

from __future__ import annotations

import sys

import pytest


def pytest_sessionstart(session) -> None:
    """S12 — fail the session ONCE, before any test, when the interpreter's
    installed packages disagree with poetry.lock (tests/env_drift.py). Drift,
    never path: a correctly provisioned Docker / tox / system-python run passes;
    a wrong-version install in the right directory fails."""
    from tests import env_drift

    offenders, checked = env_drift.check()
    if offenders:
        raise pytest.UsageError(env_drift.report(offenders, checked))


def pytest_sessionfinish(session, exitstatus) -> None:
    """Close the agents' shared Neo4j driver if anything in the run created it.

    ``tests/integration/test_graph_qa_read_mode.py`` builds the driver at
    COLLECTION time (its ``skipif`` probes connectivity at module scope), so the
    singleton exists even on the default run where ``-m 'not integration'``
    deselects every test in that file. Left open, it survives to interpreter
    shutdown and its destructor emits a DeprecationWarning about relying on
    ``__del__``. Looked up via ``sys.modules`` so this never imports the agents
    package — or their ``.env`` — into runs that did not already load it.
    """
    module = sys.modules.get("common.neo4j_tool")
    if module is not None:
        module.close_driver()
