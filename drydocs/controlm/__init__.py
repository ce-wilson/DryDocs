"""Control-M domain utilities."""
from .commands import (
    Invocation,
    FileOp,
    extract_container_command,
    parse_command,
)
from .facts import route_fact
from .folder_name import ParsedFolderName, parse_folder_name
from .paths import FileRef, build_file_ref, canonicalize_path, classify_role
from .resolver import ResolvedVariable, resolve_job, resolve_layers
from .staging import build_staging_bundle, build_staging_rows, collect_jobs
from .variable_report import VariableCoverage
from .variables import (
    ClassifiedVariable,
    VariableKind,
    classify_job_variables,
    classify_variable,
)

__all__ = [
    "ParsedFolderName",
    "parse_folder_name",
    "ClassifiedVariable",
    "VariableKind",
    "classify_variable",
    "classify_job_variables",
    "VariableCoverage",
    "ResolvedVariable",
    "resolve_job",
    "resolve_layers",
    # Phase C — command / path / fact parsing
    "Invocation",
    "FileOp",
    "parse_command",
    "extract_container_command",
    "FileRef",
    "build_file_ref",
    "canonicalize_path",
    "classify_role",
    "route_fact",
    "build_staging_bundle",
    "build_staging_rows",
    "collect_jobs",
]
