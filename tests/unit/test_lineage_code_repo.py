"""G24 — code-repo source seam + server/repo corroboration.

SYNTHETIC fixtures (shape-faithful, value-fake). Cases pin the acceptance:
(a) manifest rows stage in the SAME shape as G20's records, differing only in
    provenance origin (origin=code-repo with repo/ref/commit vs
    origin=server-extract with host/path/mtime);
(b) the corroboration report joins on git blob CONTENT hash into the four
    verdict buckets, names the de-facto current ref mechanically, and lists
    path-tail hints only as the weak fallback;
(c) trusted_ref comes from the registry field and is checked, never inferred;
(d) unmatched/uncomputable records are counted, never dropped; no rels, no
    new relationship types, no graph writes.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from drydocs_lineage.extractors import (
    CodeRepoExtractor,
    RuaInventoryExtractor,
    corroborate,
    git_blob_sha1,
)
from drydocs_lineage.model import LineageGraph, process_id

USER = "svc_synth"
REPO = "synth-org/etl-scripts"

# server-side contents (carried-back copies)
CURRENT = "#!/bin/ksh\necho current\n"       # committed at the live ref tip
OLD_AHEAD = "#!/bin/ksh\necho old-version\n"  # in HISTORY only (no live tip) —
                                              # the server still runs it: "behind"
ROGUE = "#!/bin/ksh\necho never-committed\n"  # absent from the repo entirely
# NOTE the honest limit (recorded in the module docstring too): locally EDITED
# running code matches no repo object at all and lands in never_committed —
# pure content hashing cannot tell edited-after-checkout from never-committed;
# the path-tail hints are the weak signal for that case.

_META = f"""schema=rua-inventory/v2
collected_at=2026-07-27T12:00:00Z
user={USER}
hostname=vsi-synth-01
scan_roots=/opt/app
"""


def _write_bundle(root: Path) -> Path:
    bundle = root / f"rua_vsi-synth-01_{USER}_20260727"
    scripts_dir = bundle / "scripts" / "opt" / "app"
    scripts_dir.mkdir(parents=True)
    (bundle / "meta.txt").write_text(_META, encoding="utf-8")
    (bundle / "directories.tsv").write_text(
        "path\ttype\towner\tgroup\tperms\tsize\tmtime\n",
        encoding="utf-8",
    )
    (bundle / "profiles.tsv").write_text(
        "name\tpath\texists\tsize\tmtime\tperms\towner\n", encoding="utf-8"
    )
    rows = ["path\towner\tgroup\tperms\tsize\tmtime"]
    for fname, content in (
        ("current.ksh", CURRENT), ("ahead.ksh", OLD_AHEAD), ("rogue.ksh", ROGUE),
    ):
        rows.append(f"/opt/app/{fname}\t{USER}\tsynthgrp\t750\t40\t2026-07-20 09:00")
        # bytes verbatim — the content hash is over what is ON DISK, and
        # write_text would CRLF-translate on Windows
        (scripts_dir / fname).write_bytes(content.encode("utf-8"))
    # listed but no copy carried back — uncomputable, counted
    rows.append(f"/opt/app/nocopy.ksh\t{USER}\tsynthgrp\t750\t40\t2026-07-20 09:00")
    (bundle / "scripts.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    return bundle


def _write_manifest(root: Path) -> Path:
    sha_current = git_blob_sha1(CURRENT.encode())
    sha_old = git_blob_sha1(OLD_AHEAD.encode())
    sha_repo_only = git_blob_sha1(b"repo only blob\n")
    lines = [
        "repo\tref\tcommit\tcommit_date\tpath\tblob_sha",
        # live tip carries current.ksh (two refs — main older, release newer)
        f"{REPO}\tmain\tc001\t2026-07-01\tetl/current.ksh\t{sha_current}",
        f"{REPO}\trelease/2026.07\tc009\t2026-07-20\tetl/current.ksh\t{sha_current}",
        # ahead.ksh: only a HISTORICAL blob of the same path (empty ref)
        f"{REPO}\t\tc003\t2026-05-01\tetl/ahead.ksh\t{sha_old}",
        # a repo file no server copy matches
        f"{REPO}\tmain\tc001\t2026-07-01\tetl/unused_helper.ksh\t{sha_repo_only}",
        # a same-basename file for the rogue path-tail hint
        f"{REPO}\tmain\tc001\t2026-07-01\told/rogue.ksh\t{sha_repo_only}",
    ]
    manifest = root / "repo_objects.tsv"
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest


@pytest.fixture()
def corroborated(tmp_path):
    bundle = _write_bundle(tmp_path)
    manifest = _write_manifest(tmp_path)
    graph = LineageGraph()
    RuaInventoryExtractor().extract(bundle, into=graph)
    cov = CodeRepoExtractor().extract(manifest, into=graph)
    report = corroborate(graph, bundle, trusted_ref="main")
    return graph, cov, report


def test_a_same_shape_two_origins(corroborated) -> None:
    graph, cov, _ = corroborated
    assert cov.staged == 4  # current, ahead(historical), unused_helper, old/rogue
    assert cov.historical_rows == 1
    repo_node = graph.processes[process_id("repo_script", f"{REPO}:etl/current.ksh")]
    server_node = graph.processes[process_id("rua_script", "/opt/app/current.ksh")]
    assert repo_node.properties["origin"] == "code-repo"
    assert repo_node.properties["repo"] == REPO
    assert server_node.properties["origin"] == "server-extract"
    assert server_node.properties["rua_host"] == "vsi-synth-01"
    # same staging shape: both are ProcessNodes on the same graph, and the
    # two origins never collide on id (identity is G22's ruling)
    assert repo_node.node_id != server_node.node_id


def test_b_verdict_buckets_and_mechanical_candidate_ref(corroborated) -> None:
    _, _, report = corroborated
    assert [e["server_path"] for e in report.found_at_refs] == ["/opt/app/current.ksh"]
    refs = {h["ref"] for h in report.found_at_refs[0]["refs"]}
    assert refs == {"main", "release/2026.07"}
    # mechanical naming: the most recent matching tip
    assert report.candidate_ref == "release/2026.07"
    assert [e["server_path"] for e in report.behind] == ["/opt/app/ahead.ksh"]
    assert report.behind[0]["commits"][0]["commit"] == "c003"
    rogue = [e for e in report.never_committed if e["server_path"] == "/opt/app/rogue.ksh"]
    assert rogue and rogue[0]["path_tail_hints"] == ["old/rogue.ksh"]
    assert {e["repo_path"] for e in report.repo_only} == {
        "etl/unused_helper.ksh", "old/rogue.ksh",
    }


def test_c_trusted_ref_checked_never_inferred(corroborated) -> None:
    _, _, report = corroborated
    # blessed 'main' IS among the found refs — confirmed; but candidate_ref
    # (mechanical) still names the newer tip: the two are separate signals
    assert report.trusted_ref == "main"
    assert report.trusted_ref_confirmed is True
    assert report.candidate_ref != report.trusted_ref


def test_c2_null_trusted_ref_stays_null(tmp_path) -> None:
    bundle = _write_bundle(tmp_path)
    manifest = _write_manifest(tmp_path)
    graph = LineageGraph()
    RuaInventoryExtractor().extract(bundle, into=graph)
    CodeRepoExtractor().extract(manifest, into=graph)
    report = corroborate(graph, bundle)  # no trusted_ref declared
    assert report.trusted_ref is None
    assert report.trusted_ref_confirmed is None  # not inferred from findings


def test_d_counted_never_dropped_and_no_writes(corroborated) -> None:
    graph, _, report = corroborated
    assert report.server_uncomputable == 1  # nocopy.ksh
    # candidates only: the seam adds NO rels of any type
    assert not [r for r in graph.rels if "repo_script" in r[0] or "repo_script" in r[2]]
    summary = report.summary()
    assert "never_committed=1" in summary and "uncomputable=1" in summary


def test_registry_carries_the_trusted_ref_field() -> None:
    reg = yaml.safe_load(
        Path("config/source-registry.yaml").read_text(encoding="utf-8")
    )
    # v2 (N9): code-repo retired -> the bitbucket:repo-objects-manifest dataset;
    # classification lives on the bitbucket SYSTEM row.
    entry = next(s for s in reg["datasets"] if s["id"] == "bitbucket:repo-objects-manifest")
    assert "trusted_ref" in entry and entry["trusted_ref"] is None
    assert entry["confirmed"] is False
    system = next(s for s in reg["systems"] if s["id"] == entry["system"])
    assert system["classification"] == "Internal"
