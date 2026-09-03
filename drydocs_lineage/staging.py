"""The lineage EXTRACT as one operation (LIN1): run the chain's extractors in hop
order into one :class:`~drydocs_lineage.model.LineageGraph` and stage the result as
one artifact that ``lineage-load`` and ``lineage-review`` read back.

Nine extractors and a curated writer existed for weeks with no verb that ran the
chain and no verb that loaded it - ``lineage-review`` renders a page from a jobs
CSV and writes nothing, and ``write_curated`` was called from no command. This
module is the extract half of the pair; ``drydocs lineage-extract`` in the
composition root is its thin CLI.

Hop order, and what is required:

* hop 1 - the Control-M inventory (jobs CSV or a directory holding one, plus the
  variables CSV for PRECMD/POSTCMD, G60) is REQUIRED: it seeds every process node
  the later hops attach to. Job -> :ETLProcess (DPL pipeline id, Ab Initio pset)
  with INVOKES / USES_ARTIFACT and the CMD_LINE file ops (G12, G14, G15, G97).
* hop 2a - the DPL MAC root (G17: pipeline -> dataset READS_FROM / WRITES_TO on the
  GUID key) and the DPL registry landing zone (G25: pipeline and dataset GUIDs,
  cross-checked against the G15 observations). OPTIONAL.
* hop 3 - the Glue base-table inventory (G41: per-zone placements as PROPERTIES on
  the GUID-keyed asset, no edge). OPTIONAL.

An optional source that is absent is SKIPPED AND COUNTED, never silently absent
(G11's house rule, one level up): the artifact's ``sources`` block names every hop
with ``present`` / ``absent`` and the path it was resolved to, so a reader can tell
"nothing to read" from "never asked".

The ARTIFACT is the graph's ``to_dict()`` plus a header: schema, run id, captured
time, the source paths and their states, the extractor versions (each extractor's
``name``), and the per-extractor coverage ``as_dict()`` - the same provenance
envelope shape the rua bundle stamps on its records (G20). A load names the
extract it came from by run id. Written with ``newline="\\n"`` and sorted keys, so
two runs over the same inputs are byte-identical (the render-determinism rule).

Path DISCIPLINE is the caller's (the CLI): this module takes resolved paths and
never consults the data root, so it stays testable against any directory.
Boundary: imports only ``drydocs_core`` and this package.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from drydocs_lineage.extractors.controlm_inventory import ControlMInventoryExtractor
from drydocs_lineage.extractors.dpl_mac import CLONE_NAME_SEP, DplMacExtractor, parse_clone_folder
from drydocs_lineage.extractors.dpl_registry import DplRegistryExtractor, cross_check
from drydocs_lineage.extractors.glue_tables import GlueTableInventoryExtractor
from drydocs_lineage.model import LineageGraph

ARTIFACT_SCHEMA = "drydocs.lineage-staged.v1"

#: The hops, in the order the chain runs them. ``required`` hops raise when the
#: source is missing; optional hops are skipped and counted.
HOPS: tuple[tuple[str, bool], ...] = (
    ("controlm", True),
    ("dpl_mac", False),
    ("dpl_registry", False),
    ("glue", False),
)


class StagingError(RuntimeError):
    """A REQUIRED source is missing or unreadable. Never raised for an optional one."""


@dataclass
class SourceState:
    """One hop's input, as resolved: where it was looked for and whether it was there."""

    hop: str
    required: bool
    path: str
    present: bool
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "hop": self.hop,
            "required": self.required,
            "path": self.path,
            "present": self.present,
            "note": self.note,
        }


@dataclass
class StagedLineage:
    """The extract's result: the graph, what was read, and how each read went."""

    graph: LineageGraph
    sources: list[SourceState] = field(default_factory=list)
    coverage: dict[str, dict[str, Any]] = field(default_factory=dict)
    extractors: dict[str, str] = field(default_factory=dict)

    def summary_lines(self) -> list[str]:
        lines = []
        for s in self.sources:
            state = "present" if s.present else ("MISSING" if s.required else "absent - skipped")
            lines.append(f"{s.hop:<13} {state:<18} {s.path}")
        lines.append(
            "graph: {processes} processes, {data_assets} data assets, {rels} rels".format(
                **self.graph.stats()
            )
        )
        return lines


def _state(hop: str, required: bool, path: Path | None) -> SourceState:
    """Present = the path exists and, for a directory, holds something. An empty
    declared zone is the normal producer state for the optional hops and reads as
    absent, with the path recorded so the artifact shows where it looked."""
    if path is None:
        return SourceState(hop, required, "", False, "no path given")
    if not path.exists():
        return SourceState(hop, required, str(path), False, "not found")
    if path.is_dir() and not any(path.iterdir()):
        return SourceState(hop, required, str(path), False, "directory is empty")
    return SourceState(hop, required, str(path), True)


def _clone_pipeline_guids(mac_root: Path) -> set[str]:
    """The pipeline-folder GUIDs a promotion clone names (``<name>#<guid>``,
    lowercase = pipeline) - the cross-check's third signal column. Same walk the
    MAC extractor does; read here so the registry pass can be handed a set."""
    candidates = [p for p in mac_root.rglob(f"*{CLONE_NAME_SEP}*") if p.is_dir()]
    candidates.append(mac_root)
    guids: set[str] = set()
    for folder in candidates:
        parsed = parse_clone_folder(folder.name)
        if parsed is not None and parsed.kind == "pipeline":
            guids.add(parsed.guid)
    return guids


def stage_chain(
    *,
    jobs: Path,
    variables: Path | None = None,
    mac_root: Path | None = None,
    registry_root: Path | None = None,
    glue_inventory: Path | None = None,
) -> StagedLineage:
    """Run the chain's extractors, in hop order, into one graph.

    ``jobs`` is the jobs CSV or a directory holding one (REQUIRED - a missing one
    is a :class:`StagingError`). Every other source is optional: a ``None`` or an
    absent path is recorded as such in ``sources`` and the hop is skipped.
    """
    graph = LineageGraph()
    staged = StagedLineage(graph=graph)

    # hop 1 - required
    s_jobs = _state("controlm", True, jobs)
    staged.sources.append(s_jobs)
    if not s_jobs.present:
        raise StagingError(f"the Control-M jobs source is required and is not there: {jobs}")
    s_vars = _state("controlm_variables", False, variables)
    staged.sources.append(s_vars)
    controlm = ControlMInventoryExtractor()
    staged.extractors["controlm"] = controlm.name
    cov = controlm.extract(
        jobs,
        graph,
        variables_csv=variables if s_vars.present else None,
    )
    staged.coverage["controlm"] = cov.as_dict()

    # hop 2a - optional: the MAC root, then the registry (the cross-check reads
    # the clone's GUIDs, so the MAC pass runs first)
    s_mac = _state("dpl_mac", False, mac_root)
    staged.sources.append(s_mac)
    clone_guids: set[str] | None = None
    if s_mac.present:
        mac = DplMacExtractor()
        staged.extractors["dpl_mac"] = mac.name
        staged.coverage["dpl_mac"] = mac.extract(mac_root, graph).as_dict()
        clone_guids = _clone_pipeline_guids(mac_root)
    s_reg = _state("dpl_registry", False, registry_root)
    staged.sources.append(s_reg)
    if s_reg.present:
        reg = DplRegistryExtractor()
        staged.extractors["dpl_registry"] = reg.name
        extract = reg.extract(registry_root)
        staged.coverage["dpl_registry"] = extract.coverage.as_dict()
        staged.coverage["dpl_registry_crosscheck"] = cross_check(
            extract, graph, clone_guids
        ).as_dict()

    # hop 3 - optional
    s_glue = _state("glue", False, glue_inventory)
    staged.sources.append(s_glue)
    if s_glue.present:
        glue = GlueTableInventoryExtractor()
        staged.extractors["glue"] = glue.name
        staged.coverage["glue"] = glue.extract(glue_inventory, graph).as_dict()

    return staged


def artifact_dict(
    staged: StagedLineage,
    *,
    run_id: str,
    acquisition: dict[str, str] | None = None,
    captured_at: datetime | None = None,
) -> dict[str, Any]:
    """The artifact as a plain dict: header + the graph."""
    when = (captured_at or datetime.now(UTC)).astimezone(UTC)
    return {
        "schema": ARTIFACT_SCHEMA,
        "run_id": run_id,
        "captured_at": when.isoformat(timespec="seconds"),
        "acquisition": dict(acquisition or {}),
        "sources": [s.as_dict() for s in staged.sources],
        "extractors": dict(staged.extractors),
        "coverage": staged.coverage,
        "graph": staged.graph.to_dict(),
    }


def write_artifact(
    staged: StagedLineage,
    out_dir: Path,
    *,
    run_id: str,
    acquisition: dict[str, str] | None = None,
    captured_at: datetime | None = None,
) -> Path:
    """Write ``<out_dir>/lineage-<run_id>.json``; deterministic for the same inputs
    and the same ``captured_at``. ``out_dir`` must already exist - creating a
    directory is a data-root decision the caller makes through a declared helper."""
    path = Path(out_dir) / f"lineage-{run_id}.json"
    payload = artifact_dict(staged, run_id=run_id, acquisition=acquisition, captured_at=captured_at)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


def read_artifact(path: Path) -> tuple[LineageGraph, dict[str, Any]]:
    """Read an artifact back: the graph, and the header (everything but the graph)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != ARTIFACT_SCHEMA:
        raise ValueError(f"not a staged lineage artifact (schema {data.get('schema')!r}): {path}")
    graph = LineageGraph.from_dict(data["graph"])
    header = {k: v for k, v in data.items() if k != "graph"}
    return graph, header
