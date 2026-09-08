"""N26 — the registry view organized by class, and the registry verb.

One generator (``drydocs_core.registry_view``) feeds the load map's By-class view,
the rendered ``docs/plan/load-map.html`` and ``drydocs registry <loader>``, so the
derived predicates are tested HERE, once, on fixtures built from the real shapes,
and the two consumers are tested only for wiring:

* the derived facts — application-id state, replica-ness (four states, never a
  boolean), ontology class from RULED map entries (node classes, not edge types),
  the displaced predicate that makes the DPL row visibly odd, the constant-field
  probe that renders the ``asset_type`` default as UNCLASSIFIED;
* the third-loader case (acceptance f): a fixture loader registered through
  ``register_loaders`` binding a dataset two producer loaders already bind shows
  up on both of their reports, and the registry is restored after;
* the stamp (acceptance g): the blob id is git's own (``git hash-object``), the
  digest is deterministic, and the verb and the render hash the SAME input tuple;
* the verb's contract — exit 2 on an unknown loader, one JSON document on
  ``--json`` carrying the tree stamp and the digest. Output IS the contract here,
  so the test reads CLI output on purpose (J37's stated exception) with ANSI
  stripped, and never enumerates commands from it.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from drydocs_core import registry_view as rv

REPO_ROOT = Path(__file__).resolve().parents[2]
runner = CliRunner()
_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _plain(text: str) -> str:
    return re.sub(r"\s+", " ", _ANSI.sub("", text))


# ---- derived facts -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "state"),
    [
        ("[seal-id]", rv.APPLICATION_ID_PLACEHOLDER),
        ("70001", rv.APPLICATION_ID_DECLARED),
        (None, rv.APPLICATION_ID_ABSENT),
        ("", rv.APPLICATION_ID_ABSENT),
        ("~", rv.APPLICATION_ID_ABSENT),
    ],
)
def test_application_id_state_reads_the_placeholder_as_its_own_state(value, state):
    assert rv.application_id_state(value) == state


def test_replica_state_is_four_states_never_a_boolean():
    original = {"id": "a", "system": "s", "origin": "s"}
    corroborated = {"id": "b", "system": "replica-db", "origin": "src", "authority": "ADS"}
    uncorroborated = {"id": "c", "system": "replica-db", "origin": "src"}
    ads_same = {"id": "d", "system": "s", "origin": "s", "authority": "ADS"}
    assert rv.replica_state(original)["state"] == rv.ORIGINAL
    assert rv.replica_state(corroborated)["state"] == rv.REPLICA
    assert rv.replica_state(corroborated)["corroboration"] == "authority: ADS"
    assert rv.replica_state(uncorroborated)["state"] == rv.REPLICA_UNCORROBORATED
    assert rv.replica_state(ads_same)["state"] == rv.ADS_WITHOUT_DISTINCT_ORIGIN


def test_ontology_class_is_the_node_classes_of_ruled_entries_not_the_edge_type():
    rows = [
        {"id": "x", "status": "applied", "label": "CONTAINS_FOLDER",
         "from_node": "ControlMApplication", "to_node": "ControlMFolder"},
        {"id": "y", "status": "proposed", "label": "READS", "from_node": "Job", "to_node": "Dataset"},
        {"id": "z", "status": "rejected", "label": "OLD", "from_node": "Gone", "to_node": "Gone"},
    ]  # fmt: skip
    oc = rv.ontology_class(rows)
    assert oc["state"] == "classified"
    assert oc["classes"] == ["ControlMApplication", "ControlMFolder"]
    assert oc["relationships"] == ["CONTAINS_FOLDER"]
    assert oc["pending"] == 1


@pytest.mark.parametrize(
    ("rows", "reason_fragment"),
    [
        ([], "no map entry"),
        ([{"id": "p", "status": "proposed", "label": "R", "from_node": "A", "to_node": "B"}], "proposed, none ruled"),
        ([{"id": "r", "status": "rejected", "label": "R", "from_node": "A", "to_node": "B"}], "none is applied or confirmed"),
    ],
)  # fmt: skip
def test_ontology_class_unclassified_says_why(rows, reason_fragment):
    oc = rv.ontology_class(rows)
    assert oc["state"] == rv.UNCLASSIFIED
    assert oc["classes"] == []
    assert reason_fragment in oc["reason"]


def test_constant_field_is_the_bare_default_rendered_unclassified():
    datasets = [{"id": str(i), "asset_type": "dcat:Dataset"} for i in range(3)]
    probe = rv.constant_fields(datasets, "asset_type")
    assert probe == {
        "field": "asset_type",
        "constant": True,
        "value": "dcat:Dataset",
        "rows": 3,
        "of": 3,
    }
    datasets[0]["asset_type"] = "dcat:Catalog"
    assert rv.constant_fields(datasets, "asset_type")["constant"] is False


def test_displaced_is_a_singleton_whose_category_has_a_home_under_another_layer():
    """The DPL shape: one Data Asset row under technology while data holds four."""
    systems = {
        "d1": {"id": "d1", "layer": "data"},
        "t1": {"id": "t1", "layer": "technology"},
    }
    datasets = [
        *({"id": f"data-{i}", "system": "d1", "taxonomy_category": "Data Asset"} for i in range(4)),
        {"id": "dpl:dataset-registry", "system": "t1", "taxonomy_category": "Data Asset"},
        {"id": "arch-1", "system": "t1", "taxonomy_category": "Architecture"},
        {"id": "arch-2", "system": "t1", "taxonomy_category": "Architecture"},
        {"id": "gov-only", "system": "t1", "taxonomy_category": "ITSM / Gov"},
    ]
    m = rv.layer_category_matrix(datasets, systems)
    displaced = {r["dataset"]: r for r in m["displaced"]}
    assert set(displaced) == {
        "dpl:dataset-registry"
    }, "a singleton with no home elsewhere is not displaced"
    assert displaced["dpl:dataset-registry"]["home_layer"] == "data"
    assert displaced["dpl:dataset-registry"]["home_rows"] == 4
    assert {(s["layer"], s["category"]) for s in m["singletons"]} >= {
        ("technology", "Data Asset"),
        ("technology", "ITSM / Gov"),
    }


def test_the_shipped_tree_flags_the_dpl_row_as_displaced():
    """The acceptance case measured on the real registry — not a fixture claim."""
    import yaml

    doc = yaml.safe_load(
        (REPO_ROOT / "config" / "source-registry.yaml").read_text(encoding="utf-8")
    )
    systems = {s["id"]: s for s in doc["systems"]}
    m = rv.layer_category_matrix(doc["datasets"], systems)
    assert "dpl:dataset-registry" in {r["dataset"] for r in m["displaced"]}


# ---- the third loader (acceptance f) ---------------------------------------------------


def test_a_third_loader_bound_to_the_same_dataset_appears_on_every_report():
    from drydocs.cli_shared import LOADER_REGISTRY, register_loaders

    bound = {n: c.source_id for n, c in LOADER_REGISTRY.items()}
    shared = next(
        sid
        for sid in set(bound.values())
        if sid and sum(1 for v in bound.values() if v == sid) >= 2
    )
    firsts = sorted(n for n, sid in bound.items() if sid == shared)
    base = LOADER_REGISTRY[firsts[0]]

    class ThirdProbe(base):  # type: ignore[misc,valid-type]
        name = "third_probe"
        source_id = shared

    before = dict(LOADER_REGISTRY)
    try:
        register_loaders({"third_probe": ThirdProbe})
        bound = {n: c.source_id for n, c in LOADER_REGISTRY.items()}
        report = rv.loader_binding(
            firsts[0], declared=shared, effective=shared, bound_loaders=bound,
            dataset=None, system=None, map_rows=(),
        )  # fmt: skip
        assert "third_probe" in report["other_loaders_bound_here"]
        assert set(firsts[1:]) <= set(report["other_loaders_bound_here"])
        third = rv.loader_binding(
            "third_probe", declared=shared, effective=shared, bound_loaders=bound,
            dataset=None, system=None, map_rows=(),
        )  # fmt: skip
        assert third["other_loaders_bound_here"] == firsts
    finally:
        LOADER_REGISTRY.clear()
        LOADER_REGISTRY.update(before)
        from drydocs.cli_shared import _rederive_loader_views

        _rederive_loader_views()
    assert "third_probe" not in LOADER_REGISTRY


def test_overlay_applied_is_declared_versus_effective():
    report = rv.loader_binding(
        "l", declared="a", effective="b", bound_loaders={"l": "b"},
        dataset=None, system=None, map_rows=(),
    )  # fmt: skip
    assert report["overlay_applied"] is True
    assert report["other_loaders_bound_here"] == []


# ---- the stamp (acceptance g) -----------------------------------------------------------


def test_git_blob_id_is_gits_own(tmp_path: Path):
    data = b"systems: []\ndatasets: []\n"
    expected = (
        subprocess.run(
            ["git", "hash-object", "--stdin"], input=data, capture_output=True, check=True
        )
        .stdout.decode()
        .strip()
    )
    assert rv.git_blob_id(data) == expected


def test_input_provenance_is_deterministic_and_crlf_neutral(tmp_path: Path):
    (tmp_path / "a.yaml").write_bytes(b"x: 1\ny: 2\n")
    (tmp_path / "d").mkdir()
    (tmp_path / "d" / "z.yaml").write_bytes(b"k: v\n")
    (tmp_path / "d" / "ignored.txt").write_bytes(b"not yaml")
    one = rv.input_provenance(tmp_path, ("a.yaml", "d", "missing.yaml"))
    assert [r["path"] for r in one["inputs"]] == ["a.yaml", "d/z.yaml"]
    (tmp_path / "a.yaml").write_bytes(b"x: 1\r\ny: 2\r\n")
    two = rv.input_provenance(tmp_path, ("a.yaml", "d"))
    assert two["digest"] == one["digest"], "CRLF is a checkout artifact, not content"
    (tmp_path / "a.yaml").write_bytes(b"x: 1\ny: 3\n")
    assert rv.input_provenance(tmp_path, ("a.yaml", "d"))["digest"] != one["digest"]


def test_the_render_and_the_verb_hash_the_same_inputs():
    """One tuple, imported by both — never two lists that agree today."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "render_load_map", REPO_ROOT / "scripts" / "render_load_map.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    assert mod.INPUTS is rv.LOAD_MAP_INPUTS


def test_the_committed_load_map_carries_the_digest_of_its_inputs():
    """The view stamps the tree: the digest in the committed JSON is the digest
    of the inputs as they sit in this checkout (the drift test's other half)."""
    data = json.loads(
        (REPO_ROOT / "web" / "src" / "generated" / "load-map.json").read_text(encoding="utf-8")
    )
    live = rv.input_provenance(REPO_ROOT, rv.LOAD_MAP_INPUTS)
    assert data["provenance"]["digest"] == live["digest"]
    assert data["class_view"]["asset_type"]["field"] == "asset_type"


# ---- the verb ---------------------------------------------------------------------------


def test_registry_verb_refuses_an_unknown_loader_with_exit_2():
    from drydocs import cli as cli_mod

    result = runner.invoke(cli_mod.app, ["registry", "no_such_loader"])
    assert result.exit_code == 2
    assert "Unknown loader 'no_such_loader'" in _plain(result.output)


def test_registry_verb_json_is_one_document_stamped_with_the_tree():
    from drydocs import cli as cli_mod
    from drydocs.cli_shared import LOADER_REGISTRY, LOADER_SOURCE

    name = next(n for n, sid in LOADER_SOURCE.items() if sid is not None)
    result = runner.invoke(cli_mod.app, ["registry", name, "--json"])
    assert result.exit_code == 0, result.output
    doc = json.loads(_ANSI.sub("", result.output))
    assert doc["loader"] == name
    assert doc["declared_source_id"] == LOADER_REGISTRY[name].source_id
    assert doc["dataset_state"] == "registered"
    assert set(doc["dataset"]) == {
        "layer",
        "taxonomy_category",
        "acquisition",
        "replica",
        "ontology_class",
    }
    assert set(doc["tree"]) == {"commit", "branch", "dirty"}
    assert doc["inputs_digest"] == rv.input_provenance(REPO_ROOT, rv.LOAD_MAP_INPUTS)["digest"]
    assert isinstance(doc["commands"], list)
