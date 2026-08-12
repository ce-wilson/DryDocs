"""A render run must write into the checkout the CALLER is in (Idea-109).

WHY THIS EXISTS. On 2026-08-11 two agents working in separate
``.claude/worktrees/`` trees each ran the CLAUDE.md §0 session-end render ritual and
each silently wrote part of its output into the MAIN repo. Both recovered; neither
tree showed anything wrong, which is the point — the worktree stayed clean and main
picked up an uncommitted render nobody in that session had authored.

The mechanism, in one line: ``drydocs`` is installed **editable** (a ``drydocs.pth``
pinned at the main tree), so a module that anchors its default paths on
``Path(__file__)`` names the main tree from anywhere. ``python scripts/render_board.py``
puts ``scripts/`` on ``sys.path[0]`` and never the cwd, so the worktree's own
``drydocs/`` is not shadowed in and the import falls through to that install.

What made it nasty was that it was PARTIAL. ``render_board.py`` invokes five sibling
scripts by bare name — those resolve out of the worktree's ``scripts/`` and anchor on
their own ``__file__``, so they wrote to the worktree correctly — while the three
outputs that route through the installed package went to main. One command, one torn
render, two trees.

So these tests assert the RULE, not a committed artifact: repo-*content* defaults
follow the caller's checkout, and the end-to-end case drives a real second worktree
and asserts the main tree came back untouched. A drift guard could never have caught
this — from the authoring machine the render is correct and the damage is in a
directory the test does not look at.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from drydocs_core.repo_paths import repo_root

REPO = Path(__file__).resolve().parents[2]

#: Modules whose defaults point at repo CONTENT and must therefore follow the caller.
#: Each entry is (import path, constant name) and every constant is asserted to live
#: under the resolved root. Package-internal resources (``drydocs_core/schema/*.cypher``)
#: are deliberately absent: those travel with the package and keep the ``__file__``
#: anchor.
CONTENT_PATH_CONSTANTS: tuple[tuple[str, str], ...] = (
    ("drydocs.plan_board", "DEFAULT_BACKLOG_PATH"),
    ("drydocs.plan_board", "DEFAULT_BOARD_PATH"),
    ("drydocs.plan_ideas", "DEFAULT_IDEAS_PATH"),
    ("drydocs.plan_ideas", "DEFAULT_IDEAS_OUT_PATH"),
    ("drydocs.plan_roadmap", "DEFAULT_ROADMAP_PATH"),
    ("drydocs.plan_roadmap", "DEFAULT_ROADMAP_BACKLOG_PATH"),
    ("drydocs.plan_roadmap", "DEFAULT_ROADMAP_OUT_PATH"),
)


def _make_fake_checkout(root: Path) -> Path:
    """Build the minimum tree ``repo_paths`` recognizes as a DryDocs checkout."""
    root.mkdir(parents=True, exist_ok=True)
    (root / ".git").write_text("gitdir: /elsewhere\n", encoding="utf-8")
    (root / "pyproject.toml").write_text("[tool.poetry]\nname='drydocs'\n", encoding="utf-8")
    (root / "drydocs").mkdir(exist_ok=True)
    (root / "drydocs" / "__init__.py").write_text("", encoding="utf-8")
    return root


# --------------------------------------------------------------------------- unit


def test_resolves_to_the_checkout_containing_the_cwd(tmp_path, monkeypatch):
    """The whole bug in one assertion: cwd in tree B, anchor in tree A -> B wins."""
    installed = _make_fake_checkout(tmp_path / "main-tree")
    caller = _make_fake_checkout(tmp_path / "worktree")

    monkeypatch.chdir(caller)
    assert repo_root(installed / "drydocs") == caller.resolve()


def test_resolves_from_a_subdirectory_of_the_checkout(tmp_path, monkeypatch):
    """Renders are run from anywhere in the tree, not only its root."""
    installed = _make_fake_checkout(tmp_path / "main-tree")
    caller = _make_fake_checkout(tmp_path / "worktree")
    deep = caller / "docs" / "plan"
    deep.mkdir(parents=True)

    monkeypatch.chdir(deep)
    assert repo_root(installed / "drydocs") == caller.resolve()


def test_falls_back_when_the_cwd_is_outside_any_repo(tmp_path, monkeypatch):
    """An installed-package consumer keeps the old behaviour exactly."""
    installed = _make_fake_checkout(tmp_path / "main-tree")
    outside = tmp_path / "somewhere-else"
    outside.mkdir()

    monkeypatch.chdir(outside)
    anchor = installed / "drydocs"
    assert repo_root(anchor) == anchor.resolve()


def test_a_foreign_repo_never_captures_the_paths(tmp_path, monkeypatch):
    """cwd inside the ``depgraph`` sibling must NOT redirect DryDocs' own defaults."""
    installed = _make_fake_checkout(tmp_path / "main-tree")
    foreign = tmp_path / "depgraph"
    foreign.mkdir()
    (foreign / ".git").mkdir()
    (foreign / "pyproject.toml").write_text("[project]\nname='depgraph'\n", encoding="utf-8")

    monkeypatch.chdir(foreign)
    anchor = installed / "drydocs"
    assert repo_root(anchor) == anchor.resolve()


def test_a_parent_repo_never_captures_the_paths(tmp_path, monkeypatch):
    """The climb stops at the nearest ``.git``; it does not keep going up to find a match."""
    outer = _make_fake_checkout(tmp_path / "outer-drydocs")
    inner = outer / "vendored"
    inner.mkdir()
    (inner / ".git").mkdir()
    (inner / "pyproject.toml").write_text("[project]\nname='other'\n", encoding="utf-8")

    monkeypatch.chdir(inner)
    anchor = tmp_path / "main-tree" / "drydocs"
    assert repo_root(anchor) == anchor.resolve()


@pytest.mark.parametrize(("module_path", "constant"), CONTENT_PATH_CONSTANTS)
def test_content_defaults_live_under_the_resolved_root(module_path, constant):
    """Every repo-content default must sit inside the checkout, wherever that is.

    Guards the adoption, not the helper: a new default added with a bare
    ``Path(__file__)`` anchor is exactly the regression, and adding its constant here
    is the one-line cost of the fix staying applied.
    """
    module = __import__(module_path, fromlist=[constant])
    value = getattr(module, constant)
    assert value.is_relative_to(module._REPO_ROOT), f"{module_path}.{constant} escapes the root"
    assert module._REPO_ROOT == REPO, "the test suite runs from the main checkout"


# ---------------------------------------------------------------------- end-to-end


@pytest.mark.skipif(shutil.which("git") is None, reason="git not on PATH")
def test_a_worktree_render_does_not_touch_the_main_tree(tmp_path):
    """The original incident, reproduced and asserted against.

    Drives a REAL ``git worktree`` and a REAL ``scripts/render_board.py`` run, then
    asserts the main tree's committed renders are byte-for-byte unchanged. Before the
    fix this failed on ``board.html``: the render succeeded, the worktree looked clean,
    and main quietly acquired three regenerated files.
    """
    watched = (
        REPO / "docs" / "plan" / "board.html",
        REPO / "docs" / "plan" / "ideas.html",
        REPO / "docs" / "plan" / "roadmap.html",
    )
    before = {p: p.read_bytes() for p in watched if p.is_file()}
    if not before:  # pragma: no cover - the renders are committed
        pytest.skip("no committed renders present to protect")

    worktree = tmp_path / "wt"
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(worktree), "HEAD"],
        cwd=REPO,
        check=True,
        capture_output=True,
    )
    try:
        # Strip PYTHONPATH so nothing re-injects the main tree ahead of the discovery.
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        result = subprocess.run(
            [sys.executable, str(worktree / "scripts" / "render_board.py")],
            cwd=worktree,
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0, f"render failed:\n{result.stdout}\n{result.stderr}"

        # The worktree is where the output belongs...
        assert (worktree / "docs" / "plan" / "board.html").is_file()
        # ...and every path the run printed must be inside it, not in main.
        for line in result.stdout.splitlines():
            if line.startswith("wrote "):
                assert str(REPO) not in line or str(worktree) in line, (
                    f"render wrote outside the caller's worktree: {line}"
                )

        after = {p: p.read_bytes() for p in before}
        assert after == before, "a worktree render modified the MAIN tree (Idea-109)"
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree)],
            cwd=REPO,
            check=False,
            capture_output=True,
        )
