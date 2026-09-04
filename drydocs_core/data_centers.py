"""Reader for the data-center spelling registry (LOAD2; RELAY-25, the company's P6 finding).

One ``--data-center`` value has to reach two families of psgmgr tables that spell a
data center differently: ``CM_DEF_VTAB.DATA_CENTER`` carries the SHORT Control-M server
code (folders, and the folder-joined jobs and variables extracts) while
``CM_HOSTS.DATA_CENTER`` and ``CM_AVG_RUN.DATA_CENTER`` carry the LONG-form name. A
long-form value against the VTAB family returns zero rows and reads as an empty data
center rather than as an error — the failure this module exists to remove.

- :func:`load_registry` — the validated declaration (cached; ``reload`` for tests). Reads
  the INTERNAL TWIN when it is present and the publishable sample otherwise, and records
  which on :attr:`DataCenterRegistry.source` so a caller can name its venue (J18).
- :func:`resolve` — one operator value to the pair of spellings, or a refusal that names
  both domains. Never computes one spelling from the other: the long form carries the
  default-time and suffix segments that the short code does not contain, so short → long
  is not derivable and the pairing is a declared fact (LOAD2 c).

Pure config read, no graph write, no database.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from drydocs_core.repo_paths import repo_root

_REPO_ROOT = repo_root(Path(__file__).resolve().parent.parent)
#: The publishable, synthetic sample — the SHAPE, producer-side.
REGISTRY_FILE = _REPO_ROOT / "config" / "taxonomy" / "data-centers.yaml"
#: The J13 twin: the real inventory, machine-local, never tracked.
INTERNAL_TWIN = _REPO_ROOT / "internal" / "controlm-config" / "data-centers.yaml"

SCHEMA = "drydocs.data-centers.v1"


class DataCenterError(RuntimeError):
    """A declaration that cannot be trusted, or a value in neither domain."""


@dataclass(frozen=True)
class DataCenter:
    """One data center, in both spellings."""

    code: str  # SHORT — CM_DEF_VTAB.DATA_CENTER
    name: str  # LONG — CM_HOSTS / CM_AVG_RUN
    default_time: str = ""
    suffix: str = ""
    sample: bool = False
    note: str = ""


@dataclass(frozen=True)
class DataCenterRegistry:
    data_centers: tuple[DataCenter, ...]
    updated: str = ""
    #: ``"internal-twin"`` or ``"publishable-sample"`` — the venue a claim names (J18).
    source: str = "publishable-sample"

    def codes(self) -> tuple[str, ...]:
        return tuple(d.code for d in self.data_centers)

    def names(self) -> tuple[str, ...]:
        return tuple(d.name for d in self.data_centers)

    def real(self) -> tuple[DataCenter, ...]:
        return tuple(d for d in self.data_centers if not d.sample)


def _row(raw: dict) -> DataCenter:
    if not isinstance(raw, dict):
        raise DataCenterError(f"a data-center row must be a mapping, got {type(raw).__name__}")
    code = str(raw.get("code") or "").strip()
    name = str(raw.get("name") or "").strip()
    if not code or not name:
        raise DataCenterError(
            f"data-center row {raw!r}: both `code` (short) and `name` (long) are required — "
            "the PAIRING is the fact this registry declares"
        )
    sample = raw.get("sample", False)
    if not isinstance(sample, bool):
        raise DataCenterError(f"data center {code!r}: sample must be an explicit boolean")
    return DataCenter(
        code=code,
        name=name,
        default_time=str(raw.get("default_time") or "").strip(),
        suffix=str(raw.get("suffix") or "").strip(),
        sample=sample,
        note=str(raw.get("note") or "").strip(),
    )


def _load(path: Path, *, source: str) -> DataCenterRegistry:
    import yaml

    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if doc.get("schema") != SCHEMA:
        raise DataCenterError(f"{path}: schema must be {SCHEMA!r}, got {doc.get('schema')!r}")
    rows = [_row(raw) for raw in (doc.get("data_centers") or [])]
    for field, values in (("code", [d.code for d in rows]), ("name", [d.name for d in rows])):
        dupes = sorted({v for v in values if values.count(v) > 1})
        if dupes:
            raise DataCenterError(f"{path}: duplicate {field}(s) {dupes} — the pairing must be 1:1")
    return DataCenterRegistry(
        data_centers=tuple(rows), updated=str(doc.get("updated") or ""), source=source
    )


_CACHE: dict[Path, DataCenterRegistry] = {}


def load_registry(path: Path | None = None, *, reload: bool = False) -> DataCenterRegistry:
    """The validated registry: the INTERNAL TWIN where it exists, else the publishable
    sample. An explicit ``path`` overrides both (tests, and a declared override)."""
    if path is None:
        path = INTERNAL_TWIN if INTERNAL_TWIN.is_file() else REGISTRY_FILE
    source = "internal-twin" if path == INTERNAL_TWIN else "publishable-sample"
    if reload or path not in _CACHE:
        if not path.is_file():
            raise DataCenterError(
                f"the data-center registry is missing: {path}. The short/long pairing is "
                "declared THERE (LOAD2 c); it is never computed from the string."
            )
        _CACHE[path] = _load(path, source=source)
    return _CACHE[path]


def resolve(value: str, registry: DataCenterRegistry | None = None) -> DataCenter:
    """One operator ``--data-center`` value to both spellings.

    Matches the SHORT code or the LONG name, case-insensitively and exactly — a value in
    neither domain is REFUSED with both spellings named, because the alternative (passing
    it through) is the silent zero-row result this item removes. A LIKE pattern is not
    resolvable here and is the caller's to handle.
    """
    reg = registry or load_registry()
    needle = (value or "").strip().casefold()
    for d in reg.data_centers:
        if needle in (d.code.casefold(), d.name.casefold()):
            return d
    raise DataCenterError(
        f"--data-center {value!r} matches neither spelling in the registry "
        f"({reg.source}). SHORT codes (CM_DEF_VTAB — folders/jobs/variables): "
        f"{sorted(reg.codes())}. LONG names (CM_HOSTS/CM_AVG_RUN): {sorted(reg.names())}. "
        "Pass one of these; the run binds the other spelling for you."
    )
