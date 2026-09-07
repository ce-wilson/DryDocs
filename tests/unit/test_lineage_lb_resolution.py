"""Z4 — the load-balancer resolver, proven against a canned transcript.

NEVER LIVE DNS. The item's acceptance makes this explicit and it is not a
convenience: the live run is company-side by construction, so if the mechanism
could only be proven there it could not be proven at all. A transcript fixture
is the whole point — shell collects, Python parses, and the parser is the half
that has to be right.

Most of these tests are about ONE failure: recording the RESOLVER as the
machine a job runs on. An nslookup answer opens with the DNS server's own name
and address, and a parser that reads top-to-bottom will happily report
`10.0.0.53` as the box the batch runs on. It would look like data, place jobs
in the wrong city, and nothing downstream could tell.
"""

from __future__ import annotations

import json
from pathlib import Path

from drydocs_lineage.extractors.lb_resolution import (
    MATCH_TIER,
    SCHEMA,
    LbResolutionCoverage,
    parse_nslookup,
    read_meta,
    resolve_bundle,
)

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "tests" / "fixtures" / "lineage" / "lb_resolve"

#: The inventory side of the join, as :Server.name values would arrive. Short
#: names on purpose: the transcript answers with FQDNs, and the T2 rule has to
#: bridge them in both directions or nothing matches.
SERVERS = {"host-hldm-02", "host-hldm-03", "host-hldm-04", "host-auto-01"}


# --- the parser, and the four ways an nslookup answer is misread -------------


def test_the_resolvers_own_address_is_never_read_as_an_answer() -> None:
    """`Server:` / `Address: ...#53` is the DNS server, not the target."""
    answer = parse_nslookup(
        (BUNDLE / "nslookup" / "lb-hldm-pool.synth.txt").read_text(encoding="utf-8")
    )
    assert "10.0.0.53" not in answer.addresses
    assert answer.addresses == ("10.0.0.11", "10.0.0.12")


def test_a_cname_hop_is_an_alias_and_not_a_machine() -> None:
    """`canonical name =` names another label, never a host to place a job on."""
    answer = parse_nslookup(
        (BUNDLE / "nslookup" / "lb-hldm-pool.synth.txt").read_text(encoding="utf-8")
    )
    assert answer.aliases == ("pool-hldm-a.synth",)
    assert "pool-hldm-a.synth" not in answer.names


def test_an_answer_with_no_banner_still_parses() -> None:
    """An authoritative answer carries no 'Non-authoritative answer:' line.

    Finding the answer section by that string alone would drop every
    authoritative reply — silently, and only in the environments that have
    their own zone.
    """
    answer = parse_nslookup((BUNDLE / "nslookup" / "host-auto-01.txt").read_text(encoding="utf-8"))
    assert answer.names == ("host-auto-01.synth",)
    assert answer.addresses == ("10.0.0.21",)


def test_nxdomain_is_an_outcome_and_not_a_parse_failure() -> None:
    answer = parse_nslookup(
        (BUNDLE / "nslookup" / "no-such-alias.synth.txt").read_text(encoding="utf-8")
    )
    assert answer.nxdomain is True
    assert answer.answered is False
    assert answer.unreadable_reason is None


def test_a_transcript_with_no_subject_is_unreadable_not_silently_dropped() -> None:
    """A resolution with no queried name cannot be attributed to any host.

    Guessing one from the filename would attribute a DNS answer to whatever the
    file happened to be called — so it is counted as unreadable instead.
    """
    answer = parse_nslookup(
        (BUNDLE / "nslookup" / "garbled-answer.synth.txt").read_text(encoding="utf-8")
    )
    assert answer.unreadable_reason is not None
    assert "query" in answer.unreadable_reason


def test_a_caller_supplied_query_overrides_the_missing_comment() -> None:
    text = (BUNDLE / "nslookup" / "garbled-answer.synth.txt").read_text(encoding="utf-8")
    answer = parse_nslookup(text, query="lb-recovered.synth")
    assert answer.query == "lb-recovered.synth"
    assert answer.names == ("host-hldm-02.synth",)


# --- the match, and what it refuses to do ------------------------------------


def test_the_bundle_resolves_and_every_name_lands_in_exactly_one_bucket() -> None:
    report = resolve_bundle(BUNDLE, SERVERS)
    coverage = report.coverage
    assert coverage.total_queried == 6
    assert coverage.matched == 3  # hldm pool, mixed pool, the plain auto host
    assert coverage.unmatched == 1  # orphan pool: answered, nothing inventoried
    assert coverage.unresolved == 1  # NXDOMAIN
    assert coverage.unreadable == 1  # no queried name
    assert coverage.reconciles(), coverage.as_dict()


def test_one_alias_fanning_out_to_two_servers_yields_two_records() -> None:
    """The gate's own note: an LB alias may resolve to MANY servers at T3."""
    report = resolve_bundle(BUNDLE, SERVERS)
    fanned = [r for r in report.records if r.nodeid == "lb-hldm-pool.synth"]
    assert {r.server for r in fanned} == {"host-hldm-02", "host-hldm-03"}


def test_records_carry_the_edges_own_shape_so_the_loader_needs_no_translation() -> None:
    """server_resolution.py promises T3 feeds 'the same edge + evidence shape'."""
    report = resolve_bundle(BUNDLE, SERVERS)
    assert report.records, "the fixture must produce at least one record"
    for record in report.records:
        assert record.match_tier == MATCH_TIER == "dns-resolved"
        assert record.nodeid and record.server
        assert record.match_evidence, "an untraceable match is what the tiers exist to prevent"
        assert record.nodeid in record.match_evidence


def test_a_partially_inventoried_pool_keeps_the_half_it_can_place() -> None:
    """Half an answer is still evidence; dropping the pairing would lose it."""
    report = resolve_bundle(BUNDLE, SERVERS)
    mixed = [r for r in report.records if r.nodeid == "lb-mixed-pool.synth"]
    assert [r.server for r in mixed] == ["host-hldm-04"]


def test_an_answer_matching_no_inventory_server_is_listed_not_dropped() -> None:
    """The actionable half of a gap is WHICH names DNS gave, not how many."""
    report = resolve_bundle(BUNDLE, SERVERS)
    listed = dict(report.coverage.unmatched_names)
    assert "lb-orphan-pool.synth" in listed
    assert listed["lb-orphan-pool.synth"] == ("host-elsewhere-01.synth",)


def test_nothing_resolves_when_the_inventory_is_empty_and_that_reconciles() -> None:
    """An empty server list must report total absence, never crash or match."""
    report = resolve_bundle(BUNDLE, set())
    assert report.records == ()
    assert report.coverage.matched == 0
    # All FOUR transcripts that DNS answered — the three pools and the plain
    # host — become unmatched; the NXDOMAIN and the unreadable one keep their
    # own buckets, because "nothing to match against" is a different fact from
    # "nothing answered".
    assert report.coverage.unmatched == 4
    assert (report.coverage.unresolved, report.coverage.unreadable) == (1, 1)
    assert report.coverage.reconciles()


def test_coverage_that_does_not_reconcile_says_so() -> None:
    """The invariant has to be capable of failing, or it asserts nothing."""
    assert not LbResolutionCoverage(total_queried=4, matched=1).reconciles()


# --- the evidence file -------------------------------------------------------


def test_the_evidence_file_is_written_whole_and_reads_back(tmp_path: Path) -> None:
    report = resolve_bundle(BUNDLE, SERVERS)
    out = report.write(tmp_path / "lb-resolution.json")
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema"] == SCHEMA
    assert data["collector"]["schema"] == "lb-resolve/v1"
    assert data["coverage"]["reconciles"] is True
    assert len(data["records"]) == len(report.records)


def test_the_report_is_deterministic_so_two_runs_can_be_diffed() -> None:
    first = resolve_bundle(BUNDLE, SERVERS).as_dict()
    second = resolve_bundle(BUNDLE, SERVERS).as_dict()
    assert json.dumps(first) == json.dumps(second)


def test_the_collector_envelope_travels_onto_the_report() -> None:
    """Provenance rides with the evidence: which host, when, which tool."""
    report = resolve_bundle(BUNDLE, SERVERS)
    assert report.collector["lookup_source"] == "nslookup"
    assert report.collector["collected_at"] == "20260905T071500Z"
    assert read_meta(BUNDLE)["queried"] == "6"


def test_a_bundle_with_no_envelope_still_parses(tmp_path: Path) -> None:
    """An older or hand-assembled bundle degrades to unknown provenance."""
    (tmp_path / "nslookup").mkdir(parents=True)
    (tmp_path / "nslookup" / "a.txt").write_text(
        "; query: host-auto-01\nName:\thost-auto-01.synth\nAddress: 10.0.0.21\n",
        encoding="utf-8",
    )
    report = resolve_bundle(tmp_path, SERVERS)
    assert report.collector["schema"] == "unknown"
    assert report.coverage.matched == 1


def test_a_future_schema_tag_warns_without_refusing(tmp_path: Path) -> None:
    """Dispatch is on the sections PRESENT, never on the schema tag (rua's rule).

    A collector that gains a section must not make every older parser refuse
    the bundle — that is how a fleet of servers ends up unable to report.
    """
    import shutil

    copy = tmp_path / "bundle"
    shutil.copytree(BUNDLE, copy)
    (copy / "meta.txt").write_text(
        (BUNDLE / "meta.txt").read_text(encoding="utf-8").replace("lb-resolve/v1", "lb-resolve/v9"),
        encoding="utf-8",
    )
    report = resolve_bundle(copy, SERVERS)
    assert report.coverage.matched == 3, "a newer stamp must not stop the parse"
    assert any("newer than this parser" in note for note in report.coverage.notes)


# --- the collector script ----------------------------------------------------


def test_the_collector_ships_executable_with_an_lf_shebang() -> None:
    """A CRLF in the shebang breaks execution on the Linux hosts these run on.

    .gitattributes pins *.sh to LF for that reason; this asserts the file on
    disk actually is what the pin promises, since a checkout is where the pin
    either held or did not.
    """
    script = REPO / "drydocs_lineage" / "collect" / "lb_resolve.sh"
    raw = script.read_bytes()
    assert raw.startswith(b"#!/bin/sh\n"), "shebang must be the first line and LF-terminated"
    assert b"\r\n" not in raw, "CRLF in a collector script breaks it on the scheduler hosts"


def test_the_collector_stamps_its_version_into_every_bundle() -> None:
    """Two copies of this script will exist (server and repo) before they
    converge, so a transcript has to say which one wrote it."""
    script = (REPO / "drydocs_lineage" / "collect" / "lb_resolve.sh").read_text(encoding="utf-8")
    assert 'COLLECTOR_VERSION="lb-resolve/v1"' in script
    assert "schema=%s" in script


def test_the_collector_parses_nothing_itself() -> None:
    """Shell collects, Python parses (the rua_inventory.sh precedent).

    A transcript written verbatim can be re-read whole when the parser changes;
    fields extracted in shell cannot. This checks the answer files are produced
    by redirection rather than by a field-splitting pipeline.
    """
    script = (REPO / "drydocs_lineage" / "collect" / "lb_resolve.sh").read_text(encoding="utf-8")
    assert 'nslookup "$name"' in script
    for parser in ("awk ", "grep -o", "cut -d"):
        assert parser not in script, f"the collector must not parse ({parser!r} found)"
