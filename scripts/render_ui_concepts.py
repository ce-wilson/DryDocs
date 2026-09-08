"""Generate the UI-concept provenance artifact for the console header (WEB18).

Reads ``config/taxonomy/ui-concepts.yaml`` and emits
``web/src/generated/ui-concepts.json`` — the console reads the artifact, never
the yaml, and never hand-writes the sentence. A second definition of Tower is
the whole defect WEB18 exists to close, so the header's hover has exactly one
source and it is the guarded one.

WHY AN ARTIFACT RATHER THAN A LIVE CALL. WEB18's clause (c) left the choice
open and it was ruled 2026-09-08: the render step, on the gates.json /
enforcement-matrix.json / context-types.json precedent. Two reasons carried it.
A page HEADER should not depend on a request — a hover that is empty whenever
the API is cold is a provenance note that disappears exactly when someone is
debugging. And an artifact is drift-guarded, where a live read is only as
current as the last deploy.

WHAT IT CARRIES, AND THE LINE IT DOES NOT CROSS. Every row's term, aliases,
cardinality, member titles, the in-repo source that defines it, and the
declared ``graph_binding``. It does NOT compose a sentence: the console builds
its own wording from these fields, because a rendered sentence in a generated
file is a second definition wearing a build step. And nothing here may assert
what a term MEANS in the ontology — ``graph_binding`` is carried as declared
(``none`` today for Tower) precisely so the console can say "not from the
graph" without saying what it IS instead. That mapping is the HITL gate's
question; ``config/taxonomy/ui-concepts.yaml``'s own header states the boundary
and this artifact inherits it rather than restating it.

Rides the default ``render_board.py`` run (the J17/J20/N4 one-entry-point
idiom); ``tests/unit/test_ui_concepts_json.py`` is the drift guard.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SOURCE = REPO / "config" / "taxonomy" / "ui-concepts.yaml"
OUT = REPO / "web" / "src" / "generated" / "ui-concepts.json"


def build_ui_concepts() -> dict:
    data = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
    return {
        "schema": data["schema"],
        "updated": str(data["updated"]),
        "concepts": [
            {
                "term": c["term"],
                "aliases": list(c.get("aliases") or []),
                "source": c["source"],
                "source_kind": c["source_kind"],
                "cardinality": c["cardinality"],
                "members": [m["title"] for m in (c.get("members") or [])],
                # Carried as DECLARED. 'none' is a statement about where the
                # term comes from, never about what it maps to.
                "graph_binding": c["graph_binding"],
            }
            for c in data["concepts"]
        ],
    }


def main() -> None:
    view = build_ui_concepts()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(view, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT} ({len(view['concepts'])} concepts)")


if __name__ == "__main__":
    main()
