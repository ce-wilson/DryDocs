"""R2 — server-enforced READ mode is the write boundary, proven on a live graph.

The acceptance clause this exists for: *"a write-shaped query is rejected
server-side by READ access mode (a test proves the token guard alone is NOT
the boundary)"*. Two probes, each chosen to slip a token guard:

- ``CREATE(x:...)`` — no space after CREATE, so the agents' legacy
  ``_WRITE_TOKENS`` substring guard misses it;
- ``CALL db.createLabel(...)`` — a write PROCEDURE; tokenizes as
  ``createlabel``, so even the word-boundary API guard misses it.

Both must be rejected by the server inside graph_read's READ-access session.

Opt-in like the other integration tests: marked ``integration`` (deselected
by default) and auto-SKIPS when the local Neo4j (config/dev-environment.yaml
container) is unreachable. Uses agents/.env for credentials, same as the
service itself.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
for entry in (str(REPO_ROOT / "agents"), str(REPO_ROOT)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

pytestmark = pytest.mark.integration


def _connectable() -> bool:
    try:
        from common.neo4j_tool import get_driver

        get_driver().verify_connectivity()
        return True
    except Exception:
        return False


needs_neo4j = pytest.mark.skipif(
    not _connectable(), reason="local Neo4j not reachable (agents/.env / bolt:7687)"
)


@needs_neo4j
def test_read_query_works() -> None:
    from common.graph_read import run_read

    result = run_read("RETURN 1 AS ok")
    assert result.records == [{"ok": 1}]
    assert result.row_count == 1


@needs_neo4j
@pytest.mark.parametrize(
    "probe",
    [
        "CREATE(x:GuardProbe {p: 1}) RETURN x",  # evades the legacy substring guard
        "CALL db.createLabel('GuardProbe')",     # evades BOTH token guards
    ],
)
def test_server_rejects_writes_the_token_guards_miss(probe: str) -> None:
    from common.graph_read import CypherReadError, run_read
    from common.neo4j_tool import _WRITE_TOKENS

    # At least one probe slips the legacy guard entirely; the CALL probe slips both.
    normalized = " " + " ".join(probe.lower().split()) + " "
    if probe.startswith("CALL"):
        from drydocs_api.guard import is_write_cypher

        assert not any(tok in normalized for tok in _WRITE_TOKENS)
        assert is_write_cypher(probe) is None  # even the API guard misses it
    else:
        assert not any(tok in normalized for tok in _WRITE_TOKENS)

    with pytest.raises(CypherReadError) as exc_info:
        run_read(probe)
    message = str(exc_info.value).lower()
    assert "read" in message or "write" in message  # server access-mode rejection

    # and nothing was written
    from common.graph_read import run_read as rr

    assert rr("MATCH (x:GuardProbe) RETURN count(x) AS n").records == [{"n": 0}]
