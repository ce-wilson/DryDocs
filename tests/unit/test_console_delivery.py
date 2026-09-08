"""The console's delivery shape (ADR 0020, WEB10): same-origin, path-routed, no coordinate in the bundle.

THE DEFECT CLASS THIS RETIRES. From O69 until 2026-08-30 the console could not sign
in on its own documented verification port, because drydocs-api's cross-origin
allowlist named two ports and the ledger had quietly moved to a third (Idea-200,
found at O77; fixed at O85 with a probe that told "blocked origin" from "dead
server"). The predecessor of this file, test_console_origins.py, guarded that
allowlist against the ledger. ADR 0020 removed the boundary instead of guarding
it: the console calls the PATH ``/api`` on its own origin and a reverse proxy
forwards it (Vite's own proxy in dev and preview, the Compose stack in
production), so there is no allowlist to drift, no ``DRYDOCS_CORS_ORIGINS`` to
forget, and no probe to run. What this file guards is that the shape stays.

J37 - the app is READ AS AN OBJECT (``create_app().user_middleware``), the env
registry as an object (``env_refs.DECLARED_VARIABLES``), and the path map as the
JSON it is. The two TypeScript readers of ``web/delivery.json`` and the dist
guard are checked with their comments removed (J66): a comment naming the file
does not count as reading it. ``tests.source_scan`` is Python's tokenizer and
cannot read TypeScript, so this file carries the same local ``//`` and ``/* */``
stripper ``test_first_party_queries.py`` uses, by that file's precedent.

FASTAPI IS OPTIONAL (the api group), so the app-object checks ``importorskip`` at
function scope and the rest runs everywhere - the same trade the predecessor made,
and for the same reason (a module-scope import once failed CI on the venue
without the api group).

The ledger-shape check at the bottom is carried over from the predecessor: the
``Vite :<port>`` shape in ``config/taxonomy/ui-tests.yaml`` is how a reader finds
which port a case was run on, and that stays true whether or not an allowlist
ever reads it again.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
WEB = REPO / "web"
DELIVERY = WEB / "delivery.json"
DIST_GUARD = WEB / "scripts" / "checkDistCoordinates.mjs"
CI = REPO / ".github" / "workflows" / "ci.yml"
LEDGER = REPO / "config" / "taxonomy" / "ui-tests.yaml"

#: The two TypeScript readers of the path map. Both must read the FILE, never
#: hold the strings: that is what keeps the browser's base and the proxy's route
#: from drifting apart.
READERS = (WEB / "vite.config.ts", WEB / "src" / "lib" / "auth.ts")

#: The three shapes a service coordinate takes in a built bundle; the dist guard
#: must carry each one as a pattern (read as code, so a comment does not count).
COORDINATE_SHAPES = ("localhost:", "127", "https?:")


def _delivery() -> dict:
    return json.loads(DELIVERY.read_text(encoding="utf-8"))


def _ts_code(path: Path) -> str:
    """TypeScript / JavaScript source with `//` and `/* */` comments removed;
    string literals stay, because the file paths and prefixes under test ARE
    string literals. Line-anchored on purpose, so a `//` inside a URL literal
    on a code line is left alone (the same trade test_first_party_queries makes).
    Line comments go FIRST: vite.config.ts's header quotes the route `/api/*`
    in a `//` comment, and a block-comment pass that ran first would read that
    as an opener and eat the code down to the next `*/`."""
    source = path.read_text(encoding="utf-8")
    source = re.sub(r"(?m)^\s*//.*$", "", source)
    return re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)


# ---- the path map -------------------------------------------------------------------


def test_the_path_map_declares_two_prefixes_and_nothing_else() -> None:
    """Prefixes ONLY. An upstream default in this file would reach dist/ through the
    JSON import in auth.ts, which is the coordinate ADR 0020 keeps out of the bundle."""
    d = _delivery()
    assert set(d) == {"api", "agent"}, sorted(d)
    for name, entry in d.items():
        assert set(entry) == {"prefix"}, (name, sorted(entry))
        prefix = entry["prefix"]
        assert prefix.startswith("/") and not prefix.endswith("/") and "//" not in prefix, prefix
        assert "localhost" not in prefix and ":" not in prefix, prefix
    assert d["api"]["prefix"] != d["agent"]["prefix"]


@pytest.mark.parametrize("reader", READERS, ids=lambda p: p.name)
def test_both_typescript_readers_read_the_file_as_code(reader: Path) -> None:
    code = _ts_code(reader)
    assert "delivery.json" in code, f"{reader.name} no longer reads web/delivery.json in code"


def test_no_reader_holds_the_prefix_as_a_literal_beside_the_file() -> None:
    """The file is the single declaration; a literal copy in either reader is the
    drift this shape exists to prevent."""
    prefixes = {e["prefix"] for e in _delivery().values()}
    for reader in READERS:
        code = _ts_code(reader)
        for p in prefixes:
            for quote in ("'", '"', "`"):
                assert f"{quote}{p}{quote}" not in code, (reader.name, p)


# ---- the API side: no CORS boundary, one non-secret config route --------------------


def test_the_api_carries_no_cors_middleware() -> None:
    pytest.importorskip("fastapi", reason="fastapi is an optional dep (the api group)")
    from drydocs_api.app import create_app

    app = create_app()
    names = [m.cls.__name__ for m in app.user_middleware]
    assert "CORSMiddleware" not in names, (
        f"a CORS middleware is back on the app ({names}). ADR 0020 made the console "
        "same-origin with the API through a reverse proxy; an allowlist is the boundary "
        "that drifted from O69 to 2026-08-30 and it is retired, not re-tuned."
    )


def test_the_api_serves_its_non_secret_runtime_values_on_config() -> None:
    """GET /config is where a per-deployment, non-secret value lives (the O39
    deep-link template), so the bundle need not inline it and one build can be
    promoted through every environment."""
    pytest.importorskip("fastapi", reason="fastapi is an optional dep (the api group)")
    from fastapi.testclient import TestClient

    from drydocs_api.app import create_app

    client = TestClient(create_app())
    res = client.get("/config")
    assert res.status_code == 200
    body = res.json()
    assert set(body) == {"runtime_view_url_template"}, body


def test_the_cors_allowlist_variable_is_retired_from_the_env_registry() -> None:
    from drydocs_core import env_refs

    names = {v.name for v in env_refs.DECLARED_VARIABLES}
    assert "DRYDOCS_CORS_ORIGINS" not in names
    # The variables that replaced it: where the services live, read by the Vite
    # PROCESS (never inlined), and the API-side home of the O39 template.
    assert {
        "DRYDOCS_API_UPSTREAM",
        "DRYDOCS_AGENT_UPSTREAM",
        "DRYDOCS_RUNTIME_VIEW_URL_TEMPLATE",
    } <= names


# ---- the bundle guard exists and CI runs it -----------------------------------------


def test_the_dist_coordinate_guard_exists_and_ci_runs_it() -> None:
    assert DIST_GUARD.exists()
    pkg = json.loads((WEB / "package.json").read_text(encoding="utf-8"))
    assert pkg["scripts"].get("dist:check") == "node scripts/checkDistCoordinates.mjs"
    ci = CI.read_text(encoding="utf-8")
    assert "npm run dist:check" in ci, "the web CI job no longer runs the dist coordinate guard"


def test_the_guard_carries_every_shape_a_service_coordinate_takes() -> None:
    """Read as code: the patterns are the contract, so a later edit that drops one
    is visible here and not only in a bundle that happens to carry it."""
    code = _ts_code(DIST_GUARD)
    for shape in COORDINATE_SHAPES:
        assert shape in code, shape


# ---- neither proxy forwards the browser's Origin to an upstream ----------------------
#
# THE DEFECT THIS RETIRES (2026-09-07). ADR 0020's premise is that the browser makes
# no cross-origin request, so no service needs an allowlist. True at the BROWSER —
# page and /agent share an origin — and false at the UPSTREAM: both proxies rewrite
# Host and forwarded `Origin` untouched, so a service on its own port received
# `Origin: <page origin>` and read it as cross-origin, which at that hop it is. The
# ADK (agents/serve.py, no --allow_origins on this ADR's reasoning) has origin
# checking on with an EMPTY allowlist, so every console Ask got
# "403 Forbidden: origin not allowed" while every /api page worked, because
# drydocs-api has no origin check to fail. Reproduced both ways: the ADK answers 200
# with no Origin header and 403 with one.
#
# Both proxies must therefore drop the header, and BOTH are checked here because the
# defect was that they agreed on Host and diverged on nothing else — one fixed and
# one not would put dev and the Compose stack back on two different requests, which
# is the drift this whole file exists to prevent.


def test_the_nginx_renderer_clears_origin_on_every_proxied_prefix() -> None:
    """The RENDERED config, not the script's prose: the renderer is run and its
    output read, so this fails if the directive stops reaching nginx for any reason
    - a moved template, a prefix that renders its own header block, an edit that
    drops it from COMMON."""
    node = shutil.which("node")
    if node is None:  # pragma: no cover - node is present in CI's web job
        pytest.skip("node not on PATH")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "default.conf"
        subprocess.run(
            [node, str(REPO / "deploy" / "render_proxy_config.mjs"), str(DELIVERY), str(out)],
            check=True,
            capture_output=True,
        )
        conf = out.read_text(encoding="utf-8")
    # One `proxy_pass` per proxied location; every one of them must sit under a
    # block that clears Origin. COMMON is shared, so counting is the cheap check
    # that no location grew its own header set without it.
    assert 'proxy_set_header Origin "";' in conf, conf
    assert conf.count('proxy_set_header Origin "";') == conf.count(
        "proxy_set_header X-Forwarded-Proto"
    ), "a proxied location carries the forwarded-proto header but not the Origin clear"


def test_the_vite_proxy_removes_the_origin_header() -> None:
    """Read as code (J66), because the comment above the hook explains the defect and
    would satisfy a substring test on its own. `changeOrigin` rewrites HOST only, so
    the removal has to be explicit and this is what proves it still is."""
    code = _ts_code(WEB / "vite.config.ts")
    assert "proxyReq" in code, "the proxy no longer hooks proxyReq"
    assert re.search(
        r"removeHeader\(\s*['\"]origin['\"]\s*\)", code, re.IGNORECASE
    ), "vite.config.ts no longer removes the Origin header before forwarding"


# ---- the ledger still records venues in the readable shape (carried from O85) ------


def test_the_ledger_still_records_its_venues_in_the_readable_shape() -> None:
    ledger = yaml.safe_load(LEDGER.read_text(encoding="utf-8"))
    cases = [c for suite in ledger["suites"] for c in suite.get("cases", [])]
    venue_shape = re.compile(r"Vite :(\d{4,5})")
    ports = {int(m.group(1)) for c in cases for m in venue_shape.finditer(c.get("source", ""))}
    assert ports, "no case records the Vite port it was run on"
    assert all(1024 <= p <= 65535 for p in ports), sorted(ports)
