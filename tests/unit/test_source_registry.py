"""Source registry confirmed-gate (D3) — no Neo4j required.

Acceptance: *loading a source with confirmed:false fails fast with a clear message.*
Covered at two levels: the registry guard (`require_confirmed`) and the CLI path
(`drydocs load ...` exits 2 before touching Neo4j when its source is unconfirmed).
"""
from __future__ import annotations

from pathlib import Path

import pytest

try:
    import yaml

    from drydocs_core.source_registry import (
        SourceRegistry,
        UnconfirmedSourceError,
        UnknownSourceError,
        DEFAULT_REGISTRY_PATH,
    )

    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False

pytestmark = pytest.mark.skipif(not _AVAILABLE, reason="PyYAML not installed")


def _write_registry(tmp_path: Path, sources: list[dict]) -> Path:
    doc = {"schema": "drydocs.source-registry.v1", "sources": sources}
    p = tmp_path / "source-registry.yaml"
    p.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return p


# --- the gate -----------------------------------------------------------------

def test_confirmed_source_passes(tmp_path: Path) -> None:
    reg = SourceRegistry.from_yaml(_write_registry(tmp_path, [
        {"id": "live-feed", "confirmed": True, "classification": "Internal", "source": "x"},
    ]))
    assert reg.is_confirmed("live-feed")
    assert reg.require_confirmed("live-feed").id == "live-feed"  # no raise


def test_unconfirmed_source_fails_fast_with_clear_message(tmp_path: Path) -> None:
    reg = SourceRegistry.from_yaml(_write_registry(tmp_path, [
        {"id": "autosys-export", "confirmed": False, "classification": "Internal",
         "source": "autosys (TBD)", "crosswalk": "external/orchestration/autosys/README.md"},
    ]))
    assert not reg.is_confirmed("autosys-export")
    with pytest.raises(UnconfirmedSourceError) as exc:
        reg.require_confirmed("autosys-export")
    msg = str(exc.value)
    assert "autosys-export" in msg
    assert "confirmed: false" in msg
    assert "external/orchestration/autosys/README.md" in msg  # points to the crosswalk


def test_missing_confirmed_defaults_to_unconfirmed(tmp_path: Path) -> None:
    # A source with no `confirmed:` key is treated as NOT confirmed (fail-closed).
    reg = SourceRegistry.from_yaml(_write_registry(tmp_path, [
        {"id": "no-flag", "classification": "Internal", "source": "x"},
    ]))
    with pytest.raises(UnconfirmedSourceError):
        reg.require_confirmed("no-flag")


def test_unknown_source_raises(tmp_path: Path) -> None:
    reg = SourceRegistry.from_yaml(_write_registry(tmp_path, []))
    with pytest.raises(UnknownSourceError):
        reg.require_confirmed("ghost")


# --- the shipped registry is wired as documented ------------------------------

def test_real_registry_gate_state() -> None:
    reg = SourceRegistry.from_yaml(DEFAULT_REGISTRY_PATH)
    for live in ("controlm-psgmgr", "seal-extract", "catalog-pat"):
        assert reg.is_confirmed(live), f"{live} should be confirmed"
    for placeholder in ("autosys-export", "airflow-mwaa", "oracle-schemas", "snowflake"):
        assert not reg.is_confirmed(placeholder), f"{placeholder} should be unconfirmed"
        with pytest.raises(UnconfirmedSourceError):
            reg.require_confirmed(placeholder)


# --- CLI fail-fast: load <loader> exits 2 before touching Neo4j ---------------

def test_cli_load_blocks_unconfirmed_source(tmp_path: Path, monkeypatch) -> None:
    """If a loader's source is unconfirmed, `drydocs load` exits 2 with the gate
    message — before any adapter is opened or Neo4j is contacted."""
    typer_testing = pytest.importorskip("typer.testing")
    from drydocs import cli

    # Flip the Control-M source to unconfirmed via an injected registry.
    reg = SourceRegistry.from_yaml(_write_registry(tmp_path, [
        {"id": "controlm-psgmgr", "confirmed": False, "classification": "Internal",
         "source": "oracle:psgmgr"},
    ]))
    monkeypatch.setattr(cli, "_registry", reg)

    runner = typer_testing.CliRunner()
    # --csv points nowhere on purpose: the gate must fire BEFORE the adapter check.
    args = ["load", "controlm_folders", "--csv", str(tmp_path / "nope.csv")]
    result = runner.invoke(cli.app, args)
    assert result.exit_code == 2
    assert "not confirmed" in result.stdout
    assert "controlm-psgmgr" in result.stdout
