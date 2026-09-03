"""Agent query command — the read-only, deterministic graph-navigation surface
for agents (R9).

::

    python -m drydocs_api.agent_query list
    python -m drydocs_api.agent_query describe <spec-id>
    python -m drydocs_api.agent_query run <spec-id> [-p KEY=VALUE ...] [--pretty]

WHY A COMMAND, AND WHY HERE. An agent that navigates the graph needs one
surface that is deterministic (the same input yields the same bytes), testable
(drivable with no server and no driver), and incapable of writing. The O33-
guarded QuerySpec registry (``query_specs.py``) is already all three: every
spec is versioned, read-only by construction (``ensure_read_only`` at registry
build), classified, and routed to its own database. This command exposes that
registry and NOTHING else — there is no Cypher input anywhere on it, which is
the difference between it and the ``graph_query`` ADK agent (``agents/``),
which takes raw Cypher. It lives inside ``drydocs_api`` because that component
owns the specs: a ``drydocs`` sub-command would make the root CLI import this
component, and the module-boundary guard (``tests/unit/test_module_boundary.py``)
is exactly what the item says must stay green.

ONE ENVELOPE. ``run`` prints the same dict ``POST /specs/{id}/run`` returns
(``exports.execute_spec``), so an agent reading this and a console reading the
API see the same ten keys. ``list`` and ``describe`` print the ``GET /specs``
rows. No third shape is minted here.

WHAT IT REFUSES, by name, on stdout: an unknown spec id; a param the spec does
not declare, a missing required one, or a value that cannot take the declared
type; an ephemeral (``eph.``) spec id — those are session-scoped registrations
(R4) and this command has no session. Raw Cypher is not an option to refuse
because it is not an option.

EXIT CONTRACT (the .sh / agent tests this):

    0  ran — the envelope is on stdout
    1  the runner raised (driver, connection, or query error) — stdout carries
       ``{"ok": false, "error": "run-failed", ...}`` with the exception's class
       and message
    2  usage — unknown spec, bad param, ephemeral id (stdout carries
       ``{"ok": false, "error": <kind>, ...}``); an argparse-level usage error
       (unknown sub-command, missing operand) is argparse's own exit 2 with
       usage on stderr

OUTPUT: one JSON document on stdout for every outcome, keys sorted, values the
driver returned (temporals fall back to ``str``), one trailing newline. ASCII-
safe, so a Windows console with a legacy code page cannot mangle it. A success
carries no ``ok`` key — it IS the envelope; every failure carries ``ok: false``.

FRAMEWORK-FREE ON IMPORT. Importing this module pulls the registry, the guard
and the param validator — never fastapi, never ``drydocs_api.app`` (the wiring
module that builds the driver). The live runner is imported lazily inside
:func:`_live_runner`, only when no runner was injected, which is what lets the
agents venv (a separate interpreter; see ``agents/common/specs_catalog.py``)
and the unit suite use it identically. (The ``neo4j`` package itself rides in
with ``drydocs_core.config`` on every first-party import; no driver is built.)

MCP (``mcp-neo4j-cypher``) is recorded as the richer LATER option and is out of
scope here: it adds a config surface and a write-risk surface this command
deliberately does not have.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping

from drydocs_api.ephemeral_specs import is_ephemeral_ref
from drydocs_api.exports import execute_spec, list_specs
from drydocs_api.handlers import GraphRunner
from drydocs_api.queries import ParamValidationError, validate_params
from drydocs_api.query_specs import QUERY_SPECS, QuerySpec, UnknownSpecError, query_spec

EXIT_OK = 0
EXIT_RUN_FAILED = 1
EXIT_USAGE = 2


class ParamSyntaxError(ValueError):
    """A ``-p`` operand that is not ``KEY=VALUE``."""


def parse_param_operands(operands: list[str]) -> dict[str, str]:
    """``-p KEY=VALUE`` (repeatable) to a string map. Split on the FIRST ``=``
    so a value may itself contain one. A repeated key is refused rather than
    last-wins: an agent that sent two values did not mean either of them."""
    out: dict[str, str] = {}
    for item in operands:
        key, sep, value = item.partition("=")
        if not sep or not key:
            raise ParamSyntaxError(f"--param takes KEY=VALUE, got {item!r}")
        if key in out:
            raise ParamSyntaxError(f"param {key!r} given twice")
        out[key] = value
    return out


def coerce_params(spec: QuerySpec, raw: Mapping[str, str]) -> dict[str, object]:
    """Command-line strings to the DECLARED types, before ``validate_params``.

    The validator rejects the string ``"10"`` for an ``int`` param — correctly,
    at the API, where JSON carries types. A shell carries only strings, so the
    declared type decides the conversion here: ``int`` via ``int()`` (a value
    that cannot take it is refused by name), ``string`` passes through. A name
    the spec does not declare passes through untouched so ``validate_params``
    refuses it by name with the message the API would give.
    """
    declared = {p.name: p for p in spec.params}
    out: dict[str, object] = {}
    for name, value in raw.items():
        param = declared.get(name)
        if param is None or param.type != "int":
            out[name] = value
            continue
        try:
            out[name] = int(value)
        except ValueError:
            raise ParamValidationError(
                f"param '{name}' of '{spec.id}' must be int, got {value!r}"
            ) from None
    return out


def describe_spec(spec: QuerySpec) -> dict[str, object]:
    """The ``GET /specs`` row for one spec — the same shape ``list`` prints."""
    return next(row for row in list_specs() if row["id"] == spec.id)


def _declared_params(spec: QuerySpec) -> list[dict[str, object]]:
    return [
        {"name": p.name, "type": p.type, "required": p.required, "default": p.default}
        for p in spec.params
    ]


def _failure(kind: str, message: str, **detail: object) -> dict[str, object]:
    return {"ok": False, "error": kind, "message": message, **detail}


def _live_runner() -> GraphRunner:
    # Lazy on purpose: drydocs_api.app imports the neo4j driver at module level
    # and this command must import framework-free (the agents venv, the unit
    # suite). Credentials come from the server environment (Neo4jSettings),
    # exactly as the API's runner reads them; READ routing is pinned there.
    from drydocs_api.app import LiveRunner

    return LiveRunner()


def emit(payload: object, *, pretty: bool = False, out=None) -> None:
    """One JSON document, keys sorted, ASCII-safe, one trailing newline."""
    text = json.dumps(payload, sort_keys=True, default=str, indent=2 if pretty else None)
    print(text, file=out or sys.stdout)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="drydocs-agent-query",
        description="Read-only, deterministic QuerySpec navigation for agents (R9). "
        "JSON on stdout; exit 0 ran, 1 runner failed, 2 usage.",
    )
    ap.add_argument("--pretty", action="store_true", help="indent the JSON")
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="every registry spec: id, description, database, params, columns")
    describe = sub.add_parser("describe", help="one spec's contract, including its Cypher")
    describe.add_argument("spec_id")
    run = sub.add_parser("run", help="execute one spec with typed params; prints the run envelope")
    run.add_argument("spec_id")
    run.add_argument(
        "-p",
        "--param",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="declared parameter, repeatable; converted to the declared type",
    )
    return ap


def main(argv: list[str] | None = None, *, runner: GraphRunner | None = None) -> int:
    """Entry point. ``runner`` is the injection seam the unit suite drives —
    the same duck-typed ``GraphRunner`` every handler takes — and the live
    driver is built only when it is None."""
    ns = build_parser().parse_args(argv)

    if ns.command == "list":
        emit(list_specs(), pretty=ns.pretty)
        return EXIT_OK

    spec_id: str = ns.spec_id
    if is_ephemeral_ref(spec_id):
        emit(
            _failure(
                "ephemeral-spec",
                f"'{spec_id}' is a session-scoped ephemeral registration (R4); this command "
                "has no session and runs registry specs only",
                spec_id=spec_id,
            )
        )
        return EXIT_USAGE
    try:
        spec = query_spec(spec_id)
    except UnknownSpecError:
        emit(
            _failure(
                "unknown-spec",
                f"unknown spec '{spec_id}' — `list` names the registry",
                spec_id=spec_id,
                registry_size=len(QUERY_SPECS),
            )
        )
        return EXIT_USAGE

    if ns.command == "describe":
        emit(describe_spec(spec), pretty=ns.pretty)
        return EXIT_OK

    try:
        bound = validate_params(spec, coerce_params(spec, parse_param_operands(ns.param)))
    except (ParamSyntaxError, ParamValidationError) as exc:
        emit(_failure("bad-param", str(exc), spec_id=spec.id, declared=_declared_params(spec)))
        return EXIT_USAGE

    try:
        envelope = execute_spec(spec, bound, runner if runner is not None else _live_runner())
    except Exception as exc:  # the runner's failure is the outcome being reported
        emit(
            _failure(
                "run-failed",
                f"{type(exc).__name__}: {exc}",
                spec_id=spec.id,
                database=spec.database,
                params=bound,
            )
        )
        return EXIT_RUN_FAILED

    emit(envelope, pretty=ns.pretty)
    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
