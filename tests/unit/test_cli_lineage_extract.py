"""LIN1 - ``drydocs lineage-extract``: the thin verb over ``drydocs_lineage.staging``.

What the verb owns and this file proves: path DISCIPLINE (an explicit input sits
inside a declared read zone or the run refuses, no override - G121), the declared
defaults (the bundled samples for hop 1, the declared zones for the optional hops,
the ``lineage/staged/`` write zone for the artifact), and the run log. The extract
itself is proven in ``test_lineage_staging.py``.

Every run here sets ``DRYDOCS_DATA_ROOT`` to a tmp directory - the zones resolve
under it, so nothing touches this machine's data root.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from typer.testing import CliRunner

from drydocs import cli as cli_mod
from drydocs.cli_shared import DEFAULT_SAMPLES_DIR

runner = CliRunner()
_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _plain(text: str) -> str:
    """ANSI stripped and whitespace collapsed: the console wraps long messages at the
    terminal width, so a phrase can straddle a line break."""
    return re.sub(r"\s+", " ", _ANSI.sub("", text))


def _artifacts(root: Path) -> list[Path]:
    return sorted((root / "lineage" / "staged").glob("lineage-*.json"))


def test_default_run_stages_the_bundled_samples_into_the_write_zone(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    result = runner.invoke(cli_mod.app, ["lineage-extract"])
    assert result.exit_code == 0, _plain(result.output)
    out = _plain(result.output)
    assert "controlm" in out and "present" in out
    assert "absent - skipped" in out  # the optional hops were asked and had nothing
    files = _artifacts(tmp_path)
    assert len(files) == 1, "one artifact per run, in the declared lineage/staged/ zone"
    data = json.loads(files[0].read_text(encoding="utf-8"))
    assert data["schema"] == "drydocs.lineage-staged.v1"
    assert data["acquisition"]["jobs"] == "bundled-samples"
    assert data["acquisition"]["variables"] in ("bundled-samples", "bundled-samples-absent")
    assert files[0].name.endswith(f"-{data['run_id']}.json")
    assert files[0].name.startswith("lineage-2")  # the UTC stamp leads - sortable
    assert data["code_commit"] not in ("", None)
    by_hop = {s["hop"]: s for s in data["sources"]}
    assert by_hop["controlm"]["path"] == str(DEFAULT_SAMPLES_DIR / "controlm_jobs__sample.csv")
    # the declared zones were LOOKED AT, and the artifact says where
    assert by_hop["dpl_mac"]["path"] == str(tmp_path / "dpl-mac")
    assert by_hop["dpl_mac"]["present"] is False and by_hop["dpl_mac"]["note"] == "not found"
    assert by_hop["dpl_registry"]["path"] == str(tmp_path / "dpl-registry")
    assert by_hop["glue"]["path"] == str(tmp_path / "glue-inventory")
    assert data["graph"]["stats"]["processes"] > 0
    # the run log names the run
    logs = list((tmp_path / "logs").rglob("*lineage_extract*"))
    assert logs, "a LoaderRunLog per run (G107)"
    assert data["run_id"] in logs[0].read_text(encoding="utf-8")


def test_an_explicit_jobs_path_outside_every_declared_zone_is_refused(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    stray = tmp_path / "somewhere-else" / "jobs.csv"
    stray.parent.mkdir()
    stray.write_text(
        "job_id,folder_id,job_name,parent_table,owner,node_id,cmd_line\n", encoding="utf-8"
    )
    result = runner.invoke(cli_mod.app, ["lineage-extract", "--jobs", str(stray)])
    assert result.exit_code == 2
    out = _plain(result.output)
    assert "REFUSED" in out and "outside every declared read zone" in out
    assert "controlm-exports" in out, "the refusal names the hop's own zone"
    assert not _artifacts(tmp_path), "a refused run writes nothing"


def test_a_jobs_path_inside_another_hops_zone_is_refused(tmp_path: Path, monkeypatch):
    """Per-hop discipline (the review's nit): a jobs CSV under dpl-mac/ is a misfiled
    file, not an acquisition route, even though dpl-mac/ IS a declared read zone."""
    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    misfiled = tmp_path / "dpl-mac" / "jobs.csv"
    misfiled.parent.mkdir()
    misfiled.write_text(
        "job_id,folder_id,job_name,parent_table,owner,node_id,cmd_line\n", encoding="utf-8"
    )
    result = runner.invoke(cli_mod.app, ["lineage-extract", "--jobs", str(misfiled)])
    assert result.exit_code == 2
    out = _plain(result.output)
    assert "not this hop's" in out and "controlm-exports" in out
    assert not _artifacts(tmp_path)


def test_an_explicit_jobs_path_inside_the_declared_export_zone_runs(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    zone = tmp_path / "controlm-exports"
    zone.mkdir()
    jobs = zone / "jobs.csv"
    jobs.write_text(
        "job_id,folder_id,job_name,parent_table,owner,node_id,cmd_line,is_current_version\n"
        '1,10,JOB_AWS,F1,svc.x,h1,"/apps/t/dt-launcher.sh -pipeline '
        '11111111-aaaa-4bbb-8ccc-000000000001 -i",Y\n',
        encoding="utf-8",
    )
    result = runner.invoke(cli_mod.app, ["lineage-extract", "--jobs", str(jobs)])
    assert result.exit_code == 0, _plain(result.output)
    data = json.loads(_artifacts(tmp_path)[0].read_text(encoding="utf-8"))
    assert data["acquisition"] == {"jobs": "declared-zone"}
    kinds = {p["kind"] for p in data["graph"]["processes"]}
    assert kinds == {"controlm_job", "dpl"}


def test_the_declared_optional_zones_are_read_when_they_hold_something(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    guid = "11111111-aaaa-4bbb-8ccc-000000000001"
    mac = tmp_path / "dpl-mac" / f"conform_accounts#{guid}"
    mac.mkdir(parents=True)
    (mac / "pipeline.json").write_text(
        json.dumps({"pipelineId": guid, "subType": "transformation", "ownerSealId": "88888"}),
        encoding="utf-8",
    )
    (mac / "dataset_flow.json").write_text(
        json.dumps(
            {
                "pipelineId": guid,
                "inputDatasets": [{"guid": "aaaa0001-dddd-4eee-8fff-000000000010", "zone": "RAW"}],
                "outputDatasets": [],
            }
        ),
        encoding="utf-8",
    )
    result = runner.invoke(cli_mod.app, ["lineage-extract"])
    assert result.exit_code == 0, _plain(result.output)
    data = json.loads(_artifacts(tmp_path)[0].read_text(encoding="utf-8"))
    by_hop = {s["hop"]: s for s in data["sources"]}
    assert by_hop["dpl_mac"]["present"] is True
    assert "dpl_mac" in data["extractors"] and "dpl_mac" in data["coverage"]
    # the samples carry no DPL job, so the MAC set stages as mac_only - counted, not lost
    assert data["coverage"]["dpl_mac"]["unmatched"] == 1


def test_an_explicit_out_dir_inside_a_read_zone_is_refused(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    read_zone = tmp_path / "dpl-mac"
    read_zone.mkdir()
    result = runner.invoke(cli_mod.app, ["lineage-extract", "--out-dir", str(read_zone / "out")])
    assert result.exit_code == 2
    assert not list(read_zone.rglob("*.json")), "nothing is written into a read zone (G81)"


def test_the_verb_is_registered_on_the_root_beside_lineage_review() -> None:
    names = {c.name for c in cli_mod.app.registered_commands}
    assert {"lineage-extract", "lineage-review"} <= names


# --- LIN2 (c): the LIN1 follow-ups that bite at load time -----------------------------


def test_every_lineage_input_zone_id_is_a_declared_zone() -> None:
    """LINEAGE_INPUT_ZONES names zone ids as string literals; before this guard a typo
    refused every input for that hop - correctly closed, wrongly. Every id resolves to a
    declared READ zone in config/data-zones.yaml or a source-registry drop (the same
    union ``read_zone_containing`` searches)."""
    from drydocs_core.data_zones import READ, all_zones

    declared = {z.id for z in all_zones() if z.mode == READ}
    for option, ids in cli_mod.LINEAGE_INPUT_ZONES.items():
        for zone_id in ids:
            assert zone_id in declared, f"--{option}: zone id {zone_id!r} is declared nowhere"


def test_the_extract_prunes_the_staged_zone_to_keep(tmp_path: Path, monkeypatch):
    """Retention (LIN2 c): after a successful write the extract keeps the newest --keep
    artifacts; 0 keeps everything; the default is DEFAULT_KEEP."""
    from drydocs_lineage.staging import DEFAULT_KEEP

    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    staged = tmp_path / "lineage" / "staged"
    staged.mkdir(parents=True)
    old = [staged / f"lineage-2025010{d}T000000Z-old{d}.json" for d in range(1, 4)]
    for p in old:
        p.write_text("{}", encoding="utf-8")
    result = runner.invoke(cli_mod.app, ["lineage-extract", "--keep", "2"])
    assert result.exit_code == 0, _plain(result.output)
    assert "pruned 2 older artifact(s)" in _plain(result.output)
    left = _artifacts(tmp_path)
    assert len(left) == 2 and old[2] in left and old[0] not in left
    result = runner.invoke(cli_mod.app, ["lineage-extract", "--keep", "0"])
    assert result.exit_code == 0 and "pruned" not in _plain(result.output)
    assert len(_artifacts(tmp_path)) == 3
    assert DEFAULT_KEEP == 10
