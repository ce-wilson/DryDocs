"""Row models for the remediation axis — today, fix tracking.

The fix-tracking row is what ``drydocs_core.fix_tracking.parse_change_set``
produces and what the drydocs-load fix-tracking loader UNWINDs. It is the
narrow, already-checked shape: the parser has ruled on the schema id, the
target label, the NODE KEY and the status enum, so what this model adds is the
per-field type contract every loader row model carries (gate
remediation-fix-tracking §C1).

``job_id`` is optional BY SHAPE, not by rule: folder targets are keyed on
``folder_id`` alone, and one batch carries both kinds, so every row needs the
same fields for the Cypher to UNWIND them together. The ``kind`` discriminator
is what the Cypher branches on, and the cross-field check below is what keeps
the two in step — a ``job`` row with no ``job_id`` would MATCH every job in the
folder.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from ..fix_tracking import FIX_STATUS_ENUM, TARGET_KINDS


class FixTrackingRow(BaseModel):
    """One fix-tracking target: a node key, and the three ruled properties."""

    kind: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    folder_id: str = Field(..., min_length=1)
    job_id: str | None = None
    display_name: str = ""
    remediation_fix_id: str = Field(..., min_length=1)
    remediation_status: str = Field(..., min_length=1)
    remediation_status_date: str = Field(..., min_length=1)

    @field_validator("folder_id", "job_id", mode="before")
    @classmethod
    def _keys(cls, v: Any) -> str | None:
        """Node-key fields arrive from YAML, where an id may parse as an int."""
        if v is None:
            return None
        text = str(v).strip()
        return text or None

    @field_validator("remediation_status_date", mode="before")
    @classmethod
    def _date(cls, v: Any) -> str:
        """A YAML date scalar round-trips to ISO; the Cypher calls date() on it."""
        return str(v).strip()

    @field_validator("remediation_status")
    @classmethod
    def _status(cls, v: str) -> str:
        if v not in FIX_STATUS_ENUM:
            raise ValueError(
                f"unknown remediation_status {v!r} — the ruled enum is "
                f"{' | '.join(FIX_STATUS_ENUM)} (gate remediation-fix-tracking §B2)"
            )
        return v

    @model_validator(mode="after")
    def _kind_matches_the_key(self) -> FixTrackingRow:
        if self.kind not in TARGET_KINDS.values():
            raise ValueError(
                f"unknown target kind {self.kind!r} — the ruled kinds are "
                f"{' | '.join(sorted(set(TARGET_KINDS.values())))}"
            )
        if self.kind == "job" and not self.job_id:
            raise ValueError(
                "a job target needs job_id — the :ControlMJob NODE KEY is "
                "(folder_id, job_id), and folder_id alone would MATCH every job "
                "in the folder"
            )
        if self.kind == "folder" and self.job_id:
            raise ValueError(
                f"a folder target carries no job_id (got {self.job_id!r}) — the "
                ":ControlMFolder NODE KEY is folder_id alone"
            )
        return self
