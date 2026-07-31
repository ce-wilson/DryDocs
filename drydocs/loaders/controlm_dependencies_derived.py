"""Control-M derived :WAS_INFORMED_BY edges (M3 part 2).

Consumes the output of the dependency SQL
(``drydocs/loaders/sql/controlm_dependencies_recursive.sql``) and
materializes ``:WAS_INFORMED_BY`` edges between :ControlMJob nodes.

DIRECT pairs only (phased-loader change, ported from the company repo
2026-07-23): each row is pure ctlm_id composites + the linking condition.
Transitive reach is a graph traversal, not a stored closure — no cycle
guard needed because nothing recurses anymore.

Run order: this is the DEFERRED ``--phase relationships`` pass — run once,
UNSCOPED, after ALL nodes are loaded. The edge links jobs across DIFFERENT
folders, so a per-folder scoped run silently dropped it (the second
endpoint's MATCH missed because that job wasn't loaded yet).
"""
from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from drydocs_core.models import ControlMDependencyRow
from .base import BaseLoader


class ControlMDependenciesDerivedLoader(BaseLoader):
    name: ClassVar[str] = "controlm_dependencies_derived.v1"
    # anchor dataset of the IN⋈OUT condition pairing (recorded on the dataset
    # row's note at the N9 per-row confirmation, 2026-07-31)
    source_id: ClassVar[str | None] = "controlm@[db].psgmgr.cm_def_lnki_p_vw"
    cypher_path: ClassVar[Path | None] = (
        Path(__file__).resolve().parent / "cypher" / "controlm_dependencies_derived.cypher"
    )
    row_model: ClassVar[type] = ControlMDependencyRow
    source_label: ClassVar[str] = "oracle"
