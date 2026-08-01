"""O19 gates.json drift guard (the enforcement-matrix pattern): a gate-log
entry or gate-prompt file with no row cannot ship."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
COMMITTED = REPO / "web" / "src" / "generated" / "gates.json"


def _generator():
    spec = importlib.util.spec_from_file_location(
        "render_gates", REPO / "scripts" / "render_gates.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_committed_gates_match_regeneration():
    fresh = _generator().build_gates()
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    assert committed == fresh, (
        "gates.json drifted from the gate record — run: "
        "python scripts/render_gates.py and commit the result"
    )


def test_every_log_entry_and_prompt_has_a_row():
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    log_text = (REPO / "config" / "gate-log.md").read_text(encoding="utf-8")
    n_entries = len(re.findall(r"^## \d{4}-\d{2}-\d{2}", log_text, re.MULTILINE))
    n_log_rows = sum(1 for g in committed["gates"] if g["kind"] == "log-entry")
    assert n_log_rows == n_entries, "a gate-log entry has no gates.json row"

    covered_prompts = {p for g in committed["gates"] for p in g["prompt_files"]}
    for p in sorted((REPO / "config" / "gate-prompts").glob("*.yaml")):
        assert (
            f"config/gate-prompts/{p.stem}.yaml" in covered_prompts
        ), f"gate prompt {p.name} has no gates.json row"
