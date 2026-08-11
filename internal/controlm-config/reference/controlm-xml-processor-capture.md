# Capture — the three company-side Control-M XML processors

**Classification: Internal.** Carries a real incoming landing path, a real folder name with a
SEAL, and source for a module (`controlm_xml_adapter.py`) that exists **only company-side**.
Nothing in this file may leave `internal/`.

- **Captured:** 2026-08-11, desktop, from 19 screenshots (`xml-extractor.png`, `-2` … `-19`).
- **Source:** a company-side Claude session plus VS Code views of three files.
- **Trust: VERBATIM** for the code blocks — transcribed from the screenshots, not from a repo
  read. Line numbers are the editor's. Gaps are marked rather than filled.
- **Why it was taken:** the SME asked whether the producer-side remediation work should reuse
  the company's XML processors or build new. The answer needs the actual code, not a memory of it.

---

## Part A — the company session's own summary (screenshots 1–2, verbatim)

The prompt that opened it:

> I sent you down the wrong path. I meant this file
> "I:\projects\data\rua\incoming\PRSRVG-HLDM-110865-UDM-RFND-ADHOC-PRPL.xml"

The reply, transcribed:

> Here's the picture. Your file is a Control-M `DEFTABLE` XML export (`Folder.xsd` schema) — a
> `SMART_FOLDER` (`PRSRVG-HLDM-110865-UDM-RFND-ADHOC-PRPL`) with 22 `JOB`s, each an ADPS
> data-provision `Command` job whose `CMDLINE` carries `-pipeline <guid>`, plus `VARIABLE`,
> `QUANTITATIVE`, and `OUTCOND` children. Three separate modules process this exact shape, each
> in a different component:

### 1. Live graph ingestion — `controlm_xml_adapter.py`

> The primary processor. `controlm_xml_adapter.py` parses the file once and yields rows in the
> **same dict shape the Oracle SQL projections produce**, so it reuses the entire
> `ingest-controlm` loader chain. It emits four+ streams: folders, jobs, `conditions_in`,
> `conditions_out`, plus quantitatives and M6 contact-metadata parsed from `<JOB DESCRIPTION>`.
>
> Built into it:
>
> - **Active-folder filter** — a `SMART_FOLDER` is ingested only if it has a non-empty
>   `FOLDER_ORDER_METHOD`; manual-order folders are skipped (mirrors the Oracle
>   `USER_DAILY IS NOT NULL` filter).
> - **Folder pseudo-job** (`JOBISN=1`) so folder-level `PL-<folder>-OK` OUTCONDs attach to a real node.
> - **Condition scope** — `PL-` = LOCAL (resolves within `DATACENTER`), `PG-` = GLOBAL; each row
>   carries `data_center` + `scope`.
> - **BMC timestamp normalization** (`20260730082031UTC` → ISO for Neo4j `datetime()`).
>
> Wired to the CLI as `ingest-controlm-xml --path <file>` (`cli.py:2031`). `QUANTITATIVE` rows go
> through `controlm_quantitatives.py` (→ `CONSUMES_FROM_POOL`). Source-registry id
> `controlm:deftable-xml-export`, `confirmed: true` company-side.

### 2. CMDLINE lineage staging — `controlm_xml.py` (G47)

> `controlm_xml.py` is the taxonomy-first extractor that stages folders, jobs, and ordered
> variables — with `CMDLINE` kept verbatim (`-pipeline c34bcf50-…`). This is the seam that feeds
> the G48 `resolve-cmdline-staging` step, where the resolver substitutes `%%DATA_FLOW`,
> `%%SCRIPT_PATH`, etc. and links the `-pipeline <guid>` to the DPL dataset/pipeline registry.
> Zero graph writes; every skip is counted by reason (`XmlDefsCoverage`).

### 3. Remediation format seam — `formats.py` (STUB)

> `XmlDefinitionFormat` in `formats.py` is the intended detect→transform→prove→Jira input format,
> but it's **schema-blocked** (the authoritative `Folder.xsd`/`exportdeftable` output is
> company-side; the vendor doc fetch is 403). Today that path uses the `TranscriptDefinitionFormat`
> YAML fallback instead.

The caveat the session closed on:

> One concrete caveat for your file: the `SMART_FOLDER` element here has **no**
> `FOLDER_ORDER_METHOD` attribute, so module #1 (the live adapter) would **skip it as
> manual-order/inactive** and log an INFO line. Module #2 (lineage staging) would still stage all
> 22 jobs and their pipeline GUIDs. Also note the path — `rua/incoming/` is the rua-bundle landing
> zone; the convention landing zone for these generic XML exports is `controlm-xml/` under
> `DRYDOCS_DATA_ROOT`.

---

## Part B — `drydocs_remediation/formats.py` (screenshots 3–5, lines 1–181)

**Company copy. Compare to producer: this is PRE-G67** — `JobDefinition` here has four fields;
producer's has `description`, `command_line` and `post_command` as well, and producer's file is
226 lines with a `ScopeLayer` type the company copy does not carry.

```python
"""Definition interchange formats — the format-agnostic seam (0002-B §2 step 4).

The target environment imports/exports job & folder *definitions* as XML
(Control-M 9.0.21.300; deprecated-but-supported per the vendor corpus), but the
authoritative XML element schema is NOT yet acquired — see
``external/orchestration/bmc-controlm/controlm-xml-definition-format.md`` (fetch
403-blocked; the ``.dtd`` files / a real ``exportdeftable`` output are company-side).
Until that lands, the wire format here is the **transcript**: the M0 gate-1 fallback
(definitions transcribed from screenshots/monitoring), as a small documented YAML shape.
Everything above this module speaks :class:`DefinitionSet`; only a
:class:`DefinitionFormat` implementation may know a wire shape.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

import yaml

TRANSCRIPT_SCHEMA = "drydocs.remediation.transcript.v1"

#: variable definitions are ordered (name, value) pairs — order matters to the
#: resolver (scope chain / src_ordinal), so transcripts are lists, never maps.
VariableDefs = list[tuple[str, str | None]]


@dataclass
class JobDefinition:
    """One job's definition, format-independent.

    Deliberately job-definition-shaped (not extract-row-shaped — core's models
    stay the home for anything shared with the loaders).
    """

    name: str
    job_type: str | None = None  # e.g. "FileWatcher"
    variables: VariableDefs = field(default_factory=list)
    watch_template: str | None = None  # FileWatcher watched-path template


@dataclass
class FolderDefinition:
    """The folder scope a job resolves under."""

    name: str
    variables: VariableDefs = field(default_factory=list)


@dataclass
class DefinitionSet:
    """A parsed set of Control-M definitions (folders + jobs), format-independent."""

    folders: list[FolderDefinition] = field(default_factory=list)
    jobs: list[JobDefinition] = field(default_factory=list)
    source: str | None = None  # provenance of the loaded artifact (path/export id)

    def folder_variables(self) -> VariableDefs:
        """The folder-scope definitions jobs resolve under (M0: single folder)."""
        out: VariableDefs = []
        for folder in self.folders:
            out.extend(folder.variables)
        return out


class DefinitionFormat(ABC):
    """Load/dump boundary for definition artifacts."""

    @abstractmethod
    def load(self, source: Path) -> DefinitionSet:
        """Parse a definition artifact into a :class:`DefinitionSet`."""

    @abstractmethod
    def dump(self, definitions: DefinitionSet, target: Path) -> Path:
        """Write a :class:`DefinitionSet` as a definition artifact; returns the path."""


def _read_vars(raw: list | None) -> VariableDefs:
    return [
        (str(v["name"]), None if v.get("value") is None else str(v["value"])) for v in (raw or [])
    ]


class TranscriptDefinitionFormat(DefinitionFormat):
    """The M0 gate-1 fallback wire format: a hand-transcribed definition as YAML.

    Shape (schema ``drydocs.remediation.transcript.v1``)::

        schema: drydocs.remediation.transcript.v1
        source: <provenance of the transcription>
        folder:
          name: <folder name>
          variables: [{name: "%%X", value: "..."}, ...]   # ordered
        jobs:
          - name: <job name>
            type: FileWatcher
            watch_template: "%%DIR.%%PFX..."
            variables: [{name: "%%DIR", value: "..."}, ...]  # ordered

    Transcripts of REAL definitions are Internal — they live under ``internal/``
    (or ``internal-local/``), never in tests. Test fixtures are synthetic.
    """

    def load(self, source: Path) -> DefinitionSet:
        data = yaml.safe_load(source.read_text(encoding="utf-8"))
        schema = data.get("schema")
        if schema != TRANSCRIPT_SCHEMA:
            raise ValueError(f"not a {TRANSCRIPT_SCHEMA} transcript: schema={schema!r}")
        folders: list[FolderDefinition] = []
        if data.get("folder"):
            folders.append(
                FolderDefinition(
                    name=str(data["folder"]["name"]),
                    variables=_read_vars(data["folder"].get("variables")),
                )
            )
        jobs = [
            JobDefinition(
                name=str(j["name"]),
                job_type=j.get("type"),
                variables=_read_vars(j.get("variables")),
                watch_template=j.get("watch_template"),
            )
            for j in (data.get("jobs") or [])
        ]
        return DefinitionSet(folders=folders, jobs=jobs, source=data.get("source") or str(source))

    def dump(self, definitions: DefinitionSet, target: Path) -> Path:
        payload = {
            "schema": TRANSCRIPT_SCHEMA,
            "source": definitions.source,
            "folder": (
                {
                    "name": definitions.folders[0].name,
                    "variables": [
                        {"name": n, "value": v} for n, v in definitions.folders[0].variables
                    ],
                }
                if definitions.folders
                else None
            ),
            "jobs": [
                {
                    "name": j.name,
                    "type": j.job_type,
                    "watch_template": j.watch_template,
                    "variables": [{"name": n, "value": v} for n, v in j.variables],
                }
                for j in definitions.jobs
            ],
        }
        target.write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        return target


class XmlDefinitionFormat(DefinitionFormat):
    """Control-M definition XML — the environment's current wire format.

    BLOCKED on schema acquisition: the authoritative element schema (the EM
    ``.dtd`` files or a real ``exportdeftable`` output) is company-side only;
    the vendor doc fetch is 403-blocked (see the acquisition stub in
    ``external/orchestration/bmc-controlm/``). Implementing this from memory
    would ship SYNTHESIZED guesses as vendor ground truth — deliberately not done.
    """

    _BLOCKED = (
        "XML schema acquisition pending — see external/orchestration/bmc-controlm/"
        "controlm-xml-definition-format.md (company-side .dtd / exportdeftable are "
        "the authoritative sources). Use TranscriptDefinitionFormat meanwhile."
    )

    def load(self, source: Path) -> DefinitionSet:
        raise NotImplementedError(self._BLOCKED)

    def dump(self, definitions: DefinitionSet, target: Path) -> Path:
        raise NotImplementedError(self._BLOCKED)
```

---

## Part C — `drydocs_lineage/extractors/controlm_xml.py` (screenshots 6–11, lines 1–375)

**Company copy. Compare to producer: this is PRE-G66** — no `DESCRIPTION` attribute in the
ASSUMED XML CONTRACT block, no `description` field on `XmlFolderRecord` / `XmlJobRecord`, and no
`descriptions_absent` counter on `XmlDefsCoverage`. Producer's file is 455 lines.

Screenshot coverage stops at line 375; anything after is **not captured**.

```python
"""Control-M XML definition-export ingestion seam (G47) — folders, jobs, and
ORDERED variables from the environment's real config SoR, taxonomy-first.

The target environment (Control-M 9.0.21.300) imports/exports definitions as
XML (the XML-not-JSON finding; the JSON Automation API is conceptual
reference only). One export carries the job definition AND its folder/job
variables in a single self-consistent snapshot — which is exactly what the
XML-fed resolution chain needs: this extractor STAGES the ordered
definitions; substitution happens exclusively in
:mod:`drydocs_core.orchestration.controlm.resolver` (guardrail 1 — one resolver, never a
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
    kind: str  # "folder" | "smart_folder"
    source_file: str = ""


@dataclass(frozen=True)
class XmlJobRecord:
    """One exported job definition. ``cmd_line`` is VERBATIM — resolution is
    the resolver's job (G46), never the extractor's."""

    data_center: str
    folder_name: str
    subfolder_path: str  # "" at folder level, else "A" / "A/B" / …
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
    scope: str  # FOLDER | SUBFOLDER | JOB (resolver spellings)
    container: str  # "" | subfolder path | subfolder path + "/" + job name
    ordinal: int
    name: str  # verbatim, %% prefix as exported
    value: str
    source_file: str = ""


@dataclass
class XmlDefsCoverage:
    """Per-run accounting — every skip is counted BY REASON, never silent."""

    files_read: int = 0
    files_invalid: int = 0  # unparseable XML / root not DEFTABLE
    folders: int = 0
    jobs: int = 0
    variables: int = 0
    folders_no_name: int = 0  # folder element without a name — skipped
    jobs_no_name: int = 0  # JOB without JOBNAME — skipped
    jobs_no_cmd_line: int = 0  # staged anyway (file watchers etc.) — counted
    variables_no_name: int = 0  # VARIABLE without NAME — skipped
    duplicate_jobs: int = 0  # same (dc, folder, subfolder, name) — first wins
    elements_ignored: int = 0  # tags this seam does not consume — tolerated

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
        ``layers`` shape :func:`drydocs_core.orchestration.controlm.resolve_command_line`
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
                layers.append(("SUBFOLDER", defs("SUBFOLDER", "/".join(parts[:i]))))
        layers.append(("JOB", defs("JOB", _job_container(job.subfolder_path, job.job_name))))
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

    # -- one export file ------------------------------------------------
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
        result.folders.append(
            XmlFolderRecord(
                data_center=data_center,
                folder_name=folder_name,
                kind="smart_folder" if tag in _SMART_TAGS else "folder",
                source_file=path.as_posix(),
            )
        )
        coverage.folders += 1
        self._read_container(
            elem,
            data_center,
            folder_name,
            "",
            "FOLDER",
            "",
            path,
            result,
            seen_jobs,
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
                result.variables.append(
                    XmlVariableRecord(
                        data_center=data_center,
                        folder_name=folder_name,
                        scope=var_scope,
                        container=var_container,
                        ordinal=ordinal,
                        name=name,
                        value=_attr(child, "VALUE"),
                        source_file=path.as_posix(),
                    )
                )
                coverage.variables += 1
            elif tag in _SUBFOLDER_TAGS:
                sub_name = _attr(child, *_SUBFOLDER_NAME_ATTRS)
                if not sub_name:
                    coverage.folders_no_name += 1
                    continue
                sub_path = f"{subfolder_path}/{sub_name}" if subfolder_path else sub_name
                self._read_container(
                    child,
                    data_center,
                    folder_name,
                    sub_path,
                    "SUBFOLDER",
                    sub_path,
                    path,
                    result,
                    seen_jobs,
                )
            elif tag == "JOB":
                self._read_job(
                    child,
                    data_center,
                    folder_name,
                    subfolder_path,
                    path,
                    result,
                    seen_jobs,
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
        result.jobs.append(
            XmlJobRecord(
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
            )
        )
        coverage.jobs += 1
        # job-scope variables (and anything else nested under the job)
        self._read_container(
            elem,
            data_center,
            folder_name,
            subfolder_path,
            "JOB",
            _job_container(subfolder_path, job_name),
            path,
            result,
            seen_jobs,
        )
```

---

## Part D — `drydocs_core/adapters/controlm_xml_adapter.py` (screenshots 12–19, lines 27–505)

**COMPANY-ONLY.** No producer counterpart exists — verified 2026-08-11 by path check. Neither
does `drydocs_core/adapters/controlm_quantitatives.py` nor
`drydocs_core/orchestration/controlm/resource_pool.py`, both of which it imports.

Lines 1–26 are **not captured** (the module docstring's opening). Screenshot coverage runs
27–505 continuously; whether the file continues past 505 is unknown.

```python
    # downstream dependency derivation works uniformly across job-level
    # and folder-level conditions.

    Condition scope (PL- / PG-)
    ---------------------------
    Per the production support convention only two prefixes occur on
    condition names:

      * ``PL-...`` — LOCAL: resolves within the emitting folder's
        ``DATACENTER``. Two LOCAL conditions with the same name in different
        DCs are distinct.
      * ``PG-...`` — GLOBAL: resolves across DCs by name.

    Each emitted condition row carries ``data_center`` (from the parent
    SMART_FOLDER) and ``scope`` (LOCAL / GLOBAL / UNKNOWN). The Cypher
    upserts derive the MERGE key from these.
    """

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from pathlib import Path
from xml.etree import ElementTree as ET

from ..orchestration.controlm.description_tokens import (
    classify_job_role,
    parse_tokens,
)
from ..orchestration.controlm.resource_pool import classify as classify_pool

LOGGER = logging.getLogger(__name__)


def _scope_from_name(name: str) -> str:
    if name.startswith("PL-"):
        return "LOCAL"
    if name.startswith("PG-"):
        return "GLOBAL"
    return "UNKNOWN"


def _str(elem: ET.Element, attr: str) -> str | None:
    v = elem.get(attr)
    if v is None:
        return None
    v = v.strip()
    return v or None


#: trailing zone token on a BMC timestamp (``...UTC`` / ``...Z`` / ``...+0100``)
_TS_ZONE_RE = re.compile(r"(UTC|Z|[+-]\d{2}:?\d{2})$", re.IGNORECASE)


def _ts(value: str | None) -> str | None:
    """Normalize a BMC compact Control-M timestamp to the ISO contract the
    loaders' ``datetime(replace(x, ' ', 'T'))`` Cypher expects.

    BMC XML exports stamp audit times as ``YYYYMMDDHHMMSS`` optionally suffixed
    with a zone token (``UTC`` / ``Z`` / ``+hhmm``), e.g. ``20250715172540UTC``
    — a form Neo4j ``datetime()`` cannot parse ("Text cannot be parsed to a
    DateTime"). The Oracle projections already deliver ``YYYY-MM-DD HH:MM:SS``,
    so a value that is NOT the compact BMC form is handed through untouched (the
    Cypher's space->T handles it). An 8-digit date-only value becomes midnight.
    Anything else unparseable returns ``None`` so the loaders' existing
    null-guard drops it, rather than a malformed string reaching the driver and
    aborting the whole load.
    """
    if value is None:
        return None
    raw = value.strip()
    if not raw:
        return None
    zone = ""
    m = _TS_ZONE_RE.search(raw)
    if m:
        tok = m.group(0).upper()
        zone = "Z" if tok in ("UTC", "Z") else m.group(0)  # keep a numeric offset verbatim
        raw = raw[: m.start()]
    if raw.isdigit() and len(raw) == 14:  # YYYYMMDDHHMMSS
        return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}T{raw[8:10]}:{raw[10:12]}:{raw[12:14]}{zone}"
    if raw.isdigit() and len(raw) == 8:  # YYYYMMDD (date only)
        return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}T00:00:00{zone}"
    return value  # already ISO/space form, or unknown -> hand through


class ControlMXmlParse:
    """Parses a single Control-M Folder.xsd XML export once and caches
    the active-folder projection in memory.

    Use :meth:`folders`, :meth:`jobs`, :meth:`conditions_in`,
    :meth:`conditions_out` to get sub-adapters bound to this parse.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._parsed = False
        self._folders: list[dict] = []
        self._jobs: list[dict] = []
        self._in: list[dict] = []
        self._out: list[dict] = []
        self._quantitatives: list[dict] = []
        # M6 — contact-metadata streams parsed from <JOB DESCRIPTION="...">.
        self._fw_metadata: list[dict] = []
        self._pub_metadata: list[dict] = []
        # Stats for tests + INFO logs.
        self.skipped_folders: list[tuple[str, int]] = []  # (folder_name, dropped_job_count)

    # ---------------------------------------------------------------- parse
    def parse(self) -> None:
        if self._parsed:
            return
        if not self.path.exists():
            raise FileNotFoundError(f"Control-M XML not found: {self.path}")
        tree = ET.parse(self.path)
        root = tree.getroot()
        for sf in root.findall("SMART_FOLDER"):
            self._handle_smart_folder(sf)
        self._parsed = True
        LOGGER.info(
            "controlm_xml: %s -> %d active folders, %d jobs (incl. pseudo), "
            "%d INCONDs, %d OUTCONDs, %d QUANTITATIVEs, %d FW-meta, %d PUB-meta "
            "(%d folders skipped: no FOLDER_ORDER_METHOD)",
            self.path.name,
            len(self._folders),
            len(self._jobs),
            len(self._in),
            len(self._out),
            len(self._quantitatives),
            len(self._fw_metadata),
            len(self._pub_metadata),
            len(self.skipped_folders),
        )

    # ---------------------------------------------------------------- handlers
    def _handle_smart_folder(self, sf: ET.Element) -> None:
        order_method = _str(sf, "FOLDER_ORDER_METHOD")
        folder_name = _str(sf, "FOLDER_NAME") or _str(sf, "JOBNAME") or "<unknown>"
        if not order_method:
            dropped = len(sf.findall("JOB"))
            self.skipped_folders.append((folder_name, dropped))
            LOGGER.info(
                "controlm_xml: skipping manual-order folder %r (%d JOB elements dropped)",
                folder_name,
                dropped,
            )
            return

        folder_id = _str(sf, "REAL_FOLDER_ID")
        if not folder_id:
            LOGGER.warning(
                "controlm_xml: SMART_FOLDER %r has no REAL_FOLDER_ID; skipping",
                folder_name,
            )
            return
        data_center = _str(sf, "DATACENTER") or ""
        version_serial_raw = _str(sf, "VERSION_SERIAL")
        try:
            version_serial = int(version_serial_raw) if version_serial_raw else None
        except ValueError:
            version_serial = None

        # ---- folder row -------------------------------------------------
        folder_row = {
            "folder_id": folder_id,
            "sched_table": folder_name,
            "data_center": data_center,
            # USER_DAILY in Oracle stores the same string FOLDER_ORDER_METHOD
            # carries in the XML. Project it onto user_daily so the existing
            # Cypher 'active' computation (user_daily IS NOT NULL) works.
            "user_daily": order_method,
            "folder_order_method": order_method,
            "table_status": None,
            "table_type": None,
            "instance_name": None,
            "last_updated": _ts(_str(sf, "CHANGE_DATE")),
            "last_updated_user": _str(sf, "CHANGE_USERID"),
            "capture_date": _ts(_str(sf, "LAST_UPLOAD")),
            "application": _str(sf, "APPLICATION"),
            "sub_application": _str(sf, "SUB_APPLICATION"),
            "parent_folder": _str(sf, "PARENT_FOLDER"),
            "run_as": _str(sf, "RUN_AS"),
            "created_by": _str(sf, "CREATED_BY"),
            "platform": _str(sf, "PLATFORM"),
            "version": _str(sf, "VERSION"),
            "is_current_version": _str(sf, "IS_CURRENT_VERSION"),
            "version_serial": version_serial,
            "rule_based_calendar_relationship": _str(sf, "RULE_BASED_CALENDAR_RELATIONSHIP"),
        }
        self._folders.append(folder_row)

        # ---- folder pseudo-job (JOBISN=1) -------------------------------
        pseudo_job_id = f"{folder_id}.1"
        self._jobs.append(self._build_job_row(sf, folder_id, pseudo_job_id, is_folder_pseudo=True))

        # Folder-level INCOND/OUTCOND (direct children of SMART_FOLDER).
        self._collect_conditions(
            sf, folder_id, pseudo_job_id, data_center, version_serial or 0, direct_only=True
        )

        # ---- real JOBs --------------------------------------------------
        for job in sf.findall("JOB"):
            jobisn = _str(job, "JOBISN")
            if not jobisn:
                continue
            job_id = f"{folder_id}.{jobisn}"
            job_version_raw = _str(job, "VERSION_SERIAL")
            try:
                job_version = int(job_version_raw) if job_version_raw else 0
            except ValueError:
                job_version = 0
            self._jobs.append(self._build_job_row(job, folder_id, job_id, is_folder_pseudo=False))
            self._collect_conditions(
                job, folder_id, job_id, data_center, job_version, direct_only=True
            )
            self._collect_quantitatives(job, folder_id, job_id)
            self._collect_description_metadata(job, folder_id, job_id)

    def _build_job_row(
        self,
        elem: ET.Element,
        folder_id: str,
        job_id: str,
        *,
        is_folder_pseudo: bool,
    ) -> dict:
        version_serial_raw = _str(elem, "VERSION_SERIAL")
        try:
            version_serial = int(version_serial_raw) if version_serial_raw else 0
        except ValueError:
            version_serial = 0
        return {
            "folder_id": folder_id,
            "job_id": job_id,
            "version_serial": version_serial,
            "job_name": _str(elem, "JOBNAME"),
            "parent_table": _str(elem, "PARENT_FOLDER"),
            "application": _str(elem, "APPLICATION"),
            "sub_application": _str(elem, "SUB_APPLICATION"),
            "group_name": None,
            "task_type": _str(elem, "TASKTYPE"),
            "cyclic": _str(elem, "CYCLIC"),
            "cyclic_type": _str(elem, "CYCLIC_TYPE"),
            "cyclic_times_sequence": _str(elem, "CYCLIC_TIMES_SEQUENCE"),
            "cyclic_tolerance": _str(elem, "CYCLIC_TOLERANCE"),
            "ind_cyclic": _str(elem, "IND_CYCLIC"),
            "job_order": None,
            "owner": _str(elem, "RUN_AS"),
            "run_as": _str(elem, "RUN_AS"),
            "author": _str(elem, "CREATED_BY"),
            "node_id": _str(elem, "NODEID"),
            "cmd_line": _str(elem, "CMDLINE"),
            "description": _str(elem, "DESCRIPTION"),
            "memname": _str(elem, "MEMNAME"),
            "priority": _str(elem, "PRIORITY"),
            "critical": _str(elem, "CRITICAL"),
            "active_from": _ts(_str(elem, "ACTIVE_FROM")),
            "active_till": _ts(_str(elem, "ACTIVE_TILL")),
            "end_folder": "Y" if is_folder_pseudo else _str(elem, "END_FOLDER"),
            "is_current_version": _str(elem, "IS_CURRENT_VERSION") or "Y",
            "version_opcode": _str(elem, "VERSION_OPCODE"),
            "version_timestamp": _str(elem, "CHANGE_DATE"),
            "version_user": _str(elem, "CHANGE_USERID"),
            "instance_name": None,
            "capture_date": _ts(_str(elem, "LAST_UPLOAD")),
            "rule_based_calendar_relationship": _str(elem, "RULE_BASED_CALENDAR_RELATIONSHIP"),
            "appl_type": _str(elem, "APPL_TYPE"),
        }

    def _collect_conditions(
        self,
        elem: ET.Element,
        folder_id: str,
        job_id: str,
        data_center: str,
        version_serial: int,
        *,
        direct_only: bool,
    ) -> None:
        # Only collect direct children — never recurse into <JOB> from a
        # SMART_FOLDER pass, otherwise job-level conditions would double-count.
        in_order = 0
        for child in elem:
            tag = child.tag
            if tag == "INCOND":
                name = _str(child, "NAME")
                if not name:
                    continue
                in_order += 1
                self._in.append(
                    {
                        "folder_id": folder_id,
                        "job_id": job_id,
                        "version_serial": version_serial,
                        "condition_name": name,
                        "odate": _str(child, "ODATE"),
                        "and_or": _str(child, "AND_OR"),
                        "parentheses": None,
                        "order_": in_order,
                        "isn": None,
                        "version_opcode": None,
                        "is_current_version": "Y",
                        "capture_date": None,
                        "data_center": data_center,
                        "scope": _scope_from_name(name),
                    }
                )
            elif tag == "OUTCOND":
                name = _str(child, "NAME")
                if not name:
                    continue
                self._out.append(
                    {
                        "folder_id": folder_id,
                        "job_id": job_id,
                        "version_serial": version_serial,
                        "condition_name": name,
                        "odate": _str(child, "ODATE"),
                        "sign": _str(child, "SIGN"),
                        "isn": None,
                        "version_opcode": None,
                        "is_current_version": "Y",
                        "capture_date": None,
                        "data_center": data_center,
                        "scope": _scope_from_name(name),
                    }
                )
            # JOB / VARIABLE / RULE_BASED_CALENDAR / QUANTITATIVE / ON etc are
            # handled (or ignored) by the SMART_FOLDER pass — never here.

    def _collect_quantitatives(
        self,
        job_elem: ET.Element,
        folder_id: str,
        job_id: str,
    ) -> None:
        """Collect <QUANTITATIVE> children of a <JOB>.

        BMC's Quantitative Resource pool — each row means *this job
        consumes `quant` slot(s) from `pool_name`*. ONFAIL / ONOK govern
        whether the slot is released on completion (``R``) or kept (``K``).

        Classification is done here so the loader Cypher receives the
        secondary label + structured tokens flat on the row.
        """
        for q in job_elem.findall("QUANTITATIVE"):
            pool_name = _str(q, "NAME")
            if not pool_name:
                continue
            quant_raw = _str(q, "QUANT")
            try:
                quantity = int(quant_raw) if quant_raw else 1
            except ValueError:
                quantity = 1
            cls = classify_pool(pool_name)
            if cls.category == "unknown":
                LOGGER.warning(
                    "controlm_xml: unclassified ResourcePool %r on job %s",
                    pool_name,
                    job_id,
                )
            self._quantitatives.append(
                {
                    "folder_id": folder_id,
                    "job_id": job_id,
                    "pool_name": pool_name,
                    "quantity": quantity,
                    "on_fail": _str(q, "ONFAIL"),
                    "on_ok": _str(q, "ONOK"),
                    "category": cls.category,
                    "app_code": cls.app_code,
                    "subsystem": cls.subsystem,
                    "kind_suffix": cls.kind_suffix,
                    "secondary_label": cls.secondary_label,
                }
            )

    def _collect_description_metadata(
        self,
        job_elem: ET.Element,
        folder_id: str,
        job_id: str,
    ) -> None:
        """Parse <JOB DESCRIPTION="..."> contact-metadata tokens (M6).

        Classifies the job role from BMC ``TASKTYPE`` + parsed
        ``JOB_ROLE`` token. Emits at most one row per job, on either
        :attr:`_fw_metadata` (FileWatcher) or :attr:`_pub_metadata`
        (Publisher). Jobs that classify as neither produce no row.

        Token parsing is delegated to
        :func:`drydocs.controlm.description_tokens.parse_tokens` so the
        Oracle side-tables (if/when they land) can reuse the same
        parser. Unknown / future tokens log a WARN and are dropped.
        """
        description = _str(job_elem, "DESCRIPTION")
        if not description:
            return
        tokens = parse_tokens(description)
        if not tokens:
            return
        task_type = _str(job_elem, "TASKTYPE")
        role = classify_job_role(task_type, tokens)
        if role == "FILEWATCHER":
            self._fw_metadata.append(
                {
                    "folder_id": folder_id,
                    "job_id": job_id,
                    "delivery_mechanism": tokens.get("DELIVERY_MECHANISM"),
                    "user": tokens.get("USER"),
                    "env": tokens.get("ENV"),
                    "inbound_route": tokens.get("INBOUND_ROUTE"),
                    "outbound_route": tokens.get("OUTBOUND_ROUTE"),
                    "email_dl_l3": tokens.get("EMAIL_DL_L3", []) or [],
                    "email_dl_l2": tokens.get("EMAIL_DL_L2", []) or [],
                    "source_contact": tokens.get("SOURCE_CONTACT", []) or [],
                }
            )
        elif role == "PUBLISHER":
            self._pub_metadata.append(
                {
                    "folder_id": folder_id,
                    "job_id": job_id,
                    "email_dl_l3": tokens.get("EMAIL_DL_L3", []) or [],
                    "email_dl_l2": tokens.get("EMAIL_DL_L2", []) or [],
                    "pdn_dl": tokens.get("PDN_DL", []) or [],
                    # PDN_SNOW_QUEUE: 'NULL' was already collapsed to None by
                    # parse_tokens — preserve that None semantically.
                    "pdn_snow_queue": tokens.get("PDN_SNOW_QUEUE"),
                }
            )
        # Else: tokens present but no role match — likely a non-FW/Pub job
        # carrying ad-hoc keys (e.g. EMAIL_DL_L3 on a generic Command job).
        # Silently drop; m3-verify will flag if this becomes common.

    # ---------------------------------------------------------------- factories
    def folders(self) -> _XmlSubAdapter:
        return _XmlSubAdapter(self, "folders", self._folders)

    def jobs(self) -> _XmlSubAdapter:
        return _XmlSubAdapter(self, "jobs", self._jobs)

    def conditions_in(self) -> _XmlSubAdapter:
        return _XmlSubAdapter(self, "conditions_in", self._in)

    def conditions_out(self) -> _XmlSubAdapter:
        return _XmlSubAdapter(self, "conditions_out", self._out)

    def quantitatives(self) -> _XmlSubAdapter:
        return _XmlSubAdapter(self, "quantitatives", self._quantitatives)

    def filewatcher_metadata(self) -> _XmlSubAdapter:
        return _XmlSubAdapter(self, "filewatcher_metadata", self._fw_metadata)

    def publisher_metadata(self) -> _XmlSubAdapter:
        return _XmlSubAdapter(self, "publisher_metadata", self._pub_metadata)


class _XmlSubAdapter:
    """Adapter view over one cached stream from a :class:`ControlMXmlParse`."""

    def __init__(self, parse: ControlMXmlParse, kind: str, rows: list[dict]) -> None:
        self._parse = parse
        self._rows = rows
        self.name = f"controlm_xml:{parse.path.name}:{kind}"

    def __enter__(self) -> _XmlSubAdapter:
        self._parse.parse()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        return None

    def rows(self) -> Iterator[dict]:
        # Yield a shallow copy so loader-side mutation can't corrupt the cache.
        for row in self._rows:
            yield dict(row)
```

---

## Part E — what the capture settles

### E1. Three processors, three different jobs — and only one is missing here

| Module | Producer | Company | Purpose |
|---|---|---|---|
| `drydocs_core/adapters/controlm_xml_adapter.py` | **ABSENT** | present | XML → Oracle-shaped rows → live graph load |
| `drydocs_core/adapters/controlm_quantitatives.py` | **ABSENT** | present | `QUANTITATIVE` → `CONSUMES_FROM_POOL` |
| `drydocs_core/orchestration/controlm/resource_pool.py` | **ABSENT** | present | resource-pool name classifier |
| `drydocs_lineage/extractors/controlm_xml.py` | present (455 ln) | present, **pre-G66** | taxonomy-first staging, zero graph writes |
| `drydocs_core/orchestration/controlm/description_tokens.py` | present | present | pipe-delimited token parser |
| `drydocs_remediation/formats.py` | present (226 ln) | present, **pre-G67** | detect→transform seam; XML still blocked |

### E2. The screenshots date the company tree independently of the port ledger

Two structural absences pin it, both verifiable rather than inferred:

- Company `controlm_xml.py` has no `DESCRIPTION` in its ASSUMED XML CONTRACT block, no
  `description` field on `XmlFolderRecord` / `XmlJobRecord`, and no `descriptions_absent` counter
  — so it predates **G66**.
- Company `formats.py` `JobDefinition` carries `name` / `job_type` / `variables` /
  `watch_template` only, and the file ends at 181 lines with no `ScopeLayer` — so it predates
  **G67**.

Both land above the last verifiable port (`5417ef10`, 2026-08-07), which is exactly what the SME
reported. The screenshots corroborate the ledger from the other side.

### E3. The adapter is the older ontology, and it shows in three places

The SME's framing — *"the .xml adapter was one of the first attempts to ingest data, use it for
the scaffold not the goal"* — is confirmed by the code itself:

1. **`_collect_description_metadata` encodes the retired token model.** It reads
   `INBOUND_ROUTE` / `OUTBOUND_ROUTE` (retired at C30 — a watcher is inherently inbound), `ENV`
   in its transfer-instance meaning (renamed `FTS_ID` at C30), and `PDN_SNOW_QUEUE` (dropped at
   C30 — no ServiceNow queue belongs in a Control-M object). Its comment even records
   `pdn_snow_queue` being carefully preserved as `None`, which is now a value the standard says
   should not exist.
2. **It flattens the scope ladder away.** `_build_job_row` produces one flat dict per job; folder,
   sub-folder and job scope are not distinguished, and `VARIABLE` elements are not collected at
   all in the captured region. The C30 ladder — the whole point of the greenfield standard — is
   invisible to it. `controlm_xml.py` is the module that models scope, via `scope_layers()`.
3. **Its filter drops the folders remediation most needs.** The `FOLDER_ORDER_METHOD` gate skips
   manual-order folders outright. That is correct for a *live-graph* load (mirror the Oracle
   `USER_DAILY IS NOT NULL` active filter) and wrong for a *conformance* pass, where an inactive
   or hand-built folder is precisely the population carrying drift. The company session's own
   caveat proves it on a real file: the SME's 22-job export has no `FOLDER_ORDER_METHOD`, so the
   adapter would skip the entire folder.

### E4. What is worth taking from it anyway

Three pieces are mechanism, not ontology, and are good regardless of which era they came from:

- **`_ts()`** — BMC compact-timestamp normalization (`YYYYMMDDHHMMSS` + zone token → ISO), with
  the reasoning for handing non-BMC forms through untouched and returning `None` rather than a
  malformed string. Producer has no equivalent.
- **`_scope_from_name()`** — the `PL-` = LOCAL / `PG-` = GLOBAL condition-scope convention, and
  the rule that two LOCAL conditions with the same name in different DCs are distinct.
- **The folder pseudo-job (`JOBISN=1`)** — so folder-level `PL-<folder>-OK` OUTCONDs attach to a
  real node instead of dangling.

### E5. Loose ends

Two closed by the SME on 2026-08-11:

- **`controlm_xml.py` is complete as captured** — the company file ends at line 374, and 375 is
  blank. So the company copy is **374 lines against the producer's 455**, and the 81-line
  difference is G66 plus what followed. Not a capture gap.
- **`resource_pool.py` captured in full** — see Part F, all 130 lines.

Still open:

- Adapter lines 1–26 not captured (the module docstring's opening).
- `cli.py:2031` (`ingest-controlm-xml --path <file>`) not captured — only referenced.
- `controlm_quantitatives.py` not captured.
- The producer source-registry entry `controlm:deftable-xml-export` is `confirmed: false` behind
  the OPEN psgmgr-vs-XML precedence ruling; company-side the session reported it `confirmed: true`.
  That divergence is real and unresolved.

---

## Part F — `drydocs_core/orchestration/controlm/resource_pool.py` (130 lines, complete)

**COMPANY-ONLY.** No producer counterpart. Captured 2026-08-11 from `resource-pool.png` and
`resource-pool-2.png`; the file ends at 130.

```python
"""Classify a Control-M Quantitative Resource pool name into a category.

A `<QUANTITATIVE NAME="...">` element on a `<JOB>` declares that the job
consumes one or more slots from a named pool. Pool names follow a loose
convention exercised across the PRDCL/CAF and PRSRV/MSP exports:

    <APP_CODE>-<SUBSYSTEM>[-<MODIFIER>]*-<KIND>

This module parses the pool name into a structured `PoolClassification`
without any I/O. The categorisation drives the secondary label applied to
the `:ResourcePool` node in Neo4j (`:TargetDatabase`, `:EtlPlatform`,
`:SourcePlatform`, `:HostNode`, `:BusinessApplication`) and exposes the
component tokens (`app_code`, `subsystem`, `kind_suffix`) as node
properties.

Rules are evaluated top-to-bottom; first match wins. See
`/memories/session/plan.md` (Phase A) for the design rationale.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

PoolCategory = Literal[
    "target_database",
    "etl_platform",
    "source_platform",
    "host_node",
    "business_app",
    "unknown",
]

# Secondary Neo4j label per category. `unknown` adds no secondary label.
CATEGORY_LABEL: dict[str, str | None] = {
    "target_database": "TargetDatabase",
    "etl_platform": "EtlPlatform",
    "source_platform": "SourcePlatform",
    "host_node": "HostNode",
    "business_app": "BusinessApplication",
    "unknown": None,
}

# Match rules (regex on the raw pool name). Order matters — first match wins.
_RULES: tuple[tuple[PoolCategory, re.Pattern[str]], ...] = (
    # Oracle Exadata / "ORAC" target databases.
    ("target_database", re.compile(r"(?:^|-)(?:ORAC|EXA)(?:-|$)", re.IGNORECASE)),
    # ETL/orchestration controller pools (launch, compute, generic CTRL).
    ("etl_platform", re.compile(r"-(?:LNCH-CTRL|COMPUTE-CTRL|CTRL)(?:-|$)", re.IGNORECASE)),
    # Source-platform data-distribution throttles (e.g. PRAOC-DAT-VSI,
    # PRDCL-DAT-DCL-VSI). Match -DAT- anywhere AFTER an ETL controller rule.
    ("source_platform", re.compile(r"-DAT(?:-|$)", re.IGNORECASE)),
    # Host / queue-side throttles. Terminal -VSI or -QR.
    ("host_node", re.compile(r"-(?:VSI|QR)$", re.IGNORECASE)),
)

# App-code prefix: 3-5 alphanumeric chars beginning with "PR" at the start.
_APP_CODE_RE = re.compile(r"^(PR[A-Z0-9]{1,3})(?:-|$)")


@dataclass(frozen=True)
class PoolClassification:
    """Structured view of a parsed Quantitative Resource pool name.

    Attributes carry the values the loader writes onto the
    `:ResourcePool` node and onto its `:CONSUMES_FROM_POOL` edges.
    """

    name: str
    category: PoolCategory
    app_code: str | None  # parsed prefix, e.g. "PRDCL"
    subsystem: str | None  # second token if present, e.g. "CAF" or "HLDM"
    kind_suffix: str | None  # terminal token, e.g. "VSI", "EXA", "QR"
    secondary_label: str | None  # multi-label tag for the Cypher MERGE


def classify(pool_name: str) -> PoolClassification:
    """Classify a pool name. Always returns a result.

    Unrecognised names land in the `unknown` category with no secondary
    label; the loader logs a WARN for those so misses surface in CI.
    """
    raw = (pool_name or "").strip()
    if not raw:
        return PoolClassification(
            name="",
            category="unknown",
            app_code=None,
            subsystem=None,
            kind_suffix=None,
            secondary_label=None,
        )

    tokens = raw.split("-")
    # App code: parse from the head if it matches the PR<...> shape.
    app_match = _APP_CODE_RE.match(raw)
    app_code = app_match.group(1) if app_match else None
    subsystem = tokens[1] if len(tokens) >= 2 else None
    kind_suffix = tokens[-1] if len(tokens) >= 2 else None

    category: PoolCategory = "unknown"
    for cat, pattern in _RULES:
        if pattern.search(raw):
            category = cat
            break

    # `business_app` fallback: pure <APP>-<SUBSYSTEM> with no recognised
    # suffix, and we did parse an app_code. (None observed yet, but
    # reserve the slot so the contract is complete.)
    if category == "unknown" and app_code and len(tokens) == 2:
        category = "business_app"

    return PoolClassification(
        name=raw,
        category=category,
        app_code=app_code,
        subsystem=subsystem,
        kind_suffix=kind_suffix,
        secondary_label=CATEGORY_LABEL[category],
    )


__all__ = [
    "PoolCategory",
    "PoolClassification",
    "CATEGORY_LABEL",
    "classify",
]
```

### F1. What reproducing this producer-side has to solve

**The module is a mechanism with company values compiled into it.** `_RULES` names `ORAC`, `EXA`,
`LNCH-CTRL`, `COMPUTE-CTRL`, `CTRL`, `DAT`, `VSI`, `QR`; `_APP_CODE_RE` hardcodes the `PR` prefix;
the docstring's worked examples are real pool names. Several of those tokens are on the
never-outside-`internal/` list. A producer copy must be the **mechanism** — the grammar
`<APP_CODE>-<SUBSYSTEM>[-<MODIFIER>]*-<KIND>`, the ordered first-match-wins table, the
`PoolClassification` shape, the always-returns-a-result contract — with the rule table and the
app-code prefix supplied as **data**, not literals.

Three details are load-bearing and easy to lose in a rewrite:

1. **Rule order is a correctness property, not style.** The `source_platform` rule matches `-DAT-`
   *anywhere*, so it must stay after the ETL-controller rule; a pool that is both reads as ETL.
   The module comments say so, which means a data-driven table has to preserve **ordering**, not
   just membership — a dict keyed by category would silently lose it.
2. **`unknown` is a first-class outcome, not an error.** It returns with `secondary_label=None`
   so the loader adds no label and logs a WARN, which is how misses surface in CI. That is the
   aliases-suggest / values-decide discipline the FACT_REGISTRY already follows.
3. **`business_app` has never fired.** The comment says so outright — *"None observed yet, but
   reserve the slot so the contract is complete."* A producer copy should carry the branch **and**
   its honesty, or drop the branch; keeping it while dropping the comment ships a speculative
   category as though it were observed.

One inconsistency worth noting rather than silently fixing: `subsystem` and `kind_suffix` are both
derived from a token split with `len(tokens) >= 2`, so a two-token name yields
`subsystem == kind_suffix` — the same token in two fields. Whether that is intended is a question
for the reproduction, not something to assume either way.

The docstring also cites `/memories/session/plan.md` (Phase A) for the design rationale — a
company-side path with no producer equivalent. The reproduction needs its own written warrant.
