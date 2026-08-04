"""Static checks on the Cypher schema files (no Neo4j connection required)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from drydocs_core import yaml_fragments
from drydocs_core.cypher_split import strip_comments

try:
    import yaml  # noqa: F401  (availability probe; loader does the parsing)

    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "drydocs_core" / "schema"
ONTOLOGY_DIR = Path(__file__).resolve().parents[2] / "drydocs_core" / "ontology"
CONSTRAINTS_FILE = SCHEMA_DIR / "constraints.cypher"
ONTOLOGY_FILE = SCHEMA_DIR / "ontology.cypher"
VOCAB_FILE = ONTOLOGY_DIR / "relationship_vocabulary"

# 35 after schema consolidation: m3_constraints_upgrade.cypher absorbed into
# constraints.cypher + the PAT area_product_id constraint. 37 after the
# software registry (plan 07 / ADR 0004): vendor_id + softwareproduct_id.
# 38 after controlmapplication_name (folder-pass grouping label; gate
# controlm-q1q3-phase1, load-order definition 2026-07-07).
# 40 after document_id + chunk_id (bmc-docs lexical graph, gate
# bmc-docs-lexical-load 2026-07-08). 46 after the six L7 doc-traceability
# NODE KEYs (DesignDoc/DocSection/Requirement/Component/TestCase/FeedbackNote,
# gate doc-traceability-feedback 2026-07-20 — source-namespaced keys, gate A2).
# 47 after scheduler_kind removed (2026-07-23, C13 leftover sweep — pre-C13
# graphs are wiped and rebuilt from bootstrap, the kept-for-old-graphs
# rationale no longer applies).
# 49 after the P3 host topology (gate controlm-hosts-topology 2026-07-09):
# controlmhostgroup_key (data_center, name) NODE KEY + executionhost_nodeid.
# 51 after the G33 self-documentation code graph (gate
# self-documentation-code-graph 2026-07-27): project_id + codemodule_file_id.
# 52 after the BusinessApplication identity cutover (S3; gate
# business-application-identity 2026-07-27): +businessapplication_app_id, and
# port_unique -> port_app_key (a DROP + a rename, so the CREATE count is
# unchanged by that half — see the trap comment in constraints.cypher).
# Bump this when you intentionally add/remove a CREATE CONSTRAINT.
EXPECTED_CONSTRAINTS = 52

# SchedulerKind removed 2026-07-21 (C12 platforms-taxonomy gate): its seeds are
# retired (commented, audit-kept) in ontology.cypher — no longer a seeded label.
EXPECTED_ONTOLOGY_LABELS = [
    "DprodClass",
    "DcatClass",
    "ProvClass",
    "DqvClass",
    "OrgClass",
    "SwoClass",
    "OlClass",
    "Role",
    "BusinessSegment",
    "Dimension",
    "Metric",
]


def test_schema_files_exist() -> None:
    assert CONSTRAINTS_FILE.exists(), f"Missing: {CONSTRAINTS_FILE}"
    assert ONTOLOGY_FILE.exists(), f"Missing: {ONTOLOGY_FILE}"


# A DECLARATION only — anchored at line start, so a `//` comment that quotes the
# DDL is prose, not a constraint. Both checks below read the file as text, and
# constraints.cypher documents its own traps in comments (the port_app_key rename
# has to spell out why re-declaring under the same name is a silent no-op). Without
# the anchor those comments inflate the count and false-fail the idempotence check.
# This mirrors drydocs_core/schema/constraints.py's `_DECLARATION_RE`, which the
# bootstrap presence guard already keys on — one reading of "a declaration", not two.
_DECLARATION_LINE = re.compile(r"^\s*CREATE CONSTRAINT\b")


def test_constraint_count() -> None:
    text = CONSTRAINTS_FILE.read_text(encoding="utf-8")
    found = sum(1 for line in text.splitlines() if _DECLARATION_LINE.match(line))
    assert found == EXPECTED_CONSTRAINTS, (
        f"Expected {EXPECTED_CONSTRAINTS} constraints, found {found}. "
        "Update EXPECTED_CONSTRAINTS if you intentionally added or removed constraints."
    )


def test_constraints_are_idempotent() -> None:
    text = CONSTRAINTS_FILE.read_text(encoding="utf-8")
    non_idempotent = [
        line.strip()
        for line in text.splitlines()
        if _DECLARATION_LINE.match(line) and "IF NOT EXISTS" not in line
    ]
    assert not non_idempotent, "Constraints missing IF NOT EXISTS (not idempotent):\n" + "\n".join(
        non_idempotent
    )


def test_ontology_labels_present() -> None:
    # Comment-stripped (J26): a label named only in a comment is not a label the
    # schema declares — the pin is on CODE, so a comment cannot false-pass it.
    text = strip_comments(ONTOLOGY_FILE.read_text(encoding="utf-8"))
    for label in EXPECTED_ONTOLOGY_LABELS:
        assert label in text, f"Expected label :{label} not found in ontology.cypher"


def test_ontology_merges_are_idempotent() -> None:
    # Comment-stripped (J26): a comment DESCRIBING the bare-CREATE trap must not
    # trip the ban — the file has to be able to explain its own rule.
    text = strip_comments(ONTOLOGY_FILE.read_text(encoding="utf-8"))
    # Every node-creation statement should be MERGE, not CREATE.
    bare_creates = re.findall(r"\bCREATE\s+\(", text)
    assert not bare_creates, (
        f"Found {len(bare_creates)} bare CREATE node statement(s) in ontology.cypher; "
        "use MERGE for idempotency."
    )


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML not installed")
def test_vocabulary_file_exists() -> None:
    assert VOCAB_FILE.exists(), (
        f"relationship_vocabulary.yaml not found at {VOCAB_FILE}. "
        "Run: create drydocs_core/ontology/relationship_vocabulary.yaml"
    )


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML not installed")
def test_vocabulary_active_entries_declared_in_supplements() -> None:
    """Every active local_relationship must have its neo4j_label present in
    its declared supplement file. Catches drift between the registry and the
    schema — if you add a vocabulary entry but forget the supplement block,
    this test fails before CI merges it.
    """
    if not VOCAB_FILE.exists():
        pytest.skip("relationship_vocabulary.yaml not present")

    vocab = yaml_fragments.load_yaml_source(VOCAB_FILE)
    failures: list[str] = []

    for rel in vocab.get("local_relationships", []):
        if rel.get("status") != "active":
            continue
        supplement = rel.get("supplement")
        if not supplement or supplement in (None, "~", "null"):
            continue  # cross-domain provenance — no supplement required

        supplement_path = SCHEMA_DIR / supplement
        if not supplement_path.exists():
            failures.append(f"[{rel['id']}] supplement '{supplement}' declared but file not found")
            continue

        # Comment-stripped (J26; the G29 lesson) — a commented-out MERGE must not
        # satisfy a declaration check, same reading supplements.declared_terms uses.
        text = strip_comments(supplement_path.read_text(encoding="utf-8"))
        label = rel["neo4j_label"]
        if label not in text:
            failures.append(f"[{rel['id']}] label '{label}' not found in {supplement}")

    assert not failures, f"{len(failures)} vocabulary drift error(s):\n" + "\n".join(failures)


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML not installed")
def test_vocabulary_prov_matrix_complete() -> None:
    """The prov_matrix section must contain all 9 expected rows."""
    if not VOCAB_FILE.exists():
        pytest.skip("relationship_vocabulary.yaml not present")

    vocab = yaml_fragments.load_yaml_source(VOCAB_FILE)
    matrix = vocab.get("prov_matrix", [])
    labels = {row["neo4j_label"] for row in matrix}
    expected = {
        "WAS_INFORMED_BY",
        "USED",
        "GENERATED",
        "WAS_ASSOCIATED_WITH",
        "WAS_GENERATED_BY",
        "WAS_DERIVED_FROM",
        "WAS_ATTRIBUTED_TO",
        "ACTED_ON_BEHALF_OF",
        "HAD_MEMBER",
    }
    missing = expected - labels
    assert not missing, f"prov_matrix is missing rows for: {missing}"


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML not installed")
def test_vocabulary_no_duplicate_ids() -> None:
    if not VOCAB_FILE.exists():
        pytest.skip("relationship_vocabulary.yaml not present")

    vocab = yaml_fragments.load_yaml_source(VOCAB_FILE)
    ids = [r["id"] for r in vocab.get("local_relationships", [])]
    dupes = {i for i in ids if ids.count(i) > 1}
    assert not dupes, f"Duplicate relationship ids in vocabulary: {dupes}"


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML not installed")
def test_vocabulary_every_entry_has_inverse_label() -> None:
    """C15: every entry carries a non-empty inverse_label — the target-side
    display phrasing (SUPPORTS -> "supported by"). PRESENTATIONAL ONLY: it
    changes no direction, type, status, or semantics (storage stays one
    directed edge), so its presence is a schema rule, not a gate matter."""
    if not VOCAB_FILE.exists():
        pytest.skip("relationship_vocabulary.yaml not present")

    vocab = yaml_fragments.load_yaml_source(VOCAB_FILE)
    missing = [
        r["id"]
        for r in vocab.get("local_relationships", [])
        if not (isinstance(r.get("inverse_label"), str) and r["inverse_label"].strip())
    ]
    assert not missing, f"Entries without inverse_label: {missing}"
