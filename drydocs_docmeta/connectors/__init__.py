"""Acquisition connectors — fetch raw pages, and nothing else.

The two generic connectors shipped here (``web``, ``filedrop``) are the pair
that has ZERO internal dependencies and is therefore offline-testable in this
repo. ``confluence``, ``sharepoint``, ``teams`` and ``email`` are company-side
implementations behind the same protocol (docmeta plan §6) — the producer
ships the interface, not a stub that pretends to work.
"""

from __future__ import annotations

from .base import Connector, RawPage, SourceUnavailableError
from .filedrop import FiledropConnector
from .web import WebConnector

__all__ = [
    "Connector",
    "FiledropConnector",
    "RawPage",
    "SourceUnavailableError",
    "WebConnector",
]
