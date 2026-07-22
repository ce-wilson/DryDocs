"""Guard: config/dev-environment.yaml is the single source of truth for local
dev/test infrastructure names — the .env.example templates must agree with it.

Hermetic (files only, no Docker/Neo4j): the point is that when the canonical
container/port/database changes, it changes in ONE place and this test forces
the templates to follow.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / "config" / "dev-environment.yaml"


def _load() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def test_schema_and_required_fields():
    cfg = _load()
    assert cfg["schema"] == "drydocs.dev-environment.v1"
    neo = cfg["neo4j"]
    assert neo["container"], "container name required"
    assert neo["image"], "image required"
    assert isinstance(neo["ports"]["bolt"], int)
    assert isinstance(neo["ports"]["http"], int)
    dbs = neo["databases"]
    assert set(dbs) == {"ground_truth", "lineage", "uncertain_context", "composite"}


def test_databases_match_provisioning_script():
    """The topology names here must be exactly what 01_databases.cypher creates."""
    dbs = _load()["neo4j"]["databases"]
    cypher = (
        REPO / "drydocs_core" / "schema" / "provisioning" / "01_databases.cypher"
    ).read_text(encoding="utf-8")
    for name in dbs.values():
        assert re.search(
            rf"CREATE (?:COMPOSITE )?DATABASE {re.escape(name)} IF NOT EXISTS", cypher
        ), f"database {name!r} not provisioned by 01_databases.cypher"


def test_env_templates_agree_with_canonical_bolt_port():
    neo = _load()["neo4j"]
    bolt = f"bolt://localhost:{neo['ports']['bolt']}"
    for template, key in [
        (REPO / ".env.example", "NEO4J_URI"),
        (REPO / "agents" / ".env.example", "NEO4J_URI"),
        (REPO / "web" / ".env.example", "VITE_NEO4J_URI"),
    ]:
        text = template.read_text(encoding="utf-8")
        m = re.search(rf"^{key}=(\S+)", text, re.MULTILINE)
        assert m, f"{template.name}: {key} line missing"
        assert m.group(1) == bolt, (
            f"{template.name}: {key}={m.group(1)} disagrees with "
            f"config/dev-environment.yaml bolt port {neo['ports']['bolt']}"
        )


def test_env_templates_target_ground_truth_db_not_home_db():
    neo = _load()["neo4j"]
    ground = neo["databases"]["ground_truth"]
    for template, key in [
        (REPO / ".env.example", "NEO4J_DATABASE"),
        (REPO / "agents" / ".env.example", "NEO4J_DATABASE"),
        (REPO / "web" / ".env.example", "VITE_NEO4J_DATABASE"),
    ]:
        text = template.read_text(encoding="utf-8")
        m = re.search(rf"^{key}=(\S+)", text, re.MULTILINE)
        assert m, f"{template.name}: {key} line missing"
        assert m.group(1) == ground, (
            f"{template.name}: {key}={m.group(1)} — templates must default to the "
            f"ADR 0002 ground-truth db {ground!r}, never the EE home db"
        )
