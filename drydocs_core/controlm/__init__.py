"""Control-M domain utilities.

Definition interchange format
-----------------------------
The target environment (Control-M 9.0.21.300) imports and exports job &
folder *definitions* as **XML**. XML is therefore the **primary source and
sink** for the remediation spin-off: import the **legacy** definition XML,
analyze/normalize it here, and export a **greenfield** definition XML — the
greenfield XML is the artifact handed to the dev team as a Jira (they hold
deploy rights; we author, per SoD).

The Oracle extract (``psgmgr.*``) and the Neo4j graph are the **corroborating
source of truth**: a parsed legacy XML must reconcile with the loaded snapshot,
and a greenfield XML is trusted only once it re-derives the same resolved
behavior (offline equivalence proof).

NOTE: XML is being **phased out** — BMC's SaaS direction replaces it with the
**JSON Automation API** (name-as-key; see ``external/orchestration/bmc-controlm/controlm-api-*.md``).
Keep import/export behind a format-agnostic interface so a JSON backend can be
added when the platform migrates; do not bake XML assumptions into the engine.
"""

from .commands import (
    FileOp,
    Invocation,
    extract_container_command,
    parse_command,
    pipeline_guid,
)
from .facts import route_fact
from .folder_name import ParsedFolderName, parse_folder_name
from .paths import FileRef, build_file_ref, canonicalize_path, classify_role
from .resolver import (
    ResolvedCommandLine,
    ResolvedVariable,
    resolve_command_line,
    resolve_job,
    resolve_layers,
)
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
    "ResolvedCommandLine",
    "ResolvedVariable",
    "resolve_command_line",
    "resolve_job",
    "resolve_layers",
    # Phase C — command / path / fact parsing
    "Invocation",
    "FileOp",
    "parse_command",
    "pipeline_guid",
    "extract_container_command",
    "FileRef",
    "build_file_ref",
    "canonicalize_path",
    "classify_role",
    "route_fact",
]
# NOTE (0002-a §6 borderline): the staging bundle builder (build_staging_bundle /
# build_staging_rows / collect_jobs) is load-cadence-coupled and lives component-side
# as drydocs.staging — core must not re-export it (boundary test enforces).
