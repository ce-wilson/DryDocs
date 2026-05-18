"""Oracle catalog row models — restored from the M1 pack.

These models target the canonical product catalog hierarchy:

    BusinessSegment -> CatalogLOB -> ProductLine -> Product -> Application
                                                              -> DevTeam

Each loader runs an Oracle SQL query that projects to the columns named
below. When the team confirms exact catalog table names + column names
in their psgmgr (or other) schema, only the SQL SELECT in each loader
needs to change — the model field names stay constant.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .base import BaseLoader

_CYPHER = Path(__file__).resolve().parent / "cypher"


def _date_or_none(v: Any) -> date | None:
    if v in (None, ""):
        return None
    if isinstance(v, date):
        return v
    return date.fromisoformat(str(v).strip()[:10])


class BusinessSegmentRow(BaseModel):
    """Business segment from the annual report (manual seed; M0 already
    seeded the four current segments). This model is for the rare case of
    a re-org refresh that bumps effective dates."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True, extra="ignore")

    code: str = Field(..., min_length=1)  # 'CCB' | 'CIB' | 'AWM' | 'Corp'
    name: str = Field(..., min_length=1)
    effective_from: date | None = None
    effective_to: date | None = None
    retired: bool = False

    @field_validator("effective_from", "effective_to", mode="before")
    @classmethod
    def _coerce_date(cls, v: Any) -> Any:
        return _date_or_none(v)


class CatalogLOBRow(BaseModel):
    """Internal product-catalog Line of Business (different list from the
    corporate BusinessSegments — see v3 §B). Reconciliation to a
    BusinessSegment is via a separate :RECONCILES_TO edge that the
    loader records when ``reconciles_to_segment`` is populated.
    """

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True, extra="ignore")

    lob_id: str = Field(..., min_length=1)
    code: str | None = None  # e.g. 'AWMCIB', 'CCB', 'CT', 'HR', 'ET'
    name: str | None = None
    reconciles_to_segment: str | None = Field(
        None,
        description="BusinessSegment.code for the reconciliation edge.",
    )
    reconcile_confidence: float | None = Field(None, ge=0.0, le=1.0)


class ProductLineRow(BaseModel):
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True, extra="ignore")

    product_line_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    parent_lob_id: str = Field(..., min_length=1)


class ProductRow(BaseModel):
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True, extra="ignore")

    product_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    parent_product_line_id: str = Field(..., min_length=1)


class DevTeamRow(BaseModel):
    """Catalog DevTeam — does NOT include the dev_team -> seal_id mapping
    (that's the M2 PAT product-mapping CSV). This model is the team
    metadata only: id, name, jira_board_id."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True, extra="ignore")

    team_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    jira_board_id: str | None = None
    parent_product_id: str | None = Field(
        None,
        description=(
            "Optional. Catalog may anchor dev teams under a Product; if so, "
            "loader writes :Product->:HAS_DEV_TEAM->:DevTeam."
        ),
    )


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
