"""O33 live proof — the meta-graph applied to a REAL database contaminates
nothing: every QuerySpec returns zero rows, no loader guard is satisfied,
and the runs_on write path refuses the exemplar bait.

Opt-in and Docker-gated exactly like test_e2e_load (J9 harness): marked
``integration``, deselected by default, auto-skips without Docker. Needs no
bundled samples and no bootstrap — the whole point is a database holding
ONLY the schema exemplars.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_GRAPH = REPO_ROOT / "drydocs_core" / "schema" / "schema_graph.cypher"
RUNS_ON_CYPHER = REPO_ROOT / "drydocs" / "loaders" / "cypher" / "runs_on_resolution.cypher"
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
def meta_only_client():
    """A throwaway Neo4j holding ONLY the applied schema meta-graph."""
    from testcontainers.neo4j import Neo4jContainer

    from drydocs_core.neo4j_client import Neo4jClient

    container = (
        Neo4jContainer(NEO4J_IMAGE)
        .with_env("NEO4J_PLUGINS", '["apoc"]')
        .with_env("NEO4J_ACCEPT_LICENSE_AGREEMENT", "eval")
    )
    with container as neo4j:
        with Neo4jClient(
            neo4j.get_connection_url(), neo4j.username, neo4j.password, "neo4j"
        ) as client:
            client.run_script(SCHEMA_GRAPH.read_text(encoding="utf-8"))
            yield client


def test_exemplars_are_present(meta_only_client) -> None:
    """Sanity: the fixture really applied the meta-graph — the contamination
    exists for the other tests to disprove reaching."""
    rows = meta_only_client.run("MATCH (n:SchemaMeta) RETURN count(n) AS n")
    assert rows[0]["n"] >= 40


def test_no_spec_returns_a_schema_meta_row(meta_only_client) -> None:
    """The O33 acceptance clause, verbatim: with the meta-graph applied,
    every registered QuerySpec returns ZERO rows — the exemplars (and their
    property-qualified exemplar edges) satisfy no spec."""
    from drydocs_api.query_specs import QUERY_SPECS

    offenders = {}
    for spec in QUERY_SPECS.values():
        params = {p.name: p.default for p in spec.params}
        rows = meta_only_client.run(spec.cypher, **params)
        if rows:
            offenders[spec.id] = rows[:3]
    assert not offenders, f"specs returned exemplar rows: {offenders}"


def test_no_loader_guard_is_satisfied_by_exemplars_alone(meta_only_client) -> None:
    """The write-side clause: every whole-registry prereq probe counts ZERO
    against a database of exemplars — while the bare (unguarded) count is
    positive, proving the predicate is what excludes them."""
    for label, key in (
        ("BusinessApplication", "seal_id"),
        ("SoftwareProduct", "product_id"),
        ("DocSection", "anchor"),
        ("Employee", "employee_id"),
    ):
        bare = meta_only_client.run(f"MATCH (n:{label}) RETURN count(n) AS n")[0]["n"]
        assert bare > 0, f"exemplar for {label} missing — fixture regressed"
        guarded = meta_only_client.run(
            f"MATCH (n:{label}) WHERE NOT n:SchemaMeta AND n.{key} IS NOT NULL "
            "RETURN count(n) AS n"
        )[0]["n"]
        assert guarded == 0, f"{label} guard satisfied by exemplars alone"


def test_runs_on_resolution_refuses_the_exemplar_bait(meta_only_client) -> None:
    """The one write path an exemplar could reach: a real job whose node_id
    IS the label string 'ControlMHostGroup' must resolve to nothing — never
    edge to the schema exemplar."""
    meta_only_client.run(
        "MERGE (j:ControlMJob {folder_id: 'F-EXEMPLAR-BAIT', job_id: '1'}) "
        "SET j.job_name = 'bait', j.node_id = 'ControlMHostGroup'"
    )
    try:
        meta_only_client.run_script(
            RUNS_ON_CYPHER.read_text(encoding="utf-8"),
            params={
                "run_id": "o33-test-run",
                "resolved_at": "2026-07-28T00:00:00+00:00",
                "loader": "runs_on_resolution.test",
            },
        )
        rows = meta_only_client.run(
            "MATCH (:ControlMJob {folder_id: 'F-EXEMPLAR-BAIT'})"
            "-[r:RUNS_ON]->(t) RETURN count(r) AS edges"
        )
        assert rows[0]["edges"] == 0, "resolution edged the bait job to an exemplar"
    finally:
        meta_only_client.run("MATCH (j:ControlMJob {folder_id: 'F-EXEMPLAR-BAIT'}) DETACH DELETE j")
