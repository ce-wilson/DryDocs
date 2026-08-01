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
    job_type: str | None = None            # e.g. "FileWatcher"
    variables: VariableDefs = field(default_factory=list)
    watch_template: str | None = None      # FileWatcher watched-path template


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
    return [(str(v["name"]), None if v.get("value") is None else str(v["value"]))
            for v in (raw or [])]


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
            folders.append(FolderDefinition(
                name=str(data["folder"]["name"]),
                variables=_read_vars(data["folder"].get("variables")),
            ))
        jobs = [
            JobDefinition(
                name=str(j["name"]),
                job_type=j.get("type"),
                variables=_read_vars(j.get("variables")),
                watch_template=j.get("watch_template"),
            )
            for j in (data.get("jobs") or [])
        ]
        return DefinitionSet(folders=folders, jobs=jobs,
                             source=data.get("source") or str(source))

    def dump(self, definitions: DefinitionSet, target: Path) -> Path:
        payload = {
            "schema": TRANSCRIPT_SCHEMA,
            "source": definitions.source,
            "folder": (
                {
                    "name": definitions.folders[0].name,
                    "variables": [{"name": n, "value": v}
                                  for n, v in definitions.folders[0].variables],
                }
                if definitions.folders else None
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
