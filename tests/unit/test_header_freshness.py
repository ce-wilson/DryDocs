"""J59 — the freshness check that cannot live in CI.

J58 made `updated:` required and validated its shape; this checks whether it is
TRUE. The tests below are about the three ways the check could be wrong in a way
nobody would notice:

* it could compare the staged file against git, which reads a correctly-refreshed
  date as a lie about the future (the staged file's git date is the PREVIOUS
  commit — this change has not landed);
* it could pass a file it could not actually look at;
* it could drift from J58's class map and quietly check a different set of files
  than the one the schema governs.

The last is pinned by IDENTITY rather than equality, the same shape the
fix-tracking enum uses: two equal copies is the state that goes stale silently.
"""

from __future__ import annotations

import datetime as dt
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts import check_header_freshness as hook

REPO = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# It checks the set J58 governs — not a set of its own
# ---------------------------------------------------------------------------


def test_the_class_map_is_j58s_object_not_a_copy() -> None:
    """If someone moves CLASSES, THIS breaks — not the hook, silently, at commit
    time on somebody else's machine.

    The import points at the test module on purpose: PORT-MANIFEST.yaml carries a
    per-entry row on that exact path recording that CLASSES is PER-SIDE data the
    company extends, and the row exists so the tests/** default cannot revert
    those entries at a port. Promoting the map to shared test infrastructure
    would strand them, so the hook imports where the manifest says the data is.
    """
    from tests.unit import test_config_identity_header as j58

    assert hook.CLASSES is j58.CLASSES
    assert hook.classify is j58.classify
    assert hook.normalize_dates is j58.normalize_dates


def test_only_the_dated_classes_are_checked() -> None:
    """TEMPLATE forbids `updated:` outright (a hand-maintained date in a file
    whose updates arrive as a three-way merge is a guaranteed conflict), and the
    exempt classes have no identity of their own. Checking them would turn J58's
    reasoned exemptions into failures."""
    from tests.unit import test_config_identity_header as j58

    assert hook.DATED_CLASSES == frozenset({j58.REQUIRED, j58.SOURCE_DESCRIBING, j58.GATE_PROMPT})
    for excluded in (j58.TEMPLATE, j58.FRAGMENT, j58.TOOLING, j58.GENERATED, j58.FIXTURE):
        assert excluded not in hook.DATED_CLASSES


def test_the_governed_filter_drops_an_exempt_file() -> None:
    """A real path from each side, so the filter is exercised rather than asserted."""
    governed = hook._governed(
        [
            "config/classification.yaml",  # REQUIRED
            ".pre-commit-config.yaml",  # TOOLING — somebody else's schema
        ]
    )
    assert "config/classification.yaml" in governed
    assert ".pre-commit-config.yaml" not in governed


# ---------------------------------------------------------------------------
# The two modes ask different questions
# ---------------------------------------------------------------------------


def _write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, updated: str) -> str:
    """A governed file at a real governed path, in a throwaway repo root."""
    relpath = "config/classification.yaml"
    target = tmp_path / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        yaml.safe_dump({"schema": "drydocs.classification.v1", "updated": updated}),
        encoding="utf-8",
    )
    monkeypatch.setattr(hook, "REPO", tmp_path)
    return relpath


def test_staged_mode_compares_against_today_not_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The bug this prevents: at commit time the staged file's git date is the
    PREVIOUS commit, so comparing against git would fail a file whose `updated:`
    was correctly refreshed to today — punishing exactly the right behaviour."""
    today = dt.date.today().isoformat()
    relpath = _write(tmp_path, monkeypatch, today)

    def _never(_relpath: str) -> str:
        raise AssertionError("staged mode must not consult git for the file's date")

    monkeypatch.setattr(hook, "_git_date", _never)
    results = hook.check([relpath], against_git=False, today=today)
    assert [r[0] for r in results[hook.OK]] == [relpath]
    assert not results[hook.STALE]


def test_a_stale_date_fails_and_names_both_dates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    relpath = _write(tmp_path, monkeypatch, "2026-08-20")
    monkeypatch.setattr(hook, "_git_date", lambda _p: "2026-09-08")
    results = hook.check([relpath], against_git=True, today="2026-09-08")
    assert results[hook.STALE] == [(relpath, "2026-08-20", "2026-09-08", "git")]


def test_the_tolerance_absorbs_a_timezone_straddle_and_nothing_more(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One day, because git's %as is the author's LOCAL date and this laptop runs
    America/Chicago while CI runs UTC — a commit after 18:00 local is already
    tomorrow in UTC. Two days would start absorbing real staleness, so the
    boundary is pinned from both sides."""
    assert hook.TOLERANCE_DAYS == 1
    relpath = _write(tmp_path, monkeypatch, "2026-09-07")

    monkeypatch.setattr(hook, "_git_date", lambda _p: "2026-09-08")  # 1 day
    assert not hook.check([relpath], against_git=True, today="2026-09-08")[hook.STALE]

    monkeypatch.setattr(hook, "_git_date", lambda _p: "2026-09-09")  # 2 days
    assert hook.check([relpath], against_git=True, today="2026-09-09")[hook.STALE]


# ---------------------------------------------------------------------------
# It never passes because it could not look
# ---------------------------------------------------------------------------


def test_an_unparseable_date_is_reported_never_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    relpath = _write(tmp_path, monkeypatch, "last week")
    results = hook.check([relpath], against_git=False, today="2026-09-08")
    assert not results[hook.OK]
    assert results[hook.REPORTED][0][0] == relpath
    assert "unparseable" in results[hook.REPORTED][0][1]


def test_a_file_git_cannot_date_is_reported_never_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An absent git date means the check could not look, which is not a pass."""
    relpath = _write(tmp_path, monkeypatch, "2026-09-08")
    monkeypatch.setattr(hook, "_git_date", lambda _p: None)
    results = hook.check([relpath], against_git=True, today="2026-09-08")
    assert not results[hook.OK]
    assert "no git history" in results[hook.REPORTED][0][1]


def test_a_missing_updated_key_is_j58s_and_does_not_fail_here(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Presence is J58's rule and this item's declared out-of-scope (clause (e)).
    Reported under its own heading so the two guards cannot blame each other."""
    relpath = "config/classification.yaml"
    target = tmp_path / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump({"schema": "drydocs.classification.v1"}), encoding="utf-8")
    monkeypatch.setattr(hook, "REPO", tmp_path)

    results = hook.check([relpath], against_git=False, today="2026-09-08")
    assert results[hook.J58] == [(relpath,)]
    assert not results[hook.STALE] and not results[hook.REPORTED]


def test_a_stale_file_makes_the_hook_exit_nonzero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    relpath = _write(tmp_path, monkeypatch, "2026-01-01")
    monkeypatch.delenv(hook.SKIP_ENV, raising=False)
    assert hook.main([relpath]) == 1
    assert "STALE" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# The bypass is deliberate and loud (clause (d))
# ---------------------------------------------------------------------------


def test_the_bypass_prints_what_it_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """--no-verify skips every hook and says nothing, which is the habit J62's
    config warns about. This one leaves a line on the record."""
    relpath = _write(tmp_path, monkeypatch, "2026-01-01")
    monkeypatch.setenv(hook.SKIP_ENV, "1")
    assert hook.main([relpath]) == 0
    out = capsys.readouterr().out
    assert "SKIPPED" in out and hook.SKIP_ENV in out
    assert "NOT compared" in out


def test_it_can_find_the_project_interpreter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The bug this prevents actually happened, on this hook's first commit.

    pre-commit's `language: system` runs whatever `python` PATH resolves to, which
    was NOT the project virtualenv: the hook died with `No module named 'pytest'`
    and aborted a commit for a reason that had nothing to do with freshness. It
    now re-execs under the in-project interpreter. The two alternatives were both
    worse — pinning the venv path in the config is not portable across the two
    machines, and catching the ImportError to pass is the very defect this item
    exists to end.
    """
    assert hook._project_python() is not None, (
        "no in-project .venv found — the hook falls back to failing loudly, which "
        "is correct, but this checkout cannot exercise the re-exec path"
    )

    for layout in ("Scripts/python.exe", "bin/python"):
        probe = tmp_path / ".venv" / layout
        probe.parent.mkdir(parents=True, exist_ok=True)
        probe.write_text("", encoding="utf-8")
        monkeypatch.setattr(hook, "REPO", tmp_path)
        assert hook._project_python() == probe
        probe.unlink()


def test_git_being_unavailable_fails_rather_than_passing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """The whole item exists because a check that cannot look reported green."""

    def _boom(*_a: str) -> str:
        raise subprocess.CalledProcessError(128, "git")

    monkeypatch.delenv(hook.SKIP_ENV, raising=False)
    monkeypatch.setattr(hook, "_staged_yaml", lambda: (_ for _ in ()).throw(_boom()))
    assert hook.main([]) == 1
    assert "git is unavailable" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# The reason it is a hook, verified against the workflow rather than recalled
# ---------------------------------------------------------------------------


def _checkout_depths() -> dict[str, object]:
    """``{job: fetch-depth}`` for every checkout step, read as PARSED YAML.

    Not a grep. The first version of this guard searched the raw file for
    "fetch-depth" and matched the COMMENT explaining the setting — J66's exact
    disease, and it reported the opposite of the truth. ci.yml is a structured
    document; the answer is a key in it, so read the key.
    """
    ci = yaml.safe_load((REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    depths: dict[str, object] = {}
    for job_name, job in ci["jobs"].items():
        for step in job.get("steps", []):
            if str(step.get("uses", "")).startswith("actions/checkout"):
                depths[job_name] = (step.get("with") or {}).get("fetch-depth", "shallow")
    return depths


def test_the_premise_that_made_this_a_hook_is_recorded_as_it_actually_is() -> None:
    """J59's acceptance says CI has "no `fetch-depth` override". That was true when
    the item was groomed (2026-08-28) and is NOT true now: the `gates` job checks
    out with `fetch-depth: 0` for the commit-message ceiling guard.

    So the honest statement of why this is a hook is no longer "CI cannot do it"
    — it is that a hook fails the COMMIT, before the push, which is the only
    intervention that does not depend on somebody reading a CI result afterwards
    (the J62 argument, and the reason a hundred red runs went unnoticed). Whether
    to ALSO add a sweep step to the `gates` job is a real open decision, and this
    test exists so it is taken deliberately rather than inherited from a sentence
    that has quietly stopped being true (J76: check which version of the
    instrument you hold).
    """
    depths = _checkout_depths()
    assert depths["gates"] == 0, (
        "the `gates` job no longer checks out full history — if that was "
        "deliberate, J59's original premise is restored and this note should say so"
    )
    assert {job for job, depth in depths.items() if depth == "shallow"}, (
        "every job now has full history; the cost argument in ci.yml's comment "
        "has changed and the scoping decision deserves re-reading"
    )
