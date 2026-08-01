"""Build STG_* staging rows from classified + resolved variables.

Phase A delivered STG_VARIABLE / STG_PARSE_QUALITY. Phase C adds the
technical-object tables — STG_INVOCATION, STG_FILE_OP, STG_FILE_REF,
STG_NOTIFICATION, STG_APP_FACT — by routing each classified+resolved
variable to the right handler:

  EMBEDDED_SHELL (PRECMD/POSTCMD)   -> commands.parse_command
  PLUGIN_NS FileWatch *FILE_PATH    -> paths.build_file_ref (WATCH_INPUT)
  PLUGIN_NS UCM *CONTAINER_OVERRIDES-> commands.extract_container_command
  SEMANTIC_FACT                     -> facts.route_fact
  LITERAL / VAR_REF path-like value -> paths.build_file_ref (role by name)

Row dict keys match controlm_staging_ddl.sql columns exactly so the
emitted CSVs load without mapping. Variant rows (env-triplet expansions)
are still emitted on STG_VARIABLE only.
"""
from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field

from drydocs_core.controlm.commands import extract_container_command, parse_command
from drydocs_core.controlm.facts import route_fact
from drydocs_core.controlm.paths import build_file_ref
from drydocs_core.controlm.resolver import ResolvedVariable, resolve_job
from drydocs_core.controlm.variables import ClassifiedVariable, VariableKind, classify_job_variables
from drydocs_core.models import ControlMVariableRow

_ENV_NAME_TO_LETTER = {"Development": "D", "QA": "Q", "Production": "P"}


@dataclass
class JobDefinitions:
    """All variable definitions of one (data_center, folder, job)."""

    data_center: str
    folder_id: str
    job_id: str
    is_folder_header: bool
    defs: list[tuple[str, str | None]] = field(default_factory=list)


@dataclass
class StagingBundle:
    """All STG_* row lists from one normalizer run."""

    variable: list[dict] = field(default_factory=list)
    parse_quality: list[dict] = field(default_factory=list)
    invocation: list[dict] = field(default_factory=list)
    file_op: list[dict] = field(default_factory=list)
    file_ref: list[dict] = field(default_factory=list)
    notification: list[dict] = field(default_factory=list)
    app_fact: list[dict] = field(default_factory=list)


def collect_jobs(rows: Iterable[ControlMVariableRow]) -> dict[tuple, JobDefinitions]:
    """Group validated extract rows per job, preserving definition order.

    Folder-scope detection: ``var_scope`` from the formal projection when
    present, else the smart-folder header heuristic (JOB_ID = 1) for raw
    SQL Developer exports.
    """
    jobs: dict[tuple, JobDefinitions] = {}
    for row in rows:
        dc = row.data_center or "UNKNOWN"
        key = (dc, row.folder_id, row.job_id)
        jd = jobs.get(key)
        if jd is None:
            is_header = row.var_scope == "FOLDER" or (
                row.var_scope is None and row.job_id == "1"
            )
            jd = JobDefinitions(dc, row.folder_id, row.job_id, is_header)
            jobs[key] = jd
        jd.defs.append((row.var_name, row.var_value))
    return jobs


def _env_letter(cv: ClassifiedVariable) -> str | None:
    return cv.env_candidate if cv.env_tag else None


def _job_keys(jd: JobDefinitions) -> dict:
    return {"data_center": jd.data_center, "folder_id": jd.folder_id, "job_id": jd.job_id}


def _stg_variable_row(jd, run_id, ordinal, cv, rv) -> dict:
    unresolved = list(rv.unresolved) + list(rv.external_refs)
    return {
        "run_id": run_id,
        **_job_keys(jd),
        "src_ordinal": ordinal,
        "var_scope": "FOLDER" if jd.is_folder_header else "JOB",
        "var_name": cv.raw_name,
        "raw_value": cv.raw_value,
        "resolved_value": rv.resolved_value,
        "var_kind": cv.kind.value,
        "env_tag": _env_letter(cv),
        "is_fully_resolved": "Y" if rv.is_fully_resolved else "N",
        "resolution_depth": rv.resolution_depth,
        "unresolved_tokens": ",".join(unresolved) or None,
    }


def _route_technical_objects(
    jd: JobDefinitions,
    run_id: str,
    cv: ClassifiedVariable,
    rv: ResolvedVariable,
    counters: dict,
    bundle: StagingBundle,
) -> None:
    """Emit STG_INVOCATION / FILE_OP / FILE_REF / NOTIFICATION / APP_FACT
    rows for one classified+resolved variable."""
    base = {"run_id": run_id, **_job_keys(jd)}
    value = rv.resolved_value

    if cv.kind is VariableKind.EMBEDDED_SHELL:
        source = "PRECMD" if "PRE" in cv.name.upper() else "POSTCMD"
        _emit_command(base, source, value, cv.raw_name, counters, bundle)
        return

    if cv.kind is VariableKind.PLUGIN_NS and cv.plugin_namespace == "FileWatch":
        if cv.name.upper().endswith("FILE_PATH"):
            ref = build_file_ref(cv.name, value, source_field=cv.raw_name,
                                 role="WATCH_INPUT")
            if ref:
                bundle.file_ref.append({**base, **_file_ref_cols(ref)})
        return

    if cv.kind is VariableKind.PLUGIN_NS and cv.plugin_namespace == "UCM":
        if "CONTAINER_OVERRIDES" in cv.name.upper():
            inner = extract_container_command(value)
            if inner:
                _emit_command(base, "CONTAINER_OVERRIDE", inner, cv.raw_name,
                              counters, bundle, default_type="ECS_TASK")
        return

    if cv.kind is VariableKind.SEMANTIC_FACT:
        facts, notes = route_fact(cv, value)
        for f in facts:
            bundle.app_fact.append({
                **base, "fact_type": f.fact_type, "fact_value": f.fact_value,
                "environment": f.environment, "source_var": f.source_var,
            })
        for note in notes:
            bundle.notification.append({
                **base, "channel": note.channel, "address": note.address,
                "source_var": note.source_var,
            })
        return

    if cv.kind in (VariableKind.LITERAL, VariableKind.VAR_REF):
        ref = build_file_ref(cv.name, value, source_field=cv.raw_name)
        if ref:
            bundle.file_ref.append({**base, **_file_ref_cols(ref)})


def _file_ref_cols(ref) -> dict:
    return {
        "ref_role": ref.ref_role,
        "path_raw": ref.path_raw,
        "path_canonical": ref.path_canonical,
        "directory_path": ref.directory_path,
        "filename_pattern": ref.filename_pattern,
        "date_token": ref.date_token,
        "source_field": ref.source_field,
    }


def _emit_command(
    base, source, command, source_field, counters, bundle,
    *, default_type: str | None = None,
) -> None:
    parsed = parse_command(command)
    for inv in parsed.invocations:
        counters["inv"] += 1
        itype = inv.invocation_type
        if itype == "UNKNOWN" and default_type:
            itype = default_type
        bundle.invocation.append({
            **base,
            "seq": counters["inv"],
            "invocation_source": source,
            "invocation_type": itype,
            "executable_path": inv.executable_path,
            "script_path": inv.script_path,
            "config_path": inv.config_path,
            "args_json": json.dumps(list(inv.args)) if inv.args else None,
            "raw_command": inv.raw_command,
            "is_classified": "Y" if (inv.is_classified or default_type) else "N",
            "classifier_rule": inv.classifier_rule,
        })
    for fop in parsed.file_ops:
        counters["fop"] += 1
        bundle.file_op.append({
            **base,
            "seq": counters["fop"],
            "op_type": fop.op_type,
            "src_pattern": fop.src_pattern,
            "tgt_pattern": fop.tgt_pattern,
            "source_field": source,
            "raw_statement": fop.raw_statement,
        })


def build_staging_bundle(
    jobs: dict[tuple, JobDefinitions], run_id: str
) -> StagingBundle:
    """Classify + resolve every job and emit every STG_* row type."""
    headers: dict[tuple, JobDefinitions] = {
        (jd.data_center, jd.folder_id): jd
        for jd in jobs.values()
        if jd.is_folder_header
    }
    bundle = StagingBundle()
    for jd in jobs.values():
        classified = classify_job_variables(jd.defs)
        if jd.is_folder_header:
            resolved = resolve_job(jd.defs, [])
        else:
            header = headers.get((jd.data_center, jd.folder_id))
            fdefs = header.defs if header else []
            resolved = [
                rv for rv in resolve_job(fdefs, jd.defs) if rv.scope == "JOB"
            ]

        counters = {"inv": 0, "fop": 0}
        var_resolved = 0
        job_unresolved: list[str] = []
        for ordinal, (cv, rv) in enumerate(zip(classified, resolved, strict=False), start=1):
            bundle.variable.append(_stg_variable_row(jd, run_id, ordinal, cv, rv))
            var_resolved += rv.is_fully_resolved
            job_unresolved.extend(rv.unresolved)
            for env_name, variant_value in rv.variants:
                row = _stg_variable_row(jd, run_id, ordinal, cv, rv)
                row["env_tag"] = _ENV_NAME_TO_LETTER.get(env_name)
                row["resolved_value"] = variant_value
                row["is_fully_resolved"] = "Y" if "%%" not in variant_value else "N"
                bundle.variable.append(row)
            _route_technical_objects(jd, run_id, cv, rv, counters, bundle)

        has_cmd = any(c.kind is VariableKind.EMBEDDED_SHELL for c in classified)
        bundle.parse_quality.append({
            "run_id": run_id,
            **_job_keys(jd),
            "var_total": len(jd.defs),
            "var_resolved": var_resolved,
            "cmd_present": "Y" if has_cmd else "N",
            "cmd_classified": "Y" if counters["inv"] or counters["fop"] else "N",
            "invocation_count": counters["inv"],
            "file_ref_count": counters["fop"],
            "unresolved_tokens": ",".join(dict.fromkeys(job_unresolved)) or None,
            "notes": None,
        })
    return bundle


def build_staging_rows(
    jobs: dict[tuple, JobDefinitions], run_id: str
) -> tuple[list[dict], list[dict]]:
    """Back-compat shim (Phase A): returns just (variable, parse_quality)."""
    bundle = build_staging_bundle(jobs, run_id)
    return bundle.variable, bundle.parse_quality
