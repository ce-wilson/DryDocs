"""O72 — the one-command console stack says what the runbook says.

A Compose file is configuration that nothing type-checks and that only fails
when somebody runs it, which on a convenience stack can be weeks. The four rules
below are the ones whose breakage is SILENT — the stack still starts, and what
it starts is wrong:

* **Every service declares a health check.** `docker compose up --wait` returns
  when every service is healthy; a service with no health check counts as
  healthy the moment its process exists. One missing block and `--wait` goes
  back to meaning "started", which is the thing the item exists to replace.
* **No secret is a literal.** Every value under a password/key/secret-shaped name
  is a `${...}` reference. CLAUDE.md §3 keeps credentials out of commits, and a
  Compose file is a normal tracked file with an unusually inviting place to type
  one.
* **The health checks are the RUNBOOK's checks.** The agent's is the whole of the
  runbook's "exactly four apps, not five" (R14): a fifth entry named `common`
  means the flat loader came back. Asserting the four names here is what makes
  that regression a service that never comes up.
* **The proxy's path map is not restated.** ADR 0020 declares it once, in
  `web/delivery.json`. `deploy/render_proxy_config.mjs` renders the nginx config
  from that file, and the prefixes must appear nowhere else — a hand-typed
  `/api` in a config or a Dockerfile is a second copy that dev cannot contradict,
  because Vite re-reads the JSON and nginx would not.

**J66 — the scan of the renderer reads CODE, not the prose around it.** The
script's header explains the `/api` example at length, so a bare substring search
would match the explanation and fail on it. Comments and string literals are
stripped the way `tests/source_scan.py` does it for Python; the stripper here is
JS-shaped and local, because that helper does not speak JavaScript.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
COMPOSE = REPO / "compose.yaml"
DEPLOY = REPO / "deploy"
DELIVERY = REPO / "web" / "delivery.json"
DEV_ENVIRONMENT = REPO / "config" / "dev-environment.yaml"
RENDERER = DEPLOY / "render_proxy_config.mjs"

#: The runbook's Startup step 3 success check, verbatim: "returns exactly
#: controlm_fix, core_ingest, graph_qa, graph_query — four apps, not five".
#: Sorted, because the health check sorts before comparing.
AGENT_APPS = ["controlm_fix", "core_ingest", "graph_qa", "graph_query"]

#: A value under a name matching this is a credential. Substring, case-folded —
#: DRYDOCS_AGENT_REG_KEY and NEO4J_PASSWORD both land here, and so does anything
#: named later without this list needing an edit.
SECRET_NAME_PARTS = ("password", "secret", "_key", "token", "credential")

#: Names that match the list above but carry a LOCATION rather than a value.
#: Enumerated, never inferred from the value's shape: "it looks like a path" is a
#: test a real leaked secret can pass, and this exemption has to be a decision
#: somebody made about a specific name. Adding one means saying why here.
NOT_SECRET_NAMES = {
    # The credential FILE's path inside the container. The file itself is a
    # read-only bind mount from gitignored internal-local/; the path is as
    # public as any other mount point.
    "DRYDOCS_CONSOLE_CREDENTIALS",
}

#: Services that run to completion instead of staying up (plugin copy, database
#: provisioning). A health check on a container that exits is meaningless — and
#: `--wait` already covers them, through `service_completed_successfully`.
INIT_SERVICES = {"neo4j-plugins", "neo4j-provision"}


def _compose() -> dict:
    return yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))


def _services() -> dict[str, dict]:
    return _compose()["services"]


def _js_code_only(text: str) -> str:
    """JavaScript with comments and string/template literals blanked out.

    The same idea as ``tests.source_scan.code_only`` and for the same reason
    (J66), reimplemented because that helper tokenises Python. Deliberately
    simple: it handles ``//``, ``/* */`` and the three quote forms, which is all
    this one file uses. The instrument test below proves it did something.
    """
    out = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    out = re.sub(r"(?m)//.*$", " ", out)
    for quote in ("'", '"', "`"):
        out = re.sub(rf"{quote}(?:\\.|[^{quote}\\])*{quote}", '""', out, flags=re.DOTALL)
    return out


def test_every_long_running_service_declares_a_health_check() -> None:
    missing = [
        name
        for name, spec in _services().items()
        if name not in INIT_SERVICES and "healthcheck" not in spec
    ]
    assert not missing, (
        f"services with no healthcheck: {missing}. `docker compose up --wait` treats a "
        "service with none as healthy as soon as its process exists, so --wait silently "
        "goes back to meaning 'started' — which is the failure O72 replaced."
    )


def test_no_credential_is_written_as_a_literal() -> None:
    literals: list[str] = []
    for name, spec in _services().items():
        for key, value in (spec.get("environment") or {}).items():
            if key in NOT_SECRET_NAMES:
                continue
            if not any(part in key.casefold() for part in SECRET_NAME_PARTS):
                continue
            if not isinstance(value, str) or "${" not in value:
                literals.append(f"{name}.environment.{key}")
    assert not literals, (
        f"credential-shaped values that are not ${{...}} references: {literals}. "
        "Secrets reach the stack from the environment or the gitignored .env; a "
        "literal here is a credential in a tracked file (CLAUDE.md §3)."
    )


def test_the_agent_health_check_is_the_runbooks_four_apps() -> None:
    """R14's regression, expressed as a health check rather than as a surprise."""
    test = _services()["agent"]["healthcheck"]["test"]
    body = "\n".join(test) if isinstance(test, list) else str(test)
    assert "/list-apps" in body, "the agent health check does not call /list-apps"
    for app in AGENT_APPS:
        assert app in body, f"the agent health check does not name {app}"
    assert "common" not in body, (
        "the agent health check names `common`, the shared package the flat loader "
        "wrongly lists as a fifth app — it must be absent, not expected"
    )


def test_the_api_health_check_asserts_the_value_not_just_a_response() -> None:
    test = _services()["api"]["healthcheck"]["test"]
    body = "\n".join(test) if isinstance(test, list) else str(test)
    assert "/health" in body and "ok" in body, (
        "the api health check must assert {'status': 'ok'} — the runbook's own success "
        f"test for Startup step 2 — not merely that something answered: {body!r}"
    )


def test_the_proxy_path_map_is_read_from_delivery_json_and_not_restated() -> None:
    """ADR 0020's map is declared once; nginx gets it by rendering, not by retyping."""
    code = _js_code_only(RENDERER.read_text(encoding="utf-8"))
    assert "delivery" in code, "the renderer does not read delivery.json"
    restated = [p for p in ("/api", "/agent") if p in code]
    assert not restated, (
        f"the proxy renderer hard-codes {restated} in CODE. The prefixes come from "
        "web/delivery.json (ADR 0020) — a second copy cannot be contradicted by dev, "
        "because Vite re-reads the JSON and nginx would not, so the stack would "
        "silently forward nothing and the SPA fallback would answer 200."
    )


def test_the_compose_neo4j_matches_the_declared_dev_environment() -> None:
    """config/dev-environment.yaml is the source of truth for the container facts."""
    declared = yaml.safe_load(DEV_ENVIRONMENT.read_text(encoding="utf-8"))["neo4j"]
    neo4j = _services()["neo4j"]
    assert neo4j["image"] == declared["image"], (
        f"compose.yaml runs {neo4j['image']}, config/dev-environment.yaml declares "
        f"{declared['image']} — change the declaration first, then this file"
    )
    env = neo4j["environment"]
    assert "NEO4J_PLUGINS" not in env, (
        "NEO4J_PLUGINS asks the entrypoint to DOWNLOAD each plugin at startup; when the "
        "download cannot happen the container starts anyway with the plugin ABSENT. That "
        "ran undetected for weeks (dev-environment.yaml, 2026-07-28). The jars ship in "
        "the image — copy them into the plugins volume, as neo4j-plugins does."
    )


def test_the_stack_never_touches_the_canonical_container_or_its_volumes() -> None:
    """The one mistake here that destroys data rather than annoying you.

    Two Neo4j servers on one store corrupts it, and `docker compose down -v` on a
    stack that mounted `neo4j-testdata` would delete the graph the whole session
    ritual runs on.
    """
    declared = yaml.safe_load(DEV_ENVIRONMENT.read_text(encoding="utf-8"))["neo4j"]
    reserved = {declared["volume"], declared["plugins_volume"]}
    compose = _compose()
    assert not (reserved & set(compose.get("volumes") or {})), (
        f"compose.yaml declares one of the canonical container's volumes ({reserved}). "
        "The stack must own its own volumes."
    )
    for name, spec in compose["services"].items():
        for mount in spec.get("volumes") or []:
            source = str(mount).split(":", 1)[0]
            assert source not in reserved, (
                f"{name} mounts {source}, which belongs to the `{declared['container']}` "
                "container — two servers on one store corrupts it"
            )


def test_the_dockerignore_keeps_internal_material_out_of_every_image() -> None:
    """The publish boundary in image form: a COPY bakes what the context holds."""
    ignored = {
        line.strip()
        for line in (REPO / ".dockerignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    for required in ("internal-local/", "internal/", "web/.env.local", "node_modules/"):
        assert required in ignored, (
            f".dockerignore does not exclude {required!r}. An image layer survives every "
            "later delete and travels with the image, so the rule that decides what may "
            "be pushed decides what may enter a build context (CLAUDE.md §3)."
        )


def test_the_instruments_read_what_they_claim_to() -> None:
    """J76 — three of the checks above fail INTO 'clean' if their reader breaks.

    An empty service map passes the healthcheck and secret tests vacuously; a
    JS stripper that blanked the whole file passes the path-map test the same
    way. Pin a known member of each.
    """
    services = _services()
    assert {"neo4j", "api", "agent", "console"} <= set(
        services
    ), f"compose.yaml does not define the expected services: {sorted(services)}"
    assert any(
        "password" in key.casefold()
        for spec in services.values()
        for key in (spec.get("environment") or {})
    ), "no credential-shaped environment name found at all — is the parse working?"
    code = _js_code_only(RENDERER.read_text(encoding="utf-8"))
    assert "writeFileSync" in code, "the JS stripper removed the renderer's own code"
    assert "ADR 0020" not in code, "the JS stripper did not strip comments"


def test_the_delivery_prefixes_are_the_two_the_stack_proxies() -> None:
    """Reads delivery.json (the declaration), never the rendered nginx config (J37)."""
    import json

    delivery = json.loads(DELIVERY.read_text(encoding="utf-8"))
    assert set(delivery) == {"api", "agent"}, (
        f"web/delivery.json declares {sorted(delivery)}; the stack's proxy renders a "
        "route per entry, so a new one needs a service to forward to"
    )
