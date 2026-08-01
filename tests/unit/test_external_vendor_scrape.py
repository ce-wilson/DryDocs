"""Offline guards for the external-vendor documentation scraper (backlog Q12).

Every test here runs with NO network (the Track-1 portable rule): the table of
contents is a fixture and the fetcher is injected. The behaviour that matters
is the REFUSAL — a capture nobody sized must not start.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from scripts.external_vendor_scrape import (
    DEFAULT_MAX_PAGES,
    TREES,
    TooManyPages,
    build_parser,
    capture,
    enforce_ceiling,
    parse_toc,
    render_plan,
)

# A miniature Author-it toc.json: two books, one of which we filter to.
FIXTURE_TOC = json.dumps(
    [
        {
            "id": 1,
            "text": "Welcome",
            "url": "welcome.htm",
            "leaf": True,
        },
        {
            "id": 2,
            "text": "Utilities",
            "children": [
                {
                    "id": 3,
                    "text": "emdef utility for jobs",
                    "url": "emdef.htm",
                    "children": [
                        {
                            "id": 4,
                            "text": "defjob XML file rules",
                            "url": "16200.htm",
                            "leaf": True,
                        },
                        {"id": 5, "text": "exportdefjob", "url": "3930.htm", "leaf": True},
                        # duplicate url reachable from a second place
                        {
                            "id": 6,
                            "text": "defjob XML file rules",
                            "url": "16200.htm",
                            "leaf": True,
                        },
                    ],
                }
            ],
        },
        {
            "id": 7,
            "text": "Messages",
            "children": [{"id": 8, "text": "CTM100", "url": "ctm100.htm", "leaf": True}],
        },
    ]
)


def test_parse_toc_filters_to_one_book_and_dedupes():
    entries, per_book = parse_toc(FIXTURE_TOC, book="Utilities")
    urls = [e.url for e in entries]

    assert urls == ["emdef.htm", "16200.htm", "3930.htm"], "deduped, document order"
    assert "welcome.htm" not in urls and "ctm100.htm" not in urls, "other books excluded"
    # Every book is still SIZED, even the ones we are not capturing — the
    # operator needs the whole picture to notice a wrong-tree pick.
    assert per_book["Messages"] == 2
    assert per_book["Welcome"] == 1


def test_parse_toc_carries_breadcrumb_hierarchy():
    entries, _ = parse_toc(FIXTURE_TOC, book="Utilities")
    by_url = {e.url: e for e in entries}
    assert by_url["16200.htm"].breadcrumb == "Utilities > emdef utility for jobs"


def test_whole_tree_when_no_book_filter():
    entries, _ = parse_toc(FIXTURE_TOC, book=None)
    assert len(entries) == 5  # welcome + emdef + 2 unique children + ctm100


# --------------------------------------------------------------------------- #
# the guardrail itself
# --------------------------------------------------------------------------- #
def test_enforce_ceiling_refuses_above_limit():
    with pytest.raises(TooManyPages) as exc:
        enforce_ceiling(1017, 600)
    message = str(exc.value)
    assert "1017" in message, "the refusal names the actual count"
    assert "600" in message, "and the ceiling it exceeded"
    assert "Nothing was fetched" in message


def test_enforce_ceiling_allows_at_and_below_limit():
    enforce_ceiling(600, 600)  # boundary is inclusive
    enforce_ceiling(1, 600)


def test_default_ceiling_would_stop_every_real_bmc_tree():
    """Regression pin for the numbers that motivated Q12 (measured 2026-07-31).

    If someone raises the default, this fails and makes them think about it.
    """
    for real_tree_size in (1017, 1965, 3860, 10912):
        assert real_tree_size > DEFAULT_MAX_PAGES


def test_cli_defaults_to_refusing_rather_than_fetching():
    args = build_parser().parse_args(["bmc-controlm-9.0.20-utilities"])
    assert args.max_pages == DEFAULT_MAX_PAGES
    assert args.delay > 0, "a zero default delay would hammer the vendor"
    assert args.refresh is False


# --------------------------------------------------------------------------- #
# capture writes verbatim bytes + a manifest, and never leaves the data root
# --------------------------------------------------------------------------- #
def test_capture_writes_pages_and_manifest(tmp_path):
    tree = TREES["bmc-controlm-9.0.20-utilities"]
    entries, _ = parse_toc(FIXTURE_TOC, book="Utilities")
    payload = b"<html><body>hello</body></html>"
    calls: list[str] = []

    def fake_fetch(url: str) -> bytes:
        calls.append(url)
        return payload

    manifest = capture(tree, entries, delay=0, fetcher=fake_fetch, out_root=tmp_path)

    assert manifest["documents"] == 3
    assert manifest["failed"] == 0
    assert manifest["trust"] == "VERBATIM", "a scrape is the vendor's words, not our summary"
    assert manifest["classification"] == "External"
    assert all(u.startswith(tree.base_url) for u in calls)

    for entry in entries:
        written = tmp_path / "pages" / entry.url
        assert written.read_bytes() == payload, "bytes land verbatim, unconverted"

    on_disk = json.loads((tmp_path / "capture-manifest.json").read_text(encoding="utf-8"))
    page = on_disk["pages"][0]
    assert page["bytes"] == len(payload)
    assert page["sha256"] == hashlib.sha256(payload).hexdigest()
    assert page["breadcrumb"], "hierarchy is captured for the loader to use"


def test_capture_skips_existing_unless_refresh(tmp_path):
    tree = TREES["bmc-controlm-9.0.20-utilities"]
    entries, _ = parse_toc(FIXTURE_TOC, book="Utilities")
    (tmp_path / "pages").mkdir(parents=True)
    (tmp_path / "pages" / "16200.htm").write_bytes(b"already here")

    manifest = capture(tree, entries, delay=0, fetcher=lambda url: b"new", out_root=tmp_path)
    assert manifest["documents_skipped_existing"] == 1
    assert (tmp_path / "pages" / "16200.htm").read_bytes() == b"already here"


def test_skipped_pages_still_appear_in_the_manifest(tmp_path):
    """A resumed capture must produce a COMPLETE manifest.

    Regression: rows were only recorded for pages fetched by that run, so
    re-running a finished capture wrote a manifest describing almost nothing —
    and the manifest is what the loader consumes.
    """
    tree = TREES["bmc-controlm-9.0.20-utilities"]
    entries, _ = parse_toc(FIXTURE_TOC, book="Utilities")
    payload = b"<html>x</html>"

    first = capture(tree, entries, delay=0, fetcher=lambda url: payload, out_root=tmp_path)
    assert first["documents_fetched_this_run"] == 3

    def refuse(url: str) -> bytes:  # nothing should be re-fetched
        raise AssertionError(f"unexpected refetch of {url}")

    second = capture(tree, entries, delay=0, fetcher=refuse, out_root=tmp_path)
    assert second["documents_skipped_existing"] == 3
    assert second["toc_nodes_recorded"] == first["toc_nodes_recorded"] == 3
    assert [p["sha256"] for p in second["pages"]] == [p["sha256"] for p in first["pages"]]


def test_capture_survives_a_failing_page(tmp_path):
    tree = TREES["bmc-controlm-9.0.20-utilities"]
    entries, _ = parse_toc(FIXTURE_TOC, book="Utilities")

    def flaky(url: str) -> bytes:
        if url.endswith("3930.htm"):
            raise RuntimeError("503")
        return b"ok"

    manifest = capture(tree, entries, delay=0, fetcher=flaky, out_root=tmp_path)
    assert manifest["documents"] == 2
    assert manifest["failed"] == 1
    assert manifest["failures"][0]["url"] == "3930.htm"


# --------------------------------------------------------------------------- #
# fragment (#anchor) TOC nodes: real navigation, but not a second document
# --------------------------------------------------------------------------- #
FIXTURE_TOC_WITH_ANCHOR = json.dumps(
    [
        {
            "id": 1,
            "text": "Utilities",
            "children": [
                {"id": 2, "text": "ctl", "url": "89881.htm", "leaf": True},
                # a SECTION of the page above — a real TOC node, same document
                {"id": 3, "text": "ctl HA parameters", "url": "89881.htm#o90021", "leaf": True},
            ],
        }
    ]
)


def test_fragment_node_keeps_its_identity_but_is_not_a_second_document(tmp_path):
    """Regression from the live 1,017-page run.

    `89881.htm#o90021` was written as a literal filename and fetched a second
    time, producing two byte-identical files for one page.
    """
    tree = TREES["bmc-controlm-9.0.20-utilities"]
    entries, _ = parse_toc(FIXTURE_TOC_WITH_ANCHOR, book="Utilities")
    assert [e.page for e in entries] == ["89881.htm", "89881.htm"]
    assert [e.anchor for e in entries] == [None, "o90021"]

    calls: list[str] = []

    def counting_fetch(url: str) -> bytes:
        calls.append(url)
        return b"<html>ctl</html>"

    manifest = capture(tree, entries, delay=0, fetcher=counting_fetch, out_root=tmp_path)

    assert calls == [tree.base_url + "89881.htm"], "the page is fetched exactly once"
    assert manifest["documents"] == 1
    assert manifest["toc_nodes_recorded"] == 2, "both navigation nodes survive"

    on_disk = [p.name for p in (tmp_path / "pages").iterdir()]
    assert on_disk == ["89881.htm"], "no '#' in any filename"

    anchored = next(p for p in manifest["pages"] if p["anchor"])
    assert anchored["page"] == "89881.htm"
    assert anchored["title"] == "ctl HA parameters"


# --------------------------------------------------------------------------- #
# the wrong-tree trap the plan output exists to catch
# --------------------------------------------------------------------------- #
def test_plan_names_every_book_and_the_capture_target():
    tree = TREES["bmc-controlm-9.0.20-utilities"]
    entries, per_book = parse_toc(FIXTURE_TOC, book="Utilities")
    plan = render_plan(tree, entries, per_book, delay=1.0)

    assert "Messages" in plan and "Welcome" in plan, "non-captured books still listed"
    assert "<-- CAPTURING" in plan
    assert "PAGES TO FETCH : 3" in plan
    assert tree.base_url in plan, "the tree is named, not just a count"


def test_registered_trees_are_distributed_not_mainframe():
    """/supportu/INC/ is the INCONTROL mainframe family — never a default target."""
    for tree in TREES.values():
        assert "/supportu/INC/" not in tree.base_url
