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

from drydocs_lineage.extractors import (
    DplMacExtractor,
    MacCoverage,
    parse_clone_folder,
)
from drydocs_lineage.model import LineageGraph, ProcessNode, process_id
from drydocs_lineage.writer import plan_curated

GUID_A = "11111111-aaaa-4bbb-8ccc-000000000001"  # extracted + MAC-covered
GUID_B = "22222222-aaaa-4bbb-8ccc-000000000002"  # MAC-only (unmatched)
GUID_C = "33333333-aaaa-4bbb-8ccc-000000000003"  # extracted, NO MAC set
DS_IN = "aaaa0001-dddd-4eee-8fff-000000000010"
DS_OUT = "aaaa0002-dddd-4eee-8fff-000000000020"


def _write_set(
    root: Path, name: str, pipeline: dict, flow: dict | None, extra: dict[str, dict] | None = None
) -> Path:
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
    g.add_process(
        ProcessNode(
            node_id=process_id("dpl", GUID_A),
            kind="dpl",
            name="dt-launcher.sh",
            properties={"seal": "88888", "env": "prod"},
        )
    )
    g.add_process(
        ProcessNode(
            node_id=process_id("dpl", GUID_C),
            kind="dpl",
            name="dt-launcher.sh",
        )
    )
    return g


@pytest.fixture()
def mac_root(tmp_path: Path) -> Path:
    root = tmp_path / "mac"
    _write_set(
        root,
        "pipe_a",
        pipeline={
            "pipelineId": GUID_A,
            "pipelineType": "batch",
            "subType": "transformation",
            "ownerSealId": "88888",
            "name": "conform-accounts",
        },
        flow={
            "pipelineId": GUID_A,
            "inputDatasets": [
                {"guid": DS_IN, "version": "3", "zone": "RAW", "name": "accounts_raw"}
            ],
            "outputDatasets": [{"guid": DS_OUT, "version": "1", "zone": "TRUSTED"}],
        },
        extra={"schedule.json": {}, "notify.json": {}},  # rest of the 6 — counted
    )
    _write_set(
        root,
        "pipe_b",
        pipeline={
            "pipelineId": GUID_B,
            "pipelineType": "batch",
            "subType": "provisioning",
            "ownerSealId": "77777",
            "name": "provision-accounts",
        },
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
    assert cov.matched == 1  # GUID_A joined the extracted node
    assert cov.unmatched == 1  # GUID_B staged, not dropped
    assert cov.unmatched_guids == [GUID_B]
    assert cov.dpl_without_mac == 1  # GUID_C visible as the gap
    node_b = g.processes[process_id("dpl", GUID_B)]
    assert node_b.properties["mac_only"] == "true"
    assert node_b.name == "provision-accounts"


def test_rest_of_set_counted_not_consumed(run) -> None:
    _, cov = run
    assert cov.files_ignored == 2  # schedule.json + notify.json
    assert cov.flow_missing == 1  # pipe_b has no dataset_flow.json


# -- (b) dataset-flow candidates on the gate-confirmed endpoints ------------------


def test_dataset_flow_candidates(run) -> None:
    g, cov = run
    pid = process_id("dpl", GUID_A)
    assert (pid, "READS_FROM", f"data#dpl_dataset:{DS_IN}") in g.rels
    assert (pid, "WRITES_TO", f"data#dpl_dataset:{DS_OUT}") in g.rels
    assert cov.reads_added == 1 and cov.writes_added == 1
    ds_in = g.data_assets[f"data#dpl_dataset:{DS_IN}"]
    assert ds_in.location == DS_IN  # identity = GUID alone (G22-f pending)
    assert ds_in.properties == {"version": "3", "zone": "RAW", "dataset_name": "accounts_raw"}


def test_version_conflict_counted_first_seen_wins(mac_root: Path) -> None:
    _write_set(
        mac_root,
        "pipe_d",
        pipeline={
            "pipelineId": "44444444-aaaa-4bbb-8ccc-000000000004",
            "subType": "transformation",
        },
        flow={
            "inputDatasets": [{"guid": DS_IN, "version": "9", "zone": "RAW"}],
            "outputDatasets": [],
        },
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
    assert "mac_kind" not in node_b.properties  # NOT decided here
    assert node_b.properties["mac_kind_rider"] == "provisioning"
    assert cov.kind_riders == 1


def test_writer_consults_mac_kind(run) -> None:
    g, _ = run
    pid = process_id("dpl", GUID_A)
    rel = (pid, "READS_FROM", f"data#dpl_dataset:{DS_IN}")
    plan = plan_curated(g, {rel})
    rows = next(params["rows"] for stmt, params in plan.statements if "MERGE (e:ETLProcess" in stmt)
    assert rows[0]["kind"] == "etl"  # derived, no longer blind
    assert rows[0]["token"] == GUID_A


def test_writer_default_stands_without_mac_kind() -> None:
    g = _seed_graph()
    pid = process_id("dpl", GUID_C)
    coverage = MacCoverage()  # no MAC run at all — today's behavior unchanged
    from drydocs_lineage.model import DataAssetNode

    g.add_data_asset(
        DataAssetNode(
            node_id="data#local_file:/tmp/x.dat", kind="local_file", location="/tmp/x.dat"
        )
    )
    g.add_rel(pid, "WRITES_TO", "data#local_file:/tmp/x.dat")
    plan = plan_curated(g, set(g.rels))
    rows = next(params["rows"] for stmt, params in plan.statements if "MERGE (e:ETLProcess" in stmt)
    assert rows[0]["kind"] == "etl"
    assert coverage.kind_riders == 0


# -- (d) SEAL attribution facts, never edges --------------------------------------


def test_owner_seal_is_a_property_fact(run) -> None:
    g, cov = run
    node_a = g.processes[process_id("dpl", GUID_A)]
    assert node_a.properties["mac_owner_seal"] == "88888"
    assert node_a.properties["seal"] == "88888"  # the G15 fact sits beside it
    assert cov.seal_facts == 2
    assert cov.seal_disagreements == 0
    # no attribution edge of any kind entered the candidate graph
    assert all(rel[1] in {"READS_FROM", "WRITES_TO"} for rel in g.rels)


def test_seal_disagreement_counted(tmp_path: Path) -> None:
    root = tmp_path / "mac"
    _write_set(
        root,
        "pipe_a",
        pipeline={
            "pipelineId": GUID_A,
            "subType": "transformation",
            "ownerSealId": "99999",
        },  # != the G15 -seal 88888
        flow={"inputDatasets": [], "outputDatasets": []},
    )
    g = _seed_graph()
    cov = DplMacExtractor().extract(root, g)
    assert cov.seal_disagreements == 1
    node = g.processes[process_id("dpl", GUID_A)]
    assert node.properties["seal"] == "88888"  # both facts kept, neither judged
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


def test_hand_staged_root_has_zero_clone_counters(run) -> None:
    _, cov = run
    assert cov.clone_pipeline_folders == 0
    assert cov.clone_dataset_folders == 0
    assert cov.clone_sets_missing == 0
    assert cov.clone_missing_set_guids == []


# -- promotion-clone layout (name#guid sibling folders; per-folder scope) ----------

GUID_D = "44444444-aaaa-4bbb-8ccc-000000000004"  # clone folder, set staged
GUID_E = "55555555-aaaa-4bbb-8ccc-000000000005"  # clone folder, NO set yet


def test_parse_clone_folder_casing_is_the_discriminator() -> None:
    pipe = parse_clone_folder(f"accounts_conform_aws_ingest#{GUID_D}")
    assert pipe is not None
    assert (pipe.kind, pipe.name, pipe.guid) == ("pipeline", "accounts_conform_aws_ingest", GUID_D)
    ds = parse_clone_folder(f"ACCOUNTS_RAW#{DS_IN}")
    assert ds is not None and ds.kind == "dataset" and ds.guid == DS_IN
    mixed = parse_clone_folder(f"Accounts_Raw#{DS_IN}")
    assert mixed is not None and mixed.kind == "ambiguous"
    assert parse_clone_folder("no-separator-here") is None
    assert parse_clone_folder(f"#{GUID_D}") is None


@pytest.fixture()
def clone_root(tmp_path: Path) -> Path:
    """A shape-faithful promotion-repo checkout: dataset and pipeline folders
    as SIBLINGS under src/main/resources/promotion/pipelines/."""
    pipelines = tmp_path / "clone" / "src" / "main" / "resources" / "promotion" / "pipelines"
    (pipelines / f"ACCOUNTS_RAW#{DS_IN}").mkdir(parents=True)
    (pipelines / f"ACCOUNTS_TRUSTED#{DS_OUT}").mkdir()
    staged = pipelines / f"accounts_conform_aws_ingest#{GUID_A}"
    staged.mkdir()
    (staged / "pipeline.json").write_text(
        json.dumps(
            {
                "pipelineId": GUID_A,
                "pipelineType": "batch",
                "subType": "transformation",
                "ownerSealId": "88888",
            },
        ),
        encoding="utf-8",
    )
    (staged / "dataset_flow.json").write_text(
        json.dumps(
            {
                "pipelineId": GUID_A,
                "inputDatasets": [{"guid": DS_IN, "version": "3", "zone": "RAW"}],
                "outputDatasets": [
                    {"guid": DS_OUT, "zone": "TRUSTED", "name": "flow_says_trusted"}
                ],
            },
        ),
        encoding="utf-8",
    )
    (pipelines / f"accounts_provision_aws_ingest#{GUID_E}").mkdir()  # fresh clone: no set
    return tmp_path / "clone"


def test_clone_discovery_and_missing_set_worklist(clone_root: Path) -> None:
    g = _seed_graph()
    cov = DplMacExtractor().extract(clone_root, g)
    assert cov.clone_pipeline_folders == 2
    assert cov.clone_dataset_folders == 2
    assert cov.sets_read == 1  # only the staged folder consumed
    assert cov.clone_sets_missing == 1  # the swagger per-pipeline fetch list
    assert cov.clone_missing_set_guids == [GUID_E]
    assert cov.clone_guid_mismatch == 0
    assert "missing_sets=1" in cov.summary()


def test_clone_folder_name_is_a_fact_on_the_joined_process(clone_root: Path) -> None:
    g = _seed_graph()
    g.add_process(
        ProcessNode(
            node_id=process_id("dpl", GUID_E),
            kind="dpl",
            name="dt-launcher.sh",
        )
    )
    cov = DplMacExtractor().extract(clone_root, g)
    staged = g.processes[process_id("dpl", GUID_A)]
    assert staged.properties["mac_clone_name"] == "accounts_conform_aws_ingest"
    # no set yet, but the folder name still joined the extracted process
    unstaged = g.processes[process_id("dpl", GUID_E)]
    assert unstaged.properties["mac_clone_name"] == "accounts_provision_aws_ingest"
    assert "mac_covered" not in unstaged.properties  # a name is NOT MAC coverage
    assert cov.clone_names_applied == 2


def test_dataset_folder_names_fill_gaps_never_override(clone_root: Path) -> None:
    g = _seed_graph()
    cov = DplMacExtractor().extract(clone_root, g)
    ds_in = g.data_assets[f"data#dpl_dataset:{DS_IN}"]
    assert ds_in.properties["dataset_name"] == "ACCOUNTS_RAW"  # gap filled
    ds_out = g.data_assets[f"data#dpl_dataset:{DS_OUT}"]
    assert ds_out.properties["dataset_name"] == "flow_says_trusted"  # flow entry wins
    assert cov.dataset_names_from_clone == 1


def test_clone_guid_mismatch_counted_json_wins(clone_root: Path) -> None:
    pipelines = clone_root / "src" / "main" / "resources" / "promotion" / "pipelines"
    misplaced = pipelines / f"accounts_stale_aws_ingest#{GUID_D}"
    misplaced.mkdir()
    (misplaced / "pipeline.json").write_text(
        json.dumps(
            {"pipelineId": GUID_B, "subType": "transformation"},
        ),
        encoding="utf-8",
    )
    g = _seed_graph()
    cov = DplMacExtractor().extract(clone_root, g)
    assert cov.clone_guid_mismatch == 1
    assert process_id("dpl", GUID_B) in g.processes  # json's GUID keyed the join
    assert process_id("dpl", GUID_D) not in g.processes


def test_single_clone_folder_root_is_the_per_folder_scope(clone_root: Path) -> None:
    one = (
        clone_root
        / "src"
        / "main"
        / "resources"
        / "promotion"
        / "pipelines"
        / f"accounts_conform_aws_ingest#{GUID_A}"
    )
    g = _seed_graph()
    cov = DplMacExtractor().extract(one, g)
    assert cov.clone_pipeline_folders == 1
    assert cov.sets_read == 1 and cov.matched == 1
    node = g.processes[process_id("dpl", GUID_A)]
    assert node.properties["mac_clone_name"] == "accounts_conform_aws_ingest"


def test_ambiguous_casing_counted_never_guessed(tmp_path: Path) -> None:
    root = tmp_path / "clone"
    (root / f"Accounts_Mixed#{GUID_D}").mkdir(parents=True)
    g = _seed_graph()
    cov = DplMacExtractor().extract(root, g)
    assert cov.clone_ambiguous_folders == 1
    assert cov.clone_pipeline_folders == 0
    assert cov.clone_dataset_folders == 0


def test_the_serialized_coverage_carries_a_count_not_every_pipeline_guid(tmp_path) -> None:
    """Idea-254: the artifact's coverage block is a HEADER. `clone_pipeline_guids` is one
    entry per pipeline folder the clone walk parsed - unbounded at estate scale - so
    `as_dict()` serializes the distinct COUNT and keeps the list on the object, where
    staging's registry cross-check reads it. `clone_missing_set_guids` stays a list: it is
    the fetch work list, bounded by what is missing, and it IS the finding."""
    cov = MacCoverage()
    cov.clone_pipeline_guids = ["g1", "g2", "g3"]
    cov.clone_missing_set_guids = ["g9"]
    out = cov.as_dict()
    assert "clone_pipeline_guids" not in out, "the unbounded list never reaches the header"
    assert out["clone_pipeline_guids_distinct"] == 3
    assert out["clone_missing_set_guids"] == ["g9"], "the work list stays a list"
    assert cov.clone_pipeline_guids == ["g1", "g2", "g3"], "the object keeps what staging reads"
