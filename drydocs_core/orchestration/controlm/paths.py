r"""The Control-M PATH DIALECT — the vendor half of the old ``controlm/paths.py``.

The shape (``FileRef``, role vocabulary, assembly) is neutral and lives at
``orchestration/paths.py``. What is Control-M is the TOKEN VOCABULARY, and it is
all here:

  ``?``  single-char wildcard — a run of N collapses to a token, so one logical
         file is one node across instances. The 16-``?`` idiom is this shop's
         epoch-ish timestamp stamp (``CMS_IDW_SCRA_Reporting_????????????????.dat``)
         and gets its own ``{TS16}``; other runs become ``{Q<n>}``.
         (vendor: controlm-file-watcher.md, controlm-pattern-matching.md)
  ``*``  one-or-more chars — kept as ``*``; a glob is role-neutral.
  ``{ODATE}`` / ``{ODATE-1}`` / ``{DATE}`` — Phase-B date tokens, already
         symbolic by the time a value reaches here.
  ``%%`` — an UNRESOLVED AutoEdit variable. A value still carrying one is not a
         path; it is a substitution that did not happen.
  ``FILEWATCH`` — a source field or variable name that declares a watched input.

Every public name here is the neutral function bound to :data:`CONTROLM`, so
callers importing ``build_file_ref`` / ``classify_role`` / ``looks_like_path``
from ``drydocs_core.orchestration.controlm`` get identical behavior to the
pre-split module — the split changed where the knowledge lives, not what it does.
"""

from __future__ import annotations

import re

from ..paths import FileRef, PathDialect
from ..paths import build_file_ref as _build_file_ref
from ..paths import classify_role as _classify_role
from ..paths import looks_like_path as _looks_like_path

# a run of '?' wildcards. 16 is the ubiquitous epoch-ish timestamp stamp in
# this shop's dropbox filenames (CMS_IDW_SCRA_Reporting_????????????????.dat).
_QRUN_RE = re.compile(r"\?{2,}")
# already-symbolic Phase-B date token, e.g. {ODATE}, {ODATE-1}, {DATE}
_DATE_TOKEN_RE = re.compile(r"\{[A-Z][A-Z0-9_]*[+-]?\d*\}")


def canonicalize_path(value: str) -> str:
    """Collapse wildcard runs to stable tokens; leave Phase-B date tokens
    and ``*`` globs intact."""

    def _qrun(m: re.Match) -> str:
        n = len(m.group(0))
        return "{TS16}" if n == 16 else f"{{Q{n}}}"

    return _QRUN_RE.sub(_qrun, value)


def date_token(canonical: str) -> str | None:
    """The symbolic token that makes this path vary per run, or None."""
    m = _DATE_TOKEN_RE.search(canonical)
    if m:
        return m.group(0)
    for synthetic in ("{TS16}",):
        if synthetic in canonical:
            return synthetic
    return None


#: The Control-M dialect. The only one that exists today; an AutoSys or Airflow
#: module supplies its own rather than editing ``orchestration/paths.py``.
CONTROLM = PathDialect(
    name="controlm",
    canonicalize=canonicalize_path,
    date_token=date_token,
    # an unresolved AutoEdit variable is a failed substitution, not a path
    non_path_prefixes=("%%",),
    # checked BEFORE the neutral rules — it was first in the pre-split list and
    # WATCH beats the generic OUT/LOG hits on names like FW_OUT_DIR
    role_rules=((re.compile(r"FILEWATCH|WATCH|FW_"), "WATCH_INPUT"),),
    source_field_roles=(("FILEWATCH", "WATCH_INPUT"),),
)


def looks_like_path(value: str) -> bool:
    """:func:`orchestration.paths.looks_like_path` in the Control-M dialect."""
    return _looks_like_path(value, dialect=CONTROLM)


def classify_role(var_name: str, *, source_field: str | None = None) -> str:
    """:func:`orchestration.paths.classify_role` in the Control-M dialect."""
    return _classify_role(var_name, source_field=source_field, dialect=CONTROLM)


def build_file_ref(
    var_name: str,
    resolved_value: str,
    *,
    source_field: str,
    role: str | None = None,
) -> FileRef | None:
    """:func:`orchestration.paths.build_file_ref` in the Control-M dialect."""
    return _build_file_ref(
        var_name,
        resolved_value,
        source_field=source_field,
        role=role,
        dialect=CONTROLM,
    )


__all__ = [
    "CONTROLM",
    "FileRef",
    "build_file_ref",
    "canonicalize_path",
    "classify_role",
    "date_token",
    "looks_like_path",
]
