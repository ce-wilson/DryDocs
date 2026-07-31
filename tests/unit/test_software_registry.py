"""Guards for the third-party software registry (plan 07 / ADR 0004).

The registry YAML is the ledger and the graph is the lookup — these tests
keep the ledger well-formed (schema, unique ids, resolvable vendor refs,
gated enums) and keep the loader wiring honest (adapter flattening, row
validation, cypher/constraints/supplement declarations) without needing a
Neo4j connection.
"""
from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml", reason="PyYAML not installed")

REPO = Path(__file__).resolve().parents[2]
REGISTRY_FILE = REPO / "config" / "taxonomy" / "software-registry.yaml"
CYPHER_FILE = REPO / "drydocs" / "loaders" / "cypher" / "software_registry.cypher"
CONSTRAINTS_FILE = REPO / "drydocs_core" / "schema" / "constraints.cypher"
SUPPLEMENT_FILE = REPO / "drydocs_core" / "schema" / "registry_ontology_supplement.cypher"

# ADR 0004: role absorbs the Tier-1/Tier-2 split; type mirrors the company
# catalog's Software Type axis.
ALLOWED_ROLES = {"orchestrator", "data-platform", "graph-platform", "tool"}
ALLOWED_TYPES = {"commercial", "open-source", "internal", "hybrid"}


def _doc() -> dict:
    return yaml.safe_load(REGISTRY_FILE.read_text(encoding="utf-8"))


def test_registry_schema_and_classification() -> None:
    doc = _doc()
    assert doc["schema"] == "drydocs.software-registry.v1"
    assert doc["classification"] == "Internal-Public"
    assert doc["drydocs_application_id"], "reserved DryDocs Application id required"


def test_ids_unique_and_vendor_refs_resolve() -> None:
    doc = _doc()
    vendor_ids = [v["id"] for v in doc["vendors"]]
    assert len(vendor_ids) == len(set(vendor_ids)), "duplicate vendor id"
    product_ids = [p["id"] for p in doc["products"]]
    assert len(product_ids) == len(set(product_ids)), "duplicate product id"
    for product in doc["products"]:
        assert product["vendor"] in vendor_ids, (
            f"product '{product['id']}' references unknown vendor '{product['vendor']}'"
        )


def test_product_required_fields_and_enums() -> None:
    for product in _doc()["products"]:
        for field in ("id", "vendor", "name", "category", "role", "type"):
            assert product.get(field), f"product '{product.get('id')}' missing '{field}'"
        assert product["role"] in ALLOWED_ROLES, f"'{product['id']}': bad role"
        assert product["type"] in ALLOWED_TYPES, f"'{product['id']}': bad type"
        assert isinstance(product.get("versions", []), list)


def test_vendors_carry_publisher_url() -> None:
    for vendor in _doc()["vendors"]:
        assert str(vendor.get("publisher_url", "")).startswith("http"), (
            f"vendor '{vendor['id']}' missing publisher_url"
        )


def test_adapter_flattens_and_rows_validate() -> None:
    from drydocs.loaders.software_registry import RegistryYamlAdapter
    from drydocs_core.models.registry import SoftwareProductRow

    doc = _doc()
    with RegistryYamlAdapter(REGISTRY_FILE) as adapter:
        rows = list(adapter.rows())

    assert len(rows) == len(doc["products"])
    for raw in rows:
        row = SoftwareProductRow.model_validate(raw)
        assert row.vendor_id and row.vendor_name

    used = [r for r in rows if r["used_by_app_id"]]
    assert used, "expected at least one used_by_drydocs product (DryDocs' own stack)"
    assert all(
        r["used_by_app_id"] == doc["drydocs_application_id"] for r in used
    ), "used_by_app_id must be the reserved DryDocs Application id"


def test_loader_class_wiring() -> None:
    from drydocs.loaders.software_registry import SoftwareRegistryLoader

    assert SoftwareRegistryLoader.cypher_path == CYPHER_FILE
    assert SoftwareRegistryLoader.cypher_path.exists()
    assert SoftwareRegistryLoader.row_model is not None
    assert SoftwareRegistryLoader.source_label == "registry"


def test_cypher_constraints_and_supplement_declare_the_gated_labels() -> None:
    cypher = CYPHER_FILE.read_text(encoding="utf-8")
    for token in (":Vendor", ":SoftwareProduct", "MADE_BY", "USES_SOFTWARE"):
        assert token in cypher, f"loader cypher missing {token}"

    constraints = CONSTRAINTS_FILE.read_text(encoding="utf-8")
    assert "vendor_id" in constraints
    assert "softwareproduct_id" in constraints

    supplement = SUPPLEMENT_FILE.read_text(encoding="utf-8")
    for token in ("Vendor", "SoftwareProduct", "MADE_BY", "USES_SOFTWARE", "wasAttributedTo"):
        assert token in supplement, f"supplement missing {token}"


# --------------------------------------------------------------------------- #
# documentation pointer: which vendor docs describe this product, and are they
# still current for the version we actually run (user requirement 2026-07-31)
# --------------------------------------------------------------------------- #
DOC_REGISTRY_FILE = REPO / "config" / "doc-source-registry.yaml"


def _doc_corpus_ids() -> set[str]:
    reg = yaml.safe_load(DOC_REGISTRY_FILE.read_text(encoding="utf-8"))
    return {s["id"] for s in reg.get("sources", [])}


def test_documentation_pointer_is_well_formed_and_resolves() -> None:
    """A pointer to a corpus that does not exist is worse than no pointer."""
    corpus_ids = _doc_corpus_ids()
    for product in _doc()["products"]:
        doc = product.get("documentation")
        if doc is None:
            continue
        pid = product["id"]
        assert doc.get("corpus") in corpus_ids, (
            f"product '{pid}' documentation.corpus '{doc.get('corpus')}' is not a "
            f"doc-source-registry id: {sorted(corpus_ids)}"
        )
        assert doc.get("docs_version"), f"product '{pid}' documentation missing docs_version"
        assert isinstance(doc.get("current_for", []), list), (
            f"product '{pid}' documentation.current_for must be a list"
        )


def test_documentation_currency_drift_is_visible_not_hidden() -> None:
    """Every RUNTIME version must be declared `current_for`, or reported as drift.

    This is the mechanism behind the requirement: when the estate moves to a new
    version it lands in `versions:` and is absent from `current_for`, so the gap
    is computable. The test does not FAIL on drift — drift is a true statement
    about the world today (9.0.20 docs, 9.0.21.300 runtime), not a code defect.
    What it enforces is that the drift can be COMPUTED at all: both sides
    present and typed, so a report can never silently find nothing.
    """
    drifted: list[str] = []
    for product in _doc()["products"]:
        doc = product.get("documentation")
        if doc is None:
            continue
        current_for = set(doc.get("current_for") or [])
        for version in product.get("versions", []) or []:
            if version not in current_for:
                drifted.append(f"{product['id']}: runtime {version} not covered by docs {doc['docs_version']}")

    # The known state, pinned so a silent change is loud. Update this list when
    # an SME confirms a capture against a runtime version (or recaptures).
    assert drifted == [
        "controlm: runtime 9.0.21.300 not covered by docs 9.0.20",
    ], f"documentation currency changed: {drifted}"
