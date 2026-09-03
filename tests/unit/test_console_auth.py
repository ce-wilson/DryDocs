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
    FORMAT_VERSION,
    GENERATED_SECRET_STALE_DAYS,
    ORIGIN_GENERATED,
    ORIGIN_PROMPTED,
    ORIGIN_UNKNOWN,
    PATH_ENV_VAR,
    READABLE_VERSIONS,
    Credential,
    CredentialChecker,
    CredentialError,
    CredentialStore,
    ReloadingCredentialStore,
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
from drydocs_api.personas import PERSONAS
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
    creds = _store("mouse")
    target = save_store(creds, tmp_path / "console-credentials.json")
    text = target.read_text(encoding="utf-8")
    assert SECRET not in text
    payload = json.loads(text)
    assert payload["credentials"]["mouse"]["algorithm"] == ALGORITHM


def test_empty_store_refuses_everything():
    creds = CredentialStore()
    assert creds.is_bootstrapped is False
    assert creds.verify("mouse", SECRET) is False


def test_unknown_identity_returns_false_rather_than_raising():
    """An exception would be an enumeration oracle: the caller could tell a
    real id from an invented one by which failure it got."""
    creds = _store("mouse")
    assert creds.verify("nobody-at-all", SECRET) is False


def test_round_trip_through_the_file(tmp_path: Path):
    target = save_store(_store("mouse", "morpheus"), tmp_path / "creds.json")
    reloaded = CredentialStore.load(target)
    assert reloaded.identities() == ("morpheus", "mouse")
    assert reloaded.verify("mouse", SECRET) is True
    assert reloaded.verify("morpheus", "wrong") is False


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
        encoding="utf-8",
    )
    assert tracked.stdout.strip() == ""


# ── login ───────────────────────────────────────────────────────────────────


def test_login_issues_a_session_with_an_expiry():
    sessions = InMemorySessionStore()
    out = login("morpheus", SECRET, sessions, _store("morpheus"))
    assert out["persona_id"] == "morpheus"
    assert out["role"] == "admin"  # resolved server-side, never sent by the client
    assert datetime.fromisoformat(out["expires_at"]) > datetime.now(UTC)
    assert authenticate(out["token"], sessions).role == "admin"


def test_login_refuses_a_wrong_secret():
    sessions = InMemorySessionStore()
    with pytest.raises(BadCredentialsError):
        login("morpheus", "not-the-secret", sessions, _store("morpheus"))


def test_login_refuses_an_empty_secret():
    """Empty must never short-circuit into a truthy comparison, and must not
    reach the KDF as a legitimate input."""
    sessions = InMemorySessionStore()
    with pytest.raises(BadCredentialsError):
        login("morpheus", "", sessions, _store("morpheus"))


def test_unknown_identity_and_wrong_secret_are_indistinguishable():
    """Same exception type, same message — which of the two it was is exactly
    what turns a login route into an account enumerator."""
    sessions = InMemorySessionStore()
    creds = _store("morpheus")
    with pytest.raises(BadCredentialsError) as unknown:
        login("no-such-person", SECRET, sessions, creds)
    with pytest.raises(BadCredentialsError) as wrong:
        login("morpheus", "nope", sessions, creds)
    assert str(unknown.value) == str(wrong.value)


def test_fresh_clone_says_what_to_run():
    sessions = InMemorySessionStore()
    with pytest.raises(CredentialsNotConfiguredError) as exc:
        login("morpheus", SECRET, sessions, CredentialStore())
    assert "set_console_credential.py" in str(exc.value)


def test_a_failed_login_issues_no_session():
    sessions = InMemorySessionStore()
    with pytest.raises(BadCredentialsError):
        login("morpheus", "wrong", sessions, _store("morpheus"))
    assert sessions.purge_expired() == 0
    assert len(sessions._sessions) == 0  # the assertion IS the internal state


# ── expiry ──────────────────────────────────────────────────────────────────


def test_expired_token_is_rejected():
    sessions = InMemorySessionStore(ttl=timedelta(minutes=30))
    issued = datetime.now(UTC)
    session = sessions.issue("mouse", now=issued)
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
    session = sessions.issue("mouse", now=issued)
    with pytest.raises(ExpiredTokenError):
        sessions.resolve(session.token, now=issued + timedelta(seconds=2))
    with pytest.raises(InvalidTokenError):  # gone, not merely expired
        sessions.resolve(session.token, now=issued)


def test_purge_expired_clears_only_the_stale_ones():
    sessions = InMemorySessionStore(ttl=timedelta(minutes=10))
    issued = datetime.now(UTC)
    old = sessions.issue("mouse", now=issued - timedelta(hours=1))
    fresh = sessions.issue("morpheus", now=issued)
    assert sessions.purge_expired(now=issued) == 1
    assert sessions.resolve(fresh.token, now=issued).persona_id == "morpheus"
    with pytest.raises(InvalidTokenError):
        sessions.resolve(old.token, now=issued)


# ── role, as a dependency rather than per-handler code ──────────────────────


def test_require_role_admits_and_refuses():
    sessions = InMemorySessionStore()
    admin = sessions.issue("morpheus")
    user = sessions.issue("mouse")
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
    creds = _store("mouse")
    assert not hasattr(creds, "save")
    payload = creds.as_payload()  # serializes, writes nothing
    assert payload["version"] == FORMAT_VERSION and "mouse" in payload["credentials"]


def test_the_admin_only_route_declares_admin():
    by_path = dict(_route_functions())
    assert "AdminUser" in _annotation_names(by_path["/raw-cypher"])


# ── O73: the store re-reads when its file changes ───────────────────────────


def test_reloading_store_sees_a_credential_added_after_it_started(tmp_path: Path):
    """The whole point: no restart between setting a secret and using it."""
    target = tmp_path / "creds.json"
    store = ReloadingCredentialStore(target)
    assert store.is_bootstrapped is False

    save_store(_store("mouse"), target)
    assert store.is_bootstrapped is True
    assert store.verify("mouse", SECRET) is True


def test_reloading_store_sees_a_rotation(tmp_path: Path):
    target = tmp_path / "creds.json"
    save_store(_store("mouse"), target)
    store = ReloadingCredentialStore(target)
    assert store.verify("mouse", SECRET) is True

    rotated = CredentialStore()
    rotated.set("mouse", "a-different-secret")
    save_store(rotated, target)

    assert store.verify("mouse", SECRET) is False
    assert store.verify("mouse", "a-different-secret") is True


def test_reloading_store_honours_deletion(tmp_path: Path):
    """An ABSENT file is unambiguous: somebody removed the accounts."""
    target = tmp_path / "creds.json"
    save_store(_store("mouse"), target)
    store = ReloadingCredentialStore(target)
    assert store.is_bootstrapped is True

    target.unlink()
    assert store.is_bootstrapped is False
    assert store.verify("mouse", SECRET) is False


def test_a_corrupt_file_keeps_the_last_good_store(tmp_path: Path):
    """An UNREADABLE file is ambiguous - it may be a write in progress - so the
    previous credentials stand. Failing closed here would turn a routine
    rotation into a lockout: a denial of service caused by the safety
    behaviour rather than by the fault."""
    target = tmp_path / "creds.json"
    save_store(_store("mouse"), target)
    store = ReloadingCredentialStore(target)
    assert store.verify("mouse", SECRET) is True

    target.write_text('{"version":1,"credentials":{"jdoe', encoding="utf-8")
    assert store.verify("mouse", SECRET) is True  # last good stands

    save_store(_store("mouse", "morpheus"), target)
    assert store.verify("morpheus", SECRET) is True  # and it recovers


def test_a_corrupt_file_is_retried_rather_than_treated_as_settled(tmp_path: Path):
    """The bad file's stat must NOT be recorded as the loaded state, or a file
    that is repaired to the same size within one timestamp tick would be
    ignored forever."""
    target = tmp_path / "creds.json"
    save_store(_store("mouse"), target)
    store = ReloadingCredentialStore(target)
    target.write_text("not json at all", encoding="utf-8")
    store.is_bootstrapped  # noqa: B018 — the refresh is the point
    assert store._stamp is not None  # still the last GOOD file's stamp
    assert store._stamp != (target.stat().st_mtime_ns, target.stat().st_size)


def test_an_unchanged_file_is_not_re_parsed(tmp_path: Path):
    """A stat per login is the budget; re-deriving the store every request is
    not. Counted rather than asserted in prose."""
    target = tmp_path / "creds.json"
    save_store(_store("mouse"), target)
    store = ReloadingCredentialStore(target)

    calls = 0
    original = CredentialStore.load

    def counting_load(path=None):
        nonlocal calls
        calls += 1
        return original(path)

    CredentialStore.load = staticmethod(counting_load)  # type: ignore[method-assign]
    try:
        for _ in range(5):
            store.verify("mouse", SECRET)
    finally:
        CredentialStore.load = original  # type: ignore[method-assign]
    assert calls == 0


def test_both_stores_satisfy_what_login_needs(tmp_path: Path):
    """The protocol is what lets the API hold a reloading store while every
    test injects a plain one."""
    plain: CredentialChecker = _store("mouse")
    reloading: CredentialChecker = ReloadingCredentialStore(tmp_path / "creds.json")
    for checker in (plain, reloading):
        assert isinstance(checker.is_bootstrapped, bool)
        assert checker.verify("nobody", "x") is False


# ── O73: the write is atomic ────────────────────────────────────────────────


def test_save_leaves_no_temp_file_behind(tmp_path: Path):
    target = tmp_path / "creds.json"
    save_store(_store("mouse"), target)
    assert target.exists()
    assert list(tmp_path.iterdir()) == [target]


def test_save_replaces_rather_than_truncating(tmp_path: Path):
    """A truncate-then-write gives a concurrent reader a half-file. The proof
    a reader can rely on: the old content is complete right up until the new
    content is complete - there is no moment where the path holds neither."""
    target = tmp_path / "creds.json"
    save_store(_store("mouse"), target)
    before = target.read_text(encoding="utf-8")
    assert json.loads(before)["credentials"].keys() == {"mouse"}

    save_store(_store("mouse", "morpheus"), target)
    after = target.read_text(encoding="utf-8")
    assert json.loads(after)["credentials"].keys() == {"morpheus", "mouse"}
    assert before != after


def test_the_writer_uses_a_sibling_temp_path(tmp_path: Path):
    """os.replace is only atomic within one filesystem, so the temp file must
    be a sibling of the target rather than somewhere in the system temp dir."""
    source = (REPO_ROOT / "scripts" / "set_console_credential.py").read_text(encoding="utf-8")
    assert "target.with_name(" in source
    assert "os.replace(" in source
    assert "tempfile" not in source


# ── the demo script's alias table ───────────────────────────────────────────


def test_every_alias_points_at_a_real_persona():
    """The failure this guards was a live one: the alias table was edited with
    names that were not persona ids, and it surfaced as a KeyError from inside
    a format string rather than as a message saying what was wrong."""
    import admin_demo_login

    unknown = sorted(v for v in admin_demo_login.ALIASES.values() if v not in PERSONAS)
    assert unknown == [], f"aliases point at ids the server does not know: {unknown}"


def test_alias_roles_are_what_the_names_claim():
    """An alias called 'admin' that resolves to a user-tier account would send
    a demo down the wrong path silently."""
    import admin_demo_login

    expected = {"admin": "admin", "steward": "steward", "user": "user", "sme": "user"}
    for alias, role in expected.items():
        identity = admin_demo_login.ALIASES[alias]
        assert PERSONAS[identity].role == role, f"alias {alias!r} -> {identity!r} is not {role}"


def test_the_roster_keeps_one_account_per_gated_tier_plus_spare_seats():
    """Every role a route gates on needs at least one account, or that surface
    becomes untestable; and per-persona isolation needs two accounts alike in
    everything but identity."""
    by_role: dict[str, list[str]] = {}
    for identity, p in PERSONAS.items():
        by_role.setdefault(p.role, []).append(identity)
    assert set(by_role) == {"admin", "steward", "user"}
    assert len(by_role["admin"]) >= 1 and len(by_role["steward"]) >= 1
    assert len(by_role["user"]) >= 2, "per-persona isolation cannot be tested with one user"


# ── O75: withdrawing an account withdraws its access ────────────────────────


def test_withdrawn_account_token_is_refused_on_the_next_request():
    """The defect in one test. Before O75 this session kept resolving, at its
    full role, until its eight-hour term ran out."""
    creds = _store("morpheus")
    sessions = InMemorySessionStore()
    token = login("morpheus", SECRET, sessions, creds)["token"]

    # Still good while the account exists.
    assert authenticate(token, sessions, creds).persona_id == "morpheus"

    creds.remove("morpheus")

    with pytest.raises(InvalidTokenError):
        authenticate(token, sessions, creds)


def test_a_refused_session_is_dropped_not_merely_refused():
    """A withdrawn account must not leave a resolvable-looking entry sitting in
    the store until purge_expired happens to run."""
    creds = _store("morpheus")
    sessions = InMemorySessionStore()
    token = login("morpheus", SECRET, sessions, creds)["token"]
    creds.remove("morpheus")

    with pytest.raises(InvalidTokenError):
        authenticate(token, sessions, creds)

    # Gone from the store itself: the session-only path no longer knows it.
    with pytest.raises(InvalidTokenError):
        sessions.resolve(token)


def test_withdrawing_one_account_leaves_the_others_signed_in():
    """Withdrawal is per identity. A blast radius of 'everyone' would be its own
    defect, and it is exactly what a naive store.clear() would produce."""
    creds = _store("morpheus", "mouse")
    sessions = InMemorySessionStore()
    admin = login("morpheus", SECRET, sessions, creds)["token"]
    user = login("mouse", SECRET, sessions, creds)["token"]

    creds.remove("morpheus")

    with pytest.raises(InvalidTokenError):
        authenticate(admin, sessions, creds)
    assert authenticate(user, sessions, creds).persona_id == "mouse"


def test_authenticate_without_a_credential_store_is_unchanged():
    """The offline layer stays offline: handlers.py is provable with no FastAPI
    and no credential store, and its own second authenticate call passes
    neither. Omitting the argument must not change what it did before."""
    creds = _store("morpheus")
    sessions = InMemorySessionStore()
    token = login("morpheus", SECRET, sessions, creds)["token"]
    creds.remove("morpheus")

    # No credential store supplied -> the O69 behaviour, verbatim.
    assert authenticate(token, sessions).persona_id == "morpheus"


def test_rotation_is_not_caught_and_the_test_says_so():
    """Clause (f), pinned as a test so the limit is documented where it will be
    read. A rotated secret leaves the identity present, so an identity check
    cannot see it. Catching rotation needs a per-identity generation stamp the
    credential file does not carry. If this test ever starts failing, the
    capability grew and the docstring on authenticate() is stale."""
    creds = _store("morpheus")
    sessions = InMemorySessionStore()
    token = login("morpheus", SECRET, sessions, creds)["token"]

    creds.set("morpheus", "a-completely-different-secret")

    assert authenticate(token, sessions, creds).persona_id == "morpheus"


def test_revoke_identity_drops_every_session_that_persona_holds():
    """The explicit lever. Not what makes withdrawal work -- authenticate does
    that with no coordination -- but a caller that already knows an account is
    gone should not wait for each token to be presented.

    No credential store here on purpose: this lever is the session store's own,
    and it never learns WHY an identity is finished."""
    sessions = InMemorySessionStore()
    first = sessions.issue("morpheus").token
    second = sessions.issue("morpheus").token
    other = sessions.issue("mouse").token

    assert sessions.revoke_identity("morpheus") == 2
    assert sessions.revoke_identity("morpheus") == 0  # idempotent

    for token in (first, second):
        with pytest.raises(InvalidTokenError):
            sessions.resolve(token)
    assert sessions.resolve(other).persona_id == "mouse"


def test_a_corrupt_credential_file_does_not_sign_anybody_out(tmp_path):
    """Clause (d), the half that must NOT fail closed. O73 ruled an unreadable
    file ambiguous and kept the last known-good store, because failing closed
    there turns a routine rotation into a lockout. The new check inherits that
    ruling and adds no failure mode of its own."""
    target = save_store(_store("morpheus"), tmp_path / "creds.json")
    creds = ReloadingCredentialStore(target)
    sessions = InMemorySessionStore()
    token = login("morpheus", SECRET, sessions, creds)["token"]

    target.write_text("{ not json at all", encoding="utf-8", newline=chr(10))

    assert authenticate(token, sessions, creds).persona_id == "morpheus"


def test_deleting_the_credential_file_signs_everybody_out(tmp_path):
    """Clause (d), the half that MUST fail closed. An absent file is not
    ambiguous: somebody removed the accounts."""
    target = save_store(_store("morpheus", "mouse"), tmp_path / "creds.json")
    creds = ReloadingCredentialStore(target)
    sessions = InMemorySessionStore()
    admin = login("morpheus", SECRET, sessions, creds)["token"]
    user = login("mouse", SECRET, sessions, creds)["token"]

    target.unlink()

    for token in (admin, user):
        with pytest.raises(InvalidTokenError):
            authenticate(token, sessions, creds)


def test_has_identity_answers_without_enumerating():
    """It is narrower than identities() on purpose: a yes/no about an id the
    caller already holds, which is why the auth path may call it at all."""
    creds = _store("morpheus")
    assert creds.has_identity("morpheus") is True
    assert creds.has_identity("mouse") is False
    assert creds.has_identity("") is False


def test_the_checker_protocol_covers_both_implementations(tmp_path):
    """Adding a protocol member must stay a two-implementation change, or the
    API could hold a store no test can substitute."""
    target = save_store(_store("morpheus"), tmp_path / "creds.json")
    for store in (_store("morpheus"), ReloadingCredentialStore(target)):
        checker: CredentialChecker = store
        assert checker.is_bootstrapped is True
        assert checker.verify("morpheus", SECRET) is True
        assert checker.has_identity("morpheus") is True


# ── O76: how each secret was set, and the migration that must not lock anyone out ──


def test_a_version_one_file_still_loads_and_is_not_guessed_at():
    """Clause (b) and (c) together, and the reason the item exists at all.

    The real file on a working machine is version 1 carrying every account. If
    the version bump refused it, the operator would be signed out of their own
    console and told to re-bootstrap -- six working credentials destroyed to
    gain a metadata field.
    """
    legacy = {
        "version": 1,
        "credentials": {"morpheus": hash_secret(SECRET).as_dict()},
    }
    # Strip the v2 keys, so this is genuinely a v1 entry rather than a v2 one
    # wearing a v1 version number.
    for key in ("origin", "set_at"):
        legacy["credentials"]["morpheus"].pop(key, None)

    store = CredentialStore({"morpheus": Credential.from_dict(legacy["credentials"]["morpheus"])})
    assert store.verify("morpheus", SECRET) is True

    credential = store.get("morpheus")
    assert credential.origin == ORIGIN_UNKNOWN, "a migrated entry must not claim to be prompted"
    assert credential.set_at is None
    assert credential.age_days is None
    assert credential.wants_rotation is False, "nothing is known about it, so nothing is claimed"


def test_a_version_one_file_round_trips_through_load(tmp_path):
    """The same thing through the real reader, since `load` is what refuses."""
    target = tmp_path / "v1.json"
    entry = hash_secret(SECRET).as_dict()
    for key in ("origin", "set_at"):
        entry.pop(key, None)
    target.write_text(
        json.dumps({"version": 1, "credentials": {"morpheus": entry}}),
        encoding="utf-8",
        newline=chr(10),
    )
    store = CredentialStore.load(target)
    assert store.verify("morpheus", SECRET) is True
    assert store.get("morpheus").origin == ORIGIN_UNKNOWN
    # And it upgrades on the next WRITE, never on the read above.
    assert store.as_payload()["version"] == FORMAT_VERSION


def test_a_version_the_build_does_not_know_is_still_refused(tmp_path):
    """Reading an older KNOWN version is not permission to read any version."""
    target = tmp_path / "future.json"
    target.write_text(
        json.dumps({"version": max(READABLE_VERSIONS) + 1, "credentials": {}}),
        encoding="utf-8",
        newline=chr(10),
    )
    with pytest.raises(CredentialError, match="format version"):
        CredentialStore.load(target)


def test_provenance_round_trips(tmp_path):
    creds = CredentialStore()
    creds.set("morpheus", SECRET, origin=ORIGIN_GENERATED)
    creds.set("mouse", SECRET, origin=ORIGIN_PROMPTED)
    target = save_store(creds, tmp_path / "creds.json")

    reloaded = CredentialStore.load(target)
    assert reloaded.get("morpheus").origin == ORIGIN_GENERATED
    assert reloaded.get("mouse").origin == ORIGIN_PROMPTED
    assert reloaded.get("morpheus").set_at is not None
    assert reloaded.verify("morpheus", SECRET) is True


def test_provenance_defaults_to_unknown_rather_than_the_common_case():
    """A caller that has not thought about origin records that it has not."""
    creds = CredentialStore()
    creds.set("morpheus", SECRET)
    assert creds.get("morpheus").origin == ORIGIN_UNKNOWN


def test_an_unrecognised_origin_reads_as_unknown_not_as_an_error():
    """Provenance is metadata. Being unable to interpret it is not a reason to
    refuse a credential that verifies."""
    entry = hash_secret(SECRET, origin=ORIGIN_PROMPTED).as_dict()
    entry["origin"] = "invented-by-a-future-build"
    assert Credential.from_dict(entry).origin == ORIGIN_UNKNOWN


def test_hash_secret_refuses_an_origin_it_does_not_know():
    with pytest.raises(ValueError, match="unknown credential origin"):
        hash_secret(SECRET, origin="nonsense")


def _aged(origin: str, days: int) -> Credential:
    stamp = datetime.now(UTC) - timedelta(days=days)
    return Credential(
        algorithm=ALGORITHM,
        salt="00",
        hash="00",
        n=2,
        r=8,
        p=1,
        origin=origin,
        set_at=stamp.isoformat(timespec="seconds"),
    )


def test_rotation_flag_fires_only_for_stale_generated_secrets():
    """Clause (f). A flag that fires on everything is a flag nobody reads."""
    threshold = GENERATED_SECRET_STALE_DAYS
    assert _aged(ORIGIN_GENERATED, threshold).wants_rotation is True
    assert _aged(ORIGIN_GENERATED, threshold + 40).wants_rotation is True
    # The boundary, from below.
    assert _aged(ORIGIN_GENERATED, threshold - 1).wants_rotation is False
    assert _aged(ORIGIN_GENERATED, 0).wants_rotation is False
    # A prompted secret was never printed anywhere, so age alone is not a reason.
    assert _aged(ORIGIN_PROMPTED, threshold + 400).wants_rotation is False
    # An unknown-origin entry has no age to judge.
    assert (
        Credential(
            algorithm=ALGORITHM, salt="00", hash="00", n=2, r=8, p=1, origin=ORIGIN_UNKNOWN
        ).wants_rotation
        is False
    )


def test_the_two_listings_share_one_definition_of_stale():
    """Two surfaces that disagreed about what 'stale' means would be worse than
    one surface that never said it, so admin_demo_login IMPORTS the helper."""
    import admin_demo_login
    import set_console_credential

    assert admin_demo_login.describe is set_console_credential.describe
    assert "ROTATE" in set_console_credential.describe(
        _aged(ORIGIN_GENERATED, GENERATED_SECRET_STALE_DAYS + 1)
    )
    assert "ROTATE" not in set_console_credential.describe(_aged(ORIGIN_PROMPTED, 900))
    unknown = Credential(
        algorithm=ALGORITHM, salt="00", hash="00", n=2, r=8, p=1, origin=ORIGIN_UNKNOWN
    )
    assert "provenance" in set_console_credential.describe(unknown)


def test_the_stored_payload_carries_no_secret_material():
    """Provenance is added to a file whose whole discipline is that the secret
    is not recoverable from it. Pin that the new fields did not change that."""
    creds = CredentialStore()
    creds.set("morpheus", SECRET, origin=ORIGIN_GENERATED)
    blob = json.dumps(creds.as_payload())
    assert SECRET not in blob
    entry = creds.as_payload()["credentials"]["morpheus"]
    assert set(entry) == {"algorithm", "salt", "hash", "n", "r", "p", "origin", "set_at"}
