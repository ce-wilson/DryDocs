"""O68: the log estate, and the one rule stated in the negative.

Clause (c) — the debug tier is REPORTED, never RENDERED. ADR 0014 clause 6
splits the lean API log from a verbose short-retention debug log that carries
Cypher text and request detail. CAPTURING that text is ruled; SURFACING it in a
console is not, and they are different risks: a short-lived file on an
operator's disk versus a page anyone with the console can read.

A comment saying "we never return contents" is not a guard. What makes it true
is that nothing in the path OPENS a file — core stats, the API shapes, the panel
renders — and that is what the tests below assert, in the code rather than in
the prose around it (J66).
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from drydocs_core.log_estate import estate
from drydocs_core.log_kinds import LogKind

REPO = Path(__file__).resolve().parents[2]
API_MODULE = REPO / "drydocs_api" / "log_estate.py"
CORE_MODULE = REPO / "drydocs_core" / "log_estate.py"
PANEL = REPO / "web" / "src" / "routes" / "LogEstatePanel.tsx"
CLIENT = REPO / "web" / "src" / "lib" / "logEstate.ts"


def _kind(kind_id: str, retention: int = 90, directory: str | None = None) -> LogKind:
    return LogKind(
        id=kind_id,
        level="INFO",
        retention_days=retention,
        rotation="per-run",
        format="log",
        dir=directory,
        writer="test",
        status="active",
        note="",
    )


def _write(path: Path, name: str, size: int, age_days: int = 0) -> None:
    import os

    target = path / name
    target.write_bytes(b"x" * size)
    if age_days:
        when = (datetime.now(UTC) - timedelta(days=age_days)).timestamp()
        os.utime(target, (when, when))


# --------------------------------------------------------------------------- #
# the core walk
# --------------------------------------------------------------------------- #
def test_a_kind_counts_only_its_own_files(tmp_path: Path) -> None:
    """Every kind currently declares ``dir: null`` — they share one root — so a
    kind's files are the ones its naming rule claims. Without the prefix filter
    every kind would report every other kind's bytes, and the panel's whole
    subject is per-kind size."""
    _write(tmp_path, "load.run.20260101.log", 100)
    _write(tmp_path, "load.other.20260102.log", 50)
    _write(tmp_path, "api-debug.run.20260101.log", 900)
    out = {e.kind.id: e for e in estate(kinds=(_kind("load"), _kind("api-debug")), root=tmp_path)}
    assert (out["load"].file_count, out["load"].total_bytes) == (2, 150)
    assert (out["api-debug"].file_count, out["api-debug"].total_bytes) == (1, 900)


def test_a_kind_with_its_own_directory_owns_everything_in_it(tmp_path: Path) -> None:
    sub = tmp_path / "audit"
    sub.mkdir()
    _write(sub, "anything-at-all.txt", 42)
    (out,) = estate(kinds=(_kind("audit", directory="audit"),), root=tmp_path)
    assert (out.exists, out.file_count, out.total_bytes) == (True, 1, 42)


def test_an_absent_directory_is_absent_and_not_empty(tmp_path: Path) -> None:
    """Absent and empty are different facts and the panel says which. A kind
    declared before its writer exists has no directory, which is correct; an
    active kind with none is worth a look."""
    (out,) = estate(kinds=(_kind("load"),), root=tmp_path / "nothing")
    assert out.exists is False
    assert (out.file_count, out.total_bytes, out.oldest_days) == (0, 0, None)


def test_it_never_creates_the_directory_it_reports_on(tmp_path: Path) -> None:
    missing = tmp_path / "nothing"
    estate(kinds=(_kind("load"),), root=missing)
    assert not missing.exists(), "a report that repairs the tree has hidden what it was asked about"


def test_over_retention_is_reported_not_acted_on(tmp_path: Path) -> None:
    _write(tmp_path, "api-debug.run.20260101.log", 10, age_days=30)
    (out,) = estate(kinds=(_kind("api-debug", retention=7),), root=tmp_path)
    assert out.oldest_days is not None and out.oldest_days >= 29
    assert out.over_retention is True
    # and the file is still there — this reports, it does not sweep
    assert (tmp_path / "api-debug.run.20260101.log").exists()


def test_a_kind_within_retention_is_not_flagged(tmp_path: Path) -> None:
    _write(tmp_path, "load.run.20260101.log", 10, age_days=3)
    (out,) = estate(kinds=(_kind("load", retention=90),), root=tmp_path)
    assert out.over_retention is False


# --------------------------------------------------------------------------- #
# clause (c): the debug tier's CONTENTS are unreachable
# --------------------------------------------------------------------------- #
def test_the_estate_returns_no_file_contents(tmp_path: Path) -> None:
    """The behavioural half: a file with distinctive text in it, and nothing in
    the returned structure carries that text."""
    secret = "MATCH (n:Secret) RETURN n"
    _write(tmp_path, "api-debug.run.20260101.log", 0)
    (tmp_path / "api-debug.run.20260101.log").write_text(secret, encoding="utf-8")
    (out,) = estate(kinds=(_kind("api-debug", retention=7),), root=tmp_path)
    assert secret not in repr(out)
    assert out.total_bytes == len(secret)  # it was measured, not read


def test_no_module_in_the_path_opens_a_file() -> None:
    """The structural half, and the one that matters: "never rendered" is only
    true while nothing in the chain CAN read a log. Core stats, the API shapes,
    the client fetches, the panel renders — none of them opens anything.

    Read as code with comments stripped (J66): every one of these modules names
    the rule in its own header, and a raw scan would fail on the explanation.
    """
    opener = re.compile(r"\b(open|read_text|read_bytes|readlines)\s*\(")
    for path in (CORE_MODULE, API_MODULE):
        code = re.sub(r'"""[\s\S]*?"""|#[^\n]*', " ", path.read_text(encoding="utf-8"))
        found = opener.findall(code)
        assert not found, f"{path.name} can read a file's contents: {found}"


def test_the_web_half_asks_for_no_file() -> None:
    """The panel makes ONE request with no arguments, and the payload it declares
    has no contents field. A parameter naming a file is how this rule would be
    lost — not by someone deciding to render a log, but by a `?path=` that looked
    harmless."""
    client = CLIENT.read_text(encoding="utf-8")
    panel = PANEL.read_text(encoding="utf-8")
    # the client's only call is the bare endpoint
    calls = re.findall(r"api\.(GET|POST|PUT|DELETE)\(([^)]*)\)", client)
    assert calls == [("GET", "'/admin/log-estate', { signal }")], calls
    # and neither declares a field that could hold a log's text
    for name, text in (("client", client), ("panel", panel)):
        code = re.sub(r"/\*[\s\S]*?\*/|//[^\n]*", " ", text)
        for word in ("contents", "body:", "tail", "preview"):
            assert (
                word not in code
            ), f"{name} names {word!r} — clause (c) forbids surfacing contents"


def test_the_scan_would_notice(tmp_path: Path) -> None:
    """Instrument check (J76). Both scans above are absence assertions, and an
    absence assertion over a pattern that never matches anything is a pass that
    means nothing. These are the same patterns against text that DOES contain
    what they look for."""
    opener = re.compile(r"\b(open|read_text|read_bytes|readlines)\s*\(")
    assert opener.findall("data = path.read_text(encoding='utf-8')")
    assert opener.findall("with open(p) as fh:")
    calls = re.findall(r"api\.(GET|POST|PUT|DELETE)\(([^)]*)\)", "api.GET('/x', { signal })")
    assert calls == [("GET", "'/x', { signal }")]


# --------------------------------------------------------------------------- #
# the panel is on the page the SME asked for
# --------------------------------------------------------------------------- #
def test_the_panel_is_a_tab_on_the_admin_page_not_a_new_route() -> None:
    """Clause (a): a PANEL on the existing O12 surface. A new route would also
    need a new registry entry, a new gate and a new nav item — and the SME
    placed it here."""
    admin = (REPO / "web" / "src" / "routes" / "AdminConfigRoute.tsx").read_text(encoding="utf-8")
    assert "LogEstatePanel" in admin
    assert "'Log estate':" in admin
    app = (REPO / "web" / "src" / "App.tsx").read_text(encoding="utf-8")
    assert "LogEstatePanel" not in app, "the estate is a panel, not a route"


@pytest.mark.parametrize("clause", ["landing-zones", "Contents are never shown"])
def test_the_panel_states_why_it_exists(clause: str) -> None:
    """Clause (e) asks for the reason in the panel's OWN COPY or the PR note.
    In the copy: a reader looking at a table of directories is exactly the person
    who should be told the CLI answers the same question, and that no log's text
    will ever appear here."""
    assert clause in PANEL.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# the endpoint actually answers (clause b: "a read endpoint over that")
# --------------------------------------------------------------------------- #
class _AcceptingCredentials:
    """O75 re-checks on every request that the session's account still exists,
    against a machine-local file a fresh clone does not have. Injected so the
    test is venue-independent (J18) rather than passing only where someone has
    signed in once."""

    is_bootstrapped = True

    def verify(self, identity: str, secret: str) -> bool:
        return False

    def has_identity(self, identity: str) -> bool:
        return True


@pytest.fixture()
def api_client(monkeypatch, tmp_path):
    """drydocs-api in process, with the data root pointed at a tmp tree.

    G81: create_app builds the intake store at import and the data root has no
    default. A per-test tmp_path also keeps the estate this reports from being
    the developer's real one — the endpoint walks whatever DRYDOCS_LOGDIR names,
    and a test that walked a real log directory would be both unrepeatable and
    slow.
    """
    pytest.importorskip("fastapi", reason="fastapi lives in the optional 'api' group")
    from fastapi.testclient import TestClient

    from drydocs_api.app import create_app
    from drydocs_api.sessions import InMemorySessionStore

    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    (tmp_path / "logs").mkdir(parents=True)
    _write(tmp_path / "logs", "load.run.20260101.log", 128)

    sessions = InMemorySessionStore()
    app = create_app(runner=None, store=sessions, credentials=_AcceptingCredentials())
    with TestClient(app) as client:
        client.sessions = sessions  # type: ignore[attr-defined]
        yield client


def _bearer(client, persona: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {client.sessions.issue(persona).token}"}


def test_the_endpoint_answers_for_an_admin(api_client) -> None:
    """Registered is not the same as working. test_openapi_client proves the
    route EXISTS; this proves it returns something, through the real dependency
    chain that resolves the log root and the zones from the environment."""
    res = api_client.get("/admin/log-estate", headers=_bearer(api_client, "morpheus"))
    assert res.status_code == 200, res.text
    body = res.json()
    assert set(body) == {"kinds", "zones"}
    kinds = {k["id"]: k for k in body["kinds"]}
    assert "load" in kinds and "api-debug" in kinds
    assert kinds["load"]["file_count"] == 1
    assert kinds["load"]["total_bytes"] == 128
    # the debug kind is REPORTED like any other, with no contents anywhere
    assert kinds["api-debug"]["retention_days"] == 7
    assert "contents" not in res.text and "tail" not in res.text


def test_the_endpoint_is_admin_only(api_client) -> None:
    """It names real paths on the host's disk — operational detail an admin is
    asking for and a user-tier persona is not."""
    res = api_client.get("/admin/log-estate", headers=_bearer(api_client, "mouse"))
    assert res.status_code == 403, res.text


def test_the_endpoint_refuses_an_unauthenticated_caller(api_client) -> None:
    assert api_client.get("/admin/log-estate").status_code == 401
