"""Control-M derived :DEPENDS_ON edges (M3 part 2).

Consumes the output of the recursive predecessor SQL
(``drydocs/loaders/sql/controlm_dependencies_recursive.sql``) and
materializes ``:DEPENDS_ON`` edges between :ControlMJob nodes.

Cycle detection happens **in the SQL** via path-INSTR + recursion-level
cap; this loader writes the result without any further filtering.

Run order: folders -> jobs -> conditions in/out -> dependencies derived.
The derivation depends on having the jobs and (for queryability) the
:Condition graph in place; technically only :ControlMJob is required for
the edge MERGE itself.
"""
from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from ..models import ControlMDependencyRow
from .base import BaseLoader


class ControlMDependenciesDerivedLoader(BaseLoader):
    name: ClassVar[str] = "controlm_dependencies_derived.v1"
    cypher_path: ClassVar[Path | None] = (
        Path(__file__).resolve().parent / "cypher" / "controlm_dependencies_derived.cypher"
    )
    row_model: ClassVar[type] = ControlMDependencyRow
    source_label: ClassVar[str] = "oracle"
