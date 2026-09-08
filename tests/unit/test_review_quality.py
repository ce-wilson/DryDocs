"""O51 — reviewer-quality signals, and the separation the whole item rests on.

THE CLAIM UNDER TEST is not "the arithmetic is right" (though it is checked). It
is that a LIMIT CANNOT BLOCK ANYONE. `review_quality.py` measures and
`intake.py` blocks, a person stands between them, and that is asserted by
reading the code rather than by trusting the paragraph that says so.

The derivation takes rows as arguments, so every rule below is tested without a
store — the shape `undeclared_constraints` uses for live constraint rows, and
the reason both are unit-testable at all.
"""

from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from drydocs_api.review_quality import (
    AUTO_ACCEPT_UNAVAILABLE,
    Limits,
    ReviewFloor,
    ReviewQualityConfigError,
    decisions,
    limits_as_dict,
    load_limits,
    summarize,
)
from tests.source_scan import called_names, imported_modules, source_text

REPO = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 9, 7, 12, 0, tzinfo=UTC)

LIMITS = Limits(
    window_days=30,
    min_decisions_for_flag=5,
    auto_accept_rate_max=0.9,
    admin_return_rate_max=0.25,
    too_fast_rate_max=0.3,
    review_floor=ReviewFloor(min_review_seconds=60, seconds_per_kb=2.0, max_review_seconds=900),
)


def _at(days_ago: float) -> str:
    return (NOW - timedelta(days=days_ago)).isoformat()


def _submit(intake_id: str, actor: str, days_ago: float, frm: str = "correlated") -> dict:
    return {
        "intake_id": intake_id,
        "at": _at(days_ago),
        "actor": actor,
        "action": f"transition:{frm}->sme-confirmed",
    }


def _returned(intake_id: str, days_ago: float, actor: str = "admin1") -> dict:
    return {
        "intake_id": intake_id,
        "at": _at(days_ago),
        "actor": actor,
        "action": "transition:sme-confirmed->admin-returned",
    }


def _upload(intake_id: str, days_ago: float, size: int = 1024) -> dict:
    return {"intake_id": intake_id, "uploaded_at": _at(days_ago), "size": size}


# ── the limits file ──────────────────────────────────────────────────────────


def test_the_shipped_limits_file_loads_and_declares_every_key() -> None:
    limits = load_limits()
    assert limits.window_days > 0
    assert 0 < limits.admin_return_rate_max <= 1
    assert limits.review_floor.max_review_seconds >= limits.review_floor.min_review_seconds


def test_a_missing_or_wrong_file_raises_rather_than_defaulting(tmp_path) -> None:
    """A silent default would have two machines flagging different people from
    the same data — the exact failure the file exists to prevent."""
    with pytest.raises(ReviewQualityConfigError):
        load_limits(tmp_path / "nope.yaml")

    wrong = tmp_path / "wrong.yaml"
    wrong.write_text("schema: something.else.v1\n", encoding="utf-8")
    with pytest.raises(ReviewQualityConfigError):
        load_limits(wrong)

    partial = tmp_path / "partial.yaml"
    partial.write_text("schema: drydocs.review-quality.v1\nwindow_days: 30\n", encoding="utf-8")
    with pytest.raises(ReviewQualityConfigError):
        load_limits(partial)


def test_the_limits_file_declares_no_way_to_block_anyone() -> None:
    """The absence is the design, so it is asserted rather than assumed. A key
    that turned a threshold into an action would make every other guard here a
    formality."""
    text = (REPO / "config" / "review-quality.yaml").read_text(encoding="utf-8")
    keys = {line.split(":")[0].strip() for line in text.splitlines() if ":" in line}
    assert not {k for k in keys if "block" in k.lower() or "auto_" in k and "accept" not in k}


# ── the review floor ─────────────────────────────────────────────────────────


def test_the_floor_scales_with_evidence_and_then_stops() -> None:
    floor = LIMITS.review_floor
    assert floor.seconds_for(0) == 60
    assert floor.seconds_for(1024) == 62
    # the cap: nobody reads a 10 MB attachment line by line, and an uncapped
    # floor would make every large record "too fast" forever
    assert floor.seconds_for(100 * 1024 * 1024) == 900


# ── what a decision is ───────────────────────────────────────────────────────


def test_only_submits_inside_the_window_count() -> None:
    events = [
        _submit("i1", "sme1", days_ago=1),
        _submit("i2", "sme1", days_ago=40),  # outside the window
        {"intake_id": "i3", "at": _at(1), "actor": "sme1", "action": "created"},
        {
            "intake_id": "i4",
            "at": _at(1),
            "actor": "sme1",
            "action": "transition:draft->ontology-reviewed",
        },
    ]
    made = decisions(events, [], LIMITS, now=NOW)
    assert [d.intake_id for d in made] == ["i1"]


def test_both_paths_into_sme_confirmed_are_submits() -> None:
    """`correlated ->` is a first submit and `admin-returned ->` is a re-submit.
    Counting only the first would make a reviewer who is returned repeatedly
    look like a reviewer who submits rarely."""
    events = [
        _submit("i1", "sme1", days_ago=3, frm="correlated"),
        _submit("i1", "sme1", days_ago=1, frm="admin-returned"),
    ]
    assert len(decisions(events, [], LIMITS, now=NOW)) == 2


def test_review_time_runs_from_the_last_hand_over_not_the_last_event() -> None:
    """THE RULING, asserted. The record was uploaded five days ago, returned by
    an admin an hour before the re-confirm, and re-confirmed. The reviewer had
    it for an hour, not for five days — measuring from the upload would make a
    careful re-review look like a week of neglect, and measuring from the
    previous event of ANY kind would measure somebody else's action."""
    events = [
        _submit("i1", "sme1", days_ago=4),
        _returned("i1", days_ago=1 / 24),  # one hour before now
        _submit("i1", "sme1", days_ago=0, frm="admin-returned"),
    ]
    made = decisions(events, [_upload("i1", days_ago=5)], LIMITS, now=NOW)
    resubmit = made[-1]
    assert resubmit.review_seconds == pytest.approx(3600, abs=2)
    assert not resubmit.too_fast


def test_a_decision_with_no_hand_over_has_no_review_time_and_is_not_too_fast() -> None:
    """An intake whose upload predates the event log has nothing to measure
    from. Counting that as a violation would flag people for the deployment
    date, so unknown is unknown — not fast."""
    [made] = decisions([_submit("i1", "sme1", days_ago=1)], [], LIMITS, now=NOW)
    assert made.review_seconds is None
    assert made.too_fast is False


def test_too_fast_is_measured_against_this_record_s_own_floor() -> None:
    events = [_submit("i1", "sme1", days_ago=1)]
    # handed over 30 seconds before the submit, with 1 KB of evidence: floor 62s
    evidence = [_upload("i1", days_ago=1 + 30 / 86400, size=1024)]
    [made] = decisions(events, evidence, LIMITS, now=NOW)
    assert made.review_seconds == pytest.approx(30, abs=2)
    assert made.floor_seconds == 62
    assert made.too_fast


def test_a_return_after_the_submit_marks_that_submit_returned() -> None:
    """And a return BEFORE it does not: an earlier return is what put the record
    back in front of the reviewer, not a judgment on this submission."""
    events = [
        _submit("i1", "sme1", days_ago=5),
        _returned("i1", days_ago=4),
        _submit("i1", "sme1", days_ago=3, frm="admin-returned"),
    ]
    first, second = decisions(events, [], LIMITS, now=NOW)
    assert first.returned_by_admin is True
    assert second.returned_by_admin is False


def test_a_decision_keeps_per_decision_detail_not_only_a_rate() -> None:
    """The future confirmation-weight trust model needs the individual acts; a
    rate cannot be un-averaged. `modified_fields` is the O48-shaped hole — the
    place exists, and is empty because nothing proposes anything yet."""
    [made] = decisions([_submit("i1", "sme1", days_ago=1)], [_upload("i1", 2)], LIMITS, now=NOW)
    assert made.intake_id == "i1" and made.persona_id == "sme1"
    assert made.from_status == "correlated"
    assert made.evidence_bytes == 1024
    assert made.modified_fields == []


# ── the rollups and the flags ────────────────────────────────────────────────


def _many(actor: str, count: int, *, returned: int = 0) -> tuple[list[dict], list[dict]]:
    events: list[dict] = []
    evidence: list[dict] = []
    for i in range(count):
        intake = f"i{i}"
        events.append(_submit(intake, actor, days_ago=10 - i * 0.1))
        evidence.append(_upload(intake, days_ago=10 - i * 0.1 + 1))
        if i < returned:
            events.append(_returned(intake, days_ago=10 - i * 0.1 - 0.05))
    return events, evidence


def test_rates_are_reported_and_nothing_is_flagged_below_the_floor() -> None:
    """One return out of two submissions is a 50% rate and is not evidence of
    anything. Suppressing the FLAG is not the same as hiding the data, so both
    halves are asserted."""
    events, evidence = _many("sme1", 2, returned=2)
    [persona] = summarize(decisions(events, evidence, LIMITS, now=NOW), LIMITS)
    assert persona.submissions == 2
    assert persona.admin_return_rate == 1.0
    assert persona.flags == []


def test_crossing_a_limit_flags_with_the_metric_that_tripped() -> None:
    events, evidence = _many("sme1", 8, returned=6)
    [persona] = summarize(decisions(events, evidence, LIMITS, now=NOW), LIMITS)
    [flag] = [f for f in persona.flags if f.metric == "admin_return_rate"]
    assert flag.value == pytest.approx(0.75)
    assert flag.limit == 0.25
    assert "6 of 8" in flag.detail


def test_auto_accept_is_null_with_its_reason_and_can_never_flag() -> None:
    """THE O56 CLAUSE. A zero here reads as a reviewer who modifies every
    candidate — the best possible score, invented from no data. So it is null,
    the reason travels beside it, and no flag can name it."""
    events, evidence = _many("sme1", 20, returned=20)
    personas = summarize(decisions(events, evidence, LIMITS, now=NOW), LIMITS)
    for persona in personas:
        assert persona.auto_accept_rate is None
        assert "O48" in persona.auto_accept_unavailable_because
        assert persona.auto_accept_unavailable_because == AUTO_ACCEPT_UNAVAILABLE
        assert not [f for f in persona.flags if f.metric == "auto_accept_rate"]


def test_personas_come_back_by_id_and_not_worst_first() -> None:
    """ "Coaching and triage, not a leaderboard" (plan §8). A list sorted by the
    worst number IS a leaderboard whatever the heading says."""
    events_a, evidence_a = _many("zeta", 8, returned=8)
    events_b, evidence_b = _many("alpha", 8, returned=0)
    events = events_a + [dict(e, intake_id="b" + e["intake_id"]) for e in events_b]
    evidence = evidence_a + [dict(e, intake_id="b" + e["intake_id"]) for e in evidence_b]
    personas = summarize(decisions(events, evidence, LIMITS, now=NOW), LIMITS)
    assert [p.persona_id for p in personas] == ["alpha", "zeta"]


def test_the_median_review_time_ignores_decisions_with_no_reading() -> None:
    events = [_submit("i1", "sme1", days_ago=1), _submit("i2", "sme1", days_ago=1)]
    evidence = [_upload("i1", days_ago=1 + 120 / 86400)]  # only i1 has a hand-over
    [persona] = summarize(decisions(events, evidence, LIMITS, now=NOW), LIMITS)
    assert persona.median_review_seconds == pytest.approx(120, abs=2)


def test_the_blocked_flag_rides_with_the_rollup() -> None:
    events, evidence = _many("sme1", 6)
    [persona] = summarize(decisions(events, evidence, LIMITS, now=NOW), LIMITS, blocked=["sme1"])
    assert persona.blocked is True


def test_the_limits_travel_to_the_console_so_it_holds_no_second_copy() -> None:
    payload = limits_as_dict(LIMITS)
    assert payload["admin_return_rate_max"] == 0.25
    assert payload["review_floor"]["min_review_seconds"] == 60


# ── the separation: measure here, block there ────────────────────────────────


def test_the_measuring_module_cannot_block_anyone() -> None:
    """Structural, not a promise. `review_quality` imports nothing that can
    block and calls no blocking function — read off its imports and its calls,
    never off its prose (J66), because this module's own docstring explains the
    very separation being checked."""
    source = source_text(REPO / "drydocs_api" / "review_quality.py")
    imported = imported_modules(source)
    assert not any("intake" in module for module in imported), imported
    called = called_names(source)
    assert not {"block_persona", "unblock_persona"} & called, sorted(called)


def _handlers_referencing(source: str, names: set[str]) -> dict[str, set[str]]:
    """Function name -> the block functions it mentions, and the annotations it
    declares. An AST walk rather than `call_sites`, and the reason is a real
    one: these are handed to `_intake_call` as VALUES, so they are `ast.Name`
    references and not calls at all. A guard written against the wrong node type
    passes on any tree — which is what the first version of this test did, and
    what CORE2's positive control exists to stop happening silently."""

    def own_names(fn: ast.FunctionDef) -> set[str]:
        """Names this function mentions ITSELF, not through a nested one.

        Every route in app.py is defined inside `create_app`, so a plain
        `ast.walk` reports the factory as a referencing handler too — and the
        factory takes no `AdminUser`, so the guard would fail on the enclosing
        scope rather than on anything real.
        """
        seen: set[str] = set()
        stack: list[ast.AST] = list(ast.iter_child_nodes(fn))
        while stack:
            node = stack.pop()
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue  # its own scope; it is visited on its own
            if isinstance(node, ast.Name) and node.id in names:
                seen.add(node.id)
            stack.extend(ast.iter_child_nodes(node))
        return seen

    found: dict[str, set[str]] = {}
    declared: dict[str, set[str]] = {}
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.FunctionDef):
            continue
        referenced = own_names(node)
        if referenced:
            found[node.name] = referenced
            declared[node.name] = {
                ast.unparse(arg.annotation) for arg in node.args.args if arg.annotation
            }
    return {name: declared[name] for name in found}


def test_the_block_is_reached_from_exactly_two_handlers_and_both_are_admin_only() -> None:
    """Clause: "the ADMIN — never the machine".

    The dependency IS the check: a handler that declares `AdminUser` cannot be
    reached by a non-admin session, and one that does not could be. Read off the
    AST, so it cannot pass on the comment above the route.
    """
    app = source_text(REPO / "drydocs_api" / "app.py")
    handlers = _handlers_referencing(app, {"block_persona", "unblock_persona"})
    assert set(handlers) == {
        "post_review_quality_block",
        "post_review_quality_unblock",
    }, sorted(handlers)
    for handler, declared in handlers.items():
        assert "AdminUser" in declared, f"{handler} does not require an admin session"


def test_the_handler_scan_finds_a_handler_that_is_not_admin_only() -> None:
    """The positive control for the test above (CORE2). Both halves have to be
    demonstrated: that the scan sees a reference at all, and that it can tell an
    admin handler from an open one — otherwise a scan matching nothing would
    report every handler compliant."""
    open_route = (
        "def post_anything(body: BlockBody, user: CurrentUser):\n    return block_persona\n"
    )
    found = _handlers_referencing(open_route, {"block_persona"})
    assert set(found) == {"post_anything"}
    assert "AdminUser" not in found["post_anything"]


def test_no_module_blocks_anyone_from_a_threshold() -> None:
    """The whole-tree version of the two tests above: outside the intake module
    that defines them and the app module that routes them, nothing calls the
    block functions at all."""
    offenders = []
    for path in sorted((REPO / "drydocs_api").glob("*.py")):
        if path.name in ("intake.py", "app.py"):
            continue
        called = called_names(source_text(path))
        if {"block_persona", "unblock_persona"} & called:
            offenders.append(path.name)
    assert not offenders, f"these modules call the block directly: {offenders}"
