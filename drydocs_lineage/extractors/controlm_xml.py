"""Control-M XML definition-export ingestion seam (G47) — folders, jobs, and
ORDERED variables from the environment's real config SoR, taxonomy-first.

The target environment (Control-M 9.0.21.300) imports/exports definitions as
XML (the XML-not-JSON finding; the JSON Automation API is conceptual
reference only). One export carries the job definition AND its folder/job
variables in a single self-consistent snapshot — which is exactly what the
XML-fed resolution chain needs: this extractor STAGES the ordered
definitions; substitution happens exclusively in
:mod:`drydocs_core.controlm.resolver` (guardrail 1 — one resolver, never a
second engine in an adapter), and the G48 ``resolve-cmdline-staging`` step
joins the two. ZERO graph writes anywhere — no LineageGraph parameter exists
in this API; the source entry (``controlm-xml-export``) is ``confirmed:
false`` behind the OPEN psgmgr-vs-XML precedence ruling (guardrail 3).

ASSUMED XML CONTRACT (defined by the SYNTHETIC fixtures, adjust when a real
9.0.21.300 export validates it — the dpl_mac discipline; XML schema docs are
a known reference gap):

- Root element ``DEFTABLE``; folders as ``FOLDER`` / ``SMART_FOLDER``
  (older-format synonyms ``TABLE`` / ``SMART_TABLE`` accepted), named by
  ``FOLDER_NAME`` (synonym ``TABLE_NAME``) with ``DATACENTER``.
- Jobs as ``JOB`` elements (``JOBNAME``, ``TASKTYPE``, ``CMDLINE`` —
  verbatim, never resolved here — ``NODEID``, ``APPLICATION``, ``RUN_AS``),
  at folder level or nested inside ``SUB_FOLDER`` elements
  (``SUB_FOLDER_NAME`` / ``FOLDER_NAME`` / ``JOBNAME`` naming synonyms).
- Variables as ``VARIABLE`` elements (``NAME`` verbatim with its ``%%``
  prefix, ``VALUE``) at folder, sub-folder, and job scope. DOCUMENT ORDER IS
  THE CONTRACT: the resolver's sequential-assignment semantics depend on
  definition order, so ordinals are per-container document positions.
- Elements this seam does not consume (INCOND/OUTCOND/SHOUT/ON/…) are
  tolerated AND counted — present, just not this seam's business.

Real exports are Internal (real folder/job names, command lines, variable
values) and live in the G19 landing zone (``controlm-xml/``, resolver
``drydocs_core.data_root.controlm_xml_dir``), never in the repo. Exports are
arbitrarily-named generic ``.xml``, so no filename-fingerprint tree sweep is
possible (unlike rua bundles / catalog exports) — the landing-zone
convention and the source entry's classification are the guard, and that
limitation is documented rather than papered over.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path

#: folder-level container tags (newer / older format synonyms)
_FOLDER_TAGS = {"FOLDER", "SMART_FOLDER", "TABLE", "SMART_TABLE"}
_SMART_TAGS = {"SMART_FOLDER", "SMART_TABLE"}
_SUBFOLDER_TAGS = {"SUB_FOLDER", "SUBFOLDER"}

#: attribute synonyms, first hit wins
_FOLDER_NAME_ATTRS = ("FOLDER_NAME", "TABLE_NAME")
_SUBFOLDER_NAME_ATTRS = ("SUB_FOLDER_NAME", "FOLDER_NAME", "JOBNAME")


def _attr(elem: ET.Element, *names: str) -> str:
    for name in names:
        value = elem.get(name)
        if value is not None and value.strip():
            return value.strip()
    return ""


@dataclass(frozen=True)
class XmlFolderRecord:
    """One exported folder — pure classification facts + provenance."""

    data_center: str
    folder_name: str
    kind: str                    # "folder" | "smart_folder"
    source_file: str = ""


@dataclass(frozen=True)
class XmlJobRecord:
    """One exported job definition. ``cmd_line`` is VERBATIM — resolution is
    the resolver's job (G46), never the extractor's."""

    data_center: str
    folder_name: str
    subfolder_path: str          # "" at folder level, else "A" / "A/B" / …
    job_name: str
    task_type: str = ""
    cmd_line: str = ""
    node_id: str = ""
    application: str = ""
    run_as: str = ""
    source_file: str = ""


@dataclass(frozen=True)
class XmlVariableRecord:
    """One ordered variable definition. ``ordinal`` is the document position
    within its container — the resolver's sequential-assignment contract."""

    data_center: str
    folder_name: str
    scope: str                   # FOLDER | SUBFOLDER | JOB (resolver spellings)
    container: str               # "" | subfolder path | subfolder path + "/" + job name
    ordinal: int
    name: str                    # verbatim, %% prefix as exported
    value: str
    source_file: str = ""


@dataclass
class XmlDefsCoverage:
    """Per-run accounting — every skip is counted BY REASON, never silent."""

    files_read: int = 0
    files_invalid: int = 0           # unparseable XML / root not DEFTABLE
    folders: int = 0
    jobs: int = 0
    variables: int = 0
    folders_no_name: int = 0         # folder element without a name — skipped
    jobs_no_name: int = 0            # JOB without JOBNAME — skipped
    jobs_no_cmd_line: int = 0        # staged anyway (file watchers etc.) — counted
    variables_no_name: int = 0       # VARIABLE without NAME — skipped
    duplicate_jobs: int = 0          # same (dc, folder, subfolder, name) — first wins
    elements_ignored: int = 0        # tags this seam does not consume — tolerated

    def as_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        return (
            f"files={self.files_read} folders={self.folders} jobs={self.jobs} "
            f"variables={self.variables} | counted: "
            f"no_cmd_line={self.jobs_no_cmd_line} "
            f"dupes={self.duplicate_jobs} ignored={self.elements_ignored} | "
            f"skipped: invalid_files={self.files_invalid} "
            f"folders_no_name={self.folders_no_name} "
            f"jobs_no_name={self.jobs_no_name} "
            f"variables_no_name={self.variables_no_name}"
        )


def _job_container(subfolder_path: str, job_name: str) -> str:
    return f"{subfolder_path}/{job_name}" if subfolder_path else job_name


@dataclass
class XmlDefsExtract:
    """The staged export: flat records + the run's coverage."""

    folders: list[XmlFolderRecord] = field(default_factory=list)
    jobs: list[XmlJobRecord] = field(default_factory=list)
    variables: list[XmlVariableRecord] = field(default_factory=list)
    coverage: XmlDefsCoverage = field(default_factory=XmlDefsCoverage)

    def scope_layers(self, job: XmlJobRecord):
        """The vendor-priority scope chain for one job — EXACTLY the
        ``layers`` shape :func:`drydocs_core.controlm.resolve_command_line`
        takes (folder first, enclosing sub-folders outermost-in, job last).
        This is the G48 join surface: staging hands the ordered definitions
        over; the shared resolver does every substitution."""
        def defs(scope: str, container: str):
            return [
                (v.name, v.value)
                for v in self.variables
                if v.data_center == job.data_center
                and v.folder_name == job.folder_name
                and v.scope == scope
                and v.container == container
            ]

        layers = [("FOLDER", defs("FOLDER", ""))]
        if job.subfolder_path:
            parts = job.subfolder_path.split("/")
            for i in range(1, len(parts) + 1):
                layers.append(
                    ("SUBFOLDER", defs("SUBFOLDER", "/".join(parts[:i])))
                )
        layers.append(
            ("JOB", defs("JOB", _job_container(job.subfolder_path, job.job_name)))
        )
        return layers


class ControlMXmlDefsExtractor:
    """XML definition exports → taxonomy-first staging records (no graph,
    no edges, no substitution — the resolver owns resolution, the
    precedence ruling owns activation)."""

    name = "controlm-xml-export"

    def extract(self, source: str | Path) -> XmlDefsExtract:
        """``source`` is the controlm-xml landing zone or a single export
        file. Returns the staged :class:`XmlDefsExtract`; callers report
        its coverage."""
        root = Path(source)
        files = sorted(root.glob("*.xml")) if root.is_dir() else [root]
        result = XmlDefsExtract()
        seen_jobs: set[tuple[str, str, str, str]] = set()
        for path in files:
            self._read_file(path, result, seen_jobs)
        return result

    # -- one export file -----------------------------------------------------
    def _read_file(
        self,
        path: Path,
        result: XmlDefsExtract,
        seen_jobs: set[tuple[str, str, str, str]],
    ) -> None:
        coverage = result.coverage
        try:
            tree = ET.parse(path)
        except (ET.ParseError, OSError):
            coverage.files_invalid += 1
            return
        root = tree.getroot()
        if root.tag.upper() != "DEFTABLE":
            coverage.files_invalid += 1
            return
        coverage.files_read += 1
        for elem in root:
            tag = elem.tag.upper()
            if tag in _FOLDER_TAGS:
                self._read_folder(elem, tag, path, result, seen_jobs)
            else:
                coverage.elements_ignored += 1

    def _read_folder(
        self,
        elem: ET.Element,
        tag: str,
        path: Path,
        result: XmlDefsExtract,
        seen_jobs: set[tuple[str, str, str, str]],
    ) -> None:
        coverage = result.coverage
        folder_name = _attr(elem, *_FOLDER_NAME_ATTRS)
        if not folder_name:
            coverage.folders_no_name += 1
            return
        data_center = _attr(elem, "DATACENTER")
        result.folders.append(XmlFolderRecord(
            data_center=data_center,
            folder_name=folder_name,
            kind="smart_folder" if tag in _SMART_TAGS else "folder",
            source_file=path.as_posix(),
        ))
        coverage.folders += 1
        self._read_container(
            elem, data_center, folder_name, "", "FOLDER", "",
            path, result, seen_jobs,
        )

    # -- one container level (folder / sub-folder / job) ------------------------
    def _read_container(
        self,
        elem: ET.Element,
        data_center: str,
        folder_name: str,
        subfolder_path: str,
        var_scope: str,
        var_container: str,
        path: Path,
        result: XmlDefsExtract,
        seen_jobs: set[tuple[str, str, str, str]],
    ) -> None:
        coverage = result.coverage
        ordinal = 0
        for child in elem:
            tag = child.tag.upper()
            if tag == "VARIABLE":
                name = _attr(child, "NAME")
                if not name:
                    coverage.variables_no_name += 1
                    continue
                ordinal += 1
                result.variables.append(XmlVariableRecord(
                    data_center=data_center,
                    folder_name=folder_name,
                    scope=var_scope,
                    container=var_container,
                    ordinal=ordinal,
                    name=name,
                    value=_attr(child, "VALUE"),
                    source_file=path.as_posix(),
                ))
                coverage.variables += 1
            elif tag in _SUBFOLDER_TAGS:
                sub_name = _attr(child, *_SUBFOLDER_NAME_ATTRS)
                if not sub_name:
                    coverage.folders_no_name += 1
                    continue
                sub_path = (
                    f"{subfolder_path}/{sub_name}" if subfolder_path else sub_name
                )
                self._read_container(
                    child, data_center, folder_name, sub_path,
                    "SUBFOLDER", sub_path, path, result, seen_jobs,
                )
            elif tag == "JOB":
                self._read_job(
                    child, data_center, folder_name, subfolder_path,
                    path, result, seen_jobs,
                )
            else:
                coverage.elements_ignored += 1

    def _read_job(
        self,
        elem: ET.Element,
        data_center: str,
        folder_name: str,
        subfolder_path: str,
        path: Path,
        result: XmlDefsExtract,
        seen_jobs: set[tuple[str, str, str, str]],
    ) -> None:
        coverage = result.coverage
        job_name = _attr(elem, "JOBNAME")
        if not job_name:
            coverage.jobs_no_name += 1
            return
        key = (data_center, folder_name, subfolder_path, job_name)
        if key in seen_jobs:
            coverage.duplicate_jobs += 1
            return
        seen_jobs.add(key)
        cmd_line = _attr(elem, "CMDLINE")
        if not cmd_line:
            coverage.jobs_no_cmd_line += 1
        result.jobs.append(XmlJobRecord(
            data_center=data_center,
            folder_name=folder_name,
            subfolder_path=subfolder_path,
            job_name=job_name,
            task_type=_attr(elem, "TASKTYPE"),
            cmd_line=cmd_line,
            node_id=_attr(elem, "NODEID"),
            application=_attr(elem, "APPLICATION"),
            run_as=_attr(elem, "RUN_AS"),
            source_file=path.as_posix(),
        ))
        coverage.jobs += 1
        # job-scope variables (and anything else nested under the job)
        self._read_container(
            elem, data_center, folder_name, subfolder_path,
            "JOB", _job_container(subfolder_path, job_name),
            path, result, seen_jobs,
        )
