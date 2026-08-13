"""The change doc — per-change what/why/evidence with before/after excerpts.

The PACKAGING-TIME diff surface (user ruling 2026-08-12: the console diff is
the working session; this excerpt is what ships in the fix package). Pure
renderer: everything here is derived from artifacts the caller already holds —
the approved changes, the enumerated effects, the self-check report's changed
lines, and the read-only graph anchors — so the doc is deterministic and
regenerable from (original + change-set), per the fix-package contract.

Markdown, mechanism-shaped. Real fix packages carry real values and are
Internal; this module only formats what it is given.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .changes import ApprovedChange, FixAnchor
from .xml_io import Effect, SelfCheckReport


@dataclass
class ChangeDoc:
    """Inputs for one fix package's change doc."""

    fix_id: str
    original_name: str  # e.g. "PRXYZ3C.xml" — evidence file name, not a path
    updated_name: str  # e.g. "PRXYZ3C.updated.xml"
    issue: str  # the original problem, caller-authored
    changes: list[ApprovedChange] = field(default_factory=list)
    effects: list[Effect] = field(default_factory=list)
    report: SelfCheckReport | None = None
    anchors: list[FixAnchor] = field(default_factory=list)


def _excerpt(original: bytes, updated: bytes, newline: bytes, line_numbers: list[int]) -> list[str]:
    """Before/after pairs for exactly the self-checked changed lines.

    The self-check already proved every changed line intersects an approved
    edit span, so excerpting by its line numbers cannot leak an unreviewed
    change into the doc — the excerpt IS the diff, not a sample of it.
    """
    before_lines = original.split(newline)
    after_lines = updated.split(newline)
    out: list[str] = []
    for lineno in line_numbers:
        idx = lineno - 1
        before = (
            before_lines[idx].decode("utf-8", "replace").strip() if idx < len(before_lines) else ""
        )
        after = (
            after_lines[idx].decode("utf-8", "replace").strip() if idx < len(after_lines) else ""
        )
        out.append(f"```\nline {lineno}\n- {before}\n+ {after}\n```")
    return out


def render_change_doc(
    doc: ChangeDoc, original: bytes, updated: bytes, newline: bytes = b"\n"
) -> str:
    """The fix package's ``change-doc.md`` body."""
    lines: list[str] = [
        f"# Change doc — {doc.fix_id}",
        "",
        f"Original: `{doc.original_name}` (evidence, checksummed in the manifest)",
        f"Updated: `{doc.updated_name}` (regenerable from original + this change-set)",
        "",
        "## Issue",
        "",
        doc.issue,
        "",
    ]

    if doc.anchors:
        lines += [
            "## Graph anchors (read-only; the fix's start and end points as the graph keys them)",
            "",
            "| Node | Labels | Node key | Citable relationships |",
            "|---|---|---|---|",
        ]
        for anchor in doc.anchors:
            key = ", ".join(f"{k}={v}" for k, v in anchor.node_key.items())
            lines.append(
                f"| {anchor.display_name} | :{':'.join(anchor.labels)} | `{key}` "
                f"| {', '.join(anchor.relationships) or '—'} |"
            )
        lines.append("")

    lines += ["## Changes (each 1:1 with a gate approval — §XML rule 3)", ""]
    for change in doc.changes:
        lines += [
            f"### {change.approval_id} — {change.kind}: {change.detail}",
            "",
            f"- **Target:** folder `{change.locator.folder}`"
            + (
                f", sub-folder `{change.locator.subfolder_path}`"
                if change.locator.subfolder_path
                else ""
            )
            + (f", job `{change.locator.job}`" if change.locator.job else ""),
        ]
        if change.value is not None:
            lines.append(f"- **New value:** `{change.value}`")
        if change.evidence:
            lines.append(f"- **Why / evidence:** {change.evidence}")
        touched = [
            e for e in doc.effects if e.kind == "attr-set" and change.kind == "rename-variable"
        ]
        if change.kind == "rename-variable" and touched:
            lines.append(
                f"- **Sites rewritten by the sweep:** {len(touched)} (every one enumerated below)"
            )
        lines.append("")

    if doc.effects:
        lines += ["## Every effect, enumerated", ""]
        for effect in doc.effects:
            old = f" was `{effect.old}`" if effect.old is not None else ""
            new = f" now `{effect.new}`" if effect.new is not None else ""
            lines.append(f"- `{effect.kind}` {effect.path} **{effect.detail}**{old}{new}")
        lines.append("")

    if doc.report is not None:
        lines += [
            "## Self-check (§XML rule 4)",
            "",
            f"- Verdict: {'PASS' if doc.report.ok else 'FAILED — this package must not ship'}",
            f"- Changed lines: {len(doc.report.changed_line_numbers)} "
            "(every one intersects an approved edit span — proven, not sampled)",
            "",
            "## Diff excerpt (exactly the changed lines)",
            "",
        ]
        lines += _excerpt(original, updated, newline, doc.report.changed_line_numbers)
        lines.append("")

    return "\n".join(lines)
