"""DRYDOCS_DATA_ROOT — the out-of-repo landing zone (G19).

Contract: one shared resolver (env override > ``~/data/DryDocs`` default),
per-source subfolders (``rua/incoming/``, ``rua/extracted/<bundle>/``), and —
the publish-boundary safety net — the repo tree NEVER contains a rua bundle
(``rua_*.tar.gz`` or an extracted bundle dir), only pointers.
"""
from __future__ import annotations

from pathlib import Path

from drydocs_core import data_root as dr
from drydocs_core.data_root import (
    catalog_dir,
    dpl_registry_dir,
    resolve_data_root,
    rua_extracted_dir,
    rua_incoming_dir,
    source_dir,
)

REPO = Path(__file__).resolve().parents[2]


# ---- resolution -------------------------------------------------------------

def test_default_and_env_override(tmp_path, monkeypatch):
    monkeypatch.delenv(dr.DATA_ROOT_ENV, raising=False)
    assert resolve_data_root() == dr.DEFAULT_DATA_ROOT
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


def test_create_on_demand_only(tmp_path, monkeypatch):
    monkeypatch.setenv(dr.DATA_ROOT_ENV, str(tmp_path / "root"))
    path = rua_incoming_dir()
    assert not path.exists()  # resolving never creates
    created = rua_incoming_dir(create=True)
    assert created.is_dir()
    assert source_dir("dpl", "swagger", create=True).is_dir()


# ---- publish-boundary safety net (the root-image-rule spirit) ---------------

_SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}


def test_repo_tree_contains_no_rua_bundles():
    """Bundles hold real hostnames/uids/home paths (Internal-Confidential) —
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
    app ids, contact emails, and physical coordinates (Internal-Confidential)
    — they live under DRYDOCS_DATA_ROOT/catalog/, never in the tree (G42).
    An export is recognized by the curated view name traveling in the file
    name (``*_DATASETS_V`` / ``*_DISTRIBUTIONS_V``, either case — test
    fixtures are built in tmp_path, so any hit here is a real stray)."""
    offenders: set[str] = set()
    for pattern in ("*datasets_v*", "*distributions_v*",
                    "*DATASETS_V*", "*DISTRIBUTIONS_V*"):
        for path in REPO.rglob(pattern):
            if any(part in _SKIP_DIRS for part in path.parts):
                continue
            if path.is_file() and path.suffix.lower() in {".csv", ".json"}:
                offenders.add(str(path.relative_to(REPO)))
    assert not offenders, (
        "catalog view export found IN the repo tree — move it to the "
        f"DRYDOCS_DATA_ROOT landing zone (~/data/DryDocs/catalog/): {sorted(offenders)}"
    )
