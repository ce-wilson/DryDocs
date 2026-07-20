"""Row models for the doc-traceability loaders (backlog L7; gate
doc-traceability-feedback signed off 2026-07-20 — config/gate-log.md).

PRODUCT-PLANE documentation ontology, source connector #1 ("tenant 0"): the
DryDocs outline system itself — ``docs/design/*.md`` (drydocs.doc-outline.v1
anchors + the requirements traceability matrix) and the anchor-keyed feedback
files ``docs/design/feedback/<doc_id>-rev<N>.yaml``. Every row carries
``origin`` (the source-connector discriminator, gate A1) and every node key is
source-namespaced (gate A2).

Three row streams — three loaders (one cypher each, BaseLoader contract):

- :class:`DocSectionRow`     — one row per AUTHORED anchor per design doc;
  doc-level fields denormalized (the BmcDocChunkRow idiom) so the Cypher
  MERGEs :DesignDoc idempotently alongside each :DocSection + PART_OF.
- :class:`TraceabilityRow`   — one row per traceability-matrix table row;
  fans out to SPECIFIED_IN / IMPLEMENTED_BY / VERIFIED_BY (the star off
  :Requirement, gate B4). Sections are MATCHed, never MERGEd (load order:
  sections first).
- :class:`FeedbackNoteRow`   — one row per anchor-keyed note per feedback
  file; carries the review lifecycle ``status`` (gate C3) and the rev the
  note was taken against (gate C2). ANNOTATES targets the note's BASE
  authored anchor (an L11 derived anchor degrades to its parent section —
  the ``feedback_anchor_valid`` rule, mirrored graph-side).
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

#: Source-connector discriminator for connector #1 (gate A1/A2).
DESIGN_DOCS_ORIGIN = "drydocs-design-docs"


def _str_or_none(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


class DocSectionRow(BaseModel):
    """One authored section (``<!-- anchor: id -->``) of one design doc."""

    model_config = ConfigDict(
        populate_by_name=True, str_strip_whitespace=True, extra="ignore"
    )

    # --- DesignDoc fields (denormalized onto every section row) ---
    origin: str = Field(DESIGN_DOCS_ORIGIN, min_length=1)
    doc_id: str = Field(..., min_length=1, description="File stem, e.g. 'controlm-ingestion-tdd'.")
    title: str = Field(..., min_length=1, description="First H1 text (falls back to doc_id).")
    doc_type: str = Field(..., min_length=1, description="TDD | Runbook | Review | Explainer | DesignDoc (stem-suffix rule).")
    rev: int | None = Field(None, ge=1, description="Declared front-matter Rev (design_doc._REV_RE rule); None if undeclared.")
    doc_status: str | None = Field(None, description="DESCRIPTIVE | PRESCRIPTIVE, if declared.")
    commit: str | None = Field(None, description="Front-matter `commit \\`hash\\`` citation, if declared.")
    path: str = Field(..., min_length=1, description="Repo-relative path, posix-style.")

    # --- DocSection fields ---
    anchor: str = Field(..., min_length=1, description="The authored anchor id (stable, never positional).")
    heading: str = Field(..., min_length=1, description="The heading/first line following the anchor comment.")
    seq: int = Field(..., ge=0, description="Anchor order within the doc (file order).")

    @field_validator("doc_status", "commit", mode="before")
    @classmethod
    def _opt_str(cls, v: Any) -> str | None:
        return _str_or_none(v)


class TraceabilityCitation(BaseModel):
    """One test/verify citation cell fragment (gate A7: kind is an OPEN enum)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    kind: str = Field(..., min_length=1, description="unit | verify | gate | graph-test (open enum, kind-rule-v1).")
    ref: str = Field(..., min_length=1, description="The cleaned citation string (backticks stripped).")


class TraceabilityRow(BaseModel):
    """One requirements-traceability-matrix table row, fanned out to the star."""

    model_config = ConfigDict(
        populate_by_name=True, str_strip_whitespace=True, extra="ignore"
    )

    origin: str = Field(DESIGN_DOCS_ORIGIN, min_length=1)
    doc_id: str = Field(..., min_length=1, description="The doc whose matrix carries this row.")
    requirement_id: str = Field(..., min_length=1, description="e.g. 'FR-CMI-003' (per-source format, mode: loose today — gate D5).")
    kind: str = Field(..., min_length=1, description="FR | UC | NFR | other — derived from the id prefix (gate A3).")
    description: str = Field("", description="The Description cell, verbatim.")
    matrix_status: str | None = Field(None, description="The Status cell (done | open | ...), if the table carries one.")
    section_anchors: list[str] = Field(
        default_factory=list,
        description="Design-section cell anchors (comma-split). SPECIFIED_IN targets; MATCHed, never MERGEd.",
    )
    components: list[str] = Field(
        default_factory=list,
        description="Component/module cell refs (comma-split, backticks stripped). IMPLEMENTED_BY targets, key (origin, ref).",
    )
    tests: list[TraceabilityCitation] = Field(
        default_factory=list,
        description="Test/verify cell citations (semicolon-split). VERIFIED_BY targets, key (origin, ref).",
    )

    @field_validator("matrix_status", mode="before")
    @classmethod
    def _opt_str(cls, v: Any) -> str | None:
        return _str_or_none(v)


class FeedbackNoteRow(BaseModel):
    """One anchor-keyed note from one ``<doc_id>-rev<N>.yaml`` feedback file."""

    model_config = ConfigDict(
        populate_by_name=True, str_strip_whitespace=True, extra="ignore"
    )

    origin: str = Field(DESIGN_DOCS_ORIGIN, min_length=1)
    doc_id: str = Field(..., min_length=1)
    doc_rev: int = Field(..., ge=1, description="The rev the note was taken AGAINST (filename <N> — gate C2).")
    anchor: str = Field(..., min_length=1, description="The note's anchor as written (may be an L11 derived id).")
    base_anchor: str = Field(..., min_length=1, description="Authored anchor the note attaches to (derived ids degrade to their parent).")
    note: str = Field(..., min_length=1, description="The note text, verbatim.")
    status: Literal["open", "applied", "rejected", "superseded"] = Field(
        "open", description="Review lifecycle (gate C3). Optional per-note in the yaml; defaults open."
    )
    author: str | None = Field(
        None,
        description="Employee id of the reviewer (note-level `author:`, else file-level). "
        "Attribution edge MATCHes :Employee {employee_id} — absent/unmatched drops the edge, never fabricates.",
    )

    @field_validator("author", mode="before")
    @classmethod
    def _opt_str(cls, v: Any) -> str | None:
        return _str_or_none(v)
