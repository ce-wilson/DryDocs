"""Row model for the infrastructure server export (Epic Z; gate
server-location-ontology SIGNED OFF 12/12, 2026-08-19 — config/gate-log.md).

One row = one server in one per-business-application download
(``infra:server-export``; the acquisition grain is ONE FILE PER APPLICATION —
the prod filter selects which applications are listed, and each application's
download then carries BOTH its prod and DR servers).

The column list is the Z1 FIELD CONTRACT (config/taxonomy/server-location.yaml
``fields:``, pinned to the synthetic fixture by
tests/unit/test_server_inventory_fixture.py). The site's physical
column-header spellings are recorded company-side at the first real drop;
aliases here are where that lands when they differ.

THE STANDING CAUTION rides every consumer of ``data_center``: this is PHYSICAL
geography (a building), never the Control-M scheduling "data center" (whose
name encodes a default run time). The two never join by field name (gate §B4).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ServerInventoryRow(BaseModel):
    """One server row of a per-application infrastructure export."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="ignore",
    )

    server_name: str = Field(..., min_length=1, description="The Z2 join key (gate §C1).")
    os_product: str | None = Field(
        None, description="OS product (e.g. RHEL) — plain property per gate §A2."
    )
    os_version: str | None = Field(None, description="OS version — plain property per gate §A2.")
    rack: str | None = Field(None, description="Rack id — rides the LOCATED_IN edge (gate §B1).")
    data_center: str | None = Field(
        None, description="PHYSICAL building — never the Control-M scheduling DC (gate §B4)."
    )
    city: str | None = None
    state: str | None = None
    country: str | None = None
    designation: str = Field(..., description="PROD | DR — a :Server property (gate §A3).")
    business_application: str = Field(
        ..., min_length=1, description="Owning application (app_id) — the download grain."
    )

    @field_validator("designation")
    @classmethod
    def _designation_enum(cls, v: str) -> str:
        up = v.upper()
        if up not in {"PROD", "DR"}:
            raise ValueError(f"designation must be PROD or DR, got {v!r}")
        return up

    @property
    def location_grain(self) -> str | None:
        """The Idea-90 mixed-grain declaration (gate §B2): the FINEST geography
        level this row actually supplied. Never inferred; null when the row
        carries no geography at all."""
        if self.data_center:
            return "building"
        if self.city:
            return "city"
        if self.state:
            return "state"
        if self.country:
            return "country"
        return None
