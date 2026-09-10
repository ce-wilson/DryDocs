"""CFG14 — the console roster is declared once, and the claim block is deferred not absent.

Three things are guarded here, and the third is the one that matters most.

The DECLARATION: the roster parses, its roles are a closed set, and every refusal
the reader promises actually fires — each proven by feeding it a broken
declaration rather than by trusting the code path exists.

The RENDER: `web/src/generated/console-personas.json` matches the YAML and is
deterministic, which is what replaces the regex that used to parse TypeScript to
catch drift between two declarations.

The TWO PROPERTIES THE CHANGE MUST NOT WEAKEN. Moving a hard-coded roster into a
config file is exactly the change that could quietly erode them, so they are
pinned rather than trusted: the file is the DEMO ROSTER and not an authorization
source, and per-PERSONA scoping survives.
"""

from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

import pytest
import yaml

from drydocs_core.console_personas import (
    CLAIM_REASON_MIN,
    DEFAULT_PERSONAS_PATH,
    ConsolePersonaError,
    ConsolePersonas,
)

REPO = Path(__file__).resolve().parents[2]
GENERATED = REPO / "web" / "src" / "generated" / "console-personas.json"


@pytest.fixture(scope="module")
def raw() -> dict:
    return yaml.safe_load(DEFAULT_PERSONAS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def roster() -> ConsolePersonas:
    return ConsolePersonas.from_yaml()


# --- the declaration ----------------------------------------------------------


def test_the_declaration_carries_the_identity_header(raw):
    assert raw["schema"] == "drydocs.console-personas.v1"
    assert raw["classification"] == "Internal-Public"
    assert raw["updated"]


def test_every_seat_maps_to_a_role_on_the_closed_list(roster):
    assert roster.roles == ("user", "steward", "admin")
    assert roster.personas, "an empty roster would make every guard over it vacuous"
    for p in roster.personas.values():
        assert p.role in roster.roles, (p.id, p.role)
        assert p.display_name


@pytest.mark.parametrize(
    ("mutate", "match"),
    [
        (lambda c: c["personas"]["neo"].update(role="wizard"), "not on the closed list"),
        (lambda c: c["personas"]["neo"].pop("role"), "declares no role"),
        (lambda c: c["personas"]["neo"].pop("display_name"), "declares no display_name"),
        # a tower scopes a user-tier drill; on a steward or admin it contradicts itself
        (lambda c: c["personas"]["trinity"].update(tower_key="home"), "contradicts itself"),
        (lambda c: c.update(personas={}), "missing or empty"),
        (lambda c: c.update(schema="drydocs.console-personas.v99"), "unexpected schema"),
        (lambda c: c.update(roles=[]), "non-empty closed list"),
    ],
)
def test_the_reader_refuses_a_declaration_it_cannot_trust(raw, mutate, match):
    cfg = copy.deepcopy(raw)
    mutate(cfg)
    with pytest.raises(ConsolePersonaError, match=match):
        ConsolePersonas(cfg)


def test_a_missing_declaration_raises_rather_than_defaulting(tmp_path):
    with pytest.raises(ConsolePersonaError, match="missing"):
        ConsolePersonas.from_yaml(tmp_path / "nope.yaml")


# --- the claim block ----------------------------------------------------------


def test_the_claim_block_is_deferred_and_says_why(roster):
    claims = roster.claims
    assert claims.is_deferred
    assert claims.mapping == {}, "deferred means nothing maps yet"
    assert len(claims.reason) >= CLAIM_REASON_MIN


@pytest.mark.parametrize(
    ("mutate", "match"),
    [
        # the status and the contents must agree, in both directions
        (
            lambda c: c["claims"]["mapping"].update({"Admin-1-2-PROD": "admin"}),
            "the status and the contents disagree",
        ),
        (lambda c: c["claims"].update(status="adopted"), "maps nothing grants nothing"),
        (lambda c: c["claims"].update(reason="soon"), f"at least {CLAIM_REASON_MIN}"),
        (lambda c: c["claims"].pop("reason"), f"at least {CLAIM_REASON_MIN}"),
        (lambda c: c.pop("claims"), "declared and deferred, never absent"),
        (lambda c: c["claims"].update(status="maybe"), "is not one of"),
    ],
)
def test_the_claim_block_refuses_a_status_that_disagrees_with_its_contents(raw, mutate, match):
    cfg = copy.deepcopy(raw)
    mutate(cfg)
    with pytest.raises(ConsolePersonaError, match=match):
        ConsolePersonas(cfg)


def test_an_adopted_mapping_must_name_roles_on_the_closed_list(raw):
    cfg = copy.deepcopy(raw)
    cfg["claims"]["status"] = "adopted"
    cfg["claims"]["mapping"] = {"Admin-1-2-PROD": "wizard"}
    with pytest.raises(ConsolePersonaError, match="not on the closed list"):
        ConsolePersonas(cfg)


def test_an_adopted_block_with_a_real_mapping_is_accepted(raw):
    """The deferral is a STATE, not a wall: the shape it will take must parse today,
    or the refusals above are guarding a path nobody can ever walk."""
    cfg = copy.deepcopy(raw)
    cfg["claims"]["status"] = "adopted"
    cfg["claims"]["mapping"] = {"ReadOnly-1-2-PROD": "user", "Admin-1-2-PROD": "admin"}
    parsed = ConsolePersonas(cfg)
    assert not parsed.claims.is_deferred
    assert parsed.claims.mapping["Admin-1-2-PROD"] == "admin"


# --- the render ---------------------------------------------------------------


def test_the_generated_file_matches_the_declaration_and_is_deterministic(roster):
    """This is what replaces the regex that parsed TypeScript to catch drift."""
    import scripts.render_console_personas as renderer

    committed = json.loads(GENERATED.read_text(encoding="utf-8"))
    built = renderer.build(roster)
    assert committed == built, (
        "web/src/generated/console-personas.json is stale — re-run "
        "scripts/render_console_personas.py (or render_board.py, which chains it)"
    )
    assert renderer.build(roster) == built, "two builds over one declaration differ"


def test_the_generated_rows_use_the_typescript_key_names(roster):
    """The JSON is imported straight into a typed structure in auth.ts, so a rename
    here is a silent break at a boundary no Python test crosses."""
    rows = {r["id"]: r for r in roster.as_rows()}
    assert set(rows["neo"]) == {"id", "displayName", "role", "chip", "towerKey"}
    # absent rather than null when there is no tower — the interface declares it optional
    assert "towerKey" not in rows["morpheus"]


# --- the two properties the change must not weaken ----------------------------


def test_the_roster_grants_nothing_it_only_names_seats(raw, roster):
    """PROPERTY ONE: this file is the DEMO ROSTER, not an authorization source.

    The server re-resolves the real role from the bearer token on every request
    (ADR 0005 decision 3); what a browser holds drives nav rendering only. The
    testable form of that promise is that no seat can carry a field which grants
    anything — no permission, scope, entitlement or secret — so a future edit that
    tried to make this file the authorization source fails here first.
    """
    forbidden = {"permissions", "scopes", "entitlements", "grants", "secret", "password", "token"}
    for pid, spec in raw["personas"].items():
        assert not (forbidden & set(spec)), f"{pid} carries a granting field"
    # and the Python surface exposes exactly the two facts the server needs
    from drydocs_api.personas import Persona

    assert set(Persona.__dataclass_fields__) == {"id", "role"}


def test_more_than_one_user_seat_exists(roster):
    """PROPERTY TWO: per-PERSONA scoping survives.

    Several console behaviours are scoped per persona rather than per role — the
    Ask panel's stored last turn is the case O64 tested — and proving isolation
    needs two accounts differing in nothing but identity. A later tidy-up would
    read the duplicates as redundant and collapse them, which would silently
    delete the only way that property is testable.
    """
    users = roster.by_role("user")
    assert len(users) >= 2, (
        "fewer than two user-tier seats — per-persona isolation stops being testable "
        "(O64), and the seats are duplicated on purpose rather than by accident"
    )


def test_the_api_roster_reads_the_declaration(roster):
    """The contract drydocs_api offers is unchanged; only its source moved."""
    from drydocs_api.personas import PERSONAS, UnknownPersonaError, persona

    assert {p.id: p.role for p in PERSONAS.values()} == {
        p.id: p.role for p in roster.personas.values()
    }
    assert persona("neo").role == "user"
    with pytest.raises(UnknownPersonaError):
        persona("smith")


def _module_scope_calls(source: str) -> list[int]:
    """Line numbers of calls evaluated when the module is IMPORTED.

    Statement-level only: a call inside a function body or a decorator runs later
    or is the definition itself, and counting those would make the guard fire on
    every ``@lru_cache`` in the file.
    """
    tree = ast.parse(source)
    return sorted(
        node.lineno
        for stmt in tree.body
        if isinstance(stmt, ast.Assign | ast.AnnAssign | ast.Expr)
        for node in ast.walk(stmt)
        if isinstance(node, ast.Call)
    )


def test_importing_the_api_module_does_not_read_the_declaration():
    """The refusal fires at the reader, not at an importer four modules away.

    ``drydocs_api.intake`` imports ``sessions``, which imports ``personas``. A
    module-level ``PERSONAS = _roster()`` would make an unreadable declaration abort
    that import with a traceback naming neither the roster nor the caller - which is
    how the J48 worktree probe in ``tests/unit/test_repo_paths.py`` failed while this
    file was still uncommitted. ``PERSONAS`` is served by a module ``__getattr__``
    instead, so the read happens on first access.

    Read as CODE (J66), and with a POSITIVE CONTROL, because a guard asserting an
    absence proves nothing until it has been shown to find the thing when it is
    there - twice in this repo a scan passed by looking in the wrong place.
    """
    control = "PERSONAS = _roster()\n"
    assert _module_scope_calls(control) == [1], "the guard cannot see the shape it forbids"

    decorated = "import functools\n\n\n@functools.lru_cache\ndef f():\n    return g()\n"
    assert not _module_scope_calls(decorated), "a decorator is not an import-time read"

    import drydocs_api.personas as mod

    calls = _module_scope_calls(Path(mod.__file__).read_text(encoding="utf-8"))
    assert not calls, (
        f"drydocs_api/personas.py calls at module scope (lines {calls}) — importing it "
        "would read the declaration, and the refusal would surface at an importer "
        "rather than at whoever asked for the roster"
    )
