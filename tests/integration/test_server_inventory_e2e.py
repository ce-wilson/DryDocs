"""Z3 e2e — the synthetic server export through the real CLI into real Neo4j.

The acceptance's own words, proven against a throwaway Enterprise container
(the test_e2e_load harness): "a loader ingests the registered export per Z2's
signed shapes, IDEMPOTENTLY, with the sanitized fixture e2e green".

* bootstrap + the full default supplement chain (which now includes the
  infrastructure supplement — chain step 5);
* a seeded :BusinessApplication (the fixture's synthetic app 70055) and three
  seeded :ExecutionHost nodes — one exact-name match, one FQDN whose short
  name matches exactly one server (T2), one that matches nothing;
* `drydocs load-server-inventory --export <fixture>` — loader + the derived
  resolution pass in one verb;
* shape assertions per the signed rulings, then the verb AGAIN and a
  node/edge census diff of ZERO — idempotency as an assertion, not a claim;
* the Z3 QuerySpec traversal contract (UNMATCHED marker semantics) is
  unit-pinned in test_server_inventory_load.py; here we assert the graph
  halves it reads (RESOLVES_TO_SERVER tiers + LOCATED_IN geography) landed.

Opt-in and Docker-gated exactly like test_e2e_load: marked ``integration``
(deselected by default), auto-SKIPS without Docker.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "server_inventory" / "synthetic-server-export.csv"
DEV_ENVIRONMENT = REPO_ROOT / "config" / "dev-environment.yaml"

NEO4J_IMAGE = yaml.safe_load(DEV_ENVIRONMENT.read_text(encoding="utf-8"))["neo4j"]["image"]


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        return subprocess.run(["docker", "info"], capture_output=True, timeout=30).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not _docker_available(), reason="Docker daemon unavailable"),
]


@pytest.fixture(scope="module")
def neo4j_env():
    from testcontainers.neo4j import Neo4jContainer

    container = (
        Neo4jContainer(NEO4J_IMAGE)
        .with_env("NEO4J_PLUGINS", '["apoc"]')
        .with_env("NEO4J_ACCEPT_LICENSE_AGREEMENT", "eval")
    )
    with container as neo4j:
        yield {
            "NEO4J_URI": neo4j.get_connection_url(),
            "NEO4J_USER": neo4j.username,
            "NEO4J_PASSWORD": neo4j.password,
            "NEO4J_DATABASE": "neo4j",
        }


def _invoke(env: dict, *args: str):
    from typer.testing import CliRunner

    from drydocs.cli import app

    result = CliRunner().invoke(app, list(args), env=env)
    assert (
        result.exit_code == 0
    ), f"drydocs {' '.join(args)} exited {result.exit_code}:\n{result.output}"
    return result


def _client(env):
    from drydocs_core.neo4j_client import Neo4jClient

    return Neo4jClient(
        env["NEO4J_URI"], env["NEO4J_USER"], env["NEO4J_PASSWORD"], env["NEO4J_DATABASE"]
    )


_CENSUS = (
    "MATCH (s:Server) WITH count(s) AS servers "
    "MATCH (d:DataCenter) WITH servers, count(d) AS dcs "
    "OPTIONAL MATCH ()-[loc:LOCATED_IN]->() WITH servers, dcs, count(loc) AS located "
    "OPTIONAL MATCH (:Port)-[r:RUNS_ON {role:'technology_port'}]->() "
    "WITH servers, dcs, located, count(r) AS port_runs "
    "OPTIONAL MATCH ()-[res:RESOLVES_TO_SERVER]->() "
    "RETURN servers, dcs, located, port_runs, count(res) AS resolved"
)


@pytest.fixture(scope="module")
def loaded(neo4j_env):
    _invoke(neo4j_env, "bootstrap")
    # The FULL default chain — proves the infrastructure supplement (chain
    # step 5) lands against real Neo4j, not merely that its Cypher parses.
    _invoke(neo4j_env, "apply-supplements")
    with _client(neo4j_env) as cli:
        # The fixture's synthetic app (the reserved 70001-70099 block) — the
        # §C2 leg is MATCH-only, so the app must pre-exist to get its port.
        cli.run(
            "MERGE (a:BusinessApplication {app_id: '70055'}) "
            "SET a.seal_id = '70055', a.name = 'Synthetic App 70055'"
        )
        # Three Control-M-side hosts: T1 exact, T2 short-name, unmatched.
        cli.run("MERGE (h:ExecutionHost:Agent {nodeid: 'srv-synth-01'})")
        cli.run("MERGE (h:ExecutionHost:Agent {nodeid: 'SRV-SYNTH-02.corp.example'})")
        cli.run("MERGE (h:ExecutionHost:Agent {nodeid: 'no-such-box'})")
    _invoke(neo4j_env, "load-server-inventory", "--export", str(FIXTURE))
    return neo4j_env


def test_signed_shapes_landed(loaded) -> None:
    with _client(loaded) as cli:
        census = cli.run(_CENSUS)[0]
        assert census["servers"] == 5
        assert census["dcs"] == 2
        assert census["located"] == 5
        # One technology port, five RUNS_ON legs (both PROD and DR — §A3).
        assert census["port_runs"] == 5
        ports = cli.run(
            "MATCH (a:BusinessApplication {app_id:'70055'})-[:HAS_PORT]->"
            "(p:Port {kind:'Technology'}) RETURN count(p) AS n"
        )[0]
        assert ports["n"] == 1

        # §C1 tiers with evidence: exact + normalized, unmatched has NO edge.
        tiers = cli.run(
            "MATCH (h:ExecutionHost)-[r:RESOLVES_TO_SERVER]->(s:Server) "
            "RETURN h.nodeid AS nodeid, r.match_tier AS tier, "
            "r.match_evidence AS evidence ORDER BY nodeid"
        )
        assert {(t["nodeid"], t["tier"]) for t in tiers} == {
            ("srv-synth-01", "exact"),
            ("SRV-SYNTH-02.corp.example", "normalized"),
        }
        assert all(t["evidence"] for t in tiers)
        unmatched = cli.run(
            "MATCH (h:ExecutionHost {nodeid:'no-such-box'}) "
            "WHERE NOT (h)-[:RESOLVES_TO_SERVER]->() RETURN count(h) AS n"
        )[0]
        assert unmatched["n"] == 1

        # §B2: the grain declaration landed on the geography node.
        grains = cli.run("MATCH (d:DataCenter) RETURN collect(DISTINCT d.location_grain) AS g")[0]
        assert grains["g"] == ["building"]


def test_second_run_changes_nothing(loaded) -> None:
    """The acceptance's word: idempotently."""
    with _client(loaded) as cli:
        before = cli.run(_CENSUS)[0]
    _invoke(loaded, "load-server-inventory", "--export", str(FIXTURE))
    with _client(loaded) as cli:
        after = cli.run(_CENSUS)[0]
    assert after == before
