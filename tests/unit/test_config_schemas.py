"""S6 — JSON Schemas for the config families (config/schemas/).

The split of labor (S6's design): the SCHEMA owns shape — required keys,
types, closed enums, the urn-refusal — so a malformed entry fails in the
editor (any JSON-Schema-aware YAML plugin picks the schemas up) rather than
minutes later in pytest. The TESTS keep semantics — cross-file joins
(classification levels vs registry labels), lifecycle rules, retired-id
refusal — exactly where they already live.

Deliberately NO drydocs_core import anywhere in this module: the acceptance
requires the schemas be usable by consumers with no Python dependency on the
package (the console's admin surface, the agent tier), and the subprocess
test proves it end to end.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml", reason="PyYAML not installed")
jsonschema = pytest.importorskip("jsonschema", reason="jsonschema not installed (dev group)")

from jsonschema import Draft202012Validator  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "config" / "schemas"

#: family -> (schema file, live files it governs). Fragment families list a
#: whole directory; every fragment must validate against the one schema.
FAMILIES: dict[str, tuple[str, list[Path]]] = {
    "source-registry": (
        "source-registry.schema.json",
        [REPO / "config" / "source-registry.yaml"],
    ),
    "precedence": (
        "precedence.schema.json",
        [REPO / "config" / "precedence.yaml"],
    ),
    "classification": (
        "classification.schema.json",
        [REPO / "config" / "classification.yaml"],
    ),
    "source-mapping": (
        "source-mapping.schema.json",
        sorted((REPO / "config" / "source-mappings").glob("*.yaml")),
    ),
    "taxonomy-ontology-map": (
        "taxonomy-ontology-map.schema.json",
        sorted((REPO / "config" / "taxonomy-ontology-map").glob("*.yaml")),
    ),
    "relationship-vocabulary": (
        "relationship-vocabulary.schema.json",
        sorted((REPO / "drydocs_core" / "ontology" / "relationship_vocabulary").glob("*.yaml")),
    ),
    "domains": (
        "domains.schema.json",
        [REPO / "config" / "taxonomy" / "domains.yaml"],
    ),
    "editions": (
        "editions.schema.json",
        [REPO / "config" / "taxonomy" / "editions.yaml"],
    ),
    "data-centers": (
        "data-centers.schema.json",
        [REPO / "config" / "taxonomy" / "data-centers.yaml"],
    ),
}


def _schema(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def _load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# every family has a schema; every schema is itself valid draft 2020-12
# --------------------------------------------------------------------------- #


def test_every_family_has_a_valid_schema() -> None:
    for family, (schema_name, files) in FAMILIES.items():
        schema = _schema(schema_name)
        Draft202012Validator.check_schema(schema)
        assert files, f"{family}: the live-file glob matched nothing — the family moved?"


def test_no_stray_schema_files() -> None:
    """Every schema on disk is claimed by a family — an unclaimed schema is
    either a rename leftover or an unguarded new family."""
    claimed = {name for name, _ in FAMILIES.values()}
    on_disk = {p.name for p in SCHEMAS.glob("*.schema.json")}
    assert on_disk == claimed, f"unclaimed/missing schemas: {on_disk ^ claimed}"


# --------------------------------------------------------------------------- #
# the live files validate
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("family", sorted(FAMILIES))
def test_live_files_validate(family: str) -> None:
    schema_name, files = FAMILIES[family]
    validator = Draft202012Validator(_schema(schema_name))
    problems: list[str] = []
    for path in files:
        for err in validator.iter_errors(_load(path)):
            problems.append(f"{path.relative_to(REPO)} :: {err.json_path}: {err.message}")
    assert not problems, "\n".join(problems)


# --------------------------------------------------------------------------- #
# a malformed entry fails with a PATH-PRECISE message naming the offending key
# --------------------------------------------------------------------------- #

_MALFORMED: dict[str, tuple[dict | list, str]] = {
    # registry: a hand-maintained urn (refused by schema AND by from_yaml)
    "source-registry": (
        {
            "schema": "drydocs.source-registry.v2",
            "updated": "2026-08-07",
            "systems": [
                {"id": "x", "name": "X", "classification": "Internal", "urn": "urn:hand:rolled"}
            ],
            "datasets": [],
        },
        "$.systems[0]",
    ),
    # precedence: authority must be an integer
    "precedence": (
        {
            "schema": "drydocs.precedence.v1",
            "updated": "2026-08-07",
            "order": [{"id": "a", "authority": "first", "role": "r", "governs": ["x"]}],
        },
        "$.order[0].authority",
    ),
    # classification: publishable must be a bool
    "classification": (
        {
            "schema": "drydocs.classification.v1",
            "updated": "2026-08-07",
            "levels": [{"id": "External", "rank": 0, "publishable": "yes", "description": "d"}],
            "publish_rule": {},
        },
        "$.levels[0].publishable",
    ),
    # source-mapping: a disposition outside the doc-08 vocabulary
    "source-mapping": (
        {
            "schema": "drydocs.source-mapping.v1",
            "source": "psgmgr",
            "classification": "Internal-Public",
            "objects": [{"name": "T", "columns": [{"name": "C", "disposition": "kept"}]}],
        },
        "$.objects[0].columns[0].disposition",
    ),
    # map fragment: a status outside the lifecycle
    "taxonomy-ontology-map": (
        [{"id": "x-map", "status": "loaded"}],
        "$[0].status",
    ),
    # vocabulary fragment: an entry missing its gate-bound status entirely
    "relationship-vocabulary": (
        [{"id": "x_edge", "neo4j_label": "X_EDGE", "from_node": "A", "to_node": "B"}],
        "$[0]",
    ),
    # domain registry: a row with no vocabulary_fragment (REQUIRED, gate sB3)
    "domains": (
        {
            "schema": "drydocs.domains.v1",
            "classification": "Internal-Public",
            "updated": "2026-09-04",
            "domains": [
                {
                    "id": "topic",
                    "title": "T",
                    "minted_by": "producer",
                    "registered_at": "2026-09-04",
                    "authority": "x",
                    "status": "active",
                }
            ],
        },
        "$.domains[0]",
    ),
    # edition registry: a lowercase code (the segment is 2-5 UPPERCASE letters, sC1)
    "editions": (
        {
            "schema": "drydocs.editions.v1",
            "classification": "Internal",
            "updated": "2026-09-04",
            "editions": [
                {
                    "code": "xmpl",
                    "title": "T",
                    "area_product_id": "AP",
                    "minted_by": "producer",
                    "registered_at": "2026-09-04",
                    "authority": "x",
                }
            ],
        },
        "$.editions[0].code",
    ),
    # data-center registry: a row with only one spelling (the PAIRING is the fact)
    "data-centers": (
        {
            "schema": "drydocs.data-centers.v1",
            "classification": "Internal",
            "updated": "2026-09-04",
            "data_centers": [{"code": "P12"}],
        },
        "$.data_centers[0]",
    ),
}


@pytest.mark.parametrize("family", sorted(_MALFORMED))
def test_malformed_entry_fails_path_precise(family: str) -> None:
    schema_name, _ = FAMILIES[family]
    doc, expected_path = _MALFORMED[family]
    validator = Draft202012Validator(_schema(schema_name))
    errors = list(validator.iter_errors(doc))
    assert errors, f"{family}: the deliberately malformed fixture validated clean"
    best = jsonschema.exceptions.best_match(errors)
    paths = (
        {best.json_path}
        | {e.json_path for err in errors for e in (err.context or [])}
        | {e.json_path for e in errors}
    )
    assert any(
        p.startswith(expected_path) for p in paths
    ), f"{family}: no error path names the offending key {expected_path}; got {sorted(paths)}"


# --------------------------------------------------------------------------- #
# usable WITHOUT importing drydocs_core (console admin surface / agent tier)
# --------------------------------------------------------------------------- #

_STANDALONE = """
import json, sys
import yaml, jsonschema
assert "drydocs_core" not in sys.modules and "drydocs" not in sys.modules
schema = json.load(open(sys.argv[1], encoding="utf-8"))
doc = yaml.safe_load(open(sys.argv[2], encoding="utf-8"))
jsonschema.Draft202012Validator(schema).validate(doc)
assert "drydocs_core" not in sys.modules and "drydocs" not in sys.modules
print("standalone-ok")
"""


def test_schemas_validate_without_importing_drydocs_core(tmp_path: Path) -> None:
    script = tmp_path / "standalone.py"
    script.write_text(_STANDALONE, encoding="utf-8")
    res = subprocess.run(
        [
            sys.executable,
            str(script),
            str(SCHEMAS / "precedence.schema.json"),
            str(REPO / "config" / "precedence.yaml"),
        ],
        capture_output=True,
        encoding="utf-8",
        cwd=tmp_path,  # not the repo root — no accidental package resolution
    )
    assert res.returncode == 0, res.stderr
    assert "standalone-ok" in res.stdout


def test_this_module_itself_stays_core_free() -> None:
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split('"""', 2)[2]  # ignore the docstring's prose mentions
    needle = "import " + "drydocs"  # split so this line does not match itself
    assert needle not in body, "the schema guard must not depend on the package"
