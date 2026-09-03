"""G96 — Control-M API-call framework acceptance guards.

Covers the item's test clauses: config resolution (in/out dirs from the
data root, no repo-tree writes), the generic-wrapper contract (JSON +
exit codes), and the discovery reference existing with per-call version
notes that stay in step with the OPERATIONS registry.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from drydocs_core.adapters.controlm import api

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = Path(api.__file__).resolve().parent


@pytest.fixture()
def data_root(tmp_path, monkeypatch):
    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path / "dataroot"))
    monkeypatch.delenv(api.CFG_ENV, raising=False)
    return tmp_path / "dataroot"


# --- config resolution -----------------------------------------------------


def test_default_dirs_resolve_from_data_root_not_repo(data_root):
    cfg = api.load_config()
    assert cfg.pull_out_dir == data_root / "remediation" / "incoming"
    assert cfg.deploy_in_dir == data_root / "remediation" / "outgoing"
    for p in (cfg.pull_out_dir, cfg.deploy_in_dir):
        assert not p.is_relative_to(REPO_ROOT), "in/out dirs must be out-of-tree"


def test_missing_default_config_is_fine_but_named_path_raises(data_root, tmp_path):
    assert api.load_config().source_path is None  # defaults, no error
    with pytest.raises(FileNotFoundError):
        api.load_config(tmp_path / "nope.cfg")


def test_sample_cfg_parses_with_blank_paths_falling_back(data_root):
    cfg = api.load_config(PKG_DIR / "controlm_api.sample.cfg")
    assert cfg.endpoint.endswith("/automation-api")
    assert "example" in cfg.endpoint, "sample endpoint must stay a placeholder"
    assert cfg.pull_out_dir == data_root / "remediation" / "incoming"
    assert cfg.templates == {}, "sample ships no live call templates"


def test_config_can_override_dirs_and_templates(data_root, tmp_path):
    cfg_file = tmp_path / "filled.cfg"
    cfg_file.write_text(
        "[paths]\npull_out_dir = {out}\n[calls]\n"
        "folder_export = exportdeffolder -arg {name} -out {out}\n".format(
            out=(tmp_path / "landing").as_posix(), name="{name}"
        ),
        encoding="utf-8",
    )
    cfg = api.load_config(cfg_file)
    assert cfg.pull_out_dir == tmp_path / "landing"
    planned = api.plan("folder_export", cfg, name="F1")
    assert not planned.capability_gap
    assert planned.argv[0] == "exportdeffolder"
    assert "F1" in planned.argv


# --- availability guardrail (clause d) -------------------------------------


def test_templateless_operation_is_reported_gap_not_silent_fallback(data_root):
    planned = api.plan("folder_export", api.load_config())
    assert planned.capability_gap and planned.argv == ()
    assert "API-CALLS.md" in planned.gap_reason
    result = api.execute(planned)
    assert not result.ok and result.capability_gap
    assert result.exit_code == api.EXIT_CAPABILITY_GAP


def test_runtime_condition_ops_always_gap_even_with_template(data_root, tmp_path):
    cfg_file = tmp_path / "c.cfg"
    cfg_file.write_text("[calls]\ncondition_add = madeup {name}\n", encoding="utf-8")
    planned = api.plan("condition_add", api.load_config(cfg_file), name="X")
    assert planned.capability_gap, "no-corpus ops must never resolve to a call"


def test_probe_has_grounded_default(data_root):
    planned = api.plan("api_probe", api.load_config())
    assert planned.argv == ("ctm", "config", "servers::get")


def test_missing_template_parameter_is_config_error(data_root, tmp_path):
    cfg_file = tmp_path / "c.cfg"
    cfg_file.write_text("[calls]\njob_export = exportdefjob {name}\n", encoding="utf-8")
    with pytest.raises(KeyError, match="name"):
        api.plan("job_export", api.load_config(cfg_file))


def test_unknown_operation_raises(data_root):
    with pytest.raises(KeyError, match="unknown operation"):
        api.plan("job_teleport", api.load_config())


# --- generic-wrapper contract (the .sh side) -------------------------------


def test_execute_returns_machine_readable_result(data_root, tmp_path):
    cfg_file = tmp_path / "c.cfg"
    cfg_file.write_text("[calls]\njob_export = exportdefjob {name}\n", encoding="utf-8")
    planned = api.plan("job_export", api.load_config(cfg_file), name="J1")

    def fake_runner(argv):
        return subprocess.CompletedProcess(argv, 0, stdout="exported", stderr="")

    result = api.execute(planned, runner=fake_runner)
    assert result.ok and result.exit_code == api.EXIT_OK
    payload = json.loads(result.to_json())
    assert payload["target_version"] == api.TARGET_VERSION
    assert {
        "ok",
        "operation",
        "transport",
        "availability",
        "argv",
        "in_dir",
        "out_dir",
        "capability_gap",
        "message",
        "returncode",
    } <= set(payload)


def test_cli_plan_only_emits_json_and_gap_exit_code(data_root, capsys):
    rc = api.main(["folder_export", "--plan-only"])
    assert rc == api.EXIT_CAPABILITY_GAP
    payload = json.loads(capsys.readouterr().out)
    assert payload["capability_gap"] is True


def test_cli_bad_cfg_path_is_config_exit(data_root, capsys, tmp_path):
    rc = api.main(["api_probe", "--cfg", str(tmp_path / "nope.cfg"), "--plan-only"])
    assert rc == api.EXIT_CONFIG
    assert "error" in json.loads(capsys.readouterr().out)


# --- G133: a tool the host cannot start is an outcome, not a traceback --------


def _raising_runner(argv):
    raise FileNotFoundError(2, "No such file or directory", argv[0])


def test_cli_missing_binary_emits_json_and_the_not_runnable_exit(data_root, capsys, tmp_path):
    """Drives the REAL default runner: the template names a binary no host has,
    so subprocess.run raises FileNotFoundError from the OS itself. Both halves
    are asserted — parseable JSON on stdout AND the contracted code — because
    the exit code alone passes on a traceback that happens to exit non-zero."""
    cfg_file = tmp_path / "c.cfg"
    cfg_file.write_text(
        "[calls]\napi_probe = drydocs-g133-no-such-binary config servers::get\n",
        encoding="utf-8",
    )
    rc = api.main(["api_probe", "--cfg", str(cfg_file)])
    out = capsys.readouterr().out
    payload = json.loads(out)  # a traceback would fail here, not at the exit code
    assert rc == api.EXIT_NOT_RUNNABLE == 4
    assert payload["ok"] is False
    assert payload["not_runnable"] is True
    assert payload["capability_gap"] is False
    assert payload["returncode"] is None
    assert "drydocs-g133-no-such-binary" in payload["message"]
    assert payload["argv"][0] == "drydocs-g133-no-such-binary"


def test_cli_runner_seam_reaches_the_entry_point(data_root, capsys):
    """Clause (e): main() takes the same Runner execute() does, so the RUN path
    of the entry point is testable and not only --plan-only."""
    seen: list[tuple[str, ...]] = []

    def recording_runner(argv):
        seen.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout="probe ok", stderr="")

    rc = api.main(["api_probe"], runner=recording_runner)
    payload = json.loads(capsys.readouterr().out)
    assert rc == api.EXIT_OK and payload["ok"] is True and payload["not_runnable"] is False
    assert seen == [("ctm", "config", "servers::get")]

    rc = api.main(["api_probe"], runner=_raising_runner)
    payload = json.loads(capsys.readouterr().out)
    assert rc == api.EXIT_NOT_RUNNABLE and payload["not_runnable"] is True


def test_not_runnable_is_distinct_from_ran_and_failed(data_root):
    """The three non-gap outcomes must not collapse into one another: a tool
    that ran and returned 1 is exit 1 with a returncode; a tool that never
    started is exit 4 with none. A PermissionError (present but not
    executable) is the same outcome as a missing one."""
    planned = api.plan("api_probe", api.load_config())

    failed = api.execute(planned, runner=lambda a: subprocess.CompletedProcess(a, 1, "", "boom"))
    assert failed.exit_code == api.EXIT_RUN_FAILED
    assert failed.returncode == 1 and failed.not_runnable is False

    absent = api.execute(planned, runner=_raising_runner)
    assert absent.exit_code == api.EXIT_NOT_RUNNABLE
    assert absent.returncode is None and absent.not_runnable is True and absent.ok is False

    def not_executable(argv):
        raise PermissionError(13, "Permission denied", argv[0])

    assert api.execute(planned, runner=not_executable).exit_code == api.EXIT_NOT_RUNNABLE


def test_exit_codes_are_distinct_and_the_readme_table_names_each():
    """Reads README prose on purpose: the table IS the contract the wrapper .sh
    is written against (J66's stated exception), so a code the module defines
    and the table does not name is a contract the operator cannot see."""
    codes = {
        api.EXIT_OK: 0,
        api.EXIT_RUN_FAILED: 1,
        api.EXIT_CONFIG: 2,
        api.EXIT_CAPABILITY_GAP: 3,
        api.EXIT_NOT_RUNNABLE: 4,
    }
    assert len(codes) == 5
    readme = (PKG_DIR / "README.md").read_text(encoding="utf-8")
    for code in codes.values():
        assert f"| {code} |" in readme, f"README exit-code table has no row for {code}"
    assert "`not_runnable`" in readme, "the JSON key list must name the new field"


def test_discovery_reference_records_both_folder_export_transports():
    """Clause (c): the folder_export row must stop implying one path."""
    doc = (PKG_DIR / "API-CALLS.md").read_text(encoding="utf-8")
    row = next(line for line in doc.splitlines() if line.startswith("| `folder_export`"))
    assert "exportdeffolder" in row and "/deploy/jobs" in row
    assert "REAL_FOLDER_ID=0" in row
    # clause (d): the cost is named in this repo's terms, not left as a curiosity
    assert "folder_id" in doc and "IS_CURRENT_VERSION" in doc
    assert "controlm_folders.cypher" in doc


# --- discovery reference (clause c) ----------------------------------------


def test_registry_carries_version_note_and_corpus_source():
    for op in api.OPERATIONS.values():
        assert api.TARGET_VERSION in op.version_note, op.name
        assert op.corpus_source, op.name


def test_discovery_reference_exists_and_covers_every_operation():
    doc = (PKG_DIR / "API-CALLS.md").read_text(encoding="utf-8")
    assert api.TARGET_VERSION in doc
    for name in api.OPERATIONS:
        assert f"`{name}`" in doc, f"API-CALLS.md missing operation {name}"


def test_no_real_values_in_committed_artifacts():
    for fname in ("api.py", "README.md", "API-CALLS.md", "controlm_api.sample.cfg"):
        text = (PKG_DIR / fname).read_text(encoding="utf-8").lower()
        assert "jpmchase" not in text and "seal" not in text, fname
