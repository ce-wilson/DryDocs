"""Control-M job loader (M3 part 1).

Source: ``psgmgr.DEF_JOB`` via OracleAdapter; CSV via CsvAdapter for
samples / dev. Produces :ControlMJob nodes with composite NODE KEY
``(job_id, version_serial)`` so version history is non-destructive
(v3 §J / §H.1).

This loader is phase-1 **structural only** — it loads job *definitions*.
Execution history (`:JobRun {kind:'controlm_execution'}` with timing
metrics) is M3 phase 2 (P2-B).

Prereq: :class:`ControlMFoldersLoader` must run first; jobs match their
parent folder by ``folder_id``.
"""
from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from ..models import ControlMJobRow
from .base import BaseLoader


class ControlMJobsLoader(BaseLoader):
    name: ClassVar[str] = "controlm_jobs.v1"
    cypher_path: ClassVar[Path | None] = (
        Path(__file__).resolve().parent / "cypher" / "controlm_jobs.cypher"
    )
    row_model: ClassVar[type] = ControlMJobRow
    source_label: ClassVar[str] = "oracle"
