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
    title: str = Field(
        ..., min_length=1, description="First H1 text (falls back to doc_id if absent)."
    )
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
    # Q18/Q26: REQUIRED, no default — a fallback literal beside the declared
    # registry field is how the two silently disagree later (the removed
    # SUBJECT_PRODUCT_ID constant's defect, one layer down).
    subject_product_id: str = Field(..., min_length=1)
    corpus_id: str = Field(
        ...,
        min_length=1,
        description="The doc-source-registry row id (Q26 — the G32 SS-A blast-radius scoping property, stamped on every :Document and :Chunk; the adapter reads it from the registry row, never a literal).",
    )

    # --- Chunk fields ---
    chunk_id: str = Field(
        ...,
        min_length=1,
        description="'<doc_id>#<seq>' zero-padded, e.g. 'controlm-variables#003'.",
    )
    seq: int = Field(
        ...,
        ge=0,
        description="0 = preamble (before the first H2); 1..N = H2 sections in file order.",
    )
    heading: str = Field(
        ..., min_length=1, description="H2 heading text, or '(preamble)' for seq 0."
    )
    level: int = Field(
        ..., ge=0, description="0 for the preamble chunk; 2 for every H2-split chunk."
    )
    text: str = Field(
        ..., min_length=1, description="Verbatim chunk markdown (heading line included)."
    )
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
        "source_url",
        "source_page",
        "scraped_on",
        "purpose",
        "prev_chunk_id",
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
    subject_product_id: str | None = Field(
        default=None,
        description=(
            "Q9 (2026-08-19): the DESCRIBES hook target — the SoftwareProduct this "
            "book is vendor documentation FOR (MATCH-only in the cypher; None keeps "
            "a book hook-less). extra='ignore' silently DROPPED this field before it "
            "was declared, which is why the first live reload wrote no edge."
        ),
    )
    title: str = Field(..., min_length=1, description="Book title (subtitle included).")
    authors: str = Field(..., min_length=1, description="Comma-separated author names.")
    publisher: str = Field(..., min_length=1, description="e.g. 'Manning'.")
    published: str = Field(..., min_length=1, description="Publication year/month, e.g. '2025-07'.")
    source_url: str = Field(
        ..., min_length=1, description="Citation URL (the PDF itself is local-only)."
    )
    path: str = Field(
        ..., min_length=1, description="Repo-relative path of the local (gitignored) PDF."
    )
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
    chunk_id: str = Field(
        ...,
        min_length=1,
        description="'<doc_id>#<seq>' zero-padded, e.g. 'essential-graphrag#012'.",
    )
    seq: int = Field(
        ..., ge=0, description="0 = front matter; then chapter/section chunks in book order."
    )
    heading: str = Field(
        ...,
        min_length=1,
        description="Section heading line, chapter title, '(front matter)' or '(back matter)'.",
    )
    level: int = Field(
        ...,
        ge=0,
        description="0 front/back matter; 1 chapter/appendix preamble; 2 numbered section.",
    )
    text: str = Field(
        ...,
        min_length=1,
        description="Verbatim extracted text of the chunk (heading line included).",
    )
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
        None,
        ge=1,
        description="Chapter number for chapter/section chunks; None for front/back matter and appendix.",
    )
    section: str | None = Field(
        None,
        description="Section number as printed, e.g. '3.2' or 'A.1'; None for non-section chunks.",
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
    corpus_id: str = Field(
        ...,
        min_length=1,
        description=(
            "The doc-source-registry CORPUS id, e.g. 'bmc-docs-controlm-utilities' — NOT the "
            "capture id. `drydocs docs-verify` looks a corpus up through its registry "
            "entry's graph_locator (Q7), so a graph keyed by capture id reports a loaded "
            "corpus as MISSING."
        ),
    )
    capture_id: str = Field(
        ...,
        min_length=1,
        description=(
            "Which CAPTURE of that corpus produced this row, e.g. "
            "'bmc-controlm-9.0.20-utilities'. One corpus has many captures over time; "
            "the capture id embeds the version, which is what keeps two versions of the "
            "same topic from merging onto one node."
        ),
    )
    doc_id: str = Field(
        ...,
        min_length=1,
        description=(
            "Capture-scoped topic identity, '<capture_id>/<file stem>' e.g. "
            "'bmc-controlm-9.0.20-utilities/3921'. Scoped rather than the bare stem "
            "because Author-it reuses topic ids ACROSS publications: MERGE on a bare "
            "'3921' would silently overwrite the 9.0.20 topic with its 9.0.21 namesake "
            "and take the version distinction with it."
        ),
    )
    title: str = Field(..., min_length=1)
    abstract: str = Field(
        "", description="First paragraph — cheap triage before spending context on chunks."
    )
    page_role: str = Field(
        ..., min_length=1, description="examples|parameters|rules|overview|topic."
    )
    breadcrumb: str = Field(
        "", description="TOC path as text, e.g. 'Utilities > emdef utility for jobs'."
    )
    toc_path: list[str] = Field(default_factory=list, description="TOC ancestry, outermost first.")
    source_url: str = Field(
        ..., min_length=1, description="Canonical vendor URL, fragment stripped."
    )
    sha256: str = Field(..., min_length=1, description="Digest of the captured bytes.")
    captured_at: str = Field(..., min_length=1)
    doc_version: str = Field(
        ..., min_length=1, description="Vendor documentation version, e.g. '9.0.20'."
    )
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


class EmailExtractRow(BaseModel):
    """One chunk of one failure/activity email extract (Q10).

    Same one-ROW-=-one-CHUNK contract as the other lexical rows. The SOURCE is
    the Copilot JSON extract on the file server; the original .msg is referenced
    by path and NEVER copied or parsed — after the 6-18 month Outlook purge the
    file-server pair is the only copy (a system of record, not a cache), so the
    loader treats both paths as citations.

    DELIBERATELY ABSENT: any folder/process assignment field. An email whose
    subject is not extractable loads UNASSIGNED — the assignment edge is new
    relationship semantics owned by gate email-folder-assignment, and no loader
    field may exist for it before that gate signs (the invent-a-relationship-
    during-import failure CLAUDE.md §1 forbids).
    """

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True, extra="ignore")

    # --- Document fields (denormalized onto every chunk row) ---
    doc_id: str = Field(
        ...,
        min_length=1,
        description="'email:<12-hex digest>' — deterministic from (subject, sent_at), truncate-and-reload safe.",
    )
    subject: str = Field(..., min_length=1)
    sent_at: str = Field(
        ...,
        min_length=1,
        description="ISO timestamp from the extract; freshness metadata, never identity.",
    )
    msg_path: str = Field(
        ...,
        min_length=1,
        description="File-server path of the original .msg — a CITATION, never opened by the loader.",
    )
    extract_path: str = Field(
        ..., min_length=1, description="Path of the JSON extract this row was read from."
    )
    trust_default: str = Field(
        default="VERBATIM", description="The extract is the sender's own words as extracted."
    )
    classification: str = Field(default="Internal")

    # --- Chunk fields (vary per row) ---
    chunk_id: str = Field(..., min_length=1, description="'<doc_id>#<seq>' zero-padded.")
    seq: int = Field(..., ge=0)
    text: str = Field(..., min_length=1)
    char_count: int = Field(..., ge=0)
    prev_chunk_id: str | None = Field(default=None)
    row_checksum: str = Field(..., min_length=1)
