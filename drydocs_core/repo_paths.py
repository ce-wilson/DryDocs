"""repo_paths.py — resolve the DryDocs checkout the CALLER is standing in (Idea-109).

Why this exists
---------------
Modules that default a path to repo *content* (``docs/``, ``config/``, ``knowledge/``)
used to anchor it on ``Path(__file__)``::

    _REPO_ROOT = Path(__file__).resolve().parent.parent
    DEFAULT_BOARD_PATH = _REPO_ROOT / "docs" / "plan" / "board.html"

``drydocs`` is installed **editable** — ``.venv`` carries a ``drydocs.pth`` pinned at the
main tree — so ``__file__`` names the main tree no matter which checkout the caller is in.
Running ``python scripts/render_board.py`` puts ``scripts/`` on ``sys.path[0]`` and does
*not* put the cwd on the path, so a worktree's own ``drydocs/`` is never shadowed in and
the import falls through to that editable install.

The result, reproduced on 2026-08-11 by two independent agents inside
``.claude/worktrees/`` and re-verified 2026-08-12: one ``render_board.py`` run from a
worktree writes a **torn render**. The five sibling scripts it invokes
(``render_gates``, ``render_enforcement_matrix``, ``render_load_map``,
``render_software_registry``, ``render_context_types``) anchor on their *own* ``__file__``
and correctly write into the worktree, while ``board.html``, ``ideas.html`` and
``roadmap.html`` resolve through the installed package and land in **main** — silently, on
a tree the session never touched, with the worktree left clean.

What this fixes and what it deliberately does not
-------------------------------------------------
Repo-*content* defaults follow the caller's checkout; package-*internal* resources
(``drydocs_core/schema/*.cypher`` and friends) keep their ``__file__`` anchor, because
those genuinely travel with the package. That split is the whole rule.

``fallback`` is required rather than defaulted: every caller already has the correct
``__file__`` anchor, and that anchor stays the answer whenever the cwd is not inside a
DryDocs checkout at all (an installed-package consumer, a cron job started from ``/``).
This function only ever *redirects* to a checkout it has positively identified.
"""

from __future__ import annotations

from pathlib import Path

__all__ = ["repo_root"]

# Markers that identify a DryDocs checkout specifically, rather than "some git repo".
# Both must be present: ``pyproject.toml`` alone matches any Python project, and the
# package directory alone matches a source export with no project file. The pair keeps a
# sibling repo (``depgraph``) or an unrelated parent repo from ever being adopted.
_MARKERS: tuple[tuple[str, ...], ...] = (
    ("drydocs", "__init__.py"),
    ("pyproject.toml",),
)


def _is_checkout(candidate: Path) -> bool:
    """True when ``candidate`` looks like a DryDocs checkout root."""
    return all((candidate.joinpath(*parts)).is_file() for parts in _MARKERS)


def _discover(fallback: Path) -> Path:
    """Climb from the cwd to the nearest enclosing git checkout; validate; else fallback.

    Deliberately uncached: callers resolve this once at import to freeze a module
    constant, so there is nothing to amortize, and a cache would make the cwd-dependent
    behaviour untestable within one process.

    Nearest-first is what makes worktrees work: ``.claude/worktrees/agent-x/`` sits
    *inside* the main tree, and its root carries a ``.git`` **file** (a gitdir pointer)
    rather than a directory — hence ``.exists()``, not ``.is_dir()``.

    The climb stops at the first ``.git`` it finds whether or not that repo validates. A
    non-DryDocs repo enclosing the cwd means the caller is somewhere else entirely, and
    continuing upward would let an unrelated parent repo capture the paths.
    """
    try:
        cwd = Path.cwd().resolve()
    except OSError:  # cwd deleted out from under the process
        return fallback

    for candidate in (cwd, *cwd.parents):
        if not (candidate / ".git").exists():
            continue
        return candidate if _is_checkout(candidate) else fallback
    return fallback


def repo_root(fallback: Path) -> Path:
    """Return the DryDocs checkout containing the cwd, or ``fallback``.

    ``fallback`` is the module's own ``Path(__file__)``-derived anchor — the answer when
    the cwd is outside any DryDocs checkout, which keeps installed-package consumers
    working exactly as before.
    """
    return _discover(Path(fallback).resolve())
