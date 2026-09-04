"""Reader for the domain registry (CFG1; gate ontology-domain-registry-and-edition-grain §B1-§B3).

``config/taxonomy/domains.yaml`` is the ONE surface that says which ontology
domains exist. Until 2026-09-04 that fact lived in a comment block in
``00-header.yaml`` and a closed enum in ``relationship-vocabulary.schema.json``,
and "registered" meant somebody edited the comment. This module is how code reads
the registry:

- :func:`load_registry` — the validated declaration (cached; ``reload`` for tests).
  Validation refuses rather than guesses, the ``tom_role_vocabulary`` idiom: a
  malformed registry is a configuration error, never a silent fallback.
- :meth:`DomainRegistry.active_ids` — what a vocabulary entry's ``domain:`` may be.

Two rules the reader ENFORCES because the gate ruled them and a rule nobody is
forced to obey rots into prose:

- **§B3 — ``vocabulary_fragment`` is REQUIRED.** A domain is a file/loader
  partition of the vocabulary and nothing else; a row without a fragment fails.
- **§B5 rider — the ontology is COMMON and BASE-OWNED.** A base (``producer``,
  ``company``) mints; an edition (any other ``minted_by``) EXTENDS and never
  overrides: an edition row may not reuse a base id, and a base row is never
  superseded by an edition row. Both refusals are proven by a synthetic edition
  fixture in ``tests/unit/test_domain_registry.py`` — no edition row exists in
  this repo and none will (CFG2 c), so a guard with no positive case here would
  first run unobserved at the company (review F7).

Pure config read, no graph write — the ``concept_scheme.py`` precedent.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from drydocs_core.repo_paths import repo_root

_REPO_ROOT = repo_root(Path(__file__).resolve().parent.parent.parent)
REGISTRY_FILE = _REPO_ROOT / "config" / "taxonomy" / "domains.yaml"
VOCABULARY_DIR = _REPO_ROOT / "drydocs_core" / "ontology" / "relationship_vocabulary"

SCHEMA = "drydocs.domains.v1"
#: The bases — everything else in ``minted_by`` is an EDITION code (§B2).
BASES: tuple[str, ...] = ("producer", "company")
STATUSES: tuple[str, ...] = ("active", "deprecated")
AUTHORITY_STATUSES: tuple[str, ...] = ("signed", "pending")


class DomainRegistryError(RuntimeError):
    """A declaration that cannot be trusted — never a silent fallback."""


@dataclass(frozen=True)
class Domain:
    """One registered domain: the partition and the ruling that made it one."""

    id: str
    title: str
    vocabulary_fragment: str
    minted_by: str
    registered_at: str
    authority: str
    status: str
    authority_status: str = "signed"
    superseded_by: str | None = None
    note: str = ""

    @property
    def is_base(self) -> bool:
        return self.minted_by in BASES

    @property
    def active(self) -> bool:
        return self.status == "active"


@dataclass(frozen=True)
class DomainRegistry:
    """The declaration."""

    domains: tuple[Domain, ...]
    updated: str

    def by_id(self, domain_id: str) -> Domain:
        for d in self.domains:
            if d.id == domain_id:
                return d
        raise DomainRegistryError(
            f"unregistered domain {domain_id!r} — registered: {sorted(self.ids())}"
        )

    def ids(self) -> tuple[str, ...]:
        return tuple(d.id for d in self.domains)

    def active_ids(self) -> tuple[str, ...]:
        return tuple(d.id for d in self.domains if d.active)

    def fragment_for(self, domain_id: str) -> Path:
        return VOCABULARY_DIR / self.by_id(domain_id).vocabulary_fragment


def _str(raw: dict, key: str, row: str) -> str:
    value = raw.get(key)
    if value is None or str(value).strip() == "":
        raise DomainRegistryError(f"domain {row}: {key!r} is required")
    return str(value).strip()


def _row(raw: dict) -> Domain:
    if not isinstance(raw, dict):
        raise DomainRegistryError(f"a domain row must be a mapping, got {type(raw).__name__}")
    row = str(raw.get("id") or "<no id>")
    domain_id = _str(raw, "id", row)
    status = _str(raw, "status", row)
    if status not in STATUSES:
        raise DomainRegistryError(f"domain {row}: unknown status {status!r} — {STATUSES}")
    authority_status = str(raw.get("authority_status") or "signed").strip()
    if authority_status not in AUTHORITY_STATUSES:
        raise DomainRegistryError(
            f"domain {row}: unknown authority_status {authority_status!r} — {AUTHORITY_STATUSES}"
        )
    superseded_by = raw.get("superseded_by")
    superseded_by = str(superseded_by).strip() if superseded_by else None
    if status == "deprecated" and not superseded_by:
        raise DomainRegistryError(
            f"domain {row}: a deprecated domain names its successor (superseded_by) — "
            "the G87 shape, add-new + deprecate-old, never a bare removal"
        )
    if status == "active" and superseded_by:
        raise DomainRegistryError(
            f"domain {row}: active with superseded_by — deprecate it or drop the field"
        )
    return Domain(
        id=domain_id,
        title=_str(raw, "title", row),
        # §B3: REQUIRED. A domain is a partition of the vocabulary and nothing else.
        vocabulary_fragment=_str(raw, "vocabulary_fragment", row),
        minted_by=_str(raw, "minted_by", row),
        registered_at=_str(raw, "registered_at", row),
        authority=_str(raw, "authority", row),
        status=status,
        authority_status=authority_status,
        superseded_by=superseded_by,
        note=str(raw.get("note") or "").strip(),
    )


def validate_rows(rows: list[Domain]) -> None:
    """The cross-row rules. Separate from :func:`_load` so a test can hand in a
    synthetic edition row and watch each refusal fire."""
    seen: dict[str, Domain] = {}
    for d in rows:
        if d.id in seen:
            first = seen[d.id]
            if first.is_base != d.is_base:
                edition = d if not d.is_base else first
                raise DomainRegistryError(
                    f"domain {d.id!r}: edition {edition.minted_by!r} reuses a BASE id — "
                    "the ontology is common and base-owned (§B5 rider): an edition "
                    "extends the registry with its own ids and never overrides a base row"
                )
            raise DomainRegistryError(f"duplicate domain id {d.id!r}")
        seen[d.id] = d
    for d in rows:
        if d.superseded_by is None:
            continue
        successor = seen.get(d.superseded_by)
        if successor is None:
            raise DomainRegistryError(
                f"domain {d.id!r}: superseded_by {d.superseded_by!r} is not a registered domain"
            )
        if d.is_base and not successor.is_base:
            raise DomainRegistryError(
                f"domain {d.id!r}: a BASE row superseded by edition row {successor.id!r} "
                f"(minted_by {successor.minted_by!r}) — a base row is never deprecated "
                "by an edition (§B5 rider); the base deprecates its own"
            )


def _load(path: Path) -> DomainRegistry:
    import yaml

    if not path.is_file():
        raise DomainRegistryError(
            f"the domain registry is missing: {path}. The vocabulary's domain axis is "
            "declared THERE (gate ontology-domain-registry-and-edition-grain §B1), so a "
            "missing file is a configuration error, not a reason to fall back to the "
            "header comment — that is the state CFG1 removed."
        )
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if doc.get("schema") != SCHEMA:
        raise DomainRegistryError(f"{path}: schema must be {SCHEMA!r}, got {doc.get('schema')!r}")
    raw_rows = doc.get("domains") or []
    if not raw_rows:
        raise DomainRegistryError(
            f"{path} declares no domains — an empty registry is never what was meant"
        )
    rows = [_row(raw) for raw in raw_rows]
    validate_rows(rows)
    return DomainRegistry(domains=tuple(rows), updated=str(doc.get("updated") or ""))


_CACHE: dict[Path, DomainRegistry] = {}


def load_registry(path: Path | None = None, *, reload: bool = False) -> DomainRegistry:
    """The validated registry, cached per path (the file changes only with a commit)."""
    target = path or REGISTRY_FILE
    if reload or target not in _CACHE:
        _CACHE[target] = _load(target)
    return _CACHE[target]
