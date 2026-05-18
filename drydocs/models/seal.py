"""SEAL row models — locked to the real DECO_SEAL_APP_INFO column list and
the SEAL framework role vocabulary.

Source table: ``PSGMGR.DECO_SEAL_APP_INFO``. Column list locked to the
DDL the production support team shared. The ~90 source columns are
projected down to ~40 in :class:`SealApplicationRow` — identity,
lifecycle, risk/compliance, hosting/platform, and the three embedded
contacts (App Owner, CTO, Primary Information Owner). Additional roles
(BIO, DA, CBT, L1/L2 Operate Manager, etc.) come from a separate SEAL
Contact extract and load via :class:`SealContactRow`.

The pydantic ``extra="ignore"`` config means the model tolerates either
direction of drift: missing optional columns are fine, extra source
columns (e.g., bespoke MNPI-related fields a team adds) are silently
dropped at the boundary.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# Coercers
# ============================================================================

_NULL_TOKENS = {"", "[null]", "null", "none", "n/a", "na"}


def _str_or_none(v: Any) -> str | None:
    """Treat empty strings and SQL '[Null]' tokens as None."""
    if v is None:
        return None
    s = str(v).strip()
    return None if s.lower() in _NULL_TOKENS else s


def _int_or_none(v: Any) -> int | None:
    s = _str_or_none(v)
    return int(s) if s is not None else None


_YES_TOKENS = {"yes", "y", "true", "t", "1"}
_NO_TOKENS = {"no", "n", "false", "f", "0"}


def _bool_or_none(v: Any) -> bool | None:
    """SEAL yes/no fields — tolerant boolean coercer; '[Null]' -> None."""
    s = _str_or_none(v)
    if s is None:
        return None
    sl = s.lower()
    if sl in _YES_TOKENS:
        return True
    if sl in _NO_TOKENS:
        return False
    return None  # unknown token; preserve as null rather than fail


# ============================================================================
# Enums
# ============================================================================


class AppState(str, Enum):
    """SEAL APP_STATE values. Phase-1 ingest filters to OPERATE-status
    apps for support inventory; BUILD / RETIRE land in the graph but are
    flagged inactive."""

    BUILD = "Build"
    OPERATE = "Operate"
    RETIRE = "Retire"
    UNKNOWN = "Unknown"


class RiskLevel(str, Enum):
    """SEAL OVERALL_RISK_RATING values."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class SealRole(str, Enum):
    """SEAL framework role vocabulary (per seal-overview-with-roles.txt).

    Mandatory application-level roles come from the SEAL spec.
    L1/L2 Operate Manager and Risk Manager are optional but commonly
    set by production support teams; Backup Application Owner became
    effective 2026-05-18.
    """

    APPLICATION_OWNER = "Application Owner"
    PRIMARY_INFORMATION_OWNER = "Primary Information Owner"
    BACKUP_INFORMATION_OWNER = "Backup Information Owner"
    CTO = "CTO"
    DESIGN_AUTHORITY = "Design Authority"
    CHIEF_BUSINESS_TECHNOLOGIST = "Chief Business Technologist"
    L1_OPERATE_MANAGER = "L1 Operate Manager"
    L2_OPERATE_MANAGER = "L2 Operate Manager"
    BACKUP_APPLICATION_OWNER = "Backup Application Owner"
    # Kept from the original DryDocs v3 §F design even though it doesn't
    # appear in the published SEAL spec — production support teams set
    # it via a custom field.
    RISK_MANAGER = "Risk Manager"


# Role name canonicalizer — tolerates common drift from real CSV exports.
_ROLE_CANONICAL: dict[str, str] = {
    # App Owner family
    "app owner": "Application Owner",
    "application owner": "Application Owner",
    "ao": "Application Owner",
    # Primary Information Owner family (replaces 'Data Owner')
    "primary information owner": "Primary Information Owner",
    "pio": "Primary Information Owner",
    "data owner": "Primary Information Owner",
    "info owner": "Primary Information Owner",
    "information owner": "Primary Information Owner",
    # Backup Information Owner
    "backup information owner": "Backup Information Owner",
    "bio": "Backup Information Owner",
    # CTO
    "cto": "CTO",
    "chief technology officer": "CTO",
    "chief tech officer": "CTO",
    # Design Authority
    "design authority": "Design Authority",
    "da": "Design Authority",
    # CBT
    "chief business technologist": "Chief Business Technologist",
    "cbt": "Chief Business Technologist",
    # Operate managers
    "l1 operate manager": "L1 Operate Manager",
    "l1 ops manager": "L1 Operate Manager",
    "l2 operate manager": "L2 Operate Manager",
    "l2 ops manager": "L2 Operate Manager",
    "l2 manager": "L2 Operate Manager",
    "operate manager": "L2 Operate Manager",
    # Backup App Owner (effective 2026-05-18)
    "backup application owner": "Backup Application Owner",
    "bao": "Backup Application Owner",
    # Risk Manager (non-SEAL-spec, user-confirmed)
    "risk manager": "Risk Manager",
    "rm": "Risk Manager",
}


def canonicalize_role(raw: Any) -> str | None:
    """Canonical role name from an arbitrary input string. Returns the
    canonical SEAL-spec name or None if unrecognised."""
    s = _str_or_none(raw)
    if s is None:
        return None
    return _ROLE_CANONICAL.get(s.lower())


# ============================================================================
# SealApplicationRow
# ============================================================================


class SealApplicationRow(BaseModel):
    """One row of ``PSGMGR.DECO_SEAL_APP_INFO``.

    Identity:           app_id, name
    Lifecycle:          app_state, dates, retirement / replacement metadata
    Org context:        app_lob, reporting_cio_lob, reporting_cto_group,
                        tech_group_owner + id
    Risk + compliance:  overall_risk_rating, *_reportable flags, info_classification,
                        strictest_rpo / rto, personal_info / phi / mnpi flags
    Tech + hosting:     platforms, programming_languages, hosting_vendor,
                        overall_hosting_type, authentication / authorization
    Embedded contacts:  app_owner, chief_tech_officer, info_owner (sid + name)
    Audit:              capture_date, creation_date, last_certified_*

    All fields except ``app_id`` and ``name`` are optional. Empty strings
    and SQL ``[Null]`` tokens coerce to None.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="ignore",
    )

    # ---- identity ----
    app_id: str = Field(..., alias="app_id", min_length=1)
    name: str = Field(..., alias="name", min_length=1)
    app_short_name: str | None = None
    description: str | None = None

    # ---- lifecycle ----
    app_state: str | None = Field(
        None,
        description="Build / Operate / Retire (raw string; case-tolerant).",
    )
    investment_strategy: str | None = None
    creation_date: str | None = None
    actual_build_start_date: str | None = None
    actual_operate_date: str | None = None
    actual_decom_date: str | None = None
    actual_retirement_date: str | None = None
    planned_build_start_date: str | None = None
    planned_operate_date: str | None = None
    planned_decom_date: str | None = None
    planned_decom_date_chg_reason: str | None = None
    planned_retirement_date: str | None = None
    replaced_by_app_ids: str | None = None
    replacement_app_type: str | None = None
    retirement_type: str | None = None

    # ---- org context ----
    app_lob: str | None = None
    reporting_cio_lob: str | None = None
    reporting_cto_group: str | None = None
    tech_group_owner: str | None = None
    tech_group_owner_id: str | None = None
    owning_legal_entity: str | None = None
    using_lob_sub_lobs: str | None = None

    # ---- risk + compliance ----
    overall_risk_rating: str | None = None
    sox_reportable: bool | None = None
    glba_reportable: bool | None = None
    pci_reportable: bool | None = None
    soc1_reportable: bool | None = None
    ccar_reportable: bool | None = None
    global_statutory_audit: bool | None = None
    payment_card_industry_category: str | None = None
    info_classification: str | None = None
    personal_info: bool | None = None
    sensitive_personal_info: bool | None = None
    client_confidential_info: bool | None = None
    phi: bool | None = None
    mnpi: bool | None = None
    strictest_rpo: str | None = None
    strictest_rto: str | None = None

    # ---- tech + hosting ----
    hosting_vendor: str | None = None
    overall_hosting_type: str | None = None
    platforms: str | None = None
    kapp: str | None = Field(
        None, description="KAPP platform alignment (e.g., 'Public Cloud - Atlas (AWS)')."
    )
    provides_platforms: str | None = None
    programming_languages: str | None = Field(
        None,
        description="Pipe-separated string, e.g. 'Java | SQL | Python'. "
                    "Downstream may split on '|'.",
    )
    app_dev_responsibility: str | None = None
    app_dev_vendor_name: str | None = None
    firm_owned_source_code: bool | None = None
    internally_shared: bool | None = None
    dev_app_only: bool | None = None
    external_service: bool | None = None
    tech_maintained: bool | None = None
    hardware_deployments: bool | None = None
    software_deployments: bool | None = None
    third_party_direct_access: bool | None = None
    vendor_engagements: bool | None = None
    source_code_vendor_name: str | None = None
    direct_access_vendor_name: str | None = None
    cpof_logical_deployment: bool | None = None
    hvbe: bool | None = None
    iwp_deployment: bool | None = None

    # ---- auth + network ----
    authentication_type: str | None = None
    authorization_type: str | None = None
    fine_grain_authorization_type: str | None = None
    external_network_connectivity: bool | None = None
    not_external_facing_reason: str | None = None
    external_network_exposure: bool | None = None
    tier_0_1_or_2_network_assets: bool | None = None
    external_api_connectivity: bool | None = None
    external_access_control: bool | None = None
    instant_change_authorization: bool | None = None

    # ---- embedded contacts (3 of them; the rest come via SealContactRow) ----
    app_owner_sid: str | None = None
    app_owner_name: str | None = None
    chief_tech_officer_sid: str | None = None
    chief_tech_officer_name: str | None = None
    info_owner_sid: str | None = None
    info_owner_name: str | None = None

    # ---- audit / certification ----
    capture_date: str | None = None
    certification_status: str | None = None
    last_certified_by_sid: str | None = None
    last_certified_date: str | None = None
    data_integrity: str | None = None
    externally_mandated: bool | None = None
    externally_mandated_type: str | None = None

    # ---- coercers ----

    @field_validator(
        "name", "app_short_name", "description", "app_state",
        "investment_strategy", "creation_date", "actual_build_start_date",
        "actual_operate_date", "actual_decom_date", "actual_retirement_date",
        "planned_build_start_date", "planned_operate_date", "planned_decom_date",
        "planned_decom_date_chg_reason", "planned_retirement_date",
        "replaced_by_app_ids", "replacement_app_type", "retirement_type",
        "app_lob", "reporting_cio_lob", "reporting_cto_group",
        "tech_group_owner", "tech_group_owner_id", "owning_legal_entity",
        "using_lob_sub_lobs", "overall_risk_rating",
        "payment_card_industry_category", "info_classification",
        "strictest_rpo", "strictest_rto", "hosting_vendor",
        "overall_hosting_type", "platforms", "kapp", "provides_platforms",
        "programming_languages", "app_dev_responsibility",
        "app_dev_vendor_name", "source_code_vendor_name",
        "direct_access_vendor_name", "authentication_type",
        "authorization_type", "fine_grain_authorization_type",
        "not_external_facing_reason", "app_owner_sid", "app_owner_name",
        "chief_tech_officer_sid", "chief_tech_officer_name",
        "info_owner_sid", "info_owner_name", "capture_date",
        "certification_status", "last_certified_by_sid",
        "last_certified_date", "data_integrity", "externally_mandated_type",
        mode="before",
    )
    @classmethod
    def _str(cls, v: Any) -> str | None:
        return _str_or_none(v)

    @field_validator(
        "sox_reportable", "glba_reportable", "pci_reportable",
        "soc1_reportable", "ccar_reportable", "global_statutory_audit",
        "personal_info", "sensitive_personal_info", "client_confidential_info",
        "phi", "mnpi", "firm_owned_source_code", "internally_shared",
        "dev_app_only", "external_service", "tech_maintained",
        "hardware_deployments", "software_deployments",
        "third_party_direct_access", "vendor_engagements",
        "cpof_logical_deployment", "hvbe", "iwp_deployment",
        "external_network_connectivity", "external_network_exposure",
        "tier_0_1_or_2_network_assets", "external_api_connectivity",
        "external_access_control", "instant_change_authorization",
        "externally_mandated",
        mode="before",
    )
    @classmethod
    def _bool(cls, v: Any) -> bool | None:
        return _bool_or_none(v)

    @field_validator("app_id", mode="before")
    @classmethod
    def _app_id(cls, v: Any) -> str:
        s = _str_or_none(v)
        if s is None:
            raise ValueError("app_id is required")
        return s


# ============================================================================
# SealContactRow — additional / optional roles beyond the 3 embedded in
# DECO_SEAL_APP_INFO. Long format: one row per (app_id, role, employee).
# ============================================================================


class SealContactRow(BaseModel):
    """One row of an external SEAL Contact extract.

    Use this when the team provides BIO / Design Authority / Chief Business
    Technologist / L1-L2 Operate Manager / Backup Application Owner / Risk
    Manager mappings in a separate file (DECO_SEAL_APP_INFO only carries
    App Owner / CTO / Info Owner directly).

    Expected columns (case-insensitive, populated_by_name aliases):
        app_id, role_name, employee_sid, employee_name, employee_email
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="ignore",
    )

    app_id: str = Field(..., min_length=1)
    role_name: SealRole
    employee_sid: str = Field(
        ...,
        min_length=1,
        description="SEAL standard ID (e.g., 'Q000874').",
    )
    employee_name: str | None = None
    employee_email: str | None = None

    @field_validator("app_id", "employee_sid", mode="before")
    @classmethod
    def _id(cls, v: Any) -> str:
        s = _str_or_none(v)
        if s is None:
            raise ValueError("id field cannot be null")
        return s

    @field_validator("employee_name", "employee_email", mode="before")
    @classmethod
    def _opt_str(cls, v: Any) -> str | None:
        return _str_or_none(v)

    @field_validator("role_name", mode="before")
    @classmethod
    def _role(cls, v: Any) -> str:
        canon = canonicalize_role(v)
        if canon is None:
            raise ValueError(f"unrecognised SEAL role: {v!r}")
        return canon
