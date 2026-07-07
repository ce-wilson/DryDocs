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
CONSTRAINTS_FILE = REPO / "drydocs" / "schema" / "constraints.cypher"
SUPPLEMENT_FILE = REPO / "drydocs" / "schema" / "registry_ontology_supplement.cypher"

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
    from drydocs.models.registry import SoftwareProductRow

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
