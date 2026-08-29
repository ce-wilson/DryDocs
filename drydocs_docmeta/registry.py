"""Typed view over ``config/doc-source-registry.yaml`` + the curation ladder.

READ-ONLY, and deliberately not a second source of truth: the YAML is the
ledger and ``tests/unit/test_doc_registry.py`` is its schema guard. This module
gives the component a typed handle on the same rows plus the two ladders the
bkup scrapers carried, which had no home in the YAML because they describe a
DOCUMENT's state rather than a SOURCE's declaration.

WHAT A REGISTRY ENTRY DOES NOT SAY: which pages to fetch. That comes from the
publisher's own manifest, resolved before any request — the property that makes
the Q12 ceiling exact. The entry governs (classification, tier, curation,
target database); it does not enumerate.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from drydocs_core.repo_paths import repo_root

from .connectors.base import FetchSource

_REPO_ROOT = repo_root(Path(__file__).resolve().parents[1])
DEFAULT_LEDGER_PATH = _REPO_ROOT / "config" / "doc-source-registry.yaml"
SCHEMA = "drydocs.doc-source-registry.v1"

#: ADR 0006 §4 — the curation ladder is FIXED per tier, not chosen per entry.
#: An entry cannot soften its own gate, which is the whole reason the ladder
#: is derived rather than declared.
CURATION_BY_TIER: dict[str, str] = {
    "T1": "none",  # public vendor documentation — nothing to confirm
    "T2": "sme-confirm",
    "T3": "sme-confirm",
    "T4": "sme-confirm",  # J23 retired the +confidential rider with the tier collapse
}

#: The bkup curation vocabulary mapped onto this repo's HITL gate states
#: (docmeta plan §5). The bkup words survive because company-side records
#: already carry them; what changes is that they now MEAN a gate position.
CURATION_STATUS_TO_GATE: dict[str, str] = {
    "unapproved": "pre-gate",
    "ai_generated_review_needed": "gate-queued",
    "approved_by_sme": "confirmed",
}

#: The ``last_synced_from`` authority ladder, weakest first. A sync from a
#: WEAKER authority must never overwrite what a stronger one wrote — the
#: bootstrap pass re-running should not undo an SME's manual correction.
SYNC_AUTHORITY: tuple[str, ...] = ("bootstrap", "manual", "jet")


class UnknownDocSourceError(KeyError):
    """No ledger entry with that id."""


def outranks(candidate: str, incumbent: str | None) -> bool:
    """Whether ``candidate`` may overwrite what ``incumbent`` synced.

    Unknown authorities rank below every known one rather than raising: an
    unrecognized label is a reason to be conservative, not to crash a sync.
    """
    if incumbent is None:
        return True
    rank = {name: i for i, name in enumerate(SYNC_AUTHORITY)}
    return rank.get(candidate, -1) > rank.get(incumbent, -1)


@dataclass(frozen=True)
class DocSourceEntry:
    """One governed document corpus."""

    id: str
    classification: str
    connector: str
    tier: str
    curation: str
    target_db: str
    refresh: str
    trust_default: str
    confirmed: bool
    data: dict[str, Any]

    @property
    def source_url(self) -> str | None:
        return self.data.get("source_url")

    @property
    def captured_at(self) -> str | None:
        captured = self.data.get("captured_at")
        return None if captured is None else str(captured)

    @property
    def manifest(self) -> str | None:
        return self.data.get("manifest")

    @property
    def graph_locator(self) -> dict[str, Any]:
        return self.data.get("graph_locator") or {"match": "none", "value": None}

    @property
    def required_curation(self) -> str:
        """What the ladder demands for this tier, whatever the entry says."""
        return CURATION_BY_TIER[self.tier]

    @property
    def needs_sme_confirmation(self) -> bool:
        return self.required_curation != "none"

    def fetch_source(
        self, locations: tuple[str, ...] | list[str], *, max_pages: int | None = None
    ) -> FetchSource:
        """Build the connector request for an already-resolved page list."""
        return FetchSource(id=self.id, locations=tuple(locations), max_pages=max_pages)


def load_doc_sources(path: str | Path | None = None) -> dict[str, DocSourceEntry]:
    """Parse the ledger into typed entries, keyed by id."""
    raw = yaml.safe_load(Path(path or DEFAULT_LEDGER_PATH).read_text(encoding="utf-8"))
    if raw.get("schema") != SCHEMA:
        raise ValueError(f"expected schema {SCHEMA}, got {raw.get('schema')!r}")
    entries: dict[str, DocSourceEntry] = {}
    for row in raw.get("sources") or []:
        entry = DocSourceEntry(
            id=row["id"],
            classification=row["classification"],
            connector=row["connector"],
            tier=row["tier"],
            curation=row["curation"],
            target_db=row["target_db"],
            refresh=row["refresh"],
            trust_default=row["trust_default"],
            confirmed=bool(row.get("confirmed", False)),
            data=row,
        )
        if entry.id in entries:
            raise ValueError(f"duplicate doc-source id {entry.id!r}")
        entries[entry.id] = entry
    return entries


class AmbiguousDocSourceError(LookupError):
    """A --purpose string matched more than one ledger row (Q23 — the run
    must name exactly one row; the SME picking by hand is the removed case)."""


def resolve_capture_registry_id(
    registry_id: str | None = None,
    *,
    purpose: str | None = None,
    path: str | Path | None = None,
) -> DocSourceEntry:
    """Q23: the run <-> row join, ONE resolver for both capture doors.

    A capture run must be able to say WHICH doc-source-registry row it
    fulfils — the 7c18ff4b port review found a VERBATIM upgrade whose run was
    keyed by a Confluence space plus a free-text purpose, neither a registry
    id, so the SME had to pick the row by hand. This function is the removal
    of that case: an explicit ``registry_id`` must exist
    (:class:`UnknownDocSourceError` otherwise); a ``purpose`` free-text must
    match EXACTLY ONE row across id/source/notes
    (:class:`AmbiguousDocSourceError` names every candidate otherwise);
    neither given is an error, never a warning — a run that cannot name its
    row does not run.
    """
    if registry_id:
        return get(registry_id, path)
    if purpose:
        needle = purpose.strip().lower()
        if needle:
            entries = load_doc_sources(path)
            hits = [
                e
                for sid, e in sorted(entries.items())
                if needle in sid.lower()
                or needle in str(e.data.get("source", "")).lower()
                or needle in str(e.data.get("notes", "")).lower()
            ]
            if len(hits) == 1:
                return hits[0]
            if not hits:
                raise UnknownDocSourceError(
                    f"purpose {purpose!r} matches no doc-source-registry row — "
                    "register the corpus first (docmeta invariant 1)"
                )
            raise AmbiguousDocSourceError(
                f"purpose {purpose!r} matches {len(hits)} rows "
                f"({[e.id for e in hits]}) — pass --registry-id to name exactly one"
            )
    raise UnknownDocSourceError(
        "no registry id and no resolvable purpose — a capture run that cannot "
        "say which doc-source-registry row it fulfils does not run (Q23)"
    )


def get(source_id: str, path: str | Path | None = None) -> DocSourceEntry:
    try:
        return load_doc_sources(path)[source_id]
    except KeyError as exc:
        raise UnknownDocSourceError(
            f"{source_id!r} is not in config/doc-source-registry.yaml — register the corpus "
            f"before ingesting it (docmeta invariant 1)"
        ) from exc
