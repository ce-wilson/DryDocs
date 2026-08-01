"""Catalog loaders — product hierarchy, PAT team mapping, and area products.

Target hierarchy:

    BusinessSegment -> CatalogLOB -> ProductLine -> Product -> Application
                                                            -> AreaProduct -> DevTeam
                                                            -> DevTeam (home team)

Row models are defined here alongside their loaders. When the team confirms
exact catalog table names + column names, only the SQL SELECT in each loader
needs to change — the model field names stay constant.

KEYING (C17, gate `seal-app-ref-edge-reshape` §G6-RIDER, 2026-08-01). Every
grain in this hierarchy — LOB, Sub-LOB, Product Line, Product, Area Product —
carries a NUMERIC id at source. Our node keys are strings, so every id field
below runs through ``_catalog_id``: the ids arrive as numbers and pydantic v2
does not coerce a number to a string. A name is NEVER a key here; see the
ruling in ``config/gate-log.md``.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from drydocs_core.precedence import Claim, PrecedenceResolver

from .base import BaseLoader

_CYPHER = Path(__file__).resolve().parent / "cypher"

# The product catalog feed speaks for the org-taxonomy authority (precedence.yaml#order
# id 'lob-product-team'). When a more-authoritative reconciliation override exists
# (e.g. an internal-standards crosswalk), pass it through `extra_reconcile_claims`
# below — the precedence.yaml order, not this code, decides which one wins.
_CATALOG_AUTHORITY = "lob-product-team"


def resolve_lob_reconciliation(
    model: CatalogLOBRow,
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


def _catalog_id(v: Any) -> Any:
    """Coerce a source catalog id to its canonical string node-key form.

    The catalog grains are NUMERIC at source (C17 §a) while every node key here
    is a string, and pydantic v2 — unlike v1 — refuses int -> str. Without this
    validator an Oracle NUMBER column or a numerically-typed CSV read rejects
    EVERY row of a catalog load, not some of them. ``attribution.py`` already
    carries the same coercion for the Control-M keys ("Coerce Oracle NUMBER /
    int inputs to the stripped-string node-key form") — the catalog loaders
    simply never got it.

    A blind ``str(v)`` is not good enough, and that is the whole reason this is
    a function rather than one line: a nullable numeric column read through
    pandas comes back as float64, so ``str(12345.0)`` yields ``'12345.0'`` —
    an id that matches NOTHING and MERGEs a duplicate node beside the real one.
    Integral floats/Decimals therefore normalize to their integer form, and a
    genuinely fractional value is REFUSED rather than rounded: an id with a
    fractional part is corruption, and guessing at it is how a bad join becomes
    permanent.
    """
    if v is None:
        return None
    if isinstance(v, bool):
        # bool is an int subclass — True would silently key a node as '1'
        raise ValueError("a boolean is not a catalog id")
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, int | float | Decimal):
        try:
            number = Decimal(str(v))
        except InvalidOperation as exc:  # NaN / Infinity
            raise ValueError(f"{v!r} is not a usable catalog id") from exc
        if number != number.to_integral_value():
            raise ValueError(
                f"catalog id {v!r} has a fractional part — refusing to coerce "
                "(rounding would invent a key)"
            )
        return str(int(number))
    return str(v).strip()


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

    @field_validator("lob_id", mode="before")
    @classmethod
    def _ids(cls, v: Any) -> Any:
        return _catalog_id(v)


class ProductLineRow(BaseModel):
    """A Product Line, keyed on the source's numeric product_line_id.

    ``product_line_id`` is REQUIRED and stays required — that is the executable
    half of the C17 §a ruling. The PAT team report projects this grain as a NAME
    with no id column, and a name is exactly what must not become the key here:
    product lines are renamed and near-duplicate names exist, so a name-keyed
    join silently re-points a confirmed mapping the next time someone edits a
    label. The id exists at source; the fix is to extract it, not to key on what
    the report happened to project.
    """

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True, extra="ignore")

    product_line_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    parent_lob_id: str = Field(..., min_length=1)

    @field_validator("product_line_id", "parent_lob_id", mode="before")
    @classmethod
    def _ids(cls, v: Any) -> Any:
        return _catalog_id(v)


class ProductRow(BaseModel):
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True, extra="ignore")

    product_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    parent_product_line_id: str = Field(..., min_length=1)

    @field_validator("product_id", "parent_product_line_id", mode="before")
    @classmethod
    def _ids(cls, v: Any) -> Any:
        return _catalog_id(v)


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

    @field_validator("team_id", "parent_product_id", "jira_board_id", mode="before")
    @classmethod
    def _ids(cls, v: Any) -> Any:
        return _catalog_id(v)


class AreaProductRow(BaseModel):
    """Area Product Group (Team of Teams) — intermediate between Product and
    DevTeam in the PAT/Align hierarchy.

    This is the hierarchy grain (one row per area product). It is UNQUALIFIED
    on purpose: Supporting vs Sponsoring is a property of a TEAM's relationship
    to an area product, not of the area product itself — see
    ``PatProductMappingRow`` for where that qualification lives (C17 §b).
    """

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True, extra="ignore")

    area_product_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    parent_product_id: str = Field(..., min_length=1)

    @field_validator("area_product_id", "parent_product_id", mode="before")
    @classmethod
    def _ids(cls, v: Any) -> Any:
        return _catalog_id(v)


_VALID_TEAM_TYPES = {"aligned", "flex", "dedicated"}


class PatProductMappingRow(BaseModel):
    """PAT product mapping — links DevTeam to home Product, optional AreaProduct,
    and SEAL applications. Records team type and sponsored status.

    C17 §b — WHICH SOURCE COLUMN FEEDS ``area_product_id``. The team report
    splits its area-product columns into **Supporting** and **Sponsoring**;
    ``area_product_id`` is the SUPPORTING one (the team's own alignment) and
    ``sponsored_area_product_id`` is the Sponsoring one. The field name is
    unqualified for a reason worth stating rather than fixing by rename: the
    qualification is REPORT-SPECIFIC — a sibling member-level report carries a
    plain "Area Product" with no split at all, and it means the supporting one.
    So the unqualified name is the union of both spellings and this docstring is
    the join key; a rename to ``supporting_area_product_id`` would read as if the
    member report had a column it does not have.

    C17 §c — the THIRD sponsoring form is OUT OF SCOPE. The team report also
    carries **Sponsoring Product Line**, beyond the two sponsoring forms C9 §d
    modelled. It is deliberately absent here: that column is NAME-ONLY, and
    modelling it would require keying a :ProductLine by name — precisely what
    §a forbids. It becomes modellable the day the extract carries a sponsoring
    product-line ID, and not before. Note ``extra="ignore"`` means the column is
    silently dropped when present, which is the intended handling but is only
    visible because it is written down here.
    """

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True, extra="ignore")

    team_id: str = Field(..., min_length=1)
    product_id: str = Field(..., min_length=1)
    area_product_id: str | None = Field(
        None, description="PAT Supporting Area Product — the team's alignment target (C17 §b)."
    )
    seal_ids: str | None = Field(
        None,
        description="SEAL app IDs (team-scoped; feeds arch_develops). Comma- or "
        "semicolon-delimited on input; normalized to commas.",
    )
    team_type: str = Field(..., description="aligned | flex | dedicated")
    sponsored: bool = False
    sponsored_product_id: str | None = None
    sponsored_area_product_id: str | None = Field(
        None, description="PAT Sponsoring Area Product (C9 gate 2026-07-18)."
    )

    @field_validator(
        "team_id",
        "product_id",
        "area_product_id",
        "sponsored_product_id",
        "sponsored_area_product_id",
        mode="before",
    )
    @classmethod
    def _ids(cls, v: Any) -> Any:
        return _catalog_id(v)

    @field_validator("seal_ids", mode="before")
    @classmethod
    def _normalize_seal_ids(cls, v: Any) -> Any:
        # The real PAT team report delimits SEAL ids with ';' (see
        # internal/pat-evidence); the loader cypher splits on ','.
        if v is None:
            return v
        return str(v).replace(";", ",")

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
    valid_from: str | None = None
    valid_to: str | None = None

    @field_validator("team_id", "employee_sid", "role_id", mode="before")
    @classmethod
    def _ids(cls, v: Any) -> Any:
        return _catalog_id(v)


class CatalogLOBsLoader(BaseLoader):
    name: ClassVar[str] = "catalog_lobs.v1"
    source_id: ClassVar[str | None] = "pat:product-catalog"
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
    source_id: ClassVar[str | None] = "pat:product-catalog"
    cypher_path: ClassVar[Path | None] = _CYPHER / "product_lines.cypher"
    row_model: ClassVar[type] = ProductLineRow
    source_label: ClassVar[str] = "oracle"


class ProductsLoader(BaseLoader):
    name: ClassVar[str] = "products.v1"
    source_id: ClassVar[str | None] = "pat:product-catalog"
    cypher_path: ClassVar[Path | None] = _CYPHER / "products.cypher"
    row_model: ClassVar[type] = ProductRow
    source_label: ClassVar[str] = "oracle"


class DevTeamsLoader(BaseLoader):
    name: ClassVar[str] = "dev_teams.v1"
    source_id: ClassVar[str | None] = "pat:product-catalog"
    cypher_path: ClassVar[Path | None] = _CYPHER / "dev_teams.cypher"
    row_model: ClassVar[type] = DevTeamRow
    source_label: ClassVar[str] = "oracle"


class AreaProductsLoader(BaseLoader):
    name: ClassVar[str] = "area_products.v1"
    source_id: ClassVar[str | None] = "pat:product-catalog"
    cypher_path: ClassVar[Path | None] = _CYPHER / "area_products.cypher"
    row_model: ClassVar[type] = AreaProductRow
    source_label: ClassVar[str] = "pat"


class PatProductMappingLoader(BaseLoader):
    name: ClassVar[str] = "pat_product_mapping.v1"
    # the PAT team report (seal_ids / alignment), not the catalog hierarchy —
    # the C9 team_applications feed, split out at the v2 registry (N9)
    source_id: ClassVar[str | None] = "pat:people-report"
    cypher_path: ClassVar[Path | None] = _CYPHER / "pat_product_mapping.cypher"
    row_model: ClassVar[type] = PatProductMappingRow
    source_label: ClassVar[str] = "pat"


class PatTeamRolesLoader(BaseLoader):
    name: ClassVar[str] = "pat_team_roles.v1"
    # team-member roles come from the PAT team/people report, not the hierarchy
    source_id: ClassVar[str | None] = "pat:people-report"
    cypher_path: ClassVar[Path | None] = _CYPHER / "pat_team_roles.cypher"
    row_model: ClassVar[type] = PatTeamRoleRow
    source_label: ClassVar[str] = "pat"
