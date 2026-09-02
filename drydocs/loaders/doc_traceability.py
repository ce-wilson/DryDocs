"""Doc-traceability loaders — the L7 connector-#1 chain (gate
doc-traceability-feedback signed off 2026-07-20 — config/gate-log.md).

DryDocs documenting itself ("tenant 0"): three deterministic, offline parses
of repo-committed artifacts, three BaseLoader passes in a fixed order —

1. :class:`DesignDocSectionsLoader`  — docs/design/*.md → :DesignDoc +
   :DocSection + PART_OF (every authored anchor, matrix or not — the runbook
   loads here too).
2. :class:`DocTraceabilityLoader`    — the requirements-traceability matrix
   rows → :Requirement + :Component + :TestCase + the star (SPECIFIED_IN /
   IMPLEMENTED_BY / VERIFIED_BY). Sections are MATCHed only (pass 1 first).
3. :class:`DocFeedbackLoader`        — docs/design/feedback/<doc>-rev<N>.yaml
   → :FeedbackNote + ANNOTATES (+ WAS_ATTRIBUTED_TO {role: feedback_author}
   when an author resolves to a real :Employee — never fabricated).

Parsing is stdlib + PyYAML only and reuses the Epic L anchor contract
(drydocs.docgen.doc_outline.ANCHOR_RE / DERIVED_ANCHOR_SEP). No LLM, no heuristic
beyond the documented cell-split + kind rules below — same determinism bar as
the render pipeline.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import yaml
from pydantic import BaseModel

from drydocs_core.doc_anchors import ANCHOR_RE, DERIVED_ANCHOR_SEP
from drydocs_core.models.doc_traceability import (
    DESIGN_DOCS_ORIGIN,
    DocSectionRow,
    FeedbackNoteRow,
    TraceabilityRow,
)
from drydocs_core.repo_paths import repo_root

from .base import BaseLoader, LoadSummary, compute_row_checksum

if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

    from drydocs_core.run_log import LoaderRunLog

LOGGER = logging.getLogger(__name__)

REPO_ROOT = repo_root(Path(__file__).resolve().parents[2])
CYPHER_DIR = Path(__file__).resolve().parent / "cypher"
DEFAULT_DESIGN_DIR = REPO_ROOT / "docs" / "design"
DEFAULT_FEEDBACK_DIR = DEFAULT_DESIGN_DIR / "feedback"

MATRIX_ANCHOR = "traceability-matrix"
TEST_KIND_RULE_ID = "kind-rule-v1"

# Front-matter facts — the SAME regex family the render pipeline keys on
# (drydocs.docgen.design_doc): Rev + commit for the print footer; DESCRIPTIVE /
# PRESCRIPTIVE is the Epic L status vocabulary.
_H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_REV_RE = re.compile(r"\bRev\s+(\d+)\b")
_COMMIT_RE = re.compile(r"commit\s+`([0-9a-f]{7,40})`")
_DOC_STATUS_RE = re.compile(r"\b(DESCRIPTIVE|PRESCRIPTIVE)\b")
_FEEDBACK_FILE_RE = re.compile(r"^(?P<doc_id>.+)-rev(?P<rev>\d+)\.ya?ml$")

#: stem-suffix → doc_type (deterministic; extend as new outline types land).
_DOC_TYPE_SUFFIXES = {
    "-tdd": "TDD",
    "-runbook": "Runbook",
    "-review": "Review",
    "-explainer": "Explainer",
}


def doc_type_for_stem(stem: str) -> str:
    for suffix, doc_type in _DOC_TYPE_SUFFIXES.items():
        if stem.endswith(suffix):
            return doc_type
    return "DesignDoc"


def _clean_ref(cell_fragment: str) -> str:
    """One citation token: trim whitespace and surrounding backticks."""
    return cell_fragment.strip().strip("`").strip()


def classify_test_kind(ref: str) -> str:
    """Deterministic kind rule (kind-rule-v1; gate A7 — OPEN enum).

    Order matters: a graph-tests path wins over the word 'gate' appearing in
    prose; a gate citation wins over '-verify' (a gate name could embed it);
    the m1/m3-verify invariant family next; everything else is 'unit' (pytest
    ids and code-note citations — the conservative default).
    """
    low = ref.lower()
    if "graph-tests/" in low:
        return "graph-test"
    if low.startswith("gate") or "gate `" in low or "(gate" in low:
        return "gate"
    if "-verify" in low:
        return "verify"
    return "unit"


def _split_cell(cell: str, sep: str) -> list[str]:
    """Split on *sep* OUTSIDE parentheses only (L18).

    Component/test refs may carry a parenthetical qualifier whose text itself
    contains the separator (``drydocs/cli.py (bootstrap, verify)``). A naive
    split sheared 8 of 56 committed Component.ref values into two corrupt
    ``(origin, ref)`` identities each; the depth-0 split keeps the ref whole.
    The parenthetical stays PART of the ref — stripping it would re-key every
    already-loaded ref that carries a benign qualifier.
    """
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    for ch in cell:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == sep and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    return [t for t in (_clean_ref(part) for part in parts) if t]


#: A trailing "(Stage B)"-style qualifier on a design-section citation — a
#: human sub-locator within the anchored section, not part of the anchor id.
_PAREN_QUALIFIER_RE = re.compile(r"\s*\([^)]*\)\s*$")


def _section_tokens(cell: str) -> list[str]:
    """Design-section cell -> authored anchor ids. Committed matrices separate
    multiple anchors with ',' OR ';' and may suffix a parenthetical qualifier
    (`detailed-design (Stage B)`) — both normalize away deterministically."""
    tokens: list[str] = []
    for part in re.split(r"[;,]", cell):
        t = _PAREN_QUALIFIER_RE.sub("", _clean_ref(part)).strip()
        if t:
            tokens.append(t.lower())
    return tokens


def parse_doc_header(md_path: Path) -> dict:
    """DesignDoc-level facts, denormalized onto every row of that doc."""
    text = md_path.read_text(encoding="utf-8")
    h1 = _H1_RE.search(text)
    rev_m = _REV_RE.search(text)
    commit_m = _COMMIT_RE.search(text)
    status_m = _DOC_STATUS_RE.search(text)
    return {
        "origin": DESIGN_DOCS_ORIGIN,
        "doc_id": md_path.stem,
        "title": h1.group(1).strip() if h1 else md_path.stem,
        "doc_type": doc_type_for_stem(md_path.stem),
        "rev": int(rev_m.group(1)) if rev_m else None,
        "doc_status": status_m.group(1) if status_m else None,
        "commit": commit_m.group(1) if commit_m else None,
        "path": md_path.resolve().relative_to(REPO_ROOT).as_posix(),
    }


def parse_sections(md_text: str) -> list[dict]:
    """Every AUTHORED anchor in file order with the heading line that follows it."""
    sections: list[dict] = []
    for seq, m in enumerate(ANCHOR_RE.finditer(md_text)):
        anchor = m.group(1).lower()
        heading = anchor
        for line in md_text[m.end() :].splitlines():
            stripped = line.strip()
            if stripped:
                heading = stripped.lstrip("#").strip() or anchor
                break
        sections.append({"anchor": anchor, "heading": heading, "seq": seq})
    return sections


def _matrix_block(md_text: str) -> str | None:
    """The text between the traceability-matrix anchor and the next anchor."""
    match = None
    anchors = list(ANCHOR_RE.finditer(md_text))
    for i, m in enumerate(anchors):
        if m.group(1).lower() == MATRIX_ANCHOR:
            end = anchors[i + 1].start() if i + 1 < len(anchors) else len(md_text)
            match = md_text[m.end() : end]
            break
    return match


def _matrix_column_map(header_cells: list[str]) -> dict[str, int] | None:
    """Map the matrix's semantic columns by HEADER NAME, not position.

    The loose-mode outline pins the section's presence and the anchor/test
    citations, not a column count — committed matrices span two layouts today:
    the 6-column controlm form (Requirement | Description | Design section |
    Component / module | Test / verify | Status) and the 5-column TDD form
    (Requirement (source item) | Design section | Component | Test / verify |
    Status, no Description). A fixed-position parse shifts every cell on the
    second form, so columns are located by their header text instead.
    """
    mapping: dict[str, int] = {}
    for idx, cell in enumerate(header_cells):
        low = cell.lower()
        if low.startswith("requirement") and "requirement" not in mapping:
            mapping["requirement"] = idx
        elif low.startswith("description"):
            mapping["description"] = idx
        elif "design section" in low:
            mapping["section"] = idx
        elif low.startswith("component"):
            mapping["component"] = idx
        elif "test" in low or "verify" in low:
            mapping["test"] = idx
        elif low.startswith("status"):
            mapping["status"] = idx
    if "requirement" not in mapping or "test" not in mapping:
        return None  # not a traceability table
    return mapping


def _cell(cells: list[str], mapping: dict[str, int], key: str) -> str:
    idx = mapping.get(key)
    if idx is None or idx >= len(cells):
        return ""
    return cells[idx]


def parse_matrix_rows(md_text: str, doc_id: str) -> list[dict]:
    """One dict per data row of the matrix table (header + separator skipped).

    Columns are located by header name (:func:`_matrix_column_map`).
    Components split on ',' — Tests split on ';' (one cell can cite several,
    e.g. FR-CMI-007's gate + graph-tests pair). Backticks are presentation.
    requirement_id is the Requirement cell as written — under the loose
    per-source id mode (gate D5) a prose row-identity is valid data; kind
    derives from a recognized FR/UC/NFR prefix, else 'other'.
    """
    block = _matrix_block(md_text)
    if block is None:
        return []
    rows: list[dict] = []
    mapping: dict[str, int] | None = None
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if mapping is None:
            mapping = _matrix_column_map(cells)
            continue
        if not cells[0] or set(cells[0]) <= {"-", " ", ":"}:
            continue  # separator / blank id rows
        requirement_id = _clean_ref(_cell(cells, mapping, "requirement"))
        if not requirement_id:
            continue
        prefix = requirement_id.split("-", 1)[0].upper()
        status_cell = _cell(cells, mapping, "status")
        rows.append(
            {
                "origin": DESIGN_DOCS_ORIGIN,
                "doc_id": doc_id,
                "requirement_id": requirement_id,
                "kind": prefix if prefix in ("FR", "UC", "NFR") else "other",
                "description": _cell(cells, mapping, "description"),
                "section_anchors": _section_tokens(_cell(cells, mapping, "section")),
                "components": _split_cell(_cell(cells, mapping, "component"), ","),
                "tests": [
                    {"kind": classify_test_kind(ref), "ref": ref}
                    for ref in _split_cell(_cell(cells, mapping, "test"), ";")
                ],
                "matrix_status": status_cell or None,
            }
        )
    return rows


def _design_doc_paths(design_dir: Path) -> list[Path]:
    """Committed design docs — top-level *.md only (templates/ and feedback/
    are subdirectories, so a non-recursive glob excludes them by construction)."""
    return sorted(p for p in design_dir.glob("*.md") if p.is_file())


class DesignDocSectionsAdapter:
    """One row per authored anchor across every docs/design/*.md."""

    name = "design-docs-sections"

    def __init__(self, design_dir: Path | str = DEFAULT_DESIGN_DIR) -> None:
        self.design_dir = Path(design_dir)

    def __enter__(self) -> DesignDocSectionsAdapter:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    def rows(self) -> Iterator[dict]:
        for md_path in _design_doc_paths(self.design_dir):
            header = parse_doc_header(md_path)
            text = md_path.read_text(encoding="utf-8")
            for section in parse_sections(text):
                yield {**header, **section}


class TraceabilityMatrixAdapter:
    """One row per traceability-matrix table row across every design doc."""

    name = "design-docs-matrix"

    def __init__(self, design_dir: Path | str = DEFAULT_DESIGN_DIR) -> None:
        self.design_dir = Path(design_dir)

    def __enter__(self) -> TraceabilityMatrixAdapter:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    def rows(self) -> Iterator[dict]:
        for md_path in _design_doc_paths(self.design_dir):
            text = md_path.read_text(encoding="utf-8")
            yield from parse_matrix_rows(text, md_path.stem)


class DesignDocFeedbackAdapter:
    """One row per note across every docs/design/feedback/<doc>-rev<N>.yaml.

    Optional yaml fields beyond the exported format (docs/design/feedback/
    README.md): file-level ``author:`` and per-note ``status:`` / ``author:``
    — data entry recording review outcomes, never generated by the export.
    """

    name = "design-docs-feedback"

    #: top-level files that are legitimately not feedback exports: the
    #: directory's own README. Subdirectories (scans/, the L6 paper archive)
    #: are outside the contract by shape, not by name.
    expected_extra_names: ClassVar[frozenset[str]] = frozenset({"README.md"})

    def __init__(self, feedback_dir: Path | str = DEFAULT_FEEDBACK_DIR) -> None:
        self.feedback_dir = Path(feedback_dir)

    def __enter__(self) -> DesignDocFeedbackAdapter:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    def stray_files(self) -> list[str]:
        """L20 — files in feedback/ that match no expected pattern, as findings.

        The L5 Copy-feedback export trusts the human to name the file
        ``<doc>-rev<N>.yaml``, and until 2026-07-28 a wrong name (``... - Copy
        .yaml``, ``...-rev1 (1).yaml``) was invisible: outside the loader's
        glob-plus-regex filter, silently ignored, feedback never loaded. Every
        top-level file that is neither a well-named export nor an expected
        extra is a finding for the caller to surface — never silence.
        """
        if not self.feedback_dir.is_dir():
            return []
        return sorted(
            p.name
            for p in self.feedback_dir.iterdir()
            if p.is_file()
            and p.name not in self.expected_extra_names
            and not _FEEDBACK_FILE_RE.match(p.name)
        )

    def rows(self) -> Iterator[dict]:
        for fb_path in sorted(self.feedback_dir.glob("*.y*ml")):
            m = _FEEDBACK_FILE_RE.match(fb_path.name)
            if not m:
                continue
            data = yaml.safe_load(fb_path.read_text(encoding="utf-8")) or {}
            doc_id = str(data.get("doc") or m.group("doc_id"))
            file_author = data.get("author")
            for entry in data.get("notes") or []:
                anchor = str(entry.get("anchor", "")).strip().lower()
                note = str(entry.get("note", "")).strip()
                if not anchor or not note:
                    continue
                yield {
                    "origin": DESIGN_DOCS_ORIGIN,
                    "doc_id": doc_id,
                    "doc_rev": int(m.group("rev")),
                    "anchor": anchor,
                    "base_anchor": anchor.split(DERIVED_ANCHOR_SEP, 1)[0],
                    "note": note,
                    "status": entry.get("status") or "open",
                    "author": entry.get("author") or file_author,
                }


class _ChecksummedLoader(BaseLoader):
    """Shared to_params: the doc 06 Phase 2 delta checksum over the full row."""

    def to_params(self, model: BaseModel) -> dict:
        params = model.model_dump(mode="json")
        params["row_checksum"] = compute_row_checksum(params)
        return params


class DesignDocSectionsLoader(_ChecksummedLoader):
    name: ClassVar[str] = "doc_sections.v1"
    source_id: ClassVar[str | None] = "repo:design-docs"
    cypher_path: ClassVar[Path] = CYPHER_DIR / "doc_sections.cypher"
    row_model: ClassVar[type] = DocSectionRow
    source_label: ClassVar[str] = "markdown"


class _SectionPrereqLoader(_ChecksummedLoader):
    """Shared L17 guard: both passes 2 and 3 MATCH (never MERGE) the
    :DocSection nodes pass 1 (doc_sections.v1) wrote — the OPTIONAL MATCH +
    FOREACH idiom means an absent section registry drops EVERY anchor link
    while the run still reports OK (the Q8 / batch_port_orchestrator
    "succeeds loudly, does nothing" family). Whole-registry absence is
    refused up front; per-row misses are tolerated (one mis-cited anchor
    must not cost the other rows their edges) but COUNTED and listed after
    the load, never silent.
    """

    #: subclass hook: the row field naming the anchors this loader links to
    anchor_field: ClassVar[str] = ""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # (origin, doc_id, anchor) triples this run actually sent — a MATCH
        # miss leaves no trace in the graph, so the loader must remember
        # what it cited (the batch_port seal_ids_sent idiom).
        self.anchors_sent: set[tuple[str, str, str]] = set()
        self.unmatched_anchors: list[dict] = []

    def _load(self, summary: LoadSummary, run_log: LoaderRunLog | None) -> LoadSummary:
        """Refusal runs BEFORE ``super()._load`` — which is what reaches
        ``_preflight_indexes`` and ``_open_run`` — so a refused load writes
        nothing at all, not even the :JobRun."""
        self._assert_prereqs()
        result = super()._load(summary, run_log)
        self._report_link_coverage()
        return result

    def _assert_prereqs(self) -> None:
        self._assert_doc_sections_present()

    def _report_link_coverage(self) -> None:
        self._report_unmatched_anchors()

    def to_params(self, model: BaseModel) -> dict:
        params = super().to_params(model)
        anchors = params.get(self.anchor_field)
        for anchor in anchors if isinstance(anchors, list) else [anchors]:
            if anchor:
                self.anchors_sent.add((params["origin"], params["doc_id"], anchor))
        return params

    def _count_real_nodes(self, label: str, key: str) -> int:
        """Count real nodes of ``label``, excluding the schema exemplars.

        ``schema_graph.cypher`` MERGEs ``:SchemaMeta:<Label>`` exemplars that
        carry the REAL label with no key property, so a bare ``count()``
        would wave an empty registry straight through — the whole failure
        this check exists to catch. (``label``/``key`` are module-controlled
        literals, never row data — no injection surface.)
        """
        rows = self.client.run(
            f"MATCH (n:{label}) WHERE NOT n:SchemaMeta AND n.{key} IS NOT NULL "
            "RETURN count(n) AS found"
        )
        return rows[0].get("found", 0) if rows else 0

    def _assert_doc_sections_present(self) -> None:
        if self._count_real_nodes("DocSection", "anchor"):
            return
        raise RuntimeError(
            f"Loader {self.name}: refusing to load — no :DocSection nodes are "
            "reachable in this database, so every anchor link would be silently "
            "dropped (OPTIONAL MATCH + FOREACH guard) and the run would still "
            "report success. Run the doc_sections.v1 pass against THIS database "
            "first (`drydocs load-doc-traceability` runs the three passes in "
            "order — a relationship cannot span databases)."
        )

    def _report_unmatched_anchors(self) -> None:
        if not self.anchors_sent:
            return
        triples = sorted(self.anchors_sent)
        rows = self.client.run(
            "UNWIND $anchors AS p "
            "MATCH (ds:DocSection {origin: p.origin, doc_id: p.doc_id, anchor: p.anchor}) "
            "RETURN p.origin AS origin, p.doc_id AS doc_id, p.anchor AS anchor",
            anchors=[{"origin": o, "doc_id": d, "anchor": a} for o, d, a in triples],
        )
        found = {(r.get("origin"), r.get("doc_id"), r.get("anchor")) for r in rows}
        self.unmatched_anchors = [
            {"doc_id": d, "anchor": a} for o, d, a in triples if (o, d, a) not in found
        ]
        if self.unmatched_anchors:
            LOGGER.warning(
                "Loader %s: %d cited anchor(s) matched no :DocSection — their "
                "anchor links were dropped, not written: %s",
                self.name,
                len(self.unmatched_anchors),
                self.unmatched_anchors,
            )


class DocTraceabilityLoader(_SectionPrereqLoader):
    name: ClassVar[str] = "doc_traceability.v1"
    source_id: ClassVar[str | None] = "repo:design-docs"
    cypher_path: ClassVar[Path] = CYPHER_DIR / "doc_traceability.cypher"
    row_model: ClassVar[type] = TraceabilityRow
    source_label: ClassVar[str] = "markdown"
    anchor_field: ClassVar[str] = "section_anchors"


class DocFeedbackLoader(_SectionPrereqLoader):
    """Pass 3 — the L5/L6 re-attachment loop itself, so its silent failure
    mode is the worst of the family: SME feedback loading "successfully"
    while detached from the doc it annotates. Beyond the section guard it
    also refuses an authored batch against an EMPTY :Employee registry —
    an unknown author dropping its attribution edge is by-design (gate C1,
    provenance never fabricated) and stays a per-row reported case, but a
    whole-registry absence means every attribution silently drops."""

    name: ClassVar[str] = "doc_feedback.v1"
    source_id: ClassVar[str | None] = "repo:design-docs"
    cypher_path: ClassVar[Path] = CYPHER_DIR / "doc_feedback.cypher"
    row_model: ClassVar[type] = FeedbackNoteRow
    source_label: ClassVar[str] = "human"
    anchor_field: ClassVar[str] = "base_anchor"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.authors_sent: set[str] = set()
        self.unknown_authors: list[str] = []
        self.stray_feedback_files: list[str] = []

    def _assert_prereqs(self) -> None:
        super()._assert_prereqs()
        self._assert_employees_present_if_authored()

    def _report_link_coverage(self) -> None:
        super()._report_link_coverage()
        self._report_unknown_authors()
        self._report_stray_files()

    def _report_stray_files(self) -> None:
        """L20 — a misnamed export in feedback/ is a finding, not silence.

        Duck-typed so a fake adapter without the census stays valid; the real
        DesignDocFeedbackAdapter always carries it."""
        census = getattr(self.adapter, "stray_files", None)
        if census is None:
            return
        self.stray_feedback_files = census()
        if self.stray_feedback_files:
            LOGGER.warning(
                "Loader %s: %d file(s) in the feedback directory match no "
                "expected <doc>-rev<N>.yaml pattern and were NOT loaded — "
                "rename them to load their notes, or remove them: %s",
                self.name,
                len(self.stray_feedback_files),
                ", ".join(self.stray_feedback_files),
            )

    def to_params(self, model: BaseModel) -> dict:
        params = super().to_params(model)
        if params.get("author"):
            self.authors_sent.add(str(params["author"]))
        return params

    def _assert_employees_present_if_authored(self) -> None:
        """Pre-scan the (re-enterable, file-backed) adapter: only a batch
        that actually carries authors needs the :Employee registry — an
        author-less batch loads fine without one."""
        with self.adapter as adapter:
            authored = any(r.get("author") for r in adapter.rows())
        if not authored or self._count_real_nodes("Employee", "employee_id"):
            return
        raise RuntimeError(
            f"Loader {self.name}: refusing to load — this batch carries "
            "author(s) but no :Employee nodes are reachable in this database, "
            "so every WAS_ATTRIBUTED_TO edge would be silently dropped and the "
            "run would still report success. Load the employee registry "
            "against THIS database first, or remove the author fields if "
            "attribution is not wanted (gate C1: never fabricated)."
        )

    def _report_unknown_authors(self) -> None:
        if not self.authors_sent:
            return
        rows = self.client.run(
            "UNWIND $authors AS a MATCH (e:Employee {employee_id: a}) "
            "RETURN e.employee_id AS employee_id",
            authors=sorted(self.authors_sent),
        )
        found = {r.get("employee_id") for r in rows}
        self.unknown_authors = sorted(self.authors_sent - found)
        if self.unknown_authors:
            LOGGER.warning(
                "Loader %s: %d author(s) matched no :Employee — their "
                "WAS_ATTRIBUTED_TO edges were dropped by design (gate C1, "
                "never fabricated), reported here: %s",
                self.name,
                len(self.unknown_authors),
                self.unknown_authors,
            )
