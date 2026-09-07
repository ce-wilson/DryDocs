"""Reviewer-quality signals (O51, intake plan §8) — derived, never entered.

THE THING BEING MEASURED. An SME who confirms every agent candidate without
reading is indistinguishable from a careful one unless something measures the
difference. The intake flow is where that would do damage, so this module
derives four per-persona signals over a rolling window and compares them against
`config/review-quality.yaml`.

NOTHING HERE ACTS. Crossing a limit produces a FLAG carrying the metric that
tripped. The block is an admin action in `intake.py`, taken by a person, and no
code path calls it from a threshold. That separation is the whole design, so it
is a separation in the code and not only in the prose: this module cannot block
anyone because it imports nothing that can.

NO NEW DATA ENTRY, and this turned out to be literally true rather than
aspirational. Every transition already writes an `event` row (intake_id, at,
actor, action, detail) and every upload writes an `evidence` row with its byte
size, so three of the four signals need no schema change at all -- they are a
different question asked of rows the store has kept since O46. The fourth needs
something that does not exist yet; see below.

AUTO-ACCEPT IS UNAVAILABLE, NOT ZERO. The metric is "agent candidates confirmed
with zero modification", and the candidate-binding set is the intake plan's
section 4, which O48 builds. There is nothing today for a confirmation to be
compared against. So it is reported as `None` with the reason beside it, at every
layer, and it CANNOT trip a flag. A zero here would be the worst possible
default: it reads as a reviewer who modifies everything, which is the best
possible score. (O56's rule -- never invent a green or a zero -- and the same
seam O50 used for a proposal set that has no producer yet.)

WHAT "REVIEW TIME" MEANS, because the obvious reading is wrong. The floor is
compared against the time the SME had the record IN FRONT OF THEM, which starts
at the most recent moment the record was handed to them: the last evidence
upload, or the last admin return, whichever is later. Taking the previous event
blindly would measure from another persona's action -- an admin's return three
days ago makes every re-confirm look slow, and a re-upload makes a careful
review look instant. This is a ruling and it is stated here so it can be
overturned somewhere visible.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Final

import yaml

from drydocs_core.repo_paths import repo_root

_REPO = repo_root(Path(__file__).resolve().parent.parent)
LIMITS_FILE: Final[Path] = _REPO / "config" / "review-quality.yaml"

#: The status a submit lands on. Both paths into it (`correlated ->` and
#: `admin-returned ->`) are submits and both count.
SUBMIT_STATUS: Final = "sme-confirmed"
RETURN_STATUS: Final = "admin-returned"

#: Why the auto-accept rate is None. Carried in the payload beside the null so a
#: reader never has to guess whether the metric is zero, missing or broken.
AUTO_ACCEPT_UNAVAILABLE: Final = (
    "Not computable yet: 'accepted with zero modification' needs the agent's "
    "candidate-binding set to compare against, which is the intake plan's "
    "section 4 and lands with O48. Reported as no-data rather than 0%, because "
    "0% reads as the best possible score."
)


class ReviewQualityConfigError(ValueError):
    """The limits file is unreadable or does not declare what it must."""


@dataclass(frozen=True)
class ReviewFloor:
    min_review_seconds: float
    seconds_per_kb: float
    max_review_seconds: float

    def seconds_for(self, evidence_bytes: int) -> float:
        """The floor for one decision, scaled by the evidence it had to read."""
        scaled = self.min_review_seconds + self.seconds_per_kb * (evidence_bytes / 1024)
        return min(scaled, self.max_review_seconds)


@dataclass(frozen=True)
class Limits:
    window_days: int
    min_decisions_for_flag: int
    auto_accept_rate_max: float
    admin_return_rate_max: float
    too_fast_rate_max: float
    review_floor: ReviewFloor


def load_limits(path: Path = LIMITS_FILE) -> Limits:
    """Read the limits file. Raises rather than defaulting.

    A silent default would mean two machines flagging different people from the
    same data, which is exactly the failure the file exists to prevent.
    """
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ReviewQualityConfigError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, Mapping):
        raise ReviewQualityConfigError(f"{path} does not parse to a mapping")
    if data.get("schema") != "drydocs.review-quality.v1":
        raise ReviewQualityConfigError(f"{path}: unexpected schema {data.get('schema')!r}")
    try:
        limits = data["limits"]
        floor = data["review_floor"]
        return Limits(
            window_days=int(data["window_days"]),
            min_decisions_for_flag=int(data["min_decisions_for_flag"]),
            auto_accept_rate_max=float(limits["auto_accept_rate_max"]),
            admin_return_rate_max=float(limits["admin_return_rate_max"]),
            too_fast_rate_max=float(limits["too_fast_rate_max"]),
            review_floor=ReviewFloor(
                min_review_seconds=float(floor["min_review_seconds"]),
                seconds_per_kb=float(floor["seconds_per_kb"]),
                max_review_seconds=float(floor["max_review_seconds"]),
            ),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ReviewQualityConfigError(f"{path}: {exc}") from exc


@dataclass(frozen=True)
class Decision:
    """ONE submit, with what it can be judged on.

    Per-decision and not a rollup, because the future confirmation-weight trust
    model needs the individual acts and a rate cannot be un-averaged.
    ``modified_fields`` is the O48-shaped hole: the list exists so a decision
    already has a place to record what the reviewer changed, and it is empty
    everywhere today because nothing proposes anything yet.
    """

    intake_id: str
    persona_id: str
    at: str
    from_status: str
    handed_over_at: str | None
    review_seconds: float | None
    evidence_bytes: int
    floor_seconds: float
    returned_by_admin: bool
    modified_fields: list[str] = field(default_factory=list)

    @property
    def too_fast(self) -> bool:
        """Unknown review time is NOT too fast. A record whose hand-over moment
        predates the event log (an intake created before O51) has no measurable
        review time, and counting that as a violation would flag people for the
        deployment date."""
        return self.review_seconds is not None and self.review_seconds < self.floor_seconds


def _parse(ts: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _is_submit(action: str) -> bool:
    return action.startswith("transition:") and action.endswith(f"->{SUBMIT_STATUS}")


def _is_return(action: str) -> bool:
    return action.startswith("transition:") and action.endswith(f"->{RETURN_STATUS}")


def _from_status(action: str) -> str:
    return action.removeprefix("transition:").split("->")[0]


def decisions(
    events: Iterable[Mapping[str, Any]],
    evidence: Iterable[Mapping[str, Any]],
    limits: Limits,
    *,
    now: datetime | None = None,
) -> list[Decision]:
    """Every submit in the window, as a judgeable decision.

    ``events`` and ``evidence`` are the store's own rows. Taking them as
    arguments rather than reading the database is what makes every rule below
    unit-testable without a store -- the same shape `undeclared_constraints`
    uses for the live constraint rows.
    """
    now = now or datetime.now(UTC)
    cutoff = now - timedelta(days=limits.window_days)

    rows = [dict(e) for e in events]
    rows.sort(key=lambda e: str(e.get("at", "")))

    uploads: dict[str, list[tuple[datetime, int]]] = {}
    for row in evidence:
        when = _parse(str(row.get("uploaded_at", "")))
        if when is not None:
            uploads.setdefault(str(row["intake_id"]), []).append((when, int(row.get("size", 0))))

    returns: dict[str, list[datetime]] = {}
    for row in rows:
        if _is_return(str(row.get("action", ""))):
            when = _parse(str(row.get("at", "")))
            if when is not None:
                returns.setdefault(str(row["intake_id"]), []).append(when)

    out: list[Decision] = []
    for row in rows:
        action = str(row.get("action", ""))
        if not _is_submit(action):
            continue
        at = _parse(str(row.get("at", "")))
        if at is None or at < cutoff:
            continue
        intake_id = str(row["intake_id"])

        # The hand-over: the last moment the record was put in front of this
        # reviewer, which is an upload or a return -- whichever came last, and
        # only if it came BEFORE the submit.
        candidates = [w for w, _ in uploads.get(intake_id, []) if w <= at]
        candidates += [w for w in returns.get(intake_id, []) if w <= at]
        handed_over = max(candidates) if candidates else None

        evidence_bytes = sum(size for w, size in uploads.get(intake_id, []) if w <= at)
        out.append(
            Decision(
                intake_id=intake_id,
                persona_id=str(row.get("actor", "")),
                at=str(row.get("at", "")),
                from_status=_from_status(action),
                handed_over_at=handed_over.isoformat() if handed_over else None,
                review_seconds=(at - handed_over).total_seconds() if handed_over else None,
                evidence_bytes=evidence_bytes,
                floor_seconds=limits.review_floor.seconds_for(evidence_bytes),
                returned_by_admin=any(w > at for w in returns.get(intake_id, [])),
            )
        )
    return out


@dataclass(frozen=True)
class Flag:
    metric: str
    value: float
    limit: float
    detail: str


@dataclass(frozen=True)
class PersonaQuality:
    persona_id: str
    submissions: int
    auto_accept_rate: float | None
    auto_accept_unavailable_because: str
    too_fast_rate: float
    admin_return_rate: float
    median_review_seconds: float | None
    flags: list[Flag]
    blocked: bool = False

    def as_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["flags"] = [asdict(f) for f in self.flags]
        return out


def _median(values: Sequence[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def summarize(
    made: Sequence[Decision], limits: Limits, *, blocked: Iterable[str] = ()
) -> list[PersonaQuality]:
    """Per-persona rollups and the flags they trip, ordered by persona id.

    ORDERED BY ID, not by worst-first. The plan's own words are "coaching and
    triage, not a leaderboard", and a list sorted by the worst number is a
    leaderboard whatever the heading says.
    """
    blocked_set = set(blocked)
    by_persona: dict[str, list[Decision]] = {}
    for decision in made:
        by_persona.setdefault(decision.persona_id, []).append(decision)

    out: list[PersonaQuality] = []
    for persona_id in sorted(by_persona):
        theirs = by_persona[persona_id]
        total = len(theirs)
        too_fast = sum(1 for d in theirs if d.too_fast) / total
        returned = sum(1 for d in theirs if d.returned_by_admin) / total
        measured = [d.review_seconds for d in theirs if d.review_seconds is not None]

        flags: list[Flag] = []
        # BELOW THE FLOOR, NOTHING IS FLAGGED. One return out of two submissions
        # is a 50% rate and is not evidence of anything. The numbers are still
        # reported -- suppressing the flag is not the same as hiding the data.
        if total >= limits.min_decisions_for_flag:
            if too_fast > limits.too_fast_rate_max:
                flags.append(
                    Flag(
                        metric="too_fast_rate",
                        value=too_fast,
                        limit=limits.too_fast_rate_max,
                        detail=(
                            f"{sum(1 for d in theirs if d.too_fast)} of {total} confirms came "
                            "in under their own review floor (which scales with evidence size)"
                        ),
                    )
                )
            if returned > limits.admin_return_rate_max:
                flags.append(
                    Flag(
                        metric="admin_return_rate",
                        value=returned,
                        limit=limits.admin_return_rate_max,
                        detail=(
                            f"{sum(1 for d in theirs if d.returned_by_admin)} of {total} "
                            "submissions were sent back by an admin"
                        ),
                    )
                )
        # auto_accept_rate is deliberately absent from this block: a None cannot
        # be compared to a limit, and a metric with no source must not flag a
        # person. Guarded by tests/unit/test_review_quality.py.
        out.append(
            PersonaQuality(
                persona_id=persona_id,
                submissions=total,
                auto_accept_rate=None,
                auto_accept_unavailable_because=AUTO_ACCEPT_UNAVAILABLE,
                too_fast_rate=too_fast,
                admin_return_rate=returned,
                median_review_seconds=_median(measured),
                flags=flags,
                blocked=persona_id in blocked_set,
            )
        )
    return out


def limits_as_dict(limits: Limits) -> dict[str, Any]:
    """The limits as the console reads them, so a rail can render the number a
    metric was compared against instead of restating it in TypeScript."""
    return json.loads(json.dumps(asdict(limits)))
