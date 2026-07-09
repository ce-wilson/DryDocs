"""Control-M IN-condition loader (M3 part 2).

Source: ``psgmgr.CM_DEF_LNKI_P_VW`` (wraps ``dtsremgr.DEF_LNKI_P``).
Schema differs from the OUT side: has AND_OR / PARENTHESES / ORDER_ for
boolean-expression metadata, no SIGN column.

Prereq: :class:`ControlMJobsLoader` must run first; conditions MATCH
their parent job by ``(job_id, version_serial)``.
"""
from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel

from ..models import ControlMConditionInRow
from .base import BaseLoader, compute_row_checksum


class ControlMConditionsInLoader(BaseLoader):
    name: ClassVar[str] = "controlm_conditions_in.v1"
    cypher_path: ClassVar[Path | None] = (
        Path(__file__).resolve().parent / "cypher" / "controlm_conditions_in.cypher"
    )
    row_model: ClassVar[type] = ControlMConditionInRow
    source_label: ClassVar[str] = "oracle"

    def to_params(self, model: BaseModel) -> dict:
        """Add the delta checksum (doc 06 Phase 2) the Cypher template uses
        to gate :WAS_GENERATED_BY on the shared :Condition node."""
        params = model.model_dump(mode="json")
        params["row_checksum"] = compute_row_checksum(params)
        return params
