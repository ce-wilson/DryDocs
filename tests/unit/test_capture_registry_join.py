"""Q23 — a capture run names the doc-source-registry row it fulfils.

The 7c18ff4b port review found a VERBATIM trust upgrade tracing to a run keyed
by a Confluence space + a free-text purpose — neither a registry id — so the
SME picked the row by hand. The join is now a mechanism: ONE resolver in
drydocs_docmeta.registry for both capture doors, error-not-warning, and the
vendor-scrape door refuses BEFORE any fetch."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from drydocs_docmeta.registry import (
    AmbiguousDocSourceError,
    UnknownDocSourceError,
    resolve_capture_registry_id,
)

FIXTURE = """
schema: drydocs.doc-source-registry.v1
updated: 2026-08-27
sources:
  - id: fixture-alpha
    classification: External
    source: "the alpha corpus fixture (frameworks prose)"
    connector: web
    trust_default: VERBATIM
    tier: T1
    curation: none
    target_db: drydocs
    refresh: manual
    confirmed: false
    manifest: {manifest_path}
    notes: "alpha"
  - id: fixture-beta
    classification: External
    source: "the beta corpus fixture (frameworks prose too)"
    connector: web
    trust_default: VERBATIM
    tier: T1
    curation: none
    target_db: drydocs
    refresh: manual
    confirmed: false
    notes: "beta"
"""


@pytest.fixture()
def fixture_registry(tmp_path: Path) -> tuple[Path, Path]:
    manifest_path = tmp_path / "capture-manifest.json"
    reg = tmp_path / "doc-source-registry.yaml"
    reg.write_text(FIXTURE.format(manifest_path=manifest_path.as_posix()), encoding="utf-8")
    return reg, manifest_path


# -- the resolver: error, never a warning --------------------------------------


def test_explicit_id_must_exist(fixture_registry) -> None:
    reg, _ = fixture_registry
    assert resolve_capture_registry_id("fixture-alpha", path=reg).id == "fixture-alpha"
    with pytest.raises(UnknownDocSourceError):
        resolve_capture_registry_id("no-such-row", path=reg)


def test_purpose_resolves_exactly_one_row_or_fails(fixture_registry) -> None:
    reg, _ = fixture_registry
    assert resolve_capture_registry_id(purpose="alpha", path=reg).id == "fixture-alpha"
    with pytest.raises(AmbiguousDocSourceError, match="fixture-alpha.*fixture-beta"):
        resolve_capture_registry_id(purpose="frameworks", path=reg)
    with pytest.raises(UnknownDocSourceError, match="matches no"):
        resolve_capture_registry_id(purpose="zzz-nothing", path=reg)


def test_a_run_with_no_id_and_no_purpose_does_not_run(fixture_registry) -> None:
    reg, _ = fixture_registry
    with pytest.raises(UnknownDocSourceError, match="does not run"):
        resolve_capture_registry_id(None, path=reg)


# -- (c) the round trip: run manifest <-> registry row -------------------------


def test_round_trip_manifest_names_the_row_and_the_row_finds_the_manifest(
    fixture_registry,
) -> None:
    reg, manifest_path = fixture_registry
    entry = resolve_capture_registry_id("fixture-alpha", path=reg)
    # the run stamps the RESOLVED id — never a space name, never a purpose string
    manifest_path.write_text(
        json.dumps({"corpus_id": entry.id, "captured_at": "2026-08-27T00:00:00Z"}),
        encoding="utf-8",
    )
    # and the row's manifest path resolves back to a manifest naming that id
    assert entry.manifest == manifest_path.as_posix()
    loaded = json.loads(Path(entry.manifest).read_text(encoding="utf-8"))
    assert loaded["corpus_id"] == entry.id


# -- the vendor-scrape door refuses before any fetch ---------------------------


def test_scrape_door_refuses_an_unregistered_tree_before_fetching(monkeypatch, capsys) -> None:
    import scripts.external_vendor_scrape as scrape

    tree = next(iter(scrape.TREES.values()))
    unregistered = scrape.replace(tree, corpus_id=None)
    monkeypatch.setitem(scrape.TREES, tree.id, unregistered)

    def _never(*a, **k):
        raise AssertionError("fetch must not run for a row-less capture")

    monkeypatch.setattr(scrape, "fetch", _never)
    rc = scrape.main([tree.id])
    assert rc == 2
    assert "REFUSED" in capsys.readouterr().err


def test_scrape_door_stamps_the_resolved_id(monkeypatch) -> None:
    """--registry-id overrides the tree's declared corpus_id, and the resolved
    row id is what the capture stamps (main rebinds the tree before fetch)."""
    import scripts.external_vendor_scrape as scrape

    seen: dict = {}

    def _capture(tree, entries, **kwargs):
        seen["corpus_id"] = tree.corpus_id
        return {
            "captured_at": "2026-08-27T00:00:00Z",
            "toc_nodes_recorded": 0,
            "documents": 0,
            "documents_fetched_this_run": 0,
            "documents_skipped_existing": 0,
            "failed": 0,
        }

    tree = next(iter(scrape.TREES.values()))
    monkeypatch.setattr(scrape, "fetch", lambda url: "{}")
    monkeypatch.setattr(scrape, "parse_toc", lambda raw, book=None: ([], {}))
    monkeypatch.setattr(scrape, "capture", _capture)
    rc = scrape.main([tree.id, "--registry-id", "bmc-docs"])
    assert rc == 0
    assert seen["corpus_id"] == "bmc-docs"
