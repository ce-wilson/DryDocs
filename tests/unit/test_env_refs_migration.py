"""G128 — the resolvers now read through the one expansion function.

G125 shipped the function, the declared list and the masking, and deliberately
left the resolvers on their own semantics because each raised a type other tests
catch by name. This file guards the migration that finished it, and it guards the
two things the migration could quietly have broken: the ruled behavior (G81
clause (d)) and the declared-variable guard itself (clause (d) — "if the
migration needs that test relaxed, stop and say why").
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest
import yaml

from drydocs_core import data_root, env_refs, log_kinds
from tests.source_scan import code_only, source_text

REPO = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# (a) THE DESIGN DECISION, made before anything moved and asserted here
# ---------------------------------------------------------------------------
def test_the_resolver_error_subclasses_the_generic_one() -> None:
    """SUBCLASS, not replace — the decision recorded in G128 clause (a).

    Two catch sites (``drydocs/cli.py``, ``drydocs/cli_ingest.py``) catch the
    data root's OWN type to print its own remediation. One flat type would have
    made an unset ``NEO4J_PASSWORD`` print advice about the data root — a
    regression wearing a refactor's clothes.
    """
    assert issubclass(data_root.DataRootNotSetError, env_refs.UnsetVariableError)
    assert data_root.DataRootNotSetError is not env_refs.UnsetVariableError


def test_the_family_catch_works_and_the_specific_one_still_discriminates(
    monkeypatch,
) -> None:
    monkeypatch.delenv("DRYDOCS_DATA_ROOT", raising=False)
    with pytest.raises(env_refs.UnsetVariableError):
        data_root.resolve_data_root()
    with pytest.raises(data_root.DataRootNotSetError):
        data_root.resolve_data_root()
    # and the generic error is NOT caught by the specific handler
    assert not isinstance(
        env_refs.UnsetVariableError("x"), data_root.DataRootNotSetError
    ), "the specific type must stay narrower than the family, or the split buys nothing"


# ---------------------------------------------------------------------------
# (b) THE RESOLVERS MOVED — no module reads os.environ for a declared variable
# ---------------------------------------------------------------------------
MIGRATED = (
    "drydocs_core/data_root.py",
    "drydocs_api/credentials.py",
    "drydocs/loaders/manual_loads.py",
    "drydocs/loaders/seal_contacts.py",
    "drydocs_api/mappings.py",
)


def test_the_migrated_resolvers_no_longer_read_the_environment_directly() -> None:
    """Read the SOURCE, because the point is that the lookup is gone.

    ``log_kinds.resolve_env_override`` deliberately keeps its own
    ``os.environ`` read and is excluded — see the rationale test below.
    """
    for rel in MIGRATED:
        source = code_only(source_text(rel, REPO))
        assert "os.environ" not in source.replace(" ", ""), (
            f"{rel} still reads os.environ directly. The whole of G125 clause (c) "
            "is that one function does the lookup, so seven private ones cannot "
            "disagree about what 'unset' means."
        )


def test_every_migrated_module_uses_the_declared_accessor() -> None:
    for rel in MIGRATED:
        assert "resolve_optional" in code_only(
            source_text(rel, REPO)
        ), f"{rel} does not read through env_refs"


def test_mapping_store_itself_never_read_the_environment() -> None:
    """A correction to G128's own clause (b), recorded as a test.

    The item says ``MappingStore.__init__`` imports ``os`` inside its constructor
    to read one variable. It does not, and did not: ``drydocs_core/mapping_store.py``
    reads no environment variable at all. The three reads live at component call
    sites (``manual_loads``, ``seal_contacts``, ``drydocs_api/mappings``), which
    is where the migration went.
    """
    code = code_only(source_text("drydocs_core/mapping_store.py", REPO)).replace(" ", "")
    assert "os.environ" not in code
    assert "importos" not in code


# ---------------------------------------------------------------------------
# (c) RULED BEHAVIOUR IS PRESERVED EXACTLY
# ---------------------------------------------------------------------------
def test_an_unset_data_root_still_fails_naming_the_variable(monkeypatch) -> None:
    """G81 (d): FAIL, never a silent relocation. The message is the remediation."""
    monkeypatch.delenv("DRYDOCS_DATA_ROOT", raising=False)
    with pytest.raises(data_root.DataRootNotSetError) as info:
        data_root.resolve_data_root()
    message = str(info.value)
    assert "DRYDOCS_DATA_ROOT" in message
    assert str(data_root.DEFAULT_DATA_ROOT) in message, (
        "the conventional location is still SUGGESTED even though nothing resolves "
        "to it implicitly — that is the whole shape of G81 (d)"
    )


def test_a_whitespace_only_data_root_is_unset(monkeypatch) -> None:
    """The empty-string semantics G125 catalogued, preserved through the move."""
    monkeypatch.setenv("DRYDOCS_DATA_ROOT", "   ")
    with pytest.raises(data_root.DataRootNotSetError):
        data_root.resolve_data_root()


def test_no_default_operator_entered_at_any_layer() -> None:
    """The expander refuses bash defaults; the migration must not smuggle one in."""
    for rel in (*MIGRATED, "drydocs_core/env_refs.py", "drydocs_core/log_kinds.py"):
        code = code_only(source_text(rel, REPO))
        assert ":-" not in code.replace(" ", ""), (
            f"{rel} appears to use a bash default operator in CODE (its prose may "
            "name one -- env_refs documents the operator it refuses)"
        )


def test_the_log_root_order_is_unchanged(monkeypatch, tmp_path) -> None:
    """Primary wins over legacy; legacy still resolves; default is last."""
    monkeypatch.delenv("DRYDOCS_LOGDIR", raising=False)
    monkeypatch.delenv("SPIDERP_LOGDIR", raising=False)
    fallback = tmp_path / "fallback"
    assert log_kinds.resolve_root(default=fallback) == fallback

    monkeypatch.setenv("SPIDERP_LOGDIR", str(tmp_path / "legacy"))
    with pytest.warns(DeprecationWarning, match="SPIDERP_LOGDIR"):
        assert log_kinds.resolve_root(default=fallback) == tmp_path / "legacy"

    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "primary"))
    assert log_kinds.resolve_root(default=fallback) == tmp_path / "primary"


# ---------------------------------------------------------------------------
# (d) THE GUARD THAT HOLDS THE LINE STAYS GREEN AND IS NOT WEAKENED
# ---------------------------------------------------------------------------
def test_the_declared_variable_guard_still_reads_importable_objects() -> None:
    """Clause (d): it must not have been relaxed to fit the migration.

    The test it names lives in test_source_bindings.py and reads the settings
    classes' ``env_prefix`` plus their fields — because no grep can see
    ``NEO4J_URI`` when the prefix composes it (J37). Assert that shape survives.
    """
    source = (REPO / "tests" / "unit" / "test_source_bindings.py").read_text(encoding="utf-8")
    assert "test_every_variable_first_party_code_reads_is_declared" in source
    assert "env_prefix" in source and "model_fields" in source, (
        "the guard stopped reading the importable settings objects, which is the "
        "only way it can see a prefix-composed variable name"
    )


def test_resolve_env_override_keeps_its_own_lookup_and_says_why() -> None:
    """The one place the declared-list check is deliberately ABSENT (clause d).

    The first attempt raised from here for an undeclared name and broke
    ``test_resolve_honors_env_when_set_and_falls_back_when_empty_or_unset``,
    which drives the mechanism with a synthetic probe. That test was right: this
    function answers "is this NAME set", and a caller naming its own variable is
    legitimate. The rationale is required to stay in the source so the next
    person does not re-add the guard and re-break the test.
    """
    source = inspect.getsource(log_kinds.resolve_env_override)
    assert "G128" in source, "the reason this check is absent must stay recorded here"
    assert "os.environ" in source, "and the direct lookup is the deliberate part"


def test_committed_declarations_reference_only_declared_variables() -> None:
    """Where the check DOES belong: the committed config, not the resolver.

    ``config/log-kinds.yaml``'s root and every ``env:`` in
    ``config/data-zones.yaml`` name variables that first-party code will read, so
    each must appear in DECLARED_VARIABLES. A synthetic probe in a test is not a
    committed declaration and is correctly out of scope here.
    """
    names: set[str] = set()
    kinds = yaml.safe_load((REPO / "config" / "log-kinds.yaml").read_text(encoding="utf-8"))
    root = kinds.get("root") or {}
    names |= {n for n in (root.get("env"), root.get("legacy_env")) if n}

    zones = yaml.safe_load((REPO / "config" / "data-zones.yaml").read_text(encoding="utf-8"))
    for zone in zones.get("zones") or []:
        if zone.get("env"):
            names.add(zone["env"])

    assert names, "precondition: the committed declarations must name some variables"
    undeclared = sorted(
        n
        for n in names
        if env_refs.declared(n) is None
        and not any(n in v.aliases for v in env_refs.DECLARED_VARIABLES)
    )
    assert not undeclared, (
        "committed declaration(s) name undeclared variable(s): "
        + ", ".join(undeclared)
        + " — add each to DECLARED_VARIABLES in drydocs_core/env_refs.py."
    )


def test_the_legacy_alias_agrees_between_its_two_declarations() -> None:
    """``config/log-kinds.yaml``'s ``legacy_env`` and the EnvVar alias are one fact.

    Two declarations of one alias chain is a drift risk; this is the guard that
    makes them agree rather than a third place to keep them in step by hand.
    """
    kinds = yaml.safe_load((REPO / "config" / "log-kinds.yaml").read_text(encoding="utf-8"))
    root = kinds.get("root") or {}
    primary, legacy = root.get("env"), root.get("legacy_env")
    assert primary and legacy, "precondition: the declaration carries both names"

    var = env_refs.declared(primary)
    assert var is not None, f"{primary} is not declared"
    assert legacy in var.aliases, (
        f"config/log-kinds.yaml declares {legacy!r} as the legacy alias of {primary!r}, "
        f"but env_refs declares aliases {var.aliases}. One fact, two declarations, "
        "now disagreeing."
    )


# ---------------------------------------------------------------------------
# the optional read, which is the new part of the surface
# ---------------------------------------------------------------------------
def test_resolve_optional_reports_which_name_answered(monkeypatch) -> None:
    """The log resolver can only warn about the legacy alias if the lookup says so."""
    monkeypatch.delenv("DRYDOCS_LOGDIR", raising=False)
    monkeypatch.setenv("SPIDERP_LOGDIR", "/somewhere")
    value, which = env_refs.resolve_optional("DRYDOCS_LOGDIR", where="test")
    assert value == "/somewhere"
    assert which == "SPIDERP_LOGDIR"


def test_resolve_optional_refuses_an_undeclared_name() -> None:
    """Having a default is not an exemption from being enumerable."""
    with pytest.raises(env_refs.UndeclaredVariableError):
        env_refs.resolve_optional("NOT_A_DECLARED_VARIABLE", where="test")


def test_resolve_optional_registers_a_secret(monkeypatch) -> None:
    """A value read here is as real as a value read through expand()."""
    env_refs.reset_secret_registry()
    monkeypatch.setenv("DRYDOCS_CONSOLE_CREDENTIALS", "/tmp/secret-path-value")
    try:
        env_refs.resolve_optional("DRYDOCS_CONSOLE_CREDENTIALS", where="test")
        assert "********" in env_refs.mask("path=/tmp/secret-path-value")
    finally:
        env_refs.reset_secret_registry()


def test_resolve_optional_returns_none_when_unset(monkeypatch) -> None:
    monkeypatch.delenv("DRYDOCS_LOGDIR", raising=False)
    monkeypatch.delenv("SPIDERP_LOGDIR", raising=False)
    assert env_refs.resolve_optional("DRYDOCS_LOGDIR", where="test") == (None, None)
