"""Generate the O19 /gates page data (the O12 enforcement-matrix pattern).

Scans config/gate-log.md (one row per ``## `` entry), config/gate-prompts/
(one row per prompt file, joined to log entries by slug mention), and
backlog/ (which items mention each gate slug -> the "unblocks" edges of
the gate dependency graph) and emits ``web/src/generated/gates.json``.
``tests/unit/test_gates_json.py`` is the drift guard: a gate-log entry or
gate-prompt file with no row fails the build.

Status vocabulary (derived from the log verbatim -- the page renders the
record, it never reinterprets it):
- ``open``       -- a gate-prompt file NO log entry is ABOUT and which does not
                    self-declare its disposition. Two flavours, distinguished in
                    the row title: never run (no mention anywhere) vs cited or
                    partially ruled without a recorded sign-off (J28).
- ``deferred``   -- the entry heading says DEFERRED.
- ``pending``    -- the entry heading says PENDING (a later entry may resolve
                    it; rows reflect the log as written).
- ``signed-off`` -- the heading says SIGNED OFF / ACCEPTED / CONFIRMED.
- ``recorded``   -- everything else (decisions logged without the formal
                    sign-off wording, e.g. early C1-C4 entries).

J28 -- which entry ACCOUNTS FOR a prompt. A bare substring scan of section
bodies classified a prompt as handled when ANY entry merely cited its file, so
a gate with only partial rulings rendered as closed (seal-app-ref-edge-reshape
was invisible for six weeks of governance work until a manual log read found
it). An entry accounts for a prompt only when the prompt's slug appears in the
entry's SLUGIFIED HEADING (the entry is about that gate) and the heading does
not say PARTIAL -- a partial ruling decides a slice and must leave the gate
visible. A prompt may also account for itself with a ``# SIGNED OFF ...`` /
``# DEFERRED ...`` marker line in its header comment (the
controlm-hosts-topology / self-documentation-code-graph convention) -- the
committed record for early gates whose log headings use prose names rather
than slugs. Body citations still populate ``prompt_files`` on log-entry rows
(the display join), they just never close a gate.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from drydocs_core.backlog_store import load_backlog_document

REPO = Path(__file__).resolve().parent.parent
LOG = REPO / "config" / "gate-log.md"
PROMPTS = REPO / "config" / "gate-prompts"
BACKLOG = REPO / "docs" / "restructure" / "backlog"  # the sharded tree (ADR 0013)
OUT = REPO / "web" / "src" / "generated" / "gates.json"

_HEADING_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2})(?:[^\S\n]*[—-][^\S\n]*)(.+)$", re.MULTILINE)

# A prompt-file header line that declares the gate's own disposition. Anchored
# at comment-line start so prose that MENTIONS another gate's sign-off (e.g.
# code-graph-package-layer's "RE-OPENS ... (SIGNED OFF" line) never matches.
_SELF_DECLARED_RE = re.compile(r"^#\s*(?:\*+\s*)?(?:SIGNED OFF|DEFERRED)\b", re.MULTILINE)


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower())


def section_accounts_for(slug: str, heading: str) -> bool:
    """J28 -- is this log entry ABOUT the gate this prompt proposes?

    Heading identity, not body citation: the slug must appear in the slugified
    heading (which also matches prose headings like "SEAL attribution match
    policy gate"), and a PARTIAL heading never accounts -- it decides a slice
    and the gate as a whole must stay visible as open.
    """
    if "PARTIAL" in heading.upper():
        return False
    return slug in _slugify(heading)


def prompt_self_declares(prompt_path: Path) -> bool:
    return bool(_SELF_DECLARED_RE.search(prompt_path.read_text(encoding="utf-8")))


def _status_for(heading: str) -> str:
    up = heading.upper()
    if "DEFERRED" in up:
        return "deferred"
    if "PENDING" in up:
        return "pending"
    if "SIGNED OFF" in up or "ACCEPTED" in up or "CONFIRMED" in up:
        return "signed-off"
    return "recorded"


def build_gates() -> dict:
    log_text = LOG.read_text(encoding="utf-8")
    backlog_items = load_backlog_document(BACKLOG)["items"]

    # split the log into (date, heading, body) sections
    sections: list[dict] = []
    matches = list(_HEADING_RE.finditer(log_text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(log_text)
        sections.append(
            {
                "date": m.group(1),
                "heading": m.group(2).strip(),
                "body": log_text[m.end() : end],
                "line": log_text.count("\n", 0, m.start()) + 1,
            }
        )

    prompt_slugs = sorted(p.stem for p in PROMPTS.glob("*.yaml"))

    def unblocks(slug_or_words: list[str]) -> list[str]:
        """J50 (2026-08-21): DECLARED, not inferred. An item that genuinely
        waits on (or builds what was ruled at) a gate says so in its `gates:`
        field, validated against config/gate-prompts/*.yaml slugs by
        tests/unit/test_backlog.py. The previous mention scan serialised each
        item to JSON and matched the slug ANYWHERE, so a prose citation became a
        dependency edge — the census at J50 found 581 edges, the great majority
        citations (a blocked item "unblocked" by seventeen unrelated gates
        through its notes). Same rule the gate-log side already had at J28:
        only an entry ABOUT the gate counts, a citation never does.
        """
        wanted = {w for w in slug_or_words if w in prompt_slugs}
        return [item["id"] for item in backlog_items if wanted & set(item.get("gates") or [])]

    rows: list[dict] = []
    accounted_slugs: set[str] = set()
    cited_slugs: set[str] = set()

    for s in sections:
        # display join: prompt files whose slug appears in the heading or body
        slugs = [p for p in prompt_slugs if p in s["heading"] or p in s["body"]]
        cited_slugs.update(slugs)
        # J28: only an entry ABOUT the gate closes it -- a citation never does
        own = [p for p in slugs if section_accounts_for(p, s["heading"])]
        accounted_slugs.update(own)
        # J50: the unblocks edge hangs off the gate the section is ABOUT (J28's
        # rule), never off a gate the section merely cites — a RECORD that
        # mentions three other gates does not make their declared items its own.
        search_terms = own
        rows.append(
            {
                "kind": "log-entry",
                "date": s["date"],
                "title": s["heading"],
                "status": _status_for(s["heading"]),
                "prompt_files": [f"config/gate-prompts/{p}.yaml" for p in slugs],
                "log_ref": f"config/gate-log.md:{s['line']}",
                "unblocks": unblocks(search_terms) if search_terms else [],
            }
        )

    for p in prompt_slugs:
        if p in accounted_slugs or prompt_self_declares(PROMPTS / f"{p}.yaml"):
            continue
        title = (
            f"{p} (rulings/citations logged — gate sign-off not recorded)"
            if p in cited_slugs
            else f"{p} (gate page rendered — session not yet run)"
        )
        rows.append(
            {
                "kind": "prompt-only",
                "date": None,
                "title": title,
                "status": "open",
                "prompt_files": [f"config/gate-prompts/{p}.yaml"],
                "log_ref": None,
                "unblocks": unblocks([p]),
            }
        )

    return {
        "note": (
            "GENERATED by scripts/render_gates.py -- never hand-edit. "
            "tests/unit/test_gates_json.py fails when this drifts from the record. "
            "The page renders the gate RECORD read-only; acting on gates from the "
            "UI is exactly what the O20 gate decides."
        ),
        "gates": rows,
    }


def main() -> int:
    data = build_gates()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    open_n = sum(1 for g in data["gates"] if g["status"] in ("open", "deferred", "pending"))
    print(f"wrote {OUT} ({len(data['gates'])} gates, {open_n} open/deferred/pending)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
