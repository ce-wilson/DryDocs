"""Build STG_* staging rows from classified + resolved variables (Phase A
output side).

Combines the Phase-A classifier (kind, env tags, fact types) and the
Phase-B resolver (resolved values, unresolved tokens, env variants) into
row dicts whose keys match the controlm_staging_ddl.sql columns exactly,
so the emitted CSVs load into STG_VARIABLE / STG_PARSE_QUALITY /
STG_RUN via SQL Developer import or SQL*Loader without mapping.

Variant rows: when the resolver expands an environment triplet
(%%SCRIPT_PATH_%%HOSTNM -> one value per D/Q/P), each variant is emitted
as an ADDITIONAL stg_variable row carrying env_tag — duplicate
(job, var_name) rows are by design (surrogate PK in the DDL).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from ..models import ControlMVariableRow
from .resolver import ResolvedVariable, resolve_job
from .variables import ClassifiedVariable, classify_job_variables

# resolver variants carry the long environment name; STG env_tag is the letter
_ENV_NAME_TO_LETTER = {"Development": "D", "QA": "Q", "Production": "P"}


@dataclass
class JobDefinitions:
    """All variable definitions of one (data_center, folder, job)."""

    data_center: str
    folder_id: str
    job_id: str
    is_folder_header: bool
    defs: list[tuple[str, str | None]] = field(default_factory=list)


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


def _stg_variable_row(
    jd: JobDefinitions,
    run_id: str,
    ordinal: int,
    cv: ClassifiedVariable,
    rv: ResolvedVariable,
) -> dict:
    unresolved = list(rv.unresolved) + list(rv.external_refs)
    return {
        "run_id": run_id,
        "data_center": jd.data_center,
        "folder_id": jd.folder_id,
        "job_id": jd.job_id,
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


def build_staging_rows(
    jobs: dict[tuple, JobDefinitions], run_id: str
) -> tuple[list[dict], list[dict]]:
    """Classify + resolve every job and emit (stg_variable rows,
    stg_parse_quality rows). Folder headers resolve standalone; jobs
    resolve under their folder's scope."""
    headers: dict[tuple, JobDefinitions] = {
        (jd.data_center, jd.folder_id): jd
        for jd in jobs.values()
        if jd.is_folder_header
    }

    variable_rows: list[dict] = []
    quality_rows: list[dict] = []
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

        var_resolved = 0
        job_unresolved: list[str] = []
        for ordinal, (cv, rv) in enumerate(zip(classified, resolved), start=1):
            variable_rows.append(_stg_variable_row(jd, run_id, ordinal, cv, rv))
            var_resolved += rv.is_fully_resolved
            job_unresolved.extend(rv.unresolved)
            # one extra row per environment variant, tagged with its letter
            for env_name, variant_value in rv.variants:
                row = _stg_variable_row(jd, run_id, ordinal, cv, rv)
                row["env_tag"] = _ENV_NAME_TO_LETTER.get(env_name)
                row["resolved_value"] = variant_value
                row["is_fully_resolved"] = "Y" if "%%" not in variant_value else "N"
                variable_rows.append(row)

        quality_rows.append({
            "run_id": run_id,
            "data_center": jd.data_center,
            "folder_id": jd.folder_id,
            "job_id": jd.job_id,
            "var_total": len(jd.defs),
            "var_resolved": var_resolved,
            # command fields are Phase-C territory; defaults until then
            "cmd_present": "N",
            "cmd_classified": "N",
            "invocation_count": 0,
            "file_ref_count": 0,
            "unresolved_tokens": ",".join(dict.fromkeys(job_unresolved)) or None,
            "notes": None,
        })
    return variable_rows, quality_rows
