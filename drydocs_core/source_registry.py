"""Source registry v2 + confirmed-gate (the config layer's activation guard).

``config/source-registry.yaml`` (schema ``drydocs.source-registry.v2``; gate
``source-registry-v2``, SIGNED OFF 2026-07-31) declares SYSTEM rows (the thing
we connect to) and DATASET rows (the thing a loader reads and a gate rules —
each with its OWN ``confirmed`` state). Loaders bind to DATASET ids; nothing
loads until the dataset's gate has signed (``confirmed: true``) — placeholder
feeds ship ``confirmed: false`` so a half-wired pipeline **fails fast** instead
of writing un-vetted edges.

The runtime registry is the UNION of two ledgers, one home per source:
``config/source-registry.yaml`` (data feeds) and
``config/doc-source-registry.yaml`` (doc corpora — their pipeline twins dropped
at N9, but doc loaders still gate here through the union).

D4 — the reconcile guard: the registry file carries a ``retired:`` refusal
list of every legacy v1 flat id. ``from_yaml`` refuses a row registered under
a retired id, lookups on a retired id raise :class:`RetiredSourceIdError`
naming the replacement, and the loader-source overlay (D2,
``config/loader-source-overlay.yaml``) refuses retired or unregistered
values. A retired string can never be silently re-minted with a different
meaning (the catalog-pat / pat-catalog T19 collision class).

D3 — every dataset's URN handle
``urn:drydocs:dataset:({carrier-or-origin},{artifact},prod)`` is DERIVED here
(lowercase, env always prod per Q2); a YAML row hand-carrying ``urn:`` is
refused at parse time.

``require_confirmed(source_id)`` is the gate: it raises a clear, actionable
error for an unknown, retired, or unconfirmed source, and is a no-op for a
confirmed one. The CLI wraps it at each production-load point (see
``drydocs/cli.py``).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY_PATH = _REPO_ROOT / "config" / "source-registry.yaml"
DEFAULT_DOC_REGISTRY_PATH = _REPO_ROOT / "config" / "doc-source-registry.yaml"
DEFAULT_OVERLAY_PATH = _REPO_ROOT / "config" / "loader-source-overlay.yaml"


class UnknownSourceError(KeyError):
    """A source id that is not declared in either registry ledger."""


class DuplicateSourceIdError(ValueError):
    """The same source id declared more than once across the ledgers.

    Silent last-one-wins would let file position decide the D3 gate: two
    entries sharing an id with different ``confirmed`` values (the
    catalog-pat / pat-catalog collision class) must refuse at parse time,
    never resolve.
    """


class UnconfirmedSourceError(RuntimeError):
    """A declared source whose crosswalk is not yet SME-confirmed (confirmed: false)."""


class RetiredSourceIdError(ValueError):
    """A legacy flat id on the D4 refusal list — renamed at the v2 migration.

    Raised both for lookups (the caller must re-bind to the replacement id)
    and at parse time if a row or overlay tries to re-register a retired id.
    """


class OverlayBindingError(ValueError):
    """A loader-source overlay entry that does not resolve to a registered,
    non-retired dataset id (the D2 guard, extending the J21 agreement guard)."""


@dataclass(frozen=True)
class System:
    """A v2 SYSTEM row — the thing we connect to (connection/locator level)."""

    id: str
    data: dict[str, Any]

    @property
    def classification(self) -> str | None:
        return self.data.get("classification")


@dataclass(frozen=True)
class Source:
    """A v2 DATASET row — the thing a loader reads and a gate rules.

    (Doc-corpus rows from the doc ledger surface through the same class so
    the confirmed-gate has one code path; their ``data`` carries the doc
    ledger's fields and ``home`` says which file they came from.)
    """

    id: str
    confirmed: bool
    data: dict[str, Any]
    home: str = "source-registry"  # 'source-registry' | 'doc-registry'

    @property
    def crosswalk(self) -> str | None:
        return self.data.get("crosswalk")

    @property
    def urn(self) -> str | None:
        """D3 — derived, never hand-maintained: lowercase
        ``urn:drydocs:dataset:({carrier-or-origin},{artifact},prod)``.
        ``None`` for doc-ledger rows (doc corpora keep the docmeta identity)."""
        if self.home != "source-registry":
            return None
        carrier = self.data.get("system") or self.id
        artifact = self.data.get("artifact") or self.id
        return f"urn:drydocs:dataset:({carrier},{artifact},prod)".lower()


@dataclass(frozen=True)
class RetiredId:
    id: str
    replaced_by: tuple[str, ...] = ()
    reason: str = ""


class SourceRegistry:
    """Read-only union view over the two ledgers with a confirmed-gate."""

    def __init__(
        self,
        sources: dict[str, Source],
        systems: dict[str, System] | None = None,
        retired: dict[str, RetiredId] | None = None,
        overlay: dict[str, str] | None = None,
    ) -> None:
        self._sources = sources
        self._systems = systems or {}
        self._retired = retired or {}
        self._overlay = overlay or {}

    # ---- construction ----------------------------------------------------

    @classmethod
    def from_yaml(
        cls,
        path: str | Path = DEFAULT_REGISTRY_PATH,
        doc_registry_path: str | Path | None = None,
        overlay_path: str | Path | None = None,
    ) -> "SourceRegistry":
        """Parse the v2 registry (+ the doc ledger union + the D2 overlay).

        ``doc_registry_path`` / ``overlay_path`` default to the shipped files
        ONLY when ``path`` is the shipped registry — a test writing a
        temporary registry gets exactly what it wrote, nothing merged in.
        Legacy v1-shaped documents (a top-level ``sources:`` list) still
        parse — the entries are treated as dataset rows — so fixture-driven
        tests and the company's not-yet-migrated twin keep working; the
        SHIPPED file is v2 (guarded by tests/unit/test_source_registry.py).
        """
        path = Path(path)
        is_default = path == DEFAULT_REGISTRY_PATH
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

        # -- retired refusal list (D4) --------------------------------------
        retired: dict[str, RetiredId] = {}
        for entry in doc.get("retired", []) or []:
            retired[entry["id"]] = RetiredId(
                id=entry["id"],
                replaced_by=tuple(entry.get("replaced_by") or ()),
                reason=entry.get("reason", ""),
            )

        # -- systems ---------------------------------------------------------
        systems: dict[str, System] = {}
        for entry in doc.get("systems", []) or []:
            sid = entry["id"]
            if sid in systems:
                raise DuplicateSourceIdError(
                    f"Duplicate system id {sid!r} in {path} — each id must be "
                    f"declared exactly once."
                )
            systems[sid] = System(id=sid, data=entry)

        # -- datasets (v2 `datasets:`; legacy `sources:` accepted) -----------
        sources: dict[str, Source] = {}

        def _add(entry: dict[str, Any], home: str) -> None:
            sid = entry["id"]
            if sid in retired:
                rep = ", ".join(retired[sid].replaced_by) or "(no replacement)"
                raise RetiredSourceIdError(
                    f"Source id {sid!r} is RETIRED (D4 refusal list; replaced "
                    f"by: {rep}) and cannot be re-registered — a retired id "
                    f"never comes back with a different meaning."
                )
            if sid in sources:
                raise DuplicateSourceIdError(
                    f"Duplicate source id {sid!r} — each id must be declared "
                    f"exactly once across the ledgers (last-one-wins would let "
                    f"file position decide the confirmed-gate)."
                )
            if home == "source-registry" and "urn" in entry:
                raise ValueError(
                    f"Dataset {sid!r} hand-carries a `urn:` field — the URN is "
                    f"DERIVED (D3: a render, never hand-maintained). Remove it."
                )
            sources[sid] = Source(
                id=sid,
                confirmed=bool(entry.get("confirmed", False)),
                data=entry,
                home=home,
            )

        for entry in doc.get("datasets", []) or []:
            _add(entry, "source-registry")
        for entry in doc.get("sources", []) or []:  # legacy v1 shape
            _add(entry, "source-registry")

        # -- doc-ledger union (one home per source; gate still covers docs) --
        doc_path = Path(doc_registry_path) if doc_registry_path else (
            DEFAULT_DOC_REGISTRY_PATH if is_default else None
        )
        if doc_path is not None and doc_path.exists():
            doc_doc = yaml.safe_load(doc_path.read_text(encoding="utf-8")) or {}
            for entry in doc_doc.get("sources", []) or []:
                _add(entry, "doc-registry")

        # -- the D2 overlay ---------------------------------------------------
        ov_path = Path(overlay_path) if overlay_path else (
            DEFAULT_OVERLAY_PATH if is_default else None
        )
        overlay: dict[str, str] = {}
        if ov_path is not None and ov_path.exists():
            ov_doc = yaml.safe_load(ov_path.read_text(encoding="utf-8")) or {}
            overlay = dict(ov_doc.get("overrides") or {})
            for loader_name, dataset_id in overlay.items():
                if dataset_id in retired:
                    rep = ", ".join(retired[dataset_id].replaced_by) or "(none)"
                    raise OverlayBindingError(
                        f"Overlay binds loader {loader_name!r} to RETIRED id "
                        f"{dataset_id!r} (replaced by: {rep}) — re-bind to a "
                        f"registered dataset id ({ov_path})."
                    )
                if dataset_id not in sources:
                    raise OverlayBindingError(
                        f"Overlay binds loader {loader_name!r} to unregistered "
                        f"id {dataset_id!r} — every override must resolve to a "
                        f"registered dataset id ({ov_path}; the J21 agreement "
                        f"guard, extended per D2)."
                    )

        return cls(sources, systems=systems, retired=retired, overlay=overlay)

    # ---- queries ---------------------------------------------------------

    def __contains__(self, source_id: str) -> bool:
        return source_id in self._sources

    def ids(self) -> list[str]:
        return sorted(self._sources)

    def system_ids(self) -> list[str]:
        return sorted(self._systems)

    def systems(self) -> list[System]:
        return [self._systems[sid] for sid in sorted(self._systems)]

    def get_system(self, system_id: str) -> System:
        try:
            return self._systems[system_id]
        except KeyError:
            raise UnknownSourceError(
                f"Unknown system {system_id!r} — not in "
                f"config/source-registry.yaml (known: {self.system_ids()})"
            ) from None

    def retired_ids(self) -> list[str]:
        return sorted(self._retired)

    def get(self, source_id: str) -> Source:
        try:
            return self._sources[source_id]
        except KeyError:
            if source_id in self._retired:
                r = self._retired[source_id]
                rep = ", ".join(r.replaced_by) or "(no replacement)"
                raise RetiredSourceIdError(
                    f"Source id {source_id!r} is RETIRED (v2 migration, gate "
                    f"source-registry-v2 2026-07-31) — replaced by: {rep}. "
                    f"Re-bind to the replacement id; retired ids never resolve. "
                    f"({r.reason})"
                ) from None
            raise UnknownSourceError(
                f"Unknown source {source_id!r} — not in config/source-registry.yaml "
                f"(known: {self.ids()})"
            ) from None

    def is_confirmed(self, source_id: str) -> bool:
        return self.get(source_id).confirmed

    # ---- the D2 overlay ---------------------------------------------------

    def effective_source_id(
        self, loader_name: str, declared: str | None
    ) -> str | None:
        """The dataset id a loader actually binds to: the per-side overlay
        entry when one exists (D2 — config wins over the class default),
        else the loader's own declared ``source_id``."""
        return self._overlay.get(loader_name, declared)

    # ---- the gate --------------------------------------------------------

    def require_confirmed(self, source_id: str) -> Source:
        """Return the source if confirmed; otherwise raise with a clear message.

        Raises :class:`UnknownSourceError` for an undeclared id,
        :class:`RetiredSourceIdError` for a D4-retired id, and
        :class:`UnconfirmedSourceError` for a declared-but-unconfirmed source.
        """
        src = self.get(source_id)
        if not src.confirmed:
            where = src.crosswalk or "config/source-registry.yaml"
            if src.home == "doc-registry":
                where = src.crosswalk or "config/doc-source-registry.yaml"
            ledger = (
                "config/doc-source-registry.yaml"
                if src.home == "doc-registry"
                else "config/source-registry.yaml"
            )
            raise UnconfirmedSourceError(
                f"Source {source_id!r} is not confirmed (confirmed: false) and will not load. "
                f"Its crosswalk must pass the HITL gate (docs/restructure/03-hitl-sme-flow.md), "
                f"then set confirmed: true in {ledger}. See {where}."
            )
        return src
