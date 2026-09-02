"""Assemble authored XHTML fragments into a single page body via a template."""

from __future__ import annotations

from collections.abc import Iterable

# The template wraps the joined fragments; ``{body}`` is the only placeholder.
DEFAULT_TEMPLATE = '<div class="drydocs-doc">\n{body}\n</div>'


def assemble(fragments: Iterable[str], *, template: str = DEFAULT_TEMPLATE, sep: str = "\n") -> str:
    """Join ``fragments`` and wrap them in ``template`` (must contain ``{body}``)."""
    if "{body}" not in template:
        raise ValueError("template must contain the '{body}' placeholder")
    body = sep.join(f.strip() for f in fragments if f and f.strip())
    return template.format(body=body)
