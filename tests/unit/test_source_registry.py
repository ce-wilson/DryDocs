"""Source registry v2 confirmed-gate + D4 reconcile guard + D2 overlay — no Neo4j.

Acceptance (gate source-registry-v2, SIGNED OFF 2026-07-31; built at N9):
- loading a source with confirmed:false fails fast with a clear message
  (registry guard + CLI path);
- duplicate ids refuse at parse time (J21 pk check, carried forward);
- RETIRED legacy flat ids refuse everywhere: registration, lookup, and the
  loader-source overlay (D4 — the catalog-pat / pat-catalog collision class);
- the per-side loader→dataset overlay wins over class defaults and is guarded
  to resolve to registered dataset ids (D2, extending the J21 agreement guard);
- URNs are DERIVED, never hand-maintained (D3 + Q2: env always prod);
- the runtime registry is the UNION of the pipeline and doc ledgers (one home
  per source — doc loaders still gate).
"""
from __future__ import annotations

from pathlib import Path

import pytest

try:
    import yaml

    from drydocs_core.source_registry import (
        DuplicateSourceIdError,
        OverlayBindingError,
        RetiredSourceIdError,
        SourceRegistry,
        UnconfirmedSourceError,
        UnknownSourceError,
        DEFAULT_REGISTRY_PATH,
    )

    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False

pytestmark = pytest.mark.skipif(not _AVAILABLE, reason="PyYAML not installed")


def _write_registry(
    tmp_path: Path,
    datasets: list[dict],
    *,
    systems: list[dict] | None = None,
    retired: list[dict] | None = None,
    name: str = "source-registry.yaml",
) -> Path:
    doc: dict = {"schema": "drydocs.source-registry.v2", "datasets": datasets}
    if systems is not None:
        doc["systems"] = systems
    if retired is not None:
        doc["retired"] = retired
    p = tmp_path / name
    p.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return p


# --- the gate -----------------------------------------------------------------

def test_confirmed_source_passes(tmp_path: Path) -> None:
    reg = SourceRegistry.from_yaml(_write_registry(tmp_path, [
        {"id": "sys:live-feed", "confirmed": True, "system": "sys", "artifact": "live-feed"},
    ]))
    assert reg.is_confirmed("sys:live-feed")
    assert reg.require_confirmed("sys:live-feed").id == "sys:live-feed"  # no raise


def test_unconfirmed_source_fails_fast_with_clear_message(tmp_path: Path) -> None:
    reg = SourceRegistry.from_yaml(_write_registry(tmp_path, [
        {"id": "autosys:export", "confirmed": False, "system": "autosys",
         "artifact": "export", "crosswalk": "external/orchestration/autosys/README.md"},
    ]))
    assert not reg.is_confirmed("autosys:export")
    with pytest.raises(UnconfirmedSourceError) as exc:
        reg.require_confirmed("autosys:export")
    msg = str(exc.value)
    assert "autosys:export" in msg
    assert "confirmed: false" in msg
    assert "external/orchestration/autosys/README.md" in msg  # points to the crosswalk


def test_missing_confirmed_defaults_to_unconfirmed(tmp_path: Path) -> None:
    # A dataset with no `confirmed:` key is treated as NOT confirmed (fail-closed).
    reg = SourceRegistry.from_yaml(_write_registry(tmp_path, [
        {"id": "sys:no-flag", "system": "sys", "artifact": "no-flag"},
    ]))
    with pytest.raises(UnconfirmedSourceError):
        reg.require_confirmed("sys:no-flag")


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
        {"id": "sys:twin-feed", "confirmed": True, "system": "sys", "artifact": "twin-feed"},
        {"id": "sys:twin-feed", "confirmed": False, "system": "sys", "artifact": "twin-feed"},
    ])
    with pytest.raises(DuplicateSourceIdError) as exc:
        SourceRegistry.from_yaml(path)
    assert "sys:twin-feed" in str(exc.value)


def test_shipped_registry_ids_are_unique() -> None:
    """The house per-entry-registry idiom: pin uniqueness on the shipped file
    itself, not only on the parser — across systems, datasets AND the doc
    ledger the runtime view unions in."""
    doc = yaml.safe_load(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8"))
    ds_ids = [entry["id"] for entry in doc["datasets"]]
    sys_ids = [entry["id"] for entry in doc["systems"]]
    for ids, kind in ((ds_ids, "dataset"), (sys_ids, "system")):
        dupes = sorted({sid for sid in ids if ids.count(sid) > 1})
        assert not dupes, f"Duplicate {kind} id(s) in config/source-registry.yaml: {dupes}"
    # And the parser accepts the whole union (datasets + doc-ledger rows).
    reg = SourceRegistry.from_yaml(DEFAULT_REGISTRY_PATH)
    assert set(ds_ids) <= set(reg.ids())
    assert set(sys_ids) == set(reg.system_ids())


# --- D4: retired ids refuse everywhere ----------------------------------------

RETIRED_FIXTURE = [{"id": "catalog-pat",
                    "replaced_by": ["pat:product-catalog", "pat:people-report"],
                    "reason": "T19 split"}]


def test_retired_id_lookup_names_the_replacement(tmp_path: Path) -> None:
    reg = SourceRegistry.from_yaml(_write_registry(
        tmp_path,
        [{"id": "pat:product-catalog", "confirmed": True, "system": "pat",
          "artifact": "product-catalog", "replaces": "catalog-pat"}],
        retired=RETIRED_FIXTURE,
    ))
    with pytest.raises(RetiredSourceIdError) as exc:
        reg.require_confirmed("catalog-pat")
    msg = str(exc.value)
    assert "catalog-pat" in msg and "pat:product-catalog" in msg


def test_retired_id_cannot_be_reregistered(tmp_path: Path) -> None:
    """A row registered UNDER a retired id refuses at parse time — a retired
    string never comes back with a different meaning (D4)."""
    path = _write_registry(
        tmp_path,
        [{"id": "catalog-pat", "confirmed": True, "system": "pat", "artifact": "x"}],
        retired=RETIRED_FIXTURE,
    )
    with pytest.raises(RetiredSourceIdError):
        SourceRegistry.from_yaml(path)


def test_shipped_registry_retires_the_full_v1_id_set() -> None:
    """The N9 acceptance names the retirement explicitly — including BOTH legacy
    strings of the T19 collision — and every replaces: back-pointer must agree
    with the refusal list."""
    reg = SourceRegistry.from_yaml(DEFAULT_REGISTRY_PATH)
    retired = set(reg.retired_ids())
    for legacy in ("controlm-psgmgr", "catalog-pat", "pat-catalog", "seal-extract",
                   "controlm-xml-export", "autosys-export", "airflow-mwaa",
                   "software-registry", "depgraph-snapshot", "design-docs",
                   "rua-inventory", "dpl-registry", "snowflake-data-catalog",
                   "code-repo", "oracle-schemas", "snowflake", "stg-app-fact"):
        assert legacy in retired, f"v1 id {legacy!r} missing from the retired list"
        with pytest.raises(RetiredSourceIdError):
            reg.get(legacy)
    # back-pointer agreement: every dataset `replaces:` value is a retired id,
    # and every retired replacement resolves to a registered dataset.
    doc = yaml.safe_load(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8"))
    ds_ids = {e["id"] for e in doc["datasets"]}
    for entry in doc["datasets"]:
        rep = entry.get("replaces")
        if rep:
            assert rep in retired, f"{entry['id']}: replaces {rep!r} not on the retired list"
    for r in doc["retired"]:
        for new_id in r.get("replaced_by") or []:
            assert new_id in ds_ids, (
                f"retired {r['id']!r} points at {new_id!r}, which is not a registered dataset"
            )


# --- D3: the derived URN ------------------------------------------------------

def test_urn_is_derived_lowercase_prod(tmp_path: Path) -> None:
    reg = SourceRegistry.from_yaml(_write_registry(tmp_path, [
        {"id": "seal@[db].psgmgr.cm_escalation_db", "system": "psgmgr",
         "origin": "seal", "artifact": "CM_ESCALATION_DB", "confirmed": False},
    ]))
    src = reg.get("seal@[db].psgmgr.cm_escalation_db")
    assert src.urn == "urn:drydocs:dataset:(psgmgr,cm_escalation_db,prod)"


def test_hand_maintained_urn_is_refused(tmp_path: Path) -> None:
    path = _write_registry(tmp_path, [
        {"id": "sys:x", "system": "sys", "artifact": "x",
         "urn": "urn:drydocs:dataset:(sys,x,prod)"},
    ])
    with pytest.raises(ValueError, match="DERIVED"):
        SourceRegistry.from_yaml(path)


# --- D2: the loader-source overlay --------------------------------------------

def _write_overlay(tmp_path: Path, overrides: dict) -> Path:
    p = tmp_path / "loader-source-overlay.yaml"
    p.write_text(
        yaml.safe_dump(
            {"schema": "drydocs.loader-source-overlay.v1", "overrides": overrides}
        ),
        encoding="utf-8",
    )
    return p


def test_overlay_wins_over_class_default(tmp_path: Path) -> None:
    reg_path = _write_registry(tmp_path, [
        {"id": "sys:default", "confirmed": True, "system": "sys", "artifact": "default"},
        {"id": "sys:override", "confirmed": True, "system": "sys", "artifact": "override"},
    ])
    ov = _write_overlay(tmp_path, {"some_loader.v1": "sys:override"})
    reg = SourceRegistry.from_yaml(reg_path, overlay_path=ov)
    assert reg.effective_source_id("some_loader.v1", "sys:default") == "sys:override"
    assert reg.effective_source_id("other_loader.v1", "sys:default") == "sys:default"


def test_overlay_refuses_unregistered_and_retired_ids(tmp_path: Path) -> None:
    reg_path = _write_registry(
        tmp_path,
        [{"id": "pat:product-catalog", "confirmed": True, "system": "pat",
          "artifact": "product-catalog"}],
        retired=RETIRED_FIXTURE,
    )
    with pytest.raises(OverlayBindingError, match="unregistered"):
        SourceRegistry.from_yaml(
            reg_path, overlay_path=_write_overlay(tmp_path, {"l.v1": "sys:ghost"})
        )
    with pytest.raises(OverlayBindingError, match="RETIRED"):
        SourceRegistry.from_yaml(
            reg_path, overlay_path=_write_overlay(tmp_path, {"l.v1": "catalog-pat"})
        )


def test_shipped_overlay_is_empty_and_parses() -> None:
    """Producer ships an EMPTY overlay (class defaults are already the v2 ids);
    the file existing and parsing is the company rebind seam's contract."""
    reg = SourceRegistry.from_yaml(DEFAULT_REGISTRY_PATH)
    assert reg.effective_source_id("controlm_folders.v1",
                                   "controlm@[db].psgmgr.cm_def_vtab") \
        == "controlm@[db].psgmgr.cm_def_vtab"


# --- the doc-ledger union (one home per source) --------------------------------

def test_doc_ledger_union_gates_doc_corpora() -> None:
    reg = SourceRegistry.from_yaml(DEFAULT_REGISTRY_PATH)
    bmc = reg.require_confirmed("bmc-docs")          # gate bmc-docs-lexical-load
    assert bmc.home == "doc-registry"
    assert bmc.urn is None                            # doc corpora keep docmeta identity
    reg.require_confirmed("essential-graphrag")
    with pytest.raises(UnconfirmedSourceError) as exc:
        reg.require_confirmed("fcdo-frameworks")      # crosswalk gate not drafted (W1)
    assert "doc-source-registry" in str(exc.value)


def test_temp_registry_does_not_union_shipped_ledgers(tmp_path: Path) -> None:
    """A test-written registry gets exactly what it wrote — the shipped doc
    ledger and overlay merge in ONLY for the default path."""
    reg = SourceRegistry.from_yaml(_write_registry(tmp_path, [
        {"id": "sys:only", "confirmed": True, "system": "sys", "artifact": "only"},
    ]))
    assert reg.ids() == ["sys:only"]


# --- the loader: field agrees with the N3 class binding (J21) -----------------

def test_registry_loader_fields_agree_with_class_source_id() -> None:
    """A registry entry naming a loader module must AGREE with that module's
    class-level source_id (the N3 binding) — no second, unguarded home for the
    loader<->source join. Today the stg_app_fact dataset is the one such entry;
    the guard covers every future one."""
    import importlib

    from drydocs.loaders.base import BaseLoader

    doc = yaml.safe_load(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8"))
    checked = 0
    for entry in doc["datasets"]:
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
        "No registry dataset carries a loader: field — the stg_app_fact row was "
        "expected to; if the field was removed, retire this guard deliberately, "
        "not by silence."
    )


# --- the shipped registry is wired as documented ------------------------------

def test_real_registry_gate_state() -> None:
    reg = SourceRegistry.from_yaml(DEFAULT_REGISTRY_PATH)
    # Q6 transfers (previously signed gates ride the rename); the per-row split
    # also made cm_avg_run's 2026-07-14 sign-off (P2) finally visible.
    for live in ("controlm@[db].psgmgr.cm_def_vtab",
                 "controlm@[db].psgmgr.cm_def_vjob",
                 "controlm@[db].psgmgr.cm_hosts",
                 "controlm@[db].psgmgr.cm_avg_run",
                 "seal:app-extract", "pat:product-catalog", "pat:people-report",
                 "airflow:dag-export", "autosys:export",
                 "controlm@[db].drydocs_stg.stg_app_fact",
                 "repo:software-registry", "repo:depgraph-snapshot",
                 "repo:design-docs"):
        assert reg.is_confirmed(live), f"{live} should be confirmed"
    # Everything else landed confirmed: false at the N9 per-row sweep.
    for placeholder in ("oracle:schema-inventory", "snowflake:schema-inventory",
                        "exec-hosts:rua-bundle", "dpl:pipeline-registry",
                        "dpl:dataset-registry", "snow:cmdb-ci-classes",
                        "seal@[db].psgmgr.cm_escalation_db",
                        "controlm@[db].psgmgr.cm_hist_vw",
                        "controlm:deftable-xml-export",
                        "bitbucket:repo-objects-manifest"):
        assert not reg.is_confirmed(placeholder), f"{placeholder} should be unconfirmed"
        with pytest.raises(UnconfirmedSourceError):
            reg.require_confirmed(placeholder)


# --- CLI fail-fast: load <loader> exits 2 before touching Neo4j ---------------

def test_cli_load_blocks_unconfirmed_source(tmp_path: Path, monkeypatch) -> None:
    """If a loader's source is unconfirmed, `drydocs load` exits 2 with the gate
    message — before any adapter is opened or Neo4j is contacted."""
    typer_testing = pytest.importorskip("typer.testing")
    from drydocs import cli

    # Flip the folders dataset to unconfirmed via an injected registry.
    reg = SourceRegistry.from_yaml(_write_registry(tmp_path, [
        {"id": "controlm@[db].psgmgr.cm_def_vtab", "confirmed": False,
         "system": "psgmgr", "origin": "controlm", "artifact": "cm_def_vtab"},
    ]))
    monkeypatch.setattr(cli, "_registry", reg)

    runner = typer_testing.CliRunner()
    # --csv points nowhere on purpose: the gate must fire BEFORE the adapter check.
    args = ["load", "controlm_folders", "--csv", str(tmp_path / "nope.csv")]
    result = runner.invoke(cli.app, args)
    assert result.exit_code == 2
    assert "not confirmed" in result.stdout
    assert "cm_def_vtab" in result.stdout


def test_cli_load_blocks_retired_binding(tmp_path: Path, monkeypatch) -> None:
    """A loader whose (overlaid or declared) source id has been RETIRED exits 2
    with the replacement named — the D4 guard reaches the CLI."""
    typer_testing = pytest.importorskip("typer.testing")
    from drydocs import cli

    reg = SourceRegistry.from_yaml(_write_registry(
        tmp_path,
        [{"id": "pat:product-catalog", "confirmed": True, "system": "pat",
          "artifact": "product-catalog"}],
        retired=[{"id": "controlm@[db].psgmgr.cm_def_vtab",
                  "replaced_by": ["pat:product-catalog"], "reason": "test"}],
    ))
    monkeypatch.setattr(cli, "_registry", reg)

    runner = typer_testing.CliRunner()
    args = ["load", "controlm_folders", "--csv", str(tmp_path / "nope.csv")]
    result = runner.invoke(cli.app, args)
    assert result.exit_code == 2
    assert "RETIRED" in result.stdout
