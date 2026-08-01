r"""File-path canonicalization and role classification (Phase C).

Operates on RESOLVED values (Phase B output), so Control-M date tokens are
already symbolic ({ODATE}, {ODATE-1}). This module canonicalizes the
remaining wildcards so one logical file = one node regardless of business
date or instance, then classifies the reference role and splits the path
into directory + filename pattern for STG_FILE_REF.

Wildcards (vendor: controlm-file-watcher.md, controlm-pattern-matching.md):
  ``*``  one-or-more chars  -> kept as ``*`` (glob, role-neutral)
  ``?``  single char        -> a run of N is collapsed to a token: the
         16-``?`` timestamp idiom -> ``{TS16}``; other runs -> ``{Q<n>}``
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# a run of '?' wildcards. 16 is the ubiquitous epoch-ish timestamp stamp in
# this shop's dropbox filenames (CMS_IDW_SCRA_Reporting_????????????????.dat).
_QRUN_RE = re.compile(r"\?{2,}")
# already-symbolic Phase-B date token, e.g. {ODATE}, {ODATE-1}, {DATE}
_DATE_TOKEN_RE = re.compile(r"\{[A-Z][A-Z0-9_]*[+-]?\d*\}")
# a value worth treating as a path: has a separator and no shell metachars
_PATHISH_RE = re.compile(r"^[^\s;|&<>]*/[^\s;|&<>]*$")

# variable-name -> ref_role heuristics, checked in order (first hit wins).
# Matched against the UPPER-cased bare variable name.
_ROLE_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"FILEWATCH|WATCH|FW_"), "WATCH_INPUT"),
    (re.compile(r"BACKUP|BKF|BKP"), "BACKUP"),
    (re.compile(r"ARCHIVE|ARCH"), "ARCHIVE"),
    (re.compile(r"DROPBOX|DROP_BOX"), "DROPBOX"),
    (re.compile(r"\bLOG\b|_LOG|LOG_|LOGDIR|APPL_LOG"), "LOG"),
    (re.compile(r"CONFIG|CONF|_JSON|COMPUTE|CFG"), "CONFIG"),
    (re.compile(r"SCRIPT|WRAPPER|LAUNCH|_BIN\b|BIN_PATH|PSET|RPATH|_DIR\b"), "SCRIPT_DIR"),
    (re.compile(r"OUT|TGT|TARGET|DEST"), "OUTPUT"),
]
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


def looks_like_path(value: str) -> bool:
    """True if the value is a single filesystem path (not a command line,
    URL, JSON blob, or e-mail)."""
    v = value.strip()
    if not v or v.startswith("%%") or "@" in v or "://" in v:
        return False
    if v.lstrip().startswith("{") or v.startswith("("):  # JSON / config blob
        return False
    return bool(_PATHISH_RE.match(v))


def canonicalize_path(value: str) -> str:
    """Collapse wildcard runs to stable tokens; leave Phase-B date tokens
    and ``*`` globs intact."""

    def _qrun(m: re.Match) -> str:
        n = len(m.group(0))
        return "{TS16}" if n == 16 else f"{{Q{n}}}"

    return _QRUN_RE.sub(_qrun, value)


def classify_role(var_name: str, *, source_field: str | None = None) -> str:
    """Map a variable name (or source field) to a STG_FILE_REF ref_role.
    Defaults to INPUT when nothing matches."""
    name = (var_name or "").upper()
    if source_field and source_field.upper().startswith("FILEWATCH"):
        return "WATCH_INPUT"
    for pattern, role in _ROLE_RULES:
        if pattern.search(name):
            return role
    return "INPUT"


def _date_token(canonical: str) -> str | None:
    m = _DATE_TOKEN_RE.search(canonical)
    if m:
        return m.group(0)
    for synthetic in ("{TS16}",):
        if synthetic in canonical:
            return synthetic
    return None


def build_file_ref(
    var_name: str,
    resolved_value: str,
    *,
    source_field: str,
    role: str | None = None,
) -> FileRef | None:
    """Build a FileRef from a resolved path value, or None if the value is
    not path-like. ``role`` overrides the name-based heuristic (used by the
    FileWatch handler, which always knows the role is WATCH_INPUT)."""
    value = (resolved_value or "").strip()
    if not looks_like_path(value):
        return None
    canonical = canonicalize_path(value)
    directory, _, filename = canonical.rpartition("/")
    chosen = role or classify_role(var_name, source_field=source_field)
    if chosen not in _VALID_ROLES:
        chosen = "INPUT"
    return FileRef(
        ref_role=chosen,
        path_raw=value[:2000],
        path_canonical=canonical[:2000],
        directory_path=(directory or None) and directory[:1000],
        filename_pattern=(filename or None) and filename[:500],
        date_token=_date_token(canonical),
        source_field=source_field[:60],
    )
