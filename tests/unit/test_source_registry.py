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
        DuplicateSourceIdError,
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


# --- the pk check (J21): duplicate ids refuse loudly --------------------------

def test_duplicate_source_id_refuses_naming_the_id(tmp_path: Path) -> None:
    """Last-one-wins would let file position decide the D3 gate — a duplicated
    id with different confirmed values must refuse at parse time (the
    catalog-pat / pat-catalog collision class, PORT-REPORT-e60822fc)."""
    path = _write_registry(tmp_path, [
        {"id": "twin-feed", "confirmed": True, "classification": "Internal", "source": "a"},
        {"id": "twin-feed", "confirmed": False, "classification": "Internal", "source": "b"},
    ])
    with pytest.raises(DuplicateSourceIdError) as exc:
        SourceRegistry.from_yaml(path)
    assert "twin-feed" in str(exc.value)


def test_shipped_registry_ids_are_unique() -> None:
    """The house per-entry-registry idiom (test_backlog / test_taxonomy_ontology_map):
    pin uniqueness on the shipped file itself, not only on the parser."""
    doc = yaml.safe_load(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8"))
    ids = [entry["id"] for entry in doc["sources"]]
    dupes = sorted({sid for sid in ids if ids.count(sid) > 1})
    assert not dupes, f"Duplicate source id(s) in config/source-registry.yaml: {dupes}"
    # And the parser accepts it whole (refusal path not triggered by the real file).
    assert len(SourceRegistry.from_yaml(DEFAULT_REGISTRY_PATH).ids()) == len(ids)


# --- the loader: field agrees with the N3 class binding (J21) -----------------

def test_registry_loader_fields_agree_with_class_source_id() -> None:
    """A registry entry naming a loader module must AGREE with that module's
    class-level source_id (the N3 binding) — no second, unguarded home for the
    loader<->source join. Today stg-app-fact is the one such entry; the guard
    covers every future one."""
    import importlib

    from drydocs.loaders.base import BaseLoader

    doc = yaml.safe_load(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8"))
    checked = 0
    for entry in doc["sources"]:
        loader_path = entry.get("loader")
        if not loader_path:
            continue
        module_name = loader_path.replace("/", ".").removesuffix(".py")
        mod = importlib.import_module(module_name)
        declared = {
            cls.source_id
            for cls in vars(mod).values()
            if isinstance(cls, type)
            and issubclass(cls, BaseLoader)
            and cls is not BaseLoader
            and not cls.__name__.startswith("_")
            and cls.source_id is not None
        }
        assert declared == {entry["id"]}, (
            f"registry entry {entry['id']!r} names loader {loader_path!r}, but that "
            f"module's concrete loader class(es) declare source_id {sorted(declared)} "
            f"— the loader: field must agree with the N3 class binding, not restate "
            f"it differently."
        )
        checked += 1
    assert checked >= 1, (
        "No registry entry carries a loader: field — stg-app-fact was expected to; "
        "if the field was removed, retire this guard deliberately, not by silence."
    )


# --- the shipped registry is wired as documented ------------------------------

def test_real_registry_gate_state() -> None:
    reg = SourceRegistry.from_yaml(DEFAULT_REGISTRY_PATH)
    # airflow-mwaa / autosys-export: crosswalk gates signed off 2026-07-14
    # (source-row activation only — loading still requires a loader + its own gate).
    # stg-app-fact: match-policy gate signed off 2026-07-14; the K2 loader
    # (drydocs/loaders/seal_attribution.py) was built with the flip.
    for live in ("controlm-psgmgr", "seal-extract", "catalog-pat", "airflow-mwaa",
                 "autosys-export", "stg-app-fact"):
        assert reg.is_confirmed(live), f"{live} should be confirmed"
    # rua-inventory: G19 registration; activation condition = the G22 rua-load gate
    # dpl-registry: G25 registration; G22 clauses (f)/(g) own its rulings
    for placeholder in ("oracle-schemas", "snowflake", "rua-inventory", "dpl-registry"):
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
