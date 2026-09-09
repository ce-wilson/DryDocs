"""Registration descriptors — five finite axes per dataset, derived from the
source registry and overridable in ``config/source-descriptors.yaml``, plus a
sixth, ``wired``, that is DECLARED there per side and never derived (CFG13,
2026-09-09: is the pipeline that reads the dataset built on this tree).

The registry (``drydocs_core.source_registry``) says WHAT a source is; the
bindings say HOW TO REACH it; this module says how it is REGISTERED as a
catalog asset. Every value is drawn from a closed axis declared in the config,
so a consumer (the DataHub emitter, the synthetic generator, a test) reads a
value and never interprets prose. Derivation first, override second, and a
value off its axis is refused — the reader never guesses.

Pure config reading: no graph, no database, no network.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from drydocs_core.repo_paths import repo_root
from drydocs_core.source_registry import Source, SourceRegistry, System

REPO_ROOT = repo_root(Path(__file__).resolve().parents[1])
DEFAULT_DESCRIPTORS_PATH = REPO_ROOT / "config" / "source-descriptors.yaml"

AXES: tuple[str, ...] = ("acquisition", "format", "authority", "layer", "access")
#: The sixth axis (registry-wiring-readiness B1/B2, source-descriptor-axes B1-B4, SIGNED
#: 2026-09-09): DECLARED per side in the config's ``wired:`` block, never derived here -
#: core cannot see loader registration. Required for every registry-home dataset; a
#: false carries a reason of at least this many characters (the SOURCELESS_LOADERS idiom).
WIRED_AXIS = "wired"
WIRED_REASON_MIN = 40


class DescriptorError(ValueError):
    """The descriptor config disagrees with its own axes or with the registry."""


@dataclass(frozen=True)
class Descriptor:
    """One dataset's registration descriptor — the five axis values plus the
    facts the emitter needs alongside them."""

    source_id: str
    system_id: str
    acquisition: str
    format: str
    authority: str
    layer: str
    access: str
    urn: str
    derived: bool
    confirmed: bool
    #: The declared wiring fact: is the pipeline that reads this dataset built on THIS
    #: side. Independent of ``confirmed``, which is the semantic ruling only.
    wired: bool = False
    wired_reason: str | None = None

    def axis_values(self) -> dict[str, str]:
        return {axis: getattr(self, axis) for axis in AXES}


@dataclass(frozen=True)
class SyntheticPlan:
    """Which files a generated stand-in produces for one dataset, and where."""

    source_id: str
    files: tuple[str, ...]
    #: ``zone`` when the dataset has a manual landing zone, ``mirror`` when it
    #: is db-carried and gets a CSV mirror instead.
    placement: str


class SourceDescriptors:
    """The descriptor table, derived from a registry and a descriptor config."""

    def __init__(self, config: dict[str, Any], registry: SourceRegistry) -> None:
        self._config = config
        self._registry = registry
        self.axes: dict[str, tuple[str, ...]] = {
            axis: tuple(values) for axis, values in config["axes"].items()
        }
        missing = [axis for axis in AXES if axis not in self.axes]
        if missing:
            raise DescriptorError(f"axes missing from descriptor config: {missing}")
        self._authority_map: dict[str, str] = dict(config.get("authority_map", {}))
        self._overrides: dict[str, dict[str, str]] = dict(config.get("overrides", {}))
        self.datahub: dict[str, Any] = dict(config.get("datahub", {}))
        self.synthetic: dict[str, Any] = dict(config.get("synthetic", {}))
        self._wired: dict[str, tuple[bool, str | None]] = {}
        self._validate_overrides()
        self._validate_wired(config.get(WIRED_AXIS))

    # ------------------------------------------------------------------ load
    @classmethod
    def from_yaml(
        cls,
        path: Path | None = None,
        *,
        registry: SourceRegistry | None = None,
    ) -> SourceDescriptors:
        p = Path(path) if path is not None else DEFAULT_DESCRIPTORS_PATH
        with p.open(encoding="utf-8") as fh:
            config = yaml.safe_load(fh) or {}
        if config.get("schema") != "drydocs.source-descriptors.v1":
            raise DescriptorError(f"{p}: unexpected schema {config.get('schema')!r}")
        return cls(config, registry or SourceRegistry.from_yaml())

    # -------------------------------------------------------------- validate
    def dataset_ids(self) -> list[str]:
        """Registry-home dataset ids only. The doc ledger's entries share the
        registry's id space but carry no system row, so they have no carrier
        to register against; they are catalogued by the docs ledger, not here."""
        return [
            sid for sid in self._registry.ids() if self._registry.get(sid).home == "source-registry"
        ]

    def _validate_overrides(self) -> None:
        known = set(self.dataset_ids())
        for source_id, values in self._overrides.items():
            if source_id not in known:
                raise DescriptorError(f"override names unknown dataset {source_id!r}")
            for axis, value in values.items():
                self._check(axis, value, source_id)

    def _validate_wired(self, block: Any) -> None:
        """The sixth axis is DECLARED and REQUIRED (wiring page B4/B5, 2026-09-09).

        Every registry-home dataset carries an entry: ``true``, or a mapping with
        ``value: false`` and a ``reason`` of at least :data:`WIRED_REASON_MIN`
        characters. A missing block, a missing entry, an unknown id, a non-boolean
        value or a bare or short reason is refused HERE, at construction, so a
        config that has not answered for a new row fails before the first read
        rather than on whichever dataset is asked for first. Never derived: a
        declared value with a reason is a decision someone can re-read and reverse;
        a computed one is neither.
        """
        if not isinstance(block, dict):
            raise DescriptorError(
                f"{WIRED_AXIS}: block missing or not a mapping keyed by dataset id "
                f"(every registry-home dataset must declare true, or value: false + reason)"
            )
        known = set(self.dataset_ids())
        unknown = sorted(set(block) - known)
        if unknown:
            raise DescriptorError(f"{WIRED_AXIS} names unknown dataset(s) {unknown}")
        missing = sorted(known - set(block))
        if missing:
            raise DescriptorError(
                f"{WIRED_AXIS} is REQUIRED for every registry-home dataset; missing {missing}"
            )
        for source_id, entry in block.items():
            if entry is True:
                self._wired[source_id] = (True, None)
                continue
            if isinstance(entry, dict) and isinstance(entry.get("value"), bool):
                reason = entry.get("reason")
                if entry["value"]:
                    self._wired[source_id] = (True, reason if isinstance(reason, str) else None)
                    continue
                if not isinstance(reason, str) or len(reason.strip()) < WIRED_REASON_MIN:
                    raise DescriptorError(
                        f"{source_id}: {WIRED_AXIS}=false needs a reason of at least "
                        f"{WIRED_REASON_MIN} characters - a bare false is a fact, a reasoned "
                        f"false is a decision someone can re-read and reverse"
                    )
                self._wired[source_id] = (False, reason.strip())
                continue
            raise DescriptorError(
                f"{source_id}: {WIRED_AXIS} must be true, or a mapping with value: false and "
                f"a reason - got {entry!r}"
            )

    def wired(self, source_id: str) -> tuple[bool, str | None]:
        """The declared wiring fact and its reason for one registry-home dataset."""
        try:
            return self._wired[source_id]
        except KeyError:
            raise DescriptorError(
                f"{source_id}: no {WIRED_AXIS} entry (not a registry-home dataset?)"
            ) from None

    def _check(self, axis: str, value: str, source_id: str) -> str:
        if axis not in self.axes:
            raise DescriptorError(f"{source_id}: {axis!r} is not a descriptor axis")
        if value not in self.axes[axis]:
            raise DescriptorError(
                f"{source_id}: {axis}={value!r} is not on its axis {list(self.axes[axis])}"
            )
        return value

    # ---------------------------------------------------------------- derive
    def _derive(self, source: Source, system: System) -> dict[str, str]:
        acq = source.data.get("acquisition") or {}
        mode = acq.get("mode") or "automated"
        if mode == "manual":
            fmt = acq.get("format") or "ascii"
        else:
            fmt = acq.get("via") or "db"
        if source.data.get("derived"):
            authority = self._authority_map.get("derived", "replica")
        else:
            authority = self._authority_map.get(source.data.get("authority"), "replica")
        layer = system.data.get("layer") or "technology"
        if system.data.get("binding"):
            access = "fid"
        elif acq.get("drop_dir_base") == "repo":
            access = "repo"
        elif mode == "manual":
            access = "human"
        else:
            # automated but unbound: still read by a service identity, not a person
            access = "fid"
        return {
            "acquisition": mode,
            "format": fmt,
            "authority": authority,
            "layer": layer,
            "access": access,
        }

    def get(self, source_id: str) -> Descriptor:
        source = self._registry.get(source_id)
        system = self._registry.get_system(source.data["system"])
        values = self._derive(source, system)
        values.update(self._overrides.get(source_id, {}))
        for axis, value in values.items():
            self._check(axis, value, source_id)
        wired, wired_reason = self.wired(source_id)
        return Descriptor(
            source_id=source_id,
            system_id=system.id,
            urn=source.urn,
            derived=bool(source.data.get("derived")),
            confirmed=bool(source.confirmed),
            wired=wired,
            wired_reason=wired_reason,
            **values,
        )

    def all(self) -> tuple[Descriptor, ...]:
        """Every dataset's descriptor, in registry id order — stable by construction."""
        return tuple(self.get(sid) for sid in self.dataset_ids())

    def systems(self) -> tuple[System, ...]:
        return tuple(sorted(self._registry.systems(), key=lambda s: s.id))

    # ------------------------------------------------------------- synthetic
    def synthetic_plans(self) -> tuple[SyntheticPlan, ...]:
        plans = []
        for source_id, spec in sorted((self.synthetic.get("datasets") or {}).items()):
            desc = self.get(source_id)
            placement = "zone" if desc.acquisition == "manual" else "mirror"
            plans.append(SyntheticPlan(source_id, tuple(spec["files"]), placement))
        return tuple(plans)

    def platform_for(self, system_id: str) -> str:
        platforms = self.datahub.get("platforms") or {}
        return platforms.get(system_id, platforms.get("default", "file"))
