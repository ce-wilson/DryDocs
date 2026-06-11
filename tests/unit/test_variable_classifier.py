"""Unit tests for the Control-M variable taxonomy classifier (Phase A).

Every classification case below is a real row from the production
SQL Developer extract (controlm_variables__sample.csv) — not synthetic.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from drydocs.adapters.csv_adapter import CsvAdapter
from drydocs.controlm import (
    VariableCoverage,
    VariableKind,
    classify_job_variables,
    classify_variable,
)
from drydocs.models import ControlMVariableRow

SAMPLE = (
    Path(__file__).resolve().parents[2]
    / "drydocs" / "data" / "samples" / "controlm_variables__sample.csv"
)


# --- single-definition classification ----------------------------------------

@pytest.mark.parametrize(
    ("name", "value", "expected"),
    [
        # literals
        ("%%IMAGE_NAME", "CEMS", VariableKind.SEMANTIC_FACT),
        ("%%CLUST", "prod", VariableKind.LITERAL),
        ("%%SANDBOX_PATH", "/Data/abinitio/sandboxes/BB/BB_CDM/bb_cdm_pvt/pset",
         VariableKind.LITERAL),
        # system functions only
        ("%%ODAT", "%%$ODATE", VariableKind.SYSTEM_FUNC),
        ("%%PREV_ODATE", "%%$CALCDATE %%$ODATE -1", VariableKind.SYSTEM_FUNC),
        # %%$SUBSTR is a system func but %%$CURR_DATE_NEXT is a user var
        # referenced with dollar syntax -> needs resolution -> VAR_REF
        ("%%CURR_DAY_PREV", "%%$SUBSTR %%$CURR_DATE_NEXT 7 2",
         VariableKind.VAR_REF),
        # plain var references
        ("%%B1_SCRIPT", "/gpfs/%%ENV/script/common", VariableKind.VAR_REF),
        # %%$DROPBOX is a dollar-referenced user var; %%$ODATE_1 is a system
        # date token (ODATE-prefixed)
        ("%%DAT_FILE", "%%$DROPBOX/ptrx_sax_posting_%%$ODATE_1.dat.gz",
         VariableKind.VAR_REF),
        # dynamic name composition
        ("%%SCRIPT_PATH", "%%SCRIPT_PATH_%%HOSTNM", VariableKind.DYNAMIC_NAME),
        ("%%TENV", "%%TENV%%CURRENVIRON", VariableKind.DYNAMIC_NAME),
        # cross-flow pointers (single AND double backslash separators)
        ("%%PROID", r"%%\\SCRA_REPORTING\\PROID", VariableKind.FLOW_REF),
        ("%%PROID", r"%%\\CALCMOSUMTOTAL\PROID", VariableKind.FLOW_REF),
        # fact name holding a flow pointer is a pointer, not a fact
        ("%%TGT_TABLE", r"%%\\PDM_CRI_ACTL_TRUSTED\\INGESTED_FILE_NAME",
         VariableKind.FLOW_REF),
        # plugin namespaces
        ("%%FileWatch-MIN_AGE", "NO_MIN_AGE", VariableKind.PLUGIN_NS),
        ("%%UCM-CLUSTER_NAME", "%%CLUSTER_NAME", VariableKind.PLUGIN_NS),
        # embedded shell — including the observed POSCMD typo
        ("%%POSTCMD",
         "sh /home/b02supp/xmtr_scripts/run_calp_temp.sh bb.m %%$PRD_END_DATE_1,2,Y,NO",
         VariableKind.EMBEDDED_SHELL),
        ("%%POSCMD", "cc /apps/cds/sftp/UIP/vms/DW050/preprocess; mv a b;",
         VariableKind.EMBEDDED_SHELL),
        ("%%PRECMD", "mkdir -p %%R_PATH/VPC_P_VMSTR_BAL_%%$ODATE/%%R_PATH/backup;",
         VariableKind.EMBEDDED_SHELL),
        # semantic facts
        ("%%SEAL", "34544", VariableKind.SEMANTIC_FACT),
        ("%%FID_D", "B022876", VariableKind.SEMANTIC_FACT),
        ("%%RFID", "B019757", VariableKind.SEMANTIC_FACT),
        ("%%DATAFLOW", "CMHA_HLSF_CAMPAIGN", VariableKind.SEMANTIC_FACT),
        ("%%NOTIFY",
         "CDW_L2_Production_Support@restricted.chase.com;Team_Data_Pirates@restricted.chase.com",
         VariableKind.SEMANTIC_FACT),
        ("%%TGT_DB_NM", "ICDW_MB_PRSN_T", VariableKind.SEMANTIC_FACT),
        # malformed — a system-function expression where a NAME should be
        ("%%CALCDATE %%$ODATE -1", "", VariableKind.MALFORMED),
    ],
)
def test_classification(name: str, value: str, expected: VariableKind) -> None:
    assert classify_variable(name, value).kind is expected


def test_feature_extraction_tokens() -> None:
    cv = classify_variable(
        "%%FileWatch-FILE_PATH",
        "%%DROPBOX/%%FILE_NAME_PREFIX_%%FILE_NM_SUFFIX.%%FILE_EXT",
    )
    assert cv.kind is VariableKind.PLUGIN_NS
    assert cv.plugin_namespace == "FileWatch"
    assert "DROPBOX" in cv.plain_refs
    assert "FILE_EXT" in cv.plain_refs
    assert cv.has_adjacent_refs  # %%FILE_NAME_PREFIX_%%FILE_NM_SUFFIX hazard


def test_flow_ref_extraction() -> None:
    cv = classify_variable("%%VALUE", r"%%\\SCRA_REPORTING\\INGESTED_FILE_NAME")
    assert cv.flow_refs == (("SCRA_REPORTING", "INGESTED_FILE_NAME"),)


def test_dollar_user_refs_split_from_system_funcs() -> None:
    cv = classify_variable(
        "%%POSTCMD",
        "sh run_calp_temp.sh bb.m %%$PRD_END_DATE_1,2,Y,NO",
    )
    assert cv.kind is VariableKind.EMBEDDED_SHELL
    assert cv.dollar_refs == ("PRD_END_DATE_1",)
    assert cv.system_funcs == ()
    assert "PRD_END_DATE_1" in cv.all_var_refs


def test_malformed_name_extracts_no_namespace() -> None:
    # '%%CALCDATE %%$ODATE -1' as a NAME must not pollute the namespace table
    cv = classify_variable("%%CALCDATE %%$ODATE -1", "")
    assert cv.kind is VariableKind.MALFORMED
    assert cv.plugin_namespace is None
    assert cv.fact_type is None


def test_fact_type_via_env_suffix_base() -> None:
    # FID_D maps through base name FID in the registry
    assert classify_variable("%%FID_Q", "H024490").fact_type == "FID"


# --- job-level environment-triplet confirmation -------------------------------

def test_env_triplet_confirmed() -> None:
    defs = [
        ("%%FID_D", "B022876"),
        ("%%FID_Q", "H024490"),
        ("%%FID_P", "K024761"),
        ("%%CLUST", "prod"),
    ]
    out = {cv.name: cv for cv in classify_job_variables(defs)}
    assert out["FID_D"].env_tag == "Development"
    assert out["FID_Q"].env_tag == "QA"
    assert out["FID_P"].env_tag == "Production"
    assert out["CLUST"].env_tag is None


def test_lone_env_suffix_not_tagged() -> None:
    # a single _D name with no Q/P siblings stays a candidate, never a tag
    out = classify_job_variables([("%%NETWORK_D", "subnet-0504f9e1")])
    assert out[0].env_candidate == "D"
    assert out[0].env_tag is None


def test_env_suffix_requires_underscore() -> None:
    # SOR_UP ends in _UP, not _P — must not even be a candidate
    cv = classify_variable("%%SOR_UP", "MSP465")
    assert cv.env_candidate is None


# --- model + sample integration -----------------------------------------------

def test_model_accepts_raw_extract_headers() -> None:
    row = ControlMVariableRow.model_validate(
        {
            "table_name": "185894",
            "job_name": "PDCLD0003_24412_CMS_IDW_SCRA_REPORTING_CZ_AWS_TRUST",
            "job_id": "4",
            "appl_type": "OS",
            "name": "%%SEAL",
            "value": "34544",
        }
    )
    assert row.folder_id == "185894"
    assert row.var_name == "%%SEAL"
    assert row.var_value == "34544"
    assert row.data_center is None


def test_sample_classifies_end_to_end() -> None:
    per_job: dict[tuple, list[tuple[str, str | None]]] = {}
    with CsvAdapter(SAMPLE) as adapter:
        for raw in adapter.rows():
            row = ControlMVariableRow.model_validate(raw)
            per_job.setdefault((row.folder_id, row.job_id), []).append(
                (row.var_name, row.var_value)
            )

    cov = VariableCoverage()
    for key, defs in per_job.items():
        for cv in classify_job_variables(defs):
            cov.add(cv, job_key=key)

    assert cov.total == 323
    # every definition got exactly one kind
    assert sum(cov.by_kind.values()) == cov.total
    # known population facts from the extract
    assert cov.by_kind["PLUGIN_NS"] > 0          # FileWatch-/UCM- rows exist
    assert cov.by_kind["EMBEDDED_SHELL"] > 0     # PRECMD/POSTCMD rows exist
    assert cov.by_kind["FLOW_REF"] > 0           # %%\FLOW\VAR rows exist
    assert cov.fact_types["SEAL"] >= 1           # %%SEAL 34544 + UCM-SEALID
    assert cov.system_funcs["ODATE"] > 0
    # the unclassifiable junk rows land in MALFORMED, not in a crash
    assert cov.by_kind["MALFORMED"] >= 1
