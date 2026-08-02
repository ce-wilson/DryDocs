"""Unit tests for the Control-M variable taxonomy classifier (Phase A).

Every classification case below is a real row from the production
SQL Developer extract (controlm_variables__sample.csv) — not synthetic.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from drydocs_core.adapters.csv_adapter import CsvAdapter
from drydocs_core.models import ControlMVariableRow
from drydocs_core.orchestration.controlm import (
    VariableCoverage,
    VariableKind,
    classify_job_variables,
    classify_variable,
)

SAMPLE = (
    Path(__file__).resolve().parents[2]
    / "drydocs"
    / "data"
    / "samples"
    / "controlm_variables__sample.csv"
)

# The production extract is gitignored (stays company-side / regenerate via
# `normalize-variables --use-oracle`). Tests that read it are skipped — not
# failed — where it is absent, so the suite is green on any clone. The inline
# cases below give deterministic, CSV-free coverage of every classifier path.
requires_sample = pytest.mark.skipif(
    not SAMPLE.exists(),
    reason="production sample CSV absent (gitignored); regenerate locally via psgmgr",
)


# --- single-definition classification ----------------------------------------


@pytest.mark.parametrize(
    ("name", "value", "expected"),
    [
        # literals
        ("%%IMAGE_NAME", "CEMS", VariableKind.SEMANTIC_FACT),
        ("%%CLUST", "prod", VariableKind.LITERAL),
        (
            "%%SANDBOX_PATH",
            "/Data/abinitio/sandboxes/BB/BB_CDM/bb_cdm_pvt/pset",
            VariableKind.LITERAL,
        ),
        # system functions only
        ("%%ODAT", "%%$ODATE", VariableKind.SYSTEM_FUNC),
        ("%%PREV_ODATE", "%%$CALCDATE %%$ODATE -1", VariableKind.SYSTEM_FUNC),
        # %%$SUBSTR is a system func but %%$CURR_DATE_NEXT is a user var
        # referenced with dollar syntax -> needs resolution -> VAR_REF
        ("%%CURR_DAY_PREV", "%%$SUBSTR %%$CURR_DATE_NEXT 7 2", VariableKind.VAR_REF),
        # plain var references
        ("%%B1_SCRIPT", "/gpfs/%%ENV/script/common", VariableKind.VAR_REF),
        # %%$DROPBOX is a dollar-referenced user var; %%$ODATE_1 is a system
        # date token (ODATE-prefixed)
        ("%%DAT_FILE", "%%$DROPBOX/ptrx_sax_posting_%%$ODATE_1.dat.gz", VariableKind.VAR_REF),
        # dynamic name composition
        ("%%SCRIPT_PATH", "%%SCRIPT_PATH_%%HOSTNM", VariableKind.DYNAMIC_NAME),
        ("%%TENV", "%%TENV%%CURRENVIRON", VariableKind.DYNAMIC_NAME),
        # cross-flow pointers (single AND double backslash separators)
        ("%%PROID", r"%%\\SCRA_REPORTING\\PROID", VariableKind.FLOW_REF),
        ("%%PROID", r"%%\\CALCMOSUMTOTAL\PROID", VariableKind.FLOW_REF),
        # fact name holding a flow pointer is a pointer, not a fact
        ("%%TGT_TABLE", r"%%\\PDM_CRI_ACTL_TRUSTED\\INGESTED_FILE_NAME", VariableKind.FLOW_REF),
        # plugin namespaces
        ("%%FileWatch-MIN_AGE", "NO_MIN_AGE", VariableKind.PLUGIN_NS),
        ("%%UCM-CLUSTER_NAME", "%%CLUSTER_NAME", VariableKind.PLUGIN_NS),
        # embedded shell — including the observed POSCMD typo
        (
            "%%POSTCMD",
            "sh /home/b02supp/xmtr_scripts/run_calp_temp.sh bb.m %%$PRD_END_DATE_1,2,Y,NO",
            VariableKind.EMBEDDED_SHELL,
        ),
        (
            "%%POSCMD",
            "cc /apps/cds/sftp/UIP/vms/DW050/preprocess; mv a b;",
            VariableKind.EMBEDDED_SHELL,
        ),
        (
            "%%PRECMD",
            "mkdir -p %%R_PATH/VPC_P_VMSTR_BAL_%%$ODATE/%%R_PATH/backup;",
            VariableKind.EMBEDDED_SHELL,
        ),
        # semantic facts
        ("%%SEAL", "70004", VariableKind.SEMANTIC_FACT),
        ("%%FID_D", "B0004", VariableKind.SEMANTIC_FACT),
        ("%%RFID", "B0007", VariableKind.SEMANTIC_FACT),
        ("%%DATAFLOW", "CMHA_HLSF_CAMPAIGN", VariableKind.SEMANTIC_FACT),
        (
            "%%NOTIFY",
            "APP_L2_Production_Support@example.com;Team_Night_Herons@example.com",
            VariableKind.SEMANTIC_FACT,
        ),
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


def test_system_variables_not_user_refs() -> None:
    # external/orchestration/bmc-controlm/controlm-variables.md §System Variables Reference:
    # ORDERID / JOBNAME are system variables — they must NOT enter the
    # Phase-B resolution hot set. Real row: %%UCM-KEYVALUE on folder 185675.
    cv = classify_variable(
        "%%UCM-KEYVALUE",
        "JOB_NAME=%%JOBNAME;ORDER_ID=%%ORDERID;FEED_NAME=%%FEED_NAME",
    )
    assert "JOBNAME" in cv.system_vars
    assert "ORDERID" in cv.system_vars
    assert cv.all_var_refs == ("FEED_NAME",)


def test_plain_substr_is_system_function() -> None:
    # classic AutoEdit function syntax without the $ prefix
    # (real row: %%HOSTNM on folder 155768)
    cv = classify_variable("%%HOSTNM", "%%SUBSTR %%DATACENTER 1 1")
    assert cv.kind is VariableKind.VAR_REF  # DATACENTER needs resolution
    assert cv.system_funcs == ("SUBSTR",)
    assert cv.all_var_refs == ("DATACENTER",)


def test_single_backslash_global_ref() -> None:
    # vendor §Scope Levels: %%\VAR is a server-global variable — must be
    # captured, not silently dropped by both the pool and plain-ref regexes
    cv = classify_variable("%%BASE", r"%%\BASEPATH/data")
    assert cv.kind is VariableKind.FLOW_REF
    assert cv.global_refs == ("BASEPATH",)
    assert cv.plain_refs == ()


def test_malformed_name_extracts_no_namespace() -> None:
    # '%%CALCDATE %%$ODATE -1' as a NAME must not pollute the namespace table
    cv = classify_variable("%%CALCDATE %%$ODATE -1", "")
    assert cv.kind is VariableKind.MALFORMED
    assert cv.plugin_namespace is None
    assert cv.fact_type is None


def test_fact_type_via_env_suffix_base() -> None:
    # FID_D maps through base name FID in the registry
    assert classify_variable("%%FID_Q", "H0005").fact_type == "FID"


# --- job-level environment-triplet confirmation -------------------------------


def test_env_triplet_confirmed() -> None:
    defs = [
        ("%%FID_D", "B0004"),
        ("%%FID_Q", "H0005"),
        ("%%FID_P", "K0006"),
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
            "job_name": "PDCLD0003_70013_CMS_IDW_SCRA_REPORTING_CZ_AWS_TRUST",
            "job_id": "4",
            "appl_type": "OS",
            "name": "%%SEAL",
            "value": "70004",
        }
    )
    assert row.folder_id == "185894"
    assert row.var_name == "%%SEAL"
    assert row.var_value == "70004"
    assert row.data_center is None


@requires_sample
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
    assert cov.by_kind["PLUGIN_NS"] > 0  # FileWatch-/UCM- rows exist
    assert cov.by_kind["EMBEDDED_SHELL"] > 0  # PRECMD/POSTCMD rows exist
    assert cov.by_kind["FLOW_REF"] > 0  # %%\FLOW\VAR rows exist
    assert cov.fact_types["SEAL"] >= 1  # %%SEAL 70004 + UCM-SEALID
    assert cov.system_vars["ODATE"] > 0  # system variable, not function
    assert cov.system_funcs["CALCDATE"] > 0
    # system variables must NOT appear in the user-resolution hot set
    assert "ORDERID" not in cov.referenced_names
    assert "JOBNAME" not in cov.referenced_names
    # the unclassifiable junk rows land in MALFORMED, not in a crash
    assert cov.by_kind["MALFORMED"] >= 1


# -- G16: artifact/launcher canonicals + value contracts (gate cmdline-nfr-vetting,
# SME-4, 2026-07-21 — aliases suggest, VALUES decide; canonical names WARN-free) --


def test_image_rolls_up_to_artifact_uri_clean_break() -> None:
    # v2 decision log: IMAGE -> IMAGE is removed; IMAGE now suggests ARTIFACT_URI
    cv = classify_variable("%%IMAGE", "registry/app/ingest-img:1.0")
    assert cv.fact_type == "ARTIFACT_URI"
    assert cv.kind is VariableKind.SEMANTIC_FACT
    # legacy alias stays materialized (non-destructive) but flags the rename
    assert cv.fact_alias_of == "ETL_ARTIFACT_URI"
    assert cv.fact_name_mismatch is False


def test_launcher_valued_variable_is_launcher_regardless_of_name() -> None:
    # the JAR_PATH -> dt-launcher.sh gotcha: name says jar, value IS the
    # registered launcher — the VALUE decides, and the mismatch is a WARN
    cv = classify_variable("%%JAR_PATH", "/apps/tenants/dpl_utils/dt-accelerators/dt-launcher.sh")
    assert cv.fact_type == "LAUNCHER_SCRIPT_PATH"
    assert cv.fact_name_mismatch is True
    # even an UNREGISTERED name is corrected by the value contract
    cv2 = classify_variable("%%SOME_TEAM_VAR", "/x/y/dpl_spark_processor")
    assert cv2.fact_type == "LAUNCHER_SCRIPT_PATH"
    assert cv2.kind is VariableKind.SEMANTIC_FACT
    assert cv2.fact_name_mismatch is False  # nothing was suggested, nothing lied


def test_sha_digest_is_artifact_sha_never_uri() -> None:
    sha256 = "934fe87c0cae8b9983a3a21b5a4a70fb408faf487a3d48af73ada3b8320a27a7"
    cv = classify_variable("%%IMAGE_SHA", sha256)
    assert cv.fact_type == "ARTIFACT_SHA"
    assert cv.fact_name_mismatch is False  # name and value agree
    # a URI-named variable holding a digest is corrected + flagged
    cv2 = classify_variable("%%ETL_ARTIFACT_URI", sha256)
    assert cv2.fact_type == "ARTIFACT_SHA"
    assert cv2.fact_name_mismatch is True


def test_canonical_names_are_warn_free() -> None:
    cv = classify_variable("%%ETL_ARTIFACT_URI", "https://artifactory/maven/app/bar-1.4.0.jar")
    assert cv.fact_type == "ARTIFACT_URI"
    assert cv.fact_alias_of is None
    assert cv.fact_name_mismatch is False
    cv2 = classify_variable("%%LAUNCHER_SCRIPT_PATH", "/apps/x/dt-launcher.sh")
    assert cv2.fact_type == "LAUNCHER_SCRIPT_PATH"
    assert cv2.fact_alias_of is None and cv2.fact_name_mismatch is False


def test_production_alias_rollups_materialize_with_rename_warn() -> None:
    for name in ("%%USER_JAR", "%%CONTAINER_IMAGE", "%%JAR_LOC", "%%MULTI_FILE_JAR"):
        cv = classify_variable(name, "/apps/uds/tenants/x/jars/thing-1.0.jar")
        assert cv.fact_type == "ARTIFACT_URI", name
        assert cv.fact_alias_of == "ETL_ARTIFACT_URI", name
    for name in ("%%PY_LAUNCH", "%%SCRIPT_PATH", "%%ACCELERATOR_PATH"):
        cv = classify_variable(name, "/apps/x/dt-accelerators/dt-launcher.sh")
        assert cv.fact_type == "LAUNCHER_SCRIPT_PATH", name
        # aliases OF the canonical LAUNCHER_SCRIPT_PATH spelling — rename WARN
        assert cv.fact_alias_of == "LAUNCHER_SCRIPT_PATH", name


def test_value_contract_skips_unresolved_and_multitoken_values() -> None:
    # %%VAR-bearing values cannot be judged by value — no override, no warn
    cv = classify_variable("%%JAR_PATH", "%%JAR_DIR/dt-launcher.sh")
    assert cv.kind is VariableKind.VAR_REF
    assert cv.fact_name_mismatch is False
    # a full command string is not a single artifact token
    cv2 = classify_variable("%%SOME_CMD", "sh /apps/x/dt-launcher.sh -i")
    assert cv2.fact_type is None


def test_icdw_run_interface_classifies_informatica() -> None:
    from drydocs_core.orchestration.shell import classify_executable

    itype, rule = classify_executable("/etlapps/icdw/prod/ops/Scripts/ICDW_etl_run_interface.ksh")
    assert itype == "INFORMATICA"
    assert rule == "informatica.icdw_run_interface"
    # generic shell scripts still classify SHELL_SCRIPT, not launcher
    from drydocs_core.orchestration.shell import is_registered_launcher

    assert is_registered_launcher("/apps/x/dt-launcher.sh")
    assert not is_registered_launcher("/opt/scripts/hldm/onpm_fw.ksh")


def test_fact_warns_counted_in_coverage() -> None:
    cov = VariableCoverage()
    cov.add(classify_variable("%%JAR_PATH", "/a/dt-launcher.sh"))  # mismatch
    cov.add(classify_variable("%%IMAGE", "registry/app/img:1"))  # alias
    cov.add(classify_variable("%%ETL_ARTIFACT_URI", "https://r/a.jar"))  # canonical
    assert cov.fact_warns["name_value_mismatch"] == 1
    assert cov.fact_warns["alias_rename"] == 1
    assert sum(cov.fact_warns.values()) == 2
