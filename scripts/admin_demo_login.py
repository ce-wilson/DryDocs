"""Get the console signed-in-able for a demo, and prove it end to end.

    poetry run python scripts/admin_demo_login.py                 # status
    poetry run python scripts/admin_demo_login.py --ensure        # set what is missing
    poetry run python scripts/admin_demo_login.py --ensure admin  # just that account
    poetry run python scripts/admin_demo_login.py --rotate admin
    poetry run python scripts/admin_demo_login.py --check-login admin

THIS SCRIPT IS DELIBERATELY DISPOSABLE. It exists because the producer repo is a
proof of concept whose console gets demonstrated, and a demo needs one command
that answers "is this thing signed-in-able right now" without reading three
files to find out. It is the operator's to maintain until SSO arrives, and it is
written to be DELETED at that point rather than adapted: ADR 0005 already put
role resolution on the server, so a company binding its own OIDC replaces the
credential half underneath and keeps every route, role and guard above it. The
day `/login` becomes a code-for-token exchange, this file has no job left.

WHAT IT WILL NOT DO. It never takes a secret as an argument -- argv lands in
shell history, the process table, and anyone's screen share. `--ensure` and
`--rotate` prompt with no echo, the same way `set_console_credential.py` does,
because they call it. `--generate` is the one exception and it says so at the
prompt: it invents a strong secret and prints it ONCE, which is the right
trade for a synthetic account on localhost and the wrong one for anything else.

WHAT `--check-login` IS FOR. During a demo, "the console will not let me in"
has three unrelated causes: no credential set, the API not running, or a browser
problem. This performs the real HTTP login the browser performs and reports
which of the three it is, so the next thirty seconds are spent on the right one.
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from set_console_credential import save_store  # noqa: E402 — sibling script

from drydocs_api.credentials import (  # noqa: E402 — after the sys.path fix above
    CredentialError,
    CredentialStore,
    credentials_path,
)
from drydocs_api.personas import PERSONAS  # noqa: E402

#: Short names, so a demo does not need the synthetic ids memorised. The ids
#: themselves stay accepted, and `--ensure` with no argument covers all of them.
ALIASES: dict[str, str] = {
    "admin": "asmith7734",
    "steward": "kchen2190",
    "user": "jdoe4821",
    "sme": "sme",
}

DEFAULT_API = "http://localhost:8001"

#: Long enough that the generated form is not the weak link, short enough to
#: read off a terminal and type into a browser once.
GENERATED_SECRET_BYTES = 12


def _resolve(name: str) -> str:
    identity = ALIASES.get(name, name)
    if identity not in PERSONAS:
        known = ", ".join(sorted(ALIASES) + sorted(PERSONAS))
        raise SystemExit(f"unknown account {name!r} (try one of: {known})")
    return identity


def _load(target: Path) -> CredentialStore:
    try:
        return CredentialStore.load(target)
    except CredentialError as exc:
        raise SystemExit(f"error: {exc}") from None


def _set_secret(identity: str, target: Path, *, generate: bool) -> None:
    """Delegate to the one place that owns writing, so there is one writer."""
    if generate:
        secret = secrets.token_urlsafe(GENERATED_SECRET_BYTES)
        store = _load(target)
        store.set(identity, secret)
        save_store(store, target)
        print(f"  {identity}: generated secret -> {secret}")
        print("  (shown once; it is not recoverable from the stored hash)")
        return
    # Reuse the operator script wholesale rather than re-implementing its
    # prompt, its confirmation and its minimum length.
    import set_console_credential

    rc = set_console_credential.main([identity, "--path", str(target)])
    if rc != 0:
        raise SystemExit(rc)


def _api_login(api: str, identity: str, secret: str) -> tuple[int, str]:
    # A localhost URL the operator passed on the command line, by design.
    request = urllib.request.Request(
        f"{api}/login",
        data=json.dumps({"persona_id": identity, "secret": secret}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        return 0, str(exc.reason)


def _status(target: Path, api: str) -> int:
    store = _load(target)
    ready = set(store.identities())
    print(f"credential file: {target}")
    if not ready:
        print("  NO ACCOUNT CAN SIGN IN - run with --ensure")
    for alias, identity in sorted(ALIASES.items()):
        mark = "ready" if identity in ready else "no secret set"
        print(f"  {alias:<8} {identity:<12} {PERSONAS[identity].role:<8} {mark}")
    orphans = sorted(ready - set(PERSONAS))
    for identity in orphans:
        print(f"  {'?':<8} {identity:<12} {'-':<8} has a secret but is not a known persona")

    status, _ = _api_login(api, "", "")
    if status == 0:
        print(f"api at {api}: NOT RUNNING")
        print("  start it: poetry run uvicorn drydocs_api.app:create_app --factory --port 8001")
    else:
        print(f"api at {api}: running (it answered the login probe with {status})")
        print("  credentials re-read on change (O73) - no restart needed after --ensure")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Demo sign-in helper for the DryDocs console. Delete this when SSO lands."
    )
    parser.add_argument(
        "--ensure",
        nargs="?",
        const="__all__",
        metavar="ACCOUNT",
        help="set a secret for any demo account that has none (or just the one named)",
    )
    parser.add_argument("--rotate", metavar="ACCOUNT", help="replace an account's secret")
    parser.add_argument(
        "--check-login",
        metavar="ACCOUNT",
        help="prove a real login against the running API and say which layer failed",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="invent the secret instead of prompting, and PRINT IT ONCE (localhost demo only)",
    )
    parser.add_argument("--api", default=DEFAULT_API, help=f"API base URL (default {DEFAULT_API})")
    parser.add_argument("--path", type=Path, default=None, help="override the credential file")
    args = parser.parse_args(argv)

    target = args.path if args.path is not None else credentials_path()

    if args.rotate:
        identity = _resolve(args.rotate)
        print(f"rotating {identity}")
        _set_secret(identity, target, generate=args.generate)
        return 0

    if args.ensure:
        wanted = (
            sorted(set(ALIASES.values())) if args.ensure == "__all__" else [_resolve(args.ensure)]
        )
        have = set(_load(target).identities())
        missing = [i for i in wanted if i not in have]
        if not missing:
            print("every requested account already has a secret; nothing to do")
        for identity in missing:
            print(f"setting a secret for {identity} ({PERSONAS[identity].role})")
            _set_secret(identity, target, generate=args.generate)
        return _status(target, args.api)

    if args.check_login:
        identity = _resolve(args.check_login)
        if identity not in _load(target).identities():
            print(
                f"{identity}: NO SECRET SET - that is the failure. Run --ensure {args.check_login}"
            )
            return 1
        import getpass

        secret = getpass.getpass(f"Secret for {identity} (to prove the login): ")
        status, body = _api_login(args.api, identity, secret)
        if status == 0:
            print(f"api at {args.api}: NOT RUNNING ({body}) - that is the failure, not the secret")
            return 1
        if status == 200:
            payload = json.loads(body)
            print(f"OK - {identity} signed in as role {payload['role']}")
            print(f"  session expires {payload['expires_at']}")
            print(f"  token {payload['token']}")
            print("  (use it as: Authorization: Bearer <token>)")
            return 0
        print(f"REFUSED ({status}): {body}")
        print("  the API is up and the account exists, so this is the secret itself")
        return 1

    return _status(target, args.api)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
