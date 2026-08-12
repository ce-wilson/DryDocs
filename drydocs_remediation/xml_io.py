"""Lossless Control-M definition-XML I/O — locate, splice, never re-serialize.

THE ONE IDEA. ``fix-package.md`` §XML requires the emitted ``<folder>.updated.xml``
to diff against the original by exactly the approved changes. No DOM serializer can
deliver that: measured on this repo's own fixture style (venv 3.13.3), both
``ElementTree`` and lxml rebuild each start tag from an attribute dict, collapsing
multi-line attribute wrapping onto one line — the "100%-diff file no developer can
review" that §XML rule 1 forbids — and ElementTree additionally drops DOCTYPE,
comments, quote style, and escapes literal ``>``. So this module **parses only to
LOCATE**: ``xml.parsers.expat`` supplies byte offsets (``CurrentByteIndex``), a
small start-tag lexer turns each tag into attribute spans, and emission is the
original bytes with N non-overlapping ranges replaced. Everything outside an edit
span is *copied*, so §XML rule 2 (preserve unknown elements/attributes and sibling
order) holds by construction — ``INCOND``/``OUTCOND``/``ON``/``CAPTURE``/calendars
survive because nobody ever rewrites them, not because we modeled them.

WHAT THIS DISSOLVES. ``XmlDefinitionFormat.dump`` was blocked on the vendor
schema (``Folder.xsd``, 403-blocked acquisition) because emitting XML meant
authoring element shapes from memory. Splicing authors nothing: the output is the
vendor's own file with attribute *values* changed. The residual risk is honest and
recorded: we can prove the emitted file differs from a Control-M-produced file by
exactly the approved bytes — not that Control-M will re-import it; the acquired
``.dtd``/``.xsd`` (see ``module-requirements.md``) is what upgrades that.

BOUNDARIES. Stdlib + ``drydocs_core`` + ``.formats`` only — no lxml (that is the
*validator's* dependency, never the emitter's), no ``drydocs_lineage`` (component
boundary); the tag/attribute vocabulary is shared through
``drydocs_core.orchestration.controlm.xml_vocab``. Byte-mode I/O throughout;
ASCII-superset encodings only — UTF-16 is refused (``UnsupportedEncoding``)
because byte-offset lexing is unsound there.

The projection ``to_definition_set`` is POSITION-FAITHFUL: a nameless or
malformed ``VARIABLE`` is kept (``name=""``) so list index equals document
ordinal. The lineage extractor deliberately skips-and-counts those; an editor
cannot, because a locator that miscounts edits the wrong line.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from xml.parsers import expat

from drydocs_core.orchestration.controlm.xml_vocab import (
    DESCRIPTION_ATTRS,
    FOLDER_NAME_ATTRS,
    FOLDER_TAGS,
    NOTIFICATION_TAGS,
    POSTCMD_ATTRS,
    SCAN_STOP_TAGS,
    SUBFOLDER_NAME_ATTRS,
    SUBFOLDER_TAGS,
    WATCH_ATTRS,
)

from .formats import DefinitionSet, FolderDefinition, JobDefinition, ScopeLayer

# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #


class XmlIoError(RuntimeError):
    """Base for every xml_io failure."""


class UnsupportedEncoding(XmlIoError):
    """The document's encoding cannot be byte-offset-lexed (UTF-16/32) or is unknown."""


class MalformedXml(XmlIoError):
    """expat rejected the document; position carried in the message."""


class LocatorNotFound(XmlIoError):
    """A Locator matched nothing."""


class NoTemplateSibling(XmlIoError):
    """An element insert found no same-tag element to clone style from.

    Splicing never authors XML shapes; without a template the insert would be
    an invented element — Tier-2/HITL territory, not a mechanical edit.
    """


class SelfCheckFailed(XmlIoError):
    """The emitted document does not diff by exactly the intended changes.

    Carries the full :class:`SelfCheckReport`; nothing was written.
    """

    def __init__(self, report: "SelfCheckReport") -> None:
        self.report = report
        super().__init__(report.summary())


class AmbiguousLocator(XmlIoError):
    """A Locator matched more than one node and carried no ordinal.

    Never resolved by "first wins": §VARS makes duplicate (job, variable)
    definitions a first-class change kind, so picking silently would edit
    the wrong line.
    """


# --------------------------------------------------------------------------- #
# Spans and the located tree
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Span:
    """Half-open byte range [start, end) into :attr:`XmlDocument.source`."""

    start: int
    end: int

    def slice(self, source: bytes) -> bytes:
        return source[self.start : self.end]


@dataclass(frozen=True)
class AttrSlot:
    """One attribute occurrence with every byte fact an editor needs."""

    name: str
    value: str  # unescaped, decoded
    name_span: Span
    value_span: Span  # strictly inside the quotes
    quote: str  # '"' or "'"
    slot_span: Span  # leading separator + NAME="value" — removable as a unit
    #: byte spans of `&...;` reference regions inside value_span (document-absolute).
    #: Non-empty means token-level splicing inside this value is unsafe.
    ref_spans: tuple[Span, ...] = ()


@dataclass
class XmlNode:
    """One element, located. ``attrs`` is document order, duplicates preserved."""

    tag: str
    attrs: list[AttrSlot] = field(default_factory=list)
    children: list["XmlNode"] = field(default_factory=list)
    parent: "XmlNode | None" = field(default=None, repr=False)
    span: Span = Span(0, 0)  # '<' .. past '/>' or '</tag>'
    start_tag_span: Span = Span(0, 0)  # '<' .. past '>'
    empty: bool = False  # self-closed IN THE SOURCE
    path: str = ""  # "/DEFTABLE/SMART_FOLDER[0]/JOB[1]"
    line: int = 0

    def attr(self, *names: str) -> AttrSlot | None:
        """First attribute matching any of ``names`` (synonym-aware, first hit wins)."""
        for name in names:
            for slot in self.attrs:
                if slot.name == name:
                    return slot
        return None

    def attr_value(self, *names: str) -> str:
        slot = self.attr(*names)
        return slot.value.strip() if slot is not None else ""

    def iter(self):
        """This node and every descendant, document order."""
        yield self
        for child in self.children:
            yield from child.iter()


@dataclass
class XmlDocument:
    """A parsed definition export: the source bytes ARE the model of record;
    the tree is an index into them."""

    source: bytes
    encoding: str
    newline: bytes  # b"\n" | b"\r\n", detected
    bom: bytes
    root: XmlNode
    origin: Path | None = None


# --------------------------------------------------------------------------- #
# Encoding — refuse what byte-offset lexing cannot handle
# --------------------------------------------------------------------------- #

#: BOMs whose presence makes byte-offset lexing unsound. Checked longest-first
#: (UTF-32 LE starts with the UTF-16 LE bytes).
_HOSTILE_BOMS = (
    (b"\xff\xfe\x00\x00", "utf-32-le"),
    (b"\x00\x00\xfe\xff", "utf-32-be"),
    (b"\xff\xfe", "utf-16-le"),
    (b"\xfe\xff", "utf-16-be"),
)
_UTF8_BOM = b"\xef\xbb\xbf"

_DECL_ENCODING_RE = re.compile(rb'<\?xml[^>]*?encoding\s*=\s*["\']([A-Za-z0-9._-]+)["\']')

#: declared-name -> (python codec for VALUE decoding, encoding expat parses AS).
#: windows-125x are ASCII supersets whose every byte decodes under iso-8859-1,
#: so expat lexes them safely at that setting while values decode with the real
#: codec. ``ParserCreate(encoding=...)`` overrides the declaration, which is what
#: makes this trick sound.
_ENCODINGS: dict[str, tuple[str, str]] = {
    "utf-8": ("utf-8", "utf-8"),
    "us-ascii": ("ascii", "us-ascii"),
    "ascii": ("ascii", "us-ascii"),
    "iso-8859-1": ("iso-8859-1", "iso-8859-1"),
    "latin-1": ("iso-8859-1", "iso-8859-1"),
    "windows-1250": ("cp1250", "iso-8859-1"),
    "windows-1251": ("cp1251", "iso-8859-1"),
    "windows-1252": ("cp1252", "iso-8859-1"),
    "windows-1254": ("cp1254", "iso-8859-1"),
    "windows-1256": ("cp1256", "iso-8859-1"),
}


def _detect_encoding(source: bytes) -> tuple[str, str, bytes]:
    """(declared name, python codec, bom) — or raise :class:`UnsupportedEncoding`."""
    for bom, name in _HOSTILE_BOMS:
        if source.startswith(bom):
            raise UnsupportedEncoding(
                f"{name} (BOM detected): byte-offset lexing is unsound for "
                "multi-byte-unit encodings — re-encode the export as UTF-8"
            )
    bom = _UTF8_BOM if source.startswith(_UTF8_BOM) else b""
    match = _DECL_ENCODING_RE.search(source[:256])
    declared = match.group(1).decode("ascii").lower() if match else "utf-8"
    if declared not in _ENCODINGS:
        raise UnsupportedEncoding(
            f"declared encoding {declared!r} is not a supported ASCII superset "
            f"(supported: {', '.join(sorted(_ENCODINGS))})"
        )
    codec, _ = _ENCODINGS[declared]
    return declared, codec, bom


# --------------------------------------------------------------------------- #
# Entity handling — values decode, spans stay byte-true
# --------------------------------------------------------------------------- #

_ENTITY_RE = re.compile(rb"&(?:#x[0-9A-Fa-f]+|#[0-9]+|amp|lt|gt|quot|apos);")
_NAMED = {b"&amp;": "&", b"&lt;": "<", b"&gt;": ">", b"&quot;": '"', b"&apos;": "'"}


def _unescape(raw: bytes, codec: str, base: int) -> tuple[str, tuple[Span, ...]]:
    """Decode one attribute value's raw bytes.

    Returns the unescaped text and the document-absolute spans of every
    entity/char-ref region — the regions token-level splices must not cross,
    because offsets are not stable through decoding.
    """
    out: list[str] = []
    refs: list[Span] = []
    pos = 0
    for match in _ENTITY_RE.finditer(raw):
        out.append(raw[pos : match.start()].decode(codec))
        token = match.group(0)
        if token in _NAMED:
            out.append(_NAMED[token])
        elif token[:3] == b"&#x":
            out.append(chr(int(token[3:-1], 16)))
        else:
            out.append(chr(int(token[2:-1])))
        refs.append(Span(base + match.start(), base + match.end()))
        pos = match.end()
    out.append(raw[pos:].decode(codec))
    return "".join(out), tuple(refs)


def escape_attr_value(value: str, quote: str, codec: str) -> bytes:
    """Minimal, quote-aware escaping for a value being spliced in.

    Escapes ``&``, ``<``, the DELIMITER quote, and control whitespace (as
    numeric refs). Deliberately does NOT escape ``>`` or the other quote —
    gratuitous escaping is a byte diff on a line nobody approved.
    Characters outside the target codec are escaped as numeric refs rather
    than failing, so an edit can always land.
    """
    out: list[bytes] = []
    for ch in value:
        if ch == "&":
            out.append(b"&amp;")
        elif ch == "<":
            out.append(b"&lt;")
        elif ch == quote:
            out.append(b"&quot;" if quote == '"' else b"&apos;")
        elif ch in ("\n", "\r", "\t"):
            out.append(f"&#{ord(ch)};".encode("ascii"))
        else:
            try:
                out.append(ch.encode(codec))
            except UnicodeEncodeError:
                out.append(f"&#{ord(ch)};".encode("ascii"))
    return b"".join(out)


# --------------------------------------------------------------------------- #
# The start-tag lexer — spans for every attribute, style facts for edits
# --------------------------------------------------------------------------- #

_WS = b" \t\r\n"


def _lex_start_tag(source: bytes, start: int, codec: str) -> tuple[list[AttrSlot], int, bool]:
    """Lex one start tag beginning at ``source[start] == '<'``.

    Returns (attribute slots, offset just past '>', self-closing?). Structure
    bytes are ASCII in every supported encoding, so byte-wise lexing is exact.
    expat has already accepted the document, so this lexer may assume
    well-formedness and only needs to FIND things, not validate them.
    """
    i = start + 1
    n = len(source)
    while i < n and source[i : i + 1] not in _WS and source[i] not in (ord(">"), ord("/")):
        i += 1  # tag name
    slots: list[AttrSlot] = []
    while i < n:
        sep_start = i
        while i < n and source[i : i + 1] in _WS:
            i += 1
        if source[i] == ord(">"):
            return slots, i + 1, False
        if source[i] == ord("/"):  # '/>' — well-formedness guarantees the '>'
            return slots, i + 2, True
        name_start = i
        while i < n and source[i] not in (ord("="), ord(">"), ord("/")) and source[i : i + 1] not in _WS:
            i += 1
        name_span = Span(name_start, i)
        while i < n and source[i : i + 1] in _WS:
            i += 1
        i += 1  # '='
        while i < n and source[i : i + 1] in _WS:
            i += 1
        quote = source[i : i + 1]
        value_start = i + 1
        value_end = source.index(quote, value_start)  # delimiter can't appear unescaped
        i = value_end + 1
        value, refs = _unescape(source[value_start:value_end], codec, value_start)
        slots.append(
            AttrSlot(
                name=source[name_start : name_span.end].decode("ascii"),
                value=value,
                name_span=name_span,
                value_span=Span(value_start, value_end),
                quote=quote.decode("ascii"),
                slot_span=Span(sep_start, i),
                ref_spans=refs,
            )
        )
    raise MalformedXml(f"unterminated start tag at byte {start}")  # pragma: no cover


# --------------------------------------------------------------------------- #
# load / render
# --------------------------------------------------------------------------- #


def load_document(src: Path | bytes, *, origin: Path | None = None) -> XmlDocument:
    """Parse a definition export into a located tree over its own bytes."""
    if isinstance(src, Path):
        origin = origin or src
        source = src.read_bytes()
    else:
        source = src
    declared, codec, bom = _detect_encoding(source)
    parser = expat.ParserCreate(encoding=_ENCODINGS[declared][1])
    # DTDs: never load external ones; the internal subset is preserved as bytes anyway.
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)

    root: XmlNode | None = None
    stack: list[XmlNode] = []
    tag_counts: list[dict[str, int]] = [{}]

    def start_element(name: str, _attrs: dict[str, str]) -> None:
        nonlocal root
        offset = parser.CurrentByteIndex
        slots, tag_end, empty = _lex_start_tag(source, offset, codec)
        counts = tag_counts[-1]
        ordinal = counts.get(name, 0)
        counts[name] = ordinal + 1
        parent = stack[-1] if stack else None
        node = XmlNode(
            tag=name,
            attrs=slots,
            parent=parent,
            span=Span(offset, tag_end),  # provisional; end event finalizes paired tags
            start_tag_span=Span(offset, tag_end),
            empty=empty,
            path=(parent.path if parent else "") + f"/{name}[{ordinal}]",
            line=parser.CurrentLineNumber,
        )
        if parent is not None:
            parent.children.append(node)
        else:
            root = node
        stack.append(node)
        tag_counts.append({})

    def end_element(_name: str) -> None:
        node = stack.pop()
        tag_counts.pop()
        if not node.empty:
            # end event points at '</'; span runs past the closing '>'
            close = parser.CurrentByteIndex
            node.span = Span(node.span.start, source.index(b">", close) + 1)

    parser.StartElementHandler = start_element
    parser.EndElementHandler = end_element
    try:
        parser.Parse(source, True)
    except expat.ExpatError as exc:
        raise MalformedXml(str(exc)) from exc
    if root is None:  # pragma: no cover - expat errors first
        raise MalformedXml("no root element")
    return XmlDocument(
        source=source,
        encoding=declared,
        newline=b"\r\n" if b"\r\n" in source else b"\n",
        bom=bom,
        root=root,
        origin=origin,
    )


@dataclass(frozen=True)
class Edit:
    """One compiled splice: replace ``span`` with ``replacement``."""

    span: Span
    replacement: bytes
    change_id: str
    description: str = ""


def render(doc: XmlDocument, edits: list[Edit] | None = None) -> bytes:
    """The original bytes with the edits spliced in. No edits → the source,
    byte for byte: that identity is the module's thesis and test class A."""
    if not edits:
        return doc.source
    ordered = sorted(edits, key=lambda e: (e.span.start, e.span.end))
    for prev, cur in zip(ordered, ordered[1:], strict=False):
        if cur.span.start < prev.span.end:
            raise XmlIoError(
                f"overlapping edits: {prev.change_id!r} [{prev.span.start},{prev.span.end}) "
                f"and {cur.change_id!r} [{cur.span.start},{cur.span.end})"
            )
    out: list[bytes] = []
    pos = 0
    for edit in ordered:
        out.append(doc.source[pos : edit.span.start])
        out.append(edit.replacement)
        pos = edit.span.end
    out.append(doc.source[pos:])
    return b"".join(out)


# --------------------------------------------------------------------------- #
# Locator — domain coordinates, never someone else's list index
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Locator:
    """Address one element by Control-M coordinates.

    ``ordinal`` disambiguates duplicates; ``None`` means "must be unique" and
    more than one match raises :class:`AmbiguousLocator`.
    """

    folder: str
    subfolder_path: str = ""
    job: str = ""
    element: str = ""  # e.g. "VARIABLE"; "" addresses the container itself
    name: str = ""  # the element's NAME attribute, verbatim with %%
    ordinal: int | None = None


def _folder_nodes(doc: XmlDocument) -> list[XmlNode]:
    return [n for n in doc.root.children if n.tag.upper() in FOLDER_TAGS]


def _subfolder_name(node: XmlNode) -> str:
    return node.attr_value(*SUBFOLDER_NAME_ATTRS)


def locate(doc: XmlDocument, loc: Locator) -> XmlNode:
    """Resolve a :class:`Locator` to exactly one node."""
    containers = [n for n in _folder_nodes(doc) if n.attr_value(*FOLDER_NAME_ATTRS) == loc.folder]
    if not containers:
        raise LocatorNotFound(f"folder {loc.folder!r} not in document")
    if len(containers) > 1:
        raise AmbiguousLocator(f"folder {loc.folder!r} appears {len(containers)} times")
    node = containers[0]
    for part in filter(None, loc.subfolder_path.split("/")):
        subs = [
            c for c in node.children if c.tag.upper() in SUBFOLDER_TAGS and _subfolder_name(c) == part
        ]
        if not subs:
            raise LocatorNotFound(f"sub-folder {part!r} not under {node.path}")
        if len(subs) > 1:
            raise AmbiguousLocator(f"sub-folder {part!r} appears {len(subs)} times under {node.path}")
        node = subs[0]
    if loc.job:
        jobs = [c for c in node.children if c.tag.upper() == "JOB" and c.attr_value("JOBNAME") == loc.job]
        if not jobs:
            raise LocatorNotFound(f"job {loc.job!r} not under {node.path}")
        if len(jobs) > 1:
            # ordinal disambiguates the INNERMOST coordinate; when an element
            # lookup follows, it belongs to the element, so a duplicated job
            # cannot be resolved past.
            if loc.element or loc.ordinal is None:
                raise AmbiguousLocator(
                    f"job {loc.job!r} appears {len(jobs)} times under {node.path}"
                    + ("; give ordinal" if not loc.element else " — element lookup needs a unique job")
                )
            if loc.ordinal >= len(jobs):
                raise LocatorNotFound(
                    f"job {loc.job!r} ordinal {loc.ordinal} out of range ({len(jobs)} matches)"
                )
            node = jobs[loc.ordinal]
        else:
            node = jobs[0]
    if not loc.element:
        return node
    matches = [
        c
        for c in node.children
        if c.tag.upper() == loc.element.upper()
        and (not loc.name or c.attr_value("NAME") == loc.name)
    ]
    if not matches:
        raise LocatorNotFound(f"{loc.element}[NAME={loc.name!r}] not under {node.path}")
    if loc.ordinal is not None:
        if loc.ordinal >= len(matches):
            raise LocatorNotFound(
                f"{loc.element}[NAME={loc.name!r}] ordinal {loc.ordinal} out of range "
                f"({len(matches)} matches under {node.path})"
            )
        return matches[loc.ordinal]
    if len(matches) > 1:
        raise AmbiguousLocator(
            f"{loc.element}[NAME={loc.name!r}] matches {len(matches)} elements under "
            f"{node.path} — duplicates are a first-class change kind (§VARS); give ordinal"
        )
    return matches[0]


# --------------------------------------------------------------------------- #
# Projection — position-faithful DefinitionSet
# --------------------------------------------------------------------------- #


def _variables_of(node: XmlNode) -> list[tuple[str, str | None]]:
    """Direct VARIABLE children, document order, POSITION-FAITHFUL: a nameless
    or value-less VARIABLE stays in the list (name "", value None) so that list
    index == document ordinal. The lineage extractor skips-and-counts these;
    an editor must not, or its locators miscount."""
    out: list[tuple[str, str | None]] = []
    for child in node.children:
        if child.tag.upper() != "VARIABLE":
            continue
        name_slot = child.attr("NAME")
        value_slot = child.attr("VALUE")
        out.append(
            (
                name_slot.value.strip() if name_slot is not None else "",
                value_slot.value if value_slot is not None else None,
            )
        )
    return out


def _notifications_of(node: XmlNode) -> tuple[str, ...]:
    """Notification tags under ``node`` without descending into nested jobs or
    sub-folders — their notifications belong to THEM (mirrors the extractor)."""
    found: list[str] = []
    queue = list(node.children)
    while queue:
        child = queue.pop(0)
        tag = child.tag.upper()
        if tag in SCAN_STOP_TAGS:
            continue
        if tag in NOTIFICATION_TAGS and tag not in found:
            found.append(tag)
        queue = list(child.children) + queue
    return tuple(found)


def _project_job(
    node: XmlNode, chain_above: list[ScopeLayer], subfolder_path: str
) -> JobDefinition:
    own = _variables_of(node)
    name = node.attr_value("JOBNAME")
    watch = node.attr(*WATCH_ATTRS)
    return JobDefinition(
        name=name,
        job_type=node.attr_value("TASKTYPE") or None,
        variables=own,
        watch_template=watch.value if watch is not None else None,
        description=node.attr_value(*DESCRIPTION_ATTRS),
        command_line=node.attr_value("CMDLINE"),
        post_command=node.attr_value(*POSTCMD_ATTRS),
        notification_tags=_notifications_of(node),
        subfolder_path=subfolder_path,
        scope_chain=[*chain_above, ("JOB", name, own)],
    )


# --------------------------------------------------------------------------- #
# Effects, the edit script, and the self-check (§XML rules 3 + 4)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Effect:
    """One intended-or-observed structural consequence, comparable as a value.

    The self-check is a MULTISET comparison of intended vs observed effects,
    so both sides must normalize identically: element inserts/deletes carry
    the PARENT's path (an inserted node's own ordinal is unknowable at intent
    time), attribute effects carry the element's path.
    """

    kind: str  # attr-set | attr-add | attr-remove | element-insert | element-delete
    path: str
    detail: str  # attribute name, or inserted/deleted tag
    old: str | None = None
    new: str | None = None


class EditScript:
    """Accumulates attributed edits against one document.

    ``change_id`` is a REQUIRED keyword on every method: xml_io does not know
    what an approval is — ``changes.py`` owns that — but it is structurally
    incapable of producing an unattributed edit (§XML rule 3 enforced by the
    signature, not by review).
    """

    def __init__(self, doc: XmlDocument) -> None:
        self._doc = doc
        self._codec = _ENCODINGS[doc.encoding][0]
        self._edits: list[Edit] = []
        self._intended: list[Effect] = []
        #: effects already true in the source (set-to-same-value): recorded so
        #: re-running an approved change-set is idempotent instead of "missing".
        self.satisfied: list[Effect] = []

    # -- attribute edits ---------------------------------------------------- #

    def set_attribute(self, node: XmlNode, name: str, value: str, *, change_id: str) -> Effect:
        slot = node.attr(name)
        if slot is None:
            raise LocatorNotFound(
                f"{node.path} has no attribute {name!r} — use add_attribute for new ones"
            )
        effect = Effect("attr-set", node.path, name, old=slot.value, new=value)
        if slot.value == value:
            self.satisfied.append(effect)
            return effect
        self._edits.append(
            Edit(
                span=slot.value_span,
                replacement=escape_attr_value(value, slot.quote, self._codec),
                change_id=change_id,
                description=f"set {name} on {node.path}",
            )
        )
        self._intended.append(effect)
        return effect

    def add_attribute(
        self, node: XmlNode, name: str, value: str, *, change_id: str
    ) -> Effect:
        """Insert ``NAME="value"`` after the tag's last attribute, cloning that
        attribute's own leading separator — a wrapped tag wraps the new
        attribute at the same column; a one-line tag gets a single space."""
        if node.attr(name) is not None:
            raise XmlIoError(f"{node.path} already has {name!r} — use set_attribute")
        source = self._doc.source
        if node.attrs:
            last = node.attrs[-1]
            sep = last.slot_span.slice(source)[: last.name_span.start - last.slot_span.start]
            pos = last.slot_span.end
        else:
            sep = b" "
            pos = node.start_tag_span.end - (2 if node.empty else 1)
            while source[pos - 1 : pos] in (b" ", b"\t"):
                pos -= 1
        payload = sep + name.encode("ascii") + b'="' + escape_attr_value(value, '"', self._codec) + b'"'
        effect = Effect("attr-add", node.path, name, old=None, new=value)
        self._edits.append(
            Edit(Span(pos, pos), payload, change_id, f"add {name} on {node.path}")
        )
        self._intended.append(effect)
        return effect

    def remove_attribute(self, node: XmlNode, name: str, *, change_id: str) -> Effect:
        slot = node.attr(name)
        if slot is None:
            raise LocatorNotFound(f"{node.path} has no attribute {name!r}")
        effect = Effect("attr-remove", node.path, name, old=slot.value, new=None)
        self._edits.append(
            Edit(slot.slot_span, b"", change_id, f"remove {name} on {node.path}")
        )
        self._intended.append(effect)
        return effect

    # -- element edits ------------------------------------------------------ #

    def _template_for(self, parent: XmlNode, tag: str) -> XmlNode:
        """Style template: prefer a same-tag child of ``parent``, else any
        same-tag element in the document. No template → refuse: inventing an
        element shape is exactly what splicing exists to avoid."""
        for child in parent.children:
            if child.tag == tag:
                return child
        for node in self._doc.root.iter():
            if node.tag == tag:
                return node
        raise NoTemplateSibling(
            f"no <{tag}> element anywhere in the document to clone style from — "
            "inserting one would author an element shape (HITL, not mechanical)"
        )

    def _indent_of(self, node: XmlNode) -> bytes:
        """The whitespace run between the preceding newline and the node."""
        source = self._doc.source
        i = node.span.start
        j = i
        while j > 0 and source[j - 1 : j] in (b" ", b"\t"):
            j -= 1
        return source[j:i]

    def insert_element(
        self,
        parent: XmlNode,
        tag: str,
        attrs: list[tuple[str, str]],
        *,
        after: XmlNode | None = None,
        change_id: str,
    ) -> Effect:
        """Insert a new element as a child of ``parent``, cloned in style from
        an existing same-tag element (indentation and empty-tag form)."""
        if parent.empty:
            raise XmlIoError(
                f"{parent.path} is self-closed; converting it to a paired tag is "
                "not a mechanical edit (HITL)"
            )
        template = self._template_for(parent, tag)
        indent = self._indent_of(template)
        closer = self._doc.source[template.start_tag_span.end - 3 : template.start_tag_span.end]
        empty_form = b" />" if template.empty and closer == b" />" else b"/>"
        body = b" ".join(
            name.encode("ascii") + b'="' + escape_attr_value(value, '"', self._codec) + b'"'
            for name, value in attrs
        )
        element = b"<" + tag.encode("ascii") + (b" " + body if body else b"") + empty_form
        if after is not None:
            pos = after.span.end
        elif parent.children:
            pos = parent.children[-1].span.end
        else:
            pos = parent.start_tag_span.end
        payload = self._doc.newline + indent + element
        name_attr = next((v for n, v in attrs if n == "NAME"), "")
        effect = Effect("element-insert", parent.path, tag, old=None, new=name_attr)
        self._edits.append(Edit(Span(pos, pos), payload, change_id, f"insert <{tag}> under {parent.path}"))
        self._intended.append(effect)
        return effect

    def delete_element(self, node: XmlNode, *, change_id: str) -> Effect:
        """Delete an element, extending backwards over the whitespace-only run
        up to and including the preceding newline so no blank line is left."""
        source = self._doc.source
        start = node.span.start
        j = start
        while j > 0 and source[j - 1 : j] in (b" ", b"\t"):
            j -= 1
        if source[j - 1 : j] == b"\n":
            j -= 1
            if source[j - 1 : j] == b"\r":
                j -= 1
        effect = Effect(
            "element-delete",
            node.parent.path if node.parent else "",
            node.tag,
            old=node.attr_value("NAME") or None,
            new=None,
        )
        self._edits.append(
            Edit(Span(j, node.span.end), b"", change_id, f"delete <{node.tag}> at {node.path}")
        )
        self._intended.append(effect)
        return effect

    # -- compile ------------------------------------------------------------ #

    def compile(self) -> list[Edit]:
        """Sorted, overlap-checked edits. Overlaps raise here (render re-checks)."""
        ordered = sorted(self._edits, key=lambda e: (e.span.start, e.span.end))
        for prev, cur in zip(ordered, ordered[1:], strict=False):
            if cur.span.start < prev.span.end:
                raise XmlIoError(
                    f"overlapping edits: {prev.description!r} and {cur.description!r}"
                )
        return ordered

    @property
    def intended_effects(self) -> list[Effect]:
        return list(self._intended)


# --------------------------------------------------------------------------- #
# Structural diff + self-check
# --------------------------------------------------------------------------- #


def _signature(node: XmlNode) -> tuple[str, str]:
    """Alignment key for sibling matching: tag + NAME (the Control-M identity
    attribute where one exists). Deliberately excludes other attribute values
    so an attr-set does not read as delete+insert."""
    return (node.tag, node.attr_value("NAME"))


def _diff_attrs(before: XmlNode, after: XmlNode, effects: list[Effect]) -> None:
    before_names = [a.name for a in before.attrs]
    after_names = [a.name for a in after.attrs]
    common = [n for n in before_names if n in after_names]
    common_after = [n for n in after_names if n in before_names]
    if common != common_after:
        raise SelfCheckFailed(
            SelfCheckReport(
                unexpected=[Effect("attr-reorder", before.path, ",".join(after_names))],
                missing=[],
            )
        )
    before_map = {a.name: a.value for a in before.attrs}
    after_map = {a.name: a.value for a in after.attrs}
    for name in before_names:
        if name not in after_map:
            effects.append(Effect("attr-remove", before.path, name, old=before_map[name], new=None))
        elif before_map[name] != after_map[name]:
            effects.append(
                Effect("attr-set", before.path, name, old=before_map[name], new=after_map[name])
            )
    for name in after_names:
        if name not in before_map:
            effects.append(Effect("attr-add", before.path, name, old=None, new=after_map[name]))


def _diff_children(before: XmlNode, after: XmlNode, effects: list[Effect]) -> None:
    from difflib import SequenceMatcher

    b_sigs = [_signature(c) for c in before.children]
    a_sigs = [_signature(c) for c in after.children]
    matcher = SequenceMatcher(a=b_sigs, b=a_sigs, autojunk=False)
    deleted: list[tuple[str, str]] = []
    inserted: list[tuple[str, str]] = []
    for op, b1, b2, a1, a2 in matcher.get_opcodes():
        if op == "equal":
            for offset in range(b2 - b1):
                _diff_node(before.children[b1 + offset], after.children[a1 + offset], effects)
        elif (
            op == "replace"
            and (b2 - b1) == (a2 - a1)
            and all(
                before.children[b1 + k].tag == after.children[a1 + k].tag
                for k in range(b2 - b1)
            )
        ):
            # Same count, same tags, same position: these are the SAME elements
            # whose identity attribute changed (e.g. a ratified rename rewriting
            # VARIABLE NAME) — an attr-set, not a delete+insert.
            for offset in range(b2 - b1):
                _diff_node(before.children[b1 + offset], after.children[a1 + offset], effects)
        else:
            for child in before.children[b1:b2]:
                deleted.append(_signature(child))
                effects.append(
                    Effect(
                        "element-delete",
                        before.path,
                        child.tag,
                        old=child.attr_value("NAME") or None,
                        new=None,
                    )
                )
            for child in after.children[a1:a2]:
                inserted.append(_signature(child))
                effects.append(
                    Effect(
                        "element-insert",
                        before.path,
                        child.tag,
                        old=None,
                        new=child.attr_value("NAME"),
                    )
                )
    reordered = set(deleted) & set(inserted)
    if reordered:
        raise SelfCheckFailed(
            SelfCheckReport(
                unexpected=[
                    Effect("sibling-reorder", before.path, f"{tag}[NAME={name!r}]")
                    for tag, name in sorted(reordered)
                ],
                missing=[],
            )
        )


def _diff_node(before: XmlNode, after: XmlNode, effects: list[Effect]) -> None:
    if before.tag != after.tag:
        raise SelfCheckFailed(
            SelfCheckReport(
                unexpected=[Effect("tag-rename", before.path, f"{before.tag}->{after.tag}")],
                missing=[],
            )
        )
    _diff_attrs(before, after, effects)
    _diff_children(before, after, effects)


def structural_diff(before: XmlDocument, after: XmlDocument) -> list[Effect]:
    """Every structural difference between two documents as typed effects.

    Tag renames and sibling reorders raise immediately: no approved change
    kind can produce them, so observing one means the splicer corrupted the
    document — that is not a diff to report, it is an abort.
    """
    effects: list[Effect] = []
    _diff_node(before.root, after.root, effects)
    return effects


@dataclass
class SelfCheckReport:
    """What §XML rule 4 saw. ``ok`` only when the emitted file's structural
    diff equals exactly the intended change list and every post-condition holds."""

    unexpected: list[Effect] = field(default_factory=list)
    missing: list[Effect] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    changed_line_numbers: list[int] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.unexpected and not self.missing and not self.violations

    def summary(self) -> str:
        parts = []
        if self.unexpected:
            parts.append(f"{len(self.unexpected)} unexpected effect(s): {self.unexpected[:3]}")
        if self.missing:
            parts.append(f"{len(self.missing)} intended effect(s) missing: {self.missing[:3]}")
        if self.violations:
            parts.append(
                f"{len(self.violations)} post-condition violation(s): {self.violations[:3]}"
            )
        return "; ".join(parts) or "ok"


def self_check(
    doc: XmlDocument, script: EditScript, emitted: bytes
) -> SelfCheckReport:
    """§XML rule 4: the emitted document must diff by exactly the intended list."""
    from collections import Counter
    from difflib import unified_diff

    report = SelfCheckReport()
    try:
        after = load_document(emitted, origin=doc.origin)
    except XmlIoError as exc:
        report.violations.append(f"emitted document does not re-parse: {exc}")
        return report
    observed = Counter(structural_diff(doc, after))
    intended = Counter(script.intended_effects)
    report.unexpected = list((observed - intended).elements())
    report.missing = list((intended - observed).elements())

    newline = doc.newline.decode("ascii")
    before_lines = doc.source.split(doc.newline)
    after_lines = emitted.split(doc.newline)
    lineno = 0
    for line in unified_diff(
        [line.decode(_ENCODINGS[doc.encoding][0], "replace") for line in before_lines],
        [line.decode(_ENCODINGS[doc.encoding][0], "replace") for line in after_lines],
        lineterm=newline,
        n=0,
    ):
        if line.startswith("@@"):
            lineno = int(line.split(" ")[1].lstrip("-").split(",")[0])
        elif line.startswith("-") and not line.startswith("---"):
            report.changed_line_numbers.append(lineno)
            lineno += 1
    return report


def write(
    doc: XmlDocument,
    script: EditScript,
    target: Path,
) -> SelfCheckReport:
    """Render, self-check FILE-TO-FILE, and only then let the file stand.

    File-to-file is what makes layer 1 non-tautological: the bytes are read
    back from disk, so an accidental text-mode open, BOM strip, or newline
    translation fails here instead of in the developer's diff.
    """
    emitted = render(doc, script.compile())
    tmp = target.with_suffix(target.suffix + ".selfcheck-tmp")
    tmp.write_bytes(emitted)
    try:
        read_back = tmp.read_bytes()
        report = self_check(doc, script, read_back)
        if read_back != emitted:  # pragma: no cover - binary I/O is exact
            report.violations.append("file round-trip altered bytes (I/O mode bug)")
        if not report.ok:
            raise SelfCheckFailed(report)
        tmp.replace(target)
    finally:
        tmp.unlink(missing_ok=True)
    return report


def to_definition_set(doc: XmlDocument) -> DefinitionSet:
    """Project the located tree into the format-agnostic currency.

    Curated fields only — everything the model does not carry stays in
    ``doc.source`` and survives emission untouched. Sub-folders become
    ``FolderDefinition(scope="SUBFOLDER")`` entries named ``folder/path``,
    mirroring the xml_bridge convention so the two entry paths agree.
    """
    definitions = DefinitionSet(source=str(doc.origin) if doc.origin else "<bytes>")

    def walk(container: XmlNode, folder_name: str, chain: list[ScopeLayer], path: str) -> None:
        for child in container.children:
            tag = child.tag.upper()
            if tag == "JOB":
                definitions.jobs.append(_project_job(child, chain, path))
            elif tag in SUBFOLDER_TAGS:
                sub_name = _subfolder_name(child)
                sub_path = f"{path}/{sub_name}" if path else sub_name
                sub_vars = _variables_of(child)
                definitions.folders.append(
                    FolderDefinition(
                        name=f"{folder_name}/{sub_path}",
                        variables=sub_vars,
                        scope="SUBFOLDER",
                        description=child.attr_value(*DESCRIPTION_ATTRS),
                        notification_tags=_notifications_of(child),
                    )
                )
                walk(child, folder_name, [*chain, ("SUBFOLDER", sub_path, sub_vars)], sub_path)

    for folder in _folder_nodes(doc):
        folder_name = folder.attr_value(*FOLDER_NAME_ATTRS)
        folder_vars = _variables_of(folder)
        definitions.folders.append(
            FolderDefinition(
                name=folder_name,
                variables=folder_vars,
                scope="FOLDER",
                description=folder.attr_value(*DESCRIPTION_ATTRS),
                notification_tags=_notifications_of(folder),
            )
        )
        walk(folder, folder_name, [("FOLDER", folder_name, folder_vars)], "")

    return definitions
