"""Control-M folder loader (M3 part 1).

Source: ``psgmgr.CM_DEF_VTAB`` (wraps ``dtsremgr.DEF_TAB``) via
OracleAdapter; CSV via CsvAdapter for samples / dev. Produces :JobFolder
nodes and the :ControlMServer mesh (deduped on DATA_CENTER value).

Active filter (``WHERE IS_CURRENT_VERSION = 1 AND USER_DAILY IS NOT NULL``)
lives in the SQL projection — see ``drydocs/loaders/sql/controlm_folders.sql``.
Inactive folders that have leaked through still land in the graph with
``active: false`` so historical references don't break.

Always run **before** :class:`ControlMJobsLoader` — jobs match their
parent folder by ``folder_id`` and silently skip if the folder isn't
present yet.
"""
from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from ..models import ControlMFolderRow
from .base import BaseLoader


class ControlMFoldersLoader(BaseLoader):
    name: ClassVar[str] = "controlm_folders.v1"
    cypher_path: ClassVar[Path | None] = (
        Path(__file__).resolve().parent / "cypher" / "controlm_folders.cypher"
    )
    row_model: ClassVar[type] = ControlMFolderRow
    # BMC is Oracle from day one; flips to 'csv' only when running samples.
    source_label: ClassVar[str] = "oracle"
