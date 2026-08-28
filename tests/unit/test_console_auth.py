"""O69 — console authentication: the credential half, the expiry, and the two
structural guards that keep both from quietly regressing.

Everything here runs WITHOUT FastAPI installed, which is the point. CI runs
``poetry install`` with no optional groups, so a credential check reachable only
through the ``api`` group would be a check CI never performs. The route-shape
guard below reads the source with ``ast`` for the same reason.
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from drydocs_api.credentials import (
    ALGORITHM,
    DEFAULT_RELATIVE_PATH,
    PATH_ENV_VAR,
    CredentialError,
    CredentialStore,
    credentials_path,
    hash_secret,
    verify_secret,
)
from drydocs_api.handlers import (
    BadCredentialsError,
    CredentialsNotConfiguredError,
    Forbidden,
    authenticate,
    login,
    require_role,
)
from drydocs_api.sessions import (
    ExpiredTokenError,
    InMemorySessionStore,
    InvalidTokenError,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SECRET = "a-test-console-secret"

# The WRITER lives outside drydocs_api on purpose (the ADR 0009 write guard);
# importing it from the script is the test admitting where it really is.
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from set_console_credential import save_store  # noqa: E402


def _store(*identities: str) -> CredentialStore:
    creds = CredentialStore()
    for identity in identities:
        creds.set(identity, SECRET)
    return creds


# ── the hash ────────────────────────────────────────────────────────────────


def test_hash_verifies_and_rejects():
    credential = hash_secret(SECRET)
    assert credential.algorithm == ALGORITHM
    assert verify_secret(credential, SECRET) is True
    assert verify_secret(credential, SECRET + "x") is False


def test_hash_is_salted_so_two_accounts_with_one_secret_do_not_match():
    """Equal hashes would tell anyone reading the file which accounts share a
    secret — the whole reason a salt is per-credential."""
    first, second = hash_secret(SECRET), hash_secret(SECRET)
    assert first.salt != second.salt
    assert first.hash != second.hash


def test_stored_file_never_contains_the_plaintext(tmp_path: Path):
    creds = _store("jdoe4821")
    target = save_store(creds, tmp_path / "console-credentials.json")
    text = target.read_text(encoding="utf-8")
    assert SECRET not in text
    payload = json.loads(text)
    assert payload["credentials"]["jdoe4821"]["algorithm"] == ALGORITHM


def test_empty_store_refuses_everything():
    creds = CredentialStore()
    assert creds.is_bootstrapped is False
    assert creds.verify("jdoe4821", SECRET) is False


def test_unknown_identity_returns_false_rather_than_raising():
    """An exception would be an enumeration oracle: the caller could tell a
    real id from an invented one by which failure it got."""
    creds = _store("jdoe4821")
    assert creds.verify("nobody-at-all", SECRET) is False


def test_round_trip_through_the_file(tmp_path: Path):
    target = save_store(_store("jdoe4821", "asmith7734"), tmp_path / "creds.json")
    reloaded = CredentialStore.load(target)
    assert reloaded.identities() == ("asmith7734", "jdoe4821")
    assert reloaded.verify("jdoe4821", SECRET) is True
    assert reloaded.verify("asmith7734", "wrong") is False


def test_absent_file_is_the_fresh_clone_state_not_an_error(tmp_path: Path):
    creds = CredentialStore.load(tmp_path / "does-not-exist.json")
    assert len(creds) == 0 and creds.is_bootstrapped is False


@pytest.mark.parametrize(
    ("payload", "fragment"),
    [
        ({"version": 99, "credentials": {}}, "format version"),
        ({"version": 1}, "credentials object"),
        ({"version": 1, "credentials": {"a": {"algorithm": "scrypt"}}}, "malformed"),
        (
            {
                "version": 1,
                "credentials": {
                    "a": {
                        "algorithm": "md5",
                        "salt": "00",
                        "hash": "00",
                        "n": 1,
                        "r": 1,
                        "p": 1,
                    }
                },
            },
            "unsupported hash algorithm",
        ),
    ],
)
def test_untrustworthy_file_is_refused_loudly(tmp_path: Path, payload: dict, fragment: str):
    target = tmp_path / "creds.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(CredentialError) as exc:
        CredentialStore.load(target)
    assert fragment in str(exc.value)


# ── where the hash lives (the ADR 0009 gap this item had to close) ──────────


def test_credential_file_is_not_under_var(monkeypatch: pytest.MonkeyPatch):
    """var/ carries a delete-me-freely contract because everything in it is
    derived from committed text. A credential has no committed source, so
    putting it there would silently break that contract for everything else."""
    monkeypatch.delenv(PATH_ENV_VAR, raising=False)
    parts = DEFAULT_RELATIVE_PATH.parts
    assert "var" not in parts
    assert parts[0] == "internal-local"
    assert credentials_path(REPO_ROOT) == REPO_ROOT / DEFAULT_RELATIVE_PATH


def test_credential_file_is_gitignored():
    """The publish boundary is enforced by git, not by intent. Ask git directly
    rather than reading .gitignore and reasoning about precedence."""
    target = REPO_ROOT / DEFAULT_RELATIVE_PATH
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(target)],
        cwd=REPO_ROOT,
        capture_output=True,
    )
    assert result.returncode == 0, f"{target} is NOT gitignored — a secret could be committed"


def test_no_credential_file_is_tracked():
    tracked = subprocess.run(
        ["git", "ls-files", "--", f"*{DEFAULT_RELATIVE_PATH.name}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert tracked.stdout.strip() == ""


# ── login ───────────────────────────────────────────────────────────────────


def test_login_issues_a_session_with_an_expiry():
    sessions = InMemorySessionStore()
    out = login("asmith7734", SECRET, sessions, _store("asmith7734"))
    assert out["persona_id"] == "asmith7734"
    assert out["role"] == "admin"  # resolved server-side, never sent by the client
    assert datetime.fromisoformat(out["expires_at"]) > datetime.now(UTC)
    assert authenticate(out["token"], sessions).role == "admin"


def test_login_refuses_a_wrong_secret():
    sessions = InMemorySessionStore()
    with pytest.raises(BadCredentialsError):
        login("asmith7734", "not-the-secret", sessions, _store("asmith7734"))


def test_login_refuses_an_empty_secret():
    """Empty must never short-circuit into a truthy comparison, and must not
    reach the KDF as a legitimate input."""
    sessions = InMemorySessionStore()
    with pytest.raises(BadCredentialsError):
        login("asmith7734", "", sessions, _store("asmith7734"))


def test_unknown_identity_and_wrong_secret_are_indistinguishable():
    """Same exception type, same message — which of the two it was is exactly
    what turns a login route into an account enumerator."""
    sessions = InMemorySessionStore()
    creds = _store("asmith7734")
    with pytest.raises(BadCredentialsError) as unknown:
        login("no-such-person", SECRET, sessions, creds)
    with pytest.raises(BadCredentialsError) as wrong:
        login("asmith7734", "nope", sessions, creds)
    assert str(unknown.value) == str(wrong.value)


def test_fresh_clone_says_what_to_run():
    sessions = InMemorySessionStore()
    with pytest.raises(CredentialsNotConfiguredError) as exc:
        login("asmith7734", SECRET, sessions, CredentialStore())
    assert "set_console_credential.py" in str(exc.value)


def test_a_failed_login_issues_no_session():
    sessions = InMemorySessionStore()
    with pytest.raises(BadCredentialsError):
        login("asmith7734", "wrong", sessions, _store("asmith7734"))
    assert sessions.purge_expired() == 0
    assert len(sessions._sessions) == 0  # the assertion IS the internal state


# ── expiry ──────────────────────────────────────────────────────────────────


def test_expired_token_is_rejected():
    sessions = InMemorySessionStore(ttl=timedelta(minutes=30))
    issued = datetime.now(UTC)
    session = sessions.issue("jdoe4821", now=issued)
    assert sessions.resolve(session.token, now=issued + timedelta(minutes=29)).role == "user"
    with pytest.raises(ExpiredTokenError):
        sessions.resolve(session.token, now=issued + timedelta(minutes=31))


def test_expired_reads_as_invalid_to_every_existing_caller():
    """ExpiredTokenError subclasses InvalidTokenError on purpose: ~20 routes
    already map that to 401, and expiry must not become a case one of them can
    forget."""
    assert issubclass(ExpiredTokenError, InvalidTokenError)


def test_expired_session_is_dropped_not_left_behind():
    sessions = InMemorySessionStore(ttl=timedelta(seconds=1))
    issued = datetime.now(UTC)
    session = sessions.issue("jdoe4821", now=issued)
    with pytest.raises(ExpiredTokenError):
        sessions.resolve(session.token, now=issued + timedelta(seconds=2))
    with pytest.raises(InvalidTokenError):  # gone, not merely expired
        sessions.resolve(session.token, now=issued)


def test_purge_expired_clears_only_the_stale_ones():
    sessions = InMemorySessionStore(ttl=timedelta(minutes=10))
    issued = datetime.now(UTC)
    old = sessions.issue("jdoe4821", now=issued - timedelta(hours=1))
    fresh = sessions.issue("asmith7734", now=issued)
    assert sessions.purge_expired(now=issued) == 1
    assert sessions.resolve(fresh.token, now=issued).persona_id == "asmith7734"
    with pytest.raises(InvalidTokenError):
        sessions.resolve(old.token, now=issued)


# ── role, as a dependency rather than per-handler code ──────────────────────


def test_require_role_admits_and_refuses():
    sessions = InMemorySessionStore()
    admin = sessions.issue("asmith7734")
    user = sessions.issue("jdoe4821")
    assert require_role(admin, "admin") is admin
    assert require_role(user, "user", "steward") is user
    with pytest.raises(Forbidden):
        require_role(user, "admin")


# ── the structural guard ────────────────────────────────────────────────────

#: Routes that are public BY DESIGN. Anything else must declare a user.
#: /queries and /specs list the query CATALOGUE — descriptions and parameter
#: shapes, never graph data. Both were public before this item; the guard's
#: value is that they are now public by decision rather than by nobody
#: noticing, and re-gating them would be a different item's call.
PUBLIC_ROUTES = {"/health", "/queries", "/specs", "/login", "/demo"}

#: The registration route is gated by an agent key, not a browser session; it
#: takes the owner's token in its BODY, which is the thing being validated.
AGENT_KEY_ROUTES = {"/specs/ephemeral"}


def _route_functions() -> list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    """Every function in app.py carrying an @app.<method>("<path>") decorator."""
    tree = ast.parse((REPO_ROOT / "drydocs_api" / "app.py").read_text(encoding="utf-8"))
    found: list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            target = decorator.func.value
            if not isinstance(target, ast.Name) or target.id != "app":
                continue
            if decorator.args and isinstance(decorator.args[0], ast.Constant):
                found.append((str(decorator.args[0].value), node))
    return found


def _annotation_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    names = set()
    for arg in [*node.args.args, *node.args.kwonlyargs]:
        if isinstance(arg.annotation, ast.Name):
            names.add(arg.annotation.id)
    return names


def test_every_route_is_discovered():
    """A guard that silently matches nothing is worse than no guard."""
    paths = {path for path, _ in _route_functions()}
    assert len(paths) > 25
    assert PUBLIC_ROUTES <= paths


def test_authentication_is_declared_in_the_route_signature():
    """The O69 shape: an authenticated route names CurrentUser or AdminUser.

    A route that forgets the parameter does not become an unguarded
    authenticated route — it becomes an obviously public one, which is a
    difference a reviewer can see and this test can measure.
    """
    unguarded = [
        path
        for path, fn in _route_functions()
        if path not in PUBLIC_ROUTES
        and path not in AGENT_KEY_ROUTES
        and not _annotation_names(fn) & {"CurrentUser", "AdminUser"}
    ]
    assert unguarded == [], f"routes with no declared user: {unguarded}"


def test_no_route_still_takes_a_raw_authorization_header():
    """The old shape: a header parameter the handler had to remember to check.
    Only the dependency itself may read it now."""
    offenders = [
        path
        for path, fn in _route_functions()
        if any(arg.arg == "authorization" for arg in fn.args.args)
    ]
    assert offenders == [], f"routes still reading the header directly: {offenders}"


def test_the_api_package_cannot_write_a_credential(monkeypatch: pytest.MonkeyPatch):
    """The store the API loads has no way to persist itself.

    ADR 0009 rule 5 bans filesystem writes in drydocs_api, and that ban lands on
    credentials for a reason of its own: an endpoint that can rewrite the
    credential file is an endpoint that can grant itself an account. Writing
    lives in scripts/set_console_credential.py, run by a person.
    """
    creds = _store("jdoe4821")
    assert not hasattr(creds, "save")
    payload = creds.as_payload()  # serializes, writes nothing
    assert payload["version"] == 1 and "jdoe4821" in payload["credentials"]


def test_the_admin_only_route_declares_admin():
    by_path = dict(_route_functions())
    assert "AdminUser" in _annotation_names(by_path["/raw-cypher"])
