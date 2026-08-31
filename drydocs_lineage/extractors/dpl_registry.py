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

READING THE ACCOUNTING (G135). Every counter on :class:`RegistryCoverage` except
the field census is a SKIP counter: it fires when a record is REJECTED. A record
that parses and stages with five of its six fields empty fires none of them, so a
wrong contract used to look exactly like a right one. The census
(:meth:`RegistryCoverage.contract_lines`) is the half that can see that: per kind,
per contract field, how many records had it present / absent / present-but-empty.
"absent on N of N" is the sentence that says the assumption above is wrong.

That is the whole of G135's remit — the extractor can now REPORT a wrong contract.
It still has no opinion about the right one: amending the field names is clause C1
of the ``dpl-pipeline-registry-contract`` gate (tracker T13), and no spelling here
moves before that signs.
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

#: the ASSUMED contract's optional fields — censused per kind alongside the guid
#: field, so "absent on N of N" is reportable. NOT a mapping and not a lookup
#: order: nothing here changes which key the extractor reads.
_CENSUS_FIELDS = ("version", "active", "ownerSealId", "sealId", "name")

#: active-flag spellings → normalized value (unknown spellings stay "", counted)
_ACTIVE_SPELLINGS = {
    "true": "true",
    "active": "true",
    "y": "true",
    "yes": "true",
    "1": "true",
    "false": "false",
    "inactive": "false",
    "n": "false",
    "no": "false",
    "0": "false",
}


@dataclass(frozen=True)
class RegistryRecord:
    """One registry row, taxonomy-first: classification facts + provenance,
    no meaning."""

    guid: str
    kind: str  # "pipeline" | "dataset"
    version: str = ""
    active: str = ""  # "true" | "false" | "" (unknown — counted)
    seal: str = ""  # record field, else the per-SEAL folder name
    name: str = ""
    source_file: str = ""  # provenance: which export file staged this record
    seal_origin: str = ""  # "record" | "folder" | "" — WHERE the seal came from


@dataclass
class FieldCensus:
    """One contract field's truth across the records of one kind.

    ``absent`` is the finding this class exists for: a field the assumed
    contract names and the real export does not carry. It is not a skip — the
    record staged fine — so nothing else in the accounting can see it."""

    present: int = 0  # key present, carries a value
    empty: int = 0  # key present, carries nothing (null / "" / [])
    absent: int = 0  # key not in the record at all

    @property
    def total(self) -> int:
        return self.present + self.empty + self.absent


@dataclass
class RegistryCoverage:
    """Per-run accounting — every skip is counted BY REASON, never silent."""

    files_read: int = 0
    files_invalid: int = 0  # unreadable JSON / unexpected shape
    files_skipped_by_name: int = 0  # JSON under the root, not an expected name
    skipped_file_names: list[str] = field(default_factory=list)  # distinct, sorted
    pipelines_read: int = 0
    datasets_read: int = 0
    records_no_guid: int = 0  # entry without its guid field — skipped
    records_no_seal: int = 0  # no seal field AND no per-SEAL folder
    seal_from_folder: int = 0  # seal INFERRED from the path, not read off the record
    duplicate_guids: int = 0  # same (kind, guid) again — first wins
    active_unknown: int = 0  # active PRESENT, spelling unrecognized — staged ""
    active_absent: int = 0  # active not in the record at all — a contract question
    #: kind → contract field → :class:`FieldCensus`
    fields: dict[str, dict[str, FieldCensus]] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)

    def census(self, kind: str, field_name: str) -> FieldCensus:
        """The census cell for one (kind, field), created on first touch."""
        return self.fields.setdefault(kind, {}).setdefault(field_name, FieldCensus())

    def summary(self) -> str:
        return (
            f"files={self.files_read} pipelines={self.pipelines_read} "
            f"datasets={self.datasets_read} | skipped: "
            f"invalid={self.files_invalid} by_name={self.files_skipped_by_name} "
            f"no_guid={self.records_no_guid} dupes={self.duplicate_guids} | "
            f"no_seal={self.records_no_seal} "
            f"seal_from_folder={self.seal_from_folder} "
            f"active_absent={self.active_absent} "
            f"active_unknown={self.active_unknown}"
        )

    def contract_lines(self) -> list[str]:
        """The field census, one line per (kind, field), worst first.

        A line reading ``pipeline.version: absent 508/508`` is the report that
        the ASSUMED contract is wrong on that field. Fields fully present are
        reported too — a census that only listed problems could not be read as
        a census."""
        lines: list[str] = []
        for kind in sorted(self.fields):
            for field_name in sorted(self.fields[kind]):
                cell = self.fields[kind][field_name]
                parts = [
                    f"{label} {count}/{cell.total}"
                    for label, count in (
                        ("absent", cell.absent),
                        ("empty", cell.empty),
                        ("present", cell.present),
                    )
                    if count
                ]
                lines.append(f"{kind}.{field_name}: " + ", ".join(parts))
        return lines


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
        self._count_passed_over(root, result)
        return result

    @staticmethod
    def _count_passed_over(root: Path, result: RegistryExtract) -> None:
        """JSON under the root whose NAME the extractor does not recognize.

        Without this a landing zone full of exports named some other way reads
        as an empty directory: ``files=0`` and not one complaint. Which name
        wins — this module's convention or a rename at intake — is the gate's
        question (OQ-8); counting the mismatch is not."""
        passed_over = [
            found.name for found in root.rglob("*.json") if found.name not in _EXPORT_SHAPES
        ]
        result.coverage.files_skipped_by_name = len(passed_over)
        result.coverage.skipped_file_names = sorted(set(passed_over))

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
            # the census runs BEFORE any skip: a record rejected for a missing
            # guid is still evidence about every other field the contract names
            for field_name in (guid_field, *_CENSUS_FIELDS):
                cell = coverage.census(kind, field_name)
                if field_name not in entry:
                    cell.absent += 1
                elif entry[field_name] in (None, "", [], {}):
                    cell.empty += 1
                else:
                    cell.present += 1

            guid = str(entry.get(guid_field) or "").strip()
            if not guid:
                coverage.records_no_guid += 1
                continue
            if (kind, guid) in seen:
                coverage.duplicate_guids += 1
                continue
            seen.add((kind, guid))

            # WHERE the seal came from is staged, not just WHAT it is: under the
            # documented per-SEAL layout the folder IS the seal, and under any
            # other layout this fallback stages a directory name as an
            # identifier. Counting the inference is what tells the two apart
            seal = str(entry.get("ownerSealId") or entry.get("sealId") or "").strip()
            seal_origin = "record" if seal else ""
            if not seal:
                seal = folder_seal if folder_seal != "dpl-registry" else ""
                if seal:
                    seal_origin = "folder"
                    coverage.seal_from_folder += 1
            if not seal:
                coverage.records_no_seal += 1

            # an ABSENT flag and an UNREADABLE flag are the same event — the
            # flag was not read — and each needs its own name: a missing field
            # is a contract question, a strange value is a data question
            raw_active = entry.get("active")
            if isinstance(raw_active, bool):
                active = "true" if raw_active else "false"
            else:
                spelled = str(raw_active or "").strip().lower()
                active = _ACTIVE_SPELLINGS.get(spelled, "")
                if spelled and not active:
                    coverage.active_unknown += 1
                elif "active" not in entry:
                    coverage.active_absent += 1

            result.records.append(
                RegistryRecord(
                    guid=guid,
                    kind=kind,
                    version=str(entry.get("version") or "").strip(),
                    active=active,
                    seal=seal,
                    name=str(entry.get("name") or "").strip(),
                    source_file=export.as_posix(),
                    seal_origin=seal_origin,
                )
            )
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
    observed_pipelines: int = 0  # proc#dpl:{GUID} nodes in the graph
    observed_not_registered: list[str] = field(default_factory=list)
    registered_not_observed: list[str] = field(default_factory=list)
    clone_checked: bool = False  # third column ran (SME 2026-07-23)
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
        node_id[len(_DPL_PROC_PREFIX) :]
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
