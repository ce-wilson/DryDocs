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
PROVISIONING = REPO / "drydocs_core" / "schema" / "provisioning" / "01_databases.cypher"

#: Same idiom as ``tests/unit/test_database_names.py`` — deliberately a local copy
#: rather than a cross-test import: the two guards read the same DDL for different
#: reasons (that one checks CODE against it, this one checks CONFIG against it) and
#: neither should be able to break the other by editing its own parser.
_CREATE_DB = re.compile(
    r"CREATE\s+(?:COMPOSITE\s+)?DATABASE\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE
)


def _load() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def _provisioned() -> set[str]:
    text = PROVISIONING.read_text(encoding="utf-8")
    # Strip // comments so a commented-out CREATE never counts as provisioned.
    live = "\n".join(line.split("//")[0] for line in text.splitlines())
    return set(_CREATE_DB.findall(live))


def test_schema_and_required_fields():
    cfg = _load()
    assert cfg["schema"] == "drydocs.dev-environment.v1"
    neo = cfg["neo4j"]
    assert neo["container"], "container name required"
    assert neo["image"], "image required"
    assert isinstance(neo["ports"]["bolt"], int)
    assert isinstance(neo["ports"]["http"], int)
    dbs = neo["databases"]
    assert set(dbs) == {
        "ground_truth",
        "lineage",
        "uncertain_context",
        "composite",
        "schema_meta",
    }


def test_databases_match_provisioning_script():
    """The topology names here must be exactly what 01_databases.cypher creates.

    BIDIRECTIONAL on purpose. The first version asserted only that every name in
    this file is provisioned — a subset check whose docstring already said
    "exactly". G51 walked straight through it: ``ddschema`` was added to the DDL
    and never to this file, so the single source of truth for the local stack went
    stale on a green suite. Same defect, same day, as the CODE-side guard G51 itself
    widened (``test_module_level_database_constants_are_provisioned`` keyed on the
    literal identifier ``DATABASE``), and the same family as J26.
    """
    declared = set(_load()["neo4j"]["databases"].values())
    provisioned = _provisioned()

    missing_here = provisioned - declared
    assert not missing_here, (
        f"provisioned by 01_databases.cypher but absent from {CONFIG.name}: "
        f"{sorted(missing_here)} — add it to neo4j.databases (and to the key set in "
        "test_schema_and_required_fields, which is the deliberate speed bump)"
    )
    missing_there = declared - provisioned
    assert not missing_there, (
        f"declared in {CONFIG.name} but not provisioned by 01_databases.cypher: "
        f"{sorted(missing_there)}"
    )


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


PROVISION_PS1 = REPO / "drydocs_core" / "schema" / "provisioning" / "provision.ps1"


def test_plugins_are_declared():
    """Plugins are infrastructure, so they belong in the canonical file too.

    They were invisible here while `NEO4J_PLUGINS=[apoc]` sat on the container and
    /plugins held only README.txt — declared nowhere, verified by nothing, and only
    noticed when `drydocs bootstrap` refused with "APOC required" (2026-07-28).
    """
    neo = _load()["neo4j"]
    assert neo["plugins_volume"], "the plugins volume must be named here"
    assert neo["plugins_volume"] != neo["volume"], "plugins and data are separate volumes"
    assert set(neo["plugins"]) >= {"apoc", "graph-data-science"}


def test_provisioning_header_matches_canonical_container():
    """The documented `docker run` must not drift from the canonical facts.

    It did: the header said `neo4j:5-enterprise`, no volume mounts, and the
    NEO4J_PLUGINS env-var form — while the real container ran 2026.05.0 with a
    named data volume. A stale recipe is worse than none; it gets copy-pasted.
    """
    neo = _load()["neo4j"]
    header = PROVISION_PS1.read_text(encoding="utf-8")
    for token in (
        neo["image"],
        f"{neo['volume']}:/data",
        f"{neo['plugins_volume']}:/plugins",
        f"--name {neo['container']}",
        f"-p {neo['ports']['http']}:{neo['ports']['http']}",
        f"-p {neo['ports']['bolt']}:{neo['ports']['bolt']}",
    ):
        assert token in header, f"provision.ps1 no longer documents {token!r}"


def test_provisioning_header_warns_off_the_download_form():
    """NEO4J_PLUGINS must not come back as the recommended mechanism.

    It fails OPEN — the container starts fine and the plugin is simply missing —
    so nothing surfaces the mistake until a loader refuses.
    """
    header = PROVISION_PS1.read_text(encoding="utf-8")
    assert "DO NOT use" in header and "NEO4J_PLUGINS" in header
    for proc in ("apoc.*", "gds.*"):
        assert proc in header, f"allowlist for {proc} missing from the documented run"
