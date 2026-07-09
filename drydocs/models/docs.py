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
