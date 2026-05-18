"""SEAL Contact Data loader.

Long-format CSV: one row per (seal_id, role_name, employee_id) triple.
The pydantic SealContactRow canonicalizes role labels (e.g. 'L2 Manager'
-> 'L2 Operate Manager') so minor source drift doesn't reject rows.

If the actual SEAL Contact extract is wide-format (one row per app with
five role columns), add a small splayer in this module that emits one
SealContactRow per non-empty role column before invoking the loader.
"""
from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from ..models import SealContactRow
from .base import BaseLoader


class SealContactsLoader(BaseLoader):
    name: ClassVar[str] = "seal_contacts.v1"
    cypher_path: ClassVar[Path | None] = (
        Path(__file__).resolve().parent / "cypher" / "seal_contacts.cypher"
    )
    row_model: ClassVar[type] = SealContactRow
    source_label: ClassVar[str] = "csv"
