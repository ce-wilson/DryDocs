"""J62 guards: the pre-commit hooks run the two commands CI blocks on, at the ruff
version the project pins — so local and CI cannot disagree about what a violation is.

A hook that lints to a different standard than CI is worse than no hook (the item's own
words), and the only way the two can drift is the hook's ``rev`` moving apart from
pyproject's exact pin. That is what these tests hold together. The pin is read from
``pyproject.toml`` and ``poetry.lock`` as parsed TOML (the objects, not the prose), the
hook config as parsed YAML, and the CI workflow as parsed YAML — all artifacts under
test, none of them renders (J37).
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
PRECOMMIT = REPO / ".pre-commit-config.yaml"
PYPROJECT = REPO / "pyproject.toml"
LOCK = REPO / "poetry.lock"
CI = REPO / ".github" / "workflows" / "ci.yml"
CLAUDE_MD = REPO / "CLAUDE.md"

RUFF_REPO = "https://github.com/astral-sh/ruff-pre-commit"


def _config() -> dict:
    return yaml.safe_load(PRECOMMIT.read_text(encoding="utf-8"))


def _pinned_ruff() -> str:
    """The exact ruff version pyproject pins (J10: no caret, byte-identical formatting
    across the two repos)."""
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    groups = project["tool"]["poetry"].get("group", {})
    for group in groups.values():
        spec = group.get("dependencies", {}).get("ruff")
        if spec:
            break
    else:
        spec = project["tool"]["poetry"]["dependencies"].get("ruff")
    assert isinstance(spec, str), f"ruff pin not found in pyproject: {spec!r}"
    assert re.fullmatch(
        r"\d+\.\d+\.\d+", spec
    ), f"ruff must stay pinned EXACTLY (J10 stage 0), got {spec!r}"
    return spec


def _locked_ruff() -> str:
    lock = tomllib.loads(LOCK.read_text(encoding="utf-8"))
    versions = [p["version"] for p in lock["package"] if p["name"] == "ruff"]
    assert len(versions) == 1, versions
    return versions[0]


def test_the_ruff_hooks_are_the_only_hooks_and_carry_no_extra_arguments() -> None:
    """Exactly the two commands CI blocks on, run as CI runs them: no --fix on `ruff`
    (the hook reports the finding CI would report rather than editing under you),
    nothing else bolted on that CI does not enforce."""
    repos = _config()["repos"]
    assert [r["repo"] for r in repos] == [RUFF_REPO]
    hooks = repos[0]["hooks"]
    assert [h["id"] for h in hooks] == ["ruff", "ruff-format"]
    for hook in hooks:
        assert set(hook) == {"id"}, f"hook {hook['id']} carries extra keys: {sorted(hook)}"


def test_the_hook_rev_equals_the_exact_ruff_pin_and_the_lock() -> None:
    rev = _config()["repos"][0]["rev"]
    pinned = _pinned_ruff()
    assert rev == f"v{pinned}", (
        f".pre-commit-config.yaml rev {rev} != pyproject ruff pin {pinned} — the hook would "
        "lint to a different standard than CI; move the two together (J62)"
    )
    assert _locked_ruff() == pinned, "poetry.lock and pyproject disagree on ruff"


def test_ci_keeps_both_ruff_steps_unchanged() -> None:
    """The hook is a faster first line, never a replacement for the gate."""
    workflow = yaml.safe_load(CI.read_text(encoding="utf-8"))
    runs = [
        step.get("run", "")
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
        if isinstance(step, dict)
    ]
    assert "poetry run ruff check ." in runs, runs
    assert "poetry run ruff format --check ." in runs, runs


def test_the_session_ritual_says_where_the_install_goes() -> None:
    """Reads CLAUDE.md prose on purpose: the item says installation is one documented
    command AND the session ritual says where it goes, so the prose is the artifact
    under test (J66's stated exception). The hook is not silently mandatory: the
    config's own header explains itself, and this line is where a session learns
    the command."""
    ritual = CLAUDE_MD.read_text(encoding="utf-8")
    assert (
        "pre-commit install" in ritual
    ), "CLAUDE.md §0 session ritual must name `pre-commit install`"


def test_the_config_explains_itself_to_a_fresh_clone() -> None:
    """A repo that fails an unexplained hook on a fresh clone teaches people to pass
    --no-verify. The file's header names the install command and the reason the rev
    is pinned, so the first person the hook stops can read why."""
    text = PRECOMMIT.read_text(encoding="utf-8")
    assert "pre-commit install" in text
    assert "no --fix" in text
    assert "pyproject.toml" in text and "ruff-format-convergence" in text
