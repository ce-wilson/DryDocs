"""doc_outline.py — validate a design doc against its canonical outline (Epic L / L1).

drydocs-docgen. The outline file (``docs/design/templates/<type>.outline.yaml``, schema
``drydocs.doc-outline.v1``) is the STRUCTURAL-determinism contract: every doc of a given
type carries the same sections, so completeness and requirement traceability are guaranteed
by construction rather than by reviewer diligence.

ANCHOR CONVENTION — sections are tagged in the markdown with an HTML comment placed
immediately before the heading::

    <!-- anchor: traceability-matrix -->
    ## 10. Requirements traceability matrix

The comment is invisible in every renderer (GitHub, VS Code, the L3 pipeline) and is the
stable id namespace that the render pipeline emits as element ids, the traceability matrix
keys on, and the HITL feedback loops (L5 digital / L6 paper) re-attach to. Anchors are
AUTHORED, never positional, so inserting a section never renumbers another or breaks a
prior annotation.

What this checks (all are hard errors):
  1. COMPLETENESS — every ``required: true`` section (and required subsection) anchor is
     present in the doc. A required section may hold an explicit "N/A — <reason>"; the
     anchor must still be there.
  2. TRACEABILITY — every requirement id that appears anywhere in the doc has exactly one
     row in the matrix section; every matrix row cites a design-section anchor that exists
     in the outline and a non-empty test/verify.

Pure + offline: stdlib + PyYAML only (no Neo4j, no component imports). Importable, and
runnable as a CLI for envs without pytest::

    python -m drydocs.doc_outline --outline docs/design/templates/tdd.outline.yaml \
                                  --doc docs/design/controlm-ingestion-tdd.md
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

#: The anchor contract lives in core (shared with the L7 loaders — ADR 0002-a);
#: re-exported here under the established names: ANCHOR_RE is the
#: ``<!-- anchor: some-id -->`` section marker, and DERIVED_ANCHOR_SEP is the
#: L11 ``--`` separator (design_doc._inject_subsection_anchors) — RESERVED,
#: never use a double hyphen inside an authored anchor id.
from drydocs_core.doc_anchors import ANCHOR_RE, DERIVED_ANCHOR_SEP  # noqa: E402


def feedback_anchor_valid(anchor: str, md: str) -> bool:
    """Whether a feedback-file anchor re-attaches to this doc: either an AUTHORED anchor
    (``<!-- anchor: id -->`` present in the md) or an L11 DERIVED subsection anchor
    (``<authored>--<slug>``) whose base section is authored — a derived note degrades to
    its parent section if the subsection text (and so its slug) later changes."""
    anchors = set(doc_anchors(md))
    if anchor.lower() in anchors:
        return True
    base = anchor.lower().split(DERIVED_ANCHOR_SEP, 1)[0]
    return base in anchors


@dataclass
class Outline:
    """A parsed ``*.outline.yaml`` (schema drydocs.doc-outline.v1)."""

    schema: str
    doc_type: str
    sections: list[dict]
    traceability: dict
    raw: dict

    def all_anchors(self) -> set[str]:
        out: set[str] = set()
        for sec in self.sections:
            out.add(sec["anchor"])
            for sub in sec.get("subsections") or []:
                out.add(sub["anchor"])
        return out

    def required_anchors(self) -> list[str]:
        out: list[str] = []
        for sec in self.sections:
            if sec.get("required"):
                out.append(sec["anchor"])
            for sub in sec.get("subsections") or []:
                if sub.get("required"):
                    out.append(sub["anchor"])
        return out


def load_outline(path: str | Path) -> Outline:
    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if doc.get("schema") != "drydocs.doc-outline.v1":
        raise ValueError(f"{path}: not a drydocs.doc-outline.v1 outline (schema={doc.get('schema')!r})")
    return Outline(
        schema=doc["schema"],
        doc_type=doc.get("doc_type", "?"),
        sections=doc.get("sections") or [],
        traceability=doc.get("traceability") or {},
        raw=doc,
    )


def doc_anchors(md: str) -> list[str]:
    """Anchor ids present in the markdown, in document order (may repeat)."""
    return [m.group(1).lower() for m in ANCHOR_RE.finditer(md)]


def _matrix_slice(md: str, matrix_anchor: str) -> str:
    """The text of the matrix section: from its anchor to the next anchor (or EOF)."""
    anchors = list(ANCHOR_RE.finditer(md))
    for i, m in enumerate(anchors):
        if m.group(1).lower() == matrix_anchor.lower():
            start = m.end()
            end = anchors[i + 1].start() if i + 1 < len(anchors) else len(md)
            return md[start:end]
    return ""


def _parse_table(slice_text: str) -> tuple[list[str], list[list[str]]]:
    """First pipe-table in ``slice_text`` -> (header cells, data rows). ``([], [])`` if none."""
    rows: list[list[str]] = []
    for line in slice_text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            if rows:  # table ended
                break
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        rows.append(cells)
    if len(rows) < 2:
        return [], []
    header = rows[0]
    # row 1 is the |---|---| separator
    data = [r for r in rows[2:] if any(c for c in r)]
    return header, data


def _col(header: list[str], *keywords: str) -> int:
    for idx, name in enumerate(header):
        low = name.lower()
        if any(k in low for k in keywords):
            return idx
    return -1


def check(outline: Outline, md: str) -> list[str]:
    """Return a list of human-readable problems; empty list == the doc conforms."""
    problems: list[str] = []
    present = set(doc_anchors(md))

    # 1 — completeness
    for anchor in outline.required_anchors():
        if anchor not in present:
            problems.append(f"missing required section — add `<!-- anchor: {anchor} -->` before its heading")

    # 2 — traceability. `mode: loose` (default when absent = strict) checks the matrix
    # shape only; `strict` also enforces requirement-id format + no-orphans/no-dups.
    trace = outline.traceability
    matrix_anchor = trace.get("matrix_section")
    if not matrix_anchor:
        return problems

    strict = (trace.get("mode") or "strict").lower() == "strict"
    pattern = trace.get("requirement_id_pattern")
    req_re = re.compile(pattern) if pattern else None

    if matrix_anchor not in present:
        return problems  # completeness already flags a missing required matrix

    header, data = _parse_table(_matrix_slice(md, matrix_anchor))
    if not header:
        problems.append(f"matrix section `{matrix_anchor}` has no markdown table")
        return problems

    c_req = _col(header, "requirement")
    c_design = _col(header, "design", "section")
    c_test = _col(header, "test", "verify")
    if min(c_design, c_test) < 0:
        problems.append(f"matrix table needs Design-section and Test columns (saw header {header})")
        return problems

    valid_anchors = outline.all_anchors()
    matrix_ids: list[str] = []
    for row in data:
        need = max(c for c in (c_req, c_design, c_test) if c >= 0)
        if len(row) <= need:
            problems.append(f"matrix row has too few cells: {row}")
            continue
        # both modes: each row must trace a design-section anchor + a test
        if not any(a in row[c_design] for a in valid_anchors):
            problems.append(f"matrix row design cell {row[c_design]!r} cites no known outline anchor")
        if not row[c_test].strip():
            problems.append(f"matrix row has an empty test/verify cell: {row}")
        # strict only: collect + format-check the requirement id
        if strict and req_re and c_req >= 0:
            m = req_re.search(row[c_req])
            if not m:
                problems.append(f"matrix row id {row[c_req]!r} does not match {pattern}")
            else:
                matrix_ids.append(m.group(0))

    if strict and req_re:
        for rid in sorted({r for r in matrix_ids if matrix_ids.count(r) > 1}):
            problems.append(f"[{rid}] appears in more than one matrix row")
        body_ids = {t for t in re.findall(r"[A-Za-z0-9][A-Za-z0-9-]*", md) if req_re.match(t)}
        for rid in sorted(body_ids - set(matrix_ids)):
            problems.append(f"[{rid}] requirement id used in the doc but has no traceability-matrix row")

    return problems


def validate_paths(outline_path: str | Path, doc_path: str | Path) -> list[str]:
    outline = load_outline(outline_path)
    md = Path(doc_path).read_text(encoding="utf-8")
    return check(outline, md)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate a design doc against its canonical outline.")
    ap.add_argument("--outline", required=True, type=Path)
    ap.add_argument("--doc", required=True, type=Path)
    args = ap.parse_args(argv)

    problems = validate_paths(args.outline, args.doc)
    if problems:
        print(f"FAIL — {args.doc} does not conform to {args.outline.name}:")
        for p in problems:
            print(f"  • {p}")
        return 1
    print(f"OK — {args.doc.name} conforms to {args.outline.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
