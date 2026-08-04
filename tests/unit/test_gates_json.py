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


# --------------------------------------------------------------------------- #
# J28 — a citation never closes a gate; only an entry ABOUT it does
# --------------------------------------------------------------------------- #
def test_a_citation_or_partial_ruling_never_accounts_for_a_gate():
    """The mechanism pin, on the exact three-entry pattern that hid
    seal-app-ref-edge-reshape for six weeks (as the log stood 2026-08-01):
    a partial-ruling entry heading-naming the slug and a DIFFERENT gate's
    sign-off citing the file in its body must both leave the gate open;
    the heading-named sign-off that arrived at K7 (2026-08-03) closes it."""
    g = _generator()
    slug = "seal-app-ref-edge-reshape"
    partial = "PARTIAL RULING: PAT grain keying (C17; gate `seal-app-ref-edge-reshape`, a-c)"
    other_gates_signoff = "BusinessApplication identity: `seal_id` → `app_id` — SIGNED OFF"
    assert not g.section_accounts_for(slug, partial)
    assert not g.section_accounts_for(slug, other_gates_signoff)  # body cite is not a heading
    assert g.section_accounts_for(
        slug, "GATE: seal-app-ref-edge-reshape (backlog K7) — SIGNED OFF, 24/24"
    )
    # prose headings still match through slugification (the K2 shape)
    assert g.section_accounts_for(
        "seal-attribution-match-policy", "SEAL attribution match policy gate — SIGNED OFF (K2)"
    )


def test_self_declaration_is_a_marker_line_not_a_prose_mention():
    """A prompt may account for itself with a `# SIGNED OFF ...` header marker
    (the crosswalk gates, whose log headings predate the slug convention) — but
    prose that mentions ANOTHER gate's sign-off must not count
    (code-graph-package-layer's 'RE-OPENS ... (SIGNED OFF' line)."""
    g = _generator()
    prompts = REPO / "config" / "gate-prompts"
    assert g.prompt_self_declares(prompts / "airflow-crosswalk.yaml")
    assert g.prompt_self_declares(prompts / "autosys-crosswalk.yaml")
    assert not g.prompt_self_declares(prompts / "code-graph-package-layer.yaml")


def test_unsigned_but_cited_gates_render_open():
    """The live pins. The item's original proof case (seal-app-ref-edge-reshape)
    was overtaken by events — K7 signed it 2026-08-03 with a heading-named
    entry, so it is correctly ABSENT from the open rows (the mechanism test
    above pins its pre-K7 pattern instead). The fix's live catches: the two
    gates whose only log presence is citations or a pending entry."""
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    prompt_only = {
        g["prompt_files"][0]: g for g in committed["gates"] if g["kind"] == "prompt-only"
    }
    for slug in ("software-usage-patterns", "seal-tom-attribution-reshape"):
        row = prompt_only.get(f"config/gate-prompts/{slug}.yaml")
        assert (
            row is not None
        ), f"{slug} has rulings/citations but no recorded sign-off — must render open"
        assert row["status"] == "open"
        assert "sign-off not recorded" in row["title"]
    assert "config/gate-prompts/seal-app-ref-edge-reshape.yaml" not in prompt_only, (
        "K7 signed this gate 2026-08-03 (heading-named entry) — an open row here "
        "means the classifier stopped honouring heading-named sign-offs"
    )
