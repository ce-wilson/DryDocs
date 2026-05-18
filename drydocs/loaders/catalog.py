"""Catalog loaders — CatalogLOB, ProductLine, Product, DevTeam.

Each is a thin BaseLoader subclass pointing at its Cypher template and
row model. The Oracle SQL queries that feed them in production live in
``drydocs/queries/catalog/*.sql`` (one per loader) — confirm exact table
and column names with the catalog DBA, then update the SQL only. Row
models and Cypher don't change.
"""
from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from ..models import CatalogLOBRow, DevTeamRow, ProductLineRow, ProductRow
from .base import BaseLoader

_CYPHER = Path(__file__).resolve().parent / "cypher"


class CatalogLOBsLoader(BaseLoader):
    name: ClassVar[str] = "catalog_lobs.v1"
    cypher_path: ClassVar[Path | None] = _CYPHER / "catalog_lobs.cypher"
    row_model: ClassVar[type] = CatalogLOBRow
    source_label: ClassVar[str] = "oracle"


class ProductLinesLoader(BaseLoader):
    name: ClassVar[str] = "product_lines.v1"
    cypher_path: ClassVar[Path | None] = _CYPHER / "product_lines.cypher"
    row_model: ClassVar[type] = ProductLineRow
    source_label: ClassVar[str] = "oracle"


class ProductsLoader(BaseLoader):
    name: ClassVar[str] = "products.v1"
    cypher_path: ClassVar[Path | None] = _CYPHER / "products.cypher"
    row_model: ClassVar[type] = ProductRow
    source_label: ClassVar[str] = "oracle"


class DevTeamsLoader(BaseLoader):
    name: ClassVar[str] = "dev_teams.v1"
    cypher_path: ClassVar[Path | None] = _CYPHER / "dev_teams.cypher"
    row_model: ClassVar[type] = DevTeamRow
    source_label: ClassVar[str] = "oracle"
