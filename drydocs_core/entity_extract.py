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
                          .parse_folder_name; a 5-to-7-digit segment inside it is
                          ALSO emitted as an application_id, cued ``folder-segment``
    3. issue_key          ``<PROJECT>-<n>`` — an upper-case project key and a number
    4. table_name         ``SCHEMA.TABLE`` — an upper-case dotted pair (the Oracle
                          idiom); a ``TABLE.COLUMN`` pair has the same shape and
                          is reported the same way — the caller disambiguates
    5. distribution_list  a ``DL-``/``DL_``/``DL.``-prefixed mailbox name, with or
                          without its ``@domain``
    6. application_id     a standalone run of 4 to 7 digits — the MEASURED width
                          of the live SEAL population, not a believed one (the
                          ledger's ``Seal IDs`` note in
                          config/source-mappings/pat-team-report.yaml: "token width
                          is 4 to 7 digits, never assume 5 or 6", profile
                          SME-reported 2026-09-07, cited by the K30 close note).
                          ``cued=True`` when a cue precedes it (``-seal``, ``seal``,
                          ``app_id``, ``application``) or a landing-prefix ``/raw/``
                          follows it.

                          THE BARE FLOOR IS FIVE; FOUR NEEDS A CUE. A 5-, 6- or
                          7-digit run is emitted bare as well as cued, because a
                          bare id in a page title is a real signal (design doc §5,
                          plan C) and a bare id in prose is usually noise — the
                          extractor reports both, marks which, and the CALLER ranks.
                          A 4-digit run is emitted ONLY when the text names it,
                          because bare 4-digit runs are years, clock times, ports
                          and small counts: at that width the class stops carrying
                          information and every document in the corpus would
                          contribute a handful of them to the novelty score.
    7. acronym            MM12. A standalone run of 2 to 6 upper-case characters,
                          at least one of them a letter, that no earlier pass
                          claimed — so a project key inside an issue key, a
                          schema inside a table name and a folder prefix are
                          already taken and never read twice. It runs LAST
                          because it is the widest shape, and the precedence
                          order is the whole of what keeps it from stealing them.

                          THE SENTENCE TRAVELS WITH THE TOKEN, which is what
                          makes this class different from the six above. ``SNOW``
                          is worth nothing on its own; it is worth something
                          because a person wrote down that it means ServiceNow
                          and explicitly NOT Snowflake, and that distinction
                          lives in the prose rather than in the token. Every
                          acronym match carries an ``evidence`` attribute holding
                          the sentence it was found in, so two occurrences of one
                          acronym are two matches with two sentences — never one
                          collapsed reading.

                          ``cued=True`` when the text GLOSSES it: an adjacent
                          parenthetical either way round (``ServiceNow (SNOW)``,
                          ``SNOW (ServiceNow)``) or a naming verb (``stands
                          for``, ``means``, ``short for``). A parenthetical also
                          records what it said in a ``gloss`` attribute —
                          recorded, never resolved. Whether the gloss is RIGHT is
                          the reader's question, and one acronym glossed two ways
                          in two documents is exactly the finding this class
                          exists to surface.

                          THE FUNCTION-WORD FLOOR is the same rule as the 4-digit
                          floor above, not a new kind of exception. A closed class
                          of English function words — articles, conjunctions,
                          auxiliaries — appears in caps for EMPHASIS in every
                          corpus, and at that shape the class stops carrying
                          information exactly as a bare ``2026`` does, so a
                          function word is emitted only when the text glosses it.
                          Closed class, not a blocklist of tokens that "look
                          wrong": a real acronym is never an article, and if one
                          ever is, the gloss cue emits it anyway.

What this deliberately does not do: guess. No class is inferred from context
beyond the cue flag, no token is normalized to a graph key, and no match is
suppressed because it "looks wrong" — a suppressed token is invisible to the
novelty score, and a wrong token that is visible can be ranked down.

The width floor above is a CANDIDATE SHAPE, not an exception to that: it decides
what is a candidate before any match exists, exactly as the issue-key pass
requires an upper-case project key and the table pass an upper-case dotted pair.
Once a token IS a candidate it is always reported. A six-digit row count is a
candidate, is emitted uncued, and is ranked down by the caller — that is the
design working, not a hole in it.

Every value in the tests is synthetic: 5-digit ids sit in the reserved block
70001-70099 (tests/unit/test_publish_boundary_values.py sweeps every tracked
file for anything else), domains are ``.invalid``, project keys are plain words.
The other widths have no reserved block, so the tests extend the same ``700``
prefix (``7001``, ``700011``, ``7000111``) and the one sweep that can see them
carries an allowlist row saying so.
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
ACRONYM = "acronym"

#: Pass order == precedence (see the module docstring).
KINDS: tuple[str, ...] = (
    GUID,
    FOLDER_NAME,
    ISSUE_KEY,
    TABLE_NAME,
    DISTRIBUTION_LIST,
    APPLICATION_ID,
    ACRONYM,
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

#: The candidate width, measured rather than believed: the live SEAL population
#: runs 4 to 7 digits, with five AND six both common (the `Seal IDs` note in
#: config/source-mappings/pat-team-report.yaml, profile SME-reported 2026-09-07,
#: cited by the K30 close note). It was `\d{5}` until CORE5, which is why a
#: six-digit id — an ordinary width in that column — was never emitted at all.
_APP_ID_RE = re.compile(r"(?<![0-9A-Za-z_])\d{4,7}(?![0-9A-Za-z_])")
#: The narrowest width that survives on its own. Below it a bare run of digits is
#: a year, a clock time, a port or a small count far more often than an id, so a
#: 4-digit candidate is emitted only when a cue names it (see the module
#: docstring). This is the precision half of the widening: widening the floor as
#: well as the ceiling would have put a `2026` into every document's matches.
_APP_ID_BARE_MIN_WIDTH = 5
#: The top of the measured range, kept as a name so the folder-segment pass and
#: `_APP_ID_RE` cannot drift apart the way the five-digit belief did.
_APP_ID_MAX_WIDTH = 7
#: What counts as a cue, read from the 24 characters before the token: the
#: launcher's `-seal` flag, the `seal`/`app_id`/`application` words the design
#: doc's sources use (§2 `owner_app`), with up to four non-word characters
#: between cue and value — `"APP_ID": "70005"` has exactly four.
_APP_ID_CUE_BEFORE = re.compile(r"(?i)(?:seal|app[_ ]?id|application)\W{0,4}$")
#: ... or the landing-prefix shape after it: `<APP_ID>/raw/<flow>/...` (§2).
_APP_ID_CUE_AFTER = re.compile(r"^/raw/")
_CUE_WINDOW = 24

#: MM12. Two to six upper-case characters, at least ONE of them a letter, so
#: ``S3``, ``EC2``, ``DL`` and ``P12`` are candidates and ``70002`` is not.
#: Digits are allowed inside the run because vendors put them there (S3, EC2)
#: and because this estate's own codes carry them (the P12 data centre, an L2
#: support tier) — not so that a number can qualify as an acronym. The
#: lookarounds keep it off the tail of a longer word; overlap with a span an
#: earlier pass CLAIMED is checked separately, because the claim is the
#: authority here and a regex cannot see it.
_ACRONYM_RE = re.compile(
    r"(?<![A-Za-z0-9_-])(?=[A-Z0-9]{2,6}(?![A-Za-z0-9_-]))[A-Z0-9]*[A-Z][A-Z0-9]*(?![A-Za-z0-9_-])"
)
#: The closed class of English function words that appear in caps for emphasis.
#: Articles, conjunctions, prepositions, auxiliaries, negations, quantifiers —
#: the parts of speech a real acronym is never drawn from. Emitted only when the
#: text glosses them (see the module docstring's function-word floor).
_ACRONYM_FUNCTION_WORDS = frozenset(
    {
        "A",
        "AN",
        "THE",
        "AND",
        "OR",
        "NOT",
        "BUT",
        "IF",
        "THEN",
        "ELSE",
        "SO",
        "AS",
        "AT",
        "BY",
        "FOR",
        "FROM",
        "IN",
        "INTO",
        "OF",
        "ON",
        "TO",
        "UP",
        "WITH",
        "IS",
        "ARE",
        "WAS",
        "WERE",
        "BE",
        "BEEN",
        "DO",
        "DOES",
        "DID",
        "HAS",
        "HAVE",
        "HAD",
        "CAN",
        "MAY",
        "MUST",
        "WILL",
        "WOULD",
        "SHOULD",
        "ALL",
        "ANY",
        "NO",
        "YES",
        "ONE",
        "TWO",
        "THIS",
        "THAT",
        "THESE",
        "NEVER",
        "ALWAYS",
        "ONLY",
        "EVERY",
        "EACH",
        "BOTH",
        "SAME",
        "NEW",
    }
)
#: ``<expansion> (ACRONYM)`` — the gloss precedes, and group 1 is what it said.
#: Bounded to six words so a whole clause before an unrelated parenthesis is not
#: read as an expansion.
_ACRONYM_GLOSS_BEFORE = re.compile(r"((?:[A-Za-z][\w-]*[ ]){0,5}[A-Za-z][\w-]*)[ ]*\($")
#: ``ACRONYM (expansion)`` — the gloss follows, in the parenthesis.
_ACRONYM_GLOSS_AFTER = re.compile(r"^[ ]*\(([^()]{1,80})\)")
#: ``ACRONYM stands for ...`` — a naming verb marks the token as glossed without
#: capturing an expansion; the sentence carries the meaning either way.
_ACRONYM_NAMING_VERB = re.compile(r"(?i)^[ ]*(?:stands[ ]for|short[ ]for|means)\b")
#: How far either side of an acronym the gloss is looked for.
_ACRONYM_GLOSS_WINDOW = 60
#: The most evidence one candidate carries. A sentence longer than this is a
#: run-on or a table row, and the point is a readable breadcrumb, not the page.
_EVIDENCE_MAX = 400
_SENTENCE_END = re.compile(r"[.!?](?=[ \n\"')\]]|$)|\n")


def _sentence_around(text: str, start: int, end: int) -> str:
    """The sentence containing ``[start:end]``, as a reader would quote it.

    An APPROXIMATION on purpose, and the docstring says so where the caller can
    see it: the boundary is a terminator followed by a space or a newline, which
    ``e.g.`` and ``No. 4`` both defeat. This is evidence for a person to read,
    not a parse anything branches on — over-long is recoverable and a wrong
    branch is not, so the window is capped rather than made clever.
    """
    left = 0
    for m in _SENTENCE_END.finditer(text, 0, start):
        left = m.end()
    right = len(text)
    tail = _SENTENCE_END.search(text, end)
    if tail:
        right = tail.end()
    left = max(left, end - _EVIDENCE_MAX)
    right = min(right, start + _EVIDENCE_MAX)
    return text[left:right].strip()


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
        # is a bundle of things to chase, and a numeric segment is one of them.
        #
        # The width range is the bare one (>= _APP_ID_BARE_MIN_WIDTH), not the
        # cued one, even though the match IS marked cued: this pass scans EVERY
        # segment rather than reading position 3, which is where the naming
        # convention actually puts the application id
        # (knowledge/standards/technology/folder-naming-convention.md). "A numeric
        # segment somewhere in a folder name" is a weaker claim than "the prose
        # said seal", so a 4-digit segment here is a year or a sequence number as
        # readily as an id. Enforce the position and 4 can come back.
        offset = m.start() + len(parsed.prefix) + 1
        for seg in parsed.segments:
            if seg.isdigit() and _APP_ID_BARE_MIN_WIDTH <= len(seg) <= _APP_ID_MAX_WIDTH:
                out.append(
                    EntityMatch(
                        APPLICATION_ID,
                        seg,
                        offset,
                        offset + len(seg),
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
        # The floor, and the only place a candidate is dropped: an uncued run
        # narrower than 5 digits is not reported. Not claimed either — a `2026`
        # left unclaimed here is a `2026` a later pass could still read, and the
        # bare pass is the last one, so the span simply stays free.
        if not cued and len(m.group(0)) < _APP_ID_BARE_MIN_WIDTH:
            continue
        attrs: tuple[tuple[str, str], ...] = ()
        if cued:
            attrs = (("cue", "landing-prefix" if _APP_ID_CUE_AFTER.match(after) else "keyword"),)
        take(
            EntityMatch(APPLICATION_ID, m.group(0), m.start(), m.end(), cued=cued, attributes=attrs)
        )

    # 7. acronym — last, so every narrower class has already claimed its spans
    for m in _ACRONYM_RE.finditer(text):
        if _overlaps(m.start(), m.end(), claimed):
            continue
        value = m.group(0)
        before = text[max(0, m.start() - _ACRONYM_GLOSS_WINDOW) : m.start()]
        after = text[m.end() : m.end() + _ACRONYM_GLOSS_WINDOW]
        gloss = None
        if (bracket := _ACRONYM_GLOSS_BEFORE.search(before)) is not None:
            gloss = bracket.group(1).strip()
        elif (paren := _ACRONYM_GLOSS_AFTER.match(after)) is not None:
            gloss = paren.group(1).strip()
        cued = gloss is not None or _ACRONYM_NAMING_VERB.match(after) is not None
        # The function-word floor, and the ONLY place an acronym candidate is
        # dropped. Uncued and closed-class: not reported, and not claimed either
        # — nothing runs after this pass, so the span simply stays free.
        if not cued and value in _ACRONYM_FUNCTION_WORDS:
            continue
        attrs = (("evidence", _sentence_around(text, m.start(), m.end())),)
        if gloss:
            attrs += (("gloss", gloss),)
        take(EntityMatch(ACRONYM, value, m.start(), m.end(), cued=cued, attributes=attrs))

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
