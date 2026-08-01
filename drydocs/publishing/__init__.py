"""drydocs-review docs-publish pipeline (``drydocs-review`` component).

Manifest-driven publishing of review/doc pages: author XHTML fragments, assemble them
via a template, validate (well-formed XML + a macro allow-list), preview locally, and
push through a **pluggable publisher**. The real Confluence push is deliberately
abstracted behind :class:`Publisher` — this public template ships offline publishers
only; a company implementation supplies a ConfluencePublisher (space coordinates,
auth, wrapper) in its gitignored twin. No internal push details live here.

Offline tooling — assembling/validating/previewing needs no HITL gate. classification:
Internal-Public.
"""
from __future__ import annotations

from .assembler import DEFAULT_TEMPLATE, assemble
from .preview import write_preview
from .publisher import LocalPublisher, NoopPublisher, Publisher, PublishResult
from .validator import (
    DEFAULT_ALLOWED_MACROS,
    ValidationError,
    validate,
    validate_macros,
    validate_xml,
)

__all__ = [
    "assemble",
    "DEFAULT_TEMPLATE",
    "write_preview",
    "Publisher",
    "NoopPublisher",
    "LocalPublisher",
    "PublishResult",
    "validate",
    "validate_xml",
    "validate_macros",
    "ValidationError",
    "DEFAULT_ALLOWED_MACROS",
]
