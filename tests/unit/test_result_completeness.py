"""API1 — result completeness is part of the read contract.

The defect this closes (web review 2026-09-05, finding S1): every QuerySpec
shares one ``limit`` parameter defaulting to 500, no console surface ever passes
it, and nothing in the response said whether it bit. A spec whose true answer
was 900 rows returned 500 and rendered ``500/500 · drydocs · LIVE``. Worse, the
export button labelled "full" fed ``result.params`` — which already carried
``limit: 500`` — back to the server, which streamed exactly 500 rows and filed a
provenance manifest recording ``row_count: 500`` with no field saying the extract
was capped. A governance artifact that faithfully describes a truncated answer
and cannot say so is the failure the canvas's own NODE_CEILING comment names.

So the two facts are DECLARED now, at the one place both the API and the agent
CLI build their envelope:

* ``truncated`` — did the ceiling cut the answer
* ``limit`` — which ceiling applied (``None`` for a spec that has none)

and the export manifest carries the same pair beside ``row_count``.

The mechanism is ``limit + 1``: ask the driver for one row past the ceiling and
report whether it came back. The probe row is evidence and is dropped before
anything is emitted — the tests below pin that, because a 501st row reaching a
caller would break the very contract the field states.

The boundary case is the reason this is a typed field and not a console
heuristic: at EXACTLY ``limit`` rows, ``rows.length === limit`` says "truncated"
and the truth is "complete". That case has its own test.
"""

from __future__ import annotations

import json

import pytest

from drydocs_api.exports import (
    EXPORT_LIMIT_CEILING,
    ExportLedger,
    execute_spec,
    export_spec,
    run_spec,
)
from drydocs_api.queries import validate_params
from drydocs_api.query_specs import (
    DEFAULT_DISPLAY_LIMIT,
    DISPLAY_LIMIT_PARAM,
    QUERY_SPECS,
    display_limit_param,
    query_spec,
)
from drydocs_api.sessions import InMemorySessionStore

CAPPED_SPEC = "explorer.jobs.v2"


class LimitHonoringRunner:
    """A fake that behaves like Cypher's ``LIMIT $limit`` actually does.

    The other fakes in this suite return their rows verbatim, which is fine for
    routing and auth assertions and useless here: the whole mechanism under test
    is what happens when the driver returns exactly as many rows as it was asked
    for. This one slices, so "the extra row came back" is a real outcome and not
    a fixture's decision.
    """

    def __init__(self, total: int, keys: list[str] | None = None) -> None:
        self.total = total
        self.keys = keys or ["job_id"]
        self.calls: list[tuple[str, dict, str]] = []

    def _rows(self, params) -> list[dict[str, object]]:
        rows = [{self.keys[0]: f"row-{i}"} for i in range(self.total)]
        limit = params.get(DISPLAY_LIMIT_PARAM)
        return rows[:limit] if isinstance(limit, int) else rows

    def run(self, cypher, params, database):
        self.calls.append((cypher, dict(params), database))
        return self.keys, self._rows(params)

    def stream(self, cypher, params, database):
        self.calls.append((cypher, dict(params), database))
        return self.keys, iter(self._rows(params))


def _token(store: InMemorySessionStore) -> str:
    return store.issue("mouse").token


def _bound(spec_id: str, **params) -> dict:
    return validate_params(query_spec(spec_id), params)


def _uncapped_spec_id() -> str:
    for spec in QUERY_SPECS.values():
        if not display_limit_param(spec):
            return spec.id
    pytest.skip("every registered spec declares a display limit")


# ── the registry invariant the mechanism rests on ────────────────────────────


def test_a_declared_limit_and_a_bound_limit_go_together() -> None:
    """``display_limit_param`` requires BOTH the parameter and a ``$limit`` the
    Cypher binds, and the registry keeps them in lockstep.

    A spec that declared the parameter without using it would have every result
    over 500 rows reported as truncated AND SLICED — the API inventing a cap no
    query applied. A spec that used ``$limit`` without declaring it would fail
    param validation instead. Neither exists; this holds the registry there.
    """
    needle = "$" + DISPLAY_LIMIT_PARAM
    mismatched = [
        s.id
        for s in QUERY_SPECS.values()
        if any(p.name == DISPLAY_LIMIT_PARAM for p in s.params) != (needle in s.cypher)
    ]
    assert not mismatched, f"specs declaring a limit they do not bind (or vice versa): {mismatched}"


def test_the_shared_default_is_still_the_documented_five_hundred() -> None:
    spec = query_spec(CAPPED_SPEC)
    declared = next(p for p in spec.params if p.name == DISPLAY_LIMIT_PARAM)
    assert declared.default == DEFAULT_DISPLAY_LIMIT == 500


# ── clause (a): the run envelope carries completeness ────────────────────────


def test_more_rows_than_the_limit_reports_truncated_and_drops_the_probe_row() -> None:
    runner = LimitHonoringRunner(total=900)
    out = execute_spec(query_spec(CAPPED_SPEC), _bound(CAPPED_SPEC, limit=500), runner)
    assert out["truncated"] is True
    assert out["limit"] == 500
    assert len(out["rows"]) == 500, "the 501st row is evidence, and must not be payload"
    assert runner.calls[0][1][DISPLAY_LIMIT_PARAM] == 501, "the driver is asked one row past"
    assert (
        out["params"][DISPLAY_LIMIT_PARAM] == 500
    ), "the caller is told the ceiling, not the probe"


def test_fewer_rows_than_the_limit_reports_complete() -> None:
    out = execute_spec(
        query_spec(CAPPED_SPEC), _bound(CAPPED_SPEC, limit=500), LimitHonoringRunner(total=12)
    )
    assert out["truncated"] is False
    assert out["limit"] == 500
    assert len(out["rows"]) == 12


def test_exactly_the_limit_is_complete_which_is_what_a_row_count_heuristic_gets_wrong() -> None:
    """The case that makes this a declared field instead of a console check.

    At exactly 500 rows, ``rows.length === limit`` renders TRUNCATED over a
    complete answer. The server knows the difference because it asked for 501
    and got 500.
    """
    out = execute_spec(
        query_spec(CAPPED_SPEC), _bound(CAPPED_SPEC, limit=500), LimitHonoringRunner(total=500)
    )
    assert out["truncated"] is False
    assert len(out["rows"]) == 500


def test_a_spec_with_no_ceiling_reports_a_null_limit_and_never_truncates() -> None:
    spec_id = _uncapped_spec_id()
    out = execute_spec(query_spec(spec_id), {}, LimitHonoringRunner(total=5000))
    assert out["limit"] is None
    assert out["truncated"] is False
    assert len(out["rows"]) == 5000, "a spec with no ceiling is never silently cut"


def test_a_caller_raised_run_limit_is_the_ceiling_that_is_reported() -> None:
    out = execute_spec(
        query_spec(CAPPED_SPEC), _bound(CAPPED_SPEC, limit=10), LimitHonoringRunner(total=900)
    )
    assert (out["truncated"], out["limit"], len(out["rows"])) == (True, 10, 10)


def test_run_spec_carries_completeness_through_the_authenticated_path() -> None:
    store = InMemorySessionStore()
    out = run_spec(CAPPED_SPEC, {}, _token(store), store, LimitHonoringRunner(total=900))
    assert out["truncated"] is True and out["limit"] == 500


# ── clause (b): the manifest records it ──────────────────────────────────────


def _export(spec_id: str, total: int, fmt: str = "csv", **kwargs) -> tuple[list[str], dict]:
    store = InMemorySessionStore()
    ledger = ExportLedger()
    job = export_spec(
        spec_id,
        {},
        fmt,
        _token(store),
        store,
        LimitHonoringRunner(total=total),
        ledger,
        **kwargs,
    )
    body = list(job.chunks)  # exhausting the generator is what registers the manifest
    return body, ledger.manifest(job.export_id)


def _data_rows(body: list[str], fmt: str) -> list[str]:
    """The emitted DATA lines, with the framing removed.

    Both formats prepend a classification banner for an `internal` spec, and csv
    adds a header line on top of that. Counting raw chunks instead of stripping
    the framing is how the first draft of these assertions was off by exactly
    the banner — the count has to mean data rows or it proves nothing about
    where the probe row went.
    """
    if fmt == "csv":
        return [ln for ln in body if not ln.startswith("#")][1:]
    return [ln for ln in body if not ln.startswith('{"_classification_banner"')]


@pytest.mark.parametrize("fmt", ["csv", "jsonl"])
def test_a_capped_export_says_so_in_its_manifest(fmt: str) -> None:
    body, manifest = _export(CAPPED_SPEC, total=900, fmt=fmt)
    assert manifest["truncated"] is True
    assert manifest["limit"] == 500
    assert manifest["row_count"] == 500
    assert len(_data_rows(body, fmt)) == 500, "the probe row must not reach the file either"


@pytest.mark.parametrize("fmt", ["csv", "jsonl"])
def test_an_uncapped_export_says_that_too(fmt: str) -> None:
    _, manifest = _export(CAPPED_SPEC, total=42, fmt=fmt)
    assert manifest["truncated"] is False
    assert manifest["limit"] == 500
    assert manifest["row_count"] == 42


def test_the_manifest_pair_is_what_distinguishes_a_full_five_hundred_from_a_cut_one() -> None:
    """``row_count`` alone cannot tell these apart — which is the whole finding."""
    _, capped = _export(CAPPED_SPEC, total=900)
    _, complete = _export(CAPPED_SPEC, total=500)
    assert capped["row_count"] == complete["row_count"] == 500
    assert capped["truncated"] is True and complete["truncated"] is False


def test_a_jsonl_export_never_emits_the_probe_row_as_data() -> None:
    body, _ = _export(CAPPED_SPEC, total=900, fmt="jsonl")
    rows = [json.loads(ln) for ln in _data_rows(body, "jsonl")]
    assert len(rows) == 500
    assert {r["job_id"] for r in rows} == {f"row-{i}" for i in range(500)}


# ── clause (c): the ceiling is raisable, and refusals are loud ───────────────


def test_the_export_ceiling_can_be_raised_and_the_manifest_records_the_raised_one() -> None:
    body, manifest = _export(CAPPED_SPEC, total=900, limit=900)
    assert manifest["truncated"] is False
    assert manifest["limit"] == 900
    assert manifest["row_count"] == 900
    assert manifest["params"][DISPLAY_LIMIT_PARAM] == 900, "params describe the run that happened"
    assert len(_data_rows(body, "csv")) == 900


def test_a_raised_ceiling_that_still_bites_is_still_reported() -> None:
    _, manifest = _export(CAPPED_SPEC, total=5000, limit=2000)
    assert manifest["truncated"] is True and manifest["limit"] == 2000


def test_an_export_limit_above_the_server_ceiling_is_refused_not_clamped() -> None:
    """Silently clamping would hand back exactly the quietly-capped artifact
    this item exists to abolish."""
    with pytest.raises(ValueError, match="exceeds the server ceiling"):
        _export(CAPPED_SPEC, total=10, limit=EXPORT_LIMIT_CEILING + 1)


@pytest.mark.parametrize("bad", [0, -5, "500"])
def test_a_nonsense_export_limit_is_refused(bad) -> None:
    with pytest.raises(ValueError):
        _export(CAPPED_SPEC, total=10, limit=bad)


def test_raising_a_ceiling_a_spec_does_not_have_is_refused() -> None:
    with pytest.raises(ValueError, match="no export ceiling to raise"):
        _export(_uncapped_spec_id(), total=10, limit=100)


def test_omitting_the_export_limit_keeps_exactly_todays_behaviour() -> None:
    """The compatibility promise: an un-updated caller sees no change."""
    _, manifest = _export(CAPPED_SPEC, total=200)
    assert manifest["params"][DISPLAY_LIMIT_PARAM] == DEFAULT_DISPLAY_LIMIT
    assert manifest["row_count"] == 200
