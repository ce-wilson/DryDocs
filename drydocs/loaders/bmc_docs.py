"""BmcDocsAdapter / BmcDocsLoader — bmc-docs lexical-graph loader.

Manual chunking + MERGE (Neo4j llm-graph-builder pattern): chunk-only, NO LLM
extraction, NO embeddings, fully deterministic. Corpus:
``external/orchestration/bmc-controlm/controlm-*.md`` (26 converted BMC docs;
provenance model in ``SOURCE-MANIFEST.md`` — read its "PROVENANCE MODEL"
section before touching the tier classifier below).

Chunking rule: split each doc on H2 (``## ``) headings. The preamble before
the first H2 is chunk seq 0 with heading ``'(preamble)'``; H3+ stays nested
inside its parent H2 chunk (no further splitting). One ROW = one CHUNK; the
parent :Document's header fields are denormalized onto every row so the
Cypher can MERGE the :Document idempotently per row.

Each chunk is classified into a provenance tier (VERBATIM / GROUNDED /
SYNTHESIZED) by a deterministic heading + code-density rule — see
:func:`classify_chunk_tier`. This is intentionally coarse (heading-text
matching, not semantic understanding): the manifest's own per-file
"Provenance Classification" sections describe tiers at the *section* level,
and an H2 heading is the closest deterministic proxy available without an
LLM pass — which this loader deliberately does not use.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from pydantic import BaseModel

from drydocs_core.models.docs import BmcDocChunkRow
from drydocs_core.repo_paths import repo_root
from drydocs_core.source_registry import SourceRegistry

from .base import BaseLoader, LoadSummary, compute_row_checksum

if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

    from drydocs_core.run_log import LoaderRunLog

LOGGER = logging.getLogger(__name__)

REPO_ROOT = repo_root(Path(__file__).resolve().parents[2])
CYPHER_DIR = Path(__file__).resolve().parent / "cypher"
DEFAULT_CORPUS_DIR = REPO_ROOT / "external" / "orchestration" / "bmc-controlm"

TARGET_VERSION = "9.0.21.300"
CLASSIFICATION = "External"
TRUST_DEFAULT = "GROUNDED"
TIER_RULE_ID = "manifest-default-v1"


def declared_describes_product(registry: SourceRegistry | None = None) -> str:
    """Q18: the product id this corpus documents, from its OWN registry row.

    `describes_product` is optional per corpus — not every corpus describes a
    product — but for THIS loader it is load-bearing: without it the
    (:Document)-[:DESCRIBES]->(:SoftwareProduct) join has no declared target,
    which is exactly the unreproducible-constant state Q18 closed. The guard
    in tests/unit/test_doc_registry.py proves the declared id is a real
    config/taxonomy/software-registry.yaml product.
    """
    reg = registry or SourceRegistry.from_yaml()
    entry = reg.get("bmc-docs")
    product_id = (entry.data or {}).get("describes_product")
    if not product_id:
        raise ValueError(
            "doc-source-registry entry 'bmc-docs' declares no describes_product — "
            "the DESCRIBES join has no target. Declare the product id in "
            "config/doc-source-registry.yaml (Q18: the loader reads the ledger; "
            "there is no fallback constant)."
        )
    return str(product_id)


# ---- header parsing ---------------------------------------------------------

_H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_SOURCE_RE = re.compile(r"^\*\*Source:\*\*\s*(.+?)\s*$", re.MULTILINE)
_DOCUMENT_RE = re.compile(r"^\*\*Document:\*\*\s*(.+?)\s*$", re.MULTILINE)
_DATE_SCRAPED_RE = re.compile(r"^\*\*Date Scraped:\*\*\s*(.+?)\s*$", re.MULTILINE)
_CAPTURED_RE = re.compile(r"^\*\*Captured:\*\*\s*(.+?)\s*$", re.MULTILINE)
_PURPOSE_RE = re.compile(r"^\*\*Purpose:\*\*\s*(.+?)\s*$", re.MULTILINE)
_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
_URL_RE = re.compile(r"https?://[^\s)`\]]+")

# ---- tier classifier (SOURCE-MANIFEST default tier rule) --------------------
#
# Order matters: an "Authoritative ..." heading (Authoritative Corrections /
# Authoritative Additions — the per-file sections that supersede the
# SaaS-derived body, per each doc's own Provenance Classification block) wins
# first as VERBATIM. Then the SYNTHESIZED heading family named in the
# manifest's default tier rule. Then the majority-fenced-code rule, which
# catches illustrative code under an innocuous heading. Everything else
# defaults to GROUNDED — the conservative default; VERBATIM is granted only
# by the heading rule above, never by absence of a SYNTHESIZED signal.
#
# "\bpatterns\b" (plural) deliberately does NOT match bare "pattern" so it
# does not misfire on controlm-pattern-matching.md's "Pattern Matching ..."
# headings (always singular + "Matching") while still catching "Advanced
# Patterns" / "Integration Patterns" / "JSON Structure Patterns" / etc.
#
# "planning agents?" (no leading anchor) catches "Notes for Planning Agents",
# the singular "Notes for Planning Agent" variant seen in
# controlm-planning-specifications.md, and the bare "For Planning Agents: ..."
# lead-in used in controlm-planning-quick-reference.md.
_VERBATIM_HEADING_RE = re.compile(r"authoritative", re.IGNORECASE)
_SYNTHESIZED_HEADING_RE = re.compile(
    r"\bpatterns\b|\bbest practices\b|\buse cases?\b|planning agents?"
    r"|\bvendor attributes\b|\bworkflow\b|\bapi examples?\b",
    re.IGNORECASE,
)
_FENCE_MARK_RE = re.compile(r"^\s*```")


def _is_majority_code(text: str) -> bool:
    """True if more than half of a chunk's non-blank lines sit inside fenced
    code blocks (``` ... ```). Fence-marker lines themselves count as code."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return False
    in_fence = False
    code_lines = 0
    for ln in lines:
        if _FENCE_MARK_RE.match(ln):
            in_fence = not in_fence
            code_lines += 1
            continue
        if in_fence:
            code_lines += 1
    return code_lines / len(lines) > 0.5


def classify_chunk_tier(heading: str, text: str) -> str:
    """Deterministic heading + code-density classifier (manifest-default-v1).

    Returns one of VERBATIM / GROUNDED / SYNTHESIZED. See the module-level
    comment above for the rule ordering and the two documented heading-regex
    edge cases (pattern-matching doc, planning-agent variants).
    """
    if _VERBATIM_HEADING_RE.search(heading):
        return "VERBATIM"
    if _SYNTHESIZED_HEADING_RE.search(heading):
        return "SYNTHESIZED"
    if _is_majority_code(text):
        return "SYNTHESIZED"
    return "GROUNDED"


@dataclass
class _DocHeader:
    doc_id: str
    title: str
    source_url: str | None
    source_page: str | None
    scraped_on: str | None
    purpose: str | None
    path: str


def _parse_header(md_path: Path) -> _DocHeader:
    text = md_path.read_text(encoding="utf-8")
    doc_id = md_path.stem

    h1_match = _H1_RE.search(text)
    title = h1_match.group(1).strip() if h1_match else doc_id

    # Confine header-field search to the block before the first H2 — fields
    # that happen to repeat the same labels deeper in the doc (e.g. a
    # per-parameter "Purpose:" line inside a table) must not be picked up.
    h2_match = _H2_RE.search(text)
    header_block = text[: h2_match.start()] if h2_match else text

    document_m = _DOCUMENT_RE.search(header_block)
    date_m = _DATE_SCRAPED_RE.search(header_block) or _CAPTURED_RE.search(header_block)
    purpose_m = _PURPOSE_RE.search(header_block)
    url_m = _URL_RE.search(header_block)

    scraped_on = None
    if date_m:
        date_only = _DATE_RE.search(date_m.group(1))
        scraped_on = date_only.group(1) if date_only else None

    rel_path = md_path.resolve().relative_to(REPO_ROOT).as_posix()

    return _DocHeader(
        doc_id=doc_id,
        title=title,
        source_url=url_m.group(0).rstrip(".,)`]") if url_m else None,
        source_page=document_m.group(1).strip() if document_m else None,
        scraped_on=scraped_on,
        purpose=purpose_m.group(1).strip() if purpose_m else None,
        path=rel_path,
    )


def _split_chunks(full_text: str) -> list[tuple[int, str, int, str]]:
    """Split ``full_text`` on H2 headings.

    Returns a list of ``(seq, heading, level, text)`` tuples. seq 0 is the
    preamble (``heading='(preamble)'``, ``level=0``) — everything from the
    start of the file up to (not including) the first H2 line. Every
    subsequent tuple is one H2 section (``level=2``) running through to the
    next H2 or end of file; H3+ subheadings stay embedded in that text
    verbatim (no further splitting).
    """
    h2_matches = list(_H2_RE.finditer(full_text))
    if not h2_matches:
        return [(0, "(preamble)", 0, full_text)]

    chunks: list[tuple[int, str, int, str]] = [
        (0, "(preamble)", 0, full_text[: h2_matches[0].start()])
    ]
    for i, m in enumerate(h2_matches):
        heading = m.group(1).strip()
        start = m.start()
        end = h2_matches[i + 1].start() if i + 1 < len(h2_matches) else len(full_text)
        chunks.append((i + 1, heading, 2, full_text[start:end]))
    return chunks


class BmcDocsAdapter:
    """Yield one row per chunk across every ``controlm-*.md`` file in the corpus.

    ``SOURCE-MANIFEST.md`` itself is not a ``controlm-*.md`` file so the glob
    naturally excludes it; the explicit filename check below is a defensive
    no-op guard against that ever changing.
    """

    name = "bmc-docs"

    def __init__(
        self,
        corpus_dir: Path | str = DEFAULT_CORPUS_DIR,
        *,
        registry: SourceRegistry | None = None,
    ) -> None:
        self.corpus_dir = Path(corpus_dir)
        # Q18: the DESCRIBES target is DECLARED on this corpus's own
        # doc-source-registry row (`describes_product`), read here — the
        # former SUBJECT_PRODUCT_ID module constant is REMOVED, not shadowed:
        # a fallback constant beside a declared field is how the two silently
        # disagree later. A row without the field refuses loudly at
        # construction, before anything is read or written.
        reg = registry or SourceRegistry.from_yaml()
        self.describes_product = declared_describes_product(reg)
        # Q26: corpus_id is the G32 SS-A blast-radius scoping — stamped on every
        # Document and Chunk row, READ FROM the corpus's registry row (the same
        # row the describes_product read resolved), never a loader literal. It
        # is the docs-verify graph_locator join key.
        self.corpus_id = reg.get(self.name).id

    def __enter__(self) -> BmcDocsAdapter:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    def rows(self) -> Iterator[dict]:
        for md_path in sorted(self.corpus_dir.glob("controlm-*.md")):
            if md_path.name == "SOURCE-MANIFEST.md":
                continue
            header = _parse_header(md_path)
            full_text = md_path.read_text(encoding="utf-8")
            prev_chunk_id: str | None = None
            for seq, heading, level, chunk_text in _split_chunks(full_text):
                chunk_id = f"{header.doc_id}#{seq:03d}"
                yield {
                    "doc_id": header.doc_id,
                    "title": header.title,
                    "source_url": header.source_url,
                    "source_page": header.source_page,
                    "scraped_on": header.scraped_on,
                    "purpose": header.purpose,
                    "path": header.path,
                    "trust_default": TRUST_DEFAULT,
                    "target_version": TARGET_VERSION,
                    "classification": CLASSIFICATION,
                    "subject_product_id": self.describes_product,
                    "corpus_id": self.corpus_id,
                    "chunk_id": chunk_id,
                    "seq": seq,
                    "heading": heading,
                    "level": level,
                    "text": chunk_text,
                    "char_count": len(chunk_text),
                    "provenance": classify_chunk_tier(heading, chunk_text),
                    "tier_rule": TIER_RULE_ID,
                    "prev_chunk_id": prev_chunk_id,
                }
                prev_chunk_id = chunk_id


class BmcDocsLoader(BaseLoader):
    """Loads the chunked corpus and joins each :Document to its :SoftwareProduct.

    The DESCRIBES join is an OPTIONAL MATCH inside a FOREACH guard (see
    ``bmc_docs.cypher``), which tolerates a per-row miss by design — a single
    misspelled ``subject_product_id`` drops that row's edge and nothing else.
    That same mechanism used to swallow the far bigger failure of the product
    registry being absent from the database ENTIRELY: every DESCRIBES edge
    silently missing, reported as a clean success. The two are distinguished
    here — the whole-registry case is a refusal, the per-row case is a warning.
    """

    name: ClassVar[str] = "bmc_docs.v1"
    source_id: ClassVar[str | None] = "bmc-docs"
    cypher_path: ClassVar[Path] = CYPHER_DIR / "bmc_docs.cypher"
    row_model: ClassVar[type] = BmcDocChunkRow
    source_label: ClassVar[str] = "markdown"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # Documents this run wrote that ended up with no DESCRIBES edge —
        # [{doc_id, subject_product_id}], populated post-load.
        self.documents_without_product: list[dict] = []

    def to_params(self, model: BaseModel) -> dict:
        """Add the delta checksum (doc 06 Phase 2) over the full chunk row —
        including the denormalized doc-header fields, so an edit to the doc's
        header (title/purpose/etc.) also re-triggers WAS_GENERATED_BY on every
        one of that doc's chunks, not just a content edit."""
        params = model.model_dump(mode="json")
        params["row_checksum"] = compute_row_checksum(params)
        return params

    # ---- prereq enforcement ------------------------------------------------

    def _load(self, summary: LoadSummary, run_log: LoaderRunLog | None) -> LoadSummary:
        """Refuse an absent product registry, then report per-row misses.

        The refusal runs BEFORE ``super()._load`` — which is what reaches
        ``_preflight_indexes`` and ``_open_run`` — so a refused load writes
        nothing at all, not even the :JobRun (the ``_preflight_indexes``
        convention).
        """
        self._assert_product_registry_present()
        result = super()._load(summary, run_log)
        self._report_documents_without_product()
        return result

    def _assert_product_registry_present(self) -> None:
        """Fail loudly when NO real :SoftwareProduct is reachable.

        The predicate deliberately excludes :SchemaMeta. ``schema_graph.cypher``
        MERGEs a ``:SchemaMeta:SoftwareProduct {name: 'SoftwareProduct'}``
        exemplar carrying the real label with NO product_id, so a bare
        ``count(:SoftwareProduct)`` would count the exemplar and wave an empty
        registry straight through — the whole failure this check exists to
        catch. ``NOT sp:SchemaMeta`` is the rename-proof form; the
        product_id-not-null clause additionally rejects any other keyless stub.
        """
        rows = self.client.run(
            "MATCH (sp:SoftwareProduct) "
            "WHERE NOT sp:SchemaMeta AND sp.product_id IS NOT NULL "
            "RETURN count(sp) AS products"
        )
        products = rows[0].get("products", 0) if rows else 0
        if products:
            LOGGER.info(
                "Loader %s: product registry present (%d :SoftwareProduct)",
                self.name,
                products,
            )
            return
        raise RuntimeError(
            f"Loader {self.name}: refusing to load — no :SoftwareProduct nodes are "
            "reachable in this database, so every DESCRIBES edge would be silently "
            "dropped and the load would still report success. Run "
            "`drydocs load-software-registry` against this database first "
            "(a relationship cannot span databases — check you are pointed at the "
            "database that holds the registry)."
        )

    def _report_documents_without_product(self) -> None:
        """Warn (never fail) about the per-row misses the FOREACH guard drops.

        Asks the graph what actually happened rather than re-deriving it from
        the rows: any :Document this run touched that has no DESCRIBES edge is
        a miss, whatever caused it. Tolerated by design — one bad
        subject_product_id must not cost the corpus its Documents and Chunks —
        but never silent (the counts-are-always-reported house rule).
        """
        rows = self.client.run(
            "MATCH (doc:Document {last_run_id: $run_id}) "
            "WHERE NOT (doc)-[:DESCRIBES]->(:SoftwareProduct) "
            "RETURN doc.doc_id AS doc_id, "
            "       doc.subject_product_id AS subject_product_id "
            "ORDER BY doc_id",
            run_id=self.run_id,
        )
        self.documents_without_product = [dict(r) for r in rows]
        if not self.documents_without_product:
            return
        unresolved = sorted(
            {
                r.get("subject_product_id")
                for r in self.documents_without_product
                if r.get("subject_product_id") is not None
            }
        )
        LOGGER.warning(
            "Loader %s: %d document(s) loaded WITHOUT a DESCRIBES edge — their "
            "subject_product_id did not resolve to a :SoftwareProduct "
            "(unresolved id(s): %s; documents: %s)",
            self.name,
            len(self.documents_without_product),
            ", ".join(unresolved) or "<none set>",
            ", ".join(r["doc_id"] for r in self.documents_without_product),
        )
