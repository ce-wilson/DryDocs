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
        assert (
            product["vendor"] in vendor_ids
        ), f"product '{product['id']}' references unknown vendor '{product['vendor']}'"


def test_product_required_fields_and_enums() -> None:
    for product in _doc()["products"]:
        for field in ("id", "vendor", "name", "category", "role", "type"):
            assert product.get(field), f"product '{product.get('id')}' missing '{field}'"
        assert product["role"] in ALLOWED_ROLES, f"'{product['id']}': bad role"
        assert product["type"] in ALLOWED_TYPES, f"'{product['id']}': bad type"
        assert isinstance(product.get("versions", []), list)


# Vendors with no public publisher page. An internally-built product has no
# vendor site, and pointing the field at a company URL would put an internal
# host into an Internal-Public file — so the field is omitted rather than
# filled with a placeholder that a later reader cannot tell from a stale link
# (C25, 2026-08-09). Kept as an explicit allow-list so a THIRD-PARTY vendor
# can never lose its URL by accident: adding an id here is a deliberate act.
VENDORS_WITHOUT_PUBLISHER = {"in-house"}


def test_third_party_vendors_carry_publisher_url() -> None:
    """publisher_url is REQUIRED of third-party vendors and OPTIONAL of the rest.

    The exemption means "not required", NOT "forbidden" — and the difference is
    load-bearing across the port. The producer's `in-house` row omits the field
    because a company URL in an Internal-Public file would cross the publish
    boundary; the CONSUMER has no such constraint and can legitimately carry the
    real internal URL in its own tree. A first draft of this guard asserted the
    field was absent, which would have failed the consumer's suite for doing the
    correct thing — the Idea-100 class exactly: a producer-only precondition
    written as a universal invariant.
    """
    for vendor in _doc()["vendors"]:
        url = vendor.get("publisher_url")
        if vendor["id"] in VENDORS_WITHOUT_PUBLISHER:
            # May be absent. If present it must still be a real URL, so the
            # exemption cannot be used to smuggle in a placeholder.
            assert url is None or str(url).startswith("http"), (
                f"vendor '{vendor['id']}' is exempt from REQUIRING a publisher_url, but the "
                f"value it carries is not a URL: {url!r}. Omit the field or give it a real "
                f"address — the exemption is not a licence for a placeholder."
            )
            continue
        assert str(url or "").startswith(
            "http"
        ), f"vendor '{vendor['id']}' missing publisher_url"


def test_products_of_url_less_vendors_are_internal() -> None:
    """The allow-list is not a general escape hatch.

    A vendor may skip the publisher URL only because it ships nothing publicly,
    which is the same fact as its products being `type: internal`. If a
    commercial product ever pointed at an in-house vendor, the exemption would
    be laundering a missing URL rather than recording an absent one.
    """
    doc = _doc()
    for product in doc["products"]:
        if product["vendor"] in VENDORS_WITHOUT_PUBLISHER:
            assert product["type"] == "internal", (
                f"product '{product['id']}' claims vendor '{product['vendor']}', which is "
                f"exempt from publisher_url because it publishes nothing — but the product "
                f"is type '{product['type']}', not 'internal'"
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
        assert isinstance(
            doc.get("current_for", []), list
        ), f"product '{pid}' documentation.current_for must be a list"


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
                drifted.append(
                    f"{product['id']}: runtime {version} not covered by docs {doc['docs_version']}"
                )

    # The known state, pinned so a silent change is loud. Update this list when
    # an SME confirms a capture against a runtime version (or recaptures).
    assert drifted == [
        "controlm: runtime 9.0.21.300 not covered by docs 9.0.20",
    ], f"documentation currency changed: {drifted}"


ACCESS_STATES = {"open", "forbidden"}
ENUMERABLE_STATES = {True, False, "unknown"}


def test_available_documentation_versions_are_well_formed() -> None:
    """The pre-populated version list must stay usable as a lookup table."""
    for product in _doc()["products"]:
        doc = product.get("documentation") or {}
        available = doc.get("available_versions")
        if available is None:
            continue
        pid = product["id"]
        seen: set[str] = set()
        for row in available:
            ver = row.get("version")
            assert ver, f"'{pid}' available_versions row missing version: {row}"
            assert ver not in seen, f"'{pid}' duplicate documentation version '{ver}'"
            seen.add(ver)
            assert row.get("path"), f"'{pid}' version '{ver}' missing path"
            assert (
                row.get("access") in ACCESS_STATES
            ), f"'{pid}' version '{ver}' access '{row.get('access')}' not in {ACCESS_STATES}"
            assert (
                row.get("enumerable") in ENUMERABLE_STATES
            ), f"'{pid}' version '{ver}' enumerable '{row.get('enumerable')}' not in {ENUMERABLE_STATES}"
            # A forbidden tree cannot have been probed for a toc.json, so
            # claiming to know is a transcription error.
            if row["access"] == "forbidden":
                assert row["enumerable"] == "unknown", (
                    f"'{pid}' version '{ver}' is forbidden but claims enumerable="
                    f"{row['enumerable']} — unprobeable, so this cannot be known"
                )


def test_captured_docs_version_is_one_of_the_available_versions() -> None:
    """docs_version must name a real published version, and one we can reach."""
    for product in _doc()["products"]:
        doc = product.get("documentation") or {}
        available = doc.get("available_versions")
        if not available:
            continue
        by_version = {r["version"]: r for r in available}
        captured = doc["docs_version"]
        assert captured in by_version, (
            f"'{product['id']}' docs_version '{captured}' is not in available_versions "
            f"{sorted(by_version)}"
        )
        assert by_version[captured]["access"] == "open", (
            f"'{product['id']}' claims a capture from '{captured}', which is not "
            f"reachable — a capture cannot have come from a forbidden tree"
        )


def test_estate_runtime_documentation_reachability_is_recorded() -> None:
    """Pin the finding that motivated the list.

    Docs for the exact runtime exist but are not retrievable, so "recapture at
    the right version" is not currently available. If this ever changes, this
    test fails and the recapture becomes a real option worth taking.
    """
    controlm = next(p for p in _doc()["products"] if p["id"] == "controlm")
    by_version = {r["version"]: r for r in controlm["documentation"]["available_versions"]}
    for runtime in controlm["versions"]:
        assert runtime in by_version, f"runtime {runtime} absent from available_versions"
        assert by_version[runtime]["access"] == "forbidden", (
            f"runtime {runtime} documentation is now reachable — recapture is "
            f"newly possible; update this pin and consider recapturing"
        )


# --------------------------------------------------------------------------- #
# stack membership: "what is DryDocs built on" as a query, not a comment
# --------------------------------------------------------------------------- #
ALLOWED_STACKS = {"backend", "web-console", "source"}


def test_stack_membership_is_declared_for_everything_we_build_on() -> None:
    """`used_by_drydocs` says THAT we use it; `stack` says WHERE.

    Without the second field "what is our UI stack?" is answerable only by
    reading comments or package.json — which is how the ReUI/Neo4j-driver
    membership got missed in the first place.
    """
    failures: list[str] = []
    for product in _doc()["products"]:
        pid, stack = product["id"], product.get("stack")
        if not product.get("used_by_drydocs"):
            assert stack is None, f"'{pid}': stack is only meaningful when used_by_drydocs"
            continue
        if not stack:
            failures.append(f"'{pid}' is used_by_drydocs but declares no stack")
            continue
        bad = set(stack) - ALLOWED_STACKS
        if bad:
            failures.append(f"'{pid}' has unknown stack(s) {sorted(bad)}")
    assert not failures, "\n".join(failures)


def test_neo4j_spans_both_stacks() -> None:
    """One product, two stacks — the case that motivated the field.

    The database is backend; the SAME product's JS driver (neo4j-driver in
    web/package.json) also ships in the console for the ADR 0005 dev-mode bolt
    adapter. Registering the driver separately would collide with this file's
    "drivers stay out" scope rule, so membership is modelled on the product.
    """
    neo4j = next(p for p in _doc()["products"] if p["id"] == "neo4j")
    assert set(neo4j["stack"]) == {"backend", "web-console"}


def test_web_console_stack_matches_the_locked_site_plan() -> None:
    """The locked stack (UI-WIP/site-plan.md §1), pinned so a swap is deliberate."""
    web = {p["id"] for p in _doc()["products"] if "web-console" in (p.get("stack") or [])}
    assert web == {"react", "reui", "react-flow", "tailwindcss", "neo4j"}
