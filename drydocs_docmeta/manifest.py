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

THEME — the shared metadata envelope field (G77, 2026-08-21). The two-corpus
architecture keeps the vendor and Confluence corpora EPISTEMICALLY SEPARATE
and lets them meet only through a shared metadata envelope; ``themes`` on a
:class:`PageRecord` is exactly such a field. It carries CONCEPT IRIs of the
lob-product-team ``skos:ConceptScheme`` — the same scheme the Control-M
folder-scope ``THEME`` token resolves into, through the same reader
(:mod:`drydocs_core.ontology.concept_scheme`) — so one vocabulary classifies
both corpora and the join is by IRI, never by label. THE DISCIPLINE: the join
is at the CLASSIFICATION, never the content. A document and a folder sharing
a theme are both ABOUT that subject; no edge between them follows from it,
and trust tiers do not merge because two things share a subject. Each page
also carries a three-way ``theme_status`` (C34 (c)): ``classified`` /
``unclassified`` (in scope, pending) / ``out_of_scope`` (External sources,
permanently) — kept apart so coverage never confuses backlog with scope.
Zero graph writes: the field, its validation, the split.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from drydocs_core.ontology.concept_scheme import (
    ConceptScheme,
    ThemeStatus,
    load_concept_scheme,
    theme_status,
)

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
    #: dcat:theme — concept IRIs (``<scheme>#<notation>``), never labels.
    #: Empty for an unclassified or out-of-scope page.
    themes: tuple[str, ...] = ()
    #: C34 (c): classified | unclassified | out_of_scope — see ThemeStatus.
    theme_status: str = ThemeStatus.UNCLASSIFIED.value


@dataclass(frozen=True)
class ThemeFinding:
    """A theme value the scheme does not know. RETURNED, never raised."""

    location: str
    value: str


@dataclass(frozen=True)
class ThemeCoverage:
    """The three populations reported APART (C34 (c)): ``unclassified`` is
    backlog, ``out_of_scope`` is not, and a single "untagged" number would
    make the difference unmeasurable."""

    classified: int = 0
    unclassified: int = 0
    out_of_scope: int = 0

    @property
    def total(self) -> int:
        return self.classified + self.unclassified + self.out_of_scope

    @property
    def in_scope(self) -> int:
        return self.classified + self.unclassified

    @property
    def ratio(self) -> float:
        """classified ÷ in-scope — coverage of the pages that can be classified."""
        return self.classified / self.in_scope if self.in_scope else 0.0


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
        themes: dict[str, list[str] | tuple[str, ...]] | None = None,
        scheme: ConceptScheme | None = None,
    ) -> CaptureManifest:
        """``themes`` maps a page location to its raw theme values (notations
        or IRIs). Values are resolved into the scheme at build time — a value
        the scheme does not know is DROPPED from the record and surfaced by
        :meth:`theme_findings` on the raw input, never raised — and every
        page gets its three-way status from :func:`theme_status`: an External
        source is out of scope whatever ``themes`` says."""
        resolver = scheme or (load_concept_scheme() if themes else None)
        records: list[PageRecord] = []
        for p in pages:
            raw_values = tuple((themes or {}).get(p.location, ()))
            resolution = resolver.resolve_all(raw_values) if (resolver and raw_values) else None
            status = theme_status(classification, resolution)
            records.append(
                PageRecord(
                    location=p.location,
                    sha256=sha256_bytes(p.body),
                    bytes=len(p.body),
                    content_type=p.content_type,
                    themes=resolution.iris
                    if (resolution and status is ThemeStatus.CLASSIFIED)
                    else (),
                    theme_status=status.value,
                )
            )
        return cls(
            source_id=source_id,
            connector=connector,
            captured_at=captured_at,
            corpus_id=corpus_id,
            classification=classification,
            trust=trust,
            invocation=scrub(invocation or {}),
            pages=records,
        )

    @staticmethod
    def theme_findings(
        themes: dict[str, list[str] | tuple[str, ...]] | None,
        scheme: ConceptScheme | None = None,
    ) -> list[ThemeFinding]:
        """Every raw theme value that does not resolve — the finding stream
        the build step drops from the record. Aliases suggest, values decide."""
        if not themes:
            return []
        resolver = scheme or load_concept_scheme()
        out: list[ThemeFinding] = []
        for location, values in themes.items():
            for bad in resolver.resolve_all(tuple(values)).unrecognised:
                out.append(ThemeFinding(location=location, value=bad))
        return out

    def theme_coverage(self) -> ThemeCoverage:
        """The split, reported — never a single number."""
        counts = {s.value: 0 for s in ThemeStatus}
        for page in self.pages:
            counts[page.theme_status] = counts.get(page.theme_status, 0) + 1
        return ThemeCoverage(
            classified=counts[ThemeStatus.CLASSIFIED.value],
            unclassified=counts[ThemeStatus.UNCLASSIFIED.value],
            out_of_scope=counts[ThemeStatus.OUT_OF_SCOPE.value],
        )

    # ---- persistence -------------------------------------------------------

    def write(self, directory: str | Path) -> Path:
        path = Path(directory) / MANIFEST_FILENAME
        path.parent.mkdir(parents=True, exist_ok=True)
        # sort_keys so two runs over identical content produce identical
        # files — a manifest that differs only by key order would make every
        # diff-based freshness check useless.
        # J49: LF is part of the determinism claim above — without it the same
        # manifest written on Windows and on Linux differs byte-for-byte, and the
        # diff-based freshness check would read a line-ending as a vendor edit.
        path.write_text(
            json.dumps(asdict(self), indent=2, sort_keys=True),
            encoding="utf-8",
            newline="\n",
        )
        return path

    @classmethod
    def read(cls, directory: str | Path) -> CaptureManifest:
        raw = json.loads((Path(directory) / MANIFEST_FILENAME).read_text(encoding="utf-8"))
        pages = []
        for p in raw.pop("pages", []):
            # pre-G77 manifests carry no theme fields; the defaults read them
            # as unclassified, which is the honest state for an unread page.
            p["themes"] = tuple(p.get("themes", ()))
            pages.append(PageRecord(**p))
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
