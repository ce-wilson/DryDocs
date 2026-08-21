"""Vendor-docs pipeline stages 2 and 3 — convert, then load (backlog Q13).

STANDALONE by ruling (2026-07-31), not a widening of :mod:`bmc_docs`. That
loader consumes hand-written markdown and INFERS a provenance tier from heading
text — a heuristic that exists only because its corpus is our lossy paraphrase.
This corpus is ``VERBATIM`` throughout, so there is no tier to infer, and its
real structure (TOC hierarchy, page_role, section anchors) has nowhere to live
in that model. Two loaders with honest contracts beat one with a mode flag.

REPEATABLE: the capture manifest is the contract between three independently
re-runnable stages.

    capture ──capture-manifest.json──▶ convert ──convert-manifest.json──▶ load
    (scripts/external_vendor_scrape.py)   (here)                          (here)

Re-running any stage is idempotent: convert rewrites markdown from the same
bytes, and the load MERGEs on ``doc_id``. The load's delta-only provenance
tail is what makes "idempotent" a REPORTED fact rather than a claim — see the
tail note in ``cypher/vendor_docs.cypher``.

A CAPTURE IS NOT A CORPUS. ``bmc-controlm-9.0.20-utilities`` is one fetch of
one tree at one version; ``bmc-docs-controlm-utilities`` is the registry entry that
governs it and the id ``docs-verify`` searches for. Both ride every row, and
the capture id scopes ``doc_id`` so two versions of a topic cannot merge onto
one node — see :func:`resolve_corpus_id`.

TAXONOMY ONLY. This writes :Document, :Chunk and the publisher's own TOC
hierarchy — all transcription of structure the vendor already publishes. It
writes NO meaning edges: no :ControlMUtility, no DOCUMENTS, no SEE_ALSO. The
vendor's related-topic links ARE carried through conversion (as data, on disk)
so Q14's gate can argue from evidence, but nothing here turns them into edges.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from pydantic import BaseModel

from drydocs_core.data_root import vendor_docs_dir
from drydocs_core.docs.vendor_html import html_to_markdown
from drydocs_core.models.docs import VendorDocChunkRow
from drydocs_core.source_registry import SourceRegistry

from .base import BaseLoader, compute_row_checksum

if TYPE_CHECKING:  # pragma: no cover
    pass

LOGGER = logging.getLogger(__name__)
CYPHER_DIR = Path(__file__).resolve().parent / "cypher"

TRUST = "VERBATIM"
CLASSIFICATION = "External"


# --------------------------------------------------------------------------- #
# corpus identity — a capture is not a corpus
# --------------------------------------------------------------------------- #
class CorpusNotRegisteredError(RuntimeError):
    """A capture that no ``config/doc-source-registry.yaml`` entry claims."""


def resolve_corpus_id(capture_id: str, *, registry: SourceRegistry | None = None) -> str:
    """Which REGISTRY corpus this capture belongs to.

    Two ids, and conflating them is a silent reporting bug rather than a
    crash. ``bmc-controlm-9.0.20-utilities`` is a CAPTURE — one fetch of one
    tree at one version. ``bmc-docs-controlm-utilities`` is the CORPUS — the
    doc-source-registry entry that governs it, and the id ``drydocs
    docs-verify`` searches for, because that entry's ``graph_locator`` says
    ``match: corpus_id, value: bmc-docs-controlm-utilities`` (Q7). A graph keyed by
    the capture id therefore answers "corpus missing" for a corpus that is
    fully loaded — the reconciliation check reporting a false negative, which
    is worse than not having run it.

    Resolution is REGISTRY-DRIVEN, never a string transform of the capture id:
    the entry that names this capture in its ``manifest`` path owns it. An
    unregistered capture raises rather than inventing an id — docmeta
    invariant 1 (no doc content loads while its registry entry is missing).
    """
    reg = registry or SourceRegistry.from_yaml()
    owners = [
        src.id
        for src in (reg.get(sid) for sid in reg.ids())
        if src.home == "doc-registry" and f"/{capture_id}/" in str(src.data.get("manifest") or "")
    ]
    if len(owners) == 1:
        return owners[0]
    if not owners:
        raise CorpusNotRegisteredError(
            f"capture {capture_id!r} belongs to no corpus: no config/doc-source-registry.yaml "
            f"entry names it in its `manifest:` path. Register the corpus before converting it "
            f"(docmeta invariant 1), or pass an explicit corpus id."
        )
    raise CorpusNotRegisteredError(
        f"capture {capture_id!r} is claimed by {len(owners)} registry entries ({', '.join(owners)}) "
        f"— exactly one entry must own a capture. Pass an explicit corpus id to disambiguate."
    )


# --------------------------------------------------------------------------- #
# page_role — an explicit title rule, never an LLM
# --------------------------------------------------------------------------- #
#: Ordered; first match wins. `topic` is the explicit fallback for a primary
#: topic page, NOT a silent default — every run reports the per-role counts, so
#: 593 topics is a visible fact rather than an unexamined bucket.
_ROLE_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("examples", re.compile(r"\bexamples?\b", re.I)),
    ("parameters", re.compile(r"\bparameters\b", re.I)),
    ("rules", re.compile(r"\brules\b", re.I)),
    ("overview", re.compile(r"\b(overview|introduction to)\b", re.I)),
)
ROLE_FALLBACK = "topic"
ROLES = (*tuple(name for name, _ in _ROLE_RULES), ROLE_FALLBACK)


def derive_page_role(title: str) -> str:
    for role, pattern in _ROLE_RULES:
        if pattern.search(title or ""):
            return role
    return ROLE_FALLBACK


# --------------------------------------------------------------------------- #
# stage 2 — convert
# --------------------------------------------------------------------------- #
@dataclass
class ConvertSummary:
    capture_id: str
    corpus_id: str
    documents: int
    toc_nodes: int
    roles: dict[str, int]
    related_links: int
    markdown_bytes: int

    def render(self) -> str:
        roles = "  ".join(f"{r}={self.roles.get(r, 0)}" for r in ROLES)
        return (
            f"converted {self.documents} documents / {self.toc_nodes} toc nodes "
            f"({self.markdown_bytes / 1e6:.1f} MB markdown)\n"
            f"  corpus: {self.corpus_id}  (capture: {self.capture_id})\n"
            f"  roles: {roles}\n"
            f"  related links carried (data, not edges): {self.related_links}"
        )


def convert_capture(
    capture_id: str,
    *,
    corpus_id: str | None = None,
    root: Path | None = None,
    registry: SourceRegistry | None = None,
) -> ConvertSummary:
    """Stage 2: captured HTML -> markdown + ``convert-manifest.json``.

    ``corpus_id`` resolves in three steps, most explicit first: the argument,
    then whatever the capture manifest declared, then the registry lookup in
    :func:`resolve_corpus_id`. It is never DERIVED from the capture id.
    """
    base = root or vendor_docs_dir(capture_id)
    capture_manifest = json.loads((base / "capture-manifest.json").read_text(encoding="utf-8"))
    corpus = (
        corpus_id
        or capture_manifest.get("corpus_id")
        or resolve_corpus_id(capture_id, registry=registry)
    )
    pages_dir, md_dir = base / "pages", base / "markdown"
    md_dir.mkdir(parents=True, exist_ok=True)

    docs: dict[str, dict] = {}
    roles: dict[str, int] = {}
    related_total = md_bytes = 0

    for node in capture_manifest["pages"]:
        page = node["page"]
        if page not in docs:
            converted = html_to_markdown((pages_dir / page).read_bytes())
            role = derive_page_role(node["title"] if node["anchor"] is None else converted.title)
            md_name = f"{Path(page).stem}.md"
            # J49: LF — the converted markdown is what downstream chunking and digests
            # read; a CRLF copy on Windows would hash differently from the same
            # conversion on Linux. Under DATA_ROOT, never committed.
            (md_dir / md_name).write_text(converted.markdown, encoding="utf-8", newline="\n")
            md_bytes += len(converted.markdown)
            roles[role] = roles.get(role, 0) + 1
            related_total += len(converted.related)
            docs[page] = {
                # Capture-SCOPED, not the bare stem — see VendorDocChunkRow.doc_id.
                "doc_id": f"{capture_id}/{Path(page).stem}",
                "page": page,
                "markdown": md_name,
                "title": converted.title,
                "abstract": converted.abstract,
                "page_role": role,
                "headings": converted.headings,
                "breadcrumb": node["breadcrumb"],
                "toc_path": node["toc_path"],
                "source_url": node["source_url"].split("#", 1)[0],
                "sha256": node["sha256"],
                # DATA for Q14's gate — deliberately not loaded as edges.
                "related": [{"href": r.href, "text": r.text} for r in converted.related],
                "sections": [],
            }
        if node["anchor"]:
            docs[page]["sections"].append(
                {"anchor": node["anchor"], "title": node["title"], "breadcrumb": node["breadcrumb"]}
            )

    manifest = {
        "capture_id": capture_id,
        "corpus_id": corpus,
        "vendor": capture_manifest["vendor"],
        "product": capture_manifest["product"],
        "doc_version": capture_manifest["version"],
        "book": capture_manifest["book"],
        "classification": CLASSIFICATION,
        "trust": TRUST,
        "captured_at": capture_manifest["captured_at"],
        "base_url": capture_manifest["base_url"],
        "documents": list(docs.values()),
    }
    (base / "convert-manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8", newline="\n"
    )  # J49: LF, same reason as the markdown above

    return ConvertSummary(
        capture_id=capture_id,
        corpus_id=corpus,
        documents=len(docs),
        toc_nodes=len(capture_manifest["pages"]),
        roles=roles,
        related_links=related_total,
        markdown_bytes=md_bytes,
    )


# --------------------------------------------------------------------------- #
# stage 3 — load
# --------------------------------------------------------------------------- #
def split_chunks(markdown: str) -> list[tuple[int, str, int, str]]:
    """Split on H2, the established chunking contract.

    Most pages carry a single ``#`` title and no ``##`` at all, so they are one
    chunk — honest for a corpus averaging ~6 KB per topic. The rare page with a
    section heading chunks into two, which is exactly what a fragment TOC node
    addresses.
    """
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", markdown, re.M))
    if not matches:
        return [(0, "(topic)", 0, markdown)]
    chunks = [(0, "(topic)", 0, markdown[: matches[0].start()])]
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        chunks.append((i + 1, m.group(1).strip(), 2, markdown[m.start() : end]))
    return chunks


class VendorDocsAdapter:
    """One row per chunk, from ``convert-manifest.json``."""

    name = "vendor-docs"

    def __init__(self, capture_id: str, *, root: Path | None = None) -> None:
        self.capture_id = capture_id
        self.base = root or vendor_docs_dir(capture_id)

    def __enter__(self) -> VendorDocsAdapter:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def rows(self) -> Iterator[dict]:
        manifest = json.loads((self.base / "convert-manifest.json").read_text(encoding="utf-8"))
        md_dir = self.base / "markdown"
        for doc in manifest["documents"]:
            text = (md_dir / doc["markdown"]).read_text(encoding="utf-8")
            prev_chunk_id: str | None = None
            for seq, heading, level, chunk_text in split_chunks(text):
                chunk_id = f"{doc['doc_id']}#{seq:03d}"
                yield {
                    # corpus_id is the REGISTRY id (what docs-verify searches
                    # for); capture_id says which fetch produced the row.
                    "corpus_id": manifest["corpus_id"],
                    "capture_id": manifest["capture_id"],
                    "doc_id": doc["doc_id"],
                    "title": doc["title"],
                    "abstract": doc["abstract"],
                    "page_role": doc["page_role"],
                    "breadcrumb": doc["breadcrumb"],
                    "toc_path": doc["toc_path"],
                    "source_url": doc["source_url"],
                    "sha256": doc["sha256"],
                    "captured_at": manifest["captured_at"],
                    "doc_version": manifest["doc_version"],
                    # Never true at load time: only a human confirming this
                    # capture against a runtime version may flip it (Q16).
                    "version_verified": False,
                    "trust": TRUST,
                    "classification": CLASSIFICATION,
                    "chunk_id": chunk_id,
                    "seq": seq,
                    "heading": heading,
                    "level": level,
                    "text": chunk_text,
                    "char_count": len(chunk_text),
                    "prev_chunk_id": prev_chunk_id,
                }
                prev_chunk_id = chunk_id


class VendorDocsLoader(BaseLoader):
    """Loads a converted vendor capture as :Document + :Chunk + TOC hierarchy."""

    name: ClassVar[str] = "vendor_docs.v1"
    source_id: ClassVar[str | None] = (
        "bmc-docs-controlm-utilities"  # renamed 2026-08-18 (doc-registry id grammar)
    )
    cypher_path: ClassVar[Path] = CYPHER_DIR / "vendor_docs.cypher"
    row_model: ClassVar[type] = VendorDocChunkRow
    source_label: ClassVar[str] = "vendor-docs"

    def to_params(self, model: BaseModel) -> dict:
        params = model.model_dump(mode="json")
        params["row_checksum"] = compute_row_checksum(params)
        return params
