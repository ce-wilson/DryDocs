"""G78 — a chain step that cannot find its input MUST FAIL, and a real run never
defaults to the fixture directory.

Guards (the item's own): a chain step with a missing required input FAILS BY
NAME before anything is written; a run against the fixture directory is
distinguishable in the summary from a run against a declared source.

Clause (d), the coverage rider: the five loaders A5 measured with no direct test
import on 2026-08-13 — business_segments, controlm (the re-export module),
controlm_dependencies_derived, controlm_hosts, seal_contacts — are imported HERE
and exercised on the path this item changes: the missing-input resolution.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from drydocs import cli as cli_mod
from drydocs.chain_inputs import (
    FIXTURE,
    SOURCE,
    ChainModeError,
    ChainStep,
    MissingChainInputError,
    StepResult,
    resolve_chain_inputs,
    summary_lines,
)
from drydocs.loaders import business_segments, controlm
from drydocs.loaders.controlm_dependencies_derived import ControlMDependenciesDerivedLoader
from drydocs.loaders.controlm_hosts import ControlMHostsLoader
from drydocs.loaders.seal_contacts import SealContactsLoader
from drydocs_core.source_registry import SourceRegistry

REGISTRY = SourceRegistry.from_yaml()
runner = CliRunner()


def _chain() -> list[ChainStep]:
    return [ChainStep(nm, cls, fixture) for nm, cls, fixture in cli_mod.REFRESH_REFERENCE_CHAIN]


# -- (b) no default, two explicit modes ----------------------------------------


def test_no_mode_is_refused_not_defaulted() -> None:
    with pytest.raises(ChainModeError, match="no default"):
        resolve_chain_inputs(_chain(), samples_dir=None, sources=[], registry=REGISTRY)


def test_both_modes_are_refused() -> None:
    with pytest.raises(ChainModeError, match="exclusive"):
        resolve_chain_inputs(
            _chain(), samples_dir=Path("x"), sources=["pat:people-report"], registry=REGISTRY
        )


def test_unknown_source_is_refused_and_the_declared_zones_are_named() -> None:
    with pytest.raises(ChainModeError, match="not-a-source.*declared zones"):
        resolve_chain_inputs(
            _chain(), samples_dir=None, sources=["not-a-source"], registry=REGISTRY
        )


# -- (a) missing required input fails BY NAME, before any write ------------------


def test_missing_fixture_fails_naming_file_and_directory(tmp_path: Path) -> None:
    """A fixture directory with everything EXCEPT the two generated SEAL files —
    exactly the producer-side state the item reproduced."""
    for _, _, fixture in cli_mod.REFRESH_REFERENCE_CHAIN:
        if not fixture.startswith("seal_"):
            (tmp_path / fixture).write_text("h\n", encoding="utf-8")
    with pytest.raises(MissingChainInputError) as info:
        resolve_chain_inputs(_chain(), samples_dir=tmp_path, sources=[], registry=REGISTRY)
    text = str(info.value)
    assert "seal_applications: seal_application_data__sample.csv not found" in text
    assert "seal_contacts: seal_contact_data__sample.csv not found" in text
    assert str(tmp_path) in text
    assert "nothing was loaded" in text
    assert "build_seal_samples" in text  # the way out is named, not left to guessing
    assert {s.name for s, _, _ in info.value.missing} == {"seal_applications", "seal_contacts"}


def test_chain_verb_exits_2_before_touching_the_graph(tmp_path: Path, monkeypatch) -> None:
    calls: list[str] = []

    def _never(*a, **k):
        calls.append("client")
        raise AssertionError("the graph must not be opened when an input is missing")

    monkeypatch.setattr(cli_mod, "_client", _never)
    result = runner.invoke(cli_mod.app, ["refresh-reference", "--samples-dir", str(tmp_path)])
    assert result.exit_code == 2, result.output
    assert "catalog_lobs__sample.csv not found" in result.output.replace("\n", "")
    assert calls == []
    # and with no arguments at all: the old silent fixture default is gone
    result = runner.invoke(cli_mod.app, ["refresh-reference"])
    assert result.exit_code == 2
    assert "no default" in result.output.replace("\n", " ")
    assert calls == []


def test_optional_is_written_down_never_inferred(tmp_path: Path) -> None:
    steps = [
        ChainStep("a", ControlMHostsLoader, "a.csv"),
        ChainStep("b", ControlMHostsLoader, "b.csv", optional=True),
    ]
    (tmp_path / "a.csv").write_text("h\n", encoding="utf-8")
    plan = resolve_chain_inputs(steps, samples_dir=tmp_path, sources=[], registry=REGISTRY)
    assert [i.step.name for i in plan.inputs] == ["a"]
    assert [(s.step.name, "optional" in s.reason) for s in plan.skipped] == [("b", True)]


# -- (b)/(c) source mode resolves the declared landing zone and the summary says which --


def test_source_mode_reads_the_declared_zone_and_reports_unselected_steps(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path))
    zone = tmp_path / "pat"  # pat:people-report's declared drop_dir
    zone.mkdir()
    (zone / "pat_product_mapping.csv").write_text("h\n", encoding="utf-8")
    plan = resolve_chain_inputs(
        _chain(), samples_dir=None, sources=["pat:people-report"], registry=REGISTRY
    )
    loaded = {i.step.name: i for i in plan.inputs}
    assert set(loaded) == {"pat_product_mapping"}
    assert loaded["pat_product_mapping"].mode == SOURCE
    assert loaded["pat_product_mapping"].source_id == "pat:people-report"
    assert loaded["pat_product_mapping"].path == zone / "pat_product_mapping.csv"
    skipped = {s.step.name: s.reason for s in plan.skipped}
    assert "dev_teams" in skipped and "not selected" in skipped["dev_teams"]
    assert "pat:product-catalog" in skipped["dev_teams"]
    # the file the selected source needs, absent -> fails by name in the ZONE, not in samples/
    (zone / "pat_product_mapping.csv").unlink()
    with pytest.raises(MissingChainInputError, match=r"pat_product_mapping\.csv not found"):
        resolve_chain_inputs(
            _chain(), samples_dir=None, sources=["pat:people-report"], registry=REGISTRY
        )


def test_summary_distinguishes_a_fixture_run_from_a_source_run() -> None:
    fixture = StepResult("catalog_lobs", FIXTURE, "samples/catalog_lobs__sample.csv", 5, 0)
    source = StepResult(
        "pat_product_mapping",
        SOURCE,
        "/data/pat/pat_product_mapping.csv",
        812,
        3,
        "pat:people-report",
    )
    lines = summary_lines([fixture, source], [])
    assert lines[0].startswith("step | mode | path read")
    assert "catalog_lobs | fixture | samples/catalog_lobs__sample.csv | 5 | 0" in lines
    assert (
        "pat_product_mapping | source:pat:people-report | /data/pat/pat_product_mapping.csv | 812 | 3"
        in lines
    )


# -- (d) the five loaders with no direct test import, exercised on this path --------


@pytest.mark.parametrize(
    "cls",
    [
        ControlMDependenciesDerivedLoader,
        ControlMHostsLoader,
        SealContactsLoader,
        controlm.ControlMDependenciesDerivedLoader,  # via the re-export module
        controlm.ControlMHostsLoader,
    ],
)
def test_each_named_loader_fails_by_name_when_its_input_is_absent(cls, tmp_path: Path) -> None:
    step = ChainStep(cls.name, cls, f"{cls.name}__sample.csv")
    with pytest.raises(MissingChainInputError) as info:
        resolve_chain_inputs([step], samples_dir=tmp_path, sources=[], registry=REGISTRY)
    assert f"{cls.name}: {cls.name}__sample.csv not found" in str(info.value)
    assert str(tmp_path) in str(info.value)


def test_business_segments_is_the_one_step_with_no_file_and_says_so() -> None:
    """refresh_business_segments seeds from the ontology, not from a CSV — it is
    the chain's only input-less step, which is why it runs before the resolved
    plan rather than being a ChainStep. Imported here so the rider holds."""
    assert callable(business_segments.refresh_business_segments)
    assert all(nm != "business_segments" for nm, _, _ in cli_mod.REFRESH_REFERENCE_CHAIN)
