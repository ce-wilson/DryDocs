"""Source registry + confirmed-gate (the config layer's activation guard).

``config/source-registry.yaml`` declares every data-pipeline source and whether its
crosswalk has passed the HITL gate (``confirmed: true``). Nothing loads until then —
placeholder feeds (AutoSys, Airflow, Oracle schemas, Snowflake) ship ``confirmed: false``
so a half-wired pipeline **fails fast** instead of writing un-vetted edges.

``require_confirmed(source_id)`` is the gate: it raises a clear, actionable error for an
unknown or unconfirmed source, and is a no-op for a confirmed one. The CLI wraps it at
each production-load point (see ``drydocs/cli.py``).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY_PATH = _REPO_ROOT / "config" / "source-registry.yaml"


class UnknownSourceError(KeyError):
    """A source id that is not declared in source-registry.yaml."""


class DuplicateSourceIdError(ValueError):
    """The same source id declared more than once in source-registry.yaml.

    Silent last-one-wins would let file position decide the D3 gate: two entries
    sharing an id with different ``confirmed`` values (the catalog-pat /
    pat-catalog collision class) must refuse at parse time, never resolve.
    """


class UnconfirmedSourceError(RuntimeError):
    """A declared source whose crosswalk is not yet SME-confirmed (confirmed: false)."""


@dataclass(frozen=True)
class Source:
    id: str
    confirmed: bool
    data: dict[str, Any]

    @property
    def crosswalk(self) -> str | None:
        return self.data.get("crosswalk")


class SourceRegistry:
    """Read-only view over source-registry.yaml with a confirmed-gate."""

    def __init__(self, sources: dict[str, Source]) -> None:
        self._sources = sources

    # ---- construction ----------------------------------------------------

    @classmethod
    def from_yaml(cls, path: str | Path = DEFAULT_REGISTRY_PATH) -> "SourceRegistry":
        doc = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        sources: dict[str, Source] = {}
        for entry in doc.get("sources", []):
            sid = entry["id"]
            if sid in sources:
                raise DuplicateSourceIdError(
                    f"Duplicate source id {sid!r} in {path} — each id must be "
                    f"declared exactly once (last-one-wins would let file "
                    f"position decide the confirmed-gate)."
                )
            sources[sid] = Source(id=sid, confirmed=bool(entry.get("confirmed", False)), data=entry)
        return cls(sources)

    # ---- queries ---------------------------------------------------------

    def __contains__(self, source_id: str) -> bool:
        return source_id in self._sources

    def ids(self) -> list[str]:
        return sorted(self._sources)

    def get(self, source_id: str) -> Source:
        try:
            return self._sources[source_id]
        except KeyError:
            raise UnknownSourceError(
                f"Unknown source {source_id!r} — not in config/source-registry.yaml "
                f"(known: {self.ids()})"
            ) from None

    def is_confirmed(self, source_id: str) -> bool:
        return self.get(source_id).confirmed

    # ---- the gate --------------------------------------------------------

    def require_confirmed(self, source_id: str) -> Source:
        """Return the source if confirmed; otherwise raise with a clear message.

        Raises :class:`UnknownSourceError` for an undeclared id and
        :class:`UnconfirmedSourceError` for a declared-but-unconfirmed source.
        """
        src = self.get(source_id)
        if not src.confirmed:
            where = src.crosswalk or "config/source-registry.yaml"
            raise UnconfirmedSourceError(
                f"Source {source_id!r} is not confirmed (confirmed: false) and will not load. "
                f"Its crosswalk must pass the HITL gate (docs/restructure/03-hitl-sme-flow.md), "
                f"then set confirmed: true in config/source-registry.yaml. See {where}."
            )
        return src
