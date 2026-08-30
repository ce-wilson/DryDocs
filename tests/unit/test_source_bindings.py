"""G125 — the binding table, its reference guards, and the publish boundary.

WHAT THESE TESTS ARE FOR. A binding declares how to REACH a carrier, and the one
thing that must never happen is a real host, service name, SID or credential
landing in a committed file (CLAUDE.md §3). The schema is shape-only and
permissive by design (S6), so a bad value would validate silently — the test is
the enforcement, not the schema.

They also enforce the two-direction reference guard ADR 0017 clause 4 makes part
of its ruling. DataHub ships the same standalone-profile shape and omits exactly
this link: its connection entity declares no relationship to any dataset, so a
profile nothing references is a profile nothing can audit. That omission is the
argument for the guard, so it is named here rather than assumed.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from drydocs_core import env_refs
from drydocs_core.source_bindings import (
    BROKEN,
    DECLARED_UNCONFIGURED,
    NOT_CONFIGURED_HERE,
    VERDICTS,
    BindingError,
    ConnectionProfile,
    load_profiles,
    load_unbound,
    report,
    reports,
)

REPO = Path(__file__).resolve().parents[2]
REGISTRY = REPO / "config" / "source-registry.yaml"
BINDINGS = REPO / "config" / "source-bindings.yaml"


def _registry() -> dict:
    return yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# (f) the reference is guarded IN BOTH DIRECTIONS
# ---------------------------------------------------------------------------
def test_every_system_row_declares_a_binding() -> None:
    """`binding:` is required, because silence is the defect this item closes."""
    missing = [s["id"] for s in _registry()["systems"] if "binding" not in s]
    assert not missing, (
        "system row(s) with no `binding:` key: "
        + ", ".join(missing)
        + " — a system either names a connection profile or declares `~` with a reason "
        "in source-bindings.yaml `unbound:`. Undeclared is what made 'which sources "
        "resolve through nothing' an investigation."
    )


def test_every_named_profile_exists() -> None:
    """A row naming a profile that does not exist FAILS."""
    known = {p.id for p in load_profiles()}
    dangling = [
        (s["id"], s["binding"])
        for s in _registry()["systems"]
        if s.get("binding") and s["binding"] not in known
    ]
    assert not dangling, f"system row(s) naming an unknown profile: {dangling}"


def test_every_profile_is_named_by_a_row() -> None:
    """A profile no row references is REPORTED — the DataHub omission, guarded."""
    referenced = {s.get("binding") for s in _registry()["systems"]}
    orphans = [p.id for p in load_profiles() if p.id not in referenced]
    assert not orphans, (
        "profile(s) no system row names: "
        + ", ".join(orphans)
        + " — a profile nothing references is a profile nothing can audit."
    )


def test_every_unbound_system_declares_its_reason() -> None:
    """`binding: ~` requires an `unbound:` entry. A system in neither list fails."""
    reasons = {u.carrier for u in load_unbound()}
    unexplained = [
        s["id"] for s in _registry()["systems"] if not s.get("binding") and s["id"] not in reasons
    ]
    assert not unexplained, (
        "system(s) with `binding: ~` and no reason in source-bindings.yaml `unbound:`: "
        + ", ".join(unexplained)
    )


def test_no_unbound_entry_names_a_bound_carrier() -> None:
    """The two lists are disjoint, so a carrier cannot be both."""
    bound = {p.carrier for p in load_profiles()}
    both = sorted(bound & {u.carrier for u in load_unbound()})
    assert not both, f"carrier(s) both bound and declared unbound: {both}"


def test_every_automated_dataset_sits_on_a_bound_carrier() -> None:
    """The fifteen resolve through something now. This is the item's headline."""
    systems = {s["id"]: s for s in _registry()["systems"]}
    unbound_rows = [
        row["id"]
        for row in _registry()["datasets"]
        if (row.get("acquisition") or {}).get("mode") == "automated"
        and not systems.get(row.get("system"), {}).get("binding")
    ]
    assert not unbound_rows, "automated dataset(s) whose carrier declares no binding: " + ", ".join(
        unbound_rows
    )


# ---------------------------------------------------------------------------
# (d) + (g) NO VALUE THAT IS SECRET LANDS IN COMMITTED YAML
# ---------------------------------------------------------------------------
def test_every_profile_env_entry_is_a_bare_reference() -> None:
    """The $-prefix write guard (ADR 0017 clause 6).

    A credential-keyed field holds a ${NAME} reference or nothing at all. This is
    the enforcement of a rule this repo states and NEITHER peer product has:
    DataHub has no normative prohibition and no sanitizer in either language, and
    OpenLineage has one Java implementation and no rule.
    """
    doc = yaml.safe_load(BINDINGS.read_text(encoding="utf-8"))
    for prof in doc.get("profiles") or []:
        for key, ref in (prof.get("env") or {}).items():
            assert env_refs.is_reference(str(ref)), (
                f"profile {prof['id']!r} field {key!r} holds {ref!r}. A binding names "
                "variables and never holds a host, service name, SID or credential."
            )


def test_profile_load_refuses_a_literal_value() -> None:
    """The guard fires at LOAD, not only in a test — a bad file cannot be used."""
    bad = BINDINGS.parent / "_bad-bindings.yaml"
    bad.write_text(
        "schema: drydocs.source-bindings.v1\n"
        "profiles:\n"
        "  - id: leaky\n"
        "    carrier: x\n"
        "    env:\n"
        '      dsn: "realhost.example.com:1521/PROD"\n',
        encoding="utf-8",
    )
    try:
        with pytest.raises(BindingError, match="not a .* reference"):
            load_profiles(bad)
    finally:
        bad.unlink()


def test_bindings_file_carries_no_credential_shaped_literal() -> None:
    """Belt and braces: no host:port, no URI, no obvious secret anywhere."""
    text = BINDINGS.read_text(encoding="utf-8")
    for needle in ("password:", "://"):
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or needle not in line:
                continue
            assert "${" in line, f"credential-shaped literal in a committed binding: {line!r}"


def test_every_profile_declares_a_classification() -> None:
    """CLAUDE.md §3 — there is no unlabeled default."""
    for prof in load_profiles():
        assert prof.classification, f"profile {prof.id!r} declares no classification"


# ---------------------------------------------------------------------------
# (c) the expander: substitutes, refuses defaults, registers secrets
# ---------------------------------------------------------------------------
def test_expander_refuses_a_bash_default() -> None:
    """REFUSED, not unimplemented — G81 (d) at the syntax level."""
    with pytest.raises(env_refs.MalformedRefError, match="default operator"):
        env_refs.expand("${DRYDOCS_DATA_ROOT:-/tmp/somewhere}", where="test")


def test_expander_refuses_an_undeclared_variable() -> None:
    with pytest.raises(env_refs.UndeclaredVariableError):
        env_refs.expand("${TOTALLY_UNDECLARED_VAR}", where="test")


def test_expander_error_names_the_variable_and_the_row(monkeypatch) -> None:
    monkeypatch.delenv("ORACLE_DSN", raising=False)
    with pytest.raises(env_refs.UnsetVariableError) as excinfo:
        env_refs.expand("${ORACLE_DSN}", where="profile 'oracle-psgmgr' field 'dsn'")
    message = str(excinfo.value)
    assert "ORACLE_DSN" in message and "oracle-psgmgr" in message


def test_expansion_registers_a_secret_for_masking(monkeypatch) -> None:
    """Rider (ii): masking is created at expansion, not at each print site."""
    env_refs.reset_secret_registry()
    monkeypatch.setenv("ORACLE_PASSWORD", "hunter2-not-real")
    try:
        env_refs.expand("${ORACLE_PASSWORD}", where="test")
        assert "hunter2-not-real" not in env_refs.mask("dsn=hunter2-not-real trailing")
        assert "********" in env_refs.mask("dsn=hunter2-not-real trailing")
    finally:
        env_refs.reset_secret_registry()


def test_a_non_secret_variable_is_not_registered(monkeypatch) -> None:
    """Masking follows the DECLARATION, never a guess from the name."""
    env_refs.reset_secret_registry()
    monkeypatch.setenv("ORACLE_USER", "reporting_ro")
    try:
        env_refs.expand("${ORACLE_USER}", where="test")
        assert env_refs.mask("user=reporting_ro") == "user=reporting_ro"
    finally:
        env_refs.reset_secret_registry()


def test_every_variable_first_party_code_reads_is_declared() -> None:
    """The enumerable list is LOAD-BEARING, not a doc (G125 (c)).

    ``.env.example`` declared 17 keys while first-party code read 8 more that were
    declared nowhere, and nothing could have caught it: this reads the IMPORTABLE
    objects, never a grep (J37). It has to, because ``config.py`` uses
    pydantic-settings ``env_prefix``, so ``NEO4J_URI`` never appears as a literal
    anywhere — a text search sees a prefix and misses the field, which is exactly
    how a variable stays undeclared.
    """
    from drydocs_api.credentials import PATH_ENV_VAR
    from drydocs_core.adapters.controlm.api import CFG_ENV
    from drydocs_core.config import Neo4jSettings, OracleSettings, RuntimeSettings
    from drydocs_core.data_root import DATA_ROOT_ENV
    from drydocs_core.run_log import (
        CALLER_ENV,
        LEGACY_CALLER_ENV,
        LEGACY_LOGDIR_ENV,
        LOGDIR_ENV,
    )

    names: set[str] = {
        DATA_ROOT_ENV,
        LOGDIR_ENV,
        LEGACY_LOGDIR_ENV,
        CALLER_ENV,
        LEGACY_CALLER_ENV,
        PATH_ENV_VAR,
        CFG_ENV,
        "DRYDOCS_MAPPING_DB",
        "DRYDOCS_MAPPING_READ",
        "DRYDOCS_AGENT_REG_KEY",
    }
    for settings in (Neo4jSettings, OracleSettings, RuntimeSettings):
        prefix = settings.model_config.get("env_prefix", "")
        names |= {f"{prefix}{field}".upper() for field in settings.model_fields}

    undeclared = sorted(
        name
        for name in names
        if env_refs.declared(name) is None
        and not any(name in var.aliases for var in env_refs.DECLARED_VARIABLES)
    )
    assert not undeclared, (
        "variable(s) first-party code reads that DECLARED_VARIABLES does not cover: "
        + ", ".join(undeclared)
        + " — add each to drydocs_core/env_refs.py with its purpose and whether it is "
        "secret. A list that lags the code is the state this item found."
    )


def test_every_referenced_variable_is_declared() -> None:
    """A binding cannot introduce a variable by using it."""
    for prof in load_profiles():
        for name in prof.variables:
            assert env_refs.declared(name) is not None, (
                f"profile {prof.id!r} references ${{{name}}}, which is in no declaration. "
                "Eight variables came to be read by code and declared nowhere exactly "
                "this way."
            )


# ---------------------------------------------------------------------------
# (b) the report: scope, direction and the three verdict classes
# ---------------------------------------------------------------------------
def test_unset_binding_is_a_state_and_never_a_failure(monkeypatch) -> None:
    """RULE (i): configured-on-this-machine only.

    The two machines hold different subsets. Scoring the other machine's binding
    red would make the check noise, and noise is how the original coverage lie
    survived.
    """
    for name in ("ORACLE_USER", "ORACLE_PASSWORD", "ORACLE_DSN"):
        monkeypatch.delenv(name, raising=False)
    got = report(
        ConnectionProfile(
            id="p",
            carrier="c",
            platform="oracle-db",
            classification="Internal",
            env={"dsn": "${ORACLE_DSN}"},
            serves=1,
            note="",
        ),
        datasets=1,
    )
    assert got.verdict == NOT_CONFIGURED_HERE
    assert got.is_failure is False
    assert got.unset == ("ORACLE_DSN",)


def test_a_profile_with_no_variables_is_declared_not_absent() -> None:
    """RULE (i) again: 'declared, no variables' is visible, which is the point."""
    got = report(
        ConnectionProfile(
            id="p",
            carrier="c",
            platform="snowflake",
            classification="Internal",
            env={},
            serves=3,
            note="",
        ),
        datasets=3,
    )
    assert got.verdict == DECLARED_UNCONFIGURED
    assert got.is_failure is False


def test_the_walk_starts_at_registration_not_at_env(monkeypatch) -> None:
    """RULE (ii): side (A) is never tested.

    The first stage is always ``registered``, and no stage asserts a variable's
    VALUE is correct — only that it resolves.
    """
    monkeypatch.setenv("ORACLE_DSN", "anything-at-all")
    got = report(
        ConnectionProfile(
            id="p",
            carrier="c",
            platform="oracle-db",
            classification="Internal",
            env={"dsn": "${ORACLE_DSN}"},
            serves=1,
            note="",
        ),
        datasets=1,
        adapter_built=True,
        loaded=True,
    )
    assert got.stages[0].stage == "registered"
    assert got.verdict != BROKEN


def test_the_walk_stops_at_the_first_unbuilt_stage(monkeypatch) -> None:
    """RULE (iii): not-built-yet is a third class, and the stage is NAMED."""
    monkeypatch.setenv("ORACLE_DSN", "anything-at-all")
    got = report(
        ConnectionProfile(
            id="p",
            carrier="c",
            platform="oracle-db",
            classification="Internal",
            env={"dsn": "${ORACLE_DSN}"},
            serves=1,
            note="",
        ),
        datasets=1,
        adapter_built=False,
    )
    assert got.stopped_at == "adapter"
    assert got.is_failure is False
    assert "loaded" not in [s.stage for s in got.stages]


def test_every_report_names_its_venue() -> None:
    """J18 as a return value: an untagged claim reads as a defect elsewhere."""
    for rep in reports():
        assert rep.venue
        assert rep.verdict in VERDICTS


def test_live_registry_produces_no_broken_binding() -> None:
    """The committed table is well-formed here, whatever this machine configures."""
    assert [r.carrier for r in reports() if r.is_failure] == []


def test_reports_cover_every_automated_dataset() -> None:
    """15 automated rows, all accounted for by a profile."""
    total = sum(r.datasets for r in reports())
    expected = sum(
        1
        for row in _registry()["datasets"]
        if (row.get("acquisition") or {}).get("mode") == "automated"
    )
    assert total == expected == 15


# ---------------------------------------------------------------------------
# (e) the stale prose that started this
# ---------------------------------------------------------------------------
def test_no_locator_advertises_a_data_root_default() -> None:
    """G81 (d) removed the default; four locator strings still advertised it."""
    text = REGISTRY.read_text(encoding="utf-8")
    assert "DRYDOCS_DATA_ROOT (default" not in text, (
        "a locator string still advertises a DRYDOCS_DATA_ROOT default. G81 (d) removed "
        "it — the variable is mandatory and an unset root fails naming it."
    )


# ---------------------------------------------------------------------------
# (h) the port disposition
# ---------------------------------------------------------------------------
def test_the_binding_table_has_its_own_port_disposition() -> None:
    """Without its own row it inherits config/** canonical-producer.

    A port would then carry one machine's binding onto the other side — which is
    not hypothetical: the manifest's own note records dev-environment.yaml
    sitting under that default by omission until the 2026-07-28 port.
    """
    manifest = (REPO / "PORT-MANIFEST.yaml").read_text(encoding="utf-8")
    assert "config/source-bindings.yaml" in manifest, (
        "config/source-bindings.yaml has no PORT-MANIFEST row, so it inherits the "
        "config/** default `canonical-producer` and a port would carry one machine's "
        "binding across."
    )


def test_module_map_documents_both_new_modules() -> None:
    """CLAUDE.md §6: new code means its MODULE_MAP row in the same commit.

    Matches on the basename, because the map pairs sibling core modules in one
    row and cites the second bare (``drydocs_core/data_root.py``,
    ``landing_zones.py``) — asserting the long form would force the map to break
    its own convention to satisfy a test.
    """
    text = (REPO / "MODULE_MAP.md").read_text(encoding="utf-8")
    for module in ("env_refs.py", "source_bindings.py"):
        assert module in text, f"{module} has no MODULE_MAP.md row"
