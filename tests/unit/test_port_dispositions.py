"""The port disposition renderer classifies by the manifest, and only by it (J69).

`docs/port/port-dispositions.md` is generated per-apply and is NOT committed —
its range is `<base>..HEAD`, so a committed copy would go stale on every commit and
a guard over it would red the suite constantly. A guard people learn to work around
is worse than no guard (J66's lesson at the other end), so the MECHANISM is guarded
here and the output is working state, gitignored like any other per-run artifact.

What must hold is that the classification comes from `PORT-MANIFEST.yaml` rather
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
MANIFEST = REPO / "PORT-MANIFEST.yaml"
PORT_PROMPT = REPO / "docs" / "port" / "port-prompt.md"


def _renderer():
    """Import the script by path — it lives under scripts/, not an importable package."""
    spec = importlib.util.spec_from_file_location("render_port_dispositions", RENDERER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_classify_reads_the_manifest_in_first_match_order() -> None:
    """The renderer must resolve a path the way the manifest does — specific row
    first, glob after, `default_ok` only once every row has missed, DEFAULT last.
    Synthetic rows, so this tests the logic and not today's manifest content."""
    module = _renderer()
    doc = {
        "rows": [
            {"path": "config/gate-log.md", "disposition": "union-append"},
            {"path": "config/**", "disposition": "canonical-producer"},
            {"path": "docs/x.md", "disposition": "per-entry", "entry_rule": "  keyed by id  "},
        ],
        "default_ok": [{"path": "tests/**", "reason": "expectations diverge"}],
    }
    # the specific row wins over the later glob
    assert module.classify("config/gate-log.md", doc)[:2] == ("union-append", "config/gate-log.md")
    # the glob catches everything else under it
    assert module.classify("config/other.yaml", doc)[:2] == ("canonical-producer", "config/**")
    # entry_rule comes back whitespace-normalised for the renderer
    assert module.classify("docs/x.md", doc)[2] == "keyed by id"
    # default_ok is consulted only after every row misses — J16's whole distinction
    assert module.classify("tests/unit/test_x.py", doc)[:2] == ("default_ok", "tests/**")
    # and a path in neither is DEFAULT, which is "nobody thought about it"
    assert module.classify("some/new/path.py", doc)[:2] == ("DEFAULT", "(no row)")


def test_render_buckets_by_class_and_never_invents_one() -> None:
    """Every path lands in exactly one class, the counts add up, and a disposition
    with no paths prints no section — an empty class in an apply plan reads as work
    that was skipped rather than work that did not exist."""
    module = _renderer()
    doc = {
        "rows": [
            {"path": "a/**", "disposition": "canonical-producer"},
            {"path": "b/**", "disposition": "per-entry", "entry_rule": "rows union by id"},
        ],
        "default_ok": [],
    }
    text = module.render("port-base-test", ["a/one.py", "a/two.py", "b/three.yaml"], doc)
    assert "**3 changed paths**" in text
    assert "`canonical-producer` | 2 |" in text
    assert "`per-entry` | 1 |" in text
    assert "rows union by id" in text, "the entry_rule must travel with its class"
    assert "union-append" not in text, "a class with no paths must not print a section"


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

    ``drydocs/port/port_preflight.py`` reads ONLY between the ``STEP LEDGER`` and
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
        "drydocs/port/port_preflight.py:cited_shas"
    )
