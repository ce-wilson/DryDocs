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


#: one link of the resolution chain: (scope, container, ordered definitions).
#: Scope spellings match the resolver's — FOLDER | SUBFOLDER | JOB — and the
#: list is ordered WIDEST FIRST, so the narrowest wins on a duplicate name
#: (BMC resolution order: local, then SMART folder, then global).
ScopeLayer = tuple[str, str, VariableDefs]


@dataclass
class JobDefinition:
    """One job's definition, format-independent.

    Deliberately job-definition-shaped (not extract-row-shaped — core's models
    stay the home for anything shared with the loaders).
    """

    name: str
    job_type: str | None = None  # e.g. "FileWatcher"
    #: the folder's DATACENTER, inherited — folder/job names are only unique
    #: PER DATA CENTER (the environment runs several), so a definition without
    #: its DC is only half an identity. "" when the format cannot express it
    #: (the M0 transcript shape).
    data_center: str = ""
    variables: VariableDefs = field(default_factory=list)
    watch_template: str | None = None  # FileWatcher watched-path template
    #: DESCRIPTION verbatim — the description-metadata carrier
    description: str = ""
    #: CMDLINE verbatim — never resolved here
    command_line: str = ""
    #: post-execution command verbatim
    post_command: str = ""
    #: notification tags present on this job (REQ-2 evidence)
    notification_tags: tuple[str, ...] = ()
    #: "" at folder level, else "A" / "A/B" — which sub-folder holds the job
    subfolder_path: str = ""
    #: the full ordered resolution chain, widest first, INCLUDING this job's
    #: own definitions as the last layer. Empty when the format cannot express
    #: scope (a single-folder M0 transcript) — callers fall back to
    #: :meth:`DefinitionSet.folder_variables` plus ``variables``.
    scope_chain: list[ScopeLayer] = field(default_factory=list)


@dataclass
class FolderDefinition:
    """A scope a job resolves under — a folder or a sub-folder."""

    name: str
    #: DATACENTER verbatim ("" when the format cannot express it) — the other
    #: half of the folder's identity; names repeat across data centers.
    data_center: str = ""
    variables: VariableDefs = field(default_factory=list)
    #: "FOLDER" | "SUBFOLDER" — sub-folders resolve between folder and job
    scope: str = "FOLDER"
    #: DESCRIPTION verbatim
    description: str = ""
    #: notification tags at this container's own level (REQ-2 evidence)
    notification_tags: tuple[str, ...] = ()


@dataclass
class DefinitionSet:
    """A parsed set of Control-M definitions (folders + jobs), format-independent."""

    folders: list[FolderDefinition] = field(default_factory=list)
    jobs: list[JobDefinition] = field(default_factory=list)
    source: str | None = None  # provenance of the loaded artifact (path/export id)

    def folder_variables(self) -> VariableDefs:
        """FOLDER-scope definitions only. Sub-folders now share ``folders``
        (distinguished by ``scope``) and are deliberately excluded here: they
        resolve BETWEEN folder and job, so folding them in would flatten the
        chain this method's callers assume is one layer."""
        out: VariableDefs = []
        for folder in self.folders:
            if folder.scope == "FOLDER":
                out.extend(folder.variables)
        return out

    def resolution_chain(self, job: JobDefinition) -> list[ScopeLayer]:
        """The ordered scope chain for ``job``, widest first.

        Prefers the chain the format supplied (the XML bridge carries the
        extractor's own ``scope_layers``, which is the one authority on
        sub-folder nesting). Falls back to folder-then-job for formats that
        cannot express sub-folders — the M0 transcript shape."""
        if job.scope_chain:
            return job.scope_chain
        return [
            ("FOLDER", "", self.folder_variables()),
            ("JOB", job.name, job.variables),
        ]


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
        # J49: LF. The tracked transcripts under internal/remediation/m0/ are
        # hand-authored INPUTS to load() (they carry a prose header this dump
        # never writes), so this writer produces no committed surface; LF keeps
        # a dumped round-trip byte-comparable across machines.
        target.write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
            newline="\n",
        )
        return target


class XmlDefinitionFormat(DefinitionFormat):
    """Control-M definition XML — the environment's current wire format.

    ``load`` delegates to ``xml_io.load_document`` + its position-faithful
    projection: reading needs no vendor schema, only located bytes. ``dump``
    remains deliberately unimplemented AT THIS SEAM — not because emission is
    blocked (``xml_io.render`` splices the vendor's own file and never authors
    XML), but because this interface cannot express the §XML contract: a
    ``DefinitionSet`` alone carries no original document to splice into and no
    approved change-set to attribute edits to, so any ``dump(definitions)``
    here would be exactly the regenerate-from-the-model emission that §XML
    rule 1 forbids. Emission goes through ``xml_io.write(doc, script)``.
    """

    _DUMP_SEAM = (
        "emitting Control-M XML from a bare DefinitionSet would regenerate the "
        "document from the model (forbidden by fix-package.md §XML rule 1). "
        "Emission is xml_io.write(original_document, edit_script) — parse the "
        "original, splice the approved changes, never re-serialize."
    )

    def load(self, source: Path) -> DefinitionSet:
        from . import xml_io  # local: xml_io imports this module's dataclasses

        return xml_io.to_definition_set(xml_io.load_document(source))

    def dump(self, definitions: DefinitionSet, target: Path) -> Path:
        raise NotImplementedError(self._DUMP_SEAM)
