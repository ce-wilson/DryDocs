"""Control-M FIELD ROUTING — which job fields carry shell text, and to what.

The vendor half of the old ``controlm/commands.py`` (S2 / ADR 0008). The parser
itself is vendor-neutral and now lives at ``orchestration/shell.py``; what stays
Control-M knowledge is *which fields of a job definition hold executable text
and how each one is shaped*:

  PRECMD / POSTCMD (and the observed ``POSCMD`` typo) — EMBEDDED_SHELL variables
      whose VALUE is raw shell text. Straight to ``shell.parse_command``.
  CMD_LINE — the OS job's command line. Same shape, different field.
  UCM container override — the command rides inside a container-spec ARRAY and
      has to be extracted before it is shell text at all (``extract_container_command``).

WHAT THE ADR EXPECTED HERE, AND WHAT WAS ACTUALLY THERE. ADR 0008 classified
``commands.py`` as "Mixed" and scheduled its "PRECMD/POSTCMD/CMD_LINE and
EMBEDDED_SHELL/UCM field routing" into this module. Measured at the build: the
routing was NOT in that file. Those field names appeared only in its module
docstring and two explanatory comments — every executable line was already
vendor-neutral. The real routing lives in two other places and neither moved
here, because S2's acceptance freezes ``controlm/`` content apart from the two
named splits:

  * ``controlm/variables.py`` — ``SHELL_VAR_NAMES`` and the ``EMBEDDED_SHELL``
    classification. That is the CLASSIFIER's job and it is already in the vendor
    directory, which is where rule 1 wants it.
  * ``drydocs/staging.py`` — the component-side dispatch that turns a classified
    variable into a ``source`` label. That is a load-cadence concern and belongs
    component-side (ADR 0002-a §6).

So this module holds the one genuinely Control-M-shaped thing the parser file
did carry — the UCM extraction — plus the field vocabulary re-exported from the
classifier, so a reader looking for "which Control-M fields hold commands" finds
one answer in the vendor directory instead of three files. It is deliberately
thin: inventing routing code to fill a planned module would be worse than
recording that the plan over-estimated the split.

Neutrality direction (ADR 0008 rule 1): this module may import
``orchestration.shell``; ``orchestration.shell`` must never import this one.
"""

from __future__ import annotations

import re

from ..shell import ParsedCommand, parse_command
from .variables import SHELL_VAR_NAMES

#: Control-M job fields whose value is raw shell text, ready for the neutral
#: parser as-is. The EMBEDDED_SHELL variable names come from the classifier so
#: the two cannot drift; CMD_LINE is the OS-job field, not a variable.
SHELL_TEXT_FIELDS: frozenset[str] = frozenset(SHELL_VAR_NAMES) | {"CMD_LINE"}

#: Fields whose value must be UNWRAPPED before it is shell text.
WRAPPED_COMMAND_FIELDS: frozenset[str] = frozenset({"UCM_CONTAINER_OVERRIDE"})

_CONTAINER_CMD_RE = re.compile(r"command:\s*(?P<arr>.+?)\s*[}\]]", re.IGNORECASE | re.DOTALL)


def extract_container_command(value: str) -> str | None:
    """Pull the inner shell command from a UCM container-override value.

    The override carries an array like
    ``command: /bin/sh, -c, python /app/app.py --job_name ...`` — the real
    command is the element(s) after the ``-c`` flag. Returns None when the
    override has no command array (e.g. environment-only overrides).
    """
    m = _CONTAINER_CMD_RE.search(value)
    if m is None:
        return None
    elements = [e.strip() for e in m.group("arr").split(",")]
    if "-c" in elements:
        idx = elements.index("-c")
        inner = ", ".join(elements[idx + 1 :]).strip()
        # the inner command itself may contain commas (arg lists) — those
        # were split above; rejoin with space which tokenizes the same
        return inner.replace(",", " ").strip() or None
    # no -c: the array itself is the argv
    return " ".join(e for e in elements if e and e != "/bin/sh") or None


def parse_field(field: str, value: str) -> ParsedCommand | None:
    """Parse one Control-M field's value into the neutral ``ParsedCommand``.

    Returns None when the field carries no executable text — an unknown field,
    an empty value, or a container override with no command array. Callers that
    already know a value is plain shell text can go straight to
    ``shell.parse_command``; this exists so a caller holding a FIELD NAME does
    not have to know which of the two shapes it is.
    """
    name = (field or "").upper()
    text = (value or "").strip()
    if not text:
        return None
    if name in WRAPPED_COMMAND_FIELDS:
        inner = extract_container_command(text)
        return parse_command(inner) if inner else None
    if name in SHELL_TEXT_FIELDS:
        return parse_command(text)
    return None
