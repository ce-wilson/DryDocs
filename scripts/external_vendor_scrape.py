"""external-vendor documentation scraper — VERBATIM capture, out-of-repo landing.

Captures a bounded subtree of a public vendor documentation site into the data
root (:func:`drydocs_core.data_root.vendor_docs_dir`). It writes the vendor's
pages as fetched plus a capture manifest; it converts nothing and loads
nothing. Conversion and graph loading are separate, reviewable steps — capture
stays verbatim so it can be re-converted without re-fetching.

WHY THIS IS NOT A CRAWLER
-------------------------
Every tree in ``TREES`` publishes a machine-readable table of contents, so the
exact page list — with titles and hierarchy — is known BEFORE any content
request. Nothing here follows links, guesses URLs, or discovers pages by
walking HTML. That is what makes the pre-flight refusal below cheap and exact
rather than an abort partway through a run.

THE SCALE GUARDRAIL (backlog Q12)
---------------------------------
Bulk-fetching a vendor's documentation has two real costs and one trap:

* it hammers a third party — ``robots.txt`` ALLOWS these paths, so there is no
  server-side backstop and politeness is entirely ours (hence ``--delay``);
* a verbatim capture is the vendor's copyrighted words, so it must never reach
  a repo that is private-but-sometimes-published (hence the data-root landing
  zone, and ``.gitignore`` as belt-and-braces);
* the operator can pick the WRONG TREE and not notice — BMC's ``/supportu/INC/``
  is the INCONTROL *mainframe* family (Control-D, Control-O, Control-M/Tape),
  whose "Control-M" subtree is Control-M for z/OS. A page count alone would not
  have caught that, so the pre-flight names the tree, its books and the
  subtree filter, not just a number.

So: ``--dry-run`` prints the plan and fetches nothing, and a run whose resolved
page count exceeds ``--max-pages`` REFUSES (exit 2) naming the count.

USAGE
-----
    python scripts/external_vendor_scrape.py --list
    python scripts/external_vendor_scrape.py bmc-controlm-9.0.20-utilities --dry-run
    python scripts/external_vendor_scrape.py bmc-controlm-9.0.20-utilities --max-pages 1200
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:  # allow `python scripts/...` without PYTHONPATH
    sys.path.insert(0, str(REPO_ROOT))

from drydocs_core.data_root import vendor_docs_dir  # noqa: E402

USER_AGENT = "DryDocs-docs-capture/1.0 (+internal knowledge-graph research; contact repo owner)"

#: Refuse a capture larger than this unless --max-pages raises it explicitly.
#: Deliberately well below every real tree so the default answer is "stop".
DEFAULT_MAX_PAGES = 600
DEFAULT_DELAY_SECONDS = 1.0


@dataclass(frozen=True)
class VendorTree:
    """One capturable vendor documentation subtree."""

    id: str
    vendor: str
    product: str
    version: str
    base_url: str
    #: The config/doc-source-registry.yaml entry that governs this capture.
    #: DISTINCT from `id`, which names ONE fetch of ONE tree at ONE version —
    #: a corpus outlives its captures. Declared here rather than derived
    #: because the graph is keyed by it and `drydocs docs-verify` searches by
    #: it (Q7). None = not registered yet; conversion refuses rather than
    #: guessing (docmeta invariant 1).
    corpus_id: str | None = None
    toc_path: str = "toc.json"
    #: Only capture pages under this top-level book. None = the whole tree.
    book: str | None = None
    classification: str = "External"
    note: str = ""

    @property
    def toc_url(self) -> str:
        return self.base_url + self.toc_path


TREES: dict[str, VendorTree] = {
    t.id: t
    for t in [
        VendorTree(
            id="bmc-controlm-9.0.20-utilities",
            corpus_id="bmc-controlm-utilities",
            vendor="BMC",
            product="Control-M",
            version="9.0.20",
            base_url="https://documents.bmc.com/supportu/9.0.20/help/Main_help/en-US/",
            book="Utilities",
            note=(
                "The distributed (non-mainframe) utilities reference: emdef family "
                "(defjob/exportdefjob/updatedef/copydefjob/deldefjob/duplicatedefjob), "
                "the XML file rules pages, and ctm* server utilities. 9.0.20 rather "
                "than 9.0.21 because BMC trimmed the 9.0.21 help publication and it "
                "carries NO Utilities book; the on-prem estate is 9.0.21.300, so treat "
                "version-specific details as needing confirmation against 9.0.21."
            ),
        ),
        VendorTree(
            id="bmc-controlm-9.0.21-parameters",
            vendor="BMC",
            product="Control-M",
            version="9.0.21",
            base_url="https://documents.bmc.com/supportu/9.0.21/help/Main_help/en-US/",
            book="Parameters",
            note=(
                "Version-correct parameter reference for the 9.0.21.300 estate. "
                "Overlaps the hand-converted external/orchestration/bmc-controlm/ "
                "corpus, so it doubles as a drift check of our GROUNDED paraphrase "
                "against vendor VERBATIM."
            ),
        ),
    ]
}


# --------------------------------------------------------------------------- #
# fetching
# --------------------------------------------------------------------------- #
def fetch(url: str, *, timeout: int = 30, retries: int = 3) -> bytes:
    """GET with a descriptive UA and bounded backoff."""
    last: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError) as exc:  # pragma: no cover - network
            last = exc
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url}: {last}")


# --------------------------------------------------------------------------- #
# table of contents -> the exact page list (no crawling)
# --------------------------------------------------------------------------- #
@dataclass
class TocEntry:
    """One node of the vendor's table of contents.

    A TOC node is not the same thing as a page. Some nodes address a SECTION of
    a page via a fragment (``89881.htm#o90021`` — "ctl High Availability Server
    parameters" inside the broader ``ctl`` topic). Those are real navigation
    nodes with their own titles, so they are kept, but they must not cause the
    underlying page to be fetched or stored twice: ``page`` is what gets
    downloaded, ``anchor`` is where inside it this node points.
    """

    url: str
    title: str
    path: list[str] = field(default_factory=list)

    @property
    def page(self) -> str:
        """The fetchable document — the url with any fragment removed."""
        return self.url.split("#", 1)[0]

    @property
    def anchor(self) -> str | None:
        """The within-page anchor, if this node addresses a section."""
        _, _, frag = self.url.partition("#")
        return frag or None

    @property
    def breadcrumb(self) -> str:
        return " > ".join(self.path)


def parse_toc(
    raw: bytes | str, *, book: str | None = None
) -> tuple[list[TocEntry], dict[str, int]]:
    """Flatten an Author-it ``toc.json`` into (entries, pages-per-book).

    ``book`` restricts the result to one top-level book. Entries are
    de-duplicated on the FULL url (page + fragment), first occurrence winning,
    so a topic reachable from two places appears once while a section node
    keeps its own identity.
    """
    text = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
    tree = json.loads(text)

    per_book: dict[str, int] = {}
    entries: list[TocEntry] = []
    seen: set[str] = set()

    def walk(node: dict, path: list[str]) -> int:
        count = 1
        url = node.get("url")
        title = node.get("text") or "(untitled)"
        if url and url not in seen:
            seen.add(url)
            entries.append(TocEntry(url=url, title=title, path=path))
        for child in node.get("children") or []:
            count += walk(child, [*path, title])
        return count

    for top in tree:
        name = top.get("text") or "(untitled)"
        if book is not None and name != book:
            per_book[name] = _size(top)
            continue
        per_book[name] = walk(top, [])

    return entries, per_book


def _size(node: dict) -> int:
    return 1 + sum(_size(c) for c in (node.get("children") or []))


# --------------------------------------------------------------------------- #
# pre-flight plan + the refusal
# --------------------------------------------------------------------------- #
#: Order-of-magnitude only, and it varies a lot by book — measured 2026-07-31:
#: sampled Parameters pages ~19 KB each, but the full Utilities capture came in
#: at ~5.9 KB/page (6.0 MB / 1016 documents). Sizing off three sampled pages
#: over-estimated that run by 3x, so the pre-flight says "estimated" and this
#: number exists to catch order-of-magnitude mistakes, not to be accurate.
BYTES_PER_PAGE_ESTIMATE = 12_000


def render_plan(
    tree: VendorTree, entries: list[TocEntry], per_book: dict[str, int], delay: float
) -> str:
    est_bytes = len(entries) * BYTES_PER_PAGE_ESTIMATE
    est_seconds = len(entries) * max(delay, 0.0)
    lines = [
        "",
        "CAPTURE PLAN",
        "-" * 64,
        f"  tree id        : {tree.id}",
        f"  corpus entry   : {tree.corpus_id or '(UNREGISTERED — convert will refuse)'}",
        f"  vendor/product : {tree.vendor} {tree.product} {tree.version}",
        f"  base url       : {tree.base_url}",
        f"  subtree filter : {tree.book or '(entire tree)'}",
        f"  classification : {tree.classification}",
        "",
        "  top-level books in this tree:",
    ]
    for name, count in per_book.items():
        marker = "  <-- CAPTURING" if (tree.book is None or name == tree.book) else ""
        lines.append(f"      {name[:52]:<52} {count:>6} pages{marker}")
    lines += [
        "",
        f"  PAGES TO FETCH : {len(entries)}",
        f"  estimated size : ~{est_bytes / 1e6:.1f} MB raw",
        f"  estimated time : ~{est_seconds / 60:.1f} min at {delay:.2f}s/request",
        f"  landing zone   : {vendor_docs_dir(tree.id)}",
        "-" * 64,
    ]
    if tree.note:
        lines += ["  note: " + tree.note, "-" * 64]
    return "\n".join(lines)


class TooManyPages(RuntimeError):
    """Raised when the resolved page count exceeds the operator's ceiling."""


def enforce_ceiling(page_count: int, max_pages: int) -> None:
    """The Q12 guardrail. Refuse rather than start a run nobody sized."""
    if page_count > max_pages:
        raise TooManyPages(
            f"REFUSING: this capture resolves to {page_count} pages, above the "
            f"--max-pages ceiling of {max_pages}. Nothing was fetched. Re-run with "
            f"--max-pages {page_count} if that is genuinely intended, or narrow the "
            f"subtree. Check the book list above: picking the wrong tree is the "
            f"common cause of an unexpectedly large count."
        )


# --------------------------------------------------------------------------- #
# capture
# --------------------------------------------------------------------------- #
def capture(
    tree: VendorTree,
    entries: list[TocEntry],
    *,
    delay: float,
    refresh: bool = False,
    fetcher=fetch,
    out_root: Path | None = None,
) -> dict:
    root = out_root or vendor_docs_dir(tree.id, create=True)
    pages_dir = root / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    records, failures = [], []
    fetched, skipped = 0, 0
    #: page -> (bytes, sha256) for pages this run has already handled, so a TOC
    #: node addressing a SECTION of an already-captured page costs no request.
    seen_pages: dict[str, tuple[int, str]] = {}

    for i, entry in enumerate(entries, start=1):
        dest = pages_dir / entry.page

        if entry.page not in seen_pages:
            if dest.exists() and not refresh:
                body = dest.read_bytes()
                skipped += 1
            else:
                try:
                    body = fetcher(tree.base_url + entry.page)
                except Exception as exc:  # keep going; a partial capture is still useful
                    failures.append({"url": entry.url, "page": entry.page, "error": str(exc)})
                    print(f"  [{i}/{len(entries)}] FAILED {entry.page}: {exc}", file=sys.stderr)
                    continue
                dest.write_bytes(body)
                fetched += 1
                if delay:
                    time.sleep(delay)
            seen_pages[entry.page] = (len(body), hashlib.sha256(body).hexdigest())

        size, digest = seen_pages[entry.page]
        # One row per TOC NODE — the hierarchy is the point — but `page`/`anchor`
        # make it explicit when several nodes share one document.
        records.append(
            {
                "url": entry.url,
                "page": entry.page,
                "anchor": entry.anchor,
                "source_url": tree.base_url + entry.url,
                "title": entry.title,
                "breadcrumb": entry.breadcrumb,
                "toc_path": entry.path,
                "bytes": size,
                "sha256": digest,
            }
        )
        if i % 50 == 0:
            print(f"  [{i}/{len(entries)}] captured ...")

    manifest = {
        "capture_id": tree.id,
        "corpus_id": tree.corpus_id,
        "vendor": tree.vendor,
        "product": tree.product,
        "version": tree.version,
        "base_url": tree.base_url,
        "book": tree.book,
        "classification": tree.classification,
        "captured_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "trust": "VERBATIM",
        "note": tree.note,
        # toc_nodes >= documents whenever a node addresses a section of a page.
        "toc_nodes_requested": len(entries),
        "toc_nodes_recorded": len(records),
        "documents": len(seen_pages),
        "documents_fetched_this_run": fetched,
        "documents_skipped_existing": skipped,
        "failed": len(failures),
        "failures": failures,
        "pages": records,
    }
    (root / "capture-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


# --------------------------------------------------------------------------- #
# cli
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Capture a bounded subtree of public vendor documentation (verbatim, out-of-repo).",
    )
    p.add_argument("tree", nargs="?", help="capture id (see --list)")
    p.add_argument("--list", action="store_true", help="list known vendor trees and exit")
    p.add_argument("--dry-run", action="store_true", help="print the plan, fetch nothing")
    p.add_argument(
        "--max-pages",
        type=int,
        default=DEFAULT_MAX_PAGES,
        help=f"refuse a capture larger than this (default {DEFAULT_MAX_PAGES})",
    )
    p.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY_SECONDS,
        help=f"seconds between requests (default {DEFAULT_DELAY_SECONDS})",
    )
    p.add_argument("--refresh", action="store_true", help="re-fetch pages already on disk")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.list or not args.tree:
        print("Known vendor documentation trees:\n")
        for t in TREES.values():
            print(f"  {t.id}")
            print(f"      {t.vendor} {t.product} {t.version} — book: {t.book or '(all)'}")
            print(f"      {t.base_url}\n")
        return 0

    tree = TREES.get(args.tree)
    if tree is None:
        print(f"unknown tree {args.tree!r}; use --list", file=sys.stderr)
        return 1

    print(f"Resolving table of contents: {tree.toc_url}")
    entries, per_book = parse_toc(fetch(tree.toc_url), book=tree.book)
    print(render_plan(tree, entries, per_book, args.delay))

    try:
        enforce_ceiling(len(entries), args.max_pages)
    except TooManyPages as exc:
        print(f"\n{exc}\n", file=sys.stderr)
        return 2

    if args.dry_run:
        print("\n--dry-run: nothing fetched.\n")
        return 0

    print(f"\nCapturing {len(entries)} pages at {args.delay}s/request ...\n")
    manifest = capture(tree, entries, delay=args.delay, refresh=args.refresh)
    print(
        f"\nDONE  toc_nodes={manifest['toc_nodes_recorded']} "
        f"documents={manifest['documents']} "
        f"(fetched={manifest['documents_fetched_this_run']} "
        f"skipped={manifest['documents_skipped_existing']}) "
        f"failed={manifest['failed']}"
    )
    print(f"      {vendor_docs_dir(tree.id)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
