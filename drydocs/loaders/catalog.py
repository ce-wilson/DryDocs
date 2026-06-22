"""Catalog loaders — product hierarchy, PAT team mapping, and area products.

Target hierarchy:

    BusinessSegment -> CatalogLOB -> ProductLine -> Product -> Application
                                                            -> AreaProduct -> DevTeam
                                                            -> DevTeam (home team)

Row models are defined here alongside their loaders. When the team confirms
exact catalog table names + column names, only the SQL SELECT in each loader
needs to change — the model field names stay constant.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, ClassVar, Iterable, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .base import BaseLoader
from ..precedence import Claim, PrecedenceResolver

_CYPHER = Path(__file__).resolve().parent / "cypher"

# The product catalog feed speaks for the org-taxonomy authority (precedence.yaml#order
# id 'lob-product-team'). When a more-authoritative reconciliation override exists
# (e.g. an internal-standards crosswalk), pass it through `extra_reconcile_claims`
# below — the precedence.yaml order, not this code, decides which one wins.
_CATALOG_AUTHORITY = "lob-product-team"


def resolve_lob_reconciliation(
    model: "CatalogLOBRow",
    resolver: PrecedenceResolver,
    extra_claims: Iterable[Claim] = (),
) -> dict[str, Any]:
    """Resolve a CatalogLOB's :RECONCILES_TO target through the precedence chain.

    Returns the params the catalog_lobs.cypher RECONCILES_TO block consumes:
    the winning segment + confidence, the winning authority, and any losing
    claims recorded as aliases (skos:closeMatch — never dropped).
    """
    claims = [
        Claim(
            authority=_CATALOG_AUTHORITY,
            value=model.reconciles_to_segment,
            confidence=model.reconcile_confidence,
        ),
        *extra_claims,
    ]
    res = resolver.resolve(claims)
    return {
        "reconciles_to_segment": res.value,
        "reconcile_confidence": res.confidence,
        "reconcile_authority": res.authority,
        "reconcile_aliases": res.alias_strings(),
    }


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
    DevTeam in the PAT/Align hierarchy."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True, extra="ignore")

    area_product_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    parent_product_id: str = Field(..., min_length=1)


_VALID_TEAM_TYPES = {"aligned", "flex", "dedicated"}


class PatProductMappingRow(BaseModel):
    """PAT product mapping — links DevTeam to home Product, optional AreaProduct,
    and SEAL applications. Records team type and sponsored status."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True, extra="ignore")

    team_id: str = Field(..., min_length=1)
    product_id: str = Field(..., min_length=1)
    area_product_id: Optional[str] = None
    seal_ids: Optional[str] = Field(None, description="Comma-separated SEAL app IDs.")
    team_type: str = Field(..., description="aligned | flex | dedicated")
    sponsored: bool = False
    sponsored_product_id: Optional[str] = None

    @field_validator("team_type", mode="before")
    @classmethod
    def _check_team_type(cls, v: Any) -> str:
        v = str(v).strip().lower()
        if v not in _VALID_TEAM_TYPES:
            raise ValueError(f"team_type must be one of {_VALID_TEAM_TYPES}; got {v!r}")
        return v


class PatTeamRoleRow(BaseModel):
    """PAT team role assignment — links Employee to DevTeam via a named Role.
    Follows the org:Membership n-ary pattern used by SEAL application roles."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True, extra="ignore")

    team_id: str = Field(..., min_length=1)
    employee_sid: str = Field(..., min_length=1)
    role_id: str = Field(..., min_length=1)
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None


class CatalogLOBsLoader(BaseLoader):
    name: ClassVar[str] = "catalog_lobs.v1"
    cypher_path: ClassVar[Path | None] = _CYPHER / "catalog_lobs.cypher"
    row_model: ClassVar[type] = CatalogLOBRow
    source_label: ClassVar[str] = "oracle"

    # Precedence chain (config-driven). Lazy so importing the module needs no file I/O.
    _resolver: ClassVar[PrecedenceResolver | None] = None

    @classmethod
    def resolver(cls) -> PrecedenceResolver:
        if cls._resolver is None:
            cls._resolver = PrecedenceResolver.from_yaml()
        return cls._resolver

    def to_params(self, model: BaseModel) -> dict:
        params = super().to_params(model)
        # Resolve :RECONCILES_TO through precedence.yaml rather than trusting the
        # raw catalog column — so flipping `order:` reorders the winner with no
        # code edit (D2 acceptance).
        params.update(resolve_lob_reconciliation(model, self.resolver()))  # type: ignore[arg-type]
        return params


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


class AreaProductsLoader(BaseLoader):
    name: ClassVar[str] = "area_products.v1"
    cypher_path: ClassVar[Path | None] = _CYPHER / "area_products.cypher"
    row_model: ClassVar[type] = AreaProductRow
    source_label: ClassVar[str] = "pat"


class PatProductMappingLoader(BaseLoader):
    name: ClassVar[str] = "pat_product_mapping.v1"
    cypher_path: ClassVar[Path | None] = _CYPHER / "pat_product_mapping.cypher"
    row_model: ClassVar[type] = PatProductMappingRow
    source_label: ClassVar[str] = "pat"


class PatTeamRolesLoader(BaseLoader):
    name: ClassVar[str] = "pat_team_roles.v1"
    cypher_path: ClassVar[Path | None] = _CYPHER / "pat_team_roles.cypher"
    row_model: ClassVar[type] = PatTeamRoleRow
    source_label: ClassVar[str] = "pat"
