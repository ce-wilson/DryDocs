"""Every browser origin the UI-test ledger documents must actually be served (O85).

THE DEFECT THIS CLOSES IS THE DRIFT, not the one port. ``config/taxonomy/ui-tests.yaml``
cites ``Vite :5199`` in five ``source`` fields because five real verifications ran
there — the standard port was taken, so the fallback quietly became the documented
one — while ``drydocs_api``'s cross-origin allowlist still named only 5173 and 4173.
Nothing connected the two, so from O69 until 2026-08-30 the console could not sign in
on its own documented verification port, and the client blamed an unreachable server
for it (Idea-200, found while verifying O77).

WHAT MAKES THIS CHECKABLE AT ALL: the ledger writes its venue in one shape,
``Vite :<port>``, so the ports are extractable without reading prose for meaning.
That is the whole reason this guard can exist — a free-text venue would leave nothing
to check, and the fix would have to be a convention nobody enforces.

J37 — THE ALLOWLIST IS READ FROM THE BUILT APP, never from the source of ``app.py``.
``create_app()`` is importable and the middleware stack holds the real list, so this
asks the object what it will serve instead of pattern-matching the call that
configured it. A regex over the source would also match the comment that explains the
list, which is J66's failure mode in the same file.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml", reason="PyYAML not installed")

REPO = Path(__file__).resolve().parents[2]
LEDGER = REPO / "config" / "taxonomy" / "ui-tests.yaml"

#: How the ledger writes a browser venue: "... vs Vite :5199 ...".
VITE_PORT = re.compile(r"Vite\s*:(\d{4,5})")

#: Ports the ledger cites that are deliberately NOT in the built-in allowlist,
#: each with the mechanism that supplies them instead. An entry here is a
#: statement that something else declares the origin, not a way to silence the
#: guard — adding one without naming a real mechanism is the drift this test
#: exists for.
#:
#: THE FRICTION IS THE FEATURE. Every ad-hoc verification port needs a line here
#: saying how its origin was supplied, which is mildly annoying and is the whole
#: point: the defect this guards was a port that got DOCUMENTED as a venue while
#: nothing served it. This map caught its own author within the hour — the O86
#: verification ran on 5176 and the full suite went red until the mechanism was
#: written down.
SUPPLIED_ELSEWHERE = {
    "5273": (
        "the O80 end-to-end suite's dedicated port — web/playwright.config.ts passes "
        "it through DRYDOCS_CORS_ORIGINS so the suite never adopts or collides with "
        "a dev server somebody is already running"
    ),
    "5176": (
        "the O86 full-page-canvas verification — a one-off port, supplied at run time "
        "with DRYDOCS_CORS_ORIGINS rather than added to the built-in list, which is "
        "what that variable is for. Deliberately NOT promoted to the allowlist: a "
        "built-in entry is a standing statement about what the API serves, and a "
        "single verification is not one"
    ),
}


def _allowlist() -> list[str]:
    """The origins the built app will actually serve, from the middleware stack."""
    from drydocs_api.app import create_app

    app = create_app()
    for middleware in app.user_middleware:
        origins = middleware.kwargs.get("allow_origins")
        if origins is not None:
            return list(origins)
    raise AssertionError("no CORS middleware found on the app — has create_app() changed?")


def _ledger_vite_ports() -> set[str]:
    doc = yaml.safe_load(LEDGER.read_text(encoding="utf-8"))
    ports: set[str] = set()
    for suite in doc["suites"]:
        for case in suite["cases"]:
            ports |= set(VITE_PORT.findall(case.get("source", "")))
    return ports


def test_the_ledger_still_records_its_venues_in_the_readable_shape() -> None:
    """A guard that silently finds nothing passes forever.

    If the ``Vite :<port>`` convention is dropped, this module stops checking
    anything and reports success — the same failure mode as the drift it guards.
    """
    assert _ledger_vite_ports(), (
        "no 'Vite :<port>' venue found in any ui-tests.yaml source field — either the "
        "convention changed or this guard has quietly stopped checking"
    )


def test_every_documented_verification_port_is_served_or_declared() -> None:
    allowed_ports = {
        m.group(1) for origin in _allowlist() if (m := re.search(r":(\d{4,5})$", origin))
    }
    unserved = sorted(
        port
        for port in _ledger_vite_ports()
        if port not in allowed_ports and port not in SUPPLIED_ELSEWHERE
    )
    assert not unserved, (
        f"the ui-tests ledger documents verification(s) on port(s) {unserved}, which the "
        "API's cross-origin allowlist does not serve and nothing else supplies. A console "
        "served there cannot sign in, and the browser reports it as an unreachable server. "
        "Either add the origin to create_app()'s allowlist, or add it to SUPPLIED_ELSEWHERE "
        "naming the mechanism that passes it."
    )


def test_the_standard_dev_and_preview_ports_are_served() -> None:
    """The two the console is normally reached on. Pinned so a refactor of the
    list cannot drop them silently — losing these breaks every developer at once,
    which is loud, but a guard that only catches loud failures is worth little."""
    allowlist = _allowlist()
    for origin in ("http://localhost:5173", "http://localhost:4173"):
        assert origin in allowlist, f"{origin} is no longer served"


def test_the_allowlist_is_a_list_of_named_origins_not_a_wildcard() -> None:
    """`*` or a localhost regex would end this class of bug by ending the boundary.

    Widening to "any origin", or to "any port on this machine", is a materially
    different trust decision from "these named ports" — and it is not one to adopt
    as a side effect of a port fix. DRYDOCS_CORS_ORIGINS already covers the one-off
    case declaratively, which is what makes the narrow list affordable.
    """
    assert "*" not in _allowlist()

    from drydocs_api.app import create_app

    app = create_app()
    for middleware in app.user_middleware:
        assert not middleware.kwargs.get("allow_origin_regex"), (
            "an origin REGEX was added to the console allowlist — that is a wider trust "
            "boundary than the named list and needs a decision, not a test update"
        )
