"""Console credential store — the one piece of state that is neither the source
of truth nor derived from it.

WHY THIS MODULE EXISTS AT ALL, stated against ADR 0009. That ADR gives
configuration exactly two homes: committed git text, which is the source of
truth permanently, or a derived materialization of it, which is rebuildable and
deletable at any moment without data loss. A password hash fits neither. It
cannot be committed, because ``PUBLISH-BOUNDARY.md`` forbids secret material in
tracked files. It cannot live in ``var/mapping.db`` either, and the reason is
sharper than "secrets do not belong in a cache": everything in that file is
derived from committed YAML and CSV beside it, which is what makes deleting it
free. A credential has no committed source to rebuild from, so deleting it
destroys the only copy — it would quietly break the contract that makes ``var/``
safe to wipe.

So the hash lives in a THIRD place, named here rather than left implicit: a
machine-local file under ``internal-local/``, the directory this repo already
uses for material that is real, is never published, and is gitignored as a
whole. Deliberately NOT under ``var/``, whose whole point is that a session can
delete it and rebuild. Nothing renders from this file, no port carries it, and
no classification test sees it, because it is not repo content.

WHAT A FRESH CLONE GETS: no file, therefore no accounts, therefore every login
is refused. That is the correct default — a clone of a proof of concept should
not ship working credentials — and the refusal names the bootstrap command
rather than reading as a bug. See ``scripts/set_console_credential.py``.

HASHING is stdlib ``hashlib.scrypt`` (RFC 7914), a memory-hard KDF, with
``hmac.compare_digest`` for the comparison. Not the reviewed FastAPI template's
``pwdlib``/Argon2, and the reason is a property of this repo rather than a
preference: CI runs ``poetry install`` with no optional groups, so anything
reachable only through the ``api`` dependency group is untested there, and the
pure-handler layer these functions serve is deliberately dependency-free (the
offline unit suite imports ``drydocs_api.handlers`` without FastAPI installed).
A credential check that CI never runs is worse than a slightly older KDF that it
does. Argon2id remains the upgrade path: ``ALGORITHM`` and the stored parameter
block exist so a second scheme can be added without invalidating what is
already stored.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from drydocs_core.repo_paths import repo_root

logger = logging.getLogger(__name__)

#: Bumped when the stored shape changes. This is what we WRITE.
FORMAT_VERSION = 2

#: What we can READ. Version 2 added the provenance fields below; version 1 files
#: predate them and load with ``origin`` unknown. Reading an older KNOWN version is
#: not the same permission as reading an unknown one -- a file from the future is
#: still refused, because a field this build cannot interpret may be the one that
#: matters. See ``Credential.from_dict`` and O76 clause (b): the live file on a
#: working machine is version 1 carrying every account, so refusing it on a version
#: bump would sign the operator out of their own console to gain a metadata field.
READABLE_VERSIONS = (1, 2)

ALGORITHM = "scrypt"

#: How a stored secret came to exist. Non-secret metadata: it narrows nothing
#: about the secret itself, and it is the whole point of O76 -- a generated secret
#: was PRINTED TO A TERMINAL once, and a prompted one never was.
ORIGIN_PROMPTED = "prompted"
ORIGIN_GENERATED = "generated"
#: A version-1 entry, migrated. NEVER inferred to be ``prompted``: it probably was,
#: and "probably" is not a record. Guessing here would make the staleness flag
#: below silently under-report in the exact file whose new job is provenance.
ORIGIN_UNKNOWN = "unknown"
ORIGINS = (ORIGIN_PROMPTED, ORIGIN_GENERATED, ORIGIN_UNKNOWN)

#: When a GENERATED secret starts asking to be rotated. Named here rather than
#: written at a call site so both reporting surfaces mean the same thing by
#: "stale", and so changing the policy is one edit. Two weeks is a demo cycle: long
#: enough that a secret generated for today's demo is not nagged about, short
#: enough that one still sitting there next sprint is.
GENERATED_SECRET_STALE_DAYS = 14

# OWASP's scrypt configuration (N = 2^14, r = 8, p = 5). Roughly 16 MiB per
# hash, so maxmem must be raised above hashlib's default with room to spare.
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 5
SCRYPT_MAXMEM = 96 * 1024 * 1024
SALT_BYTES = 16
KEY_BYTES = 32

#: Overridable for tests, and for a machine that keeps its secrets elsewhere.
PATH_ENV_VAR = "DRYDOCS_CONSOLE_CREDENTIALS"
DEFAULT_RELATIVE_PATH = Path("internal-local") / "console-credentials.json"

BOOTSTRAP_HINT = (
    "no console credentials are configured on this machine — "
    "run: poetry run python scripts/set_console_credential.py <persona-id>"
)


class CredentialError(Exception):
    """Raised when the credential file exists but cannot be trusted."""


@dataclass(frozen=True)
class Credential:
    """One persona's stored hash and the parameters it was derived under.

    Parameters travel WITH the hash rather than being read from the constants
    above, so raising the cost later does not invalidate what is already
    stored: an old hash still verifies under its own parameters.
    """

    algorithm: str
    salt: str  # hex
    hash: str  # hex
    n: int
    r: int
    p: int
    #: Provenance (O76). Non-secret, and deliberately not defaulted to a
    #: plausible value -- ``ORIGIN_UNKNOWN`` with no ``set_at`` is what a
    #: migrated version-1 entry honestly is.
    origin: str = ORIGIN_UNKNOWN
    set_at: str | None = None  # ISO-8601 UTC, second precision

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "algorithm": self.algorithm,
            "salt": self.salt,
            "hash": self.hash,
            "n": self.n,
            "r": self.r,
            "p": self.p,
            "origin": self.origin,
        }
        # Omitted rather than written as null: an absent stamp and a stamp whose
        # value is nothing are the same fact, and one of the two spellings is
        # easier to read in a file a person opens.
        if self.set_at is not None:
            payload["set_at"] = self.set_at
        return payload

    @property
    def age_days(self) -> int | None:
        """Whole days since this secret was set, or None when unrecorded."""
        if self.set_at is None:
            return None
        try:
            stamp = datetime.fromisoformat(self.set_at)
        except ValueError:
            return None
        if stamp.tzinfo is None:
            # Every stamp this module writes carries a zone. A naive one came
            # from a hand edit, and picking a zone for it would invent the very
            # age it is being asked to measure -- so it is unmeasurable, exactly
            # like an unparseable one above.
            #
            # (Written this way rather than with a tzinfo substitution for a
            # second reason: the ADR 0009 guard in tests/unit/test_mapping_api.py
            # scans this package for write primitives BY NAME, and .replace() is
            # one of them. Its match on datetime.replace is a false positive, but
            # a guard that stops an endpoint granting itself an account is not
            # worth an exemption for a line that has a clearer spelling anyway.)
            return None
        return max(0, (datetime.now(UTC) - stamp).days)

    @property
    def wants_rotation(self) -> bool:
        """True for a GENERATED secret past the staleness threshold.

        Only generated ones, and only when the age is actually known. A prompted
        secret was never printed anywhere, so age alone is not a reason to nag;
        an unknown-origin entry has no age to judge. A flag that fires on
        everything is a flag nobody reads.
        """
        if self.origin != ORIGIN_GENERATED:
            return False
        age = self.age_days
        return age is not None and age >= GENERATED_SECRET_STALE_DAYS

    @classmethod
    def from_dict(cls, raw: object) -> Credential:
        if not isinstance(raw, dict):
            raise CredentialError("credential entry is not an object")
        try:
            credential = cls(
                algorithm=str(raw["algorithm"]),
                salt=str(raw["salt"]),
                hash=str(raw["hash"]),
                n=int(raw["n"]),
                r=int(raw["r"]),
                p=int(raw["p"]),
                # OPTIONAL on purpose, and this is the whole migration (O76).
                # A version-1 entry has neither key and lands as unknown with no
                # stamp; nothing is invented for it. An origin string this build
                # does not recognise is also read as unknown rather than refused,
                # because provenance is metadata -- being unable to interpret it
                # is not a reason to reject a credential that verifies.
                origin=(
                    str(raw["origin"]) if str(raw.get("origin", "")) in ORIGINS else ORIGIN_UNKNOWN
                ),
                set_at=str(raw["set_at"]) if raw.get("set_at") else None,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise CredentialError(f"malformed credential entry: {exc}") from None
        if credential.algorithm != ALGORITHM:
            raise CredentialError(
                f"unsupported hash algorithm {credential.algorithm!r}; "
                f"this build verifies {ALGORITHM!r} only"
            )
        return credential


def _derive(secret: str, salt: bytes, *, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(
        secret.encode("utf-8"),
        salt=salt,
        n=n,
        r=r,
        p=p,
        maxmem=SCRYPT_MAXMEM,
        dklen=KEY_BYTES,
    )


def hash_secret(secret: str, *, origin: str = ORIGIN_UNKNOWN) -> Credential:
    """Derive a fresh salted hash at the current parameters.

    ``origin`` is keyword-only and defaults to unknown rather than to the common
    case, so a caller that has not thought about provenance records that it has
    not, instead of quietly asserting the secret was prompted for.
    """
    if not secret:
        raise ValueError("refusing to hash an empty secret")
    if origin not in ORIGINS:
        raise ValueError(f"unknown credential origin {origin!r}; expected one of {ORIGINS}")
    salt = secrets.token_bytes(SALT_BYTES)
    derived = _derive(secret, salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    return Credential(
        algorithm=ALGORITHM,
        salt=salt.hex(),
        hash=derived.hex(),
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        origin=origin,
        set_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )


def verify_secret(credential: Credential, secret: str) -> bool:
    """Constant-time check of ``secret`` against a stored credential."""
    try:
        expected = bytes.fromhex(credential.hash)
        salt = bytes.fromhex(credential.salt)
    except ValueError:
        raise CredentialError("credential hash or salt is not valid hex") from None
    derived = _derive(secret, salt, n=credential.n, r=credential.r, p=credential.p)
    return hmac.compare_digest(derived, expected)


def credentials_path(root: Path | None = None) -> Path:
    """Where the credential file lives on THIS machine.

    ``DRYDOCS_CONSOLE_CREDENTIALS`` wins; otherwise ``internal-local/`` under
    the repository root. Never ``var/`` — see this module's docstring.
    """
    override = os.environ.get(PATH_ENV_VAR)
    if override:
        return Path(override)
    base = root if root is not None else repo_root(Path(__file__).resolve().parents[1])
    return base / DEFAULT_RELATIVE_PATH


class CredentialStore:
    """The identity-to-hash mapping, loaded from a machine-local file.

    An absent file is not an error: it yields an EMPTY store in which every
    verification fails. That is the fresh-clone state, and the API turns it into
    a 401 that names the bootstrap command.
    """

    def __init__(self, credentials: dict[str, Credential] | None = None) -> None:
        self._credentials: dict[str, Credential] = dict(credentials or {})

    def __len__(self) -> int:
        return len(self._credentials)

    @property
    def is_bootstrapped(self) -> bool:
        """False when no account has a secret yet — nobody can sign in."""
        return bool(self._credentials)

    def identities(self) -> tuple[str, ...]:
        """Ids that HAVE a credential. Never exposed over HTTP: which accounts
        exist is exactly what the dummy derivation in ``verify`` hides."""
        return tuple(sorted(self._credentials))

    def has_identity(self, identity: str) -> bool:
        """Does this id still have a credential? (O75)

        Deliberately narrower than :meth:`identities`, which the docstring above
        forbids exposing. This answers a yes/no question about an id the caller
        ALREADY HOLDS -- the persona name inside a session it is authenticating
        -- so it enumerates nothing and tells an attacker nothing they did not
        present. That distinction is why the authentication path calls this
        rather than testing membership in the tuple.
        """
        return identity in self._credentials

    def verify(self, identity: str, secret: str) -> bool:
        """True when ``secret`` proves ``identity``.

        An unknown identity still pays for a full derivation against a throwaway
        salt before returning False, so response time does not tell an attacker
        which ids are real.
        """
        credential = self._credentials.get(identity)
        if credential is None:
            _derive(secret, bytes(SALT_BYTES), n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
            return False
        return verify_secret(credential, secret)

    def set(self, identity: str, secret: str, *, origin: str = ORIGIN_UNKNOWN) -> None:
        self._credentials[identity] = hash_secret(secret, origin=origin)

    def get(self, identity: str) -> Credential | None:
        """The stored entry, for a REPORTING caller that wants its provenance.

        Returns the credential rather than the secret -- there is no secret to
        return, only a hash it cannot be recovered from. The two listing surfaces
        use this; nothing on the HTTP path does.
        """
        return self._credentials.get(identity)

    def remove(self, identity: str) -> None:
        self._credentials.pop(identity, None)

    # ── persistence ─────────────────────────────────────────────────────────

    @classmethod
    def load(cls, path: Path | None = None) -> CredentialStore:
        target = path if path is not None else credentials_path()
        if not target.exists():
            return cls()
        try:
            raw = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CredentialError(f"cannot read credential file {target}: {exc}") from None
        if not isinstance(raw, dict):
            raise CredentialError(f"credential file {target} is not an object")
        version = raw.get("version")
        if version not in READABLE_VERSIONS:
            raise CredentialError(
                f"credential file {target} is format version {version!r}; "
                f"this build reads {', '.join(str(v) for v in READABLE_VERSIONS)} "
                f"and writes {FORMAT_VERSION}"
            )
        entries = raw.get("credentials")
        if not isinstance(entries, dict):
            raise CredentialError(f"credential file {target} has no credentials object")
        return cls({str(k): Credential.from_dict(v) for k, v in entries.items()})

    def as_payload(self) -> dict[str, object]:
        """The serializable form. Returns a dict and writes NOTHING.

        Writing lives in ``scripts/set_console_credential.py``, outside this
        package, and that is a rule rather than a tidiness preference. The
        ADR 0009 guard in ``tests/unit/test_mapping_api.py`` forbids every
        filesystem write primitive in ``drydocs_api``, and the reason it gives
        applies here with force: an endpoint that can rewrite the credential
        file is an endpoint that can grant itself an account. The API reads and
        verifies; a person at a terminal writes.
        """
        return {
            "version": FORMAT_VERSION,
            "note": (
                "Machine-local console credentials. Never commit this file, never port it, "
                "never copy it between machines. Deleting it removes every account; there is "
                "no committed source to rebuild it from, which is exactly why it does not "
                "live under var/. Re-bootstrap with scripts/set_console_credential.py. "
                "origin/set_at record HOW and WHEN a secret was set and are not secret; "
                "origin 'unknown' means the entry predates version 2 and was not guessed at."
            ),
            "credentials": {k: v.as_dict() for k, v in sorted(self._credentials.items())},
        }


class CredentialChecker(Protocol):
    """What the authentication path actually needs from a credential store.

    Two callers, three members. ``handlers.login`` needs the bootstrap flag and
    ``verify``; ``handlers.authenticate`` needs ``has_identity``, to refuse a
    session belonging to an account that has since been withdrawn (O75).

    Typed as a protocol so the API can hold the reloading store below while
    every test injects a plain :class:`CredentialStore`, without either knowing
    about the other. Adding a member here is therefore a two-implementation
    change by construction, which is the point: a store the API can hold but a
    test cannot substitute would make the auth path untestable offline.
    """

    @property
    def is_bootstrapped(self) -> bool: ...

    def verify(self, identity: str, secret: str) -> bool: ...

    def has_identity(self, identity: str) -> bool: ...


class ReloadingCredentialStore:
    """A :class:`CredentialStore` that notices when its file changes (O73).

    WHY, in one line: without it, adding or rotating a secret does nothing until
    somebody restarts uvicorn, and that friction is what leaves a demo account's
    secret unchanged for months.

    HOW IT DECIDES: a stat, not a timer. Each check compares the file's
    modification time and size against the pair it loaded from, so an unchanged
    file costs one ``os.stat`` per login and nothing else. The pair can in
    principle miss two writes inside one filesystem timestamp tick that leave
    the size identical; for a file a person edits by hand, at a console, that is
    not a case worth a hash over.

    THE TWO FAILURE MODES ARE HANDLED DIFFERENTLY ON PURPOSE:

    * The file is UNREADABLE — corrupt, or caught mid-write. Ambiguous, so the
      last known-good store stands and the reason is logged. Failing closed here
      would turn a routine rotation into a lockout, which is a denial of service
      caused by the safety behaviour rather than by the fault. The writer makes
      this rare anyway by replacing the file atomically rather than truncating
      it in place.
    * The file is ABSENT. Not ambiguous: somebody removed the accounts. The
      store empties, and the next login gets the documented fresh-clone message.

    Reading only. This class writes nothing, and neither does anything else in
    ``drydocs_api`` — see :meth:`CredentialStore.as_payload`.
    """

    def __init__(self, path: Path | None = None) -> None:
        self._path = path if path is not None else credentials_path()
        self._store = CredentialStore()
        self._stamp: tuple[int, int] | None = None
        self._loaded_once = False
        self._refresh()

    @property
    def path(self) -> Path:
        return self._path

    def _stat_stamp(self) -> tuple[int, int] | None:
        try:
            info = self._path.stat()
        except OSError:
            return None
        return (info.st_mtime_ns, info.st_size)

    def _refresh(self) -> None:
        stamp = self._stat_stamp()
        if stamp == self._stamp and self._loaded_once:
            return
        if stamp is None:
            # Absent is unambiguous: the accounts are gone.
            if self._stamp is not None:
                logger.info(
                    "console credential file %s is gone; no account can sign in", self._path
                )
            self._store = CredentialStore()
            self._stamp = None
            self._loaded_once = True
            return
        try:
            self._store = CredentialStore.load(self._path)
        except CredentialError as exc:
            # Keep the last good store. Do NOT record the stamp, so the next
            # call retries rather than treating the bad file as settled.
            logger.warning(
                "console credential file %s could not be read (%s); "
                "continuing with the %d credential(s) loaded previously",
                self._path,
                exc,
                len(self._store),
            )
            self._loaded_once = True
            return
        self._stamp = stamp
        self._loaded_once = True

    @property
    def is_bootstrapped(self) -> bool:
        self._refresh()
        return self._store.is_bootstrapped

    def verify(self, identity: str, secret: str) -> bool:
        self._refresh()
        return self._store.verify(identity, secret)

    def identities(self) -> tuple[str, ...]:
        self._refresh()
        return self._store.identities()

    def has_identity(self, identity: str) -> bool:
        self._refresh()
        return self._store.has_identity(identity)

    def __len__(self) -> int:
        self._refresh()
        return len(self._store)
