"""Per-run capture manifests — the freshness primitive.

A manifest records what was acquired, from where, and what its bytes hashed
to. That digest is what ADR 0006 §4's gate-preserving freshness rule turns on:
a changed sha256 RE-QUEUES curation rather than silently overwriting confirmed
content, because a vendor edit can invalidate everything derived from the old
text. Without a per-page digest recorded at capture time there is nothing to
compare a refetch against, so this is the module the whole refresh story rests
on rather than bookkeeping.

The digest is taken over the RAW BYTES, not the cleaned text. Cleaning is our
transformation, so hashing after it would mean a cleaner change looked
identical to a vendor edit — the two things freshness must tell apart.

The manifest also carries a scrubbed per-run invocation record (the bkup
``prompts.json`` pattern): what was asked for, never any credential.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .connectors.base import RawPage

MANIFEST_FILENAME = "capture-manifest.json"
SCHEMA = "drydocs.docmeta-manifest.v1"


def sha256_bytes(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


@dataclass(frozen=True)
class PageRecord:
    location: str
    sha256: str
    bytes: int
    content_type: str | None = None


@dataclass
class CaptureManifest:
    """One acquisition run, as a receipt."""

    source_id: str
    connector: str
    captured_at: str
    #: The doc-source-registry corpus this run belongs to. Recorded HERE, at
    #: capture time, so downstream stages never have to derive it from a
    #: capture id — the Q13 defect, generalized: a capture is not a corpus.
    corpus_id: str | None = None
    classification: str | None = None
    trust: str | None = None
    invocation: dict[str, str] = field(default_factory=dict)
    pages: list[PageRecord] = field(default_factory=list)
    schema: str = SCHEMA

    @classmethod
    def build(
        cls,
        *,
        source_id: str,
        connector: str,
        captured_at: str,
        pages: list[RawPage],
        corpus_id: str | None = None,
        classification: str | None = None,
        trust: str | None = None,
        invocation: dict[str, str] | None = None,
    ) -> CaptureManifest:
        return cls(
            source_id=source_id,
            connector=connector,
            captured_at=captured_at,
            corpus_id=corpus_id,
            classification=classification,
            trust=trust,
            invocation=scrub(invocation or {}),
            pages=[
                PageRecord(
                    location=p.location,
                    sha256=sha256_bytes(p.body),
                    bytes=len(p.body),
                    content_type=p.content_type,
                )
                for p in pages
            ],
        )

    # ---- persistence -------------------------------------------------------

    def write(self, directory: str | Path) -> Path:
        path = Path(directory) / MANIFEST_FILENAME
        path.parent.mkdir(parents=True, exist_ok=True)
        # sort_keys so two runs over identical content produce identical
        # files — a manifest that differs only by key order would make every
        # diff-based freshness check useless.
        path.write_text(
            json.dumps(asdict(self), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return path

    @classmethod
    def read(cls, directory: str | Path) -> CaptureManifest:
        raw = json.loads((Path(directory) / MANIFEST_FILENAME).read_text(encoding="utf-8"))
        pages = [PageRecord(**p) for p in raw.pop("pages", [])]
        return cls(**raw, pages=pages)

    # ---- freshness ---------------------------------------------------------

    def digests(self) -> dict[str, str]:
        return {p.location: p.sha256 for p in self.pages}

    def diff(self, previous: CaptureManifest) -> DigestDiff:
        """What changed since ``previous`` — the input to the re-gate queue."""
        now, before = self.digests(), previous.digests()
        return DigestDiff(
            added=tuple(sorted(now.keys() - before.keys())),
            removed=tuple(sorted(before.keys() - now.keys())),
            changed=tuple(sorted(k for k in now.keys() & before.keys() if now[k] != before[k])),
            unchanged=tuple(sorted(k for k in now.keys() & before.keys() if now[k] == before[k])),
        )


@dataclass(frozen=True)
class DigestDiff:
    added: tuple[str, ...]
    removed: tuple[str, ...]
    changed: tuple[str, ...]
    unchanged: tuple[str, ...]

    @property
    def needs_regate(self) -> tuple[str, ...]:
        """Pages whose curation must be re-queued (ADR 0006 §4).

        Additions ride along with changes: a page nobody has seen has no
        confirmed curation record either, so treating it as "not a change"
        would let it into the graph ungated.
        """
        return tuple(sorted((*self.added, *self.changed)))

    def __bool__(self) -> bool:
        return bool(self.added or self.removed or self.changed)


#: Substrings that mark a key as carrying a secret. Matched case-insensitively
#: against the KEY, never the value — a value-sniffing scrubber both misses
#: things and mangles legitimate content.
_SECRET_HINTS = ("password", "token", "secret", "key", "credential", "auth", "cookie")


def scrub(invocation: dict[str, str]) -> dict[str, str]:
    """Redact anything that looks like a credential before it is written.

    The invocation record exists so a run is reproducible and auditable; it is
    not a place for secrets, and this repo's rule is architecture-level only —
    no real values in committed or persisted artifacts.
    """
    return {
        k: ("<redacted>" if any(h in k.lower() for h in _SECRET_HINTS) else v)
        for k, v in invocation.items()
    }
