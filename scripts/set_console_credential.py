"""Bootstrap or rotate a web-console credential on THIS machine.

    poetry run python scripts/set_console_credential.py morpheus
    poetry run python scripts/set_console_credential.py --list
    poetry run python scripts/set_console_credential.py --remove morpheus

The secret is read from a no-echo prompt and confirmed, never taken from argv —
an argument would land in shell history, in the process table, and in whatever
scrollback a screen share is showing. It is hashed with scrypt and written to
the machine-local file described in ``drydocs_api.credentials``: gitignored,
never ported, never rendered, and with no committed source to rebuild it from.

THE WRITE LIVES HERE, NOT IN THE API, and that placement is enforced rather
than chosen. ``tests/unit/test_mapping_api.py`` forbids every filesystem write
primitive inside ``drydocs_api`` (ADR 0009 rule 5: propose in the DB, land in
git). The rule was written about configuration, and it lands correctly on
credentials for a reason of its own: an endpoint that can rewrite the
credential file is an endpoint that can grant itself an account. The API loads
and verifies; this script, run by a person at a terminal, is the only writer.

A fresh clone has no such file and therefore no accounts, so every console login
is refused until this runs. That is the intended state — a proof of concept
should not ship working credentials — and the API's 401 names this script.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from drydocs_api.credentials import (  # noqa: E402 — after the sys.path fix above
    GENERATED_SECRET_STALE_DAYS,
    ORIGIN_PROMPTED,
    ORIGIN_UNKNOWN,
    Credential,
    CredentialError,
    CredentialStore,
    credentials_path,
)
from drydocs_api.personas import PERSONAS  # noqa: E402

#: Short enough to type at a local console, long enough that the scrypt cost is
#: not the only thing standing between a guess and a session.
MIN_SECRET_LENGTH = 12

#: Pinned so the file does not churn its line endings between machines.
NEWLINE = chr(10)


def describe(credential: Credential) -> str:
    """One column of provenance for a listing (O76).

    Lives here rather than in ``drydocs_api`` because it is presentation, and it
    is IMPORTED by ``admin_demo_login.py`` rather than reimplemented there --
    two surfaces that disagree about what "stale" means would be worse than one
    surface that never said it.
    """
    age = credential.age_days
    when = "age unknown" if age is None else ("today" if age == 0 else f"{age}d ago")
    if credential.origin == ORIGIN_UNKNOWN:
        # Predates version 2. Not guessed at, and not flagged: nothing is known
        # about when it was set, so there is nothing to judge it against.
        return "set before provenance was recorded"
    line = f"{credential.origin}, {when}"
    if credential.wants_rotation:
        line += f"  ROTATE - printed to a terminal, {GENERATED_SECRET_STALE_DAYS}d+ old"
    return line


def save_store(store: CredentialStore, target: Path) -> Path:
    """Write the store atomically, owner-readable only where the platform allows.

    ATOMIC ON PURPOSE (O73). The API re-reads this file when it changes, so a
    truncate-then-write would give a login landing in the gap a half-written
    JSON file. Writing a sibling temp file and calling os.replace makes the
    swap a single rename: a reader sees either the whole old file or the whole
    new one, never a torn one. os.replace is atomic on both platforms this repo
    runs on, and the temp file is a sibling so the rename never crosses a
    filesystem boundary.

    The permission bits are set on the temp file BEFORE the rename, so the
    credential file is never briefly world-readable under its final name.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    # newline pinned: the render-determinism guard bans an unpinned write_text
    # anywhere in the tree, and a credential file that churns its line endings
    # between machines would be a diff nobody can read.
    tmp.write_text(
        json.dumps(store.as_payload(), indent=2) + NEWLINE,
        encoding="utf-8",
        newline=NEWLINE,
    )
    try:
        tmp.chmod(0o600)
    except OSError:  # pragma: no cover - Windows ACLs; best effort only
        pass
    os.replace(tmp, target)
    return target


def _prompt_secret(identity: str) -> str:
    first = getpass.getpass(f"New console secret for {identity}: ")
    if len(first) < MIN_SECRET_LENGTH:
        raise SystemExit(f"refused: secret must be at least {MIN_SECRET_LENGTH} characters")
    second = getpass.getpass("Confirm: ")
    if first != second:
        raise SystemExit("refused: the two entries did not match")
    return first


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Set, list or remove a machine-local console credential."
    )
    parser.add_argument(
        "identity",
        nargs="?",
        help="persona id to set a secret for (see --list for the known personas)",
    )
    parser.add_argument("--list", action="store_true", help="show which ids have a credential")
    parser.add_argument("--remove", metavar="ID", help="delete an id's credential")
    parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help="override the credential file location (default: internal-local/)",
    )
    parser.add_argument(
        "--allow-unknown-persona",
        action="store_true",
        help="set a secret for an id the persona table does not define",
    )
    args = parser.parse_args(argv)

    target = args.path if args.path is not None else credentials_path()
    try:
        store = CredentialStore.load(target)
    except CredentialError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.list:
        print(f"credential file: {target}")
        if not store.is_bootstrapped:
            print("  (none - no account can sign in to the console on this machine)")
        for identity in store.identities():
            known = "" if identity in PERSONAS else "  [not a known persona]"
            credential = store.get(identity)
            provenance = describe(credential) if credential is not None else ""
            print(f"  {identity:<12} {provenance}{known}")
        for identity in sorted(PERSONAS):
            if identity not in store.identities():
                print(f"  {identity:<12} [no secret set]")
        if any((c := store.get(i)) is not None and c.wants_rotation for i in store.identities()):
            print()
            print("  A generated secret was printed to a terminal once and is still in use.")
            print("  Rotate it: poetry run python scripts/set_console_credential.py <id>")
        return 0

    if args.remove:
        if args.remove not in store.identities():
            print(f"error: no credential stored for {args.remove!r}", file=sys.stderr)
            return 1
        store.remove(args.remove)
        save_store(store, target)
        print(f"removed {args.remove}; {len(store)} credential(s) remain in {target}")
        return 0

    if not args.identity:
        parser.print_help()
        return 2

    if args.identity not in PERSONAS and not args.allow_unknown_persona:
        known = ", ".join(sorted(PERSONAS))
        print(
            f"error: {args.identity!r} is not a known persona (known: {known}).\n"
            "A credential for an id the server cannot resolve to a role would pass the "
            "secret check and then fail to issue a session, which reads as a broken login "
            "rather than a misconfiguration. Pass --allow-unknown-persona to override.",
            file=sys.stderr,
        )
        return 1

    rotating = args.identity in store.identities()
    # Prompted by construction: _prompt_secret is a no-echo getpass, so this
    # secret has never been rendered anywhere a screen share could catch it.
    store.set(args.identity, _prompt_secret(args.identity), origin=ORIGIN_PROMPTED)
    save_store(store, target)
    verb = "rotated" if rotating else "set"
    print(f"{verb} the console secret for {args.identity}")
    print(f"stored in {target} - machine-local, gitignored, never committed or ported")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
