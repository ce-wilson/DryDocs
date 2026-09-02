"""Typed accessor over ``config/review-labels.yaml`` — the shared *review backbone*.

Maps each ingestion SOURCE to the DATA node labels it populates, in chain order,
with SME provenance. Consumed by the ``drydocs-review`` component: ``graph_review``
renders one section per label; ``graph_verify`` validates a suite's declared targets
against the backbone.

Pure config layer — **no Neo4j, no graph writes**. The committed backbone is seeded from
the vendor-BMC baseline (``classification: Internal-Public``). Real internal
source->label chains live in a gitignored twin and pass the HITL gate before driving
any load.

Design note (MODULE_MAP): parked in the ``drydocs-review`` component for now. It is a
pure config accessor and could be promoted to ``drydocs_core.config`` — do that only
once a *second, non-review* consumer appears (ADR 0002-a resolve-at-move rule).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from drydocs_core.repo_paths import repo_root

_REPO_ROOT = repo_root(Path(__file__).resolve().parent.parent)
DEFAULT_REVIEW_LABELS_PATH = _REPO_ROOT / "config" / "review-labels.yaml"


class ReviewLabelsError(RuntimeError):
    """The review-labels.yaml file is malformed or missing required structure."""


class UnknownReviewSourceError(KeyError):
    """A source id not declared in review-labels.yaml."""


@dataclass(frozen=True)
class SourceLabels:
    """One source's contribution to the graph: the labels it populates, in chain order."""

    id: str
    provenance: str
    labels: tuple[str, ...]


class ReviewLabels:
    """Read-only view over the review backbone."""

    def __init__(self, sources: dict[str, SourceLabels], classification: str | None = None) -> None:
        self._sources = sources
        self.classification = classification

    @classmethod
    def load(cls, path: str | Path = DEFAULT_REVIEW_LABELS_PATH) -> ReviewLabels:
        path = Path(path)
        if not path.exists():
            raise ReviewLabelsError(f"review-labels file not found: {path}")
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls.from_dict(doc)

    @classmethod
    def from_dict(cls, doc: dict[str, Any]) -> ReviewLabels:
        raw_sources = doc.get("sources")
        if not isinstance(raw_sources, list):
            raise ReviewLabelsError("review-labels.yaml must contain a `sources:` list")
        sources: dict[str, SourceLabels] = {}
        for entry in raw_sources:
            sid = entry.get("id")
            if not sid:
                raise ReviewLabelsError(f"source entry missing `id`: {entry!r}")
            labels = entry.get("labels") or []
            if not isinstance(labels, list) or not labels:
                raise ReviewLabelsError(f"[{sid}] must declare a non-empty `labels:` list")
            if sid in sources:
                raise ReviewLabelsError(f"duplicate source id: {sid}")
            sources[sid] = SourceLabels(
                id=sid,
                provenance=str(entry.get("provenance", "")),
                labels=tuple(labels),
            )
        return cls(sources, classification=doc.get("classification"))

    def sources(self) -> list[str]:
        """Declared source ids, in file order."""
        return list(self._sources)

    def __contains__(self, source_id: str) -> bool:
        return source_id in self._sources

    def get(self, source_id: str) -> SourceLabels:
        try:
            return self._sources[source_id]
        except KeyError as exc:
            raise UnknownReviewSourceError(
                f"unknown review source '{source_id}'; known: {self.sources()}"
            ) from exc

    def labels_for(self, source_id: str) -> tuple[str, ...]:
        """The labels a source populates, in chain order."""
        return self.get(source_id).labels

    def all_labels(self) -> list[str]:
        """Every distinct DATA label across all sources, in first-seen order."""
        seen: list[str] = []
        for src in self._sources.values():
            for label in src.labels:
                if label not in seen:
                    seen.append(label)
        return seen

    def sources_for_label(self, label: str) -> list[SourceLabels]:
        """Every source that populates ``label`` (its provenance), in file order.

        The reverse of :meth:`labels_for` — used by ``graph_review`` to put the
        source provenance on each label's section header.
        """
        return [src for src in self._sources.values() if label in src.labels]
