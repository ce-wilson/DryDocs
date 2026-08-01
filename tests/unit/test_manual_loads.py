"""Offline tests for the tier-5 manual mapping mechanism (gate
seal-attribution-match-policy §F, SME-confirmed 2026-07-14).

Pins the manifest gate (registered BEFORE load, replaces_with required,
superseded refuses), the never-mint-a-relationship rule, the supported-shape
guard, and template-CSV parsing. Pure — tmp-dir manifests + the real
relationship vocabulary, no network/DB.
"""
from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

from drydocs.loaders.manual_loads import (
    DEFAULT_MANIFEST_PATH,
    SUPPORTED_SHAPE,
    ManualLoadError,
    ManualMappingAdapter,
    ManualSealAttributionLoader,
    parse_mapping_csv,
    relationship_registered,
    require_registered,
)
from drydocs_core.models import ManualMappingRow

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = REPO_ROOT / "config" / "manual-loads" / "TEMPLATE-node-mapping.csv"

CSV_HEADER = ("source_label,source_key,relationship,rel_props,target_label,"
              "target_key,create_target_if_missing,note,authored_by,authored_on")


def _repo(tmp_path: Path, *, entry: dict | None = None,
          manifest_status: str = "confirmed") -> tuple[Path, Path]:
    """Build a tmp repo skeleton: manifest + a registered CSV. Returns
    (manifest_path, csv_path)."""
    manifest_dir = tmp_path / "config" / "manual-loads"
    manifest_dir.mkdir(parents=True)
    csv_dir = tmp_path / "internal" / "manual"
    csv_dir.mkdir(parents=True)
    csv_path = csv_dir / "batch1-mappings.csv"
    csv_path.write_text(
        CSV_HEADER + "\n"
        "ControlMJob,folder_id=900001;job_id=3,WAS_ASSOCIATED_WITH,"
        "role=seal_app_ref,BusinessApplication,seal_id=SL0001,false,"
        "synthetic test row,tester0001,2026-07-14\n",
        encoding="utf-8",
    )
    default_entry = {
        "file": "internal/manual/batch1-mappings.csv",
        "scope": "synthetic test mappings",
        "status": "pending-load",
        "replaces_with": "stg-app-fact automated attribution (seal_attribution.py)",
        "authored_by": "tester0001",
    }
    manifest = {
        "schema": "drydocs.manual-loads.v1",
        "status": manifest_status,
        "template": "config/manual-loads/TEMPLATE-node-mapping.csv",
        "files": [entry if entry is not None else default_entry],
    }
    manifest_path = manifest_dir / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    return manifest_path, csv_path


# --- the manifest gate (§F.5) --------------------------------------------------

def test_registered_pending_load_csv_is_accepted(tmp_path: Path) -> None:
    manifest_path, csv_path = _repo(tmp_path)
    entry = require_registered(csv_path, manifest_path)
    assert entry["file"] == "internal/manual/batch1-mappings.csv"


def test_unregistered_csv_is_refused(tmp_path: Path) -> None:
    manifest_path, _ = _repo(tmp_path)
    rogue = tmp_path / "internal" / "manual" / "rogue.csv"
    rogue.write_text(CSV_HEADER + "\n", encoding="utf-8")
    with pytest.raises(ManualLoadError, match="not registered"):
        require_registered(rogue, manifest_path)


def test_superseded_entry_is_refused(tmp_path: Path) -> None:
    manifest_path, csv_path = _repo(tmp_path, entry={
        "file": "internal/manual/batch1-mappings.csv",
        "status": "superseded",
        "replaces_with": "stg-app-fact automated attribution",
    })
    with pytest.raises(ManualLoadError, match="superseded|not loadable"):
        require_registered(csv_path, manifest_path)


def test_entry_without_replaces_with_is_refused(tmp_path: Path) -> None:
    manifest_path, csv_path = _repo(tmp_path, entry={
        "file": "internal/manual/batch1-mappings.csv",
        "status": "pending-load",
    })
    with pytest.raises(ManualLoadError, match="replaces_with"):
        require_registered(csv_path, manifest_path)


def test_unconfirmed_manifest_refuses_everything(tmp_path: Path) -> None:
    manifest_path, csv_path = _repo(tmp_path, manifest_status="proposed")
    with pytest.raises(ManualLoadError, match="gate-bound"):
        require_registered(csv_path, manifest_path)


def test_shipped_manifest_is_confirmed_with_empty_queue() -> None:
    doc = yaml.safe_load(DEFAULT_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert doc["status"] == "confirmed"        # flipped at the 2026-07-14 gate
    assert doc["files"] == []                  # producer ships mechanism only


# --- never mint a relationship type (§F.1) --------------------------------------

def test_the_k2_shape_is_a_registered_vocabulary_entry() -> None:
    assert relationship_registered("WAS_ASSOCIATED_WITH", "seal_app_ref")


def test_unregistered_relationships_are_refused() -> None:
    assert not relationship_registered("MADE_UP_REL", None)
    assert not relationship_registered("WAS_ASSOCIATED_WITH", "owner")


def test_csv_naming_an_unregistered_relationship_is_refused(tmp_path: Path) -> None:
    manifest_path, csv_path = _repo(tmp_path)
    csv_path.write_text(
        CSV_HEADER + "\n"
        "ControlMJob,folder_id=900001;job_id=3,MADE_UP_REL,role=seal_app_ref,"
        "BusinessApplication,seal_id=SL0001,false,x,tester0001,2026-07-14\n",
        encoding="utf-8",
    )
    with pytest.raises(ManualLoadError, match="never mint a relationship type"):
        parse_mapping_csv(csv_path, manifest_path=manifest_path)


# --- the supported-shape guard ---------------------------------------------------

def test_unsupported_shape_is_refused_loudly(tmp_path: Path) -> None:
    manifest_path, csv_path = _repo(tmp_path)
    csv_path.write_text(
        CSV_HEADER + "\n"
        # WAS_INFORMED_BY is registered (so the vocab check passes) but is
        # not the supported manual-writer shape.
        "ControlMJob,folder_id=900001;job_id=3,WAS_INFORMED_BY,role=,"
        "ControlMJob,folder_id=900001;job_id=4,false,x,tester0001,2026-07-14\n",
        encoding="utf-8",
    )
    with pytest.raises(ManualLoadError, match="unsupported shape"):
        parse_mapping_csv(csv_path, manifest_path=manifest_path)


def test_source_key_missing_a_node_key_part_is_refused(tmp_path: Path) -> None:
    manifest_path, csv_path = _repo(tmp_path)
    csv_path.write_text(
        CSV_HEADER + "\n"
        "ControlMJob,folder_id=900001,WAS_ASSOCIATED_WITH,role=seal_app_ref,"
        "BusinessApplication,seal_id=SL0001,false,x,tester0001,2026-07-14\n",
        encoding="utf-8",
    )
    with pytest.raises(ManualLoadError, match="job_id"):
        parse_mapping_csv(csv_path, manifest_path=manifest_path)


# --- parsing ---------------------------------------------------------------------

def test_valid_row_parses_to_the_narrowed_shape(tmp_path: Path) -> None:
    manifest_path, csv_path = _repo(tmp_path)
    rows = parse_mapping_csv(csv_path, manifest_path=manifest_path)
    assert len(rows) == 1
    row = rows[0]
    assert isinstance(row, ManualMappingRow)
    assert (row.folder_id, row.job_id, row.seal_id) == ("900001", "3", "SL0001")
    assert row.create_target_if_missing is False
    assert row.manual_load_file == "internal/manual/batch1-mappings.csv"
    assert row.authored_by == "tester0001"


def test_create_target_flag_parses_truthy_strings(tmp_path: Path) -> None:
    manifest_path, csv_path = _repo(tmp_path)
    csv_path.write_text(
        CSV_HEADER + "\n"
        "ControlMJob,folder_id=900001;job_id=3,WAS_ASSOCIATED_WITH,"
        "role=seal_app_ref,BusinessApplication,seal_id=SL0001,TRUE,x,tester0001,2026-07-14\n",
        encoding="utf-8",
    )
    rows = parse_mapping_csv(csv_path, manifest_path=manifest_path)
    assert rows[0].create_target_if_missing is True


def test_template_header_matches_the_parser_contract() -> None:
    header = TEMPLATE.read_text(encoding="utf-8").splitlines()[0]
    assert header == CSV_HEADER


def test_shape_constant_is_the_k2_edge() -> None:
    assert SUPPORTED_SHAPE == {
        "source_label": "ControlMJob",
        "relationship": "WAS_ASSOCIATED_WITH",
        "role": "seal_app_ref",
        "target_label": "BusinessApplication",
    }


def test_adapter_and_loader_wiring(tmp_path: Path) -> None:
    manifest_path, csv_path = _repo(tmp_path)
    rows = parse_mapping_csv(csv_path, manifest_path=manifest_path)
    with ManualMappingAdapter(rows) as adapter:
        emitted = list(adapter.rows())
    assert emitted[0]["seal_id"] == "SL0001"
    assert ManualSealAttributionLoader.name == "manual_seal_attribution.v1"
    assert ManualSealAttributionLoader.row_model is ManualMappingRow
    assert ManualSealAttributionLoader.cypher_path is not None
    assert ManualSealAttributionLoader.cypher_path.exists()
    assert ManualSealAttributionLoader.source_label == "human"
