"""O70 guards: the committed OpenAPI schema the console's TypeScript client is
generated from, and the response declarations behind it.

The chain is drydocs_api → web/src/generated/openapi.json → api.d.ts → tsc.
This file holds the FIRST link: the committed schema must equal a fresh dump of
the importable app (the gates.json discipline), and the routes the console's
GraphAccess seam reads must declare typed responses — otherwise the generated
client types them ``Record<string, unknown>`` and the hand-written cast has only
moved. The second link (openapi.json → api.d.ts) is web/src/generated/api.test.ts
under vitest, which can run the generator; the third is ``npm run build`` in CI.

Reads ``create_app().openapi()`` — the importable object — never ``/openapi.json``
over HTTP (J37).

fastapi lives in the optional ``api`` group, which the CI ``gates`` job installs
without; the ``web`` job runs ``scripts/dump_openapi.py --check`` for the same
drift assertion where the group IS installed, so a skip here is not a gap there.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi", reason="optional api group (poetry install --with api)")

from drydocs_api import schemas  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
COMMITTED = REPO / "web" / "src" / "generated" / "openapi.json"
GENERATED_TYPES = REPO / "web" / "src" / "generated" / "api.d.ts"


def _dumper():
    spec = importlib.util.spec_from_file_location(
        "dump_openapi", REPO / "scripts" / "dump_openapi.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _committed() -> dict:
    return json.loads(COMMITTED.read_text(encoding="utf-8"))


# --- drift: the committed schema is a fresh dump ----------------------------


def test_committed_schema_matches_a_fresh_dump() -> None:
    dump = _dumper()
    assert dump.check_schema(COMMITTED), (
        "web/src/generated/openapi.json is stale — run `poetry run python "
        "scripts/dump_openapi.py` then `npm run api:types` in web/, and commit both"
    )


def test_the_dump_is_deterministic() -> None:
    dump = _dumper()
    assert dump.render_schema() == dump.render_schema()
    assert dump.render_schema().endswith("\n")


def test_generated_types_exist_beside_the_schema() -> None:
    """The TS half of the artifact. Its CONTENT is guarded by vitest
    (web/src/generated/api.test.ts), which can run the generator; this only
    says the file is where the client imports it from."""
    assert GENERATED_TYPES.is_file(), "run `npm run api:types` in web/"


# --- declarations: the seam's routes carry typed responses ------------------

#: route -> (method, declared 200 model, list-of?)
CONSOLE_ROUTES = {
    "/health": ("get", "HealthOut", False),
    "/login": ("post", "LoginOut", False),
    "/logout": ("post", "StatusOut", False),
    "/queries": ("get", "NamedQueryOut", True),
    "/query/{query_id}": ("post", "NamedRunOut", False),
    "/raw-cypher": ("post", "NamedRunOut", False),
    "/specs": ("get", "SpecOut", True),
    "/specs/{spec_id}/run": ("post", "SpecRunOut", False),
}


def _ok_schema(doc: dict, path: str, method: str) -> dict:
    return doc["paths"][path][method]["responses"]["200"]["content"]["application/json"]["schema"]


@pytest.mark.parametrize("path", sorted(CONSOLE_ROUTES))
def test_console_route_declares_its_response_model(path: str) -> None:
    method, model, is_list = CONSOLE_ROUTES[path]
    ref = {"$ref": f"#/components/schemas/{model}"}
    got = _ok_schema(_committed(), path, method)
    if is_list:
        assert got.get("type") == "array" and got.get("items") == ref, (path, got)
    else:
        assert got == ref, (path, got)


def test_seam_fields_are_declared_by_the_server() -> None:
    """The console's SpecResult / NamedResult (web/src/lib/graph.ts) promise
    these fields; lib/graphApi.ts asserts the generated types cover them at
    compile time. This is the same claim read from the schema, so a server that
    drops one fails here with the field's name."""
    comps = _committed()["components"]["schemas"]
    spec_run = set(comps["SpecRunOut"]["properties"])
    assert {
        "spec_id",
        "database",
        "classification",
        "columns",
        "cypher",
        "params",
        "keys",
        "rows",
        "watermarked",
    } <= spec_run, spec_run
    assert {"keys", "rows", "database"} <= set(comps["NamedRunOut"]["properties"])
    assert {"token", "persona_id", "role", "expires_at"} <= set(comps["LoginOut"]["properties"])


def test_declared_models_forbid_undeclared_keys() -> None:
    """extra='forbid' on every response model: a handler that adds a key the
    schema does not name fails response validation in the API tests, instead
    of the wire silently dropping it (the O70 defect class, inverted)."""
    models = [
        cls
        for cls in vars(schemas).values()
        if isinstance(cls, type)
        and issubclass(cls, schemas._Declared)
        and cls is not schemas._Declared
    ]
    assert len(models) >= 8
    for cls in models:
        assert cls.model_config.get("extra") == "forbid", cls.__name__


def test_routes_still_declared_as_free_objects_are_the_recorded_follow_up() -> None:
    """Not a defect pin — a scope record. These prefixes return free objects
    today; their browser wrappers use `unwrapAs` (a claimed type, not a
    declared one). When one gains a model, move it OUT of this list and into
    CONSOLE_ROUTES so the claim becomes a guard."""
    doc = _committed()
    free = [
        p
        for p in doc["paths"]
        if p.startswith(("/mappings/", "/intake", "/docs-verify", "/specs/ephemeral", "/demo"))
    ]
    assert free, "the follow-up list emptied — retire this test and its note in O70"
    for path in free:
        for method, op in doc["paths"][path].items():
            got = op["responses"]["200"]["content"]["application/json"]["schema"]
            assert (
                "$ref" not in got
            ), f"{method.upper()} {path} now declares {got} — promote it to CONSOLE_ROUTES"
