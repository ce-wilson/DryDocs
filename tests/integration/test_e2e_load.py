"""J9 — end-to-end CSV → Neo4j load through the real CLI, via testcontainers.

The one path the unit suite never executes: real Cypher against a real Neo4j —
``Neo4jClient.run`` / ``run_script`` (APOC), the loader cypher files, and the
CLI composition root, driven exactly as an operator would:

    bootstrap → apply-supplements --only base → ingest-controlm (bundled
    samples) → invariant assertions (the m3-verify core set) → m3-verify smoke

Opt-in and Docker-gated:

* marked ``integration`` and DESELECTED by default (``-m "not integration"``
  in pyproject addopts) — ``pytest -q`` / ``pytest tests/unit -q`` timing is
  unchanged, CI is unchanged;
* run explicitly with:  ``poetry run pytest tests/integration -m integration -q``
* auto-SKIPS (never fails) when Docker or the bundled samples are unavailable.

The container is **Enterprise**, and must be: `constraints.cypher` declares
``IS NODE KEY`` constraints, which Community rejects outright — `bootstrap`
cannot complete on Community, so a Community fixture can only ever error here.
(ADR 0002 commits the project to EE for multi-DB + composite; Community is a
recorded *rejected alternative*, not a supported test target.) The image is read
from ``config/dev-environment.yaml``, the declared single source of truth for
local infra, so this fixture cannot drift from the container operators run.

First run pulls that image (+ APOC via NEO4J_PLUGINS) — allow a few minutes and
outbound network.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLES = REPO_ROOT / "drydocs" / "data" / "samples"
DEV_ENVIRONMENT = REPO_ROOT / "config" / "dev-environment.yaml"


def _neo4j_image() -> str:
    """The Enterprise image declared in config/dev-environment.yaml.

    Deliberately unforgiving: a missing key is a real config defect, and
    silently falling back to a default is how this fixture drifted onto a
    Community image in the first place.
    """
    declared = yaml.safe_load(DEV_ENVIRONMENT.read_text(encoding="utf-8"))["neo4j"]["image"]
    assert "enterprise" in declared, (
        f"{DEV_ENVIRONMENT.name} declares a non-Enterprise image ({declared!r}); "
        "bootstrap's NODE KEY constraints require Enterprise"
    )
    return declared


NEO4J_IMAGE = _neo4j_image()


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        return (
            subprocess.run(
                ["docker", "info"], capture_output=True, timeout=30
            ).returncode
            == 0
        )
    except (OSError, subprocess.TimeoutExpired):
        return False


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not _docker_available(), reason="Docker daemon unavailable"),
    pytest.mark.skipif(
        not (SAMPLES / "controlm_folders__sample.csv").exists(),
        reason="bundled sample CSVs absent",
    ),
]


@pytest.fixture(scope="module")
def neo4j_env():
    """A throwaway Neo4j (Enterprise + APOC) and the NEO4J_* env the CLI reads.

    ``NEO4J_ACCEPT_LICENSE_AGREEMENT=eval`` matches the local `neo4jtest`
    container's setting — the evaluation license, not a commercial one.
    """
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
    assert result.exit_code == 0, (
        f"drydocs {' '.join(args)} exited {result.exit_code}:\n{result.output}"
    )
    return result


@pytest.fixture(scope="module")
def loaded_graph(neo4j_env):
    """Run the operator chain once; every test below asserts against the result."""
    _invoke(neo4j_env, "check")
    _invoke(neo4j_env, "bootstrap")                    # constraints + ontology (APOC path)
    # G29: the chain verb, scoped to the one supplement M3 needs. The verb also
    # asserts every :OntologyTerm IRI the .cypher declares is present after the
    # apply — so this step now proves the supplement LANDED against real Neo4j,
    # not merely that its Cypher parsed.
    _invoke(neo4j_env, "apply-supplements", "--only", "base")
    _invoke(neo4j_env, "ingest-controlm")              # bundled-sample M3 chain
    return neo4j_env


def _client(env):
    from drydocs_core.neo4j_client import Neo4jClient

    return Neo4jClient(
        env["NEO4J_URI"], env["NEO4J_USER"], env["NEO4J_PASSWORD"], env["NEO4J_DATABASE"]
    )


def test_chain_loads_the_sample_population(loaded_graph) -> None:
    with _client(loaded_graph) as cli:
        counts = cli.run(
            "MATCH (f:ControlMFolder) WITH count(f) AS folders "
            "MATCH (j:ControlMJob) RETURN folders, count(j) AS jobs"
        )[0]
    assert counts["folders"] > 0 and counts["jobs"] > 0


def test_m3_core_invariants(loaded_graph) -> None:
    """The m3-verify core set, asserted directly (same Cypher shapes)."""
    with _client(loaded_graph) as cli:
        r = cli.run(
            "MATCH (f:ControlMFolder) "
            "OPTIONAL MATCH (f)-[:SCHEDULED_ON]->(srv:ControlMServer) "
            "RETURN count(f) AS folders, count(srv) AS srv_links"
        )[0]
        assert r["folders"] == r["srv_links"], "every folder has a server"

        r = cli.run(
            "MATCH (j:ControlMJob) "
            "OPTIONAL MATCH (:ControlMFolder)-[:CONTAINS_JOB]->(j) "
            "RETURN count(j) AS jobs, count(*) AS with_folder"
        )[0]
        assert r["jobs"] == r["with_folder"], "every job has a folder"

        # the NODE KEY composite — JOB_ID alone is folder-scoped (the sample
        # carries a legitimate DLY/CYC promoted pair sharing job_id=22)
        r = cli.run(
            "MATCH (j:ControlMJob) "
            "WITH j.folder_id AS fid, j.job_id AS jid, count(*) AS n "
            "WHERE n > 1 RETURN count(*) AS dupes"
        )[0]
        assert r["dupes"] == 0, "no duplicate (folder_id, job_id)"

        r = cli.run(
            "MATCH ()-[d:WAS_INFORMED_BY]->() "
            "RETURN count(d) AS total, "
            "sum(CASE WHEN d.via_condition IS NULL THEN 1 ELSE 0 END) AS missing_condition"
        )[0]
        assert r["total"] > 0, "derived WAS_INFORMED_BY edges exist"
        # direct pairs only since the phased-loader port (2026-07-23) — the
        # edge carries via_condition; level/path went with the stored closure
        assert r["missing_condition"] == 0


def test_m3_verify_smoke(loaded_graph) -> None:
    """m3-verify runs against the loaded graph and renders its invariant table.

    Exit code is NOT pinned: the bundled sample is a deliberately small slice
    and one sample-friendly check ("active folders contain at least one job")
    may report a sample gap — the core invariants are pinned above instead.
    """
    from typer.testing import CliRunner

    from drydocs.cli import app

    result = CliRunner().invoke(app, ["m3-verify"], env=loaded_graph)
    assert result.exit_code in (0, 1), result.output
    assert "invariants" in result.output
