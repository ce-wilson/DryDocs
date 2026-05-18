"""BMC Control-M row models.

Sources:
  - ``psgmgr.CM_DEF_VTAB``       (folders; wraps ``dtsremgr.DEF_TAB``)
  - ``psgmgr.CM_DEF_VJOB``       (jobs;    wraps ``dtsremgr.DEF_JOB``)
  - ``psgmgr.CM_DEF_LNKI_P_VW``  (in-conditions;  wraps ``dtsremgr.DEF_LNKI_P``)
  - ``psgmgr.CM_DEF_LNKO_P_VW``  (out-conditions; wraps ``dtsremgr.DEF_LNKO_P``)

The Oracle SELECT lives in ``drydocs/loaders/sql/controlm_*.sql``; this
module defines the columns the loaders expect after projection. CSV
samples in ``data/samples/`` use the same column names so offline dev
paths exercise the same models.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _int_or_none(v: Any) -> int | None:
    if v in (None, ""):
        return None
    return int(str(v).strip())


def _str_or_none(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


class ControlMFolderRow(BaseModel):
    """One row of ``psgmgr.CM_DEF_VTAB`` (wraps ``dtsremgr.DEF_TAB``).

    BMC calls these "tables" but they are folders. The naming gotcha is
    documented in ``docs/m3_controlm_concept_mapping.md``.

    Expected projection (matches ``drydocs/loaders/sql/controlm_folders.sql``):
        folder_id, parent_table, data_center, user_daily,
        is_current_version, version_serial, capture_date
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="ignore",
    )

    folder_id: str = Field(..., min_length=1)
    parent_table: str = Field(..., min_length=1, description="Folder name.")
    data_center: str = Field(
        ...,
        min_length=1,
        description="Control-M server (P12 / P14 / P32 / P33 / ...).",
    )
    user_daily: str | None = Field(
        None,
        description="Active-scheduling flag; null = inactive (quarantined, not dropped).",
    )
    is_current_version: str | int | None = Field(
        None,
        description="psgmgr view filter — 1/'Y' = active version of this folder definition.",
    )
    version_serial: int | None = Field(
        None,
        description="Version of the folder definition; new VERSION_SERIAL = history.",
    )
    capture_date: str | None = Field(
        None,
        description="Audit timestamp from the psgmgr replication.",
    )

    @field_validator("user_daily", mode="before")
    @classmethod
    def _user_daily(cls, v: Any) -> str | None:
        return _str_or_none(v)

    @field_validator("is_current_version", mode="before")
    @classmethod
    def _icv(cls, v: Any) -> Any:
        if v in (None, ""):
            return None
        return v

    @field_validator("version_serial", mode="before")
    @classmethod
    def _vs(cls, v: Any) -> int | None:
        return _int_or_none(v)

    @field_validator("capture_date", mode="before")
    @classmethod
    def _cap(cls, v: Any) -> str | None:
        return _str_or_none(v)

    @property
    def active(self) -> bool:
        """True iff scheduled (``user_daily``) AND current-version (``is_current_version``)."""
        scheduled = self.user_daily is not None and self.user_daily != ""
        current = str(self.is_current_version).strip().lower() in {"1", "y", "true"} if self.is_current_version is not None else False
        return scheduled and current


class ControlMJobRow(BaseModel):
    """One row of ``psgmgr.CM_DEF_VJOB`` (wraps ``dtsremgr.DEF_JOB``).

    Composite key is ``(job_id, version_serial)`` — new ``VERSION_SERIAL``
    means a new graph node so history is non-destructive (v3 §J node-key
    constraint).

    Expected projection (matches ``drydocs/loaders/sql/controlm_jobs.sql``):
        job_id, version_serial, folder_id, job_name, cyclic_type, job_order,
        is_current_version, capture_date
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="ignore",
    )

    job_id: str = Field(..., min_length=1)
    version_serial: int = Field(..., ge=0)
    folder_id: str = Field(..., min_length=1, description="FK to JobFolder.folder_id.")
    job_name: str = Field(..., min_length=1)
    cyclic_type: str | None = Field(
        None,
        description="DAILY / 15MIN / etc. Matters for condition matching (cyclic class).",
    )
    job_order: int | None = Field(
        None,
        description="Ordering within the folder. NULL allowed.",
    )
    is_current_version: str | int | None = Field(
        None,
        description="psgmgr view filter — 1/'Y' = active version of this job definition.",
    )
    capture_date: str | None = Field(
        None,
        description="Audit timestamp from the psgmgr replication.",
    )

    @field_validator("version_serial", mode="before")
    @classmethod
    def _version_serial(cls, v: Any) -> int:
        return int(str(v).strip())

    @field_validator("job_order", mode="before")
    @classmethod
    def _job_order(cls, v: Any) -> int | None:
        return _int_or_none(v)

    @field_validator("cyclic_type", mode="before")
    @classmethod
    def _cyclic_type(cls, v: Any) -> str | None:
        return _str_or_none(v)

    @field_validator("is_current_version", mode="before")
    @classmethod
    def _icv(cls, v: Any) -> Any:
        if v in (None, ""):
            return None
        return v

    @field_validator("capture_date", mode="before")
    @classmethod
    def _cap(cls, v: Any) -> str | None:
        return _str_or_none(v)


class ControlMConditionRow(BaseModel):
    """One row of ``psgmgr.CM_DEF_LNKI_P_VW`` or ``CM_DEF_LNKO_P_VW``.

    Same shape on both sides — only the loader's intent differs (in vs out).
    Schema confirmed for LNKO_P_VW; LNKI_P_VW is inferred by symmetry and
    must be validated against the actual DDL once that re-upload succeeds.

    Each row is "job J (in folder F) consumes/emits condition C (with SIGN)
    on operational date ODATE in this VERSION_SERIAL of the definition."
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="ignore",
    )

    folder_id: str = Field(..., min_length=1, description="TABLE_ID.")
    job_id: str = Field(..., min_length=1)
    version_serial: int = Field(..., ge=0)
    condition_name: str = Field(..., min_length=1, description="The condition / event name.")
    odate: str | None = Field(None, description="Operational date (business-date axis).")
    sign: str | None = Field(None, description="Operator (+ / - / AND / OR).")
    isn: int | None = Field(None, description="ISN_ — internal sequence number.")
    version_opcode: str | None = Field(
        None,
        description="VERSION_OPCODE — present on out-conditions; absent on in-conditions.",
    )
    is_current_version: str | int | None = None
    capture_date: str | None = None

    @field_validator("version_serial", "isn", mode="before")
    @classmethod
    def _int(cls, v: Any) -> int | None:
        return _int_or_none(v)

    @field_validator(
        "odate", "sign", "version_opcode", "capture_date", mode="before"
    )
    @classmethod
    def _strv(cls, v: Any) -> str | None:
        return _str_or_none(v)

    @field_validator("is_current_version", mode="before")
    @classmethod
    def _icv2(cls, v: Any) -> Any:
        if v in (None, ""):
            return None
        return v
