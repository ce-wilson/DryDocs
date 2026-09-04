"""Reader for the edition registry (CFG2; gate ontology-domain-registry-and-edition-grain §C1-§C4).

``config/taxonomy/editions.yaml`` declares the EDITIONS — the tenants of the id
space, each a short code that prefixes its ids (``[<EDITION>-]<MODULE><n>``, §C1)
and is cut at one Area Product (§C2, keyed by ``area_product_id``, the K5 §B key).

This module is how code reads it:

- :func:`load_registry` — the validated declaration (cached; ``reload`` for tests).
  Validation refuses rather than guesses: a malformed registry is a configuration
  error, never a silent fallback (the ``tom_role_vocabulary`` idiom).
- :func:`code_collisions` — the rule CFG2 (e) states: a code is unique, is never a
  module series code, never a frozen letter series and never ``DD``. The module
  series and the frozen set are handed IN (they live in ``modules.yaml`` and the
  allocator, which core does not import), so the check is a pure function a test
  can drive with the real sets or synthetic ones.
- :func:`unresolved_area_products` — real rows whose ``area_product_id`` is not in a
  supplied set of loaded ids. The graph read is the caller's (J18: the venue
  names itself); this function only compares.

The two registries never share (§A2): domains partition the vocabulary
(``drydocs_core.ontology.domain_registry``), editions partition the id space.
Pure config read, no graph write.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from drydocs_core.repo_paths import repo_root

_REPO_ROOT = repo_root(Path(__file__).resolve().parent.parent)
REGISTRY_FILE = _REPO_ROOT / "config" / "taxonomy" / "editions.yaml"

SCHEMA = "drydocs.editions.v1"
BASES: tuple[str, ...] = ("producer", "company")
#: 2-5 uppercase letters (§C1; CFG2 b). Three or more never collide with a frozen
#: letter series; two is allowed so a short real code is not refused on length.
CODE_RE = re.compile(r"^[A-Z]{2,5}$")
#: The company-side-only series the cross-repo convention reserved (git-readme.md,
#: 2026-07-20). Retired forward-only as a PARTITION rule (§C4); still never a code.
RESERVED_CODES: frozenset[str] = frozenset({"DD"})


class EditionRegistryError(RuntimeError):
    """A declaration that cannot be trusted — never a silent fallback."""


@dataclass(frozen=True)
class Edition:
    """One declared edition: the segment, the Area Product it is cut at, the ruling."""

    code: str
    title: str
    area_product_id: str
    minted_by: str
    registered_at: str
    authority: str
    legacy_band: int | None = None
    sample: bool = False
    note: str = ""


@dataclass(frozen=True)
class EditionRegistry:
    editions: tuple[Edition, ...]
    updated: str

    def codes(self) -> tuple[str, ...]:
        return tuple(e.code for e in self.editions)

    def by_code(self, code: str) -> Edition:
        for e in self.editions:
            if e.code == code:
                return e
        raise EditionRegistryError(
            f"undeclared edition {code!r} — declared: {sorted(self.codes())}"
        )

    def real(self) -> tuple[Edition, ...]:
        """The rows that name something: every row that is not a sample."""
        return tuple(e for e in self.editions if not e.sample)


def _str(raw: dict, key: str, row: str) -> str:
    value = raw.get(key)
    if value is None or str(value).strip() == "":
        raise EditionRegistryError(f"edition {row}: {key!r} is required")
    return str(value).strip()


def _row(raw: dict) -> Edition:
    if not isinstance(raw, dict):
        raise EditionRegistryError(f"an edition row must be a mapping, got {type(raw).__name__}")
    row = str(raw.get("code") or "<no code>")
    code = _str(raw, "code", row)
    if not CODE_RE.match(code):
        raise EditionRegistryError(
            f"edition {code!r}: a code is 2-5 UPPERCASE letters (the id segment, §C1)"
        )
    if code in RESERVED_CODES:
        raise EditionRegistryError(
            f"edition {code!r}: DD is the reserved company-side series, never an edition code"
        )
    minted_by = _str(raw, "minted_by", row)
    if minted_by not in BASES:
        raise EditionRegistryError(
            f"edition {code!r}: minted_by {minted_by!r} — an edition is declared by a BASE "
            f"{BASES} (§B2: a base mints, an instance requests)"
        )
    band = raw.get("legacy_band")
    legacy_band: int | None
    if band is None or str(band).strip() in ("", "~"):
        legacy_band = None
    else:
        try:
            legacy_band = int(band)
        except (TypeError, ValueError) as exc:
            raise EditionRegistryError(
                f"edition {code!r}: legacy_band must be an integer or null"
            ) from exc
    sample = raw.get("sample", False)
    if not isinstance(sample, bool):
        raise EditionRegistryError(f"edition {code!r}: sample must be an explicit boolean")
    return Edition(
        code=code,
        title=_str(raw, "title", row),
        area_product_id=_str(raw, "area_product_id", row),
        minted_by=minted_by,
        registered_at=_str(raw, "registered_at", row),
        authority=_str(raw, "authority", row),
        legacy_band=legacy_band,
        sample=sample,
        note=str(raw.get("note") or "").strip(),
    )


def code_collisions(
    editions: tuple[Edition, ...] | list[Edition],
    *,
    module_series: dict[str, str] | None = None,
    frozen_series: dict[str, int] | set[str] | None = None,
) -> list[str]:
    """CFG2 (e) as a pure function: the codes that are not usable as an id segment,
    each with its reason. Empty means every code is clear."""
    problems: list[str] = []
    seen: set[str] = set()
    modules = {v.upper(): k for k, v in (module_series or {}).items()}
    frozen = {s.upper() for s in (frozen_series or ())}
    for e in editions:
        if e.code in seen:
            problems.append(f"{e.code}: declared twice")
        seen.add(e.code)
        if e.code in modules:
            problems.append(f"{e.code}: is the series code of module {modules[e.code]!r}")
        if e.code in frozen:
            problems.append(f"{e.code}: is a FROZEN legacy series")
        if e.code in RESERVED_CODES:
            problems.append(f"{e.code}: reserved (DD)")
    return problems


def unresolved_area_products(
    editions: tuple[Edition, ...] | list[Edition], loaded_ids: set[str]
) -> list[tuple[str, str]]:
    """``(code, area_product_id)`` for every REAL row whose Area Product is not in
    ``loaded_ids``. Samples are invented by construction and never checked."""
    return [
        (e.code, e.area_product_id)
        for e in editions
        if not e.sample and e.area_product_id not in loaded_ids
    ]


def _load(path: Path) -> EditionRegistry:
    import yaml

    if not path.is_file():
        raise EditionRegistryError(
            f"the edition registry is missing: {path}. The id grammar's edition segment "
            "is declared THERE (gate ontology-domain-registry-and-edition-grain §C3); an "
            "undeclared segment is a typo, not a tenant."
        )
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if doc.get("schema") != SCHEMA:
        raise EditionRegistryError(f"{path}: schema must be {SCHEMA!r}, got {doc.get('schema')!r}")
    rows = [_row(raw) for raw in (doc.get("editions") or [])]
    dupes = code_collisions(rows)
    if dupes:
        raise EditionRegistryError("; ".join(dupes))
    return EditionRegistry(editions=tuple(rows), updated=str(doc.get("updated") or ""))


_CACHE: dict[Path, EditionRegistry] = {}


def load_registry(path: Path | None = None, *, reload: bool = False) -> EditionRegistry:
    """The validated registry, cached per path (the file changes only with a commit)."""
    target = path or REGISTRY_FILE
    if reload or target not in _CACHE:
        _CACHE[target] = _load(target)
    return _CACHE[target]
