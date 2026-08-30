"""The internal-twin doctor, and the one rule that outranks every other (G129).

THAT RULE IS (f): NO VERB PRINTS A VALUE. It is asserted three ways rather than
once, because the three ways fail at different times. The record has no field
that could hold a value (structural — fails at import). The generated
`.env.example` carries no secret value (content — fails at render). The writer
takes no value from argv (static — fails the moment somebody adds the argument
"for scripting").

THE ENUMERATION IS NOT A GREP (e). ``tests/unit/test_source_bindings.py`` already
holds the guard that reads the settings classes' ``env_prefix`` and
``model_fields``, because no text search can see ``NEO4J_URI`` when the prefix
composes it (J37). What is asserted HERE is the other direction: the doctor's
list IS the declared tuple, so it cannot quietly grow a second source.
"""

from __future__ import annotations

import ast
import dataclasses
import subprocess
import sys
from pathlib import Path

import pytest

from drydocs_core import env_doctor
from drydocs_core.env_doctor import (
    DOTENV,
    MACHINE_LOCAL_ENV,
    NOT_APPLICABLE,
    PROCESS,
    SET,
    STATES,
    TWIN_ROOTS,
    UNSET,
    VariableStatus,
    dotenv_names,
    report,
)
from drydocs_core.env_refs import DECLARED_VARIABLES, GROUPS, EnvVar
from drydocs_core.source_bindings import ConnectionProfile, load_profiles
from tests.source_scan import imported_modules, source_text

REPO = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# (f) No value is printed, ever. Three independent assertions.
# ---------------------------------------------------------------------------
def test_the_status_record_has_no_field_that_could_hold_a_value() -> None:
    """Structural, and deliberately so.

    A print site that masks is a print site somebody can forget to update. A
    record with nowhere to put a value cannot leak one however it is rendered,
    which is why the guarantee lives in the dataclass rather than in the CLI.
    """
    fields = {f.name for f in dataclasses.fields(VariableStatus)}
    forbidden = {"value", "raw", "secret_value", "resolved", "contents"}
    assert not (fields & forbidden), (
        f"VariableStatus grew a value-shaped field: {sorted(fields & forbidden)}. "
        "The doctor reports names and states; a value has no place on the record."
    )
    # resolved_via is a NAME. Assert it against the declared names so a later
    # change that repurposes it into a value fails here.
    rep = report()
    names = {v.name for v in DECLARED_VARIABLES} | {
        a for v in DECLARED_VARIABLES for a in v.aliases
    }
    for status in rep.variables:
        assert status.resolved_via in ({""} | names), (
            f"{status.name}.resolved_via is {status.resolved_via!r}, which is not a "
            "declared variable name. That field carries WHICH name answered, never what it holds."
        )


def test_a_secret_declaration_may_not_carry_an_example_value() -> None:
    with pytest.raises(ValueError, match="may not carry an example value"):
        EnvVar(name="X_SECRET", purpose="p", secret=True, example="hunter2")


def test_the_generated_example_emits_no_value_for_any_secret() -> None:
    from scripts.render_env_example import render

    text = render()
    for var in DECLARED_VARIABLES:
        if var.secret:
            assert f"{var.name}=\n" in text or text.endswith(f"{var.name}="), (
                f"{var.name} is declared secret and the generated .env.example gives it a "
                "value. A placeholder credential in a template is a credential somebody ships."
            )


def test_the_writer_never_takes_a_value_from_the_command_line() -> None:
    """Static: the value must come from a prompt, not from argv.

    An argument lands in shell history, in the process table, and in whatever
    scrollback a screen share is showing. The check reads the parser's declared
    arguments rather than the help text, because help text reflows (J37).
    """
    source = (REPO / "scripts" / "set_env_var.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    added: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_argument"
            and node.args
            and isinstance(node.args[0], ast.Constant)
        ):
            added.append(str(node.args[0].value))
    assert added, "expected to find the argument parser"
    assert not [a for a in added if "value" in a.lower()], (
        f"scripts/set_env_var.py declares a value-shaped argument: {added}. "
        "The value is read from a prompt (getpass when the declaration says secret)."
    )
    assert "getpass" in source, "the secret path must use a no-echo prompt"


# ---------------------------------------------------------------------------
# (a) FIND — the doctor itself.
# ---------------------------------------------------------------------------
def test_the_doctor_reports_every_declared_variable_and_nothing_else() -> None:
    rep = report()
    assert [v.name for v in rep.variables] == [v.name for v in DECLARED_VARIABLES], (
        "the doctor's list must BE the declared tuple, in its order -- a second "
        "source of variable names is how eight of them came to be read and declared nowhere"
    )


def test_the_report_names_its_venue() -> None:
    """J18 as a return value: the two machines hold different subsets."""
    assert report().venue


def test_every_state_is_one_of_the_three() -> None:
    assert {v.state for v in report().variables} <= set(STATES)


def test_an_unset_optional_variable_is_a_state_and_not_a_gap(monkeypatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(env_doctor, "dotenv_names", lambda path=None: frozenset())
    status = report().by_name("GITHUB_TOKEN")
    assert status is not None
    assert status.state == NOT_APPLICABLE
    assert not status.is_gap, (
        "scoring a variable this machine does not use as a defect is how a check "
        "becomes noise, and noise is how the original silence survived"
    )


def test_an_unset_required_variable_is_a_gap(monkeypatch) -> None:
    monkeypatch.delenv("DRYDOCS_DATA_ROOT", raising=False)
    monkeypatch.setattr(env_doctor, "dotenv_names", lambda path=None: frozenset())
    rep = report()
    status = rep.by_name("DRYDOCS_DATA_ROOT")
    assert status is not None and status.state == UNSET and status.is_gap
    assert rep.is_failure


def test_a_half_configured_profile_makes_its_missing_variable_a_gap(monkeypatch) -> None:
    """The middle case, and the only one worth a red line.

    None-set is a carrier this machine does not use. All-set is configured. Only
    the middle is somebody's half-finished setup.
    """
    monkeypatch.setenv("ORACLE_USER", "someone")
    monkeypatch.delenv("ORACLE_PASSWORD", raising=False)
    monkeypatch.delenv("ORACLE_DSN", raising=False)
    monkeypatch.setattr(env_doctor, "dotenv_names", lambda path=None: frozenset())
    rep = report()
    assert rep.by_name("ORACLE_DSN").state == UNSET
    assert rep.by_name("ORACLE_USER").state == SET


def test_nothing_set_on_a_profile_is_not_a_gap(monkeypatch) -> None:
    for name in ("ORACLE_USER", "ORACLE_PASSWORD", "ORACLE_DSN"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(env_doctor, "dotenv_names", lambda path=None: frozenset())
    rep = report()
    assert all(rep.by_name(n).state == NOT_APPLICABLE for n in ("ORACLE_USER", "ORACLE_DSN"))
    assert not rep.gaps or {g.name for g in rep.gaps}.isdisjoint({"ORACLE_USER", "ORACLE_DSN"})


def test_the_deprecated_alias_is_reported_by_name(monkeypatch) -> None:
    monkeypatch.delenv("DRYDOCS_LOGDIR", raising=False)
    monkeypatch.setenv("SPIDERP_LOGDIR", "/somewhere")
    monkeypatch.setattr(env_doctor, "dotenv_names", lambda path=None: frozenset())
    status = report().by_name("DRYDOCS_LOGDIR")
    assert status.state == SET
    assert status.resolved_via == "SPIDERP_LOGDIR"
    assert status.via_deprecated_alias


# ---------------------------------------------------------------------------
# The two channels. The divergence is REPORTED, not papered over.
# ---------------------------------------------------------------------------
def test_the_process_environment_wins_over_the_file(monkeypatch) -> None:
    """pydantic's own precedence, so the doctor's answer is the settings' answer."""
    monkeypatch.setenv("GITHUB_USER", "from-process")
    monkeypatch.setattr(env_doctor, "dotenv_names", lambda path=None: frozenset({"GITHUB_USER"}))
    assert report().by_name("GITHUB_USER").channel == PROCESS


def test_a_file_only_variable_is_set_and_labelled_as_such(monkeypatch) -> None:
    monkeypatch.delenv("GITHUB_USER", raising=False)
    monkeypatch.setattr(env_doctor, "dotenv_names", lambda path=None: frozenset({"GITHUB_USER"}))
    status = report().by_name("GITHUB_USER")
    assert status.state == SET and status.channel == DOTENV


def test_a_file_only_variable_on_a_profile_is_flagged_invisible_to_bindings(monkeypatch) -> None:
    """The one place two honest surfaces disagree, named rather than hidden.

    The settings classes declare ``env_file=.env``; ``env_refs.expand`` reads
    ``os.environ`` and nothing else. So a loader connects and the binding check
    calls the profile not-configured-here. Making the expander read the file
    would be the wrong fix -- every test that monkeypatches a variable to empty
    would then pick up the author's own file.
    """
    for name in ("ORACLE_USER", "ORACLE_PASSWORD", "ORACLE_DSN"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(
        env_doctor,
        "dotenv_names",
        lambda path=None: frozenset({"ORACLE_USER", "ORACLE_PASSWORD", "ORACLE_DSN"}),
    )
    rep = report()
    assert {v.name for v in rep.divergent} == {"ORACLE_USER", "ORACLE_PASSWORD", "ORACLE_DSN"}


def test_dotenv_names_returns_names_and_drops_empty_keys(tmp_path) -> None:
    target = tmp_path / ".env"
    target.write_text(
        "\n".join(
            [
                "# a comment",
                "",
                "NEO4J_URI=bolt://localhost:7687",
                "EMPTY=",
                'QUOTED_EMPTY=""',
                "export EXPORTED=yes",
                "malformed line with no equals sign",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )
    assert dotenv_names(target) == frozenset({"NEO4J_URI", "EXPORTED"})


def test_dotenv_names_is_empty_when_the_file_is_absent(tmp_path) -> None:
    assert dotenv_names(tmp_path / "nope") == frozenset()


# ---------------------------------------------------------------------------
# (d) The registry says WHICH twin file.
# ---------------------------------------------------------------------------
def test_every_profile_with_variables_names_a_twin() -> None:
    """A profile that reaches something must say where the coordinates are written down.

    The empty-``env`` profile is exempt BY ITS OWN DECLARATION: there is nothing
    to document until an account exists, and its ``status`` says so. That is the
    same shape as the unbound list -- an absence is declared, never inferred.
    """
    missing = [p.id for p in load_profiles() if p.env and not p.twin]
    assert not missing, (
        f"profile(s) with variables and no twin: {missing}. Name the machine-local "
        "file that documents these coordinates, or the null service locator is an "
        "empty slot again (G129 (d))."
    )


def test_a_declared_twin_is_a_pointer_and_never_a_value() -> None:
    """The path is repo-relative and lands in the gitignored tree, not in git.

    Naming a gitignored file is not publishing its contents. What would be a
    defect is a twin field that had grown into a host, a service name or a
    credential, so assert the shape.
    """
    for prof in load_profiles():
        if not prof.twin:
            continue
        assert prof.twin.startswith(TWIN_ROOTS), (
            f"{prof.id}: twin {prof.twin!r} does not point into the machine-local or "
            "internal tree. A twin is a FILE POINTER; coordinates live in variables."
        )
        assert (
            "=" not in prof.twin and "@" not in prof.twin
        ), f"{prof.id}: twin {prof.twin!r} looks like a value, not a path"


def test_the_doctor_carries_the_twin_through_to_the_variable() -> None:
    status = report().by_name("ORACLE_DSN")
    assert status is not None
    assert status.profiles, "ORACLE_DSN is referenced by the Oracle profiles"
    assert status.twins, (
        "the twin pointer must reach the VARIABLE view -- a reader looking up a "
        "variable should not have to know which profile references it first"
    )


# ---------------------------------------------------------------------------
# (b) DOCUMENT — the generated file.
# ---------------------------------------------------------------------------
def test_the_committed_example_matches_a_fresh_render() -> None:
    from scripts.render_env_example import TARGET, render

    assert TARGET.read_text(encoding="utf-8") == render(), (
        ".env.example is stale. Re-run: "
        "poetry run python scripts/render_env_example.py -- and never hand-edit it, "
        "because a key added there alone is a key no binding may reference."
    )


def test_the_generated_example_declares_every_variable_and_no_others() -> None:
    """The measured gap, closed and held.

    The hand-maintained file carried 17 keys against 24 declarations. This is the
    guard that makes reopening it impossible rather than unlikely.
    """
    from scripts.render_env_example import TARGET

    keys = {
        line.split("=", 1)[0]
        for line in TARGET.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#") and "=" in line
    }
    assert keys == {v.name for v in DECLARED_VARIABLES}


def test_the_check_mode_agrees_with_the_committed_file() -> None:
    from scripts.render_env_example import main

    assert main(["--check"]) == 0


def test_every_declared_variable_belongs_to_a_declared_group() -> None:
    groups = {key for key, _ in GROUPS}
    ungrouped = [v.name for v in DECLARED_VARIABLES if v.group not in groups]
    assert not ungrouped, (
        f"{ungrouped} carry a group no heading declares, so the generated file "
        "would silently drop them"
    )


def test_the_renderer_is_pure_and_reads_no_environment() -> None:
    """A template that varied by machine would be a template nobody could diff."""
    source = (REPO / "scripts" / "render_env_example.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    code_only = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Attribute) and n.attr in {"environ", "getenv"}
    ]
    assert not code_only, "the renderer must not read the environment"


# ---------------------------------------------------------------------------
# (c) UPDATE — the operator's tool, and the fence around it.
# ---------------------------------------------------------------------------
def test_no_module_imports_the_writer() -> None:
    """G126: the machine-local tree is READ-mode for the SYSTEM.

    The operator's hand is not the system, so the writer is a script in
    ``scripts/`` that nothing imports. That placement IS the enforcement -- the
    same reasoning that keeps the credential writer out of ``drydocs_api``.
    """
    roots = ("drydocs", "drydocs_core", "drydocs_api")
    offenders: list[str] = []
    for root in roots:
        for path in sorted((REPO / root).rglob("*.py"), key=lambda p: p.as_posix()):
            modules = imported_modules(source_text(path))
            if any("set_env_var" in m for m in modules):
                offenders.append(path.relative_to(REPO).as_posix())
    assert not offenders, (
        f"{offenders} IMPORT the operator's writer. Nothing the pipeline runs may "
        "write the machine-local tree (G126)."
    )


def test_the_writer_refuses_an_undeclared_name(capsys) -> None:
    from scripts.set_env_var import main

    assert main(["NOT_A_DECLARED_VARIABLE"]) == 1
    err = capsys.readouterr().err
    assert "not a declared variable" in err
    assert "drydocs_core/env_refs.py" in err, "the refusal must name where to declare it"


def test_the_writer_lists_names_and_never_values(tmp_path, monkeypatch, capsys) -> None:
    target = tmp_path / ".env"
    target.write_text("GITHUB_USER=a-real-username\n", encoding="utf-8", newline="\n")
    import scripts.set_env_var as writer

    monkeypatch.setattr(writer, "TARGET", target)
    assert writer.main(["--list"]) == 0
    out = capsys.readouterr().out
    assert "GITHUB_USER" in out and "set" in out
    assert "a-real-username" not in out, "the listing printed a value"


def test_the_rewrite_replaces_in_place_and_keeps_every_other_line() -> None:
    from scripts.set_env_var import _rewrite

    lines = ["# my note about which host this points at", "A=1", "B=2", "# trailing note"]
    assert _rewrite(lines, "B", "9") == [
        "# my note about which host this points at",
        "A=1",
        "B=9",
        "# trailing note",
    ]
    assert _rewrite(lines, "C", "3")[-1] == "C=3"
    assert "B=2" not in _rewrite(lines, "B", None)
    # A commented-out key is a note, not a setting: leave it alone.
    assert _rewrite(["#B=old", "B=2"], "B", None) == ["#B=old"]


def test_the_writer_runs_as_a_script(tmp_path) -> None:
    """Import order is not the contract here -- the operator runs it directly.

    Subprocess for the same reason ``test_cli_import_order`` uses one: an
    in-process import proves nothing about what happens at a terminal.
    """
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "set_env_var.py"), "--help"],
        capture_output=True,
        text=True,
        cwd=str(REPO),
    )
    assert proc.returncode == 0, proc.stderr


# ---------------------------------------------------------------------------
# The CLI surface. Guards read the --json document, never the table (J37).
# ---------------------------------------------------------------------------
def test_the_command_is_registered() -> None:
    from drydocs import cli

    names = {c.name for c in cli.app.registered_commands}
    assert "env-doctor" in names


def test_the_json_document_carries_no_value() -> None:
    """Every leaf in the payload, compared EXACTLY against what is set here.

    Exact and not substring: a legitimate value collides with the report's own
    prose (``NEO4J_DATABASE`` is ``drydocs``, which appears on almost every line),
    so a substring scan is a guard that fails on the truth. What must never
    happen is a FIELD whose content IS a value, and that is what this asserts.

    Weaker than the structural guard above and worth having anyway: it is the one
    that would catch a future field added to the CLI payload rather than to the
    record.
    """
    import json
    import os

    from typer.testing import CliRunner

    from drydocs import cli

    result = CliRunner().invoke(cli.app, ["env-doctor", "--json"])
    assert result.exit_code == 0, result.output

    leaves: list[str] = []

    def walk(node) -> None:
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
        elif isinstance(node, str):
            leaves.append(node)

    walk(json.loads(result.stdout))

    # Subtract the payload's own DECLARED VOCABULARY before comparing. Every
    # string the report is built from is declared somewhere -- variable and alias
    # names, group keys, states, channels, profile ids, twin paths, the file name
    # -- and a value is allowed to collide with one of them: NEO4J_USER is
    # `neo4j` and `neo4j` is also the group key, which made the first version of
    # this guard fail on the truth. What remains after the subtraction is any
    # string the report could only have got from the environment, which is the
    # actual leak. A value that exactly equals a declared token is missed, and
    # that is the price of a guard that does not cry wolf.
    vocabulary = (
        {v.name for v in DECLARED_VARIABLES}
        | {a for v in DECLARED_VARIABLES for a in v.aliases}
        | {v.group for v in DECLARED_VARIABLES}
        | set(STATES)
        | {PROCESS, DOTENV, "", MACHINE_LOCAL_ENV}
        | {p.id for p in load_profiles()}
        | {p.twin for p in load_profiles()}
        | {v.purpose for v in DECLARED_VARIABLES}
        | {report().venue}
    )
    suspect = [leaf for leaf in leaves if leaf not in vocabulary]

    # The tripwire must be armed. A guard whose subtraction swallowed everything
    # would pass forever and prove nothing, so plant a leaf that is not
    # vocabulary and assert the filter keeps it.
    planted = "a-value-no-declaration-contains"
    assert planted not in vocabulary
    assert planted in [leaf for leaf in [*leaves, planted] if leaf not in vocabulary]

    for var in DECLARED_VARIABLES:
        for name in (var.name, *var.aliases):
            value = os.environ.get(name, "").strip()
            if value:
                assert value not in suspect, f"{name}'s value reached the JSON report"


def test_the_json_document_is_one_parseable_object() -> None:
    import json

    from typer.testing import CliRunner

    from drydocs import cli

    result = CliRunner().invoke(cli.app, ["env-doctor", "--json"])
    doc = json.loads(result.stdout)
    assert set(doc) == {
        "venue",
        "env_file",
        "env_file_exists",
        "variables",
        "gaps",
        "invisible_to_bindings",
        "is_failure",
    }
    assert doc["env_file"] == MACHINE_LOCAL_ENV


def test_a_profile_is_a_frozen_declaration() -> None:
    """The twin field is part of the profile, not bolted on beside it."""
    prof = ConnectionProfile(
        id="x",
        carrier="c",
        platform="p",
        classification="Internal",
        env={},
        serves=0,
        note="",
        twin=TWIN_ROOTS[0] + "x.md",
    )
    assert prof.twin == TWIN_ROOTS[0] + "x.md"
    with pytest.raises(dataclasses.FrozenInstanceError):
        prof.twin = "other"  # type: ignore[misc]
