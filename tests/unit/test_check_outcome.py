"""ADR 0021's instrument (CORE10): the three-outcome type and the declared probe registry.

Two things are guarded. The TYPE's two properties - it never coerces to a boolean,
and every state renders itself - each with a positive and a negative case. And the
REGISTRY: every dotted name in ``drydocs_core.check_outcome.PROBES`` imports (a
registered probe that no longer exists fails - the list is shrink-only in that
direction) and its return annotation, read from the tree through
``tests/source_scan.return_annotation`` (J66), is the type. A probe returning a
bare boolean, or carrying no annotation, fails by name.

What this does NOT do, so it is not over-read: it does not find unregistered
probes. Registration is the act the rule asks for.
"""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path

import pytest

from drydocs_core.check_outcome import (
    PROBES,
    REASON_MIN,
    CheckOutcome,
    Outcome,
    checked_clean,
    findings,
    not_checked,
)
from tests.source_scan import return_annotation, source_text

# --- the type ---------------------------------------------------------------------


def test_three_states_and_only_three() -> None:
    assert {s.value for s in Outcome} == {"checked-clean", "findings", "not-checked"}


def test_the_type_never_coerces_to_a_boolean() -> None:
    """The negative case is the one that matters: ``if outcome:`` must not be writable."""
    for outcome in (
        checked_clean(size=3),
        findings(["x"]),
        not_checked("the graph was not reachable from this venue, so nothing was scanned"),
    ):
        with pytest.raises(TypeError, match="does not coerce to a boolean"):
            bool(outcome)
        with pytest.raises(TypeError):
            if outcome:  # the forbidden shape, on purpose
                pass
        with pytest.raises(TypeError):
            _ = not outcome


def test_is_clean_is_true_only_for_checked_clean() -> None:
    assert checked_clean().is_clean
    assert not findings(["a finding"]).is_clean
    assert not not_checked("no seam was given, so the graph layer never ran here").is_clean
    assert not_checked("no seam was given, so the graph layer never ran here").is_not_checked
    assert not findings(["a finding"]).is_not_checked


def test_a_not_checked_result_needs_a_written_reason() -> None:
    with pytest.raises(ValueError, match=f"at least {REASON_MIN}"):
        not_checked("skipped")
    with pytest.raises(ValueError, match=f"at least {REASON_MIN}"):
        CheckOutcome(Outcome.NOT_CHECKED, reason=None)
    ok = not_checked("the suite was skipped by --skip-tests, and a skipped suite is no proof")
    assert ok.reason and len(ok.reason) >= REASON_MIN


def test_an_empty_findings_list_is_refused_as_the_seventh_spelling() -> None:
    with pytest.raises(ValueError, match="CHECKED_CLEAN - say so"):
        findings([])
    with pytest.raises(ValueError, match="cannot carry findings"):
        CheckOutcome(Outcome.CHECKED_CLEAN, findings=("x",))
    with pytest.raises(ValueError, match="carries no findings"):
        CheckOutcome(
            Outcome.NOT_CHECKED,
            findings=("x",),
            reason="a reason long enough to pass the length rule but the findings are wrong",
        )


def test_every_state_renders_itself_and_never_as_a_number_or_a_pass() -> None:
    assert checked_clean(size=1204, subject="1,204 rows").render() == "checked, clean (1,204 rows)"
    assert checked_clean(size=0).render() == "checked, clean (0 scanned)"
    assert findings(["a", "b", "c"], size=45).render() == "3 findings over 45 scanned"
    assert findings(["a"]).render() == "1 finding"
    line = not_checked("the base did not resolve, so the range could not be read at all").render()
    assert line.startswith("NOT CHECKED - the base did not resolve")
    assert "PASS" not in line and not line[0].isdigit()
    stamped = checked_clean(venue="desktop, neo4jtest").render()
    assert stamped.endswith("[venue: desktop, neo4jtest]")


def test_size_travels_with_the_findings_and_clean_over_zero_is_visible() -> None:
    out = findings(["f"], size=17)
    assert out.count == 1 and out.size == 17
    assert checked_clean(size=0).size == 0  # visible, not hidden behind "clean"
    with pytest.raises(ValueError):
        checked_clean(size=-1)


# --- the registry -----------------------------------------------------------------


def _resolve(dotted: str):
    """Import the object a dotted name points at; the module part is the longest
    importable prefix, the rest is attribute access."""
    parts = dotted.split(".")
    for split in range(len(parts) - 1, 0, -1):
        try:
            obj = importlib.import_module(".".join(parts[:split]))
        except ModuleNotFoundError:
            continue
        for attr in parts[split:]:
            obj = getattr(obj, attr)
        return obj
    raise ModuleNotFoundError(dotted)


def _annotation_of(dotted: str) -> str | None:
    """The registered probe's return annotation, read from its SOURCE FILE through
    the shared helper (J66) - never from a name heuristic, never from prose."""
    obj = _resolve(dotted)
    path = Path(inspect.getsourcefile(obj))  # type: ignore[arg-type]
    return return_annotation(source_text(path), obj.__qualname__)


def _is_the_type(annotation: str | None) -> bool:
    return annotation is not None and annotation.strip("'\"").split(".")[-1] == "CheckOutcome"


def test_the_registry_is_declared_and_not_empty() -> None:
    assert PROBES, "the registry is the instrument; an empty one guards nothing"
    assert len(set(PROBES)) == len(PROBES)


@pytest.mark.parametrize("dotted", PROBES)
def test_every_registered_probe_resolves_and_returns_the_type(dotted: str) -> None:
    """Shrink-only in one direction: a registered name that no longer resolves fails
    here rather than rotting into a claim; and the annotation must be the type."""
    try:
        obj = _resolve(dotted)
    except (ModuleNotFoundError, AttributeError) as exc:
        pytest.fail(f"registered probe {dotted!r} no longer resolves ({exc}) - remove or fix")
    assert callable(obj), dotted
    annotation = _annotation_of(dotted)
    assert _is_the_type(annotation), (
        f"{dotted} is a registered probe but its return annotation is {annotation!r} - "
        "a probe returns CheckOutcome, never a bare boolean and never nothing (ADR 0021 D2)"
    )


def test_the_annotation_check_has_a_positive_and_a_negative_case() -> None:
    """The guard's own instrument, exercised on inline source so a change to the
    helper cannot silently turn it vacuous (J76: check the instrument)."""
    src = (
        "from drydocs_core.check_outcome import CheckOutcome\n"
        "def good() -> CheckOutcome: ...\n"
        "def qualified() -> check_outcome.CheckOutcome: ...\n"
        "def bare() -> bool: ...\n"
        "def silent(): ...\n"
    )
    assert _is_the_type(return_annotation(src, "good"))
    assert _is_the_type(return_annotation(src, "qualified"))
    assert not _is_the_type(return_annotation(src, "bare"))
    assert not _is_the_type(return_annotation(src, "silent"))
