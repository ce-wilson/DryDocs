"""Oracle/CSV catalog row models — restored from the M1 pack, extended for PAT.

These models target the canonical product catalog hierarchy:

    BusinessSegment -> CatalogLOB -> ProductLine -> Product -> Application
                                                            -> AreaProduct -> DevTeam
                                                            -> DevTeam (home team)

Each loader runs an Oracle SQL query (or reads a CSV via CsvAdapter) that
projects to the columns named below. When the team confirms exact catalog
table names + column names, only the SQL SELECT in each loader needs to
change — the model field names stay constant.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class AreaProductRow(BaseModel):
    """Area Product Group (Team of Teams) — intermediate between Product and
    DevTeam in the PAT/Align hierarchy.  One Product may contain multiple
    Area Product Groups; each groups several DevTeams."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True, extra="ignore")

    area_product_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    parent_product_id: str = Field(..., min_length=1)


_VALID_TEAM_TYPES = {"aligned", "flex", "dedicated"}


class PatProductMappingRow(BaseModel):
    """PAT product mapping — links a DevTeam to its home Product and optional
    AreaProduct, lists the SEAL application IDs the team owns, records the
    team type (aligned/flex/dedicated) and whether the team is sponsored."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True, extra="ignore")

    team_id: str = Field(..., min_length=1)
    product_id: str = Field(..., min_length=1, description="Home product ID.")
    area_product_id: Optional[str] = Field(None, description="Optional intermediate AreaProduct.")
    seal_ids: Optional[str] = Field(
        None,
        description="Comma-separated SEAL application IDs owned by this team.",
    )
    team_type: str = Field(
        ...,
        description="aligned | flex | dedicated — governs work prioritization.",
    )
    sponsored: bool = Field(
        False,
        description="True when this team is sponsored to support a product outside its home.",
    )
    sponsored_product_id: Optional[str] = Field(
        None,
        description="Product or AreaProduct ID the team is sponsored to support.",
    )

    @field_validator("team_type", mode="before")
    @classmethod
    def _check_team_type(cls, v: Any) -> str:
        v = str(v).strip().lower()
        if v not in _VALID_TEAM_TYPES:
            raise ValueError(f"team_type must be one of {_VALID_TEAM_TYPES}; got {v!r}")
        return v


class PatTeamRoleRow(BaseModel):
    """PAT team role assignment — links an Employee to a DevTeam via a named
    Role (Tech Partner, Software Engineering Manager, etc.).  Follows the
    same org:Membership n-ary pattern used by SEAL application roles."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True, extra="ignore")

    team_id: str = Field(..., min_length=1)
    employee_sid: str = Field(..., min_length=1, description="Employee SID / employee_id.")
    role_id: str = Field(..., min_length=1, description="Role.role_id from the canonical role vocabulary.")
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
