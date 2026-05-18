"""Static checks on the M3 Control-M Cypher templates."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

CYPHER_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "drydocs" / "loaders" / "cypher"
)
SCHEMA_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "drydocs" / "schema"
)

CYPHERS = [
    "controlm_folders.cypher",
    "controlm_jobs.cypher",
]


@pytest.mark.parametrize("name", CYPHERS)
def test_cypher_exists(name: str) -> None:
    assert (CYPHER_DIR / name).exists()


@pytest.mark.parametrize("name", CYPHERS)
def test_cypher_uses_unwind_batch(name: str) -> None:
    text = (CYPHER_DIR / name).read_text(encoding="utf-8")
    assert "UNWIND $batch AS row" in text


@pytest.mark.parametrize("name", CYPHERS)
def test_cypher_idempotent_merge(name: str) -> None:
    text = (CYPHER_DIR / name).read_text(encoding="utf-8")
    body = "\n".join(
        l for l in text.splitlines()
        if l.strip() and not l.strip().startswith("//")
    )
    assert "MERGE" in body
    # No CREATE for primary entities — only MERGE.
    bad = re.findall(r"^\s*CREATE\s+\(", body, re.MULTILINE)
    assert not bad, f"{name} uses CREATE for primary entities"


def test_folders_creates_server_and_runs_on() -> None:
    text = (CYPHER_DIR / "controlm_folders.cypher").read_text(encoding="utf-8")
    assert ":ControlMServer" in text
    assert ":JobFolder" in text
    assert ":RUNS_ON" in text
    # Folder is labeled as both :JobFolder and :Collection (prov:Collection anchor).
    assert "JobFolder:Collection" in text
    # Server is labeled :ControlMServer:Platform.
    assert "ControlMServer:Platform" in text


def test_jobs_uses_composite_node_key() -> None:
    text = (CYPHER_DIR / "controlm_jobs.cypher").read_text(encoding="utf-8")
    # MERGE on both job_id and version_serial — matches v3 §J NODE KEY constraint.
    assert "job_id: row.job_id" in text
    assert "version_serial: row.version_serial" in text
    assert ":ControlMJob:Activity" in text
    assert ":CONTAINS_JOB" in text
    # Folder must be MATCHed (not MERGEd) so we don't accidentally create
    # orphan placeholder folders.
    assert "MATCH (f:JobFolder" in text


def test_m3_supplement_anchors_present() -> None:
    text = (SCHEMA_DIR / "m3_ontology_supplement.cypher").read_text(encoding="utf-8")
    for fragment in [
        "https://drydocs.local/ontology#ControlMServer",
        "https://drydocs.local/ontology#JobFolder",
        "https://drydocs.local/ontology#ControlMJob",
    ]:
        assert fragment in text


def test_m3_supplement_wires_to_prov_anchors() -> None:
    text = (SCHEMA_DIR / "m3_ontology_supplement.cypher").read_text(encoding="utf-8")
    # SUBCLASS_OF edges to prov:Collection and prov:Activity.
    assert "SUBCLASS_OF" in text
    assert "http://www.w3.org/ns/prov#Collection" in text
    assert "http://www.w3.org/ns/prov#Activity" in text


def test_m3_supplement_scheduler_kind_idempotent() -> None:
    text = (SCHEMA_DIR / "m3_ontology_supplement.cypher").read_text(encoding="utf-8")
    # Re-asserts SchedulerKind ControlM exists (M0 seeded it; supplement double-checks).
    assert 'SchedulerKind {name: "ControlM"}' in text
