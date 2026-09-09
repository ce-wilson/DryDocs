"""J59 — the `updated:` key checked against something, in the one place it can be.

J58 made `updated:` REQUIRED and validated its SHAPE. Shape is not truth: on
2026-08-27 sixteen of the twenty-four files carrying the key disagreed with git
about when their content last moved, `PORT-MANIFEST.yaml` itself reading
`updated: 2026-08-20` against a git date of 2026-08-27. A date that is present,
well-formed and wrong is worse than an absent one, because a reader trusts it.

WHY THIS IS A LOCAL HOOK — stated as it actually is, not as the item assumed.

J59's acceptance says the comparison is blind in CI because the workflow checks
out shallow "with no `fetch-depth` override, verified against
.github/workflows/ci.yml". That was true when the item was groomed on
2026-08-28. It is NOT true now: the `gates` job checks out with `fetch-depth: 0`
for the commit-message ceiling guard, so per-file history IS on the runner and a
CI-hosted sweep would work. Writing a check about lying dates on top of a
premise that had quietly stopped being true would have been its own joke
(CLAUDE.md J76 — check which VERSION of the instrument you hold;
`tests/unit/test_header_freshness.py` pins the real state as parsed YAML rather
than as prose, which is how the stale premise was caught).

The reason that survives is the J62 one, and it is a better reason. A hook fails
the COMMIT, before the push. CI reports afterwards, and the repo has already
proved what happens then: `ruff` ran red for more than a hundred consecutive
runs while sessions kept pushing past it, invisible because nothing local ever
looked wrong. A date is fixed most cheaply in the commit that moved the file, by
the person who moved it, which is here.

Whether to ALSO add an `--all-files` sweep step to the `gates` job is a real
open decision and deliberately not taken here — see the item's close notes.

TWO MODES, BECAUSE THE QUESTION IS DIFFERENT IN EACH.

* Default (the hook): the files STAGED for this commit. Their git date is the
  PREVIOUS commit — this change has not landed — so comparing `updated:` to git
  here would read a correctly-refreshed `updated: <today>` as a lie about the
  future. The staged question is therefore "does `updated:` say today?", which
  is exactly what a commit that moves the file should have made true.
* ``--all-files`` (the sweep): every governed file, `updated:` against
  `git log -1 --format=%as`. This is the mode that reproduces the item's
  baseline measurement and the one to re-run when asking how bad the drift is.

TOLERANCE IS ONE DAY, and the reason is timezones rather than slack. Git's `%as`
is the author date in the author's local zone; this laptop runs
America/Chicago while CI runs UTC, so a commit made after 18:00 local is already
"tomorrow" in UTC. One day absorbs exactly that straddle and nothing else — two
days would start absorbing real staleness.

WHICH FILES ARE GOVERNED is not re-derived here. J58 centralised that decision so
that guards validate against one expression of the rule instead of each
inventing its own, so this imports J58's class map. That map deliberately lives
in the test module: `PORT-MANIFEST.yaml` carries a per-entry row on that exact
path recording that the CLASSES dict is PER-SIDE data the company extends with
its own files, and the row exists so the `tests/**` default cannot revert those
entries at a port. Moving the map to shared test infrastructure would strand
them, so the import points where the manifest says the data lives.

NEVER PASSES BECAUSE IT COULD NOT LOOK. A file whose `updated:` cannot be parsed,
or whose git date cannot be resolved, is REPORTED and fails — it is not skipped.
The one thing it does not fail on is a MISSING `updated:` key, which is J58's
presence rule and this item's declared out-of-scope (clause (e)); those are
listed as J58's so the two guards cannot quietly blame each other.

BYPASS IS DELIBERATE AND LOUD. `--no-verify` skips every hook silently, which is
the habit J62's config warns about. `DRYDOCS_FRESHNESS_SKIP=1` skips THIS check
and prints what it skipped and why, so a bypass leaves a line in the terminal.

KNOWN LIMIT, stated rather than discovered later: a hook is machine-local and
nothing installs it for you, so this is enforced only for people who ran
`pre-commit install`. That is a property of where the history lives, not an
oversight — and it is why the session ritual names the install.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

SKIP_ENV = "DRYDOCS_FRESHNESS_SKIP"

#: Set on the re-exec below so a broken project interpreter cannot loop forever.
_REEXEC_ENV = "DRYDOCS_FRESHNESS_REEXEC"

# The bypass is honoured BEFORE anything is imported. Otherwise the one situation
# a person most needs it in — an environment this hook cannot load in — is the one
# where it would not work.
if os.environ.get(SKIP_ENV):
    print(
        f"freshness check SKIPPED — {SKIP_ENV} is set. The `updated:` keys of the "
        "staged governed files were NOT compared to anything. This line exists so "
        "the bypass is on the record; --no-verify would have left none."
    )
    raise SystemExit(0)


def _project_python() -> Path | None:
    """The in-project virtualenv's interpreter, if this checkout has one."""
    for candidate in (
        REPO / ".venv" / "Scripts" / "python.exe",  # Windows
        REPO / ".venv" / "bin" / "python",  # POSIX
    ):
        if candidate.exists():
            return candidate
    return None


def _reexec_under_project_python() -> None:
    """Run again under the project interpreter when this one lacks the repo's deps.

    pre-commit's `language: system` runs whatever `python` PATH resolves to, and
    that is frequently NOT the project virtualenv — it was not on the very first
    commit this hook ran on, which failed with `No module named 'pytest'`. Two
    ways to get that wrong, and both are worse than this: pinning the venv path
    in `.pre-commit-config.yaml` (not portable across the two machines), or
    catching the ImportError and passing (a check that skips because it could not
    load is the exact defect this item exists to end).

    So: re-exec once under the in-project interpreter. If that is missing, or it
    still cannot import, FAIL with a message naming the fix — never pass.
    """
    if os.environ.get(_REEXEC_ENV):
        return  # already the second attempt; let the ImportError surface
    venv = _project_python()
    if venv is None or Path(sys.executable).resolve() == venv.resolve():
        return
    result = subprocess.run(  # — our own interpreter, our own script
        [str(venv), str(Path(__file__).resolve()), *sys.argv[1:]],
        env={**os.environ, _REEXEC_ENV: "1"},
    )
    raise SystemExit(result.returncode)


try:
    import pytest  # — the class map's module imports it at module scope
    import yaml  # — probe only; the real use is inside _updated_of
except ModuleNotFoundError:
    _reexec_under_project_python()
    try:
        import pytest  # noqa: F401
        import yaml  # noqa: F401
    except ModuleNotFoundError as exc:  # pragma: no cover — the fail-loud path
        raise SystemExit(
            f"freshness check FAILED: cannot import {exc.name!r} with {sys.executable}, "
            f"and no usable interpreter was found at {REPO / '.venv'}. The check did "
            "NOT run and nothing was compared. Install the project environment "
            "(`poetry install`) or run the hook from the project virtualenv. To "
            f"commit without this check: {SKIP_ENV}=1 git commit ..."
        ) from exc

# The class map is J58's and is imported, never re-derived. CLASSES itself is not
# called here — `classify` reads it — but it is re-exported deliberately so
# tests/unit/test_header_freshness.py can pin it by IDENTITY: if someone later
# moves the map, that test breaks first, rather than this hook quietly checking a
# different set of files at commit time on somebody else's machine.
from tests.unit.test_config_identity_header import (  # noqa: E402
    CLASSES,  # noqa: F401 — re-exported so the identity guard has something to hold
    GATE_PROMPT,
    REQUIRED,
    SOURCE_DESCRIBING,
    classify,
    normalize_dates,
)

#: The classes that must carry a truthful `updated:`. The other classes either
#: forbid the key (TEMPLATE), have no identity of their own (FRAGMENT), or are
#: somebody else's file (TOOLING/GENERATED/FIXTURE) — see the J58 schema.
DATED_CLASSES = frozenset({REQUIRED, SOURCE_DESCRIBING, GATE_PROMPT})

#: One day. Timezones, not slack — see the module docstring.
TOLERANCE_DAYS = 1

OK = "ok"
STALE = "stale"
REPORTED = "reported"  # could not determine — never a pass
J58 = "j58"  # no `updated:` key at all: presence is J58's, out of scope here


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, encoding="utf-8", check=True
    ).stdout.strip()


def _tracked_yaml() -> list[str]:
    """Every tracked YAML path, repo-relative, forward-slashed.

    Reimplemented rather than imported: J58's helper calls ``pytest.skip`` when
    git is unavailable, and a hook cannot skip — a check that cannot look must
    say so, which is what the caller does with the error below.
    """
    out = _git("ls-files", "*.yaml", "*.yml")
    return [line.replace("\\", "/") for line in out.splitlines() if line]


def _staged_yaml() -> list[str]:
    out = _git("diff", "--cached", "--name-only", "--diff-filter=ACMR")
    return [
        line.replace("\\", "/") for line in out.splitlines() if line.endswith((".yaml", ".yml"))
    ]


def _governed(paths: list[str]) -> list[str]:
    governed = []
    for relpath in paths:
        entry = classify(relpath)
        if entry and entry[0] in DATED_CLASSES:
            governed.append(relpath)
    return governed


def _updated_of(relpath: str) -> tuple[str, str | None]:
    """``(outcome, iso_date)`` for the file's own `updated:` key."""
    import yaml

    path = REPO / relpath
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return REPORTED, f"unreadable: {exc.__class__.__name__}"
    if not isinstance(doc, dict) or "updated" not in doc:
        return J58, None
    value = normalize_dates(doc)["updated"]
    try:
        dt.date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return REPORTED, f"unparseable updated: {value!r}"
    return OK, str(value)


def _git_date(relpath: str) -> str | None:
    """The file's last-touch author date, or None when git cannot answer."""
    try:
        out = _git("log", "-1", "--format=%as", "--", relpath)
    except (OSError, subprocess.CalledProcessError):
        return None
    return out or None


def _within(a: str, b: str) -> bool:
    return abs((dt.date.fromisoformat(a) - dt.date.fromisoformat(b)).days) <= TOLERANCE_DAYS


def check(paths: list[str], *, against_git: bool, today: str) -> dict[str, list[tuple]]:
    """Classify every governed path. Returns ``{outcome: [(path, ...), ...]}``."""
    results: dict[str, list[tuple]] = {OK: [], STALE: [], REPORTED: [], J58: []}
    for relpath in _governed(paths):
        outcome, value = _updated_of(relpath)
        if outcome is J58 or outcome == J58:
            results[J58].append((relpath,))
            continue
        if outcome == REPORTED:
            results[REPORTED].append((relpath, value))
            continue
        assert value is not None
        if against_git:
            reference = _git_date(relpath)
            if reference is None:
                results[REPORTED].append(
                    (relpath, "no git history — untracked, or git could not answer")
                )
                continue
            label = "git"
        else:
            reference, label = today, "today"
        (results[OK] if _within(value, reference) else results[STALE]).append(
            (relpath, value, reference, label)
        )
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--all-files",
        action="store_true",
        help="Sweep every governed file and compare `updated:` against its git "
        "last-touch date (the item's baseline measurement). Default is the "
        "staged files, compared against today.",
    )
    parser.add_argument(
        "paths", nargs="*", help="Paths pre-commit passes; ignored with --all-files."
    )
    args = parser.parse_args(argv)

    if os.environ.get(SKIP_ENV):
        print(
            f"freshness check SKIPPED — {SKIP_ENV} is set. The `updated:` keys of "
            "the staged governed files were NOT compared to anything. This line "
            "exists so the bypass is on the record; --no-verify would have left none."
        )
        return 0

    try:
        if args.all_files:
            paths, against_git = _tracked_yaml(), True
        else:
            paths = [p.replace("\\", "/") for p in args.paths] or _staged_yaml()
            against_git = False
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"freshness check FAILED: git is unavailable, so nothing was compared ({exc}).")
        return 1

    today = dt.date.today().isoformat()
    results = check(paths, against_git=against_git, today=today)

    for relpath, value, reference, label in results[STALE]:
        print(f"STALE  {relpath}: updated: {value}  vs  {label}: {reference}")
    for relpath, why in results[REPORTED]:
        print(f"REPORTED  {relpath}: {why}")
    for (relpath,) in results[J58]:
        print(f"(no `updated:` key — J58's presence rule, not this check) {relpath}")

    if results[STALE] or results[REPORTED]:
        checked = sum(len(v) for v in results.values()) - len(results[J58])
        print(
            f"\n{len(results[STALE])} stale, {len(results[REPORTED])} undeterminable "
            f"of {checked} governed file(s) checked "
            f"({'against git' if against_git else 'against today'}; "
            f"tolerance {TOLERANCE_DAYS} day for the timezone straddle).\n"
            "Set the file's `updated:` to the date its content actually moved. "
            f"To commit anyway: {SKIP_ENV}=1 git commit ... (it prints that it skipped)."
        )
        return 1

    if results[OK]:
        print(
            f"freshness OK — {len(results[OK])} governed file(s) agree with {'git' if against_git else 'today'}."
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
