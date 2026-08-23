"""Guards for the standalone vendor-docs pipeline (backlog Q13).

Offline throughout: the Author-it HTML is a fixture, the capture manifest is
written to tmp_path, and nothing touches Neo4j.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from drydocs.loaders.vendor_docs import (
    ROLE_FALLBACK,
    CorpusNotRegisteredError,
    VendorDocsAdapter,
    VendorDocsLoader,
    convert_capture,
    derive_page_role,
    resolve_corpus_id,
    split_chunks,
)
from drydocs_core.docs.vendor_html import html_to_markdown
from drydocs_core.source_registry import SourceRegistry

CYPHER = (
    Path(__file__).resolve().parents[2] / "drydocs" / "loaders" / "cypher" / "vendor_docs.cypher"
)

# Trimmed from a real captured topic: the isTOCLoaded shim, the Previous/Next
# icon strip, the topic heading rendered at h4 (depth, not importance), and the
# foot "Related Topics" block.
FIXTURE_HTML = """﻿<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html><head><meta charset="UTF-8" /><title> defjob XML file rules </title>
<script type="text/javascript">function isTOCLoaded() { location.href = "x"; return false; }</script>
</head>
<body onload="if (isTOCLoaded()) {expand('1');highlight('2')}">
<table class="relatedtopics aboveheading"><tr><td>
<p class="bodytext"><a href="7345.htm"><img alt="Previous Topic"></a></p></td>
<td><p class="bodytext"><a href="89957.htm"><img alt="Next Topic"></a></p></td></tr></table>
<h4 id="t16200" class="heading4">defjob XML file rules</h4>
<p class="bodytext">The defjob utility reads an XML file. See
<a class="jumptemplate" href="17196.htm">defjob XML file example</a>.</p>
<ul class="listbullet"><li class="listbullet">Tags are case sensitive.</li>
<li class="listbullet">Values are quoted.</li></ul>
<h5 class="heading5">Advanced usage</h5>
<p class="bodytext">Only for batch definitions.</p>
<table class="relatedtopics belowtopictext"><tr><td>
<h3 class="relatedheading">Related Topics</h3>
<p class="relateditem"><a href="16201.htm">defjob XML file parameters</a></p>
<p class="relateditem"><a href="3930.htm">exportdefjob</a></p></td></tr></table>
</body></html>"""


# --------------------------------------------------------------------------- #
# conversion
# --------------------------------------------------------------------------- #
def test_navigation_chrome_never_reaches_the_body():
    doc = html_to_markdown(FIXTURE_HTML)
    for chrome in (
        "Previous Topic",
        "Next Topic",
        "isTOCLoaded",
        "Related Topics",
        "location.href",
    ):
        assert chrome not in doc.markdown, f"chrome leaked into body: {chrome}"


def test_heading_levels_are_normalized_not_trusted():
    """Author-it renders the title at a level reflecting TOC DEPTH.

    In the real capture the topic title appears as h1 once, h2 15x, h3 120x,
    h4 383x, h5 379x and h6 97x — so level cannot be read as importance. The
    first content heading becomes '#' and later ones '##' regardless of source
    level, which is also what makes split-on-H2 behave uniformly.
    """
    doc = html_to_markdown(FIXTURE_HTML)  # title is h4, section is h5
    assert doc.markdown.startswith("# defjob XML file rules")
    assert "\n## Advanced usage" in doc.markdown
    assert doc.headings == ["defjob XML file rules", "Advanced usage"]


def test_related_links_are_captured_as_data_not_body_text():
    doc = html_to_markdown(FIXTURE_HTML)
    assert [(r.text, r.href) for r in doc.related] == [
        ("defjob XML file parameters", "16201.htm"),
        ("exportdefjob", "3930.htm"),
    ]
    # ...and the foot block's link text must not appear as prose
    assert "defjob XML file parameters" not in doc.markdown


def test_inline_links_survive_with_their_href():
    """The href is the raw material for a future SEE_ALSO (Q14's gate)."""
    doc = html_to_markdown(FIXTURE_HTML)
    assert "[defjob XML file example](17196.htm)" in doc.markdown


def test_list_items_and_abstract():
    doc = html_to_markdown(FIXTURE_HTML)
    assert "- Tags are case sensitive." in doc.markdown
    assert doc.abstract.startswith("The defjob utility reads an XML file")
    assert not doc.abstract.startswith("#")


def test_page_with_no_heading_still_gets_a_title():
    doc = html_to_markdown(
        "<html><head><title>Bare</title></head><body>"
        "<p class='bodytext'>Body only.</p></body></html>"
    )
    assert doc.markdown.startswith("# Bare")
    assert doc.abstract == "Body only."


# --------------------------------------------------------------------------- #
# page_role — explicit rules, and a REPORTED fallback rather than a silent one
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "title,expected",
    [
        ("defjob XML file examples", "examples"),
        ("Copy jobs XML file example", "examples"),
        ("defjob XML file parameters", "parameters"),
        ("defjob XML file rules", "rules"),
        ("Introduction to Utilities", "overview"),
        ("Utility reference table", ROLE_FALLBACK),
        ("ctmorder", ROLE_FALLBACK),
    ],
)
def test_derive_page_role(title, expected):
    assert derive_page_role(title) == expected


def test_examples_wins_over_parameters_when_a_title_has_both():
    """Ordering is load-bearing: 'XML file parameters for folders examples'
    is an examples page, and rule order is what decides that."""
    assert derive_page_role("updatedef XML file parameters examples") == "examples"


# --------------------------------------------------------------------------- #
# chunking
# --------------------------------------------------------------------------- #
def test_single_topic_page_is_one_chunk():
    seq = split_chunks("# Title\n\nbody text\n")
    assert len(seq) == 1
    assert seq[0][0] == 0 and seq[0][1] == "(topic)"


def test_section_heading_splits_into_a_second_chunk():
    seq = split_chunks("# Title\n\nintro\n\n## Section\n\nmore\n")
    assert [(s[0], s[1], s[2]) for s in seq] == [(0, "(topic)", 0), (1, "Section", 2)]
    assert "intro" in seq[0][3] and "more" in seq[1][3]


# --------------------------------------------------------------------------- #
# convert stage + adapter, end to end on a fake capture
# --------------------------------------------------------------------------- #
@pytest.fixture()
def fake_capture(tmp_path: Path) -> Path:
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "16200.htm").write_text(FIXTURE_HTML, encoding="utf-8")
    manifest = {
        "corpus_id": "bmc-docs-controlm-utilities",
        "vendor": "BMC",
        "product": "Control-M",
        "version": "9.0.20",
        "book": "Utilities",
        "captured_at": "2026-07-31T14:43:32Z",
        "base_url": "https://example.invalid/",
        "pages": [
            {
                "url": "16200.htm",
                "page": "16200.htm",
                "anchor": None,
                "source_url": "https://example.invalid/16200.htm",
                "title": "defjob XML file rules",
                "breadcrumb": "Utilities > emdef utility for jobs",
                "toc_path": ["Utilities", "emdef utility for jobs"],
                "bytes": 10,
                "sha256": "abc123",
            },
            {  # a fragment node: same document, a section within it
                "url": "16200.htm#adv",
                "page": "16200.htm",
                "anchor": "adv",
                "source_url": "https://example.invalid/16200.htm#adv",
                "title": "Advanced usage",
                "breadcrumb": "Utilities > emdef utility for jobs > Advanced usage",
                "toc_path": ["Utilities", "emdef utility for jobs", "defjob XML file rules"],
                "bytes": 10,
                "sha256": "abc123",
            },
        ],
    }
    (tmp_path / "capture-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return tmp_path


def test_convert_writes_markdown_and_manifest(fake_capture: Path):
    summary = convert_capture("fake", root=fake_capture)

    assert summary.documents == 1, "the fragment node must not create a second document"
    assert summary.toc_nodes == 2
    assert summary.roles == {"rules": 1}
    assert summary.related_links == 2

    manifest = json.loads((fake_capture / "convert-manifest.json").read_text(encoding="utf-8"))
    doc = manifest["documents"][0]
    assert doc["doc_id"] == "fake/16200"
    assert doc["page_role"] == "rules"
    assert doc["source_url"] == "https://example.invalid/16200.htm", "fragment stripped"
    assert doc["sections"] == [
        {
            "anchor": "adv",
            "title": "Advanced usage",
            "breadcrumb": "Utilities > emdef utility for jobs > Advanced usage",
        }
    ]
    assert (fake_capture / "markdown" / "16200.md").exists()


def test_convert_is_idempotent(fake_capture: Path):
    first = convert_capture("fake", root=fake_capture)
    before = (fake_capture / "convert-manifest.json").read_text(encoding="utf-8")
    second = convert_capture("fake", root=fake_capture)
    assert (fake_capture / "convert-manifest.json").read_text(encoding="utf-8") == before
    assert (first.documents, first.roles) == (second.documents, second.roles)


def test_adapter_rows_validate_and_chain_chunks(fake_capture: Path):
    convert_capture("fake", root=fake_capture)
    with VendorDocsAdapter("fake", root=fake_capture) as adapter:
        rows = list(adapter.rows())

    assert len(rows) == 2, "one topic chunk + one section chunk"
    models = [VendorDocsLoader.row_model.model_validate(r) for r in rows]

    assert models[0].seq == 0 and models[0].prev_chunk_id is None
    assert models[1].prev_chunk_id == models[0].chunk_id, "NEXT_CHUNK order comes from Python"
    for m in models:
        assert m.trust == "VERBATIM"
        assert m.doc_version == "9.0.20"
        assert m.version_verified is False, "only a human may flip this (Q16)"
        assert m.toc_path[0] == "Utilities"


# --------------------------------------------------------------------------- #
# corpus identity — a capture is not a corpus (Q13 close)
# --------------------------------------------------------------------------- #
REGISTRY_PATH = Path(__file__).resolve().parents[2] / "config" / "doc-source-registry.yaml"
REAL_CAPTURE = "bmc-controlm-9.0.20-utilities"


def test_resolve_corpus_id_finds_the_registry_entry_that_names_the_capture():
    assert resolve_corpus_id(REAL_CAPTURE) == "bmc-docs-controlm-utilities"


def test_unregistered_capture_refuses_rather_than_inventing_an_id():
    """docmeta invariant 1: no doc content moves toward a graph while its
    registry entry is missing. Deriving a corpus id from the capture id would
    have produced a plausible, wrong, unqueryable one."""
    with pytest.raises(CorpusNotRegisteredError, match="belongs to no corpus"):
        resolve_corpus_id("some-vendor-tree-nobody-registered")


def test_graph_corpus_id_is_what_docs_verify_searches_for():
    """THE REGRESSION THIS CLOSES. The loader wrote corpus_id=<capture id>
    while the registry's graph_locator says match: corpus_id / value:
    <registry id>, so `drydocs docs-verify` would report a fully loaded
    corpus as MISSING — a false negative in the one check Q7 built to stop
    false claims. Nothing had ever run both halves together, which is exactly
    why it survived. The two ids must agree, in that direction."""
    import yaml

    registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    entry = next(s for s in registry["sources"] if s["id"] == "bmc-docs-controlm-utilities")
    locator = entry["graph_locator"]
    assert locator["match"] == "corpus_id", "this guard assumes the corpus_id locator"
    assert resolve_corpus_id(REAL_CAPTURE) == locator["value"]


def test_capture_declares_its_corpus_so_conversion_needs_no_lookup():
    """The scraper writes corpus_id into capture-manifest.json — the manifest
    is the contract between stages, so the corpus travels with the capture."""
    from scripts.external_vendor_scrape import TREES

    assert TREES[REAL_CAPTURE].corpus_id == "bmc-docs-controlm-utilities"


def test_explicit_corpus_id_beats_the_manifest(fake_capture: Path):
    summary = convert_capture("fake", corpus_id="an-override", root=fake_capture)
    assert summary.corpus_id == "an-override"


def test_doc_id_is_capture_scoped_so_two_versions_never_collide(fake_capture: Path):
    """Author-it reuses topic ids ACROSS publications. On a bare-stem MERGE
    the 9.0.21 capture of topic 16200 would overwrite the 9.0.20 one and take
    doc_version with it — losing the single distinction this corpus exists to
    carry ("the 9.0.20 docs say X, unverified for your 9.0.21.300 estate")."""
    convert_capture("cap-9.0.20", root=fake_capture, corpus_id="c")
    with VendorDocsAdapter("cap-9.0.20", root=fake_capture) as adapter:
        first = [r["doc_id"] for r in adapter.rows()]

    convert_capture("cap-9.0.21", root=fake_capture, corpus_id="c")
    with VendorDocsAdapter("cap-9.0.21", root=fake_capture) as adapter:
        second = [r["doc_id"] for r in adapter.rows()]

    assert first == ["cap-9.0.20/16200"] * 2
    assert second == ["cap-9.0.21/16200"] * 2
    assert not set(first) & set(second), "same topic, two captures, two identities"


def test_rows_carry_both_ids(fake_capture: Path):
    convert_capture("fake", root=fake_capture)
    with VendorDocsAdapter("fake", root=fake_capture) as adapter:
        row = next(iter(adapter.rows()))
    assert row["corpus_id"] == "bmc-docs-controlm-utilities"  # what docs-verify searches
    assert row["capture_id"] == "fake"  # which fetch produced it


def test_registry_lookup_is_used_when_the_manifest_predates_the_field(fake_capture: Path):
    """Captures taken before the field existed carry no corpus_id — the
    1016-page 2026-07-31 capture among them. Those resolve through the
    registry instead of being re-fetched."""
    manifest_path = fake_capture / "capture-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest["corpus_id"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    summary = convert_capture(REAL_CAPTURE, root=fake_capture)
    assert summary.corpus_id == "bmc-docs-controlm-utilities"


def test_resolution_order_never_derives_from_the_capture_id(fake_capture: Path):
    """A capture that is neither declared nor registered fails loudly. The
    tempting fallback — strip the version out of the capture id — would mint
    an id no registry entry and no docs-verify run has ever heard of."""
    manifest_path = fake_capture / "capture-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest["corpus_id"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(CorpusNotRegisteredError):
        convert_capture("bmc-controlm-9.9.99-invented", root=fake_capture)


def test_registry_is_injectable_so_the_guard_is_not_shipped_config_only(tmp_path: Path):
    pipeline = tmp_path / "source-registry.yaml"
    pipeline.write_text("schema: drydocs.source-registry.v1\nsources: []\n", encoding="utf-8")
    docs = tmp_path / "doc-source-registry.yaml"
    docs.write_text(
        "schema: drydocs.doc-source-registry.v1\nsources:\n"
        "  - id: my-corpus\n    manifest: some/path/my-capture/capture-manifest.json\n",
        encoding="utf-8",
    )
    reg = SourceRegistry.from_yaml(pipeline, doc_registry_path=docs)
    assert resolve_corpus_id("my-capture", registry=reg) == "my-corpus"


def test_only_the_doc_ledger_may_claim_a_capture(tmp_path: Path):
    """The doc ledger is each corpus's ONE home (N9). A pipeline-registry row
    that happens to name the same path does not own the corpus, so it must
    not be able to answer for it."""
    pipeline = tmp_path / "source-registry.yaml"
    pipeline.write_text(
        "schema: drydocs.source-registry.v1\nsources:\n"
        "  - id: impostor\n    manifest: some/path/my-capture/capture-manifest.json\n",
        encoding="utf-8",
    )
    docs = tmp_path / "doc-source-registry.yaml"
    docs.write_text("schema: drydocs.doc-source-registry.v1\nsources: []\n", encoding="utf-8")
    reg = SourceRegistry.from_yaml(pipeline, doc_registry_path=docs)
    with pytest.raises(CorpusNotRegisteredError):
        resolve_corpus_id("my-capture", registry=reg)


# --------------------------------------------------------------------------- #
# the version caveat rides every node, and the loader can actually report change
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("node", ["doc", "chunk", "leaf", "child", "parent"])
def test_every_node_carries_the_version_caveat(node: str):
    """Acceptance: "Every node carries doc_version and version_verified=false."
    A chunk that surfaces alone in a retrieval result must still say which
    documentation version it came from and that nobody confirmed it against
    the running estate."""
    cypher = CYPHER.read_text(encoding="utf-8")
    for prop in ("doc_version", "version_verified"):
        assert f"{node}.{prop}" in cypher, f"{node} does not carry {prop}"


def test_provenance_tail_exists_and_is_delta_only():
    """BaseLoader derives rows_changed by counting WAS_GENERATED_BY edges a
    run attached. A template that writes none reports rows_changed=0 on the
    FIRST load exactly as on a no-op re-run, so the acceptance's idempotence
    evidence would be unfalsifiable."""
    cypher = CYPHER.read_text(encoding="utf-8")
    assert "WAS_GENERATED_BY" in cypher
    assert "chunk.row_checksum IS NULL OR chunk.row_checksum <> row.row_checksum" in cypher
    assert "SET chunk.row_checksum = row.row_checksum" in cypher


def test_provenance_tail_sits_above_the_subsection_unwind():
    """Placement is load-bearing: the SUBSECTION_OF block's UNWIND of an empty
    list drops every row at TOC depth <= 1 from the remainder of the
    statement, so a tail placed after it would silently skip those rows —
    the tail-ordering trap bmc_docs.cypher documents."""
    body = CYPHER.read_text(encoding="utf-8")
    assert body.index("WAS_GENERATED_BY") < body.index(
        "UNWIND CASE WHEN size(path) > 1"
    ), "the provenance tail must precede the row-dropping UNWIND"


class _RecordingClient:
    """Captures flushed batches; enough to run BaseLoader offline."""

    def __init__(self) -> None:
        self.batches: list[list[dict]] = []

    def run(self, cypher: str, params: dict | None = None, **kwargs):
        bind = {**(params or {}), **kwargs}
        if "batch" in bind:
            self.batches.append(bind["batch"])
        return []

    def run_script(self, script: str, params: dict | None = None) -> None:
        if params and "batch" in params:
            self.batches.append(params["batch"])


def test_two_loads_of_one_capture_send_identical_checksums(fake_capture: Path):
    """The offline half of "a second full run reports zero net change": the
    delta-only tail fires when the stored checksum differs from the incoming
    one, so equal checksums across two independent loads is what makes the
    re-run a no-op. (The graph-side count needs a live database and the
    capture payload, neither of which exists on this machine — see the Q13
    close note.)"""
    convert_capture("fake", root=fake_capture)

    def checksums() -> list[str]:
        client = _RecordingClient()
        with VendorDocsAdapter("fake", root=fake_capture) as adapter:
            VendorDocsLoader(client, adapter).load()
        return [r["row_checksum"] for b in client.batches for r in b]

    first, second = checksums(), checksums()
    assert first and all(first), "every row must carry a checksum for the tail to compare"
    assert first == second, "re-running the same capture must produce the same checksums"


# --------------------------------------------------------------------------- #
# the taxonomy-only boundary
# --------------------------------------------------------------------------- #
def test_loader_wiring():
    assert VendorDocsLoader.cypher_path == CYPHER and CYPHER.exists()
    assert VendorDocsLoader.source_id == "bmc-docs-controlm-utilities"
    assert VendorDocsLoader.source_label == "vendor-docs"


def test_cypher_writes_the_backbone():
    cypher = CYPHER.read_text(encoding="utf-8")
    for token in (
        ":Document",
        ":Chunk",
        ":DocSection",
        "PART_OF",
        "FIRST_CHUNK",
        "NEXT_CHUNK",
        "IN_SECTION",
        "SUBSECTION_OF",
    ):
        assert token in cypher, f"missing {token}"


def test_cypher_writes_no_meaning_edges():
    """Q13 is taxonomy only — the loader writes NOT ONE meaning edge. Those
    belong to Q14's gate (and G32 for the estate join, since a relationship
    cannot span Neo4j databases)."""
    body = "\n".join(
        line
        for line in CYPHER.read_text(encoding="utf-8").splitlines()
        if not line.strip().startswith("//")
    )
    for forbidden in (":ControlMUtility", "DESCRIBES", "SEE_ALSO", "DOCUMENTS", ":SoftwareProduct"):
        assert (
            forbidden not in body
        ), f"{forbidden} is gate-bound and must not appear in the executable template"
