"""Pluggable publisher interface + offline implementations.

The real Confluence push (space coordinates, auth, the internal wrapper) is
deliberately **not** in this public template — a company profile provides a
``ConfluencePublisher`` implementing :class:`Publisher` in its gitignored twin. The
template ships only offline publishers so the pipeline is testable without any
external service or credentials.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class PublishResult:
    title: str
    location: str          # a URL/path/uri identifying where it went
    published: bool


@runtime_checkable
class Publisher(Protocol):
    def publish(self, *, title: str, body: str, space: str | None = None) -> PublishResult: ...


@dataclass
class NoopPublisher:
    """Records what *would* be published without sending anything anywhere."""

    sent: list[PublishResult] = field(default_factory=list)

    def publish(self, *, title: str, body: str, space: str | None = None) -> PublishResult:
        result = PublishResult(title=title, location=f"noop://{space or 'preview'}/{title}", published=False)
        self.sent.append(result)
        return result


@dataclass
class LocalPublisher:
    """Writes each page to ``out_dir`` as a local file (offline 'publish')."""

    out_dir: Path

    def __post_init__(self) -> None:
        self.out_dir = Path(self.out_dir)

    def publish(self, *, title: str, body: str, space: str | None = None) -> PublishResult:
        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in title) or "page"
        path = self.out_dir / (safe + ".html")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return PublishResult(title=title, location=path.as_uri(), published=True)
