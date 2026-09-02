"""Entity / identifier extraction — typed matches with spans, mechanism only.

MM3 (epic MM, docs/design/deepdoc-data-flow-overview.md §5-§6). The three
session search scripts shared one contract, "IDs in → references out": every
hit is read for the identifiers it carries, and those identifiers are what the
next search chases. This module is that reading, factored out once so the
deepdoc connectors (MM4/MM5), the mind-map state (drydocs_deepdoc.mindmap) and
the novelty score (drydocs_deepdoc.search_log) all see the same tokens.

Pure parse over text (ADR 0002-A §2: no I/O, no graph, no config) — which is
why it lives in core rather than in the deepdoc component, and why a token's
MEANING is never decided here. A match says "this span has the shape of an
issue key"; whether that key exists, and what it refers to, is the caller's
question against the graph.

THE CLASSES, IN THE ORDER THE PASSES RUN. The order is the design, because the
classes overlap on the same text: the folder name ``PRARAG-HLDM-70002-PEX-RFND-DLY``
contains ``HLDM-70002``, which has the exact shape of an issue key, and
``70002``, which has the shape of an application id. Each pass skips any span an
earlier pass claimed, so the folder wins and the issue-key reading never fires.

    1. guid               8-4-4-4-12 hex; the DPL pipeline / dataset / placement ids
    2. folder_name        the PRAOCG-coded Control-M folder name, decoded
                          positionally by drydocs_core.orchestration.controlm
                          .parse_folder_name; a 5-digit segment inside it is ALSO
                          emitted as an application_id, cued ``folder-segment``
    3. issue_key          ``<PROJECT>-<n>`` — an upper-case project key and a number
    4. table_name         ``SCHEMA.TABLE`` — an upper-case dotted pair (the Oracle
                          idiom); a ``TABLE.COLUMN`` pair has the same shape and
                          is reported the same way — the caller disambiguates
    5. distribution_list  a ``DL-``/``DL_``/``DL.``-prefixed mailbox name, with or
                          without its ``@domain``
    6. application_id     a standalone 5-digit token. Emitted ALWAYS, with
                          ``cued=True`` when a cue precedes it (``-seal``, ``seal``,
                          ``app_id``, ``application``) or a landing-prefix ``/raw/``
                          follows it. A bare 5-digit token in a page title is a
                          real signal (design doc §5, plan C) and a bare 5-digit
                          token in prose is usually noise; the extractor reports
                          both and marks which, and the CALLER ranks.

What this deliberately does not do: guess. No class is inferred from context
beyond the cue flag, no token is normalized to a graph key, and no match is
suppressed because it "looks wrong" — a suppressed token is invisible to the
novelty score, and a wrong token that is visible can be ranked down.

Every value in the tests is synthetic: 5-digit ids sit in the reserved block
70001-70099 (tests/unit/test_publish_boundary_values.py sweeps every tracked
file for anything else), domains are ``.invalid``, project keys are plain words.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from drydocs_core.orchestration.controlm.folder_name import parse_folder_name

GUID = "guid"
FOLDER_NAME = "folder_name"
ISSUE_KEY = "issue_key"
TABLE_NAME = "table_name"
DISTRIBUTION_LIST = "distribution_list"
APPLICATION_ID = "application_id"

#: Pass order == precedence (see the module docstring).
KINDS: tuple[str, ...] = (
    GUID,
    FOLDER_NAME,
    ISSUE_KEY,
    TABLE_NAME,
    DISTRIBUTION_LIST,
    APPLICATION_ID,
)


@dataclass(frozen=True)
class EntityMatch:
    """One typed match: the class, the text it matched, and where.

    ``attributes`` is a tuple of pairs rather than a dict so the match stays
    hashable — a set of matches is how a caller de-duplicates across sources.
    """

    kind: str
    value: str
    start: int
    end: int
    cued: bool = False
    attributes: tuple[tuple[str, str], ...] = ()

    @property
    def span(self) -> tuple[int, int]:
        return (self.start, self.end)

    def attribute(self, name: str) -> str | None:
        for key, val in self.attributes:
            if key == name:
                return val
        return None


# -- the shapes ---------------------------------------------------------------

# The unanchored twin of drydocs_core.orchestration.shell._GUID_RE, which is
# anchored because it classifies a whole argv token; this one scans prose.
_GUID_RE = re.compile(
    r"(?<![0-9A-Za-z])[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}(?![0-9A-Za-z])"
)
#: The flag/field names whose presence just before a GUID says which id it is.
#: Recorded as the ``cue`` attribute, lower-cased, dashes stripped; nothing else
#: is inferred from it.
_GUID_CUES = frozenset(
    {"pipeline", "pipelineid", "dataset", "datasetid", "proid", "provenanceguid", "provenanceid"}
)

# The candidate shape is the publish-boundary guard's own
# (tests/unit/test_publish_boundary_values.py `_FOLDER_TOKEN`): a 6-letter
# prefix and at least two dash segments. `parse_folder_name` alone is too loose
# for a scanner — it recognises any >=6-character token that starts with P/D/Q,
# so `PIPELINE-ID-1` would pass; the shape gate runs first, the decode second.
_FOLDER_RE = re.compile(r"(?<![A-Za-z0-9_-])[A-Z]{6}(?:-[A-Z0-9]{2,20}){2,}(?![A-Za-z0-9_-])")

_ISSUE_KEY_RE = re.compile(r"(?<![A-Za-z0-9_-])([A-Z][A-Z0-9]{1,9})-(\d{1,6})(?![A-Za-z0-9])")

_TABLE_RE = re.compile(
    r"(?<![A-Za-z0-9_.$])([A-Z][A-Z0-9_$]{1,29})\.([A-Z][A-Z0-9_$]{1,29})(?![A-Za-z0-9_.$])"
)

_DL_RE = re.compile(
    r"(?<![A-Za-z0-9_])[Dd][Ll][-_.][A-Za-z0-9][A-Za-z0-9._-]*"
    r"(?:@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)?"
)

_APP_ID_RE = re.compile(r"(?<![0-9A-Za-z_])\d{5}(?![0-9A-Za-z_])")
#: What counts as a cue for a 5-digit token, read from the 24 characters before
#: it: the launcher's `-seal` flag, the `seal`/`app_id`/`application` words the
#: design doc's sources use (§2 `owner_app`), with up to four non-word
#: characters between cue and value — `"APP_ID": "70005"` has exactly four.
_APP_ID_CUE_BEFORE = re.compile(r"(?i)(?:seal|app[_ ]?id|application)\W{0,4}$")
#: ... or the landing-prefix shape after it: `<APP_ID>/raw/<flow>/...` (§2).
_APP_ID_CUE_AFTER = re.compile(r"^/raw/")
_CUE_WINDOW = 24


def _overlaps(start: int, end: int, claimed: list[tuple[int, int]]) -> bool:
    return any(start < c_end and end > c_start for c_start, c_end in claimed)


def _preceding_token(text: str, start: int) -> str:
    """The word-ish token just before ``start`` (flag dashes and `=`/`:` stripped)."""
    head = text[:start].rstrip()
    if head.endswith(("=", ":")):
        head = head[:-1].rstrip()
    token = re.split(r"[\s\"']+", head)[-1] if head else ""
    return token.lstrip("-").replace("-", "").replace("_", "").lower()


def extract_entities(text: str) -> tuple[EntityMatch, ...]:
    """Every typed match in ``text``, ordered by position.

    Pure and total: any string in, a (possibly empty) tuple out, never an
    exception for content. See the module docstring for the classes and the
    precedence between them.
    """
    if not text:
        return ()
    claimed: list[tuple[int, int]] = []
    out: list[EntityMatch] = []

    def take(match: EntityMatch) -> None:
        claimed.append(match.span)
        out.append(match)

    # 1. guid
    for m in _GUID_RE.finditer(text):
        cue = _preceding_token(text, m.start())
        attrs = (("cue", cue),) if cue in _GUID_CUES else ()
        take(EntityMatch(GUID, m.group(0), m.start(), m.end(), cued=bool(attrs), attributes=attrs))

    # 2. folder_name (+ the application ids its segments carry)
    for m in _FOLDER_RE.finditer(text):
        if _overlaps(m.start(), m.end(), claimed):
            continue
        parsed = parse_folder_name(m.group(0))
        if not parsed.prefix_recognized:
            continue
        attrs = (
            ("environment_code", parsed.environment_code or ""),
            ("lob_code", parsed.lob_code or ""),
            ("app_code", parsed.app_code or ""),
            ("folder_type_code", parsed.folder_type_code or ""),
            ("segments", "-".join(parsed.segments)),
        )
        take(EntityMatch(FOLDER_NAME, m.group(0), m.start(), m.end(), attributes=attrs))
        # The identifier decomposition of design doc §6 step 3: a folder name
        # is a bundle of things to chase, and a 5-digit segment is one of them.
        offset = m.start() + len(parsed.prefix) + 1
        for seg in parsed.segments:
            if len(seg) == 5 and seg.isdigit():
                out.append(
                    EntityMatch(
                        APPLICATION_ID,
                        seg,
                        offset,
                        offset + 5,
                        cued=True,
                        attributes=(("cue", "folder-segment"),),
                    )
                )
            offset += len(seg) + 1

    # 3. issue_key
    for m in _ISSUE_KEY_RE.finditer(text):
        if _overlaps(m.start(), m.end(), claimed):
            continue
        attrs = (("project", m.group(1)), ("number", m.group(2)))
        take(EntityMatch(ISSUE_KEY, m.group(0), m.start(), m.end(), attributes=attrs))

    # 4. table_name
    for m in _TABLE_RE.finditer(text):
        if _overlaps(m.start(), m.end(), claimed):
            continue
        attrs = (("schema", m.group(1)), ("object", m.group(2)))
        take(EntityMatch(TABLE_NAME, m.group(0), m.start(), m.end(), attributes=attrs))

    # 5. distribution_list
    for m in _DL_RE.finditer(text):
        value = m.group(0).rstrip("._-")  # a sentence's full stop is not part of the name
        start, end = m.start(), m.start() + len(value)
        if _overlaps(start, end, claimed):
            continue
        local, _, domain = value.partition("@")
        attrs = (("local_part", local), ("domain", domain))
        take(EntityMatch(DISTRIBUTION_LIST, value, start, end, attributes=attrs))

    # 6. application_id (bare)
    for m in _APP_ID_RE.finditer(text):
        if _overlaps(m.start(), m.end(), claimed):
            continue
        before = text[max(0, m.start() - _CUE_WINDOW) : m.start()]
        after = text[m.end() : m.end() + 5]
        cued = bool(_APP_ID_CUE_BEFORE.search(before)) or bool(_APP_ID_CUE_AFTER.match(after))
        attrs: tuple[tuple[str, str], ...] = ()
        if cued:
            attrs = (("cue", "landing-prefix" if _APP_ID_CUE_AFTER.match(after) else "keyword"),)
        take(
            EntityMatch(APPLICATION_ID, m.group(0), m.start(), m.end(), cued=cued, attributes=attrs)
        )

    out.sort(key=lambda e: (e.start, e.end, KINDS.index(e.kind)))
    return tuple(out)


def values(matches: Iterable[EntityMatch], *kinds: str) -> tuple[str, ...]:
    """The distinct matched values, in first-seen order — optionally of ``kinds`` only.

    This is the "references out" half of the connector contract: what a search
    hit contributes to the next search, and what the novelty score compares
    against the graph and the record.
    """
    wanted = set(kinds) if kinds else None
    seen: dict[str, None] = {}
    for m in matches:
        if wanted is None or m.kind in wanted:
            seen.setdefault(m.value, None)
    return tuple(seen)
