"""The ONE expansion function, the declared variable list, and secret masking (G125 (c), (g)).

WHY THIS MODULE EXISTS. Seven modules each implemented their own version of
"explicit argument, then environment variable, then default", and they disagreed:
:func:`drydocs_core.data_root.resolve_data_root` treats an empty string as unset,
``resolve_log_dir`` walks two variables before its default, ``credentials_path``
takes any non-empty override verbatim, and ``MappingStore.__init__`` imports
``os`` inside the constructor to read one variable. There was no place to look up
which variables exist. ADR 0017 clause 3 rules that a committed file REFERENCES a
variable and never holds a value, which only means something if one function does
the referencing and one list says what may be referenced.

THE TWO RIDERS, both from ADR 0017 clause 3 as amended 2026-08-30, and both are
the point rather than details.

**The expander substitutes and REFUSES defaults.** DataHub's ``${VAR}`` expander
is bash-style, so ``${VAR:-default}`` silently supplies a fallback. Adopting that
would put G81 clause (d)'s silent relocation back at the SYNTAX level, where the
one expansion function cannot see it — the committed YAML would carry the
fallback, not the code, and the whole point of G81 (d) is that an unset data root
FAILS rather than quietly moving every read and write somewhere else. So
``${VAR:-x}`` is not "unsupported"; it is REJECTED, with an error that says why.
An unset variable is an error naming the variable and the row that wanted it.

**The expander is also where a resolved value is registered as secret.** It is
the only place that can know: the declaration says a variable is secret, and the
expansion is where its value first exists. Registering there means masking is
created at the point of read rather than bolted onto each print site, which is
the failure mode a per-site approach always has — the one site nobody updated.

WHAT THIS MODULE DOES NOT DO. It does not test side (A). Nothing here asserts a
variable holds a CORRECT host, and nothing probes a credential — ADR 0017 clause
7 rules that the check starts at the registration, not at ``.env``. This module
answers "is it set, and what may reference it", never "is it right".
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Final

#: A reference is exactly ``${NAME}``. Bash's ``:-`` / ``-`` / ``:=`` / ``:?``
#: default operators are deliberately absent from this pattern so that a
#: reference carrying one fails to match and is reported, rather than being
#: read as a variable named ``VAR:-default``.
_REF = re.compile(r"^\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)\}$")

#: Any ``${...}`` at all, so a malformed reference is REPORTED rather than
#: silently treated as a literal string. A committed value that looks like a
#: reference and is not one is the exact defect this module exists to prevent.
_REF_SHAPED = re.compile(r"\$\{(?P<body>[^}]*)\}")

#: Bash default/alternate operators, named so the error can say which one.
_DEFAULT_OPS: Final = (":-", ":=", ":?", ":+", "-", "=", "?", "+")


class EnvRefError(RuntimeError):
    """Base for every failure this module raises."""


class MalformedRefError(EnvRefError):
    """A value is reference-SHAPED but is not a bare ``${NAME}``."""


class UnsetVariableError(EnvRefError):
    """A declared reference resolved to nothing. Names the variable and the row."""


class UndeclaredVariableError(EnvRefError):
    """A reference names a variable no declaration covers."""


@dataclass(frozen=True)
class EnvVar:
    """One environment variable the system may read.

    ``secret`` is what makes the value maskable; ``required`` is what makes an
    unset value an error rather than a state. Both are declared, never inferred
    from the name, because a naming convention is a guess and this list is a
    contract.
    """

    name: str
    purpose: str
    secret: bool = False
    required: bool = False
    aliases: tuple[str, ...] = ()

    @property
    def is_set(self) -> bool:
        return bool(self.value)

    @property
    def value(self) -> str:
        """The raw value, or ``""``. Reads aliases in declaration order."""
        for candidate in (self.name, *self.aliases):
            raw = os.environ.get(candidate, "").strip()
            if raw:
                return raw
        return ""


# ---------------------------------------------------------------------------
# The enumerable list (G125 (c)).
#
# Before this existed, `.env.example` declared 17 keys and first-party code read
# 8 more that were declared nowhere. A variable absent from this tuple cannot be
# referenced by a committed binding: `expand()` refuses it. That is what keeps
# the list honest rather than aspirational -- it is load-bearing, not a doc.
# ---------------------------------------------------------------------------
DECLARED_VARIABLES: Final[tuple[EnvVar, ...]] = (
    EnvVar(
        name="DRYDOCS_DATA_ROOT",
        purpose="root for every source drop and every output the system writes (G81)",
        required=True,
    ),
    EnvVar(
        name="DRYDOCS_LOGDIR",
        purpose="root for loader and supplement run logs (ADR 0014 clause 1)",
        aliases=("SPIDERP_LOGDIR",),
    ),
    EnvVar(name="DRYDOCS_LOG_LEVEL", purpose="fallback level for a log kind that declares none"),
    EnvVar(
        name="DRYDOCS_LOG_RETENTION_DAYS",
        purpose="fallback retention for a log kind that declares none",
    ),
    EnvVar(
        name="DRYDOCS_CONSOLE_CREDENTIALS",
        purpose="path to the machine-local console credential file (O69/O73)",
        secret=True,
    ),
    EnvVar(name="DRYDOCS_MAPPING_DB", purpose="path to the derived mapping read model (ADR 0009)"),
    EnvVar(name="DRYDOCS_MAPPING_READ", purpose="read-only toggle for the mapping store"),
    EnvVar(name="DRYDOCS_CONTROLM_API_CFG", purpose="path to the Control-M API adapter config"),
    EnvVar(name="DRYDOCS_AGENT_REG_KEY", purpose="agent registry key"),
    EnvVar(
        name="DRYDOCS_CALLER",
        purpose="caller identity stamped on run logs",
        aliases=("SPIDERP_CALLER",),
    ),
    EnvVar(name="NEO4J_URI", purpose="bolt URI of the destination graph", required=True),
    EnvVar(name="NEO4J_USER", purpose="graph user", required=True),
    EnvVar(name="NEO4J_PASSWORD", purpose="graph password", secret=True, required=True),
    EnvVar(name="NEO4J_DATABASE", purpose="target topology database (ADR 0002)"),
    EnvVar(name="NEO4J_IMPORT_DIR", purpose="server import directory for bulk-import flows"),
    EnvVar(name="NEO4J_CONTAINER", purpose="local container name (config/dev-environment.yaml)"),
    EnvVar(name="ORACLE_USER", purpose="Oracle account the psgmgr extracts read as", secret=False),
    EnvVar(name="ORACLE_PASSWORD", purpose="Oracle account password", secret=True),
    EnvVar(
        name="ORACLE_DSN",
        purpose="Oracle connection descriptor -- a CONNECTION COORDINATE, twin-only",
        secret=True,
    ),
    EnvVar(name="GITHUB_TOKEN", purpose="code loader token", secret=True),
    EnvVar(name="GITHUB_USER", purpose="code loader user"),
    EnvVar(name="OPENAI_API_KEY", purpose="GraphRAG experiments", secret=True),
    EnvVar(name="ANTHROPIC_API_KEY", purpose="GraphRAG experiments", secret=True),
    EnvVar(name="ANTHROPIC_MODEL", purpose="model id for GraphRAG experiments"),
)

_BY_NAME: Final[dict[str, EnvVar]] = {v.name: v for v in DECLARED_VARIABLES}


def declared(name: str) -> EnvVar | None:
    """The declaration for ``name``, or ``None``. Exact match only."""
    return _BY_NAME.get(name)


# ---------------------------------------------------------------------------
# Secret masking (G125 (c) rider ii).
# ---------------------------------------------------------------------------
@dataclass
class _SecretRegistry:
    """Values resolved from variables DECLARED secret, for masking.

    Deliberately tiny and process-local. It holds values, so it is never
    serialized, never logged and never returned by any read surface -- the only
    public operation is :func:`mask`, which consumes it and emits no secret.
    """

    _values: set[str] = field(default_factory=set)

    def register(self, value: str) -> None:
        if value and len(value) >= 4:  # a 3-char secret would mask half the corpus
            self._values.add(value)

    def mask(self, text: str) -> str:
        out = text
        for value in sorted(self._values, key=len, reverse=True):
            out = out.replace(value, "********")
        return out

    def clear(self) -> None:
        self._values.clear()


_SECRETS = _SecretRegistry()


def mask(text: str) -> str:
    """Replace every registered secret value in ``text``. Never raises."""
    return _SECRETS.mask(text)


def reset_secret_registry() -> None:
    """Test seam. Production never needs it -- the registry is process-local."""
    _SECRETS.clear()


# ---------------------------------------------------------------------------
# The one expansion function (G125 (c)).
# ---------------------------------------------------------------------------
def is_reference(value: str) -> bool:
    """True when ``value`` is a bare ``${NAME}``.

    The reference-vs-value discriminator, and the one a committed-YAML guard
    asserts on: a credential-keyed field holds a reference or nothing. DataHub
    carries the same rule in its redaction helper -- a value beginning with ``$``
    is safe to show as-is, anything else is masked -- and this is that rule made
    into a write guard rather than a display convenience.
    """
    return bool(_REF.match(value.strip()))


def expand(value: str, *, where: str) -> str:
    """Resolve a bare ``${NAME}`` reference. NO DEFAULTS, ever.

    ``where`` names the row that wanted it and appears in every error, because a
    failure that does not say which declaration asked is a failure someone has
    to bisect for.

    Raises :class:`MalformedRefError` for anything reference-shaped that is not a
    bare ``${NAME}`` -- including bash defaults, which are refused by design and
    not merely unimplemented (ADR 0017 clause 3). Raises
    :class:`UndeclaredVariableError` for a name absent from
    :data:`DECLARED_VARIABLES`, so a new variable cannot enter by being used.
    Raises :class:`UnsetVariableError` when the variable is not set here.
    """
    raw = value.strip()
    match = _REF.match(raw)
    if match is None:
        shaped = _REF_SHAPED.search(raw)
        if shaped is None:
            raise MalformedRefError(
                f"{where}: {raw!r} is not a variable reference. A binding references a "
                "variable as ${NAME} and never holds a literal value (ADR 0017 clause 3)."
            )
        body = shaped.group("body")
        used = next((op for op in _DEFAULT_OPS if op in body), None)
        if used is not None:
            raise MalformedRefError(
                f"{where}: {raw!r} uses the bash default operator {used!r}. Defaults are "
                "REFUSED, not unimplemented: a default in committed YAML puts G81 (d)'s "
                "silent relocation back at the syntax level, where the one expansion "
                "function cannot see it. Reference the variable and let an unset value fail."
            )
        raise MalformedRefError(
            f"{where}: {raw!r} is not a bare ${{NAME}} reference (got ${{{body}}})."
        )

    name = match.group("name")
    var = _BY_NAME.get(name)
    if var is None:
        raise UndeclaredVariableError(
            f"{where}: ${{{name}}} names no declared variable. Add it to "
            "DECLARED_VARIABLES in drydocs_core/env_refs.py with its purpose and "
            "whether it is secret -- a variable that enters by being used is how "
            "eight of them came to be read by code and declared nowhere."
        )
    resolved = var.value
    if not resolved:
        alias_note = f" (also checked {', '.join(var.aliases)})" if var.aliases else ""
        raise UnsetVariableError(
            f"{where}: ${{{name}}} is not set on this machine{alias_note}. {var.purpose}. "
            "Set it in your machine-local .env -- it is never committed."
        )
    if var.secret:
        _SECRETS.register(resolved)
    return resolved


def is_set(name: str) -> bool:
    """Whether a DECLARED variable resolves to a value here. Never returns it."""
    var = _BY_NAME.get(name)
    return bool(var and var.is_set)
