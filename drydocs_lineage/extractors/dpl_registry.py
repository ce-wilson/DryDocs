"""DPL taxonomy-registry ingestion seam (G25) — the registry ABOVE the pipelines.

The DPL registry DB shows every pipeline/dataset for a SEAL with its version
and active|inactive lifecycle flag, exportable per-SEAL as Swagger JSON (user
disclosure 2026-07-21). This seam ingests those exports TAXONOMY-FIRST — pure
classification, no meaning edges, NO graph writes — into flat staging records,
and emits the GUID cross-check report the groom asked for.

Why it matters (SME, 2026-07-23): the promotion-repo clone's main may LAG
(feature branches pushed, not reliably merged), so the clone folder listing is
a floor on the inventory — this bulk per-SEAL export is the BACKUP discovery
source, and the cross-check turns "the clone might be stale" into measured
lists. Dataflow remains per-pipeline swagger either way (G17's seam).

ASSUMED FIELD CONTRACT (defined by the SYNTHETIC fixtures, adjust when a real
sample validates it — the dpl_mac discipline):

    <root>/<seal>/pipeline_id.json   a list (bare, or under "pipelines") of
        {"pipelineId": "<guid>", "version"?, "active"?, "ownerSealId"?|"sealId"?,
         "name"?}
    <root>/<seal>/dataset_id.json    same shape under "datasets"/bare list,
        keyed by "datasetId"

The SEAL comes from the record field when present, else from the enclosing
per-SEAL folder name (the download is keyed by SEAL); records with neither are
counted. ``active`` normalizes bool / ACTIVE / INACTIVE / Y / N spellings to
``"true"``/``"false"``; anything else stays ``""`` and is counted — the flag is
a THIRD usage signal (beside referenced and present-on-server), staged only:
any conflation with "used" is a G22 clause-(f)/(g) ruling, never decided here.

Cross-check (:func:`cross_check`): registry pipeline GUIDs vs the GUIDs G15
observed on launcher CMD_LINEs (the graph's ``proc#dpl:{GUID}`` identities) —
observed-not-registered and registered-not-observed are each counted AND
listed, never dropped; the registry is also the truth table for which job
families carry pipeline ids at all (the code-fetch tooling gap). An optional
third column takes clone folder GUIDs (:func:`~.dpl_mac.parse_clone_folder`)
so clone lag is measured, not guessed.

Real exports are confidential (Internal, J23) (SEALs + GUIDs + lifecycle state) and
live in the G19 landing zone (``dpl-registry/<seal>/``), never in the repo.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from ..model import LineageGraph

#: per-SEAL export file names (the download tool's spellings)
PIPELINE_ID_JSON = "pipeline_id.json"
DATASET_ID_JSON = "dataset_id.json"

#: file name → (record kind, guid field, wrapper key when not a bare list)
_EXPORT_SHAPES = {
    PIPELINE_ID_JSON: ("pipeline", "pipelineId", "pipelines"),
    DATASET_ID_JSON: ("dataset", "datasetId", "datasets"),
}

#: active-flag spellings → normalized value (unknown spellings stay "", counted)
_ACTIVE_SPELLINGS = {
    "true": "true", "active": "true", "y": "true", "yes": "true", "1": "true",
    "false": "false", "inactive": "false", "n": "false", "no": "false", "0": "false",
}


@dataclass(frozen=True)
class RegistryRecord:
    """One registry row, taxonomy-first: classification facts + provenance,
    no meaning."""

    guid: str
    kind: str            # "pipeline" | "dataset"
    version: str = ""
    active: str = ""     # "true" | "false" | "" (unknown — counted)
    seal: str = ""       # record field, else the per-SEAL folder name
    name: str = ""
    source_file: str = ""  # provenance: which export file staged this record


@dataclass
class RegistryCoverage:
    """Per-run accounting — every skip is counted BY REASON, never silent."""

    files_read: int = 0
    files_invalid: int = 0              # unreadable JSON / unexpected shape
    pipelines_read: int = 0
    datasets_read: int = 0
    records_no_guid: int = 0            # entry without its guid field — skipped
    records_no_seal: int = 0            # no seal field AND no per-SEAL folder
    duplicate_guids: int = 0            # same (kind, guid) again — first wins
    active_unknown: int = 0             # unrecognized active spelling — staged ""

    def as_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        return (
            f"files={self.files_read} pipelines={self.pipelines_read} "
            f"datasets={self.datasets_read} | skipped: "
            f"invalid={self.files_invalid} no_guid={self.records_no_guid} "
            f"dupes={self.duplicate_guids} | "
            f"no_seal={self.records_no_seal} active_unknown={self.active_unknown}"
        )


@dataclass
class RegistryExtract:
    """The staged registry: flat records + the run's coverage."""

    records: list[RegistryRecord] = field(default_factory=list)
    coverage: RegistryCoverage = field(default_factory=RegistryCoverage)

    def guids(self, kind: str) -> set[str]:
        return {r.guid for r in self.records if r.kind == kind}


class DplRegistryExtractor:
    """Per-SEAL Swagger exports → taxonomy-first staging records (no graph,
    no edges — G22 owns everything the signals could mean)."""

    name = "dpl-registry"

    def extract(self, source: str | Path) -> RegistryExtract:
        """``source`` is the registry landing zone (``dpl-registry/`` — one
        subfolder per SEAL) or a single per-SEAL folder. Returns the staged
        :class:`RegistryExtract`; callers report its coverage."""
        root = Path(source)
        result = RegistryExtract()
        seen: set[tuple[str, str]] = set()
        for file_name, (kind, guid_field, wrapper) in _EXPORT_SHAPES.items():
            for export in sorted(root.rglob(file_name)):
                self._read_export(export, kind, guid_field, wrapper, result, seen)
        return result

    # -- one export file --------------------------------------------------------
    def _read_export(
        self,
        export: Path,
        kind: str,
        guid_field: str,
        wrapper: str,
        result: RegistryExtract,
        seen: set[tuple[str, str]],
    ) -> None:
        coverage = result.coverage
        try:
            data = json.loads(export.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            coverage.files_invalid += 1
            return
        if isinstance(data, dict):
            data = data.get(wrapper)
        if not isinstance(data, list):
            coverage.files_invalid += 1
            return
        coverage.files_read += 1

        # the download is keyed by SEAL — the enclosing folder is the fallback
        folder_seal = export.parent.name
        for entry in data:
            if not isinstance(entry, dict):
                coverage.records_no_guid += 1
                continue
            guid = str(entry.get(guid_field) or "").strip()
            if not guid:
                coverage.records_no_guid += 1
                continue
            if (kind, guid) in seen:
                coverage.duplicate_guids += 1
                continue
            seen.add((kind, guid))

            seal = str(entry.get("ownerSealId") or entry.get("sealId") or "").strip()
            if not seal:
                seal = folder_seal if folder_seal != "dpl-registry" else ""
            if not seal:
                coverage.records_no_seal += 1

            raw_active = entry.get("active")
            if isinstance(raw_active, bool):
                active = "true" if raw_active else "false"
            else:
                spelled = str(raw_active or "").strip().lower()
                active = _ACTIVE_SPELLINGS.get(spelled, "")
                if spelled and not active:
                    coverage.active_unknown += 1

            result.records.append(RegistryRecord(
                guid=guid,
                kind=kind,
                version=str(entry.get("version") or "").strip(),
                active=active,
                seal=seal,
                name=str(entry.get("name") or "").strip(),
                source_file=export.as_posix(),
            ))
            if kind == "pipeline":
                coverage.pipelines_read += 1
            else:
                coverage.datasets_read += 1


# -- the GUID cross-check report ------------------------------------------------

@dataclass
class RegistryCrossCheck:
    """Registry vs G15 CMD_LINE observations (and optionally the clone) —
    every disagreement is counted AND listed, never dropped."""

    registered_pipelines: int = 0
    observed_pipelines: int = 0                 # proc#dpl:{GUID} nodes in the graph
    observed_not_registered: list[str] = field(default_factory=list)
    registered_not_observed: list[str] = field(default_factory=list)
    clone_checked: bool = False                 # third column ran (SME 2026-07-23)
    clone_pipelines: int = 0
    clone_not_registered: list[str] = field(default_factory=list)
    registered_not_in_clone: list[str] = field(default_factory=list)  # the lag, measured

    def as_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        base = (
            f"registered={self.registered_pipelines} "
            f"observed={self.observed_pipelines} | "
            f"observed_not_registered={len(self.observed_not_registered)} "
            f"registered_not_observed={len(self.registered_not_observed)}"
        )
        if self.clone_checked:
            base += (
                f" | clone={self.clone_pipelines} "
                f"clone_not_registered={len(self.clone_not_registered)} "
                f"registered_not_in_clone={len(self.registered_not_in_clone)}"
            )
        return base


_DPL_PROC_PREFIX = "proc#dpl:"


def cross_check(
    extract: RegistryExtract,
    graph: LineageGraph,
    clone_guids=None,
) -> RegistryCrossCheck:
    """Join registry pipeline GUIDs against the graph's G15 observations.

    ``clone_guids`` (optional): pipeline-folder GUIDs from a promotion-repo
    clone (``parse_clone_folder``) — the third signal column, so the clone-main
    lag is a measured list instead of a guess. READ-ONLY on the graph."""
    registered = extract.guids("pipeline")
    observed = {
        node_id[len(_DPL_PROC_PREFIX):]
        for node_id in graph.processes
        if node_id.startswith(_DPL_PROC_PREFIX)
    }
    report = RegistryCrossCheck(
        registered_pipelines=len(registered),
        observed_pipelines=len(observed),
        observed_not_registered=sorted(observed - registered),
        registered_not_observed=sorted(registered - observed),
    )
    if clone_guids is not None:
        clone = set(clone_guids)
        report.clone_checked = True
        report.clone_pipelines = len(clone)
        report.clone_not_registered = sorted(clone - registered)
        report.registered_not_in_clone = sorted(registered - clone)
    return report
