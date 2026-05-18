"""Control-M folder loader (M3 part 1).

Source: ``psgmgr.CM_DEF_VTAB`` (replicated copy of ``dtsremgr.DEF_VTAB``)
via OracleAdapter; CSV via CsvAdapter for samples / dev. Produces
:JobFolder nodes and the :ControlMServer mesh (deduped on DATA_CENTER).

The loader parses the ``SCHED_TABLE`` folder name into structured
properties (environment / lob / app_code / folder_type) using
:func:`drydocs.controlm.folder_name.parse_folder_name`. The Cypher
template writes those properties onto the :JobFolder node so downstream
queries can filter by environment, LOB, or appcode without re-parsing.

Active filter (``USER_DAILY IS NOT NULL``) lives in the SQL projection.
There is NO ``IS_CURRENT_VERSION`` filter on folders — that column
doesn't exist on ``CM_DEF_VTAB`` (only jobs and conditions are versioned).
"""
from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel

from ..controlm import parse_folder_name
from ..models import ControlMFolderRow
from .base import BaseLoader


class ControlMFoldersLoader(BaseLoader):
    name: ClassVar[str] = "controlm_folders.v1"
    cypher_path: ClassVar[Path | None] = (
        Path(__file__).resolve().parent / "cypher" / "controlm_folders.cypher"
    )
    row_model: ClassVar[type] = ControlMFolderRow
    source_label: ClassVar[str] = "oracle"

    def to_params(self, model: BaseModel) -> dict:
        """Add parsed-folder-name fields to the row params."""
        params = model.model_dump(mode="json")
        parsed = parse_folder_name(params.get("sched_table") or "")
        params["environment_code"] = parsed.environment_code
        params["environment"] = parsed.environment
        params["lob_code"] = parsed.lob_code
        params["lob"] = parsed.lob
        params["app_code"] = parsed.app_code
        params["folder_type_code"] = parsed.folder_type_code
        params["folder_type"] = parsed.folder_type
        params["prefix_recognized"] = parsed.prefix_recognized
        return params
