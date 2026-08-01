"""Control-M host-topology loader (P3; gate controlm-hosts-topology).

Source: ``psgmgr.CM_HOSTS`` — the replica of the BMC node-group / host-group
membership structure (vendor 6.4.01 poster: CMS_NODGRP) — via OracleAdapter;
CSV via CsvAdapter for samples / dev. Produces :ControlMHostGroup nodes
(keyed ``(data_center, name)``), :ExecutionHost nodes (keyed ``nodeid``
alone — the same host legitimately belongs to many groups), and the
CONTAINS_HOST membership edges (prov:hadMember; participation_type +
last_capture_date ride the edge).

Gate SIGNED OFF 2026-07-09 (config/gate-log.md). Deliberately NOT here:

* DEFINED_ON (group → ControlMServer) — the DC key rule is signed but the
  value-domain verification (probe P3) and the 22-DC-vs-production scope
  call are open gate-log residuals; ``m3_host_group_defined_on`` stays
  ``status: planned``.
* RUNS_ON — the NODE_ID resolution is the separate derived pass
  (:mod:`drydocs.loaders.runs_on_resolution`), run after jobs + hosts.

The object is NOT versioned and carries no USER_DAILY: every extract is a
full snapshot of the membership structure, so the removed-from-source mark
pass sweeps ControlMHostGroup whenever the caller declares full_extract.
(ExecutionHost is deliberately NOT swept — hosts are shared endpoints of
the agent_host edges and the wipe-and-rebuild doctrine covers them.)
"""
from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from drydocs_core.models import ControlMHostRow

from .base import BaseLoader


class ControlMHostsLoader(BaseLoader):
    name: ClassVar[str] = "controlm_hosts.v1"
    source_id: ClassVar[str | None] = "controlm@[db].psgmgr.cm_hosts"
    cypher_path: ClassVar[Path | None] = (
        Path(__file__).resolve().parent / "cypher" / "controlm_hosts.cypher"
    )
    row_model: ClassVar[type] = ControlMHostRow
    source_label: ClassVar[str] = "oracle"
    sweep_label: ClassVar[str | None] = "ControlMHostGroup"
