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
import os
import secrets
from dataclasses import dataclass
from pathlib import Path

from drydocs_core.repo_paths import repo_root

#: Bumped when the stored shape changes; a file from the future is refused.
FORMAT_VERSION = 1

ALGORITHM = "scrypt"

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

    def as_dict(self) -> dict[str, object]:
        return {
            "algorithm": self.algorithm,
            "salt": self.salt,
            "hash": self.hash,
            "n": self.n,
            "r": self.r,
            "p": self.p,
        }

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


def hash_secret(secret: str) -> Credential:
    """Derive a fresh salted hash at the current parameters."""
    if not secret:
        raise ValueError("refusing to hash an empty secret")
    salt = secrets.token_bytes(SALT_BYTES)
    derived = _derive(secret, salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    return Credential(
        algorithm=ALGORITHM,
        salt=salt.hex(),
        hash=derived.hex(),
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
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

    def set(self, identity: str, secret: str) -> None:
        self._credentials[identity] = hash_secret(secret)

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
        if version != FORMAT_VERSION:
            raise CredentialError(
                f"credential file {target} is format version {version!r}; "
                f"this build reads version {FORMAT_VERSION}"
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
                "live under var/. Re-bootstrap with scripts/set_console_credential.py."
            ),
            "credentials": {k: v.as_dict() for k, v in sorted(self._credentials.items())},
        }
