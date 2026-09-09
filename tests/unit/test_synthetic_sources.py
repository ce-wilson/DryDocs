"""The synthetic stand-ins: generator, bundle, extraction, DataHub emission.

Two skip rules, both deliberate. The bundle
(``drydocs/data/samples/synthetic-sources.json.gz``) is never-port, so every
test that READS it skips when it is absent — a consumer tree has no data and
"not tested" is the truthful verdict, not "failed". And ``duckdb`` is not a repo
dependency, so the load test ``importorskip``s it. The generator itself needs
neither and always runs.
"""

from __future__ import annotations

import csv
import gzip
import io
import json
from pathlib import Path

import pytest

from drydocs.seal_samples import RESERVED_SEALID_RANGE, SYNTHETIC_EMAIL_DOMAIN
from drydocs.source_registration import bundle as bundle_mod
from drydocs.source_registration.datahub_emit import build_mcps, dataset_name
from drydocs.source_registration.synthetic import SyntheticSources
from drydocs_core.source_descriptors import SourceDescriptors


@pytest.fixture(scope="module")
def descriptors() -> SourceDescriptors:
    return SourceDescriptors.from_yaml()


@pytest.fixture(scope="module")
def tables(descriptors):
    return SyntheticSources(descriptors).tables()


def _bundle_or_skip(descriptors) -> Path:
    p = bundle_mod.bundle_path(descriptors)
    if not p.is_file():
        pytest.skip(f"{p.name} absent - never-port, consumer tree: not tested, no data")
    return p


def _rows(table) -> list[dict]:
    return list(csv.DictReader(io.StringIO(table.to_csv())))


# ----------------------------------------------------------------- generator


def test_generator_is_deterministic(descriptors):
    a = SyntheticSources(descriptors).tables()
    b = SyntheticSources(descriptors).tables()
    assert [(t.source_id, t.name, t.to_csv()) for t in a] == [
        (t.source_id, t.name, t.to_csv()) for t in b
    ]


def test_generator_covers_every_planned_file_exactly(descriptors, tables):
    planned = {(p.source_id, f) for p in descriptors.synthetic_plans() for f in p.files}
    assert {(t.source_id, t.name) for t in tables} == planned


def test_every_row_is_marked_as_a_sample(descriptors, tables):
    field = descriptors.synthetic["record_origin_field"]
    value = descriptors.synthetic["record_origin_value"]
    for t in tables:
        assert t.header[-1] == field, t.name
        rows = _rows(t)
        assert rows, t.name
        assert {r[field] for r in rows} == {value}, t.name


def test_identifiers_stay_inside_the_synthetic_fences(tables):
    by_name = {t.name: t for t in tables}
    for r in _rows(by_name["seal_applications.csv"]):
        assert int(r["app_id"]) in RESERVED_SEALID_RANGE
    for r in _rows(by_name["seal_contacts.csv"]):
        assert r["employee_email"].endswith("@" + SYNTHETIC_EMAIL_DOMAIN)
        assert r["employee_sid"].startswith("K7")  # K700000+, never a real SID shape
    for r in _rows(by_name["pat_product_mapping.csv"]):
        for sid in filter(None, r["seal_ids"].split("; ")):
            assert int(sid) in RESERVED_SEALID_RANGE


# -------------------------------------------------------------------- bundle


def test_pack_is_byte_stable(descriptors, tables):
    gen = SyntheticSources(descriptors)
    assert bundle_mod.pack(tables, gen.seed) == bundle_mod.pack(tables, gen.seed)


def test_committed_bundle_matches_the_generator(descriptors, tables):
    """The tracked .json.gz IS the generator's output at this config; a diff
    means one of them changed without the other.

    Compared as the DECOMPRESSED PAYLOAD, not as the compressed bytes, and that
    distinction is the whole point of the test. gzip guarantees that a stream
    decompresses to one answer; it guarantees nothing about which stream an
    encoder produces for a given input. CPython links zlib-ng on some platforms
    and stock zlib on others, and the two deflate the same bytes differently at
    the same level, so a raw-bytes comparison fails everywhere except the
    machine that happened to write the file. It did: the bundle was committed
    from Windows and this assertion was red on every Linux runner, with the gzip
    trailer -- the payload's checksum and length -- identical on both sides,
    which is what proves the disagreement was never about content.
    """
    p = _bundle_or_skip(descriptors)
    gen = SyntheticSources(descriptors)
    committed = gzip.decompress(p.read_bytes())
    rebuilt = gzip.decompress(bundle_mod.pack(tables, gen.seed))
    assert committed == rebuilt, "bundle stale: python scripts/build_synthetic_sources.py --bundle"


def test_extract_lands_in_the_loader_zones(descriptors, tmp_path):
    _bundle_or_skip(descriptors)
    written = bundle_mod.extract(descriptors, out_root=tmp_path)
    assert written
    for item in written:
        assert item.path.is_file()
        assert item.path.is_relative_to(tmp_path)  # never into the repo tree
    # SOURCE-mode chain steps read <step>.csv from the registry's drop_dir
    assert (tmp_path / "pat" / "catalog_lobs.csv").is_file()
    assert (tmp_path / "seal" / "seal_applications.csv").is_file()
    # a base: repo zone is redirected under <out_root>/repo, never into the checkout
    assert (tmp_path / "repo" / "internal" / "server-inventory" / "server_inventory.csv").is_file()
    # db-carried datasets get a CSV mirror
    mirror = tmp_path / descriptors.synthetic["mirror_dir"]
    assert (mirror / "controlm_jobs.csv").is_file()
    assert {i.placement for i in written} == {"zone", "mirror"}


def test_duckdb_load_when_available(descriptors, tmp_path):
    duckdb = pytest.importorskip("duckdb")
    _bundle_or_skip(descriptors)
    from drydocs.source_registration.duckdb_load import RUN_TABLE, SOURCES_TABLE, load

    written = bundle_mod.extract(descriptors, out_root=tmp_path)
    db = tmp_path / "synthetic.duckdb"
    counts = load(descriptors, written, db)
    assert set(counts) == {Path(w.name).stem for w in written}
    con = duckdb.connect(str(db), read_only=True)
    try:
        (n,) = con.execute(f"SELECT count(*) FROM {SOURCES_TABLE}").fetchone()
        assert n == len(written)
        (seed,) = con.execute(f"SELECT seed FROM {RUN_TABLE}").fetchone()
        assert seed == descriptors.synthetic["seed"]
        (origins,) = con.execute(
            "SELECT count(DISTINCT record_origin) FROM seal_applications"
        ).fetchone()
        assert origins == 1
    finally:
        con.close()


# ------------------------------------------------------------------- datahub


def test_dataset_names_are_urn_safe_and_unique(descriptors):
    names = [dataset_name(d.source_id) for d in descriptors.all()]
    assert len(set(names)) == len(names)
    for n in names:
        assert n.replace("_", "").replace("-", "").replace(".", "").isalnum(), n


def test_mcp_file_registers_every_system_and_dataset(descriptors, tables):
    mcps = build_mcps(descriptors, tables)
    by = {}
    for m in mcps:
        by.setdefault((m["entityType"], m["aspectName"]), []).append(m)
    n_sys = len(descriptors.systems())
    n_ds = len(descriptors.all())
    assert len(by[("container", "containerProperties")]) == n_sys
    assert len(by[("dataset", "datasetProperties")]) == n_ds
    assert len(by[("dataset", "globalTags")]) == n_ds
    # one schema per dataset that has a synthetic stand-in
    assert len(by[("dataset", "schemaMetadata")]) == len({t.source_id for t in tables})
    # every dataset carries the five axes as custom properties and as tags
    for m in by[("dataset", "datasetProperties")]:
        props = m["aspect"]["json"]["customProperties"]
        assert set(props) >= set(descriptors.axes) | {"drydocs_id", "drydocs_urn"}
    for m in by[("dataset", "globalTags")]:
        tags = {t["tag"] for t in m["aspect"]["json"]["tags"]}
        assert len([t for t in tags if t.startswith("urn:li:tag:drydocs.")]) >= 5
    # every tag used is declared as a tag entity
    used = {t["tag"] for m in by[("dataset", "globalTags")] for t in m["aspect"]["json"]["tags"]}
    declared = {m["entityUrn"] for m in by[("tag", "tagProperties")]}
    assert used == declared
    # the file-sink shape: aspect under "json", systemMetadata present
    for m in mcps:
        assert set(m) == {
            "entityType",
            "entityUrn",
            "changeType",
            "aspectName",
            "aspect",
            "systemMetadata",
        }
        assert "json" in m["aspect"]


def test_mcp_emission_is_deterministic(descriptors, tables):
    a = json.dumps(build_mcps(descriptors, tables), sort_keys=True)
    b = json.dumps(build_mcps(descriptors, tables), sort_keys=True)
    assert a == b
