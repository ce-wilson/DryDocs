"""config/source-descriptors.yaml + drydocs_core.source_descriptors — the five
registration axes over every registry-home dataset.

The value of the descriptor table is that every field is drawn from a closed
axis and every dataset gets one, so a consumer never reads prose. These tests
pin exactly that: closed axes, full coverage, refusal of off-axis values, and
the derivations the emitter and the synthetic generator depend on.
"""

from __future__ import annotations

import copy

import pytest
import yaml

from drydocs_core.source_descriptors import (
    AXES,
    DEFAULT_DESCRIPTORS_PATH,
    DescriptorError,
    SourceDescriptors,
)
from drydocs_core.source_registry import SourceRegistry


@pytest.fixture(scope="module")
def registry() -> SourceRegistry:
    return SourceRegistry.from_yaml()


@pytest.fixture(scope="module")
def descriptors(registry: SourceRegistry) -> SourceDescriptors:
    return SourceDescriptors.from_yaml(registry=registry)


@pytest.fixture(scope="module")
def raw_config() -> dict:
    with DEFAULT_DESCRIPTORS_PATH.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def test_config_carries_the_identity_header(raw_config):
    assert raw_config["schema"] == "drydocs.source-descriptors.v1"
    assert raw_config["classification"] == "Internal-Public"
    assert set(raw_config["axes"]) == set(AXES)


def test_every_registry_dataset_has_a_descriptor_on_axis(descriptors, registry):
    expected = sorted(sid for sid in registry.ids() if registry.get(sid).home == "source-registry")
    got = descriptors.all()
    assert sorted(d.source_id for d in got) == expected
    assert len(got) >= 30  # the registry's dataset count at build time; grows, never shrinks
    for d in got:
        for axis, value in d.axis_values().items():
            assert value in descriptors.axes[axis], (d.source_id, axis, value)
        assert d.system_id in {s.id for s in descriptors.systems()}
        assert d.urn


def test_doc_ledger_entries_are_not_registered_here(descriptors, registry):
    ledger = {sid for sid in registry.ids() if registry.get(sid).home != "source-registry"}
    assert ledger, "the doc ledger union is what makes this test meaningful"
    assert ledger.isdisjoint(descriptors.dataset_ids())


@pytest.mark.parametrize(
    ("source_id", "expected"),
    [
        # manual CSV drop from a business-layer system, read by a person
        ("seal:app-extract", ("manual", "csv", "primary", "business", "human")),
        # db-carried replica read through a bound service identity; the layer is the
        # carrier schema's (psgmgr = data), not the source system's (controlm = technology)
        ("controlm@[db].psgmgr.cm_def_vtab", ("automated", "db", "replica", "data", "fid")),
        # repo-based landing zone -> access repo
        ("infra:server-export", ("manual", "csv", "primary", "technology", "repo")),
        # layer override: people data is the human layer whatever system carries it
        ("hr@[db].psgmgr.hr_phone_exp", ("automated", "db", "replica", "human", "fid")),
        ("pat:people-report", ("manual", "csv", "primary", "human", "human")),
        # derived datasets are never primary
        ("repo:depgraph-snapshot", ("manual", "json", "replica", "technology", "repo")),
    ],
)
def test_derivations_and_overrides(descriptors, source_id, expected):
    d = descriptors.get(source_id)
    assert tuple(d.axis_values().values()) == expected


def test_off_axis_override_is_refused(raw_config, registry):
    cfg = copy.deepcopy(raw_config)
    cfg["overrides"]["seal:app-extract"] = {"layer": "spiritual"}
    with pytest.raises(DescriptorError, match="not on its axis"):
        SourceDescriptors(cfg, registry)


def test_unknown_axis_in_override_is_refused(raw_config, registry):
    cfg = copy.deepcopy(raw_config)
    cfg["overrides"]["seal:app-extract"] = {"colour": "red"}
    with pytest.raises(DescriptorError, match="not a descriptor axis"):
        SourceDescriptors(cfg, registry)


def test_override_for_unknown_dataset_is_refused(raw_config, registry):
    cfg = copy.deepcopy(raw_config)
    cfg["overrides"]["nope:nothing"] = {"layer": "human"}
    with pytest.raises(DescriptorError, match="unknown dataset"):
        SourceDescriptors(cfg, registry)


def test_synthetic_plans_name_only_registered_datasets(descriptors):
    plans = descriptors.synthetic_plans()
    assert plans
    ids = set(descriptors.dataset_ids())
    for plan in plans:
        assert plan.source_id in ids
        assert plan.files and all(f.endswith(".csv") for f in plan.files)
        assert plan.placement in {"zone", "mirror"}
        d = descriptors.get(plan.source_id)
        assert plan.placement == ("zone" if d.acquisition == "manual" else "mirror")


def test_platform_map_falls_back_to_default(descriptors):
    assert descriptors.platform_for("psgmgr") == "oracle"
    assert descriptors.platform_for("no-such-system") == descriptors.datahub["platforms"]["default"]
