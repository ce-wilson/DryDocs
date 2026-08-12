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
