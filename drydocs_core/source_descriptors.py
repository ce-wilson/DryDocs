"""Registration descriptors — five finite axes per dataset, derived from the
source registry and overridable in ``config/source-descriptors.yaml``.

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
        self._validate_overrides()

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
        return Descriptor(
            source_id=source_id,
            system_id=system.id,
            urn=source.urn,
            derived=bool(source.data.get("derived")),
            confirmed=bool(source.confirmed),
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
