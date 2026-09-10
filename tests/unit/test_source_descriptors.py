"""config/source-descriptors.yaml + drydocs_core.source_descriptors — the five
registration axes over every registry-home dataset, plus the sixth, `wired`,
declared per side (CFG13, 2026-09-09).

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
    WIRED_AXIS,
    WIRED_REASON_MIN,
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
    assert set(raw_config["axes"]) == set(AXES) | {WIRED_AXIS}


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
        # CORE18: the drop left the tree for the data root, so `access` derives `human`
        # rather than `repo` - and that is a CORRECTION, not just a consequence. The
        # export is a hand download from a site UI; it was never read by the checkout.
        ("infra:server-export", ("manual", "csv", "primary", "technology", "human")),
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


# --- the sixth axis (CFG13, 2026-09-09) ----------------------------------------------


def test_wired_is_declared_for_every_registry_dataset(descriptors):
    """Declared, never derived, never silent (wiring page B4/B5): every registry-home
    dataset carries a bool, a false carries its reason at the ruled length, and the
    descriptor's fields say the same thing as the reader's own accessor."""
    for d in descriptors.all():
        assert isinstance(d.wired, bool), d.source_id
        assert (d.wired, d.wired_reason) == descriptors.wired(d.source_id)
        if not d.wired:
            assert d.wired_reason and len(d.wired_reason) >= WIRED_REASON_MIN, d.source_id
    assert {d.wired for d in descriptors.all()} == {
        True,
        False,
    }, "both values must be occupied, or the axis is dressing up a constant"


def test_wired_declaration_agrees_with_the_tree(descriptors):
    """DECLARED, because core cannot see loader registration - but it is a fact about
    THIS tree, so the guard (not the reader) holds the declaration against what the
    load component registers: a loader bound to an id the block calls false is an
    undeclared build, and a true with no loader is a false declaration. Either fails
    here, by name, and the fix is the one-line declaration the message asks for."""
    from drydocs import cli  # the load component; a test may look where core may not

    bound = {cls.source_id for cls in cli.LOADER_REGISTRY.values() if cls.source_id}
    for classes in cli.COMMAND_LOADERS.values():
        bound |= {cls.source_id for cls in classes if cls.source_id}
    for d in descriptors.all():
        assert d.wired == (d.source_id in bound), (
            f"{d.source_id}: declared wired={d.wired} but a loader is "
            f"{'bound' if d.source_id in bound else 'not bound'} to it - "
            "update the wired: block in config/source-descriptors.yaml (with a reason if false)"
        )


def test_wired_block_is_required(raw_config, registry):
    cfg = copy.deepcopy(raw_config)
    del cfg["wired"]
    with pytest.raises(DescriptorError, match="block missing"):
        SourceDescriptors(cfg, registry)


def test_wired_missing_entry_is_refused(raw_config, registry):
    cfg = copy.deepcopy(raw_config)
    del cfg["wired"]["seal:app-extract"]
    with pytest.raises(DescriptorError, match="REQUIRED for every registry-home dataset"):
        SourceDescriptors(cfg, registry)


def test_wired_unknown_dataset_is_refused(raw_config, registry):
    cfg = copy.deepcopy(raw_config)
    cfg["wired"]["nope:nothing"] = True
    with pytest.raises(DescriptorError, match="unknown dataset"):
        SourceDescriptors(cfg, registry)


@pytest.mark.parametrize(
    ("entry", "why"),
    [
        (False, "must be true, or a mapping"),  # a bare false is a fact with no owner
        ("yes", "must be true, or a mapping"),  # not a boolean at all
        ({"value": False}, "at least 40"),  # false with no reason
        ({"value": False, "reason": "not yet"}, "at least 40"),  # false with a short one
        ({"value": "false", "reason": "x" * 40}, "must be true, or a mapping"),  # string value
    ],
)
def test_wired_false_needs_a_written_reason(raw_config, registry, entry, why):
    cfg = copy.deepcopy(raw_config)
    cfg["wired"]["seal:app-extract"] = entry
    with pytest.raises(DescriptorError, match=why):
        SourceDescriptors(cfg, registry)


def test_wired_true_may_carry_a_reason_and_false_reason_is_stripped(raw_config, registry):
    cfg = copy.deepcopy(raw_config)
    cfg["wired"]["seal:app-extract"] = {"value": True, "reason": "a note the reader keeps"}
    cfg["wired"]["snow:cmdb-ci-classes"] = {"value": False, "reason": "  " + "r" * 40 + "  "}
    ds = SourceDescriptors(cfg, registry)
    assert ds.wired("seal:app-extract") == (True, "a note the reader keeps")
    assert ds.wired("snow:cmdb-ci-classes") == (False, "r" * 40)
    with pytest.raises(DescriptorError, match="no wired entry"):
        ds.wired("bmc-docs")  # a doc-ledger id: no descriptor answers for it
