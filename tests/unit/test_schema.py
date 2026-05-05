"""Static checks on the Cypher schema files (no Neo4j connection required)."""
from __future__ import annotations

import re
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "drydocs" / "schema"
CONSTRAINTS_FILE = SCHEMA_DIR / "constraints.cypher"
ONTOLOGY_FILE = SCHEMA_DIR / "ontology.cypher"

EXPECTED_CONSTRAINTS = 33

EXPECTED_ONTOLOGY_LABELS = [
    "DprodClass",
    "DcatClass",
    "ProvClass",
    "DqvClass",
    "OrgClass",
    "SwoClass",
    "OlClass",
    "Role",
    "SchedulerKind",
    "BusinessSegment",
    "Dimension",
    "Metric",
]


def test_schema_files_exist() -> None:
    assert CONSTRAINTS_FILE.exists(), f"Missing: {CONSTRAINTS_FILE}"
    assert ONTOLOGY_FILE.exists(), f"Missing: {ONTOLOGY_FILE}"


def test_constraint_count() -> None:
    text = CONSTRAINTS_FILE.read_text(encoding="utf-8")
    found = len(re.findall(r"CREATE CONSTRAINT", text))
    assert found == EXPECTED_CONSTRAINTS, (
        f"Expected {EXPECTED_CONSTRAINTS} constraints, found {found}. "
        "Update EXPECTED_CONSTRAINTS if you intentionally added or removed constraints."
    )


def test_constraints_are_idempotent() -> None:
    text = CONSTRAINTS_FILE.read_text(encoding="utf-8")
    non_idempotent = [
        line.strip()
        for line in text.splitlines()
        if "CREATE CONSTRAINT" in line and "IF NOT EXISTS" not in line
    ]
    assert not non_idempotent, (
        f"Constraints missing IF NOT EXISTS (not idempotent):\n"
        + "\n".join(non_idempotent)
    )


def test_ontology_labels_present() -> None:
    text = ONTOLOGY_FILE.read_text(encoding="utf-8")
    for label in EXPECTED_ONTOLOGY_LABELS:
        assert label in text, f"Expected label :{label} not found in ontology.cypher"


def test_ontology_merges_are_idempotent() -> None:
    text = ONTOLOGY_FILE.read_text(encoding="utf-8")
    # Every node-creation statement should be MERGE, not CREATE.
    bare_creates = re.findall(r"\bCREATE\s+\(", text)
    assert not bare_creates, (
        f"Found {len(bare_creates)} bare CREATE node statement(s) in ontology.cypher; "
        "use MERGE for idempotency."
    )
