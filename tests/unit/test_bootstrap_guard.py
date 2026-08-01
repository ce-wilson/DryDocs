"""D8 — the bootstrap constraint-count guard.

``execute_file`` raising is not enough: ``apoc.cypher.runMany`` silently
no-ops DDL, so pre-D5 bootstraps printed "Constraints applied." while
creating zero constraints. Bootstrap now parses the names
``constraints.cypher`` declares and asserts every one is present in
``SHOW CONSTRAINTS`` after the apply — the supplement-chain guard pattern
(``test_supplements``), driven here against a fake client that models the
database as the set of constraint names it holds.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from drydocs import cli as cli_mod
from drydocs_core.schema.constraints import declared_constraint_names

runner = CliRunner()

CONSTRAINTS_FILE = (
    Path(__file__).resolve().parents[2] / "drydocs_core" / "schema" / "constraints.cypher"
)


# ---- the parser --------------------------------------------------------------


def test_parser_agrees_with_the_schema_census() -> None:
    """Every CREATE CONSTRAINT in the real file yields exactly one name."""
    names = declared_constraint_names(CONSTRAINTS_FILE)
    text = CONSTRAINTS_FILE.read_text(encoding="utf-8")
    raw = sum(1 for line in text.splitlines() if line.lstrip().startswith("CREATE CONSTRAINT"))
    assert len(names) == raw
    assert len(set(names)) == len(names), "constraint names must be unique"
    assert "controlmjob_key" in names  # spot anchor


def test_parser_ignores_commented_declarations(tmp_path) -> None:
    """Retiring a constraint by commenting it out must shrink the contract."""
    f = tmp_path / "probe.cypher"
    f.write_text(
        "// CREATE CONSTRAINT retired_key IF NOT EXISTS FOR (n:Old) REQUIRE n.id IS UNIQUE;\n"
        "CREATE CONSTRAINT live_key IF NOT EXISTS FOR (n:New) REQUIRE n.id IS UNIQUE;\n",
        encoding="utf-8",
    )
    assert declared_constraint_names(f) == ("live_key",)


def test_parser_refuses_an_anonymous_declaration(tmp_path) -> None:
    """A nameless declaration would silently fall outside the guard."""
    f = tmp_path / "probe.cypher"
    f.write_text(
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:X) REQUIRE n.id IS UNIQUE;\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="no parseable name"):
        declared_constraint_names(f)


def test_parser_refuses_duplicate_names(tmp_path) -> None:
    f = tmp_path / "probe.cypher"
    f.write_text(
        "CREATE CONSTRAINT twin IF NOT EXISTS FOR (n:A) REQUIRE n.a IS UNIQUE;\n"
        "CREATE CONSTRAINT twin IF NOT EXISTS FOR (n:B) REQUIRE n.b IS UNIQUE;\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate constraint names"):
        declared_constraint_names(f)


# ---- the bootstrap refusal ----------------------------------------------------


class _FakeClient:
    """Models the database as the set of constraint names it holds."""

    def __init__(self, *, apply_lands: bool = True, preexisting: set[str] | None = None) -> None:
        self.names: set[str] = set(preexisting or ())
        self.applied: list[str] = []
        self._apply_lands = apply_lands

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def apoc_available(self) -> bool:
        return True

    def execute_file(self, path: Path) -> None:
        self.applied.append(path.name)
        if self._apply_lands and path.name == "constraints.cypher":
            self.names |= set(declared_constraint_names(path))

    def constraint_names(self) -> frozenset[str]:
        return frozenset(self.names)


@pytest.fixture()
def fake_client(monkeypatch):
    def _install(client: _FakeClient) -> _FakeClient:
        monkeypatch.setattr(cli_mod, "_client", lambda *a, **k: client)
        return client

    return _install


def test_bootstrap_reports_the_declared_count_on_success(fake_client) -> None:
    fake_client(_FakeClient(apply_lands=True))
    result = runner.invoke(cli_mod.app, ["bootstrap", "--skip-ontology"])
    assert result.exit_code == 0, result.output
    n = len(declared_constraint_names(CONSTRAINTS_FILE))
    assert f"Constraints applied ({n}/{n} declared present)." in result.output


def test_bootstrap_refuses_when_the_apply_lands_nothing(fake_client) -> None:
    """The load-bearing check: success output while nothing landed must fail."""
    fake_client(_FakeClient(apply_lands=False))
    result = runner.invoke(cli_mod.app, ["bootstrap", "--skip-ontology"])
    assert result.exit_code == 2, result.output
    assert "absent after apply" in result.output
    assert "Constraints applied" not in result.output


def test_bootstrap_refuses_a_partial_landing_and_names_the_missing(fake_client) -> None:
    declared = declared_constraint_names(CONSTRAINTS_FILE)
    all_but_last = set(declared[:-1])
    fake_client(_FakeClient(apply_lands=False, preexisting=all_but_last))
    result = runner.invoke(cli_mod.app, ["bootstrap", "--skip-ontology"])
    assert result.exit_code == 2, result.output
    assert declared[-1] in result.output


def test_bootstrap_guard_tolerates_extra_undeclared_constraints(fake_client) -> None:
    """Names carry the check, not counts — foreign constraints never false-fail."""
    fake_client(_FakeClient(apply_lands=True, preexisting={"provisioning_extra_key"}))
    result = runner.invoke(cli_mod.app, ["bootstrap", "--skip-ontology"])
    assert result.exit_code == 0, result.output


def test_skip_constraints_skips_the_guard(fake_client) -> None:
    client = fake_client(_FakeClient(apply_lands=False))
    result = runner.invoke(cli_mod.app, ["bootstrap", "--skip-constraints", "--skip-ontology"])
    assert result.exit_code == 0, result.output
    assert client.applied == []
