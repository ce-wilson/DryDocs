"""Validate a page fragment: well-formed XML + a macro allow-list.

Confluence "storage format" is XHTML with ``ac:`` / ``ri:`` namespaced elements; macros
appear as ``<ac:structured-macro ac:name="...">``. We parse the fragment (wrapped so the
namespace prefixes resolve) to check well-formedness, then reject any macro whose name is
not on the allow-list — a guard against unreviewed/unsafe macros slipping into a push.
"""

from __future__ import annotations

from collections.abc import Iterable
from xml.etree import ElementTree as ET

_AC = "http://www.atlassian.com/schema/confluence/4/ac/"
_RI = "http://www.atlassian.com/schema/confluence/4/ri/"
_WRAP = f'<root xmlns:ac="{_AC}" xmlns:ri="{_RI}">{{}}</root>'

# Macros considered safe for the public template. A company profile can extend this.
DEFAULT_ALLOWED_MACROS: frozenset[str] = frozenset(
    {"info", "note", "warning", "tip", "panel", "code", "toc", "expand", "status"}
)


class ValidationError(RuntimeError):
    """The fragment is not well-formed XML or uses a disallowed macro."""


def _parse(fragment: str) -> ET.Element:
    return ET.fromstring(_WRAP.format(fragment))


def validate_xml(fragment: str) -> list[str]:
    """Return a list of well-formedness errors (empty = valid)."""
    try:
        _parse(fragment)
    except ET.ParseError as exc:
        return [f"not well-formed XML: {exc}"]
    return []


def validate_macros(fragment: str, allowed: Iterable[str] = DEFAULT_ALLOWED_MACROS) -> list[str]:
    """Return errors for any ``ac:structured-macro`` whose name is not allowed."""
    allow = frozenset(allowed)
    try:
        root = _parse(fragment)
    except ET.ParseError as exc:
        return [f"not well-formed XML: {exc}"]
    errors: list[str] = []
    for macro in root.iter(f"{{{_AC}}}structured-macro"):
        name = macro.get(f"{{{_AC}}}name")
        if name is None:
            errors.append("structured-macro missing ac:name")
        elif name not in allow:
            errors.append(f"macro '{name}' not in allow-list {sorted(allow)}")
    return errors


def validate(
    fragment: str, *, allowed: Iterable[str] = DEFAULT_ALLOWED_MACROS, raise_on_error: bool = False
) -> list[str]:
    """Full check: well-formedness then macros. Optionally raise on the first failure."""
    errors = validate_xml(fragment)
    if not errors:  # only check macros if it parses
        errors = validate_macros(fragment, allowed)
    if errors and raise_on_error:
        raise ValidationError("; ".join(errors))
    return errors
