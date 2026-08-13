"""Generate the context-type vocabulary artifact for the intake page (O45).

Reads ``config/taxonomy/context-types.yaml`` and emits
``web/src/generated/context-types.json`` — the console dropdown reads the
artifact, never the yaml, and never hardcodes the list. Active entries only
carry into ``context_types``; retired ids are kept in ``retired`` so the UI
can still resolve them on historical intake records.

Rides the default ``render_board.py`` run (the J17/J20/N4 one-entry-point
idiom); ``tests/unit/test_context_types.py`` is the drift guard.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SOURCE = REPO / "config" / "taxonomy" / "context-types.yaml"
OUT = REPO / "web" / "src" / "generated" / "context-types.json"


def build_context_types() -> dict:
    data = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
    active = [e for e in data["context_types"] if e["status"] == "active"]
    retired = [e for e in data["context_types"] if e["status"] == "retired"]
    return {
        "schema": data["schema"],
        "updated": str(data["updated"]),
        "context_types": [
            {"id": e["id"], "label": e["label"], "description": " ".join(e["description"].split())}
            for e in active
        ],
        "retired": [{"id": e["id"], "label": e["label"]} for e in retired],
    }


def main() -> None:
    view = build_context_types()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(view, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT} ({len(view['context_types'])} active, {len(view['retired'])} retired)")


if __name__ == "__main__":
    main()
