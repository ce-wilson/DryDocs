"""Guards for the UI test-case ledger (config/taxonomy/ui-tests.yaml).

Adopted from the Process/Testing domains of the Miller software-development
process model, on the condition that it works with what we already have. It
does: our :Feature layer is web/src/modules/registry.ts, so the model's
TestSuite -> Feature join is a lookup rather than a new vocabulary.

The test that matters is test_which_cases_should_i_run_after_changing — it
exercises the actual payoff chain (component -> module -> suite -> cases)
rather than merely asserting the ledger is well-formed.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml", reason="PyYAML not installed")

REPO = Path(__file__).resolve().parents[2]
UI_TESTS = REPO / "config" / "taxonomy" / "ui-tests.yaml"
UI_COMPONENTS = REPO / "config" / "taxonomy" / "ui-components.yaml"
MODULE_REGISTRY_TS = REPO / "web" / "src" / "modules" / "registry.ts"

#: the shell is deliberately not a registry module — it is the frame they render in
NON_MODULE_SUITES = {"shell"}


def _tests() -> dict:
    return yaml.safe_load(UI_TESTS.read_text(encoding="utf-8"))


def _components() -> dict:
    return yaml.safe_load(UI_COMPONENTS.read_text(encoding="utf-8"))


def _module_ids() -> set[str]:
    return set(re.findall(r"id:\s*'([a-z-]+)'", MODULE_REGISTRY_TS.read_text(encoding="utf-8")))


# --------------------------------------------------------------------------- #
# shape
# --------------------------------------------------------------------------- #
def test_schema_and_declared_joins_resolve() -> None:
    doc = _tests()
    assert doc["schema"] == "drydocs.ui-tests.v1"
    assert doc["classification"] == "Internal-Public"
    assert (REPO / doc["component_ledger"]).exists()
    assert (REPO / doc["module_registry"]).exists()
    assert doc["execution"] == "mixed", (
        "a runner landed at O80, so execution is per-case via `automated_by` — "
        "flipping this back to `manual` would deny a harness that runs in CI"
    )
    for name, path in doc["runners"].items():
        assert (REPO / path).exists(), f"runner {name} points at a missing file: {path}"


def test_every_suite_targets_a_real_module() -> None:
    valid = _module_ids() | NON_MODULE_SUITES
    bad = [(s["id"], s["module"]) for s in _tests()["suites"] if s["module"] not in valid]
    assert not bad, f"suite(s) target unknown modules: {bad} (valid: {sorted(valid)})"


def test_one_suite_per_module_and_unique_ids() -> None:
    suites = _tests()["suites"]
    ids = [s["id"] for s in suites]
    assert len(ids) == len(set(ids)), "duplicate suite id"
    mods = [s["module"] for s in suites]
    assert len(mods) == len(set(mods)), "two suites claim the same module"


def test_case_ids_are_globally_unique_and_well_formed() -> None:
    seen: set[str] = set()
    for suite in _tests()["suites"]:
        for case in suite["cases"]:
            cid = case["id"]
            assert cid not in seen, f"duplicate case id {cid}"
            seen.add(cid)
            assert case.get("description"), f"{cid} missing description"
            assert case.get("expect"), f"{cid} missing expect"
            assert case.get("steps"), f"{cid} missing steps"


def test_every_case_cites_verified_behaviour() -> None:
    """A case with no source is a case nobody has watched pass.

    The seed set was lifted from backlog close notes recording observations
    that actually happened; keeping `source` mandatory stops the ledger
    drifting into aspirational tests.
    """
    unsourced = [c["id"] for s in _tests()["suites"] for c in s["cases"] if not c.get("source")]
    assert not unsourced, f"case(s) with no verified source: {unsourced}"


# --------------------------------------------------------------------------- #
# coverage, stated as a number rather than an absence
# --------------------------------------------------------------------------- #
def test_coverage_is_pinned_so_the_gap_stays_visible() -> None:
    suites = _tests()["suites"]
    seeded = [s for s in suites if s["cases"]]
    # 3/12 -> 4/13 at O57 (2026-08-20): TS-LOADMAP arrives SEEDED, from
    # in-browser observation at the build rather than from a commit message.
    # Both numbers move together — a new module adds a suite by the
    # every-module-has-a-suite rule below, and this one is not an empty one.
    # 4/13 -> 5/13 at O66 (2026-08-21): TS-OWNERSHIP seeded from the label-
    # readability fix's own in-browser verification (laptop, headless Chrome).
    # 5/13 -> 6/13 at O64 (2026-08-21): TS-ASK seeded from the last-turn
    # persistence verification — with its stated caveat that the completed
    # turn was storage-seeded, not produced by a live agent run.
    # 6/13 -> 8/13 at O80 (2026-08-31): TS-GATES and TS-EXPLORER arrive seeded,
    # both from cases the new runners actually execute rather than from prose.
    assert (len(seeded), len(suites)) == (8, 13), (
        f"UI test coverage changed: {len(seeded)}/{len(suites)} suites seeded — "
        f"update the pin (and be glad)"
    )


# --------------------------------------------------------------------------- #
# automation, stated as a number for the same reason coverage is (O80)
# --------------------------------------------------------------------------- #
def test_automated_cases_name_a_file_that_exists() -> None:
    """`automated_by` is a claim that something RUNS this case.

    A path that has been renamed or deleted turns the ledger's most load-bearing
    new field into decoration, and the failure mode is silent: the case still
    reads as covered. Checking the file exists is the cheapest thing that makes
    the claim mean something.
    """
    missing = [
        (c["id"], c["automated_by"])
        for s in _tests()["suites"]
        for c in s["cases"]
        if c.get("automated_by") and not (REPO / c["automated_by"]).exists()
    ]
    assert not missing, f"case(s) claim automation by a missing file: {missing}"


def test_the_automated_share_is_pinned_so_it_cannot_drift_up_quietly() -> None:
    """Four of twenty-three. The point is that the number is SMALL and visible.

    O80 bought the capability and proved it on cases that had already escaped
    into main; it did not backfill coverage, and this pin is what stops a later
    session from believing it did.
    """
    cases = [c for s in _tests()["suites"] for c in s["cases"]]
    automated = [c for c in cases if c.get("automated_by")]
    assert (len(automated), len(cases)) == (
        4,
        23,
    ), f"automated case count changed: {len(automated)}/{len(cases)} — update the pin"


def test_every_console_module_has_a_suite_even_if_empty() -> None:
    """An unlisted module is an invisible gap; an empty suite is a visible one."""
    covered = {s["module"] for s in _tests()["suites"]}
    missing = sorted(_module_ids() - covered)
    assert not missing, f"console module(s) with no suite at all: {missing}"


# --------------------------------------------------------------------------- #
# THE PAYOFF: the model's headline query, on our data
# --------------------------------------------------------------------------- #
def _cases_for_component(component_id: str) -> list[str]:
    """component -> module -> suite -> case ids. The whole point of the join."""
    comp = next((c for c in _components()["components"] if c["id"] == component_id), None)
    if comp is None or not comp.get("module"):
        return []
    suite = next((s for s in _tests()["suites"] if s["module"] == comp["module"]), None)
    return [c["id"] for c in suite["cases"]] if suite else []


def test_which_cases_should_i_run_after_changing_a_component() -> None:
    """'I changed LoadsTimeline — what do I re-test?'"""
    assert _cases_for_component("LoadsTimeline") == ["TC-LOADS-01", "TC-LOADS-02"]
    assert _cases_for_component("LoadsRoute") == ["TC-LOADS-01", "TC-LOADS-02"]
    # a module whose suite is declared but unseeded resolves to nothing YET —
    # correctly empty rather than falsely reassuring
    assert _cases_for_component("LineageGraphPane") == []


def test_shared_components_resolve_to_nothing_and_that_is_honest() -> None:
    """The 36 unbound components cannot answer this question.

    StatTiles is used BY the loads module (TC-LOADS-01 exercises it) but lives
    in the shared component folder, so no evidence-based module binding exists
    for it. Reaching it needs import edges — O42's TS resolver. Pinned so the
    limitation is explicit rather than discovered later by someone trusting an
    empty result.
    """
    assert _cases_for_component("StatTiles") == []
    assert _cases_for_component("Shell") == []
