"""SEAL Application Data loader.

Phase 1: CSV.  Phase 2: swap to OracleAdapter, identical row model + Cypher.

Idempotent. Always creates :EventProcessing and :BatchProcessing ports for
every Application per v3 §C, even if the app currently has no observed
runtime in that mode.
"""
from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from ..models import SealApplicationRow
from .base import BaseLoader


class SealApplicationsLoader(BaseLoader):
    name: ClassVar[str] = "seal_applications.v1"
    cypher_path: ClassVar[Path | None] = (
        Path(__file__).resolve().parent / "cypher" / "seal_applications.cypher"
    )
    row_model: ClassVar[type] = SealApplicationRow
    source_label: ClassVar[str] = "csv"  # 'oracle' once phase 2 swap lands
