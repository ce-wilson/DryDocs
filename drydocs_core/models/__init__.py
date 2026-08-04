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

# NOTE: the catalog row models are NOT re-exported here. They live with their
# loaders in drydocs/loaders/catalog.py, which is the ONLY definition — a stale
# shadow copy of all eight lived in this package until 2026-07-27 (backlog C18)
# and had already drifted past the C9 gate (missing sponsored_area_product_id
# and the ';'->',' seal_ids normalizer). Because its model_config is
# extra="ignore", importing the shadow would have dropped that column SILENTLY
# at validation. Deleted rather than re-synced: two definitions is the defect,
# not which one is stale. tests/unit/test_no_shadow_definitions.py keeps a
# second copy from reappearing. Phase C (ADR 0002-A-1) may move the live models
# here — one definition, MOVED.
from .attribution import (
    FolderAttributionRow,
    ManualMappingRow,
    SealAttributionRow,
    StgAppFactRow,
)
from .code_snapshot import CodeModuleRow
from .controlm import (
    ControlMConditionInRow,
    ControlMConditionOutRow,
    ControlMDependencyRow,
    ControlMFolderRow,
    ControlMHostRow,
    ControlMJobRow,
    ControlMVariableRow,
)
from .docs import BmcDocChunkRow
from .registry import SoftwareProductRow
from .seal import SealApplicationRow, SealContactRow

__all__ = [
    # SEAL
    "SealApplicationRow",
    "SealContactRow",
    # Catalog — see the note above: defined in drydocs/loaders/catalog.py only.
    # Control-M (M3 part 1 — folders + jobs)
    "ControlMFolderRow",
    "ControlMJobRow",
    # Control-M (M3 part 2 — conditions + derived dependencies)
    "ControlMConditionInRow",
    "ControlMConditionOutRow",
    "ControlMDependencyRow",
    # Control-M (P3 — host topology)
    "ControlMHostRow",
    # Control-M (C3/C4 normalization — variables)
    "ControlMVariableRow",
    # Software registry (plan 07 / ADR 0004)
    "SoftwareProductRow",
    # bmc-docs lexical graph (Document -> Chunk)
    "BmcDocChunkRow",
    # SEAL attribution (K2 — STG_APP_FACT facts -> WAS_ASSOCIATED_WITH edges)
    "StgAppFactRow",
    "SealAttributionRow",
    "FolderAttributionRow",
    "ManualMappingRow",
    # Self-documentation code graph (G33 / Epic U)
    "CodeModuleRow",
]
