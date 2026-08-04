"""The connector protocol — ACQUISITION ONLY.

``fetch(source) -> list[RawPage]``, and that is the whole contract. Cleaning,
tokenizing and hashing are downstream stages with their own modules, so a
connector never decides what a page MEANS or what its digest is. That split is
what lets the company implement Confluence/SharePoint/Teams/email behind this
same protocol without re-deciding anything the producer already settled.

A connector returns pages VERBATIM. It does not follow links, discover URLs,
or expand a location into more locations — every capturable set of pages is
resolved from the publisher's own manifest before any request is issued, which
is what makes the Q12 pre-flight refusal exact rather than a mid-run abort.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


class SourceUnavailableError(RuntimeError):
    """The source could not be reached or read.

    Distinct from a refusal: a refusal (``TooManyPagesError``,
    ``DisallowedSchemeError``) means we declined on purpose and nothing was
    fetched; this means we tried and the world said no. Callers that retry
    should retry only this one.
    """


@dataclass(frozen=True)
class RawPage:
    """One fetched document, exactly as the source returned it."""

    #: Where it came from — a URL for `web`, a filesystem path for `filedrop`.
    location: str
    #: Undecoded bytes. Decoding is a cleaning decision, not an acquisition
    #: one: the charset a page DECLARES and the charset it IS often differ,
    #: and guessing here would lose the evidence.
    body: bytes
    #: Whatever the source said it was, unvalidated (`text/html; charset=...`).
    content_type: str | None = None
    #: Connector-specific extras (HTTP status, file mtime). Never load-bearing.
    meta: dict[str, str] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.body)


@dataclass(frozen=True)
class FetchSource:
    """What to acquire — a connector-neutral request.

    Deliberately NOT a doc-source-registry row: connectors stay ignorant of
    the registry's file format, so a registry schema change cannot reach into
    them. :mod:`drydocs_docmeta.registry` builds these.
    """

    id: str
    #: URLs (`web`) or filesystem paths (`filedrop`). Resolved in full BEFORE
    #: the first request, which is what the ceiling is checked against.
    locations: tuple[str, ...]
    #: Per-source override of the configured page ceiling. Explicit opt-in —
    #: the config default is what applies when this is None.
    max_pages: int | None = None


@runtime_checkable
class Connector(Protocol):
    """What every connector implements — the company-side ones included."""

    name: str

    def fetch(self, source: FetchSource) -> list[RawPage]:
        """Acquire every location in ``source``, in order.

        Raises ``TooManyPagesError`` before issuing any request when the
        resolved count exceeds the ceiling, and ``SourceUnavailableError``
        when a location cannot be read.
        """
        ...
