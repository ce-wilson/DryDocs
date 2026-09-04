"""LIN2 (d)/(e) - ``drydocs lineage-extract`` then ``drydocs lineage-load --write``
against a REAL Neo4j (testcontainers, J9): the bundled-sample artifact loads its
Script / ETLProcess nodes and the confirmed INVOKES edges into a database literally
named ``drydocs`` (the trust boundary refuses anything else), the graph count matches
the WritePlan, a second run is idempotent (MERGE - counts unchanged, one more :JobRun),
and every written node and rel names the extract it came from.

The :ControlMJob endpoints are MATCHed, never MERGEd (the M3 load owns them), so this
test seeds them from the artifact's own job ids before the load - the same seeding
shape ``test_server_inventory_e2e.py`` uses for its hosts.

Marked ``integration`` and deselected by default; run with
``poetry run pytest tests/integration -m integration -q``.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
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
            "NEO4J_DATABASE": "drydocs",
        }


def _invoke(env: dict, *args: str):
    from typer.testing import CliRunner

    from drydocs.cli import app

    result = CliRunner().invoke(app, list(args), env=env)
    assert (
        result.exit_code == 0
    ), f"drydocs {' '.join(args)} exited {result.exit_code}:\n{result.output}"
    return result


def _client(env, database: str = "drydocs"):
    from drydocs_core.neo4j_client import Neo4jClient

    return Neo4jClient(env["NEO4J_URI"], env["NEO4J_USER"], env["NEO4J_PASSWORD"], database)


_CENSUS = (
    "OPTIONAL MATCH (s:Script) WITH count(s) AS scripts "
    "OPTIONAL MATCH (e:ETLProcess) WITH scripts, count(e) AS etl "
    "OPTIONAL MATCH ()-[r:INVOKES]->() WITH scripts, etl, count(r) AS invokes "
    "OPTIONAL MATCH (run:JobRun {loader: 'lineage-load'}) "
    "RETURN scripts, etl, invokes, count(run) AS loads"
)


@pytest.fixture(scope="module")
def staged(neo4j_env, tmp_path_factory):
    """Provision + bootstrap ``drydocs``, stage the bundled samples into a tmp data root,
    seed the :ControlMJob endpoints, and write a decisions file confirming every INVOKES."""
    with _client(neo4j_env, "system") as sys_cli:
        sys_cli.run_script("CREATE DATABASE drydocs IF NOT EXISTS WAIT")
    _invoke(neo4j_env, "bootstrap")

    root = tmp_path_factory.mktemp("lineage-root")
    env = {**neo4j_env, "DRYDOCS_DATA_ROOT": str(root), "DRYDOCS_LOGDIR": str(root / "logs")}
    _invoke(env, "lineage-extract")
    artifact = sorted((root / "lineage" / "staged").glob("lineage-*.json"))[-1]
    data = json.loads(artifact.read_text(encoding="utf-8"))
    invokes = [r for r in data["graph"]["rels"] if r[1] == "INVOKES"]
    assert invokes, "the bundled samples carry INVOKES candidates"

    with _client(neo4j_env) as cli:
        for p in data["graph"]["processes"]:
            if p["kind"] != "controlm_job":
                continue
            folder_id, job_id = p["node_id"].split(":", 1)[1].split(".", 1)
            cli.run(
                "MERGE (j:ControlMJob {folder_id: $f, job_id: $j}) SET j.name = $n",
                f=folder_id,
                j=job_id,
                n=p["name"],
            )
    decisions = root / "decisions.json"
    decisions.write_text(
        json.dumps(
            {
                "schema": "drydocs.lineage-decisions.v1",
                "doc": "e2e",
                "exported": "2026-09-04T00:00:00Z",
                "decisions": [
                    {"from": a, "type": t, "to": b, "decision": "confirmed"} for a, t, b in invokes
                ],
            }
        ),
        encoding="utf-8",
    )
    return {
        "env": env,
        "artifact": artifact,
        "data": data,
        "decisions": decisions,
        "invokes": invokes,
    }


def _plan(staged) -> tuple[int, int, int]:
    from drydocs_lineage.model import LineageGraph
    from drydocs_lineage.writer import plan_curated

    graph = LineageGraph.from_dict(staged["data"]["graph"])
    plan = plan_curated(graph, {tuple(r) for r in staged["invokes"]})
    return plan.scripts, plan.etl_processes, plan.rels


def test_the_load_lands_the_plan_exactly_and_names_its_extract(neo4j_env, staged) -> None:
    env, data = staged["env"], staged["data"]
    result = _invoke(
        env,
        "lineage-load",
        str(staged["artifact"]),
        "--confirmed",
        str(staged["decisions"]),
        "--write",
    )
    assert f"wrote {len(staged['invokes'])} rel(s) to drydocs" in result.output.replace("\n", "")
    scripts, etl, rels = _plan(staged)
    with _client(neo4j_env) as cli:
        census = cli.run(_CENSUS)[0]
        assert (census["scripts"], census["etl"], census["invokes"]) == (scripts, etl, rels)
        assert census["loads"] == 1
        stamped = cli.run(
            "MATCH (n) WHERE n:Script OR n:ETLProcess "
            "RETURN count(n) AS nodes, count(n.extract_run_id) AS with_run, "
            "collect(DISTINCT n.extract_code_commit) AS commits"
        )[0]
        assert stamped["nodes"] == stamped["with_run"] == scripts + etl
        assert stamped["commits"] == [data["code_commit"]]
        rel_stamp = cli.run(
            "MATCH ()-[r:INVOKES]->() RETURN count(r) AS n, "
            "count(r.extract_run_id) AS with_run, collect(DISTINCT r.extract_run_id) AS runs"
        )[0]
        assert rel_stamp["n"] == rel_stamp["with_run"] == rels
        assert rel_stamp["runs"] == [data["run_id"]]
        run = cli.run(
            "MATCH (run:JobRun {loader: 'lineage-load'}) "
            "RETURN run.status AS status, run.extract_run_id AS extract, run.sources AS sources"
        )[0]
        assert run["status"] == "COMPLETED" and run["extract"] == data["run_id"]
        sources = [json.loads(s) for s in run["sources"]]
        assert sources == data["sources"], "the artifact's sources block, verbatim, on the graph"
        by_hop = {s["hop"]: s for s in sources}
        assert by_hop["controlm"]["present"] is True
        # the variables CSV is machine-local (drydocs/data/ is ignored); whichever way
        # it went on this machine, the graph says what the EXTRACTOR saw, not a default
        expected = data["acquisition"]["variables"] == "bundled-samples"
        assert by_hop["controlm_variables"]["present"] is expected


def test_a_second_run_is_idempotent(neo4j_env, staged) -> None:
    env = staged["env"]
    with _client(neo4j_env) as cli:
        before = cli.run(_CENSUS)[0]
    _invoke(
        env,
        "lineage-load",
        str(staged["artifact"]),
        "--confirmed",
        str(staged["decisions"]),
        "--write",
    )
    with _client(neo4j_env) as cli:
        after = cli.run(_CENSUS)[0]
    assert (after["scripts"], after["etl"], after["invokes"]) == (
        before["scripts"],
        before["etl"],
        before["invokes"],
    )
    assert after["loads"] == before["loads"] + 1, "each load is its own :JobRun"


def test_plan_only_touches_nothing(neo4j_env, staged) -> None:
    env = staged["env"]
    with _client(neo4j_env) as cli:
        before = cli.run(_CENSUS)[0]
    _invoke(env, "lineage-load", str(staged["artifact"]), "--confirmed", str(staged["decisions"]))
    with _client(neo4j_env) as cli:
        assert cli.run(_CENSUS)[0] == before
