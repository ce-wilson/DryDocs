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
(drydocs.doc_outline.ANCHOR_RE / DERIVED_ANCHOR_SEP). No LLM, no heuristic
beyond the documented cell-split + kind rules below — same determinism bar as
the render pipeline.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Iterator

import yaml
from pydantic import BaseModel

from drydocs_core.models.doc_traceability import (
    DESIGN_DOCS_ORIGIN,
    DocSectionRow,
    FeedbackNoteRow,
    TraceabilityRow,
)
from drydocs_core.doc_anchors import ANCHOR_RE, DERIVED_ANCHOR_SEP
from .base import BaseLoader, compute_row_checksum

if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

REPO_ROOT = Path(__file__).resolve().parents[2]
CYPHER_DIR = Path(__file__).resolve().parent / "cypher"
DEFAULT_DESIGN_DIR = REPO_ROOT / "docs" / "design"
DEFAULT_FEEDBACK_DIR = DEFAULT_DESIGN_DIR / "feedback"

MATRIX_ANCHOR = "traceability-matrix"
TEST_KIND_RULE_ID = "kind-rule-v1"

# Front-matter facts — the SAME regex family the render pipeline keys on
# (drydocs.design_doc): Rev + commit for the print footer; DESCRIPTIVE /
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
    return [t for t in (_clean_ref(part) for part in cell.split(sep)) if t]


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
        for line in md_text[m.end():].splitlines():
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
            match = md_text[m.end():end]
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

    def __enter__(self) -> "DesignDocSectionsAdapter":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: "TracebackType | None",
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

    def __enter__(self) -> "TraceabilityMatrixAdapter":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: "TracebackType | None",
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

    def __init__(self, feedback_dir: Path | str = DEFAULT_FEEDBACK_DIR) -> None:
        self.feedback_dir = Path(feedback_dir)

    def __enter__(self) -> "DesignDocFeedbackAdapter":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: "TracebackType | None",
    ) -> None:
        return None

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
    cypher_path: ClassVar[Path] = CYPHER_DIR / "doc_sections.cypher"
    row_model: ClassVar[type] = DocSectionRow
    source_label: ClassVar[str] = "markdown"


class DocTraceabilityLoader(_ChecksummedLoader):
    name: ClassVar[str] = "doc_traceability.v1"
    cypher_path: ClassVar[Path] = CYPHER_DIR / "doc_traceability.cypher"
    row_model: ClassVar[type] = TraceabilityRow
    source_label: ClassVar[str] = "markdown"


class DocFeedbackLoader(_ChecksummedLoader):
    name: ClassVar[str] = "doc_feedback.v1"
    cypher_path: ClassVar[Path] = CYPHER_DIR / "doc_feedback.cypher"
    row_model: ClassVar[type] = FeedbackNoteRow
    source_label: ClassVar[str] = "human"
