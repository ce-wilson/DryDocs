"""``filedrop`` — read documents already on this machine.

The backfill path: content that arrives as files rather than over a network —
an export someone dropped on a share, a PDF-adjacent markdown conversion, the
``internal/`` transcriptions. A location is a file OR a directory; a directory
is read one level of ``rglob`` deep and filtered to the extensions this
connector admits, in sorted order so two runs over the same tree produce the
same page order and therefore the same manifest.

It does NOT walk outside the locations it was handed, and it does not follow
symlinks out of them — the filesystem equivalent of the web connector's
allow-list.
"""

from __future__ import annotations

from pathlib import Path

from drydocs_core.run_log import batch_run_log

from ..policy import CapturePolicy
from .base import FetchSource, RawPage, SourceUnavailableError

#: What a document corpus may consist of. PDFs are deliberately absent: they
#: need an extraction step with its own provenance label (the pypdf precedent),
#: so admitting them here would let a lossy extraction masquerade as a
#: verbatim read.
ADMITTED_SUFFIXES: frozenset[str] = frozenset({".md", ".txt", ".html", ".htm"})


class FiledropConnector:
    """Reads local files. Acquisition only."""

    name = "filedrop"

    def __init__(self, *, policy: CapturePolicy | None = None) -> None:
        self.policy = policy or CapturePolicy.load()

    def _fetch(self, source: FetchSource) -> list[RawPage]:
        paths = self._resolve(source)
        # Same pre-flight discipline as the web connector: a filedrop that
        # resolves to thousands of files is as much an unsized run as a scrape,
        # and the count is equally knowable in advance.
        self.policy.enforce_ceiling(len(paths), max_pages=source.max_pages)
        return [
            RawPage(
                location=str(p),
                body=p.read_bytes(),
                content_type=self._content_type(p),
                meta={"suffix": p.suffix.lower()},
            )
            for p in paths
        ]

    def fetch(self, source: FetchSource) -> list[RawPage]:
        """One acquisition batch, wrapped in a run log (G107).

        Delegates to :meth:`_fetch` unchanged — this records that the batch ran
        and what it acquired; it does not change what is fetched. Keeps the
        public name so the ``Connector`` protocol is still satisfied.
        """
        with batch_run_log(
            "docmeta.filedrop",
            source=source.id,
            meta={"connector": "FiledropConnector"},
        ) as summary:
            pages = self._fetch(source)
            summary["pages fetched"] = len(pages)
            summary["bytes fetched"] = sum(len(page.body) for page in pages)
            return pages

    def _resolve(self, source: FetchSource) -> list[Path]:
        found: list[Path] = []
        for location in source.locations:
            path = Path(location)
            if path.is_dir():
                found.extend(
                    sorted(
                        p
                        for p in path.rglob("*")
                        if p.is_file() and p.suffix.lower() in ADMITTED_SUFFIXES
                    )
                )
            elif path.is_file():
                if path.suffix.lower() not in ADMITTED_SUFFIXES:
                    raise SourceUnavailableError(
                        f"{path} has suffix {path.suffix!r}, which filedrop does not admit "
                        f"({sorted(ADMITTED_SUFFIXES)}). A format needing extraction gets its "
                        f"own stage so the lossy step keeps a provenance label."
                    )
                found.append(path)
            else:
                raise SourceUnavailableError(f"no such file or directory: {location}")
        return found

    @staticmethod
    def _content_type(path: Path) -> str:
        return {
            ".md": "text/markdown",
            ".txt": "text/plain",
            ".html": "text/html",
            ".htm": "text/html",
        }[path.suffix.lower()]
