"""G23 — the rua curated load (gate rua-load-shapes, SIGNED OFF 2026-08-07).

Pins, in ruling order:

- **§D2 extractor fix (the precondition):** occurrences ACCUMULATE as reified
  records — a second arrival of the same staged id appends the second host's
  record instead of dropping it (the as-built defect the clause exposed);
  cross_host_collisions stays the §D3 ambiguity counter.
- **§D1 identity:** normalization is MECHANICAL ONLY; malformed paths are
  counted, never loaded; the URN is a render, the path is the key.
- **§D2 grain (the acceptance's two-source fixture):** the SAME logical script
  arriving as a server-extract occurrence AND a code-repo occurrence (joined
  on CONTENT HASH, never path) plans ONE :Script with BOTH occurrence records
  — origin + full locator retained per record.
- **§D3:** only a qualified rua_fqdn resolves against ExecutionHost.nodeid;
  everything else is counted unresolvable, never prefix-matched.
- **Refusals:** the same trust-boundary and gate-bound-vocabulary contracts as
  write_curated, on the rua load's own labels (g22_occurrence_of /
  u1_is_encoded_in) — checked against the REAL registry, where both are
  active since G23.
- **Coverage:** the G20/G21/G24 counters ride the load report verbatim.

Synthetic fixtures only (the collector contract shapes from
test_lineage_rua.py); real bundles stay in the G19 landing zone.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from drydocs_lineage.extractors import CodeRepoExtractor, RuaInventoryExtractor
from drydocs_lineage.extractors.code_repo import git_blob_sha1
from drydocs_lineage.model import LineageGraph, ProcessNode, process_id
from drydocs_lineage.writer import (
    GateBoundVocabularyError,
    TrustBoundaryError,
    normalize_script_path,
    plan_rua,
    script_urn,
    write_rua,
)

HOST = "vsi-synth-01"
HOST2 = "vsi-synth-02"
USER = "svc_synth"
SHA_CONFORM = "bb" * 32

_META = """schema=rua-inventory/v2
collected_at=2026-07-23T12:00:00Z
collected_by={user}
user={user}
uid=4242
groups=synthgrp etl
login_shell=/bin/ksh
hostname={host}
fqdn={fqdn}
os=Linux
kernel=5.14.0-synth
scan_roots=/home/{user} /opt/app
"""

_DIRECTORIES = (
    "path\ttype\towner\tgroup\tperms\tsize\tmtime\n"
    f"/home/{USER}\td\t{USER}\tsynthgrp\t750\t4096\t2026-07-20 09:00\n"
)

_PROFILES = (
    "name\tpath\texists\tsize\tmtime\tperms\towner\tsha256\n"
    f".profile\t/home/{USER}/.profile\tyes\t42\t2026-07-20 09:00\t644\t{USER}\t{'aa' * 32}\n"
)

_SCRIPTS = (
    "path\towner\tgroup\tperms\tsize\tmtime\tsha256\n"
    f"/home/{USER}/app/conform.ksh\t{USER}\tsynthgrp\t644\t17\t2026-07-20 09:00\t{SHA_CONFORM}\n"
    f"/home/{USER}/app/big.ksh\t{USER}\tsynthgrp\t644\t500\t2026-07-20 09:00\t\n"
)

_CONFORM_BODY = b'echo "conform"\n'


def _write_bundle(root: Path, *, host: str = HOST, fqdn: str | None = None) -> Path:
    bundle = root / f"rua_{host}_{USER}_20260723T120000Z"
    bundle.mkdir(parents=True)
    (bundle / "meta.txt").write_text(
        _META.format(
            user=USER, host=host, fqdn=fqdn if fqdn is not None else f"{host}.example.internal"
        ),
        encoding="utf-8",
    )
    (bundle / "directories.tsv").write_text(_DIRECTORIES, encoding="utf-8")
    (bundle / "profiles").mkdir()
    (bundle / "profiles" / ".profile").write_text("export SYNTH=1\n", encoding="utf-8")
    (bundle / "profiles.tsv").write_text(_PROFILES, encoding="utf-8")
    (bundle / "scripts.tsv").write_text(_SCRIPTS, encoding="utf-8")
    copy = bundle / "scripts" / "home" / USER / "app"
    copy.mkdir(parents=True)
    (copy / "conform.ksh").write_bytes(_CONFORM_BODY)  # big.ksh = over-cap, no copy
    return bundle


def _manifest(root: Path, blob_sha: str) -> Path:
    manifest = root / "repo_objects.tsv"
    manifest.write_text(
        "repo\tref\tcommit\tcommit_date\tpath\tblob_sha\n"
        f"synth-repo\trefs/heads/main\tabc1234\t2026-07-01T00:00:00Z\tapp/conform.ksh\t{blob_sha}\n",
        encoding="utf-8",
    )
    return manifest


class _FakeClient:
    def __init__(self, database: str = "drydocs", known_hosts: tuple[str, ...] = ()) -> None:
        self._database = database
        self._known_hosts = set(known_hosts)
        self.calls: list[tuple[str, dict]] = []

    def connection_info(self) -> dict:
        return {"uri": "bolt://synthetic", "user": "u", "database": self._database}

    def run(self, cypher: str, params: dict | None = None, **kwargs) -> list[dict]:
        merged = {**(params or {}), **kwargs}
        self.calls.append((cypher, merged))
        if "UNWIND $fqdns" in cypher:
            return [{"fqdn": f, "resolved": f in self._known_hosts} for f in merged["fqdns"]]
        if "AS written" in cypher and "rows" in merged:
            return [{"written": len(merged["rows"])}]
        return []


# --- §D2 extractor fix: occurrences accumulate --------------------------------------


def test_second_host_arrival_accumulates_instead_of_dropping(tmp_path: Path) -> None:
    """THE §D2 defect, fixed: before, a second arrival of a staged id was
    counted (cross_host_collisions) and DISCARDED — the second host's origin,
    sha256, owner, perms, mtime and envelope never landed. Now both records
    exist on the node, and the counter still counts (it is the §D3 ambiguity
    signal, not the drop's excuse)."""
    g = LineageGraph()
    cov1 = RuaInventoryExtractor().extract(_write_bundle(tmp_path / "a", host=HOST), g)
    cov2 = RuaInventoryExtractor().extract(_write_bundle(tmp_path / "b", host=HOST2), g)
    assert cov1.cross_host_collisions == 0
    assert cov2.cross_host_collisions == 4  # dir + profile + 2 scripts re-arrived

    node = g.processes[process_id("rua_script", f"/home/{USER}/app/conform.ksh")]
    assert len(node.occurrences) == 2
    hosts = {occ.get("rua_host") for occ in node.occurrences}
    assert hosts == {HOST, HOST2}
    # the second record carries its own facts — nothing was overwritten or lost
    for occ in node.occurrences:
        assert occ.get("sha256") == SHA_CONFORM
        assert occ.get("owner") == USER
        assert occ.get("path") == f"/home/{USER}/app/conform.ksh"


def test_identical_restage_dedups_for_idempotent_staging(tmp_path: Path) -> None:
    g = LineageGraph()
    bundle = _write_bundle(tmp_path, host=HOST)
    RuaInventoryExtractor().extract(bundle, g)
    RuaInventoryExtractor().extract(bundle, g)
    node = g.processes[process_id("rua_script", f"/home/{USER}/app/conform.ksh")]
    assert len(node.occurrences) == 1


# --- §D1 normalization ----------------------------------------------------------------


def test_normalization_is_mechanical_only() -> None:
    assert normalize_script_path("/opt//scripts///x.ksh") == "/opt/scripts/x.ksh"
    assert normalize_script_path("/opt/scripts/") == "/opt/scripts"
    # NO case folding (POSIX is case-sensitive), NO symlink resolution
    assert normalize_script_path("/Opt/Scripts/X.KSH") == "/Opt/Scripts/X.KSH"
    # relative and ..-bearing are malformed, never guessed absolute
    assert normalize_script_path("relative/x.ksh") is None
    assert normalize_script_path("/opt/../etc/x.ksh") is None
    assert normalize_script_path("") is None
    assert script_urn("/opt/scripts/x.ksh") == "urn:drydocs:script:/opt/scripts/x.ksh"


def test_malformed_path_is_counted_never_loaded() -> None:
    g = LineageGraph()
    g.add_process(
        ProcessNode(
            node_id=process_id("rua_script", "relative/x.ksh"),
            kind="rua_script",
            name="x.ksh",
            path="relative/x.ksh",
        )
    )
    plan = plan_rua(g)
    assert plan.malformed_paths == 1
    assert plan.scripts == 0
    assert plan.statements == ()


# --- the plan: ruled node set + mechanics ---------------------------------------------


def test_plan_covers_the_ruled_node_set(tmp_path: Path) -> None:
    """Scripts + profile artifacts land as :Script (a profile IS a Script with
    script_role='profile', §C2), directories as :DataAsset, every staged
    observation as a :SourceOccurrence anchored OCCURRENCE_OF, and §C3's
    IS_ENCODED_IN derives from the extension via the shared core adapter."""
    g = LineageGraph()
    RuaInventoryExtractor().extract(_write_bundle(tmp_path), g)
    plan = plan_rua(g)

    assert plan.scripts == 3 and plan.profiles == 1
    assert plan.assets == 1
    assert plan.server_occurrences == 3
    assert plan.rel_types == ("IS_ENCODED_IN", "OCCURRENCE_OF")
    assert plan.encoded_in == 2  # the two .ksh scripts → SWO Shell
    assert plan.unbound_extensions == 1  # .profile has no seeded term — reported
    assert plan.hash_missing == 1  # big.ksh staged hash-absent (§G2, a real state)

    cyphers = [c for c, _ in plan.statements]
    assert any("CREATE CONSTRAINT script_path IF NOT EXISTS" in c for c in cyphers)
    assert any("CREATE CONSTRAINT sourceoccurrence_id IF NOT EXISTS" in c for c in cyphers)
    occ = next(c for c in cyphers if "MERGE (o:SourceOccurrence" in c)
    assert "MERGE (o:SourceOccurrence {occurrenceId: row.occurrence_id})" in occ
    assert "MERGE (o)-[r:OCCURRENCE_OF]->(s)" in occ
    assert "r.vocab_id      = 'g22_occurrence_of'" in occ
    assert "MATCH (s:Script {path: row.script_path})" in occ  # scripts are MERGEd first
    enc = next(c for c in cyphers if "IS_ENCODED_IN" in c)
    assert "OPTIONAL MATCH (lang:OntologyTerm:SwoClass {iri: row.language_iri})" in enc
    assert "enc.vocab_id      = 'u1_is_encoded_in'" in enc

    script_rows = next(p for c, p in plan.statements if "MERGE (s:Script" in c)["rows"]
    profile_row = next(r for r in script_rows if r["path"] == f"/home/{USER}/.profile")
    assert profile_row["script_role"] == "profile"
    conform_row = next(r for r in script_rows if r["path"].endswith("conform.ksh"))
    assert conform_row["script_role"] is None
    assert conform_row["urn"] == script_urn(f"/home/{USER}/app/conform.ksh")

    asset_rows = next(p for c, p in plan.statements if "MERGE (a:DataAsset" in c)["rows"]
    assert asset_rows[0]["asset_id"] == f"urn:drydocs:dataasset:rua_path:/home:{USER}"
    # §C1 is K17-blocked: the directory owner is a PLAIN property, no edge
    assert asset_rows[0]["props"]["owner"] == USER
    assert not any(
        "AppUser" in c or "DELEGATES_TO" in c or "WAS_ATTRIBUTED_TO" in c for c in cyphers
    )


def test_occurrence_rows_carry_origin_locator_and_envelope(tmp_path: Path) -> None:
    g = LineageGraph()
    RuaInventoryExtractor().extract(_write_bundle(tmp_path), g)
    plan = plan_rua(g)
    rows = next(p for c, p in plan.statements if "SourceOccurrence" in c and "rows" in p)["rows"]
    conform = next(r for r in rows if r["script_path"] == f"/home/{USER}/app/conform.ksh")
    urn = script_urn(f"/home/{USER}/app/conform.ksh")
    assert conform["occurrence_id"] == (
        f"{urn}#server-extract#{HOST}.example.internal#/home/{USER}/app/conform.ksh"
    )
    props = conform["props"]
    assert props["origin"] == "server-extract"
    assert props["host"] == f"{HOST}.example.internal"
    assert props["path"] == f"/home/{USER}/app/conform.ksh"
    assert props["sha256"] == SHA_CONFORM
    assert props["storage_scope"] == "unknown"  # until G56 captures the mount table
    # the §D4 as-built envelope split: rua_* capture props ride the record
    assert props["rua_user"] == USER
    assert props["rua_collected_at"] == "2026-07-23T12:00:00Z"


# --- the acceptance's two-source fixture ----------------------------------------------


def test_two_source_fixture_single_node_both_records(tmp_path: Path) -> None:
    """THE acceptance clause: the SAME logical script arriving as a
    server-extract occurrence AND a code-repo occurrence (content-hash join —
    never path) plans ONE :Script on the §D1 URN with BOTH source records,
    origin + full locator retained on each."""
    bundle = _write_bundle(tmp_path)
    g = LineageGraph()
    RuaInventoryExtractor().extract(bundle, g)
    CodeRepoExtractor().extract(_manifest(tmp_path, git_blob_sha1(_CONFORM_BODY)), g)

    plan = plan_rua(g, bundle_dir=bundle)
    assert plan.repo_occurrences == 1
    assert plan.repo_join_uncomputable == 1  # big.ksh has no carried copy to hash

    rows = next(p for c, p in plan.statements if "SourceOccurrence" in c and "rows" in p)["rows"]
    conform_path = f"/home/{USER}/app/conform.ksh"
    conform = [r for r in rows if r["script_path"] == conform_path]
    assert len(conform) == 2  # ONE script key, BOTH occurrence records
    by_origin = {r["props"]["origin"]: r for r in conform}
    assert set(by_origin) == {"server-extract", "code-repo"}
    server, repo = by_origin["server-extract"], by_origin["code-repo"]
    assert server["props"]["path"] == conform_path  # host+path locator
    assert repo["props"]["path"] == "app/conform.ksh"  # repo+ref+commit+path locator
    assert repo["props"]["repo"] == "synth-repo"
    assert repo["props"]["ref"] == "refs/heads/main"
    assert repo["props"]["commit"] == "abc1234"
    assert repo["props"]["blob_sha"] == git_blob_sha1(_CONFORM_BODY)
    assert server["occurrence_id"] != repo["occurrence_id"]

    # no :Script row was planned for the repo side by path — the join is the
    # hash, and repo-only rows have no §D1 absolute path to key on
    script_rows = next(p for c, p in plan.statements if "MERGE (s:Script" in c)["rows"]
    assert all(not r["path"].startswith("app/") for r in script_rows)


# --- multi-host identity (D-amendment) ------------------------------------------------


def test_multi_host_scripts_flag_identity_unconfirmed(tmp_path: Path) -> None:
    """§D1 + the D-amendment: same path on N hosts stays ONE node (the path is
    the key), and with storage_scope unknown the claim is suppressed — the
    node carries identity_unconfirmed_across_hosts, counted, never silently
    read as corroborated."""
    g = LineageGraph()
    RuaInventoryExtractor().extract(_write_bundle(tmp_path / "a", host=HOST), g)
    RuaInventoryExtractor().extract(_write_bundle(tmp_path / "b", host=HOST2), g)
    plan = plan_rua(g)
    assert plan.scripts == 3  # ONE node per path — never re-keyed per host
    assert plan.server_occurrences == 6
    assert plan.multi_host_unconfirmed == 3
    script_rows = next(p for c, p in plan.statements if "MERGE (s:Script" in c)["rows"]
    assert all(r["identity_unconfirmed"] is True for r in script_rows)


# --- §D3 host resolution ---------------------------------------------------------------


def test_only_qualified_fqdns_are_resolution_candidates(tmp_path: Path) -> None:
    """A bare hostname is NEVER matched (§D3 — a prefix match across domains
    binds a script to the WRONG server); records without a qualified fqdn are
    counted unresolvable."""
    g = LineageGraph()
    RuaInventoryExtractor().extract(_write_bundle(tmp_path / "a", host=HOST), g)
    RuaInventoryExtractor().extract(_write_bundle(tmp_path / "b", host=HOST2, fqdn=HOST2), g)
    plan = plan_rua(g)
    assert plan.hosts == (f"{HOST}.example.internal",)
    assert plan.hosts_unqualified == 3  # the three HOST2 records — bare spelling


def test_write_resolves_hosts_and_counts_misses(tmp_path: Path) -> None:
    g = LineageGraph()
    RuaInventoryExtractor().extract(_write_bundle(tmp_path / "a", host=HOST), g)
    RuaInventoryExtractor().extract(_write_bundle(tmp_path / "b", host=HOST2), g)
    client = _FakeClient(known_hosts=(f"{HOST}.example.internal",))
    report = write_rua(g, client)
    assert report.hosts_resolved == 1
    assert report.hosts_unresolved == (f"{HOST2}.example.internal",)
    # resolution is a READ — rua mints no second host identity
    assert not any("MERGE (h:ExecutionHost" in c for c, _ in client.calls)


# --- refusals + the live load ----------------------------------------------------------


def test_write_requires_a_client(tmp_path: Path) -> None:
    g = LineageGraph()
    RuaInventoryExtractor().extract(_write_bundle(tmp_path), g)
    with pytest.raises(ValueError, match="plan_rua"):
        write_rua(g)


def test_trust_boundary_refuses_other_databases(tmp_path: Path) -> None:
    g = LineageGraph()
    RuaInventoryExtractor().extract(_write_bundle(tmp_path), g)
    with pytest.raises(TrustBoundaryError, match="drydocs"):
        write_rua(g, _FakeClient(database="ddcontext"))


def test_gate_bound_on_a_planned_registry(tmp_path: Path) -> None:
    """The rua load carries its OWN gate check: a registry where the occurrence
    edge is still planned refuses the live load — the gate is a registry read,
    exactly as for write_curated."""
    registry = tmp_path / "vocab.yaml"
    registry.write_text(
        "  - id:           g22_occurrence_of\n"
        "    status:       planned\n"
        "  - id:           u1_is_encoded_in\n"
        "    status:       active\n",
        encoding="utf-8",
    )
    g = LineageGraph()
    RuaInventoryExtractor().extract(_write_bundle(tmp_path), g)
    with pytest.raises(GateBoundVocabularyError, match="g22_occurrence_of"):
        write_rua(g, _FakeClient(), registry=registry)


def test_live_load_executes_against_the_real_registry(tmp_path: Path) -> None:
    """g22_occurrence_of and u1_is_encoded_in are both status: active in the
    real registry since G23 — the live load proceeds and the report carries
    the write counts plus the passed-through extractor coverage."""
    g = LineageGraph()
    cov = RuaInventoryExtractor().extract(_write_bundle(tmp_path), g)
    client = _FakeClient(known_hosts=(f"{HOST}.example.internal",))
    report = write_rua(g, client, coverage={"rua_inventory": cov.as_dict()})
    assert report.occurrence_edges_written == 3
    assert report.encoded_in_written == 2
    assert report.hosts_resolved == 1 and report.hosts_unresolved == ()
    assert report.coverage["rua_inventory"]["scripts_staged"] == 2
    assert "occurrences=3+0" in report.summary()
    ran = [c for c, _ in client.calls]
    assert any("CREATE CONSTRAINT sourceoccurrence_id" in c for c in ran)
    assert all("written_at" in p for c, p in client.calls if "UNWIND $rows" in c)


def test_replan_is_deterministic(tmp_path: Path) -> None:
    """Idempotent re-load rests on MERGE over deterministic identity keys —
    the same staging plans the same statements, byte for byte."""
    bundle = _write_bundle(tmp_path)
    g = LineageGraph()
    RuaInventoryExtractor().extract(bundle, g)
    assert plan_rua(g).statements == plan_rua(g).statements
