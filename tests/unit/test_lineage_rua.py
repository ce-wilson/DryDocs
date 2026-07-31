"""G20 — the rua bundle extractor (bundle → provenance-stamped candidates).

SYNTHETIC fixtures throughout (shape-faithful, value-fake — the collector's
output contract from ``drydocs_lineage/collect/rua_inventory.sh``; real bundles
are confidential (Internal, J23) and live in the G19 landing zone, never here). Each
case pins one acceptance clause: (a) the meta.txt provenance envelope on every
record, (b) directories/ownership → rua_path DataAssets, (c) profile + script
artifacts with sha256 and copy pointers, (d) v1 AND v2 bundles both parse,
(e) tarball input, (f) malformed/missing counted never dropped, (g) candidates
only — no rels, no graph writes.
"""
from __future__ import annotations

import tarfile
from pathlib import Path

import pytest

from drydocs_lineage.extractors import RuaInventoryExtractor
from drydocs_lineage.model import LineageGraph, asset_id, process_id

HOST = "vsi-synth-01"
USER = "svc_synth"

_META = """schema={schema}
collected_at=2026-07-23T12:00:00Z
collected_by={user}
user={user}
uid=4242
primary_group=synthgrp
groups=synthgrp etl
login_shell=/bin/ksh
home=/home/{user}
home_real=/home/{user}
hostname={host}
fqdn={host}.example.internal
os=Linux
os_pretty=Synthetic Linux 9
kernel=5.14.0-synth
scan_roots=/home/{user} /opt/app
max_depth=4
ownership_sweep=no
name_globs=*.py *.sh
copy_scripts=yes
script_copy_max_bytes=200
config=./rua_inventory.conf
directories_captured=2
scripts_captured=2
scripts_copy_skipped_size=1
"""

_DIRECTORIES = (
    "path\ttype\towner\tgroup\tperms\tsize\tmtime\n"
    f"/home/{USER}\td\t{USER}\tsynthgrp\t750\t4096\t2026-07-20 09:00\n"
    f"/home/{USER}/app\td\t{USER}\tsynthgrp\t750\t4096\t2026-07-20 09:00\n"
)

SHA_PROFILE = "aa" * 32
SHA_CONFORM = "bb" * 32
SHA_BIG = "cc" * 32

_PROFILES_V2 = (
    "name\tpath\texists\tsize\tmtime\tperms\towner\tsha256\n"
    f".profile\t/home/{USER}/.profile\tyes\t42\t2026-07-20 09:00\t644\t{USER}\t{SHA_PROFILE}\n"
)

_PROFILES_V1 = (
    "name\tpath\texists\tsize\tmtime\tperms\towner\n"
    f".profile\t/home/{USER}/.profile\tyes\t42\t2026-07-20 09:00\t644\t{USER}\n"
)

_SCRIPTS = (
    "path\towner\tgroup\tperms\tsize\tmtime\tsha256\n"
    f"/home/{USER}/app/conform.py\t{USER}\tsynthgrp\t644\t17\t2026-07-20 09:00\t{SHA_CONFORM}\n"
    f"/home/{USER}/app/big.py\t{USER}\tsynthgrp\t644\t500\t2026-07-20 09:00\t{SHA_BIG}\n"
)

_OWNERSHIP = (
    "path\ttype\tperms\tsize\tmtime\n"
    f"/home/{USER}\td\t750\t4096\t2026-07-20 09:00\n"      # dup of directories.tsv
    f"/data/landing/in.dat\tf\t640\t100\t2026-07-20 09:00\n"
)


def _write_bundle(root: Path, name: str = f"rua_{HOST}_{USER}_20260723T120000Z",
                  *, v2: bool = True, host: str = HOST,
                  ownership: bool = False) -> Path:
    bundle = root / name
    bundle.mkdir(parents=True)
    schema = "rua-inventory/v2" if v2 else "rua-inventory/v1"
    (bundle / "meta.txt").write_text(
        _META.format(schema=schema, host=host, user=USER), encoding="utf-8")
    (bundle / "directories.tsv").write_text(_DIRECTORIES, encoding="utf-8")
    (bundle / "profiles").mkdir()
    (bundle / "profiles" / ".profile").write_text("export SYNTH=1\n", encoding="utf-8")
    if v2:
        (bundle / "profiles.tsv").write_text(_PROFILES_V2, encoding="utf-8")
        (bundle / "scripts.tsv").write_text(_SCRIPTS, encoding="utf-8")
        # only conform.py was copied (big.py is the over-cap listing)
        copy = bundle / "scripts" / "home" / USER / "app"
        copy.mkdir(parents=True)
        (copy / "conform.py").write_text('print("conform")\n', encoding="utf-8")
    else:
        (bundle / "profiles.tsv").write_text(_PROFILES_V1, encoding="utf-8")
    if ownership:
        (bundle / "ownership_dirs.tsv").write_text(_OWNERSHIP, encoding="utf-8")
    (bundle / "rua_inventory.conf.used").write_text("MAX_DEPTH=4\n", encoding="utf-8")
    return bundle


@pytest.fixture()
def v2_run(tmp_path: Path):
    bundle = _write_bundle(tmp_path, v2=True)
    g = LineageGraph()
    cov = RuaInventoryExtractor().extract(bundle, g)
    return g, cov


# -- (a) the provenance envelope on every record ------------------------------------

def test_envelope_stamped_on_every_record(v2_run) -> None:
    g, cov = v2_run
    everything = list(g.processes.values()) + list(g.data_assets.values())
    assert everything, "nothing staged"
    for node in everything:
        assert node.properties["rua_schema"] == "rua-inventory/v2"
        assert node.properties["rua_host"] == HOST
        assert node.properties["rua_fqdn"] == f"{HOST}.example.internal"
        assert node.properties["rua_user"] == USER
        assert node.properties["rua_uid"] == "4242"
        assert node.properties["rua_shell"] == "/bin/ksh"
        assert node.properties["rua_collected_at"] == "2026-07-23T12:00:00Z"
        assert node.properties["rua_bundle"].startswith("rua_")
    assert cov.meta_fields_missing == 0
    assert cov.meta["kernel"] == "5.14.0-synth"      # full meta kept for G23
    assert cov.meta["scripts_copy_skipped_size"] == "1"


# -- (b) directories / ownership → rua_path DataAssets ------------------------------

def test_directories_become_rua_path_assets(v2_run) -> None:
    g, cov = v2_run
    home = g.data_assets[asset_id("rua_path", f"/home/{USER}")]
    assert home.kind == "rua_path"
    assert home.properties["type"] == "d"
    assert home.properties["perms"] == "750"
    assert home.properties["rua_section"] == "directories.tsv"
    assert cov.directories_rows == 2 and cov.directories_staged == 2


def test_ownership_sweep_consumed_and_dedups(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path, v2=True, ownership=True)
    g = LineageGraph()
    cov = RuaInventoryExtractor().extract(bundle, g)
    assert cov.ownership_rows == 2
    assert cov.ownership_staged == 1                 # /home dup deduped by id
    swept = g.data_assets[asset_id("rua_path", "/data/landing/in.dat")]
    assert swept.properties["type"] == "f"
    assert swept.properties["rua_section"] == "ownership_dirs.tsv"
    assert cov.cross_host_collisions == 0            # same host — not a collision


# -- (c) profile + script artifacts --------------------------------------------------

def test_profile_artifact_with_hash_and_copy(v2_run) -> None:
    g, cov = v2_run
    prof = g.processes[process_id("rua_profile", f"/home/{USER}/.profile")]
    assert prof.kind == "rua_profile" and prof.name == ".profile"
    assert prof.path == f"/home/{USER}/.profile"
    assert prof.properties["sha256"] == SHA_PROFILE
    assert prof.properties["rua_copy"] == "profiles/.profile"
    assert cov.profiles_staged == 1 and cov.profile_copies_present == 1


def test_script_artifacts_copy_pointer_and_overcap_listing(v2_run) -> None:
    g, cov = v2_run
    copied = g.processes[process_id("rua_script", f"/home/{USER}/app/conform.py")]
    assert copied.properties["rua_copy"] == f"scripts/home/{USER}/app/conform.py"
    listed = g.processes[process_id("rua_script", f"/home/{USER}/app/big.py")]
    assert "rua_copy" not in listed.properties       # over-cap: listed, not copied
    assert listed.properties["sha256"] == SHA_BIG    # hash still travels
    assert cov.scripts_staged == 2
    assert cov.script_copies_present == 1 and cov.script_copies_missing == 1


# -- (d) v1 AND v2 bundles both parse -------------------------------------------------

def test_v1_bundle_fully_ingestible(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path, v2=False)
    g = LineageGraph()
    cov = RuaInventoryExtractor().extract(bundle, g)
    assert cov.directories_staged == 2 and cov.profiles_staged == 1
    assert cov.scripts_staged == 0
    assert "scripts.tsv" in cov.sections_optional_absent   # optional, NOT missing
    assert not any(s.startswith("scripts.tsv") for s in cov.sections_missing)
    prof = g.processes[process_id("rua_profile", f"/home/{USER}/.profile")]
    assert "sha256" not in prof.properties
    assert cov.hash_missing == 1                     # v1 has no hashes — counted


# -- (e) tarball input ----------------------------------------------------------------

def test_tarball_unpacks_and_parses(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path / "staging", v2=True)
    tarball = tmp_path / f"{bundle.name}.tar.gz"
    with tarfile.open(tarball, "w:gz") as tf:
        tf.add(bundle, arcname=bundle.name)
    g = LineageGraph()
    cov = RuaInventoryExtractor().extract(
        tarball, g, unpack_dir=tmp_path / "unpacked")
    assert cov.directories_staged == 2 and cov.scripts_staged == 2
    assert next(iter(g.data_assets.values())).properties["rua_host"] == HOST


# -- (f) malformed / missing counted, never dropped -----------------------------------

def test_malformed_rows_and_missing_meta_counted(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path, v2=True)
    (bundle / "directories.tsv").write_text(
        "path\ttype\towner\tgroup\tperms\tsize\tmtime\n"
        f"/home/{USER}\td\t{USER}\tsynthgrp\t750\t4096\t2026-07-20 09:00\n"
        "short\trow\n",                                 # wrong column count
        encoding="utf-8")
    (bundle / "meta.txt").unlink()
    g = LineageGraph()
    cov = RuaInventoryExtractor().extract(bundle, g)
    assert cov.meta_missing == 1
    assert cov.directories_malformed == 1
    assert cov.directories_staged == 1                  # the good row still lands
    node = g.data_assets[asset_id("rua_path", f"/home/{USER}")]
    assert node.properties["rua_bundle"] == bundle.name  # bundle stamp survives
    assert "rua_host" not in node.properties


def test_cross_host_collision_counted_first_seen_wins(tmp_path: Path) -> None:
    a = _write_bundle(tmp_path / "a", v2=True, host="vsi-synth-01")
    b = _write_bundle(tmp_path / "b", v2=True, host="vsi-synth-02",
                      name=f"rua_vsi-synth-02_{USER}_20260723T130000Z")
    g = LineageGraph()
    extractor = RuaInventoryExtractor()
    extractor.extract(a, g)
    cov_b = extractor.extract(b, g)
    assert cov_b.cross_host_collisions > 0              # same paths, other host
    home = g.data_assets[asset_id("rua_path", f"/home/{USER}")]
    assert home.properties["rua_host"] == "vsi-synth-01"   # first seen wins


# -- (g) candidates only: no rels, nothing but nodes -----------------------------------

def test_no_rels_and_no_new_relationship_types(v2_run) -> None:
    g, cov = v2_run
    assert g.rels == set()                              # G20 stages NODES only
    assert "scripts=2" in cov.summary()
    assert "profiles=1" in cov.summary()


# -- (h) G45: the metadata-only scripts.csv listing fallback ---------------------------
# Real bundles ship the listing (pipe-delimited, no sha256, no body mirror)
# while still wearing the v1 schema tag; pre-G45 every such row silently
# dropped (scripts_rows=0, section filed optional-absent).

_SCRIPTS_CSV = (
    "path|script|permission|date|size\n"
    f"/home/{USER}/app|conform.py|644|2026-07-20 09:00|17\n"
    "/opt/app/lookup|refund_lkp.ksh|750|2026-07-19 08:30|2048\n"
)


def test_scripts_csv_metadata_only_fallback(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path, v2=False)          # v1: no scripts.tsv
    (bundle / "scripts.csv").write_text(_SCRIPTS_CSV, encoding="utf-8")
    g = LineageGraph()
    cov = RuaInventoryExtractor().extract(bundle, g)
    assert cov.scripts_rows == 2 and cov.scripts_staged == 2
    assert cov.script_copies_missing == 2       # a LISTING never implies content
    node = g.processes[process_id("rua_script", f"/home/{USER}/app/conform.py")]
    assert node.path == f"/home/{USER}/app/conform.py"  # joined absolute path
    assert node.name == "conform.py"
    assert node.properties["perms"] == "644"
    assert node.properties["mtime"] == "2026-07-20 09:00"
    assert node.properties["size"] == "17"
    assert node.properties["origin"] == "server-extract"
    assert "sha256" not in node.properties
    assert "rua_copy" not in node.properties
    assert cov.hash_missing == 3                # 2 csv rows + the v1 profile
    # the section ARRIVED — it must not also be filed optional-absent
    assert "scripts.tsv" not in cov.sections_optional_absent


def test_scripts_tsv_preferred_over_csv(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path, v2=True)           # scripts.tsv present (richer)
    (bundle / "scripts.csv").write_text(_SCRIPTS_CSV, encoding="utf-8")
    g = LineageGraph()
    cov = RuaInventoryExtractor().extract(bundle, g)
    # the tsv route ran: its sha256 travels, and the csv-only row never staged
    conform = g.processes[process_id("rua_script", f"/home/{USER}/app/conform.py")]
    assert conform.properties["sha256"] == SHA_CONFORM
    assert process_id("rua_script", "/opt/app/lookup/refund_lkp.ksh") not in g.processes
    assert cov.scripts_staged == 2                      # the two tsv rows only


def test_scripts_csv_malformed_rows_counted_never_dropped(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path, v2=False)
    (bundle / "scripts.csv").write_text(
        "path|script|permission|date|size\n"
        "/opt/app|good.sh|644|2026-07-20 09:00|10\n"
        "|orphan.sh|644|2026-07-20 09:00|10\n"          # empty containing dir
        "broken-row\n",                                 # wrong cell count
        encoding="utf-8")
    g = LineageGraph()
    cov = RuaInventoryExtractor().extract(bundle, g)
    assert cov.scripts_staged == 1
    assert cov.scripts_malformed == 2
