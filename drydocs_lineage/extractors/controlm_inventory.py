"""Control-M inventory extractor — the lineage seed (re-homed, ADR 0002-C §4).

Reads a CSV export of ``psgmgr.CM_DEF_VJOB`` (the projection in the load side's
``controlm_jobs.sql``) and turns each current-version job into a
:class:`~drydocs_lineage.model.ProcessNode` carrying the authoritative
job/cmd/host/run_as/folder/application. It then parses each CMD_LINE — via the
SHARED core parser, ``drydocs_core.controlm.parse_command`` (the depgraph fork is
gone; 0002-C §3/G8) — to find the *next lower dependency*, the script/executable the
job launches, and links it with an ``INVOKES`` rel (m3_invokes, prov:used). Shared
scripts invoked from multiple folders collapse to one child node with multiple
INVOKES — exactly the lineage we want.

Division of labor preserved (0002-C §4): the Oracle pull + pydantic row models stay
in core/load; lineage consumes the CSV projection.

Column contract (CSV header == controlm_jobs.sql aliases):
    job_id, version_serial, folder_id, job_name, parent_table, application,
    owner, author, node_id, cmd_line, is_current_version, ...   (extras ignored)
Mapping → ProcessNode:
    node_id→host   owner→run_as   job_name→name   parent_table→folder
    application→application   cmd_line→command
"""
from __future__ import annotations

import csv
from pathlib import Path

from drydocs_core.controlm import parse_command

from ..model import LineageGraph, ProcessNode, process_id

# header tokens that identify a Control-M jobs CSV when searching a directory
_JOBS_CSV_HINTS = ("job_name", "cmd_line", "node_id")


def _basename(path: str) -> str:
    return path.replace("\\", "/").rstrip("/").split("/")[-1] or path


class ControlMInventoryExtractor:
    """CSV export → ProcessNodes + INVOKES candidates (curation decides the rest)."""

    name = "controlm-inventory"

    def extract(self, source: str | Path, into: LineageGraph) -> None:
        """``source`` is the jobs CSV (preferred) or a directory to search."""
        csv_path = self._resolve_csv(Path(source))
        if csv_path is None:
            return  # nothing to do — no Control-M export present
        with csv_path.open(newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                self._row(row, into)

    # -- internals --------------------------------------------------------------
    def _resolve_csv(self, root: Path) -> Path | None:
        if root.is_file() and root.suffix.lower() == ".csv":
            return root
        if root.is_dir():
            for cand in sorted(root.glob("*.csv")):
                try:
                    header = cand.open(encoding="utf-8-sig").readline().lower()
                except OSError:
                    continue
                if all(h in header for h in _JOBS_CSV_HINTS):
                    return cand
        return None

    def _row(self, row: dict, into: LineageGraph) -> None:
        # only current-version definitions (CSV may already be filtered)
        icv = (row.get("is_current_version") or "").strip()
        if icv and icv != "1":
            return
        job_name = (row.get("job_name") or "").strip()
        if not job_name:
            return
        folder = (row.get("parent_table") or row.get("folder_id") or "").strip()
        folder_id = (row.get("folder_id") or "").strip()
        job_id = (row.get("job_id") or "").strip()
        cmd = (row.get("cmd_line") or "").strip()

        # stable identity = the graph's ControlMJob NODE KEY composite
        # (folder_id, job_id); fall back to folder/job_name for hand-made CSVs.
        key = f"{folder_id}.{job_id}" if (folder_id and job_id) else f"{folder}/{job_name}"
        jid = process_id("controlm_job", key)
        into.add_process(ProcessNode(
            node_id=jid,
            kind="controlm_job",
            name=job_name,
            command=cmd,
            host=(row.get("node_id") or "").strip(),
            run_as=(row.get("owner") or "").strip(),
            folder=folder,
            application=(row.get("application") or "").strip(),
        ))

        for inv in parse_command(cmd).invocations:
            target = inv.target
            if not target:
                continue
            kind = inv.invocation_type.lower()
            cid = process_id(kind, target)
            into.add_process(ProcessNode(
                node_id=cid,
                kind=kind,
                name=_basename(target),
                path=inv.script_path or inv.executable_path or "",
            ))
            into.add_rel(jid, "INVOKES", cid)
