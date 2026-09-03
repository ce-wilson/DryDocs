"""Response models for the routes the console consumes (O70).

WHY THESE EXIST. Until O70 every handler in ``app.py`` returned
``dict[str, object]``, so the OpenAPI schema drydocs-api publishes described
each response as a free object, and the browser's response types were written
by hand against what the handlers happened to return. That is a restatement
of a declaration with nothing guarding it — the defect class this repo has a
rule about twice over (never parse a render, never hand-copy a declaration).
The console's TypeScript client is now GENERATED from the schema, so a
response type has to be declared HERE, by the server, or the generated client
carries ``Record<string, unknown>`` and the hand-written cast has merely moved.

WHY ``extra='forbid'``. Pydantic's default silently DROPS a returned key the
model does not name — a handler could add a field, the wire would lose it, and
nothing would say so. Forbidding extras makes that a response-validation
failure in the API test suite, which is where a declaration and its handler
should be caught disagreeing. Every key each handler returns today is named
below; add a key to the handler and you add it here in the same commit, then
regenerate (``scripts/dump_openapi.py`` and ``npm run api:types`` in ``web/``).

The export MANIFEST stays a free object on purpose: the ledger record is open
by design and the console types it ``Record<string, unknown>`` already. The
``/docs-verify``, ``/mappings/*``, ``/intake/*`` and ``/specs/ephemeral``
routes are not modelled here yet — their browser wrappers gained typed paths
and request bodies at O70 and keep hand-declared response types until the
server declares them (recorded in the O70 close notes).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class _Declared(BaseModel):
    """A response shape the server stands behind: no undeclared keys pass."""

    model_config = ConfigDict(extra="forbid")


class HealthOut(_Declared):
    status: str


class StatusOut(_Declared):
    status: str


class LoginOut(_Declared):
    """The session the browser holds. Never the secret (O69)."""

    token: str
    persona_id: str
    role: str
    expires_at: str


class ParamOut(_Declared):
    """One declared parameter of a named query or a QuerySpec."""

    name: str
    type: str
    required: bool
    default: Any = None


class NamedQueryOut(_Declared):
    id: str
    description: str
    params: list[ParamOut]


class NamedRunOut(_Declared):
    """``/query/{query_id}`` and ``/raw-cypher`` share this envelope — the
    database is named AFTER the fact because routing is a server decision
    (ADR 0002 / ADR 0005 decision 2)."""

    query_id: str
    database: str
    keys: list[str]
    rows: list[dict[str, Any]]
    diagnostics: dict[str, Any]


class ColumnOut(_Declared):
    name: str
    type: str
    label: str


class SpecOut(_Declared):
    """One registry row as ``/specs`` lists it — the declaration, never the
    database (G102: ``watermarked`` comes from the spec)."""

    id: str
    description: str
    database: str
    classification: str
    cypher: str
    columns: list[ColumnOut]
    params: list[ParamOut]
    watermarked: bool


class SpecRunOut(_Declared):
    """A QuerySpec run (O11): the registry echoes the spec's contract back
    with the rows, so the UI renders the classification banner and the
    SYNTHESIZED watermark without holding its own query definitions. This is
    the server-side twin of the console's ``SpecResult`` seam type."""

    spec_id: str
    database: str
    classification: str
    columns: list[ColumnOut]
    cypher: str
    params: dict[str, Any]
    keys: list[str]
    rows: list[dict[str, Any]]
    watermarked: bool
    ephemeral: bool
