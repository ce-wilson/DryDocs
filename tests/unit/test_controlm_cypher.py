"""Static checks on the M3 Control-M Cypher templates and SQL projections."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
CYPHER_DIR = ROOT / "drydocs" / "loaders" / "cypher"
SQL_DIR = ROOT / "drydocs" / "loaders" / "sql"
SCHEMA_DIR = ROOT / "drydocs" / "schema"

ALL_CYPHERS = [
    "controlm_folders.cypher",
    "controlm_jobs.cypher",
    "controlm_conditions_in.cypher",
    "controlm_conditions_out.cypher",
    "controlm_dependencies_derived.cypher",
]

ALL_SQL = [
    "controlm_folders.sql",
    "controlm_jobs.sql",
    "controlm_conditions_in.sql",
    "controlm_conditions_out.sql",
    "controlm_dependencies_recursive.sql",
]


# ---- Cypher --------------------------------------------------------------

@pytest.mark.parametrize("name", ALL_CYPHERS)
def test_cypher_exists(name: str) -> None:
    assert (CYPHER_DIR / name).exists()


@pytest.mark.parametrize("name", ALL_CYPHERS)
def test_cypher_uses_unwind_batch(name: str) -> None:
    text = (CYPHER_DIR / name).read_text(encoding="utf-8")
    assert "UNWIND $batch AS row" in text


@pytest.mark.parametrize("name", ALL_CYPHERS)
def test_cypher_idempotent_merge(name: str) -> None:
    text = (CYPHER_DIR / name).read_text(encoding="utf-8")
    body = "\n".join(
        l for l in text.splitlines()
        if l.strip() and not l.strip().startswith("//")
    )
    assert "MERGE" in body
    assert not re.findall(r"^\s*CREATE\s+\(", body, re.MULTILINE)


def test_folders_uses_sched_table_not_parent_table() -> None:
    text = (CYPHER_DIR / "controlm_folders.cypher").read_text(encoding="utf-8")
    assert "row.sched_table" in text
    # NO parent_table on the folder loader (that lives on the job side).
    assert "row.parent_table" not in text


def test_jobs_keeps_parent_table_property() -> None:
    text = (CYPHER_DIR / "controlm_jobs.cypher").read_text(encoding="utf-8")
    assert "row.parent_table" in text
    assert "row.application" in text  # Control-M app code (NOT seal_id)
    assert "row.cmd_line" in text


def test_jobs_node_key_is_folder_id_job_id_only() -> None:
    """NODE KEY is (folder_id, job_id). version_serial is a property."""
    text = (CYPHER_DIR / "controlm_jobs.cypher").read_text(encoding="utf-8")
    # MERGE pattern: both folder_id and job_id in the key block
    merge_block_pattern = re.compile(
        r"MERGE\s*\(j:ControlMJob:Activity\s*\{[^}]*\}",
        re.MULTILINE | re.DOTALL,
    )
    m = merge_block_pattern.search(text)
    assert m, "ControlMJob MERGE block not found"
    merge_keys = m.group(0)
    assert "folder_id: row.folder_id" in merge_keys
    assert "job_id: row.job_id" in merge_keys
    # version_serial should NOT be in the MERGE key block
    assert "version_serial:" not in merge_keys
    # but should still be SET as a property elsewhere
    assert "j.version_serial" in text


def test_conditions_match_jobs_on_folder_id_job_id() -> None:
    """Conditions MATCH :ControlMJob on (folder_id, job_id) only."""
    for name in ("controlm_conditions_in.cypher", "controlm_conditions_out.cypher"):
        text = (CYPHER_DIR / name).read_text(encoding="utf-8")
        match_block_pattern = re.compile(
            r"MATCH\s*\(j:ControlMJob\s*\{[^}]*\}",
            re.MULTILINE | re.DOTALL,
        )
        m = match_block_pattern.search(text)
        assert m, f"{name} ControlMJob MATCH not found"
        match_keys = m.group(0)
        assert "folder_id: row.folder_id" in match_keys
        assert "job_id: row.job_id" in match_keys
        # version_serial must NOT be in the MATCH key block
        assert "version_serial:" not in match_keys, \
            f"{name} should not key on version_serial"


def test_conditions_node_key_is_folder_id_name_only() -> None:
    """:Condition NODE KEY is (folder_id, name). version_serial is a property."""
    for name in ("controlm_conditions_in.cypher", "controlm_conditions_out.cypher"):
        text = (CYPHER_DIR / name).read_text(encoding="utf-8")
        merge_block_pattern = re.compile(
            r"MERGE\s*\(c:Condition:Entity\s*\{[^}]*\}",
            re.MULTILINE | re.DOTALL,
        )
        m = merge_block_pattern.search(text)
        assert m, f"{name} :Condition MERGE block not found"
        merge_keys = m.group(0)
        assert "folder_id: row.folder_id" in merge_keys
        assert "name: row.condition_name" in merge_keys
        assert "version_serial:" not in merge_keys
        # But the property should be SET elsewhere.
        assert "c.version_serial" in text


def test_dependencies_match_on_folder_plus_job() -> None:
    text = (CYPHER_DIR / "controlm_dependencies_derived.cypher").read_text(encoding="utf-8")
    # Successor: matches both folder_id and job_id
    assert "folder_id: row.in_parent_table_id" in text
    assert "job_id:    row.in_job_id" in text or "job_id: row.in_job_id" in text
    # Predecessor: same pattern
    assert "folder_id: row.dependent_table_id" in text
    assert "job_id:    row.dependent_job_id" in text or "job_id: row.dependent_job_id" in text


def test_conditions_in_carries_boolean_expr_props() -> None:
    text = (CYPHER_DIR / "controlm_conditions_in.cypher").read_text(encoding="utf-8")
    for fragment in ["and_or", "parentheses", "order_"]:
        assert fragment in text, f"in.cypher missing {fragment}"
    # No SIGN on the IN side.
    assert "row.sign" not in text


def test_conditions_out_carries_sign() -> None:
    text = (CYPHER_DIR / "controlm_conditions_out.cypher").read_text(encoding="utf-8")
    assert "row.sign" in text
    assert "and_or" not in text


def test_conditions_share_composite_key() -> None:
    """Both IN and OUT loaders key :Condition the same way so the same
    node is shared when (folder_id, name, version_serial) matches."""
    for name in ("controlm_conditions_in.cypher", "controlm_conditions_out.cypher"):
        text = (CYPHER_DIR / name).read_text(encoding="utf-8")
        assert "folder_id: row.folder_id" in text
        assert "name: row.condition_name" in text
        assert "version_serial: row.version_serial" in text


def test_dependencies_materializes_derived_edge() -> None:
    text = (CYPHER_DIR / "controlm_dependencies_derived.cypher").read_text(encoding="utf-8")
    assert ":DEPENDS_ON" in text
    assert "derived" in text
    assert "via_condition" in text
    assert "recursion_level" in text
    assert "dependency_path" in text


# ---- SQL projections ------------------------------------------------------

@pytest.mark.parametrize("name", ALL_SQL)
def test_sql_exists(name: str) -> None:
    assert (SQL_DIR / name).exists()


@pytest.mark.parametrize("name", ALL_SQL)
def test_sql_references_psgmgr(name: str) -> None:
    text = (SQL_DIR / name).read_text(encoding="utf-8")
    assert "psgmgr." in text


def test_folder_sql_uses_sched_table() -> None:
    text = (SQL_DIR / "controlm_folders.sql").read_text(encoding="utf-8")
    assert "T.SCHED_TABLE" in text
    # Confirm NO is_current_version filter on the folder side (that column
    # doesn't exist on CM_DEF_VTAB).
    assert "T.IS_CURRENT_VERSION" not in text


def test_jobs_sql_filters_current_version_as_string() -> None:
    text = (SQL_DIR / "controlm_jobs.sql").read_text(encoding="utf-8")
    # IS_CURRENT_VERSION is VARCHAR2(1); literal must be a string.
    assert "J.IS_CURRENT_VERSION = '1'" in text


def test_recursive_sql_has_cycle_guard() -> None:
    text = (SQL_DIR / "controlm_dependencies_recursive.sql").read_text(encoding="utf-8")
    assert "INSTR(PREV_DEP.dependency_path" in text
    assert "PREV_DEP.recursion_level < 10" in text
    assert "WITH RecursiveJobDependencies" in text


def test_recursive_sql_cyclic_type_disabled() -> None:
    """The canonical version intentionally disables CYCLIC_TYPE matching."""
    text = (SQL_DIR / "controlm_dependencies_recursive.sql").read_text(encoding="utf-8")
    # The disabling marker appears at the cyclic-type comparison sites.
    assert "intentionally disabled" in text


# ---- Ontology supplement -------------------------------------------------

def test_m3_supplement_wires_to_prov_anchors() -> None:
    text = (SCHEMA_DIR / "m3_ontology_supplement.cypher").read_text(encoding="utf-8")
    assert "SUBCLASS_OF" in text
    assert "http://www.w3.org/ns/prov#Collection" in text
    assert "http://www.w3.org/ns/prov#Activity" in text
