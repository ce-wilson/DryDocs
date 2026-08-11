"""Normalize the audit timestamps a Control-M XML export stamps on definitions.

A BMC XML export writes audit times (``CHANGE_DATE``, ``LAST_UPLOAD``,
``ACTIVE_FROM``, ``ACTIVE_TILL``) in a **compact** form Neo4j cannot read::

    20250715172540UTC     ->  2025-07-15T17:25:40Z
    20250715172540+0100   ->  2025-07-15T17:25:40+0100
    20250715              ->  2025-07-15T00:00:00

Handing that to the loaders' ``datetime(replace(x, ' ', 'T'))`` Cypher raises
*"Text cannot be parsed to a DateTime"*, which aborts the whole load — not the
one row.

The **Oracle** projections of the same fields already deliver
``YYYY-MM-DD HH:MM:SS``, and the loaders' Cypher handles the space-to-``T``
itself. So this function must be a no-op on that form: both carriers feed the
same loaders, and a normalizer that "helpfully" rewrote the Oracle form would
break the path that already works.

Four decisions, each one a failure mode rather than a preference:

1. ``UTC`` and ``Z`` both normalize to ``Z``; a **numeric** offset is kept
   verbatim, because rewriting ``+0100`` to ``Z`` would move the instant.
2. An 8-digit date-only value becomes midnight rather than being rejected —
   a date with no time is a real export value, not a defect.
3. A value that is **not** the compact form but *is* recognizably a date is
   handed through untouched (the Oracle case above).
4. Anything else returns ``None``, so the loaders' existing null-guard drops
   one field instead of a malformed string reaching the driver.

.. note::

   Point 4 is a **deliberate divergence** from the captured company original
   (``internal/controlm-config/reference/controlm-xml-processor-capture.md``
   Part D). That implementation *documents* returning ``None`` for anything
   unparseable, but its fall-through returns the input string, so only
   ``None``/empty ever produced ``None`` — a garbage value still reached the
   driver. This is the "docstring promises more than the code matches" family
   J26 sweeps, so the promise is implemented here rather than the behaviour
   copied. The pass-through the Oracle path depends on is preserved by
   recognizing the ISO-ish shape explicitly instead of by falling through.
"""

from __future__ import annotations

import re

#: Trailing zone token on a compact BMC timestamp: ``UTC`` / ``Z`` / ``+hhmm``
#: / ``+hh:mm``. Anchored to the end — a zone token is a suffix, never inline.
_ZONE_RE = re.compile(r"(UTC|Z|[+-]\d{2}:?\d{2})$", re.IGNORECASE)

#: The forms this module hands through UNCHANGED: an ISO-ish date or datetime,
#: separated by a space or a ``T``, with an optional zone. This is what the
#: Oracle projections emit and what the loaders' Cypher already parses.
_ISOISH_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}"  # date
    r"(?:[ T]\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?)?"  # optional time
    r"(?:Z|[+-]\d{2}:?\d{2})?$",  # optional zone
    re.IGNORECASE,
)

__all__ = ["normalize_export_timestamp"]


def normalize_export_timestamp(value: str | None) -> str | None:
    """Return *value* as an ISO timestamp the loaders' Cypher can parse.

    Returns ``None`` when there is nothing usable — never a malformed string,
    because the caller's null-guard can drop a field but the Neo4j driver
    cannot recover from a bad one mid-load.
    """
    if value is None:
        return None
    raw = value.strip()
    if not raw:
        return None

    zone = ""
    match = _ZONE_RE.search(raw)
    if match:
        token = match.group(0).upper()
        # UTC and Z mean the same instant; a numeric offset does not, so it
        # survives exactly as written.
        zone = "Z" if token in ("UTC", "Z") else match.group(0)
        raw = raw[: match.start()]

    if raw.isdigit() and len(raw) == 14:  # YYYYMMDDHHMMSS
        return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}" f"T{raw[8:10]}:{raw[10:12]}:{raw[12:14]}{zone}"
    if raw.isdigit() and len(raw) == 8:  # YYYYMMDD — a date with no time
        return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}T00:00:00{zone}"

    # Already an ISO-ish form (the Oracle projections) — hand it through
    # exactly as received, zone token included.
    if _ISOISH_RE.match(value.strip()):
        return value.strip()

    return None
