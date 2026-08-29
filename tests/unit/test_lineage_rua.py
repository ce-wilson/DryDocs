"""G20 — the rua bundle extractor (bundle → provenance-stamped candidates).

SYNTHETIC fixtures throughout (shape-faithful, value-fake — the collector's
output contract from ``drydocs_lineage/collect/rua_inventory.sh``; real bundles
are confidential (Internal, J23) and live in the G19 landing zone, never here). Each
case pins one acceptance clause: (a) the meta.txt provenance envelope on every
record, (b) directories/ownership → rua_path DataAssets, (c) profile + script
artifacts with sha256 and copy pointers, (d) v1 AND v2 bundles both parse,
(e) tarball input, (f) malformed/missing counted never dropped, (g) candidates
only — no rels, no graph writes, (i) G56: the v3 mount table derives
mount_root/fstype/storage_scope, and a mounts-absent bundle is unchanged.
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
    f"/home/{USER}\td\t750\t4096\t2026-07-20 09:00\n"  # dup of directories.tsv
    f"/data/landing/in.dat\tf\t640\t100\t2026-07-20 09:00\n"
)


def _write_bundle(
    root: Path,
    name: str = f"rua_{HOST}_{USER}_20260723T120000Z",
    *,
    v2: bool = True,
    host: str = HOST,
    ownership: bool = False,
    mounts: str | None = None,
    dirs: str = _DIRECTORIES,
) -> Path:
    bundle = root / name
    bundle.mkdir(parents=True)
    schema = "rua-inventory/v2" if v2 else "rua-inventory/v1"
    if mounts is not None:
        schema = "rua-inventory/v3"
    (bundle / "meta.txt").write_text(
        _META.format(schema=schema, host=host, user=USER), encoding="utf-8"
    )
    (bundle / "directories.tsv").write_text(dirs, encoding="utf-8")
    if mounts is not None:
        (bundle / "mounts.tsv").write_text(mounts, encoding="utf-8")
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
    assert cov.meta["kernel"] == "5.14.0-synth"  # full meta kept for G23
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
    assert cov.ownership_staged == 1  # /home dup deduped by id
    swept = g.data_assets[asset_id("rua_path", "/data/landing/in.dat")]
    assert swept.properties["type"] == "f"
    assert swept.properties["rua_section"] == "ownership_dirs.tsv"
    assert cov.cross_host_collisions == 0  # same host — not a collision


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
    assert "rua_copy" not in listed.properties  # over-cap: listed, not copied
    assert listed.properties["sha256"] == SHA_BIG  # hash still travels
    assert cov.scripts_staged == 2
    assert cov.script_copies_present == 1 and cov.script_copies_missing == 1


# -- (d) v1 AND v2 bundles both parse -------------------------------------------------


def test_v1_bundle_fully_ingestible(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path, v2=False)
    g = LineageGraph()
    cov = RuaInventoryExtractor().extract(bundle, g)
    assert cov.directories_staged == 2 and cov.profiles_staged == 1
    assert cov.scripts_staged == 0
    assert "scripts.tsv" in cov.sections_optional_absent  # optional, NOT missing
    assert not any(s.startswith("scripts.tsv") for s in cov.sections_missing)
    prof = g.processes[process_id("rua_profile", f"/home/{USER}/.profile")]
    assert "sha256" not in prof.properties
    assert cov.hash_missing == 1  # v1 has no hashes — counted


# -- (e) tarball input ----------------------------------------------------------------


def test_tarball_unpacks_and_parses(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path / "staging", v2=True)
    tarball = tmp_path / f"{bundle.name}.tar.gz"
    with tarfile.open(tarball, "w:gz") as tf:
        tf.add(bundle, arcname=bundle.name)
    g = LineageGraph()
    cov = RuaInventoryExtractor().extract(tarball, g, unpack_dir=tmp_path / "unpacked")
    assert cov.directories_staged == 2 and cov.scripts_staged == 2
    assert next(iter(g.data_assets.values())).properties["rua_host"] == HOST


# -- (f) malformed / missing counted, never dropped -----------------------------------


def test_malformed_rows_and_missing_meta_counted(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path, v2=True)
    (bundle / "directories.tsv").write_text(
        "path\ttype\towner\tgroup\tperms\tsize\tmtime\n"
        f"/home/{USER}\td\t{USER}\tsynthgrp\t750\t4096\t2026-07-20 09:00\n"
        "short\trow\n",  # wrong column count
        encoding="utf-8",
    )
    (bundle / "meta.txt").unlink()
    g = LineageGraph()
    cov = RuaInventoryExtractor().extract(bundle, g)
    assert cov.meta_missing == 1
    assert cov.directories_malformed == 1
    assert cov.directories_staged == 1  # the good row still lands
    node = g.data_assets[asset_id("rua_path", f"/home/{USER}")]
    assert node.properties["rua_bundle"] == bundle.name  # bundle stamp survives
    assert "rua_host" not in node.properties


def test_cross_host_collision_counted_first_seen_wins(tmp_path: Path) -> None:
    a = _write_bundle(tmp_path / "a", v2=True, host="vsi-synth-01")
    b = _write_bundle(
        tmp_path / "b",
        v2=True,
        host="vsi-synth-02",
        name=f"rua_vsi-synth-02_{USER}_20260723T130000Z",
    )
    g = LineageGraph()
    extractor = RuaInventoryExtractor()
    extractor.extract(a, g)
    cov_b = extractor.extract(b, g)
    assert cov_b.cross_host_collisions > 0  # same paths, other host
    home = g.data_assets[asset_id("rua_path", f"/home/{USER}")]
    assert home.properties["rua_host"] == "vsi-synth-01"  # first seen wins


# -- (g) candidates only: no rels, nothing but nodes -----------------------------------


def test_no_rels_and_no_new_relationship_types(v2_run) -> None:
    g, cov = v2_run
    assert g.rels == set()  # G20 stages NODES only
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
    bundle = _write_bundle(tmp_path, v2=False)  # v1: no scripts.tsv
    (bundle / "scripts.csv").write_text(_SCRIPTS_CSV, encoding="utf-8")
    g = LineageGraph()
    cov = RuaInventoryExtractor().extract(bundle, g)
    assert cov.scripts_rows == 2 and cov.scripts_staged == 2
    assert cov.script_copies_missing == 2  # a LISTING never implies content
    node = g.processes[process_id("rua_script", f"/home/{USER}/app/conform.py")]
    assert node.path == f"/home/{USER}/app/conform.py"  # joined absolute path
    assert node.name == "conform.py"
    assert node.properties["perms"] == "644"
    assert node.properties["mtime"] == "2026-07-20 09:00"
    assert node.properties["size"] == "17"
    assert node.properties["origin"] == "server-extract"
    assert "sha256" not in node.properties
    assert "rua_copy" not in node.properties
    assert cov.hash_missing == 3  # 2 csv rows + the v1 profile
    # the section ARRIVED — it must not also be filed optional-absent
    assert "scripts.tsv" not in cov.sections_optional_absent


def test_scripts_tsv_preferred_over_csv(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path, v2=True)  # scripts.tsv present (richer)
    (bundle / "scripts.csv").write_text(_SCRIPTS_CSV, encoding="utf-8")
    g = LineageGraph()
    cov = RuaInventoryExtractor().extract(bundle, g)
    # the tsv route ran: its sha256 travels, and the csv-only row never staged
    conform = g.processes[process_id("rua_script", f"/home/{USER}/app/conform.py")]
    assert conform.properties["sha256"] == SHA_CONFORM
    assert process_id("rua_script", "/opt/app/lookup/refund_lkp.ksh") not in g.processes
    assert cov.scripts_staged == 2  # the two tsv rows only


def test_scripts_csv_malformed_rows_counted_never_dropped(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path, v2=False)
    (bundle / "scripts.csv").write_text(
        "path|script|permission|date|size\n"
        "/opt/app|good.sh|644|2026-07-20 09:00|10\n"
        "|orphan.sh|644|2026-07-20 09:00|10\n"  # empty containing dir
        "broken-row\n",  # wrong cell count
        encoding="utf-8",
    )
    g = LineageGraph()
    cov = RuaInventoryExtractor().extract(bundle, g)
    assert cov.scripts_staged == 1
    assert cov.scripts_malformed == 2


# --- G103: the script-copy path is ONE convention held by two files ----------------


def test_collector_mirror_layout_and_extractor_derivation_are_the_same_convention() -> None:
    """G103 (2026-08-21), resolution (b) PIN THE CONVENTION. scripts.tsv carries
    no copy_path column: the collector mirrors the absolute tree under
    `scripts/` (rua_inventory.sh: dest="$BUNDLE/scripts$path") and the extractor
    RE-DERIVES that location (rua_inventory.py: copy_rel = f"scripts{path}").
    A change on either side used to fail SILENTLY — the miss lands in the same
    counters as an over-cap file the collector listed but did not copy
    (SCRIPT_COPY_MAX_BYTES), so "the layout changed" read as "this estate has
    large scripts". Both halves live in this repo, so the contract is pinned by
    reading both: the collector's literal and the extractor's f-string must
    agree, and the fixture walk below proves the derived path is readable."""
    import re

    repo = Path(__file__).resolve().parents[2]
    collector = (repo / "drydocs_lineage" / "collect" / "rua_inventory.sh").read_text(
        encoding="utf-8"
    )
    extractor = (repo / "drydocs_lineage" / "extractors" / "rua_inventory.py").read_text(
        encoding="utf-8"
    )
    dest = re.search(r'dest="\$BUNDLE/(scripts)\$path"', collector)
    assert dest, "collector no longer mirrors scripts under $BUNDLE/scripts$path — update the extractor AND this test together"
    derived = re.search(r'copy_rel = f"(scripts)\{row\[.path.\]\}"', extractor)
    assert (
        derived
    ), "extractor no longer derives scripts{path} — update the collector AND this test together"
    assert dest.group(1) == derived.group(1) == "scripts"


def test_derived_copy_path_is_readable_from_the_extractor_side(tmp_path: Path) -> None:
    """The other half of (b): on a bundle laid out the collector's way, the
    extractor's pointer resolves to a real, readable file (so a layout drift
    would surface here as an unreadable/no-copy count, not pass unseen)."""
    bundle_dir = _write_bundle(tmp_path, v2=True)
    graph = LineageGraph()
    coverage = RuaInventoryExtractor().extract(bundle_dir, graph)
    copied = next(
        n
        for n in graph.processes.values()
        if n.properties.get("rua_copy", "").startswith("scripts/")
    )
    target = bundle_dir / copied.properties["rua_copy"]
    assert target.is_file(), f"derived copy path {target} is not a file"
    assert target.read_text(encoding="utf-8")
    assert coverage.script_copies_present >= 1


def test_unpacking_into_a_read_zone_is_refused(tmp_path, monkeypatch) -> None:
    """G81, THE RUNTIME LEG. `unpack_dir` is caller-supplied, so no comparison of
    DECLARED zones can catch it — an operator naming their own extract folder
    gets it overwritten file by file, because extractall overwrites with no
    warning and no diff. That is the 2026-08-11 incident's shape, so the refusal
    lives at the write site as well as in the declaration check."""
    import tarfile

    from drydocs_core.data_root import ReadZoneWriteError

    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path))
    tarball = tmp_path / "rua_host_20260823.tar.gz"
    payload = tmp_path / "payload"
    payload.mkdir()
    (payload / "meta.txt").write_text("host=h\n", encoding="utf-8")
    with tarfile.open(tarball, "w:gz") as tf:
        tf.add(payload, arcname="rua_host_20260823")

    # remediation/incoming is a declared READ zone — a hand-drop area.
    victim = tmp_path / "remediation" / "incoming"
    victim.mkdir(parents=True)
    (victim / "precious.xml").write_text("<original/>", encoding="utf-8")

    with pytest.raises(ReadZoneWriteError) as info:
        RuaInventoryExtractor().extract(tarball, LineageGraph(), unpack_dir=victim)

    assert "remediation-incoming" in str(info.value)
    assert (victim / "precious.xml").read_text(
        encoding="utf-8"
    ) == "<original/>", "the existing file was touched despite the refusal"


# -- (i) G56: the v3 mount table → mount_root / fstype / storage_scope -------------------
# The D-amendment's problem in one line: a path may be SHARED, and then the same
# path on N hosts is ONE FILE SEEN N TIMES, not N deployments. Sharing follows
# from the FSTYPE, never from the array — so these fixtures vary the fstype and
# nothing else. Synthetic throughout: a real mount spec carries a live filer name.

_MOUNTS_SHARED = (
    "source\ttarget\tfstype\toptions\n"
    "/dev/mapper/rootvg-root\t/\txfs\trw,relatime\n"  # the root is LOCAL...
    f"synthfiler01:/export/apps\t/home/{USER}\tnfs4\trw,relatime,vers=4.1\n"  # ...home is not
)

_MOUNTS_LOCAL = (
    "source\ttarget\tfstype\toptions\n"
    "/dev/mapper/rootvg-root\t/\txfs\trw,relatime\n"
    f"/dev/mapper/homevg-home\t/home/{USER}\text4\trw,relatime\n"
)

_MOUNTS_UNRECOGNISED = (
    "source\ttarget\tfstype\toptions\n"
    "/dev/mapper/rootvg-root\t/\txfs\trw,relatime\n"
    f"synthnsd\t/home/{USER}\tgpfs\trw,relatime\n"  # clustered, but NOT in the map
)


def _home_asset(graph: LineageGraph):
    return graph.data_assets[asset_id("rua_path", f"/home/{USER}")]


def _conform(graph: LineageGraph):
    return graph.processes[process_id("rua_script", f"/home/{USER}/app/conform.py")]


def test_shared_nfs_bundle_derives_shared_scope_by_longest_match(tmp_path: Path) -> None:
    """The acceptance's shared case, and the longest-match proof in one fixture:
    `/` is xfs and would read LOCAL, `/home/svc_synth` is nfs4 and is the real
    answer. Only the deeper target says so, so a first-match or shortest-match
    resolver fails this test rather than passing it by luck."""
    bundle = _write_bundle(tmp_path, v2=True, mounts=_MOUNTS_SHARED)
    g = LineageGraph()
    cov = RuaInventoryExtractor().extract(bundle, g)

    for node in (_home_asset(g), _conform(g)):
        assert node.properties["storage_scope"] == "shared"
        assert node.properties["mount_root"] == f"/home/{USER}"  # NOT "/"
        assert node.properties["fstype"] == "nfs4"
        assert node.properties["mount_source"] == "synthfiler01:/export/apps"

    # §D2's grain: the load and the G58 report read the OCCURRENCE, not the node
    occ = _conform(g).occurrences[0]
    assert occ["storage_scope"] == "shared"
    assert occ["mount_root"] == f"/home/{USER}"
    assert occ["fstype"] == "nfs4"

    assert cov.mounts_rows == 2
    assert cov.mount_scope_unknown_fstype == 0 and cov.mount_unresolved == 0
    assert cov.mount_fstypes_unrecognised == []
    assert "mounts.tsv" not in cov.sections_optional_absent
    assert _conform(g).properties["rua_schema"] == "rua-inventory/v3"
    assert "mounts=2" in cov.summary()


def test_local_only_bundle_derives_local_scope(tmp_path: Path) -> None:
    """Same paths, same hosts, ext4 instead of nfs4 — and the answer flips. That
    is the whole point of keying on fstype: nothing else in the bundle changed."""
    bundle = _write_bundle(tmp_path, v2=True, mounts=_MOUNTS_LOCAL)
    g = LineageGraph()
    cov = RuaInventoryExtractor().extract(bundle, g)

    for node in (_home_asset(g), _conform(g)):
        assert node.properties["storage_scope"] == "local"
        assert node.properties["fstype"] == "ext4"
    assert _conform(g).occurrences[0]["storage_scope"] == "local"
    assert cov.mount_scope_unknown_fstype == 0 and cov.mount_unresolved == 0


def test_mounts_absent_v2_bundle_stays_ingestible_and_stamps_nothing(tmp_path: Path) -> None:
    """The compat clause, and it is the STRONG form: a pre-v3 bundle must not
    merely parse, it must come out UNCHANGED. Stamping `unknown` here would look
    harmless and would be wrong — it would assert that the table was read and
    the path was not covered, when in fact no table was ever captured."""
    bundle = _write_bundle(tmp_path, v2=True)  # no mounts= → a v2 bundle
    g = LineageGraph()
    cov = RuaInventoryExtractor().extract(bundle, g)

    assert "mounts.tsv" in cov.sections_optional_absent  # optional, NOT missing
    assert not any(s.startswith("mounts.tsv") for s in cov.sections_missing)
    for node in (_home_asset(g), _conform(g)):
        for key in ("storage_scope", "mount_root", "fstype", "mount_source"):
            assert key not in node.properties
    assert "storage_scope" not in _conform(g).occurrences[0]
    assert cov.mounts_rows == 0
    assert cov.mount_unresolved == 0 and cov.mount_scope_unknown_fstype == 0
    # everything else about the bundle is exactly as it was pre-G56
    assert cov.directories_staged == 2 and cov.scripts_staged == 2


def test_unrecognised_fstype_is_unknown_and_counted_never_guessed(tmp_path: Path) -> None:
    """gpfs IS a clustered filesystem, and the extractor still says `unknown` —
    deliberately. The map holds only the fstypes the gate named; widening it is
    an evidence decision, and this counter is the feed that raises it. Guessing
    `shared` would suppress real drift; guessing `local` would manufacture the
    independent observations G2 and the G24 corroboration assume."""
    bundle = _write_bundle(tmp_path, v2=True, mounts=_MOUNTS_UNRECOGNISED)
    g = LineageGraph()
    cov = RuaInventoryExtractor().extract(bundle, g)

    node = _conform(g)
    assert node.properties["storage_scope"] == "unknown"
    assert node.properties["fstype"] == "gpfs"  # the EVIDENCE still travels
    assert node.properties["mount_root"] == f"/home/{USER}"
    assert cov.mount_scope_unknown_fstype > 0
    assert cov.mount_fstypes_unrecognised == ["gpfs"]  # named, not just tallied
    assert cov.mount_unresolved == 0  # it MATCHED a mount; the fstype is the gap


def test_mount_target_matching_is_boundary_aware(tmp_path: Path) -> None:
    """/opt/app2 is not under /opt/app. A naive startswith would put this path on
    the NFS mount and report a local file as one-seen-N-times — the exact wrong
    answer the amendment is about, arrived at from the right table."""
    dirs = (
        "path\ttype\towner\tgroup\tperms\tsize\tmtime\n"
        f"/opt/app\td\t{USER}\tsynthgrp\t750\t4096\t2026-07-20 09:00\n"
        f"/opt/app2\td\t{USER}\tsynthgrp\t750\t4096\t2026-07-20 09:00\n"
    )
    mounts = (
        "source\ttarget\tfstype\toptions\n"
        "/dev/mapper/rootvg-root\t/\txfs\trw,relatime\n"
        "synthfiler01:/export/app\t/opt/app\tnfs4\trw,relatime\n"
    )
    g = LineageGraph()
    RuaInventoryExtractor().extract(_write_bundle(tmp_path, v2=True, mounts=mounts, dirs=dirs), g)
    under = g.data_assets[asset_id("rua_path", "/opt/app")]
    beside = g.data_assets[asset_id("rua_path", "/opt/app2")]
    assert under.properties["storage_scope"] == "shared"
    assert under.properties["mount_root"] == "/opt/app"
    assert beside.properties["storage_scope"] == "local"  # falls back to the root
    assert beside.properties["mount_root"] == "/"


def test_path_covered_by_no_mount_target_is_unknown_and_counted(tmp_path: Path) -> None:
    """A table with no root row cannot answer for every path. Present-but-
    unmatched is its own state: `unknown` with NO mount_root, and counted —
    distinct from the mounts-absent bundle above, which stamps nothing at all."""
    mounts = (
        "source\ttarget\tfstype\toptions\n"
        "synthfiler01:/export/other\t/srv/other\tnfs4\trw,relatime\n"
    )
    g = LineageGraph()
    cov = RuaInventoryExtractor().extract(_write_bundle(tmp_path, v2=True, mounts=mounts), g)
    node = _conform(g)
    assert node.properties["storage_scope"] == "unknown"
    assert "mount_root" not in node.properties and "fstype" not in node.properties
    assert cov.mount_unresolved > 0
    assert cov.mount_scope_unknown_fstype == 0  # nothing matched, so nothing to classify


def test_malformed_mount_rows_counted_never_dropped_silently(tmp_path: Path) -> None:
    mounts = (
        "source\ttarget\tfstype\toptions\n"
        "/dev/mapper/rootvg-root\t/\txfs\trw,relatime\n"
        "orphan-spec\t\txfs\trw\n"  # no target — unusable, and said so
        "broken-row\n"  # wrong cell count
    )
    g = LineageGraph()
    cov = RuaInventoryExtractor().extract(_write_bundle(tmp_path, v2=True, mounts=mounts), g)
    assert cov.mounts_rows == 1
    assert cov.mounts_malformed == 2
    assert _conform(g).properties["storage_scope"] == "local"  # the good row still works


def test_collector_emits_the_mount_columns_the_extractor_requires() -> None:
    """The G103 discipline applied to the new section: the collector's header
    literal and the extractor's required-column tuple are ONE contract held by
    two files, and both halves live in this repo. A column renamed on one side
    would otherwise surface as a bad-header count, i.e. as a bad bundle."""
    repo = Path(__file__).resolve().parents[2]
    collector = (repo / "drydocs_lineage" / "collect" / "rua_inventory.sh").read_text(
        encoding="utf-8"
    )
    from drydocs_lineage.extractors.rua_inventory import _REQUIRED_COLS, MOUNTS_TSV

    header = "printf 'source\\ttarget\\tfstype\\toptions\\n'"
    assert collector.count(header) == 2, (
        "the collector's mounts.tsv header changed (or a branch lost it) — "
        "update _REQUIRED_COLS[MOUNTS_TSV] and this test together"
    )
    assert _REQUIRED_COLS[MOUNTS_TSV] == ("source", "target", "fstype", "options")
    assert 'COLLECTOR_VERSION="rua-inventory/v3"' in collector


def test_storage_scope_map_is_exactly_the_amendment_set() -> None:
    """Pinned on purpose. Widening this map is an evidence decision that belongs
    with the SME, not a convenience edit — an fstype added here silently changes
    what every downstream corroboration claim is allowed to assert."""
    from drydocs_lineage.extractors.rua_inventory import storage_scope_for

    for shared in ("nfs", "nfs4", "cifs", "gfs2", "ocfs2", "NFS4"):
        assert storage_scope_for(shared) == "shared"
    for local in ("xfs", "ext4", "XFS"):
        assert storage_scope_for(local) == "local"
    for unknown in ("ext3", "btrfs", "tmpfs", "overlay", "zfs", "", "  "):
        assert storage_scope_for(unknown) == "unknown"
