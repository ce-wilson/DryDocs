"""Staged Control-M XML → remediation :class:`DefinitionSet` (G67).

WHY A BRIDGE AND NOT A LOADER. This bridge adapts a STAGED extract (the
lineage component's ``controlm_xml`` extractor output, consumed via the
protocols below) into a curated ``DefinitionSet``. It predates ``xml_io``,
which now reads definition XML directly inside this component — so the
schema-acquisition blocker this docstring used to describe is fully retired:
reading was solved twice over, and emission goes through ``xml_io``'s
byte-splicing ``write`` (which never authors XML, so it never needed
``Folder.xsd`` — the acquired schema's remaining role is validating emitted
files, per ``module-requirements.md``). The bridge stays because a staged
extract is still a legitimate second source: anything satisfying the
protocols adapts, XML or not.

WHY THERE IS NO IMPORT OF THE EXTRACTOR. Components may not import each other
(``tests/unit/test_module_boundary.py``, group ``remediation``), and that rule
is right: remediation depending on lineage would make the fix engine
unusable without the ingestion component. So this module declares the SHAPE it
needs as protocols and takes anything that satisfies them. The extractor is
one such thing; a test fixture is another; a future JSON-API extract would be
a third. The composition root does the wiring — that is what entrypoints are
for. Dependency inversion, not a boundary exception.

The protocols below are deliberately the minimum: this module owns no XML
knowledge. Element names, attribute synonyms and the ASSUMED CONTRACT stay
with whoever parses, and the scope chain is TAKEN from the staged extract
rather than recomputed, because two implementations of Control-M scope
resolution would be the same mistake as two resolvers.

READ ONLY. Nothing here writes a graph, a file, or the source extract.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .formats import DefinitionSet, FolderDefinition, JobDefinition, ScopeLayer

#: resolver spelling for the scope that sits between folder and job
SUBFOLDER_SCOPE = "SUBFOLDER"
FOLDER_SCOPE = "FOLDER"


@runtime_checkable
class StagedVariable(Protocol):
    """One ordered variable definition, located by scope + container."""

    data_center: str
    folder_name: str
    scope: str  # FOLDER | SUBFOLDER | JOB
    container: str
    name: str
    value: str


@runtime_checkable
class StagedFolder(Protocol):
    data_center: str
    folder_name: str
    description: str
    notification_tags: tuple[str, ...]


@runtime_checkable
class StagedJob(Protocol):
    data_center: str
    folder_name: str
    subfolder_path: str
    job_name: str
    task_type: str
    cmd_line: str
    description: str
    post_command: str
    watch_template: str
    notification_tags: tuple[str, ...]
    source_file: str


class StagedExtract(Protocol):
    """What a staged definition export must offer to be adaptable.

    ``scope_layers`` is the load-bearing member: it returns the vendor-priority
    chain for one job, widest first, and it is the one authority on how
    sub-folders nest.
    """

    folders: list  # Sequence[StagedFolder]
    jobs: list  # Sequence[StagedJob]
    variables: list  # Sequence[StagedVariable]

    def scope_layers(self, job) -> list: ...


def to_definition_set(extract: StagedExtract, source: str | None = None) -> DefinitionSet:
    """Adapt one staged extract into the shape the detectors consume.

    Sub-folders become :class:`FolderDefinition` entries with
    ``scope="SUBFOLDER"``, reconstructed from the variable rows' ``container``:
    a staged extract carries no record per sub-folder — it is a variable
    container — and minting one here would mean inventing its provenance too.
    """
    definitions = DefinitionSet(source=source or _source_of(extract))

    for record in extract.folders:
        definitions.folders.append(
            FolderDefinition(
                name=record.folder_name,
                variables=_variables_at(
                    extract, record.data_center, record.folder_name, FOLDER_SCOPE, ""
                ),
                scope=FOLDER_SCOPE,
                description=record.description,
                notification_tags=tuple(record.notification_tags),
            )
        )

    for data_center, folder_name, path in _subfolder_containers(extract):
        definitions.folders.append(
            FolderDefinition(
                name=f"{folder_name}/{path}",
                variables=_variables_at(
                    extract, data_center, folder_name, SUBFOLDER_SCOPE, path
                ),
                scope=SUBFOLDER_SCOPE,
            )
        )

    for job in extract.jobs:
        chain: list[ScopeLayer] = [
            (scope, _container_label(scope, job), list(defs))
            for scope, defs in extract.scope_layers(job)
        ]
        definitions.jobs.append(
            JobDefinition(
                name=job.job_name,
                job_type=job.task_type or None,
                variables=list(chain[-1][2]) if chain else [],
                watch_template=job.watch_template or None,
                description=job.description,
                command_line=job.cmd_line,
                post_command=job.post_command,
                notification_tags=tuple(job.notification_tags),
                subfolder_path=job.subfolder_path,
                scope_chain=chain,
            )
        )

    return definitions


def _variables_at(
    extract: StagedExtract, data_center: str, folder: str, scope: str, container: str
) -> list[tuple[str, str | None]]:
    """Ordered (name, value) pairs for one scope+container. Document order is
    preserved because the staged list preserves it — the resolver's
    sequential-assignment contract depends on it."""
    return [
        (v.name, v.value)
        for v in extract.variables
        if v.data_center == data_center
        and v.folder_name == folder
        and v.scope == scope
        and v.container == container
    ]


def _container_label(scope: str, job: StagedJob) -> str:
    """Display/provenance label for a scope layer. ``scope_layers`` returns
    ``(scope, defs)`` without a container, and the label is never used for
    resolution — the DEFINITIONS are."""
    if scope == FOLDER_SCOPE:
        return job.folder_name
    if scope == SUBFOLDER_SCOPE:
        return job.subfolder_path
    return job.job_name


def _subfolder_containers(extract: StagedExtract) -> list[tuple[str, str, str]]:
    """Distinct (data centre, folder, sub-folder path) triples in first-seen
    order. Ordered, not a set: stable output is worth more than the lookup."""
    seen: list[tuple[str, str, str]] = []
    for variable in extract.variables:
        if variable.scope != SUBFOLDER_SCOPE:
            continue
        key = (variable.data_center, variable.folder_name, variable.container)
        if key not in seen:
            seen.append(key)
    return seen


def _source_of(extract: StagedExtract) -> str:
    """Provenance for the adapted set: the export file(s) behind it."""
    files: list[str] = []
    for record in extract.jobs:
        if record.source_file and record.source_file not in files:
            files.append(record.source_file)
    return ", ".join(files) if files else "controlm-xml-export"
