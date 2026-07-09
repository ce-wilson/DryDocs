"""Typed accessor over ``config/source-mappings/<source-id>.yaml`` — the per-source
COLUMN LEDGER (doc 08): which columns of a wide source table we PROJECT into the
graph/staging, which are FILTER-ONLY (used in a WHERE clause, never landed), which
are EXCLUDED (a deliberate no — ``reason: scope | sensitivity | junk | duplicate``),
and which are DEFERRED (a named future use).

Pure config layer — **no Neo4j, no graph writes**. Schema ``drydocs.source-mapping.v1``.
The committed ``controlm-psgmgr.yaml`` ledger is TRANSCRIBED from already-decided
sources: the five ``drydocs/loaders/sql/controlm_*.sql`` projections, the
``controlm-q1q3-phase1`` gate, ``config/audit-fields.yaml``, and doc 06a's SME
resolutions — never invented here. See
``docs/restructure/08-source-column-mappings.md`` for the full design.

Design note (MODULE_MAP): parked in the ``drydocs-review`` component alongside
``review_labels.py`` — the same kind of typed-config accessor. Promote to
``drydocs_core.config`` only if a non-review second consumer appears (ADR 0002-a
resolve-at-move rule).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE_MAPPINGS_DIR = _REPO_ROOT / "config" / "source-mappings"

SCHEMA_ID = "drydocs.source-mapping.v1"

VALID_DISPOSITIONS: frozenset[str] = frozenset(
    {"projected", "filter-only", "excluded", "deferred"}
)
VALID_ORIGINS: frozenset[str] = frozenset({"source", "derived"})
VALID_EXCLUDED_REASONS: frozenset[str] = frozenset(
    {"scope", "sensitivity", "junk", "duplicate"}
)


class SourceMappingError(RuntimeError):
    """A source-mapping YAML file is malformed or missing required structure."""


class UnknownMappingObjectError(KeyError):
    """An object name not declared in the mapping file."""


@dataclass(frozen=True)
class ColumnDisposition:
    """One profiled column's disposition: where it lands, or why it doesn't.

    ``disposition`` — projected (lands in staging/graph) | filter-only (used in
    WHERE, never projected) | excluded (deliberate no; ``reason`` required) |
    deferred (known future use).

    ``target`` — ``Label.property`` for graph-bound columns, ``staging:<field>``
    for staging-only columns (never promoted to a node/edge property).

    ``origin`` — ``source`` (the raw column value) | ``derived`` (computed).
    ``derived_also`` records a second, transformed landing (e.g. ``employee_sid``)
    alongside the primary one, per the gate-page vocabulary.
    """

    name: str
    disposition: str
    origin: str | None = None
    target: str | None = None
    note: str | None = None
    reason: str | None = None
    decided_by: str | None = None
    derived_also: dict[str, Any] | None = None


@dataclass(frozen=True)
class ObjectProfile:
    """Provenance of the column census backing an object's ledger entries.

    ``column_count`` / ``census`` are nullable by design: Phase 0 (transcription)
    predates the real db-skill profile (Phase 2). ``census: pending`` marks that
    gap explicitly rather than faking a count.
    """

    profiled_on: str | None = None
    via: str | None = None
    column_count: int | None = None
    census: str | None = None


@dataclass(frozen=True)
class MappedObject:
    """One source object's (table/view) column ledger."""

    name: str
    kind: str | None
    profile: ObjectProfile | None
    columns: tuple[ColumnDisposition, ...]
    default_disposition: dict[str, Any] | None = None
    note: str | None = None

    def column_names(self) -> list[str]:
        """Every explicitly-dispositioned column name, in file order."""
        return [c.name for c in self.columns]

    def get(self, column: str) -> ColumnDisposition:
        for c in self.columns:
            if c.name == column:
                return c
        raise KeyError(f"unknown column '{column}' on object '{self.name}'")

    def projected(self) -> list[str]:
        """Explicitly-listed columns dispositioned ``projected``, in file order."""
        return [c.name for c in self.columns if c.disposition == "projected"]

    def unaccounted(self, profile_columns: Iterable[str]) -> list[str]:
        """Columns in ``profile_columns`` with no disposition row, when there is
        no ``default_disposition`` sweep to catch them.

        A declared ``default_disposition`` sweeps the long tail by design (doc 08
        §Direction), so once one is present every profiled column is accounted
        for and this returns ``[]`` — the *count* reconciliation (profiled total
        vs. rows + sweep) is the Phase-1 coverage test's job, not this method's.
        Without a sweep, any profiled column absent from the explicit list is
        genuinely unaccounted and is returned, in the order given.
        """
        if self.default_disposition is not None:
            return []
        known = set(self.column_names())
        return [c for c in profile_columns if c not in known]


@dataclass(frozen=True)
class SourceMapping:
    """Read-only view over one source's column ledger."""

    source: str
    classification: str
    schema: str
    objects_by_name: dict[str, MappedObject]

    @classmethod
    def load(cls, path: str | Path) -> "SourceMapping":
        """Load and validate a source-mapping YAML file at an explicit path."""
        path = Path(path)
        if not path.exists():
            raise SourceMappingError(f"source-mapping file not found: {path}")
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls.from_dict(doc)

    @classmethod
    def load_source(
        cls, source_id: str, base_dir: str | Path = DEFAULT_SOURCE_MAPPINGS_DIR
    ) -> "SourceMapping":
        """Load ``<base_dir>/<source_id>.yaml`` — the registry-id-keyed convenience path."""
        return cls.load(Path(base_dir) / f"{source_id}.yaml")

    @classmethod
    def from_dict(cls, doc: dict[str, Any]) -> "SourceMapping":
        schema = doc.get("schema")
        if schema != SCHEMA_ID:
            raise SourceMappingError(
                f"source-mapping schema must be {SCHEMA_ID!r}, got {schema!r}"
            )
        source = doc.get("source")
        if not source:
            raise SourceMappingError("source-mapping must declare a `source:` id")
        classification = doc.get("classification")
        if not classification:
            raise SourceMappingError(f"[{source}] must declare a `classification:`")

        raw_objects = doc.get("objects")
        if not isinstance(raw_objects, list) or not raw_objects:
            raise SourceMappingError(f"[{source}] must contain a non-empty `objects:` list")

        objects: dict[str, MappedObject] = {}
        for obj in raw_objects:
            if not isinstance(obj, dict):
                raise SourceMappingError(f"[{source}] malformed object entry: {obj!r}")
            oname = obj.get("name")
            if not oname:
                raise SourceMappingError(f"[{source}] object entry missing `name`: {obj!r}")
            if oname in objects:
                raise SourceMappingError(f"[{source}] duplicate object name: {oname}")

            profile = cls._parse_profile(source, oname, obj.get("profile"))
            columns = cls._parse_columns(source, oname, obj.get("columns") or [])
            default_disposition = cls._parse_default_disposition(
                source, oname, obj.get("default_disposition")
            )

            objects[oname] = MappedObject(
                name=oname,
                kind=obj.get("kind"),
                profile=profile,
                columns=columns,
                default_disposition=default_disposition,
                note=obj.get("note"),
            )

        return cls(
            source=source,
            classification=classification,
            schema=schema,
            objects_by_name=objects,
        )

    @staticmethod
    def _parse_profile(
        source: str, oname: str, raw_profile: Any
    ) -> ObjectProfile | None:
        if raw_profile is None:
            return None
        if not isinstance(raw_profile, dict):
            raise SourceMappingError(f"[{source}/{oname}] `profile:` must be a mapping")
        return ObjectProfile(
            profiled_on=raw_profile.get("profiled_on"),
            via=raw_profile.get("via"),
            column_count=raw_profile.get("column_count"),
            census=raw_profile.get("census"),
        )

    @staticmethod
    def _parse_columns(
        source: str, oname: str, raw_columns: Any
    ) -> tuple[ColumnDisposition, ...]:
        if not isinstance(raw_columns, list):
            raise SourceMappingError(f"[{source}/{oname}] `columns:` must be a list")

        columns: list[ColumnDisposition] = []
        seen: set[str] = set()
        for col in raw_columns:
            if not isinstance(col, dict):
                raise SourceMappingError(f"[{source}/{oname}] malformed column entry: {col!r}")
            cname = col.get("name")
            if not cname:
                raise SourceMappingError(
                    f"[{source}/{oname}] column entry missing `name`: {col!r}"
                )
            if cname in seen:
                raise SourceMappingError(f"[{source}/{oname}/{cname}] duplicate column")
            seen.add(cname)

            disposition = col.get("disposition")
            if disposition not in VALID_DISPOSITIONS:
                raise SourceMappingError(
                    f"[{source}/{oname}/{cname}] invalid disposition {disposition!r}; "
                    f"must be one of {sorted(VALID_DISPOSITIONS)}"
                )
            origin = col.get("origin")
            if origin is not None and origin not in VALID_ORIGINS:
                raise SourceMappingError(
                    f"[{source}/{oname}/{cname}] invalid origin {origin!r}; "
                    f"must be one of {sorted(VALID_ORIGINS)}"
                )
            reason = col.get("reason")
            if disposition == "excluded" and not reason:
                raise SourceMappingError(
                    f"[{source}/{oname}/{cname}] excluded columns must carry a `reason:`"
                )
            if reason is not None and reason not in VALID_EXCLUDED_REASONS:
                raise SourceMappingError(
                    f"[{source}/{oname}/{cname}] invalid reason {reason!r}; "
                    f"must be one of {sorted(VALID_EXCLUDED_REASONS)}"
                )

            columns.append(
                ColumnDisposition(
                    name=cname,
                    disposition=disposition,
                    origin=origin,
                    target=col.get("target"),
                    note=col.get("note"),
                    reason=reason,
                    decided_by=col.get("decided_by"),
                    derived_also=col.get("derived_also"),
                )
            )
        return tuple(columns)

    @staticmethod
    def _parse_default_disposition(
        source: str, oname: str, raw: Any
    ) -> dict[str, Any] | None:
        if raw is None:
            return None
        if not isinstance(raw, dict):
            raise SourceMappingError(f"[{source}/{oname}] `default_disposition:` must be a mapping")
        disposition = raw.get("disposition")
        if disposition not in VALID_DISPOSITIONS:
            raise SourceMappingError(
                f"[{source}/{oname}] default_disposition has invalid disposition "
                f"{disposition!r}; must be one of {sorted(VALID_DISPOSITIONS)}"
            )
        reason = raw.get("reason")
        if disposition == "excluded" and not reason:
            raise SourceMappingError(
                f"[{source}/{oname}] default_disposition excluded must carry a `reason:`"
            )
        if reason is not None and reason not in VALID_EXCLUDED_REASONS:
            raise SourceMappingError(
                f"[{source}/{oname}] default_disposition has invalid reason {reason!r}; "
                f"must be one of {sorted(VALID_EXCLUDED_REASONS)}"
            )
        return dict(raw)

    def objects(self) -> list[str]:
        """Declared object names, in file order."""
        return list(self.objects_by_name)

    def __contains__(self, object_name: str) -> bool:
        return object_name in self.objects_by_name

    def get(self, object_name: str) -> MappedObject:
        try:
            return self.objects_by_name[object_name]
        except KeyError as exc:
            raise UnknownMappingObjectError(
                f"unknown object '{object_name}'; known: {self.objects()}"
            ) from exc

    def projected(self, object_name: str) -> list[str]:
        """Ordered list of columns dispositioned ``projected`` for ``object_name``."""
        return self.get(object_name).projected()

    def unaccounted(self, object_name: str, profile_columns: Iterable[str]) -> list[str]:
        """Profiled columns of ``object_name`` with no disposition row, and not
        covered by that object's default sweep."""
        return self.get(object_name).unaccounted(profile_columns)

    def to_records(self) -> list[dict[str, Any]]:
        """Flat, DataFrame-ready view — one record per (object, column) disposition
        row, in file order. Deliberately returns plain dicts, not a DataFrame:
        callers wrap this in ``pandas.DataFrame(...)`` themselves (doc 08 —
        "a DataFrame is a view the accessor can emit, never the ledger itself")."""
        records: list[dict[str, Any]] = []
        for obj in self.objects_by_name.values():
            for col in obj.columns:
                records.append(
                    {
                        "source": self.source,
                        "object": obj.name,
                        "column": col.name,
                        "disposition": col.disposition,
                        "origin": col.origin,
                        "target": col.target,
                        "reason": col.reason,
                        "decided_by": col.decided_by,
                        "note": col.note,
                    }
                )
        return records
