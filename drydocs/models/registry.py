"""Row model for the third-party software registry (plan 07 / ADR 0004).

One row per SoftwareProduct, with its Vendor fields denormalized by the
RegistryYamlAdapter (the registry YAML is nested vendors/products; the
loader Cypher wants flat rows). ``used_by_app_id`` is the reserved DryDocs
Application id when the product is part of DryDocs' own stack, else None —
the Cypher writes a USES_SOFTWARE edge only when it is set.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class SoftwareProductRow(BaseModel):
    product_id: str
    name: str
    category: str
    role: Literal["orchestrator", "data-platform", "graph-platform", "tool"]
    type: Literal["commercial", "open-source", "internal", "hybrid"]
    versions: list[str] = []
    primary_version: str | None = None
    vendor_id: str
    vendor_name: str
    publisher_url: str = ""
    used_by_app_id: str | None = None
