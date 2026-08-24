"""DRYDOCS_DATA_ROOT — the out-of-repo landing zone (G19).

Contract: one shared resolver (env override > ``~/data/DryDocs`` default),
per-source subfolders (``rua/incoming/``, ``rua/extracted/<bundle>/``), and —
the publish-boundary safety net — the repo tree NEVER contains a rua bundle
(``rua_*.tar.gz`` or an extracted bundle dir), only pointers.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from drydocs_core import data_root as dr
from drydocs_core.data_root import (
    catalog_dir,
    controlm_xml_dir,
    dpl_registry_dir,
    remediation_incoming_dir,
    remediation_outgoing_dir,
    remediation_recommendations_dir,
    resolve_data_root,
    rua_extracted_dir,
    rua_incoming_dir,
    source_dir,
)

REPO = Path(__file__).resolve().parents[2]


# ---- resolution -------------------------------------------------------------


def test_an_unset_root_fails_naming_the_variable(tmp_path, monkeypatch):
    """G81 (d): THERE IS NO DEFAULT. An unset variable used to relocate every
    read and write to ~/data/DryDocs — a plausible-looking place a person might
    also pick by hand — so the same command in two shells targeted two different
    trees and a write meant for one could land on the other. Same family as
    G78's fixture default, one layer down and worse: G78 loaded the wrong data,
    this destroys the right data."""
    monkeypatch.delenv(dr.DATA_ROOT_ENV, raising=False)
    with pytest.raises(dr.DataRootNotSetError) as info:
        resolve_data_root()
    assert dr.DATA_ROOT_ENV in str(info.value), "the failure must NAME the variable"

    monkeypatch.setenv(dr.DATA_ROOT_ENV, "   ")
    with pytest.raises(dr.DataRootNotSetError):
        resolve_data_root()  # whitespace-only is unset, not a path


def test_the_conventional_location_is_still_documented(tmp_path, monkeypatch):
    """DEFAULT_DATA_ROOT survives as the location an operator SHOULD usually
    pick — and the error message suggests it — but nothing resolves to it
    implicitly."""
    assert dr.DEFAULT_DATA_ROOT == Path.home() / "data" / "DryDocs"
    monkeypatch.setenv(dr.DATA_ROOT_ENV, str(tmp_path / "elsewhere"))
    assert resolve_data_root() == tmp_path / "elsewhere"


def test_rua_subfolder_convention(tmp_path, monkeypatch):
    monkeypatch.setenv(dr.DATA_ROOT_ENV, str(tmp_path))
    assert rua_incoming_dir() == tmp_path / "rua" / "incoming"
    assert rua_extracted_dir() == tmp_path / "rua" / "extracted"
    assert (
        rua_extracted_dir("rua_host_20260722.tar.gz")
        == tmp_path / "rua" / "extracted" / "rua_host_20260722.tar.gz"
    )


def test_dpl_registry_subfolder_convention(tmp_path, monkeypatch):
    monkeypatch.setenv(dr.DATA_ROOT_ENV, str(tmp_path))
    assert dpl_registry_dir() == tmp_path / "dpl-registry"
    assert dpl_registry_dir("88888") == tmp_path / "dpl-registry" / "88888"


def test_catalog_subfolder_convention(tmp_path, monkeypatch):
    monkeypatch.setenv(dr.DATA_ROOT_ENV, str(tmp_path))
    assert catalog_dir() == tmp_path / "catalog"
    assert catalog_dir("screenshots") == tmp_path / "catalog" / "screenshots"


def test_controlm_xml_subfolder_convention(tmp_path, monkeypatch):
    # G47: exports are arbitrarily-named generic .xml, so no tree sweep is
    # possible — the landing-zone convention itself is the guard
    monkeypatch.setenv(dr.DATA_ROOT_ENV, str(tmp_path))
    assert controlm_xml_dir() == tmp_path / "controlm-xml"


def test_remediation_subfolder_convention(tmp_path, monkeypatch):
    # remediation working zones are deliberately separate from the ingestion
    # landing zone (controlm-xml/): per-fix lifecycle, not graph-load lifecycle
    monkeypatch.setenv(dr.DATA_ROOT_ENV, str(tmp_path))
    assert remediation_incoming_dir() == tmp_path / "remediation" / "incoming"
    assert remediation_outgoing_dir() == tmp_path / "remediation" / "outgoing"
    assert remediation_recommendations_dir() == tmp_path / "remediation" / "recommendations"


def test_create_on_demand_only(tmp_path, monkeypatch):
    monkeypatch.setenv(dr.DATA_ROOT_ENV, str(tmp_path / "root"))
    path = rua_incoming_dir()
    assert not path.exists()  # resolving never creates
    # G81 (e): rua_incoming_dir is a READ zone (hand-carried bundles) and no
    # longer takes `create` at all — any path a create-capable helper may build
    # is write-mode BY CONSTRUCTION, so the converse is enforced in the
    # signature rather than left to discipline.
    assert "create" not in inspect.signature(rua_incoming_dir).parameters
    created = rua_extracted_dir("bundle-1", create=True)
    assert created.is_dir()  # the WRITE half still creates on demand
    # A WRITE zone creates; the read-zone refusal is proved in test_data_zones.py.
    assert source_dir("cmdline-staging", "work", create=True).is_dir()


# ---- publish-boundary safety net (the root-image-rule spirit) ---------------

_SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}


def test_repo_tree_contains_no_rua_bundles():
    """Bundles hold real hostnames/uids/home paths (confidential (Internal, J23)) —
    they live under DRYDOCS_DATA_ROOT, never in the tree. An extracted bundle
    is recognized by its collector marker (a ``meta.txt`` inside a ``rua_*``
    directory)."""
    offenders: list[str] = []
    for path in REPO.rglob("rua_*"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        name = path.name.lower()
        if path.is_file() and (name.endswith(".tar.gz") or name.endswith(".tgz")):
            offenders.append(str(path.relative_to(REPO)))
        elif path.is_dir() and (path / "meta.txt").exists():
            offenders.append(str(path.relative_to(REPO)) + "/ (extracted bundle)")
    assert not offenders, (
        "rua bundle payload found IN the repo tree — move it to the "
        f"DRYDOCS_DATA_ROOT landing zone (~/data/DryDocs/rua/): {offenders}"
    )


def test_repo_tree_contains_no_catalog_exports():
    """Data-catalog view exports hold real dataset names, GUIDs, producing
    app ids, contact emails, and physical coordinates (confidential (Internal, J23))
    — they live under DRYDOCS_DATA_ROOT/catalog/, never in the tree (G42).
    An export is recognized by the curated view name traveling in the file
    name (``*_DATASETS_V`` / ``*_DISTRIBUTIONS_V``, either case — test
    fixtures are built in tmp_path, so any hit here is a real stray)."""
    offenders: set[str] = set()
    for pattern in ("*datasets_v*", "*distributions_v*", "*DATASETS_V*", "*DISTRIBUTIONS_V*"):
        for path in REPO.rglob(pattern):
            if any(part in _SKIP_DIRS for part in path.parts):
                continue
            if path.is_file() and path.suffix.lower() in {".csv", ".json"}:
                offenders.add(str(path.relative_to(REPO)))
    assert not offenders, (
        "catalog view export found IN the repo tree — move it to the "
        f"DRYDOCS_DATA_ROOT landing zone (~/data/DryDocs/catalog/): {sorted(offenders)}"
    )
