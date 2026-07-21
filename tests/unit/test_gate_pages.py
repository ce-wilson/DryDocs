"""Unit tests for gate_pages (drydocs/gate_pages.py) — pure, no Neo4j."""
from __future__ import annotations

import pytest

from drydocs.gate_pages import (
    DEFAULT_GATE_PROMPTS_DIR,
    GateSpecError,
    draft_gate_log_entry,
    load_gate_spec,
    render_gate_page,
    spec_from_dict,
)

_DOC = {
    "id": "demo",
    "title": "Demo gate",
    "step": "Step 1",
    "classification": "Internal-Public",
    "summary": "loads a thing",
    "sections": [
        {"title": "A. Scope", "confirmations": ["source is authoritative", "no PII in scope"]},
        {"title": "B. Sign-off", "confirmations": ["safe to confirm"]},
    ],
    "mapping": [{"n": 1, "element": "Folder", "target": ":ControlMFolder", "edge": "—"}],
}


def test_spec_counts_confirmations() -> None:
    spec = spec_from_dict(_DOC)
    assert spec.total_confirmations == 3
    assert spec.sections[0].title == "A. Scope"


def test_spec_requires_title() -> None:
    with pytest.raises(GateSpecError):
        spec_from_dict({"sections": []})


def test_render_has_checkbox_per_confirmation() -> None:
    out = render_gate_page(spec_from_dict(_DOC))
    assert out.count('type="checkbox"') == 3


def test_render_includes_gate_semantics() -> None:
    out = render_gate_page(spec_from_dict(_DOC))
    assert "No graph write" in out
    assert "localStorage" in out                    # persistence wired
    assert "CLASSIFICATION: Internal-Public" in out
    assert "0 / 3" in out                            # progress counter seeded
    assert ":ControlMFolder" in out                       # mapping table rendered


def test_render_is_self_contained() -> None:
    out = render_gate_page(spec_from_dict(_DOC))
    assert out.startswith("<!doctype html>")
    assert "<script>" in out and "<style>" in out


def test_committed_example_spec_loads_and_renders() -> None:
    spec = load_gate_spec(DEFAULT_GATE_PROMPTS_DIR / "bmc-docs-example.yaml")
    assert spec.classification in {"External", "Internal-Public"}
    out = render_gate_page(spec)
    assert spec.title in out
    assert out.count('type="checkbox"') == spec.total_confirmations


_DOC_RICH = {
    **_DOC,
    "meta": {"Module": "drydocs-core", "Registry ref": "controlm-psgmgr — confirmed"},
    "provenance": [
        {
            "label": ":ControlMFolder",
            "source_object": "CM_DEF_VTAB",
            "key": "folder_id",
            "loader": "controlm_folders",
            "properties": [
                {"name": "folder_id", "origin": "source", "from": "TABLE_ID"},
                {"name": "app_code", "origin": "derived", "from": "name pos 3-5", "note": "platform caveat"},
            ],
        }
    ],
}


def test_render_meta_header_card() -> None:
    out = render_gate_page(spec_from_dict(_DOC_RICH))
    assert "controlm-psgmgr" in out and "drydocs-core" in out


def test_render_provenance_origin_badges() -> None:
    out = render_gate_page(spec_from_dict(_DOC_RICH))
    assert "origin-source" in out and "origin-derived" in out
    assert "CM_DEF_VTAB" in out and "platform caveat" in out


def test_provenance_rejects_bad_origin() -> None:
    bad = {**_DOC, "provenance": [{"label": "X", "properties": [{"name": "p", "origin": "guessed"}]}]}
    with pytest.raises(GateSpecError):
        spec_from_dict(bad)


def test_all_committed_specs_follow_the_standard_format() -> None:
    """Every gate spec follows 03-hitl-sme-flow.md §Gate-page format: meta header
    (Module/Source/Registry ref/Classification) + provenance with the source-vs-derived split."""
    specs = sorted(DEFAULT_GATE_PROMPTS_DIR.glob("*.yaml"))
    assert specs, "no committed gate specs found"
    required_meta = {"Module", "Source", "Registry ref", "Classification"}
    for path in specs:
        spec = load_gate_spec(path)
        meta_keys = {k for k, _ in spec.meta}
        assert required_meta <= meta_keys, f"{path.name}: meta missing {required_meta - meta_keys}"
        assert spec.provenance, f"{path.name}: no provenance blocks (source-vs-derived split)"
        origins = {p.origin for b in spec.provenance for p in b.properties}
        assert origins <= {"source", "derived"}, f"{path.name}: bad origins {origins}"


def test_committed_q1q3_spec_loads_and_renders() -> None:
    spec = load_gate_spec(DEFAULT_GATE_PROMPTS_DIR / "controlm-q1q3-phase1.yaml")
    assert spec.classification == "Internal-Public"
    out = render_gate_page(spec)
    assert out.count('type="checkbox"') == spec.total_confirmations
    assert "origin-derived" in out                    # provenance split rendered
    assert "CONTAINS_FOLDER" in out                   # proposed edge visible


# ---------------------------------------------------------------------------
# O25 — the M1 drafting affordance (ui-write-surface gate SME-2, 2026-07-21):
# draft_gate_log_entry is the pure reference implementation of the page's
# client-side assembly (the payload embeds prebuilt lines, JS only selects).
# ---------------------------------------------------------------------------

def test_draft_entry_all_ticked_proposes_signed_off() -> None:
    spec = spec_from_dict(_DOC)
    all_ids = {f"c{si}_{ci}" for si, s in enumerate(spec.sections)
               for ci in range(len(s.confirmations))}
    entry = draft_gate_log_entry(spec, ticked=all_ids, date="2026-07-21")
    assert entry.startswith("## 2026-07-21 — Demo gate (demo) — SIGNED OFF\n")
    assert "- **Ticked: 3/3**" in entry
    assert "  - **A. Scope — 2/2**" in entry
    assert "  - **B. Sign-off — 1/1**" in entry
    assert "    - [x] safe to confirm" in entry
    assert "[ ]" not in entry
    assert "- **Scope:** Step 1 — DRAFT assembled client-side" in entry
    assert "the page wrote NOTHING server-side" in entry
    assert entry.rstrip().endswith("nothing is applied by this draft>")


def test_draft_entry_partially_ticked_is_pending() -> None:
    spec = spec_from_dict(_DOC)
    entry = draft_gate_log_entry(spec, ticked={"c0_0"})
    # date defaults to a placeholder; anything short of all ticks drafts PENDING
    assert entry.startswith("## YYYY-MM-DD — Demo gate (demo) — PENDING\n")
    assert "- **Ticked: 1/3**" in entry
    assert "  - **A. Scope — 1/2**" in entry
    assert "    - [x] source is authoritative" in entry
    assert "    - [ ] no PII in scope" in entry
    assert "    - [ ] safe to confirm" in entry


def test_draft_entry_unticked_and_empty_spec_are_pending() -> None:
    assert "— PENDING" in draft_gate_log_entry(spec_from_dict(_DOC))
    empty = spec_from_dict({"id": "e", "title": "Empty gate", "sections": []})
    assert "— PENDING" in draft_gate_log_entry(empty)  # 0/0 never claims sign-off


def test_render_embeds_the_draft_affordance() -> None:
    """The page carries the drafting control + the prebuilt payload lines the
    JS selects from (so browser output cannot drift from the Python
    reference), and adds NO extra checkboxes (the count guard's invariant)."""
    out = render_gate_page(spec_from_dict(_DOC))
    assert "Draft gate-log entry" in out
    assert "Copy snippet" in out and "Download .md" in out
    assert '"    - [x] safe to confirm"' in out    # prebuilt ticked line, JSON-embedded
    assert '"    - [ ] safe to confirm"' in out    # ... and its unticked twin
    assert "gate-log-entry-demo-draft.md" in out
    assert "this page writes nothing" in out
    assert out.count('type="checkbox"') == 3       # affordance adds no checkboxes


def test_render_page_footer_carries_paths() -> None:
    """SME request 2026-07-21: gate pages show their own rendered-file path
    (with a copy button) plus the durable spec path, like design-doc renders."""
    spec = load_gate_spec(DEFAULT_GATE_PROMPTS_DIR / "ui-write-surface.yaml")
    out = render_gate_page(spec, page_path="C:/coding/projects/DryDocs/var/gate-ui-write-surface.html")
    assert "C:/coding/projects/DryDocs/var/gate-ui-write-surface.html" in out
    assert "Copy path" in out
    assert "config/gate-prompts/ui-write-surface.yaml" in out
    # without a page_path the footer still names the spec (system of record)
    bare = render_gate_page(spec)
    assert "Copy path" not in bare
    assert "config/gate-prompts/ui-write-surface.yaml" in bare
