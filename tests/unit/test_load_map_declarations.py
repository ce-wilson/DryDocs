"""N3 — the three declared joins a load map is built from, guarded.

(1) loader -> source: every concrete BaseLoader subclass declares a
    ``source_id`` resolving to a config/source-registry.yaml id, or is a
    NAMED exemption with a written reason (cli.SOURCELESS_LOADERS) — never
    a silent omission.
(2) command -> loaders: cli.COMMAND_LOADERS declares which loaders each
    Typer command runs, in order; the chain constants it derives from are
    the same objects the command bodies consume, so declaration == behavior.
(3) the ONE canonical ordered load sequence: cli.CANONICAL_LOAD_SEQUENCE —
    every step a real registered command (ingest.sh and the startup/refresh
    runbook derive from it at N6).

Discovery walks the drydocs.loaders package, so a NEW loader module is
covered the moment it exists — an undeclared source_id fails here by name.
"""

from __future__ import annotations

import importlib
import pkgutil

import drydocs.loaders as loaders_pkg
from drydocs import cli
from drydocs.loaders.base import BaseLoader
from drydocs_core.source_registry import SourceRegistry


def _all_loader_classes() -> set[type]:
    """Every BaseLoader subclass defined under drydocs/loaders (recursive)."""
    for mod in pkgutil.iter_modules(loaders_pkg.__path__):
        importlib.import_module(f"{loaders_pkg.__name__}.{mod.name}")

    found: set[type] = set()

    def _walk(cls: type) -> None:
        for sub in cls.__subclasses__():
            if sub.__module__.startswith(loaders_pkg.__name__):
                found.add(sub)
            _walk(sub)

    _walk(BaseLoader)
    return found


def _concrete_loader_classes() -> set[type]:
    """Leading-underscore classes are abstract bases by convention."""
    return {c for c in _all_loader_classes() if not c.__name__.startswith("_")}


def _registered_command_names() -> set[str]:
    names: set[str] = set()
    for info in cli.app.registered_commands:
        names.add(info.name or info.callback.__name__.replace("_", "-"))
    return names


REGISTRY_IDS = frozenset(SourceRegistry.from_yaml().ids())


# ---- (1) loader -> source ----------------------------------------------------


def test_every_concrete_loader_declares_a_source_or_is_named_exempt():
    missing = sorted(
        cls.__name__
        for cls in _concrete_loader_classes()
        if cls.source_id is None and cls not in cli.SOURCELESS_LOADERS
    )
    assert not missing, (
        "Concrete loader(s) with no source_id and no SOURCELESS_LOADERS "
        f"exemption: {missing} — declare the source-registry id on the class "
        "or add a named exemption with a written reason (N3: no silent "
        "omissions)."
    )


def test_sourceless_exemptions_are_real_and_carry_reasons():
    concrete = _concrete_loader_classes()
    for cls, reason in cli.SOURCELESS_LOADERS.items():
        assert cls in concrete, (
            f"SOURCELESS_LOADERS names {cls.__name__}, which is not a concrete "
            "loader under drydocs/loaders — stale exemption."
        )
        assert cls.source_id is None, (
            f"{cls.__name__} declares source_id={cls.source_id!r} AND sits in "
            "SOURCELESS_LOADERS — pick one."
        )
        assert isinstance(reason, str) and len(reason.strip()) >= 20, (
            f"SOURCELESS_LOADERS[{cls.__name__}] needs a written reason, not "
            f"{reason!r} — reason-less exemptions are the silent omission "
            "this guard exists to end."
        )


def test_declared_source_ids_resolve_in_the_registry():
    unresolved = sorted(
        f"{cls.__name__} -> {cls.source_id}"
        for cls in _concrete_loader_classes()
        if cls.source_id is not None and cls.source_id not in REGISTRY_IDS
    )
    assert not unresolved, f"source_id(s) not in config/source-registry.yaml: {unresolved}"


def test_loader_source_projection_matches_the_class_declarations():
    """LOADER_SOURCE must stay a projection of the classes (D3 gate input)."""
    derived = {
        name: cls.source_id
        for name, cls in cli.LOADER_REGISTRY.items()
        if cls.source_id is not None
    }
    assert cli.LOADER_SOURCE == derived, (
        "cli.LOADER_SOURCE has drifted from the loader classes' own source_id "
        "declarations — it is derived, never hand-maintained (N3)."
    )


def test_every_registry_runnable_loader_declares_a_source():
    """`drydocs load <name>` gates on LOADER_SOURCE — a registry loader with
    no source_id would skip the D3 confirmed-gate silently."""
    ungated = sorted(name for name, cls in cli.LOADER_REGISTRY.items() if cls.source_id is None)
    assert not ungated, f"LOADER_REGISTRY loader(s) with no source_id: {ungated}"


# ---- (2) command -> loaders --------------------------------------------------


def test_command_loaders_name_real_commands_and_real_loaders():
    registered = _registered_command_names()
    concrete = _concrete_loader_classes()
    for command, loader_classes in cli.COMMAND_LOADERS.items():
        assert command in registered, (
            f"COMMAND_LOADERS declares {command!r}, which is not a registered " "Typer command."
        )
        assert loader_classes, f"COMMAND_LOADERS[{command!r}] is empty."
        for cls in loader_classes:
            assert cls in concrete, (
                f"COMMAND_LOADERS[{command!r}] names {cls.__name__}, not a "
                "concrete loader under drydocs/loaders."
            )


def test_chain_constants_agree_with_the_loader_registry():
    """The (cli name, class) pairs in the chain constants must be the SAME
    binding LOADER_REGISTRY carries — a renamed key or swapped class here
    would run one loader while reporting another."""
    pairs = [(nm, cls) for nm, cls, _ in cli.chain_steps()]
    pairs += [
        (nm, cls)
        for nm, cls, *_ in (
            cli.CONTROLM_NODE_STAGES + cli.CONTROLM_PART2_STAGES + cli.CONTROLM_REL_STAGES
        )
    ]
    for nm, cls in pairs:
        assert nm in cli.LOADER_REGISTRY, f"chain name {nm!r} not in LOADER_REGISTRY"
        assert cli.LOADER_REGISTRY[nm] is cls, (
            f"chain binds {nm!r} to {cls.__name__} but LOADER_REGISTRY binds "
            f"it to {cli.LOADER_REGISTRY[nm].__name__}"
        )


def test_every_concrete_loader_is_reachable_or_ad_hoc():
    """No orphans: every concrete loader is run by a declared command or is
    runnable ad hoc via `drydocs load` (LOADER_REGISTRY)."""
    reachable: set[type] = set(cli.LOADER_REGISTRY.values())
    for loader_classes in cli.COMMAND_LOADERS.values():
        reachable.update(loader_classes)
    orphans = sorted(cls.__name__ for cls in _concrete_loader_classes() if cls not in reachable)
    assert not orphans, (
        f"Concrete loader(s) no declared command runs and `load` cannot reach: "
        f"{orphans} — declare them in COMMAND_LOADERS or LOADER_REGISTRY."
    )


# ---- G80: registry membership alone is not reachability ----------------------


def test_no_registry_loader_is_silently_unchained():
    """G80: the test above accepts bare LOADER_REGISTRY membership, which is
    exactly how area_products and pat_team_roles sat runnable-by-name while no
    operator path ever ran them. A registry loader in NO command's chain fails
    BY NAME unless cli.UNCHAINED_LOADER_EXCLUSIONS carries its written reason
    (the G59 unchained-supplement guard, one registry over)."""
    missing = cli.unchained_loaders()
    assert not missing, (
        f"LOADER_REGISTRY loader(s) no declared command runs and no written "
        f"reason excuses: {list(missing)} — wire each into a COMMAND_LOADERS "
        "chain or add it to UNCHAINED_LOADER_EXCLUSIONS with a written reason."
    )


def test_unchained_exclusions_are_real_unchained_and_carry_reasons():
    """Exclusion hygiene (the SCHEDULED_INGEST_EXCLUSIONS idiom): every entry
    names a registry loader (else stale), one that is NOT in any chain (else
    contradictory — this is what forces G79 to delete the exclusion when it
    wires the orphan), and carries a sentence, not a token."""
    chained = {cls for classes in cli.COMMAND_LOADERS.values() for cls in classes}
    for name, reason in cli.UNCHAINED_LOADER_EXCLUSIONS.items():
        assert name in cli.LOADER_REGISTRY, f"stale exclusion: {name!r} not in LOADER_REGISTRY"
        assert cli.LOADER_REGISTRY[name] not in chained, (
            f"{name!r} is excluded AND chained — contradictory; delete the " "exclusion"
        )
        assert len(reason.split()) >= 5, f"{name!r}: the reason must be a sentence, not a token"


def test_unchained_detection_names_the_loader(monkeypatch):
    """The guard actually fires: a registry entry no chain runs is reported by
    NAME, not swallowed into a count — repo-agnostic (a synthetic orphan, not a
    pinned producer membership, so the consumer repo's differing chains pass)."""

    class _OrphanProbeLoader:
        pass

    monkeypatch.setitem(cli.LOADER_REGISTRY, "orphan_probe", _OrphanProbeLoader)
    assert "orphan_probe" in cli.unchained_loaders()
    # and the excused set stays out of the failure list
    for name in cli.UNCHAINED_LOADER_EXCLUSIONS:
        assert name not in cli.unchained_loaders()


def test_generated_sample_declarations_are_real_and_carry_reasons():
    """GENERATED_SAMPLE_FILES hygiene: every entry names a file some chain
    actually declares (else stale), and says how to build it."""
    declared = {sample for _nm, _cls, sample in cli.chain_steps()}
    declared |= {
        sample
        for _nm, _cls, sample, _sql in (
            cli.CONTROLM_NODE_STAGES + cli.CONTROLM_PART2_STAGES + cli.CONTROLM_REL_STAGES
        )
    }
    for filename, reason in cli.GENERATED_SAMPLE_FILES.items():
        assert (
            filename in declared
        ), f"stale GENERATED_SAMPLE_FILES entry: {filename!r} is declared by no chain"
        assert len(reason.split()) >= 5, f"{filename!r}: say how to build it, not a token"


# ---- (3) the canonical sequence ---------------------------------------------


def test_sequence_steps_are_real_commands_with_valid_modes():
    registered = _registered_command_names()
    seen: set[str] = set()
    for step in cli.CANONICAL_LOAD_SEQUENCE:
        assert step.command in registered, (
            f"CANONICAL_LOAD_SEQUENCE step {step.command!r} is not a registered " "Typer command."
        )
        assert step.command not in seen, f"duplicate sequence step {step.command!r}"
        seen.add(step.command)
        assert step.mode in (
            "standing",
            "optional",
            "gated",
        ), f"step {step.command!r}: mode {step.mode!r} not in standing|optional|gated"
        assert step.note.strip(), f"step {step.command!r}: empty note"


def test_loader_commands_are_sequenced_or_declared_ad_hoc():
    """NOTE the direction: this walks COMMAND_LOADERS, so it only ever reaches
    LOADER-backed verbs. Non-loader steps are checked from the operator surfaces
    inward by tests/unit/test_load_sequence_surfaces.py (N6) — that asymmetry is
    how `bootstrap-schema-graph` stayed undeclared while both surfaces ran it."""
    sequenced = {step.command for step in cli.CANONICAL_LOAD_SEQUENCE}
    stray = sorted(
        command
        for command in cli.COMMAND_LOADERS
        if command not in sequenced and command not in cli.AD_HOC_COMMANDS
    )
    assert not stray, (
        f"Loader-running command(s) neither in CANONICAL_LOAD_SEQUENCE nor "
        f"declared AD_HOC: {stray} — place them, don't drop them (N3)."
    )


def test_ad_hoc_commands_are_real():
    registered = _registered_command_names()
    for command in cli.AD_HOC_COMMANDS:
        assert (
            command in registered
        ), f"AD_HOC_COMMANDS names {command!r}, not a registered command."
