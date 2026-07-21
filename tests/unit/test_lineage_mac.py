"""G17 — the DPL Metadata-As-Code ingest seam.

SYNTHETIC fixtures throughout (shape-faithful, value-fake; the field names ARE
the assumed contract documented in ``dpl_mac.py`` — a real sample validates or
amends them). Every case pins one acceptance clause: (a) GUID join + unmatched
accounting, (b) dataset-flow READS_FROM/WRITES_TO candidates on the
gate-confirmed endpoints, (c) subType kind derivation incl. the provisioning
rider path, (d) owner-SEAL attribution facts as properties, never edges.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from drydocs_lineage.extractors import DplMacExtractor, MacCoverage
from drydocs_lineage.model import LineageGraph, ProcessNode, process_id
from drydocs_lineage.writer import plan_curated

GUID_A = "11111111-aaaa-4bbb-8ccc-000000000001"   # extracted + MAC-covered
GUID_B = "22222222-aaaa-4bbb-8ccc-000000000002"   # MAC-only (unmatched)
GUID_C = "33333333-aaaa-4bbb-8ccc-000000000003"   # extracted, NO MAC set
DS_IN = "aaaa0001-dddd-4eee-8fff-000000000010"
DS_OUT = "aaaa0002-dddd-4eee-8fff-000000000020"


def _write_set(root: Path, name: str, pipeline: dict, flow: dict | None,
               extra: dict[str, dict] | None = None) -> Path:
    set_dir = root / name
    set_dir.mkdir(parents=True)
    (set_dir / "pipeline.json").write_text(json.dumps(pipeline), encoding="utf-8")
    if flow is not None:
        (set_dir / "dataset_flow.json").write_text(json.dumps(flow), encoding="utf-8")
    for fname, payload in (extra or {}).items():
        (set_dir / fname).write_text(json.dumps(payload), encoding="utf-8")
    return set_dir


def _seed_graph() -> LineageGraph:
    """A graph the inventory extractor would have produced: two DPL processes
    keyed by pipeline GUID (G15 identity), one with a G15 -seal property."""
    g = LineageGraph()
    g.add_process(ProcessNode(
        node_id=process_id("dpl", GUID_A), kind="dpl", name="dt-launcher.sh",
        properties={"seal": "88888", "env": "prod"},
    ))
    g.add_process(ProcessNode(
        node_id=process_id("dpl", GUID_C), kind="dpl", name="dt-launcher.sh",
    ))
    return g


@pytest.fixture()
def mac_root(tmp_path: Path) -> Path:
    root = tmp_path / "mac"
    _write_set(
        root, "pipe_a",
        pipeline={"pipelineId": GUID_A, "pipelineType": "batch",
                  "subType": "transformation", "ownerSealId": "88888",
                  "name": "conform-accounts"},
        flow={"pipelineId": GUID_A,
              "inputDatasets": [{"guid": DS_IN, "version": "3", "zone": "RAW",
                                 "name": "accounts_raw"}],
              "outputDatasets": [{"guid": DS_OUT, "version": "1",
                                  "zone": "TRUSTED"}]},
        extra={"schedule.json": {}, "notify.json": {}},  # rest of the 6 — counted
    )
    _write_set(
        root, "pipe_b",
        pipeline={"pipelineId": GUID_B, "pipelineType": "batch",
                  "subType": "provisioning", "ownerSealId": "77777",
                  "name": "provision-accounts"},
        flow=None,  # no dataset_flow.json — counted
    )
    return root


@pytest.fixture()
def run(mac_root: Path) -> tuple[LineageGraph, MacCoverage]:
    g = _seed_graph()
    coverage = DplMacExtractor().extract(mac_root, g)
    return g, coverage


# -- (a) GUID join + accounting ---------------------------------------------------

def test_join_and_unmatched_accounting(run) -> None:
    g, cov = run
    assert cov.sets_read == 2
    assert cov.matched == 1                       # GUID_A joined the extracted node
    assert cov.unmatched == 1                     # GUID_B staged, not dropped
    assert cov.unmatched_guids == [GUID_B]
    assert cov.dpl_without_mac == 1               # GUID_C visible as the gap
    node_b = g.processes[process_id("dpl", GUID_B)]
    assert node_b.properties["mac_only"] == "true"
    assert node_b.name == "provision-accounts"


def test_rest_of_set_counted_not_consumed(run) -> None:
    _, cov = run
    assert cov.files_ignored == 2                 # schedule.json + notify.json
    assert cov.flow_missing == 1                  # pipe_b has no dataset_flow.json


# -- (b) dataset-flow candidates on the gate-confirmed endpoints ------------------

def test_dataset_flow_candidates(run) -> None:
    g, cov = run
    pid = process_id("dpl", GUID_A)
    assert (pid, "READS_FROM", f"data#dpl_dataset:{DS_IN}") in g.rels
    assert (pid, "WRITES_TO", f"data#dpl_dataset:{DS_OUT}") in g.rels
    assert cov.reads_added == 1 and cov.writes_added == 1
    ds_in = g.data_assets[f"data#dpl_dataset:{DS_IN}"]
    assert ds_in.location == DS_IN                # identity = GUID alone (G22-f pending)
    assert ds_in.properties == {"version": "3", "zone": "RAW",
                                "dataset_name": "accounts_raw"}


def test_version_conflict_counted_first_seen_wins(mac_root: Path) -> None:
    _write_set(
        mac_root, "pipe_d",
        pipeline={"pipelineId": "44444444-aaaa-4bbb-8ccc-000000000004",
                  "subType": "transformation"},
        flow={"inputDatasets": [{"guid": DS_IN, "version": "9", "zone": "RAW"}],
              "outputDatasets": []},
    )
    g = _seed_graph()
    cov = DplMacExtractor().extract(mac_root, g)
    assert cov.dataset_version_conflicts == 1
    assert g.data_assets[f"data#dpl_dataset:{DS_IN}"].properties["version"] == "3"


# -- (c) kind derivation + the provisioning rider ---------------------------------

def test_kind_derived_where_enum_safe(run) -> None:
    g, cov = run
    node_a = g.processes[process_id("dpl", GUID_A)]
    assert node_a.properties["mac_pipeline_type"] == "batch"
    assert node_a.properties["mac_sub_type"] == "transformation"
    assert node_a.properties["mac_kind"] == "etl"
    assert cov.kind_derived == 1


def test_provisioning_takes_rider_path_never_auto_decided(run) -> None:
    g, cov = run
    node_b = g.processes[process_id("dpl", GUID_B)]
    assert "mac_kind" not in node_b.properties     # NOT decided here
    assert node_b.properties["mac_kind_rider"] == "provisioning"
    assert cov.kind_riders == 1


def test_writer_consults_mac_kind(run) -> None:
    g, _ = run
    pid = process_id("dpl", GUID_A)
    rel = (pid, "READS_FROM", f"data#dpl_dataset:{DS_IN}")
    plan = plan_curated(g, {rel})
    rows = next(params["rows"] for stmt, params in plan.statements
                if "MERGE (e:ETLProcess" in stmt)
    assert rows[0]["kind"] == "etl"               # derived, no longer blind
    assert rows[0]["token"] == GUID_A


def test_writer_default_stands_without_mac_kind() -> None:
    g = _seed_graph()
    pid = process_id("dpl", GUID_C)
    coverage = MacCoverage()  # no MAC run at all — today's behavior unchanged
    from drydocs_lineage.model import DataAssetNode
    g.add_data_asset(DataAssetNode(node_id="data#local_file:/tmp/x.dat",
                                   kind="local_file", location="/tmp/x.dat"))
    g.add_rel(pid, "WRITES_TO", "data#local_file:/tmp/x.dat")
    plan = plan_curated(g, set(g.rels))
    rows = next(params["rows"] for stmt, params in plan.statements
                if "MERGE (e:ETLProcess" in stmt)
    assert rows[0]["kind"] == "etl"
    assert coverage.kind_riders == 0


# -- (d) SEAL attribution facts, never edges --------------------------------------

def test_owner_seal_is_a_property_fact(run) -> None:
    g, cov = run
    node_a = g.processes[process_id("dpl", GUID_A)]
    assert node_a.properties["mac_owner_seal"] == "88888"
    assert node_a.properties["seal"] == "88888"    # the G15 fact sits beside it
    assert cov.seal_facts == 2
    assert cov.seal_disagreements == 0
    # no attribution edge of any kind entered the candidate graph
    assert all(rel[1] in {"READS_FROM", "WRITES_TO"} for rel in g.rels)


def test_seal_disagreement_counted(tmp_path: Path) -> None:
    root = tmp_path / "mac"
    _write_set(
        root, "pipe_a",
        pipeline={"pipelineId": GUID_A, "subType": "transformation",
                  "ownerSealId": "99999"},           # != the G15 -seal 88888
        flow={"inputDatasets": [], "outputDatasets": []},
    )
    g = _seed_graph()
    cov = DplMacExtractor().extract(root, g)
    assert cov.seal_disagreements == 1
    node = g.processes[process_id("dpl", GUID_A)]
    assert node.properties["seal"] == "88888"        # both facts kept, neither judged
    assert node.properties["mac_owner_seal"] == "99999"


# -- hygiene ----------------------------------------------------------------------

def test_invalid_and_keyless_sets_counted(tmp_path: Path) -> None:
    root = tmp_path / "mac"
    bad = root / "bad"
    bad.mkdir(parents=True)
    (bad / "pipeline.json").write_text("not json", encoding="utf-8")
    _write_set(root, "keyless", pipeline={"pipelineType": "batch"}, flow=None)
    g = _seed_graph()
    cov = DplMacExtractor().extract(root, g)
    assert cov.sets_invalid == 1
    assert cov.sets_no_guid == 1
    assert len(g.rels) == 0


def test_coverage_summary_mentions_riders(run) -> None:
    _, cov = run
    assert "riders=1" in cov.summary()
    assert "unmatched=1" in cov.summary()
