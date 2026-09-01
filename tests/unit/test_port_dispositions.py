"""The generated port disposition table matches its sources (J69).

`docs/port/port-dispositions.md` is a DERIVED artifact — the same
generated-artifact + drift-test pattern the board, the enforcement matrix and
`gates.json` use. It exists because a port is applied by disposition class rather
than in commit order, and the classes must come from `PORT-MANIFEST.yaml` rather
than from a hand-typed copy of it.

The hand-typed copy is not hypothetical: J68 (2026-09-01) removed four disposition
assertions from `.claude/skills/reconcile-port/SKILL.md`, two of which had drifted
into contradicting the manifest, one of which would have flattened the company's
ontology entries had its path still existed. A generated table cannot drift out of
step with the manifest; that is the whole reason this one is generated.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO = Path(__file__).resolve().parents[2]
RENDERER = REPO / "scripts" / "render_port_dispositions.py"
RENDERED = REPO / "docs" / "port" / "port-dispositions.md"
MANIFEST = REPO / "PORT-MANIFEST.yaml"
PORT_PROMPT = REPO / "docs" / "port" / "port-prompt.md"


def _renderer():
    """Import the script by path — it lives under scripts/, not an importable package."""
    spec = importlib.util.spec_from_file_location("render_port_dispositions", RENDERER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_the_committed_table_matches_a_fresh_render() -> None:
    """Re-render from the same default base and compare. A diff means the committed
    artifact stopped describing the manifest — which is the state this file exists to
    make impossible to reach quietly."""
    module = _renderer()
    base = module.newest_base_tag()
    if not base:
        pytest.skip("no port-base-* tag in this clone — nothing to render against")
    doc = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    fresh = module.render(base, module.changed_paths(base), doc)
    assert RENDERED.read_text(encoding="utf-8") == fresh, (
        f"{RENDERED.relative_to(REPO)} is stale — re-run "
        "`PYTHONPATH=. python scripts/render_port_dispositions.py` and commit the result"
    )


def test_every_disposition_the_manifest_uses_has_an_apply_rule() -> None:
    """APPLY_ORDER is the operator-facing half of the disposition vocabulary. A class
    the manifest can emit but the renderer has no rule for would print as
    '(not in APPLY_ORDER — add it)' in the artifact, which is a fallback and not a
    plan. Fail here instead, where the message can say what to do."""
    module = _renderer()
    doc = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    used = {row["disposition"] for row in doc["rows"]}
    covered = {disposition for disposition, _rule in module.APPLY_ORDER}
    missing = sorted(used - covered)
    assert not missing, (
        f"dispositions the manifest uses with no apply rule: {missing}. "
        "Add each to APPLY_ORDER in scripts/render_port_dispositions.py, in the "
        "position a session should work it."
    )


def test_the_apply_section_sits_above_the_ledger_the_coverage_guard_reads() -> None:
    """J69 (c), and it is a real trap rather than a formality.

    ``drydocs/port_preflight.py`` reads ONLY between the ``STEP LEDGER`` and
    ``ACCEPTANCE GATE`` markers, and ``cited_shas`` harvests every backticked sha in
    that span. Put the apply section INSIDE those markers and its citations start
    counting as ledger coverage — commits would read as cited because a disposition
    table happened to name their sha. Above the marker, it is prose; below it, it is
    evidence. That distinction is worth a guard.
    """
    text = PORT_PROMPT.read_text(encoding="utf-8")
    apply_at = text.index("APPLY BY DISPOSITION")
    ledger_at = text.index("STEP LEDGER")
    assert apply_at < ledger_at, (
        "the APPLY BY DISPOSITION section must sit ABOVE the STEP LEDGER marker — "
        "inside it, its backticked shas would be counted as ledger citations by "
        "drydocs/port_preflight.py:cited_shas"
    )
