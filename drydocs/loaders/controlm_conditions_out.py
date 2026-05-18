"""Control-M OUT-condition loader (M3 part 2).

Source: ``psgmgr.CM_DEF_LNKO_P_VW`` (wraps ``dtsremgr.DEF_LNKO_P``).
Schema has the ``SIGN`` operator column (``+`` to emit, ``-`` to remove),
no AND_OR/PARENTHESES/ORDER_ machinery (those are IN-side concerns).

Prereq: :class:`ControlMJobsLoader` must run first.
"""
from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from ..models import ControlMConditionOutRow
from .base import BaseLoader


class ControlMConditionsOutLoader(BaseLoader):
    name: ClassVar[str] = "controlm_conditions_out.v1"
    cypher_path: ClassVar[Path | None] = (
        Path(__file__).resolve().parent / "cypher" / "controlm_conditions_out.cypher"
    )
    row_model: ClassVar[type] = ControlMConditionOutRow
    source_label: ClassVar[str] = "oracle"
