"""SoftwareRegistryLoader — loads the third-party software registry.

Source of truth: ``config/taxonomy/software-registry.yaml`` (the ledger,
plan 07 / ADR 0004). The RegistryYamlAdapter flattens the nested
vendors/products document into one row per product with the vendor fields
denormalized, so the standard BaseLoader lifecycle (JobRun, validation,
UNWIND batch) applies unchanged.

Writes :Vendor (org:Organization), :SoftwareProduct (dd:SoftwareProduct),
MADE_BY (prov:wasAttributedTo), and — for rows where ``used_by_drydocs`` is
true — a USES_SOFTWARE edge from the reserved DryDocs :BusinessApplication node
(``drydocs_application_id``; company side reconciles it to the real SEAL id).
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import yaml

from drydocs_core.models.registry import SoftwareProductRow
from drydocs_core.repo_paths import repo_root

from .app_identity import PreCutoverApplicationGuard
from .base import BaseLoader

if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

# PACKAGE-INTERNAL: the .cypher files are package data and travel with it.
CYPHER_DIR = Path(__file__).resolve().parent / "cypher"
_REPO_ROOT = repo_root(Path(__file__).resolve().parents[2])
DEFAULT_REGISTRY_PATH = _REPO_ROOT / "config" / "taxonomy" / "software-registry.yaml"


class RegistryYamlAdapter:
    """Adapter over the registry YAML: yields one flat dict per product.

    Vendor fields are denormalized onto each product row; ``used_by_drydocs``
    is converted to ``used_by_app_id`` (the reserved DryDocs Application id,
    or None) so the Cypher can gate the USES_SOFTWARE MERGE on it.
    """

    def __init__(self, path: Path | str = DEFAULT_REGISTRY_PATH) -> None:
        self.path = Path(path)

    def __enter__(self) -> RegistryYamlAdapter:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    def rows(self) -> Iterator[dict]:
        doc = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        app_id = doc.get("drydocs_application_id")
        vendors = {v["id"]: v for v in doc.get("vendors", [])}
        for product in doc.get("products", []):
            vendor = vendors.get(product.get("vendor"), {})
            versions = product.get("versions") or []
            yield {
                "product_id": product.get("id"),
                "name": product.get("name"),
                "category": product.get("category"),
                "role": product.get("role"),
                "type": product.get("type"),
                "versions": versions,
                "primary_version": versions[0] if versions else None,
                "vendor_id": vendor.get("id"),
                "vendor_name": vendor.get("name"),
                "publisher_url": vendor.get("publisher_url", ""),
                "used_by_app_id": app_id if product.get("used_by_drydocs") else None,
            }


class SoftwareRegistryLoader(PreCutoverApplicationGuard, BaseLoader):
    name: ClassVar[str] = "software_registry.v1"
    source_id: ClassVar[str | None] = "repo:software-registry"
    cypher_path: ClassVar[Path] = CYPHER_DIR / "software_registry.cypher"
    row_model: ClassVar[type] = SoftwareProductRow
    source_label: ClassVar[str] = "registry"
