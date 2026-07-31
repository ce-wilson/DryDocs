"""Row model for the bmc-docs lexical-graph loader (Document -> Chunk).

Source: ``external/orchestration/bmc-controlm/controlm-*.md`` (26 converted
BMC docs; provenance model in ``SOURCE-MANIFEST.md``). This is a manual
chunking + MERGE lexical graph (Neo4j llm-graph-builder pattern) — chunk-only,
no LLM extraction, no embeddings, fully deterministic.

One ROW = one CHUNK. Its parent :Document's header fields are denormalized
onto every chunk row (BmcDocsAdapter yields one row per chunk, never a
separate "document row") so the Cypher template can MERGE the :Document
idempotently in the same UNWIND that MERGEs the :Chunk — matching the
BaseLoader row-streaming contract (no document-then-chunks two-pass loader
needed).
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _str_or_none(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


class BmcDocChunkRow(BaseModel):
    """One chunk of one BMC documentation file.

    Doc-level fields (doc_id .. subject_product_id) are constant across every
    row for the same ``doc_id`` — the Cypher MERGEs :Document once per row
    (idempotent) alongside the :Chunk. Chunk-level fields (chunk_id ..
    prev_chunk_id) vary per row.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="ignore",
    )

    # --- Document fields (denormalized onto every chunk row) ---
    doc_id: str = Field(..., min_length=1, description="File stem, e.g. 'controlm-variables'.")
    title: str = Field(..., min_length=1, description="First H1 text (falls back to doc_id if absent).")
    source_url: str | None = Field(
        None, description="URL parsed from the doc header, if the header carries one. Null-safe."
    )
    source_page: str | None = Field(
        None, description="The '**Document:**' header line (e.g. 'Variables.htm'), if present."
    )
    scraped_on: str | None = Field(
        None,
        description="'**Date Scraped:**' or '**Captured:**' header date (YYYY-MM-DD), if present.",
    )
    purpose: str | None = Field(None, description="The '**Purpose:**' header line, if present.")
    path: str = Field(..., min_length=1, description="Repo-relative path, posix-style.")
    trust_default: str = Field(
        "GROUNDED",
        description=(
            "Doc-level fallback tier absent any chunk-level override — the "
            "SOURCE-MANIFEST default tier rule's baseline outcome for "
            "unflagged content. Every doc carries the same constant; the "
            "per-chunk 'provenance' field is what actually varies."
        ),
    )
    target_version: str = "9.0.21.300"
    classification: str = "External"
    subject_product_id: str = "controlm"

    # --- Chunk fields ---
    chunk_id: str = Field(..., min_length=1, description="'<doc_id>#<seq>' zero-padded, e.g. 'controlm-variables#003'.")
    seq: int = Field(..., ge=0, description="0 = preamble (before the first H2); 1..N = H2 sections in file order.")
    heading: str = Field(..., min_length=1, description="H2 heading text, or '(preamble)' for seq 0.")
    level: int = Field(..., ge=0, description="0 for the preamble chunk; 2 for every H2-split chunk.")
    text: str = Field(..., min_length=1, description="Verbatim chunk markdown (heading line included).")
    char_count: int = Field(..., ge=0, description="len(text); computed by the adapter.")
    provenance: Literal["VERBATIM", "GROUNDED", "SYNTHESIZED"] = Field(
        ..., description="Per-chunk tier from the deterministic heading classifier."
    )
    tier_rule: str = Field(
        "manifest-default-v1",
        description="Id of the classifier rule that produced 'provenance' (audit trail).",
    )
    prev_chunk_id: str | None = Field(
        None, description="Previous chunk's chunk_id in file order; None for seq 0."
    )

    @field_validator(
        "source_url", "source_page", "scraped_on", "purpose", "prev_chunk_id",
        mode="before",
    )
    @classmethod
    def _opt_str(cls, v: Any) -> str | None:
        return _str_or_none(v)


class BookChunkRow(BaseModel):
    """One chunk of a published-book PDF loaded as a lexical graph (Q2).

    Same one-ROW-=-one-CHUNK contract as :class:`BmcDocChunkRow` (doc fields
    denormalized onto every row for the idempotent :Document MERGE), tailored
    to a book: no scraped-page/vendor-version fields, and three navigation
    properties (``chapter``/``section``/``page_start``) so traversal queries
    can address the book the way its own citations do.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="ignore",
    )

    # --- Document fields (denormalized onto every chunk row) ---
    doc_id: str = Field(..., min_length=1, description="Stable id, e.g. 'essential-graphrag'.")
    title: str = Field(..., min_length=1, description="Book title (subtitle included).")
    authors: str = Field(..., min_length=1, description="Comma-separated author names.")
    publisher: str = Field(..., min_length=1, description="e.g. 'Manning'.")
    published: str = Field(..., min_length=1, description="Publication year/month, e.g. '2025-07'.")
    source_url: str = Field(..., min_length=1, description="Citation URL (the PDF itself is local-only).")
    path: str = Field(..., min_length=1, description="Repo-relative path of the local (gitignored) PDF.")
    trust_default: str = Field(
        "GROUNDED",
        description=(
            "Doc-level tier: GROUNDED — pypdf text extraction is mechanical "
            "but lossy (ligature drops, intra-word splits), so chunks are "
            "faithful-derivation, not byte-VERBATIM."
        ),
    )
    classification: str = "External"

    # --- Chunk fields ---
    chunk_id: str = Field(..., min_length=1, description="'<doc_id>#<seq>' zero-padded, e.g. 'essential-graphrag#012'.")
    seq: int = Field(..., ge=0, description="0 = front matter; then chapter/section chunks in book order.")
    heading: str = Field(..., min_length=1, description="Section heading line, chapter title, '(front matter)' or '(back matter)'.")
    level: int = Field(..., ge=0, description="0 front/back matter; 1 chapter/appendix preamble; 2 numbered section.")
    text: str = Field(..., min_length=1, description="Verbatim extracted text of the chunk (heading line included).")
    char_count: int = Field(..., ge=0, description="len(text); computed by the adapter.")
    provenance: Literal["VERBATIM", "GROUNDED", "SYNTHESIZED"] = Field(
        ..., description="Per-chunk tier; constant GROUNDED under pdf-extract-grounded-v1."
    )
    tier_rule: str = Field(
        "pdf-extract-grounded-v1",
        description="Id of the rule that produced 'provenance' (audit trail).",
    )
    prev_chunk_id: str | None = Field(
        None, description="Previous chunk's chunk_id in book order; None for seq 0."
    )
    chapter: int | None = Field(
        None, ge=1, description="Chapter number for chapter/section chunks; None for front/back matter and appendix."
    )
    section: str | None = Field(
        None, description="Section number as printed, e.g. '3.2' or 'A.1'; None for non-section chunks."
    )
    page_start: int = Field(..., ge=1, description="1-based PDF page where the chunk begins.")

    @field_validator("prev_chunk_id", "section", mode="before")
    @classmethod
    def _opt_str(cls, v: Any) -> str | None:
        return _str_or_none(v)


class VendorDocChunkRow(BaseModel):
    """One chunk of one captured vendor documentation topic (Q13).

    Distinct from :class:`BmcDocChunkRow` on purpose. That corpus is our
    paraphrase, so it carries a per-chunk provenance TIER inferred from heading
    text. This corpus is a verbatim vendor capture: the trust is uniform, and
    what varies instead is navigational structure — breadcrumb, toc_path,
    page_role — plus the version the documentation describes.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="ignore",
    )

    # --- corpus / document fields (denormalized onto every chunk row) ---
    corpus_id: str = Field(..., min_length=1, description="Capture id, e.g. 'bmc-controlm-9.0.20-utilities'.")
    doc_id: str = Field(..., min_length=1, description="Topic file stem, e.g. '3921'.")
    title: str = Field(..., min_length=1)
    abstract: str = Field("", description="First paragraph — cheap triage before spending context on chunks.")
    page_role: str = Field(..., min_length=1, description="examples|parameters|rules|overview|topic.")
    breadcrumb: str = Field("", description="TOC path as text, e.g. 'Utilities > emdef utility for jobs'.")
    toc_path: list[str] = Field(default_factory=list, description="TOC ancestry, outermost first.")
    source_url: str = Field(..., min_length=1, description="Canonical vendor URL, fragment stripped.")
    sha256: str = Field(..., min_length=1, description="Digest of the captured bytes.")
    captured_at: str = Field(..., min_length=1)
    doc_version: str = Field(..., min_length=1, description="Vendor documentation version, e.g. '9.0.20'.")
    version_verified: bool = Field(
        False,
        description=(
            "Whether a human confirmed this documentation against the runtime version. "
            "NEVER true at load time — only Q16's currency workflow may flip it."
        ),
    )
    trust: str = Field("VERBATIM", description="A capture is the vendor's own words.")
    classification: str = Field("External")

    # --- chunk fields ---
    chunk_id: str = Field(..., min_length=1)
    seq: int = Field(..., ge=0)
    heading: str = Field(..., min_length=1)
    level: int = Field(..., ge=0, le=6)
    text: str = Field(...)
    char_count: int = Field(..., ge=0)
    prev_chunk_id: str | None = Field(None)
