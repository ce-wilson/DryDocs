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

# S2 (ADR 0008): the parser and the FileRef shape are vendor-NEUTRAL and now
# live one level up at orchestration/. They are re-exported here unchanged so
# every existing importer keeps working — what moved is where the knowledge
# lives, not what any of it does. `extract_container_command` came with the
# Control-M half into .fields; `build_file_ref` / `classify_role` /
# `canonicalize_path` are the neutral functions bound to the Control-M
# PathDialect in .paths.
from ..shell import FileOp, Invocation, parse_command, pipeline_guid
from .audit_time import normalize_export_timestamp
from .conditions import (
    SCOPE_PREFIXES,
    ConditionScope,
    condition_identity,
    condition_scope,
)
from .facts import route_fact
from .fields import extract_container_command
from .folder_name import ParsedFolderName, parse_folder_name
from .paths import FileRef, build_file_ref, canonicalize_path, classify_role
from .resolver import (
    ResolvedCommandLine,
    ResolvedVariable,
    resolve_command_line,
    resolve_job,
    resolve_layers,
)

# `classify` is re-exported as `classify_pool`: the package already carries
# classify_role / classify_variable, so a bare `classify` reads as ambiguous
# at every call site. The module keeps the short name; the package qualifies it.
from .resource_pool import (
    CATEGORY_LABEL,
    DEFAULT_APP_CODE_RE,
    DEFAULT_RULES,
    PoolCategory,
    PoolClassification,
    PoolRule,
)
from .resource_pool import (
    classify as classify_pool,
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
    # G75 — XML-export field mechanics back-flowed from the company adapter
    "normalize_export_timestamp",
    "ConditionScope",
    "SCOPE_PREFIXES",
    "condition_scope",
    "condition_identity",
    # G76 — Quantitative Resource pool classification (vocabulary is caller-supplied)
    "PoolCategory",
    "PoolRule",
    "PoolClassification",
    "CATEGORY_LABEL",
    "DEFAULT_RULES",
    "DEFAULT_APP_CODE_RE",
    "classify_pool",
]
# NOTE (0002-a §6 borderline): the staging bundle builder (build_staging_bundle /
# build_staging_rows / collect_jobs) is load-cadence-coupled and lives component-side
# as drydocs.staging — core must not re-export it (boundary test enforces).
