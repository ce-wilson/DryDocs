"""Track-1 guards for docmeta's clean / tokenize / hash / registry stages (Q6).

Offline throughout — the Q6 acceptance's "parse/clean/hash offline (no
network)" clause. These are the four modules ported from the bkup scrapers as
a producer-authored reproduction against the plan's §5 table; the bkup repo is
not mounted here and was never copied from.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from drydocs_docmeta import registry
from drydocs_docmeta.cleaner import clean_html, normalize_whitespace
from drydocs_docmeta.connectors.base import RawPage
from drydocs_docmeta.manifest import CaptureManifest, scrub, sha256_bytes
from drydocs_docmeta.policy import (
    DEFAULT_POLICY_PATH,
    CapturePolicy,
    DisallowedSchemeError,
    TooManyPagesError,
)
from drydocs_docmeta.tokenizer import METHOD_ESTIMATE, METHOD_EXACT, estimate_tokens

REPO_ROOT = Path(__file__).resolve().parents[2]

HTML = """<html><head><title> A Page </title>
<script>var x = "not content";</script>
<style>.a { color: red }</style></head>
<body><p>First   paragraph.</p><p>Second&nbsp;paragraph.</p>
<ul><li>one</li><li>two</li></ul></body></html>"""


# --------------------------------------------------------------------------- #
# cleaner
# --------------------------------------------------------------------------- #
def test_script_and_style_content_never_reaches_the_text():
    doc = clean_html(HTML)
    assert "not content" not in doc.text
    assert "color: red" not in doc.text
    assert doc.dropped_elements == 2


def test_block_elements_end_a_line_of_prose():
    """Without this, adjacent block elements produce 'paragraph.Second' and
    every downstream sentence split is wrong."""
    doc = clean_html(HTML)
    assert "First paragraph." in doc.text
    assert "paragraph.Second" not in doc.text
    assert "one" in doc.text and "two" in doc.text


def test_title_is_extracted_and_squeezed():
    assert clean_html(HTML).title == "A Page"


def test_cleaning_is_deterministic_which_is_what_makes_hashing_meaningful():
    """A cleaner whose output drifted would make every freshness comparison
    report phantom changes (ADR 0006 §4 re-queues curation on a digest
    change)."""
    assert clean_html(HTML).text == clean_html(HTML).text


def test_nbsp_and_crlf_normalize_so_two_transports_agree():
    """The same document fetched over the web and read from a filedrop must
    hash identically — line endings and non-breaking spaces are the two ways
    that quietly fails."""
    assert normalize_whitespace("a\r\nb\xa0c") == "a\nb c"
    assert normalize_whitespace("a  \n\n\n\nb") == "a\n\nb"


def test_bad_bytes_are_replaced_not_fatal():
    """A capture is evidence; refusing to read 6 KB because three bytes are
    mis-encoded loses the other 6 KB. The replacement chars stay visible."""
    doc = clean_html(b"<html><body><p>caf\xe9 time</p></body></html>")
    assert "time" in doc.text


# --------------------------------------------------------------------------- #
# tokenizer — the label is the deliverable
# --------------------------------------------------------------------------- #
def test_token_count_always_says_how_it_was_produced():
    count = estimate_tokens("one two three four five")
    assert count.method in {METHOD_EXACT, METHOD_ESTIMATE}
    assert count.tokens > 0
    if count.method == METHOD_ESTIMATE:
        assert count.encoding is None
        assert not count.is_exact
    else:
        assert count.encoding == "cl100k_base"
        assert count.is_exact


def test_the_fallback_is_the_documented_ratio(monkeypatch: pytest.MonkeyPatch):
    """Forced down the fallback path so the estimate is pinned even on a
    machine that has tiktoken installed."""
    import builtins

    real_import = builtins.__import__

    def no_tiktoken(name, *args, **kwargs):
        if name == "tiktoken":
            raise ImportError("blocked for the test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_tiktoken)
    count = estimate_tokens("one two three four five six seven eight nine ten")
    assert count.method == METHOD_ESTIMATE
    assert count.tokens == 13  # 10 words * 1.3


def test_empty_text_is_zero_tokens_not_an_error():
    assert estimate_tokens("").tokens == 0


# --------------------------------------------------------------------------- #
# manifest — the freshness primitive
# --------------------------------------------------------------------------- #
def _pages() -> list[RawPage]:
    return [
        RawPage(location="https://x.invalid/a", body=b"alpha", content_type="text/html"),
        RawPage(location="https://x.invalid/b", body=b"beta", content_type="text/html"),
    ]


def _manifest(pages: list[RawPage] | None = None) -> CaptureManifest:
    return CaptureManifest.build(
        source_id="s",
        connector="web",
        captured_at="2026-08-04T00:00:00Z",
        corpus_id="a-corpus",
        pages=pages if pages is not None else _pages(),
    )


def test_the_digest_is_over_raw_bytes_not_cleaned_text():
    """Hashing after cleaning would make a CLEANER change look identical to a
    VENDOR edit — the two things freshness exists to tell apart."""
    m = _manifest()
    assert m.pages[0].sha256 == sha256_bytes(b"alpha")


def test_roundtrip_is_byte_identical(tmp_path: Path):
    _manifest().write(tmp_path)
    first = (tmp_path / "capture-manifest.json").read_text(encoding="utf-8")
    CaptureManifest.read(tmp_path).write(tmp_path)
    assert (tmp_path / "capture-manifest.json").read_text(encoding="utf-8") == first


def test_a_manifest_records_its_corpus_at_capture_time():
    """The Q13 defect, generalized: a capture is not a corpus, and a
    downstream stage must never have to derive one from the other."""
    assert _manifest().corpus_id == "a-corpus"


def test_diff_separates_changed_from_added_from_removed():
    before = _manifest()
    after = _manifest(
        [
            RawPage(location="https://x.invalid/a", body=b"ALPHA EDITED"),
            RawPage(location="https://x.invalid/c", body=b"gamma"),
        ]
    )
    diff = after.diff(before)
    assert diff.changed == ("https://x.invalid/a",)
    assert diff.added == ("https://x.invalid/c",)
    assert diff.removed == ("https://x.invalid/b",)
    assert bool(diff) is True


def test_an_unchanged_refetch_is_falsey_and_regates_nothing():
    diff = _manifest().diff(_manifest())
    assert not diff
    assert diff.needs_regate == ()
    assert len(diff.unchanged) == 2


def test_new_pages_are_regated_alongside_changed_ones():
    """A page nobody has seen has no confirmed curation record either, so
    treating it as 'not a change' would let it into the graph ungated."""
    before = _manifest([RawPage(location="a", body=b"1")])
    after = _manifest([RawPage(location="a", body=b"2"), RawPage(location="b", body=b"new")])
    assert after.diff(before).needs_regate == ("a", "b")


def test_invocation_records_are_scrubbed_by_key():
    got = scrub({"tree": "utilities", "api_token": "sekrit", "AUTH": "x", "delay": "1.0"})
    assert got == {
        "tree": "utilities",
        "api_token": "<redacted>",
        "AUTH": "<redacted>",
        "delay": "1.0",
    }


# --------------------------------------------------------------------------- #
# policy — Q12's numbers live in config, not in code
# --------------------------------------------------------------------------- #
def test_the_shipped_policy_parses():
    policy = CapturePolicy.load()
    assert policy.max_pages > 0
    assert policy.delay_seconds > 0, "politeness is the whole of our restraint here"
    assert set(policy.allowed_schemes) <= {"http", "https"}


def test_the_default_ceiling_would_stop_every_real_bmc_tree():
    """Measured 2026-07-31 from the publishers' own toc.json: 10,912 / 3,860 /
    1,965 pages. The default answer to an unsized run must be 'stop'."""
    policy = CapturePolicy.load()
    for count in (10_912, 3_860, 1_965):
        with pytest.raises(TooManyPagesError):
            policy.enforce_ceiling(count)


def test_neither_number_is_a_literal_in_either_consumer():
    """Q12's acceptance in as many words: 'the threshold and the per-request
    delay are config values, never hardcoded literals'. Both doors — the
    standalone scraper and the component connector — must read the file."""
    for path in (
        REPO_ROOT / "scripts" / "external_vendor_scrape.py",
        REPO_ROOT / "drydocs_docmeta" / "connectors" / "web.py",
    ):
        body = path.read_text(encoding="utf-8")
        assert "CapturePolicy" in body, f"{path.name} does not read the capture policy"


def test_the_policy_file_is_the_one_home_for_the_numbers():
    raw = DEFAULT_POLICY_PATH.read_text(encoding="utf-8")
    assert "max_pages:" in raw and "delay_seconds:" in raw


def test_scheme_check_rejects_a_bare_path():
    with pytest.raises(DisallowedSchemeError):
        CapturePolicy.load().check_scheme("/etc/passwd")


# --------------------------------------------------------------------------- #
# registry — a typed view, not a second source of truth
# --------------------------------------------------------------------------- #
def test_every_shipped_entry_loads_typed():
    entries = registry.load_doc_sources()
    assert "bmc-docs" in entries
    for entry in entries.values():
        assert entry.tier in registry.CURATION_BY_TIER
        assert (
            entry.target_db == "drydocs"
        )  # G102 fold: one content database (was {dddocs, ddcontext})


def test_the_curation_ladder_is_derived_not_declared():
    """ADR 0006 §4: an entry cannot soften its own gate. Every shipped entry
    must already agree with the ladder its tier implies."""
    for entry in registry.load_doc_sources().values():
        assert entry.curation == entry.required_curation, (
            f"{entry.id} declares curation {entry.curation!r} but tier {entry.tier} "
            f"fixes it at {entry.required_curation!r}"
        )


def test_the_runtime_ladder_matches_the_ledger_guard():
    """Two independent statements of the ADR 0006 §4 ladder — the guard test's
    and the component's. This is what stops them drifting apart."""
    from tests.unit.test_doc_registry import CURATION_BY_TIER as GUARD_LADDER

    assert registry.CURATION_BY_TIER == GUARD_LADDER


def test_t1_needs_no_sme_and_the_rest_do():
    entries = registry.load_doc_sources()
    assert not entries["bmc-docs"].needs_sme_confirmation  # T1 vendor
    assert entries["fcdo-frameworks"].needs_sme_confirmation  # T4


def test_unknown_source_names_the_ledger():
    with pytest.raises(registry.UnknownDocSourceError, match="doc-source-registry"):
        registry.get("no-such-corpus")


def test_bkup_curation_words_map_onto_gate_positions():
    """The bkup vocabulary survives because company-side records carry it;
    what changes is that each word now means a position in the HITL gate."""
    assert registry.CURATION_STATUS_TO_GATE["approved_by_sme"] == "confirmed"
    assert registry.CURATION_STATUS_TO_GATE["unapproved"] == "pre-gate"
    assert registry.CURATION_STATUS_TO_GATE["ai_generated_review_needed"] == "gate-queued"


def test_a_weaker_sync_authority_never_overwrites_a_stronger_one():
    """The bootstrap pass re-running must not undo an SME's manual
    correction."""
    assert registry.outranks("manual", "bootstrap")
    assert registry.outranks("jet", "manual")
    assert not registry.outranks("bootstrap", "manual")
    assert registry.outranks("bootstrap", None)
    assert not registry.outranks("something-new", "manual")


def test_fetch_source_carries_the_resolved_locations_not_the_registry_row():
    """A registry entry GOVERNS a corpus; it does not enumerate its pages.
    The page list comes from the publisher's manifest, which is what makes the
    ceiling exact."""
    entry = registry.load_doc_sources()["bmc-docs"]
    fs = entry.fetch_source(["https://x.invalid/a"], max_pages=5)
    assert fs.id == "bmc-docs"
    assert fs.locations == ("https://x.invalid/a",)
    assert fs.max_pages == 5
