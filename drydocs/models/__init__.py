"""Pydantic row models — one per source. Each model is the contract
between an Adapter (yields raw dict rows) and a loader's Cypher (UNWIND a
list of validated dicts).

ASSUMED COLUMN LISTS:  the SEAL and PAT extracts haven't been schema-shared
yet. The SEAL / catalog models capture our reasonable guesses based on the
v3 plan. The Control-M models match the BMC base-table schema referenced
in BMC-CONTROL-M-LOOP.txt, with the BMC -> psgmgr substitution applied.

When real CSVs / table columns land, only the ``alias`` arguments / SELECT
columns need to change — adapters and Cypher do not.
"""

from .seal import SealApplicationRow, SealContactRow
from .catalog import (
    BusinessSegmentRow,
    CatalogLOBRow,
    DevTeamRow,
    ProductLineRow,
    ProductRow,
)
from .controlm import ControlMConditionRow, ControlMFolderRow, ControlMJobRow

__all__ = [
    # SEAL
    "SealApplicationRow",
    "SealContactRow",
    # Catalog
    "BusinessSegmentRow",
    "CatalogLOBRow",
    "ProductLineRow",
    "ProductRow",
    "DevTeamRow",
    # Control-M (M3 part 1)
    "ControlMFolderRow",
    "ControlMJobRow",
    # Control-M (M3 part 2 — pending column-list confirmation)
    "ControlMConditionRow",
]
