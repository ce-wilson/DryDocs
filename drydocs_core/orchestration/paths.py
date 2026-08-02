r"""File-path canonicalization and role classification — the VENDOR-NEUTRAL half.

Lifted from ``controlm/paths.py`` at S2 (ADR 0008 rule 1: a vendor directory
holds vendor semantics and nothing else). What is neutral is the SHAPE and the
ASSEMBLY — one logical file becomes one ``FileRef`` with a role, a directory and
a filename pattern, ready for STG_FILE_REF. What is NOT neutral is the token
vocabulary: which wildcard runs collapse to what, which brace tokens mean a
business date, which variable-name prefix means "this is a watched input".

That difference is carried by :class:`PathDialect` rather than by an
``if orchestrator ==`` branch, so a second orchestrator supplies a dialect
instead of forking this module — the reusability ADR 0008 is buying. The
Control-M dialect lives at ``orchestration/controlm/paths.py`` and is the only
one that exists today; ``NEUTRAL`` is a real, usable dialect (identity
canonicalization, no date tokens), not a placeholder.

Operates on RESOLVED values, so vendor variable substitution has already
happened and only symbolic tokens remain.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field

# a value worth treating as a path: has a separator and no shell metachars
_PATHISH_RE = re.compile(r"^[^\s;|&<>]*/[^\s;|&<>]*$")

# variable-name -> ref_role heuristics, checked in order (first hit wins), AFTER
# any dialect-supplied rules. These hold for any orchestrator: they read the
# author's own naming intent, not the vendor's syntax.
_ROLE_RULES: tuple[tuple[re.Pattern, str], ...] = (
    (re.compile(r"BACKUP|BKF|BKP"), "BACKUP"),
    (re.compile(r"ARCHIVE|ARCH"), "ARCHIVE"),
    (re.compile(r"DROPBOX|DROP_BOX"), "DROPBOX"),
    (re.compile(r"\bLOG\b|_LOG|LOG_|LOGDIR|APPL_LOG"), "LOG"),
    (re.compile(r"CONFIG|CONF|_JSON|COMPUTE|CFG"), "CONFIG"),
    (re.compile(r"SCRIPT|WRAPPER|LAUNCH|_BIN\b|BIN_PATH|PSET|RPATH|_DIR\b"), "SCRIPT_DIR"),
    (re.compile(r"OUT|TGT|TARGET|DEST"), "OUTPUT"),
)
_VALID_ROLES = {
    "WATCH_INPUT",
    "INPUT",
    "OUTPUT",
    "BACKUP",
    "ARCHIVE",
    "LOG",
    "CONFIG",
    "DROPBOX",
    "SCRIPT_DIR",
}


def _identity(value: str) -> str:
    return value


def _no_date_token(value: str) -> str | None:
    return None


@dataclass(frozen=True)
class PathDialect:
    """One orchestrator's path vocabulary.

    ``canonicalize`` collapses vendor wildcard runs to stable tokens so one
    logical file is one node across business dates and instances.
    ``date_token`` reports which symbolic token (if any) made it varying.
    ``non_path_prefixes`` are value prefixes that mean "not a path" in this
    vendor's syntax (Control-M's unresolved ``%%`` variables, say).
    ``role_rules`` and ``source_field_roles`` are vendor role heuristics; both
    are checked BEFORE the neutral rules, which preserves first-hit-wins order.
    """

    name: str
    canonicalize: Callable[[str], str] = _identity
    date_token: Callable[[str], str | None] = _no_date_token
    non_path_prefixes: tuple[str, ...] = ()
    role_rules: tuple[tuple[re.Pattern, str], ...] = ()
    source_field_roles: tuple[tuple[str, str], ...] = field(default=())


#: A usable dialect, not a stub: identity canonicalization, no date tokens, no
#: vendor role rules. An orchestrator whose paths carry no wildcard vocabulary
#: is correctly served by this.
NEUTRAL = PathDialect(name="neutral")


@dataclass(frozen=True)
class FileRef:
    """One file/path reference, ready for STG_FILE_REF."""

    ref_role: str
    path_raw: str
    path_canonical: str
    directory_path: str | None
    filename_pattern: str | None
    date_token: str | None
    source_field: str


def looks_like_path(value: str, *, dialect: PathDialect = NEUTRAL) -> bool:
    """True if the value is a single filesystem path (not a command line,
    URL, JSON blob, or e-mail)."""
    v = value.strip()
    if not v or "@" in v or "://" in v:
        return False
    if any(v.startswith(p) for p in dialect.non_path_prefixes):
        return False
    if v.lstrip().startswith("{") or v.startswith("("):  # JSON / config blob
        return False
    return bool(_PATHISH_RE.match(v))


def classify_role(
    var_name: str,
    *,
    source_field: str | None = None,
    dialect: PathDialect = NEUTRAL,
) -> str:
    """Map a variable name (or source field) to a STG_FILE_REF ref_role.
    Defaults to INPUT when nothing matches."""
    name = (var_name or "").upper()
    if source_field:
        upper_field = source_field.upper()
        for prefix, role in dialect.source_field_roles:
            if upper_field.startswith(prefix):
                return role
    for pattern, role in (*dialect.role_rules, *_ROLE_RULES):
        if pattern.search(name):
            return role
    return "INPUT"


def build_file_ref(
    var_name: str,
    resolved_value: str,
    *,
    source_field: str,
    role: str | None = None,
    dialect: PathDialect = NEUTRAL,
) -> FileRef | None:
    """Build a FileRef from a resolved path value, or None if the value is
    not path-like. ``role`` overrides the name-based heuristic (used by the
    FileWatch handler, which always knows the role is WATCH_INPUT)."""
    value = (resolved_value or "").strip()
    if not looks_like_path(value, dialect=dialect):
        return None
    canonical = dialect.canonicalize(value)
    directory, _, filename = canonical.rpartition("/")
    chosen = role or classify_role(var_name, source_field=source_field, dialect=dialect)
    if chosen not in _VALID_ROLES:
        chosen = "INPUT"
    return FileRef(
        ref_role=chosen,
        path_raw=value[:2000],
        path_canonical=canonical[:2000],
        directory_path=(directory or None) and directory[:1000],
        filename_pattern=(filename or None) and filename[:500],
        date_token=dialect.date_token(canonical),
        source_field=source_field[:60],
    )
