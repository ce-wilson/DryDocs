"""G121 — `load <name> --csv <path>` is a DECLARED acquisition route or it refuses.

THE SEAM. Every other input path the CLI accepts resolves through a declaration
— the chain verbs through the source registry's landing zones (G78), writes
through the data-zone invariant (G81). `load --csv` took an arbitrary path,
gated the LOADER but never the PATH, and recorded nothing about where the rows
came from. G78's own close note said so: "load --csv untouched — its contract
was copied up, not rebuilt".

THE CONTRACT (G121, the declare-or-refuse rule the
source-connection-and-run-identity gate's E1 clause ratifies as policy —
this closure builds as a plain defect and does not wait on that gate):

* a path inside a declared READ zone loads as before, and the run record
  names the zone (``acquisition_zone`` in the loader's ``run_meta``);
* a path outside every declared zone is REFUSED, exit 2, message naming
  ``drydocs landing-zones`` and the two declaration files — BEFORE the graph
  is touched;
* ``--allow-unzoned`` accepts the path anyway, and the override records
  itself (flag, path, operator) in the run_meta that feeds BOTH the
  ``:JobRun`` and the disk log — a declared escape hatch, never a silent
  side door. If the gate later rules E2 as refuse-entirely, the flag is
  removed in that build.

Resolution is ``data_zones.read_zone_containing()`` — the one runtime check
G81 already ships. No second resolution mechanism is minted here.
"""

from __future__ import annotations

import getpass
from pathlib import Path

import pytest
from typer.testing import CliRunner

from drydocs import cli as cli_mod
from drydocs_core.data_zones import read_zone_containing

runner = CliRunner()


class _StubSummary:
    def as_dict(self) -> dict:
        return {"status": "OK"}


class _StubLoader:
    """Captures what the CLI hands a loader — the run_meta channel under test."""

    source_id = None  # no source binding: stays out of the confirmed-gate path
    captured_run_meta: dict | None = None

    def __init__(self, client, adapter, *, batch_size: int = 1000, run_meta=None) -> None:
        type(self).captured_run_meta = dict(run_meta or {})

    def load(self) -> _StubSummary:
        return _StubSummary()


class _OkClient:
    def __enter__(self) -> _OkClient:
        return self

    def __exit__(self, *exc) -> bool:
        return False


@pytest.fixture()
def stub_loader(monkeypatch):
    _StubLoader.captured_run_meta = None
    monkeypatch.setitem(cli_mod.LOADER_REGISTRY, "zone_probe", _StubLoader)
    return _StubLoader


def _outside_csv(tmp_path: Path) -> Path:
    """A real file that no declared read zone contains — asserted, not assumed
    (config drift should fail as a named precondition, not an exit-code riddle)."""
    csv = tmp_path / "outside" / "rows.csv"
    csv.parent.mkdir(parents=True, exist_ok=True)
    csv.write_text("h\n", encoding="utf-8")
    assert read_zone_containing(csv) is None, "precondition: path must be unzoned"
    return csv


# -- (b) outside every zone: refuse, exit 2, before the graph ------------------


def test_unzoned_csv_is_refused_before_the_graph_is_touched(
    tmp_path: Path, monkeypatch, stub_loader
) -> None:
    csv = _outside_csv(tmp_path)

    def _never(database=None):
        raise AssertionError("the graph must not be opened for a refused --csv path")

    monkeypatch.setattr(cli_mod, "_client", _never)
    result = runner.invoke(cli_mod.app, ["load", "zone_probe", "--csv", str(csv)])
    assert result.exit_code == 2, result.output
    flat = result.output.replace("\n", "")
    assert "landing-zones" in flat  # where to see what IS declared
    assert "acquisition.drop_dir" in flat  # where to declare it
    assert "data-zones.yaml" in flat
    assert "--allow-unzoned" in flat  # the recorded escape hatch is named, not hidden
    assert stub_loader.captured_run_meta is None  # no loader was ever constructed


# -- (a) inside a declared zone: loads as today, run record names the zone -----


def test_zoned_csv_loads_and_the_run_meta_names_the_zone(
    tmp_path: Path, monkeypatch, stub_loader
) -> None:
    # conftest points DRYDOCS_DATA_ROOT at tmp_path/"data-root"; pat:people-report
    # declares drop_dir pat/ under it (the same zone test_chain_inputs uses).
    zone_dir = tmp_path / "data-root" / "pat"
    zone_dir.mkdir(parents=True)
    csv = zone_dir / "rows.csv"
    csv.write_text("h\n", encoding="utf-8")
    zone = read_zone_containing(csv)
    # pat/ is a drop_dir SHARED by more than one pat:* source; the zone that
    # resolves is whichever declares first. The contract is "names the zone it
    # resolved", so the assertion pins the resolved id, not a hand-picked one.
    assert zone is not None and zone.id.startswith("pat:"), "precondition: declared zone"

    monkeypatch.setattr(cli_mod, "_client", lambda database=None: _OkClient())
    result = runner.invoke(cli_mod.app, ["load", "zone_probe", "--csv", str(csv)])
    assert result.exit_code == 0, result.output
    meta = stub_loader.captured_run_meta
    assert meta is not None
    assert meta["acquisition_zone"] == zone.id
    assert meta["acquisition_path"] == str(csv)
    assert "acquisition_override" not in meta  # a zoned load is not an override


# -- (b) the override: explicit, and recorded — never silent -------------------


def test_override_is_recorded_flag_path_operator(tmp_path: Path, monkeypatch, stub_loader) -> None:
    csv = _outside_csv(tmp_path)
    monkeypatch.setattr(cli_mod, "_client", lambda database=None: _OkClient())
    result = runner.invoke(
        cli_mod.app, ["load", "zone_probe", "--csv", str(csv), "--allow-unzoned"]
    )
    assert result.exit_code == 0, result.output
    meta = stub_loader.captured_run_meta
    assert meta is not None
    assert meta["acquisition_override"] == "--allow-unzoned"
    assert meta["acquisition_path"] == str(csv)
    try:
        expected_operator = getpass.getuser()
    except Exception:
        expected_operator = ""
    assert meta["acquisition_operator"] == expected_operator
    # and the console said so too — the operator sees the override at the prompt
    assert "override" in result.output.replace("\n", "").lower()


# -- the record channel: run_meta reaches BOTH the :JobRun and the disk log ----


class _RecordingClient:
    def __init__(self) -> None:
        self.run_calls: list[tuple[str, dict]] = []

    def run(self, cypher: str, params: dict | None = None, **kwargs) -> list[dict]:
        self.run_calls.append((cypher, {**(params or {}), **kwargs}))
        return []


class _PathAdapter:
    path = Path("somewhere/rows.csv")


def test_run_meta_reaches_the_job_run_and_the_disk_log(tmp_path: Path) -> None:
    from drydocs.loaders.controlm_hosts import ControlMHostsLoader

    meta = {"acquisition_override": "--allow-unzoned", "acquisition_operator": "op"}
    client = _RecordingClient()
    loader = ControlMHostsLoader(client, _PathAdapter(), run_meta=meta)

    loader._open_run()
    job_runs = [(c, p) for c, p in client.run_calls if "JobRun" in c]
    assert len(job_runs) == 1
    cypher, params = job_runs[0]
    assert "run += $run_meta" in cypher  # the record is ON the :JobRun, not beside it
    assert params["run_meta"] == meta

    log = loader._open_run_log()
    assert log is not None
    try:
        assert log.meta["acquisition_override"] == "--allow-unzoned"
    finally:
        log.close()  # detaches the global-logger handler AND flushes the header
    header = Path(log.path).read_text(encoding="utf-8")
    assert "acquisition_override" in header and "--allow-unzoned" in header
