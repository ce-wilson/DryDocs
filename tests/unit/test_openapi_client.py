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

#: (route, method) -> (declared 200 model, list-of?)
#:
#: WEB8 re-keyed this by METHOD as well as path. ``/intake`` answers GET with the
#: queue and POST with one created record, and those are different shapes — a
#: path-keyed table could only pin one of them, which is how a surface with two
#: verbs keeps half a guard.
CONSOLE_ROUTES = {
    ("/health", "get"): ("HealthOut", False),
    ("/login", "post"): ("LoginOut", False),
    ("/logout", "post"): ("StatusOut", False),
    ("/queries", "get"): ("NamedQueryOut", True),
    ("/query/{query_id}", "post"): ("NamedRunOut", False),
    ("/raw-cypher", "post"): ("NamedRunOut", False),
    ("/specs", "get"): ("SpecOut", True),
    ("/specs/{spec_id}/run", "post"): ("SpecRunOut", False),
    # ── WEB8: O70's recorded follow-up, now declared ──────────────────────
    ("/docs-verify", "get"): ("CorpusStatusOut", False),
    ("/admin/log-estate", "get"): ("LogEstateOut", False),
    ("/specs/ephemeral", "post"): ("EphemeralRegisterOut", False),
    ("/intake", "get"): ("IntakeListOut", False),
    ("/intake", "post"): ("IntakeRecordOut", False),
    ("/intake/{intake_id}", "get"): ("IntakeRecordOut", False),
    ("/intake/{intake_id}/evidence", "post"): ("IntakeEvidenceOut", False),
    ("/intake/{intake_id}/transition", "post"): ("IntakeRecordOut", False),
    ("/intake/{intake_id}/thread-decision", "post"): ("IntakeRecordOut", False),
    ("/mappings/domains", "get"): ("MappingDomainsOut", False),
    ("/mappings/grid/{domain_id}", "get"): ("MappingGridOut", False),
    ("/mappings/options", "get"): ("MappingOptionsOut", False),
    ("/mappings/changeset", "post"): ("ChangesetArtifactOut", False),
    ("/mappings/overrides/draft", "post"): ("DraftReceiptOut", False),
    ("/mappings/overrides/report", "get"): ("CorrectionsReportOut", False),
    ("/mappings/pending/report", "get"): ("PendingCorrectionsReportOut", False),
    ("/mappings/drafts", "get"): ("OpenDraftsOut", False),
    ("/mappings/drafts/{draft_id}/promote", "post"): ("PromotedDiffOut", False),
    ("/mappings/app-code/draft", "post"): ("DraftReceiptOut", False),
    ("/mappings/app-code/migrations", "get"): ("AppCodeMigrationsOut", False),
}


def _ok_schema(doc: dict, path: str, method: str) -> dict:
    return doc["paths"][path][method]["responses"]["200"]["content"]["application/json"]["schema"]


@pytest.mark.parametrize("route", sorted(CONSOLE_ROUTES))
def test_console_route_declares_its_response_model(route: tuple[str, str]) -> None:
    path, method = route
    model, is_list = CONSOLE_ROUTES[route]
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


#: The ONLY operations allowed to answer without a declared model, each with the
#: reason it is not one. Two return no JSON at all; the third is open by design.
UNMODELLED = {
    ("/demo", "get"): "the dev-mode demo PAGE — HTML, not JSON",
    ("/specs/{spec_id}/export", "post"): "a streamed export file, not a JSON body",
    ("/exports/{export_id}/manifest", "get"): (
        "the export ledger record is open by design — the console types it "
        "Record<string, unknown> and drydocs_api.schemas says so"
    ),
}


def test_every_json_route_declares_a_response_model() -> None:
    """WEB8, and the inversion of the test this replaces.

    O70 modelled the query/spec surface and left a list of routes that still
    answered with free objects; the guard here USED to assert that list was
    non-empty, so that promoting a route out of it was a deliberate act. WEB8
    emptied it, so the guard now runs the other way: every operation that
    answers with JSON declares a model, and the only exceptions are the three
    named in UNMODELLED with their reasons.

    Why this direction is the stronger one. The old shape guarded the routes it
    already knew about — a NEW route added with `-> dict[str, object]` was
    invisible to it, which is exactly how /admin/log-estate (O68, after O70)
    opened the same hole again and was found by re-measuring rather than by a
    test. This shape fails on the new route instead."""
    doc = _committed()
    holes = []
    for path, ops in doc["paths"].items():
        for method, op in ops.items():
            if (path, method) in UNMODELLED:
                continue
            content = op.get("responses", {}).get("200", {}).get("content", {})
            schema = content.get("application/json", {}).get("schema")
            if schema is None:
                holes.append(f"{method.upper()} {path} — no JSON 200 body, and not in UNMODELLED")
                continue
            if "$ref" in schema:
                continue
            if schema.get("type") == "array" and "$ref" in schema.get("items", {}):
                continue
            holes.append(f"{method.upper()} {path} — answers {schema}")
    assert not holes, (
        "these operations answer JSON without a declared model — model them in "
        "drydocs_api.schemas and add them to CONSOLE_ROUTES, or record the reason "
        "in UNMODELLED:\n  " + "\n  ".join(holes)
    )


def test_the_unmodelled_exceptions_still_exist() -> None:
    """An exception that outlives its route is a licence nobody revoked. If one
    of these 404s out of the schema, delete its row rather than leave it."""
    doc = _committed()
    for path, method in UNMODELLED:
        assert path in doc["paths"], f"{path} is gone — drop it from UNMODELLED"
        assert method in doc["paths"][path], f"{method.upper()} {path} is gone — drop its row"
