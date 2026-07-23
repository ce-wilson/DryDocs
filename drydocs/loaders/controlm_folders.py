"""Control-M folder loader (M3 part 1).

Source: ``psgmgr.CM_DEF_VTAB`` (replicated copy of ``dtsremgr.DEF_VTAB``)
via OracleAdapter; CSV via CsvAdapter for samples / dev. Produces
:ControlMFolder nodes and the :ControlMServer mesh (deduped on DATA_CENTER).

The loader parses the ``SCHED_TABLE`` folder name with
:func:`drydocs.controlm.folder_name.parse_folder_name` and forwards ONLY
``app_code`` — the join key for the app-code → BusinessApplication
defined mapping (seal-app-ref gate). SME ruling 2026-07-23 (folder
property diet): the expanded naming-convention decode (environment /
lob / folder_type) stays OFF the node. The convention is the internal
Control-M app-code definition; as node properties it confused users
(``f.lob='Retail'`` collided with the org-taxonomy LOB, and env truth
is the ``data_center`` prefix on :ControlMServer, not folder-name
pos 1). The decode lives in ``folder_name.py``, once.

Active filter (``USER_DAILY IS NOT NULL``) lives in the SQL projection.
There is NO ``IS_CURRENT_VERSION`` filter on folders — that column
doesn't exist on ``CM_DEF_VTAB`` (only jobs and conditions are versioned).
"""
from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel

from drydocs_core.controlm import parse_folder_name
from drydocs_core.models import ControlMFolderRow
from .base import BaseLoader, compute_row_checksum


class ControlMFoldersLoader(BaseLoader):
    name: ClassVar[str] = "controlm_folders.v1"
    cypher_path: ClassVar[Path | None] = (
        Path(__file__).resolve().parent / "cypher" / "controlm_folders.cypher"
    )
    row_model: ClassVar[type] = ControlMFolderRow
    source_label: ClassVar[str] = "oracle"
    # D7: no scope property — a folder-filtered extract cannot declare which
    # folders are gone, so the mark pass runs ONLY when the caller passes
    # full_extract=True (ingest-controlm does when no --folder filter is set).
    sweep_label: ClassVar[str | None] = "ControlMFolder"

    def to_params(self, model: BaseModel) -> dict:
        """Add the app_code join key parsed from the folder name, then the
        delta checksum (doc 06 Phase 2). Only app_code survives the folder
        property diet (SME ruling 2026-07-23) — see the module docstring.
        prefix_recognized rides for the checksum only (parse-quality
        signal; never a node property). Both are deterministic functions
        of sched_table, so including them doesn't destabilize the hash."""
        params = model.model_dump(mode="json")
        parsed = parse_folder_name(params.get("sched_table") or "")
        params["app_code"] = parsed.app_code
        params["prefix_recognized"] = parsed.prefix_recognized
        params["row_checksum"] = compute_row_checksum(params)
        return params
