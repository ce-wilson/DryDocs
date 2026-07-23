"""Tier-1 schema grounding: ontology vocabulary + live schema + few-shot specs.

NEVER whole-graph state (ADR 0007 gotcha 2 — KGoT's inject-everything trick
only works on a toy task graph). Three bounded ingredients:

1. ``relationship_vocabulary.yaml`` — the ACTIVE local_relationships rows:
   the curated meaning of every edge (label, endpoints, role, note);
2. live ``graph_schema()`` output — labels / relationship types / property
   keys actually present in the routed database;
3. few-shot examples — a handful of registered QuerySpec cyphers, the house
   idiom for reading this graph.

Everything is character-bounded so the schema prompt is a fixed, predictable
context cost per call.
"""

from __future__ import annotations

from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
VOCABULARY_PATH = _REPO_ROOT / "drydocs_core" / "ontology" / "relationship_vocabulary.yaml"

MAX_VOCAB_ROWS = 80
MAX_EXAMPLES = 6
MAX_NOTE_CHARS = 90
MAX_PROMPT_CHARS = 12_000

# Per-section character budgets. Tail-truncating the WHOLE prompt silently
# dropped the live schema, per-label properties, and every example the first
# time the vocabulary outgrew the cap (live finding, 2026-07-23) — each
# section now survives on its own budget; sums stay under MAX_PROMPT_CHARS.
SECTION_BUDGETS = {"vocab": 4_800, "live": 1_400, "by_label": 2_800, "examples": 2_800}


def load_vocabulary(path: Path | None = None) -> list[dict]:
    """Active relationship rows only — planned/deprecated edges must not be suggested."""
    doc = yaml.safe_load((path or VOCABULARY_PATH).read_text(encoding="utf-8"))
    rows = doc.get("local_relationships", []) or []
    return [r for r in rows if r.get("status") == "active"]


def _clip(lines: list[str], budget: int) -> list[str]:
    """Whole-line clipping with an explicit truncation marker — never mid-line."""
    out: list[str] = []
    used = 0
    for line in lines:
        if used + len(line) + 1 > budget:
            out.append("… (section truncated)")
            break
        out.append(line)
        used += len(line) + 1
    return out


def _vocab_lines(rows: list[dict]) -> list[str]:
    lines = []
    for r in rows[:MAX_VOCAB_ROWS]:
        role = f" role={r['role']}" if r.get("role") else ""
        note = (r.get("note") or "")[:MAX_NOTE_CHARS]
        lines.append(
            f"(:{r.get('from_node')})-[:{r.get('neo4j_label')}{role}]->(:{r.get('to_node')})"
            + (f"  // {note}" if note else "")
        )
    return lines


def build_schema_prompt(
    vocab_rows: list[dict],
    live_schema: dict,
    examples: list[tuple[str, str, str]],  # (spec_id, description, cypher)
    max_chars: int = MAX_PROMPT_CHARS,
) -> str:
    parts = [
        "You write read-only Cypher for the DryDocs knowledge graph.",
        "",
        "## Relationship vocabulary (curated — the ONLY edge semantics that exist)",
        *_clip(_vocab_lines(vocab_rows), SECTION_BUDGETS["vocab"]),
        "",
        "## Live schema of the routed database",
        *_clip(
            [
                f"labels: {', '.join(live_schema.get('labels', []))}",
                f"relationship types: {', '.join(live_schema.get('relationshipTypes', []))}",
                f"property keys: {', '.join(live_schema.get('propertyKeys', []))}",
            ],
            SECTION_BUDGETS["live"],
        ),
    ]
    if live_schema.get("propertiesByLabel"):
        parts += [
            "",
            "## Properties by label (use ONLY these per label)",
            *_clip(
                [
                    f"{label}: {', '.join(props)}"
                    for label, props in live_schema["propertiesByLabel"].items()
                ],
                SECTION_BUDGETS["by_label"],
            ),
        ]
    example_lines: list[str] = []
    for spec_id, description, cypher in examples[:MAX_EXAMPLES]:
        example_lines += [f"-- {spec_id}: {description}", cypher, ""]
    parts += [
        "",
        "## Example queries (registered specs — follow this idiom)",
        *_clip(example_lines, SECTION_BUDGETS["examples"]),
    ]
    return "\n".join(parts)[:max_chars]
