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
    group: str = ""
    doc: str = ""
    example: str = ""

    def __post_init__(self) -> None:
        # A secret with an example is how a fake value becomes a real one: the
        # next operator copies `.env.example`, the placeholder looks like a
        # setting rather than a prompt, and it ships. G129 (f) forbids a value
        # in any of the three verbs; this forbids one in the DECLARATION, which
        # is the only place a generated file could have picked one up.
        if self.secret and self.example:
            raise ValueError(
                f"{self.name}: a secret declaration may not carry an example value. "
                "The generated .env.example emits the key and its documentation; the "
                "value is typed at a no-echo prompt (scripts/set_env_var.py)."
            )

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
#: The section headings the generated `.env.example` emits, in order. Declared
#: rather than derived from the variable order, because the FILE's order is a
#: reading order for a human and the tuple's is an append order for code; making
#: one serve both would mean every new variable silently re-arranges the file.
GROUPS: Final[tuple[tuple[str, str], ...]] = (
    ("neo4j", "Neo4j connection (required)"),
    ("roots", "Data root and log roots"),
    ("machine-local", "Machine-local paths and identity (optional -- all have defaults)"),
    ("oracle", "Oracle (optional -- the psgmgr replica; see config/source-bindings.yaml)"),
    ("github", "GitHub (optional -- code loader)"),
    ("llm", "LLM keys (optional -- GraphRAG experiments)"),
)

DECLARED_VARIABLES: Final[tuple[EnvVar, ...]] = (
    EnvVar(
        name="DRYDOCS_DATA_ROOT",
        purpose="root for every source drop and every output the system writes (G81)",
        required=True,
        group="roots",
        doc=(
            "MANDATORY since 2026-08-23: there is no default. Every source drop and every\n"
            "output the system writes is rooted here, and an unset variable used to\n"
            "relocate all of them silently to ~/data/DryDocs -- which is how a write lands\n"
            "on somebody else's source data. Point it at YOUR data root (a real local path;\n"
            "never committed). See config/dev-environment.yaml and config/data-zones.yaml."
        ),
    ),
    EnvVar(
        name="DRYDOCS_LOGDIR",
        purpose="root for loader and supplement run logs (ADR 0014 clause 1)",
        aliases=("SPIDERP_LOGDIR",),
        group="roots",
        doc=(
            "OPTIONAL, unlike the data root above: it defaults to ~/logs/DryDocs, and a\n"
            "relocated log is annoying where a relocated data root is destructive (G81 (d)\n"
            "names the DATA root deliberately, and config/data-zones.yaml records the same\n"
            "scope fence on the run-logs zone). Every loader and supplement run log lands\n"
            "here. SPIDERP_LOGDIR is still honored as a deprecated alias on both log\n"
            "families and is dropped at the cycle ADR 0014 clause 1 names -- set this one."
        ),
    ),
    EnvVar(
        name="DRYDOCS_LOG_LEVEL",
        purpose="fallback level for a log kind that declares none",
        group="roots",
        example="INFO",
        doc=(
            "Level and retention are the FALLBACKS a log kind inherits when it declares\n"
            "none of its own -- the per-kind values live in config/log-kinds.yaml (ADR 0014\n"
            "clause 1 as amended: per KIND, not one global set). Setting these changes what\n"
            "an undeclared kind gets, not what `qa` or `api` get."
        ),
    ),
    EnvVar(
        name="DRYDOCS_LOG_RETENTION_DAYS",
        purpose="fallback retention for a log kind that declares none",
        group="roots",
        example="90",
    ),
    EnvVar(
        name="DRYDOCS_CONSOLE_CREDENTIALS",
        purpose="path to the machine-local console credential file (O69/O73)",
        secret=True,
        group="machine-local",
        doc=(
            "A PATH, not a secret -- and declared secret anyway, because the file it points\n"
            "at IS the credential store, and a path naming an operator's home directory is\n"
            "still worth masking in a shared terminal. Defaults into internal-local/. Write\n"
            "the credentials themselves with scripts/set_console_credential.py, never by hand."
        ),
    ),
    EnvVar(
        name="DRYDOCS_MAPPING_DB",
        purpose="path to the derived mapping read model (ADR 0009)",
        group="machine-local",
        doc="Derived, gitignored and rebuildable -- override only to move it off the default.",
    ),
    EnvVar(
        name="DRYDOCS_MAPPING_READ",
        purpose="read-only toggle for the mapping store",
        group="machine-local",
    ),
    EnvVar(
        name="DRYDOCS_CONTROLM_API_CFG",
        purpose="path to the Control-M API adapter config",
        group="machine-local",
        doc=(
            "The adapter config carries CONNECTION COORDINATES, so it lives in the\n"
            "machine-local tree and this variable is the only committed thing that knows\n"
            "its name (CLAUDE.md section 3)."
        ),
    ),
    EnvVar(
        name="DRYDOCS_AGENT_REG_KEY",
        purpose="agent registry key",
        group="machine-local",
    ),
    EnvVar(
        name="DRYDOCS_CALLER",
        purpose="caller identity stamped on run logs",
        aliases=("SPIDERP_CALLER",),
        group="machine-local",
        doc="SPIDERP_CALLER is the deprecated alias, on the same cycle as SPIDERP_LOGDIR.",
    ),
    EnvVar(
        name="NEO4J_URI",
        purpose="bolt URI of the destination graph",
        required=True,
        group="neo4j",
        example="bolt://localhost:7687",
        doc=(
            "NEO4J_USER maps to the `user` field in Neo4jSettings (prefix NEO4J_), which is\n"
            "why no text search finds these names in the code -- read the settings class,\n"
            "not the tree (J37). Canonical local dev/test instance: config/dev-environment.yaml."
        ),
    ),
    EnvVar(name="NEO4J_USER", purpose="graph user", required=True, group="neo4j", example="neo4j"),
    EnvVar(
        name="NEO4J_PASSWORD",
        purpose="graph password",
        secret=True,
        required=True,
        group="neo4j",
        doc=(
            "No example value, deliberately: a placeholder password in a template is a\n"
            "password somebody ships. Type it at a no-echo prompt instead --\n"
            "  poetry run python scripts/set_env_var.py NEO4J_PASSWORD"
        ),
    ),
    EnvVar(
        name="NEO4J_DATABASE",
        purpose="target topology database (ADR 0002)",
        group="neo4j",
        example="drydocs",
        doc=(
            "Target a topology database (ADR 0002), NOT the EE home db `neo4j` -- ground\n"
            "truth loads go to `drydocs`. Provision first: drydocs_core/schema/provisioning/."
        ),
    ),
    EnvVar(
        name="NEO4J_IMPORT_DIR",
        purpose="server import directory for bulk-import flows",
        group="neo4j",
        doc="The server's import directory. Leave empty unless a loader's docs ask for it.",
    ),
    EnvVar(
        name="NEO4J_CONTAINER",
        purpose="local container name (config/dev-environment.yaml)",
        group="neo4j",
        doc=(
            "The local EE container. Declared here because first-party code reads it and\n"
            "nothing declared it until G125 -- one of the eight."
        ),
    ),
    EnvVar(
        name="ORACLE_USER",
        purpose="Oracle account the psgmgr extracts read as",
        secret=False,
        group="oracle",
    ),
    EnvVar(name="ORACLE_PASSWORD", purpose="Oracle account password", secret=True, group="oracle"),
    EnvVar(
        name="ORACLE_DSN",
        purpose="Oracle connection descriptor -- a CONNECTION COORDINATE, twin-only",
        secret=True,
        group="oracle",
        doc=(
            "The descriptor IS the connection coordinate: host, port and service. It is\n"
            "twin-only and never committed in any form, which is exactly why a registry id\n"
            "may carry the schema NAME -- the name identifies, this reaches."
        ),
    ),
    EnvVar(name="GITHUB_TOKEN", purpose="code loader token", secret=True, group="github"),
    EnvVar(name="GITHUB_USER", purpose="code loader user", group="github"),
    EnvVar(
        name="OPENAI_API_KEY",
        purpose="OpenAI key for GraphRAG experiments",
        secret=True,
        group="llm",
    ),
    EnvVar(
        name="ANTHROPIC_API_KEY",
        purpose="Anthropic key for GraphRAG experiments",
        secret=True,
        group="llm",
    ),
    EnvVar(
        name="ANTHROPIC_MODEL",
        purpose="model id for GraphRAG experiments",
        group="llm",
        example="claude-sonnet-4-6",
    ),
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


# ---------------------------------------------------------------------------
# The OPTIONAL read (G128 (b)).
#
# :func:`expand` raises on unset, which is right for a binding: a declared
# connection that cannot resolve is an error. It is WRONG for the resolvers that
# legitimately have a default -- the log directory is the case, and it is called
# from inside ``open()``, where "a broken declaration must not take the loaders
# with it". Those need the same DECLARATION and the same alias chain without the
# raise, which is what this is. Two functions, one declaration list: the thing
# G125 set out to end was seven private lookups, not the existence of a default.
# ---------------------------------------------------------------------------
def resolve_optional(name: str, *, where: str) -> tuple[str | None, str | None]:
    """``(value, which_name_resolved)`` for a declared variable, or ``(None, None)``.

    Returns WHICH name won so a caller can act on it -- the log resolver emits a
    DeprecationWarning when the legacy alias is the one that answered, and it can
    only do that if the lookup tells it. Secrets are registered exactly as
    :func:`expand` registers them, because a value read here is as real as a
    value read there.

    Raises :class:`UndeclaredVariableError` for an unknown name: a default does
    not excuse a variable from being declared.
    """
    var = _BY_NAME.get(name)
    if var is None:
        raise UndeclaredVariableError(
            f"{where}: {name!r} is not a declared variable. Add it to "
            "DECLARED_VARIABLES in drydocs_core/env_refs.py -- having a default "
            "is not an exemption from being enumerable."
        )
    for candidate in (var.name, *var.aliases):
        raw = os.environ.get(candidate, "").strip()
        if raw:
            if var.secret:
                _SECRETS.register(raw)
            return raw, candidate
    return None, None
